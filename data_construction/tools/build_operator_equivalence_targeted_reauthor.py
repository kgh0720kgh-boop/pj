#!/usr/bin/env python3
"""Freeze, packetize, and evaluate the six-question targeted re-authoring run.

The run re-authors only the six already exposed E1-challenge questions whose
two crossed-author full-eligible semantic sets differed under normalization
v0.2.  New authoring contexts receive only reconstructed sanitized E2 views.
Prior author records and normalization outputs are bound evaluation inputs,
never authoring inputs.  This tool performs no grounding or answer recovery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource

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


TOOL_VERSION = "operator_equivalence_targeted_reauthor_builder_v0_1"
PLAN_SCHEMA_VERSION = "operator_equivalence_targeted_reauthor_plan_v0_1"
PLAN_ID = "hybridqa_operator_equivalence_targeted_reauthor_plan_v0_1"
RUN_ID = "hybridqa_operator_equivalence_targeted_reauthor_v0_1_run_001"
AUTHOR_IDS = ("targeted_author_01", "targeted_author_02")
AUTHOR_PRODUCERS = ("e2_author_partition_07", "e2_author_partition_08")
REFERENCE_AUTHOR_IDS = ("crossed_author_01", "crossed_author_02")
EXPECTED_QUESTION_IDS = (
    "0d48bffa70ef4acf",
    "cc681cfdba9badd5",
    "1e2e4e4f72a64bbf",
    "1e674ae4b655c1a1",
    "1ca8ffcd3e20e498",
    "ba563b015b09bf21",
)
EXPECTED_QUESTIONS = len(EXPECTED_QUESTION_IDS)

ROOT = Path(__file__).resolve().parents[2]
SCALE_BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
CONTRACTS = SCALE_BASE / "contracts"
PROMPTS = SCALE_BASE / "prompts"
SOURCE_BASE = SCALE_BASE / "representative_environment_realization_v0_1"
CROSSED_BASE = SCALE_BASE / "operator_equivalence_crossed_author_sensitivity_v0_1"
NORMALIZATION_V02_BASE = SCALE_BASE / "operator_equivalence_normalization_v0_2"
RUN_BASE = SCALE_BASE / "operator_equivalence_targeted_reauthor_v0_1"

DEFAULT_PLAN = CONTRACTS / "operator_equivalence_targeted_reauthor_plan_v0_1.json"
DEFAULT_COMPARISON_SCHEMA = (
    CONTRACTS / "operator_equivalence_targeted_reauthor_comparison_schema_v0_1.json"
)
DEFAULT_TARGETED_NORMALIZATION_SCHEMA = (
    CONTRACTS
    / "operator_equivalence_targeted_reauthor_normalization_schema_v0_1.json"
)
DEFAULT_REALIZATION_SCHEMA = CONTRACTS / "open_operator_realization_schema_v0_1.json"
DEFAULT_PROTOCOL = PROMPTS / "operator_equivalence_targeted_reauthor_v0_1.md"
DEFAULT_VIEWS = SOURCE_BASE / "inputs/environment_views.jsonl"
DEFAULT_E2_PACKETS = tuple(
    SOURCE_BASE / f"stage_e2/authoring_packets/partition_{index:02d}.jsonl"
    for index in range(1, 5)
)
DEFAULT_V02_MANIFEST = NORMALIZATION_V02_BASE / "run_manifest.json"
DEFAULT_V02_NORMALIZED = NORMALIZATION_V02_BASE / "normalized_candidates.jsonl"
DEFAULT_V02_COMPARISONS = (
    NORMALIZATION_V02_BASE / "crossed_question_comparisons.jsonl"
)
DEFAULT_CROSSED_PLAN = (
    CONTRACTS / "operator_equivalence_crossed_author_sensitivity_plan_v0_1.json"
)
DEFAULT_CROSSED_MANIFEST = CROSSED_BASE / "run_manifest.json"
DEFAULT_REFERENCE_AUTHOR_OUTPUTS = tuple(
    CROSSED_BASE / f"author_outputs/{author_id}.jsonl"
    for author_id in REFERENCE_AUTHOR_IDS
)
DEFAULT_PACKETS = tuple(
    RUN_BASE / f"authoring_packets/{author_id}.jsonl" for author_id in AUTHOR_IDS
)
DEFAULT_AUTHOR_OUTPUTS = tuple(
    RUN_BASE / f"author_outputs/{author_id}.jsonl" for author_id in AUTHOR_IDS
)
DEFAULT_COMBINED = RUN_BASE / "combined_author_records.jsonl"
DEFAULT_NORMALIZED = RUN_BASE / "normalized_candidates.jsonl"
DEFAULT_COMPARISONS = RUN_BASE / "question_comparisons.jsonl"
DEFAULT_CHECKS = RUN_BASE / "checks.jsonl"
DEFAULT_METRICS = RUN_BASE / "metrics_v0_1.json"
DEFAULT_REPORT = RUN_BASE / "report_v0_1.md"
DEFAULT_MANIFEST = RUN_BASE / "run_manifest.json"

COMMON_RUNTIME = ROOT / "data_construction/tools/_common.py"
NORMALIZER_V01_TOOL = (
    ROOT / "data_construction/tools/build_operator_equivalence_normalization.py"
)
NORMALIZER_V02_TOOL = (
    ROOT / "data_construction/tools/build_operator_equivalence_normalization_v0_2.py"
)
CROSSED_VALIDATOR_TOOL = (
    ROOT
    / "data_construction/tools/build_operator_equivalence_crossed_author_sensitivity.py"
)
REPRESENTATIVE_VALIDATOR_TOOL = (
    ROOT / "data_construction/tools/build_representative_environment_realization.py"
)
TEST_ARTIFACT = ROOT / "tests/test_operator_equivalence_targeted_reauthor.py"

EVIDENCE_BOUNDARY = {
    "ai_non_human_non_gold": True,
    "already_exposed_question_ids_only": True,
    "prior_author_outputs_excluded_from_authoring_context": True,
    "normalization_outputs_excluded_from_authoring_context": True,
    "answer_and_trace_excluded": True,
    "grounding_evaluated": False,
    "execution_evaluated": False,
    "answer_recovery_evaluated": False,
    "human_evidence_created": False,
    "gold_claimed": False,
}

FROZEN_CRITERIA = {
    "invalid_author_record_count_max": 0,
    "technical_loss_count_max": 0,
    "eligible_set_contamination_count_max": 0,
    "unclassified_adapter_candidate_count_max": 0,
    "preferred_candidate_count_max": 0,
    "fresh_question_id_count_max": 0,
    "profile_inventory_loss_count_max": 0,
    "full_eligible_author_question_coverage_min": 12,
    "nonempty_new_author_semantic_intersection_count_min": 6,
    "new_author_semantic_exact_match_count_min": 5,
    "mean_new_author_semantic_jaccard_min": 0.90,
    "reference_compatible_author_question_count_min": 12,
    "branch_on_technical_failure": "REVISE_TARGETED_REAUTHOR_TECHNICAL_CONTRACT",
    "branch_on_coverage_failure": "REVISE_TARGETED_AUTHORING_INSTRUMENT_BEFORE_GROUNDING",
    "branch_on_semantic_failure": "NARROW_CHALLENGE_CLAIM_OR_REQUIRE_HUMAN_REVIEW",
    "branch_on_pass": "FREEZE_TARGETED_REAUTHOR_EVIDENCE_FOR_SEPARATE_NARROWED_GROUNDING_PLAN",
}


class TargetedReauthorError(ValueError):
    """Raised when the frozen targeted re-authoring contract is violated."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze-plan", action="store_true")
    modes.add_argument("--validate-plan-only", action="store_true")
    modes.add_argument("--materialize-packets", action="store_true")
    modes.add_argument("--validate-packets-only", action="store_true")
    modes.add_argument("--build-final", action="store_true")
    modes.add_argument("--validate-only", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument(
        "--comparison-schema", type=Path, default=DEFAULT_COMPARISON_SCHEMA
    )
    parser.add_argument(
        "--targeted-normalization-schema",
        type=Path,
        default=DEFAULT_TARGETED_NORMALIZATION_SCHEMA,
    )
    parser.add_argument(
        "--realization-schema", type=Path, default=DEFAULT_REALIZATION_SCHEMA
    )
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--views", type=Path, default=DEFAULT_VIEWS)
    parser.add_argument(
        "--e2-packets", nargs=4, type=Path, default=DEFAULT_E2_PACKETS
    )
    parser.add_argument("--v02-manifest", type=Path, default=DEFAULT_V02_MANIFEST)
    parser.add_argument(
        "--v02-normalized", type=Path, default=DEFAULT_V02_NORMALIZED
    )
    parser.add_argument(
        "--v02-comparisons", type=Path, default=DEFAULT_V02_COMPARISONS
    )
    parser.add_argument("--crossed-plan", type=Path, default=DEFAULT_CROSSED_PLAN)
    parser.add_argument(
        "--crossed-manifest", type=Path, default=DEFAULT_CROSSED_MANIFEST
    )
    parser.add_argument(
        "--reference-author-outputs",
        nargs=2,
        type=Path,
        default=DEFAULT_REFERENCE_AUTHOR_OUTPUTS,
    )
    parser.add_argument("--packets", nargs=2, type=Path, default=DEFAULT_PACKETS)
    parser.add_argument(
        "--author-outputs", nargs=2, type=Path, default=DEFAULT_AUTHOR_OUTPUTS
    )
    parser.add_argument("--combined-output", type=Path, default=DEFAULT_COMBINED)
    parser.add_argument("--normalized-output", type=Path, default=DEFAULT_NORMALIZED)
    parser.add_argument(
        "--comparisons-output", type=Path, default=DEFAULT_COMPARISONS
    )
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
        raise TargetedReauthorError(f"path outside repository: {path}") from exc
    if path.is_symlink() or ".." in relative.parts or ":" in relative.as_posix():
        raise TargetedReauthorError(
            f"unsafe repository path: {relative.as_posix()}"
        )
    return relative.as_posix()


def _binding(path: Path, *, record_count: int | None = None) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise TargetedReauthorError(
            f"bound artifact missing or symlink: {_relative(path)}"
        )
    result: dict[str, Any] = {
        "repository_relative_path": _relative(path),
        "sha256": sha256_file(path),
    }
    if record_count is not None:
        result["record_count"] = record_count
    return result


def _validator(path: Path) -> Draft202012Validator:
    schema = read_json(path)
    if not isinstance(schema, dict):
        raise TargetedReauthorError(f"schema is not an object: {_relative(path)}")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise TargetedReauthorError(
            f"invalid schema {_relative(path)}: {exc.message}"
        ) from exc
    registry = Registry()
    for schema_path in sorted(CONTRACTS.glob("*.json")):
        candidate = read_json(schema_path)
        if (
            isinstance(candidate, dict)
            and isinstance(candidate.get("$schema"), str)
            and isinstance(candidate.get("$id"), str)
        ):
            registry = registry.with_resource(
                candidate["$id"], Resource.from_contents(candidate)
            )
    return Draft202012Validator(schema, registry=registry)


def _contract_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "comparison_schema": args.comparison_schema,
        "targeted_normalization_schema": args.targeted_normalization_schema,
        "realization_schema": args.realization_schema,
        "protocol": args.protocol,
        "builder": Path(__file__).resolve(),
        "normalizer_v0_1": NORMALIZER_V01_TOOL,
        "normalizer_v0_2": NORMALIZER_V02_TOOL,
        "crossed_author_validator": CROSSED_VALIDATOR_TOOL,
        "representative_graph_validator": REPRESENTATIVE_VALIDATOR_TOOL,
        "common_runtime": COMMON_RUNTIME,
        "tests": TEST_ARTIFACT,
    }


