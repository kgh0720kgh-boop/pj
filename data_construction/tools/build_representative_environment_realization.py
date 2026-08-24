#!/usr/bin/env python3
"""Freeze, materialize, and validate representative environment realization.

The workflow is deliberately staged:

1. commit this implementation, schemas, prompts, and tests;
2. freeze and commit a plan without opening raw HybridQA environments;
3. materialize the exact 71 environment views from pinned Git blobs;
4. author, combine, and commit E1 backbone-adequacy assessments;
5. only then author E2 open operator realizations and derive outcome records.

Grounding, execution, and answer recovery remain not evaluated.  The E2
notation uses record-local free labels and is not a selected operator
vocabulary.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from _common import (
    canonical_json_sha256,
    canonical_string_set_sha256,
    git_tracked_commit_identity,
    historical_output_collision_errors,
    iter_json_records,
    json_file_bytes,
    jsonl_file_bytes,
    output_path_collision_errors,
    read_json,
    sha256_bytes,
    sha256_file,
    write_output_batch,
)
import _representative_environment_source as environment_source


TOOL_VERSION = "representative_environment_realization_builder_v0_1"
PLAN_SCHEMA_VERSION = "representative_environment_realization_plan_v0_1"
PLAN_ID = "hybridqa_n300_representative_environment_realization_plan_v0_1"
RUN_ID = "hybridqa_n300_representative_environment_realization_v0_1_run_001"
SELECTION_ID = "hybridqa_n300_candidate_backbone_coverage_sample_v0_1"
VIEW_SCHEMA_VERSION = "representative_environment_view_v0_1"
ADEQUACY_SCHEMA_VERSION = "backbone_adequacy_assessment_v0_1"
REALIZATION_SCHEMA_VERSION = "open_operator_realization_v0_1"
CHECK_SCHEMA_VERSION = "representative_environment_realization_check_v0_1"
RUN_MANIFEST_SCHEMA_VERSION = "representative_environment_realization_run_manifest_v0_1"
OPEN_NOTATION_ID = "open_descriptive_operator_notation_v0_1"
EXPECTED_QUESTION_COUNT = 71
EXPECTED_FAMILY_COUNT = 30
PARTITION_COUNT = 4
EXPECTED_SELECTED_ORDERED_SHA256 = (
    "5403debe2cbe9c7f55ded0a01b49d7c42bf03e53a71350efe269bbd3c0bdcb2e"
)
EXPECTED_SELECTED_SET_SHA256 = (
    "9b6e05650834871ce30acc1c2dfde18fc64910dcd238982f5d482f6a31e15680"
)

ROOT = Path(__file__).resolve().parents[2]
SCALE_BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
CONTRACTS = SCALE_BASE / "contracts"
PROMPTS = SCALE_BASE / "prompts"
RUN_BASE = SCALE_BASE / "representative_environment_realization_v0_1"
COMMON_RUNTIME = ROOT / "data_construction/tools/_common.py"
SOURCE_HELPER = ROOT / "data_construction/tools/_representative_environment_source.py"
TEST_ARTIFACT = ROOT / "tests/test_representative_environment_realization.py"

DEFAULT_PLAN = CONTRACTS / "representative_environment_realization_plan_v0_1.json"
DEFAULT_VIEW_SCHEMA = CONTRACTS / "representative_environment_view_schema_v0_1.json"
DEFAULT_ADEQUACY_SCHEMA = CONTRACTS / "backbone_adequacy_assessment_schema_v0_1.json"
DEFAULT_REALIZATION_SCHEMA = CONTRACTS / "open_operator_realization_schema_v0_1.json"
DEFAULT_OUTCOME_SCHEMA = CONTRACTS / "environment_realization_outcome_schema_v0_2.json"
DEFAULT_OUTCOME_MIGRATION = (
    CONTRACTS / "environment_realization_outcome_v0_1_to_v0_2_migration.md"
)
DEFAULT_E1_PROMPT = PROMPTS / "backbone_adequacy_assessment_v0_1.md"
DEFAULT_E2_PROMPT = PROMPTS / "open_operator_realization_v0_1.md"
DEFAULT_SELECTION = (
    SCALE_BASE
    / "candidate_backbone_library_v0_1/representative_selection_v0_1.json"
)
DEFAULT_FAMILIES = (
    SCALE_BASE
    / "candidate_backbone_library_v0_1/candidate_backbone_families_v0_1.jsonl"
)
DEFAULT_RECORDS = SCALE_BASE / "cumulative_n300_v0_1/records.jsonl"
DEFAULT_CANDIDATE_RUN_MANIFEST = (
    SCALE_BASE / "candidate_backbone_library_v0_1/run_manifest.json"
)
DEFAULT_SOURCE_MANIFEST = ROOT / "data_construction/manifests/source_manifest_v0_1.json"

DEFAULT_VIEWS = RUN_BASE / "inputs/environment_views.jsonl"
DEFAULT_VIEWS_MANIFEST = RUN_BASE / "inputs/environment_views_manifest_v0_1.json"
DEFAULT_ROUTING = RUN_BASE / "inputs/producer_routing_manifest_v0_1.json"
DEFAULT_E1_PACKETS = tuple(
    RUN_BASE / f"stage_e1/authoring_packets/partition_{index:02d}.jsonl"
    for index in range(1, PARTITION_COUNT + 1)
)
DEFAULT_E1_PARTS = tuple(
    RUN_BASE / f"stage_e1/parts/partition_{index:02d}.jsonl"
    for index in range(1, PARTITION_COUNT + 1)
)
DEFAULT_E1_COMBINED = RUN_BASE / "stage_e1/backbone_adequacy_assessments.jsonl"
DEFAULT_E1_BINDINGS = RUN_BASE / "stage_e1/assessment_bindings_for_e2.json"
DEFAULT_E2_PACKETS = tuple(
    RUN_BASE / f"stage_e2/authoring_packets/partition_{index:02d}.jsonl"
    for index in range(1, PARTITION_COUNT + 1)
)
DEFAULT_E2_PARTS = tuple(
    RUN_BASE / f"stage_e2/parts/partition_{index:02d}.jsonl"
    for index in range(1, PARTITION_COUNT + 1)
)
DEFAULT_E2_COMBINED = RUN_BASE / "stage_e2/open_operator_realizations.jsonl"
DEFAULT_OUTCOMES = RUN_BASE / "outcomes.jsonl"
DEFAULT_CHECKS = RUN_BASE / "checks.jsonl"
DEFAULT_REPORT = RUN_BASE / "report_v0_1.md"
DEFAULT_METRICS = RUN_BASE / "metrics_v0_1.json"
DEFAULT_EXPOSURE_LEDGER = RUN_BASE / "environment_exposure_ledger_v0_1.json"
DEFAULT_RUN_MANIFEST = RUN_BASE / "run_manifest.json"

E1_STATUSES = ("adequate", "partially_adequate", "inadequate", "indeterminate")
E2_STATUSES = ("available", "partial", "unavailable", "indeterminate")
E1_DOWNSTREAM_NOT_EVALUATED = {
    "environment_operator_realization": "not_evaluated",
    "grounding": "not_evaluated",
    "execution": "not_evaluated",
    "answer_recovery": "not_evaluated",
}
E2_DOWNSTREAM_NOT_EVALUATED = {
    "grounding": "not_evaluated",
    "execution": "not_evaluated",
    "answer_recovery": "not_evaluated",
}
MODEL_PROVENANCE = {
    "model_id": "codex_gpt-5",
    "exact_model_revision": None,
    "exact_model_revision_status": "not_exposed_by_interface",
    "seed": None,
    "seed_status": "not_supported_by_interface",
    "raw_response_artifact": None,
    "raw_response_status": "not_exposed_structured_partition_files_are_primary_capture",
    "statistical_reviewer_independence_claimed": False,
}


class EnvironmentRealizationError(ValueError):
    """Raised when a frozen environment-realization contract is violated."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze-plan", action="store_true")
    modes.add_argument("--materialize-views", action="store_true")
    modes.add_argument("--build-adequacy", action="store_true")
    modes.add_argument("--build-final", action="store_true")
    modes.add_argument("--validate-only", action="store_true")
    parser.add_argument("--source-cache-root", type=Path)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--view-schema", type=Path, default=DEFAULT_VIEW_SCHEMA)
    parser.add_argument("--adequacy-schema", type=Path, default=DEFAULT_ADEQUACY_SCHEMA)
    parser.add_argument("--realization-schema", type=Path, default=DEFAULT_REALIZATION_SCHEMA)
    parser.add_argument("--outcome-schema", type=Path, default=DEFAULT_OUTCOME_SCHEMA)
    parser.add_argument("--e1-prompt", type=Path, default=DEFAULT_E1_PROMPT)
    parser.add_argument("--e2-prompt", type=Path, default=DEFAULT_E2_PROMPT)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--families", type=Path, default=DEFAULT_FAMILIES)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument(
        "--candidate-run-manifest", type=Path, default=DEFAULT_CANDIDATE_RUN_MANIFEST
    )
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--views-output", type=Path, default=DEFAULT_VIEWS)
    parser.add_argument("--views-manifest-output", type=Path, default=DEFAULT_VIEWS_MANIFEST)
    parser.add_argument("--routing-output", type=Path, default=DEFAULT_ROUTING)
    parser.add_argument(
        "--e1-packets", type=Path, nargs=PARTITION_COUNT, default=DEFAULT_E1_PACKETS
    )
    parser.add_argument("--e1-parts", type=Path, nargs=PARTITION_COUNT, default=DEFAULT_E1_PARTS)
    parser.add_argument("--e1-output", type=Path, default=DEFAULT_E1_COMBINED)
    parser.add_argument(
        "--e1-bindings-output", type=Path, default=DEFAULT_E1_BINDINGS
    )
    parser.add_argument(
        "--e2-packets", type=Path, nargs=PARTITION_COUNT, default=DEFAULT_E2_PACKETS
    )
    parser.add_argument("--e2-parts", type=Path, nargs=PARTITION_COUNT, default=DEFAULT_E2_PARTS)
    parser.add_argument("--e2-output", type=Path, default=DEFAULT_E2_COMBINED)
    parser.add_argument("--outcomes-output", type=Path, default=DEFAULT_OUTCOMES)
    parser.add_argument("--checks-output", type=Path, default=DEFAULT_CHECKS)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metrics-output", type=Path, default=DEFAULT_METRICS)
    parser.add_argument(
        "--exposure-ledger-output", type=Path, default=DEFAULT_EXPOSURE_LEDGER
    )
    parser.add_argument("--run-manifest-output", type=Path, default=DEFAULT_RUN_MANIFEST)
    return parser.parse_args(argv)


def _relative(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
    except ValueError as exc:
        raise EnvironmentRealizationError(f"path is outside repository: {path}") from exc
    if path.is_symlink() or ".." in relative.parts or ":" in relative.as_posix():
        raise EnvironmentRealizationError(f"unsafe repository path: {relative.as_posix()}")
    return relative.as_posix()


def _binding(path: Path, *, record_count: int | None = None) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise EnvironmentRealizationError(f"bound artifact missing or symlink: {_relative(path)}")
    value: dict[str, Any] = {
        "repository_relative_path": _relative(path),
        "sha256": sha256_file(path),
    }
    if record_count is not None:
        value["record_count"] = record_count
    return value


def _artifact_reference(
    path: Path,
    payload_sha256: str,
    *,
    artifact_role: str,
    record_id: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "artifact_role": artifact_role,
        "repository_relative_path": _relative(path),
        "sha256": payload_sha256,
        "record_id": record_id,
    }
    return value


def _schema_validator(path: Path) -> Draft202012Validator:
    schema = read_json(path)
    if not isinstance(schema, dict):
        raise EnvironmentRealizationError(f"schema is not an object: {_relative(path)}")
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise EnvironmentRealizationError(f"schema is not Draft 2020-12: {_relative(path)}")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise EnvironmentRealizationError(
            f"invalid Draft 2020-12 schema {_relative(path)}: {exc.message}"
        ) from exc
    return Draft202012Validator(schema)


def _validation_errors(
    validator: Draft202012Validator, value: Any, label: str
) -> list[str]:
    errors: list[str] = []
    for error in sorted(validator.iter_errors(value), key=lambda item: list(item.path)):
        location = "/".join(str(item) for item in error.path) or "<root>"
        errors.append(f"{label}/{location}: {error.message}")
    return errors


def _source_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "selection": args.selection,
        "families": args.families,
        "records": args.records,
        "candidate_run_manifest": args.candidate_run_manifest,
        "source_manifest": args.source_manifest,
    }


def _contract_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "builder": Path(__file__),
        "source_helper": SOURCE_HELPER,
        "common_runtime": COMMON_RUNTIME,
        "view_schema": args.view_schema,
        "adequacy_schema": args.adequacy_schema,
        "realization_schema": args.realization_schema,
        "outcome_schema": args.outcome_schema,
        "outcome_migration": DEFAULT_OUTCOME_MIGRATION,
        "e1_prompt": args.e1_prompt,
        "e2_prompt": args.e2_prompt,
        "tests": TEST_ARTIFACT,
    }


def _planned_outputs(args: argparse.Namespace) -> dict[str, Path]:
    result: dict[str, Path] = {
        "environment_views": args.views_output,
        "environment_views_manifest": args.views_manifest_output,
        "producer_routing_manifest": args.routing_output,
        **{
            f"e1_authoring_packet_{index:02d}": path
            for index, path in enumerate(args.e1_packets, 1)
        },
        "backbone_adequacy_assessments": args.e1_output,
        "e1_assessment_bindings_for_e2": args.e1_bindings_output,
        **{
            f"e2_authoring_packet_{index:02d}": path
            for index, path in enumerate(args.e2_packets, 1)
        },
        "open_operator_realizations": args.e2_output,
        "outcomes": args.outcomes_output,
        "checks": args.checks_output,
        "report": args.report_output,
        "metrics": args.metrics_output,
        "environment_exposure_ledger": args.exposure_ledger_output,
        "run_manifest": args.run_manifest_output,
    }
    result.update(
        {f"e1_partition_{index:02d}": path for index, path in enumerate(args.e1_parts, 1)}
    )
    result.update(
        {f"e2_partition_{index:02d}": path for index, path in enumerate(args.e2_parts, 1)}
    )
    return result


def _validate_paths(args: argparse.Namespace) -> None:
    source_inputs = _source_inputs(args)
    contract_inputs = _contract_inputs(args)
    outputs = _planned_outputs(args)
    errors = output_path_collision_errors(
        {"plan": args.plan, **source_inputs, **contract_inputs}, outputs
    )
    errors.extend(historical_output_collision_errors(outputs, ROOT))
    try:
        _relative(args.plan)
    except EnvironmentRealizationError as exc:
        errors.append(str(exc))
    for label, path in {**source_inputs, **contract_inputs, **outputs}.items():
        try:
            relative = _relative(path)
        except EnvironmentRealizationError as exc:
            errors.append(f"{label}: {exc}")
            continue
        if not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", relative):
            errors.append(f"{label}: repository-relative path is not portable: {relative}")
    canonical_paths = {
        "plan": DEFAULT_PLAN,
        "view_schema": DEFAULT_VIEW_SCHEMA,
        "adequacy_schema": DEFAULT_ADEQUACY_SCHEMA,
        "realization_schema": DEFAULT_REALIZATION_SCHEMA,
        "outcome_schema": DEFAULT_OUTCOME_SCHEMA,
        "e1_prompt": DEFAULT_E1_PROMPT,
        "e2_prompt": DEFAULT_E2_PROMPT,
        "selection": DEFAULT_SELECTION,
        "families": DEFAULT_FAMILIES,
        "records": DEFAULT_RECORDS,
        "candidate_run_manifest": DEFAULT_CANDIDATE_RUN_MANIFEST,
        "source_manifest": DEFAULT_SOURCE_MANIFEST,
        "views_output": DEFAULT_VIEWS,
        "views_manifest_output": DEFAULT_VIEWS_MANIFEST,
        "routing_output": DEFAULT_ROUTING,
        "e1_output": DEFAULT_E1_COMBINED,
        "e1_bindings_output": DEFAULT_E1_BINDINGS,
        "e2_output": DEFAULT_E2_COMBINED,
        "outcomes_output": DEFAULT_OUTCOMES,
        "checks_output": DEFAULT_CHECKS,
        "report_output": DEFAULT_REPORT,
        "metrics_output": DEFAULT_METRICS,
        "exposure_ledger_output": DEFAULT_EXPOSURE_LEDGER,
        "run_manifest_output": DEFAULT_RUN_MANIFEST,
    }
    for attribute, canonical in canonical_paths.items():
        if getattr(args, attribute).resolve() != canonical.resolve():
            errors.append(
                f"{attribute}: versioned run requires canonical path {_relative(canonical)}"
            )
    for attribute, canonical_paths_for_stage in (
        ("e1_packets", DEFAULT_E1_PACKETS),
        ("e1_parts", DEFAULT_E1_PARTS),
        ("e2_packets", DEFAULT_E2_PACKETS),
        ("e2_parts", DEFAULT_E2_PARTS),
    ):
        observed = tuple(path.resolve() for path in getattr(args, attribute))
        expected = tuple(path.resolve() for path in canonical_paths_for_stage)
        if observed != expected:
            errors.append(
                f"{attribute}: versioned run requires the canonical ordered path set"
            )
    if args.source_cache_root is not None:
        cache = args.source_cache_root.resolve()
        try:
            cache.relative_to(ROOT.resolve())
        except ValueError:
            pass
        else:
            errors.append("source cache root must be outside the project repository")
        if args.source_cache_root.is_symlink():
            errors.append("source cache root must not be a symlink")
        for label, path in outputs.items():
            try:
                path.resolve().relative_to(cache)
            except ValueError:
                pass
            else:
                errors.append(f"output {label} must not be inside the source cache")
    if errors:
        raise EnvironmentRealizationError("; ".join(errors))


