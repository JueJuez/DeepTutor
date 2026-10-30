"""E1 teaching-quality sample bank: build, replay and report.

Local sample format for replayable teaching-quality evidence. Real book
content and learner answers stay in the git-ignored data/ tree; only this
tooling is committed. A replay re-runs the existing provider grading entry
over one sample's recorded answers and appends a timestamped record — it
never overwrites an earlier replay, so version and failure differences stay
traceable. No new online audit chain: replay is explicit and offline.

Usage:
  python scripts/teaching_samples.py build  --root data/teaching-samples
  python scripts/teaching_samples.py replay --root data/teaching-samples --sample S1
  python scripts/teaching_samples.py report --root data/teaching-samples
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

SCHEMA_VERSION = 1

# Situations the plan requires the report to cover; samples tagged beyond
# this list still appear, the report simply marks the uncovered ones.
PLAN_SITUATIONS = [
    "five_class_answers",
    "correct_with_unreliable_explanation",
    "missing_prerequisite",
    "step_error",
    "transfer_failure",
    "no_history",
    "user_disputes_diagnosis",
    "repeated_explanation_ineffective",
    "out_of_scope_objective_refusal",
]

REQUIRED_TOP_FIELDS = [
    "schema_version",
    "sample_id",
    "set",
    "situation",
    "source",
    "objective",
    "question",
    "grounding",
    "answers",
    "assistance",
    "teaching_state",
    "provenance",
]

REQUIRED_ANSWER_FIELDS = ["class", "answer", "verdict_result", "expectation"]

HOLDOUT_IDS = ("S2", "S3")


def mechanical_check(sample: dict) -> list[dict[str, object]]:
    """Deterministic field/structure checks — no model, no I/O beyond args."""
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    add("schema_version", sample.get("schema_version") == SCHEMA_VERSION)
    missing = [f for f in REQUIRED_TOP_FIELDS if f not in sample]
    add("required_fields", not missing, "missing: " + ",".join(missing))
    add(
        "set_membership",
        sample.get("set") in ("dev_regression", "holdout"),
        str(sample.get("set")),
    )
    add("situation_tagged", bool(sample.get("situation")))
    source = sample.get("source") or {}
    add(
        "source_pinned",
        bool(source.get("material_id"))
        and bool(source.get("revision"))
        and bool(source.get("locators")),
    )
    question = sample.get("question") or {}
    add(
        "question_contract_complete",
        bool(question.get("question_id"))
        and bool(question.get("prompt"))
        and bool(question.get("expected_answer")),
    )
    # Answer isolation: the recorded question contract must not carry verdict
    # or confidence data — those belong to the answers list only.
    leaked = [k for k in ("verdict", "confidence", "feedback") if k in question]
    add("answer_isolation", not leaked, "leaked: " + ",".join(leaked))
    answers = sample.get("answers") or []
    bad = [
        a.get("class", "?")
        for a in answers
        if not isinstance(a, dict) or any(f not in a for f in REQUIRED_ANSWER_FIELDS)
    ]
    add("answers_wellformed", not bad, "bad classes: " + ",".join(bad))
    add("assistance_recorded", isinstance(sample.get("assistance"), dict))
    prov = sample.get("provenance") or {}
    add("provenance_traceable", bool(prov.get("path_id")) and bool(prov.get("result_file")))
    return checks


def _load_samples(root: Path) -> list[dict]:
    path = root / "samples.json"
    if not path.exists():
        raise SystemExit(f"samples.json not found under {root}; run build first")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["samples"]


def _find_result_file(case_hint: str) -> Path | None:
    """Prefer a result file whose turn actually produced a card — early
    failed attempts share the case name and must not shadow the valid one."""
    matches = []
    for path in sorted(Path("data").glob("semantic-samples*/*-result.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("case") == case_hint:
            matches.append(path)
    for path in matches:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("pending_question_present"):
            return path
    return matches[0] if matches else None


def _default_situation(meta: dict) -> str:
    if str(meta.get("kind", "")).startswith("negative"):
        return "out_of_scope_objective_refusal"
    return "five_class_answers"


def _attach_verdicts(sample: dict) -> dict:
    """Attach recorded answer verdicts from audit runs, newest auditor first."""
    sources = [
        ("data/semantic-audit-27/verdicts.json", "semantic_audit_27.py"),
        ("data/semantic-audit-23/verdicts.json", "semantic_audit_23.py"),
    ]
    result_path = sample["provenance"]["result_file"]
    case = json.loads(Path(result_path).read_text(encoding="utf-8")).get("case", "")
    for path, auditor in sources:
        p = Path(path)
        if not p.exists():
            continue
        payload = json.loads(p.read_text(encoding="utf-8"))
        for entry_key, entry in payload.items():
            if not isinstance(entry, dict) or "classes" not in entry:
                continue
            # audit-23 keys entries by case with path_id inside; audit-27 keys
            # entries directly by path_id.
            if (
                entry_key != sample["provenance"]["path_id"]
                and entry.get("path_id") != (sample["provenance"]["path_id"])
                and entry.get("case") != case
            ):
                continue
            rows = entry.get("classes", [])
            answers = [
                {
                    "class": row.get("class"),
                    "answer": row.get("answer", ""),
                    "verdict_result": (row.get("verdict") or {}).get("result")
                    if isinstance(row.get("verdict"), dict)
                    else row.get("result"),
                    "confidence": (row.get("verdict") or {}).get("confidence")
                    if isinstance(row.get("verdict"), dict)
                    else row.get("confidence"),
                    "feedback_head": (
                        (row.get("verdict") or {}).get("feedback") or row.get("feedback") or ""
                    )[:200]
                    if isinstance(row.get("verdict"), dict)
                    else (row.get("feedback") or "")[:200],
                    "expectation": row.get("expectation"),
                    "matches_expectation": row.get("matches_expectation", row.get("matches")),
                }
                for row in rows
            ]
            # audit-27 recorded verdicts only; the answer texts live in its
            # module-level constants. Backfill them so replays grade the same
            # text that was originally graded.
            if auditor.endswith("semantic_audit_27.py") and all(not a["answer"] for a in answers):
                answers = _backfill_audit27_answers(sample, answers)
            sample["answers"] = answers
            sample["audit"]["auditor"] = auditor
            return sample
    return sample


def _backfill_audit27_answers(sample: dict, answers: list[dict]) -> list[dict]:
    import ast

    module_path = Path("data/semantic_audit_27.py")
    if not module_path.exists():
        return answers
    # Extract the module's constants via AST — never import or exec it: the
    # audit script calls asyncio.run(main()) at module level, so importing it
    # would silently fire a full real-model re-audit. ANSWERS is keyed by
    # module-level name constants (S1 = "semantic-…"), so resolve in two
    # passes instead of literal_eval.
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    strings: dict[str, str] = {}
    answers_node: ast.Dict | None = None
    dont_know = "我不知道。"
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "ANSWERS" in names and isinstance(node.value, ast.Dict):
                answers_node = node.value
            elif isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                for name in names:
                    strings[name] = node.value.value
            if "DONT_KNOW" in names and isinstance(node.value, ast.Constant):
                dont_know = node.value.value
    texts: dict[str, str] = {}
    if answers_node is not None:
        for key_node, value_node in zip(answers_node.keys, answers_node.values):
            key = strings.get(getattr(key_node, "id", ""), getattr(key_node, "value", None))
            if key is None:
                continue
            try:
                texts[key] = ast.literal_eval(value_node)
            except ValueError:
                pass
    path_id = sample["provenance"]["path_id"]
    per_path = texts.get(path_id, {})
    for a in answers:
        if a["class"] == "correct":
            a["answer"] = sample["question"]["expected_answer"]
        else:
            a["answer"] = per_path.get(a["class"], dont_know if a["class"] == "dont_know" else "")
    return answers


def cmd_build(args: argparse.Namespace) -> None:
    from deeptutor.learning.storage import LearningStore
    from deeptutor.reading.store import ReadingStore, unit_quality

    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    out = root / "samples.json"
    if out.exists() and not args.force:
        raise SystemExit(
            f"{out} exists; pass --force after verifying the change is intended "
            "(built banks are never silently overwritten)"
        )

    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    learning = LearningStore()
    reading = ReadingStore()
    samples: list[dict] = []
    for meta in registry["samples"]:
        sid = meta["id"]
        result_file = _find_result_file(meta.get("case_hint") or _case_hint(sid))
        if result_file is None:
            print(f"skip {sid}: no result file", flush=True)
            continue
        data = json.loads(result_file.read_text(encoding="utf-8"))
        progress = learning.load(data["path_id"])
        question = progress.pending_question if progress else None
        if question is None:
            print(f"skip {sid}: no pending question in store", flush=True)
            continue
        refs = (question.source_evidence or {}).get("sources") or []
        first_ref = (refs[0].get("reading_reference") or {}) if refs else {}
        sample = {
            "schema_version": SCHEMA_VERSION,
            "sample_id": sid,
            "set": "holdout" if sid in HOLDOUT_IDS else "dev_regression",
            "situation": meta.get("situation") or _default_situation(meta),
            "source": {
                "material_id": first_ref.get("material_id"),
                "revision": first_ref.get("revision"),
                "locators": first_ref.get("locators"),
                "quality": unit_quality(
                    reading.unit_text(first_ref["material_id"], first_ref["locators"][0])
                )
                if first_ref
                else {},
            },
            "objective": meta.get("objective")
            or (progress.modules[0].knowledge_points[0].name if progress.modules else ""),
            "knowledge_type": meta.get("class", ""),
            "question": {
                "question_id": question.question_id,
                "prompt": question.prompt,
                "expected_answer": question.expected_answer,
                "question_type": question.question_type,
                "source_evidence_kind": (question.source_evidence or {}).get("kind"),
            },
            "grounding": {
                "lesson_coverage": (
                    progress.lesson_evidence.get(question.knowledge_point_id) or {}
                ).get("coverage"),
                "citations_note": meta.get("citations", ""),
            },
            "answers": [],
            "assistance": {"hints_used": 0},
            "teaching_state": {
                "source_grounded": progress.source_grounded,
                "pending_question_present": True,
            },
            "provenance": {
                "path_id": data["path_id"],
                "session_id": data.get("session_id"),
                "turn_id": data.get("turn_id"),
                "result_file": str(result_file),
                "built_at": time.time(),
                "builder": "scripts/teaching_samples.py build",
            },
            "audit": {
                "auditor": "agent",
                "disputes": meta.get("disputes", []),
            },
        }
        samples.append(_attach_verdicts(sample))

    out.write_text(
        json.dumps({"built_at": time.time(), "samples": samples}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    failures = [c for s in samples for c in mechanical_check(s) if not c["ok"]]
    print(
        f"built {len(samples)} samples -> {out}; mechanical failures: {len(failures)}", flush=True
    )
    for c in failures:
        print(json.dumps(c, ensure_ascii=False), flush=True)


def _case_hint(sid: str) -> str:
    hints = {
        "S1": "pdf-dpo-failure",
        "S2": "epub-five-whys",
        "S3": "epub-five-whys-unsupported",
        "S4": "epub-cliche-questions",
        "S5": "pdf-proactive-memory",
    }
    return hints.get(sid, sid)


def cmd_replay(args: argparse.Namespace) -> None:
    import asyncio

    from deeptutor.learning import semantic_assessment as semantic
    from deeptutor.services.llm.config import get_llm_config

    root = Path(args.root)
    samples = _load_samples(root)
    sample = next((s for s in samples if s["sample_id"] == args.sample), None)
    if sample is None:
        raise SystemExit(f"sample {args.sample} not found")
    if sample.get("set") == "holdout" and not args.allow_holdout:
        raise SystemExit(
            f"{args.sample} is in the holdout set; pass --allow-holdout only for a "
            "one-off verification, never in a dev iteration"
        )
    if not sample["answers"]:
        raise SystemExit(f"sample {args.sample} has no recorded answers to replay")

    # Rebuild the exact grading item the audit flow used: the question
    # contract plus source evidence, loaded fresh from the store by the
    # sample's provenance path. Grading without the source text would measure
    # a different contract than the original verdict.
    from deeptutor.learning.storage import LearningStore

    progress = LearningStore().load(sample["provenance"]["path_id"])
    if progress is None or progress.pending_question is None:
        raise SystemExit(
            f"the learning path {sample['provenance']['path_id']} no longer has "
            "its pending question; the sample cannot be replayed faithfully"
        )
    question = progress.pending_question
    base_item = {**semantic.question_contract(question)}

    async def run() -> list[dict]:
        rows = []
        for answer in sample["answers"]:
            payload = {
                **base_item,
                "answer": answer["answer"],
                "source_evidence": question.source_evidence,
            }
            # A per-answer failure (e.g. the provider's output budget exhausted
            # by reasoning) is itself replay evidence: record it and continue.
            try:
                verdicts = await semantic.judge_answers(get_llm_config(), [payload])
                verdict = verdicts[question.question_id]
                rows.append(
                    {
                        "class": answer["class"],
                        "replay_result": verdict.model_dump(),
                        "original_result": answer["verdict_result"],
                        "differs": verdict.result != answer["verdict_result"],
                        "error": None,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                rows.append(
                    {
                        "class": answer["class"],
                        "replay_result": None,
                        "original_result": answer["verdict_result"],
                        "differs": None,
                        "error": repr(exc)[:300],
                    }
                )
            print(json.dumps(rows[-1], ensure_ascii=False)[:220], flush=True)
        return rows

    rows = asyncio.run(run())
    record = {
        "sample_id": args.sample,
        "replayed_at": time.time(),
        "judge_entry": "deeptutor.learning.semantic_assessment.judge_answers",
        "rows": rows,
        "diff_count": sum(1 for r in rows if r["differs"]),
        "error_count": sum(1 for r in rows if r["error"]),
    }
    out_dir = root / "replays"
    out_dir.mkdir(exist_ok=True)
    # Nanosecond names: two replays in the same second must not overwrite each
    # other — earlier records are the version trail the acceptance relies on.
    out = out_dir / f"{args.sample}-{time.time_ns()}.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"replay written -> {out} (diffs: {record['diff_count']})", flush=True)


def cmd_report(args: argparse.Namespace) -> None:
    root = Path(args.root)
    samples = _load_samples(root)
    report: dict = {
        "generated_at": time.time(),
        "samples": [],
        "situation_coverage": {s: 0 for s in PLAN_SITUATIONS},
    }
    for sample in samples:
        checks = mechanical_check(sample)
        replays_dir = root / "replays"
        replays = (
            sorted(replays_dir.glob(f"{sample['sample_id']}-*.json"))
            if replays_dir.exists()
            else []
        )
        latest = json.loads(replays[-1].read_text(encoding="utf-8")) if replays else None
        entry = {
            "sample_id": sample["sample_id"],
            "set": sample["set"],
            "situation": sample["situation"],
            "mechanical_failures": [c for c in checks if not c["ok"]],
            "answer_classes": [a.get("class") for a in sample["answers"]],
            "semantic_disputes": [
                a["class"] for a in sample["answers"] if a.get("matches_expectation") is False
            ],
            "replays": len(replays),
            "latest_replay_diffs": latest["diff_count"] if latest else None,
        }
        report["samples"].append(entry)
        if sample["situation"] in report["situation_coverage"]:
            report["situation_coverage"][sample["situation"]] += 1
    report["uncovered_situations"] = [s for s, n in report["situation_coverage"].items() if n == 0]
    out = root / f"report-{int(time.time())}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report -> {out}", flush=True)
    print(
        json.dumps(
            {
                "samples": len(report["samples"]),
                "mechanical_failures": sum(
                    len(e["mechanical_failures"]) for e in report["samples"]
                ),
                "disputed_answers": sum(len(e["semantic_disputes"]) for e in report["samples"]),
                "uncovered_situations": report["uncovered_situations"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="E1 teaching-quality sample bank")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="compile samples.json from the registry and audit runs")
    p_build.add_argument("--root", default="data/teaching-samples")
    p_build.add_argument("--registry", default="data/semantic-samples-24/sample-registry.json")
    p_build.add_argument("--force", action="store_true")
    p_build.set_defaults(func=cmd_build)

    p_replay = sub.add_parser("replay", help="re-run provider grading for one sample")
    p_replay.add_argument("--root", default="data/teaching-samples")
    p_replay.add_argument("--sample", required=True)
    p_replay.add_argument("--allow-holdout", action="store_true")
    p_replay.set_defaults(func=cmd_replay)

    p_report = sub.add_parser("report", help="aggregate mechanical checks, disputes and replays")
    p_report.add_argument("--root", default="data/teaching-samples")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
