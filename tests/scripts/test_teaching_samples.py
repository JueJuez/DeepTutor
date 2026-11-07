"""E1 sample bank: mechanical checks, replay isolation and report aggregation.

Offline only — the provider grading entry is faked; no model is called.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deeptutor.learning import semantic_assessment as semantic
from scripts import teaching_samples as ts


def _valid_sample(sample_id: str = "S1", set_name: str = "dev_regression") -> dict:
    return {
        "schema_version": ts.SCHEMA_VERSION,
        "sample_id": sample_id,
        "set": set_name,
        "situation": "five_class_answers",
        "source": {"material_id": "m1", "revision": 1, "locators": [1]},
        "objective": "Explain the objective",
        "question": {
            "question_id": "q1",
            "prompt": "Explain X from the source.",
            "expected_answer": "X is Y.",
            "source_evidence_kind": "reading",
        },
        "grounding": {"citations_note": "verbatim"},
        "answers": [
            {
                "class": "correct",
                "answer": "X is Y.",
                "verdict_result": "correct",
                "confidence": 0.97,
                "feedback_head": "Matches the source.",
                "expectation": "correct",
                "matches_expectation": True,
            }
        ],
        "assistance": {"hints_used": 0},
        "teaching_state": {"source_grounded": True},
        "provenance": {"path_id": "p1", "result_file": "data/x-result.json"},
        "audit": {"auditor": "agent", "disputes": []},
    }


def test_mechanical_check_passes_a_wellformed_sample():
    checks = ts.mechanical_check(_valid_sample())
    assert all(c["ok"] for c in checks), checks


@pytest.mark.parametrize(
    "mutate,broken",
    [
        (lambda s: s.pop("grounding"), "required_fields"),
        (lambda s: s.__setitem__("schema_version", 99), "schema_version"),
        (lambda s: s["question"].__setitem__("verdict", {"result": "correct"}), "answer_isolation"),
        (
            lambda s: s["answers"].__setitem__(0, {"class": "correct"}),
            "answers_wellformed",
        ),
        (lambda s: s.__setitem__("set", "everything"), "set_membership"),
    ],
)
def test_mechanical_check_catches_structural_defects(mutate, broken):
    sample = _valid_sample()
    mutate(sample)
    checks = ts.mechanical_check(sample)
    failed = [c["check"] for c in checks if not c["ok"]]
    assert failed == [broken], checks


def test_replay_refuses_holdout_without_explicit_flag(tmp_path: Path, monkeypatch):
    root = tmp_path / "bank"
    root.mkdir()
    (root / "samples.json").write_text(
        json.dumps({"samples": [_valid_sample("S2", "holdout")]}), encoding="utf-8"
    )
    with pytest.raises(SystemExit, match="holdout"):
        ts.cmd_replay(argparse_namespace(root=root, sample="S2", allow_holdout=False))


def test_replay_appends_timestamped_records_and_keeps_earlier_ones(tmp_path: Path, monkeypatch):
    root = tmp_path / "bank"
    root.mkdir()
    (root / "samples.json").write_text(json.dumps({"samples": [_valid_sample()]}), encoding="utf-8")

    class FakeVerdict:
        def __init__(self, result: str) -> None:
            self.result = result

        def model_dump(self) -> dict:
            return {"result": self.result, "confidence": 0.9, "feedback": "f"}

    results = iter(["correct", "partial"])
    captured: list[list[dict]] = []

    async def fake_judge(config, items):
        captured.append(items)
        return {"q1": FakeVerdict(next(results))}

    monkeypatch.setattr(semantic, "judge_answers", fake_judge)
    monkeypatch.setattr(
        semantic,
        "question_contract",
        lambda q: {"question_id": "q1", "prompt": q.prompt, "expected_answer": q.expected_answer},
    )
    from types import SimpleNamespace

    from deeptutor.learning import storage as learning_storage

    fake_question = SimpleNamespace(
        question_id="q1",
        prompt="Explain X from the source.",
        expected_answer="X is Y.",
        source_evidence={"kind": "reading", "sources": []},
    )
    fake_store = SimpleNamespace(
        load=lambda path_id: SimpleNamespace(pending_question=fake_question)
    )
    monkeypatch.setattr(learning_storage, "LearningStore", lambda: fake_store)
    args = argparse_namespace(root=root, sample="S1", allow_holdout=False)
    ts.cmd_replay(args)
    ts.cmd_replay(args)

    replays = sorted((root / "replays").glob("S1-*.json"))
    assert len(replays) == 2, "each replay appends a new record"
    first = json.loads(replays[0].read_text(encoding="utf-8"))
    second = json.loads(replays[1].read_text(encoding="utf-8"))
    assert first["rows"][0]["differs"] is False
    assert second["rows"][0]["differs"] is True  # version change stays visible
    assert len(captured) == 2
    # The grading payload carries the question contract, the answer and the
    # source evidence — never any verdict fields (isolation).
    sent = captured[0][0]
    assert {"question_id", "prompt", "expected_answer", "answer", "source_evidence"} <= set(sent)
    assert not {"verdict", "confidence", "feedback"} & set(sent)


def test_report_aggregates_failures_disputes_and_replay_diffs(tmp_path: Path):
    root = tmp_path / "bank"
    (root / "replays").mkdir(parents=True)
    sample = _valid_sample()
    sample["answers"].append(
        {
            "class": "equivalent",
            "answer": "Y is X.",
            "verdict_result": "partial",
            "confidence": 0.8,
            "feedback_head": "",
            "expectation": "correct",
            "matches_expectation": False,
        }
    )
    (root / "samples.json").write_text(json.dumps({"samples": [sample]}), encoding="utf-8")
    (root / "replays" / "S1-123.json").write_text(json.dumps({"diff_count": 1}), encoding="utf-8")
    ts.cmd_report(argparse_namespace(root=root))
    reports = sorted(root.glob("report-*.json"))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    entry = report["samples"][0]
    assert entry["mechanical_failures"] == []
    assert entry["semantic_disputes"] == ["equivalent"]
    assert entry["latest_replay_diffs"] == 1
    assert "five_class_answers" in report["situation_coverage"]
    uncovered = report["uncovered_situations"]
    assert "step_error" in uncovered and "missing_prerequisite" in uncovered


def _question_namespace(question_id: str):
    from types import SimpleNamespace

    return SimpleNamespace(
        question_id=question_id,
        prompt="Explain X from the source.",
        expected_answer="X is Y.",
        question_type="short",
        knowledge_point_id="kp1",
        source_evidence={
            "kind": "reading",
            "sources": [
                {
                    "reading_reference": {
                        "material_id": "m1",
                        "revision": 1,
                        "locators": [1],
                    }
                }
            ],
        },
    )


def test_resolve_question_falls_back_to_the_interaction_store(monkeypatch):
    """A path holds many questions over its life: the sample's own id must win
    over whatever card is merely pending now (a later registration can replace
    the pending slot on a shared path)."""
    from types import SimpleNamespace

    from deeptutor.learning import storage as learning_storage

    pending = SimpleNamespace(question_id="q-pending")
    stored = SimpleNamespace(question_id="q-stored")
    fake_store = SimpleNamespace(
        load=lambda path_id: SimpleNamespace(pending_question=pending),
        get_interaction=lambda path_id, qid: (
            SimpleNamespace(question=stored) if qid == "q-stored" else None
        ),
    )
    monkeypatch.setattr(learning_storage, "LearningStore", lambda: fake_store)

    assert ts._resolve_question("p1", "q-pending") is pending
    assert ts._resolve_question("p1", "q-stored") is stored
    with pytest.raises(SystemExit, match="neither pending nor stored"):
        ts._resolve_question("p1", "q-missing")

    gone = SimpleNamespace(load=lambda path_id: None, get_interaction=lambda *a: None)
    monkeypatch.setattr(learning_storage, "LearningStore", lambda: gone)
    with pytest.raises(SystemExit, match="no longer exists"):
        ts._resolve_question("gone", "q1")


def test_attach_verdicts_question_id_filter_keeps_same_path_samples_separate(
    tmp_path: Path, monkeypatch
):
    """The transfer-probe verdicts are keyed by question_id: they must attach
    to their own sample only, never shadow same-path samples keyed by
    path_id in the older audit files."""
    import json as jsonlib

    monkeypatch.chdir(tmp_path)
    bank_dir = tmp_path / "data" / "l4-transfer-probe"
    bank_dir.mkdir(parents=True)
    (bank_dir / "verdicts-bank.json").write_text(
        jsonlib.dumps(
            {
                "q-new": {
                    "question_id": "q-new",
                    "path_id": "p1",
                    "classes": [
                        {
                            "class": "correct",
                            "answer": "X is Y.",
                            "verdict": {"result": "correct", "confidence": 1.0, "feedback": "f"},
                            "expectation": "correct",
                            "matches_expectation": True,
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    result_file = tmp_path / "data" / "result.json"
    result_file.write_text(jsonlib.dumps({"case": "c1", "path_id": "p1"}), encoding="utf-8")

    def _sample(qid: str, sid: str) -> dict:
        sample = _valid_sample(sid)
        sample["question"]["question_id"] = qid
        sample["provenance"]["result_file"] = str(result_file)
        return sample

    old = ts._attach_verdicts(_sample("q-old", "S1"))
    assert old["audit"]["auditor"] == "agent", (
        "a question-keyed entry must not attach to another question"
    )
    assert [a["confidence"] for a in old["answers"]] == [0.97], (
        "pre-existing answers stay untouched (the bank entry carries 1.0)"
    )
    new = ts._attach_verdicts(_sample("q-new", "S6"))
    assert [a["class"] for a in new["answers"]] == ["correct"]
    assert new["audit"]["auditor"] == "l4_transfer_probe"


def test_add_appends_one_sample_without_touching_existing(tmp_path: Path, monkeypatch):
    from types import SimpleNamespace

    from deeptutor.learning import storage as learning_storage
    from deeptutor.reading import store as reading_store

    monkeypatch.chdir(tmp_path)
    root = tmp_path / "bank"
    root.mkdir()
    existing = _valid_sample("S1")
    (root / "samples.json").write_text(json.dumps({"samples": [existing]}), encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "samples": [
                    {"id": "S1"},
                    {
                        "id": "S6",
                        "kind": "positive",
                        "class": "概念",
                        "situation": "transfer_failure",
                        "objective": "Explain X",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    result_file = tmp_path / "data" / "l4-result.json"
    result_file.parent.mkdir(parents=True)
    result_file.write_text(
        json.dumps(
            {
                "case": "l4-transfer",
                "path_id": "p1",
                "pending_question": {"question_id": "q6"},
            }
        ),
        encoding="utf-8",
    )
    verdicts_dir = tmp_path / "data" / "l4-transfer-probe"
    verdicts_dir.mkdir(parents=True)
    (verdicts_dir / "verdicts-bank.json").write_text(
        json.dumps(
            {
                "q6": {
                    "question_id": "q6",
                    "path_id": "p1",
                    "classes": [
                        {
                            "class": "correct",
                            "answer": "X is Y.",
                            "verdict": {"result": "correct", "confidence": 1.0, "feedback": "f"},
                            "expectation": "correct",
                            "matches_expectation": True,
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    stored_question = _question_namespace("q6")
    fake_store = SimpleNamespace(
        load=lambda path_id: SimpleNamespace(
            modules=[],
            lesson_evidence={},
            source_grounded=False,
            pending_question=None,
        ),
        get_interaction=lambda path_id, qid: SimpleNamespace(question=stored_question),
    )
    monkeypatch.setattr(learning_storage, "LearningStore", lambda: fake_store)
    monkeypatch.setattr(
        reading_store.ReadingStore,
        "unit_text",
        lambda self, material, locator: "unit text",
    )

    ts.cmd_add(
        argparse_namespace(root=root, sample_id="S6", registry=registry, result_file=result_file)
    )
    payload = json.loads((root / "samples.json").read_text(encoding="utf-8"))
    assert [s["sample_id"] for s in payload["samples"]] == ["S1", "S6"]
    assert payload["samples"][0] == existing, "existing samples stay untouched"
    added = payload["samples"][1]
    assert added["situation"] == "transfer_failure"
    assert added["question"]["question_id"] == "q6"
    assert [a["verdict_result"] for a in added["answers"]] == ["correct"]

    with pytest.raises(SystemExit, match="refusing to duplicate"):
        ts.cmd_add(
            argparse_namespace(
                root=root, sample_id="S6", registry=registry, result_file=result_file
            )
        )


def test_add_refuses_unknown_sample_id(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "bank"
    root.mkdir()
    (root / "samples.json").write_text(json.dumps({"samples": [_valid_sample()]}), encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"samples": [{"id": "S1"}]}), encoding="utf-8")
    with pytest.raises(SystemExit, match="not in the registry"):
        ts.cmd_add(
            argparse_namespace(root=root, sample_id="S9", registry=registry, result_file=None)
        )


def argparse_namespace(
    root: Path,
    sample: str | None = None,
    allow_holdout: bool = False,
    sample_id: str | None = None,
    registry: Path | None = None,
    result_file: Path | None = None,
):
    import argparse

    return argparse.Namespace(
        root=root,
        sample=sample,
        allow_holdout=allow_holdout,
        sample_id=sample_id,
        registry=str(registry) if registry else "data/semantic-samples-24/sample-registry.json",
        result_file=str(result_file) if result_file else "",
    )
