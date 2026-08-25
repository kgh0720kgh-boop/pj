#!/usr/bin/env python3
"""Freeze and run the v0.2 targeted authoring-instrument revision.

The run reuses exactly the six already exposed targeted v0.1 questions. Two
fresh-context authors first submit immutable drafts, receive exactly one
deterministic candidate-local completeness feedback round, and then submit
final records. The checker exposes only target-node, required-dependency,
target-output, and output-arity facts. This tool performs no grounding,
execution, answer recovery, preference selection, or adjudication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from _common import (
    canonical_json_sha256,
    git_tracked_commit_identity,
    iter_json_records,
    json_file_bytes,
    jsonl_file_bytes,
    read_json,
    sha256_file,
    write_output_batch,
)
import build_operator_equivalence_crossed_author_sensitivity as sensitivity
import build_operator_equivalence_normalization as normalizer_v01
import build_operator_equivalence_normalization_v0_2 as normalizer_v02
import build_operator_equivalence_targeted_reauthor as targeted_v01


TOOL_VERSION = "operator_equivalence_targeted_instrument_builder_v0_2"
PLAN_SCHEMA_VERSION = "operator_equivalence_targeted_instrument_plan_v0_2"
PLAN_ID = "hybridqa_operator_equivalence_targeted_instrument_plan_v0_2"
RUN_ID = "hybridqa_operator_equivalence_targeted_instrument_v0_2_run_001"
AUTHOR_IDS = ("instrument_author_01", "instrument_author_02")
AUTHOR_PRODUCERS = ("e2_author_partition_09", "e2_author_partition_10")
REFERENCE_AUTHOR_IDS = targeted_v01.AUTHOR_IDS
EXPECTED_QUESTION_IDS = targeted_v01.EXPECTED_QUESTION_IDS
EXPECTED_QUESTIONS = len(EXPECTED_QUESTION_IDS)

ROOT = Path(__file__).resolve().parents[2]
SCALE_BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
CONTRACTS = SCALE_BASE / "contracts"
PROMPTS = SCALE_BASE / "prompts"
TARGETED_V01_BASE = SCALE_BASE / "operator_equivalence_targeted_reauthor_v0_1"
RUN_BASE = SCALE_BASE / "operator_equivalence_targeted_instrument_v0_2"

DEFAULT_PLAN = CONTRACTS / "operator_equivalence_targeted_instrument_plan_v0_2.json"
DEFAULT_FEEDBACK_SCHEMA = (
    CONTRACTS / "operator_equivalence_targeted_instrument_feedback_schema_v0_2.json"
)
DEFAULT_NORMALIZATION_SCHEMA = (
    CONTRACTS
    / "operator_equivalence_targeted_instrument_normalization_schema_v0_2.json"
)
DEFAULT_COMPARISON_SCHEMA = (
    CONTRACTS
    / "operator_equivalence_targeted_instrument_comparison_schema_v0_2.json"
)
DEFAULT_REALIZATION_SCHEMA = CONTRACTS / "open_operator_realization_schema_v0_1.json"
DEFAULT_PROTOCOL = PROMPTS / "operator_equivalence_targeted_instrument_v0_2.md"
DEFAULT_TARGETED_PLAN = (
    CONTRACTS / "operator_equivalence_targeted_reauthor_plan_v0_1.json"
)
DEFAULT_TARGETED_PACKETS = tuple(
    TARGETED_V01_BASE / f"authoring_packets/{author_id}.jsonl"
    for author_id in REFERENCE_AUTHOR_IDS
)
DEFAULT_TARGETED_AUTHOR_OUTPUTS = tuple(
    TARGETED_V01_BASE / f"author_outputs/{author_id}.jsonl"
    for author_id in REFERENCE_AUTHOR_IDS
)
DEFAULT_TARGETED_COMBINED = TARGETED_V01_BASE / "combined_author_records.jsonl"
DEFAULT_TARGETED_NORMALIZED = TARGETED_V01_BASE / "normalized_candidates.jsonl"
DEFAULT_TARGETED_COMPARISONS = TARGETED_V01_BASE / "question_comparisons.jsonl"
DEFAULT_TARGETED_CHECKS = TARGETED_V01_BASE / "checks.jsonl"
DEFAULT_TARGETED_METRICS = TARGETED_V01_BASE / "metrics_v0_1.json"
DEFAULT_TARGETED_REPORT = TARGETED_V01_BASE / "report_v0_1.md"
DEFAULT_TARGETED_MANIFEST = TARGETED_V01_BASE / "run_manifest.json"

DEFAULT_PACKETS = tuple(
    RUN_BASE / f"authoring_packets/{author_id}.jsonl" for author_id in AUTHOR_IDS
)
DEFAULT_DRAFTS = tuple(
    RUN_BASE / f"draft_outputs/{author_id}.jsonl" for author_id in AUTHOR_IDS
)
DEFAULT_FEEDBACK = tuple(
    RUN_BASE / f"feedback_round_01/{author_id}.jsonl" for author_id in AUTHOR_IDS
)
DEFAULT_FINALS = tuple(
    RUN_BASE / f"final_outputs/{author_id}.jsonl" for author_id in AUTHOR_IDS
)
DEFAULT_COMBINED_DRAFTS = RUN_BASE / "combined_draft_records.jsonl"
DEFAULT_DRAFT_NORMALIZED = RUN_BASE / "draft_normalized_candidates.jsonl"
DEFAULT_COMBINED_FINALS = RUN_BASE / "combined_final_records.jsonl"
DEFAULT_FINAL_NORMALIZED = RUN_BASE / "final_normalized_candidates.jsonl"
DEFAULT_COMPARISONS = RUN_BASE / "question_comparisons.jsonl"
DEFAULT_CHECKS = RUN_BASE / "checks.jsonl"
DEFAULT_METRICS = RUN_BASE / "metrics_v0_2.json"
DEFAULT_REPORT = RUN_BASE / "report_v0_2.md"
DEFAULT_MANIFEST = RUN_BASE / "run_manifest.json"

COMMON_RUNTIME = ROOT / "data_construction/tools/_common.py"
NORMALIZER_V01_TOOL = ROOT / "data_construction/tools/build_operator_equivalence_normalization.py"
NORMALIZER_V02_TOOL = ROOT / "data_construction/tools/build_operator_equivalence_normalization_v0_2.py"
TARGETED_V01_TOOL = ROOT / "data_construction/tools/build_operator_equivalence_targeted_reauthor.py"
CROSSED_VALIDATOR_TOOL = (
    ROOT / "data_construction/tools/build_operator_equivalence_crossed_author_sensitivity.py"
)
REPRESENTATIVE_VALIDATOR_TOOL = (
    ROOT / "data_construction/tools/build_representative_environment_realization.py"
)
TEST_ARTIFACT = ROOT / "tests/test_operator_equivalence_targeted_instrument_v0_2.py"

EVIDENCE_BOUNDARY = {
    "ai_non_human_non_gold": True,
    "already_exposed_question_ids_only": True,
    "prior_author_outputs_excluded_from_authoring_context": True,
    "normalization_outputs_excluded_from_authoring_context": True,
    "candidate_local_feedback_only": True,
    "answer_and_trace_excluded": True,
    "grounding_evaluated": False,
    "execution_evaluated": False,
    "answer_recovery_evaluated": False,
    "human_evidence_created": False,
    "gold_claimed": False,
}

FROZEN_CRITERIA = {
    "invalid_draft_record_count_max": 0,
    "invalid_final_record_count_max": 0,
    "technical_loss_count_max": 0,
    "feedback_record_count": 12,
    "feedback_reference_leakage_count_max": 0,
    "feedback_binding_error_count_max": 0,
    "feedback_rounds_per_author": 1,
    "eligible_set_contamination_count_max": 0,
    "unclassified_adapter_candidate_count_max": 0,
    "preferred_candidate_count_max": 0,
    "fresh_question_id_count_max": 0,
    "profile_inventory_loss_count_max": 0,
    "final_candidate_local_author_question_coverage_min": 12,
    "full_eligible_author_question_coverage_min": 12,
    "nonempty_final_author_semantic_intersection_count_min": 6,
    "final_author_semantic_exact_match_count_min": 5,
    "mean_final_author_semantic_jaccard_min": 0.90,
    "targeted_v0_1_reference_compatible_author_question_count_min": 12,
    "branch_on_technical_failure": (
        "REVISE_INSTRUMENT_V0_2_TECHNICAL_OR_ISOLATION_CONTRACT"
    ),
    "branch_on_repeated_coverage_failure": (
        "STOP_AUTOMATED_REAUTHORING_AND_REQUIRE_APPROVED_HUMAN_REVIEW"
    ),
    "branch_on_semantic_failure": (
        "NARROW_CHALLENGE_CLAIM_OR_REQUIRE_APPROVED_HUMAN_REVIEW"
    ),
    "branch_on_pass": (
        "FREEZE_INSTRUMENT_REAUTHOR_EVIDENCE_FOR_SEPARATE_NARROWED_GROUNDING_PLAN"
    ),
}

FORBIDDEN_FEEDBACK_KEYS = {
    "candidate_semantic_profile",
    "equivalence_eligibility",
    "failure_profile_sha256",
    "full_eligible_semantic_set",
    "preferred_candidate_id",
    "preference_reason",
    "reference_plan",
    "semantic_signature",
    "signature_sha256",
}
FORBIDDEN_FEEDBACK_VALUE_PATTERNS = (
    re.compile(r"\b(full_eligible|provisional_only|ineligible)\b"),
    re.compile(r"\b(answer|trace|grounding|execution)\b", re.IGNORECASE),
)


class TargetedInstrumentError(ValueError):
    """Raised when the frozen v0.2 instrument contract is violated."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze-plan", action="store_true")
    modes.add_argument("--validate-plan-only", action="store_true")
    modes.add_argument("--materialize-packets", action="store_true")
    modes.add_argument("--validate-packets-only", action="store_true")
    modes.add_argument("--check-drafts", action="store_true")
    modes.add_argument("--validate-feedback-only", action="store_true")
    modes.add_argument("--build-final", action="store_true")
    modes.add_argument("--validate-only", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--feedback-schema", type=Path, default=DEFAULT_FEEDBACK_SCHEMA)
    parser.add_argument(
        "--normalization-schema", type=Path, default=DEFAULT_NORMALIZATION_SCHEMA
    )
    parser.add_argument(
        "--comparison-schema", type=Path, default=DEFAULT_COMPARISON_SCHEMA
    )
    parser.add_argument("--realization-schema", type=Path, default=DEFAULT_REALIZATION_SCHEMA)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--targeted-plan", type=Path, default=DEFAULT_TARGETED_PLAN)
    parser.add_argument(
        "--targeted-packets", nargs=2, type=Path, default=DEFAULT_TARGETED_PACKETS
    )
    parser.add_argument(
        "--targeted-author-outputs",
        nargs=2,
        type=Path,
        default=DEFAULT_TARGETED_AUTHOR_OUTPUTS,
    )
    parser.add_argument("--targeted-combined", type=Path, default=DEFAULT_TARGETED_COMBINED)
    parser.add_argument(
        "--targeted-normalized", type=Path, default=DEFAULT_TARGETED_NORMALIZED
    )
    parser.add_argument(
        "--targeted-comparisons", type=Path, default=DEFAULT_TARGETED_COMPARISONS
    )
    parser.add_argument("--targeted-checks", type=Path, default=DEFAULT_TARGETED_CHECKS)
    parser.add_argument("--targeted-metrics", type=Path, default=DEFAULT_TARGETED_METRICS)
    parser.add_argument("--targeted-report", type=Path, default=DEFAULT_TARGETED_REPORT)
    parser.add_argument("--targeted-manifest", type=Path, default=DEFAULT_TARGETED_MANIFEST)
    parser.add_argument("--packets", nargs=2, type=Path, default=DEFAULT_PACKETS)
    parser.add_argument("--drafts", nargs=2, type=Path, default=DEFAULT_DRAFTS)
    parser.add_argument("--feedback", nargs=2, type=Path, default=DEFAULT_FEEDBACK)
    parser.add_argument("--finals", nargs=2, type=Path, default=DEFAULT_FINALS)
    parser.add_argument("--combined-drafts-output", type=Path, default=DEFAULT_COMBINED_DRAFTS)
    parser.add_argument("--draft-normalized-output", type=Path, default=DEFAULT_DRAFT_NORMALIZED)
    parser.add_argument("--combined-finals-output", type=Path, default=DEFAULT_COMBINED_FINALS)
    parser.add_argument("--final-normalized-output", type=Path, default=DEFAULT_FINAL_NORMALIZED)
    parser.add_argument("--comparisons-output", type=Path, default=DEFAULT_COMPARISONS)
    parser.add_argument("--checks-output", type=Path, default=DEFAULT_CHECKS)
    parser.add_argument("--metrics-output", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def _relative(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
    except ValueError as exc:
        raise TargetedInstrumentError(f"path outside repository: {path}") from exc
    if path.is_symlink() or ".." in relative.parts or ":" in relative.as_posix():
        raise TargetedInstrumentError(f"unsafe repository path: {relative.as_posix()}")
    return relative.as_posix()


def _binding(path: Path, *, record_count: int | None = None) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise TargetedInstrumentError(f"bound artifact missing or symlink: {_relative(path)}")
    result: dict[str, Any] = {
        "repository_relative_path": _relative(path),
        "sha256": sha256_file(path),
    }
    if record_count is not None:
        result["record_count"] = record_count
    return result


def _validator(path: Path):
    return targeted_v01._validator(path)


def _contract_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "feedback_schema": args.feedback_schema,
        "normalization_schema": args.normalization_schema,
        "comparison_schema": args.comparison_schema,
        "realization_schema": args.realization_schema,
        "protocol": args.protocol,
        "builder": Path(__file__).resolve(),
        "targeted_v0_1_builder": TARGETED_V01_TOOL,
        "normalizer_v0_1": NORMALIZER_V01_TOOL,
        "normalizer_v0_2": NORMALIZER_V02_TOOL,
        "crossed_author_validator": CROSSED_VALIDATOR_TOOL,
        "representative_graph_validator": REPRESENTATIVE_VALIDATOR_TOOL,
        "common_runtime": COMMON_RUNTIME,
        "tests": TEST_ARTIFACT,
    }


def _source_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "targeted_v0_1_plan": args.targeted_plan,
        "targeted_v0_1_packet_01": args.targeted_packets[0],
        "targeted_v0_1_packet_02": args.targeted_packets[1],
        "targeted_v0_1_author_output_01": args.targeted_author_outputs[0],
        "targeted_v0_1_author_output_02": args.targeted_author_outputs[1],
        "targeted_v0_1_combined_records": args.targeted_combined,
        "targeted_v0_1_normalized_candidates": args.targeted_normalized,
        "targeted_v0_1_question_comparisons": args.targeted_comparisons,
        "targeted_v0_1_checks": args.targeted_checks,
        "targeted_v0_1_metrics": args.targeted_metrics,
        "targeted_v0_1_report": args.targeted_report,
        "targeted_v0_1_run_manifest": args.targeted_manifest,
    }


def _all_planned_outputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "authoring_packet_01": args.packets[0],
        "authoring_packet_02": args.packets[1],
        "draft_output_01": args.drafts[0],
        "draft_output_02": args.drafts[1],
        "feedback_round_01_author_01": args.feedback[0],
        "feedback_round_01_author_02": args.feedback[1],
        "final_output_01": args.finals[0],
        "final_output_02": args.finals[1],
        "combined_draft_records": args.combined_drafts_output,
        "draft_normalized_candidates": args.draft_normalized_output,
        "combined_final_records": args.combined_finals_output,
        "final_normalized_candidates": args.final_normalized_output,
        "question_comparisons": args.comparisons_output,
        "checks": args.checks_output,
        "metrics": args.metrics_output,
        "report": args.report_output,
        "run_manifest": args.manifest_output,
    }