def _load_question_contract(
    args: argparse.Namespace,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, Any],
]:
    selection = read_json(args.selection)
    families = list(iter_json_records(args.families))
    records = list(iter_json_records(args.records))
    candidate_manifest = read_json(args.candidate_run_manifest)
    if not isinstance(selection, dict) or not isinstance(candidate_manifest, dict):
        raise EnvironmentRealizationError("selection and candidate run manifest must be objects")
    ids = selection.get("selected_question_ids")
    selections = selection.get("selections")
    if (
        selection.get("schema_version") != "representative_coverage_selection_v0_1"
        or selection.get("selection_id") != SELECTION_ID
        or selection.get("selected_question_count") != EXPECTED_QUESTION_COUNT
        or selection.get("selected_family_count") != EXPECTED_FAMILY_COUNT
        or not isinstance(ids, list)
        or not isinstance(selections, list)
        or len(ids) != EXPECTED_QUESTION_COUNT
        or len(selections) != EXPECTED_QUESTION_COUNT
        or len(set(ids)) != EXPECTED_QUESTION_COUNT
        or ids != [item.get("question_id") for item in selections]
        or [item.get("selection_index") for item in selections]
        != list(range(1, EXPECTED_QUESTION_COUNT + 1))
        or selection.get("selected_question_ids_ordered_sha256")
        != EXPECTED_SELECTED_ORDERED_SHA256
        or selection.get("selected_question_ids_set_sha256") != EXPECTED_SELECTED_SET_SHA256
        or canonical_json_sha256(ids) != EXPECTED_SELECTED_ORDERED_SHA256
        or canonical_string_set_sha256(ids) != EXPECTED_SELECTED_SET_SHA256
    ):
        raise EnvironmentRealizationError("representative selection is not the exact frozen 71-ID contract")
    family_by_id = {item.get("family_id"): item for item in families}
    record_by_id = {item.get("question_id"): item for item in records}
    if len(family_by_id) != EXPECTED_FAMILY_COUNT or len(records) != 300 or len(record_by_id) != 300:
        raise EnvironmentRealizationError("candidate family or N=300 record inventory mismatch")
    for item in selections:
        family = family_by_id.get(item.get("family_id"))
        record = record_by_id.get(item.get("question_id"))
        if (
            not isinstance(family, dict)
            or not isinstance(record, dict)
            or family.get("contracted_signature_sha256")
            != item.get("contracted_signature_sha256")
            or not any(
                member.get("question_id") == item.get("question_id")
                for member in family.get("members", [])
                if isinstance(member, dict)
            )
            or record.get("primary_graph") is None
        ):
            raise EnvironmentRealizationError(
                f"selection/family/backbone mismatch for {item.get('question_id')!r}"
            )
    if (
        candidate_manifest.get("selection_id") != SELECTION_ID
        or candidate_manifest.get("counts", {}).get("representative_questions")
        != EXPECTED_QUESTION_COUNT
    ):
        raise EnvironmentRealizationError("candidate run manifest does not bind the 71 selection")
    return selection, selections, family_by_id, record_by_id, candidate_manifest


def _routing(
    selections: list[dict[str, Any]], args: argparse.Namespace
) -> dict[str, Any]:
    partitions: list[dict[str, Any]] = []
    for partition_index in range(1, PARTITION_COUNT + 1):
        assigned = [
            item
            for item in selections
            if ((item["selection_index"] - 1) % PARTITION_COUNT) + 1 == partition_index
        ]
        partitions.append(
            {
                "routing_partition_id": f"routing_partition_{partition_index:02d}",
                "e1_producer_partition": f"e1_author_partition_{partition_index:02d}",
                "e2_producer_partition": f"e2_author_partition_{partition_index:02d}",
                "assignment_method": "round_robin_by_frozen_selection_index_modulo_4",
                "selection_indices": [item["selection_index"] for item in assigned],
                "question_ids": [item["question_id"] for item in assigned],
                "question_ids_ordered_sha256": canonical_json_sha256(
                    [item["question_id"] for item in assigned]
                ),
                "e1_output_path": _relative(args.e1_parts[partition_index - 1]),
                "e2_output_path": _relative(args.e2_parts[partition_index - 1]),
                "e1_authoring_packet_path": _relative(
                    args.e1_packets[partition_index - 1]
                ),
                "e2_authoring_packet_path": _relative(
                    args.e2_packets[partition_index - 1]
                ),
            }
        )
    return {
        "schema_version": "representative_environment_realization_routing_v0_1",
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "producer_partitions_are_independent_reviewers": False,
        "partition_count": PARTITION_COUNT,
        "record_count": EXPECTED_QUESTION_COUNT,
        "partitions": partitions,
    }


def _source_metadata_contract(source_manifest: dict[str, Any]) -> dict[str, Any]:
    return environment_source.extract_source_contract(source_manifest)


def _expected_source_verification(
    source_contract: dict[str, Any],
) -> dict[str, Any]:
    question = source_contract["question_source"]
    linked = source_contract["linked_environment_source"]
    return {
        "status": "verified_exact_official_pins",
        "question_source": {
            "source_id": question["source_id"],
            "pinned_commit": question["pinned_commit"],
            "git_tree_sha1": question["git_tree_sha1"],
            "released_data_tree_sha1": question["released_data_tree_sha1"],
            "dev_artifact": {
                "repository_relative_path": question["dev_artifact"][
                    "repository_relative_path"
                ],
                "sha256": question["dev_artifact"]["sha256"],
            },
        },
        "linked_environment_source": {
            "source_id": linked["source_id"],
            "pinned_commit": linked["pinned_commit"],
            "git_tree_sha1": linked["git_tree_sha1"],
            "tables_tree_sha1": linked["tables_artifact"]["git_tree_sha1"],
            "request_tree_sha1": linked["request_artifact"]["git_tree_sha1"],
        },
    }


def _freeze_contract() -> dict[str, Any]:
    return {
        "stage_order": [
            "implementation_commit",
            "plan_freeze_commit_without_raw_environment_access",
            "environment_view_and_e1_packet_materialization_commit",
            "e1_backbone_adequacy_authoring_and_commit",
            "e2_hash_only_packet_materialization_in_e1_commit",
            "e2_open_operator_realization_in_fresh_context",
            "combined_outcome_derivation",
        ],
        "e1_fresh_authoring_context_required": True,
        "e1_context_inherits_prior_conversation": False,
        "e1_prior_record_exposure_attestation_required": True,
        "e1_must_be_committed_before_e2": True,
        "e2_authoring_input_includes_e1_content": False,
        "e2_fresh_authoring_context_required": True,
        "e2_context_inherits_e1_conversation": False,
        "e2_prior_exposure_attestation_required": True,
        "e2_author_must_not_open_e1_artifacts": True,
        "global_nonexposure_machine_authenticated": False,
        "exact_graph_match_is_sole_correctness_target": False,
        "operator_vocabulary_selected": False,
        "operator_labels_are_record_local": True,
        "grounding_evaluated": False,
        "execution_evaluated": False,
        "answer_recovery_evaluated": False,
        "full_duplicate_review_required": False,
        "authoring_uses_stage_specific_partition_packets": True,
        "archival_view_source_bindings_exposed_to_authors": False,
    }


def open_operator_authoring_contract() -> dict[str, Any]:
    """Return the exact, vocabulary-neutral E2 authoring contract."""

    return {
        "notation_id": OPEN_NOTATION_ID,
        "notation_kind": "record_local_open_descriptive_labels",
        "operator_labels_record_local": True,
        "operator_labels_are_cross_record_taxonomy_keys": False,
        "operator_vocabulary_selected": False,
        "final_operator_vocabulary_selected": False,
        "preserved_candidate_vocabularies_consulted": False,
        "operator_granularity_empirically_open": True,
        "multiple_valid_realizations_allowed": True,
        "exact_graph_match_is_sole_correctness_target": False,
    }


def _visibility_contract() -> dict[str, Any]:
    return {
        "allowed_authoring_inputs": [
            "stage_prompt_and_output_schema",
            "opaque_record_identity_provenance_and_fixed_output_bindings",
            "question_text",
            "frozen_question_only_answer_spec_primary_and_preserved_alternative_backbones",
            "full_pinned_table_rows_and_cells",
            "table_link_reachable_pinned_document_text",
        ],
        "excluded_anchoring_metadata": [
            "candidate_source_record_status",
            "candidate_uncertainty_label",
            "cross_record_canonical_family_graph",
        ],
        "official_question_source_projection": ["question_id", "question", "table_id"],
        "linked_document_scope": "all_document_ids_reachable_from_any_table_header_or_data_cell_link",
        "question_or_answer_guided_environment_pruning": False,
        "environment_truncation": "none",
        "forbidden_authoring_inputs": [
            "official_answer_field_or_reference",
            "official_or_historical_trace",
            "historical_execution_graph",
            "prior_coarse_medium_fine_operator_proposal",
            "oracle_document_selection",
            "grounding_label",
            "execution_result",
            "answer_recovery_result",
        ],
        "environment_may_naturally_contain_answer_bearing_facts": True,
        "dataset_provided_question_table_binding": True,
        "table_retrieval_evaluated": False,
        "full_table_link_closure_supplied": True,
        "machine_authentication_scope": "exact_projection_and_bound_artifacts_not_global_human_nonexposure",
    }


def _analysis_contract() -> dict[str, Any]:
    return {
        "prevalence_estimation_authorized": False,
        "sample_design": "rarity_overweighted_coverage_stress_not_probability_sample",
        "metrics": [
            "e1_primary_and_alternative_variant_statuses_and_alt_rescue",
            "e1_by_e2_status_cross_tab_diagnostic_not_accuracy",
            "semantic_to_operator_node_edge_and_depth_expansion",
            "one_to_one_one_to_many_many_to_one_many_to_many_mapping_counts",
            "environment_extension_operator_node_counts",
            "binding_slot_modality_counts",
            "realization_variation_axis_counts",
            "label_free_operator_structural_profile_counts",
            "within_family_structural_heterogeneity",
            "producer_partition_status_stratification",
        ],
        "record_local_label_recurrence_analysis_allowed": False,
        "label_normalization_status": "deferred",
        "unlabeled_structural_profile_is_exact_graph_isomorphism": False,
        "common_executable_graph_claim_allowed": False,
    }


def build_freeze_plan(args: argparse.Namespace) -> dict[str, Any]:
    _validate_paths(args)
    for path in _planned_outputs(args).values():
        if path.is_symlink() or path.exists():
            raise EnvironmentRealizationError(
                f"planned output exists before plan freeze: {_relative(path)}"
            )
    _schema_validator(args.view_schema)
    _schema_validator(args.adequacy_schema)
    _schema_validator(args.realization_schema)
    _schema_validator(args.outcome_schema)
    selection, selections, _, _, _ = _load_question_contract(args)
    source_manifest = read_json(args.source_manifest)
    if not isinstance(source_manifest, dict):
        raise EnvironmentRealizationError("source manifest must be an object")
    source_metadata = _source_metadata_contract(source_manifest)
    source_bindings = {
        label: _binding(path) for label, path in _source_inputs(args).items()
    }
    contract_bindings = {
        label: _binding(path) for label, path in _contract_inputs(args).items()
    }
    implementation_commit = git_tracked_commit_identity(
        ROOT, list(_contract_inputs(args).values())
    )
    source_commit = git_tracked_commit_identity(ROOT, list(_source_inputs(args).values()))
    routing = _routing(selections, args)
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "status": "frozen_before_selected_raw_environment_access_and_all_planned_outputs",
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "implementation_commit": implementation_commit,
        "source_commit": source_commit,
        "source_artifacts": source_bindings,
        "contract_artifacts": contract_bindings,
        "official_source_contract": source_metadata,
        "visibility_contract": _visibility_contract(),
        "analysis_contract": _analysis_contract(),
        "stage_contract": _freeze_contract(),
        "model_provenance_contract": MODEL_PROVENANCE,
        "routing_contract": routing,
        "planned_outputs": {
            label: {"repository_relative_path": _relative(path)}
            for label, path in _planned_outputs(args).items()
        },
        "expected_result": {
            "selected_question_count": EXPECTED_QUESTION_COUNT,
            "selected_family_count": EXPECTED_FAMILY_COUNT,
            "selected_question_ids": selection["selected_question_ids"],
            "selected_question_ids_ordered_sha256": EXPECTED_SELECTED_ORDERED_SHA256,
            "selected_question_ids_set_sha256": EXPECTED_SELECTED_SET_SHA256,
            "e1_record_count": EXPECTED_QUESTION_COUNT,
            "e2_record_count": EXPECTED_QUESTION_COUNT,
            "outcome_record_count": EXPECTED_QUESTION_COUNT,
            "evaluated_signals": [
                "backbone_adequacy",
                "environment_operator_realization",
            ],
            "not_evaluated_signals": ["grounding", "execution", "answer_recovery"],
        },
    }


def _verify_commit_artifacts(
    commit: str, bindings: dict[str, Any], label: str
) -> None:
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise EnvironmentRealizationError(f"{label} is not a full lowercase Git commit")
    ancestor = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", commit, "HEAD"],
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise EnvironmentRealizationError(f"{label} is not an ancestor of HEAD")
    for item in bindings.values():
        relative = item["repository_relative_path"]
        shown = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{commit}:{relative}"],
            capture_output=True,
            check=False,
        )
        if shown.returncode != 0 or sha256_bytes(shown.stdout) != item["sha256"]:
            raise EnvironmentRealizationError(
                f"{label} does not contain bound artifact bytes: {relative}"
            )


def validate_plan(args: argparse.Namespace) -> dict[str, Any]:
    _validate_paths(args)
    if args.plan.is_symlink() or not args.plan.is_file():
        raise EnvironmentRealizationError("representative environment plan is missing")
    plan = read_json(args.plan)
    if not isinstance(plan, dict):
        raise EnvironmentRealizationError("representative environment plan must be an object")
    selection, selections, _, _, _ = _load_question_contract(args)
    source_manifest = read_json(args.source_manifest)
    expected_sources = {
        label: _binding(path) for label, path in _source_inputs(args).items()
    }
    expected_contracts = {
        label: _binding(path) for label, path in _contract_inputs(args).items()
    }
    expected_identity = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "status": "frozen_before_selected_raw_environment_access_and_all_planned_outputs",
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "source_artifacts": expected_sources,
        "contract_artifacts": expected_contracts,
        "official_source_contract": _source_metadata_contract(source_manifest),
        "visibility_contract": _visibility_contract(),
        "analysis_contract": _analysis_contract(),
        "stage_contract": _freeze_contract(),
        "model_provenance_contract": MODEL_PROVENANCE,
        "routing_contract": _routing(selections, args),
        "planned_outputs": {
            label: {"repository_relative_path": _relative(path)}
            for label, path in _planned_outputs(args).items()
        },
        "expected_result": {
            "selected_question_count": EXPECTED_QUESTION_COUNT,
            "selected_family_count": EXPECTED_FAMILY_COUNT,
            "selected_question_ids": selection["selected_question_ids"],
            "selected_question_ids_ordered_sha256": EXPECTED_SELECTED_ORDERED_SHA256,
            "selected_question_ids_set_sha256": EXPECTED_SELECTED_SET_SHA256,
            "e1_record_count": EXPECTED_QUESTION_COUNT,
            "e2_record_count": EXPECTED_QUESTION_COUNT,
            "outcome_record_count": EXPECTED_QUESTION_COUNT,
            "evaluated_signals": [
                "backbone_adequacy",
                "environment_operator_realization",
            ],
            "not_evaluated_signals": ["grounding", "execution", "answer_recovery"],
        },
    }
    if set(plan) != {*expected_identity, "implementation_commit", "source_commit"}:
        raise EnvironmentRealizationError("plan top-level fields differ from the exact contract")
    for key, expected in expected_identity.items():
        if plan.get(key) != expected:
            raise EnvironmentRealizationError(f"plan field differs from live contract: {key}")
    _verify_commit_artifacts(plan.get("implementation_commit", ""), expected_contracts, "implementation_commit")
    _verify_commit_artifacts(plan.get("source_commit", ""), expected_sources, "source_commit")
    for path in (
        args.view_schema,
        args.adequacy_schema,
        args.realization_schema,
        args.outcome_schema,
    ):
        _schema_validator(path)
    return plan


