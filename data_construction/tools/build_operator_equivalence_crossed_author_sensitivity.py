#!/usr/bin/env python3
"""Freeze, packetize, and evaluate the crossed-author normalization fallback."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

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
import build_operator_equivalence_normalization as normalizer
import build_representative_environment_realization as representative


TOOL_VERSION = "operator_equivalence_crossed_author_sensitivity_builder_v0_1"
PLAN_SCHEMA_VERSION = "operator_equivalence_crossed_author_sensitivity_plan_v0_1"
PLAN_ID = "hybridqa_operator_equivalence_crossed_author_sensitivity_plan_v0_1"
RUN_ID = "hybridqa_operator_equivalence_crossed_author_sensitivity_v0_1_run_001"
AUTHOR_IDS = ("crossed_author_01", "crossed_author_02")
AUTHOR_PRODUCERS = ("e2_author_partition_05", "e2_author_partition_06")
EXPECTED_QUESTIONS = 16

ROOT = Path(__file__).resolve().parents[2]
SCALE_BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
CONTRACTS = SCALE_BASE / "contracts"
PROMPTS = SCALE_BASE / "prompts"
SOURCE_BASE = SCALE_BASE / "representative_environment_realization_v0_1"
RUN_BASE = SCALE_BASE / "operator_equivalence_crossed_author_sensitivity_v0_1"

DEFAULT_PLAN = CONTRACTS / "operator_equivalence_crossed_author_sensitivity_plan_v0_1.json"
DEFAULT_COMPARISON_SCHEMA = CONTRACTS / "operator_equivalence_crossed_author_sensitivity_schema_v0_1.json"
DEFAULT_REALIZATION_SCHEMA = CONTRACTS / "open_operator_realization_schema_v0_1.json"
DEFAULT_NORMALIZATION_SCHEMA = CONTRACTS / "operator_equivalence_normalization_schema_v0_1.json"
DEFAULT_NORMALIZATION_PLAN = CONTRACTS / "operator_equivalence_normalization_plan_v0_1.json"
DEFAULT_PROMPT = PROMPTS / "operator_equivalence_crossed_author_sensitivity_v0_1.md"
DEFAULT_VIEWS = SOURCE_BASE / "inputs/environment_views.jsonl"
DEFAULT_E2_PACKETS = tuple(
    SOURCE_BASE / f"stage_e2/authoring_packets/partition_{index:02d}.jsonl"
    for index in range(1, 5)
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
NORMALIZER_TOOL = ROOT / "data_construction/tools/build_operator_equivalence_normalization.py"
REPRESENTATIVE_TOOL = ROOT / "data_construction/tools/build_representative_environment_realization.py"
TEST_ARTIFACT = ROOT / "tests/test_operator_equivalence_crossed_author_sensitivity.py"

EVIDENCE_BOUNDARY = {
    "ai_non_human_non_gold": True,
    "fresh_reserve_ids_used": False,
    "grounding_evaluated": False,
    "execution_evaluated": False,
    "answer_recovery_evaluated": False,
}


class SensitivityError(ValueError):
    """Raised when the crossed-author contract is violated."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze-plan", action="store_true")
    modes.add_argument("--materialize-packets", action="store_true")
    modes.add_argument("--build-final", action="store_true")
    modes.add_argument("--validate-only", action="store_true")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--comparison-schema", type=Path, default=DEFAULT_COMPARISON_SCHEMA)
    parser.add_argument("--realization-schema", type=Path, default=DEFAULT_REALIZATION_SCHEMA)
    parser.add_argument("--normalization-schema", type=Path, default=DEFAULT_NORMALIZATION_SCHEMA)
    parser.add_argument("--normalization-plan", type=Path, default=DEFAULT_NORMALIZATION_PLAN)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--views", type=Path, default=DEFAULT_VIEWS)
    parser.add_argument("--e2-packets", nargs=4, type=Path, default=DEFAULT_E2_PACKETS)
    parser.add_argument("--packets", nargs=2, type=Path, default=DEFAULT_PACKETS)
    parser.add_argument("--author-outputs", nargs=2, type=Path, default=DEFAULT_AUTHOR_OUTPUTS)
    parser.add_argument("--combined-output", type=Path, default=DEFAULT_COMBINED)
    parser.add_argument("--normalized-output", type=Path, default=DEFAULT_NORMALIZED)
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
        raise SensitivityError(f"path outside repository: {path}") from exc
    if path.is_symlink() or ".." in relative.parts or ":" in relative.as_posix():
        raise SensitivityError(f"unsafe repository path: {relative.as_posix()}")
    return relative.as_posix()


