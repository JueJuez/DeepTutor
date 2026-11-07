"""Mechanical mastery_quiz guards: position-dependency blocker and stem registry.

Two deterministic filters inspired by LogiNote's quickCheck guards
(main@d3ffa2e1): a question whose stem or options hardcode an option position
never registers (order is shuffled at registration), and every registered
stem lands in a rolling per-objective registry. The registry is deliberately
informational across turns — re-posing the same question after teaching is the
documented retry flow — while duplicates inside one registration batch are
refused outright.
"""

import json

import pytest

from deeptutor.learning.pending import (
    position_dependent_quiz_text,
    quiz_stem_key,
)
from deeptutor.learning.service import LearningService
from deeptutor.learning.storage import LearningStore
from deeptutor.learning.tests.test_mastery_tools import (
    MasteryGradeTool,
    MasteryQuizTool,
    MasteryStatusTool,
    _build_basic,
    _store_init_factory,
)


def _load(path_id):
    return LearningService(LearningStore()).store.load(path_id)


@pytest.fixture
def path_id(tmp_path, monkeypatch):
    monkeypatch.setattr(LearningStore, "__init__", _store_init_factory(tmp_path))
    from deeptutor.learning import semantic_assessment

    async def judge(_config, items):
        raise AssertionError(f"bind must stay offline for these questions: {items!r}")

    monkeypatch.setattr(semantic_assessment, "judge_answers", judge)
    return "test_path"


class TestQuizStemKey:
    def test_cosmetic_rewording_collides(self):
        assert quiz_stem_key("What is X?") == quiz_stem_key("what is x")
        assert quiz_stem_key("What is X？") == quiz_stem_key("What  is X")
        assert quiz_stem_key("ｗｈａｔ ｉｓ ｘ") == quiz_stem_key("WHAT IS X")

    def test_different_asks_stay_distinct(self):
        assert quiz_stem_key("What is X?") != quiz_stem_key("When is X used?")
        assert quiz_stem_key("解释 X 的含义") != quiz_stem_key("举一个应用 X 的例子")


class TestPositionDependentDetection:
    @pytest.mark.parametrize(
        "text",
        [
            "以上都对",
            "以上都不对",
            "以上全正确",
            "上述所有选项中",
            "请选A",
            "选择B项",
            "第二个选项",
            "All of the above",
            "None of the above",
        ],
    )
    def test_flags_position_dependent_text(self, text):
        assert position_dependent_quiz_text(text)

    @pytest.mark.parametrize(
        "text",
        [
            "以下哪项正确",
            "选项A的含义是什么",
            "请选择合适的答案",
            "Which statement is correct?",
            "",
        ],
    )
    def test_leaves_self_contained_text_alone(self, text):
        assert not position_dependent_quiz_text(text)


class TestMasteryQuizPositionGuard:
    @pytest.mark.asyncio
    async def test_stem_referencing_a_label_is_refused(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="以上哪一项是对的？请选A。",
            expected_answer="4",
            question_type="choice",
            options=[{"label": "A", "body": "4"}, {"label": "B", "body": "5"}],
        )
        assert result.success is False
        assert "option position" in result.content

    @pytest.mark.asyncio
    async def test_option_body_all_of_the_above_is_refused(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="Which value is correct?",
            expected_answer="D",
            question_type="choice",
            options=[
                {"label": "A", "body": "4"},
                {"label": "B", "body": "5"},
                {"label": "C", "body": "6"},
                {"label": "D", "body": "All of the above"},
            ],
        )
        assert result.success is False
        assert "option position" in result.content

    @pytest.mark.asyncio
    async def test_self_contained_choice_registers(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="Which value equals 2+2?",
            expected_answer="A",
            question_type="choice",
            options=[{"label": "A", "body": "4"}, {"label": "B", "body": "5"}],
        )
        assert result.success is True


class TestStemRegistry:
    @pytest.mark.asyncio
    async def test_registered_stems_land_in_the_registry(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]
        quiz = MasteryQuizTool()

        await quiz.execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="2+2?",
            expected_answer="4",
            question_type="short",
        )
        progress = _load(path_id)
        assert progress.question_stem_keys.get(kp_id) == [quiz_stem_key("2+2?")]

    @pytest.mark.asyncio
    async def test_cross_turn_repeat_stays_allowed(self, path_id):
        """Re-posing the same question after grading is the retry flow."""
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]
        quiz = MasteryQuizTool()
        grade = MasteryGradeTool()

        for _ in range(2):
            posed = await quiz.execute(
                _mastery_path_id=path_id,
                knowledge_point_id=kp_id,
                question="2+2?",
                expected_answer="4",
                question_type="short",
            )
            assert posed.success is True
            graded = json.loads((await grade.execute(_mastery_path_id=path_id, answer="4")).content)
            assert graded["is_correct"] is True
        progress = _load(path_id)
        assert len(progress.question_stem_keys.get(kp_id, [])) == 1


