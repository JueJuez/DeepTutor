"""A correct choice key must not authorize a contradictory explanation."""

import pytest

from deeptutor.learning import semantic_assessment as semantic
from deeptutor.learning.models import PendingOption
from tests.capabilities.test_mastery_question_groups import leaf

pytest_plugins = ["tests.capabilities.test_mastery_question_groups"]


def gradient_question():
    question = leaf(expected="A")
    question.prompt = "At a point with derivative -2, which direction does gradient descent move?"
    question.question_type = "choice"
    question.options = [
        PendingOption(label="A", body="Increase theta for a positive learning rate."),
        PendingOption(label="B", body="Decrease theta for a positive learning rate."),
    ]
    question.explanation = (
        "A negative derivative means increasing theta increases the loss, "
        "so to decrease the loss we increase theta."
    )
    return question


@pytest.mark.asyncio
@pytest.mark.parametrize("decision", [False, None, "true"])
async def test_correct_key_cannot_bypass_explanation_review(service, monkeypatch, decision):
    from deeptutor.capabilities.mastery import tools

    async def request(config, instruction, payload, **kwargs):
        assert "explanation" in instruction and "contradiction" in instruction
        assert payload["question"]["explanation"] == gradient_question().explanation
        result = {"supported": True, "citations": [], "provenance": "adapted"}
        if decision is not None:
            result["explanation_valid"] = decision
        return result

    monkeypatch.setattr(semantic, "_request", request)
    monkeypatch.setattr(tools, "_new_service", lambda: service)
    question = gradient_question()
    result = await tools.MasteryQuizTool().execute(
        _mastery_path_id="p",
        knowledge_point_id="kp1",
        question=question.prompt,
        expected_answer="A",
        question_type="choice",
        options=[option.model_dump() for option in question.options],
        explanation=question.explanation,
    )
    assert not result.success
    assert "explanation" in result.content.lower()
    assert service.store.get_active_interaction("p") is None
    progress = service.store.load("p")
    assert not progress.quiz_attempts and not progress.learning_evidence


@pytest.mark.asyncio
async def test_review_receipt_survives_reload_and_detects_explanation_change(service, monkeypatch):
    from deeptutor.learning.lesson_evidence import LessonUnavailable

    calls = []

    async def request(config, instruction, payload, **kwargs):
        calls.append(payload)
        return {"supported": True, "explanation_valid": True, "citations": []}

    monkeypatch.setattr(semantic, "_request", request)
    question = gradient_question()
    question.explanation = (
        "For a sufficiently small positive step, a negative derivative lowers loss."
    )
    await semantic.bind_question(service.store, service.store.load("p"), question)
    service.register_question("p", question)
    stored = service.store.get_active_interaction("p").question
    semantic.validate_question(service.store, service.store.load("p"), stored)
    assert len(calls) == 1
    assert stored.content_review["explanation_valid"] is True
    stored.explanation = gradient_question().explanation
    with pytest.raises(LessonUnavailable, match="changed"):
        semantic.validate_question(service.store, service.store.load("p"), stored)


@pytest.mark.asyncio
async def test_empty_unlocated_explanation_keeps_no_model_fast_path(service, monkeypatch):
    async def request(*args, **kwargs):
        pytest.fail("No explanation or source needs a content review")

    monkeypatch.setattr(semantic, "_request", request)
    question = leaf()
    question.explanation = ""
    await semantic.bind_question(service.store, service.store.load("p"), question)
    assert not question.source_evidence


@pytest.mark.asyncio
async def test_source_support_does_not_replace_explanation_review(service, monkeypatch):
    from deeptutor.learning import lesson_evidence

    progress = service.store.load("p")
    progress.lesson_evidence["kp1"] = {
        "sources": [
            {"ref": {}, "text": "Gradient descent moves in the negative gradient direction."}
        ]
    }
    monkeypatch.setattr(lesson_evidence, "validate_evidence", lambda *a, **kw: None)

    async def request(*args, **kwargs):
        return {
            "supported": True,
            "explanation_valid": False,
            "citations": [{"index": 0, "quote": "negative gradient direction"}],
        }

    monkeypatch.setattr(semantic, "_request", request)
    with pytest.raises(semantic.AssessmentUnavailable, match="explanation"):
        await semantic.bind_question(service.store, progress, gradient_question())


@pytest.mark.asyncio
async def test_group_reviews_explanations_in_one_call_and_rejects_one_bad_leaf(
    service, monkeypatch
):
    from deeptutor.capabilities.mastery import tools

    calls = []

    async def request(config, instruction, payload, **kwargs):
        calls.append(payload)
        return {
            "contracts": [
                {
                    "question_id": item["question"]["question_id"],
                    "supported": True,
                    "explanation_valid": index == 0,
                    "citations": [],
                }
                for index, item in enumerate(payload["questions"])
            ]
        }

    monkeypatch.setattr(semantic, "_request", request)
    monkeypatch.setattr(tools, "_new_service", lambda: service)
    result = await tools.MasteryQuizTool().execute(
        _mastery_path_id="p",
        questions=[
            {
                "knowledge_point_id": "kp1",
                "question": "First?",
                "expected_answer": "alpha",
                "explanation": "Alpha is first.",
            },
            {
                "knowledge_point_id": "kp2",
                "question": "Second?",
                "expected_answer": "beta",
                "explanation": "Beta is first so it is second.",
            },
        ],
    )
    assert not result.success and len(calls) == 1
    assert service.store.get_active_interaction("p") is None


@pytest.mark.asyncio
async def test_empty_review_output_cannot_trigger_replacement_review_loop(service, monkeypatch):
    from deeptutor.capabilities.mastery import tools
    from deeptutor.capabilities.mastery.loop import MasteryLoopCapability
    from deeptutor.core.context import UnifiedContext
    from deeptutor.services.llm import factory

    calls = []

    async def complete(**kwargs):
        calls.append(kwargs)
        assert kwargs["max_tokens"] == 4096
        return ""  # Observed reasoning-only response at its old output cap.

    monkeypatch.setattr(factory, "complete_with_config", complete)
    monkeypatch.setattr("deeptutor.services.llm.config.get_llm_config", lambda: object())
    monkeypatch.setattr(tools, "_new_service", lambda: service)
    context = UnifiedContext(
        session_id="s",
        user_message="quiz",
        metadata={
            "mastery_mode": True,
            "mastery_path_id": "p",
        },
    )
    cap = MasteryLoopCapability()
    args = {
        "knowledge_point_id": "kp1",
        "question": "Which direction?",
        "expected_answer": "up",
        "explanation": "This explanation needs review.",
    }
    first = await tools.MasteryQuizTool().execute(
        **cap.augment_kwargs("mastery_quiz", args, context)
    )
    second = await tools.MasteryQuizTool().execute(
        **cap.augment_kwargs(
            "mastery_quiz",
            {**args, "question": "Try a different question?"},
            context,
        )
    )
    assert not first.success and not second.success
    assert "JSON" in first.content and len(calls) == 1
    assert service.store.get_active_interaction("p") is None
    assert not service.store.load("p").learning_evidence
