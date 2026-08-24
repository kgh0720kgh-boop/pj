#!/usr/bin/env python3
"""Freeze and build the N=300 candidate-backbone library and coverage sample.

This tool consumes only committed question-only N=300 records, deterministic
signatures, metrics, and their manifests.  It never reads HybridQA tables,
linked documents, factual answers, traces, grounding, or execution outcomes.
The plan must be committed before any planned library output exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

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
import analyze_ai_question_structure_cumulative_n300 as n300


TOOL_VERSION = "candidate_backbone_library_builder_v0_1"
PLAN_SCHEMA_VERSION = "candidate_backbone_library_plan_v0_1"
FAMILY_SCHEMA_VERSION = "candidate_backbone_family_v0_1"
SELECTION_SCHEMA_VERSION = "representative_coverage_selection_v0_1"
CHECK_SCHEMA_VERSION = "candidate_backbone_library_check_v0_1"
RUN_MANIFEST_SCHEMA_VERSION = "candidate_backbone_library_run_manifest_v0_1"
LIBRARY_ID = "hybridqa_n300_contracted_candidate_backbone_library_v0_1"
SELECTION_ID = "hybridqa_n300_candidate_backbone_coverage_sample_v0_1"
PLAN_ID = "hybridqa_n300_candidate_backbone_library_plan_v0_1"
PLAN_STATUS = "contract_frozen_before_environment_inspection_and_library_outputs"
TARGET_RECORD_COUNT = 300
PREFIX_COUNT = 100
EXPECTED_FAMILY_COUNT = 30
EXPECTED_SAMPLE_COUNT = 71
SELECTION_SEED = "hybridqa-candidate-backbone-environment-realization-v0.1"
EXPECTED_DECISION = (
    "FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_"
    "REPRESENTATIVE_ENVIRONMENT_REALIZATION"
)

ROOT = Path(__file__).resolve().parents[2]
SCALE_BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
CONTRACTS = SCALE_BASE / "contracts"
OUTPUT_BASE = SCALE_BASE / "candidate_backbone_library_v0_1"
COMMON_RUNTIME = ROOT / "data_construction/tools/_common.py"
DEFAULT_PLAN = CONTRACTS / "candidate_backbone_library_plan_v0_1.json"
DEFAULT_FAMILY_SCHEMA = CONTRACTS / "candidate_backbone_family_schema_v0_1.json"
DEFAULT_SELECTION_SCHEMA = CONTRACTS / "representative_selection_schema_v0_1.json"
DEFAULT_OUTCOME_SCHEMA = CONTRACTS / "environment_realization_outcome_schema_v0_1.json"
DEFAULT_RECORD_SCHEMA = n300.DEFAULT_SCHEMA
DEFAULT_RECORDS = SCALE_BASE / "cumulative_n300_v0_1/records.jsonl"
DEFAULT_SIGNATURES = (
    SCALE_BASE / "cumulative_n300_v0_1/analysis/derived_signatures_v0_1.jsonl"
)
DEFAULT_METRICS = (
    SCALE_BASE
    / "cumulative_n300_v0_1/analysis/cumulative_n300_structural_saturation_metrics_v0_1.json"
)
DEFAULT_N300_RUN_MANIFEST = SCALE_BASE / "cumulative_n300_v0_1/run_manifest.json"
DEFAULT_EXPOSURE = ROOT / "data_construction/manifests/question_exposure_ledger_v0_3.json"
DEFAULT_FAMILIES_OUTPUT = OUTPUT_BASE / "candidate_backbone_families_v0_1.jsonl"
DEFAULT_SELECTION_OUTPUT = OUTPUT_BASE / "representative_selection_v0_1.json"
DEFAULT_CHECKS_OUTPUT = OUTPUT_BASE / "checks.jsonl"
DEFAULT_REPORT_OUTPUT = OUTPUT_BASE / "report_v0_1.md"
DEFAULT_RUN_MANIFEST_OUTPUT = OUTPUT_BASE / "run_manifest.json"

SELECTION_DIMENSIONS = (
    "fine_semantic_dag_signature",
    "topology_shape_signature",
    "task_signature",
    "source_slice",
    "producer_partition",
    "record_status",
    "alternative_graph_presence",
)

SELECTION_CONTRACT: dict[str, Any] = {
    "sample_kind": "deterministic_family_complete_frequency_rarity_coverage_stress_sample",
    "family_resolution": "contracted_semantic_dag",
    "all_observed_families_retained_in_library": True,
    "at_least_one_selected_question_per_family": True,
    "quota_formula": {
        "expression": "min(family_question_count, 1 + ceil(log2(family_question_count)))",
        "family_question_count_domain": "positive_integer",
        "quota_is_a_design_choice_not_a_statistical_law": True,
    },
    "within_family_selection": {
        "method": "greedy_equal_axis_marginal_coverage_then_seeded_hash",
        "feature_axes": list(SELECTION_DIMENSIONS),
        "marginal_score": "count_of_axes_whose_candidate_value_is_not_yet_covered_in_family",
        "maximize": True,
        "candidate_iteration_order_affects_result": False,
        "tie_break": (
            "ascending_sha256(seed + NUL + contracted_signature + NUL + question_id)"
        ),
        "seed": SELECTION_SEED,
    },
    "family_output_order": "descending_family_question_count_then_ascending_full_signature",
    "selection_output_order": "family_output_order_then_within_family_selection_order",
    "question_text_used_for_ranking": False,
    "environment_or_outcome_used_for_ranking": False,
    "prevalence_representative": False,
}

LIBRARY_CONTRACT: dict[str, Any] = {
    "family_identity": "full_contracted_semantic_dag_sha256",
    "expected_family_count": EXPECTED_FAMILY_COUNT,
    "post_hoc_semantic_family_merging_allowed": False,
    "same_role_contraction_establishes_semantic_equivalence": False,
    "member_partition": "all_300_question_ids_exactly_once",
    "canonical_graph_required": True,
    "frequency_slices": ["cumulative_n300", "n100_prefix", "new200_expansion"],
    "support_views": [
        "producer_partition_by_source_slice",
        "cumulative_ten_question_blocks",
        "new200_relative_ten_question_blocks",
    ],
    "crosswalk_resolutions": [
        "fine_semantic_dag",
        "topology_shape",
        "task",
    ],
    "uncontracted_role_and_transition_composition_is_separate_evidence": True,
    "candidate_status_is_not_gold_or_established": True,
}

EVIDENCE_BOUNDARY: dict[str, Any] = {
    "evidence_class": "ai_exploratory_non_human_non_gold",
    "human_evidence_count": 0,
    "semantic_correctness_evaluated": False,
    "environment_content_inspected_for_selection": False,
    "environment_noninspection_claim_basis": (
        "tool_input_allowlist_plus_procedural_research_boundary_not_global_authentication"
    ),
    "environment_noninspection_machine_authenticated": False,
    "grounding_evaluated": False,
    "execution_evaluated": False,
    "answer_recovery_evaluated": False,
    "gold_claimed": False,
    "modeling_ready_claimed": False,
}

SOURCE_SCOPE: dict[str, Any] = {
    "allowed_inputs": [
        "cumulative_n300_records",
        "derived_signatures",
        "n300_metrics",
        "n300_run_manifest",
        "completion_exposure_ledger",
    ],
    "question_text_present_in_bound_records_but_not_used_for_selection": True,
    "forbidden_inputs": [
        "table_identity_schema_rows_or_cells",
        "linked_document_identity_or_text",
        "factual_answer_or_gold_span",
        "weak_or_gold_trace",
        "operator_proposal_or_grounding",
        "historical_graph",
        "execution_or_answer_recovery_outcome",
    ],
    "environment_content_inspected_for_selection": False,
}

OUTCOME_REQUIRED_SIGNALS = (
    "backbone_adequacy",
    "environment_operator_realization",
    "grounding",
    "execution",
    "answer_recovery",
)

EXPECTED_TRIGGER_VALUES = {
    "cumulative_contracted_singleton_question_mass_above_0_05": False,
    "cumulative_OTHER_question_rate_above_0_05": False,
    "tail_50_sequential_contracted_novelty_above_0_10_with_at_least_2_new_families": False,
    "at_least_2_material_cross_partition_new_contracted_families": False,
}

EXPECTED_INDEPENDENCE_CONTRACT = {
    "all_five_signals_required_and_independently_scored": True,
    "one_signal_status_derived_from_another_signal": False,
    "execution_success_implies_backbone_adequacy": False,
    "execution_failure_implies_backbone_inadequacy": False,
    "answer_recovery_implies_prior_stage_success": False,
    "downstream_failure_overwrites_upstream_assessment": False,
}

PLAN_TOP_LEVEL_KEYS = {
    "schema_version",
    "plan_id",
    "status",
    "implementation_commit",
    "source_commit",
    "source_scope",
    "library_contract",
    "selection_contract",
    "outcome_separation_contract",
    "evidence_boundary",
    "source_artifacts",
    "contract_artifacts",
    "planned_outputs",
    "expected_result",
}

FREQUENCY_STRATA = (
    ("singleton_1", 1, 1),
    ("doubleton_2", 2, 2),
    ("low_recurrent_3_9", 3, 9),
    ("medium_recurrent_10_19", 10, 19),
    ("high_recurrent_20_99", 20, 99),
    ("dominant_100_plus", 100, None),
)


class CandidateLibraryError(ValueError):
    """Raised when the frozen candidate-library contract is violated."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-plan", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--family-schema", type=Path, default=DEFAULT_FAMILY_SCHEMA)
    parser.add_argument("--selection-schema", type=Path, default=DEFAULT_SELECTION_SCHEMA)
    parser.add_argument("--outcome-schema", type=Path, default=DEFAULT_OUTCOME_SCHEMA)
    parser.add_argument("--record-schema", type=Path, default=DEFAULT_RECORD_SCHEMA)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--signatures", type=Path, default=DEFAULT_SIGNATURES)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--n300-run-manifest", type=Path, default=DEFAULT_N300_RUN_MANIFEST)
    parser.add_argument("--exposure-ledger", type=Path, default=DEFAULT_EXPOSURE)
    parser.add_argument("--families-output", type=Path, default=DEFAULT_FAMILIES_OUTPUT)
    parser.add_argument("--selection-output", type=Path, default=DEFAULT_SELECTION_OUTPUT)
    parser.add_argument("--checks-output", type=Path, default=DEFAULT_CHECKS_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--run-manifest-output", type=Path, default=DEFAULT_RUN_MANIFEST_OUTPUT)
    return parser.parse_args(argv)


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise CandidateLibraryError(f"artifact is outside repository root: {path}") from exc


def _outcome_separation_contract(schema_path: Path) -> dict[str, Any]:
    return {
        "schema": _relative(schema_path),
        "required_independent_signals": list(OUTCOME_REQUIRED_SIGNALS),
        "execution_success_implies_backbone_correctness": False,
        "execution_failure_implies_backbone_incorrectness": False,
    }


def _require_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise CandidateLibraryError(f"{label} must be an existing regular non-symlink file: {path}")


def _binding(path: Path, *, record_count: int | None = None) -> dict[str, Any]:
    _require_file(path, "bound artifact")
    value: dict[str, Any] = {
        "repository_relative_path": _relative(path),
        "sha256": sha256_file(path),
    }
    if record_count is not None:
        value["record_count"] = record_count
    return value


def _schema_validator(schema_path: Path) -> Any:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        raise CandidateLibraryError("jsonschema is required") from exc
    _require_file(schema_path, "schema")
    schema = read_json(schema_path)
    validator_class = getattr(jsonschema, "Draft202012Validator", None)
    if validator_class is None:
        raise CandidateLibraryError("Draft 2020-12 validation is unavailable")
    validator_class.check_schema(schema)
    return validator_class(schema, format_checker=jsonschema.FormatChecker())


def _outcome_schema_validator(schema_path: Path) -> Any:
    validator = _schema_validator(schema_path)
    schema = read_json(schema_path)
    required = schema.get("required")
    if not isinstance(required, list) or not set(OUTCOME_REQUIRED_SIGNALS).issubset(required):
        raise CandidateLibraryError(
            "environment outcome schema does not require all five independent signals"
        )
    properties = (
        schema.get("$defs", {})
        .get("independence_contract", {})
        .get("properties", {})
    )
    observed = {
        key: properties.get(key, {}).get("const")
        for key in EXPECTED_INDEPENDENCE_CONTRACT
    }
    if observed != EXPECTED_INDEPENDENCE_CONTRACT:
        raise CandidateLibraryError(
            "environment outcome schema does not freeze the independence contract"
        )
    if (
        schema.get("properties", {}).get("assessment_scope", {}).get("const")
        != "selected_question_environment_instance_only"
        or schema.get("$defs", {})
        .get("evidence_boundary", {})
        .get("properties", {})
        .get("family_level_semantic_correctness_established", {})
        .get("const")
        is not False
        or "comparison_provenance"
        not in schema.get("$defs", {}).get("answer_recovery", {}).get("required", [])
        or any(
            not isinstance(schema.get("$defs", {}).get(signal, {}).get("allOf"), list)
            for signal in OUTCOME_REQUIRED_SIGNALS
        )
    ):
        raise CandidateLibraryError(
            "environment outcome schema omits scope, provenance, or signal consistency guards"
        )
    return validator


def _validation_errors(validator: Any, value: Any, label: str) -> list[str]:
    output: list[str] = []
    for error in sorted(
        validator.iter_errors(value),
        key=lambda item: [str(part) for part in item.absolute_path],
    ):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        output.append(f"{label}.{location}: {error.message}")
    return output


def evidence_tier(count: int) -> str:
    if count == 1:
        return "singleton"
    if count == 2:
        return "doubleton"
    if count >= 3:
        return "recurrent"
    raise CandidateLibraryError("family count must be positive")


def frequency_stratum(count: int) -> str:
    if count < 1:
        raise CandidateLibraryError("family count must be positive")
    for label, lower, upper in FREQUENCY_STRATA:
        if count >= lower and (upper is None or count <= upper):
            return label
    raise AssertionError("unreachable frequency stratum")


def representative_quota(count: int) -> int:
    if count < 1:
        raise CandidateLibraryError("family count must be positive")
    return min(count, 1 + math.ceil(math.log2(count)))


def _tie_rank(contracted_signature: str, question_id: str) -> str:
    payload = (
        SELECTION_SEED
        + "\0"
        + contracted_signature
        + "\0"
        + question_id
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _feature_values(item: dict[str, Any]) -> dict[str, str]:
    derived = item["derived"]
    record = item["record"]
    return {
        "fine_semantic_dag_signature": derived["signatures"]["fine_semantic_dag"],
        "topology_shape_signature": derived["signatures"]["topology_shape"],
        "task_signature": derived["signatures"]["task"],
        "source_slice": "n100_prefix" if item["position"] <= PREFIX_COUNT else "new200_expansion",
        "producer_partition": record["producer_partition"],
        "record_status": record["status"],
        "alternative_graph_presence": "present" if record["alternative_graphs"] else "absent",
    }


def select_family_members(
    contracted_signature: str,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    quota = representative_quota(len(items))
    covered: dict[str, set[str]] = {axis: set() for axis in SELECTION_DIMENSIONS}
    remaining = list(items)
    selected: list[dict[str, Any]] = []
    for within_order in range(1, quota + 1):
        candidates: list[tuple[int, str, str, dict[str, Any], dict[str, str], list[str]]] = []
        for item in remaining:
            values = _feature_values(item)
            newly = [axis for axis in SELECTION_DIMENSIONS if values[axis] not in covered[axis]]
            question_id = item["record"]["question_id"]
            candidates.append(
                (
                    -len(newly),
                    _tie_rank(contracted_signature, question_id),
                    question_id,
                    item,
                    values,
                    newly,
                )
            )
        _, tie_rank, _, chosen, values, newly = min(candidates, key=lambda value: value[:3])
        remaining.remove(chosen)
        for axis in SELECTION_DIMENSIONS:
            covered[axis].add(values[axis])
        selected.append(
            {
                "item": chosen,
                "within_family_selection_order": within_order,
                "marginal_new_axis_value_count": len(newly),
                "newly_covered_axes": newly,
                "feature_values": values,
                "tie_break_sha256": tie_rank,
            }
        )
    return selected


def _counter_dict(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _block_counts(numbers: Iterable[int]) -> list[dict[str, int]]:
    return [
        {"block_number": block, "question_count": count}
        for block, count in sorted(Counter(numbers).items())
    ]


def _canonical_transition_counts(graph: dict[str, Any]) -> tuple[dict[str, int], dict[str, int]]:
    labels = graph["labels"]
    role_counts = _counter_dict(labels)
    transitions = _counter_dict(
        f"{labels[dependency]}->{labels[dependent]}"
        for dependency, dependent in graph["edges"]
    )
    return role_counts, transitions


def _uncontracted_composition(items: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, int]]:
    roles: Counter[str] = Counter()
    transitions: Counter[str] = Counter()
    for item in items:
        graph = item["record"]["primary_graph"]
        labels = {node["node_id"]: node["role"] for node in graph["nodes"]}
        roles.update(labels.values())
        for node in graph["nodes"]:
            for dependency in node["depends_on"]:
                transitions[f"{labels[dependency]}->{node['role']}"] += 1
    return dict(sorted(roles.items())), dict(sorted(transitions.items()))


def _crosswalk(items: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    canonical: dict[str, Any] = {}
    for item in items:
        signature = item["derived"]["signatures"][kind]
        grouped[signature].append(item)
        observed = item["derived"]["canonical"][kind]
        if signature in canonical and canonical[signature] != observed:
            raise CandidateLibraryError(f"canonical payload differs within {kind} signature {signature}")
        canonical[signature] = observed
    output: list[dict[str, Any]] = []
    for signature, members in sorted(grouped.items(), key=lambda value: (-len(value[1]), value[0])):
        output.append(
            {
                "signature_sha256": signature,
                "canonical": canonical[signature],
                "question_count": len(members),
                "question_ids": [item["record"]["question_id"] for item in members],
            }
        )
    return output


def _validate_n300_decision(decision: Any) -> None:
    if (
        not isinstance(decision, dict)
        or decision.get("decision") != EXPECTED_DECISION
        or decision.get("decision_rule_status")
        != "precommitted_before_positions_101_300_model_outputs"
        or decision.get("decision_resolution") != "contracted_semantic_dag_only"
        or decision.get("trigger_composition") != "ANY"
        or decision.get("trigger_values") != EXPECTED_TRIGGER_VALUES
        or decision.get("thresholds_are_design_choices_not_universal_statistical_laws")
        is not True
        or decision.get("decision_is_operational_not_semantic_correctness") is not True
    ):
        raise CandidateLibraryError(
            "N300 metrics do not select the exact frozen candidate-library branch"
        )


def _validate_exposure_ledger(exposure: Any, record_ids: list[str]) -> None:
    candidate_exploration = (
        exposure.get("ai_question_structure_exploration", {})
        if isinstance(exposure, dict)
        else {}
    )
    exploration = candidate_exploration if isinstance(candidate_exploration, dict) else {}
    if (
        not isinstance(exposure, dict)
        or exposure.get("schema_version") != "question_exposure_ledger_v0_3"
        or exposure.get("status") != "complete_through_cumulative_n300_v0_1"
        or exploration.get("analysis_id")
        != "ai_question_structure_scale_v0_1_cumulative_n300_analysis_v0_1"
        or exploration.get("processed_count") != TARGET_RECORD_COUNT
        or exploration.get("newly_processed_count") != TARGET_RECORD_COUNT - PREFIX_COUNT
        or exploration.get("pending_count") != 0
        or exploration.get("question_ids") != record_ids
        or exploration.get("question_ids_ordered_sha256")
        != canonical_json_sha256(record_ids)
        or exploration.get("future_training_allowed") is not False
        or exploration.get("future_unseen_evaluation_allowed") is not False
    ):
        raise CandidateLibraryError(
            "completion exposure ledger is not exact and complete through N300"
        )


def load_source_bundle(
    records_path: Path,
    signatures_path: Path,
    metrics_path: Path,
    n300_run_manifest_path: Path,
    exposure_path: Path,
    record_schema_path: Path = DEFAULT_RECORD_SCHEMA,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    for path, label in (
        (records_path, "N300 records"),
        (signatures_path, "N300 derived signatures"),
        (metrics_path, "N300 metrics"),
        (n300_run_manifest_path, "N300 run manifest"),
        (exposure_path, "N300 completion exposure ledger"),
        (record_schema_path, "frozen question-only record schema"),
    ):
        _require_file(path, label)
    records = list(iter_json_records(records_path))
    derived = list(iter_json_records(signatures_path))
    metrics = read_json(metrics_path)
    run_manifest = read_json(n300_run_manifest_path)
    exposure = read_json(exposure_path)
    if not all(isinstance(value, dict) for value in (metrics, run_manifest, exposure)):
        raise CandidateLibraryError("metrics, run manifest, and exposure ledger must be objects")
    if len(records) != TARGET_RECORD_COUNT or len(derived) != TARGET_RECORD_COUNT:
        raise CandidateLibraryError("candidate library requires exactly 300 records and signatures")
    record_ids = [record.get("question_id") for record in records]
    derived_ids = [item.get("question_id") for item in derived]
    if record_ids != derived_ids or len(set(record_ids)) != TARGET_RECORD_COUNT:
        raise CandidateLibraryError("records/signatures question IDs are not aligned and unique")
    record_validator = _schema_validator(record_schema_path)
    record_errors = [
        error
        for index, record in enumerate(records)
        for error in _validation_errors(record_validator, record, f"record[{index}]")
    ]
    if record_errors:
        raise CandidateLibraryError(
            "N300 records violate the frozen question-only schema: "
            + " | ".join(record_errors[:20])
        )
    recomputed = n300.derive_signatures(records)
    if recomputed != derived:
        raise CandidateLibraryError("derived signatures differ from the frozen normalizer reconstruction")
    if not all(
        item.get("representable") is True
        and all(isinstance(item["signatures"].get(kind), str) for kind in n300.frozen_n100.SIGNATURE_KINDS)
        for item in derived
    ):
        raise CandidateLibraryError("all 300 records must be representable at all four signature levels")
    validation = metrics.get("validation")
    if not isinstance(validation, dict):
        raise CandidateLibraryError("N300 metrics validation block is invalid")
    if (
        metrics.get("schema_version")
        != "ai_question_structure_cumulative_n300_structural_saturation_metrics_v0_1"
        or metrics.get("analysis_id")
        != "ai_question_structure_scale_v0_1_cumulative_n300_analysis_v0_1"
        or metrics.get("cumulative_target") != TARGET_RECORD_COUNT
        or metrics.get("prefix_record_count") != PREFIX_COUNT
        or metrics.get("expansion_record_count") != TARGET_RECORD_COUNT - PREFIX_COUNT
        or metrics.get("record_contract_run_id") != n300.frozen_n100.RUN_ID
        or validation.get("valid_record_count") != TARGET_RECORD_COUNT
        or validation.get("invalid_record_count") != 0
        or validation.get("human_evidence_count") != 0
        or validation.get("gold_claimed") is not False
        or validation.get("semantic_correctness_evaluated") is not False
        or validation.get("grounding_or_execution_evaluated") is not False
    ):
        raise CandidateLibraryError("N300 metrics identity or validation fields are invalid")
    _validate_n300_decision(metrics.get("n1000_precommitted_decision"))
    signature_levels = metrics.get("signature_levels")
    contracted_metrics = (
        signature_levels.get("contracted_semantic_dag", {})
        if isinstance(signature_levels, dict)
        else {}
    )
    family_metrics = (
        contracted_metrics.get("cumulative_n300", {})
        if isinstance(contracted_metrics, dict)
        else {}
    )
    if not isinstance(family_metrics, dict):
        family_metrics = {}
    if (
        family_metrics.get("question_count") != TARGET_RECORD_COUNT
        or family_metrics.get("representable_count") != TARGET_RECORD_COUNT
        or family_metrics.get("observed_family_count") != EXPECTED_FAMILY_COUNT
    ):
        raise CandidateLibraryError("N300 metrics do not contain the expected 30 contracted families")
    if (
        run_manifest.get("schema_version")
        != "ai_question_structure_cumulative_n300_run_manifest_v0_1"
        or run_manifest.get("analysis_id")
        != "ai_question_structure_scale_v0_1_cumulative_n300_analysis_v0_1"
        or run_manifest.get("run_status") != "complete"
        or run_manifest.get("cumulative_target") != TARGET_RECORD_COUNT
        or run_manifest.get("prefix_record_count") != PREFIX_COUNT
        or run_manifest.get("expansion_record_count") != TARGET_RECORD_COUNT - PREFIX_COUNT
        or run_manifest.get("record_contract_run_id") != n300.frozen_n100.RUN_ID
        or run_manifest.get("human_evidence_count") != 0
        or run_manifest.get("gold_claimed") is not False
    ):
        raise CandidateLibraryError("N300 run manifest identity or completion fields are invalid")
    outputs = run_manifest.get("outputs", {})
    if not isinstance(outputs, dict):
        raise CandidateLibraryError("N300 run manifest outputs block is invalid")
    expected_output_bindings = {
        "records": records_path,
        "derived_signatures": signatures_path,
        "metrics": metrics_path,
        "completion_exposure_ledger": exposure_path,
    }
    for label, path in expected_output_bindings.items():
        item = outputs.get(label, {})
        if (
            item.get("repository_relative_path") != _relative(path)
            or item.get("sha256") != sha256_file(path)
            or (
                label in {"records", "derived_signatures"}
                and item.get("record_count") != TARGET_RECORD_COUNT
            )
        ):
            raise CandidateLibraryError(f"N300 run manifest does not bind live {label}")
    _validate_exposure_ledger(exposure, record_ids)
    return records, derived, metrics


def build_library_and_selection(
    records: list[dict[str, Any]],
    derived: list[dict[str, Any]],
    *,
    source_bindings: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for position, (record, signature_item) in enumerate(zip(records, derived), start=1):
        signature = signature_item["signatures"]["contracted_semantic_dag"]
        groups[signature].append(
            {"position": position, "record": record, "derived": signature_item}
        )
    ordered_groups = sorted(groups.items(), key=lambda value: (-len(value[1]), value[0]))
    if len(ordered_groups) != EXPECTED_FAMILY_COUNT:
        raise CandidateLibraryError(f"expected 30 contracted families, observed {len(ordered_groups)}")

    families: list[dict[str, Any]] = []
    selections: list[dict[str, Any]] = []
    strata_family_counts: Counter[str] = Counter()
    strata_member_counts: Counter[str] = Counter()
    strata_selection_counts: Counter[str] = Counter()
    for rank, (signature, items) in enumerate(ordered_groups, start=1):
        count = len(items)
        tier = evidence_tier(count)
        stratum = frequency_stratum(count)
        strata_family_counts[stratum] += 1
        strata_member_counts[stratum] += count
        canonical_graph = items[0]["derived"]["canonical"]["contracted_semantic_dag"]
        if canonical_json_sha256(canonical_graph) != signature:
            raise CandidateLibraryError(f"contracted canonical hash mismatch for {signature}")
        if any(
            item["derived"]["canonical"]["contracted_semantic_dag"] != canonical_graph
            for item in items
        ):
            raise CandidateLibraryError(f"contracted canonical payload varies within {signature}")
        chosen = select_family_members(signature, items)
        selected_ids = [value["item"]["record"]["question_id"] for value in chosen]
        strata_selection_counts[stratum] += len(chosen)
        n100 = [item for item in items if item["position"] <= PREFIX_COUNT]
        new200 = [item for item in items if item["position"] > PREFIX_COUNT]
        status_counts = _counter_dict(item["record"]["status"] for item in items)
        uncertainty_ids = [
            item["record"]["question_id"]
            for item in items
            if item["record"]["uncertainty"]["present"]
        ]
        alternative_ids = [
            item["record"]["question_id"]
            for item in items
            if item["record"]["alternative_graphs"]
        ]
        uncertainty_tags = _counter_dict(
            tag
            for item in items
            for tag in item["record"]["uncertainty"]["tags"]
        )
        cumulative_blocks = [1 + (item["position"] - 1) // 10 for item in items]
        new200_blocks = [1 + (item["position"] - PREFIX_COUNT - 1) // 10 for item in new200]
        partition_all = _counter_dict(item["record"]["producer_partition"] for item in items)
        partition_n100 = _counter_dict(item["record"]["producer_partition"] for item in n100)
        partition_new = _counter_dict(item["record"]["producer_partition"] for item in new200)
        contracted_roles, contracted_transitions = _canonical_transition_counts(canonical_graph)
        raw_roles, raw_transitions = _uncontracted_composition(items)
        member_rows: list[dict[str, Any]] = []
        for item in items:
            position = item["position"]
            record = item["record"]
            signature_item = item["derived"]
            member_rows.append(
                {
                    "question_id": record["question_id"],
                    "question_view_sha256": record["question_view_sha256"],
                    "committed_position": position,
                    "source_slice": "n100_prefix" if position <= PREFIX_COUNT else "new200_expansion",
                    "producer_partition": record["producer_partition"],
                    "cumulative_ten_question_block_number": 1 + (position - 1) // 10,
                    "new200_relative_ten_question_block_number": (
                        None if position <= PREFIX_COUNT else 1 + (position - PREFIX_COUNT - 1) // 10
                    ),
                    "status": record["status"],
                    "uncertainty_present": record["uncertainty"]["present"],
                    "uncertainty_tags": record["uncertainty"]["tags"],
                    "has_alternative_graph": bool(record["alternative_graphs"]),
                    "signatures": {
                        kind: signature_item["signatures"][kind]
                        for kind in n300.frozen_n100.SIGNATURE_KINDS
                    },
                }
            )
        material = (
            not n100
            and len(new200) >= 3
            and len(partition_new) >= 2
            and len(set(new200_blocks)) >= 2
        )
        family_id = f"cbf_v0_1:{signature}"
        family_record = {
            "schema_version": FAMILY_SCHEMA_VERSION,
            "library_id": LIBRARY_ID,
            "evidence_class": "ai_exploratory_non_human_non_gold",
            "candidate_status": "candidate_non_gold_not_established",
            "family_id": family_id,
            "contracted_signature_sha256": signature,
            "frequency_rank": rank,
            "evidence_tier": tier,
            "frequency_stratum": stratum,
            "frequency": {
                "cumulative_n300_question_count": count,
                "n100_prefix_question_count": len(n100),
                "new200_expansion_question_count": len(new200),
                "cumulative_question_rate": count / TARGET_RECORD_COUNT,
                "status_counts": status_counts,
                "uncertainty_present_question_count": len(uncertainty_ids),
                "alternative_graph_question_count": len(alternative_ids),
            },
            "canonical_contracted_graph": canonical_graph,
            "members": member_rows,
            "support": {
                "producer_partition_counts": partition_all,
                "n100_prefix_producer_partition_counts": partition_n100,
                "new200_expansion_producer_partition_counts": partition_new,
                "producer_partition_support_count": len(partition_all),
                "cumulative_ten_question_block_counts": _block_counts(cumulative_blocks),
                "cumulative_ten_question_block_support_count": len(set(cumulative_blocks)),
                "new200_relative_ten_question_block_counts": _block_counts(new200_blocks),
                "new200_relative_ten_question_block_support_count": len(set(new200_blocks)),
            },
            "crosswalks": {
                kind: _crosswalk(items, kind)
                for kind in ("fine_semantic_dag", "topology_shape", "task")
            },
            "observed_composition": {
                "edge_direction": "dependency_role_to_dependent_role",
                "canonical_contracted_node_count": len(canonical_graph["labels"]),
                "canonical_contracted_edge_count": len(canonical_graph["edges"]),
                "canonical_contracted_role_counts": contracted_roles,
                "canonical_contracted_directed_role_transition_counts": contracted_transitions,
                "uncontracted_member_role_node_counts": raw_roles,
                "uncontracted_member_directed_dependency_role_transition_counts": raw_transitions,
                "uncontracted_composition_used_to_define_family": False,
            },
            "evidence": {
                "n100_seen": bool(n100),
                "new200_seen": bool(new200),
                "seen_in_both_source_slices": bool(n100 and new200),
                "uncertain_question_ids": uncertainty_ids,
                "uncertainty_tag_counts": uncertainty_tags,
                "all_members_uncertain": len(uncertainty_ids) == count,
                "alternative_graph_question_ids": alternative_ids,
                "new200_material_cross_partition_rule_eligible": not n100,
                "qualifies_n100_unseen_material_cross_partition_recurrence": material,
            },
            "representative_selection": {
                "selection_id": SELECTION_ID,
                "quota": representative_quota(count),
                "method": SELECTION_CONTRACT["within_family_selection"]["method"],
                "question_ids": selected_ids,
            },
            "caveats": {
                "same_role_contraction_establishes_semantic_equivalence": False,
                "producer_partitions_are_independent_reviewers": False,
                "complete_status_establishes_semantic_correctness": False,
                "post_hoc_semantic_family_merge_performed": False,
                "family_is_gold": False,
            },
        }
        families.append(family_record)
        for value in chosen:
            item = value["item"]
            record = item["record"]
            selections.append(
                {
                    "selection_index": len(selections) + 1,
                    "family_id": family_id,
                    "contracted_signature_sha256": signature,
                    "family_frequency_rank": rank,
                    "family_question_count": count,
                    "family_evidence_tier": tier,
                    "family_frequency_stratum": stratum,
                    "family_quota": representative_quota(count),
                    "within_family_selection_order": value["within_family_selection_order"],
                    "question_id": record["question_id"],
                    "question_view_sha256": record["question_view_sha256"],
                    "committed_position": item["position"],
                    "marginal_new_axis_value_count": value["marginal_new_axis_value_count"],
                    "newly_covered_axes": value["newly_covered_axes"],
                    "feature_values": value["feature_values"],
                    "tie_break_sha256": value["tie_break_sha256"],
                }
            )

    selected_ids = [item["question_id"] for item in selections]
    if len(selections) != EXPECTED_SAMPLE_COUNT or len(set(selected_ids)) != EXPECTED_SAMPLE_COUNT:
        raise CandidateLibraryError(
            f"frozen quota must select 71 unique questions, observed {len(selections)}"
        )
    if len({item["family_id"] for item in selections}) != EXPECTED_FAMILY_COUNT:
        raise CandidateLibraryError("representative sample does not cover all 30 families")
    strata_summary = [
        {
            "frequency_stratum": label,
            "minimum_family_question_count": lower,
            "maximum_family_question_count": upper,
            "family_count": strata_family_counts[label],
            "source_member_question_count": strata_member_counts[label],
            "selected_question_count": strata_selection_counts[label],
        }
        for label, lower, upper in FREQUENCY_STRATA
    ]
    selection = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "selection_id": SELECTION_ID,
        "status": "selected_and_hash_bound_before_environment_inspection",
        "selection_purpose": "candidate_backbone_environment_realization_coverage_stress_test",
        "selection_contract": SELECTION_CONTRACT,
        "source_bindings": source_bindings,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "family_count": EXPECTED_FAMILY_COUNT,
        "selected_family_count": EXPECTED_FAMILY_COUNT,
        "selected_question_count": len(selections),
        "selected_question_ids": selected_ids,
        "selected_question_ids_ordered_sha256": canonical_json_sha256(selected_ids),
        "selected_question_ids_set_sha256": canonical_string_set_sha256(selected_ids),
        "strata_summary": strata_summary,
        "selections": selections,
        "limitations": {
            "probability_sample": False,
            "prevalence_estimation_supported": False,
            "rare_families_deliberately_overrepresented": True,
            "feature_axes_are_correlated": True,
            "n100_new200_and_producer_context_are_partly_confounded": True,
            "producer_partitions_are_independent_reviewers": False,
            "status_and_alternative_presence_are_ai_generated_diagnostics": True,
        },
    }
    return families, selection


def _source_bindings(
    records_path: Path,
    signatures_path: Path,
    metrics_path: Path,
    n300_run_manifest_path: Path,
    exposure_path: Path,
) -> dict[str, Any]:
    return {
        "cumulative_n300_records": _binding(records_path, record_count=TARGET_RECORD_COUNT),
        "derived_signatures": _binding(signatures_path, record_count=TARGET_RECORD_COUNT),
        "n300_metrics": _binding(metrics_path),
        "n300_run_manifest": _binding(n300_run_manifest_path),
        "completion_exposure_ledger": _binding(exposure_path),
    }


def _contract_bindings(
    family_schema_path: Path,
    selection_schema_path: Path,
    outcome_schema_path: Path,
    record_schema_path: Path,
) -> dict[str, Any]:
    return {
        "builder": _binding(Path(__file__)),
        "common_runtime": _binding(COMMON_RUNTIME),
        "family_schema": _binding(family_schema_path),
        "selection_schema": _binding(selection_schema_path),
        "environment_outcome_schema": _binding(outcome_schema_path),
        "source_record_schema": _binding(record_schema_path),
        "n300_analyzer": _binding(Path(n300.__file__)),
        "frozen_n100_normalizer": _binding(n300.FROZEN_ANALYZER),
    }


def _output_paths(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "families": args.families_output,
        "representative_selection": args.selection_output,
        "checks": args.checks_output,
        "report": args.report_output,
        "run_manifest": args.run_manifest_output,
    }


def _validate_paths(args: argparse.Namespace) -> None:
    inputs = {
        "plan": args.plan,
        "family_schema": args.family_schema,
        "selection_schema": args.selection_schema,
        "outcome_schema": args.outcome_schema,
        "record_schema": args.record_schema,
        "records": args.records,
        "signatures": args.signatures,
        "metrics": args.metrics,
        "n300_run_manifest": args.n300_run_manifest,
        "exposure_ledger": args.exposure_ledger,
    }
    outputs = _output_paths(args)
    errors = output_path_collision_errors(inputs, outputs)
    errors.extend(historical_output_collision_errors(outputs, ROOT))
    for label, path in inputs.items():
        try:
            _relative(path)
        except CandidateLibraryError as exc:
            errors.append(f"input {label}: {exc}")
    for label, path in outputs.items():
        try:
            _relative(path)
        except CandidateLibraryError as exc:
            errors.append(f"output {label}: {exc}")
    if errors:
        raise CandidateLibraryError("; ".join(errors))


def build_freeze_plan(args: argparse.Namespace) -> dict[str, Any]:
    _validate_paths(args)
    plan_errors = output_path_collision_errors(
        {
            "family_schema": args.family_schema,
            "selection_schema": args.selection_schema,
            "outcome_schema": args.outcome_schema,
            "record_schema": args.record_schema,
            "records": args.records,
            "signatures": args.signatures,
            "metrics": args.metrics,
            "n300_run_manifest": args.n300_run_manifest,
            "exposure_ledger": args.exposure_ledger,
        },
        {"plan": args.plan, **_output_paths(args)},
    )
    plan_errors.extend(historical_output_collision_errors({"plan": args.plan}, ROOT))
    try:
        _relative(args.plan)
    except CandidateLibraryError as exc:
        plan_errors.append(f"plan output: {exc}")
    if plan_errors:
        raise CandidateLibraryError("; ".join(plan_errors))
    for path in _output_paths(args).values():
        if path.is_symlink() or path.exists():
            raise CandidateLibraryError(f"planned output already exists before plan freeze: {_relative(path)}")
    family_validator = _schema_validator(args.family_schema)
    selection_validator = _schema_validator(args.selection_schema)
    _outcome_schema_validator(args.outcome_schema)
    records, derived, _ = load_source_bundle(
        args.records,
        args.signatures,
        args.metrics,
        args.n300_run_manifest,
        args.exposure_ledger,
        args.record_schema,
    )
    source_bindings = _source_bindings(
        args.records,
        args.signatures,
        args.metrics,
        args.n300_run_manifest,
        args.exposure_ledger,
    )
    families, selection = build_library_and_selection(
        records, derived, source_bindings=source_bindings
    )
    errors = [
        error
        for index, family in enumerate(families)
        for error in _validation_errors(family_validator, family, f"family[{index}]")
    ]
    errors.extend(_validation_errors(selection_validator, selection, "selection"))
    if errors:
        raise CandidateLibraryError("schema validation failed: " + " | ".join(errors[:20]))
    contract_bindings = _contract_bindings(
        args.family_schema,
        args.selection_schema,
        args.outcome_schema,
        args.record_schema,
    )
    implementation_commit = git_tracked_commit_identity(
        ROOT,
        [
            Path(__file__),
            COMMON_RUNTIME,
            args.family_schema,
            args.selection_schema,
            args.outcome_schema,
            args.record_schema,
            Path(n300.__file__),
            n300.FROZEN_ANALYZER,
        ],
    )
    source_commit = git_tracked_commit_identity(
        ROOT,
        [
            args.records,
            args.signatures,
            args.metrics,
            args.n300_run_manifest,
            args.exposure_ledger,
        ],
    )
    family_signatures = [item["contracted_signature_sha256"] for item in families]
    plan = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "status": PLAN_STATUS,
        "implementation_commit": implementation_commit,
        "source_commit": source_commit,
        "source_scope": SOURCE_SCOPE,
        "library_contract": LIBRARY_CONTRACT,
        "selection_contract": SELECTION_CONTRACT,
        "outcome_separation_contract": _outcome_separation_contract(args.outcome_schema),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_artifacts": source_bindings,
        "contract_artifacts": contract_bindings,
        "planned_outputs": {
            label: {"repository_relative_path": _relative(path)}
            for label, path in _output_paths(args).items()
        },
        "expected_result": {
            "source_record_count": TARGET_RECORD_COUNT,
            "candidate_family_count": EXPECTED_FAMILY_COUNT,
            "member_question_count": TARGET_RECORD_COUNT,
            "evidence_tier_family_counts": _counter_dict(
                family["evidence_tier"] for family in families
            ),
            "selected_question_count": EXPECTED_SAMPLE_COUNT,
            "selected_family_count": EXPECTED_FAMILY_COUNT,
            "family_signatures_ordered_sha256": canonical_json_sha256(family_signatures),
            "family_signatures_set_sha256": canonical_string_set_sha256(family_signatures),
            "selected_question_ids_ordered_sha256": selection[
                "selected_question_ids_ordered_sha256"
            ],
            "selected_question_ids_set_sha256": selection[
                "selected_question_ids_set_sha256"
            ],
            "strata_summary": selection["strata_summary"],
        },
    }
    return plan


def _verify_commit_artifacts(commit: str, bindings: dict[str, Any], label: str) -> None:
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise CandidateLibraryError(f"{label} is not a full lowercase Git commit")
    ancestor = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", commit, "HEAD"],
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise CandidateLibraryError(f"{label} is not an ancestor of HEAD")
    for item in bindings.values():
        relative = item["repository_relative_path"]
        shown = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{commit}:{relative}"],
            capture_output=True,
            check=False,
        )
        if shown.returncode != 0 or sha256_bytes(shown.stdout) != item["sha256"]:
            raise CandidateLibraryError(f"{label} does not contain bound artifact bytes: {relative}")


def validate_plan(args: argparse.Namespace) -> dict[str, Any]:
    _validate_paths(args)
    _require_file(args.plan, "candidate library freeze plan")
    plan = read_json(args.plan)
    if set(plan) != PLAN_TOP_LEVEL_KEYS:
        raise CandidateLibraryError("plan top-level fields differ from the frozen contract")
    expected_identity = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "status": PLAN_STATUS,
        "source_scope": SOURCE_SCOPE,
        "library_contract": LIBRARY_CONTRACT,
        "selection_contract": SELECTION_CONTRACT,
        "outcome_separation_contract": _outcome_separation_contract(args.outcome_schema),
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }
    for key, expected in expected_identity.items():
        if plan.get(key) != expected:
            raise CandidateLibraryError(f"plan {key} differs from the frozen contract")
    expected_sources = _source_bindings(
        args.records,
        args.signatures,
        args.metrics,
        args.n300_run_manifest,
        args.exposure_ledger,
    )
    expected_contracts = _contract_bindings(
        args.family_schema,
        args.selection_schema,
        args.outcome_schema,
        args.record_schema,
    )
    if plan.get("source_artifacts") != expected_sources:
        raise CandidateLibraryError("plan source artifact bindings differ from live inputs")
    if plan.get("contract_artifacts") != expected_contracts:
        raise CandidateLibraryError("plan contract artifact bindings differ from live implementation")
    expected_outputs = {
        label: {"repository_relative_path": _relative(path)}
        for label, path in _output_paths(args).items()
    }
    if plan.get("planned_outputs") != expected_outputs:
        raise CandidateLibraryError("runtime output paths differ from the frozen plan")
    _verify_commit_artifacts(plan.get("implementation_commit", ""), expected_contracts, "implementation_commit")
    _verify_commit_artifacts(plan.get("source_commit", ""), expected_sources, "source_commit")
    _schema_validator(args.family_schema)
    _schema_validator(args.selection_schema)
    _outcome_schema_validator(args.outcome_schema)
    _schema_validator(args.record_schema)
    return plan


def verify_plan_freeze(plan_path: Path, plan: dict[str, Any]) -> str:
    relative_plan = _relative(plan_path)
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", relative_plan],
        capture_output=True,
        text=True,
        check=False,
    )
    commit = result.stdout.strip()
    if result.returncode != 0 or len(commit) != 40:
        raise CandidateLibraryError("candidate library plan has no committed freeze commit")
    ancestor = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", commit, "HEAD"],
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise CandidateLibraryError("candidate library plan freeze commit is not an ancestor of HEAD")
    shown = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{relative_plan}"],
        capture_output=True,
        check=False,
    )
    if shown.returncode != 0 or shown.stdout != plan_path.read_bytes():
        raise CandidateLibraryError("current plan bytes differ from committed freeze-plan bytes")
    for label in ("implementation_commit", "source_commit"):
        bound_commit = plan[label]
        precedes_freeze = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "merge-base",
                "--is-ancestor",
                bound_commit,
                commit,
            ],
            capture_output=True,
            check=False,
        )
        if precedes_freeze.returncode != 0:
            raise CandidateLibraryError(
                f"{label} is not an ancestor of the plan freeze commit"
            )
    planned = [item["repository_relative_path"] for item in plan["planned_outputs"].values()]
    if len(planned) != len(set(planned)):
        raise CandidateLibraryError("freeze plan contains duplicate output paths")
    for relative in planned:
        if relative.startswith("/") or ".." in Path(relative).parts or ":" in relative:
            raise CandidateLibraryError(f"unsafe planned output path: {relative!r}")
        existed = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{commit}:{relative}"],
            capture_output=True,
            check=False,
        )
        if existed.returncode == 0:
            raise CandidateLibraryError(
                f"planned output existed at candidate-library freeze commit: {relative}"
            )
        if existed.returncode not in {1, 128}:
            raise CandidateLibraryError(f"could not audit planned output absence: {relative}")
    return commit