class TestGroupBatchStemDedup:
    @pytest.mark.asyncio
    async def test_duplicate_stems_inside_one_batch_are_refused(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            questions=[
                {
                    "knowledge_point_id": kp_id,
                    "question": "2+2?",
                    "expected_answer": "4",
                    "question_type": "short",
                },
                {
                    "knowledge_point_id": kp_id,
                    "question": "2 + 2 ?",
                    "expected_answer": "4",
                    "question_type": "short",
                },
            ],
        )
        assert result.success is False
        assert "same stem" in result.content

    @pytest.mark.asyncio
    async def test_distinct_batch_stems_register(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            questions=[
                {
                    "knowledge_point_id": kp_id,
                    "question": "2+2?",
                    "expected_answer": "4",
                    "question_type": "short",
                },
                {
                    "knowledge_point_id": kp_id,
                    "question": "What is 3+3?",
                    "expected_answer": "6",
                    "question_type": "short",
                },
            ],
        )
        assert result.success is True


class TestDesignLayer:
    @pytest.mark.asyncio
    async def test_design_is_recorded_and_hinted(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="2+2?",
            expected_answer="4",
            question_type="short",
            design={"operation": "predict", "scenario": "Two apples are added to two apples."},
        )
        assert result.success is True
        payload = (result.metadata or {})["mastery_quiz"]
        assert payload["design_hint"]["recent_operations"] == ["predict"]
        # The just-used operation is excluded from the next suggestion.
        assert payload["design_hint"]["next_operation"] != "predict"
        progress = _load(path_id)
        assert progress.question_operations.get(kp_id) == ["predict"]
        assert progress.question_stem_keys.get(kp_id) == [quiz_stem_key("2+2?")]

    @pytest.mark.asyncio
    async def test_design_survives_persistence(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="2+2?",
            expected_answer="4",
            question_type="short",
            design={
                "operation": "counterfactual",
                "scenario": "如果再加一个苹果而不是两个",
                "focus": "加法交换",
                "required_detail": "说出总数并说明理由",
            },
        )
        interaction = LearningService(LearningStore()).store.get_active_interaction(path_id)
        design = interaction.question.design
        assert design is not None
        assert design.operation == "counterfactual"
        assert design.scenario == "如果再加一个苹果而不是两个"
        assert design.focus == "加法交换"

    @pytest.mark.asyncio
    async def test_unknown_operation_refused(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="2+2?",
            expected_answer="4",
            question_type="short",
            design={"operation": "vibes", "scenario": "anything"},
        )
        assert result.success is False
        assert "design.operation must be one of" in result.content

    @pytest.mark.asyncio
    async def test_operation_without_scenario_refused(self, path_id):
        await _build_basic(path_id)
        status = json.loads((await MasteryStatusTool().execute(_mastery_path_id=path_id)).content)
        kp_id = status["next"]["knowledge_point_id"]

        result = await MasteryQuizTool().execute(
            _mastery_path_id=path_id,
            knowledge_point_id=kp_id,
            question="2+2?",
            expected_answer="4",
            question_type="short",
            design={"operation": "predict"},
        )
        assert result.success is False
        assert "design.scenario is required" in result.content

    def test_group_leaf_schema_carries_design(self):
        definition = MasteryQuizTool().get_definition()
        schema = definition.to_openai_schema()["function"]["parameters"]
        items = schema["properties"]["questions"]["items"]
        assert "design" in items["properties"]
        leaf_design = items["properties"]["design"]["items"]
        assert leaf_design["required"] == ["operation", "scenario"]
        assert "counterfactual" in leaf_design["properties"]["operation"]["enum"]


class TestNextOperationHint:
    def test_prefers_operations_not_recently_used(self):
        from deeptutor.learning.pending import next_operation_hint

        assert next_operation_hint("concept", ["counterfactual"]) == "contrast"
        assert next_operation_hint("concept", ["counterfactual", "contrast"]) == "diagnose"
        assert next_operation_hint("memory", ["counterfactual", "contrast"]) == "diagnose"
        assert next_operation_hint("design", []) == "construct"

    def test_falls_back_to_first_preference_when_all_recent(self):
        from deeptutor.learning.pending import QUIZ_OPERATIONS, next_operation_hint

        assert next_operation_hint("concept", list(QUIZ_OPERATIONS)) == "counterfactual"