def _selection(args: argparse.Namespace) -> list[dict[str, Any]]:
    plan = read_json(args.targeted_plan)
    selection = plan.get("selection") if isinstance(plan, dict) else None
    if not isinstance(selection, list):
        raise TargetedInstrumentError("targeted v0.1 plan selection is missing")
    ids = tuple(item.get("question_id") for item in selection if isinstance(item, dict))
    if ids != EXPECTED_QUESTION_IDS:
        raise TargetedInstrumentError("targeted v0.1 six-question selection changed")
    return json.loads(json.dumps(selection))


def _validate_targeted_v01_source(args: argparse.Namespace) -> None:
    result = targeted_v01.validate_materialized(
        targeted_v01.parse_args(["--validate-only"])
    )
    if result.get("status") != "pass" or result.get("questions") != 6:
        raise TargetedInstrumentError("targeted v0.1 live validation failed")
    manifest = read_json(args.targeted_manifest)
    if manifest.get("validation_status") != "pass":
        raise TargetedInstrumentError("targeted v0.1 manifest did not pass")
    if manifest.get("metrics_summary", {}).get("decision") != (
        "REVISE_TARGETED_AUTHORING_INSTRUMENT_BEFORE_GROUNDING"
    ):
        raise TargetedInstrumentError("targeted v0.1 decision changed")
    expected_packets = [
        _binding(path, record_count=EXPECTED_QUESTIONS) for path in args.targeted_packets
    ]
    expected_outputs = [
        _binding(path, record_count=EXPECTED_QUESTIONS)
        for path in args.targeted_author_outputs
    ]
    if manifest.get("author_packets") != expected_packets:
        raise TargetedInstrumentError("targeted v0.1 packet bindings changed")
    if manifest.get("author_outputs") != expected_outputs:
        raise TargetedInstrumentError("targeted v0.1 author-output bindings changed")
    if len(list(iter_json_records(args.targeted_combined))) != 12:
        raise TargetedInstrumentError("targeted v0.1 no longer has twelve records")
    if len(list(iter_json_records(args.targeted_normalized))) != 14:
        raise TargetedInstrumentError("targeted v0.1 normalized count changed")
    _selection(args)