def _latest_artifact_commit(path: Path, label: str) -> str:
    relative = _relative(path)
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", relative],
        capture_output=True,
        text=True,
        check=False,
    )
    commit = result.stdout.strip()
    if result.returncode != 0 or len(commit) != 40:
        raise EnvironmentRealizationError(f"{label} has no committed provenance")
    ancestor = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", commit, "HEAD"],
        capture_output=True,
        check=False,
    )
    shown = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{relative}"],
        capture_output=True,
        check=False,
    )
    if (
        ancestor.returncode != 0
        or shown.returncode != 0
        or path.is_symlink()
        or not path.is_file()
        or shown.stdout != path.read_bytes()
    ):
        raise EnvironmentRealizationError(f"{label} bytes are not immutable at its commit")
    return commit


def _commit_path_absent(commit: str, relative: str, label: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "-e", f"{commit}:{relative}"],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        raise EnvironmentRealizationError(f"{label} existed at forbidden commit: {relative}")
    if result.returncode not in {1, 128}:
        raise EnvironmentRealizationError(f"could not audit {label} absence: {relative}")


def verify_plan_freeze(args: argparse.Namespace, plan: dict[str, Any]) -> str:
    commit = _latest_artifact_commit(args.plan, "plan freeze")
    for label in ("implementation_commit", "source_commit"):
        result = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "merge-base",
                "--is-ancestor",
                plan[label],
                commit,
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise EnvironmentRealizationError(f"{label} is not an ancestor of plan freeze")
    planned = [
        item["repository_relative_path"] for item in plan["planned_outputs"].values()
    ]
    if len(planned) != len(set(planned)):
        raise EnvironmentRealizationError("plan contains duplicate output paths")
    for relative in planned:
        if relative.startswith("/") or ".." in Path(relative).parts or ":" in relative:
            raise EnvironmentRealizationError(f"unsafe planned output path: {relative!r}")
        _commit_path_absent(commit, relative, "planned output")
    return commit


def verify_view_freeze(args: argparse.Namespace, plan_freeze_commit: str) -> str:
    commit = _latest_artifact_commit(args.views_output, "environment view freeze")
    ancestor = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "merge-base",
            "--is-ancestor",
            plan_freeze_commit,
            commit,
        ],
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise EnvironmentRealizationError(
            "environment view freeze does not descend from the plan freeze"
        )
    for path in [
        args.views_output,
        args.views_manifest_output,
        args.routing_output,
        *args.e1_packets,
    ]:
        relative = _relative(path)
        shown = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{commit}:{relative}"],
            capture_output=True,
            check=False,
        )
        if (
            shown.returncode != 0
            or path.is_symlink()
            or not path.is_file()
            or shown.stdout != path.read_bytes()
        ):
            raise EnvironmentRealizationError(
                f"view freeze does not contain current prerequisite bytes: {relative}"
            )
    for path in [
        *args.e1_parts,
        args.e1_output,
        args.e1_bindings_output,
        *args.e2_packets,
        *args.e2_parts,
        args.e2_output,
        args.outcomes_output,
        args.checks_output,
        args.report_output,
        args.metrics_output,
        args.exposure_ledger_output,
        args.run_manifest_output,
    ]:
        _commit_path_absent(commit, _relative(path), "E1/E2/final output")
    return commit


def verify_e1_freeze(args: argparse.Namespace, view_freeze_commit: str) -> str:
    commit = _latest_artifact_commit(args.e1_output, "E1 adequacy freeze")
    ancestor = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "merge-base",
            "--is-ancestor",
            view_freeze_commit,
            commit,
        ],
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise EnvironmentRealizationError("E1 freeze does not descend from the view freeze")
    for path in [
        *args.e1_parts,
        args.e1_output,
        args.e1_bindings_output,
        *args.e2_packets,
        args.views_output,
        args.views_manifest_output,
        args.routing_output,
        *args.e1_packets,
    ]:
        relative = _relative(path)
        shown = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{commit}:{relative}"],
            capture_output=True,
            check=False,
        )
        if (
            shown.returncode != 0
            or path.is_symlink()
            or not path.is_file()
            or shown.stdout != path.read_bytes()
        ):
            raise EnvironmentRealizationError(
                f"E1 freeze does not contain current prerequisite bytes: {relative}"
            )
    for path in [
        *args.e2_parts,
        args.e2_output,
        args.outcomes_output,
        args.checks_output,
        args.report_output,
        args.metrics_output,
        args.exposure_ledger_output,
        args.run_manifest_output,
    ]:
        _commit_path_absent(commit, _relative(path), "E2/final output")
    return commit


def _canonical_record_sha256(record: dict[str, Any]) -> str:
    return canonical_json_sha256(record)


def _view_id(question_id: str) -> str:
    return f"representative_environment_view_v0_1:{question_id}"


def _assessment_id(question_id: str) -> str:
    return f"backbone_adequacy_v0_1:{question_id}"


def _realization_id(question_id: str) -> str:
    return f"open_operator_realization_v0_1:{question_id}"


def _outcome_id(question_id: str) -> str:
    return f"environment_outcome_v0_2:{question_id}"


def _e1_fixed_output_fields(
    view: dict[str, Any], producer_partition: str
) -> dict[str, Any]:
    return {
        "schema_version": ADEQUACY_SCHEMA_VERSION,
        "assessment_id": _assessment_id(view["question_id"]),
        "run_id": RUN_ID,
        "evidence_class": "ai_exploratory_non_human_non_gold",
        "producer_partition": producer_partition,
        "selection_id": SELECTION_ID,
        "selection_index": view["selection_index"],
        "question_id": view["question_id"],
        "family_id": view["family_id"],
        "contracted_signature_sha256": view["contracted_signature_sha256"],
        "input_view_id": view["view_id"],
        "input_view_payload_sha256": view["payload_sha256"],
        "visibility": "question_candidate_backbone_and_environment_no_operator_realization_answer_trace_grounding_execution_or_prior_proposals",
        "global_nonexposure_machine_authenticated": False,
        "operator_realization_seen": False,
        "downstream_status": E1_DOWNSTREAM_NOT_EVALUATED,
    }


def _e2_fixed_output_fields(
    view: dict[str, Any],
    producer_partition: str,
    backbone_assessment_binding: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": REALIZATION_SCHEMA_VERSION,
        "realization_id": _realization_id(view["question_id"]),
        "run_id": RUN_ID,
        "evidence_class": "ai_exploratory_non_human_non_gold",
        "producer_partition": producer_partition,
        "selection_id": SELECTION_ID,
        "selection_index": view["selection_index"],
        "question_id": view["question_id"],
        "family_id": view["family_id"],
        "contracted_signature_sha256": view["contracted_signature_sha256"],
        "input_view_id": view["view_id"],
        "input_view_payload_sha256": view["payload_sha256"],
        "backbone_assessment_binding": backbone_assessment_binding,
        "visibility": "question_candidate_backbone_and_environment_with_adequacy_hash_only_no_adequacy_content_answer_trace_grounding_execution_or_prior_proposals",
        "global_nonexposure_machine_authenticated": False,
        "authoring_contract": open_operator_authoring_contract(),
        "downstream_status": E2_DOWNSTREAM_NOT_EVALUATED,
    }


def _portable_source_binding(
    *, source_id: str, commit: str, portable_path: str, sha256: str
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "pinned_commit": commit,
        "portable_path": portable_path,
        "sha256": sha256,
    }


