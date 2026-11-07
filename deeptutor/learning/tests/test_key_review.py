"""Independent choice-key review at registration (L5).

The review re-derives the key from stem + option bodies alone; a derived key
that conflicts with the stored one refuses registration, so the learner never
sees a card whose printed key is wrong. Visual questions are skipped (their
keys are grounded in pixels) and offline/operator registrations (config=None)
never call the model.
"""

import json

import pytest

from deeptutor.learning import semantic_assessment as semantic
from deeptutor.learning.models import PendingOption, PendingQuestion
from deeptutor.learning.semantic_assessment import AssessmentUnavailable
from deeptutor.learning.storage import LearningStore
from deeptutor.learning.tests.test_mastery_tools import (
    MasteryQuizTool,
    MasteryStatusTool,
    _build_basic,
    _store_init_factory,
)


def _progress_with_kp():
    from deeptutor.learning.models import (
        KnowledgePoint,
        KnowledgeType,
        LearningModule,
        LearningProgress,
    )

    progress = LearningProgress(book_id="p1")
    progress.modules = [
        LearningModule(
            id="m1",
            name="M",
            order=0,
            knowledge_points=[
                KnowledgePoint(id="kp1", name="KP", type=KnowledgeType.MEMORY, module_id="m1")
            ],
        )
    ]
    progress.knowledge_types["kp1"] = KnowledgeType.MEMORY
    return progress


def _choice_question(expected: str = "A", qid: str = "q1", visual: bool = False) -> PendingQuestion:
    return PendingQuestion(
        question_id=qid,
        knowledge_point_id="kp1",
        module_id="m1",
        prompt="What does X do?",
        question_type="choice",
        expected_answer=expected,
        options=[
            PendingOption(label="A", body="It inhibits Y"),
            PendingOption(label="B", body="It promotes Y"),
        ],
        visual_context={"task": "identification"} if visual else {},
    )


def _patch_solve(monkeypatch, derived: str, reason: str = "because") -> dict:
    captured = {}

    async def fake_request(
        config, instruction, payload, sources=None, native_images=None, *, max_tokens=2200
    ):
        captured["payload"] = payload
        captured["instruction"] = instruction
        return {
            "keys": [
                {"question_id": item["question_id"], "answer_label": derived, "reason": reason}
                for item in payload["questions"]
            ]
        }

    monkeypatch.setattr(semantic, "_request", fake_request)
    return captured


class TestVerifyChoiceKeys:
    @pytest.mark.asyncio
    async def test_conflicting_key_refuses(self, monkeypatch):
        _patch_solve(monkeypatch, derived="B")
        with pytest.raises(AssessmentUnavailable, match="conflicts with the stored key"):
            await semantic.verify_choice_keys(object(), [_choice_question(expected="A")])

    @pytest.mark.asyncio
    async def test_matching_key_passes(self, monkeypatch):
        captured = _patch_solve(monkeypatch, derived="A")
        await semantic.verify_choice_keys(object(), [_choice_question(expected="A")])
        # The solve sees stem and option bodies only — never the stored key
        # or its explanation (independence).
        sent = captured["payload"]["questions"][0]
        assert set(sent) == {"question_id", "stem", "options"}

    @pytest.mark.asyncio
    async def test_review_refusal_blocks(self, monkeypatch):
        _patch_solve(monkeypatch, derived="X", reason="two options defensible")
        with pytest.raises(AssessmentUnavailable, match="could not answer"):
            await semantic.verify_choice_keys(object(), [_choice_question(expected="A")])

    @pytest.mark.asyncio
    async def test_invalid_response_refuses(self, monkeypatch):
        async def fake_request(
            config, instruction, payload, sources=None, native_images=None, *, max_tokens=2200
        ):
            return {"keys": []}

        monkeypatch.setattr(semantic, "_request", fake_request)
        with pytest.raises(AssessmentUnavailable, match="invalid response"):
            await semantic.verify_choice_keys(object(), [_choice_question()])

    @pytest.mark.asyncio
    async def test_visual_questions_are_skipped(self, monkeypatch):
        called = {"n": 0}

        async def fake_request(*args, **kwargs):
            called["n"] += 1
            return {"keys": []}

        monkeypatch.setattr(semantic, "_request", fake_request)
        await semantic.verify_choice_keys(object(), [_choice_question(visual=True)])
        assert called["n"] == 0

    @pytest.mark.asyncio
    async def test_non_choice_questions_are_skipped(self, monkeypatch):
        called = {"n": 0}

        async def fake_request(*args, **kwargs):
            called["n"] += 1
            return {"keys": []}

        monkeypatch.setattr(semantic, "_request", fake_request)
        short = PendingQuestion(
            question_id="q2",
            knowledge_point_id="kp1",
            module_id="m1",
            prompt="What is X?",
            question_type="short",
            expected_answer="Y",
        )
        await semantic.verify_choice_keys(object(), [short])
        assert called["n"] == 0

    @pytest.mark.asyncio
    async def test_batched_keys_stay_per_question(self, monkeypatch):
        captured = _patch_solve(monkeypatch, derived="A")
        questions = [
            _choice_question(expected="A", qid="q1"),
            _choice_question(expected="A", qid="q2"),
        ]
        await semantic.verify_choice_keys(object(), questions)
        assert len(captured["payload"]["questions"]) == 2