def _fixed_fields(source_packet: dict[str, Any], author_index: int) -> dict[str, Any]:
    fields = json.loads(json.dumps(source_packet["fixed_output_fields"]))
    author_id = AUTHOR_IDS[author_index]
    question_id = fields["question_id"]
    fields["realization_id"] = f"open_operator_realization_v0_1:{author_id}:{question_id}"
    fields["run_id"] = RUN_ID
    fields["producer_partition"] = AUTHOR_PRODUCERS[author_index]
    return fields


def build_packets(args: argparse.Namespace) -> list[list[dict[str, Any]]]:
    source_packets = list(iter_json_records(args.targeted_packets[0]))
    comparison_packets = list(iter_json_records(args.targeted_packets[1]))
    if [record["view"]["question_id"] for record in source_packets] != list(
        EXPECTED_QUESTION_IDS
    ):
        raise TargetedInstrumentError("targeted v0.1 packet order changed")
    if [record["view"] for record in source_packets] != [
        record["view"] for record in comparison_packets
    ]:
        raise TargetedInstrumentError("targeted v0.1 packets lost equal visibility")
    packets: list[list[dict[str, Any]]] = []
    for author_index, author_id in enumerate(AUTHOR_IDS):
        records = []
        for source in source_packets:
            records.append(
                {
                    "schema_version": "operator_equivalence_targeted_instrument_input_v0_2",
                    "run_id": RUN_ID,
                    "author_id": author_id,
                    "author_producer_partition": AUTHOR_PRODUCERS[author_index],
                    "selection_reason_hidden_from_author": True,
                    "prior_targeted_v0_1_run_hidden_from_author": True,
                    "feedback_contract": {
                        "draft_required_before_feedback": True,
                        "feedback_rounds": 1,
                        "feedback_candidate_local": True,
                        "feedback_reference_free": True,
                        "same_author_context_revises_own_draft": True,
                    },
                    "isolation_contract": {
                        "fresh_context_required": True,
                        "prior_e1_records_excluded": True,
                        "prior_e2_records_excluded": True,
                        "prior_author_outputs_excluded": True,
                        "normalization_and_comparison_artifacts_excluded": True,
                        "other_instrument_author_files_excluded": True,
                        "preserved_vocabularies_excluded": True,
                        "answers_traces_grounding_and_execution_excluded": True,
                    },
                    "fixed_output_fields": _fixed_fields(source, author_index),
                    "author_fill_fields": list(source["author_fill_fields"]),
                    "view": source["view"],
                }
            )
        packets.append(records)
    return packets


