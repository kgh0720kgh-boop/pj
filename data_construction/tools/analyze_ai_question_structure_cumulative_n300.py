#!/usr/bin/env python3
"""Validate and analyze the cumulative N=300 question-only exploration.

The first 100 record bytes are immutable inputs from the frozen N=100 run.
Positions 101--300 use the same record schema, semantic roles, prompt, and
deterministic graph normalizer.  This analyzer has a separately versioned
metrics/report contract and a precommitted operational N=1,000 trigger.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from _common import (
    canonical_json_sha256,
    iter_json_records,
    json_file_bytes,
    jsonl_file_bytes,
    read_json,
    sha256_bytes,
    sha256_file,
    write_output_batch,
)
from validate_question_structure_annotations import cue_errors, forbidden_key_paths
import run_ai_question_structure_scale_exploration as frozen_n100


TOOL_VERSION = "ai_question_structure_cumulative_n300_analyzer_v0_1"
METRICS_SCHEMA_VERSION = (
    "ai_question_structure_cumulative_n300_structural_saturation_metrics_v0_1"
)
CHECK_SCHEMA_VERSION = "ai_question_structure_cumulative_n300_check_v0_1"
RUN_MANIFEST_SCHEMA_VERSION = "ai_question_structure_cumulative_n300_run_manifest_v0_1"
PLAN_SCHEMA_VERSION = "ai_question_structure_cumulative_n300_analysis_plan_v0_1"
ANALYSIS_ID = "ai_question_structure_scale_v0_1_cumulative_n300_analysis_v0_1"
PLAN_STATUS = "contract_frozen_before_positions_101_300_model_outputs"
TARGET_COUNT = 300
PREFIX_COUNT = 100
EXPANSION_COUNT = 200
BLOCK_SIZE = 10
TAIL_BLOCK_COUNT = 5
EXPECTED_NEW_PARTITIONS = tuple(f"partition_{value:02d}" for value in range(4, 9))
EXPECTED_PROVISIONAL_ROLES = [
    "RESOLVE_REFERENT",
    "ACQUIRE_PROPERTY",
    "COMPARE",
    "AGGREGATE",
    "ORDER_OR_EXTREMUM",
    "DERIVE",
    "VERIFY",
    "COMBINE",
    "OTHER",
]
EXPECTED_ROUTING_MODEL_VISIBLE_INPUT_CONTRACT = {
    "visible_fields": ["schema_version", "visibility", "question_id", "question"],
    "routing_manifest_exposed": False,
    "producer_administrative_wrapper_exposed": True,
    "environment_answer_grounding_or_other_record_exposed": False,
    "shared_workspace_access_is_not_server_enforced": True,
    "worker_compliance_is_procedural": True,
}
EXPECTED_GENERATION_CONTRACT = {
    "one_record_per_question": True,
    "duplicate_reviewer_lanes": False,
    "single_frozen_prompt_and_schema_for_all_300": True,
    "same_frozen_prompt_as_n100": True,
    "same_frozen_record_schema_as_n100": True,
    "same_provisional_roles_as_n100": True,
    "same_deterministic_normalizer_as_n100": True,
    "partitioning_is_throughput_only_not_reviewer_multiplicity": True,
    "partition_workers_share_one_model_identity_contract": True,
    "provisional_roles": EXPECTED_PROVISIONAL_ROLES,
    "model_id": "codex_gpt-5",
    "exact_model_revision_status": "revision_not_exposed",
    "seed_status": "not_supported",
    "structured_jsonl_parts_are_primary_capture": True,
    "separate_raw_response_status": (
        "structured_JSONL_parts_are_primary_capture_no_separate_raw_response"
    ),
    "statistical_independence_claimed": False,
    "in_run_prompt_schema_role_or_normalizer_change_allowed": False,
    "other_worker_record_exposed": False,
    "downstream_metric_or_family_exposed": False,
    "environment_exposed": False,
    "answer_or_trace_exposed": False,
    "external_lookup_allowed": False,
    "factual_answer_allowed_in_output": False,
    "model_generated_family_or_signature_allowed": False,
}
EXPECTED_NORMALIZATION_CONTRACT = {
    "transitive_reduction": True,
    "exact_node_ID_and_array_order_invariant_canonicalization": True,
    "signature_levels": list(frozen_n100.SIGNATURE_KINDS),
    "same_role_linear_split_merge_contraction": True,
    "model_output_trusted_for_signature": False,
    "post_hoc_semantic_cluster_merging_in_primary_metrics": False,
}
PRECOMMITTED_N1000_DECISION = {
    "trigger_composition": "ANY",
    "trigger_conditions": {
        "cumulative_contracted_singleton_question_mass": {
            "operator": ">",
            "threshold": 0.05,
        },
        "cumulative_OTHER_question_rate_above_0_05": {
            "operator": ">",
            "threshold": 0.05,
        },
        "tail_50_sequential_contracted_novelty": {
            "positions": [251, 300],
            "novelty_operator": ">",
            "novelty_threshold": 0.10,
            "minimum_tail_new_family_count": 2,
        },
        "material_cross_partition_new_contracted_families": {
            "minimum_family_count": 2,
            "minimum_new200_question_count_per_family": 3,
            "minimum_new_partition_support_per_family": 2,
            "minimum_fixed_ten_question_block_support_per_family": 2,
        },
    },
    "triggered_decision": "EXPAND_UNCHANGED_TO_N1000",
    "no_trigger_decision": (
        "FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_"
        "REPRESENTATIVE_ENVIRONMENT_REALIZATION"
    ),
    "invalid_run_decision": "NO_DECISION_INVALID_CONTRACT_OR_RECORDS",
    "thresholds_are_design_choices_not_universal_statistical_laws": True,
}
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
DEFAULT_PLAN = BASE / "contracts/cumulative_n300_analysis_plan_v0_1.json"
DEFAULT_SCHEMA = BASE / "contracts/semantic_backbone_record_schema_v0_1.json"
DEFAULT_PROMPT = BASE / "prompts/primary_extraction_v0_1.md"
DEFAULT_VIEWS = BASE / "pool/question_only_views_n300.jsonl"
DEFAULT_ROUTING = BASE / "n300_extension_v0_1/producer_routing_manifest_v0_1.json"
DEFAULT_POOL_MANIFEST = ROOT / "data_construction/manifests/ai_question_structure_exploratory_pool_v0_2.json"
DEFAULT_PRIOR_EXPOSURE = ROOT / "data_construction/manifests/question_exposure_ledger_v0_2.json"
DEFAULT_PREFIX_RECORDS = BASE / "run_001/records.jsonl"
DEFAULT_PARTS = tuple(
    BASE / f"n300_extension_v0_1/parts/partition_{value:02d}.jsonl"
    for value in range(4, 9)
)
DEFAULT_RECORDS_OUTPUT = BASE / "cumulative_n300_v0_1/records.jsonl"
DEFAULT_CHECKS = BASE / "cumulative_n300_v0_1/checks.jsonl"
DEFAULT_SIGNATURES = (
    BASE / "cumulative_n300_v0_1/analysis/derived_signatures_v0_1.jsonl"
)
DEFAULT_METRICS = (
    BASE
    / "cumulative_n300_v0_1/analysis/cumulative_n300_structural_saturation_metrics_v0_1.json"
)
DEFAULT_REPORT = (
    BASE
    / "cumulative_n300_v0_1/analysis/cumulative_n300_structural_saturation_report_v0_1.md"
)
DEFAULT_RUN_MANIFEST = BASE / "cumulative_n300_v0_1/run_manifest.json"
DEFAULT_EXPOSURE_OUTPUT = ROOT / "data_construction/manifests/question_exposure_ledger_v0_3.json"
FROZEN_ANALYZER = Path(frozen_n100.__file__).resolve()


class N300AnalysisError(ValueError):
    """Raised when the cumulative N=300 analysis contract is violated."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--views", type=Path, default=DEFAULT_VIEWS)
    parser.add_argument("--routing", type=Path, default=DEFAULT_ROUTING)
    parser.add_argument("--pool-manifest", type=Path, default=DEFAULT_POOL_MANIFEST)
    parser.add_argument("--prior-exposure", type=Path, default=DEFAULT_PRIOR_EXPOSURE)
    parser.add_argument("--prefix-records", type=Path, default=DEFAULT_PREFIX_RECORDS)
    parser.add_argument("--parts", nargs="+", type=Path, default=list(DEFAULT_PARTS))
    parser.add_argument("--records-output", type=Path, default=DEFAULT_RECORDS_OUTPUT)
    parser.add_argument("--checks-output", type=Path, default=DEFAULT_CHECKS)
    parser.add_argument("--signatures-output", type=Path, default=DEFAULT_SIGNATURES)
    parser.add_argument("--metrics-output", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--run-manifest-output", type=Path, default=DEFAULT_RUN_MANIFEST)
    parser.add_argument("--exposure-output", type=Path, default=DEFAULT_EXPOSURE_OUTPUT)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def _require_regular_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise N300AnalysisError(f"{label} must be an existing regular non-symlink file: {path}")


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise N300AnalysisError(f"contract artifact is outside the repository: {path}") from exc


def expected_producer_administrative_wrapper(
    prompt_path: Path, schema_path: Path
) -> dict[str, Any]:
    template = (
        "Fresh fork-none producer assignment: {producer_partition}.\n"
        f"Read only the frozen prompt at {_relative(prompt_path)}, "
        f"the frozen record schema at {_relative(schema_path)}, "
        "and the assigned four-field JSONL input at {input_path}.\n"
        "The prompt phrase 'frozen N=100 question-only view' is legacy scope wording; "
        "the assigned input is the authorized positions 101-300 extension, so process it "
        "without changing any semantic instruction.\n"
        "Do not inspect any other repository artifact, prior or current worker record, "
        "metric, environment/table/document, answer/trace, or external source.\n"
        "Apply the frozen prompt, schema, provisional roles, and deterministic-normalizer "
        "contract unchanged. Preserve input order and produce exactly one JSONL record per "
        "question. Set producer_partition to the coordinator-supplied constant "
        "{producer_partition} in every record. Compute question_view_sha256 as SHA-256 of the "
        "UTF-8 compact canonical JSON of the exact four-field input object, with keys sorted, "
        "ensure_ascii=false, and comma/colon separators. Do not supply factual answers or model-derived "
        "family/signature fields. Write only the assigned output at {output_path}."
    )
    return {
        "status": "frozen_before_positions_101_300_model_outputs",
        "worker_context": "fresh_fork_none_no_inherited_conversation_context",
        "required_placeholders": [
            "{producer_partition}",
            "{input_path}",
            "{output_path}",
        ],
        "template": template,
    }


def _binding(path: Path, *, record_count: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "repository_relative_path": _relative(path),
        "sha256": sha256_file(path),
    }
    if record_count is not None:
        value["record_count"] = record_count
    return value


def _plan_bindings(plan: dict[str, Any]) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for section in ("source_artifacts", "contract_artifacts"):
        items = plan.get(section)
        if not isinstance(items, list):
            raise N300AnalysisError(f"plan {section} must be an array")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise N300AnalysisError(f"plan {section}[{index}] must be an object")
            relative = item.get("repository_relative_path")
            digest = item.get("sha256")
            if (
                not isinstance(relative, str)
                or relative.startswith("/")
                or ".." in Path(relative).parts
                or not isinstance(digest, str)
                or len(digest) != 64
            ):
                raise N300AnalysisError(f"plan {section}[{index}] has an invalid binding")
            if relative in bindings and bindings[relative] != digest:
                raise N300AnalysisError(f"plan binds {relative} to conflicting hashes")
            bindings[relative] = digest
    for relative, expected in bindings.items():
        path = ROOT / relative
        _require_regular_file(path, f"plan-bound artifact {relative}")
        observed = sha256_file(path)
        if observed != expected:
            raise N300AnalysisError(
                f"plan-bound artifact hash mismatch for {relative}: "
                f"expected {expected}, observed {observed}"
            )
    return bindings


def _nested_artifact_bindings(value: Any) -> dict[str, str]:
    output: dict[str, str] = {}
    if isinstance(value, dict):
        relative = value.get("repository_relative_path")
        digest = value.get("sha256")
        if isinstance(relative, str) and isinstance(digest, str):
            output[relative] = digest
        for item in value.values():
            output.update(_nested_artifact_bindings(item))
    elif isinstance(value, list):
        for item in value:
            output.update(_nested_artifact_bindings(item))
    return output


def _require_plan_binding(bindings: dict[str, str], path: Path, label: str) -> None:
    relative = _relative(path)
    expected = bindings.get(relative)
    if expected is None:
        raise N300AnalysisError(f"plan does not bind {label}: {relative}")
    _require_regular_file(path, label)
    observed = sha256_file(path)
    if observed != expected:
        raise N300AnalysisError(
            f"bound {label} hash mismatch: expected {expected}, observed {observed}"
        )


def _schema_validator(schema_path: Path) -> Any:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - project preflight covers this
        raise N300AnalysisError("jsonschema is required") from exc
    schema = read_json(schema_path)
    validator_class = getattr(jsonschema, "Draft202012Validator", None)
    if validator_class is None:
        raise N300AnalysisError("Draft 2020-12 validation is unavailable")
    validator_class.check_schema(schema)
    return validator_class(schema, format_checker=jsonschema.FormatChecker())


def _schema_errors(validator: Any, record: Any, label: str) -> list[str]:
    output: list[str] = []
    for error in sorted(
        validator.iter_errors(record),
        key=lambda item: [str(part) for part in item.absolute_path],
    ):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        output.append(f"{label}.{location}: {error.message}")
    return output


def validate_contract(
    plan_path: Path,
    schema_path: Path,
    prompt_path: Path,
    views_path: Path,
    routing_path: Path,
    pool_manifest_path: Path,
    prior_exposure_path: Path,
    prefix_records_path: Path,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
]:
    for path, label in (
        (plan_path, "N300 plan"),
        (schema_path, "frozen record schema"),
        (prompt_path, "frozen extraction prompt"),
        (views_path, "N300 question-only views"),
        (routing_path, "N300 routing manifest"),
        (pool_manifest_path, "N300 pool manifest"),
        (prior_exposure_path, "prior exposure ledger v0.2"),
        (prefix_records_path, "frozen N100 records"),
        (FROZEN_ANALYZER, "frozen N100 analyzer"),
    ):
        _require_regular_file(path, label)

    plan = read_json(plan_path)
    if not isinstance(plan, dict):
        raise N300AnalysisError("N300 plan must be an object")
    expected_identity = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "analysis_id": ANALYSIS_ID,
        "status": PLAN_STATUS,
        "cumulative_target": TARGET_COUNT,
        "prefix_record_count": PREFIX_COUNT,
        "expansion_record_count": EXPANSION_COUNT,
    }
    for key, expected in expected_identity.items():
        if plan.get(key) != expected:
            raise N300AnalysisError(
                f"N300 plan {key} must be {expected!r}, observed {plan.get(key)!r}"
            )
    if plan.get("record_run_id") != frozen_n100.RUN_ID:
        raise N300AnalysisError("N300 plan record_run_id differs from the frozen schema run_id")
    if plan.get("generation_contract") != EXPECTED_GENERATION_CONTRACT:
        raise N300AnalysisError("N300 plan generation_contract is not the exact frozen contract")
    if plan.get("normalization_contract") != EXPECTED_NORMALIZATION_CONTRACT:
        raise N300AnalysisError("N300 plan normalization_contract is not the exact frozen contract")
    if plan.get("producer_administrative_wrapper") != expected_producer_administrative_wrapper(
        prompt_path, schema_path
    ):
        raise N300AnalysisError("N300 plan producer_administrative_wrapper is not exact")
    expected_legacy_caveat = {
        "prompt_mentions_frozen_n100_view": True,
        "prompt_bytes_changed_for_n300": False,
        "operational_interpretation": (
            "N=100 is legacy scope wording; for this unchanged-contract extension, "
            "assigned records are positions 101-300 from the cumulative N=300 view"
        ),
        "semantic_instruction_change_claimed": False,
    }
    if plan.get("legacy_prompt_wording_caveat") != expected_legacy_caveat:
        raise N300AnalysisError("N300 plan legacy prompt wording caveat is not exact")
    if plan.get("precommitted_n1000_decision") != PRECOMMITTED_N1000_DECISION:
        raise N300AnalysisError(
            "N300 plan does not contain the exact precommitted N1000 decision rule"
        )
    question_ids = plan.get("question_ids")
    if (
        not isinstance(question_ids, list)
        or len(question_ids) != TARGET_COUNT
        or len(set(value for value in question_ids if isinstance(value, str))) != TARGET_COUNT
        or not all(isinstance(value, str) and value for value in question_ids)
    ):
        raise N300AnalysisError("N300 plan must contain 300 unique ordered question_ids")

    bindings = _plan_bindings(plan)
    for path, label in (
        (Path(__file__), "cumulative N300 analyzer"),
        (FROZEN_ANALYZER, "frozen N100 analyzer"),
        (schema_path, "frozen record schema"),
        (prompt_path, "frozen extraction prompt"),
        (views_path, "N300 question-only views"),
        (routing_path, "N300 routing manifest"),
        (pool_manifest_path, "N300 pool manifest"),
        (prior_exposure_path, "prior exposure ledger v0.2"),
        (prefix_records_path, "frozen N100 records"),
    ):
        _require_plan_binding(bindings, path, label)

    _schema_validator(schema_path)
    views = list(iter_json_records(views_path))
    allowed_view_keys = {"schema_version", "visibility", "question_id", "question"}
    if len(views) != TARGET_COUNT:
        raise N300AnalysisError(f"N300 views must contain 300 records, observed {len(views)}")
    if [view.get("question_id") for view in views] != question_ids:
        raise N300AnalysisError("N300 views do not match the exact planned question order")
    for index, view in enumerate(views):
        if set(view) != allowed_view_keys:
            raise N300AnalysisError(f"view {index} is not the exact four-field projection")
        if (
            view.get("schema_version") != "question_only_semantic_view_v0_1"
            or view.get("visibility")
            != "question_only_no_environment_answer_or_proposals"
            or not isinstance(view.get("question"), str)
            or not view["question"].strip()
        ):
            raise N300AnalysisError(f"view {index} violates question-only identity")

    prefix_records = list(iter_json_records(prefix_records_path))
    if len(prefix_records) != PREFIX_COUNT:
        raise N300AnalysisError(
            f"frozen prefix must contain 100 records, observed {len(prefix_records)}"
        )
    if [record.get("question_id") for record in prefix_records] != question_ids[:PREFIX_COUNT]:
        raise N300AnalysisError("frozen N100 records do not match the planned prefix order")

    pool = read_json(pool_manifest_path)
    selection = pool.get("selection") if isinstance(pool, dict) else None
    expected_partition_check = {
        "historical_count": 100,
        "locked_eval_overlap_count": 0,
        "official_dev_count": 3466,
        "pairwise_disjoint": True,
        "selected_ai_exploration_count": TARGET_COUNT,
        "unexposed_unallocated_reserve_count": 3066,
        "union_equals_official_dev": True,
    }
    if (
        not isinstance(pool, dict)
        or pool.get("schema_version")
        != "ai_question_structure_exploration_pool_manifest_v0_2"
        or not isinstance(selection, dict)
        or selection.get("current_target") != TARGET_COUNT
        or selection.get("selected_count") != TARGET_COUNT
        or selection.get("preserved_prefix_count") != PREFIX_COUNT
        or selection.get("added_count") != EXPANSION_COUNT
        or selection.get("selected_question_ids") != question_ids
        or selection.get("unexposed_unallocated_reserve_count") != 3066
        or pool.get("partition_check") != expected_partition_check
    ):
        raise N300AnalysisError("N300 pool manifest does not bind the exact cumulative selection")
    prior_exposure = read_json(prior_exposure_path)
    if (
        not isinstance(prior_exposure, dict)
        or prior_exposure.get("schema_version") != "question_exposure_ledger_v0_2"
    ):
        raise N300AnalysisError("prior exposure ledger must be immutable v0.2")

    routing = read_json(routing_path)
    if not isinstance(routing, dict):
        raise N300AnalysisError("routing manifest must be an object")
    routing_identity = {
        "schema_version": "ai_question_structure_n300_producer_routing_manifest_v0_1",
        "routing_id": "ai_question_structure_scale_v0_1_n300_routing_v0_1",
        "status": PLAN_STATUS,
        "cumulative_target": TARGET_COUNT,
        "prefix_record_count": PREFIX_COUNT,
        "expansion_record_count": EXPANSION_COUNT,
    }
    for key, expected in routing_identity.items():
        if routing.get(key) != expected:
            raise N300AnalysisError(
                f"routing {key} must be {expected!r}, observed {routing.get(key)!r}"
            )
    if (
        routing.get("model_visible_input_contract")
        != EXPECTED_ROUTING_MODEL_VISIBLE_INPUT_CONTRACT
    ):
        raise N300AnalysisError("routing model-visible input contract is not exact")
    routing_planned_outputs = routing.get("planned_model_outputs")
    if (
        not isinstance(routing_planned_outputs, dict)
        or set(routing_planned_outputs) != set(EXPECTED_NEW_PARTITIONS)
    ):
        raise N300AnalysisError("routing planned_model_outputs must cover partitions 04 through 08")
    simplified_routing_outputs: dict[str, dict[str, Any]] = {}
    for partition in EXPECTED_NEW_PARTITIONS:
        item = routing_planned_outputs[partition]
        if (
            not isinstance(item, dict)
            or set(item)
            != {"repository_relative_path", "expected_record_count", "write_status"}
            or item.get("expected_record_count") != 40
            or item.get("write_status") != "not_created_selection_stage"
            or not isinstance(item.get("repository_relative_path"), str)
        ):
            raise N300AnalysisError(f"routing planned model output {partition} is invalid")
        simplified_routing_outputs[partition] = {
            "repository_relative_path": item["repository_relative_path"],
            "expected_record_count": 40,
        }
    plan_parts = plan.get("planned_outputs", {}).get("new_model_parts")
    if plan_parts != simplified_routing_outputs:
        raise N300AnalysisError("plan and routing disagree on planned model outputs")
    assignments = routing.get("assignments")
    if not isinstance(assignments, list) or len(assignments) != EXPANSION_COUNT:
        raise N300AnalysisError("routing must contain exactly 200 assignments")
    if plan.get("assignments") != assignments:
        raise N300AnalysisError("plan assignments differ from the bound routing manifest")
    routing_bindings = _nested_artifact_bindings(routing.get("source_bindings"))
    views_relative = _relative(views_path)
    if routing_bindings.get(views_relative) != sha256_file(views_path):
        raise N300AnalysisError("routing source_bindings do not bind the exact N300 views")
    observed_partitions: Counter[str] = Counter()
    for offset, assignment in enumerate(assignments, start=PREFIX_COUNT + 1):
        if not isinstance(assignment, dict) or set(assignment) != {
            "committed_position",
            "question_id",
            "question_view_sha256",
            "producer_partition",
        }:
            raise N300AnalysisError(f"routing assignment for position {offset} has invalid keys")
        view = views[offset - 1]
        expected_partition = EXPECTED_NEW_PARTITIONS[(offset - PREFIX_COUNT - 1) % 5]
        if (
            assignment.get("committed_position") != offset
            or assignment.get("question_id") != view["question_id"]
            or assignment.get("question_view_sha256") != canonical_json_sha256(view)
            or assignment.get("producer_partition") != expected_partition
        ):
            raise N300AnalysisError(f"routing assignment for position {offset} is not exact")
        observed_partitions[str(assignment["producer_partition"])] += 1
    if observed_partitions != Counter({value: 40 for value in EXPECTED_NEW_PARTITIONS}):
        raise N300AnalysisError("routing must assign 40 interleaved questions to each new partition")
    partition_artifacts = routing.get("partition_artifacts")
    if (
        not isinstance(partition_artifacts, dict)
        or set(partition_artifacts) != set(EXPECTED_NEW_PARTITIONS)
    ):
        raise N300AnalysisError("routing partition_artifacts must cover partitions 04 through 08")
    assignments_by_partition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for assignment in assignments:
        assignments_by_partition[assignment["producer_partition"]].append(assignment)
    for partition in EXPECTED_NEW_PARTITIONS:
        artifact = partition_artifacts[partition]
        if not isinstance(artifact, dict):
            raise N300AnalysisError(f"routing partition artifact {partition} must be an object")
        relative = artifact.get("repository_relative_path")
        if not isinstance(relative, str) or relative.startswith("/") or ".." in Path(relative).parts:
            raise N300AnalysisError(f"routing partition artifact {partition} has invalid path")
        input_path = ROOT / relative
        _require_regular_file(input_path, f"safe input {partition}")
        expected_assignments = assignments_by_partition[partition]
        expected_positions = [item["committed_position"] for item in expected_assignments]
        if (
            artifact.get("record_count") != 40
            or artifact.get("sha256") != sha256_file(input_path)
            or artifact.get("bytes") != input_path.stat().st_size
            or artifact.get("committed_positions_ordered_sha256")
            != canonical_json_sha256(expected_positions)
        ):
            raise N300AnalysisError(f"routing partition artifact {partition} binding is invalid")
        input_views = list(iter_json_records(input_path))
        expected_views = [views[item["committed_position"] - 1] for item in expected_assignments]
        if input_views != expected_views:
            raise N300AnalysisError(
                f"safe input {partition} does not preserve its routed question order"
            )
    return plan, views, routing, prefix_records, pool