def _source_inputs(args: argparse.Namespace) -> dict[str, Path]:
    result = {
        "normalization_v0_2_run_manifest": args.v02_manifest,
        "normalization_v0_2_normalized_candidates": args.v02_normalized,
        "normalization_v0_2_crossed_comparisons": args.v02_comparisons,
        "crossed_author_plan": args.crossed_plan,
        "crossed_author_run_manifest": args.crossed_manifest,
        "crossed_author_01_records": args.reference_author_outputs[0],
        "crossed_author_02_records": args.reference_author_outputs[1],
        "representative_views": args.views,
    }
    result.update(
        {
            f"original_e2_authoring_packet_{index:02d}": path
            for index, path in enumerate(args.e2_packets, 1)
        }
    )
    return result


def _post_packet_outputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "author_output_01": args.author_outputs[0],
        "author_output_02": args.author_outputs[1],
        "combined_author_records": args.combined_output,
        "normalized_candidates": args.normalized_output,
        "question_comparisons": args.comparisons_output,
        "checks": args.checks_output,
        "metrics": args.metrics_output,
        "report": args.report_output,
        "run_manifest": args.manifest_output,
    }


def _all_planned_outputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "authoring_packet_01": args.packets[0],
        "authoring_packet_02": args.packets[1],
        **_post_packet_outputs(args),
    }