def build_freeze_plan(args: argparse.Namespace) -> dict[str, Any]:
    for path in _all_planned_outputs(args).values():
        if path.is_symlink() or path.exists():
            raise TargetedInstrumentError(
                f"planned output exists before plan freeze: {_relative(path)}"
            )
    for schema in (
        args.feedback_schema,
        args.normalization_schema,
        args.comparison_schema,
        args.realization_schema,
    ):
        _validator(schema)
    _validate_targeted_v01_source(args)
    implementation_commit = git_tracked_commit_identity(
        ROOT, _contract_inputs(args).values()
    )
    source_commit = git_tracked_commit_identity(ROOT, _source_inputs(args).values())
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "run_id": RUN_ID,
        "status": "frozen_before_instrument_packets_drafts_feedback_and_final_outputs",
        "implementation_commit": implementation_commit,
        "source_commit": source_commit,
        "contract_artifacts": {
            label: _binding(path) for label, path in _contract_inputs(args).items()
        },
        "source_artifacts": {
            label: _binding(path) for label, path in _source_inputs(args).items()
        },
        "selection": _selection(args),
        "selection_contract": {
            "question_ids_identical_to_targeted_v0_1": True,
            "expected_question_count": EXPECTED_QUESTIONS,
            "fresh_or_locked_question_ids_used": False,
            "all_selection_roles_e1_challenge": True,
        },
        "author_contract": {
            "authors": list(AUTHOR_IDS),
            "producer_partitions": list(AUTHOR_PRODUCERS),
            "fresh_contexts_required": True,
            "author_contexts_shared": False,
            "every_author_covers_every_question": True,
            "immutable_draft_precedes_feedback": True,
            "same_author_context_revises_own_draft": True,
            "prior_author_and_result_artifacts_visible": False,
            "other_instrument_author_files_visible": False,
        },
        "feedback_contract": {
            "rounds_per_author": 1,
            "all_six_question_feedback_records_delivered_together": True,
            "candidate_local_only": True,
            "reported_obligations": [
                "complete_target_node_coverage",
                "required_dependencies_preserved",
                "mapped_target_output_coverage_complete",
                "output_arity_preserved",
            ],
            "missing_node_edge_and_output_ids_may_be_reported": True,
            "reference_plan_or_preferred_candidate_revealed": False,
            "semantic_signature_or_eligibility_label_revealed": False,
            "answer_trace_grounding_or_execution_revealed": False,
            "drafts_preserved_immutable": True,
            "finals_may_retain_add_remove_or_revise_candidates": True,
        },
        "normalization_and_retention_contract": {
            "algorithm": "operator_equivalence_normalization_v0_2",
            "draft_and_final_provenance_distinct": True,
            "targeted_v0_1_records_are_reference_observations_not_gold": True,
            "all_targeted_v0_1_draft_and_final_candidate_profiles_retained": True,
            "no_candidate_preferred": True,
        },
        "frozen_decision_criteria": FROZEN_CRITERIA,
        "branch_precedence": [
            "technical_or_isolation_failure",
            "repeated_complete_coverage_failure",
            "semantic_stability_or_reference_compatibility_failure",
            "pass",
        ],
        "downstream_authorization": {
            "grounding_started": False,
            "grounding_authorized_by_this_plan": False,
            "successful_branch_requires_separate_narrowed_grounding_plan": True,
            "repeated_coverage_failure_requires_human_review_approval": True,
        },
        "planned_outputs": {
            label: {"repository_relative_path": _relative(path)}
            for label, path in _all_planned_outputs(args).items()
        },
        "output_absence_at_freeze": {
            "verified": True,
            "absent_labels": list(_all_planned_outputs(args)),
        },
    }


def _validate_plan(args: argparse.Namespace) -> dict[str, Any]:
    plan = read_json(args.plan)
    if not isinstance(plan, dict) or plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise TargetedInstrumentError("instrument v0.2 plan version mismatch")
    if plan.get("status") != (
        "frozen_before_instrument_packets_drafts_feedback_and_final_outputs"
    ):
        raise TargetedInstrumentError("instrument plan was not frozen before outputs")
    _validate_targeted_v01_source(args)
    for label, path in _contract_inputs(args).items():
        if plan.get("contract_artifacts", {}).get(label) != _binding(path):
            raise TargetedInstrumentError(f"plan contract binding mismatch: {label}")
    for label, path in _source_inputs(args).items():
        if plan.get("source_artifacts", {}).get(label) != _binding(path):
            raise TargetedInstrumentError(f"plan source binding mismatch: {label}")
    if plan.get("selection") != _selection(args):
        raise TargetedInstrumentError("instrument selection changed")
    if plan.get("frozen_decision_criteria") != FROZEN_CRITERIA:
        raise TargetedInstrumentError("instrument frozen criteria changed")
    if plan.get("author_contract", {}).get("authors") != list(AUTHOR_IDS):
        raise TargetedInstrumentError("instrument author identities changed")
    for label, path in _all_planned_outputs(args).items():
        expected = {"repository_relative_path": _relative(path)}
        if plan.get("planned_outputs", {}).get(label) != expected:
            raise TargetedInstrumentError(f"plan output binding mismatch: {label}")
    if plan.get("output_absence_at_freeze") != {
        "verified": True,
        "absent_labels": list(_all_planned_outputs(args)),
    }:
        raise TargetedInstrumentError("plan output-absence proof changed")
    return plan


def materialize_packet_outputs(
    args: argparse.Namespace,
) -> dict[str, tuple[Path, bytes]]:
    _validate_plan(args)
    return {
        f"authoring_packet_{index:02d}": (path, jsonl_file_bytes(records))
        for index, (path, records) in enumerate(zip(args.packets, build_packets(args)), 1)
    }


def validate_packets(args: argparse.Namespace) -> dict[str, Any]:
    expected = materialize_packet_outputs(args)
    mismatches = [
        label
        for label, (path, payload) in expected.items()
        if not path.is_file() or path.read_bytes() != payload
    ]
    if mismatches:
        raise TargetedInstrumentError(f"materialized packets differ: {mismatches}")
    return {
        "status": "pass",
        "mode": "validate_packets_only",
        "questions": EXPECTED_QUESTIONS,
        "authors": len(AUTHOR_IDS),
    }


def _load_stage_records(
    args: argparse.Namespace, paths: Iterable[Path], stage: str
) -> tuple[list[list[dict[str, Any]]], list[list[dict[str, Any]]]]:
    validate_packets(args)
    packets = build_packets(args)
    validator = _validator(args.realization_schema)
    all_records: list[list[dict[str, Any]]] = []
    for index, (path, author_packets) in enumerate(zip(paths, packets), 1):
        if path.is_symlink() or not path.is_file():
            raise TargetedInstrumentError(f"{stage} output missing: {_relative(path)}")
        records = list(iter_json_records(path))
        expected_ids = [packet["view"]["question_id"] for packet in author_packets]
        if [record.get("question_id") for record in records] != expected_ids:
            raise TargetedInstrumentError(f"{stage} author {index} question order changed")
        for record, packet in zip(records, author_packets):
            errors = targeted_v01._targeted_author_record_errors(
                record, packet, validator
            )
            if errors:
                raise TargetedInstrumentError(
                    f"{stage} author {index} record {record.get('question_id')} invalid: "
                    + " | ".join(errors[:20])
                )
        if path.read_bytes() != jsonl_file_bytes(records):
            raise TargetedInstrumentError(f"{stage} author {index} output is not canonical JSONL")
        all_records.append(records)
    return all_records, packets


def _dependency_records(edges: Iterable[tuple[str, str]]) -> list[dict[str, str]]:
    return [
        {"source_node_id": source, "target_node_id": target}
        for source, target in sorted(edges)
    ]