def assert_exact_prefix_bytes(
    cumulative_records_path: Path,
    prefix_records_path: Path,
    *,
    prefix_count: int = PREFIX_COUNT,
    target_count: int = TARGET_COUNT,
) -> dict[str, Any]:
    _require_regular_file(cumulative_records_path, "cumulative records")
    _require_regular_file(prefix_records_path, "prefix records")
    prefix_bytes = prefix_records_path.read_bytes()
    cumulative_bytes = cumulative_records_path.read_bytes()
    if not prefix_bytes.endswith(b"\n"):
        raise N300AnalysisError("prefix JSONL must end with a newline for an exact append boundary")
    if not cumulative_bytes.startswith(prefix_bytes):
        raise N300AnalysisError(
            "cumulative records do not preserve the frozen prefix byte-for-byte"
        )
    prefix_records = list(iter_json_records(prefix_records_path))
    cumulative_records = list(iter_json_records(cumulative_records_path))
    if len(prefix_records) != prefix_count:
        raise N300AnalysisError(
            f"prefix record count must be {prefix_count}, observed {len(prefix_records)}"
        )
    if len(cumulative_records) != target_count:
        raise N300AnalysisError(
            f"cumulative record count must be {target_count}, observed {len(cumulative_records)}"
        )
    if cumulative_records[:prefix_count] != prefix_records:
        raise N300AnalysisError("parsed cumulative prefix differs from frozen prefix records")
    return {
        "prefix_record_count": prefix_count,
        "cumulative_record_count": target_count,
        "prefix_sha256": sha256_bytes(prefix_bytes),
        "cumulative_sha256": sha256_bytes(cumulative_bytes),
        "byte_exact_prefix": True,
        "parsed_record_exact_prefix": True,
    }