def _manifest_output_binding(
    manifest: dict[str, Any], label: str, path: Path
) -> None:
    try:
        entry = manifest["outputs"][label]
    except (KeyError, TypeError) as exc:
        raise TargetedReauthorError(f"manifest lacks output binding: {label}") from exc
    if entry != _binding(path):
        raise TargetedReauthorError(f"manifest output binding mismatch: {label}")


def _load_v02_comparisons(args: argparse.Namespace) -> list[dict[str, Any]]:
    records = list(iter_json_records(args.v02_comparisons))
    if len(records) != 16:
        raise TargetedReauthorError("v0.2 crossed comparison count is not 16")
    mismatch = [
        record
        for record in records
        if not record.get("full_eligible_semantic_set_exact_match")
    ]
    ids = tuple(record.get("question_id") for record in mismatch)
    if ids != EXPECTED_QUESTION_IDS:
        raise TargetedReauthorError(
            f"v0.2 mismatch IDs changed: expected={EXPECTED_QUESTION_IDS!r} actual={ids!r}"
        )
    if any(record.get("selection_role") != "e1_challenge" for record in mismatch):
        raise TargetedReauthorError("targeted mismatch set is not entirely E1 challenge")
    return mismatch


def _selection(args: argparse.Namespace) -> list[dict[str, Any]]:
    return [
        {
            "question_id": record["question_id"],
            "selection_role": record["selection_role"],
            "original_e2_producer_partition": record[
                "original_e2_producer_partition"
            ],
            "v0_2_comparison_sha256": canonical_json_sha256(record),
        }
        for record in _load_v02_comparisons(args)
    ]


def _validate_source_contract(args: argparse.Namespace) -> None:
    v02_manifest = read_json(args.v02_manifest)
    if v02_manifest.get("schema_version") != (
        "operator_equivalence_normalization_run_manifest_v0_2"
    ):
        raise TargetedReauthorError("normalization v0.2 manifest version mismatch")
    if v02_manifest.get("validation_status") != "pass":
        raise TargetedReauthorError("normalization v0.2 manifest did not pass")
    _manifest_output_binding(
        v02_manifest, "normalized_candidates", args.v02_normalized
    )
    _manifest_output_binding(
        v02_manifest, "crossed_question_comparisons", args.v02_comparisons
    )

    crossed_manifest = read_json(args.crossed_manifest)
    if crossed_manifest.get("schema_version") != (
        "operator_equivalence_crossed_author_sensitivity_run_manifest_v0_1"
    ):
        raise TargetedReauthorError("crossed-author manifest version mismatch")
    if crossed_manifest.get("validation_status") != "pass":
        raise TargetedReauthorError("crossed-author manifest did not pass")
    expected_author_bindings = [
        _binding(path, record_count=16) for path in args.reference_author_outputs
    ]
    if crossed_manifest.get("author_outputs") != expected_author_bindings:
        raise TargetedReauthorError("crossed-author output bindings changed")

    crossed_plan = read_json(args.crossed_plan)
    previously_exposed = {
        item.get("question_id")
        for item in crossed_plan.get("selection", [])
        if isinstance(item, dict)
    }
    if not set(EXPECTED_QUESTION_IDS) <= previously_exposed:
        raise TargetedReauthorError("targeted selection contains a fresh question ID")

    normalized = list(iter_json_records(args.v02_normalized))
    if len(normalized) != 127:
        raise TargetedReauthorError("normalization v0.2 candidate count changed")
    for question_id in EXPECTED_QUESTION_IDS:
        authors = {
            record.get("source_author_id")
            for record in normalized
            if record.get("question_id") == question_id
            and record.get("source_cohort") == "crossed_author"
        }
        if authors != set(REFERENCE_AUTHOR_IDS):
            raise TargetedReauthorError(
                f"reference normalized authors incomplete for {question_id}"
            )
    _load_v02_comparisons(args)


def _original_packets(args: argparse.Namespace) -> dict[str, dict[str, Any]]:
    records = [
        record for path in args.e2_packets for record in iter_json_records(path)
    ]
    by_question = {record["view"]["question_id"]: record for record in records}
    if len(records) != 71 or len(by_question) != 71:
        raise TargetedReauthorError("original E2 packets are not 71 unique records")
    if not set(EXPECTED_QUESTION_IDS) <= set(by_question):
        raise TargetedReauthorError("an expected targeted question lacks an E2 packet")
    return by_question


