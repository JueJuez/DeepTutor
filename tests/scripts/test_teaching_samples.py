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


def argparse_namespace(root: Path, sample: str | None = None, allow_holdout: bool = False):
    import argparse

    return argparse.Namespace(root=root, sample=sample, allow_holdout=allow_holdout)
