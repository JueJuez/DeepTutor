"""Process and concurrency contracts using synthetic answers and real SQLite."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

import pytest

from deeptutor.learning import assessment
from deeptutor.learning.assessment import AssessmentRecord, record_assessment
from deeptutor.learning.models import KnowledgePoint, LearningModule, LearningProgress
from deeptutor.learning.storage import LearningStore
from deeptutor.services import session
from deeptutor.services.session.sqlite_store import SQLiteSessionStore


def _record(**changes) -> AssessmentRecord:
    values = dict(
        session_id="synthetic",
        turn_id="turn",
        question_id="question",
        question="Explain a synthetic concept",
        source="immersive_reading",
        user_answer="自制作答",
        result="correct",
        material_id="synthetic-book",
        material_revision=3,
        section_id="2",
        hints_used=1,
        mastery_path_id="path",
        knowledge_point_id="kp",
        attempt_id="event",
        created_at=1_000_000.0,
    )
    return AssessmentRecord(**(values | changes))


def _process(root: Path, phase: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), str(root), phase],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _worker(root: Path, phase: str) -> None:
    """Separate interpreter: interrupt after the event commit, then recover."""
    sessions = SQLiteSessionStore(db_path=root / "sessions.db")
    learning = LearningStore(root=root / "learning")
    session.get_sqlite_session_store = lambda: sessions
    assessment._get_learning_store = lambda: learning
    if phase == "write":
        asyncio.run(sessions.create_session(title="Synthetic", session_id="synthetic"))
        learning.save(
            LearningProgress(
                book_id="path",
                modules=[
                    LearningModule(
                        id="module",
                        name="Synthetic",
                        order=0,
                        knowledge_points=[
                            KnowledgePoint(
                                id="kp", name="Concept", type="concept", module_id="module"
                            )
                        ],
                    )
                ],
            )
        )

        def interrupted(*args, **kwargs):
            raise OSError("synthetic second-database failure")

        assessment._apply_linked_retention = interrupted
        with pytest.raises(assessment.RecordAssessmentError):
            asyncio.run(record_assessment(_record()))
        saved = asyncio.run(sessions.get_assessment_attempt("event"))
        assert learning.load("path").learning_evidence == []
        print(json.dumps(saved, ensure_ascii=False))
    else:
        first = asyncio.run(assessment.reconcile_linked_assessments())
        second = asyncio.run(assessment.reconcile_linked_assessments())
        outcome = asyncio.run(record_assessment(_record()))
        progress = learning.load("path")
        evidence = progress.learning_evidence
        state = progress.repetition_states["kp"]
        card = asyncio.run(sessions.find_notebook_entry("synthetic", "question", turn_id="turn"))
        print(
            json.dumps(
                dict(
                    first=first,
                    second=second,
                    recorded=outcome.attempt_recorded,
                    evidence=[item.model_dump(mode="json") for item in evidence],
                    reviews=state.review_count,
                    due=state.next_review_at,
                    card=card,
                ),
                ensure_ascii=False,
            )
        )


def test_interrupted_cross_database_write_recovers_in_new_process(tmp_path: Path) -> None:
    written = _process(tmp_path, "write")
    assert written["user_answer"] == "自制作答"
    assert (written["material_revision"], written["section_id"], written["hints_used"]) == (
        3,
        "2",
        1,
    )
    recovered = _process(tmp_path, "recover")
    reopened = _process(tmp_path, "recover")
    assert recovered["first"] == [1, 0]
    assert recovered["second"] == reopened["first"] == [0, 0]
    assert recovered["recorded"] is False
    assert recovered["evidence"] == reopened["evidence"]
    assert len(recovered["evidence"]) == recovered["reviews"] == 1
    assert recovered["due"] == reopened["due"]
    assert recovered["evidence"][0]["hints_used"] == 1
    assert recovered["card"]["hints_used"] == 1
    assert recovered["card"]["user_answer"] == "自制作答"


def test_concurrent_retries_and_same_time_new_answers(tmp_path: Path, monkeypatch) -> None:
    sessions = SQLiteSessionStore(db_path=tmp_path / "sessions.db")
    asyncio.run(sessions.create_session(title="Synthetic", session_id="synthetic"))
    # Independent store instances model concurrent processes. A single store's
    # asyncio.Lock belongs to one event loop, never to multiple thread loops.
    monkeypatch.setattr(
        session, "get_sqlite_session_store", lambda: SQLiteSessionStore(db_path=sessions.db_path)
    )
    record = _record(source="mastery_path", mastery_path_id="", knowledge_point_id="")
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(lambda _: asyncio.run(record_assessment(record)), range(12)))
    assert sum(outcome.attempt_recorded for outcome in outcomes) == 1
    new_records = [
        record.model_copy(update={"attempt_id": f"new-{i}", "user_answer": str(i)})
        for i in range(8)
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda item: asyncio.run(record_assessment(item)), new_records))
    attempts = asyncio.run(sessions.list_assessment_attempts("synthetic"))
    assert len(attempts) == 9
    asyncio.run(record_assessment(record))
    card = asyncio.run(sessions.find_notebook_entry("synthetic", "question", turn_id="turn"))
    assert card["user_answer"] == attempts[-1]["user_answer"]
    reopened = SQLiteSessionStore(db_path=sessions.db_path)
    persisted = asyncio.run(reopened.get_assessment_attempt("event"))
    assert persisted["material_revision"] == 3
    assert (
        AssessmentRecord.model_validate(
            {key: value for key, value in persisted.items() if key != "material_revision"}
        ).material_revision
        == 0
    )


def test_legacy_unknown_revision_is_not_replaced_on_reopen(tmp_path, monkeypatch) -> None:
    sessions = SQLiteSessionStore(db_path=tmp_path / "legacy.db")
    asyncio.run(sessions.create_session(title="Synthetic", session_id="synthetic"))
    record = _record(source="mastery_path", mastery_path_id="", knowledge_point_id="")
    legacy = record.model_dump(mode="json")
    legacy.pop("material_revision")
    legacy["occurred_at"] = record.created_at
    asyncio.run(
        sessions.record_assessment("synthetic", assessment.to_notebook_item(record, []), legacy)
    )
    reopened = SQLiteSessionStore(db_path=sessions.db_path)
    saved = asyncio.run(reopened.get_assessment_attempt("event"))
    assert "material_revision" not in saved
    unknown = AssessmentRecord.model_validate(saved)
    assert unknown.material_revision == 0
    monkeypatch.setattr(session, "get_sqlite_session_store", lambda: reopened)
    # A retry carrying the current material version must not retrofit the
    # immutable historical event's unknown provenance.
    asyncio.run(record_assessment(unknown.model_copy(update={"material_revision": 99})))
    assert "material_revision" not in asyncio.run(reopened.get_assessment_attempt("event"))


if __name__ == "__main__":
    _worker(Path(sys.argv[1]), sys.argv[2])
