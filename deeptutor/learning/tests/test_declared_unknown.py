"""Declared "I don't know" answers: ungraded semantics plus one consolidation signal.

A learner who explicitly states they do not know (or skips) is never graded
incorrect: there is no answered content to contradict, and honesty must not
cost mastery credit. The receipt stays ungraded with ``declared_unknown`` set,
no QuizAttempt or ErrorRecord is created and mastery does not move — but one
``declared_unknown`` review event (quality 0) feeds the existing scheduler so
the objective still reaches the cross-session review queue. A plain ungraded
verdict (insufficient evidence, ambiguous intent) keeps the legacy behaviour:
clarification only, no scheduling signal, nothing recorded.
"""

import pytest

from deeptutor.learning.lesson_evidence import objective_fingerprint
from deeptutor.learning.models import (
    InteractionStatus,
    KnowledgePoint,
    KnowledgeType,
    LearningModule,
    LearningProgress,
    PendingQuestion,
)
from deeptutor.learning.scheduler import SpacedRepetitionScheduler
from deeptutor.learning.semantic_assessment import Verdict, fingerprint
from deeptutor.learning.service import LearningService
from deeptutor.learning.storage import LearningStore


def _progress_with_kp(kp_type: KnowledgeType = KnowledgeType.MEMORY) -> LearningProgress:
    progress = LearningProgress(book_id="path1")
    progress.modules = [
        LearningModule(
            id="m1",
            name="Module 1",
            order=0,
            knowledge_points=[KnowledgePoint(id="kp1", name="KP1", type=kp_type, module_id="m1")],
        )
    ]
    progress.knowledge_types["kp1"] = kp_type
    return progress


def _pending() -> PendingQuestion:
    return PendingQuestion(
        question_id="q1",
        knowledge_point_id="kp1",
        module_id="m1",
        prompt="What is photosynthesis?",
        question_type="short",
        expected_answer="photosynthesis",
    )


def _unknown_verdict() -> dict:
    return Verdict(
        result="ungraded",
        confidence=0.2,
        feedback="The learner stated they do not know this yet.",
        declared_unknown=True,
    ).receipt()


def _assessment_for(interaction, progress) -> dict:
    return {
        "state": fingerprint(interaction.model_dump()),
        "objectives": {"kp1": objective_fingerprint(progress, "kp1")},
        "verdicts": {"q1": _unknown_verdict()},
        "sources": {},
    }


class TestVerdictReceipt:
    def test_declared_unknown_receipt(self):
        receipt = _unknown_verdict()
        assert receipt["result"] == "ungraded"
        assert receipt["final"] is False
        assert receipt["declared_unknown"] is True
        assert receipt["is_correct"] is None

    def test_legacy_receipt_has_no_declared_unknown(self):
        receipt = Verdict(
            result="ungraded", confidence=0, feedback="Please provide an answer."
        ).receipt()
        assert receipt["declared_unknown"] is None

    def test_graded_receipt_carries_false_flag(self):
        receipt = Verdict(result="correct", confidence=0.99, feedback="Matches.").receipt()
        assert receipt["final"] is True
        assert receipt["declared_unknown"] is None


