#!/usr/bin/env python3
"""Freeze a metadata-only grounding study; never produce grounding outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

from _common import canonical_json_sha256, iter_json_records, json_file_bytes, read_json, write_output_batch

ROOT = Path(__file__).resolve().parents[2]
BASE = "data_construction/exploration/ai_question_structure_scale_v0_1"
RUN = BASE + "/narrowed_grounding_v0_1"
PLAN = BASE + "/contracts/narrowed_grounding_plan_v0_1.json"
SPEC = BASE + "/contracts/narrowed_grounding_design_v0_1.json"
PROTOCOL = BASE + "/prompts/narrowed_grounding_v0_1.md"
TOOL = "data_construction/tools/freeze_narrowed_grounding_plan_v0_1.py"
TEST = "tests/test_narrowed_grounding_plan_v0_1.py"
SOURCE_COMMIT = "aa380e69b534e475f09d496955ebcbac69531309"
IDS = ("0d48bffa70ef4acf", "cc681cfdba9badd5", "1e2e4e4f72a64bbf",
       "1e674ae4b655c1a1", "1ca8ffcd3e20e498", "ba563b015b09bf21")
INSTRUMENT = BASE + "/operator_equivalence_targeted_instrument_v0_2"
TARGETED = BASE + "/operator_equivalence_targeted_reauthor_v0_1"
CONTRACT_PATHS = (TOOL, TEST, SPEC, PROTOCOL, "data_construction/tools/_common.py")
SOURCE_PATHS = (
    TARGETED, INSTRUMENT,
    BASE + "/contracts/operator_equivalence_targeted_reauthor_plan_v0_1.json",
    BASE + "/contracts/operator_equivalence_targeted_instrument_plan_v0_2.json",
    BASE + "/contracts/representative_environment_realization_plan_v0_1.json",
    BASE + "/contracts/open_operator_realization_schema_v0_1.json",
    BASE + "/contracts/representative_environment_view_schema_v0_1.json",
    BASE + "/representative_environment_realization_v0_1/inputs/environment_views.jsonl",
    BASE + "/representative_environment_realization_v0_1/inputs/environment_views_manifest_v0_1.json",
    "data_construction/manifests/source_manifest_v0_1.json",
    "data_construction/manifests/historical_exposed_ids.json",
    "data_construction/manifests/question_exposure_ledger_v0_3.json",
    "data_construction/manifests/split_manifest_v0_1.json",
    "data_construction/reports/research_sequencing_decision_v0_9.md",
)


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError("Git check failed: " + " ".join(args[:3]))
    return result.stdout


def safe_path(root: Path, name: str) -> Path:
    parts = PurePosixPath(name)
    if parts.is_absolute() or not parts.parts or parts.as_posix() != name or any(
        part in ("..", ".") for part in parts.parts
    ) or ":" in name or "\\" in name:
        raise ValueError("noncanonical repository path: " + name)
    current = root
    for part in parts.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlink in repository path: " + name)
    return current


def tracked_files(root: Path, commit: str, paths: tuple[str, ...]) -> list[str]:
    names = set()
    for path in paths:
        found = git(root, "ls-tree", "-r", "--name-only", commit, "--", path).decode().splitlines()
        if not found:
            raise ValueError("missing committed input: " + path)
        names.update(found)
    return sorted(names)


def bindings(root: Path, commit: str, paths: tuple[str, ...]) -> list[dict]:
    git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    result = []
    for name in tracked_files(root, commit, paths):
        path = safe_path(root, name)
        data = path.read_bytes()
        tree = git(root, "ls-tree", commit, "--", name).decode()
        if not tree.startswith(("100644 blob ", "100755 blob ")):
            raise ValueError("input is not a regular Git blob: " + name)
        if data != git(root, "show", commit + ":" + name):
            raise ValueError("source or implementation changed: " + name)
        result.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    return result


def planned_outputs() -> dict[str, str]:
    outputs = {}
    for index in range(1, 7):
        outputs[f"packet_{index:02}"] = f"{RUN}/packets/question_{index:02}.json"
        outputs[f"raw_{index:02}"] = f"{RUN}/raw/question_{index:02}.json"
    for label, filename in (
        ("packet_manifest", "packet_manifest.json"),
        ("records", "grounding_records.jsonl"),
        ("checks", "checks.jsonl"),
        ("comparisons", "question_comparisons.jsonl"),
        ("metrics", "metrics_v0_1.json"),
        ("report", "report_v0_1.md"),
        ("run_manifest", "run_manifest.json"),
        ("exposure", "grounding_exposure_ledger_v0_1.json"),
    ):
        outputs[label] = RUN + "/" + filename
    return outputs


def require_absent(root: Path, commit: str | None = None) -> None:
    if commit:
        if git(root, "ls-tree", "-r", "--name-only", commit, "--", RUN).strip():
            raise ValueError("grounding output namespace existed at freeze commit")
    else:
        directory = safe_path(root, RUN)
        # Reject even unplanned files or broken symlinks; an empty directory is harmless.
        if directory.exists() and (not directory.is_dir() or any(directory.rglob("*"))):
            raise ValueError("grounding output namespace is not empty")
        for name in planned_outputs().values():
            if safe_path(root, name).exists():
                raise ValueError("planned grounding output already exists")


def select_candidates(records: list[dict], normalized: list[dict]) -> list[dict]:
    norm = {(n["question_id"], n["producer_partition"], n["candidate_id"]): n for n in normalized}
    if len(norm) != len(normalized):
        raise ValueError("duplicate normalized observation")
    by_pair = {(r["question_id"], r["producer_partition"]): r for r in records}
    producers = ("e2_author_partition_09", "e2_author_partition_10")
    if len(by_pair) != 12 or len(records) != 12 or set(by_pair) != {
        (qid, producer) for qid in IDS for producer in producers
    }:
        raise ValueError("expected exactly twelve author-question records")
    selected = []
    seen = set()
    for index, qid in enumerate(IDS, 1):
        for producer in producers:
            record = by_pair[qid, producer]
            for candidate in sorted(record["realization_candidates"], key=lambda c: c["candidate_id"]):
                key = (qid, producer, candidate["candidate_id"])
                if key in seen or key not in norm:
                    raise ValueError("duplicate or unnormalized candidate")
                seen.add(key)
                normalized_candidate = norm[key]
                if normalized_candidate["equivalence_eligibility"]["status"] != "full_eligible":
                    raise ValueError("selected candidate is not full eligible")
                if normalized_candidate["source_author_record_sha256"] != canonical_json_sha256(record):
                    raise ValueError("normalized candidate record hash mismatch")
                slots = candidate["binding_slots"]
                if len({s["slot_id"] for s in slots}) != len(slots) or any(
                    s["resolved_locator"] is not None or s["grounding_status"] != "not_grounded_in_this_stage"
                    for s in slots
                ):
                    raise ValueError("duplicate or already grounded source slot")
                selected.append({
                    "observation_id": ":".join(key), "question_id": qid,
                    "packet_index": index, "producer_partition": producer,
                    "candidate_id": candidate["candidate_id"],
                    "target_backbone_variant_id": candidate["target_backbone_variant_id"],
                    "source_record_sha256": canonical_json_sha256(record),
                    "source_candidate_sha256": canonical_json_sha256(candidate),
                    "environment_view_id": record["input_view_id"],
                    "environment_payload_sha256": record["input_view_payload_sha256"],
                    "operator_node_ids": [n["node_id"] for n in candidate["graph"]["nodes"]],
                    "slots": [{k: s[k] for k in ("slot_id", "environment_modality", "cardinality")}
                              for s in slots],
                })
    if len(selected) != 14 or seen != set(norm):
        raise ValueError("must retain every one of the fourteen observations")
    return selected


def decision(technical_errors: int, source_unavailable: int, delivered: int,
             resolved: int, unresolved: int) -> str:
    """Frozen branch order; failures and incomplete delivery cannot become passes."""
    values = (technical_errors, source_unavailable, delivered, resolved, unresolved)
    if any(type(v) is not int or v < 0 for v in values) or delivered > 14 or resolved > delivered:
        raise ValueError("invalid decision counts")
    if technical_errors:
        return "STOP_TECHNICAL_OR_LEAKAGE_FAILURE"
    if source_unavailable:
        return "BLOCKED_PINNED_ENVIRONMENT_UNAVAILABLE"
    if delivered != 14:
        return "INCOMPLETE_GROUNDING_COLLECTION"
    if resolved != 14 or unresolved:
        return "REVIEW_AMBIGUITY_OR_COVERAGE_BEFORE_EXECUTION_PLAN"
    return "FREEZE_GROUNDING_EVIDENCE_FOR_SEPARATE_EXECUTION_PLAN"


def make_plan(root: Path, implementation_commit: str) -> dict:
    source_bindings = bindings(root, SOURCE_COMMIT, SOURCE_PATHS)
    contract_bindings = bindings(root, implementation_commit, CONTRACT_PATHS)
    history = read_json(root / "data_construction/manifests/historical_exposed_ids.json")
    ledger = read_json(root / "data_construction/manifests/question_exposure_ledger_v0_3.json")
    if history.get("is_complete") is not True or set(IDS) & set(history["exposed_question_ids"]):
        raise ValueError("historical exposure gate failed")
    if not set(IDS) <= set(ledger["ai_question_structure_exploration"]["question_ids"]):
        raise ValueError("fresh question ID would be consumed")
    metrics = read_json(root / INSTRUMENT / "metrics_v0_2.json")
    if metrics.get("decision") != "FREEZE_INSTRUMENT_REAUTHOR_EVIDENCE_FOR_SEPARATE_NARROWED_GROUNDING_PLAN":
        raise ValueError("instrument run did not authorize this plan")
    selected = select_candidates(list(iter_json_records(root / INSTRUMENT / "combined_final_records.jsonl")),
                                 list(iter_json_records(root / INSTRUMENT / "final_normalized_candidates.jsonl")))
    return {
        "schema_version": "narrowed_grounding_plan_v0_1",
        "run_id": "hybridqa_narrowed_grounding_v0_1_run_001",
        "status": "planned_not_run",
        "source_commit": SOURCE_COMMIT, "implementation_commit": implementation_commit,
        "source_artifacts": source_bindings, "contract_artifacts": contract_bindings,
        "question_ids": list(IDS), "selection": selected,
        "selection_counts": {"questions": 6, "author_question_pairs": 12, "candidates": 14,
                             "binding_slots": sum(len(c["slots"]) for c in selected)},
        "design": read_json(root / SPEC), "planned_outputs": planned_outputs(),
        "output_absence_proof": "validator_requires_empty_namespace_in_plan_introduction_commit",
        "pre_generation_implementation_gate": {
            "receipt_path": BASE + "/contracts/narrowed_grounding_runtime_freeze_v0_1.json",
            "required": True,
            "condition": "schemas_packet_builder_validator_analyzer_tests_and_protocol_bound_at_output_absent_commit",
            "no_protocol_change_allowed": True,
        },
        "grounding_outputs_created": 0, "execution_authorized": False, "answer_recovery_authorized": False,
    }


def validate_plan(root: Path = ROOT, *, require_output_absence: bool = False) -> dict:
    plan_path = safe_path(root, PLAN)
    plan = read_json(plan_path)
    expected = make_plan(root, plan["implementation_commit"])
    if plan != expected or plan_path.read_bytes() != json_file_bytes(expected):
        raise ValueError("plan differs from exact frozen contract")
    commits = git(root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--", PLAN).decode().splitlines()
    if len(commits) != 1:
        raise ValueError("plan must have exactly one committed introduction")
    freeze_commit = commits[0]
    if git(root, "show", freeze_commit + ":" + PLAN) != plan_path.read_bytes():
        raise ValueError("plan changed after freeze")
    git(root, "merge-base", "--is-ancestor", plan["implementation_commit"], freeze_commit + "^")
    git(root, "merge-base", "--is-ancestor", SOURCE_COMMIT, freeze_commit + "^")
    require_absent(root, freeze_commit)
    if require_output_absence:
        require_absent(root)
    return {"status": "pass", "freeze_commit": freeze_commit, **plan["selection_counts"],
            "planned_output_files": len(planned_outputs()),
            "current_output_absence_checked": require_output_absence,
            "grounding_results_validated": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze-plan", action="store_true")
    modes.add_argument("--validate-only", action="store_true")
    parser.add_argument("--require-output-absence", action="store_true")
    args = parser.parse_args()
    try:
        if git(ROOT, "rev-parse", "--show-toplevel").decode().strip() != str(ROOT):
            raise ValueError("unexpected repository root")
        if args.freeze_plan:
            if safe_path(ROOT, PLAN).exists():
                raise ValueError("plan already exists; never overwrite a frozen plan")
            require_absent(ROOT)
            head = git(ROOT, "rev-parse", "HEAD").decode().strip()
            plan = make_plan(ROOT, head)
            write_output_batch({"plan": (ROOT / PLAN, json_file_bytes(plan))}, overwrite=False)
            result = {"status": "plan_written_commit_required_before_use", **plan["selection_counts"]}
        else:
            result = validate_plan(require_output_absence=args.require_output_absence)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
