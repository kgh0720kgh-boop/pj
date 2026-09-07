#!/usr/bin/env python3
"""Freeze a question-free isolation design; no transport or model calls."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _common import json_file_bytes, read_json, write_output_batch
from freeze_narrowed_grounding_plan_v0_1 import bindings, git, safe_path

ROOT = Path(__file__).resolve().parents[2]
BASE = "data_construction/exploration/ai_question_structure_scale_v0_1"
DESIGN = BASE + "/contracts/grounding_input_isolation_design_v0_2.json"
PLAN = BASE + "/contracts/grounding_input_isolation_freeze_v0_2.json"
NAMESPACES = (BASE + "/grounding_input_isolation_probe_v0_2", BASE + "/narrowed_grounding_v0_2")
SOURCE_COMMIT = "bd841eaf05f2e539f1b58b88ad3a7ce57b2ce692"
SOURCE_PATHS = (
    BASE + "/narrowed_grounding_v0_1",
    BASE + "/contracts/narrowed_grounding_plan_v0_1.json",
    BASE + "/contracts/narrowed_grounding_design_v0_1.json",
    BASE + "/contracts/narrowed_grounding_runtime_freeze_v0_1.json",
    BASE + "/contracts/narrowed_grounding_packet_schema_v0_1.json",
    BASE + "/contracts/narrowed_grounding_raw_schema_v0_1.json",
    BASE + "/prompts/narrowed_grounding_v0_1.md",
    BASE + "/prompts/narrowed_grounding_author_guide_v0_1.md",
    "data_construction/tools/narrowed_grounding_runtime_v0_1.py",
    "tests/test_narrowed_grounding_plan_v0_1.py",
    "tests/test_narrowed_grounding_runtime_v0_1.py",
    "tests/test_narrowed_grounding_collection_v0_1.py",
    "state/narrowed_grounding_author_dispatch_v0_1.json",
    "data_construction/reports/research_sequencing_decision_v0_12.md",
    "data_construction/manifests/historical_exposed_ids.json",
    "data_construction/manifests/split_manifest_v0_1.json",
    "data_construction/manifests/question_exposure_ledger_v0_3.json",
)
CONTRACT_PATHS = (
    DESIGN, "data_construction/tools/freeze_grounding_input_isolation_v0_2.py",
    "tests/test_grounding_input_isolation_v0_2.py",
    "data_construction/reports/research_sequencing_decision_v0_13.md",
    "data_construction/tools/freeze_narrowed_grounding_plan_v0_1.py",
    "data_construction/tools/_common.py",
)
CATEGORIES = (
    "explicit_messages_and_attachments", "global_and_project_instructions",
    "conversation_history_and_resume_state", "memory_and_retrieval",
    "skills_metadata_and_content", "tool_definitions_and_tool_results",
    "workspace_files_and_environment_metadata", "connectors_and_external_sources",
    "platform_managed_context",
)
BRANCHES = ("STOP_INPUT_ISOLATION_FAILURE", "BLOCKED_UNVERIFIABLE_CONTEXT",
            "INCOMPLETE_ISOLATION_PROBE", "QUALIFIED_FOR_SEPARATE_PLAN_ONLY")


def validate_design(design: dict) -> None:
    """Check design invariants, not whether any host has satisfied them."""
    scope = {"research_question_ids": [], "fresh_question_ids_used": 0,
             "locked_question_ids_used": 0, "new_research_authoring_authorized": False,
             "grounding_authorized": False, "execution_authorized": False,
             "answer_recovery_authorized": False, "platform_configuration_changes_authorized": False}
    if (design.get("schema_version") != "grounding_input_isolation_design_v0_2" or
            design.get("status") != "design_only_no_transport_qualified" or
            json_file_bytes(design.get("scope")) != json_file_bytes(scope)):
        raise ValueError("isolation design must remain question-free and unauthorized for research")
    if design.get("inventory_categories") != list(CATEGORIES):
        raise ValueError("missing, duplicate or reordered context inventory category")
    if [b.get("decision") for b in design.get("branch_order", [])] != list(BRANCHES):
        raise ValueError("fail-closed branch order changed")
    probe = design["probe_contract"]
    if [(c["case_id"], c["expected"]) for c in probe["cases"]] != [
        ("synthetic_closed_context", BRANCHES[3]),
        ("synthetic_known_injection", BRANCHES[0]),
        ("synthetic_opaque_boundary", BRANCHES[1]),
    ] or type(probe["max_launches_per_case"]) is not int or probe["max_launches_per_case"] != 1:
        raise ValueError("synthetic control design or retry budget changed")
    if (probe["research_payloads_allowed"] is not False or
            type(probe["actual_platform_probe_count"]) is not int or probe["actual_platform_probe_count"] != 0):
        raise ValueError("this freeze cannot contain a research payload or claim a probe")
    if design["identity_migration"]["new_version_required_fields"] != [
        "protocol_sha256", "author_guide_sha256", "response_schema_sha256",
        "packet_payload_sha256", "input_manifest_sha256",
    ] or design["identity_migration"]["old_bytes_changed"] is not False:
        raise ValueError("component identities must be separate without rewriting v0.1")
    if json_file_bytes(design["evidence_boundary"]) != json_file_bytes({
        "human_evidence": 0, "semantic_gold": False, "grounding_quality_evaluated": False,
        "transport_qualified": False, "new_model_calls": 0,
    }):
        raise ValueError("design validation is not transport qualification")


def require_absent(root: Path, commit: str | None = None) -> None:
    for name in NAMESPACES:
        if commit:
            if git(root, "ls-tree", "-r", "--name-only", commit, "--", name).strip():
                raise ValueError("new output namespace existed at design freeze")
        else:
            path = safe_path(root, name)
            if path.exists() and (not path.is_dir() or any(path.rglob("*"))):
                raise ValueError("new output namespace is not empty")


def make_plan(root: Path, implementation_commit: str) -> dict:
    if not isinstance(implementation_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", implementation_commit):
        raise ValueError("implementation commit must be a full Git OID")
    design = read_json(safe_path(root, DESIGN))
    validate_design(design)
    return {
        "schema_version": "grounding_input_isolation_freeze_v0_2",
        "status": "design_frozen_adapter_and_probe_not_implemented",
        "source_commit": SOURCE_COMMIT, "implementation_commit": implementation_commit,
        "preserved_artifacts": bindings(root, SOURCE_COMMIT, SOURCE_PATHS),
        "contract_artifacts": bindings(root, implementation_commit, CONTRACT_PATHS),
        "design": design, "output_namespaces_absent_at_freeze": list(NAMESPACES),
        "research_question_ids": [], "transport_qualified": False,
        "new_author_outputs": 0, "grounding_authorized": False,
        "next_gate": "IMPLEMENT_AND_FREEZE_QUESTION_FREE_TRANSPORT_PROBE_BEFORE_LAUNCH",
    }


def validate_plan(root: Path = ROOT, *, require_output_absence: bool = False) -> dict:
    path = safe_path(root, PLAN)
    plan = read_json(path)
    if path.read_bytes() != json_file_bytes(make_plan(root, plan["implementation_commit"])):
        raise ValueError("freeze differs from exact bound design and preserved bytes")
    introductions = git(root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--", PLAN).decode().splitlines()
    if len(introductions) != 1:
        raise ValueError("freeze must have exactly one committed introduction")
    commit = introductions[0]
    if git(root, "show", commit + ":" + PLAN) != path.read_bytes():
        raise ValueError("freeze changed after committed introduction")
    for predecessor in (SOURCE_COMMIT, plan["implementation_commit"]):
        git(root, "merge-base", "--is-ancestor", predecessor, commit + "^")
    require_absent(root, commit)
    if require_output_absence:
        require_absent(root)
    return {"status": "pass", "freeze_commit": commit, "transport_qualified": False,
            "grounding_authorized": False, "current_output_absence_checked": require_output_absence,
            "preserved_artifact_count": len(plan["preserved_artifacts"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-design", action="store_true")
    mode.add_argument("--validate-only", action="store_true")
    parser.add_argument("--require-output-absence", action="store_true")
    args = parser.parse_args()
    try:
        if git(ROOT, "rev-parse", "--show-toplevel").decode().strip() != str(ROOT):
            raise ValueError("unexpected repository root")
        if args.freeze_design:
            if safe_path(ROOT, PLAN).exists():
                raise ValueError("freeze exists; never overwrite")
            require_absent(ROOT)
            plan = make_plan(ROOT, git(ROOT, "rev-parse", "HEAD").decode().strip())
            write_output_batch({"freeze": (ROOT / PLAN, json_file_bytes(plan))}, overwrite=False)
            result = {"status": "design_written_commit_required_before_use", "transport_qualified": False}
        else:
            result = validate_plan(require_output_absence=args.require_output_absence)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