def merge_partition_parts(
    part_paths: list[Path],
    routing: dict[str, Any],
    planned_parts: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(part_paths) != len(EXPECTED_NEW_PARTITIONS):
        raise N300AnalysisError("exactly five N300 model part files are required")
    if len({path.resolve() for path in part_paths}) != len(part_paths):
        raise N300AnalysisError("N300 model part paths must be distinct")
    if set(planned_parts) != set(EXPECTED_NEW_PARTITIONS):
        raise N300AnalysisError("plan new_model_parts must cover partitions 04 through 08")
    expected_paths: dict[str, Path] = {}
    for partition in EXPECTED_NEW_PARTITIONS:
        value = planned_parts[partition]
        if (
            not isinstance(value, dict)
            or set(value) != {"repository_relative_path", "expected_record_count"}
            or value.get("expected_record_count") != 40
            or not isinstance(value.get("repository_relative_path"), str)
        ):
            raise N300AnalysisError(f"planned model output for {partition} is invalid")
        expected_paths[partition] = ROOT / value["repository_relative_path"]
    if {path.resolve() for path in part_paths} != {
        path.resolve() for path in expected_paths.values()
    }:
        raise N300AnalysisError("runtime model part paths differ from plan planned_outputs")
    assignments_by_partition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for assignment in routing["assignments"]:
        assignments_by_partition[assignment["producer_partition"]].append(assignment)
    positioned: dict[int, dict[str, Any]] = {}
    bindings: dict[str, Any] = {}
    observed_partitions: set[str] = set()
    for path in part_paths:
        _require_regular_file(path, "N300 model part")
        part_records = list(iter_json_records(path))
        if len(part_records) != 40:
            raise N300AnalysisError(
                f"N300 model part must contain 40 records, observed {len(part_records)}: {path}"
            )
        partitions = {
            record.get("producer_partition")
            for record in part_records
            if isinstance(record, dict)
        }
        if len(partitions) != 1 or next(iter(partitions)) not in EXPECTED_NEW_PARTITIONS:
            raise N300AnalysisError(f"N300 model part has invalid producer identity: {path}")
        partition = str(next(iter(partitions)))
        if partition in observed_partitions:
            raise N300AnalysisError(f"duplicate model part for {partition}")
        observed_partitions.add(partition)
        if path.resolve() != expected_paths[partition].resolve():
            raise N300AnalysisError(f"model part path does not match planned {partition} output")
        expected = assignments_by_partition[partition]
        for record, assignment in zip(part_records, expected):
            if (
                record.get("question_id") != assignment["question_id"]
                or record.get("question_view_sha256")
                != assignment["question_view_sha256"]
                or record.get("producer_partition") != partition
            ):
                raise N300AnalysisError(
                    f"model part {partition} does not follow routed input order at "
                    f"position {assignment['committed_position']}"
                )
            position = assignment["committed_position"]
            if position in positioned:
                raise N300AnalysisError(f"duplicate routed committed position {position}")
            positioned[position] = record
        bindings[partition] = _binding(path, record_count=len(part_records))
    if observed_partitions != set(EXPECTED_NEW_PARTITIONS):
        raise N300AnalysisError("model parts do not cover partitions 04 through 08 exactly once")
    expected_positions = list(range(PREFIX_COUNT + 1, TARGET_COUNT + 1))
    if sorted(positioned) != expected_positions:
        raise N300AnalysisError("model parts do not cover committed positions 101 through 300")
    return [positioned[position] for position in expected_positions], dict(sorted(bindings.items()))


def build_cumulative_records_payload(
    prefix_records_path: Path,
    new_records: list[dict[str, Any]],
) -> tuple[bytes, list[dict[str, Any]], dict[str, Any]]:
    _require_regular_file(prefix_records_path, "frozen N100 records")
    prefix_bytes = prefix_records_path.read_bytes()
    if not prefix_bytes.endswith(b"\n"):
        raise N300AnalysisError("frozen N100 records must end at an exact JSONL newline")
    prefix_records = list(iter_json_records(prefix_records_path))
    if len(prefix_records) != PREFIX_COUNT:
        raise N300AnalysisError("frozen prefix must contain exactly 100 records")
    if len(new_records) != EXPANSION_COUNT:
        raise N300AnalysisError("N300 extension must contain exactly 200 records")
    payload = prefix_bytes + jsonl_file_bytes(new_records)
    records = prefix_records + new_records
    if not payload.startswith(prefix_bytes):  # defensive; construction should make this tautological
        raise N300AnalysisError("constructed cumulative payload lost the frozen byte prefix")
    preservation = {
        "prefix_record_count": PREFIX_COUNT,
        "cumulative_record_count": TARGET_COUNT,
        "prefix_sha256": sha256_bytes(prefix_bytes),
        "cumulative_sha256": sha256_bytes(payload),
        "byte_exact_prefix": True,
        "parsed_record_exact_prefix": records[:PREFIX_COUNT] == prefix_records,
        "construction": "frozen_prefix_bytes_plus_canonical_new200_JSONL_in_committed_order",
    }
    return payload, records, preservation


def validate_records(
    records: list[Any],
    views: list[dict[str, Any]],
    routing: dict[str, Any],
    schema_path: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    validator = _schema_validator(schema_path)
    expected_ids = [view["question_id"] for view in views]
    view_by_id = {view["question_id"]: view for view in views}
    assignments = {
        item["committed_position"]: item for item in routing["assignments"]
    }
    global_errors: list[str] = []
    observed_ids = [record.get("question_id") for record in records if isinstance(record, dict)]
    if len(records) != TARGET_COUNT:
        global_errors.append(f"records must contain exactly 300 objects, observed {len(records)}")
    if observed_ids != expected_ids:
        global_errors.append("records do not match the exact 300-question order")
    if len(set(value for value in observed_ids if isinstance(value, str))) != len(observed_ids):
        global_errors.append("record question IDs are not unique")

    checks: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        position = index + 1
        label = f"records[{index}]"
        errors = _schema_errors(validator, record, label)
        if isinstance(record, dict):
            question_id = record.get("question_id")
            view = view_by_id.get(question_id) if isinstance(question_id, str) else None
            if view is None:
                errors.append(f"{label}.question_id is outside the frozen N300 pool")
            else:
                if record.get("question") != view["question"]:
                    errors.append(f"{label}.question differs from the exact view")
                if record.get("question_view_sha256") != canonical_json_sha256(view):
                    errors.append(f"{label}.question_view_sha256 is invalid")
            if position > PREFIX_COUNT:
                assignment = assignments.get(position)
                if assignment is None:
                    errors.append(f"{label} has no frozen producer assignment")
                elif (
                    record.get("question_id") != assignment["question_id"]
                    or record.get("question_view_sha256")
                    != assignment["question_view_sha256"]
                    or record.get("producer_partition") != assignment["producer_partition"]
                ):
                    errors.append(f"{label} differs from the frozen producer assignment")
            contaminated = forbidden_key_paths(record)
            if contaminated:
                errors.append(
                    f"{label} contains forbidden later-layer keys: {contaminated[:20]!r}"
                )
            question = record.get("question")
            if isinstance(question, str):
                errors.extend(cue_errors(record, question, label))
            primary_graph = record.get("primary_graph")
            if isinstance(primary_graph, dict):
                errors.extend(frozen_n100.graph_errors(primary_graph, f"{label}.primary_graph"))
                try:
                    primary_signature = canonical_json_sha256(
                        frozen_n100.canonical_graph(primary_graph, "fine")
                    )
                except (KeyError, ValueError) as exc:
                    errors.append(f"{label}.primary_graph canonicalization failed: {exc}")
                    primary_signature = None
                alternative_ids: list[str] = []
                alternative_signatures: list[str] = []
                alternatives = record.get("alternative_graphs")
                if isinstance(alternatives, list):
                    for alt_index, alternative in enumerate(alternatives):
                        if not isinstance(alternative, dict):
                            continue
                        alternative_ids.append(str(alternative.get("alternative_id")))
                        graph = alternative.get("graph")
                        errors.extend(
                            frozen_n100.graph_errors(
                                graph, f"{label}.alternative_graphs[{alt_index}].graph"
                            )
                        )
                        if isinstance(graph, dict):
                            try:
                                signature = canonical_json_sha256(
                                    frozen_n100.canonical_graph(graph, "fine")
                                )
                                alternative_signatures.append(signature)
                                if signature == primary_signature:
                                    errors.append(
                                        f"{label}.alternative_graphs[{alt_index}] duplicates the primary graph"
                                    )
                            except (KeyError, ValueError) as exc:
                                errors.append(
                                    f"{label}.alternative_graphs[{alt_index}] canonicalization failed: {exc}"
                                )
                if len(set(alternative_ids)) != len(alternative_ids):
                    errors.append(f"{label}.alternative IDs are not unique")
                if len(set(alternative_signatures)) != len(alternative_signatures):
                    errors.append(f"{label}.alternative graphs are not structurally unique")
        errors = sorted(set(errors))
        checks.append(
            {
                "schema_version": CHECK_SCHEMA_VERSION,
                "tool_version": TOOL_VERSION,
                "record_index": index,
                "committed_position": position,
                "question_id": record.get("question_id") if isinstance(record, dict) else None,
                "status": "pass" if not errors else "fail",
                "errors": errors,
            }
        )
    all_errors = sorted(set(global_errors + [error for item in checks for error in item["errors"]]))
    if global_errors:
        checks.append(
            {
                "schema_version": CHECK_SCHEMA_VERSION,
                "tool_version": TOOL_VERSION,
                "record_index": None,
                "committed_position": None,
                "question_id": None,
                "status": "fail",
                "errors": sorted(set(global_errors)),
            }
        )
    return checks, all_errors


def derive_signatures(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Delegate all four signature resolutions to the SHA-pinned normalizer."""

    return [frozen_n100.signature_bundle(record) for record in records]


def _family_summary(signatures: list[str | None]) -> dict[str, Any]:
    valid = [value for value in signatures if isinstance(value, str)]
    counts = Counter(valid)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    total = len(valid)
    singleton_count = sum(count == 1 for count in counts.values())
    doubleton_count = sum(count == 2 for count in counts.values())
    coverage = {
        f"top_{limit}": (
            sum(count for _, count in ordered[:limit]) / total if total else None
        )
        for limit in (1, 5, 10, 20)
    }
    rarefaction: list[dict[str, Any]] = []
    if total:
        sample_sizes = list(range(10, total + 1, 10))
        if not sample_sizes or sample_sizes[-1] != total:
            sample_sizes.append(total)
        for sample_size in sample_sizes:
            denominator = math.comb(total, sample_size)
            expected = 0.0
            for count in counts.values():
                absent = (
                    math.comb(total - count, sample_size) / denominator
                    if total - count >= sample_size
                    else 0.0
                )
                expected += 1.0 - absent
            rarefaction.append(
                {
                    "sample_size": sample_size,
                    "expected_observed_families": expected,
                }
            )
    return {
        "question_count": len(signatures),
        "representable_count": total,
        "observed_family_count": len(counts),
        "singleton_family_count": singleton_count,
        "doubleton_family_count": doubleton_count,
        "singleton_question_mass": singleton_count / total if total else None,
        "good_turing_unseen_mass_diagnostic": singleton_count / total if total else None,
        "top_k_question_coverage": coverage,
        "exact_rarefaction_order_independent": rarefaction,
        "families": [
            {"signature": signature, "question_count": count}
            for signature, count in ordered
        ],
    }


def transfer_from_prefix(
    signatures: list[str | None], *, prefix_count: int = PREFIX_COUNT
) -> dict[str, Any]:
    prefix = {value for value in signatures[:prefix_count] if isinstance(value, str)}
    expansion = [value for value in signatures[prefix_count:] if isinstance(value, str)]
    seen_count = sum(value in prefix for value in expansion)
    unseen = [value for value in expansion if value not in prefix]
    return {
        "baseline_positions": [1, prefix_count],
        "expansion_positions": [prefix_count + 1, len(signatures)],
        "expansion_question_count": len(signatures) - prefix_count,
        "representable_expansion_count": len(expansion),
        "questions_in_families_seen_in_prefix": seen_count,
        "questions_in_families_unseen_in_prefix": len(unseen),
        "transfer_rate": seen_count / len(expansion) if expansion else None,
        "new_family_count": len(set(unseen)),
    }


def expansion_block_novelty(
    signatures: list[str | None],
    *,
    prefix_count: int = PREFIX_COUNT,
    block_size: int = BLOCK_SIZE,
) -> list[dict[str, Any]]:
    baseline = {value for value in signatures[:prefix_count] if isinstance(value, str)}
    sequential_seen = set(baseline)
    output: list[dict[str, Any]] = []
    for start in range(prefix_count, len(signatures), block_size):
        block = signatures[start : start + block_size]
        valid = [value for value in block if isinstance(value, str)]
        sequential_novel = [value for value in valid if value not in sequential_seen]
        baseline_unseen = [value for value in valid if value not in baseline]
        sequential_new_families = sorted(set(sequential_novel))
        output.append(
            {
                "positions": [start + 1, min(start + block_size, len(signatures))],
                "representable_questions": len(valid),
                "sequential_new_family_count": len(sequential_new_families),
                "sequential_new_family_signatures": sequential_new_families,
                "sequential_novel_question_count": len(sequential_novel),
                "sequential_question_novelty_rate": (
                    len(sequential_novel) / len(valid) if valid else None
                ),
                "n100_baseline_unseen_family_count": len(set(baseline_unseen)),
                "n100_baseline_unseen_question_count": len(baseline_unseen),
                "n100_baseline_unseen_question_rate": (
                    len(baseline_unseen) / len(valid) if valid else None
                ),
            }
        )
        sequential_seen.update(valid)
    return output


def new_family_partition_support(
    records: list[dict[str, Any]],
    signatures: list[str | None],
    *,
    prefix_count: int = PREFIX_COUNT,
    block_size: int = BLOCK_SIZE,
) -> dict[str, Any]:
    prefix = {value for value in signatures[:prefix_count] if isinstance(value, str)}
    positions_by_signature: dict[str, list[int]] = defaultdict(list)
    for position, signature in enumerate(signatures[prefix_count:], start=prefix_count + 1):
        if isinstance(signature, str) and signature not in prefix:
            positions_by_signature[signature].append(position)
    families: list[dict[str, Any]] = []
    for signature in sorted(positions_by_signature):
        positions = positions_by_signature[signature]
        partitions = Counter(str(records[position - 1]["producer_partition"]) for position in positions)
        blocks = sorted({1 + (position - prefix_count - 1) // block_size for position in positions})
        qualifies = len(positions) >= 3 and len(partitions) >= 2 and len(blocks) >= 2
        families.append(
            {
                "signature": signature,
                "new_expansion_question_count": len(positions),
                "question_ids": [records[position - 1]["question_id"] for position in positions],
                "committed_positions": positions,
                "partition_support": dict(sorted(partitions.items())),
                "partition_support_count": len(partitions),
                "fixed_ten_question_block_numbers": blocks,
                "fixed_ten_question_block_support_count": len(blocks),
                "recurs_at_least_twice": len(positions) >= 2,
                "recurs_across_new_partitions": len(partitions) >= 2,
                "qualifies_material_cross_partition_recurrence": qualifies,
            }
        )
    recurring = [item for item in families if item["recurs_at_least_twice"]]
    cross_partition = [item for item in recurring if item["recurs_across_new_partitions"]]
    material = [
        item for item in families if item["qualifies_material_cross_partition_recurrence"]
    ]
    return {
        "prefix_count": prefix_count,
        "expansion_count": len(records) - prefix_count,
        "producer_partitions_considered": sorted(
            {str(record["producer_partition"]) for record in records[prefix_count:]}
        ),
        "new_family_count": len(families),
        "recurring_new_family_count": len(recurring),
        "cross_partition_recurring_new_family_count": len(cross_partition),
        "material_cross_partition_recurring_new_family_count": len(material),
        "material_family_definition": {
            "minimum_new_expansion_question_count": 3,
            "minimum_new_partition_support_count": 2,
            "minimum_fixed_ten_question_block_support_count": 2,
        },
        "families": families,
    }


def _graph_parts(graph: dict[str, Any]) -> tuple[dict[str, str], set[tuple[str, str]]]:
    labels = {node["node_id"]: node["role"] for node in graph["nodes"]}
    edges = {
        (dependency, node["node_id"])
        for node in graph["nodes"]
        for dependency in node["depends_on"]
    }
    return labels, edges


def _edge_profile(
    records: Iterable[dict[str, Any]], *, reduce_transitive_edges: bool
) -> dict[str, Any]:
    edge_counts: list[int] = []
    branch_ids: list[str] = []
    join_ids: list[str] = []
    transitions: Counter[str] = Counter()
    for record in records:
        graph = record.get("primary_graph")
        if not isinstance(graph, dict):
            continue
        labels, edges = _graph_parts(graph)
        if reduce_transitive_edges:
            edges = frozen_n100.transitive_reduction(edges)
        edge_counts.append(len(edges))
        outdegree = Counter(source for source, _ in edges)
        indegree = Counter(target for _, target in edges)
        if any(value > 1 for value in outdegree.values()):
            branch_ids.append(record["question_id"])
        if any(value > 1 for value in indegree.values()):
            join_ids.append(record["question_id"])
        transitions.update(f"{labels[source]}->{labels[target]}" for source, target in edges)
    return {
        "representable_question_count": len(edge_counts),
        "mean_edge_count": statistics.mean(edge_counts) if edge_counts else None,
        "branch_question_count": len(branch_ids),
        "branch_question_rate": len(branch_ids) / len(edge_counts) if edge_counts else None,
        "branch_question_ids": branch_ids,
        "join_question_count": len(join_ids),
        "join_question_rate": len(join_ids) / len(edge_counts) if edge_counts else None,
        "join_question_ids": join_ids,
        "directed_role_transition_counts": dict(sorted(transitions.items())),
    }


def raw_and_normalized_graph_profile(records: list[dict[str, Any]]) -> dict[str, Any]:
    raw = _edge_profile(records, reduce_transitive_edges=False)
    reduced = _edge_profile(records, reduce_transitive_edges=True)
    removed_ids: list[str] = []
    removed_count = 0
    for record in records:
        graph = record.get("primary_graph")
        if not isinstance(graph, dict):
            continue
        _, edges = _graph_parts(graph)
        normalized = frozen_n100.transitive_reduction(edges)
        difference = len(edges) - len(normalized)
        if difference:
            removed_ids.append(record["question_id"])
            removed_count += difference
    return {
        "primary_normalized_definition": "transitive_reduction_of_declared_dependency_edges",
        "raw_declared_dependencies_sensitivity": raw,
        "transitive_reduced_normalized_dependencies": reduced,
        "removed_transitive_edge_count": removed_count,
        "questions_with_removed_transitive_edges": removed_ids,
    }


def _record_profile(records: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(str(record["status"]) for record in records)
    uncertainty = sum(bool(record["uncertainty"]["present"]) for record in records)
    alternatives = sum(bool(record["alternative_graphs"]) for record in records)
    node_counts: list[int] = []
    other_questions = 0
    for record in records:
        graph = record.get("primary_graph")
        if not isinstance(graph, dict):
            continue
        roles = [str(node["role"]) for node in graph["nodes"]]
        node_counts.append(len(roles))
        other_questions += "OTHER" in roles
    return {
        "record_count": len(records),
        "status_counts": dict(sorted(statuses.items())),
        "uncertain_count": uncertainty,
        "uncertain_rate": uncertainty / len(records) if records else None,
        "alternative_graph_question_count": alternatives,
        "alternative_graph_question_rate": alternatives / len(records) if records else None,
        "representable_question_count": len(node_counts),
        "mean_primary_node_count": statistics.mean(node_counts) if node_counts else None,
        "other_question_count": other_questions,
        "other_question_rate": other_questions / len(records) if records else None,
    }


def evaluate_n1000_trigger(
    contracted_cumulative: dict[str, Any],
    contracted_blocks: list[dict[str, Any]],
    contracted_partition_support: dict[str, Any],
    *,
    cumulative_other_question_rate: float,
) -> dict[str, Any]:
    if len(contracted_blocks) < TAIL_BLOCK_COUNT:
        raise N300AnalysisError("N1000 trigger requires at least five expansion blocks")
    singleton_mass = contracted_cumulative.get("singleton_question_mass")
    if singleton_mass is None:
        raise N300AnalysisError("N1000 trigger requires representable contracted signatures")
    tail = contracted_blocks[-TAIL_BLOCK_COUNT:]
    tail_representable = sum(item["representable_questions"] for item in tail)
    if tail_representable == 0:
        raise N300AnalysisError("N1000 tail trigger has no representable questions")
    tail_novel_questions = sum(item["sequential_novel_question_count"] for item in tail)
    tail_new_signatures = sorted(
        {
            signature
            for item in tail
            for signature in item["sequential_new_family_signatures"]
        }
    )
    tail_rate = tail_novel_questions / tail_representable
    material_count = contracted_partition_support[
        "material_cross_partition_recurring_new_family_count"
    ]
    trigger_values = {
        "cumulative_contracted_singleton_question_mass_above_0_05": (
            singleton_mass > 0.05
        ),
        "cumulative_OTHER_question_rate_above_0_05": (
            cumulative_other_question_rate > 0.05
        ),
        "tail_50_sequential_contracted_novelty_above_0_10_with_at_least_2_new_families": (
            tail_rate > 0.10 and len(tail_new_signatures) >= 2
        ),
        "at_least_2_material_cross_partition_new_contracted_families": (
            material_count >= 2
        ),
    }
    return {
        "decision_rule_status": "precommitted_before_positions_101_300_model_outputs",
        "decision_resolution": "contracted_semantic_dag_only",
        "trigger_composition": "ANY",
        "trigger_values": trigger_values,
        "observed_values": {
            "cumulative_contracted_singleton_question_mass": singleton_mass,
            "cumulative_OTHER_question_rate": cumulative_other_question_rate,
            "tail_positions": [tail[0]["positions"][0], tail[-1]["positions"][1]],
            "tail_representable_question_count": tail_representable,
            "tail_sequential_novel_question_count": tail_novel_questions,
            "tail_sequential_question_novelty_rate": tail_rate,
            "tail_sequential_new_family_count": len(tail_new_signatures),
            "material_cross_partition_new_contracted_family_count": material_count,
        },
        "decision": (
            PRECOMMITTED_N1000_DECISION["triggered_decision"]
            if any(trigger_values.values())
            else PRECOMMITTED_N1000_DECISION["no_trigger_decision"]
        ),
        "thresholds_are_design_choices_not_universal_statistical_laws": True,
        "decision_is_operational_not_semantic_correctness": True,
    }


def _checkpoint(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        key: summary[key]
        for key in (
            "question_count",
            "representable_count",
            "observed_family_count",
            "singleton_family_count",
            "doubleton_family_count",
            "singleton_question_mass",
            "top_k_question_coverage",
        )
    }


def build_metrics(
    records: list[dict[str, Any]],
    derived: list[dict[str, Any]],
    *,
    prefix_preservation: dict[str, Any],
    source_bindings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if len(records) != TARGET_COUNT or len(derived) != TARGET_COUNT:
        raise N300AnalysisError("metrics require exactly 300 aligned records/signatures")
    signatures_by_kind = {
        kind: [item["signatures"][kind] for item in derived]
        for kind in frozen_n100.SIGNATURE_KINDS
    }
    levels: dict[str, Any] = {}
    for kind in frozen_n100.SIGNATURE_KINDS:
        signatures = signatures_by_kind[kind]
        cumulative = _family_summary(signatures)
        blocks = expansion_block_novelty(signatures)
        support = new_family_partition_support(records, signatures)
        levels[kind] = {
            "cumulative_n300": cumulative,
            "checkpoints": {
                "n30": _checkpoint(_family_summary(signatures[:30])),
                "n100": _checkpoint(_family_summary(signatures[:PREFIX_COUNT])),
                "n300": _checkpoint(cumulative),
            },
            "new_200_transfer_from_n100": transfer_from_prefix(signatures),
            "new_200_block_novelty": blocks,
            "n100_unseen_family_partition_support": support,
        }

    fine = signatures_by_kind["fine_semantic_dag"]
    contracted = signatures_by_kind["contracted_semantic_dag"]
    prefix_fine = {value for value in fine[:PREFIX_COUNT] if isinstance(value, str)}
    prefix_contracted = {
        value for value in contracted[:PREFIX_COUNT] if isinstance(value, str)
    }
    novel_fine_indexes = [
        index
        for index, value in enumerate(fine[PREFIX_COUNT:], start=PREFIX_COUNT)
        if isinstance(value, str) and value not in prefix_fine
    ]
    absorbed = sum(contracted[index] in prefix_contracted for index in novel_fine_indexes)

    graph_by_partition: dict[str, Any] = {}
    records_by_partition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records[PREFIX_COUNT:]:
        records_by_partition[str(record["producer_partition"])].append(record)
    for partition in sorted(records_by_partition):
        graph_by_partition[partition] = {
            "record_profile": _record_profile(records_by_partition[partition]),
            "graph_profile": raw_and_normalized_graph_profile(records_by_partition[partition]),
        }

    cumulative_record_profile = _record_profile(records)
    contracted_value = levels["contracted_semantic_dag"]
    decision = evaluate_n1000_trigger(
        contracted_value["cumulative_n300"],
        contracted_value["new_200_block_novelty"],
        contracted_value["n100_unseen_family_partition_support"],
        cumulative_other_question_rate=cumulative_record_profile["other_question_rate"],
    )
    return {
        "schema_version": METRICS_SCHEMA_VERSION,
        "analysis_id": ANALYSIS_ID,
        "record_contract_run_id": frozen_n100.RUN_ID,
        "tool_version": TOOL_VERSION,
        "evidence_class": frozen_n100.EVIDENCE_CLASS,
        "cumulative_target": TARGET_COUNT,
        "prefix_record_count": PREFIX_COUNT,
        "expansion_record_count": EXPANSION_COUNT,
        "source_bindings": source_bindings or {},
        "validation": {
            "valid_record_count": TARGET_COUNT,
            "invalid_record_count": 0,
            "prefix_preservation": prefix_preservation,
            "human_evidence_count": 0,
            "gold_claimed": False,
            "semantic_correctness_evaluated": False,
            "grounding_or_execution_evaluated": False,
        },
        "segment_record_profiles": {
            "cumulative_n300": cumulative_record_profile,
            "frozen_prefix_n100": _record_profile(records[:PREFIX_COUNT]),
            "new_200": _record_profile(records[PREFIX_COUNT:]),
        },
        "signature_definitions": {
            "fine_semantic_dag": "frozen_N100_transitively_reduced_exact_ID_invariant_labeled_DAG",
            "contracted_semantic_dag": "frozen_N100_same_role_linear_contraction_then_canonical_transitive_reduction",
            "topology_shape": "frozen_N100_transitively_reduced_exact_ID_invariant_unlabeled_DAG",
            "task": "frozen_N100_fine_semantic_DAG_plus_answer_kind_and_cardinality",
        },
        "signature_levels": levels,
        "fine_to_contracted_transfer_sensitivity": {
            "new_200_questions_with_fine_signature_unseen_in_n100": len(novel_fine_indexes),
            "of_those_with_contracted_signature_seen_in_n100": absorbed,
            "rate": absorbed / len(novel_fine_indexes) if novel_fine_indexes else None,
            "same_role_contraction_establishes_semantic_equivalence": False,
        },
        "graph_profiles": {
            "cumulative_n300": raw_and_normalized_graph_profile(records),
            "frozen_prefix_n100": raw_and_normalized_graph_profile(records[:PREFIX_COUNT]),
            "new_200": raw_and_normalized_graph_profile(records[PREFIX_COUNT:]),
            "new_200_by_producer_partition": graph_by_partition,
        },
        "n1000_precommitted_decision": decision,
        "analysis_separation": {
            "primary_precommitted": [
                "four_frozen_signature_resolutions",
                "n100_to_new200_transfer",
                "fixed_ten_question_block_novelty",
                "transitive_reduced_normalized_branch_join_profile",
                "new_family_partition_and_block_support",
                "N1000_operational_trigger",
            ],
            "excluded_post_hoc": [
                "description_style_proxies",
                "semantic_cluster_merging",
                "alternative_normalizer_or_role_mapping",
                "threshold_changes_after_N300_outputs",
                "record_exclusion_after_observing_metrics",
            ],
            "post_hoc_results_may_not_change_primary_decision": True,
        },
        "interpretation_boundary": {
            "supported": [
                "descriptive_recurrence_under_the_frozen_question_only_AI_extractor",
                "cumulative_N300_and_new200_transfer_under_fixed_signatures",
                "producer_partition_support_as_a_robustness_diagnostic",
                "normalized_dependency_shape_frequency",
            ],
            "unsupported": [
                "semantic_correctness",
                "human_agreement_or_gold_status",
                "statistical_independence_of_producer_partitions",
                "semantic_equivalence_created_by_same_role_contraction",
                "universal_semantic_topology_or_saturation",
                "common_executable_graph",
                "grounding_answer_accuracy_or_modeling_readiness",
            ],
        },
    }


def render_report(metrics: dict[str, Any]) -> str:
    lines = [
        "# Cumulative N=300 question-only semantic-backbone exploration",
        "",
        "Evidence class: AI-generated exploratory, non-human, non-gold.",
        "",
        "## Mechanical integrity",
        "",
        f"- Valid records: {metrics['validation']['valid_record_count']}/300",
        "- Frozen N=100 prefix preserved byte-for-byte: "
        f"`{str(metrics['validation']['prefix_preservation']['byte_exact_prefix']).lower()}`",
        "- New records: positions 101–300 under the frozen schema, prompt, roles, and normalizer.",
        "",
        "## Four frozen signature resolutions",
        "",
        "| Signature | N300 families | Singleton mass | Top-10 coverage | N100→new200 transfer | New families |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for kind in frozen_n100.SIGNATURE_KINDS:
        value = metrics["signature_levels"][kind]
        cumulative = value["cumulative_n300"]
        transfer = value["new_200_transfer_from_n100"]
        lines.append(
            f"| {kind} | {cumulative['observed_family_count']}"
            f" | {cumulative['singleton_question_mass']:.3f}"
            f" | {cumulative['top_k_question_coverage']['top_10']:.3f}"
            f" | {transfer['transfer_rate']:.3f}"
            f" | {transfer['new_family_count']} |"
        )
    normalized = metrics["graph_profiles"]["cumulative_n300"][
        "transitive_reduced_normalized_dependencies"
    ]
    raw = metrics["graph_profiles"]["cumulative_n300"][
        "raw_declared_dependencies_sensitivity"
    ]
    contracted_support = metrics["signature_levels"]["contracted_semantic_dag"][
        "n100_unseen_family_partition_support"
    ]
    decision = metrics["n1000_precommitted_decision"]
    lines.extend(
        [
            "",
            "Fine, contracted, topology, and task results are reported separately. Contracted recurrence is a split/merge sensitivity view and is not semantic equivalence.",
            "",
            "## Normalized graph profile",
            "",
            f"- Transitive-reduced mean edges: {normalized['mean_edge_count']:.3f}",
            f"- Transitive-reduced branches: {normalized['branch_question_count']}/300",
            f"- Transitive-reduced joins: {normalized['join_question_count']}/300",
            f"- Raw declared branches/joins (sensitivity only): {raw['branch_question_count']}/{raw['join_question_count']}",
            "",
            "## New-family producer support",
            "",
            f"- N100-unseen contracted families: {contracted_support['new_family_count']}",
            f"- Recurring across at least two new producer partitions: {contracted_support['cross_partition_recurring_new_family_count']}",
            f"- Material trigger-qualified families: {contracted_support['material_cross_partition_recurring_new_family_count']}",
            "",
            "Producer partitions are generation contexts, not independent human reviewers. Cross-partition support is a robustness diagnostic, not proof of semantic novelty.",
            "",
            "## Precommitted N=1,000 decision",
            "",
            f"Decision: `{decision['decision']}`.",
            f"Trigger values: `{json.dumps(decision['trigger_values'], sort_keys=True)}`",
            "",
            "The trigger is an operational scale decision frozen before positions 101–300 were generated. Post-hoc style audits, semantic cluster merges, alternate normalizers, or threshold changes cannot replace it.",
            "",
            "## Interpretation boundary",
            "",
            "These metrics describe recurrence, transfer, partition support, and normalized graph shape under one frozen AI extractor. They do not establish semantic correctness, human agreement, gold labels, universal saturation, an executable graph, grounding, or answer accuracy.",
            "",
        ]
    )
    return "\n".join(lines)


def _planned_artifact(path: Path, payload: bytes, *, record_count: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "repository_relative_path": _relative(path),
        "sha256": sha256_bytes(payload),
    }
    if record_count is not None:
        value["record_count"] = record_count
    return value


def build_completion_exposure_ledger(
    *,
    question_ids: list[str],
    pool: dict[str, Any],
    prior_exposure_path: Path,
    plan_path: Path,
    pool_manifest_path: Path,
    routing_path: Path,
    cumulative_records_path: Path,
    cumulative_records_payload: bytes,
    contract_freeze_commit: str,
) -> dict[str, Any]:
    if len(question_ids) != TARGET_COUNT or len(set(question_ids)) != TARGET_COUNT:
        raise N300AnalysisError("completion exposure requires exactly 300 unique question IDs")
    selection = pool["selection"]
    reserve_set_sha = selection.get("reserve_question_ids_set_sha256")
    if not isinstance(reserve_set_sha, str) or len(reserve_set_sha) != 64:
        raise N300AnalysisError("pool manifest lacks the reserve question-ID set binding")
    prior_exposure = read_json(prior_exposure_path)
    historical_exposure = prior_exposure.get("historical_exposure")
    if not isinstance(historical_exposure, dict):
        raise N300AnalysisError("prior exposure ledger lacks historical_exposure")
    expected_partition_check = {
        "historical_count": 100,
        "locked_eval_overlap_count": 0,
        "official_dev_count": 3466,
        "pairwise_disjoint": True,
        "selected_ai_exploration_count": TARGET_COUNT,
        "unexposed_unallocated_reserve_count": 3066,
        "union_equals_official_dev": True,
    }
    if pool.get("partition_check") != expected_partition_check:
        raise N300AnalysisError("pool partition_check is not the exact N300 partition")
    return {
        "schema_version": "question_exposure_ledger_v0_3",
        "status": "complete_through_cumulative_n300_v0_1",
        "dataset": "HybridQA",
        "source_split": "dev",
        "contract_freeze_commit": contract_freeze_commit,
        "historical_exposure": historical_exposure,
        "completion_bindings": {
            "predecessor_exposure_ledger_v0_2": _binding(prior_exposure_path),
            "cumulative_n300_analysis_plan": _binding(plan_path),
            "n300_pool_manifest": _binding(pool_manifest_path),
            "n300_producer_routing_manifest": _binding(routing_path),
            "cumulative_n300_records": _planned_artifact(
                cumulative_records_path,
                cumulative_records_payload,
                record_count=TARGET_COUNT,
            ),
        },
        "ai_question_structure_exploration": {
            "analysis_id": ANALYSIS_ID,
            "record_contract_run_id": frozen_n100.RUN_ID,
            "question_ids": question_ids,
            "question_ids_ordered_sha256": canonical_json_sha256(question_ids),
            "processed_count": TARGET_COUNT,
            "newly_processed_count": EXPANSION_COUNT,
            "pending_count": 0,
            "future_unseen_evaluation_allowed": False,
            "future_training_allowed": False,
            "corpus_role_allocated": False,
        },
        "unexposed_unallocated_reserve": {
            "count": 3066,
            "question_id_set_sha256": reserve_set_sha,
            "question_text_materialized": False,
            "role_allocated": False,
        },
        "partition_check": expected_partition_check,
        "evidence_boundary": {
            "human_evidence_count": 0,
            "gold_claimed": False,
            "semantic_correctness_claimed": False,
            "unseen_evaluation_exclusion_is_exposure_accounting_not_correctness": True,
        },
    }


def verify_contract_freeze(plan_path: Path, plan: dict[str, Any]) -> str:
    """Prove that the plan was committed before every planned model/output path."""

    relative_plan = _relative(plan_path)
    log_result = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", relative_plan],
        capture_output=True,
        text=True,
        check=False,
    )
    commit = log_result.stdout.strip()
    if log_result.returncode != 0 or len(commit) != 40:
        raise N300AnalysisError("N300 plan has no committed 40-hex freeze commit")
    ancestor = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", commit, "HEAD"],
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise N300AnalysisError("N300 plan freeze commit is not an ancestor of HEAD")
    committed_plan = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{relative_plan}"],
        capture_output=True,
        check=False,
    )
    if committed_plan.returncode != 0 or committed_plan.stdout != plan_path.read_bytes():
        raise N300AnalysisError(
            "current N300 plan bytes differ from the committed freeze-plan bytes"
        )

    planned = plan["planned_outputs"]
    planned_paths = [
        item["repository_relative_path"]
        for item in planned["new_model_parts"].values()
    ] + [
        item["repository_relative_path"]
        for item in planned["cumulative_analysis"].values()
    ]
    if len(planned_paths) != len(set(planned_paths)):
        raise N300AnalysisError("freeze plan contains duplicate planned paths")
    for relative in planned_paths:
        if (
            not isinstance(relative, str)
            or relative.startswith("/")
            or ".." in Path(relative).parts
            or ":" in relative
        ):
            raise N300AnalysisError(f"unsafe planned path in freeze contract: {relative!r}")
        existed = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{commit}:{relative}"],
            capture_output=True,
            check=False,
        )
        if existed.returncode == 0:
            raise N300AnalysisError(
                f"planned model/output path already existed at freeze commit: {relative}"
            )
        if existed.returncode not in {1, 128}:
            raise N300AnalysisError(
                f"could not audit planned path absence at freeze commit: {relative}"
            )
    return commit


def build_run_manifest(
    *,
    source_bindings: dict[str, Any],
    output_payloads: dict[str, tuple[Path, bytes]],
    contract_freeze_commit: str,
) -> dict[str, Any]:
    return {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "analysis_id": ANALYSIS_ID,
        "record_contract_run_id": frozen_n100.RUN_ID,
        "run_status": "complete",
        "evidence_class": frozen_n100.EVIDENCE_CLASS,
        "contract_freeze_commit": contract_freeze_commit,
        "cumulative_target": TARGET_COUNT,
        "prefix_record_count": PREFIX_COUNT,
        "expansion_record_count": EXPANSION_COUNT,
        "source_bindings": source_bindings,
        "outputs": {
            label: _planned_artifact(
                path,
                payload,
                record_count=(
                    TARGET_COUNT
                    if label in {"records", "checks", "derived_signatures"}
                    else None
                ),
            )
            for label, (path, payload) in sorted(output_payloads.items())
        },
        "n1000_decision_is_precommitted_operational_not_semantic": True,
        "human_evidence_count": 0,
        "gold_claimed": False,
        "tool_version": TOOL_VERSION,
    }


def _validate_output_paths(inputs: Iterable[Path], outputs: Iterable[Path]) -> None:
    input_paths = {path.resolve() for path in inputs}
    output_paths = [path.resolve() for path in outputs]
    if len(output_paths) != len(set(output_paths)):
        raise N300AnalysisError("all output paths must be distinct")
    overlap = input_paths & set(output_paths)
    if overlap:
        raise N300AnalysisError(f"outputs must not overwrite inputs: {sorted(map(str, overlap))}")


def _validate_planned_paths(
    plan: dict[str, Any],
    *,
    part_paths: list[Path],
    cumulative_outputs: dict[str, Path],
) -> dict[str, Any]:
    planned = plan.get("planned_outputs")
    if not isinstance(planned, dict) or set(planned) != {
        "new_model_parts",
        "cumulative_analysis",
    }:
        raise N300AnalysisError("plan planned_outputs has invalid top-level keys")
    planned_parts = planned["new_model_parts"]
    if not isinstance(planned_parts, dict):
        raise N300AnalysisError("plan new_model_parts must be an object")
    expected_part_paths: set[Path] = set()
    for partition in EXPECTED_NEW_PARTITIONS:
        item = planned_parts.get(partition)
        if (
            not isinstance(item, dict)
            or set(item) != {"repository_relative_path", "expected_record_count"}
            or item.get("expected_record_count") != 40
            or not isinstance(item.get("repository_relative_path"), str)
            or item["repository_relative_path"].startswith("/")
            or ".." in Path(item["repository_relative_path"]).parts
        ):
            raise N300AnalysisError(f"plan new_model_parts.{partition} is invalid")
        expected_part_paths.add((ROOT / item["repository_relative_path"]).resolve())
    if set(planned_parts) != set(EXPECTED_NEW_PARTITIONS):
        raise N300AnalysisError("plan new_model_parts has unexpected partitions")
    if {path.resolve() for path in part_paths} != expected_part_paths:
        raise N300AnalysisError("runtime --parts differ from plan planned_outputs")

    expected_output_keys = {
        "records",
        "checks",
        "derived_signatures",
        "metrics",
        "report",
        "run_manifest",
        "completion_exposure_ledger",
    }
    planned_cumulative = planned["cumulative_analysis"]
    if not isinstance(planned_cumulative, dict) or set(planned_cumulative) != expected_output_keys:
        raise N300AnalysisError("plan cumulative_analysis output keys are invalid")
    if set(cumulative_outputs) != expected_output_keys:
        raise N300AnalysisError("analyzer cumulative output map is incomplete")
    for label, runtime_path in cumulative_outputs.items():
        item = planned_cumulative[label]
        if (
            not isinstance(item, dict)
            or set(item) != {"repository_relative_path"}
            or not isinstance(item.get("repository_relative_path"), str)
            or item["repository_relative_path"].startswith("/")
            or ".." in Path(item["repository_relative_path"]).parts
            or (ROOT / item["repository_relative_path"]).resolve() != runtime_path.resolve()
        ):
            raise N300AnalysisError(f"runtime {label} output differs from the frozen plan")
    return planned_parts


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        input_paths = (
            args.plan,
            args.schema,
            args.prompt,
            args.views,
            args.routing,
            args.pool_manifest,
            args.prior_exposure,
            args.prefix_records,
            *args.parts,
            FROZEN_ANALYZER,
        )
        output_paths = (
            args.records_output,
            args.checks_output,
            args.signatures_output,
            args.metrics_output,
            args.report_output,
            args.run_manifest_output,
            args.exposure_output,
        )
        _validate_output_paths(input_paths, output_paths)
        plan, views, routing, _, pool = validate_contract(
            args.plan,
            args.schema,
            args.prompt,
            args.views,
            args.routing,
            args.pool_manifest,
            args.prior_exposure,
            args.prefix_records,
        )
        planned_parts = _validate_planned_paths(
            plan,
            part_paths=args.parts,
            cumulative_outputs={
                "records": args.records_output,
                "checks": args.checks_output,
                "derived_signatures": args.signatures_output,
                "metrics": args.metrics_output,
                "report": args.report_output,
                "run_manifest": args.run_manifest_output,
                "completion_exposure_ledger": args.exposure_output,
            },
        )
        contract_freeze_commit = verify_contract_freeze(args.plan, plan)
        new_records, part_bindings = merge_partition_parts(
            args.parts,
            routing,
            planned_parts,
        )
        records_payload, records, prefix_preservation = build_cumulative_records_payload(
            args.prefix_records,
            new_records,
        )
        if [record.get("question_id") for record in records] != plan["question_ids"]:
            raise N300AnalysisError("merged cumulative records do not match the planned order")
        checks, errors = validate_records(records, views, routing, args.schema)
        if errors:
            print(
                json.dumps(
                    {
                        "status": "fail",
                        "n1000_decision": PRECOMMITTED_N1000_DECISION[
                            "invalid_run_decision"
                        ],
                        "errors": errors,
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 1
        if args.validate_only:
            print(
                json.dumps(
                    {
                        "status": "pass",
                        "records": len(records),
                        "byte_exact_prefix": True,
                    },
                    sort_keys=True,
                )
            )
            return 0

        derived = derive_signatures(records)
        source_bindings = {
            "analysis_plan": _binding(args.plan),
            "record_schema": _binding(args.schema),
            "extraction_prompt": _binding(args.prompt),
            "question_only_views": _binding(args.views, record_count=TARGET_COUNT),
            "producer_routing": _binding(args.routing),
            "pool_manifest": _binding(args.pool_manifest),
            "prior_exposure_ledger_v0_2": _binding(args.prior_exposure),
            "frozen_n100_records": _binding(args.prefix_records, record_count=PREFIX_COUNT),
            "n300_model_parts": part_bindings,
            "cumulative_n300_records": _planned_artifact(
                args.records_output,
                records_payload,
                record_count=TARGET_COUNT,
            ),
            "frozen_n100_analyzer_and_normalizer": _binding(FROZEN_ANALYZER),
            "analysis_implementation": _binding(Path(__file__)),
        }
        metrics = build_metrics(
            records,
            derived,
            prefix_preservation=prefix_preservation,
            source_bindings=source_bindings,
        )
        payloads: dict[str, tuple[Path, bytes]] = {
            "records": (args.records_output, records_payload),
            "checks": (args.checks_output, jsonl_file_bytes(checks)),
            "derived_signatures": (
                args.signatures_output,
                jsonl_file_bytes(derived),
            ),
            "metrics": (args.metrics_output, json_file_bytes(metrics)),
            "report": (args.report_output, render_report(metrics).encode("utf-8")),
        }
        exposure = build_completion_exposure_ledger(
            question_ids=plan["question_ids"],
            pool=pool,
            prior_exposure_path=args.prior_exposure,
            plan_path=args.plan,
            pool_manifest_path=args.pool_manifest,
            routing_path=args.routing,
            cumulative_records_path=args.records_output,
            cumulative_records_payload=records_payload,
            contract_freeze_commit=contract_freeze_commit,
        )
        payloads["completion_exposure_ledger"] = (
            args.exposure_output,
            json_file_bytes(exposure),
        )
        run_manifest = build_run_manifest(
            source_bindings=source_bindings,
            output_payloads=payloads,
            contract_freeze_commit=contract_freeze_commit,
        )
        payloads["run_manifest"] = (
            args.run_manifest_output,
            json_file_bytes(run_manifest),
        )
        statuses = write_output_batch(payloads)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "records": len(records),
                    "prefix_byte_exact": True,
                    "families": {
                        kind: metrics["signature_levels"][kind]["cumulative_n300"][
                            "observed_family_count"
                        ]
                        for kind in frozen_n100.SIGNATURE_KINDS
                    },
                    "n1000_decision": metrics["n1000_precommitted_decision"]["decision"],
                    "outputs": statuses,
                },
                sort_keys=True,
            )
        )
        return 0
    except (N300AnalysisError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "n1000_decision": PRECOMMITTED_N1000_DECISION[
                        "invalid_run_decision"
                    ],
                    "error": str(exc),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