def build_environment_views(
    args: argparse.Namespace,
    plan: dict[str, Any],
    plan_freeze_commit: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    if args.source_cache_root is None:
        raise EnvironmentRealizationError("--source-cache-root is required to materialize views")
    selection, selections, family_by_id, record_by_id, _ = _load_question_contract(args)
    source_manifest = read_json(args.source_manifest)
    expected_questions = {
        question_id: record_by_id[question_id]["question"]
        for question_id in selection["selected_question_ids"]
    }
    source_bundle = environment_source.load_selected_environment_bundle(
        args.source_cache_root,
        plan["official_source_contract"],
        selection["selected_question_ids"],
        expected_questions,
        ROOT,
    )
    expected_source_verification = _expected_source_verification(
        plan["official_source_contract"]
    )
    if source_bundle.get("source_verification") != expected_source_verification:
        raise EnvironmentRealizationError(
            "observed source verification differs from the frozen official pins"
        )
    source_questions = source_bundle["questions"]
    if (
        [item.get("question_id") for item in source_questions]
        != selection["selected_question_ids"]
        or [item.get("selection_index") for item in source_questions]
        != list(range(1, EXPECTED_QUESTION_COUNT + 1))
    ):
        raise EnvironmentRealizationError(
            "official question projection differs from the frozen selection order"
        )
    source_question_by_id = {item["question_id"]: item for item in source_questions}
    environment_by_table = {
        item["table_id"]: item for item in source_bundle["environment_resources"]
    }
    selected_artifacts = {
        (item["source_id"], item["repository_relative_path"]): item["sha256"]
        for item in source_bundle["selected_source_artifacts"]
    }
    question_contract = plan["official_source_contract"]["question_source"]
    linked_contract = plan["official_source_contract"]["linked_environment_source"]
    view_validator = _schema_validator(args.view_schema)
    views: list[dict[str, Any]] = []
    for item in selections:
        question_id = item["question_id"]
        source_record = record_by_id[question_id]
        source_question = source_question_by_id[question_id]
        table_id = source_question["table_id"]
        source_environment = environment_by_table.get(table_id)
        if source_environment is None:
            raise EnvironmentRealizationError(
                f"selected environment resource is missing for table {table_id!r}"
            )
        payload = {
            "question_context": {
                "question": source_record["question"],
                "question_view_sha256": source_record["question_view_sha256"],
            },
            "candidate_backbone_context": {
                "source_record_sha256": _canonical_record_sha256(source_record),
                "question_only_answer_spec": source_record["answer_spec"],
                "primary_graph": source_record["primary_graph"],
                "alternative_graphs": source_record["alternative_graphs"],
                "candidate_non_gold": True,
            },
            "environment": source_environment,
        }
        table_path = f"tables_tok/{table_id}.json"
        request_path = f"request_tok/{table_id}.json"
        try:
            table_sha = selected_artifacts[
                ("hybridqa_linked_tables_and_passages", table_path)
            ]
            request_sha = selected_artifacts[
                ("hybridqa_linked_tables_and_passages", request_path)
            ]
        except KeyError as exc:
            raise EnvironmentRealizationError(
                f"selected source inventory lacks environment blob {exc.args[0]!r}"
            ) from exc
        view = {
            "schema_version": VIEW_SCHEMA_VERSION,
            "view_id": _view_id(question_id),
            "run_id": RUN_ID,
            "selection_id": SELECTION_ID,
            "selection_index": item["selection_index"],
            "question_id": question_id,
            "family_id": item["family_id"],
            "contracted_signature_sha256": item["contracted_signature_sha256"],
            "visibility": "question_candidate_backbone_full_table_and_table_link_closure_no_answer_trace_grounding_execution_or_operator_proposals",
            "payload": payload,
            "payload_sha256": canonical_json_sha256(payload),
            "source_bindings": {
                "representative_selection": {
                    **_binding(args.selection),
                    "selected_question_count": EXPECTED_QUESTION_COUNT,
                    "selected_question_ids_ordered_sha256": EXPECTED_SELECTED_ORDERED_SHA256,
                    "selected_question_ids_set_sha256": EXPECTED_SELECTED_SET_SHA256,
                },
                "semantic_backbone_records": _binding(args.records),
                "candidate_families": _binding(args.families),
                "official_questions": {
                    **_portable_source_binding(
                        source_id="hybridqa_questions_and_code",
                        commit=question_contract["pinned_commit"],
                        portable_path=question_contract["dev_artifact"][
                            "repository_relative_path"
                        ],
                        sha256=question_contract["dev_artifact"]["sha256"],
                    ),
                    "projection_allowlist": ["question_id", "question", "table_id"],
                },
                "table_file": _portable_source_binding(
                    source_id="hybridqa_linked_tables_and_passages",
                    commit=linked_contract["pinned_commit"],
                    portable_path=table_path,
                    sha256=table_sha,
                ),
                "request_file": _portable_source_binding(
                    source_id="hybridqa_linked_tables_and_passages",
                    commit=linked_contract["pinned_commit"],
                    portable_path=request_path,
                    sha256=request_sha,
                ),
            },
            "evidence_boundary": {
                "evidence_class": "ai_exploratory_non_human_non_gold",
                "human_evidence_count": 0,
                "gold_claimed": False,
                "official_answer_annotation_in_view": False,
                "official_answer_or_trace_fields_in_view": False,
                "official_dev_blob_read_for_question_to_table_mapping": True,
                "answer_field_projected": False,
                "trace_or_reference_artifact_read": False,
                "official_trace_in_view": False,
                "historical_graph_in_view": False,
                "operator_proposal_in_view": False,
                "dataset_provided_question_table_binding": True,
                "table_retrieval_evaluated": False,
                "full_table_link_closure_supplied": True,
                "grounding_evaluated": False,
                "execution_evaluated": False,
                "answer_recovery_evaluated": False,
                "modeling_ready_claimed": False,
            },
        }
        errors = _validation_errors(view_validator, view, f"view[{item['selection_index']}]")
        if errors:
            raise EnvironmentRealizationError("view schema validation failed: " + " | ".join(errors[:20]))
        views.append(view)
    if [view["question_id"] for view in views] != selection["selected_question_ids"]:
        raise EnvironmentRealizationError("materialized view order differs from frozen selection")
    views_bytes = jsonl_file_bytes(views)
    routing = copy.deepcopy(plan["routing_contract"])
    manifest = {
        "schema_version": "representative_environment_views_manifest_v0_1",
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "status": "materialized_from_pinned_git_blobs",
        "contract_freeze_commit": plan_freeze_commit,
        "implementation_commit": plan["implementation_commit"],
        "source_commit": plan["source_commit"],
        "plan_artifact": _binding(args.plan),
        "views_artifact": {
            "repository_relative_path": _relative(args.views_output),
            "record_count": len(views),
            "bytes": len(views_bytes),
            "sha256": sha256_bytes(views_bytes),
        },
        "selected_question_ids": [view["question_id"] for view in views],
        "selected_question_ids_ordered_sha256": canonical_json_sha256(
            [view["question_id"] for view in views]
        ),
        "selected_question_ids_set_sha256": canonical_string_set_sha256(
            [view["question_id"] for view in views]
        ),
        "official_source_contract": plan["official_source_contract"],
        "source_verification": expected_source_verification,
        "source_verification_stable_during_extraction": True,
        "selected_source_artifacts": source_bundle["selected_source_artifacts"],
        "visibility_contract": plan["visibility_contract"],
        "machine_local_absolute_path_recorded": False,
        "question_or_answer_guided_environment_pruning": False,
        "official_dev_blob_read_for_question_to_table_mapping": True,
        "official_answer_or_trace_fields_in_views": False,
        "answer_field_projected": False,
        "trace_or_reference_artifact_read": False,
        "dataset_provided_question_table_binding": True,
        "table_retrieval_evaluated": False,
        "full_table_link_closure_supplied": True,
        "human_evidence_count": 0,
        "gold_claimed": False,
    }
    return views, manifest, routing


def _environment_projection_errors(environment: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(environment, dict):
        return ["environment is not an object"]
    columns = environment.get("columns")
    rows = environment.get("rows")
    documents = environment.get("linked_documents")
    if not isinstance(columns, list) or not isinstance(rows, list) or not isinstance(
        documents, list
    ):
        return ["environment columns/rows/documents are malformed"]
    if [column.get("column_index") for column in columns if isinstance(column, dict)] != list(
        range(len(columns))
    ):
        errors.append("column indices are not contiguous source order")
    linked_ids: set[str] = set()
    for column in columns:
        if isinstance(column, dict) and isinstance(
            column.get("linked_document_ids"), list
        ):
            linked_ids.update(column["linked_document_ids"])
    if [row.get("row_index") for row in rows if isinstance(row, dict)] != list(
        range(len(rows))
    ):
        errors.append("row indices are not contiguous source order")
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("cells"), list):
            errors.append(f"row {row_index} cells are malformed")
            continue
        cells = row["cells"]
        if len(cells) != len(columns):
            errors.append(f"row {row_index} width differs from columns")
        if [cell.get("column_index") for cell in cells if isinstance(cell, dict)] != list(
            range(len(cells))
        ):
            errors.append(f"row {row_index} cell indices are not contiguous")
        for cell in cells:
            if isinstance(cell, dict) and isinstance(
                cell.get("linked_document_ids"), list
            ):
                linked_ids.update(cell["linked_document_ids"])
    document_ids = [
        item.get("document_id") for item in documents if isinstance(item, dict)
    ]
    if len(document_ids) != len(documents) or any(
        not isinstance(item, str) for item in document_ids
    ):
        errors.append("linked document IDs are malformed")
    else:
        if len(document_ids) != len(set(document_ids)):
            errors.append("linked document IDs are not unique")
        if document_ids != sorted(document_ids, key=lambda value: value.encode("utf-8")):
            errors.append("linked documents are not in unsigned UTF-8 ID order")
        if set(document_ids) != linked_ids:
            errors.append("linked documents are not the exact table-link closure")
    expected_scope = {
        "table_scope": "full_selected_question_table",
        "document_scope": "table_link_closure",
        "question_or_answer_guided_pruning": False,
        "oracle_document_selection": False,
        "truncation": "none",
        "external_retrieval": False,
        "dataset_provided_question_table_binding": True,
        "table_retrieval_evaluated": False,
        "full_table_link_closure_supplied": True,
    }
    if environment.get("scope_contract") != expected_scope:
        errors.append("environment scope contract differs")
    if environment.get("source_split") != "dev":
        errors.append("environment source split differs")
    return errors


def load_materialized_views(
    args: argparse.Namespace, plan: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    if any(
        path.is_symlink() or not path.is_file()
        for path in (args.views_output, args.views_manifest_output, args.routing_output)
    ):
        raise EnvironmentRealizationError("materialized environment view bundle is incomplete")
    views = list(iter_json_records(args.views_output))
    manifest = read_json(args.views_manifest_output)
    routing = read_json(args.routing_output)
    validator = _schema_validator(args.view_schema)
    errors = [
        error
        for index, view in enumerate(views, 1)
        for error in _validation_errors(validator, view, f"view[{index}]")
    ]
    if errors:
        raise EnvironmentRealizationError("view validation failed: " + " | ".join(errors[:20]))
    canonical_views_bytes = jsonl_file_bytes(views)
    if args.views_output.read_bytes() != canonical_views_bytes:
        raise EnvironmentRealizationError(
            "environment views are not in the canonical project JSONL serialization"
        )
    expected_ids = plan["expected_result"]["selected_question_ids"]
    if (
        len(views) != EXPECTED_QUESTION_COUNT
        or [view.get("selection_index") for view in views]
        != list(range(1, EXPECTED_QUESTION_COUNT + 1))
        or [view.get("question_id") for view in views] != expected_ids
        or any(
            view.get("payload_sha256") != canonical_json_sha256(view.get("payload"))
            for view in views
        )
    ):
        raise EnvironmentRealizationError("view order, identity, or payload hash mismatch")
    selection, selections, _, record_by_id, _ = _load_question_contract(args)
    question_contract = plan["official_source_contract"]["question_source"]
    linked_contract = plan["official_source_contract"]["linked_environment_source"]
    expected_selection_binding = {
        **_binding(args.selection),
        "selected_question_count": EXPECTED_QUESTION_COUNT,
        "selected_question_ids_ordered_sha256": EXPECTED_SELECTED_ORDERED_SHA256,
        "selected_question_ids_set_sha256": EXPECTED_SELECTED_SET_SHA256,
    }
    expected_official_questions = {
        **_portable_source_binding(
            source_id="hybridqa_questions_and_code",
            commit=question_contract["pinned_commit"],
            portable_path=question_contract["dev_artifact"][
                "repository_relative_path"
            ],
            sha256=question_contract["dev_artifact"]["sha256"],
        ),
        "projection_allowlist": ["question_id", "question", "table_id"],
    }
    source_inventory = [
        {
            "source_id": "hybridqa_questions_and_code",
            "repository_relative_path": question_contract["dev_artifact"][
                "repository_relative_path"
            ],
            "sha256": question_contract["dev_artifact"]["sha256"],
        }
    ]
    environments_by_table: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for selection_item, view in zip(selections, views):
        question_id = selection_item["question_id"]
        source_record = record_by_id[question_id]
        expected_wrapper = {
            "view_id": _view_id(question_id),
            "run_id": RUN_ID,
            "selection_id": SELECTION_ID,
            "selection_index": selection_item["selection_index"],
            "question_id": question_id,
            "family_id": selection_item["family_id"],
            "contracted_signature_sha256": selection_item[
                "contracted_signature_sha256"
            ],
            "visibility": "question_candidate_backbone_full_table_and_table_link_closure_no_answer_trace_grounding_execution_or_operator_proposals",
        }
        for key, expected in expected_wrapper.items():
            if view.get(key) != expected:
                raise EnvironmentRealizationError(
                    f"view {question_id} differs from frozen identity field {key}"
                )
        expected_question_context = {
            "question": source_record["question"],
            "question_view_sha256": source_record["question_view_sha256"],
        }
        expected_backbone_context = {
            "source_record_sha256": canonical_json_sha256(source_record),
            "question_only_answer_spec": source_record["answer_spec"],
            "primary_graph": source_record["primary_graph"],
            "alternative_graphs": source_record["alternative_graphs"],
            "candidate_non_gold": True,
        }
        payload = view["payload"]
        if (
            payload.get("question_context") != expected_question_context
            or payload.get("candidate_backbone_context")
            != expected_backbone_context
        ):
            raise EnvironmentRealizationError(
                f"view {question_id} question/backbone projection differs from frozen input"
            )
        environment = payload["environment"]
        environment_errors = _environment_projection_errors(environment)
        if environment_errors:
            raise EnvironmentRealizationError(
                f"view {question_id} environment invariant failed: "
                + " | ".join(environment_errors[:20])
            )
        table_id = environment["table_id"]
        table_path = f"tables_tok/{table_id}.json"
        request_path = f"request_tok/{table_id}.json"
        bindings = view["source_bindings"]
        fixed_bindings = {
            "representative_selection": expected_selection_binding,
            "semantic_backbone_records": _binding(args.records),
            "candidate_families": _binding(args.families),
            "official_questions": expected_official_questions,
        }
        for key, expected in fixed_bindings.items():
            if bindings.get(key) != expected:
                raise EnvironmentRealizationError(
                    f"view {question_id} source binding differs: {key}"
                )
        for key, portable_path in (
            ("table_file", table_path),
            ("request_file", request_path),
        ):
            binding = bindings[key]
            if (
                binding.get("source_id")
                != "hybridqa_linked_tables_and_passages"
                or binding.get("pinned_commit") != linked_contract["pinned_commit"]
                or binding.get("portable_path") != portable_path
            ):
                raise EnvironmentRealizationError(
                    f"view {question_id} environment binding differs: {key}"
                )
            source_inventory.append(
                {
                    "source_id": binding["source_id"],
                    "repository_relative_path": binding["portable_path"],
                    "sha256": binding["sha256"],
                }
            )
        table_value = (
            environment,
            {
                "table_sha256": bindings["table_file"]["sha256"],
                "request_sha256": bindings["request_file"]["sha256"],
            },
        )
        previous = environments_by_table.get(table_id)
        if previous is not None and previous != table_value:
            raise EnvironmentRealizationError(
                f"repeated table {table_id!r} has inconsistent projected bytes or bindings"
            )
        environments_by_table[table_id] = table_value
    expected_source_inventory = environment_source.deduplicate_source_artifacts(
        source_inventory
    )
    views_bytes = args.views_output.read_bytes()
    expected_manifest_fields = {
        "schema_version": "representative_environment_views_manifest_v0_1",
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "status": "materialized_from_pinned_git_blobs",
        "contract_freeze_commit": _latest_artifact_commit(
            args.plan, "plan freeze"
        ),
        "implementation_commit": plan["implementation_commit"],
        "source_commit": plan["source_commit"],
        "plan_artifact": _binding(args.plan),
        "views_artifact": {
            "repository_relative_path": _relative(args.views_output),
            "record_count": EXPECTED_QUESTION_COUNT,
            "bytes": len(views_bytes),
            "sha256": sha256_bytes(views_bytes),
        },
        "selected_question_ids": expected_ids,
        "selected_question_ids_ordered_sha256": EXPECTED_SELECTED_ORDERED_SHA256,
        "selected_question_ids_set_sha256": EXPECTED_SELECTED_SET_SHA256,
        "official_source_contract": plan["official_source_contract"],
        "source_verification": _expected_source_verification(
            plan["official_source_contract"]
        ),
        "source_verification_stable_during_extraction": True,
        "selected_source_artifacts": expected_source_inventory,
        "visibility_contract": plan["visibility_contract"],
        "machine_local_absolute_path_recorded": False,
        "question_or_answer_guided_environment_pruning": False,
        "official_dev_blob_read_for_question_to_table_mapping": True,
        "official_answer_or_trace_fields_in_views": False,
        "answer_field_projected": False,
        "trace_or_reference_artifact_read": False,
        "dataset_provided_question_table_binding": True,
        "table_retrieval_evaluated": False,
        "full_table_link_closure_supplied": True,
        "human_evidence_count": 0,
        "gold_claimed": False,
    }
    if not isinstance(manifest, dict):
        raise EnvironmentRealizationError("environment view manifest must be an object")
    if set(manifest) != set(expected_manifest_fields):
        raise EnvironmentRealizationError(
            "environment view manifest top-level fields differ from the exact contract"
        )
    for key, expected in expected_manifest_fields.items():
        if manifest.get(key) != expected:
            raise EnvironmentRealizationError(f"environment view manifest mismatch: {key}")
    if routing != plan["routing_contract"]:
        raise EnvironmentRealizationError("live producer routing differs from the frozen plan")
    expected_packets = build_e1_authoring_packets(views, routing)
    for index, (path, expected_records) in enumerate(
        zip(args.e1_packets, expected_packets), 1
    ):
        if (
            path.is_symlink()
            or not path.is_file()
            or path.read_bytes() != jsonl_file_bytes(expected_records)
        ):
            raise EnvironmentRealizationError(
                f"E1 authoring packet {index} differs from frozen routing/views"
            )
    return views, manifest, routing


def _partition_assignments(routing: dict[str, Any]) -> dict[str, dict[str, Any]]:
    partitions = routing.get("partitions")
    if not isinstance(partitions, list) or len(partitions) != PARTITION_COUNT:
        raise EnvironmentRealizationError("routing has the wrong partition inventory")
    result: dict[str, dict[str, Any]] = {}
    for item in partitions:
        if not isinstance(item, dict) or not isinstance(
            item.get("routing_partition_id"), str
        ):
            raise EnvironmentRealizationError("routing partition is malformed")
        result[item["routing_partition_id"]] = item
    return result


def build_e1_authoring_packets(
    views: list[dict[str, Any]], routing: dict[str, Any]
) -> list[list[dict[str, Any]]]:
    view_by_question = {view["question_id"]: view for view in views}
    assignments = _partition_assignments(routing)
    packets: list[list[dict[str, Any]]] = []
    for index in range(1, PARTITION_COUNT + 1):
        assignment = assignments[f"routing_partition_{index:02d}"]
        packets.append(
            [
                {
                    "schema_version": "backbone_adequacy_authoring_input_v0_1",
                    "producer_partition": assignment["e1_producer_partition"],
                    "view": _authoring_view(view_by_question[question_id]),
                    "fixed_output_fields": _e1_fixed_output_fields(
                        view_by_question[question_id],
                        assignment["e1_producer_partition"],
                    ),
                    "authoring_context_contract": {
                        "packet_contains_only_assigned_records": True,
                        "cross_record_semantic_or_status_inference_prohibited": True,
                        "fresh_context_required": True,
                        "inherits_prior_conversation": False,
                        "prior_record_exposure_attestation_required": True,
                        "source_repository_paths_supplied": False,
                        "later_stage_content_supplied": False,
                        "global_nonexposure_machine_authenticated": False,
                    },
                }
                for question_id in assignment["question_ids"]
            ]
        )
    return packets


def _authoring_view(view: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "representative_environment_authoring_view_v0_1",
        "view_id": view["view_id"],
        "run_id": view["run_id"],
        "selection_id": view["selection_id"],
        "selection_index": view["selection_index"],
        "question_id": view["question_id"],
        "family_id": view["family_id"],
        "contracted_signature_sha256": view["contracted_signature_sha256"],
        "visibility": view["visibility"],
        "payload": view["payload"],
        "payload_sha256": view["payload_sha256"],
    }


def build_e2_authoring_packets(
    views: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    *,
    combined_e1_sha256: str,
    routing: dict[str, Any],
) -> list[list[dict[str, Any]]]:
    view_by_question = {view["question_id"]: view for view in views}
    assessment_by_question = {
        assessment["question_id"]: assessment for assessment in assessments
    }
    assignments = _partition_assignments(routing)
    packets: list[list[dict[str, Any]]] = []
    for index in range(1, PARTITION_COUNT + 1):
        assignment = assignments[f"routing_partition_{index:02d}"]
        producer_partition = assignment["e2_producer_partition"]
        records: list[dict[str, Any]] = []
        for question_id in assignment["question_ids"]:
            assessment = assessment_by_question[question_id]
            assessment_binding = {
                "binding_mode": "hash_only",
                "assessment_artifact_sha256": combined_e1_sha256,
                "assessment_record_sha256": canonical_json_sha256(assessment),
                "assessment_content_in_authoring_input": False,
            }
            records.append(
                {
                    "schema_version": "open_operator_authoring_input_v0_1",
                    "producer_partition": producer_partition,
                    "view": _authoring_view(view_by_question[question_id]),
                    "fixed_output_fields": _e2_fixed_output_fields(
                        view_by_question[question_id],
                        producer_partition,
                        assessment_binding,
                    ),
                    "authoring_context_contract": {
                        "fresh_context_required": True,
                        "inherits_e1_conversation": False,
                        "inherits_prior_conversation": False,
                        "prior_record_exposure_attestation_required": True,
                        "e1_artifact_must_not_be_opened": True,
                        "source_repository_paths_supplied": False,
                        "global_nonexposure_machine_authenticated": False,
                    },
                }
            )
        packets.append(records)
    return packets


def _graph_node_ids(view: dict[str, Any]) -> list[str]:
    graph = view["payload"]["candidate_backbone_context"]["primary_graph"]
    return [node["node_id"] for node in graph["nodes"]]


def _backbone_variants(view: dict[str, Any]) -> dict[str, dict[str, Any]]:
    context = view["payload"]["candidate_backbone_context"]
    variants = {"primary": context["primary_graph"]}
    for alternative in context["alternative_graphs"]:
        variants[alternative["alternative_id"]] = alternative["graph"]
    return variants


def _validate_e1_semantics(record: dict[str, Any], view: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "assessment_id": _assessment_id(view["question_id"]),
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "selection_index": view["selection_index"],
        "question_id": view["question_id"],
        "family_id": view["family_id"],
        "contracted_signature_sha256": view["contracted_signature_sha256"],
        "input_view_id": view["view_id"],
        "input_view_payload_sha256": view["payload_sha256"],
        "visibility": "question_candidate_backbone_and_environment_no_operator_realization_answer_trace_grounding_execution_or_prior_proposals",
        "operator_realization_seen": False,
        "downstream_status": E1_DOWNSTREAM_NOT_EVALUATED,
        "global_nonexposure_machine_authenticated": False,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            errors.append(f"{key} differs from its frozen input binding")
    status = record.get("overall_status")
    adequate = record.get("candidate_backbone_adequate")
    if status not in E1_STATUSES:
        errors.append("overall_status is unsupported")
    variants = _backbone_variants(view)
    variant_order = list(variants)
    node_ids_by_variant: dict[str, set[str]] = {
        variant_id: {node["node_id"] for node in graph["nodes"]}
        for variant_id, graph in variants.items()
    }
    assessments = record.get("variant_assessments")
    if not isinstance(assessments, list) or [
        item.get("backbone_variant_id") for item in assessments if isinstance(item, dict)
    ] != variant_order:
        errors.append("variant assessments do not exactly follow primary/alternative order")
        return errors
    variant_statuses: list[str] = []
    for assessment in assessments:
        variant_id = assessment["backbone_variant_id"]
        variant_status = assessment.get("status")
        variant_statuses.append(variant_status)
        graph_errors, _ = _graph_contract_errors(
            variants[variant_id], f"E1 backbone variant {variant_id}"
        )
        errors.extend(graph_errors)
        changes = assessment.get("required_changes", [])
        change_ids = [
            item.get("change_id") for item in changes if isinstance(item, dict)
        ]
        if len(change_ids) != len(changes) or len(change_ids) != len(set(change_ids)):
            errors.append(f"{variant_id} required change IDs are missing or non-unique")
        for change in changes:
            if isinstance(change, dict) and not set(
                change.get("backbone_node_ids", [])
            ) <= node_ids_by_variant[variant_id]:
                errors.append(f"{variant_id} required change references an unknown node")
        clarifications = assessment.get("semantic_clarifications", [])
        clarification_ids = [
            item.get("clarification_id")
            for item in clarifications
            if isinstance(item, dict)
        ]
        if len(clarification_ids) != len(clarifications) or len(
            clarification_ids
        ) != len(set(clarification_ids)):
            errors.append(
                f"{variant_id} semantic clarification IDs are missing or non-unique"
            )
        for clarification in clarifications:
            if isinstance(clarification, dict) and not set(
                clarification.get("related_backbone_node_ids", [])
            ) <= node_ids_by_variant[variant_id]:
                errors.append(
                    f"{variant_id} semantic clarification references an unknown node"
                )
        if (
            assessment.get("environment_interpretation_effect")
            == "reveals_semantic_mismatch"
            and variant_status == "adequate"
        ):
            errors.append(
                f"{variant_id} cannot be adequate when the environment reveals a semantic mismatch"
            )
    if "adequate" in variant_statuses:
        expected_status, expected_adequate = "adequate", True
    elif "partially_adequate" in variant_statuses:
        expected_status, expected_adequate = "partially_adequate", False
    elif "indeterminate" in variant_statuses:
        expected_status, expected_adequate = "indeterminate", None
    else:
        expected_status, expected_adequate = "inadequate", False
    if status != expected_status or adequate is not expected_adequate:
        errors.append("top-level E1 status does not follow the frozen variant aggregation")
    interpretations = record.get("additional_semantic_interpretations", [])
    interpretation_ids = [
        item.get("interpretation_id")
        for item in interpretations
        if isinstance(item, dict)
    ]
    if len(interpretation_ids) != len(interpretations) or len(
        interpretation_ids
    ) != len(set(interpretation_ids)):
        errors.append("additional interpretation IDs are missing or non-unique")
    for interpretation in interpretations:
        if isinstance(interpretation, dict) and not set(
            interpretation.get("related_backbone_variant_ids", [])
        ) <= set(variant_order):
            errors.append("additional interpretation references an unknown variant")
    delivery = record.get("input_delivery")
    delivery_complete = delivery == {
        "view_fully_consumed": True,
        "completeness_status": "complete",
    }
    if not delivery_complete and status != "indeterminate":
        errors.append("incomplete E1 input delivery requires an indeterminate result")
    exposure = record.get("author_prior_exposure_to_record_before_packet")
    if exposure != "procedurally_attested_none" and status != "indeterminate":
        errors.append(
            "prior or unknown E1 record exposure permits only an indeterminate result"
        )
    return errors


def _load_stage_parts(
    paths: Iterable[Path],
    *,
    stage: str,
    validator: Draft202012Validator,
    views: list[dict[str, Any]],
    routing: dict[str, Any],
    e1_by_question: dict[str, dict[str, Any]] | None = None,
    e1_artifact_sha256: str | None = None,
) -> list[dict[str, Any]]:
    view_by_question = {view["question_id"]: view for view in views}
    assignments = _partition_assignments(routing)
    records: list[dict[str, Any]] = []
    paths_list = list(paths)
    for partition_index, path in enumerate(paths_list, 1):
        partition_id = f"routing_partition_{partition_index:02d}"
        assignment = assignments[partition_id]
        if path.is_symlink() or not path.is_file():
            raise EnvironmentRealizationError(f"{stage} part is missing: {_relative(path)}")
        part = list(iter_json_records(path))
        expected_ids = assignment["question_ids"]
        if [item.get("question_id") for item in part] != expected_ids:
            raise EnvironmentRealizationError(f"{stage} {partition_id} ID order mismatch")
        for record in part:
            question_id = record.get("question_id")
            view = view_by_question.get(question_id)
            if not isinstance(view, dict):
                raise EnvironmentRealizationError(f"{stage} contains unknown question_id")
            schema_errors = _validation_errors(
                validator, record, f"{stage}/{partition_id}/{question_id}"
            )
            if schema_errors:
                semantic_errors = []
            elif stage == "e1":
                semantic_errors = _validate_e1_semantics(record, view)
            else:
                if (
                    e1_by_question is None
                    or e1_artifact_sha256 is None
                ):
                    raise EnvironmentRealizationError("E2 validation lacks frozen E1 bindings")
                semantic_errors = _validate_e2_semantics(
                    record,
                    view,
                    e1_by_question[question_id],
                    e1_artifact_sha256,
                )
            expected_producer = assignment[f"{stage}_producer_partition"]
            if record.get("producer_partition") != expected_producer:
                semantic_errors.append("producer_partition differs from frozen routing")
            if schema_errors or semantic_errors:
                raise EnvironmentRealizationError(
                    f"{stage} record validation failed for {question_id}: "
                    + " | ".join((schema_errors + semantic_errors)[:20])
                )
        records.extend(part)
    by_question = {record["question_id"]: record for record in records}
    expected_order = [view["question_id"] for view in views]
    if len(records) != EXPECTED_QUESTION_COUNT or len(by_question) != EXPECTED_QUESTION_COUNT:
        raise EnvironmentRealizationError(f"{stage} records are not exactly 71 unique questions")
    return [by_question[question_id] for question_id in expected_order]


def build_adequacy_records(
    args: argparse.Namespace, plan: dict[str, Any]
) -> list[dict[str, Any]]:
    views, _, routing = load_materialized_views(args, plan)
    validator = _schema_validator(args.adequacy_schema)
    return _load_stage_parts(
        args.e1_parts,
        stage="e1",
        validator=validator,
        views=views,
        routing=routing,
    )


def build_e1_assessment_bindings_for_e2(
    assessments: list[dict[str, Any]],
    *,
    combined_artifact_path: Path,
    combined_artifact_sha256: str,
) -> dict[str, Any]:
    """Build a content-free E1 hash sidecar for isolated E2 authoring.

    The ordered assessment IDs and canonical record hashes let E2 bind to the
    committed E1 artifact without exposing any adequacy judgment or rationale.
    """

    if (
        len(combined_artifact_sha256) != 64
        or any(character not in "0123456789abcdef" for character in combined_artifact_sha256)
    ):
        raise EnvironmentRealizationError("combined E1 artifact SHA-256 is invalid")
    bindings: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, assessment in enumerate(assessments, 1):
        assessment_id = assessment.get("assessment_id")
        if not isinstance(assessment_id, str) or not assessment_id or assessment_id in seen:
            raise EnvironmentRealizationError(
                f"E1 assessment {index} lacks a unique assessment_id"
            )
        seen.add(assessment_id)
        bindings.append(
            {
                "assessment_id": assessment_id,
                "assessment_record_sha256": canonical_json_sha256(assessment),
            }
        )
    return {
        "schema_version": "e1_assessment_bindings_for_e2_v0_1",
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "content_exposure_contract": "hash_bindings_only_no_e1_assessment_content",
        "combined_e1_artifact": {
            "repository_relative_path": _relative(combined_artifact_path),
            "sha256": combined_artifact_sha256,
            "record_count": len(assessments),
        },
        "assessment_bindings": bindings,
    }


def _graph_contract_errors(graph: Any, label: str) -> tuple[list[str], set[str]]:
    """Validate a dependency DAG and its exact root/sink declarations."""

    errors: list[str] = []
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list):
        return [f"{label} graph/nodes are malformed"], set()
    nodes = graph["nodes"]
    node_ids = [node.get("node_id") for node in nodes if isinstance(node, dict)]
    if (
        len(node_ids) != len(nodes)
        or any(not isinstance(node_id, str) or not node_id for node_id in node_ids)
        or len(node_ids) != len(set(node_ids))
    ):
        return [f"{label} node IDs are missing or non-unique"], {
            node_id for node_id in node_ids if isinstance(node_id, str)
        }
    id_set = set(node_ids)
    indegree = {node_id: 0 for node_id in node_ids}
    outgoing: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for node in nodes:
        node_id = node["node_id"]
        dependencies = node.get("depends_on")
        if not isinstance(dependencies, list):
            errors.append(f"{label} node {node_id} depends_on is not an array")
            continue
        if len(dependencies) != len(set(dependencies)):
            errors.append(f"{label} node {node_id} repeats a dependency")
        for dependency in dependencies:
            if dependency not in id_set:
                errors.append(
                    f"{label} node {node_id} references missing dependency {dependency!r}"
                )
                continue
            if dependency == node_id:
                errors.append(f"{label} node {node_id} has a self dependency")
            if node_id not in outgoing[dependency]:
                outgoing[dependency].add(node_id)
                indegree[node_id] += 1
    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    work_indegree = dict(indegree)
    visited: list[str] = []
    while queue:
        current = queue.popleft()
        visited.append(current)
        for target in sorted(outgoing[current]):
            work_indegree[target] -= 1
            if work_indegree[target] == 0:
                queue.append(target)
    if len(visited) != len(node_ids):
        errors.append(f"{label} graph contains a cycle")
    entry_ids = graph.get("entry_node_ids")
    output_ids = graph.get("output_node_ids")
    expected_entries = {node_id for node_id, degree in indegree.items() if degree == 0}
    expected_outputs = {node_id for node_id, targets in outgoing.items() if not targets}
    if not isinstance(entry_ids, list) or set(entry_ids) != expected_entries:
        errors.append(f"{label} entry_node_ids do not exactly identify graph roots")
    if not isinstance(output_ids, list) or set(output_ids) != expected_outputs:
        errors.append(f"{label} output_node_ids do not exactly identify graph sinks")
    return errors, id_set


def validate_e1_e2_graph_contract(
    *,
    backbone_variants: dict[str, dict[str, Any]],
    realization_candidates: list[dict[str, Any]],
) -> list[str]:
    """Validate candidate-local DAG, coverage, classification, and order contracts."""

    errors: list[str] = []
    backbone_ids: dict[str, set[str]] = {}
    for variant_id, graph in backbone_variants.items():
        graph_errors, node_ids = _graph_contract_errors(
            graph, f"backbone variant {variant_id}"
        )
        errors.extend(graph_errors)
        backbone_ids[variant_id] = node_ids

    candidate_ids = [
        item.get("candidate_id")
        for item in realization_candidates
        if isinstance(item, dict)
    ]
    if len(candidate_ids) != len(realization_candidates) or len(candidate_ids) != len(
        set(candidate_ids)
    ):
        errors.append("realization candidate IDs are missing or non-unique")
    for candidate_index, candidate in enumerate(realization_candidates, 1):
        if not isinstance(candidate, dict):
            errors.append(f"realization candidate {candidate_index} is malformed")
            continue
        candidate_id = candidate.get("candidate_id", f"candidate{candidate_index}")
        target = candidate.get("target_backbone_variant_id")
        if target not in backbone_ids:
            errors.append(
                f"realization candidate {candidate_id} targets unknown variant {target!r}"
            )
            continue
        graph = candidate.get("graph")
        graph_errors, operator_ids = _graph_contract_errors(
            graph, f"realization candidate {candidate_id}"
        )
        errors.extend(graph_errors)
        if graph_errors or not isinstance(graph, dict) or not isinstance(
            graph.get("nodes"), list
        ):
            continue
        nodes = graph["nodes"]
        slots = candidate.get("binding_slots")
        if not isinstance(slots, list):
            errors.append(f"realization candidate {candidate_id} slots are malformed")
            continue
        slot_ids = [slot.get("slot_id") for slot in slots if isinstance(slot, dict)]
        if len(slot_ids) != len(slots) or len(slot_ids) != len(set(slot_ids)):
            errors.append(
                f"realization candidate {candidate_id} slot IDs are missing or non-unique"
            )
        referenced_slots: set[str] = set()
        node_by_id = {node["node_id"]: node for node in nodes}
        for node in nodes:
            input_slots = node.get("input_slot_ids")
            if not isinstance(input_slots, list) or not set(input_slots) <= set(slot_ids):
                errors.append(
                    f"realization candidate {candidate_id} node {node.get('node_id')} references an unknown slot"
                )
            else:
                referenced_slots.update(input_slots)
        if set(slot_ids) - referenced_slots:
            errors.append(f"realization candidate {candidate_id} has unused slots")
        for entry_id in graph.get("entry_node_ids", []):
            if entry_id in node_by_id and not node_by_id[entry_id].get("input_slot_ids"):
                errors.append(
                    f"realization candidate {candidate_id} root {entry_id} consumes no source slot"
                )
        if candidate.get("coverage_status") == "complete_for_target_variant" and not any(
            isinstance(slot, dict)
            and slot.get("environment_modality")
            not in {"question_literal", "unknown"}
            for slot in slots
        ):
            errors.append(
                f"realization candidate {candidate_id} complete coverage lacks an environment-modality slot"
            )

        mappings = candidate.get("backbone_operator_mappings")
        if not isinstance(mappings, list):
            errors.append(f"realization candidate {candidate_id} mappings are malformed")
            continue
        mapping_ids: list[Any] = []
        mapped_backbone_members: list[str] = []
        mapped_operator_members: list[str] = []
        mapped_operators_by_backbone: dict[str, set[str]] = defaultdict(set)
        for mapping in mappings:
            if not isinstance(mapping, dict):
                errors.append(f"realization candidate {candidate_id} has malformed mapping")
                continue
            mapping_ids.append(mapping.get("mapping_id"))
            mapped_backbone = mapping.get("backbone_node_ids")
            mapped_operators = mapping.get("operator_node_ids")
            if (
                not isinstance(mapped_backbone, list)
                or not mapped_backbone
                or not set(mapped_backbone) <= backbone_ids[target]
            ):
                errors.append(
                    f"realization candidate {candidate_id} mapping references unknown target-backbone nodes"
                )
                continue
            if (
                not isinstance(mapped_operators, list)
                or not mapped_operators
                or not set(mapped_operators) <= operator_ids
            ):
                errors.append(
                    f"realization candidate {candidate_id} mapping references unknown operator nodes"
                )
                continue
            mapped_backbone_members.extend(mapped_backbone)
            mapped_operator_members.extend(mapped_operators)
            for backbone_node_id in mapped_backbone:
                mapped_operators_by_backbone[backbone_node_id].update(mapped_operators)
            expected_kind = (
                ("one" if len(mapped_backbone) == 1 else "many")
                + "_to_"
                + ("one" if len(mapped_operators) == 1 else "many")
            )
            if mapping.get("mapping_kind") != expected_kind:
                errors.append(
                    f"realization candidate {candidate_id} mapping_kind must be {expected_kind}"
                )
        if len(mapping_ids) != len(set(mapping_ids)):
            errors.append(f"realization candidate {candidate_id} mapping IDs are non-unique")
        if len(mapped_backbone_members) != len(set(mapped_backbone_members)):
            errors.append(
                f"realization candidate {candidate_id} repeats a backbone node across mappings"
            )
        if len(mapped_operator_members) != len(set(mapped_operator_members)):
            errors.append(
                f"realization candidate {candidate_id} repeats an operator node across mappings"
            )
        mapped_backbone_set = set(mapped_backbone_members)
        mapped_operator_set = set(mapped_operator_members)
        classifications = candidate.get("operator_node_classifications")
        if not isinstance(classifications, list):
            errors.append(
                f"realization candidate {candidate_id} operator classifications are malformed"
            )
            continue
        classified_ids = [
            item.get("operator_node_id")
            for item in classifications
            if isinstance(item, dict)
        ]
        if (
            len(classified_ids) != len(classifications)
            or len(classified_ids) != len(operator_ids)
            or len(classified_ids) != len(set(classified_ids))
            or set(classified_ids) != operator_ids
        ):
            errors.append(
                f"realization candidate {candidate_id} must classify every operator exactly once"
            )
        classification_by_id = {
            item["operator_node_id"]: item
            for item in classifications
            if isinstance(item, dict) and isinstance(item.get("operator_node_id"), str)
        }
        for operator_id, classification in classification_by_id.items():
            roles = set(classification.get("roles", []))
            if (operator_id in mapped_operator_set) != ("backbone_realization" in roles):
                errors.append(
                    f"realization candidate {candidate_id} classification/mapping disagrees for {operator_id}"
                )
            is_extension = "environment_extension" in roles
            has_extension_detail = bool(classification.get("extension_type")) and bool(
                classification.get("extension_description")
            )
            if is_extension != has_extension_detail:
                errors.append(
                    f"realization candidate {candidate_id} extension detail disagrees for {operator_id}"
                )
            if not roles or (operator_id not in mapped_operator_set and not is_extension):
                errors.append(
                    f"realization candidate {candidate_id} operator {operator_id} has no justified role"
                )

        unsupported_items = candidate.get("unsupported_target_backbone_nodes")
        if not isinstance(unsupported_items, list):
            errors.append(
                f"realization candidate {candidate_id} unsupported target nodes are malformed"
            )
            continue
        unsupported_ids = [
            item.get("node_id") for item in unsupported_items if isinstance(item, dict)
        ]
        if len(unsupported_ids) != len(unsupported_items) or len(unsupported_ids) != len(
            set(unsupported_ids)
        ):
            errors.append(
                f"realization candidate {candidate_id} unsupported node IDs are missing or non-unique"
            )
        unsupported_set = set(unsupported_ids)
        if not unsupported_set <= backbone_ids[target]:
            errors.append(
                f"realization candidate {candidate_id} unsupported list references unknown target nodes"
            )
        if unsupported_set & mapped_backbone_set:
            errors.append(
                f"realization candidate {candidate_id} marks mapped nodes unsupported"
            )
        coverage = candidate.get("coverage_status")
        if coverage == "complete_for_target_variant" and mapped_backbone_set != backbone_ids[target]:
            errors.append(
                f"realization candidate {candidate_id} complete coverage omits target nodes"
            )
        if coverage == "partial_for_target_variant" and (
            not mapped_backbone_set
            or not unsupported_set
            or mapped_backbone_set | unsupported_set != backbone_ids[target]
        ):
            errors.append(
                f"realization candidate {candidate_id} partial coverage is not an exhaustive mapped/unsupported partition"
            )

        reachability = _graph_reachability(graph)
        backbone_by_id = {
            node["node_id"]: node for node in backbone_variants[target]["nodes"]
        }
        for node_id, node in backbone_by_id.items():
            if node_id not in mapped_operators_by_backbone:
                continue
            for dependency in node["depends_on"]:
                if dependency not in mapped_operators_by_backbone:
                    continue
                before = mapped_operators_by_backbone[dependency]
                after = mapped_operators_by_backbone[node_id]
                if not (before & after) and not any(
                    (source, destination) in reachability
                    for source in before
                    for destination in after
                ):
                    errors.append(
                        f"realization candidate {candidate_id} reverses or loses backbone dependency {dependency}->{node_id}"
                    )
        graph_outputs = set(graph.get("output_node_ids", []))
        mapped_target_outputs = {
            operator_id
            for backbone_output in backbone_variants[target]["output_node_ids"]
            for operator_id in mapped_operators_by_backbone.get(backbone_output, set())
        }
        for operator_id in mapped_target_outputs:
            if not any(
                operator_id == output_id
                or (operator_id, output_id) in reachability
                for output_id in graph_outputs
            ):
                errors.append(
                    f"realization candidate {candidate_id} target output does not reach an operator sink"
                )
        for output_id in graph_outputs:
            roles = set(classification_by_id.get(output_id, {}).get("roles", []))
            justified = "environment_extension" in roles or any(
                operator_id == output_id
                or (operator_id, output_id) in reachability
                for operator_id in mapped_target_outputs
            )
            if not justified:
                errors.append(
                    f"realization candidate {candidate_id} operator sink {output_id} is not justified by a target output or extension"
                )

    return errors


def _graph_reachability(graph: dict[str, Any]) -> set[tuple[str, str]]:
    outgoing: dict[str, set[str]] = {
        node["node_id"]: set() for node in graph["nodes"]
    }
    for node in graph["nodes"]:
        for dependency in node["depends_on"]:
            outgoing[dependency].add(node["node_id"])
    reachable: set[tuple[str, str]] = set()
    for source in outgoing:
        stack = list(outgoing[source])
        while stack:
            destination = stack.pop()
            if (source, destination) in reachable:
                continue
            reachable.add((source, destination))
            stack.extend(outgoing[destination])
    return reachable


def _validate_e2_semantics(
    record: dict[str, Any],
    view: dict[str, Any],
    assessment: dict[str, Any],
    e1_artifact_sha256: str,
) -> list[str]:
    errors: list[str] = []
    expected = {
        "realization_id": _realization_id(view["question_id"]),
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "selection_index": view["selection_index"],
        "question_id": view["question_id"],
        "family_id": view["family_id"],
        "contracted_signature_sha256": view["contracted_signature_sha256"],
        "input_view_id": view["view_id"],
        "input_view_payload_sha256": view["payload_sha256"],
        "visibility": "question_candidate_backbone_and_environment_with_adequacy_hash_only_no_adequacy_content_answer_trace_grounding_execution_or_prior_proposals",
        "downstream_status": E2_DOWNSTREAM_NOT_EVALUATED,
        "global_nonexposure_machine_authenticated": False,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            errors.append(f"{key} differs from its frozen input binding")
    expected_assessment_binding = {
        "binding_mode": "hash_only",
        "assessment_artifact_sha256": e1_artifact_sha256,
        "assessment_record_sha256": canonical_json_sha256(assessment),
        "assessment_content_in_authoring_input": False,
    }
    if record.get("backbone_assessment_binding") != expected_assessment_binding:
        errors.append("backbone assessment binding differs from committed E1 evidence")
    authoring = record.get("authoring_contract")
    expected_authoring = open_operator_authoring_contract()
    if authoring != expected_authoring:
        errors.append("open authoring contract mismatch")
    status = record.get("realization_status")
    candidates = record.get("realization_candidates")
    results = record.get("variant_realization_results")
    if (
        status not in E2_STATUSES
        or not isinstance(candidates, list)
        or not isinstance(results, list)
    ):
        errors.append("realization status/candidate/variant-result fields are malformed")
        return errors
    variants = _backbone_variants(view)
    candidate_ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict)]
    if len(candidate_ids) != len(candidates) or len(candidate_ids) != len(set(candidate_ids)):
        errors.append("realization candidate IDs are not unique")
    errors.extend(
        validate_e1_e2_graph_contract(
            backbone_variants=variants,
            realization_candidates=candidates,
        )
    )
    result_order = [
        item.get("backbone_variant_id") for item in results if isinstance(item, dict)
    ]
    if result_order != list(variants):
        errors.append("variant realization results do not follow primary/alternative order")
        return errors
    result_statuses: list[str] = []
    for result in results:
        variant_id = result["backbone_variant_id"]
        result_status = result["status"]
        result_statuses.append(result_status)
        target_candidates = [
            candidate
            for candidate in candidates
            if candidate.get("target_backbone_variant_id") == variant_id
        ]
        target_candidate_ids = [candidate["candidate_id"] for candidate in target_candidates]
        if result.get("candidate_ids") != target_candidate_ids:
            errors.append(
                f"variant result {variant_id} does not list exactly its candidates in record order"
            )
        coverage_statuses = [candidate["coverage_status"] for candidate in target_candidates]
        complete_exists = "complete_for_target_variant" in coverage_statuses
        partial_exists = "partial_for_target_variant" in coverage_statuses
        partial_blocker_sets = [
            {
                item["node_id"]
                for item in candidate["unsupported_target_backbone_nodes"]
            }
            for candidate in target_candidates
            if candidate["coverage_status"] == "partial_for_target_variant"
        ]
        shared_blockers = (
            set.intersection(*partial_blocker_sets) if partial_blocker_sets else set()
        )
        blockers = result.get("blocking_unsupported_node_ids", [])
        if not set(blockers) <= {
            node["node_id"] for node in variants[variant_id]["nodes"]
        }:
            errors.append(f"variant result {variant_id} references an unknown blocker")
        if result_status == "fully_realized" and (
            not complete_exists or blockers
        ):
            errors.append(
                f"variant result {variant_id} fully_realized lacks a complete candidate or has blockers"
            )
        elif result_status == "partially_realized" and (
            complete_exists or not partial_exists or set(blockers) != shared_blockers
        ):
            errors.append(
                f"variant result {variant_id} partially_realized disagrees with candidate coverage/blockers"
            )
        elif result_status == "unavailable" and (
            target_candidates or not blockers
        ):
            errors.append(
                f"variant result {variant_id} unavailable requires zero candidates and explicit blockers"
            )
        elif result_status == "indeterminate" and (complete_exists or partial_exists):
            errors.append(
                f"variant result {variant_id} indeterminate conflicts with complete/partial candidates"
            )
    if "fully_realized" in result_statuses:
        expected_status = "available"
    elif "partially_realized" in result_statuses:
        expected_status = "partial"
    elif "indeterminate" in result_statuses:
        expected_status = "indeterminate"
    else:
        expected_status = "unavailable"
    if status != expected_status:
        errors.append("top-level E2 status does not follow frozen variant aggregation")
    preferred = record.get("preferred_candidate_id")
    if preferred is not None and preferred not in set(candidate_ids):
        errors.append("preferred candidate does not exist")
    if not candidates and preferred is not None:
        errors.append("record without candidates cannot prefer one")
    if preferred in set(candidate_ids):
        preferred_candidate = next(
            candidate for candidate in candidates if candidate["candidate_id"] == preferred
        )
        expected_preferred_coverage = {
            "available": "complete_for_target_variant",
            "partial": "partial_for_target_variant",
            "indeterminate": "indeterminate",
        }.get(status)
        if preferred_candidate["coverage_status"] != expected_preferred_coverage:
            errors.append(
                "preferred candidate coverage does not support the top-level E2 status"
            )
    delivery_complete = record.get("input_delivery") == {
        "view_fully_consumed": True,
        "completeness_status": "complete",
    }
    if not delivery_complete and status != "indeterminate":
        errors.append("incomplete E2 input delivery requires an indeterminate result")
    exposure = record.get("author_prior_exposure_to_backbone_adequacy")
    if exposure != "procedurally_attested_none" and status != "indeterminate":
        errors.append(
            "non-naive or unknown E2 author exposure permits only an indeterminate result"
        )
    record_exposure = record.get("author_prior_exposure_to_record_before_packet")
    if record_exposure != "procedurally_attested_none" and status != "indeterminate":
        errors.append(
            "prior or unknown E2 record exposure permits only an indeterminate result"
        )
    return errors


def load_e1_records(
    args: argparse.Namespace, plan: dict[str, Any]
) -> tuple[list[dict[str, Any]], str]:
    views, _, routing = load_materialized_views(args, plan)
    records = list(iter_json_records(args.e1_output))
    expected = _load_stage_parts(
        args.e1_parts,
        stage="e1",
        validator=_schema_validator(args.adequacy_schema),
        views=views,
        routing=routing,
    )
    if records != expected:
        raise EnvironmentRealizationError("combined E1 assessments differ from partition merge")
    if args.e1_output.read_bytes() != jsonl_file_bytes(records):
        raise EnvironmentRealizationError(
            "combined E1 assessments are not in canonical project JSONL serialization"
        )
    combined_sha256 = sha256_file(args.e1_output)
    expected_sidecar = build_e1_assessment_bindings_for_e2(
        records,
        combined_artifact_path=args.e1_output,
        combined_artifact_sha256=combined_sha256,
    )
    if (
        args.e1_bindings_output.is_symlink()
        or not args.e1_bindings_output.is_file()
        or read_json(args.e1_bindings_output) != expected_sidecar
    ):
        raise EnvironmentRealizationError(
            "E1-to-E2 hash sidecar differs from the combined E1 artifact"
        )
    if args.e1_bindings_output.read_bytes() != json_file_bytes(expected_sidecar):
        raise EnvironmentRealizationError(
            "E1-to-E2 hash sidecar is not in canonical project JSON serialization"
        )
    expected_e2_packets = build_e2_authoring_packets(
        views,
        records,
        combined_e1_sha256=combined_sha256,
        routing=routing,
    )
    for index, (path, expected_records) in enumerate(
        zip(args.e2_packets, expected_e2_packets), 1
    ):
        if (
            path.is_symlink()
            or not path.is_file()
            or path.read_bytes() != jsonl_file_bytes(expected_records)
        ):
            raise EnvironmentRealizationError(
                f"E2 authoring packet {index} differs from E1 hash bindings/views"
            )
    return records, combined_sha256


def build_realization_records(
    args: argparse.Namespace, plan: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    views, _, routing = load_materialized_views(args, plan)
    e1_records, e1_sha = load_e1_records(args, plan)
    e1_by_question = {record["question_id"]: record for record in e1_records}
    e2_records = _load_stage_parts(
        args.e2_parts,
        stage="e2",
        validator=_schema_validator(args.realization_schema),
        views=views,
        routing=routing,
        e1_by_question=e1_by_question,
        e1_artifact_sha256=e1_sha,
    )
    return views, e1_records, e2_records


def _not_evaluated_grounding() -> dict[str, Any]:
    return {
        "status": "not_evaluated",
        "all_required_inputs_grounded": None,
        "grounding_record_id": None,
        "grounded_item_count": None,
        "ungrounded_item_count": None,
        "failure_codes": [],
        "evidence_references": [],
        "notes": None,
    }


def _not_evaluated_execution() -> dict[str, Any]:
    return {
        "status": "not_evaluated",
        "executable": None,
        "execution_succeeded": None,
        "execution_record_id": None,
        "failure_codes": [],
        "evidence_references": [],
        "notes": None,
    }


def _not_evaluated_answer_recovery() -> dict[str, Any]:
    return {
        "status": "not_evaluated",
        "answer_recovered": None,
        "answer_match_assessment": None,
        "answer_record_id": None,
        "comparison_provenance": {
            "reference_answer_binding": None,
            "reference_answer_evidence_class": None,
            "reference_answer_is_gold": False,
            "comparator_id": None,
            "comparator_version": None,
        },
        "failure_codes": [],
        "evidence_references": [],
        "notes": None,
    }


def _e1_outcome_signal(record: dict[str, Any]) -> dict[str, Any]:
    status = record["overall_status"]
    outcome_status = {
        "adequate": "pass",
        "partially_adequate": "partial",
        "inadequate": "fail",
        "indeterminate": "indeterminate",
    }[status]
    change_codes = sorted(
        {
            item["change_type"]
            for assessment in record.get("variant_assessments", [])
            if isinstance(assessment, dict)
            for item in assessment.get("required_changes", [])
            if isinstance(item, dict)
            and isinstance(item.get("change_type"), str)
        }
    )
    return {
        "status": outcome_status,
        "candidate_backbone_adequate": record["candidate_backbone_adequate"],
        "required_change_codes": change_codes,
        "evidence_references": [],
        "notes": record.get("rationale"),
    }


def _e2_outcome_signal(record: dict[str, Any]) -> dict[str, Any]:
    status = record["realization_status"]
    outcome_status = {
        "available": "pass",
        "partial": "partial",
        "unavailable": "fail",
        "indeterminate": "indeterminate",
    }[status]
    complete_available: bool | None = {
        "available": True,
        "partial": False,
        "unavailable": False,
        "indeterminate": None,
    }[status]
    candidates = record["realization_candidates"]
    issues = record.get("unresolved_issues", [])
    return {
        "status": outcome_status,
        "complete_realization_available": complete_available,
        "operator_notation_id": OPEN_NOTATION_ID if candidates else None,
        "final_operator_vocabulary_selected": False,
        "realization_record_id": record["realization_id"],
        "variant_realization_results": [
            {
                "backbone_variant_id": result["backbone_variant_id"],
                "status": result["status"],
                "blocking_unsupported_node_ids": result[
                    "blocking_unsupported_node_ids"
                ],
                "candidate_count": len(result["candidate_ids"]),
            }
            for result in record["variant_realization_results"]
        ],
        "realization_candidate_count": len(candidates),
        "unresolved_issue_count": len(issues),
        "evidence_references": [],
        "notes": record.get("preference_reason") or (issues[0] if issues else None),
    }


def _validate_outcome_semantics(outcome: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    signal = outcome.get("environment_operator_realization")
    if not isinstance(signal, dict):
        return ["environment operator realization signal is malformed"]
    results = signal.get("variant_realization_results")
    total = signal.get("realization_candidate_count")
    notation = signal.get("operator_notation_id")
    if not isinstance(results, list) or not isinstance(total, int):
        return ["operator realization variant results or candidate count are malformed"]
    variant_ids = [
        result.get("backbone_variant_id")
        for result in results
        if isinstance(result, dict)
    ]
    if len(variant_ids) != len(results) or len(variant_ids) != len(set(variant_ids)):
        errors.append("outcome variant realization IDs are not unique")
    candidate_counts = [
        result.get("candidate_count")
        for result in results
        if isinstance(result, dict)
    ]
    if (
        len(candidate_counts) != len(results)
        or any(not isinstance(count, int) for count in candidate_counts)
        or sum(candidate_counts) != total
    ):
        errors.append(
            "outcome realization candidate count does not equal the variant-level sum"
        )
    if (total == 0 and notation is not None) or (total > 0 and not isinstance(notation, str)):
        errors.append("operator notation presence disagrees with realization candidate count")
    return errors


def build_outcomes(
    args: argparse.Namespace,
    views: list[dict[str, Any]],
    e1_records: list[dict[str, Any]],
    e2_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    e1_sha = sha256_file(args.e1_output)
    e2_sha = sha256_bytes(jsonl_file_bytes(e2_records))
    view_sha = sha256_file(args.views_output)
    validator = _schema_validator(args.outcome_schema)
    outcomes: list[dict[str, Any]] = []
    for view, assessment, realization in zip(views, e1_records, e2_records):
        question_id = view["question_id"]
        if assessment["question_id"] != question_id or realization["question_id"] != question_id:
            raise EnvironmentRealizationError("outcome inputs are not aligned by question")
        outcome = {
            "schema_version": "environment_realization_outcome_v0_2",
            "outcome_id": _outcome_id(question_id),
            "run_id": RUN_ID,
            "selection_id": SELECTION_ID,
            "selection_index": view["selection_index"],
            "question_id": question_id,
            "family_id": view["family_id"],
            "contracted_signature_sha256": view["contracted_signature_sha256"],
            "record_status": "in_progress",
            "assessment_scope": "selected_question_environment_instance_only",
            "source_bindings": [
                _artifact_reference(
                    args.views_output,
                    view_sha,
                    artifact_role="representative_environment_view",
                    record_id=view["view_id"],
                ),
                _artifact_reference(
                    args.e1_output,
                    e1_sha,
                    artifact_role="backbone_adequacy_assessment",
                    record_id=assessment["assessment_id"],
                ),
                _artifact_reference(
                    args.e2_output,
                    e2_sha,
                    artifact_role="open_operator_realization",
                    record_id=realization["realization_id"],
                ),
            ],
            "backbone_adequacy": _e1_outcome_signal(assessment),
            "environment_operator_realization": _e2_outcome_signal(realization),
            "grounding": _not_evaluated_grounding(),
            "execution": _not_evaluated_execution(),
            "answer_recovery": _not_evaluated_answer_recovery(),
            "independence_contract": {
                "all_five_signal_fields_required": True,
                "evaluated_signals_independently_scored": True,
                "signals_logically_separate": True,
                "author_statistical_independence_claimed": False,
                "cognitive_independence_machine_authenticated": False,
                "execution_success_implies_backbone_adequacy": False,
                "execution_failure_implies_backbone_inadequacy": False,
                "answer_recovery_implies_prior_stage_success": False,
                "downstream_failure_overwrites_upstream_assessment": False,
            },
            "evidence_boundary": {
                "human_evidence_count": 0,
                "gold_claimed": False,
                "modeling_ready_claimed": False,
                "candidate_family_semantic_correctness_presupposed": False,
                "family_level_semantic_correctness_established": False,
            },
            "limitations": [
                "E1 and E2 are AI-authored non-human exploratory assessments.",
                "The open descriptive notation is not a selected operator vocabulary.",
                "Grounding, execution, and answer recovery remain not evaluated.",
            ],
        }
        errors = _validation_errors(
            validator, outcome, f"outcome[{view['selection_index']}]"
        )
        errors.extend(_validate_outcome_semantics(outcome))
        if errors:
            raise EnvironmentRealizationError(
                "outcome schema validation failed: " + " | ".join(errors[:20])
            )
        outcomes.append(outcome)
    return outcomes


def build_checks(
    views: list[dict[str, Any]],
    e1_records: list[dict[str, Any]],
    e2_records: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = [
        {
            "schema_version": CHECK_SCHEMA_VERSION,
            "check_type": "bundle",
            "selection_index": None,
            "question_id": None,
            "status": "pass",
            "errors": [],
        }
    ]
    for check_type, records in (
        ("environment_view", views),
        ("backbone_adequacy", e1_records),
        ("open_operator_realization", e2_records),
        ("five_signal_outcome", outcomes),
    ):
        checks.extend(
            {
                "schema_version": CHECK_SCHEMA_VERSION,
                "check_type": check_type,
                "selection_index": record["selection_index"],
                "question_id": record["question_id"],
                "status": "pass",
                "errors": [],
            }
            for record in records
        )
    return checks


def _graph_statistics(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph["nodes"]
    by_id = {node["node_id"]: node for node in nodes}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in by_id}
    depth: dict[str, int] = {}
    for node in nodes:
        for dependency in node["depends_on"]:
            outgoing[dependency].append(node["node_id"])

    def node_depth(node_id: str) -> int:
        if node_id not in depth:
            dependencies = by_id[node_id]["depends_on"]
            depth[node_id] = (
                0 if not dependencies else 1 + max(node_depth(item) for item in dependencies)
            )
        return depth[node_id]

    profiles = sorted(
        (
            node_depth(node_id),
            len(by_id[node_id]["depends_on"]),
            len(outgoing[node_id]),
        )
        for node_id in by_id
    )
    profile_payload = {
        "node_count": len(nodes),
        "edge_count": sum(len(node["depends_on"]) for node in nodes),
        "longest_path_edges": max(depth.values(), default=0),
        "entry_count": len(graph["entry_node_ids"]),
        "output_count": len(graph["output_node_ids"]),
        "sorted_depth_indegree_outdegree_profiles": [list(item) for item in profiles],
    }
    return {
        **profile_payload,
        "unlabeled_structural_profile_sha256": canonical_json_sha256(profile_payload),
    }


def build_metrics(
    args: argparse.Namespace,
    views: list[dict[str, Any]],
    e1_records: list[dict[str, Any]],
    e2_records: list[dict[str, Any]],
) -> dict[str, Any]:
    e1_counts = Counter(record["overall_status"] for record in e1_records)
    e2_counts = Counter(record["realization_status"] for record in e2_records)
    cross_tab = Counter(
        (e1["overall_status"], e2["realization_status"])
        for e1, e2 in zip(e1_records, e2_records)
    )
    variant_adequacy_counts: Counter[str] = Counter()
    variant_realization_counts: Counter[str] = Counter()
    mapping_counts: Counter[str] = Counter()
    slot_modality_counts: Counter[str] = Counter()
    variation_axis_counts: Counter[str] = Counter()
    operator_role_counts: Counter[str] = Counter()
    candidate_count_distribution: Counter[int] = Counter()
    expansions: list[dict[str, Any]] = []
    family_profiles: dict[str, set[str]] = defaultdict(set)
    family_question_ids: dict[str, set[str]] = defaultdict(set)
    family_statuses: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    partition_statuses: dict[str, Counter[str]] = defaultdict(Counter)
    primary_inadequate_alt_rescue = 0
    for view, e1, e2 in zip(views, e1_records, e2_records):
        family_id = view["family_id"]
        question_id = view["question_id"]
        family_question_ids[family_id].add(question_id)
        family_statuses[family_id][
            (e1["overall_status"], e2["realization_status"])
        ] += 1
        partition_statuses[e1["producer_partition"]][e1["overall_status"]] += 1
        partition_statuses[e2["producer_partition"]][e2["realization_status"]] += 1
        variant_assessments = e1["variant_assessments"]
        for assessment in variant_assessments:
            variant_adequacy_counts[assessment["status"]] += 1
        primary = next(
            assessment
            for assessment in variant_assessments
            if assessment["backbone_variant_id"] == "primary"
        )
        if primary["status"] != "adequate" and any(
            assessment["backbone_variant_id"] != "primary"
            and assessment["status"] == "adequate"
            for assessment in variant_assessments
        ):
            primary_inadequate_alt_rescue += 1
        for result in e2["variant_realization_results"]:
            variant_realization_counts[result["status"]] += 1
        candidates = e2["realization_candidates"]
        candidate_count_distribution[len(candidates)] += 1
        variants = _backbone_variants(view)
        for candidate in candidates:
            target = candidate["target_backbone_variant_id"]
            semantic_stats = _graph_statistics(variants[target])
            operator_stats = _graph_statistics(candidate["graph"])
            family_profiles[family_id].add(
                operator_stats["unlabeled_structural_profile_sha256"]
            )
            for mapping in candidate["backbone_operator_mappings"]:
                mapping_counts[mapping["mapping_kind"]] += 1
            for slot in candidate["binding_slots"]:
                slot_modality_counts[slot["environment_modality"]] += 1
            for axis in candidate["variation_axes"]:
                variation_axis_counts[axis] += 1
            for classification in candidate["operator_node_classifications"]:
                for role in classification["roles"]:
                    operator_role_counts[role] += 1
            expansions.append(
                {
                    "question_id": question_id,
                    "candidate_id": candidate["candidate_id"],
                    "target_backbone_variant_id": target,
                    "coverage_status": candidate["coverage_status"],
                    "semantic_node_count": semantic_stats["node_count"],
                    "operator_node_count": operator_stats["node_count"],
                    "node_count_delta": operator_stats["node_count"]
                    - semantic_stats["node_count"],
                    "semantic_edge_count": semantic_stats["edge_count"],
                    "operator_edge_count": operator_stats["edge_count"],
                    "edge_count_delta": operator_stats["edge_count"]
                    - semantic_stats["edge_count"],
                    "semantic_longest_path_edges": semantic_stats[
                        "longest_path_edges"
                    ],
                    "operator_longest_path_edges": operator_stats[
                        "longest_path_edges"
                    ],
                    "depth_delta": operator_stats["longest_path_edges"]
                    - semantic_stats["longest_path_edges"],
                    "operator_unlabeled_structural_profile_sha256": operator_stats[
                        "unlabeled_structural_profile_sha256"
                    ],
                }
            )
    family_heterogeneity = [
        {
            "family_id": family_id,
            "selected_question_count": len(family_question_ids[family_id]),
            "unique_unlabeled_operator_structural_profiles": len(
                family_profiles[family_id]
            ),
            "unlabeled_operator_structural_profile_sha256s": sorted(
                family_profiles[family_id]
            ),
            "e1_by_e2_status_counts": {
                f"{e1_status}__{e2_status}": count
                for (e1_status, e2_status), count in sorted(
                    family_statuses[family_id].items()
                )
            },
        }
        for family_id in sorted(family_question_ids)
    ]
    return {
        "schema_version": "representative_environment_realization_metrics_v0_1",
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "evidence_class": "ai_exploratory_non_human_non_gold",
        "sample_design": "rarity_overweighted_coverage_stress_not_probability_sample",
        "prevalence_estimation_authorized": False,
        "record_local_label_recurrence_analyzed": False,
        "label_normalization_status": "deferred_no_cross_record_label_taxonomy_claim",
        "counts": {
            "questions": len(views),
            "families": len(family_question_ids),
            "e1_records": len(e1_records),
            "e2_records": len(e2_records),
            "realization_candidates": len(expansions),
            "primary_nonadequate_rescued_by_adequate_alternative": primary_inadequate_alt_rescue,
        },
        "status_counts": {
            "e1_overall": dict(sorted(e1_counts.items())),
            "e1_variants": dict(sorted(variant_adequacy_counts.items())),
            "e2_overall": dict(sorted(e2_counts.items())),
            "e2_variants": dict(sorted(variant_realization_counts.items())),
        },
        "e1_by_e2_cross_tab": {
            f"{e1_status}__{e2_status}": count
            for (e1_status, e2_status), count in sorted(cross_tab.items())
        },
        "candidate_count_distribution": {
            str(count): frequency
            for count, frequency in sorted(candidate_count_distribution.items())
        },
        "mapping_kind_counts": dict(sorted(mapping_counts.items())),
        "operator_node_role_counts": dict(sorted(operator_role_counts.items())),
        "slot_modality_counts": dict(sorted(slot_modality_counts.items())),
        "variation_axis_counts": dict(sorted(variation_axis_counts.items())),
        "semantic_to_operator_expansions": expansions,
        "family_structural_heterogeneity": family_heterogeneity,
        "producer_partition_status_counts": {
            partition: dict(sorted(counts.items()))
            for partition, counts in sorted(partition_statuses.items())
        },
        "interpretation_boundary": {
            "structural_profile_is_exact_graph_isomorphism": False,
            "structural_profile_uses_labels": False,
            "common_executable_graph_established": False,
            "final_operator_vocabulary_selected": False,
            "grounding_execution_answer_recovery_evaluated": False,
        },
    }


def build_environment_exposure_ledger(
    views: list[dict[str, Any]],
) -> dict[str, Any]:
    question_ids = [view["question_id"] for view in views]
    return {
        "schema_version": "representative_environment_exposure_ledger_v0_1",
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "exposure_class": "ai_environment_stage_exposure_non_human_non_gold",
        "question_count": len(question_ids),
        "question_ids": question_ids,
        "question_ids_ordered_sha256": canonical_json_sha256(question_ids),
        "question_ids_set_sha256": canonical_string_set_sha256(question_ids),
        "newly_exposed_layers": [
            "full_selected_question_table",
            "table_link_closure_documents",
            "e1_backbone_adequacy_authoring",
            "e2_open_operator_realization_authoring",
        ],
        "prior_question_only_ai_exposure_already_recorded": True,
        "official_answer_or_trace_fields_supplied": False,
        "environment_may_naturally_contain_answer_bearing_facts": True,
        "corpus_role_allocation_changed": False,
        "train_dev_locked_eval_roles_assigned_by_this_run": False,
        "future_unseen_environment_evaluation_claim_allowed_for_these_ids": False,
        "human_evidence_count": 0,
        "gold_claimed": False,
    }


def _triggered_recheck_ids(
    views: list[dict[str, Any]],
    e1_records: list[dict[str, Any]],
    e2_records: list[dict[str, Any]],
    *,
    selection_path: Path,
    records_path: Path,
) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {
        "source_backbone_uncertain": [],
        "rare_singleton_or_doubleton_family": [],
        "e1_non_adequate_or_indeterminate": [],
        "e2_partial_unavailable_or_indeterminate": [],
        "multiple_realization_candidates": [],
        "unsupported_backbone_nodes": [],
    }
    selection = read_json(selection_path)
    tier_by_question = {
        item["question_id"]: item["family_evidence_tier"]
        for item in selection["selections"]
    }
    status_by_question = {
        item["question_id"]: item["status"] for item in iter_json_records(records_path)
    }
    for view, e1, e2 in zip(views, e1_records, e2_records):
        question_id = view["question_id"]
        if status_by_question[question_id] == "uncertain":
            output["source_backbone_uncertain"].append(question_id)
        if tier_by_question[question_id] in {"singleton", "doubleton"}:
            output["rare_singleton_or_doubleton_family"].append(question_id)
        if e1["overall_status"] != "adequate":
            output["e1_non_adequate_or_indeterminate"].append(question_id)
        if e2["realization_status"] != "available":
            output["e2_partial_unavailable_or_indeterminate"].append(question_id)
        if len(e2["realization_candidates"]) > 1:
            output["multiple_realization_candidates"].append(question_id)
        if any(
            candidate["unsupported_target_backbone_nodes"]
            for candidate in e2["realization_candidates"]
        ) or any(
            result["blocking_unsupported_node_ids"]
            for result in e2["variant_realization_results"]
        ):
            output["unsupported_backbone_nodes"].append(question_id)
    return output


def render_report(
    args: argparse.Namespace,
    views: list[dict[str, Any]],
    e1_records: list[dict[str, Any]],
    e2_records: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
) -> str:
    e1_counts = Counter(record["overall_status"] for record in e1_records)
    e2_counts = Counter(record["realization_status"] for record in e2_records)
    candidate_counts = Counter(len(record["realization_candidates"]) for record in e2_records)
    metrics = build_metrics(args, views, e1_records, e2_records)
    triggers = _triggered_recheck_ids(
        views,
        e1_records,
        e2_records,
        selection_path=args.selection,
        records_path=args.records,
    )
    lines = [
        "# Representative environment realization v0.1",
        "",
        "Status: `ai_exploratory_non_human_non_gold_first_two_signals_evaluated`.",
        "",
        "## Scope",
        "",
        f"- Selected questions: {len(views)}",
        f"- Candidate families covered: {len({view['family_id'] for view in views})}",
        f"- E1 backbone-adequacy records: {len(e1_records)}",
        f"- E2 open-realization records: {len(e2_records)}",
        f"- Five-signal outcome records: {len(outcomes)} (`in_progress`)",
        "- Human evidence: 0",
        "- Final operator vocabulary selected: no",
        "- Grounding, execution, answer recovery evaluated: no",
        "",
        "## E1 backbone adequacy",
        "",
        "| Status | Questions |",
        "| --- | ---: |",
    ]
    for status in E1_STATUSES:
        lines.append(f"| `{status}` | {e1_counts[status]} |")
    lines.append(
        "\nPrimary-nonadequate records rescued by an adequate preserved alternative: "
        f"{metrics['counts']['primary_nonadequate_rescued_by_adequate_alternative']}."
    )
    lines.extend(
        [
            "",
            "## E2 open environment-aware realization",
            "",
            "| Status | Questions |",
            "| --- | ---: |",
        ]
    )
    for status in E2_STATUSES:
        lines.append(f"| `{status}` | {e2_counts[status]} |")
    lines.extend(
        [
            "",
            "Realization candidates per question: "
            + ", ".join(f"{count}→{frequency}" for count, frequency in sorted(candidate_counts.items())),
            "",
            "## Backbone-to-operator structural observations",
            "",
            "Mapping kinds: "
            + (
                ", ".join(
                    f"`{key}`={value}"
                    for key, value in metrics["mapping_kind_counts"].items()
                )
                or "none"
            )
            + ".",
            "",
            "Operator-node roles: "
            + (
                ", ".join(
                    f"`{key}`={value}"
                    for key, value in metrics["operator_node_role_counts"].items()
                )
                or "none"
            )
            + ".",
            "",
            "Families with more than one unlabeled operator structural profile: "
            + str(
                sum(
                    item["unique_unlabeled_operator_structural_profiles"] > 1
                    for item in metrics["family_structural_heterogeneity"]
                )
            )
            + f"/{len(metrics['family_structural_heterogeneity'])}.",
            "",
            "## Precommitted targeted recheck triggers",
            "",
        ]
    )
    for trigger, question_ids in triggers.items():
        lines.append(f"- `{trigger}`: {len(question_ids)}")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "E1 was committed before E2. E2 packets used record-local free operator labels",
            "and ungrounded slots, excluded preserved coarse/medium/fine proposals, and",
            "required fresh authors to attest the specified nonexposure conditions.",
            "The resulting structural and adequacy observations are AI-authored diagnostic",
            "evidence, not semantic gold, human agreement, or a final operator ontology.",
            "Environment rows and linked documents can naturally contain answer-bearing facts,",
            "but official answer/reference fields and traces were not projected into the views.",
            "The dataset-provided question-to-table binding and full link closure were supplied;",
            "table retrieval was not evaluated. Record-local label recurrence was not analyzed.",
            "The rarity-overweighted sample is not a probability sample, so counts are not",
            "population prevalence estimates. Structural-profile hashes are label-free",
            "descriptors, not proofs of exact graph isomorphism or a common executable graph.",
            "Exact graph identity is not treated as the only valid realization criterion.",
            "",
            "Grounding, execution, and answer recovery remain separate future stages. Their",
            "future results must not overwrite these upstream assessments.",
            "",
        ]
    )
    return "\n".join(lines)


def _output_descriptor(path: Path, payload: bytes, *, record_count: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "repository_relative_path": _relative(path),
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
    }
    if record_count is not None:
        result["record_count"] = record_count
    return result


def build_final_payloads(
    args: argparse.Namespace,
    plan: dict[str, Any],
    plan_freeze_commit: str,
    view_freeze_commit: str,
    e1_freeze_commit: str,
) -> tuple[dict[str, tuple[Path, bytes]], dict[str, Any]]:
    views, e1_records, e2_records = build_realization_records(args, plan)
    outcomes = build_outcomes(args, views, e1_records, e2_records)
    checks = build_checks(views, e1_records, e2_records, outcomes)
    metrics = build_metrics(args, views, e1_records, e2_records)
    exposure_ledger = build_environment_exposure_ledger(views)
    e2_bytes = jsonl_file_bytes(e2_records)
    outcome_bytes = jsonl_file_bytes(outcomes)
    checks_bytes = jsonl_file_bytes(checks)
    report_bytes = render_report(args, views, e1_records, e2_records, outcomes).encode("utf-8")
    if not report_bytes.endswith(b"\n"):
        report_bytes += b"\n"
    preliminary = {
        "open_operator_realizations": (args.e2_output, e2_bytes),
        "outcomes": (args.outcomes_output, outcome_bytes),
        "checks": (args.checks_output, checks_bytes),
        "report": (args.report_output, report_bytes),
        "metrics": (args.metrics_output, json_file_bytes(metrics)),
        "environment_exposure_ledger": (
            args.exposure_ledger_output,
            json_file_bytes(exposure_ledger),
        ),
    }
    triggers = _triggered_recheck_ids(
        views,
        e1_records,
        e2_records,
        selection_path=args.selection,
        records_path=args.records,
    )
    manifest = {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "selection_id": SELECTION_ID,
        "run_status": "complete_first_two_signals_grounding_execution_answer_not_evaluated",
        "contract_freeze_commit": plan_freeze_commit,
        "environment_view_freeze_commit": view_freeze_commit,
        "e1_freeze_commit": e1_freeze_commit,
        "implementation_commit": plan["implementation_commit"],
        "source_commit": plan["source_commit"],
        "tool_version": TOOL_VERSION,
        "model_provenance": MODEL_PROVENANCE,
        "stage_contract": plan["stage_contract"],
        "visibility_contract": plan["visibility_contract"],
        "analysis_contract": plan["analysis_contract"],
        "source_bindings": plan["source_artifacts"],
        "contract_bindings": {**plan["contract_artifacts"], "freeze_plan": _binding(args.plan)},
        "input_bindings": {
            "environment_views": _binding(args.views_output, record_count=EXPECTED_QUESTION_COUNT),
            "environment_views_manifest": _binding(args.views_manifest_output),
            "routing": _binding(args.routing_output),
            "e1_parts": [
                _binding(path, record_count=len(list(iter_json_records(path))))
                for path in args.e1_parts
            ],
            "e1_combined": _binding(args.e1_output, record_count=EXPECTED_QUESTION_COUNT),
            "e1_hash_bindings_for_e2": _binding(args.e1_bindings_output),
            "e2_parts": [
                _binding(path, record_count=len(list(iter_json_records(path))))
                for path in args.e2_parts
            ],
            "e1_authoring_packets": [_binding(path) for path in args.e1_packets],
            "e2_authoring_packets": [_binding(path) for path in args.e2_packets],
        },
        "counts": {
            "environment_views": len(views),
            "candidate_families": len({view["family_id"] for view in views}),
            "e1_assessments": len(e1_records),
            "e2_realizations": len(e2_records),
            "outcomes": len(outcomes),
            "checks": len(checks),
            "metrics_records": 1,
            "environment_exposure_ledger_records": 1,
            "human_evidence": 0,
        },
        "status_counts": {
            "backbone_adequacy": dict(sorted(Counter(item["overall_status"] for item in e1_records).items())),
            "environment_operator_realization": dict(
                sorted(Counter(item["realization_status"] for item in e2_records).items())
            ),
        },
        "targeted_recheck_triggers": {
            key: {
                "count": len(question_ids),
                "question_ids": question_ids,
                "question_ids_set_sha256": canonical_string_set_sha256(question_ids),
            }
            for key, question_ids in triggers.items()
        },
        "outputs": {
            label: _output_descriptor(
                path,
                payload,
                record_count=(
                    len(e2_records)
                    if label == "open_operator_realizations"
                    else len(outcomes)
                    if label == "outcomes"
                    else len(checks)
                    if label == "checks"
                    else 1
                    if label in {"metrics", "environment_exposure_ledger"}
                    else None
                ),
            )
            for label, (path, payload) in preliminary.items()
        },
        "evidence_boundary": {
            "evidence_class": "ai_exploratory_non_human_non_gold",
            "human_evidence_count": 0,
            "semantic_gold_claimed": False,
            "final_operator_vocabulary_selected": False,
            "grounding_evaluated": False,
            "execution_evaluated": False,
            "answer_recovery_evaluated": False,
            "modeling_ready_claimed": False,
        },
    }
    payloads = dict(preliminary)
    payloads["run_manifest"] = (args.run_manifest_output, json_file_bytes(manifest))
    return payloads, manifest


def _ensure_absent(paths: Iterable[Path], stage: str) -> None:
    for path in paths:
        if path.is_symlink() or path.exists():
            raise EnvironmentRealizationError(
                f"{stage} requires output to be absent: {_relative(path)}"
            )


def _write_payloads(payloads: dict[str, tuple[Path, bytes]]) -> dict[str, str]:
    try:
        return write_output_batch(payloads)
    except ValueError as exc:
        raise EnvironmentRealizationError(str(exc)) from exc


def freeze_plan(args: argparse.Namespace) -> dict[str, Any]:
    plan = build_freeze_plan(args)
    statuses = _write_payloads({"freeze_plan": (args.plan, json_file_bytes(plan))})
    return {"mode": "freeze_plan", "write_status": statuses}


def materialize_views(args: argparse.Namespace) -> dict[str, Any]:
    plan = validate_plan(args)
    plan_freeze_commit = verify_plan_freeze(args, plan)
    _ensure_absent(
        [
            *args.e1_packets,
            *args.e1_parts,
            args.e1_output,
            args.e1_bindings_output,
            *args.e2_packets,
            *args.e2_parts,
            args.e2_output,
            args.outcomes_output,
            args.checks_output,
            args.report_output,
            args.metrics_output,
            args.exposure_ledger_output,
            args.run_manifest_output,
        ],
        "environment materialization",
    )
    views, manifest, routing = build_environment_views(
        args, plan, plan_freeze_commit
    )
    e1_packets = build_e1_authoring_packets(views, routing)
    payloads = {
            "environment_views": (args.views_output, jsonl_file_bytes(views)),
            "environment_views_manifest": (
                args.views_manifest_output,
                json_file_bytes(manifest),
            ),
            "producer_routing_manifest": (
                args.routing_output,
                json_file_bytes(routing),
            ),
    }
    payloads.update(
        {
            f"e1_authoring_packet_{index:02d}": (path, jsonl_file_bytes(records))
            for index, (path, records) in enumerate(
                zip(args.e1_packets, e1_packets), 1
            )
        }
    )
    statuses = _write_payloads(payloads)
    return {
        "mode": "materialize_views",
        "record_count": len(views),
        "unique_table_count": len(
            {view["payload"]["environment"]["table_id"] for view in views}
        ),
        "write_status": statuses,
    }


def build_adequacy(args: argparse.Namespace) -> dict[str, Any]:
    plan = validate_plan(args)
    plan_freeze_commit = verify_plan_freeze(args, plan)
    verify_view_freeze(args, plan_freeze_commit)
    _ensure_absent(
        [
            args.e1_output,
            args.e1_bindings_output,
            *args.e2_packets,
            *args.e2_parts,
            args.e2_output,
            args.outcomes_output,
            args.checks_output,
            args.report_output,
            args.metrics_output,
            args.exposure_ledger_output,
            args.run_manifest_output,
        ],
        "E1 combination",
    )
    records = build_adequacy_records(args, plan)
    combined_bytes = jsonl_file_bytes(records)
    combined_sha256 = sha256_bytes(combined_bytes)
    sidecar = build_e1_assessment_bindings_for_e2(
        records,
        combined_artifact_path=args.e1_output,
        combined_artifact_sha256=combined_sha256,
    )
    views, _, routing = load_materialized_views(args, plan)
    e2_packets = build_e2_authoring_packets(
        views,
        records,
        combined_e1_sha256=combined_sha256,
        routing=routing,
    )
    payloads = {
            "backbone_adequacy_assessments": (args.e1_output, combined_bytes),
            "e1_assessment_bindings_for_e2": (
                args.e1_bindings_output,
                json_file_bytes(sidecar),
            ),
    }
    payloads.update(
        {
            f"e2_authoring_packet_{index:02d}": (path, jsonl_file_bytes(packet))
            for index, (path, packet) in enumerate(
                zip(args.e2_packets, e2_packets), 1
            )
        }
    )
    statuses = _write_payloads(payloads)
    return {
        "mode": "build_adequacy",
        "record_count": len(records),
        "status_counts": dict(
            sorted(Counter(record["overall_status"] for record in records).items())
        ),
        "write_status": statuses,
    }


def build_final(args: argparse.Namespace) -> dict[str, Any]:
    plan = validate_plan(args)
    plan_freeze_commit = verify_plan_freeze(args, plan)
    view_freeze_commit = verify_view_freeze(args, plan_freeze_commit)
    e1_freeze_commit = verify_e1_freeze(args, view_freeze_commit)
    _ensure_absent(
        [
            args.e2_output,
            args.outcomes_output,
            args.checks_output,
            args.report_output,
            args.metrics_output,
            args.exposure_ledger_output,
            args.run_manifest_output,
        ],
        "final combination",
    )
    payloads, manifest = build_final_payloads(
        args, plan, plan_freeze_commit, view_freeze_commit, e1_freeze_commit
    )
    statuses = _write_payloads(payloads)
    return {
        "mode": "build_final",
        "counts": manifest["counts"],
        "status_counts": manifest["status_counts"],
        "write_status": statuses,
    }


def _presence(paths: Iterable[Path]) -> tuple[bool, bool]:
    paths_list = list(paths)
    valid = [path.exists() and not path.is_symlink() for path in paths_list]
    seen = [path.exists() or path.is_symlink() for path in paths_list]
    return all(valid), any(seen)


def validate_existing(args: argparse.Namespace) -> dict[str, Any]:
    plan = validate_plan(args)
    plan_freeze_commit = verify_plan_freeze(args, plan)
    result: dict[str, Any] = {
        "mode": "validate_only",
        "plan": "pass",
        "plan_freeze_commit": plan_freeze_commit,
    }
    view_paths = [
        args.views_output,
        args.views_manifest_output,
        args.routing_output,
        *args.e1_packets,
    ]
    e1_paths = [
        *args.e1_parts,
        args.e1_output,
        args.e1_bindings_output,
        *args.e2_packets,
    ]
    final_paths = [
        *args.e2_parts,
        args.e2_output,
        args.outcomes_output,
        args.checks_output,
        args.report_output,
        args.metrics_output,
        args.exposure_ledger_output,
        args.run_manifest_output,
    ]
    views_all, views_any = _presence(view_paths)
    e1_all, e1_any = _presence(e1_paths)
    final_all, final_any = _presence(final_paths)
    if views_any and not views_all:
        raise EnvironmentRealizationError("environment view bundle is partially present")
    if e1_any and not e1_all:
        raise EnvironmentRealizationError("E1 bundle is partially present")
    if final_any and not final_all:
        raise EnvironmentRealizationError("E2/final bundle is partially present")
    if not views_all:
        if e1_any or final_any:
            raise EnvironmentRealizationError(
                "downstream artifacts exist without the environment view bundle"
            )
        result["materialized_views"] = "not_present"
        return result
    views, manifest, routing = load_materialized_views(args, plan)
    view_freeze_commit = verify_view_freeze(args, plan_freeze_commit)
    result["materialized_views"] = {"status": "pass", "record_count": len(views)}
    if args.source_cache_root is not None:
        rebuilt_views, rebuilt_manifest, rebuilt_routing = build_environment_views(
            args, plan, plan_freeze_commit
        )
        if (
            rebuilt_views != views
            or rebuilt_manifest != manifest
            or rebuilt_routing != routing
        ):
            raise EnvironmentRealizationError(
                "materialized views differ from a fresh pinned-source reconstruction"
            )
        result["pinned_source_reconstruction"] = "pass"

    if not e1_all:
        if final_any:
            raise EnvironmentRealizationError(
                "E2/final artifacts exist without the complete E1 bundle"
            )
        result["e1"] = "not_present"
        return result
    e1_records, _ = load_e1_records(args, plan)
    e1_freeze_commit = verify_e1_freeze(args, view_freeze_commit)
    result["e1"] = {
        "status": "pass",
        "record_count": len(e1_records),
        "freeze_commit": e1_freeze_commit,
    }

    if not final_all:
        result["final"] = "not_present"
        return result
    expected_payloads, expected_manifest = build_final_payloads(
        args,
        plan,
        plan_freeze_commit,
        view_freeze_commit,
        e1_freeze_commit,
    )
    for label, (path, expected_bytes) in expected_payloads.items():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != expected_bytes:
            raise EnvironmentRealizationError(
                f"final output differs from deterministic rebuild: {label}"
            )
    result["final"] = {
        "status": "pass",
        "counts": expected_manifest["counts"],
        "status_counts": expected_manifest["status_counts"],
    }
    return result


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        _validate_paths(args)
        if args.freeze_plan:
            result = freeze_plan(args)
        elif args.materialize_views:
            result = materialize_views(args)
        elif args.build_adequacy:
            result = build_adequacy(args)
        elif args.build_final:
            result = build_final(args)
        else:
            result = validate_existing(args)
    except (EnvironmentRealizationError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
