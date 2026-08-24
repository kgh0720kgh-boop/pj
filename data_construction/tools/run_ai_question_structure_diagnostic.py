#!/usr/bin/env python3
"""Validate and compare the non-evidentiary AI question-structure shadow run."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from _common import (
    canonical_json_sha256,
    iter_json_records,
    json_file_bytes,
    jsonl_file_bytes,
    read_json,
    sha256_file,
    write_output_batch,
)
from validate_question_structure_annotations import (
    cue_errors,
    forbidden_key_paths,
    structural_errors,
)


TOOL_VERSION = "ai_question_structure_diagnostic_tool_v0_1"
RUN_ID = "ai_question_structure_pipeline_v0_1_run_001"
EVIDENCE_CLASS = "ai_pipeline_diagnostic_non_human_non_gold"
REVIEWER_SLOTS = ("ai_reviewer_01", "ai_reviewer_02")
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data_construction/diagnostics/ai_question_structure_pipeline_v0_1"
PLAN_PATH = BASE / "contracts/diagnostic_plan_v0_1.json"
VIEWS_PATH = ROOT / "data_construction/pilot/question_only_semantic_views_v0_1.jsonl"
HUMAN_SCHEMA_PATH = ROOT / "data_construction/schemas/question_structure_annotation_v0_1.json"
STAGE1_SCHEMA_PATH = BASE / "contracts/stage1_observation_schema_v0_1.json"
ANNOTATION_SCHEMA_PATH = BASE / "contracts/annotation_schema_v0_1.json"
ALIGNMENT_SCHEMA_PATH = BASE / "contracts/alignment_schema_v0_1.json"
TOPOLOGY_SCHEMA_PATH = BASE / "contracts/independent_topology_schema_v0_1.json"
REPRESENTATIONS_PATH = ROOT / "data_construction/pilot/granularity_representations.jsonl"
GRANULARITY_CHECKS_PATH = ROOT / "data_construction/pilot/granularity_deterministic_checks.jsonl"
GRANULARITY_METRICS_PATH = ROOT / "data_construction/reports/operator_granularity_metrics_v0_1.json"
CHECK_SCHEMA_VERSION = "ai_question_structure_diagnostic_check_v0_1"


class ContractError(ValueError):
    """Raised when a frozen diagnostic input contract is violated."""


def _schema_validator(path: Path) -> Any:
    try:
        import jsonschema
        from referencing import Registry, Resource
    except ImportError as exc:  # pragma: no cover - exercised by project preflight
        raise ContractError("jsonschema and referencing are required") from exc
    schema = read_json(path)
    validator_class = getattr(jsonschema, "Draft202012Validator", None)
    if validator_class is None:
        raise ContractError("Draft 2020-12 validation is unavailable")
    validator_class.check_schema(schema)
    registry = Registry()
    if path == ANNOTATION_SCHEMA_PATH:
        human_schema = read_json(HUMAN_SCHEMA_PATH)
        registry = registry.with_resource(
            human_schema["$id"], Resource.from_contents(human_schema)
        )
    return validator_class(
        schema,
        registry=registry,
        format_checker=jsonschema.FormatChecker(),
    )


def _schema_errors(validator: Any, value: Any, label: str) -> list[str]:
    errors: list[str] = []
    for error in sorted(
        validator.iter_errors(value),
        key=lambda item: [str(part) for part in item.absolute_path],
    ):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"{label}.{location}: {error.message}")
    return errors


def _git_contract_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", str(PLAN_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    commit = result.stdout.strip()
    return commit if len(commit) == 40 else "contract_not_committed"


def validate_contract() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    if PLAN_PATH.is_symlink() or not PLAN_PATH.is_file():
        raise ContractError("diagnostic plan is missing or is a symlink")
    plan = read_json(PLAN_PATH)
    if not isinstance(plan, dict):
        raise ContractError("diagnostic plan must be an object")
    if (
        plan.get("schema_version")
        != "ai_question_structure_pipeline_diagnostic_plan_v0_1"
        or plan.get("run_id") != RUN_ID
        or plan.get("purpose") != "non_evidentiary_end_to_end_ai_shadow_pipeline"
    ):
        raise ContractError("unsupported diagnostic plan identity")
    paths: dict[str, str] = {}
    for section in ("source_artifacts", "contract_artifacts"):
        artifacts = plan.get(section)
        if not isinstance(artifacts, list) or not artifacts:
            raise ContractError(f"diagnostic plan {section} must be nonempty")
        for item in artifacts:
            if not isinstance(item, dict):
                raise ContractError(f"diagnostic plan {section} contains a non-object")
            relative = item.get("repository_relative_path")
            expected = item.get("sha256")
            if not isinstance(relative, str) or not isinstance(expected, str):
                raise ContractError(f"diagnostic plan {section} has an invalid artifact binding")
            path = ROOT / relative
            if path.is_symlink() or not path.is_file():
                raise ContractError(f"bound artifact missing or symlinked: {relative}")
            observed = sha256_file(path)
            if observed != expected:
                raise ContractError(
                    f"bound artifact hash mismatch: {relative}: expected {expected}, got {observed}"
                )
            paths[relative] = observed
    for schema_path in (
        STAGE1_SCHEMA_PATH,
        ANNOTATION_SCHEMA_PATH,
        ALIGNMENT_SCHEMA_PATH,
        TOPOLOGY_SCHEMA_PATH,
    ):
        _schema_validator(schema_path)
    views = list(iter_json_records(VIEWS_PATH))
    batches = plan.get("batches")
    if not isinstance(batches, list) or len(batches) != 3:
        raise ContractError("diagnostic plan must contain exactly three batches")
    planned_ids = [qid for batch in batches for qid in batch.get("question_ids", [])]
    view_ids = [view.get("question_id") for view in views]
    if len(views) != 30 or planned_ids != view_ids or len(set(view_ids)) != 30:
        raise ContractError("views do not match the exact 30-question diagnostic order")
    return plan, views, paths


def _view_maps(views: list[dict[str, Any]]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    ids = [view["question_id"] for view in views]
    return ids, {view["question_id"]: view for view in views}


def _checks(records: list[Any], per_record: list[list[str]], scope: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, (record, errors) in enumerate(zip(records, per_record)):
        question_id = record.get("question_id") if isinstance(record, dict) else None
        output.append(
            {
                "schema_version": CHECK_SCHEMA_VERSION,
                "tool_version": TOOL_VERSION,
                "scope": scope,
                "record_index": index,
                "question_id": question_id,
                "status": "pass" if not errors else "fail",
                "errors": sorted(set(errors)),
            }
        )
    return output


def validate_stage1_records(
    path: Path, reviewer_slot: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    _, views, _ = validate_contract()
    ids, by_id = _view_maps(views)
    records = list(iter_json_records(path))
    global_errors: list[str] = []
    if reviewer_slot not in REVIEWER_SLOTS:
        global_errors.append("unsupported reviewer slot")
    if len(records) != 30:
        global_errors.append("stage-1 file must contain exactly 30 records")
    if [r.get("question_id") for r in records if isinstance(r, dict)] != ids:
        global_errors.append("stage-1 records do not match the exact 30-question order")
    validator = _schema_validator(STAGE1_SCHEMA_PATH)
    per_record: list[list[str]] = []
    for index, record in enumerate(records):
        errors = _schema_errors(validator, record, f"records[{index}]")
        if isinstance(record, dict):
            qid = record.get("question_id")
            view = by_id.get(qid) if isinstance(qid, str) else None
            if record.get("reviewer_slot") != reviewer_slot:
                errors.append(f"records[{index}].reviewer_slot is not {reviewer_slot}")
            if view is None:
                errors.append(f"records[{index}].question_id is outside the diagnostic allocation")
            else:
                if record.get("question") != view["question"]:
                    errors.append(f"records[{index}].question differs from the exact view")
                if record.get("question_view_sha256") != canonical_json_sha256(view):
                    errors.append(f"records[{index}].question_view_sha256 is invalid")
        per_record.append(sorted(set(errors)))
    checks = _checks(records, per_record, "stage1_question_only_free_observation")
    all_errors = sorted(set(global_errors + [e for row in per_record for e in row]))
    return records, checks, all_errors


def validate_annotation_records(
    path: Path, stage1_path: Path, reviewer_slot: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    _, views, _ = validate_contract()
    ids, by_id = _view_maps(views)
    stage1, _, stage1_errors = validate_stage1_records(stage1_path, reviewer_slot)
    stage1_by_id = {
        record["question_id"]: record for record in stage1 if isinstance(record, dict)
    }
    records = list(iter_json_records(path))
    global_errors = [f"stage1: {error}" for error in stage1_errors]
    if len(records) != 30:
        global_errors.append("annotation file must contain exactly 30 records")
    if [r.get("question_id") for r in records if isinstance(r, dict)] != ids:
        global_errors.append("annotation records do not match the exact 30-question order")
    validator = _schema_validator(ANNOTATION_SCHEMA_PATH)
    per_record: list[list[str]] = []
    for index, record in enumerate(records):
        label = f"records[{index}]"
        errors = _schema_errors(validator, record, label)
        if isinstance(record, dict):
            qid = record.get("question_id")
            view = by_id.get(qid) if isinstance(qid, str) else None
            observation = stage1_by_id.get(qid) if isinstance(qid, str) else None
            if record.get("reviewer_slot") != reviewer_slot:
                errors.append(f"{label}.reviewer_slot is not {reviewer_slot}")
            if view is None:
                errors.append(f"{label}.question_id is outside the diagnostic allocation")
            else:
                if record.get("question") != view["question"]:
                    errors.append(f"{label}.question differs from the exact view")
                if record.get("question_view_sha256") != canonical_json_sha256(view):
                    errors.append(f"{label}.question_view_sha256 is invalid")
            if observation is None:
                errors.append(f"{label} has no bound stage-1 observation")
            else:
                if record.get("stage1_observation_sha256") != canonical_json_sha256(observation):
                    errors.append(f"{label}.stage1_observation_sha256 is invalid")
                payload = record.get("semantic_payload")
                if isinstance(payload, dict) and (
                    payload.get("unconstrained_question_paraphrase")
                    != observation.get("free_observation")
                ):
                    errors.append(f"{label} does not preserve the frozen stage-1 observation")
            payload = record.get("semantic_payload")
            if isinstance(payload, dict):
                contaminated = forbidden_key_paths(payload)
                if contaminated:
                    errors.append(f"{label} contains forbidden later-layer keys: {contaminated[:20]!r}")
                if isinstance(record.get("question"), str):
                    errors.extend(cue_errors(payload, record["question"], f"{label}.semantic_payload"))
                structural_payload = dict(payload)
                structural_payload["submission_status"] = "annotated"
                errors.extend(structural_errors(structural_payload, f"{label}.semantic_payload"))
        per_record.append(sorted(set(errors)))
    checks = _checks(records, per_record, "stage2_linked_semantic_representation")
    all_errors = sorted(set(global_errors + [e for row in per_record for e in row]))
    return records, checks, all_errors


def _side_is_reviewer_01(question_id: str) -> bool:
    digest = hashlib.sha256((RUN_ID + question_id).encode("utf-8")).digest()
    return digest[0] % 2 == 0


def build_alignment_packet(
    reviewer_01_records: list[dict[str, Any]],
    reviewer_02_records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_01 = {record["question_id"]: record for record in reviewer_01_records}
    by_02 = {record["question_id"]: record for record in reviewer_02_records}
    _, views, _ = validate_contract()
    packet: list[dict[str, Any]] = []
    side_map: list[dict[str, Any]] = []
    for view in views:
        qid = view["question_id"]
        first, second = by_01[qid], by_02[qid]
        if _side_is_reviewer_01(qid):
            left, right = first, second
            left_slot, right_slot = REVIEWER_SLOTS
        else:
            left, right = second, first
            left_slot, right_slot = REVIEWER_SLOTS[::-1]
        mapping = {
            "run_id": RUN_ID,
            "question_id": qid,
            "left_reviewer_slot": left_slot,
            "right_reviewer_slot": right_slot,
            "left_annotation_sha256": canonical_json_sha256(left),
            "right_annotation_sha256": canonical_json_sha256(right),
        }
        side_map.append(mapping)
        packet.append(
            {
                "schema_version": "ai_question_structure_blinded_alignment_input_v0_1",
                "run_id": RUN_ID,
                "question_id": qid,
                "question": view["question"],
                "side_assignment_sha256": canonical_json_sha256(mapping),
                "left": {
                    "source_annotation_sha256": mapping["left_annotation_sha256"],
                    "semantic_payload": left["semantic_payload"],
                },
                "right": {
                    "source_annotation_sha256": mapping["right_annotation_sha256"],
                    "semantic_payload": right["semantic_payload"],
                },
            }
        )
    return packet, side_map


def _item_ids(packet_record: dict[str, Any], side: str, layer: str) -> list[str]:
    payload = packet_record[side]["semantic_payload"]
    if layer == "required_information_unit":
        return [
            item["unit_id"]
            for item in payload["semantic_skeleton"]["required_information_units"]
        ]
    if layer == "obligation":
        return [item["obligation_id"] for item in payload["information_obligations"]]
    if layer == "topology_node":
        return [item["node_id"] for item in payload["abstract_topology"]["nodes"]]
    raise AssertionError(layer)


def _coverage_errors(
    alignment: dict[str, Any], packet_record: dict[str, Any], layer: str
) -> list[str]:
    groups = alignment.get(f"{layer}_groups")
    unmatched = alignment.get(f"{layer}_unmatched_items")
    if not isinstance(groups, list) or not isinstance(unmatched, list):
        return []
    errors: list[str] = []
    group_ids = [g.get("group_id") for g in groups if isinstance(g, dict)]
    if len(group_ids) != len(groups) or len(set(group_ids)) != len(group_ids):
        errors.append(f"{layer} group IDs are invalid or duplicated")
    for side in ("left", "right"):
        expected = _item_ids(packet_record, side, layer)
        observed: list[str] = []
        for group in groups:
            if isinstance(group, dict) and isinstance(group.get(f"{side}_ids"), list):
                observed.extend(group[f"{side}_ids"])
        observed.extend(
            item.get("item_id")
            for item in unmatched
            if isinstance(item, dict) and item.get("side") == side
        )
        if Counter(observed) != Counter(expected):
            errors.append(
                f"{layer} {side} coverage is not exhaustive and exactly-once: "
                f"expected={expected!r}, observed={observed!r}"
            )
    return errors


def validate_alignment_records(
    path: Path, packet_path: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    _, views, _ = validate_contract()
    ids, _ = _view_maps(views)
    packet = list(iter_json_records(packet_path))
    records = list(iter_json_records(path))
    global_errors: list[str] = []
    if len(packet) != 30 or [item.get("question_id") for item in packet] != ids:
        global_errors.append("alignment packet is not the exact 30-question projection")
    if len(records) != 30 or [item.get("question_id") for item in records] != ids:
        global_errors.append("alignment output is not in the exact 30-question order")
    packet_by_id = {item.get("question_id"): item for item in packet if isinstance(item, dict)}
    validator = _schema_validator(ALIGNMENT_SCHEMA_PATH)
    per_record: list[list[str]] = []
    for index, record in enumerate(records):
        label = f"records[{index}]"
        errors = _schema_errors(validator, record, label)
        if isinstance(record, dict):
            packet_record = packet_by_id.get(record.get("question_id"))
            if packet_record is None:
                errors.append(f"{label} has no alignment packet record")
            else:
                if record.get("alignment_packet_record_sha256") != canonical_json_sha256(packet_record):
                    errors.append(f"{label}.alignment_packet_record_sha256 is invalid")
                for layer in ("required_information_unit", "obligation", "topology_node"):
                    errors.extend(_coverage_errors(record, packet_record, layer))
        per_record.append(sorted(set(errors)))
    checks = _checks(records, per_record, "blinded_ai_semantic_alignment")
    all_errors = sorted(set(global_errors + [e for row in per_record for e in row]))
    return records, checks, all_errors


def _dag_errors(topology: dict[str, Any], label: str) -> list[str]:
    nodes = topology.get("nodes")
    if not isinstance(nodes, list):
        return [f"{label}.nodes must be an array"]
    ids = [node.get("node_id") for node in nodes if isinstance(node, dict)]
    if len(ids) != len(nodes) or len(set(ids)) != len(ids):
        return [f"{label}.node IDs are invalid or duplicated"]
    known = set(ids)
    dependencies: dict[str, list[str]] = {}
    errors: list[str] = []
    for node in nodes:
        deps = node.get("depends_on")
        if not isinstance(deps, list):
            errors.append(f"{label}.{node.get('node_id')}.depends_on must be an array")
            deps = []
        dependencies[node["node_id"]] = deps
        if node["node_id"] in deps:
            errors.append(f"{label}.{node['node_id']} has a self dependency")
        for dep in deps:
            if dep not in known:
                errors.append(f"{label}.{node['node_id']} references missing dependency {dep!r}")
    state: dict[str, int] = {}

    def visit(node_id: str) -> None:
        if state.get(node_id) == 1:
            errors.append(f"{label} contains a cycle")
            return
        if state.get(node_id) == 2:
            return
        state[node_id] = 1
        for dep in dependencies.get(node_id, []):
            if dep in known:
                visit(dep)
        state[node_id] = 2

    for node_id in ids:
        visit(node_id)
    roots = {node_id for node_id in ids if not dependencies.get(node_id)}
    depended_on = {dep for deps in dependencies.values() for dep in deps}
    sinks = known - depended_on
    if set(topology.get("entry_node_ids", [])) != roots:
        errors.append(f"{label}.entry_node_ids is not the exact root set")
    if set(topology.get("output_node_ids", [])) != sinks:
        errors.append(f"{label}.output_node_ids is not the exact sink set")
    return sorted(set(errors))


def _topology_cue_errors(topology: dict[str, Any], question: str, label: str) -> list[str]:
    errors: list[str] = []
    for index, node in enumerate(topology.get("nodes", [])):
        if not isinstance(node, dict):
            continue
        cues = node.get("source_cues")
        implicit = node.get("implicit_rationale")
        if isinstance(cues, list):
            for cue_index, cue in enumerate(cues):
                if not isinstance(cue, str) or not cue or cue not in question:
                    errors.append(
                        f"{label}.nodes[{index}].source_cues[{cue_index}] is not an exact question substring"
                    )
            if cues and implicit is not None:
                errors.append(f"{label}.nodes[{index}].implicit_rationale must be null with cues")
            if not cues and (not isinstance(implicit, str) or not implicit.strip()):
                errors.append(f"{label}.nodes[{index}].implicit_rationale is required without cues")
    return errors


def validate_topology_records(
    path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    plan, views, _ = validate_contract()
    holdout_ids = [
        qid
        for batch in plan["batches"]
        if batch["diagnostic_role"] == "shadow_holdout"
        for qid in batch["question_ids"]
    ]
    by_id = {view["question_id"]: view for view in views}
    records = list(iter_json_records(path))
    global_errors: list[str] = []
    if len(records) != 20 or [r.get("question_id") for r in records if isinstance(r, dict)] != holdout_ids:
        global_errors.append("independent topology output must contain the exact 20 hold-out questions")
    validator = _schema_validator(TOPOLOGY_SCHEMA_PATH)
    per_record: list[list[str]] = []
    for index, record in enumerate(records):
        label = f"records[{index}]"
        errors = _schema_errors(validator, record, label)
        if isinstance(record, dict):
            view = by_id.get(record.get("question_id"))
            if view is None:
                errors.append(f"{label}.question_id is outside the hold-out allocation")
            else:
                if record.get("question") != view["question"]:
                    errors.append(f"{label}.question differs from the exact view")
                if record.get("question_view_sha256") != canonical_json_sha256(view):
                    errors.append(f"{label}.question_view_sha256 is invalid")
                errors.extend(_topology_cue_errors(record, view["question"], label))
            errors.extend(_dag_errors(record, label))
            alternatives = record.get("alternative_topologies")
            if isinstance(alternatives, list):
                plan_ids = [item.get("plan_id") for item in alternatives if isinstance(item, dict)]
                if len(plan_ids) != len(alternatives) or len(set(plan_ids)) != len(plan_ids):
                    errors.append(f"{label}.alternative topology IDs are invalid")
                for alt_index, alternative in enumerate(alternatives):
                    if isinstance(alternative, dict) and isinstance(alternative.get("topology"), dict):
                        alt = alternative["topology"]
                        errors.extend(_dag_errors(alt, f"{label}.alternative_topologies[{alt_index}]"))
                        errors.extend(
                            _topology_cue_errors(
                                alt,
                                record.get("question", ""),
                                f"{label}.alternative_topologies[{alt_index}]",
                            )
                        )
        per_record.append(sorted(set(errors)))
    checks = _checks(records, per_record, "independent_question_only_topology")
    all_errors = sorted(set(global_errors + [e for row in per_record for e in row]))
    return records, checks, all_errors


def graph_invariants(topology: dict[str, Any], *, id_key: str = "node_id") -> dict[str, Any]:
    nodes = topology.get("nodes", [])
    ids = [node[id_key] for node in nodes]
    deps = {node[id_key]: list(node.get("depends_on", [])) for node in nodes}
    children = {node_id: [] for node_id in ids}
    for node_id, dependencies in deps.items():
        for dep in dependencies:
            if dep in children:
                children[dep].append(node_id)
    memo: dict[str, int] = {}

    def depth(node_id: str) -> int:
        if node_id not in memo:
            memo[node_id] = 1 + max((depth(dep) for dep in deps[node_id]), default=0)
        return memo[node_id]

    longest = max((depth(node_id) for node_id in ids), default=0)
    roots = sum(not deps[node_id] for node_id in ids)
    sinks = sum(not children[node_id] for node_id in ids)
    return {
        "node_count": len(ids),
        "edge_count": sum(len(value) for value in deps.values()),
        "root_count": roots,
        "sink_count": sinks,
        "longest_path_node_count": longest,
        "branch_present": any(len(children[node_id]) > 1 for node_id in ids),
        "join_present": any(len(deps[node_id]) > 1 for node_id in ids),
    }


def _mapped_graph_metrics(packet_record: dict[str, Any], alignment: dict[str, Any]) -> dict[str, Any]:
    groups = alignment["topology_node_groups"]
    maps = {"left": {}, "right": {}}
    for group in groups:
        for side in ("left", "right"):
            for node_id in group[f"{side}_ids"]:
                maps[side][node_id] = group["group_id"]
    edge_sets: dict[str, set[tuple[str, str]]] = {}
    reachable_sets: dict[str, set[tuple[str, str]]] = {}
    root_sets: dict[str, set[str]] = {}
    sink_sets: dict[str, set[str]] = {}
    alignable_edge_counts: dict[str, int] = {}
    total_edge_counts: dict[str, int] = {}
    collapsed_counts: dict[str, int] = {}
    for side in ("left", "right"):
        topology = packet_record[side]["semantic_payload"]["abstract_topology"]
        raw_edges = {
            (dependency, node["node_id"])
            for node in topology["nodes"]
            for dependency in node["depends_on"]
        }
        total_edge_counts[side] = len(raw_edges)
        projected: set[tuple[str, str]] = set()
        collapsed = 0
        alignable = 0
        for source, target in raw_edges:
            if source in maps[side] and target in maps[side]:
                alignable += 1
                pair = (maps[side][source], maps[side][target])
                if pair[0] == pair[1]:
                    collapsed += 1
                else:
                    projected.add(pair)
        edge_sets[side] = projected
        alignable_edge_counts[side] = alignable
        collapsed_counts[side] = collapsed
        nodes = {group_id for pair in projected for group_id in pair} | set(maps[side].values())
        closure = set(projected)
        changed = True
        while changed:
            changed = False
            for first in list(closure):
                for second in list(closure):
                    if first[1] == second[0] and first[0] != second[1]:
                        pair = (first[0], second[1])
                        if pair not in closure:
                            closure.add(pair)
                            changed = True
        reachable_sets[side] = closure
        targets = {target for _, target in projected}
        sources = {source for source, _ in projected}
        root_sets[side] = nodes - targets
        sink_sets[side] = nodes - sources

    def dice(first: set[Any], second: set[Any]) -> tuple[float, bool]:
        if not first and not second:
            return 1.0, True
        return 2 * len(first & second) / (len(first) + len(second)), False

    def jaccard(first: set[Any], second: set[Any]) -> float:
        union = first | second
        return 1.0 if not union else len(first & second) / len(union)

    edge_dice, edge_joint_empty = dice(edge_sets["left"], edge_sets["right"])
    reach_dice, reach_joint_empty = dice(reachable_sets["left"], reachable_sets["right"])
    return {
        "left_total_edges": total_edge_counts["left"],
        "right_total_edges": total_edge_counts["right"],
        "left_endpoint_alignable_edge_rate": (
            alignable_edge_counts["left"] / total_edge_counts["left"]
            if total_edge_counts["left"]
            else 1.0
        ),
        "right_endpoint_alignable_edge_rate": (
            alignable_edge_counts["right"] / total_edge_counts["right"]
            if total_edge_counts["right"]
            else 1.0
        ),
        "projected_direct_edge_dice": edge_dice,
        "projected_direct_edges_joint_empty": edge_joint_empty,
        "projected_reachability_dice": reach_dice,
        "projected_reachability_joint_empty": reach_joint_empty,
        "mapped_root_jaccard": jaccard(root_sets["left"], root_sets["right"]),
        "mapped_sink_jaccard": jaccard(sink_sets["left"], sink_sets["right"]),
        "left_collapsed_within_group_edges": collapsed_counts["left"],
        "right_collapsed_within_group_edges": collapsed_counts["right"],
    }


def _question_disposition(
    alignment: dict[str, Any], graph_metrics: dict[str, Any]
) -> str:
    decisions = list(alignment["component_decisions"].values())
    groups = [
        *alignment["required_information_unit_groups"],
        *alignment["obligation_groups"],
        *alignment["topology_node_groups"],
    ]
    unmatched = [
        *alignment["required_information_unit_unmatched_items"],
        *alignment["obligation_unmatched_items"],
        *alignment["topology_node_unmatched_items"],
    ]
    statuses = [item["status"] for item in decisions + groups]
    if "unresolved" in statuses or any(item["reason"] == "cannot_align" for item in unmatched):
        return "INDETERMINATE"
    if any(
        item["status"] == "substantive_conflict" and item.get("impact", "material") == "material"
        for item in groups
    ) or any(item["impact"] == "material" for item in unmatched):
        return "SUBSTANTIVE_DISAGREEMENT"
    full = (
        all(status == "equivalent" for status in statuses)
        and not unmatched
        and all(len(group["left_ids"]) == len(group["right_ids"]) == 1 for group in groups)
        and graph_metrics["projected_reachability_dice"] == 1.0
        and graph_metrics["mapped_root_jaccard"] == 1.0
        and graph_metrics["mapped_sink_jaccard"] == 1.0
    )
    return "FULL_EQUIVALENCE" if full else "COMPATIBLE_VARIATION"


def _layer_coverage(alignment: dict[str, Any], layer: str) -> dict[str, Any]:
    groups = alignment[f"{layer}_groups"]
    unmatched = alignment[f"{layer}_unmatched_items"]
    result: dict[str, Any] = {}
    for side in ("left", "right"):
        total = sum(len(group[f"{side}_ids"]) for group in groups) + sum(
            item["side"] == side for item in unmatched
        )
        strict = sum(
            len(group[f"{side}_ids"])
            for group in groups
            if group["status"] == "equivalent"
        )
        compatible = sum(
            len(group[f"{side}_ids"])
            for group in groups
            if group["status"] in {"equivalent", "compatible_split_merge"}
        )
        result[f"{side}_item_count"] = total
        result[f"{side}_strict_coverage"] = strict / total if total else 1.0
        result[f"{side}_compatible_coverage"] = compatible / total if total else 1.0
    for kind in ("strict", "compatible"):
        left = result[f"left_{kind}_coverage"]
        right = result[f"right_{kind}_coverage"]
        result[f"symmetric_{kind}_coverage"] = (
            1.0 if left == right == 1.0 else (0.0 if left + right == 0 else 2 * left * right / (left + right))
        )
    result["unmatched_item_count"] = len(unmatched)
    result["material_unmatched_item_count"] = sum(item["impact"] == "material" for item in unmatched)
    result["split_merge_group_count"] = sum(group["status"] == "compatible_split_merge" for group in groups)
    result["partial_overlap_group_count"] = sum(group["status"] == "partial_overlap" for group in groups)
    result["conflict_group_count"] = sum(group["status"] == "substantive_conflict" for group in groups)
    return result


def _mean(values: Iterable[float]) -> float | None:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else None


def _aggregate_subset(per_question: list[dict[str, Any]], ids: set[str]) -> dict[str, Any]:
    selected = [item for item in per_question if item["question_id"] in ids]
    return {
        "question_count": len(selected),
        "disposition_counts": dict(sorted(Counter(item["disposition"] for item in selected).items())),
        "compatible_or_full_question_rate": (
            sum(item["disposition"] in {"FULL_EQUIVALENCE", "COMPATIBLE_VARIATION"} for item in selected)
            / len(selected)
            if selected
            else None
        ),
        "mean_projected_direct_edge_dice": _mean(
            item["graph_metrics"]["projected_direct_edge_dice"] for item in selected
        ),
        "mean_projected_reachability_dice": _mean(
            item["graph_metrics"]["projected_reachability_dice"] for item in selected
        ),
        "mean_obligation_symmetric_compatible_coverage": _mean(
            item["layer_coverage"]["obligation"]["symmetric_compatible_coverage"]
            for item in selected
        ),
        "mean_topology_node_symmetric_compatible_coverage": _mean(
            item["layer_coverage"]["topology_node"]["symmetric_compatible_coverage"]
            for item in selected
        ),
    }


def _categorical_pair_metrics(
    reviewer_01: dict[str, dict[str, Any]], reviewer_02: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    extractors = {
        "representation_outcome": lambda r: r["semantic_payload"]["representation_assessment"]["outcome"],
        "selection_requirement_present": lambda r: r["semantic_payload"]["semantic_skeleton"]["selection_requirement"] is not None,
        "back_mapping_requirement_present": lambda r: r["semantic_payload"]["semantic_skeleton"]["back_mapping_requirement"] is not None,
        "ambiguity_present": lambda r: r["semantic_payload"]["ambiguity"]["present"],
        "alternative_plan_present": lambda r: bool(r["semantic_payload"]["alternative_topology_plans"]),
    }
    output: dict[str, Any] = {}
    for name, extractor in extractors.items():
        matches = sum(extractor(reviewer_01[qid]) == extractor(reviewer_02[qid]) for qid in reviewer_01)
        output[name] = {"exact_match_count": matches, "question_count": len(reviewer_01), "rate": matches / len(reviewer_01)}
    return output


def _structural_comparison(
    topology_records: list[dict[str, Any]],
    reviewer_01: dict[str, dict[str, Any]],
    reviewer_02: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    for independent in topology_records:
        qid = independent["question_id"]
        target = graph_invariants(independent)
        record: dict[str, Any] = {"question_id": qid, "independent": target}
        for label, source in (("reviewer_01", reviewer_01[qid]), ("reviewer_02", reviewer_02[qid])):
            stats = graph_invariants(source["semantic_payload"]["abstract_topology"])
            record[label] = stats
            record[f"{label}_signature_exact"] = stats == target
        pairs.append(record)
    summary: dict[str, Any] = {"question_count": len(pairs), "per_question": pairs}
    numeric = ("node_count", "edge_count", "root_count", "sink_count", "longest_path_node_count")
    boolean = ("branch_present", "join_present")
    for reviewer in ("reviewer_01", "reviewer_02"):
        summary[reviewer] = {
            "exact_signature_rate": _mean(float(item[f"{reviewer}_signature_exact"]) for item in pairs),
            "mean_absolute_difference": {
                key: _mean(abs(item[reviewer][key] - item["independent"][key]) for item in pairs)
                for key in numeric
            },
            "boolean_exact_match_rate": {
                key: _mean(float(item[reviewer][key] == item["independent"][key]) for item in pairs)
                for key in boolean
            },
        }
    return summary


def _downstream_preview(topology_records: list[dict[str, Any]]) -> dict[str, Any]:
    representations = list(iter_json_records(REPRESENTATIONS_PATH))
    checks = list(iter_json_records(GRANULARITY_CHECKS_PATH))
    by_qid = {record["question_id"]: record for record in representations}
    comparisons: dict[str, list[dict[str, Any]]] = {name: [] for name in ("coarse", "medium", "fine")}
    for independent in topology_records:
        qid = independent["question_id"]
        independent_stats = graph_invariants(independent)
        for granularity in comparisons:
            proposal = by_qid[qid]["representations"][granularity]["topology"]
            proposal_stats = graph_invariants(proposal, id_key="id")
            comparisons[granularity].append(
                {
                    "question_id": qid,
                    "independent": independent_stats,
                    "proposal": proposal_stats,
                    "signature_exact": independent_stats == proposal_stats,
                }
            )
    summary: dict[str, Any] = {}
    for granularity, items in comparisons.items():
        summary[granularity] = {
            "question_count": len(items),
            "exact_structural_signature_rate": _mean(float(item["signature_exact"]) for item in items),
            "mean_absolute_node_count_difference": _mean(
                abs(item["proposal"]["node_count"] - item["independent"]["node_count"])
                for item in items
            ),
            "mean_absolute_depth_difference": _mean(
                abs(
                    item["proposal"]["longest_path_node_count"]
                    - item["independent"]["longest_path_node_count"]
                )
                for item in items
            ),
        }
    return {
        "preserved_representation_artifact": {
            "path": str(REPRESENTATIONS_PATH.relative_to(ROOT)),
            "sha256": sha256_file(REPRESENTATIONS_PATH),
            "record_count": len(representations),
            "status": "preexisting_llm_proposed_deferred_phase_b_evidence_unchanged",
        },
        "preserved_deterministic_checks_artifact": {
            "path": str(GRANULARITY_CHECKS_PATH.relative_to(ROOT)),
            "sha256": sha256_file(GRANULARITY_CHECKS_PATH),
            "record_count": len(checks),
            "passing_check_count": sum(item.get("status") == "pass" for item in checks),
        },
        "preserved_metrics_artifact": {
            "path": str(GRANULARITY_METRICS_PATH.relative_to(ROOT)),
            "sha256": sha256_file(GRANULARITY_METRICS_PATH),
        },
        "structural_only_comparison": summary,
        "phase_b_human_review_performed": False,
        "phase_c_grounding_or_execution_performed": False,
        "semantic_plan_correctness_evaluated": False,
    }


def build_metrics(
    reviewer_01_records: list[dict[str, Any]],
    reviewer_02_records: list[dict[str, Any]],
    packet: list[dict[str, Any]],
    alignments: list[dict[str, Any]],
    topology_records: list[dict[str, Any]],
) -> dict[str, Any]:
    plan, _, _ = validate_contract()
    by_packet = {record["question_id"]: record for record in packet}
    by_01 = {record["question_id"]: record for record in reviewer_01_records}
    by_02 = {record["question_id"]: record for record in reviewer_02_records}
    per_question: list[dict[str, Any]] = []
    component_counts: Counter[str] = Counter()
    for alignment in alignments:
        qid = alignment["question_id"]
        graph_metrics = _mapped_graph_metrics(by_packet[qid], alignment)
        layer_coverage = {
            layer: _layer_coverage(alignment, layer)
            for layer in ("required_information_unit", "obligation", "topology_node")
        }
        for name, decision in alignment["component_decisions"].items():
            component_counts[f"{name}:{decision['status']}"] += 1
        per_question.append(
            {
                "question_id": qid,
                "disposition": _question_disposition(alignment, graph_metrics),
                "layer_coverage": layer_coverage,
                "graph_metrics": graph_metrics,
            }
        )
    calibration_ids = set(plan["batches"][0]["question_ids"])
    holdout_ids = {
        qid
        for batch in plan["batches"]
        if batch["diagnostic_role"] == "shadow_holdout"
        for qid in batch["question_ids"]
    }
    raw_quality: dict[str, Any] = {}
    for slot, records in ((REVIEWER_SLOTS[0], reviewer_01_records), (REVIEWER_SLOTS[1], reviewer_02_records)):
        raw_quality[slot] = {
            "record_count": len(records),
            "complete_count": sum(
                r["semantic_payload"]["representation_assessment"]["outcome"] == "complete"
                for r in records
            ),
            "schema_gap_count": sum(
                r["semantic_payload"]["representation_assessment"]["outcome"] == "incomplete_schema_gap"
                for r in records
            ),
            "not_annotatable_count": sum(
                r["semantic_payload"]["representation_assessment"]["outcome"] == "not_annotatable"
                for r in records
            ),
            "instrument_issue_count": sum(len(r["semantic_payload"]["instrument_issues"]) for r in records),
        }
    return {
        "schema_version": "ai_question_structure_pipeline_diagnostic_metrics_v0_1",
        "run_id": RUN_ID,
        "evidence_class": "non_evidentiary_ai_shadow_pipeline",
        "pipeline_execution_status": "complete",
        "scientific_gate_status": "NOT_EVALUATED_AI_SUBSTITUTE",
        "raw_integrity": {
            "expected_stage1_record_count": 60,
            "observed_stage1_record_count": 60,
            "expected_structured_record_count": 60,
            "observed_structured_record_count": 60,
            "schema_hash_cue_reference_and_dag_validation": "pass",
            "reviewer_quality": raw_quality,
        },
        "categorical_pair_metrics": _categorical_pair_metrics(by_01, by_02),
        "alignment": {
            "semantic_judgment_source": "separate_ai_alignment_assistant",
            "determinism_scope": "metrics_are_deterministic_conditional_on_the_frozen_ai_crosswalk",
            "component_status_counts": dict(sorted(component_counts.items())),
            "all_questions": _aggregate_subset(per_question, set(by_01)),
            "calibration": _aggregate_subset(per_question, calibration_ids),
            "shadow_holdout": _aggregate_subset(per_question, holdout_ids),
            "per_question": per_question,
        },
        "independent_topology": {
            "interpretation": "descriptive_structure_only_not_semantic_prediction_or_execution",
            **_structural_comparison(topology_records, by_01, by_02),
        },
        "downstream_connector_preview": _downstream_preview(topology_records),
        "canonical_research_status": {
            "human_evidence_count": 0,
            "human_agreement_observation_count": 0,
            "phase_a1_pass_claimed": False,
            "phase_a2_entry_claimed": False,
            "phase_b_entry_claimed": False,
            "gold_claimed": False,
            "modeling_ready_claimed": False,
            "common_executable_graph_claimed": False,
            "grounding_or_execution_evaluated": False,
            "current_scientific_decision": "UNDECIDED_NEEDS_ANNOTATION_EVIDENCE",
        },
        "limitations": [
            "Both reviewers are AI invocations from one model family; statistical independence is not claimed.",
            "Context isolation and absence of other-output consultation are procedural, not machine-authenticated.",
            "Semantic alignment is another AI judgment and is not human agreement or correctness.",
            "The shadow hold-out continues by design even if calibration concordance is low; it is not Phase A2 evidence.",
            "Independent topology comparison uses graph invariants without semantic node alignment.",
            "No answer, grounding, executable graph, or execution result is evaluated in this diagnostic.",
        ],
    }


def render_report(metrics: dict[str, Any]) -> str:
    alignment = metrics["alignment"]
    calibration = alignment["calibration"]
    holdout = alignment["shadow_holdout"]
    dispositions = alignment["all_questions"]["disposition_counts"]
    topology = metrics["independent_topology"]
    downstream = metrics["downstream_connector_preview"]
    lines = [
        "# AI question-structure shadow-pipeline analysis v0.1",
        "",
        "## Outcome",
        "",
        "The non-evidentiary diagnostic pipeline completed end to end. This is an engineering rehearsal, not a scientific phase pass. The canonical human lane still has zero records and the project decision remains `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`.",
        "",
        "## Raw collection and integrity",
        "",
        f"- Two AI reviewer files contain {metrics['raw_integrity']['observed_structured_record_count']} structured records in total, plus 60 frozen stage-1 observations.",
        "- Schema, source-view hash, stage-1 binding, cue, reference, root/sink, obligation-coverage, and DAG checks passed.",
        "- The reviewer contexts were procedurally separated; neither human nor statistical independence is claimed.",
        "",
        "## Blinded alignment diagnostic",
        "",
        f"- Question dispositions across all 30: `{json.dumps(dispositions, sort_keys=True)}`.",
        f"- Calibration compatible-or-full rate: `{calibration['compatible_or_full_question_rate']}` over {calibration['question_count']} questions.",
        f"- Shadow hold-out compatible-or-full rate: `{holdout['compatible_or_full_question_rate']}` over {holdout['question_count']} questions.",
        f"- Calibration mean reachability Dice: `{calibration['mean_projected_reachability_dice']}`; shadow hold-out: `{holdout['mean_projected_reachability_dice']}`.",
        "- These values are deterministic only conditional on the frozen third-AI semantic crosswalk. They do not measure correctness.",
        "",
        "## Independent topology-only diagnostic",
        "",
        f"- A fresh topology-only pass produced {topology['question_count']} held-out DAGs without upstream structure, environment, answers, or operator proposals.",
        f"- Exact full structural-signature rate versus reviewer 1: `{topology['reviewer_01']['exact_signature_rate']}`; versus reviewer 2: `{topology['reviewer_02']['exact_signature_rate']}`.",
        "- This checks structural stability only; it is not evidence that question structure predicts an executable graph.",
        "",
        "## Downstream connector preview",
        "",
        f"- The preserved Phase B proposal artifact remains unchanged with {downstream['preserved_representation_artifact']['record_count']} records.",
        f"- Its deterministic check artifact contains {downstream['preserved_deterministic_checks_artifact']['passing_check_count']} passing checks.",
        "- Coarse/medium/fine comparisons here use only graph-size/depth/branch/join invariants. No Phase B human judgment was performed.",
        "- Phase C grounding and execution were not run because this diagnostic intentionally exposes no answers or executable grounding references.",
        "",
        "## Scientific status after the rehearsal",
        "",
        "- Human evidence: 0",
        "- Human agreement observations: 0",
        "- Phase A1 pass: not claimed",
        "- Phase A2 entry: not authorized",
        "- Phase B entry: not authorized",
        "- Gold/modeling-ready/common executable graph: not claimed",
        "- Grounding/execution success: not evaluated",
        "",
        "The next canonical task therefore remains two approved, mutually independent, exposure-naive real humans annotating the first ten-question batch. The diagnostic artifacts can be used to inspect and debug pipeline mechanics only.",
    ]
    return "\n".join(lines) + "\n"


def _write_checks(path: Path, checks: list[dict[str, Any]], overwrite: bool) -> None:
    write_output_batch({"checks": (path, jsonl_file_bytes(checks))}, overwrite=overwrite)


def _fail(errors: list[str]) -> int:
    for error in errors[:100]:
        print(f"[FAIL] {error}", file=sys.stderr)
    if len(errors) > 100:
        print(f"[FAIL] {len(errors) - 100} additional errors omitted", file=sys.stderr)
    return 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("validate-stage1", "validate-annotations"):
        sub = subparsers.add_parser(name)
        sub.add_argument("input", type=Path)
        sub.add_argument("--reviewer-slot", choices=REVIEWER_SLOTS, required=True)
        if name == "validate-annotations":
            sub.add_argument("--stage1", type=Path, required=True)
        sub.add_argument("--checks-output", type=Path, required=True)
        sub.add_argument("--overwrite", action="store_true")
    build = subparsers.add_parser("build-alignment-packet")
    build.add_argument("--reviewer-01", type=Path, required=True)
    build.add_argument("--reviewer-01-stage1", type=Path, required=True)
    build.add_argument("--reviewer-02", type=Path, required=True)
    build.add_argument("--reviewer-02-stage1", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--side-map-output", type=Path, required=True)
    build.add_argument("--overwrite", action="store_true")
    align = subparsers.add_parser("validate-alignments")
    align.add_argument("input", type=Path)
    align.add_argument("--packet", type=Path, required=True)
    align.add_argument("--checks-output", type=Path, required=True)
    align.add_argument("--overwrite", action="store_true")
    topology = subparsers.add_parser("validate-topology")
    topology.add_argument("input", type=Path)
    topology.add_argument("--checks-output", type=Path, required=True)
    topology.add_argument("--overwrite", action="store_true")
    summary = subparsers.add_parser("summarize")
    summary.add_argument("--reviewer-01", type=Path, required=True)
    summary.add_argument("--reviewer-01-stage1", type=Path, required=True)
    summary.add_argument("--reviewer-02", type=Path, required=True)
    summary.add_argument("--reviewer-02-stage1", type=Path, required=True)
    summary.add_argument("--alignment-packet", type=Path, required=True)
    summary.add_argument("--alignments", type=Path, required=True)
    summary.add_argument("--topology", type=Path, required=True)
    summary.add_argument("--metrics-output", type=Path, required=True)
    summary.add_argument("--report-output", type=Path, required=True)
    summary.add_argument("--manifest-output", type=Path, required=True)
    summary.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        validate_contract()
        if args.command == "validate-stage1":
            _, checks, errors = validate_stage1_records(args.input, args.reviewer_slot)
            _write_checks(args.checks_output, checks, args.overwrite)
            if errors:
                return _fail(errors)
            print(f"PASS stage1 records=30 reviewer={args.reviewer_slot}")
            return 0
        if args.command == "validate-annotations":
            _, checks, errors = validate_annotation_records(
                args.input, args.stage1, args.reviewer_slot
            )
            _write_checks(args.checks_output, checks, args.overwrite)
            if errors:
                return _fail(errors)
            print(f"PASS annotations=30 reviewer={args.reviewer_slot}")
            return 0
        if args.command == "build-alignment-packet":
            first, _, errors_01 = validate_annotation_records(
                args.reviewer_01, args.reviewer_01_stage1, REVIEWER_SLOTS[0]
            )
            second, _, errors_02 = validate_annotation_records(
                args.reviewer_02, args.reviewer_02_stage1, REVIEWER_SLOTS[1]
            )
            errors = errors_01 + errors_02
            if errors:
                return _fail(errors)
            packet, side_map = build_alignment_packet(first, second)
            write_output_batch(
                {
                    "alignment_packet": (args.output, jsonl_file_bytes(packet)),
                    "side_map": (args.side_map_output, jsonl_file_bytes(side_map)),
                },
                overwrite=args.overwrite,
            )
            print("PASS alignment packet records=30")
            return 0
        if args.command == "validate-alignments":
            _, checks, errors = validate_alignment_records(args.input, args.packet)
            _write_checks(args.checks_output, checks, args.overwrite)
            if errors:
                return _fail(errors)
            print("PASS alignment records=30")
            return 0
        if args.command == "validate-topology":
            _, checks, errors = validate_topology_records(args.input)
            _write_checks(args.checks_output, checks, args.overwrite)
            if errors:
                return _fail(errors)
            print("PASS independent topology records=20")
            return 0
        if args.command == "summarize":
            first, _, errors_01 = validate_annotation_records(
                args.reviewer_01, args.reviewer_01_stage1, REVIEWER_SLOTS[0]
            )
            second, _, errors_02 = validate_annotation_records(
                args.reviewer_02, args.reviewer_02_stage1, REVIEWER_SLOTS[1]
            )
            alignments, _, alignment_errors = validate_alignment_records(
                args.alignments, args.alignment_packet
            )
            topology_records, _, topology_errors = validate_topology_records(args.topology)
            errors = errors_01 + errors_02 + alignment_errors + topology_errors
            if errors:
                return _fail(errors)
            packet = list(iter_json_records(args.alignment_packet))
            metrics = build_metrics(first, second, packet, alignments, topology_records)
            report = render_report(metrics).encode("utf-8")
            artifact_inputs = {
                "reviewer_01_stage1": args.reviewer_01_stage1,
                "reviewer_01_annotations": args.reviewer_01,
                "reviewer_02_stage1": args.reviewer_02_stage1,
                "reviewer_02_annotations": args.reviewer_02,
                "alignment_packet": args.alignment_packet,
                "alignments": args.alignments,
                "independent_topology": args.topology,
            }
            metrics_bytes = json_file_bytes(metrics)
            manifest = {
                "schema_version": "ai_question_structure_pipeline_diagnostic_run_manifest_v0_1",
                "run_id": RUN_ID,
                "run_status": "complete",
                "tool_version": TOOL_VERSION,
                "contract_freeze_commit": _git_contract_commit(),
                "contract_plan": {
                    "repository_relative_path": str(PLAN_PATH.relative_to(ROOT)),
                    "sha256": sha256_file(PLAN_PATH),
                },
                "inputs": {
                    label: {
                        "repository_relative_path": str(path.resolve().relative_to(ROOT.resolve())),
                        "sha256": sha256_file(path),
                        "record_count": len(list(iter_json_records(path))),
                    }
                    for label, path in artifact_inputs.items()
                },
                "outputs": {
                    "metrics": {
                        "repository_relative_path": str(args.metrics_output.resolve().relative_to(ROOT.resolve())),
                        "sha256": hashlib.sha256(metrics_bytes).hexdigest(),
                    },
                    "report": {
                        "repository_relative_path": str(args.report_output.resolve().relative_to(ROOT.resolve())),
                        "sha256": hashlib.sha256(report).hexdigest(),
                    },
                },
                "model_provenance": {
                    "reviewer_model_id": "codex_gpt-5",
                    "aligner_model_id": "codex_gpt-5",
                    "topology_model_id": "codex_gpt-5",
                    "exact_revision_status": "revision_not_exposed",
                    "seed_status": "not_supported",
                    "separate_raw_response_status": "structured_artifacts_are_primary_capture_no_separate_raw_responses",
                },
                "canonical_effects": metrics["canonical_research_status"],
            }
            write_output_batch(
                {
                    "metrics": (args.metrics_output, metrics_bytes),
                    "report": (args.report_output, report),
                    "manifest": (args.manifest_output, json_file_bytes(manifest)),
                },
                overwrite=args.overwrite,
            )
            print("PASS diagnostic summary complete")
            return 0
    except (ContractError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
