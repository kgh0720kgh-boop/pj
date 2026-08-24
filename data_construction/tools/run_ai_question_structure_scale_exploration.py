#!/usr/bin/env python3
"""Validate, canonicalize, and analyze the N=100 scale-first AI exploration."""

from __future__ import annotations

import argparse
import itertools
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
    sha256_file,
    write_output_batch,
)
from validate_question_structure_annotations import cue_errors, forbidden_key_paths


TOOL_VERSION = "ai_question_structure_scale_exploration_tool_v0_1"
RUN_ID = "ai_question_structure_scale_v0_1_run_001"
SCHEMA_VERSION = "question_only_semantic_backbone_ai_v0_1"
CHECK_SCHEMA_VERSION = "ai_question_structure_scale_check_v0_1"
EVIDENCE_CLASS = "ai_exploratory_non_human_non_gold"
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
PLAN_PATH = BASE / "contracts/exploration_plan_v0_1.json"
SCHEMA_PATH = BASE / "contracts/semantic_backbone_record_schema_v0_1.json"
VIEWS_PATH = BASE / "pool/question_only_views_n100.jsonl"
POOL_MANIFEST_PATH = ROOT / "data_construction/manifests/ai_question_structure_exploratory_pool_v0_1.json"
DEFAULT_RECORDS = BASE / "run_001/records.jsonl"
DEFAULT_CHECKS = BASE / "run_001/checks.jsonl"
DEFAULT_SIGNATURES = BASE / "run_001/analysis/derived_signatures_v0_1.jsonl"
DEFAULT_METRICS = BASE / "run_001/analysis/structural_saturation_metrics_v0_1.json"
DEFAULT_REPORT = BASE / "run_001/analysis/structural_saturation_report_v0_1.md"
DEFAULT_EXPOSURE = ROOT / "data_construction/manifests/question_exposure_ledger_v0_1.json"
DEFAULT_RUN_MANIFEST = BASE / "run_001/run_manifest.json"
ROLE_VALUES = {
    "RESOLVE_REFERENT",
    "ACQUIRE_PROPERTY",
    "COMPARE",
    "AGGREGATE",
    "ORDER_OR_EXTREMUM",
    "DERIVE",
    "VERIFY",
    "COMBINE",
    "OTHER",
}
SIGNATURE_KINDS = (
    "fine_semantic_dag",
    "contracted_semantic_dag",
    "topology_shape",
    "task",
)