def _checks(families: list[dict[str, Any]], selection: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = [
        {
            "schema_version": CHECK_SCHEMA_VERSION,
            "check_type": "bundle",
            "family_id": None,
            "question_id": None,
            "status": "pass",
            "errors": [],
        }
    ]
    output.extend(
        {
            "schema_version": CHECK_SCHEMA_VERSION,
            "check_type": "family",
            "family_id": family["family_id"],
            "question_id": None,
            "status": "pass",
            "errors": [],
        }
        for family in families
    )
    output.extend(
        {
            "schema_version": CHECK_SCHEMA_VERSION,
            "check_type": "representative_selection",
            "family_id": item["family_id"],
            "question_id": item["question_id"],
            "status": "pass",
            "errors": [],
        }
        for item in selection["selections"]
    )
    return output


def _report(families: list[dict[str, Any]], selection: dict[str, Any]) -> str:
    tier_counts = Counter(family["evidence_tier"] for family in families)
    lines = [
        "# Candidate backbone library v0.1",
        "",
        "Status: `candidate_non_gold_not_established`.",
        "",
        "## Materialized scope",
        "",
        f"- Contracted candidate families: {len(families)}",
        f"- Exhaustively assigned N=300 members: {sum(len(family['members']) for family in families)}",
        f"- Evidence tiers: recurrent={tier_counts['recurrent']}, doubleton={tier_counts['doubleton']}, singleton={tier_counts['singleton']}",
        f"- Pre-environment coverage-stress sample: {selection['selected_question_count']} questions across {selection['selected_family_count']} families",
        "- Human evidence: 0",
        "- Environment, grounding, execution, and answer recovery evaluated: no",
        "",
        "## Frozen sampling rule",
        "",
        "Each family receives `min(count, 1 + ceil(log2(count)))` seats. Within a family,",
        "questions are greedily selected for equal-axis marginal coverage of fine, topology,",
        "task, N100/new200 source slice, producer partition, record status, and alternative-graph",
        "presence; ties use the frozen seeded SHA-256 rank. Question text and environment data",
        "are not ranking features.",
        "",
        "This is a coverage stress sample, not a probability sample and not a prevalence estimate.",
        "Rare families are deliberately overrepresented.",
        "",
        "## Frequency strata",
        "",
        "| Stratum | Families | Source questions | Selected |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in selection["strata_summary"]:
        lines.append(
            f"| `{item['frequency_stratum']}` | {item['family_count']} | {item['source_member_question_count']} | {item['selected_question_count']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The library records deterministic recurrence under one AI question-only extractor",
            "and normalizer. Same-role contraction does not prove semantic equivalence; producer",
            "partitions are not independent reviewers; `complete` is not correctness. The library",
            "does not select an operator vocabulary and is not gold or modeling-ready.",
            "",
            "The next stage may inspect environment content only for the committed representative",
            "IDs, and must record backbone adequacy, operator realization, grounding, execution,",
            "and answer recovery as separate outcomes.",
            "",
        ]
    )
    return "\n".join(lines)


def build_output_payloads(
    args: argparse.Namespace,
    plan: dict[str, Any],
    freeze_commit: str,
) -> tuple[dict[str, tuple[Path, bytes]], list[dict[str, Any]], dict[str, Any]]:
    records, derived, _ = load_source_bundle(
        args.records,
        args.signatures,
        args.metrics,
        args.n300_run_manifest,
        args.exposure_ledger,
        args.record_schema,
    )
    source_bindings = _source_bindings(
        args.records,
        args.signatures,
        args.metrics,
        args.n300_run_manifest,
        args.exposure_ledger,
    )
    families, selection = build_library_and_selection(
        records, derived, source_bindings=source_bindings
    )
    expected = plan["expected_result"]
    family_signatures = [item["contracted_signature_sha256"] for item in families]
    observed_expected = {
        "source_record_count": TARGET_RECORD_COUNT,
        "candidate_family_count": len(families),
        "member_question_count": sum(len(item["members"]) for item in families),
        "evidence_tier_family_counts": _counter_dict(item["evidence_tier"] for item in families),
        "selected_question_count": selection["selected_question_count"],
        "selected_family_count": selection["selected_family_count"],
        "family_signatures_ordered_sha256": canonical_json_sha256(family_signatures),
        "family_signatures_set_sha256": canonical_string_set_sha256(family_signatures),
        "selected_question_ids_ordered_sha256": selection["selected_question_ids_ordered_sha256"],
        "selected_question_ids_set_sha256": selection["selected_question_ids_set_sha256"],
        "strata_summary": selection["strata_summary"],
    }
    if expected != observed_expected:
        raise CandidateLibraryError("live derived result differs from the committed expected-result hashes")
    family_validator = _schema_validator(args.family_schema)
    selection_validator = _schema_validator(args.selection_schema)
    errors = [
        error
        for index, family in enumerate(families)
        for error in _validation_errors(family_validator, family, f"family[{index}]")
    ]
    errors.extend(_validation_errors(selection_validator, selection, "selection"))
    if errors:
        raise CandidateLibraryError("output schema validation failed: " + " | ".join(errors[:20]))
    checks = _checks(families, selection)
    family_bytes = jsonl_file_bytes(families)
    selection_bytes = json_file_bytes(selection)
    checks_bytes = jsonl_file_bytes(checks)
    report_bytes = _report(families, selection).encode("utf-8")
    if not report_bytes.endswith(b"\n"):
        report_bytes += b"\n"
    preliminary = {
        "families": (args.families_output, family_bytes),
        "representative_selection": (args.selection_output, selection_bytes),
        "checks": (args.checks_output, checks_bytes),
        "report": (args.report_output, report_bytes),
    }
    manifest = {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "library_id": LIBRARY_ID,
        "selection_id": SELECTION_ID,
        "run_status": "complete_candidate_library_and_pre_environment_selection",
        "contract_freeze_commit": freeze_commit,
        "implementation_commit": plan["implementation_commit"],
        "source_commit": plan["source_commit"],
        "tool_version": TOOL_VERSION,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_bindings": source_bindings,
        "contract_bindings": {
            **plan["contract_artifacts"],
            "freeze_plan": _binding(args.plan),
        },
        "counts": {
            "source_records": TARGET_RECORD_COUNT,
            "candidate_families": len(families),
            "representative_questions": selection["selected_question_count"],
            "checks": len(checks),
            "human_evidence": 0,
        },
        "outputs": {
            label: {
                "repository_relative_path": _relative(path),
                "sha256": sha256_bytes(payload),
                **(
                    {"record_count": len(families)}
                    if label == "families"
                    else {"record_count": len(checks)}
                    if label == "checks"
                    else {}
                ),
            }
            for label, (path, payload) in preliminary.items()
        },
        "next_stage_contract": {
            "environment_realization_outcome_schema": _relative(args.outcome_schema),
            "representative_ids_committed_before_environment_inspection": True,
            "actual_environment_realization_status": "not_started",
            "required_separate_outcomes": [
                "backbone_adequacy",
                "environment_operator_realization",
                "grounding",
                "execution",
                "answer_recovery",
            ],
        },
    }
    payloads = dict(preliminary)
    payloads["run_manifest"] = (args.run_manifest_output, json_file_bytes(manifest))
    return payloads, families, selection


def _freeze_plan_mode(args: argparse.Namespace) -> int:
    if args.validate_only:
        raise CandidateLibraryError("--freeze-plan and --validate-only are mutually exclusive")
    plan = build_freeze_plan(args)
    status = write_output_batch({"plan": (args.plan, json_file_bytes(plan))})
    print(
        json.dumps(
            {
                "status": "pass",
                "mode": "freeze_plan",
                "plan": _relative(args.plan),
                "write_status": status["plan"],
                "families": plan["expected_result"]["candidate_family_count"],
                "selected_questions": plan["expected_result"]["selected_question_count"],
            },
            sort_keys=True,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.freeze_plan:
            return _freeze_plan_mode(args)
        plan = validate_plan(args)
        freeze_commit = verify_plan_freeze(args.plan, plan)
        payloads, families, selection = build_output_payloads(args, plan, freeze_commit)
        if args.validate_only:
            mismatches: list[str] = []
            for label, (path, payload) in payloads.items():
                if path.is_symlink() or not path.is_file():
                    mismatches.append(f"{label}: missing regular file")
                elif path.read_bytes() != payload:
                    mismatches.append(f"{label}: bytes differ from deterministic reconstruction")
            if mismatches:
                raise CandidateLibraryError("; ".join(mismatches))
            print(
                json.dumps(
                    {
                        "status": "pass",
                        "mode": "validate_only",
                        "families": len(families),
                        "selected_questions": selection["selected_question_count"],
                        "contract_freeze_commit": freeze_commit,
                    },
                    sort_keys=True,
                )
            )
            return 0
        statuses = write_output_batch(payloads)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "mode": "build",
                    "families": len(families),
                    "selected_questions": selection["selected_question_count"],
                    "checks": 1 + len(families) + selection["selected_question_count"],
                    "contract_freeze_commit": freeze_commit,
                    "write_statuses": statuses,
                },
                sort_keys=True,
            )
        )
        return 0
    except (CandidateLibraryError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "tool_version": TOOL_VERSION,
                    "error": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
