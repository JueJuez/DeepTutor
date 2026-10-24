"""Synthetic learning recovery with source revisions and actual SQLite files."""

from __future__ import annotations

import asyncio
from contextlib import closing
import json
from pathlib import Path
import sqlite3

import pymupdf
import pytest

from deeptutor.learning import assessment
from deeptutor.learning.assessment import AssessmentRecord, record_assessment
from deeptutor.learning.models import KnowledgePoint, LearningModule, LearningProgress
from deeptutor.learning.storage import LearningStore
from deeptutor.reading.store import ReadingStore
from deeptutor.services import session
from deeptutor.services.session.sqlite_store import SQLiteSessionStore
from scripts import learning_backup as backup


def test_backup_restores_answer_revision_and_schedule_without_reapplying(tmp_path, monkeypatch):
    user = tmp_path / "user"
    sessions = SQLiteSessionStore(db_path=user / "chat_history.db")
    learning = LearningStore(root=user / "workspace/learning/mastery")
    reading = ReadingStore(root=user / "workspace/reading")
    source = tmp_path / "synthetic.pdf"
    with pymupdf.open() as document:
        document.new_page().insert_text(
            (72, 72), "A synthetic passage for a verifiable recovery test."
        )
        document.save(source)
    material = reading.ingest(source)
    revision = material.revision
    text = reading.unit_text(material.material_id, 1)
    reading.refresh_document(material.material_id)
    learning.save(
        LearningProgress(
            book_id="path",
            modules=[
                LearningModule(
                    id="m",
                    name="Synthetic",
                    order=0,
                    knowledge_points=[
                        KnowledgePoint(id="kp", name="Concept", type="concept", module_id="m")
                    ],
                )
            ],
        )
    )
    monkeypatch.setattr(session, "get_sqlite_session_store", lambda: sessions)
    monkeypatch.setattr(assessment, "_get_learning_store", lambda: learning)
    asyncio.run(sessions.create_session(title="Synthetic", session_id="s"))
    record = AssessmentRecord(
        session_id="s",
        turn_id="t",
        question_id="q",
        question="Explain the passage",
        user_answer="自制回答",
        result="correct",
        source="immersive_reading",
        material_id=material.material_id,
        material_revision=revision,
        section_id="1",
        mastery_path_id="path",
        knowledge_point_id="kp",
        hints_used=1,
        attempt_id="one",
    )
    asyncio.run(record_assessment(record))
    before = learning.load("path")
    settings = user / "settings/model_catalog.json"
    settings.parent.mkdir()
    settings.write_text(
        '{"api_key":"SYNTHETIC_SECRET"}',  # pragma: allowlist secret
        encoding="utf-8",
    )
    snapshot = backup.create_backup(user, tmp_path / "backup", quiesced=True)
    manifest = backup.verify_backup(snapshot)
    assert all(not name.startswith("settings/") for name in manifest["files"])
    assert any("revisions/" in name for name in manifest["files"])
    restored = backup.restore_backup(snapshot, tmp_path / "restored")
    assert not (restored / "settings").exists()
    restored_sessions = SQLiteSessionStore(db_path=restored / "chat_history.db")
    restored_learning = LearningStore(root=restored / "workspace/learning/mastery")
    restored_reading = ReadingStore(root=restored / "workspace/reading")
    assert restored_reading.revision_unit_text(material.material_id, revision, 1) == text
    attempt = asyncio.run(restored_sessions.get_assessment_attempt("one"))
    assert (attempt["user_answer"], attempt["material_revision"], attempt["section_id"]) == (
        "自制回答",
        revision,
        "1",
    )
    monkeypatch.setattr(session, "get_sqlite_session_store", lambda: restored_sessions)
    monkeypatch.setattr(assessment, "_get_learning_store", lambda: restored_learning)
    assert asyncio.run(assessment.reconcile_linked_assessments()) == (0, 0)
    assert asyncio.run(record_assessment(record)).attempt_recorded is False
    after = restored_learning.load("path")
    assert after.learning_evidence == before.learning_evidence
    assert after.repetition_states == before.repetition_states
    assert after.review_queue == before.review_queue
    assert len(asyncio.run(restored_sessions.list_assessment_attempts("s"))) == 1
    assert asyncio.run(restored_sessions.list_notebook_entries())["total"] == 1


