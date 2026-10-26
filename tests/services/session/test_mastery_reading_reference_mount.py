"""Mastery turns must mount the reading units the learner sends with a turn.

Non-chat turns skip the chat source-inventory path, so before the fix a
``reading_references`` payload on a mastery turn was silently dropped: the
tutor taught from parametric memory while claiming to teach the open book,
and ``source_grounded`` could never reflect real source use.
"""

from __future__ import annotations

from pathlib import Path

from deeptutor.reading.store import ReadingStore
from deeptutor.services.session._turn_runtime_shared import (
    _merge_mastery_source_mounts,
    _reading_reference_manifest,
)


def _store_with_material(tmp_path: Path) -> tuple[ReadingStore, str, int]:
    source = tmp_path / "unit.txt"
    source.write_text(
        "# 1.5.1 Gradient descent\n\nThe negative gradient is the steepest descent direction.",
        encoding="utf-8",
    )
    store = ReadingStore(tmp_path / "reading")
    manifest = store.ingest(source)
    return store, manifest.material_id, manifest.revision


def test_reading_reference_manifest_resolves_units_into_index(tmp_path, monkeypatch) -> None:
    store, material_id, revision = _store_with_material(tmp_path)
    monkeypatch.setattr("deeptutor.reading.references.ReadingStore", lambda: store)

    manifest, index = _reading_reference_manifest(
        [{"material_id": material_id, "revision": revision, "locators": [1]}]
    )

    sid = f"rd-{material_id}-r{revision}-1"
    assert sid in index
    assert "negative gradient" in index[sid]
    assert f"id={sid}" in manifest
    assert "[Reading Sources]" in manifest
    assert "read_source(id)" in manifest


def test_reading_reference_manifest_fails_closed_on_unknown_material(tmp_path: Path) -> None:
    assert _reading_reference_manifest(
        [{"material_id": "abcdef0123456789", "revision": 1, "locators": [1]}]
    ) == ("", {})
    assert _reading_reference_manifest([]) == ("", {})


def test_merge_prefers_fresh_turn_references_over_topic_materials() -> None:
    topic_manifest, topic_index = "[Topic Materials]\n- id=bk-x", {"bk-x": "topic text"}
    reading_manifest, reading_index = "[Reading Sources]\n- id=rd-y", {"rd-y": "unit text"}

    manifest, index = _merge_mastery_source_mounts(
        topic_manifest, topic_index, reading_manifest, reading_index
    )

    assert manifest == f"{topic_manifest}\n\n{reading_manifest}"
    assert index == {"bk-x": "topic text", "rd-y": "unit text"}


def test_merge_keeps_topic_state_when_no_reading_references_resolved() -> None:
    topic_manifest, topic_index = "[Topic Materials]\n- id=bk-x", {"bk-x": "topic text"}

    assert _merge_mastery_source_mounts(topic_manifest, topic_index, "", {}) == (
        topic_manifest,
        topic_index,
    )