def _binding(path: Path, *, record_count: int | None = None) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise SensitivityError(f"bound artifact missing or symlink: {_relative(path)}")
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
        raise SensitivityError(f"schema is not an object: {_relative(path)}")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise SensitivityError(f"invalid schema {_relative(path)}: {exc.message}") from exc
    return Draft202012Validator(schema)


def _contract_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "comparison_schema": args.comparison_schema,
        "realization_schema": args.realization_schema,
        "normalization_schema": args.normalization_schema,
        "protocol": args.prompt,
        "builder": Path(__file__).resolve(),
        "normalizer": NORMALIZER_TOOL,
        "representative_validator": REPRESENTATIVE_TOOL,
        "common_runtime": COMMON_RUNTIME,
        "tests": TEST_ARTIFACT,
    }


def _source_inputs(args: argparse.Namespace) -> dict[str, Path]:
    result = {
        "normalization_plan": args.normalization_plan,
        "representative_views": args.views,
    }
    result.update(
        {f"original_e2_authoring_packet_{index:02d}": path for index, path in enumerate(args.e2_packets, 1)}
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


def _selection(args: argparse.Namespace) -> list[dict[str, Any]]:
    plan = read_json(args.normalization_plan)
    try:
        selection = plan["precommitted_crossed_author_fallback"]["selection"]
    except (KeyError, TypeError) as exc:
        raise SensitivityError("normalization plan lacks crossed-author fallback") from exc
    if not isinstance(selection, list) or len(selection) != EXPECTED_QUESTIONS:
        raise SensitivityError("crossed-author fallback must contain 16 records")
    ids = [item.get("question_id") for item in selection if isinstance(item, dict)]
    if len(ids) != EXPECTED_QUESTIONS or len(ids) != len(set(ids)):
        raise SensitivityError("fallback IDs are malformed or non-unique")
    if Counter(item["selection_role"] for item in selection) != Counter(
        {"e1_challenge": 7, "adequate_control": 9}
    ):
        raise SensitivityError("fallback challenge/control counts changed")
    if Counter(item["original_e2_producer_partition"] for item in selection) != Counter(
        {f"e2_author_partition_{index:02d}": 4 for index in range(1, 5)}
    ):
        raise SensitivityError("fallback is not four-per-original-partition")
    return selection


def _original_packets(args: argparse.Namespace) -> dict[str, dict[str, Any]]:
    records = [record for path in args.e2_packets for record in iter_json_records(path)]
    by_question = {record["view"]["question_id"]: record for record in records}
    if len(by_question) != 71:
        raise SensitivityError("original E2 packets are not 71 unique records")
    return by_question


def _fixed_fields(original: dict[str, Any], author_index: int) -> dict[str, Any]:
    fields = json.loads(json.dumps(original["fixed_output_fields"]))
    author_id = AUTHOR_IDS[author_index]
    producer = AUTHOR_PRODUCERS[author_index]
    question_id = fields["question_id"]
    fields["realization_id"] = f"open_operator_realization_v0_1:{author_id}:{question_id}"
    fields["run_id"] = RUN_ID
    fields["producer_partition"] = producer
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
                    "schema_version": "operator_equivalence_crossed_author_input_v0_1",
                    "run_id": RUN_ID,
                    "author_id": author_id,
                    "author_producer_partition": AUTHOR_PRODUCERS[author_index],
                    "selection_role_hidden_from_author": True,
                    "original_producer_partition_hidden_from_author": True,
                    "isolation_contract": {
                        "fresh_context_required": True,
                        "prior_e2_records_excluded": True,
                        "normalization_artifacts_excluded": True,
                        "e1_content_excluded": True,
                        "other_author_packet_and_output_excluded": True,
                        "preserved_vocabularies_excluded": True,
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
            raise SensitivityError(f"planned output exists before plan freeze: {_relative(path)}")
    _validator(args.comparison_schema)
    _validator(args.realization_schema)
    _validator(args.normalization_schema)
    selection = _selection(args)
    implementation_commit = git_tracked_commit_identity(ROOT, _contract_inputs(args).values())
    source_commit = git_tracked_commit_identity(ROOT, _source_inputs(args).values())
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "run_id": RUN_ID,
        "status": "frozen_before_author_packets_and_author_outputs",
        "implementation_commit": implementation_commit,
        "source_commit": source_commit,
        "contract_artifacts": {label: _binding(path) for label, path in _contract_inputs(args).items()},
        "source_artifacts": {label: _binding(path) for label, path in _source_inputs(args).items()},
        "selection": selection,
        "author_contract": {
            "authors": list(AUTHOR_IDS),
            "producer_partitions": list(AUTHOR_PRODUCERS),
            "every_author_covers_every_question": True,
            "fresh_contexts_required": True,
            "author_contexts_shared": False,
            "prior_e2_and_normalization_outputs_visible": False,
            "human_review_or_majority_vote_claimed": False,
            "fresh_reserve_ids_used": False,
        },
        "frozen_decision_criteria": {
            "invalid_author_record_count_max": 0,
            "normalization_not_equivalent_count_max": 0,
            "semantic_set_exact_match_rate_min": 0.875,
            "mean_semantic_set_jaccard_min": 0.95,
            "e1_challenge_semantic_exact_match_count_min": 5,
            "adequate_control_semantic_exact_match_count_min": 8,
            "normalization_provisional_fraction_max": 0.10,
            "distinct_adapter_signature_count_max": 32,
            "branch_on_pass": "FREEZE_PROVISIONAL_NON_FINAL_OPERATOR_ADAPTER_FOR_GROUNDING",
            "branch_on_fail": "REVISE_EQUIVALENCE_NORMALIZATION_CONTRACT",
        },
        "planned_outputs": {
            label: {"repository_relative_path": _relative(path)}
            for label, path in _all_planned_outputs(args).items()
        },
    }


def _validate_plan(args: argparse.Namespace) -> dict[str, Any]:
    plan = read_json(args.plan)
    if not isinstance(plan, dict) or plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise SensitivityError("crossed-author plan has the wrong version")
    if plan.get("status") != "frozen_before_author_packets_and_author_outputs":
        raise SensitivityError("crossed-author plan was not frozen before outputs")
    for label, path in _contract_inputs(args).items():
        if plan["contract_artifacts"][label] != _binding(path):
            raise SensitivityError(f"plan contract binding mismatch: {label}")
    for label, path in _source_inputs(args).items():
        if plan["source_artifacts"][label] != _binding(path):
            raise SensitivityError(f"plan source binding mismatch: {label}")
    if plan["selection"] != _selection(args):
        raise SensitivityError("plan selection differs from normalization fallback")
    for label, path in _all_planned_outputs(args).items():
        if plan["planned_outputs"][label]["repository_relative_path"] != _relative(path):
            raise SensitivityError(f"plan output binding mismatch: {label}")
    return plan


def materialize_packet_outputs(args: argparse.Namespace) -> dict[str, tuple[Path, bytes]]:
    _validate_plan(args)
    packets = build_packets(args)
    return {
        f"authoring_packet_{index:02d}": (path, jsonl_file_bytes(records))
        for index, (path, records) in enumerate(zip(args.packets, packets), 1)
    }


def _variant_graphs(view: dict[str, Any]) -> dict[str, dict[str, Any]]:
    context = view["payload"]["candidate_backbone_context"]
    result = {"primary": context["primary_graph"]}
    result.update({item["alternative_id"]: item["graph"] for item in context["alternative_graphs"]})
    return result


def _author_record_errors(
    record: dict[str, Any], packet: dict[str, Any], validator: Draft202012Validator
) -> list[str]:
    errors = [error.message for error in sorted(validator.iter_errors(record), key=lambda e: list(e.path))]
    fixed = packet["fixed_output_fields"]
    for key, value in fixed.items():
        if record.get(key) != value:
            errors.append(f"{key} differs from packet fixed_output_fields")
    if record.get("input_delivery") != {"view_fully_consumed": True, "completeness_status": "complete"}:
        errors.append("input delivery must be complete")
    if record.get("author_prior_exposure_to_record_before_packet") != "procedurally_attested_none":
        errors.append("fresh-context author must truthfully attest no prior record exposure")
    if record.get("author_prior_exposure_to_backbone_adequacy") != "procedurally_attested_none":
        errors.append("author must not have backbone-adequacy exposure")
    candidates = record.get("realization_candidates")
    results = record.get("variant_realization_results")
    if not isinstance(candidates, list) or not isinstance(results, list):
        return errors + ["candidate/results fields malformed"]
    variants = _variant_graphs(packet["view"])
    errors.extend(
        representative.validate_e1_e2_graph_contract(
            backbone_variants=variants, realization_candidates=candidates
        )
    )
    expected_variant_order = list(variants)
    if [item.get("backbone_variant_id") for item in results if isinstance(item, dict)] != expected_variant_order:
        errors.append("variant results do not follow packet variant order")
    candidate_ids = [candidate.get("candidate_id") for candidate in candidates if isinstance(candidate, dict)]
    if len(candidate_ids) != len(candidates) or len(candidate_ids) != len(set(candidate_ids)):
        errors.append("candidate IDs are missing or duplicated")
    statuses = []
    for result in results:
        if not isinstance(result, dict) or result.get("backbone_variant_id") not in variants:
            continue
        variant_id = result["backbone_variant_id"]
        targets = [candidate for candidate in candidates if candidate.get("target_backbone_variant_id") == variant_id]
        if result.get("candidate_ids") != [candidate["candidate_id"] for candidate in targets]:
            errors.append(f"{variant_id} result candidate order mismatch")
        complete = any(candidate.get("coverage_status") == "complete_for_target_variant" for candidate in targets)
        partial = any(candidate.get("coverage_status") == "partial_for_target_variant" for candidate in targets)
        status = result.get("status")
        statuses.append(status)
        if status == "fully_realized" and (not complete or result.get("blocking_unsupported_node_ids")):
            errors.append(f"{variant_id} fully_realized is inconsistent")
        if status == "partially_realized" and (complete or not partial):
            errors.append(f"{variant_id} partially_realized is inconsistent")
        if status == "indeterminate" and (complete or partial):
            errors.append(f"{variant_id} indeterminate is inconsistent")
        if status == "unavailable" and targets:
            errors.append(f"{variant_id} unavailable has candidates")
    expected_top = (
        "available" if "fully_realized" in statuses else
        "partial" if "partially_realized" in statuses else
        "indeterminate" if "indeterminate" in statuses else "unavailable"
    )
    if record.get("realization_status") != expected_top:
        errors.append("top-level realization status disagrees with variant results")
    return errors


def load_author_records(args: argparse.Namespace) -> tuple[list[list[dict[str, Any]]], list[list[dict[str, Any]]]]:
    _validate_plan(args)
    expected_packets = build_packets(args)
    for index, (path, records) in enumerate(zip(args.packets, expected_packets), 1):
        if not path.is_file() or path.read_bytes() != jsonl_file_bytes(records):
            raise SensitivityError(f"author packet {index} differs from frozen reconstruction")
    validator = _validator(args.realization_schema)
    author_records: list[list[dict[str, Any]]] = []
    for index, (path, packets) in enumerate(zip(args.author_outputs, expected_packets), 1):
        if path.is_symlink() or not path.is_file():
            raise SensitivityError(f"author output missing: {_relative(path)}")
        records = list(iter_json_records(path))
        expected_ids = [packet["view"]["question_id"] for packet in packets]
        if [record.get("question_id") for record in records] != expected_ids:
            raise SensitivityError(f"author {index} question order differs from packet")
        for record, packet in zip(records, packets):
            errors = _author_record_errors(record, packet, validator)
            if errors:
                raise SensitivityError(
                    f"author {index} record {record.get('question_id')} invalid: " + " | ".join(errors[:20])
                )
        if path.read_bytes() != jsonl_file_bytes(records):
            raise SensitivityError(f"author {index} output is not canonical JSONL")
        author_records.append(records)
    return author_records, expected_packets


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 1.0


def build_final_artifacts(args: argparse.Namespace) -> dict[str, tuple[Path, bytes]]:
    plan = _validate_plan(args)
    author_records, packets = load_author_records(args)
    normalization_validator = _validator(args.normalization_schema)
    comparison_validator = _validator(args.comparison_schema)
    normalized_by_author_question: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    all_normalized: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for author_index, records in enumerate(author_records):
        author_id = AUTHOR_IDS[author_index]
        packet_by_question = {packet["view"]["question_id"]: packet for packet in packets[author_index]}
        for record in records:
            view = packet_by_question[record["question_id"]]["view"]
            for candidate in record["realization_candidates"]:
                projection = normalizer.build_structural_projection(record, candidate, view)
                normalized = normalizer.normalize_projection(projection)
                schema_errors = list(normalization_validator.iter_errors(normalized))
                if schema_errors:
                    raise SensitivityError(f"normalization schema failure: {schema_errors[0].message}")
                normalized["normalization_id"] = (
                    f"operator_equivalence_normalization_v0_1:{author_id}:"
                    f"{record['question_id']}:{candidate['candidate_id']}"
                )
                normalized_by_author_question[(author_id, record["question_id"])].append(normalized)
                all_normalized.append(normalized)
            checks.append(
                {
                    "schema_version": "operator_equivalence_crossed_author_check_v0_1",
                    "author_id": author_id,
                    "question_id": record["question_id"],
                    "status": "pass",
                    "author_record_valid": True,
                    "candidate_count": len(record["realization_candidates"]),
                }
            )

    selection = {item["question_id"]: item for item in plan["selection"]}
    comparisons = []
    for question_id in [item["question_id"] for item in plan["selection"]]:
        author_results = []
        sets = []
        candidate_counts = []
        for author_id in AUTHOR_IDS:
            records = normalized_by_author_question[(author_id, question_id)]
            semantic_set = {record["semantic_quotient"]["signature_sha256"] for record in records}
            adapter_set = {record["environment_adapter_signature"]["signature_sha256"] for record in records}
            statuses = Counter(record["equivalence_assessment"]["status"] for record in records)
            author_results.append(
                {
                    "author_id": author_id,
                    "candidate_count": len(records),
                    "semantic_set": sorted(semantic_set),
                    "adapter_set": sorted(adapter_set),
                    "normalization_status_counts": dict(sorted(statuses.items())),
                }
            )
            sets.append((semantic_set, adapter_set))
            candidate_counts.append(len(records))
        comparison = {
            "schema_version": "operator_equivalence_crossed_author_comparison_v0_1",
            "question_id": question_id,
            "selection_role": selection[question_id]["selection_role"],
            "original_e2_producer_partition": selection[question_id]["original_e2_producer_partition"],
            "author_results": author_results,
            "semantic_set_exact_match": sets[0][0] == sets[1][0],
            "adapter_set_exact_match": sets[0][1] == sets[1][1],
            "semantic_set_jaccard": _jaccard(sets[0][0], sets[1][0]),
            "adapter_set_jaccard": _jaccard(sets[0][1], sets[1][1]),
            "candidate_count_delta": abs(candidate_counts[0] - candidate_counts[1]),
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
        errors = list(comparison_validator.iter_errors(comparison))
        if errors:
            raise SensitivityError(f"comparison schema failure: {errors[0].message}")
        comparisons.append(comparison)

    status_counts = Counter(
        record["equivalence_assessment"]["status"] for record in all_normalized
    )
    semantic_exact = sum(record["semantic_set_exact_match"] for record in comparisons)
    challenge_exact = sum(
        record["semantic_set_exact_match"] and record["selection_role"] == "e1_challenge"
        for record in comparisons
    )
    control_exact = sum(
        record["semantic_set_exact_match"] and record["selection_role"] == "adequate_control"
        for record in comparisons
    )
    mean_semantic_jaccard = sum(record["semantic_set_jaccard"] for record in comparisons) / len(comparisons)
    mean_adapter_jaccard = sum(record["adapter_set_jaccard"] for record in comparisons) / len(comparisons)
    provisional_fraction = status_counts["provisionally_equivalent"] / len(all_normalized)
    distinct_adapters = len(
        {record["environment_adapter_signature"]["signature_sha256"] for record in all_normalized}
    )
    criteria = plan["frozen_decision_criteria"]
    passed = all(
        [
            status_counts["not_equivalent"] <= criteria["normalization_not_equivalent_count_max"],
            semantic_exact / len(comparisons) >= criteria["semantic_set_exact_match_rate_min"],
            mean_semantic_jaccard >= criteria["mean_semantic_set_jaccard_min"],
            challenge_exact >= criteria["e1_challenge_semantic_exact_match_count_min"],
            control_exact >= criteria["adequate_control_semantic_exact_match_count_min"],
            provisional_fraction <= criteria["normalization_provisional_fraction_max"],
            distinct_adapters <= criteria["distinct_adapter_signature_count_max"],
        ]
    )
    decision = criteria["branch_on_pass"] if passed else criteria["branch_on_fail"]
    metrics = {
        "schema_version": "operator_equivalence_crossed_author_sensitivity_metrics_v0_1",
        "run_id": RUN_ID,
        "counts": {
            "questions": len(comparisons),
            "authors": 2,
            "author_records": sum(len(records) for records in author_records),
            "normalized_candidates": len(all_normalized),
            "normalization_status": dict(sorted(status_counts.items())),
            "semantic_set_exact_matches": semantic_exact,
            "adapter_set_exact_matches": sum(record["adapter_set_exact_match"] for record in comparisons),
            "challenge_semantic_exact_matches": challenge_exact,
            "control_semantic_exact_matches": control_exact,
            "distinct_adapter_signatures": distinct_adapters,
        },
        "rates": {
            "semantic_set_exact_match": semantic_exact / len(comparisons),
            "adapter_set_exact_match": sum(record["adapter_set_exact_match"] for record in comparisons) / len(comparisons),
            "mean_semantic_set_jaccard": mean_semantic_jaccard,
            "mean_adapter_set_jaccard": mean_adapter_jaccard,
            "normalization_provisional_fraction": provisional_fraction,
        },
        "frozen_criteria": criteria,
        "decision": decision,
        "criteria_passed": passed,
        "grounding_started": False,
        "fresh_reserve_ids_used": False,
        "human_evidence_created": False,
    }
    report = "\n".join(
        [
            "# Crossed-author operator-equivalence sensitivity v0.1",
            "",
            "Two fresh-context AI authors independently covered the same 16 already",
            "environment-exposed questions. This is a producer-confound diagnostic, not",
            "human review, gold annotation, majority voting, or unseen evaluation.",
            "",
            "## Results",
            "",
            f"- semantic-set exact match: {semantic_exact}/16",
            f"- mean semantic-set Jaccard: {mean_semantic_jaccard:.6f}",
            f"- adapter-set exact match: {metrics['counts']['adapter_set_exact_matches']}/16",
            f"- mean adapter-set Jaccard: {mean_adapter_jaccard:.6f}",
            f"- normalized candidates: {len(all_normalized)}",
            f"- provisional/not-equivalent: {status_counts['provisionally_equivalent']}/{status_counts['not_equivalent']}",
            "",
            "## Frozen branch result",
            "",
            f"`{decision}`",
            "",
            "Grounding was not performed in this diagnostic.",
            "",
        ]
    )
    combined = [record for records in author_records for record in records]
    preliminary = {
        "combined_author_records": (args.combined_output, jsonl_file_bytes(combined)),
        "normalized_candidates": (args.normalized_output, jsonl_file_bytes(all_normalized)),
        "question_comparisons": (args.comparisons_output, jsonl_file_bytes(comparisons)),
        "checks": (args.checks_output, jsonl_file_bytes(checks)),
        "metrics": (args.metrics_output, json_file_bytes(metrics)),
        "report": (args.report_output, report.encode("utf-8")),
    }
    manifest = {
        "schema_version": "operator_equivalence_crossed_author_sensitivity_run_manifest_v0_1",
        "run_id": RUN_ID,
        "plan": _binding(args.plan),
        "implementation_commit": plan["implementation_commit"],
        "source_commit": plan["source_commit"],
        "author_packets": [_binding(path, record_count=16) for path in args.packets],
        "author_outputs": [_binding(path, record_count=16) for path in args.author_outputs],
        "outputs": {
            label: {
                "repository_relative_path": _relative(path),
                "sha256": __import__("hashlib").sha256(payload).hexdigest(),
            }
            for label, (path, payload) in preliminary.items()
        },
        "metrics_summary": metrics,
        "validation_status": "pass",
    }
    return {**preliminary, "run_manifest": (args.manifest_output, json_file_bytes(manifest))}


def validate_materialized(args: argparse.Namespace) -> dict[str, Any]:
    expected_packets = materialize_packet_outputs(args)
    for _, (path, payload) in expected_packets.items():
        if not path.is_file() or path.read_bytes() != payload:
            raise SensitivityError("materialized author packet differs from reconstruction")
    expected = build_final_artifacts(args)
    mismatches = [label for label, (path, payload) in expected.items() if not path.is_file() or path.read_bytes() != payload]
    if mismatches:
        raise SensitivityError(f"materialized final artifacts differ: {mismatches}")
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
            write_output_batch({"plan": (args.plan, json_file_bytes(plan))}, overwrite=args.overwrite)
            print(json.dumps({"status": "frozen", "plan": _relative(args.plan)}, sort_keys=True))
        elif args.materialize_packets:
            statuses = write_output_batch(materialize_packet_outputs(args), overwrite=args.overwrite)
            print(json.dumps({"status": "packets_materialized", "outputs": statuses}, sort_keys=True))
        elif args.build_final:
            statuses = write_output_batch(build_final_artifacts(args), overwrite=args.overwrite)
            print(json.dumps({"status": "final_built", "outputs": statuses}, sort_keys=True))
        else:
            print(json.dumps(validate_materialized(args), sort_keys=True))
    except (SensitivityError, ValueError, OSError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