class TestDeclaredUnknownGradeFlow:
    @pytest.mark.asyncio
    async def test_declared_unknown_records_consolidation_only(self, tmp_path):
        service = LearningService(LearningStore(root=tmp_path))
        progress = _progress_with_kp()
        service.save(progress)
        _, interaction, created = service.register_question("path1", _pending())
        assert created

        graded_progress, graded, _ = service.grade_interaction(
            "path1",
            answer="我不知道",
            question_id="q1",
            scheduler=SpacedRepetitionScheduler(),
            _assessment=_assessment_for(interaction, progress),
        )

        assert graded.status is InteractionStatus.ANSWERED
        assert graded.result["result"] == "ungraded"
        assert graded.result["declared_unknown"] is True
        # One consolidation event, no attempt, no error record, no mastery move.
        evidence = [
            item
            for item in graded_progress.learning_evidence
            if item.assessment_type == "declared_unknown"
        ]
        assert len(evidence) == 1
        assert evidence[0].question_id == "q1"
        assert evidence[0].result == "ungraded"
        assert evidence[0].quality == 0.0
        assert graded_progress.quiz_attempts == []
        assert graded_progress.error_records == []
        assert "kp1" not in graded_progress.mastery_levels
        # The gap still reaches the existing scheduler.
        assert "kp1" in graded_progress.repetition_states
        assert any(task.knowledge_point_id == "kp1" for task in graded_progress.review_queue)

    @pytest.mark.asyncio
    async def test_resubmitted_unknown_does_not_duplicate_the_signal(self, tmp_path):
        service = LearningService(LearningStore(root=tmp_path))
        progress = _progress_with_kp()
        service.save(progress)
        _, interaction, _ = service.register_question("path1", _pending())
        service.grade_interaction(
            "path1",
            answer="我不知道",
            question_id="q1",
            scheduler=SpacedRepetitionScheduler(),
            _assessment=_assessment_for(interaction, progress),
        )

        # A resubmission re-grades the (still open) interaction, so the fence
        # must be rebuilt from the current persisted state.
        current = service.store.get_interaction("path1", "q1")
        _, retry_interaction, replayed = service.grade_interaction(
            "path1",
            answer="我不知道",
            question_id="q1",
            scheduler=SpacedRepetitionScheduler(),
            _assessment=_assessment_for(current, service.store.load("path1")),
        )

        assert retry_interaction.result["declared_unknown_recorded"] is True
        signals = [
            item
            for item in service.store.load("path1").learning_evidence
            if item.assessment_type == "declared_unknown"
        ]
        assert len(signals) == 1
        assert replayed is False

    @pytest.mark.asyncio
    async def test_plain_ungraded_keeps_legacy_behaviour(self, tmp_path):
        service = LearningService(LearningStore(root=tmp_path))
        progress = _progress_with_kp()
        service.save(progress)
        _, interaction, _ = service.register_question("path1", _pending())
        verdicts = {
            "q1": Verdict(
                result="ungraded",
                confidence=0.1,
                feedback="Cannot verify against the supplied evidence.",
            ).receipt()
        }

        graded_progress, graded, _ = service.grade_interaction(
            "path1",
            answer="大概是叶绿体?",
            question_id="q1",
            scheduler=SpacedRepetitionScheduler(),
            _assessment={
                "state": fingerprint(interaction.model_dump()),
                "objectives": {"kp1": objective_fingerprint(progress, "kp1")},
                "verdicts": verdicts,
                "sources": {},
            },
        )

        assert graded.status is InteractionStatus.ANSWERED
        assert graded.result["declared_unknown"] is None
        assert graded_progress.learning_evidence == []
        assert graded_progress.quiz_attempts == []
        assert graded_progress.repetition_states == {}

    @pytest.mark.asyncio
    async def test_group_leaf_declared_unknown_records_once(self, tmp_path):
        service = LearningService(LearningStore(root=tmp_path))
        progress = _progress_with_kp()
        service.save(progress)
        leaf_a = PendingQuestion(
            question_id="qA",
            knowledge_point_id="kp1",
            module_id="m1",
            prompt="What is photosynthesis?",
            question_type="short",
            expected_answer="photosynthesis",
        )
        leaf_b = PendingQuestion(
            question_id="qB",
            knowledge_point_id="kp1",
            module_id="m1",
            prompt="Where does photosynthesis happen?",
            question_type="short",
            expected_answer="chloroplast",
        )
        group = PendingQuestion(
            question_id="group1",
            knowledge_point_id="kp1",
            module_id="m1",
            prompt="",
            question_type="group",
            questions=[leaf_a, leaf_b],
        )
        _, interaction, _ = service.register_question("path1", group)
        verdicts = {
            "qA": _unknown_verdict(),
            "qB": Verdict(
                result="correct", confidence=0.95, feedback="Matches the stored answer."
            ).receipt(),
        }

        graded_progress, graded, _ = service.grade_interaction(
            "path1",
            answer="",
            answers={"qA": "我不知道", "qB": "chloroplast"},
            question_id="group1",
            scheduler=SpacedRepetitionScheduler(),
            _assessment={
                "state": fingerprint(interaction.model_dump()),
                "objectives": {"kp1": objective_fingerprint(progress, "kp1")},
                "verdicts": verdicts,
                "sources": {},
            },
        )

        signals = [
            item
            for item in graded_progress.learning_evidence
            if item.assessment_type == "declared_unknown"
        ]
        assert len(signals) == 1
        assert signals[0].question_id == "qA"
        # qB was graded final (a real attempt); qA never became one.
        assert [attempt.question_id for attempt in graded_progress.quiz_attempts] == ["qB"]
        leaf_results = {row["question_id"]: row for row in graded.result.get("results", [])}
        assert leaf_results["qA"]["declared_unknown"] is True
        assert leaf_results["qB"]["final"] is True


class TestJudgePromptContract:
    @pytest.mark.asyncio
    async def test_judge_prompt_carries_the_declared_unknown_rule(self, monkeypatch):
        from deeptutor.learning import semantic_assessment

        captured = {}

        async def fake_request(
            config, instruction, payload, sources=None, native_images=None, *, max_tokens=2200
        ):
            captured["instruction"] = instruction
            return {
                "verdicts": [
                    {
                        "question_id": "q1",
                        "result": "ungraded",
                        "confidence": 0.2,
                        "feedback": "The learner stated they do not know.",
                        "declared_unknown": True,
                    }
                ]
            }

        monkeypatch.setattr(semantic_assessment, "_request", fake_request)
        verdicts = await semantic_assessment.judge_answers(
            None,
            [{"question_id": "q1", "prompt": "What is X?", "answer": "我不知道"}],
        )
        assert "declared_unknown=true" in captured["instruction"]
        assert "never incorrect" in captured["instruction"]
        assert verdicts["q1"].declared_unknown is True