def _fixed_fields(original: dict[str, Any], author_index: int) -> dict[str, Any]:
    fields = json.loads(json.dumps(original["fixed_output_fields"]))
    author_id = AUTHOR_IDS[author_index]
    question_id = fields["question_id"]
    fields["realization_id"] = (
        f"open_operator_realization_v0_1:{author_id}:{question_id}"
    )
    fields["run_id"] = RUN_ID
    fields["producer_partition"] = AUTHOR_PRODUCERS[author_index]
    return fields


def build_packets(args: argparse.Namespace) -> list[list[dict[str, Any]]]:
    selection = _selection(args)
    originals = _original_packets(args)
    packets: list[list[dict[str, Any]]] = []
    for author_index, author_id in enumerate(AUTHOR_IDS):
        records = []
        for item in selection:
            original = originals[item["question_id"]]
            records.append(
                {
                    "schema_version": (
                        "operator_equivalence_targeted_reauthor_input_v0_1"
                    ),
                    "run_id": RUN_ID,
                    "author_id": author_id,
                    "author_producer_partition": AUTHOR_PRODUCERS[author_index],
                    "selection_reason_hidden_from_author": True,
                    "original_producer_partition_hidden_from_author": True,
                    "isolation_contract": {
                        "fresh_context_required": True,
                        "prior_e1_records_excluded": True,
                        "prior_e2_records_excluded": True,
                        "prior_author_outputs_excluded": True,
                        "normalization_artifacts_excluded": True,
                        "other_targeted_author_packet_and_output_excluded": True,
                        "preserved_vocabularies_excluded": True,
                        "answers_traces_and_grounding_excluded": True,
                    },
                    "fixed_output_fields": _fixed_fields(original, author_index),
                    "author_fill_fields": [
                        "input_delivery",
                        "author_prior_exposure_to_record_before_packet",
                        "author_prior_exposure_to_backbone_adequacy",
                        "record_status",
                        "realization_status",
                        "realization_candidates",
                        "variant_realization_results",
                        "preferred_candidate_id",
                        "preference_reason",
                        "unresolved_issues",
                        "limitations",
                    ],
                    "view": original["view"],
                }
            )
        packets.append(records)
    return packets