def candidate_local_feedback(
    record: dict[str, Any], candidate: dict[str, Any], view: dict[str, Any]
) -> dict[str, Any]:
    projection = normalizer_v01.build_structural_projection(record, candidate, view)
    _, facts, _ = normalizer_v02._semantic_profile(projection)
    target = projection["target_semantic_topology"]
    operator = projection["operator_topology"]
    complete_nodes = (
        projection["coverage_status"] == "complete_for_target_variant"
        and not facts["missing"]
    )
    dependencies = not facts["missing_required"]
    mapped_outputs = not facts["missing_outputs"]
    output_arity = (
        len(operator["output_node_ids"]) == len(facts["target_outputs"])
        and len(facts["semantic_operator_outputs"]) == len(facts["target_outputs"])
        and not facts["unmapped_operator_outputs"]
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "target_backbone_variant_id": candidate["target_backbone_variant_id"],
        "complete_target_node_coverage": complete_nodes,
        "missing_target_node_ids": sorted(facts["missing"]),
        "required_dependencies_preserved": dependencies,
        "missing_required_dependencies": _dependency_records(
            facts["missing_required"]
        ),
        "mapped_target_output_coverage_complete": mapped_outputs,
        "missing_target_output_node_ids": sorted(facts["missing_outputs"]),
        "output_arity_preserved": output_arity,
        "target_output_arity": len(target["output_node_ids"]),
        "operator_output_arity": len(operator["output_node_ids"]),
        "unmapped_operator_output_node_ids": sorted(
            facts["unmapped_operator_outputs"]
        ),
        "all_four_obligations_preserved": all(
            [complete_nodes, dependencies, mapped_outputs, output_arity]
        ),
    }


def _recursive_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        result = set(value)
        for child in value.values():
            result.update(_recursive_keys(child))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for child in value:
            result.update(_recursive_keys(child))
        return result
    return set()


def feedback_leakage_errors(feedback: dict[str, Any]) -> list[str]:
    errors = [
        f"forbidden feedback key: {key}"
        for key in sorted(_recursive_keys(feedback) & FORBIDDEN_FEEDBACK_KEYS)
    ]
    for candidate in feedback.get("candidates", []):
        serialized = json.dumps(candidate, ensure_ascii=False, sort_keys=True)
        for pattern in FORBIDDEN_FEEDBACK_VALUE_PATTERNS:
            if pattern.search(serialized):
                errors.append(f"forbidden feedback value pattern: {pattern.pattern}")
    return errors


def build_feedback_records(
    args: argparse.Namespace,
) -> tuple[list[list[dict[str, Any]]], list[list[dict[str, Any]]]]:
    drafts, packets = _load_stage_records(args, args.drafts, "draft")
    validator = _validator(args.feedback_schema)
    all_feedback: list[list[dict[str, Any]]] = []
    for author_index, (records, author_packets) in enumerate(zip(drafts, packets)):
        packet_by_question = {
            packet["view"]["question_id"]: packet for packet in author_packets
        }
        feedback_records = []
        for record in records:
            view = packet_by_question[record["question_id"]]["view"]
            candidates = [
                candidate_local_feedback(record, candidate, view)
                for candidate in record["realization_candidates"]
            ]
            feedback = {
                "schema_version": "operator_equivalence_targeted_instrument_feedback_v0_2",
                "run_id": RUN_ID,
                "author_id": AUTHOR_IDS[author_index],
                "question_id": record["question_id"],
                "feedback_round": 1,
                "source_draft_record_sha256": canonical_json_sha256(record),
                "scope": (
                    "candidate_local_target_node_required_dependency_"
                    "target_output_and_output_arity_only"
                ),
                "candidates": candidates,
                "record_has_candidate_preserving_all_four_obligations": any(
                    candidate["all_four_obligations_preserved"]
                    for candidate in candidates
                ),
                "reference_or_preference_content_included": False,
            }
            errors = sorted(
                validator.iter_errors(feedback), key=lambda error: list(error.path)
            )
            if errors:
                raise TargetedInstrumentError(
                    f"feedback schema failure: {errors[0].message}"
                )
            leakage = feedback_leakage_errors(feedback)
            if leakage:
                raise TargetedInstrumentError("feedback leakage: " + " | ".join(leakage))
            feedback_records.append(feedback)
        all_feedback.append(feedback_records)
    return all_feedback, drafts


def feedback_outputs(args: argparse.Namespace) -> dict[str, tuple[Path, bytes]]:
    _validate_plan(args)
    all_feedback, _ = build_feedback_records(args)
    return {
        f"feedback_round_01_author_{index:02d}": (path, jsonl_file_bytes(records))
        for index, (path, records) in enumerate(zip(args.feedback, all_feedback), 1)
    }


def validate_feedback(args: argparse.Namespace) -> dict[str, Any]:
    expected = feedback_outputs(args)
    mismatches = [
        label
        for label, (path, payload) in expected.items()
        if not path.is_file() or path.read_bytes() != payload
    ]
    if mismatches:
        raise TargetedInstrumentError(f"materialized feedback differs: {mismatches}")
    return {
        "status": "pass",
        "mode": "validate_feedback_only",
        "feedback_records": EXPECTED_QUESTIONS * len(AUTHOR_IDS),
        "rounds_per_author": 1,
    }