class TestBindWiring:
    @pytest.mark.asyncio
    async def test_explicit_config_triggers_review(self, monkeypatch):
        progress_question = _choice_question(expected="A")
        calls = {"review": 0}

        async def fake_review(config, questions):
            calls["review"] += 1
            assert questions[0].question_id == progress_question.question_id

        monkeypatch.setattr(semantic, "verify_choice_keys", fake_review)

        # bind_questions with no evidence and no explanation short-circuits
        # the audit, but the key review must still run for choice questions.
        class FakeStore:
            def get_topic(self, *args, **kwargs):
                return None

        progress = _progress_with_kp()
        await semantic.bind_questions(FakeStore(), progress, [progress_question], config=object())
        assert calls["review"] == 1

    @pytest.mark.asyncio
    async def test_none_config_stays_offline(self, monkeypatch):
        async def explode(config, questions):
            raise AssertionError("config=None must not call the review")

        monkeypatch.setattr(semantic, "verify_choice_keys", explode)
        progress_question = _choice_question(expected="A")

        class FakeStore:
            def get_topic(self, *args, **kwargs):
                return None

        progress = _progress_with_kp()
        await semantic.bind_questions(FakeStore(), progress, [progress_question], config=None)


class TestQuizToolWiring:
    @pytest.fixture
    def path_id(self, tmp_path, monkeypatch):
        monkeypatch.setattr(LearningStore, "__init__", _store_init_factory(tmp_path))
        from deeptutor.learning import semantic_assessment

        async def judge(_config, items):
            raise AssertionError(f"no semantic grading expected here: {items!r}")

        monkeypatch.setattr(semantic_assessment, "judge_answers", judge)
        return "test_path"

    @pytest.mark.asyncio
    async def test_conflicting_key_blocks_registration(self, path_id, monkeypatch):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        # Registration shuffles options before bind, so the reviewer derives
        # from the actual payload bodies: the wrong body "5" here.
        async def fake_request(
            config, instruction, payload, sources=None, native_images=None, *, max_tokens=2200
        ):
            return {
                "keys": [
                    {
                        "question_id": item["question_id"],
                        "answer_label": next(
                            o["label"] for o in item["options"] if o["body"] == "5"
                        ),
                        "reason": "mistakenly picked 5",
                    }
                    for item in payload["questions"]
                ]
            }

        monkeypatch.setattr(semantic, "_request", fake_request)
        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="What does 2+2 equal?",
            expected_answer="A",
            question_type="choice",
            options=[{"label": "A", "body": "4"}, {"label": "B", "body": "5"}],
        )
        assert result.success is False
        assert "conflicts with the stored key" in result.content
        # Nothing was registered: the learner never sees the wrong-key card.
        from deeptutor.learning.service import LearningService

        assert LearningService(LearningStore()).store.get_active_interaction(path_id) is None

    @pytest.mark.asyncio
    async def test_consistent_key_registers(self, path_id, monkeypatch):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        # The reviewer derives from the shuffled payload bodies and agrees
        # with the stored key (body "4" is correct).
        async def fake_request(
            config, instruction, payload, sources=None, native_images=None, *, max_tokens=2200
        ):
            return {
                "keys": [
                    {
                        "question_id": item["question_id"],
                        "answer_label": next(
                            o["label"] for o in item["options"] if o["body"] == "4"
                        ),
                        "reason": "2+2=4",
                    }
                    for item in payload["questions"]
                ]
            }

        monkeypatch.setattr(semantic, "_request", fake_request)
        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="What does 2+2 equal?",
            expected_answer="A",
            question_type="choice",
            options=[{"label": "A", "body": "4"}, {"label": "B", "body": "5"}],
        )
        assert result.success is True
