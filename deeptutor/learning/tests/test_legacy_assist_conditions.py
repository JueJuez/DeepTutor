"""Legacy assist conditions stay "unknown" — never upgraded to independent.

Records created before assist tracking (or by paths that never capture it)
load without ``hints_used`` / ``independent`` values. Those records must keep
an honest unknown state through reloads, recomputation and repair: they can
neither prove independence nor claim help (docs 9.6 R4).
"""

from __future__ import annotations

import json

from deeptutor.learning import policy
from deeptutor.learning.assessment import AssessmentRecord, to_notebook_item
from deeptutor.learning.models import (
    KnowledgePoint,
    KnowledgeType,
    LearningEvidence,
    LearningModule,
    LearningProgress,
    QuizAttempt,
)
from deeptutor.learning.scheduler import _resolved_quality
from deeptutor.learning.storage import LearningStore


def _progress(*kps: KnowledgePoint) -> LearningProgress:
    progress = LearningProgress(book_id="b1")
    progress.modules = [LearningModule(id="m1", name="M1", order=0, knowledge_points=list(kps))]
    for kp in kps:
        progress.knowledge_types[kp.id] = kp.type
    return progress


def _kp(kp_id: str, kp_type: KnowledgeType) -> KnowledgePoint:
    return KnowledgePoint(id=kp_id, name=kp_id, type=kp_type, module_id="m1")


def _legacy_evidence(kp_id: str, **overrides) -> LearningEvidence:
    """Evidence loaded from JSON written before hints capture existed."""
    raw = {
        "knowledge_point_id": kp_id,
        "assessment_type": "qualitative",
        "result": "correct",
    }
    raw.update(overrides)
    return LearningEvidence.model_validate(raw)


def test_legacy_evidence_keeps_unknown_hints_through_store_roundtrip(tmp_path):
    store = LearningStore(root=tmp_path)
    kp = _kp("kp1", KnowledgeType.CONCEPT)
    progress = _progress(kp)
    progress.learning_evidence.append(_legacy_evidence("kp1"))
    store.save(progress)

    reloaded = store.load("b1")
    assert reloaded.learning_evidence[0].hints_used is None

    # A second save/load must not fill the unknown with a captured zero.
    store.save(reloaded)
    assert store.load("b1").learning_evidence[0].hints_used is None


def test_legacy_qualitative_pass_is_not_independently_demonstrated():
    kp = _kp("kp1", KnowledgeType.CONCEPT)
    progress = _progress(kp)
    progress.qualitative_mastery["kp1"] = True
    progress.mastery_levels["kp1"] = 0.4
    progress.learning_evidence.append(_legacy_evidence("kp1"))

    assert policy.learning_stage(progress, "kp1") == "practiced_not_demonstrated"
    # The map must not show the full qualitative pass for unproven independence.
    assert policy.display_mastery(progress, kp) == 0.4

    # Only an explicitly captured "no hints" pass demonstrates independence.
    captured = _progress(_kp("kp2", KnowledgeType.CONCEPT))
    captured.qualitative_mastery["kp2"] = True
    captured.mastery_levels["kp2"] = 0.4
    captured.learning_evidence.append(_legacy_evidence("kp2", hints_used=0))
    assert policy.learning_stage(captured, "kp2") == "independently_demonstrated"
    assert policy.display_mastery(captured, _kp("kp2", KnowledgeType.CONCEPT)) == 1.0


def test_legacy_hinted_pass_still_counts_as_practiced_with_help():
    kp = _kp("kp1", KnowledgeType.CONCEPT)
    progress = _progress(kp)
    progress.learning_evidence.append(_legacy_evidence("kp1", hints_used=2))
    assert policy.learning_stage(progress, "kp1") == "practiced_with_help"


def test_legacy_quiz_attempt_without_independence_flag_stays_unknown():
    kp = _kp("kp1", KnowledgeType.MEMORY)
    progress = _progress(kp)
    legacy_attempt = QuizAttempt.model_validate(
        {"question_id": "q", "knowledge_point_id": "kp1", "is_correct": True}
    )
    assert legacy_attempt.independent is None
    progress.quiz_attempts.append(legacy_attempt)

    # Unknown independence neither demonstrates nor claims help.
    assert policy.learning_stage(progress, "kp1") == "practiced_not_demonstrated"

    # Mastery from independent attempts excludes the unknown record.
    correctness = [
        0.5 if a.result == "partial" else a.is_correct
        for a in progress.quiz_attempts
        if a.knowledge_point_id == "kp1" and not a.voided and a.independent is True
    ]
    assert correctness == []

    explicit = _progress(kp)
    explicit.quiz_attempts.append(
        QuizAttempt.model_validate(
            {
                "question_id": "q",
                "knowledge_point_id": "kp1",
                "is_correct": True,
                "independent": True,
            }
        )
    )
    assert policy.learning_stage(explicit, "kp1") == "independently_demonstrated"
    assisted = _progress(kp)
    assisted.quiz_attempts.append(
        QuizAttempt.model_validate(
            {
                "question_id": "q",
                "knowledge_point_id": "kp1",
                "is_correct": True,
                "independent": False,
            }
        )
    )
    assert policy.learning_stage(assisted, "kp1") == "practiced_with_help"


def test_visual_achievement_requires_captured_zero_hints():
    kp = _kp("kp1", KnowledgeType.DESIGN)
    progress = _progress(kp)
    progress.learning_evidence.append(
        _legacy_evidence(
            "kp1",
            visual_context={"task": "identify", "key_status": "verified"},
        )
    )
    assert policy.visual_achievements(progress, "kp1") == []

    progress.learning_evidence.append(
        _legacy_evidence(
            "kp1",
            hints_used=0,
            visual_context={"task": "compare", "key_status": "verified"},
        )
    )
    assert policy.visual_achievements(progress, "kp1") == ["compare"]


def test_legacy_assessment_record_and_notebook_boundary():
    legacy = AssessmentRecord.model_validate(
        {
            "session_id": "synthetic",
            "question_id": "q",
            "question": "q",
            "user_answer": "a",
            "result": "correct",
        }
    )
    assert legacy.hints_used is None
    junk = AssessmentRecord.model_validate(
        {
            "session_id": "synthetic",
            "question_id": "q",
            "question": "q",
            "user_answer": "a",
            "result": "correct",
            "hints_used": "not-a-number",
        }
    )
    # Unparseable hint counts are unknown, not "captured: no hints".
    assert junk.hints_used is None

    item = to_notebook_item(legacy, [])
    # The notebook API contract is an integer; unknown renders as 0 there.
    assert item["hints_used"] == 0


def test_scheduler_quality_tolerates_unknown_hints():
    evidence = _legacy_evidence("kp1", quality=None, hints_used=None)
    assert _resolved_quality(evidence) == 1.0
    hinted = _legacy_evidence("kp1", quality=None, hints_used=2)
    assert _resolved_quality(hinted) < 1.0


def test_progress_json_serializes_unknown_without_filling(tmp_path):
    import sqlite3

    store = LearningStore(root=tmp_path)
    kp = _kp("kp1", KnowledgeType.CONCEPT)
    progress = _progress(kp)
    progress.learning_evidence.append(_legacy_evidence("kp1"))
    store.save(progress)

    with sqlite3.connect(tmp_path / "mastery.sqlite3") as conn:
        state_json = conn.execute(
            "SELECT state_json FROM mastery_paths WHERE path_id = 'b1'"
        ).fetchone()[0]
    raw = json.loads(state_json)
    evidence = raw["learning_evidence"][0]
    assert "hints_used" not in evidence or evidence["hints_used"] is None