def _normalize_candidate(
    record: dict[str, Any],
    candidate: dict[str, Any],
    view: dict[str, Any],
    author_id: str,
    source_stage: str,
) -> dict[str, Any]:
    projection = normalizer_v01.build_structural_projection(record, candidate, view)
    legacy = normalizer_v01.normalize_projection(projection)
    source_candidate_key = (
        f"instrument:{source_stage}:{author_id}:{record['question_id']}:"
        f"{candidate['candidate_id']}"
    )
    source_record_sha256 = canonical_json_sha256(record)
    normalized = normalizer_v02.normalize_projection_v0_2(
        projection,
        {
            "source_candidate_key": source_candidate_key,
            "source_cohort": "targeted_instrument_reauthor",
            "source_author_id": author_id,
            "source_v0_1_normalization_sha256": source_record_sha256,
            "source_v0_1_equivalence_status": legacy["equivalence_assessment"][
                "status"
            ],
            "source_projection_sha256": canonical_json_sha256(projection),
        },
    )
    return {
        "schema_version": "operator_equivalence_targeted_instrument_normalization_v0_2",
        "normalization_algorithm_version": "operator_equivalence_normalization_v0_2",
        "normalization_id": (
            "operator_equivalence_targeted_instrument_normalization_v0_2:"
            f"{source_stage}:{author_id}:{record['question_id']}:{candidate['candidate_id']}"
        ),
        "source_candidate_key": source_candidate_key,
        "source_stage": source_stage,
        "source_cohort": "targeted_instrument_reauthor",
        "source_author_id": author_id,
        "question_id": normalized["question_id"],
        "family_id": normalized["family_id"],
        "producer_partition": normalized["producer_partition"],
        "candidate_id": normalized["candidate_id"],
        "target_backbone_variant_id": normalized["target_backbone_variant_id"],
        "source_author_record_sha256": source_record_sha256,
        "legacy_v0_1_equivalence_status": legacy["equivalence_assessment"]["status"],
        "source_projection_sha256": normalized["source_projection_sha256"],
        "candidate_semantic_profile": normalized["candidate_semantic_profile"],
        "equivalence_eligibility": normalized["equivalence_eligibility"],
        "factorized_environment_adapter": normalized["factorized_environment_adapter"],
        "reversibility_ledger": normalized["reversibility_ledger"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def _record_sets(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise TargetedInstrumentError("cannot summarize empty author/question records")
    return normalizer_v02._record_sets(records)


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 1.0


def _profile_inventory(
    staged_records: Iterable[tuple[str, Iterable[dict[str, Any]]]],
) -> tuple[list[dict[str, Any]], int]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    expected_keys: set[str] = set()
    for source_stage, records in staged_records:
        for record in records:
            key = record["source_candidate_key"]
            if key in expected_keys:
                raise TargetedInstrumentError(f"duplicate candidate observation: {key}")
            expected_keys.add(key)
            grouped[record["candidate_semantic_profile"]["signature_sha256"]].append(
                {
                    "source_stage": source_stage,
                    "author_id": record["source_author_id"],
                    "source_candidate_key": key,
                    "eligibility_status": record["equivalence_eligibility"]["status"],
                }
            )
    inventory = []
    observed_keys: set[str] = set()
    status_order = {"full_eligible": 0, "provisional_only": 1, "ineligible": 2}
    for signature, observations in sorted(grouped.items()):
        observations.sort(
            key=lambda item: (
                item["source_stage"],
                item["author_id"],
                item["source_candidate_key"],
            )
        )
        observed_keys.update(item["source_candidate_key"] for item in observations)
        inventory.append(
            {
                "signature_sha256": signature,
                "eligibility_statuses": sorted(
                    {item["eligibility_status"] for item in observations},
                    key=status_order.__getitem__,
                ),
                "observations": observations,
            }
        )
    return inventory, len(expected_keys ^ observed_keys)


def _reference_grouped(args: argparse.Namespace) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in iter_json_records(args.targeted_normalized):
        grouped[(record["source_author_id"], record["question_id"])].append(record)
    for author_id in REFERENCE_AUTHOR_IDS:
        for question_id in EXPECTED_QUESTION_IDS:
            if not grouped[(author_id, question_id)]:
                raise TargetedInstrumentError(
                    f"targeted v0.1 reference missing: {author_id}/{question_id}"
                )
    return grouped


def _decision(
    counts: dict[str, Any], rates: dict[str, float], criteria: dict[str, Any]
) -> tuple[str, dict[str, bool]]:
    technical = all(
        [
            counts["invalid_draft_records"] <= criteria["invalid_draft_record_count_max"],
            counts["invalid_final_records"] <= criteria["invalid_final_record_count_max"],
            counts["technical_loss"] <= criteria["technical_loss_count_max"],
            counts["feedback_records"] == criteria["feedback_record_count"],
            counts["feedback_reference_leakage"]
            <= criteria["feedback_reference_leakage_count_max"],
            counts["feedback_binding_errors"]
            <= criteria["feedback_binding_error_count_max"],
            counts["feedback_rounds_per_author_min"]
            == criteria["feedback_rounds_per_author"],
            counts["feedback_rounds_per_author_max"]
            == criteria["feedback_rounds_per_author"],
            counts["eligible_set_contamination"]
            <= criteria["eligible_set_contamination_count_max"],
            counts["unclassified_adapter_candidates"]
            <= criteria["unclassified_adapter_candidate_count_max"],
            counts["preferred_candidates"] <= criteria["preferred_candidate_count_max"],
            counts["fresh_question_ids"] <= criteria["fresh_question_id_count_max"],
            counts["profile_inventory_loss"]
            <= criteria["profile_inventory_loss_count_max"],
        ]
    )
    coverage = all(
        [
            counts["final_candidate_local_author_question_coverage"]
            >= criteria["final_candidate_local_author_question_coverage_min"],
            counts["full_eligible_author_question_coverage"]
            >= criteria["full_eligible_author_question_coverage_min"],
        ]
    )
    semantic = all(
        [
            counts["nonempty_final_author_semantic_intersections"]
            >= criteria["nonempty_final_author_semantic_intersection_count_min"],
            counts["final_author_semantic_exact_matches"]
            >= criteria["final_author_semantic_exact_match_count_min"],
            rates["mean_final_author_semantic_jaccard"]
            >= criteria["mean_final_author_semantic_jaccard_min"],
            counts["targeted_v0_1_reference_compatible_author_questions"]
            >= criteria[
                "targeted_v0_1_reference_compatible_author_question_count_min"
            ],
        ]
    )
    if not technical:
        decision = criteria["branch_on_technical_failure"]
    elif not coverage:
        decision = criteria["branch_on_repeated_coverage_failure"]
    elif not semantic:
        decision = criteria["branch_on_semantic_failure"]
    else:
        decision = criteria["branch_on_pass"]
    return decision, {
        "technical_and_isolation_contract_passed": technical,
        "repeated_complete_coverage_gate_passed": coverage,
        "semantic_stability_and_reference_compatibility_passed": semantic,
        "all_criteria_passed": technical and coverage and semantic,
    }


def build_final_artifacts(
    args: argparse.Namespace,
) -> dict[str, tuple[Path, bytes]]:
    plan = _validate_plan(args)
    validate_feedback(args)
    draft_records, packets = _load_stage_records(args, args.drafts, "draft")
    final_records, _ = _load_stage_records(args, args.finals, "final")
    feedback_records = [
        list(iter_json_records(path)) for path in args.feedback
    ]
    normalization_validator = _validator(args.normalization_schema)
    comparison_validator = _validator(args.comparison_schema)

    normalized_by_stage: dict[str, list[dict[str, Any]]] = {
        "draft": [],
        "final": [],
    }
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    final_local_complete: dict[tuple[str, str], bool] = {}
    checks: list[dict[str, Any]] = []
    for author_index, author_id in enumerate(AUTHOR_IDS):
        packet_by_question = {
            packet["view"]["question_id"]: packet
            for packet in packets[author_index]
        }
        feedback_by_question = {
            record["question_id"]: record for record in feedback_records[author_index]
        }
        for stage, records in (
            ("draft", draft_records[author_index]),
            ("final", final_records[author_index]),
        ):
            for record in records:
                view = packet_by_question[record["question_id"]]["view"]
                local = [
                    candidate_local_feedback(record, candidate, view)
                    for candidate in record["realization_candidates"]
                ]
                if stage == "final":
                    final_local_complete[(author_id, record["question_id"])] = any(
                        candidate["all_four_obligations_preserved"]
                        for candidate in local
                    )
                for candidate in record["realization_candidates"]:
                    normalized = _normalize_candidate(
                        record, candidate, view, author_id, stage
                    )
                    errors = sorted(
                        normalization_validator.iter_errors(normalized),
                        key=lambda error: list(error.path),
                    )
                    if errors:
                        raise TargetedInstrumentError(
                            f"{stage} normalization schema failure: {errors[0].message}"
                        )
                    normalized_by_stage[stage].append(normalized)
                    grouped[(stage, author_id, record["question_id"])].append(
                        normalized
                    )
        for draft, final in zip(
            draft_records[author_index], final_records[author_index]
        ):
            feedback = feedback_by_question[draft["question_id"]]
            checks.append(
                {
                    "schema_version": "operator_equivalence_targeted_instrument_check_v0_2",
                    "author_id": author_id,
                    "question_id": draft["question_id"],
                    "status": "pass",
                    "draft_record_sha256": canonical_json_sha256(draft),
                    "feedback_record_sha256": canonical_json_sha256(feedback),
                    "final_record_sha256": canonical_json_sha256(final),
                    "feedback_rounds_delivered": 1,
                    "feedback_bound_to_draft": feedback[
                        "source_draft_record_sha256"
                    ]
                    == canonical_json_sha256(draft),
                    "feedback_reference_leakage_count": len(
                        feedback_leakage_errors(feedback)
                    ),
                    "draft_candidate_count": len(draft["realization_candidates"]),
                    "final_candidate_count": len(final["realization_candidates"]),
                    "final_has_candidate_preserving_all_four_obligations": (
                        final_local_complete[(author_id, final["question_id"])]
                    ),
                }
            )

    reference_grouped = _reference_grouped(args)
    selection_by_id = {item["question_id"]: item for item in plan["selection"]}
    comparisons: list[dict[str, Any]] = []
    for question_id in EXPECTED_QUESTION_IDS:
        final_results = []
        final_sets: list[set[str]] = []
        final_for_question: list[dict[str, Any]] = []
        draft_for_question: list[dict[str, Any]] = []
        for author_id in AUTHOR_IDS:
            final_items = grouped[("final", author_id, question_id)]
            result = _record_sets(final_items)
            final_results.append({"author_id": author_id, **result})
            final_sets.append(set(result["full_eligible_semantic_set"]))
            final_for_question.extend(final_items)
            draft_for_question.extend(grouped[("draft", author_id, question_id)])

        reference_results = []
        reference_union: set[str] = set()
        reference_for_question: list[dict[str, Any]] = []
        for author_id in REFERENCE_AUTHOR_IDS:
            items = reference_grouped[(author_id, question_id)]
            result = _record_sets(items)
            reference_results.append({"author_id": author_id, **result})
            reference_union.update(result["full_eligible_semantic_set"])
            reference_for_question.extend(items)
        compatibility = [
            {
                "author_id": author_id,
                "intersects_targeted_v0_1_union": bool(values & reference_union),
                "semantic_intersection": sorted(values & reference_union),
            }
            for author_id, values in zip(AUTHOR_IDS, final_sets)
        ]
        inventory, loss = _profile_inventory(
            [
                ("targeted_v0_1_reference", reference_for_question),
                ("instrument_draft", draft_for_question),
                ("instrument_final", final_for_question),
            ]
        )
        comparison = {
            "schema_version": "operator_equivalence_targeted_instrument_comparison_v0_2",
            "question_id": question_id,
            "selection_role": selection_by_id[question_id]["selection_role"],
            "final_author_results": final_results,
            "targeted_v0_1_reference_results": reference_results,
            "final_author_full_eligible_semantic_set_exact_match": (
                final_sets[0] == final_sets[1]
            ),
            "final_author_full_eligible_semantic_set_jaccard": _jaccard(
                final_sets[0], final_sets[1]
            ),
            "final_author_full_eligible_semantic_intersection": sorted(
                final_sets[0] & final_sets[1]
            ),
            "targeted_v0_1_full_eligible_semantic_union": sorted(reference_union),
            "final_full_eligible_semantic_union": sorted(
                final_sets[0] | final_sets[1]
            ),
            "reference_compatibility": compatibility,
            "all_final_authors_have_full_eligible_candidate": all(final_sets),
            "all_final_authors_have_candidate_local_complete_candidate": all(
                final_local_complete[(author_id, question_id)]
                for author_id in AUTHOR_IDS
            ),
            "observed_profile_inventory": inventory,
            "profile_inventory_loss_count": loss,
            "preferred_candidate_observed": False,
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
        errors = sorted(
            comparison_validator.iter_errors(comparison),
            key=lambda error: list(error.path),
        )
        if errors:
            raise TargetedInstrumentError(
                f"comparison schema failure for {question_id}: {errors[0].message}"
            )
        comparisons.append(comparison)

    final_status = Counter(
        record["equivalence_eligibility"]["status"]
        for record in normalized_by_stage["final"]
    )
    expected_candidates = sum(
        len(record["realization_candidates"])
        for records in draft_records + final_records
        for record in records
    )
    prior_ids = {item["question_id"] for item in _selection(args)}
    feedback_counts = Counter(
        record["author_id"]
        for records in feedback_records
        for record in records
    )
    counts = {
        "questions": EXPECTED_QUESTIONS,
        "authors": len(AUTHOR_IDS),
        "draft_records": sum(len(records) for records in draft_records),
        "final_records": sum(len(records) for records in final_records),
        "draft_candidates": len(normalized_by_stage["draft"]),
        "final_candidates": len(normalized_by_stage["final"]),
        "final_eligibility_status": dict(sorted(final_status.items())),
        "invalid_draft_records": 0,
        "invalid_final_records": 0,
        "technical_loss": abs(
            expected_candidates
            - len(normalized_by_stage["draft"])
            - len(normalized_by_stage["final"])
        ),
        "feedback_records": sum(feedback_counts.values()),
        "feedback_reference_leakage": sum(
            len(feedback_leakage_errors(record))
            for records in feedback_records
            for record in records
        ),
        "feedback_binding_errors": sum(
            record["source_draft_record_sha256"]
            != canonical_json_sha256(draft)
            for records, drafts in zip(feedback_records, draft_records)
            for record, draft in zip(records, drafts)
        ),
        "feedback_rounds_per_author_min": min(
            len({record["feedback_round"] for record in records})
            for records in feedback_records
        ),
        "feedback_rounds_per_author_max": max(
            len({record["feedback_round"] for record in records})
            for records in feedback_records
        ),
        "eligible_set_contamination": sum(
            result["eligible_set_contamination_count"]
            for comparison in comparisons
            for result in comparison["final_author_results"]
        ),
        "unclassified_adapter_candidates": sum(
            not record["factorized_environment_adapter"]["classification_coverage"][
                "all_source_elements_classified"
            ]
            for record in normalized_by_stage["draft"]
            + normalized_by_stage["final"]
        ),
        "preferred_candidates": sum(
            record["preferred_candidate_id"] is not None
            for records in draft_records + final_records
            for record in records
        ),
        "fresh_question_ids": len(set(EXPECTED_QUESTION_IDS) - prior_ids),
        "profile_inventory_loss": sum(
            comparison["profile_inventory_loss_count"] for comparison in comparisons
        ),
        "final_candidate_local_author_question_coverage": sum(
            final_local_complete.values()
        ),
        "full_eligible_author_question_coverage": sum(
            result["full_eligible_candidate_count"] > 0
            for comparison in comparisons
            for result in comparison["final_author_results"]
        ),
        "nonempty_final_author_semantic_intersections": sum(
            bool(comparison["final_author_full_eligible_semantic_intersection"])
            for comparison in comparisons
        ),
        "final_author_semantic_exact_matches": sum(
            comparison["final_author_full_eligible_semantic_set_exact_match"]
            for comparison in comparisons
        ),
        "targeted_v0_1_reference_compatible_author_questions": sum(
            item["intersects_targeted_v0_1_union"]
            for comparison in comparisons
            for item in comparison["reference_compatibility"]
        ),
        "distinct_observed_semantic_profiles": len(
            {
                item["signature_sha256"]
                for comparison in comparisons
                for item in comparison["observed_profile_inventory"]
            }
        ),
    }
    rates = {
        "final_candidate_local_author_question_coverage": (
            counts["final_candidate_local_author_question_coverage"] / 12
        ),
        "full_eligible_author_question_coverage": (
            counts["full_eligible_author_question_coverage"] / 12
        ),
        "final_author_semantic_exact_match": (
            counts["final_author_semantic_exact_matches"] / 6
        ),
        "mean_final_author_semantic_jaccard": sum(
            comparison["final_author_full_eligible_semantic_set_jaccard"]
            for comparison in comparisons
        )
        / 6,
        "targeted_v0_1_reference_compatible_author_question": (
            counts["targeted_v0_1_reference_compatible_author_questions"] / 12
        ),
    }
    decision, criteria_results = _decision(
        counts, rates, plan["frozen_decision_criteria"]
    )
    metrics = {
        "schema_version": "operator_equivalence_targeted_instrument_metrics_v0_2",
        "run_id": RUN_ID,
        "counts": counts,
        "rates": rates,
        "frozen_criteria": plan["frozen_decision_criteria"],
        "criteria_results": criteria_results,
        "decision": decision,
        "fresh_or_locked_question_ids_used": False,
        "grounding_started": False,
        "separate_narrowed_grounding_plan_may_be_frozen_next": criteria_results[
            "all_criteria_passed"
        ],
        "human_evidence_created": False,
        "gold_claimed": False,
    }
    report = "\n".join(
        [
            "# Targeted authoring-instrument revision v0.2",
            "",
            "Two fresh-context AI authors drafted the same six already exposed",
            "questions, received one deterministic candidate-local completeness",
            "feedback round, and submitted final records. Drafts, feedback, and",
            "finals are retained as distinct observations. No reference plan or",
            "normalization result was visible during authoring.",
            "",
            "## Results",
            "",
            f"- draft/final records: {counts['draft_records']}/{counts['final_records']}",
            f"- draft/final candidates: {counts['draft_candidates']}/{counts['final_candidates']}",
            f"- feedback records: {counts['feedback_records']}",
            (
                "- final candidate-local complete author/questions: "
                f"{counts['final_candidate_local_author_question_coverage']}/12"
            ),
            (
                "- final full-eligible author/questions: "
                f"{counts['full_eligible_author_question_coverage']}/12"
            ),
            (
                "- nonempty final-author semantic intersections: "
                f"{counts['nonempty_final_author_semantic_intersections']}/6"
            ),
            (
                "- final-author semantic-set exact matches: "
                f"{counts['final_author_semantic_exact_matches']}/6"
            ),
            (
                "- mean final-author semantic-set Jaccard: "
                f"{rates['mean_final_author_semantic_jaccard']:.6f}"
            ),
            (
                "- targeted-v0.1-compatible author/questions: "
                f"{counts['targeted_v0_1_reference_compatible_author_questions']}/12"
            ),
            f"- final eligibility: {json.dumps(counts['final_eligibility_status'], sort_keys=True)}",
            f"- profile inventory loss: {counts['profile_inventory_loss']}",
            "",
            "## Frozen branch result",
            "",
            f"`{decision}`",
            "",
            "Grounding, execution, answer recovery, human review, preference",
            "selection, and gold annotation were not performed. A passing result",
            "authorizes only a separately frozen narrowed grounding plan.",
            "",
        ]
    )
    combined_drafts = [record for records in draft_records for record in records]
    combined_finals = [record for records in final_records for record in records]
    preliminary = {
        "combined_draft_records": (
            args.combined_drafts_output,
            jsonl_file_bytes(combined_drafts),
        ),
        "draft_normalized_candidates": (
            args.draft_normalized_output,
            jsonl_file_bytes(normalized_by_stage["draft"]),
        ),
        "combined_final_records": (
            args.combined_finals_output,
            jsonl_file_bytes(combined_finals),
        ),
        "final_normalized_candidates": (
            args.final_normalized_output,
            jsonl_file_bytes(normalized_by_stage["final"]),
        ),
        "question_comparisons": (
            args.comparisons_output,
            jsonl_file_bytes(comparisons),
        ),
        "checks": (args.checks_output, jsonl_file_bytes(checks)),
        "metrics": (args.metrics_output, json_file_bytes(metrics)),
        "report": (args.report_output, report.encode("utf-8")),
    }
    manifest = {
        "schema_version": "operator_equivalence_targeted_instrument_run_manifest_v0_2",
        "run_id": RUN_ID,
        "plan": _binding(args.plan),
        "implementation_commit": plan["implementation_commit"],
        "source_commit": plan["source_commit"],
        "author_packets": [
            _binding(path, record_count=6) for path in args.packets
        ],
        "draft_outputs": [
            _binding(path, record_count=6) for path in args.drafts
        ],
        "feedback_outputs": [
            _binding(path, record_count=6) for path in args.feedback
        ],
        "final_outputs": [
            _binding(path, record_count=6) for path in args.finals
        ],
        "targeted_v0_1_run_manifest": _binding(args.targeted_manifest),
        "outputs": {
            label: {
                "repository_relative_path": _relative(path),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for label, (path, payload) in preliminary.items()
        },
        "metrics_summary": metrics,
        "validation_status": "pass",
    }
    return {
        **preliminary,
        "run_manifest": (args.manifest_output, json_file_bytes(manifest)),
    }


def validate_materialized(args: argparse.Namespace) -> dict[str, Any]:
    expected = build_final_artifacts(args)
    mismatches = [
        label
        for label, (path, payload) in expected.items()
        if not path.is_file() or path.read_bytes() != payload
    ]
    if mismatches:
        raise TargetedInstrumentError(f"materialized final artifacts differ: {mismatches}")
    metrics = read_json(args.metrics_output)
    return {
        "status": "pass",
        "mode": "validate_only",
        "questions": metrics["counts"]["questions"],
        "authors": metrics["counts"]["authors"],
        "decision": metrics["decision"],
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.freeze_plan:
            plan = build_freeze_plan(args)
            write_output_batch(
                {"plan": (args.plan, json_file_bytes(plan))},
                overwrite=args.overwrite,
            )
            print(json.dumps({"status": "frozen", "plan": _relative(args.plan)}, sort_keys=True))
        elif args.validate_plan_only:
            plan = _validate_plan(args)
            print(json.dumps({"status": "pass", "mode": "validate_plan_only", "questions": len(plan["selection"])}, sort_keys=True))
        elif args.materialize_packets:
            statuses = write_output_batch(
                materialize_packet_outputs(args), overwrite=args.overwrite
            )
            print(json.dumps({"status": "packets_materialized", "outputs": statuses}, sort_keys=True))
        elif args.validate_packets_only:
            print(json.dumps(validate_packets(args), sort_keys=True))
        elif args.check_drafts:
            statuses = write_output_batch(feedback_outputs(args), overwrite=args.overwrite)
            print(json.dumps({"status": "feedback_materialized", "outputs": statuses}, sort_keys=True))
        elif args.validate_feedback_only:
            print(json.dumps(validate_feedback(args), sort_keys=True))
        elif args.build_final:
            statuses = write_output_batch(
                build_final_artifacts(args), overwrite=args.overwrite
            )
            print(json.dumps({"status": "final_built", "outputs": statuses}, sort_keys=True))
        else:
            print(json.dumps(validate_materialized(args), sort_keys=True))
    except (
        TargetedInstrumentError,
        ValueError,
        OSError,
        KeyError,
        TypeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