def _minimal_user(tmp_path: Path) -> Path:
    user = tmp_path / "user"
    SQLiteSessionStore(db_path=user / "chat_history.db")
    return user


def test_sqlite_backup_includes_committed_wal_pages(tmp_path):
    user = _minimal_user(tmp_path)
    with closing(sqlite3.connect(user / "chat_history.db")) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("CREATE TABLE synthetic_wal (answer TEXT)")
        writer.execute("INSERT INTO synthetic_wal VALUES ('saved only in WAL')")
        writer.commit()
        assert (user / "chat_history.db-wal").exists()
        snapshot = backup.create_backup(user, tmp_path / "backup", quiesced=True)
        assert "chat_history.db-wal" not in backup.verify_backup(snapshot)["files"]
        restored = backup.restore_backup(snapshot, tmp_path / "restored")
    with closing(sqlite3.connect(restored / "chat_history.db")) as conn:
        assert conn.execute("SELECT answer FROM synthetic_wal").fetchone() == ("saved only in WAL",)


@pytest.mark.parametrize("damage", ["changed", "missing", "extra", "traversal", "schema"])
def test_damaged_backups_are_rejected_without_a_successful_restore(tmp_path, damage):
    user = _minimal_user(tmp_path)
    snapshot = backup.create_backup(user, tmp_path / "backup", quiesced=True)
    manifest_path = snapshot / backup.MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    database = snapshot / "chat_history.db"
    if damage == "changed":
        database.write_bytes(database.read_bytes() + b"damage")
    elif damage == "missing":
        database.unlink()
    elif damage == "extra":
        (snapshot / "unexpected.txt").write_text("extra", encoding="utf-8")
    elif damage == "schema":
        manifest["files"]["chat_history.db"]["sqlite"]["user_version"] = 100
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    else:
        manifest["files"]["../escaped"] = {"size": 1, "sha256": "x"}
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError):
        backup.restore_backup(snapshot, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()


def test_writing_backup_aborts_without_publishing_when_source_changes(tmp_path, monkeypatch):
    user = _minimal_user(tmp_path)
    copy = backup._sqlite_copy

    def changed(original, destination):
        result = copy(original, destination)
        with closing(sqlite3.connect(original)) as conn:
            conn.execute("CREATE TABLE concurrent_write (id INTEGER)")
            conn.commit()
        return result

    monkeypatch.setattr(backup, "_sqlite_copy", changed)
    with pytest.raises(ValueError, match="changed during backup"):
        backup.create_backup(user, tmp_path / "backup", quiesced=True)
    assert not (tmp_path / "backup").exists()


def test_backup_requires_stopped_writers_and_never_overwrites(tmp_path):
    user = _minimal_user(tmp_path)
    with pytest.raises(ValueError, match="Stop all writers"):
        backup.create_backup(user, tmp_path / "backup")
    snapshot = backup.create_backup(user, tmp_path / "backup", quiesced=True)
    with pytest.raises(FileExistsError):
        backup.create_backup(user, snapshot, quiesced=True)
    with pytest.raises(FileExistsError):
        backup.restore_backup(snapshot, user)
    with pytest.raises(ValueError):
        backup.restore_backup(snapshot, snapshot / "nested")


def test_interrupted_copy_never_publishes_a_completed_backup(tmp_path, monkeypatch):
    user = _minimal_user(tmp_path)

    def interrupted(*args):
        raise OSError("synthetic disk interruption")

    monkeypatch.setattr(backup, "_sqlite_copy", interrupted)
    with pytest.raises(OSError, match="disk interruption"):
        backup.create_backup(user, tmp_path / "backup", quiesced=True)
    assert not (tmp_path / "backup").exists()
    partials = list(tmp_path.glob("backup.partial-*"))
    assert len(partials) == 1
    with pytest.raises(ValueError, match="Missing snapshot"):
        backup.verify_backup(partials[0])
