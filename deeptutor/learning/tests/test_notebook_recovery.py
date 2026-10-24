"""Fault injection against real learning/session databases; no paid providers."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

import pytest

from deeptutor.learning import assessment
from deeptutor.learning.models import (
    KnowledgePoint,
    LearningModule,
    LearningProgress,
    PendingQuestion,
)
from deeptutor.learning.notebook_recovery import reconcile_mastery_notebook
from deeptutor.learning.scheduler import SpacedRepetitionScheduler
from deeptutor.learning.service import LearningService
from deeptutor.learning.storage import LearningStore
from deeptutor.services import session
from deeptutor.services.session.sqlite_store import SQLiteSessionStore


def _stores(root):
    learning = LearningStore(root / "learning")
    sessions = SQLiteSessionStore(db_path=root / "sessions.db")
    return learning, sessions


def _seed(root):
    learning, sessions = _stores(root)
    asyncio.run(sessions.create_session(title="Synthetic", session_id="s"))
    learning.save(
        LearningProgress(
            book_id="p",
            modules=[
                LearningModule(
                    id="m",
                    name="Synthetic",
                    order=0,
                    knowledge_points=[
                        KnowledgePoint(id="kp", name="Value", type="memory", module_id="m"),
                        KnowledgePoint(id="concept", name="Concept", type="concept", module_id="m"),
                    ],
                )
            ],
            knowledge_types={"kp": "memory", "concept": "concept"},
        )
    )
    return learning, sessions


def _grade(learning, question_id="q", answer="wrong", assisted=False):
    service = LearningService(learning)
    service.register_question(
        "p",
        PendingQuestion(
            question_id=question_id,
            knowledge_point_id="kp",
            module_id="m",
            prompt="Name the synthetic value",
            expected_answer="alpha",
            assistance_used=assisted,
        ),
        session_id="s",
        turn_id="t",
    )
    return service.grade_interaction(
        "p",
        question_id=question_id,
        answer=answer,
        scheduler=SpacedRepetitionScheduler(),
        session_id="s",
        turn_id="t",
    )


def _worker(root, phase):
    """Exit between the source commit and delivery; never instantiate a provider."""
    import deeptutor.services.llm as llm

    calls = []

    def forbidden(*args, **kwargs):
        calls.append(1)
        raise AssertionError("Model calls are forbidden in recovery")

    llm.get_llm_client = forbidden
    if phase == "write":
        learning, sessions = _seed(root)
        _grade(learning, assisted=True)
    else:
        learning, sessions = _stores(root)
    session.get_sqlite_session_store = lambda: sessions
    if phase.startswith("repair-"):
        LearningService(learning).repair_question(
            "p",
            "q",
            action=phase.removeprefix("repair-"),
            expected_answer="wrong",
            reason="Synthetic key correction",
            scheduler=SpacedRepetitionScheduler(),
            session_id="s",
            turn_id="repair-turn",
        )
    if phase == "recover":
        outcome = asyncio.run(reconcile_mastery_notebook(learning_store=learning))
    else:
        # Reproduce a destination failure after the learning commit.
        async def interrupted(*args, **kwargs):
            raise OSError("Synthetic Notebook interruption")

        assessment.record_assessment = interrupted
        outcome = asyncio.run(reconcile_mastery_notebook(learning_store=learning))
    progress = learning.load("p")
    attempts = asyncio.run(sessions.list_assessment_attempts("s"))
    card = asyncio.run(sessions.find_notebook_entry("s", "q", turn_id="t"))
    print(
        json.dumps(
            dict(
                outcome=outcome,
                pending=len(learning.pending_notebook_assessments()),
                attempts=attempts,
                card=card,
                progress=progress.model_dump(mode="json"),
                provider_calls=len(calls),
            )
        )
    )


def _process(root, phase):
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), str(root), phase],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("action", ["correct", "void"])
def test_process_exit_after_answer_and_repair_recovers(tmp_path, action):
    written = _process(tmp_path, "write")
    assert written["pending"] == 1 and written["card"] is None
    first = _process(tmp_path, "recover")
    assert first["outcome"] == [1, 0]
    assert first["card"]["user_answer"] == "wrong"
    assert first["card"]["hints_used"] == 1
    interrupted = _process(tmp_path, f"repair-{action}")
    assert interrupted["pending"] == 1
    repaired = _process(tmp_path, "recover")
    again = _process(tmp_path, "recover")
    assert repaired["outcome"] == [1, 0] and again["outcome"] == [0, 0]
    assert len(repaired["attempts"]) == len(again["attempts"]) == 2
    assert repaired["attempts"][0]["result"] == "incorrect"
    assert repaired["attempts"][1]["correction_reason"] == "Synthetic key correction"
    assert repaired["attempts"][1]["previous_result"]["is_correct"] is False
    assert repaired["card"]["result"] == ("correct" if action == "correct" else "voided")
    assert repaired["card"]["hints_used"] == 1
    assert repaired["progress"] == again["progress"] == interrupted["progress"]
    assert all(
        item["provider_calls"] == 0 for item in (written, first, interrupted, repaired, again)
    )


def test_ack_failure_concurrent_recovery_and_other_question_preserved(tmp_path, monkeypatch):
    learning, sessions = _seed(tmp_path)
    monkeypatch.setattr(
        session, "get_sqlite_session_store", lambda: SQLiteSessionStore(db_path=sessions.db_path)
    )
    _grade(learning)
    _grade(learning, "keep", "alpha")
    before = learning.load("p").model_dump(mode="json")
    real_ack = learning.mark_notebook_assessment_applied

    def interrupted(event_id):
        raise OSError("Synthetic acknowledgement failure after destination commit")

    monkeypatch.setattr(learning, "mark_notebook_assessment_applied", interrupted)
    assert asyncio.run(reconcile_mastery_notebook(learning_store=learning)) == (0, 2)
    assert len(asyncio.run(sessions.list_assessment_attempts("s"))) == 2
    monkeypatch.setattr(learning, "mark_notebook_assessment_applied", real_ack)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(
                lambda _: asyncio.run(
                    reconcile_mastery_notebook(learning_store=LearningStore(learning._root))
                ),
                range(8),
            )
        )
    assert all(failed == 0 for _, failed in results)
    assert learning.pending_notebook_assessments() == []
    assert len(asyncio.run(sessions.list_assessment_attempts("s"))) == 2
    assert learning.load("p").model_dump(mode="json") == before
    assert (
        asyncio.run(sessions.find_notebook_entry("s", "keep", turn_id="t"))["result"] == "correct"
    )


def test_reverse_delivery_with_equal_clock_cannot_overwrite_correction(tmp_path, monkeypatch):
    learning, sessions = _seed(tmp_path)
    monkeypatch.setattr(session, "get_sqlite_session_store", lambda: sessions)
    monkeypatch.setattr("deeptutor.learning.storage.time.time", lambda: 123456.0)
    _grade(learning)
    LearningService(learning).repair_question(
        "p",
        "q",
        action="correct",
        expected_answer="wrong",
        reason="Correction",
        scheduler=SpacedRepetitionScheduler(),
        session_id="s",
        turn_id="repair",
    )
    pending = learning.pending_notebook_assessments()
    assert len(pending) == 2
    for _, snapshot in reversed(pending):
        asyncio.run(
            assessment.record_assessment(assessment.AssessmentRecord.model_validate(snapshot))
        )
    assert asyncio.run(reconcile_mastery_notebook(learning_store=learning)) == (2, 0)
    assert asyncio.run(sessions.find_notebook_entry("s", "q", turn_id="t"))["result"] == "correct"
    assert len(asyncio.run(sessions.list_assessment_attempts("s"))) == 2


def test_outbox_and_attempt_rollback_together(tmp_path, monkeypatch):
    learning, _ = _seed(tmp_path)
    from deeptutor.learning import notebook_recovery

    real_capture = notebook_recovery.capture_notebook_assessment

    def interrupted(tx, event_type, *args, **kwargs):
        if event_type == "attempt.recorded":
            raise OSError("Synthetic source commit failure")
        return real_capture(tx, event_type, *args, **kwargs)

    monkeypatch.setattr(notebook_recovery, "capture_notebook_assessment", interrupted)
    with pytest.raises(OSError):
        _grade(learning)
    assert learning.pending_notebook_assessments() == []
    assert learning.load("p").learning_evidence == []
    assert learning.get_interaction("p", "q").user_answer == ""


def test_old_uncaptured_history_stays_explicitly_unrecoverable(tmp_path, monkeypatch):
    learning, sessions = _seed(tmp_path)
    from deeptutor.learning import notebook_recovery

    # Reproduce the former best-effort boundary: learning committed with
    # no durable delivery intent. Never fabricate a historical snapshot.
    monkeypatch.setattr(notebook_recovery, "capture_notebook_assessment", lambda *a, **k: None)
    _grade(learning)
    reopened = LearningStore(learning._root)
    assert len(reopened.load("p").learning_evidence) == 1
    assert asyncio.run(reconcile_mastery_notebook(learning_store=reopened)) == (0, 0)
    assert asyncio.run(sessions.find_notebook_entry("s", "q", turn_id="t")) is None


def test_group_and_qualitative_snapshots_and_status_read_recovery(tmp_path, monkeypatch):
    learning, sessions = _seed(tmp_path)
    monkeypatch.setattr(session, "get_sqlite_session_store", lambda: sessions)
    from deeptutor.capabilities.mastery import tools
    from tests.capabilities.test_mastery_question_groups import group

    # Both synthetic leaves deliberately share one objective; each must
    # produce its own card, while the parent earns no extra evidence.
    questions = group()
    for leaf in questions.questions:
        leaf.knowledge_point_id = "kp"
        leaf.prompt = f"Name the synthetic value for {leaf.question_id}"
    questions.knowledge_point_id = "kp"
    service = LearningService(learning)
    service.register_question("p", questions, session_id="s", turn_id="t")
    service.grade_interaction(
        "p",
        question_id="g",
        answer="",
        answers={"q1": "alpha", "q2": "wrong"},
        session_id="s",
        turn_id="t",
    )
    service.record_qualitative_for_path(
        "p",
        "concept",
        passed=False,
        evidence="Synthetic explanation",
        scheduler=SpacedRepetitionScheduler(),
        session_id="s",
        turn_id="qual",
        hints_used=1,
    )
    pending = learning.pending_notebook_assessments()
    assert {snapshot["question_id"] for _, snapshot in pending} == {"q1", "q2", "qual:concept"}
    monkeypatch.setattr(tools, "_new_service", lambda: service)
    before = learning.load("p").model_dump(mode="json")
    result = asyncio.run(tools.MasteryStatusTool().execute(_mastery_path_id="p"))
    assert result.success
    assert learning.pending_notebook_assessments() == []
    assert learning.load("p").model_dump(mode="json") == before
    attempts = asyncio.run(sessions.list_assessment_attempts("s"))
    assert len(attempts) == 3
    assert next(row for row in attempts if row["question_id"] == "qual:concept")["hints_used"] == 1


def test_pending_snapshot_survives_selected_storage_backup(tmp_path, monkeypatch):
    from scripts import learning_backup as backup

    user = tmp_path / "user"
    learning = LearningStore(user / "workspace/learning/mastery")
    sessions = SQLiteSessionStore(db_path=user / "chat_history.db")
    asyncio.run(sessions.create_session(title="Synthetic", session_id="s"))
    learning.save(
        LearningProgress(
            book_id="p",
            modules=[
                LearningModule(
                    id="m",
                    name="Synthetic",
                    order=0,
                    knowledge_points=[
                        KnowledgePoint(id="kp", name="Value", type="memory", module_id="m")
                    ],
                )
            ],
            knowledge_types={"kp": "memory"},
        )
    )
    _grade(learning)
    pending = learning.pending_notebook_assessments()
    before = learning.load("p").model_dump(mode="json")
    snapshot = backup.create_backup(user, tmp_path / "backup", quiesced=True)
    restored = backup.restore_backup(snapshot, tmp_path / "restored")
    reopened = LearningStore(restored / "workspace/learning/mastery")
    destination = SQLiteSessionStore(db_path=restored / "chat_history.db")
    monkeypatch.setattr(session, "get_sqlite_session_store", lambda: destination)
    assert reopened.pending_notebook_assessments() == pending
    assert asyncio.run(reconcile_mastery_notebook(learning_store=reopened)) == (1, 0)
    assert reopened.load("p").model_dump(mode="json") == before
    assert len(asyncio.run(destination.list_assessment_attempts("s"))) == 1
    # The original storage remains pending and untouched by restore/delivery.
    assert learning.pending_notebook_assessments() == pending


def test_late_old_snapshot_cannot_replace_a_newer_answer(tmp_path, monkeypatch):
    learning, sessions = _seed(tmp_path)
    monkeypatch.setattr(session, "get_sqlite_session_store", lambda: sessions)
    _grade(learning)
    _, snapshot = learning.pending_notebook_assessments()[0]
    old = assessment.AssessmentRecord.model_validate(snapshot)
    newer = old.model_copy(
        update={
            "attempt_id": "synthetic-newer-answer",
            "user_answer": "A newer answer",
            "result": "correct",
            "is_correct": True,
            "projection_sequence": old.projection_sequence + 1,
            "created_at": old.created_at - 3600,
        }
    )
    asyncio.run(assessment.record_assessment(newer))
    assert asyncio.run(reconcile_mastery_notebook(learning_store=learning)) == (1, 0)
    card = asyncio.run(sessions.find_notebook_entry("s", "q", turn_id="t"))
    assert card["user_answer"] == "A newer answer" and card["result"] == "correct"


if __name__ == "__main__":
    _worker(Path(sys.argv[1]), sys.argv[2])