class ExplorationContractError(ValueError):
    """Raised when a frozen exploration contract is invalid."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="+", type=Path, help="One or more ordered JSONL parts")
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--views", type=Path, default=VIEWS_PATH)
    parser.add_argument("--pool-manifest", type=Path, default=POOL_MANIFEST_PATH)
    parser.add_argument("--records-output", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--checks-output", type=Path, default=DEFAULT_CHECKS)
    parser.add_argument("--signatures-output", type=Path, default=DEFAULT_SIGNATURES)
    parser.add_argument("--metrics-output", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--exposure-output", type=Path, default=DEFAULT_EXPOSURE)
    parser.add_argument("--run-manifest-output", type=Path, default=DEFAULT_RUN_MANIFEST)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def _schema_validator(schema_path: Path) -> Any:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - preflight covers dependency
        raise ExplorationContractError("jsonschema is required") from exc
    schema = read_json(schema_path)
    validator_class = getattr(jsonschema, "Draft202012Validator", None)
    if validator_class is None:
        raise ExplorationContractError("Draft 2020-12 validation is unavailable")
    validator_class.check_schema(schema)
    return validator_class(schema, format_checker=jsonschema.FormatChecker())


def _schema_errors(validator: Any, record: Any, label: str) -> list[str]:
    errors: list[str] = []
    for error in sorted(
        validator.iter_errors(record),
        key=lambda item: [str(part) for part in item.absolute_path],
    ):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"{label}.{location}: {error.message}")
    return errors


def _require_artifact(path: Path, expected_sha256: str, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise ExplorationContractError(f"bound {label} is missing or symlinked: {path}")
    observed = sha256_file(path)
    if observed != expected_sha256:
        raise ExplorationContractError(
            f"bound {label} hash mismatch: expected {expected_sha256}, observed {observed}"
        )


def validate_contract(
    plan_path: Path = PLAN_PATH,
    schema_path: Path = SCHEMA_PATH,
    views_path: Path = VIEWS_PATH,
    pool_manifest_path: Path = POOL_MANIFEST_PATH,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    for path, label in (
        (plan_path, "plan"),
        (schema_path, "record schema"),
        (views_path, "question-only views"),
        (pool_manifest_path, "pool manifest"),
    ):
        if path.is_symlink() or not path.is_file():
            raise ExplorationContractError(f"{label} is missing or symlinked: {path}")
    plan = read_json(plan_path)
    if not isinstance(plan, dict) or (
        plan.get("schema_version") != "ai_question_structure_scale_exploration_plan_v0_1"
        or plan.get("run_id") != RUN_ID
        or plan.get("status") != "contract_frozen_before_model_outputs"
    ):
        raise ExplorationContractError("unsupported exploration plan identity/status")
    bound_paths: set[str] = set()
    for section in ("source_artifacts", "contract_artifacts"):
        artifacts = plan.get(section)
        if not isinstance(artifacts, list) or not artifacts:
            raise ExplorationContractError(f"plan {section} must be nonempty")
        for item in artifacts:
            if not isinstance(item, dict):
                raise ExplorationContractError(f"plan {section} contains a non-object")
            relative = item.get("repository_relative_path")
            expected = item.get("sha256")
            if not isinstance(relative, str) or not isinstance(expected, str):
                raise ExplorationContractError(f"plan {section} has an invalid binding")
            _require_artifact(ROOT / relative, expected, relative)
            bound_paths.add(relative)
    expected_bound = {
        schema_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        views_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        pool_manifest_path.resolve().relative_to(ROOT.resolve()).as_posix(),
    }
    if not expected_bound.issubset(bound_paths):
        raise ExplorationContractError("plan does not bind schema, views, and pool manifest")
    _schema_validator(schema_path)
    views = list(iter_json_records(views_path))
    planned_ids = plan.get("question_ids")
    if (
        len(views) != 100
        or not isinstance(planned_ids, list)
        or len(planned_ids) != 100
        or len(set(planned_ids)) != 100
        or [view.get("question_id") for view in views] != planned_ids
    ):
        raise ExplorationContractError("plan and views do not share the exact 100-question order")
    allowed_view_keys = {"schema_version", "visibility", "question_id", "question"}
    for index, view in enumerate(views):
        if set(view) != allowed_view_keys:
            raise ExplorationContractError(f"view {index} is not the exact four-field projection")
        if (
            view.get("schema_version") != "question_only_semantic_view_v0_1"
            or view.get("visibility") != "question_only_no_environment_answer_or_proposals"
            or not isinstance(view.get("question"), str)
            or not view["question"].strip()
        ):
            raise ExplorationContractError(f"view {index} violates question-only identity")
    pool = read_json(pool_manifest_path)
    selection = pool.get("selection") if isinstance(pool, dict) else None
    if (
        not isinstance(pool, dict)
        or pool.get("schema_version")
        != "ai_question_structure_exploration_pool_manifest_v0_1"
        or not isinstance(selection, dict)
        or selection.get("selected_question_ids") != planned_ids
        or selection.get("selected_count") != 100
        or selection.get("preserved_prefix_count") != 30
        or selection.get("added_count") != 70
        or selection.get("unexposed_unallocated_reserve_count") != 3266
        or pool.get("artifacts", {}).get("views", {}).get("sha256") != sha256_file(views_path)
    ):
        raise ExplorationContractError("pool manifest does not bind the exact N=100 views")
    return plan, views, pool


def _dependency_map(graph: dict[str, Any]) -> tuple[list[str], dict[str, str], set[tuple[str, str]]]:
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        return [], {}, set()
    identifiers: list[str] = []
    labels: dict[str, str] = {}
    edges: set[tuple[str, str]] = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("node_id"), str):
            continue
        node_id = node["node_id"]
        identifiers.append(node_id)
        labels[node_id] = str(node.get("role"))
        dependencies = node.get("depends_on")
        if isinstance(dependencies, list):
            edges.update((dependency, node_id) for dependency in dependencies if isinstance(dependency, str))
    return identifiers, labels, edges


def graph_errors(graph: Any, label: str) -> list[str]:
    if not isinstance(graph, dict):
        return [f"{label} must be an object"]
    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return [f"{label}.nodes must be a nonempty array"]
    identifiers, labels, edges = _dependency_map(graph)
    errors: list[str] = []
    if len(identifiers) != len(nodes):
        errors.append(f"{label}.nodes contains a non-object or missing node_id")
    if len(set(identifiers)) != len(identifiers):
        errors.append(f"{label}.node IDs are not unique")
    known = set(identifiers)
    for source, target in edges:
        if source not in known:
            errors.append(f"{label}: missing dependency {source!r}")
        if source == target:
            errors.append(f"{label}: self dependency on {source!r}")
    for node_id, role in labels.items():
        if role not in ROLE_VALUES:
            errors.append(f"{label}.{node_id}: unknown semantic role {role!r}")

    children: dict[str, set[str]] = {node_id: set() for node_id in known}
    parents: dict[str, set[str]] = {node_id: set() for node_id in known}
    for source, target in edges:
        if source in known and target in known:
            children[source].add(target)
            parents[target].add(source)
    state: dict[str, int] = {}

    def visit(node_id: str) -> None:
        if state.get(node_id) == 1:
            errors.append(f"{label}: dependency graph contains a cycle")
            return
        if state.get(node_id) == 2:
            return
        state[node_id] = 1
        for child in children[node_id]:
            visit(child)
        state[node_id] = 2

    for node_id in identifiers:
        visit(node_id)
    roots = {node_id for node_id in known if not parents[node_id]}
    sinks = {node_id for node_id in known if not children[node_id]}
    entries = graph.get("entry_node_ids")
    outputs = graph.get("output_node_ids")
    if not isinstance(entries, list) or len(entries) != len(set(entries)) or set(entries) != roots:
        errors.append(f"{label}.entry_node_ids is not the exact root set")
    if not isinstance(outputs, list) or len(outputs) != len(set(outputs)) or set(outputs) != sinks:
        errors.append(f"{label}.output_node_ids is not the exact sink set")
    for node_id in known:
        stack = [node_id]
        seen: set[str] = set()
        reaches_sink = False
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            if current in sinks:
                reaches_sink = True
                break
            stack.extend(children[current])
        if not reaches_sink:
            errors.append(f"{label}.{node_id} does not reach an output")
    return sorted(set(errors))


def _reachable(
    source: str,
    target: str,
    edges: set[tuple[str, str]],
    *,
    excluded: tuple[str, str] | None = None,
) -> bool:
    children: dict[str, set[str]] = defaultdict(set)
    for edge_source, edge_target in edges:
        if excluded is not None and (edge_source, edge_target) == excluded:
            continue
        children[edge_source].add(edge_target)
    stack = [source]
    seen: set[str] = set()
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        for child in children[current]:
            if child == target:
                return True
            stack.append(child)
    return False


def transitive_reduction(edges: set[tuple[str, str]]) -> set[tuple[str, str]]:
    return {
        edge
        for edge in edges
        if not _reachable(edge[0], edge[1], edges, excluded=edge)
    }


def _canonical_serialization_from_parts(
    labels: dict[str, str], edges: set[tuple[str, str]]
) -> dict[str, Any]:
    reduced = transitive_reduction(edges)
    groups: list[tuple[str, list[str]]] = []
    for label in sorted(set(labels.values())):
        groups.append((label, sorted(node for node, value in labels.items() if value == label)))
    permutations_by_group = [list(itertools.permutations(nodes)) for _, nodes in groups]
    best_text: str | None = None
    best_value: dict[str, Any] | None = None
    for choices in itertools.product(*permutations_by_group):
        ordered_nodes = [node for group in choices for node in group]
        index = {node: position for position, node in enumerate(ordered_nodes)}
        value = {
            "labels": [labels[node] for node in ordered_nodes],
            "edges": sorted([[index[source], index[target]] for source, target in reduced]),
        }
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if best_text is None or text < best_text:
            best_text = text
            best_value = value
    if best_value is None:
        raise ValueError("cannot canonicalize an empty graph")
    return best_value


def _contract_same_role_linear(
    labels: dict[str, str], edges: set[tuple[str, str]]
) -> tuple[dict[str, str], set[tuple[str, str]]]:
    labels = dict(labels)
    edges = set(edges)
    while True:
        indegree = Counter(target for _, target in edges)
        outdegree = Counter(source for source, _ in edges)
        candidates = sorted(
            (source, target)
            for source, target in edges
            if labels[source] == labels[target]
            and outdegree[source] == 1
            and indegree[target] == 1
        )
        if not candidates:
            break
        source, target = candidates[0]
        merged = source + "|" + target
        merged_edges: set[tuple[str, str]] = set()
        for edge_source, edge_target in edges:
            if (edge_source, edge_target) == (source, target):
                continue
            new_source = merged if edge_source in {source, target} else edge_source
            new_target = merged if edge_target in {source, target} else edge_target
            if new_source != new_target:
                merged_edges.add((new_source, new_target))
        role = labels[source]
        del labels[source]
        del labels[target]
        labels[merged] = role
        edges = merged_edges
    return labels, edges


def canonical_graph(graph: dict[str, Any], mode: str) -> dict[str, Any]:
    _, labels, edges = _dependency_map(graph)
    if mode == "topology":
        labels = {node_id: "NODE" for node_id in labels}
    elif mode == "contracted":
        labels, edges = _contract_same_role_linear(labels, edges)
    elif mode != "fine":
        raise ValueError(f"unsupported canonicalization mode: {mode}")
    return _canonical_serialization_from_parts(labels, edges)


def signature_bundle(record: dict[str, Any]) -> dict[str, Any]:
    graph = record.get("primary_graph")
    if not isinstance(graph, dict):
        return {
            "question_id": record.get("question_id"),
            "representable": False,
            "signatures": {kind: None for kind in SIGNATURE_KINDS},
            "canonical": {kind: None for kind in SIGNATURE_KINDS},
        }
    fine = canonical_graph(graph, "fine")
    contracted = canonical_graph(graph, "contracted")
    topology = canonical_graph(graph, "topology")
    answer = record["answer_spec"]
    task = {
        "answer_kind": answer["kind"],
        "answer_cardinality": answer["cardinality"],
        "graph": fine,
    }
    canonical = {
        "fine_semantic_dag": fine,
        "contracted_semantic_dag": contracted,
        "topology_shape": topology,
        "task": task,
    }
    return {
        "question_id": record["question_id"],
        "representable": True,
        "signatures": {kind: canonical_json_sha256(value) for kind, value in canonical.items()},
        "canonical": canonical,
    }


def validate_records(
    records: list[Any],
    views: list[dict[str, Any]],
    schema_path: Path = SCHEMA_PATH,
) -> tuple[list[dict[str, Any]], list[str]]:
    validator = _schema_validator(schema_path)
    expected_ids = [view["question_id"] for view in views]
    view_by_id = {view["question_id"]: view for view in views}
    global_errors: list[str] = []
    observed_ids = [record.get("question_id") for record in records if isinstance(record, dict)]
    if len(records) != 100:
        global_errors.append(f"records must contain exactly 100 objects, observed {len(records)}")
    if observed_ids != expected_ids:
        global_errors.append("records do not match the exact 100-question order")
    if len(set(value for value in observed_ids if isinstance(value, str))) != len(observed_ids):
        global_errors.append("record question IDs are not unique")

    checks: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        label = f"records[{index}]"
        errors = _schema_errors(validator, record, label)
        if isinstance(record, dict):
            question_id = record.get("question_id")
            view = view_by_id.get(question_id) if isinstance(question_id, str) else None
            if view is None:
                errors.append(f"{label}.question_id is outside the frozen pool")
            else:
                if record.get("question") != view["question"]:
                    errors.append(f"{label}.question differs from the exact view")
                if record.get("question_view_sha256") != canonical_json_sha256(view):
                    errors.append(f"{label}.question_view_sha256 is invalid")
            contaminated = forbidden_key_paths(record)
            if contaminated:
                errors.append(f"{label} contains forbidden later-layer keys: {contaminated[:20]!r}")
            question = record.get("question")
            if isinstance(question, str):
                errors.extend(cue_errors(record, question, label))
            primary = record.get("primary_graph")
            if isinstance(primary, dict):
                errors.extend(graph_errors(primary, f"{label}.primary_graph"))
                try:
                    primary_signature = canonical_json_sha256(canonical_graph(primary, "fine"))
                except (KeyError, ValueError) as exc:
                    errors.append(f"{label}.primary_graph canonicalization failed: {exc}")
                    primary_signature = None
                alternatives = record.get("alternative_graphs")
                alternative_ids: list[str] = []
                alternative_signatures: list[str] = []
                if isinstance(alternatives, list):
                    for alt_index, alternative in enumerate(alternatives):
                        if not isinstance(alternative, dict):
                            continue
                        alternative_ids.append(str(alternative.get("alternative_id")))
                        graph = alternative.get("graph")
                        errors.extend(graph_errors(graph, f"{label}.alternative_graphs[{alt_index}].graph"))
                        if isinstance(graph, dict):
                            try:
                                alt_signature = canonical_json_sha256(canonical_graph(graph, "fine"))
                                alternative_signatures.append(alt_signature)
                                if primary_signature == alt_signature:
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
                "question_id": record.get("question_id") if isinstance(record, dict) else None,
                "status": "pass" if not errors else "fail",
                "errors": errors,
            }
        )
    all_errors = sorted(set(global_errors + [error for check in checks for error in check["errors"]]))
    if global_errors:
        checks.append(
            {
                "schema_version": CHECK_SCHEMA_VERSION,
                "tool_version": TOOL_VERSION,
                "record_index": None,
                "question_id": None,
                "status": "fail",
                "errors": sorted(set(global_errors)),
            }
        )
    return checks, all_errors


def _graph_depth(graph: dict[str, Any]) -> int:
    identifiers, _, edges = _dependency_map(graph)
    parents: dict[str, set[str]] = {node_id: set() for node_id in identifiers}
    for source, target in edges:
        parents[target].add(source)
    memo: dict[str, int] = {}

    def depth(node_id: str) -> int:
        if node_id not in memo:
            memo[node_id] = 1 + max((depth(parent) for parent in parents[node_id]), default=0)
        return memo[node_id]

    return max((depth(node_id) for node_id in identifiers), default=0)


def _family_metrics(signatures: list[str | None], block_size: int = 10) -> dict[str, Any]:
    valid = [value for value in signatures if isinstance(value, str)]
    counts = Counter(valid)
    total = len(valid)
    ordered_counts = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    cumulative: list[dict[str, Any]] = []
    seen: set[str] = set()
    valid_seen = 0
    for index, signature in enumerate(signatures, start=1):
        if isinstance(signature, str):
            valid_seen += 1
            seen.add(signature)
        if index % block_size == 0 or index == len(signatures):
            cumulative.append(
                {
                    "questions_seen": index,
                    "representable_seen": valid_seen,
                    "observed_family_count": len(seen),
                }
            )
    blocks: list[dict[str, Any]] = []
    previously_seen: set[str] = set()
    for start in range(0, len(signatures), block_size):
        block = signatures[start : start + block_size]
        valid_block = [value for value in block if isinstance(value, str)]
        novel_questions = [value for value in valid_block if value not in previously_seen]
        new_families = set(novel_questions)
        blocks.append(
            {
                "positions": [start + 1, min(start + block_size, len(signatures))],
                "representable_questions": len(valid_block),
                "new_family_count": len(new_families),
                "questions_in_previously_unseen_families": len(novel_questions),
                "question_novelty_rate": (
                    len(novel_questions) / len(valid_block) if valid_block else None
                ),
            }
        )
        previously_seen.update(valid_block)
    coverage: dict[str, float | None] = {}
    for k in (1, 5, 10, 20):
        coverage[f"top_{k}"] = (
            sum(count for _, count in ordered_counts[:k]) / total if total else None
        )
    singleton_count = sum(1 for count in counts.values() if count == 1)
    doubleton_count = sum(1 for count in counts.values() if count == 2)
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
    prefix = {value for value in signatures[:30] if isinstance(value, str)}
    expansion = [value for value in signatures[30:] if isinstance(value, str)]
    return {
        "question_count": len(signatures),
        "representable_count": total,
        "observed_family_count": len(counts),
        "singleton_family_count": singleton_count,
        "doubleton_family_count": doubleton_count,
        "singleton_question_mass": singleton_count / total if total else None,
        "good_turing_unseen_mass_diagnostic": singleton_count / total if total else None,
        "top_k_question_coverage": coverage,
        "cumulative_curve_committed_order": cumulative,
        "block_novelty_committed_order": blocks,
        "exact_rarefaction_order_independent": rarefaction,
        "new_70_transfer": {
            "representable_count": len(expansion),
            "questions_in_families_seen_in_first_30": sum(value in prefix for value in expansion),
            "questions_in_families_unseen_in_first_30": sum(value not in prefix for value in expansion),
            "transfer_rate": (
                sum(value in prefix for value in expansion) / len(expansion) if expansion else None
            ),
            "new_family_count": len(set(expansion) - prefix),
        },
        "families": [
            {"signature": signature, "question_count": count}
            for signature, count in ordered_counts
        ],
    }


def build_metrics(
    records: list[dict[str, Any]], derived: list[dict[str, Any]]
) -> dict[str, Any]:
    signatures_by_kind = {
        kind: [item["signatures"][kind] for item in derived] for kind in SIGNATURE_KINDS
    }
    family_metrics = {
        kind: _family_metrics(signatures) for kind, signatures in signatures_by_kind.items()
    }
    role_counts: Counter[str] = Counter()
    transition_counts: Counter[str] = Counter()
    node_counts: list[int] = []
    edge_counts: list[int] = []
    depths: list[int] = []
    branch_questions = 0
    join_questions = 0
    other_questions = 0
    for record in records:
        graph = record.get("primary_graph")
        if not isinstance(graph, dict):
            continue
        identifiers, labels, edges = _dependency_map(graph)
        node_counts.append(len(identifiers))
        edge_counts.append(len(edges))
        depths.append(_graph_depth(graph))
        role_counts.update(labels.values())
        transition_counts.update(f"{labels[source]}->{labels[target]}" for source, target in edges)
        outdegree = Counter(source for source, _ in edges)
        indegree = Counter(target for _, target in edges)
        branch_questions += any(value > 1 for value in outdegree.values())
        join_questions += any(value > 1 for value in indegree.values())
        other_questions += "OTHER" in labels.values()
    statuses = Counter(record["status"] for record in records)
    uncertainty_count = sum(record["uncertainty"]["present"] for record in records)
    alternative_count = sum(bool(record["alternative_graphs"]) for record in records)
    fine_signatures = signatures_by_kind["fine_semantic_dag"]
    contracted_signatures = signatures_by_kind["contracted_semantic_dag"]
    known_fine = {value for value in fine_signatures[:30] if isinstance(value, str)}
    known_contracted = {
        value for value in contracted_signatures[:30] if isinstance(value, str)
    }
    novel_fine_indexes = [
        index
        for index, value in enumerate(fine_signatures[30:], start=30)
        if isinstance(value, str) and value not in known_fine
    ]
    known_after_contraction = sum(
        contracted_signatures[index] in known_contracted for index in novel_fine_indexes
    )
    canonical_examples: dict[str, list[dict[str, Any]]] = {}
    for kind in SIGNATURE_KINDS:
        by_signature: dict[str, dict[str, Any]] = {}
        example_ids: dict[str, list[str]] = defaultdict(list)
        for record, item in zip(records, derived):
            signature = item["signatures"][kind]
            if not isinstance(signature, str):
                continue
            by_signature.setdefault(signature, item["canonical"][kind])
            if len(example_ids[signature]) < 3:
                example_ids[signature].append(record["question_id"])
        canonical_examples[kind] = [
            {
                "signature": family["signature"],
                "question_count": family["question_count"],
                "canonical": by_signature[family["signature"]],
                "example_question_ids": example_ids[family["signature"]],
            }
            for family in family_metrics[kind]["families"][:20]
        ]
    return {
        "schema_version": "ai_question_structure_scale_structural_saturation_metrics_v0_1",
        "run_id": RUN_ID,
        "evidence_class": EVIDENCE_CLASS,
        "question_count": len(records),
        "prefix_contract_development_count": 30,
        "new_expansion_count": 70,
        "validation": {
            "valid_record_count": len(records),
            "invalid_record_count": 0,
            "human_evidence_count": 0,
            "gold_claimed": False,
            "semantic_correctness_evaluated": False,
            "grounding_or_execution_evaluated": False,
        },
        "record_status_counts": dict(sorted(statuses.items())),
        "uncertainty": {
            "question_count": uncertainty_count,
            "rate": uncertainty_count / len(records),
        },
        "alternative_graphs": {
            "question_count": alternative_count,
            "rate": alternative_count / len(records),
        },
        "provisional_role_escape_hatch": {
            "other_node_count": role_counts["OTHER"],
            "other_question_count": other_questions,
            "other_question_rate": other_questions / len(records),
        },
        "graph_structure": {
            "representable_question_count": len(node_counts),
            "node_count_mean": statistics.mean(node_counts) if node_counts else None,
            "node_count_median": statistics.median(node_counts) if node_counts else None,
            "node_count_min": min(node_counts) if node_counts else None,
            "node_count_max": max(node_counts) if node_counts else None,
            "edge_count_mean": statistics.mean(edge_counts) if edge_counts else None,
            "depth_mean": statistics.mean(depths) if depths else None,
            "depth_max": max(depths) if depths else None,
            "branch_question_count": branch_questions,
            "join_question_count": join_questions,
        },
        "semantic_role_counts": dict(sorted(role_counts.items())),
        "directed_role_transition_counts": dict(sorted(transition_counts.items())),
        "signature_definitions": {
            "fine_semantic_dag": "transitively_reduced_exact_ID_invariant_labeled_DAG",
            "contracted_semantic_dag": "fine_graph_after_maximal_same_role_linear_contraction",
            "topology_shape": "transitively_reduced_exact_ID_invariant_unlabeled_DAG",
            "task": "fine_semantic_DAG_plus_answer_kind_and_cardinality",
        },
        "family_metrics": family_metrics,
        "split_merge_sensitivity": {
            "new_70_questions_with_fine_signature_unseen_in_first_30": len(novel_fine_indexes),
            "of_those_with_contracted_signature_seen_in_first_30": known_after_contraction,
            "rate": known_after_contraction / len(novel_fine_indexes) if novel_fine_indexes else None,
        },
        "top_family_examples": canonical_examples,
        "interpretation_boundary": {
            "supported": [
                "recurrence_under_the_frozen_question_only_AI_extractor",
                "exact_and_split_merge_tolerant_signature_coverage",
                "descriptive_N100_saturation_and_new70_transfer",
            ],
            "unsupported": [
                "semantic_correctness",
                "human_agreement",
                "gold_annotation",
                "universal_semantic_topology",
                "common_executable_graph",
                "operator_vocabulary_selection",
                "grounding_or_answer_accuracy",
                "modeling_readiness",
            ],
        },
    }


def render_report(metrics: dict[str, Any]) -> str:
    lines = [
        "# N=100 question-only semantic-backbone exploration",
        "",
        "Evidence class: AI-generated exploratory, non-human, non-gold.",
        "",
        "## Mechanical result",
        "",
        f"- Valid records: {metrics['validation']['valid_record_count']}/100",
        f"- Status counts: `{json.dumps(metrics['record_status_counts'], sort_keys=True)}`",
        f"- Provisional `OTHER` role: {metrics['provisional_role_escape_hatch']['other_question_count']}/100 questions",
        f"- Uncertainty marked: {metrics['uncertainty']['question_count']}/100 questions",
        f"- Alternative graph present: {metrics['alternative_graphs']['question_count']}/100 questions",
        "",
        "## Recurrence at four resolutions",
        "",
        "| Signature | Families | Singleton mass | Top-10 coverage | New-70 transfer from first 30 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for kind in SIGNATURE_KINDS:
        value = metrics["family_metrics"][kind]
        lines.append(
            "| "
            + kind
            + f" | {value['observed_family_count']}"
            + f" | {value['singleton_question_mass']:.3f}"
            + f" | {value['top_k_question_coverage']['top_10']:.3f}"
            + f" | {value['new_70_transfer']['transfer_rate']:.3f} |"
        )
    lines.extend(
        [
            "",
            "The four resolutions must be interpreted together. Fine labeled recurrence is strict; contracted recurrence tolerates same-role linear split/merge; topology recurrence ignores semantic labels; task recurrence additionally includes answer kind and cardinality.",
            "",
            "## Graph profile",
            "",
            f"- Mean nodes: {metrics['graph_structure']['node_count_mean']:.3f}",
            f"- Mean edges: {metrics['graph_structure']['edge_count_mean']:.3f}",
            f"- Mean depth: {metrics['graph_structure']['depth_mean']:.3f}",
            f"- Branch questions: {metrics['graph_structure']['branch_question_count']}/100",
            f"- Join questions: {metrics['graph_structure']['join_question_count']}/100",
            "",
            "## Scientific boundary",
            "",
            "This run measures recurrence and curve shape under one frozen AI extractor and deterministic normalizer. N=100 may show that a curve is flattening or not flattening; it cannot establish universal saturation. It evaluates no factual answer, environment realization, grounding, execution, human agreement, or semantic correctness.",
            "",
            "The next decision is based on the new-70 novelty curves, singleton mass, `OTHER` rate, and split/merge sensitivity: expand unchanged to N=300 if material recurring families are still appearing; otherwise freeze a candidate backbone library and begin representative environment realization while preserving an untouched reserve.",
            "",
        ]
    )
    return "\n".join(lines)


def _git_contract_commit(plan_path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", str(plan_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    commit = result.stdout.strip()
    return commit if len(commit) == 40 else "contract_not_committed"


def build_exposure_ledger(
    plan: dict[str, Any], pool: dict[str, Any], records: list[dict[str, Any]]
) -> dict[str, Any]:
    selected_ids = [record["question_id"] for record in records]
    return {
        "schema_version": "question_exposure_ledger_v0_1",
        "dataset": "HybridQA",
        "source_split": "dev",
        "status": "complete_through_ai_question_structure_scale_v0_1_run_001",
        "historical_exposure": {
            "manifest": "data_construction/manifests/historical_exposed_ids.json",
            "count": 100,
            "future_training_allowed": False,
            "future_unseen_evaluation_allowed": False,
        },
        "ai_question_structure_exploration": {
            "pool_manifest": "data_construction/manifests/ai_question_structure_exploratory_pool_v0_1.json",
            "run_id": RUN_ID,
            "question_ids": selected_ids,
            "question_ids_ordered_sha256": canonical_json_sha256(selected_ids),
            "count": len(selected_ids),
            "prior_diagnostic_prefix_count": 30,
            "newly_processed_count": 70,
            "processing_status": "complete_one_ai_record_per_question",
            "future_unseen_evaluation_allowed": False,
            "corpus_role_allocated": False,
        },
        "unexposed_unallocated_reserve": {
            "count": pool["selection"]["unexposed_unallocated_reserve_count"],
            "question_id_set_sha256": pool["selection"]["reserve_question_ids_set_sha256"],
            "question_text_materialized": False,
            "role_allocated": False,
        },
        "partition_check": pool["partition_check"],
        "evidence_boundary": {
            "human_evidence_count": 0,
            "gold_claimed": False,
            "semantic_correctness_claimed": False,
            "unseen_evaluation_exclusion_is_exposure_accounting_not_correctness": True,
        },
        "contract_plan_sha256": sha256_file(PLAN_PATH),
        "contract_freeze_commit": _git_contract_commit(PLAN_PATH),
    }


def build_run_manifest(
    *,
    plan: dict[str, Any],
    records_path: Path,
    checks_path: Path,
    signatures_path: Path,
    metrics_path: Path,
    report_path: Path,
    exposure_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "ai_question_structure_scale_run_manifest_v0_1",
        "run_id": RUN_ID,
        "run_status": "complete",
        "evidence_class": EVIDENCE_CLASS,
        "contract_freeze_commit": _git_contract_commit(PLAN_PATH),
        "contract_plan": {
            "repository_relative_path": PLAN_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(PLAN_PATH),
        },
        "model_provenance": {
            "producer_kind": "ai_model",
            "model_id": "codex_gpt-5",
            "exact_revision_status": "revision_not_exposed",
            "seed_status": "not_supported",
            "generation_interface": "codex_subagent_partitioned_single_record_per_question",
            "raw_response_status": "structured_JSONL_parts_are_primary_capture_no_separate_raw_response",
            "multi_reviewer_agreement_claimed": False,
        },
        "input_scope": {
            "question_count": 100,
            "visible_fields": ["schema_version", "visibility", "question_id", "question"],
            "environment_answer_grounding_or_other_record_exposed": False,
        },
        "outputs": {
            "records": _artifact(records_path, 100),
            "checks": _artifact(checks_path, 100),
            "derived_signatures": _artifact(signatures_path, 100),
            "metrics": _artifact(metrics_path),
            "report": _artifact(report_path),
            "exposure_ledger": _artifact(exposure_path),
        },
        "canonical_effects": {
            "human_evidence_count": 0,
            "gold_claimed": False,
            "semantic_correctness_claimed": False,
            "human_agreement_claimed": False,
            "universal_semantic_graph_claimed": False,
            "common_executable_graph_claimed": False,
            "grounding_or_execution_evaluated": False,
            "modeling_ready_claimed": False,
        },
        "tool_version": TOOL_VERSION,
    }


def _artifact(path: Path, record_count: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "repository_relative_path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "sha256": sha256_file(path),
    }
    if record_count is not None:
        value["record_count"] = record_count
    return value


def main() -> int:
    args = parse_args()
    try:
        plan, views, pool = validate_contract(
            args.plan, args.schema, args.views, args.pool_manifest
        )
        records: list[dict[str, Any]] = []
        for path in args.records:
            if path.is_symlink() or not path.is_file():
                raise ExplorationContractError(f"records part is missing or symlinked: {path}")
            records.extend(iter_json_records(path))
        checks, errors = validate_records(records, views, args.schema)
        if errors:
            print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False), file=sys.stderr)
            return 1
        if args.validate_only:
            print(json.dumps({"status": "pass", "records": len(records)}, sort_keys=True))
            return 0

        derived = [signature_bundle(record) for record in records]
        metrics = build_metrics(records, derived)
        report_bytes = render_report(metrics).encode("utf-8")
        exposure = build_exposure_ledger(plan, pool, records)
        outputs_without_manifest = {
            "records": (args.records_output, jsonl_file_bytes(records)),
            "checks": (args.checks_output, jsonl_file_bytes(checks)),
            "signatures": (args.signatures_output, jsonl_file_bytes(derived)),
            "metrics": (args.metrics_output, json_file_bytes(metrics)),
            "report": (args.report_output, report_bytes),
            "exposure": (args.exposure_output, json_file_bytes(exposure)),
        }
        write_output_batch(outputs_without_manifest, overwrite=args.overwrite)
        run_manifest = build_run_manifest(
            plan=plan,
            records_path=args.records_output,
            checks_path=args.checks_output,
            signatures_path=args.signatures_output,
            metrics_path=args.metrics_output,
            report_path=args.report_output,
            exposure_path=args.exposure_output,
        )
        statuses = write_output_batch(
            {"run_manifest": (args.run_manifest_output, json_file_bytes(run_manifest))},
            overwrite=args.overwrite,
        )
        print(
            json.dumps(
                {
                    "status": "pass",
                    "records": len(records),
                    "families": {
                        kind: metrics["family_metrics"][kind]["observed_family_count"]
                        for kind in SIGNATURE_KINDS
                    },
                    "run_manifest": statuses["run_manifest"],
                },
                sort_keys=True,
            )
        )
        return 0
    except (ExplorationContractError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