def build_freeze_plan(args: argparse.Namespace) -> dict[str, Any]:
    for path in _all_planned_outputs(args).values():
        if path.is_symlink() or path.exists():
            raise TargetedReauthorError(
                f"planned output exists before plan freeze: {_relative(path)}"
            )
    _validator(args.comparison_schema)
    _validator(args.targeted_normalization_schema)
    _validator(args.realization_schema)
    _validate_source_contract(args)
    selection = _selection(args)
    implementation_commit = git_tracked_commit_identity(
        ROOT, _contract_inputs(args).values()
    )
    source_commit = git_tracked_commit_identity(ROOT, _source_inputs(args).values())
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "run_id": RUN_ID,
        "status": "frozen_before_targeted_author_packets_and_outputs",
        "implementation_commit": implementation_commit,
        "source_commit": source_commit,
        "contract_artifacts": {
            label: _binding(path) for label, path in _contract_inputs(args).items()
        },
        "source_artifacts": {
            label: _binding(path) for label, path in _source_inputs(args).items()
        },
        "selection": selection,
        "selection_contract": {
            "selection_rule": (
                "all_and_only_v0_2_crossed_full_eligible_semantic_set_mismatches"
            ),
            "expected_question_count": EXPECTED_QUESTIONS,
            "all_ids_previously_environment_exposed": True,
            "all_selection_roles_e1_challenge": True,
            "fresh_question_ids_used": False,
        },
        "author_contract": {
            "authors": list(AUTHOR_IDS),
            "producer_partitions": list(AUTHOR_PRODUCERS),
            "every_author_covers_every_question": True,
            "fresh_contexts_required": True,
            "author_contexts_shared": False,
            "prior_author_and_normalization_outputs_visible": False,
            "selection_reason_visible": False,
            "human_review_majority_vote_or_adjudication_claimed": False,
        },
        "normalization_contract": {
            "algorithm": "operator_equivalence_normalization_v0_2",
            "new_provenance_wrapper": (
                "operator_equivalence_targeted_reauthor_normalization_v0_1"
            ),
            "existing_author_records_are_reference_observations_not_gold": True,
            "candidate1_or_any_other_candidate_preferred": False,
            "all_observed_alternative_profiles_retained": True,
        },
        "frozen_decision_criteria": FROZEN_CRITERIA,
        "threshold_rationale": {
            "full_eligibility": (
                "each of two new authors must contribute a full-eligible plan for all six questions"
            ),
            "semantic_stability": (
                "all six pairs must intersect; at least five must have exact sets and mean Jaccard must be at least 0.90"
            ),
            "alternative_plan_policy": (
                "one non-exact set is allowed because exact graph or alternative-set identity is not the sole correctness target"
            ),
            "reference_compatibility": (
                "each new author/question semantic set must intersect the union of prior full-eligible observations"
            ),
        },
        "downstream_authorization": {
            "grounding_started": False,
            "grounding_authorized_by_this_plan": False,
            "successful_branch_requires_separate_narrowed_grounding_plan": True,
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
        raise TargetedReauthorError("targeted re-authoring plan version mismatch")
    if plan.get("status") != "frozen_before_targeted_author_packets_and_outputs":
        raise TargetedReauthorError("targeted plan was not frozen before outputs")
    _validate_source_contract(args)
    for label, path in _contract_inputs(args).items():
        if plan["contract_artifacts"].get(label) != _binding(path):
            raise TargetedReauthorError(f"plan contract binding mismatch: {label}")
    for label, path in _source_inputs(args).items():
        if plan["source_artifacts"].get(label) != _binding(path):
            raise TargetedReauthorError(f"plan source binding mismatch: {label}")
    if plan.get("selection") != _selection(args):
        raise TargetedReauthorError("plan selection differs from v0.2 mismatch set")
    if plan.get("frozen_decision_criteria") != FROZEN_CRITERIA:
        raise TargetedReauthorError("frozen criteria changed")
    if plan.get("author_contract", {}).get("authors") != list(AUTHOR_IDS):
        raise TargetedReauthorError("plan author identities changed")
    for label, path in _all_planned_outputs(args).items():
        expected = {"repository_relative_path": _relative(path)}
        if plan["planned_outputs"].get(label) != expected:
            raise TargetedReauthorError(f"plan output binding mismatch: {label}")
    if plan.get("output_absence_at_freeze") != {
        "verified": True,
        "absent_labels": list(_all_planned_outputs(args)),
    }:
        raise TargetedReauthorError("plan does not preserve output-absence proof")
    return plan


def materialize_packet_outputs(
    args: argparse.Namespace,
) -> dict[str, tuple[Path, bytes]]:
    _validate_plan(args)
    packets = build_packets(args)
    return {
        f"authoring_packet_{index:02d}": (path, jsonl_file_bytes(records))
        for index, (path, records) in enumerate(zip(args.packets, packets), 1)
    }


def _targeted_author_record_errors(
    record: dict[str, Any],
    packet: dict[str, Any],
    validator: Draft202012Validator,
) -> list[str]:
    errors = sensitivity._author_record_errors(record, packet, validator)
    if record.get("preferred_candidate_id") is not None:
        errors.append("targeted packet supplies no candidate-preference evidence")
    if record.get("preference_reason") is not None:
        errors.append("preference_reason must be null without preference evidence")
    return errors


def load_author_records(
    args: argparse.Namespace,
) -> tuple[list[list[dict[str, Any]]], list[list[dict[str, Any]]]]:
    _validate_plan(args)
    expected_packets = build_packets(args)
    for index, (path, records) in enumerate(zip(args.packets, expected_packets), 1):
        if not path.is_file() or path.read_bytes() != jsonl_file_bytes(records):
            raise TargetedReauthorError(
                f"author packet {index} differs from frozen reconstruction"
            )
    validator = _validator(args.realization_schema)
    author_records: list[list[dict[str, Any]]] = []
    for index, (path, packets) in enumerate(
        zip(args.author_outputs, expected_packets), 1
    ):
        if path.is_symlink() or not path.is_file():
            raise TargetedReauthorError(
                f"author output missing: {_relative(path)}"
            )
        records = list(iter_json_records(path))
        expected_ids = [packet["view"]["question_id"] for packet in packets]
        if [record.get("question_id") for record in records] != expected_ids:
            raise TargetedReauthorError(
                f"author {index} question order differs from packet"
            )
        for record, packet in zip(records, packets):
            errors = _targeted_author_record_errors(record, packet, validator)
            if errors:
                raise TargetedReauthorError(
                    f"author {index} record {record.get('question_id')} invalid: "
                    + " | ".join(errors[:20])
                )
        if path.read_bytes() != jsonl_file_bytes(records):
            raise TargetedReauthorError(
                f"author {index} output is not canonical JSONL"
            )
        author_records.append(records)
    return author_records, expected_packets


def _normalize_candidate(
    record: dict[str, Any],
    candidate: dict[str, Any],
    view: dict[str, Any],
    author_id: str,
) -> dict[str, Any]:
    projection = normalizer_v01.build_structural_projection(record, candidate, view)
    legacy = normalizer_v01.normalize_projection(projection)
    source_candidate_key = (
        f"targeted:{author_id}:{record['question_id']}:{candidate['candidate_id']}"
    )
    source_record_sha256 = canonical_json_sha256(record)
    normalized_v02 = normalizer_v02.normalize_projection_v0_2(
        projection,
        {
            "source_candidate_key": source_candidate_key,
            "source_cohort": "targeted_reauthor",
            "source_author_id": author_id,
            "source_v0_1_normalization_sha256": source_record_sha256,
            "source_v0_1_equivalence_status": legacy["equivalence_assessment"][
                "status"
            ],
            "source_projection_sha256": canonical_json_sha256(projection),
        },
    )
    return {
        "schema_version": (
            "operator_equivalence_targeted_reauthor_normalization_v0_1"
        ),
        "normalization_algorithm_version": (
            "operator_equivalence_normalization_v0_2"
        ),
        "normalization_id": (
            "operator_equivalence_targeted_reauthor_normalization_v0_1:"
            f"{author_id}:{record['question_id']}:{candidate['candidate_id']}"
        ),
        "source_candidate_key": source_candidate_key,
        "source_cohort": "targeted_reauthor",
        "source_author_id": author_id,
        "question_id": normalized_v02["question_id"],
        "family_id": normalized_v02["family_id"],
        "producer_partition": normalized_v02["producer_partition"],
        "candidate_id": normalized_v02["candidate_id"],
        "target_backbone_variant_id": normalized_v02[
            "target_backbone_variant_id"
        ],
        "source_author_record_sha256": source_record_sha256,
        "legacy_v0_1_equivalence_status": legacy["equivalence_assessment"][
            "status"
        ],
        "source_projection_sha256": normalized_v02["source_projection_sha256"],
        "candidate_semantic_profile": normalized_v02[
            "candidate_semantic_profile"
        ],
        "equivalence_eligibility": normalized_v02["equivalence_eligibility"],
        "factorized_environment_adapter": normalized_v02[
            "factorized_environment_adapter"
        ],
        "reversibility_ledger": normalized_v02["reversibility_ledger"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def _record_sets(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise TargetedReauthorError("cannot summarize an empty author/question set")
    return normalizer_v02._record_sets(records)


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 1.0


def _profile_inventory(
    reference_records: Iterable[dict[str, Any]],
    targeted_records: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    expected_keys: set[str] = set()
    for source_cohort, records in (
        ("existing_crossed_author", reference_records),
        ("targeted_reauthor", targeted_records),
    ):
        for record in records:
            key = record["source_candidate_key"]
            if key in expected_keys:
                raise TargetedReauthorError(f"duplicate source candidate key: {key}")
            expected_keys.add(key)
            grouped[record["candidate_semantic_profile"]["signature_sha256"]].append(
                {
                    "source_cohort": source_cohort,
                    "author_id": record["source_author_id"],
                    "source_candidate_key": key,
                    "eligibility_status": record["equivalence_eligibility"][
                        "status"
                    ],
                }
            )
    inventory = []
    observed_keys: set[str] = set()
    status_order = {"full_eligible": 0, "provisional_only": 1, "ineligible": 2}
    for signature, observations in sorted(grouped.items()):
        observations.sort(
            key=lambda item: (
                item["source_cohort"],
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


def _reference_normalized_records(
    args: argparse.Namespace,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in iter_json_records(args.v02_normalized):
        if (
            record.get("question_id") in EXPECTED_QUESTION_IDS
            and record.get("source_cohort") == "crossed_author"
        ):
            grouped[(record["source_author_id"], record["question_id"])].append(
                record
            )
    for question_id in EXPECTED_QUESTION_IDS:
        for author_id in REFERENCE_AUTHOR_IDS:
            if not grouped[(author_id, question_id)]:
                raise TargetedReauthorError(
                    f"missing reference normalized records: {author_id}/{question_id}"
                )
    return grouped


def _decision(
    counts: dict[str, Any], rates: dict[str, float], criteria: dict[str, Any]
) -> tuple[str, dict[str, bool]]:
    technical = all(
        [
            counts["invalid_author_records"]
            <= criteria["invalid_author_record_count_max"],
            counts["technical_loss"] <= criteria["technical_loss_count_max"],
            counts["eligible_set_contamination"]
            <= criteria["eligible_set_contamination_count_max"],
            counts["unclassified_adapter_candidates"]
            <= criteria["unclassified_adapter_candidate_count_max"],
            counts["preferred_candidates"]
            <= criteria["preferred_candidate_count_max"],
            counts["fresh_question_ids"]
            <= criteria["fresh_question_id_count_max"],
            counts["profile_inventory_loss"]
            <= criteria["profile_inventory_loss_count_max"],
        ]
    )
    coverage = (
        counts["full_eligible_author_question_coverage"]
        >= criteria["full_eligible_author_question_coverage_min"]
    )
    semantic = all(
        [
            counts["nonempty_new_author_semantic_intersections"]
            >= criteria[
                "nonempty_new_author_semantic_intersection_count_min"
            ],
            counts["new_author_semantic_exact_matches"]
            >= criteria["new_author_semantic_exact_match_count_min"],
            rates["mean_new_author_semantic_jaccard"]
            >= criteria["mean_new_author_semantic_jaccard_min"],
            counts["reference_compatible_author_questions"]
            >= criteria["reference_compatible_author_question_count_min"],
        ]
    )
    if not technical:
        decision = criteria["branch_on_technical_failure"]
    elif not coverage:
        decision = criteria["branch_on_coverage_failure"]
    elif not semantic:
        decision = criteria["branch_on_semantic_failure"]
    else:
        decision = criteria["branch_on_pass"]
    return decision, {
        "technical_contract_passed": technical,
        "full_eligibility_coverage_passed": coverage,
        "semantic_stability_and_reference_compatibility_passed": semantic,
        "all_criteria_passed": technical and coverage and semantic,
    }


def build_final_artifacts(
    args: argparse.Namespace,
) -> dict[str, tuple[Path, bytes]]:
    plan = _validate_plan(args)
    author_records, packets = load_author_records(args)
    normalization_validator = _validator(args.targeted_normalization_schema)
    comparison_validator = _validator(args.comparison_schema)

    targeted_grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(
        list
    )
    all_targeted_normalized: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for author_index, records in enumerate(author_records):
        author_id = AUTHOR_IDS[author_index]
        packet_by_question = {
            packet["view"]["question_id"]: packet
            for packet in packets[author_index]
        }
        for record in records:
            view = packet_by_question[record["question_id"]]["view"]
            normalized_for_record = []
            for candidate in record["realization_candidates"]:
                normalized = _normalize_candidate(
                    record, candidate, view, author_id
                )
                errors = sorted(
                    normalization_validator.iter_errors(normalized),
                    key=lambda error: list(error.path),
                )
                if errors:
                    raise TargetedReauthorError(
                        "targeted normalization schema failure: "
                        f"{errors[0].message}"
                    )
                targeted_grouped[(author_id, record["question_id"])].append(
                    normalized
                )
                normalized_for_record.append(normalized)
                all_targeted_normalized.append(normalized)
            checks.append(
                {
                    "schema_version": (
                        "operator_equivalence_targeted_reauthor_check_v0_1"
                    ),
                    "author_id": author_id,
                    "question_id": record["question_id"],
                    "status": "pass",
                    "author_record_valid": True,
                    "candidate_count": len(normalized_for_record),
                    "full_eligible_candidate_count": sum(
                        candidate["equivalence_eligibility"]["status"]
                        == "full_eligible"
                        for candidate in normalized_for_record
                    ),
                }
            )

    reference_grouped = _reference_normalized_records(args)
    selection_by_id = {item["question_id"]: item for item in plan["selection"]}
    comparisons: list[dict[str, Any]] = []
    for question_id in EXPECTED_QUESTION_IDS:
        new_results = []
        new_sets: list[set[str]] = []
        new_records_for_question: list[dict[str, Any]] = []
        for author_id in AUTHOR_IDS:
            records = targeted_grouped[(author_id, question_id)]
            sets = _record_sets(records)
            new_results.append({"author_id": author_id, **sets})
            semantic = set(sets["full_eligible_semantic_set"])
            new_sets.append(semantic)
            new_records_for_question.extend(records)

        reference_results = []
        reference_union: set[str] = set()
        reference_records_for_question: list[dict[str, Any]] = []
        for author_id in REFERENCE_AUTHOR_IDS:
            records = reference_grouped[(author_id, question_id)]
            sets = _record_sets(records)
            reference_results.append({"author_id": author_id, **sets})
            reference_union.update(sets["full_eligible_semantic_set"])
            reference_records_for_question.extend(records)

        new_union = new_sets[0] | new_sets[1]
        compatibility = [
            {
                "author_id": author_id,
                "intersects_reference_union": bool(semantic & reference_union),
                "semantic_intersection": sorted(semantic & reference_union),
            }
            for author_id, semantic in zip(AUTHOR_IDS, new_sets)
        ]
        inventory, inventory_loss = _profile_inventory(
            reference_records_for_question, new_records_for_question
        )
        comparison = {
            "schema_version": (
                "operator_equivalence_targeted_reauthor_comparison_v0_1"
            ),
            "question_id": question_id,
            "selection_role": selection_by_id[question_id]["selection_role"],
            "original_e2_producer_partition": selection_by_id[question_id][
                "original_e2_producer_partition"
            ],
            "historical_v0_2_mismatch_confirmed": True,
            "new_author_results": new_results,
            "reference_author_results": reference_results,
            "new_author_full_eligible_semantic_set_exact_match": (
                new_sets[0] == new_sets[1]
            ),
            "new_author_full_eligible_semantic_set_jaccard": _jaccard(
                new_sets[0], new_sets[1]
            ),
            "new_author_full_eligible_semantic_intersection": sorted(
                new_sets[0] & new_sets[1]
            ),
            "reference_full_eligible_semantic_union": sorted(reference_union),
            "new_full_eligible_semantic_union": sorted(new_union),
            "all_observed_full_eligible_semantic_union": sorted(
                reference_union | new_union
            ),
            "reference_compatibility": compatibility,
            "all_new_authors_have_full_eligible_candidate": all(new_sets),
            "observed_profile_inventory": inventory,
            "profile_inventory_loss_count": inventory_loss,
            "candidate1_preferred": False,
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
        errors = sorted(
            comparison_validator.iter_errors(comparison),
            key=lambda error: list(error.path),
        )
        if errors:
            raise TargetedReauthorError(
                f"comparison schema failure for {question_id}: {errors[0].message}"
            )
        if [item["author_id"] for item in new_results] != list(AUTHOR_IDS):
            raise TargetedReauthorError("new author comparison order changed")
        if [item["author_id"] for item in reference_results] != list(
            REFERENCE_AUTHOR_IDS
        ):
            raise TargetedReauthorError("reference author comparison order changed")
        comparisons.append(comparison)

    status_counts = Counter(
        record["equivalence_eligibility"]["status"]
        for record in all_targeted_normalized
    )
    expected_candidate_count = sum(
        len(record["realization_candidates"])
        for records in author_records
        for record in records
    )
    prior_exposed_ids = {
        item["question_id"] for item in read_json(args.crossed_plan)["selection"]
    }
    counts = {
        "questions": len(comparisons),
        "new_authors": len(AUTHOR_IDS),
        "reference_authors": len(REFERENCE_AUTHOR_IDS),
        "new_author_records": sum(len(records) for records in author_records),
        "normalized_candidates": len(all_targeted_normalized),
        "eligibility_status": dict(sorted(status_counts.items())),
        "invalid_author_records": 0,
        "technical_loss": abs(
            expected_candidate_count - len(all_targeted_normalized)
        ),
        "eligible_set_contamination": sum(
            result["eligible_set_contamination_count"]
            for comparison in comparisons
            for result in comparison["new_author_results"]
        ),
        "unclassified_adapter_candidates": sum(
            not record["factorized_environment_adapter"][
                "classification_coverage"
            ]["all_source_elements_classified"]
            for record in all_targeted_normalized
        ),
        "preferred_candidates": sum(
            record["preferred_candidate_id"] is not None
            for records in author_records
            for record in records
        ),
        "fresh_question_ids": len(set(EXPECTED_QUESTION_IDS) - prior_exposed_ids),
        "profile_inventory_loss": sum(
            comparison["profile_inventory_loss_count"]
            for comparison in comparisons
        ),
        "full_eligible_author_question_coverage": sum(
            result["full_eligible_candidate_count"] > 0
            for comparison in comparisons
            for result in comparison["new_author_results"]
        ),
        "nonempty_new_author_semantic_intersections": sum(
            bool(comparison["new_author_full_eligible_semantic_intersection"])
            for comparison in comparisons
        ),
        "new_author_semantic_exact_matches": sum(
            comparison[
                "new_author_full_eligible_semantic_set_exact_match"
            ]
            for comparison in comparisons
        ),
        "reference_compatible_author_questions": sum(
            item["intersects_reference_union"]
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
        "new_author_semantic_exact_match": (
            counts["new_author_semantic_exact_matches"] / EXPECTED_QUESTIONS
        ),
        "mean_new_author_semantic_jaccard": sum(
            comparison["new_author_full_eligible_semantic_set_jaccard"]
            for comparison in comparisons
        )
        / EXPECTED_QUESTIONS,
        "full_eligible_author_question_coverage": (
            counts["full_eligible_author_question_coverage"]
            / (EXPECTED_QUESTIONS * len(AUTHOR_IDS))
        ),
        "reference_compatible_author_question": (
            counts["reference_compatible_author_questions"]
            / (EXPECTED_QUESTIONS * len(AUTHOR_IDS))
        ),
    }
    criteria = plan["frozen_decision_criteria"]
    decision, criteria_results = _decision(counts, rates, criteria)
    metrics = {
        "schema_version": (
            "operator_equivalence_targeted_reauthor_metrics_v0_1"
        ),
        "run_id": RUN_ID,
        "counts": counts,
        "rates": rates,
        "frozen_criteria": criteria,
        "criteria_results": criteria_results,
        "decision": decision,
        "fresh_question_ids_used": False,
        "grounding_started": False,
        "grounding_protocol_authorized_next": False,
        "separate_narrowed_grounding_plan_may_be_frozen_next": criteria_results[
            "all_criteria_passed"
        ],
        "human_evidence_created": False,
        "gold_claimed": False,
    }
    report = "\n".join(
        [
            "# Targeted crossed-author re-authoring v0.1",
            "",
            "Two new fresh-context AI authors independently re-authored the six",
            "already exposed E1-challenge questions whose prior full-eligible",
            "semantic sets differed under normalization v0.2. Prior records were",
            "reference observations only; they were not visible to the new authors",
            "and were not treated as gold, votes, or adjudication targets.",
            "",
            "## Results",
            "",
            (
                "- full-eligible author/question coverage: "
                f"{counts['full_eligible_author_question_coverage']}/12"
            ),
            (
                "- nonempty new-author semantic intersections: "
                f"{counts['nonempty_new_author_semantic_intersections']}/6"
            ),
            (
                "- new-author semantic-set exact matches: "
                f"{counts['new_author_semantic_exact_matches']}/6"
            ),
            (
                "- mean new-author semantic-set Jaccard: "
                f"{rates['mean_new_author_semantic_jaccard']:.6f}"
            ),
            (
                "- reference-compatible author/questions: "
                f"{counts['reference_compatible_author_questions']}/12"
            ),
            (
                "- targeted candidates by eligibility: "
                f"{json.dumps(counts['eligibility_status'], sort_keys=True)}"
            ),
            f"- profile inventory loss: {counts['profile_inventory_loss']}",
            "",
            "## Frozen branch result",
            "",
            f"`{decision}`",
            "",
            "Grounding, execution, answer recovery, human review, and gold",
            "annotation were not performed. Even a passing branch authorizes only",
            "freezing a separate narrowed grounding plan.",
            "",
        ]
    )
    combined = [record for records in author_records for record in records]
    preliminary = {
        "combined_author_records": (
            args.combined_output,
            jsonl_file_bytes(combined),
        ),
        "normalized_candidates": (
            args.normalized_output,
            jsonl_file_bytes(all_targeted_normalized),
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
        "schema_version": (
            "operator_equivalence_targeted_reauthor_run_manifest_v0_1"
        ),
        "run_id": RUN_ID,
        "plan": _binding(args.plan),
        "implementation_commit": plan["implementation_commit"],
        "source_commit": plan["source_commit"],
        "author_packets": [
            _binding(path, record_count=EXPECTED_QUESTIONS) for path in args.packets
        ],
        "author_outputs": [
            _binding(path, record_count=EXPECTED_QUESTIONS)
            for path in args.author_outputs
        ],
        "reference_author_outputs": [
            _binding(path, record_count=16)
            for path in args.reference_author_outputs
        ],
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


def validate_packets(args: argparse.Namespace) -> dict[str, Any]:
    expected = materialize_packet_outputs(args)
    mismatches = [
        label
        for label, (path, payload) in expected.items()
        if not path.is_file() or path.read_bytes() != payload
    ]
    if mismatches:
        raise TargetedReauthorError(
            f"materialized author packets differ: {mismatches}"
        )
    return {
        "status": "pass",
        "mode": "validate_packets_only",
        "questions": EXPECTED_QUESTIONS,
        "authors": len(AUTHOR_IDS),
    }


def validate_materialized(args: argparse.Namespace) -> dict[str, Any]:
    validate_packets(args)
    expected = build_final_artifacts(args)
    mismatches = [
        label
        for label, (path, payload) in expected.items()
        if not path.is_file() or path.read_bytes() != payload
    ]
    if mismatches:
        raise TargetedReauthorError(
            f"materialized final artifacts differ: {mismatches}"
        )
    metrics = read_json(args.metrics_output)
    return {
        "status": "pass",
        "mode": "validate_only",
        "questions": metrics["counts"]["questions"],
        "authors": metrics["counts"]["new_authors"],
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
            print(
                json.dumps(
                    {"status": "frozen", "plan": _relative(args.plan)},
                    sort_keys=True,
                )
            )
        elif args.validate_plan_only:
            plan = _validate_plan(args)
            print(
                json.dumps(
                    {
                        "status": "pass",
                        "mode": "validate_plan_only",
                        "questions": len(plan["selection"]),
                    },
                    sort_keys=True,
                )
            )
        elif args.materialize_packets:
            statuses = write_output_batch(
                materialize_packet_outputs(args), overwrite=args.overwrite
            )
            print(
                json.dumps(
                    {"status": "packets_materialized", "outputs": statuses},
                    sort_keys=True,
                )
            )
        elif args.validate_packets_only:
            print(json.dumps(validate_packets(args), sort_keys=True))
        elif args.build_final:
            statuses = write_output_batch(
                build_final_artifacts(args), overwrite=args.overwrite
            )
            print(
                json.dumps(
                    {"status": "final_built", "outputs": statuses},
                    sort_keys=True,
                )
            )
        else:
            print(json.dumps(validate_materialized(args), sort_keys=True))
    except (
        TargetedReauthorError,
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
