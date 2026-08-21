#!/usr/bin/env python3
"""Compute corpus and reusable-operator statistics from raw annotations."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from _common import (
    canonical_json_sha256,
    first_string,
    git_commit_identity,
    historical_output_collision_errors,
    iter_json_records,
    output_path_collision_errors,
    read_json,
    sha256_file,
    write_json,
)
from validate_annotation import topology_errors


STATS_TOOL_VERSION = "corpus_statistics_tool_v0_1"


VALID_REVIEW_STATES = {
    "llm_proposed",
    "deterministic_validation_only",
    "llm_assisted_pending_human",
    "human_single_review",
    "human_double_review_unadjudicated",
    "adjudicated",
    "rejected",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path)
    parser.add_argument(
        "--operator-vocabulary",
        type=Path,
        default=Path("data_construction/operator_design/operator_vocabulary_medium_v0_1.json"),
    )
    parser.add_argument(
        "--validation-checks",
        type=Path,
        help=(
            "Validator JSONL for the exact annotation bytes. Without hash-bound full-schema pass "
            "records, statistics remain integrity-failed/diagnostic."
        ),
    )
    parser.add_argument("--allow-empty", action="store_true", help="Diagnostic-only: emit an explicit empty summary")
    parser.add_argument(
        "--allow-invalid",
        action="store_true",
        help="Diagnostic-only: emit statistics even when identifiers/operators fail integrity checks",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("data_construction/reports/corpus_statistics_v0_1.json"),
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=Path("data_construction/reports/corpus_statistics.md"),
    )
    return parser.parse_args()


def operator_definitions(vocabulary: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(vocabulary, dict):
        return {}
    raw = vocabulary.get("operators", [])
    if not isinstance(raw, list) and isinstance(vocabulary.get("vocabulary"), dict):
        raw = vocabulary["vocabulary"].get("operators", [])
    definitions: dict[str, dict[str, Any]] = {}
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                definitions[item] = {"name": item}
            elif isinstance(item, dict):
                name = first_string(item, ("name", "operator", "id"))
                if name:
                    definitions[name] = item
    return definitions


def contract_types(definition: dict[str, Any], direction: str) -> list[str]:
    direct = definition.get(f"{direction}_types")
    if isinstance(direct, list):
        return [str(value) for value in direct]
    ports = definition.get(f"{direction}_ports")
    if isinstance(ports, list):
        return sorted(
            {
                str(port["type"])
                for port in ports
                if isinstance(port, dict) and isinstance(port.get("type"), str)
            }
        )
    legacy = definition.get("inputs" if direction == "input" else "outputs")
    if isinstance(legacy, list):
        return [str(value) for value in legacy]
    if direction == "output" and isinstance(definition.get("output_type"), str):
        return [definition["output_type"]]
    return []


def values_for_key(value: Any, wanted: set[str]) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in wanted and isinstance(child, (str, int)):
                yield str(child)
            yield from values_for_key(child, wanted)
    elif isinstance(value, list):
        for child in value:
            yield from values_for_key(child, wanted)


def context_signature(record: dict[str, Any]) -> str:
    skeleton = record.get("semantic_skeleton", {})
    if not isinstance(skeleton, dict):
        return "unknown"
    parts: list[str] = []
    for key in (
        "answer_type",
        "comparison_requirement",
        "comparison_requirements",
        "aggregation_requirement",
        "aggregation_requirements",
        "arithmetic_requirement",
        "arithmetic_requirements",
        "ordinal_requirement",
        "ordinal_requirements",
        "selection_requirement",
        "selection_requirements",
        "back_mapping_requirement",
        "back_mapping_requirements",
    ):
        value = skeleton.get(key)
        if value not in (None, False, "", [], {}):
            if isinstance(value, (str, int, bool)):
                parts.append(f"{key}={value}")
            else:
                parts.append(f"{key}=present")
    return "|".join(parts) or "unspecified"


def review_label(record: dict[str, Any]) -> str:
    review = record.get("review_status")
    if isinstance(review, str):
        return review
    if isinstance(review, dict):
        return first_string(review, ("state", "status", "label", "stage")) or "unknown"
    return "unknown"


def ambiguity_observation(record: dict[str, Any]) -> bool | None:
    if "ambiguity" not in record:
        return None
    ambiguity = record["ambiguity"]
    if isinstance(ambiguity, bool):
        return ambiguity
    if isinstance(ambiguity, dict):
        value = ambiguity.get("has_ambiguity")
        return value if isinstance(value, bool) else None
    return None


def validation_check_errors(
    records: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    annotations_sha256: str,
    vocabulary_sha256: str,
) -> list[str]:
    errors: list[str] = []
    if len(checks) != len(records):
        errors.append("validation checks do not have a 1:1 annotation record count")
        return errors
    for index, (record, check) in enumerate(zip(records, checks)):
        label = f"validation checks record {index}"
        expected_question_id = first_string(record, ("question_id", "qid", "id"))
        context = check.get("validation_context") if isinstance(check, dict) else None
        if not isinstance(check, dict):
            errors.append(f"{label} is not an object")
            continue
        if check.get("question_id") != expected_question_id:
            errors.append(f"{label} question_id does not match")
        if check.get("validator_version") != "annotation_validator_v0_1":
            errors.append(f"{label} validator_version is unsupported")
        if check.get("status") != "pass" or check.get("errors") not in ([], None):
            errors.append(f"{label} is not a clean pass")
        if check.get("annotation_canonical_sha256") != canonical_json_sha256(record):
            errors.append(f"{label} annotation canonical SHA-256 does not match")
        if not isinstance(context, dict):
            errors.append(f"{label} has no validation_context")
            continue
        if context.get("annotations_artifact_sha256") != annotations_sha256:
            errors.append(f"{label} annotations artifact SHA-256 does not match")
        if context.get("operator_vocabulary_artifact_sha256") != vocabulary_sha256:
            errors.append(f"{label} operator vocabulary SHA-256 does not match")
        if context.get("validation_mode") != "draft_2020_12_plus_structural":
            errors.append(f"{label} was not produced by full-schema plus structural validation")
        schema_sha = context.get("schema_artifact_sha256")
        if not isinstance(schema_sha, str) or len(schema_sha) != 64:
            errors.append(f"{label} has no schema artifact SHA-256")
    return errors


def compute(
    records: list[dict[str, Any]],
    definitions: dict[str, dict[str, Any]],
    validation_errors: list[str] | None = None,
) -> dict[str, Any]:
    role_counts: Counter[str] = Counter()
    review_counts: Counter[str] = Counter()
    graph_lengths: list[int] = []
    execution_graph_reference_count = 0
    topology_lengths: list[int] = []
    topology_missing_count = 0
    ambiguity_count = 0
    ambiguity_observation_count = 0
    alternatives_count = 0
    alternative_plan_observation_count = 0
    review_observation_count = 0
    operator_questions: dict[str, set[str]] = defaultdict(set)
    operator_nodes: Counter[str] = Counter()
    operator_contexts: dict[str, set[str]] = defaultdict(set)
    operator_schemas: dict[str, set[str]] = defaultdict(set)
    operator_ambiguities: Counter[str] = Counter()
    operator_ambiguity_observations: Counter[str] = Counter()
    operator_exceptions: dict[str, list[str]] = defaultdict(list)
    observed_question_ids: list[str] = []
    missing_question_id_records: list[int] = []
    invalid_review_status_records: list[int] = []
    topology_integrity_errors: list[str] = []

    for index, record in enumerate(records):
        observed_question_id = first_string(record, ("question_id", "qid", "id"))
        if observed_question_id is None:
            missing_question_id_records.append(index)
        else:
            observed_question_ids.append(observed_question_id)
        question_id = observed_question_id or f"__record_{index}"
        role_counts[first_string(record, ("dataset_role", "role")) or "unknown"] += 1
        observed_review = review_label(record)
        review_counts[observed_review] += 1
        if observed_review in VALID_REVIEW_STATES:
            review_observation_count += 1
        elif "review_status" in record:
            invalid_review_status_records.append(index)
        ambiguity = ambiguity_observation(record)
        if ambiguity is not None:
            ambiguity_observation_count += 1
            ambiguity_count += int(ambiguity)
        alternatives = record.get("alternative_plans")
        if isinstance(alternatives, list):
            alternative_plan_observation_count += 1
            alternatives_count += len(alternatives)

        topology = record.get("operator_topology", {})
        topology_nodes = topology.get("nodes", []) if isinstance(topology, dict) else []
        if "operator_topology" in record:
            topology_integrity_errors.extend(
                topology_errors(
                    record.get("operator_topology"),
                    f"record {index} operator_topology",
                    set(definitions),
                )
            )
        if isinstance(topology, dict) and isinstance(topology_nodes, list) and topology_nodes:
            topology_lengths.append(len(topology_nodes))
            node_ids: list[str] = []
            dependencies_by_node: dict[str, list[str]] = {}
            for node_index, node in enumerate(topology_nodes):
                if not isinstance(node, dict):
                    topology_integrity_errors.append(
                        f"record {index} operator_topology.nodes[{node_index}] is not an object"
                    )
                    continue
                node_id = first_string(node, ("node_id", "id"))
                if node_id is None:
                    topology_integrity_errors.append(
                        f"record {index} operator_topology.nodes[{node_index}] has no node_id"
                    )
                    continue
                node_ids.append(node_id)
                dependencies = node.get("depends_on")
                if not isinstance(dependencies, list) or any(
                    not isinstance(dependency, str) for dependency in dependencies
                ):
                    topology_integrity_errors.append(
                        f"record {index} operator_topology node {node_id!r} has invalid depends_on"
                    )
                    dependencies_by_node[node_id] = []
                else:
                    dependencies_by_node[node_id] = dependencies
                if first_string(node, ("operator", "operation")) is None:
                    topology_integrity_errors.append(
                        f"record {index} operator_topology node {node_id!r} has no operator"
                    )

            node_id_set = set(node_ids)
            duplicate_node_ids = sorted(
                node_id for node_id, count in Counter(node_ids).items() if count > 1
            )
            if duplicate_node_ids:
                topology_integrity_errors.append(
                    f"record {index} operator_topology has duplicate node IDs: {duplicate_node_ids}"
                )
            dependency_errors = False
            for node_id, dependencies in dependencies_by_node.items():
                unknown = sorted(set(dependencies) - node_id_set)
                if unknown:
                    dependency_errors = True
                    topology_integrity_errors.append(
                        f"record {index} operator_topology node {node_id!r} has unknown dependencies: {unknown}"
                    )
            if not duplicate_node_ids and not dependency_errors and len(node_id_set) == len(topology_nodes):
                children: dict[str, list[str]] = defaultdict(list)
                indegree = {node_id: 0 for node_id in node_id_set}
                for node_id, dependencies in dependencies_by_node.items():
                    indegree[node_id] = len(dependencies)
                    for dependency in dependencies:
                        children[dependency].append(node_id)
                queue = [node_id for node_id, degree in indegree.items() if degree == 0]
                visited = 0
                while queue:
                    node_id = queue.pop()
                    visited += 1
                    for child in children[node_id]:
                        indegree[child] -= 1
                        if indegree[child] == 0:
                            queue.append(child)
                if visited != len(node_id_set):
                    topology_integrity_errors.append(
                        f"record {index} operator_topology contains a dependency cycle"
                    )
            for field in ("entry_node_ids", "output_node_ids"):
                references = topology.get(field)
                if references is not None:
                    if not isinstance(references, list) or any(
                        not isinstance(reference, str) for reference in references
                    ):
                        topology_integrity_errors.append(
                            f"record {index} operator_topology.{field} is invalid"
                        )
                    else:
                        unknown = sorted(set(references) - node_id_set)
                        if unknown:
                            topology_integrity_errors.append(
                                f"record {index} operator_topology.{field} has unknown node IDs: {unknown}"
                            )
        else:
            topology_missing_count += 1
        graph = record.get("execution_graph", {})
        graph_nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
        if isinstance(graph_nodes, list) and graph_nodes:
            graph_lengths.append(len(graph_nodes))
        elif isinstance(graph, dict) and isinstance(graph.get("graph_artifact"), dict):
            execution_graph_reference_count += 1

        schema_ids = set(values_for_key(record.get("grounding", {}), {"schema_id", "table_id"}))
        top_table = first_string(record, ("table_id",))
        if top_table:
            schema_ids.add(top_table)
        context = context_signature(record)
        operators_for_question: set[str] = set()
        for node in topology_nodes if isinstance(topology_nodes, list) else []:
            if not isinstance(node, dict):
                continue
            operator = first_string(node, ("operator", "operation"))
            if not operator:
                continue
            operator_nodes[operator] += 1
            operators_for_question.add(operator)
            exception = first_string(node, ("exception", "exception_reason"))
            if exception and len(operator_exceptions[operator]) < 20:
                operator_exceptions[operator].append(f"{question_id}: {exception}")
        for operator in operators_for_question:
            operator_questions[operator].add(question_id)
            operator_contexts[operator].add(context)
            operator_schemas[operator].update(schema_ids)
            if ambiguity is not None:
                operator_ambiguity_observations[operator] += 1
                operator_ambiguities[operator] += int(ambiguity)

    duplicate_question_ids = sorted(
        identifier
        for identifier, count in Counter(observed_question_ids).items()
        if count > 1
    )
    unknown_operators = sorted(set(operator_nodes) - set(definitions))
    integrity_errors: list[str] = []
    if validation_errors is None:
        integrity_errors.append("hash-bound full annotation validation checks are not attached")
    else:
        integrity_errors.extend(validation_errors)
    if missing_question_id_records:
        integrity_errors.append("one or more annotation records have no question_id")
    if duplicate_question_ids:
        integrity_errors.append("duplicate question_id values are present")
    if unknown_operators:
        integrity_errors.append("operators outside the selected vocabulary are present")
    if invalid_review_status_records:
        integrity_errors.append("one or more explicit review_status values are outside the schema vocabulary")
    if topology_integrity_errors:
        integrity_errors.append("one or more operator topologies fail ID/reference/DAG integrity")

    all_operators = sorted(set(definitions) | set(operator_nodes))
    operator_statistics: dict[str, Any] = {}
    for operator in all_operators:
        definition = definitions.get(operator, {})
        input_types = contract_types(definition, "input")
        output_types = contract_types(definition, "output")
        contexts = operator_contexts[operator]
        schemas = operator_schemas[operator]
        observed_breadth = (
            "multi_context_multi_schema"
            if len(operator_questions[operator]) > 1 and len(contexts) > 1 and len(schemas) > 1
            else "insufficient_observations_for_reusability_claim"
        )
        operator_statistics[operator] = {
            "question_frequency": len(operator_questions[operator]),
            "node_frequency": operator_nodes[operator],
            "input_types": input_types,
            "output_types": output_types,
            "semantic_context_count": len(contexts),
            "semantic_contexts": sorted(contexts),
            "schema_or_table_count": len(schemas),
            "schema_or_table_ids": sorted(schemas),
            "ambiguity_count": operator_ambiguities[operator],
            "ambiguity_observation_count": operator_ambiguity_observations[operator],
            "ambiguity_rate": (
                operator_ambiguities[operator] / operator_ambiguity_observations[operator]
                if operator_ambiguity_observations[operator]
                else None
            ),
            "exceptions": operator_exceptions[operator],
            "observed_reusability_evidence": observed_breadth,
        }

    integrity_status = "fail" if integrity_errors else ("diagnostic_empty" if not records else "pass")
    evidence_complete = (
        bool(records)
        and not integrity_errors
        and topology_missing_count == 0
        and not topology_integrity_errors
        and ambiguity_observation_count == len(records)
        and alternative_plan_observation_count == len(records)
        and review_observation_count == len(records)
    )
    return {
        "schema_version": "corpus_statistics_v0_1",
        "annotation_count": len(records),
        "integrity_status": integrity_status,
        "evidence_complete": evidence_complete,
        "integrity_errors": integrity_errors,
        "missing_question_id_record_indices": missing_question_id_records,
        "duplicate_question_ids": duplicate_question_ids,
        "unknown_operators": unknown_operators,
        "invalid_review_status_record_indices": invalid_review_status_records,
        "topology_integrity_errors": topology_integrity_errors,
        "role_counts": dict(sorted(role_counts.items())),
        "review_status_counts": dict(sorted(review_counts.items())),
        "review_status_observation_count": review_observation_count,
        "ambiguity_count": ambiguity_count,
        "ambiguity_observation_count": ambiguity_observation_count,
        "ambiguity_rate": (
            ambiguity_count / ambiguity_observation_count if ambiguity_observation_count else None
        ),
        "alternative_plan_count": alternatives_count,
        "alternative_plan_observation_count": alternative_plan_observation_count,
        "operator_topology_length": distribution(topology_lengths),
        "operator_topology_missing_count": topology_missing_count,
        "execution_graph_length": distribution(graph_lengths),
        "execution_graph_reference_count": execution_graph_reference_count,
        "execution_graph_length_scope": (
            "legacy_inline_graphs_only; referenced IR artifacts require the recovered IR v0.2 parser"
        ),
        "operator_statistics": operator_statistics,
        "interpretation_limits": [
            "Schema breadth uses grounded schema_id/table_id identities when available.",
            "Observed breadth is not proof that an operator is universally reusable.",
            "Absent human review cannot be interpreted as agreement.",
            "Missing ambiguity or alternative-plan fields are unobserved, never negative observations.",
        ],
    }


def distribution(values: list[int]) -> dict[str, Any]:
    return {
        "count": len(values),
        "mean": statistics.fmean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def render_markdown(stats: dict[str, Any]) -> str:
    lines = [
        "# Corpus statistics",
        "",
        f"주석 수: **{stats['annotation_count']}**",
        f"무결성 상태: **{stats['integrity_status']}**",
        f"증거 완전성: **{str(stats['evidence_complete']).lower()}**",
        "",
        "## 역할 및 검토 상태",
        "",
        f"- 역할: `{json.dumps(stats['role_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- 검토 상태: `{json.dumps(stats['review_status_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- 검토 상태 관측 수: {stats['review_status_observation_count']}",
        f"- 모호성 표기 수/관측 수/비율: {stats['ambiguity_count']} / "
        f"{stats['ambiguity_observation_count']} / {stats['ambiguity_rate']}",
        f"- 대안 계획 수/필드 관측 수: {stats['alternative_plan_count']} / "
        f"{stats['alternative_plan_observation_count']}",
        f"- 누락 question_id 레코드: `{json.dumps(stats['missing_question_id_record_indices'])}`",
        f"- 중복 question_id: `{json.dumps(stats['duplicate_question_ids'], ensure_ascii=False)}`",
        f"- 어휘 외 연산자: `{json.dumps(stats['unknown_operators'], ensure_ascii=False)}`",
        f"- 잘못된 명시적 review_status 레코드: "
        f"`{json.dumps(stats['invalid_review_status_record_indices'])}`",
        f"- topology 무결성 오류: `{json.dumps(stats['topology_integrity_errors'], ensure_ascii=False)}`",
        "",
        "## 그래프 길이",
        "",
        f"- 연산자 topology: `{json.dumps(stats['operator_topology_length'], sort_keys=True)}`",
        f"- 연산자 topology 미관측/빈 레코드: {stats['operator_topology_missing_count']}",
        f"- 실행 그래프: `{json.dumps(stats['execution_graph_length'], sort_keys=True)}`",
        f"- 외부 실행 그래프 reference 수: {stats['execution_graph_reference_count']}",
        f"- 실행 그래프 길이 범위: {stats['execution_graph_length_scope']}",
        "",
        "## 연산자 통계",
        "",
        "| 연산자 | 질문 빈도 | 노드 빈도 | 의미 문맥 수 | 스키마/표 수 | 모호성 수 | 재사용 관측 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for operator, values in stats["operator_statistics"].items():
        lines.append(
            f"| {operator} | {values['question_frequency']} | {values['node_frequency']} | "
            f"{values['semantic_context_count']} | {values['schema_or_table_count']} | "
            f"{values['ambiguity_count']} | {values['observed_reusability_evidence']} |"
        )
    lines.extend(
        [
            "",
            "## 해석 제한",
            "",
            *[f"- {item}" for item in stats["interpretation_limits"]],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    outputs = {"json_output": args.json_output, "report_output": args.report_output}
    collisions = output_path_collision_errors(
        {
            "annotations": args.annotations,
            "operator_vocabulary": args.operator_vocabulary,
            **({"validation_checks": args.validation_checks} if args.validation_checks else {}),
        },
        outputs,
    )
    collisions.extend(historical_output_collision_errors(outputs, project_root))
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    try:
        records = list(iter_json_records(args.annotations))
        vocabulary = read_json(args.operator_vocabulary)
        definitions = operator_definitions(vocabulary)
        checks = (
            list(iter_json_records(args.validation_checks))
            if args.validation_checks is not None
            else None
        )
    except (OSError, ValueError) as exc:
        print(f"invalid statistics input JSON: {exc}", file=sys.stderr)
        return 2
    if not records and not args.allow_empty:
        print("refusing to report corpus statistics for an empty annotation input", file=sys.stderr)
        return 2
    annotations_sha256 = sha256_file(args.annotations)
    vocabulary_sha256 = sha256_file(args.operator_vocabulary)
    attached_validation_errors = (
        validation_check_errors(records, checks, annotations_sha256, vocabulary_sha256)
        if checks is not None
        else None
    )
    stats = compute(records, definitions, attached_validation_errors)
    stats["provenance"] = {
        "tool_version": STATS_TOOL_VERSION,
        "annotations_artifact_sha256": annotations_sha256,
        "operator_vocabulary_artifact_sha256": vocabulary_sha256,
        "validation_checks_artifact_sha256": (
            sha256_file(args.validation_checks) if args.validation_checks is not None else None
        ),
        "validation_checks_verified": attached_validation_errors == [],
        "operator_vocabulary_version": first_string(vocabulary, ("vocabulary_version",)),
        "operator_vocabulary_granularity": first_string(vocabulary, ("granularity",)),
        "code_commit": git_commit_identity(project_root),
    }
    write_json(args.json_output, stats)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(render_markdown(stats), encoding="utf-8", newline="\n")
    print(json.dumps({"annotations": len(records), "operators": len(stats["operator_statistics"])}, sort_keys=True))
    return 0 if stats["integrity_status"] in {"pass", "diagnostic_empty"} or args.allow_invalid else 1


if __name__ == "__main__":
    raise SystemExit(main())
