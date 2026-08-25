#!/usr/bin/env python3
"""Build a reversible, label-free two-layer operator normalization.

The semantic layer canonicalizes the target backbone under alpha-renaming,
independent node ordering, and transitive reduction.  The adapter layer retains
typed unresolved-slot, access-placement, fused/explicit-access, and output
arity information.  Free-text labels/descriptions, question/environment text,
answers, E1 judgments, grounding, execution, and vocabularies are excluded.
"""

from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

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
    stable_rank,
    write_output_batch,
)


TOOL_VERSION = "operator_equivalence_normalizer_v0_1"
PLAN_SCHEMA_VERSION = "operator_equivalence_normalization_plan_v0_1"
PLAN_ID = "hybridqa_operator_equivalence_normalization_plan_v0_1"
RUN_ID = "hybridqa_operator_equivalence_normalization_v0_1_run_001"
PROJECTION_SCHEMA_VERSION = "operator_equivalence_structural_projection_v0_1"
NORMALIZATION_SCHEMA_VERSION = "operator_equivalence_normalization_v0_1"
EXPECTED_RECORDS = 71
EXPECTED_CANDIDATES = 93
EXPECTED_VARIANTS = 72
EXPECTED_FAMILIES = 30

ROOT = Path(__file__).resolve().parents[2]
SCALE_BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
CONTRACTS = SCALE_BASE / "contracts"
SOURCE_BASE = SCALE_BASE / "representative_environment_realization_v0_1"
RUN_BASE = SCALE_BASE / "operator_equivalence_normalization_v0_1"

DEFAULT_SCHEMA = CONTRACTS / "operator_equivalence_normalization_schema_v0_1.json"
DEFAULT_PLAN = CONTRACTS / "operator_equivalence_normalization_plan_v0_1.json"
DEFAULT_REALIZATIONS = SOURCE_BASE / "stage_e2/open_operator_realizations.jsonl"
DEFAULT_VIEWS = SOURCE_BASE / "inputs/environment_views.jsonl"
DEFAULT_ROUTING = SOURCE_BASE / "inputs/producer_routing_manifest_v0_1.json"
DEFAULT_E1 = SOURCE_BASE / "stage_e1/backbone_adequacy_assessments.jsonl"
DEFAULT_PROJECTIONS = RUN_BASE / "structural_projections.jsonl"
DEFAULT_NORMALIZED = RUN_BASE / "normalized_candidates.jsonl"
DEFAULT_QUESTION_SETS = RUN_BASE / "question_normalized_sets.jsonl"
DEFAULT_FAMILY_SETS = RUN_BASE / "family_normalized_sets.jsonl"
DEFAULT_CHECKS = RUN_BASE / "checks.jsonl"
DEFAULT_METRICS = RUN_BASE / "metrics_v0_1.json"
DEFAULT_REPORT = RUN_BASE / "report_v0_1.md"
DEFAULT_MANIFEST = RUN_BASE / "run_manifest.json"
TEST_ARTIFACT = ROOT / "tests/test_operator_equivalence_normalization.py"
COMMON_RUNTIME = ROOT / "data_construction/tools/_common.py"

FORBIDDEN_PROJECTION_KEYS = {
    "question",
    "environment",
    "answer",
    "answer_text",
    "trace",
    "record_local_label",
    "operation_description",
    "output_description",
    "operator_boundary_rationale",
    "required_semantics",
    "extension_description",
    "extension_type",
    "distinguishing_assumptions",
    "limitations",
    "rationale",
    "reason",
}

EVIDENCE_BOUNDARY = {
    "label_free": True,
    "question_text_excluded": True,
    "environment_text_excluded": True,
    "answer_and_trace_excluded": True,
    "e1_content_excluded": True,
    "operator_descriptions_excluded": True,
    "preserved_vocabularies_excluded": True,
    "grounding_evaluated": False,
    "execution_evaluated": False,
    "answer_recovery_evaluated": False,
    "gold_claimed": False,
}


class NormalizationError(ValueError):
    """Raised when the frozen normalization contract is violated."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze-plan", action="store_true")
    modes.add_argument("--build", action="store_true")
    modes.add_argument("--validate-only", action="store_true")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--realizations", type=Path, default=DEFAULT_REALIZATIONS)
    parser.add_argument("--views", type=Path, default=DEFAULT_VIEWS)
    parser.add_argument("--routing", type=Path, default=DEFAULT_ROUTING)
    parser.add_argument("--e1", type=Path, default=DEFAULT_E1)
    parser.add_argument("--projections-output", type=Path, default=DEFAULT_PROJECTIONS)
    parser.add_argument("--normalized-output", type=Path, default=DEFAULT_NORMALIZED)
    parser.add_argument("--question-sets-output", type=Path, default=DEFAULT_QUESTION_SETS)
    parser.add_argument("--family-sets-output", type=Path, default=DEFAULT_FAMILY_SETS)
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
        raise NormalizationError(f"path outside repository: {path}") from exc
    if path.is_symlink() or ".." in relative.parts or ":" in relative.as_posix():
        raise NormalizationError(f"unsafe repository path: {relative.as_posix()}")
    return relative.as_posix()


def _binding(path: Path, *, record_count: int | None = None) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise NormalizationError(f"bound artifact missing or symlink: {_relative(path)}")
    result: dict[str, Any] = {
        "repository_relative_path": _relative(path),
        "sha256": sha256_file(path),
    }
    if record_count is not None:
        result["record_count"] = record_count
    return result


def _schema_validator(path: Path) -> Draft202012Validator:
    schema = read_json(path)
    if not isinstance(schema, dict):
        raise NormalizationError("normalization schema must be an object")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise NormalizationError(f"invalid normalization schema: {exc.message}") from exc
    return Draft202012Validator(schema)


def _outputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "structural_projections": args.projections_output,
        "normalized_candidates": args.normalized_output,
        "question_normalized_sets": args.question_sets_output,
        "family_normalized_sets": args.family_sets_output,
        "checks": args.checks_output,
        "metrics": args.metrics_output,
        "report": args.report_output,
        "run_manifest": args.manifest_output,
    }


def _contract_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "normalization_schema": args.schema,
        "normalizer": Path(__file__).resolve(),
        "common_runtime": COMMON_RUNTIME,
        "tests": TEST_ARTIFACT,
    }


def _source_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "open_operator_realizations": args.realizations,
        "representative_environment_views": args.views,
        "producer_routing": args.routing,
        "backbone_adequacy_for_fallback_selection_only": args.e1,
    }


def _recursive_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        found = set(value)
        for child in value.values():
            found.update(_recursive_keys(child))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for child in value:
            found.update(_recursive_keys(child))
        return found
    return set()


def _assert_label_free_projection(projection: dict[str, Any]) -> None:
    leaked = sorted(_recursive_keys(projection) & FORBIDDEN_PROJECTION_KEYS)
    if leaked:
        raise NormalizationError(f"forbidden projection keys: {leaked}")


def _graph_parts(graph: dict[str, Any]) -> tuple[list[str], set[tuple[str, str]]]:
    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise NormalizationError("graph nodes must be a non-empty array")
    ids = [node.get("node_id") for node in nodes]
    if any(not isinstance(node_id, str) for node_id in ids) or len(ids) != len(set(ids)):
        raise NormalizationError("graph node IDs must be unique strings")
    known = set(ids)
    edges: set[tuple[str, str]] = set()
    for node in nodes:
        dependencies = node.get("depends_on")
        if not isinstance(dependencies, list) or len(dependencies) != len(set(dependencies)):
            raise NormalizationError("depends_on must be a unique array")
        for dependency in dependencies:
            if dependency not in known or dependency == node["node_id"]:
                raise NormalizationError("graph dependency is unknown or self-referential")
            edges.add((dependency, node["node_id"]))
    _topological(ids, edges)
    return ids, edges


def _topological(nodes: Iterable[str], edges: set[tuple[str, str]]) -> list[str]:
    node_list = list(nodes)
    children: dict[str, set[str]] = {node: set() for node in node_list}
    indegree = {node: 0 for node in node_list}
    for source, target in edges:
        children[source].add(target)
        indegree[target] += 1
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(children[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(order) != len(node_list):
        raise NormalizationError("graph contains a cycle")
    return order


def _reachability(nodes: Iterable[str], edges: set[tuple[str, str]]) -> set[tuple[str, str]]:
    node_list = list(nodes)
    children: dict[str, set[str]] = {node: set() for node in node_list}
    for source, target in edges:
        children[source].add(target)
    reachable: set[tuple[str, str]] = set()
    for source in node_list:
        pending = list(children[source])
        seen: set[str] = set()
        while pending:
            target = pending.pop()
            if target in seen:
                continue
            seen.add(target)
            reachable.add((source, target))
            pending.extend(children[target] - seen)
    return reachable


def transitive_reduction(nodes: Iterable[str], edges: set[tuple[str, str]]) -> set[tuple[str, str]]:
    """Return the unique transitive reduction of a finite DAG."""

    node_list = list(nodes)
    _topological(node_list, edges)
    reduced = set(edges)
    for edge in sorted(edges):
        trial = reduced - {edge}
        if edge in _reachability(node_list, trial):
            reduced.remove(edge)
    return reduced


def canonicalize_semantic_graph(graph: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Canonicalize a role-labeled DAG; target backbones contain at most six nodes."""

    node_ids, edges = _graph_parts(graph)
    if len(node_ids) > 8:
        raise NormalizationError("semantic graph exceeds bounded canonicalizer size")
    reduced = transitive_reduction(node_ids, edges)
    roles = {node["node_id"]: node.get("role") for node in graph["nodes"]}
    if any(not isinstance(role, str) or not role for role in roles.values()):
        raise NormalizationError("semantic graph roles must be non-empty strings")
    entries = set(graph.get("entry_node_ids", []))
    outputs = set(graph.get("output_node_ids", []))
    if not entries or not outputs or not entries <= set(node_ids) or not outputs <= set(node_ids):
        raise NormalizationError("semantic entry/output IDs are invalid")

    best_key: str | None = None
    best_order: tuple[str, ...] | None = None
    for order in itertools.permutations(node_ids):
        index = {source: position for position, source in enumerate(order)}
        encoding = {
            "roles": [roles[source] for source in order],
            "edges": sorted((index[source], index[target]) for source, target in reduced),
            "entries": sorted(index[source] for source in entries),
            "outputs": sorted(index[source] for source in outputs),
        }
        key = json.dumps(encoding, sort_keys=True, separators=(",", ":"))
        if best_key is None or key < best_key:
            best_key = key
            best_order = order
    assert best_order is not None
    mapping = {source: f"sq{index + 1}" for index, source in enumerate(best_order)}
    dependencies: dict[str, list[str]] = {mapping[source]: [] for source in best_order}
    for source, target in reduced:
        dependencies[mapping[target]].append(mapping[source])
    payload = {
        "canonicalization": "alpha_renaming_independent_node_order_and_transitive_reduction_v0_1",
        "nodes": [
            {
                "node_id": mapping[source],
                "role": roles[source],
                "depends_on": sorted(dependencies[mapping[source]]),
            }
            for source in best_order
        ],
        "entry_node_ids": sorted(mapping[source] for source in entries),
        "output_node_ids": sorted(mapping[source] for source in outputs),
    }
    return {**payload, "signature_sha256": canonical_json_sha256(payload)}, mapping


def _target_graph(view: dict[str, Any], variant_id: str) -> dict[str, Any]:
    context = view["payload"]["candidate_backbone_context"]
    if variant_id == "primary":
        graph = context["primary_graph"]
    else:
        alternatives = {
            item["alternative_id"]: item["graph"] for item in context["alternative_graphs"]
        }
        if variant_id not in alternatives:
            raise NormalizationError(f"target variant absent from view: {variant_id}")
        graph = alternatives[variant_id]
    return {
        "nodes": [
            {
                "node_id": node["node_id"],
                "role": node["role"],
                "depends_on": list(node["depends_on"]),
            }
            for node in graph["nodes"]
        ],
        "entry_node_ids": list(graph["entry_node_ids"]),
        "output_node_ids": list(graph["output_node_ids"]),
    }


def build_structural_projection(
    realization: dict[str, Any], candidate: dict[str, Any], view: dict[str, Any]
) -> dict[str, Any]:
    target = _target_graph(view, candidate["target_backbone_variant_id"])
    operator_graph = candidate["graph"]
    operator_ids, _ = _graph_parts(operator_graph)
    slot_ids = {slot["slot_id"] for slot in candidate["binding_slots"]}
    classifications = {
        item["operator_node_id"]: sorted(item["roles"])
        for item in candidate["operator_node_classifications"]
    }
    if set(classifications) != set(operator_ids):
        raise NormalizationError("operator classifications do not exactly cover graph nodes")
    projected_operator_nodes = []
    for node in operator_graph["nodes"]:
        input_slots = node["input_slot_ids"]
        if not set(input_slots) <= slot_ids:
            raise NormalizationError("operator node references an unknown slot")
        projected_operator_nodes.append(
            {
                "node_id": node["node_id"],
                "depends_on": list(node["depends_on"]),
                "input_slot_ids": list(input_slots),
                "roles": classifications[node["node_id"]],
            }
        )
    projection = {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "projection_id": (
            f"operator_equivalence_projection_v0_1:{realization['question_id']}:"
            f"{candidate['candidate_id']}"
        ),
        "question_id": realization["question_id"],
        "family_id": realization["family_id"],
        "producer_partition": realization["producer_partition"],
        "candidate_id": candidate["candidate_id"],
        "target_backbone_variant_id": candidate["target_backbone_variant_id"],
        "variation_axes": sorted(candidate["variation_axes"]),
        "target_semantic_topology": target,
        "operator_topology": {
            "nodes": projected_operator_nodes,
            "entry_node_ids": list(operator_graph["entry_node_ids"]),
            "output_node_ids": list(operator_graph["output_node_ids"]),
        },
        "semantic_to_operator_mappings": [
            {
                "mapping_id": item["mapping_id"],
                "backbone_node_ids": list(item["backbone_node_ids"]),
                "operator_node_ids": list(item["operator_node_ids"]),
                "mapping_kind": item["mapping_kind"],
            }
            for item in candidate["backbone_operator_mappings"]
        ],
        "typed_unresolved_slots": [
            {
                "slot_id": slot["slot_id"],
                "environment_modality": slot["environment_modality"],
                "cardinality": slot["cardinality"],
            }
            for slot in candidate["binding_slots"]
        ],
        "unsupported_target_backbone_node_ids": sorted(
            item["node_id"] for item in candidate["unsupported_target_backbone_nodes"]
        ),
        "coverage_status": candidate["coverage_status"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }
    _assert_label_free_projection(projection)
    return projection


def _counter_records(counter: Counter[tuple[str, str]]) -> list[dict[str, Any]]:
    return [
        {"environment_modality": modality, "cardinality": cardinality, "count": count}
        for (modality, cardinality), count in sorted(counter.items())
    ]


def _placement(
    operator_id: str,
    semantic_operator_ids: set[str],
    reachability: set[tuple[str, str]],
) -> str:
    before = any((operator_id, semantic) in reachability for semantic in semantic_operator_ids)
    after = any((semantic, operator_id) in reachability for semantic in semantic_operator_ids)
    if before and after:
        return "explicit_between_semantics"
    if before:
        return "explicit_before_semantic"
    if after:
        return "explicit_after_semantic"
    return "explicit_disconnected"


def normalize_projection(projection: dict[str, Any]) -> dict[str, Any]:
    target = projection["target_semantic_topology"]
    quotient, canonical_map = canonicalize_semantic_graph(target)
    target_ids, target_edges = _graph_parts(target)
    target_reach = _reachability(target_ids, target_edges)
    operator_graph = projection["operator_topology"]
    operator_ids, operator_edges = _graph_parts(operator_graph)
    operator_reach = _reachability(operator_ids, operator_edges)

    backbone_to_operators: dict[str, set[str]] = defaultdict(set)
    operator_to_backbones: dict[str, set[str]] = defaultdict(set)
    mapping_kinds: Counter[str] = Counter()
    for mapping in projection["semantic_to_operator_mappings"]:
        mapping_kinds[mapping["mapping_kind"]] += 1
        for backbone in mapping["backbone_node_ids"]:
            for operator in mapping["operator_node_ids"]:
                backbone_to_operators[backbone].add(operator)
                operator_to_backbones[operator].add(backbone)
    if not set(backbone_to_operators) <= set(target_ids):
        raise NormalizationError("mapping references unknown target backbone node")
    if not set(operator_to_backbones) <= set(operator_ids):
        raise NormalizationError("mapping references unknown operator node")

    coverage_preserved = (
        set(backbone_to_operators) == set(target_ids)
        and not projection["unsupported_target_backbone_node_ids"]
    )

    def candidate_precedes(source: str, target_node: str) -> bool:
        return any(
            source_op == target_op or (source_op, target_op) in operator_reach
            for source_op in backbone_to_operators[source]
            for target_op in backbone_to_operators[target_node]
        )

    missing_dependencies = sorted(
        (source, target_node)
        for source, target_node in target_reach
        if not candidate_precedes(source, target_node)
    )
    extra_dependencies = sorted(
        (source, target_node)
        for source in target_ids
        for target_node in target_ids
        if source != target_node
        and (source, target_node) not in target_reach
        and source in backbone_to_operators
        and target_node in backbone_to_operators
        and candidate_precedes(source, target_node)
    )
    dependency_preserved = not missing_dependencies
    no_extra_dependencies = not extra_dependencies

    roles_by_operator = {
        node["node_id"]: set(node["roles"]) for node in operator_graph["nodes"]
    }
    semantic_operator_ids = set(operator_to_backbones)
    fused = {
        operator
        for operator, roles in roles_by_operator.items()
        if "backbone_realization" in roles and "environment_extension" in roles
    }
    explicit = {
        operator
        for operator, roles in roles_by_operator.items()
        if roles == {"environment_extension"}
    }
    placements: Counter[str] = Counter()
    placements["fused_with_semantic"] = len(fused)
    for operator in explicit:
        placements[_placement(operator, semantic_operator_ids, operator_reach)] += 1
    placements += Counter()
    access_mode = (
        "mixed" if fused and explicit else "fused" if fused else "explicit" if explicit else "none"
    )
    slot_counter = Counter(
        (slot["environment_modality"], slot["cardinality"])
        for slot in projection["typed_unresolved_slots"]
    )
    semantic_output_arity = sum(
        1 for node in operator_graph["output_node_ids"] if node in semantic_operator_ids
    )
    output_arity_preserved = semantic_output_arity == len(target["output_node_ids"])
    adapter_payload = {
        "access_mode": access_mode,
        "typed_slot_multiset": _counter_records(slot_counter),
        "access_placement_multiset": [
            {"placement": placement, "count": count}
            for placement, count in sorted(placements.items())
            if count
        ],
        "operator_output_arity": len(operator_graph["output_node_ids"]),
        "semantic_output_arity": semantic_output_arity,
        "fused_access_node_count": len(fused),
        "explicit_access_node_count": len(explicit),
    }
    adapter = {
        **adapter_payload,
        "signature_sha256": canonical_json_sha256(adapter_payload),
    }

    provisional_reasons: list[str] = []
    if not no_extra_dependencies:
        provisional_reasons.append("candidate_adds_semantic_dependency_not_required_by_target")
    if mapping_kinds["many_to_one"] or mapping_kinds["many_to_many"]:
        provisional_reasons.append("semantic_nodes_fused_beyond_access_only_split_or_fuse")
    if mapping_kinds["one_to_many"]:
        split_nodes = {
            operator
            for mapping in projection["semantic_to_operator_mappings"]
            if mapping["mapping_kind"] == "one_to_many"
            for operator in mapping["operator_node_ids"]
        }
        if not all("environment_extension" in roles_by_operator[node] for node in split_nodes):
            provisional_reasons.append("one_to_many_split_not_structurally_access_preserving")
    if any(slot["cardinality"] == "unknown" for slot in projection["typed_unresolved_slots"]):
        provisional_reasons.append("grounding_dependent_unknown_cardinality")
    if "explicit_disconnected" in placements:
        provisional_reasons.append("disconnected_environment_access_requires_grounding_check")
    if not output_arity_preserved:
        provisional_reasons.append("semantic_output_arity_differs_from_target")

    if not coverage_preserved or not dependency_preserved:
        status = "not_equivalent"
    elif provisional_reasons:
        status = "provisionally_equivalent"
    else:
        status = "equivalent"

    projection_sha256 = canonical_json_sha256(projection)
    return {
        "schema_version": NORMALIZATION_SCHEMA_VERSION,
        "normalization_id": (
            f"operator_equivalence_normalization_v0_1:{projection['question_id']}:"
            f"{projection['candidate_id']}"
        ),
        "question_id": projection["question_id"],
        "family_id": projection["family_id"],
        "producer_partition": projection["producer_partition"],
        "candidate_id": projection["candidate_id"],
        "target_backbone_variant_id": projection["target_backbone_variant_id"],
        "source_projection_sha256": projection_sha256,
        "semantic_quotient": quotient,
        "environment_adapter_signature": adapter,
        "equivalence_assessment": {
            "status": status,
            "coverage_preserved": coverage_preserved,
            "dependency_preserved": dependency_preserved,
            "no_extra_semantic_dependencies": no_extra_dependencies,
            "output_arity_preserved": output_arity_preserved,
            "allowed_transformations": [
                "alpha_renaming",
                "independent_node_ordering",
                "transitive_reduction",
                "meaning_and_io_preserving_access_split_or_fuse",
            ],
            "provisional_reasons": sorted(provisional_reasons),
        },
        "reversibility_ledger": {
            "structural_projection": projection,
            "reconstruction_sha256": projection_sha256,
            "reconstruction_verified": canonical_json_sha256(projection) == projection_sha256,
        },
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def _load_sources(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    realizations = list(iter_json_records(args.realizations))
    views = {record["question_id"]: record for record in iter_json_records(args.views)}
    candidate_count = sum(len(record["realization_candidates"]) for record in realizations)
    variant_count = sum(len(record["variant_realization_results"]) for record in realizations)
    family_count = len({record["family_id"] for record in realizations})
    if (len(realizations), candidate_count, variant_count, family_count) != (
        EXPECTED_RECORDS,
        EXPECTED_CANDIDATES,
        EXPECTED_VARIANTS,
        EXPECTED_FAMILIES,
    ):
        raise NormalizationError(
            "source count mismatch: "
            f"records={len(realizations)} candidates={candidate_count} "
            f"variants={variant_count} families={family_count}"
        )
    question_ids = [record["question_id"] for record in realizations]
    if len(question_ids) != len(set(question_ids)) or set(question_ids) != set(views):
        raise NormalizationError("realization/view question IDs are not a one-to-one match")
    return realizations, views


def _fallback_selection(args: argparse.Namespace, realizations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    e1 = {record["question_id"]: record for record in iter_json_records(args.e1)}
    route = {record["question_id"]: record["producer_partition"] for record in realizations}
    selected: list[dict[str, Any]] = []
    for partition_index in range(1, 5):
        partition = f"e2_author_partition_{partition_index:02d}"
        members = [question_id for question_id, value in route.items() if value == partition]
        challenge = sorted(
            (
                question_id
                for question_id in members
                if e1[question_id]["overall_status"] != "adequate"
            ),
            key=lambda question_id: stable_rank("normalization-fallback-challenge-v0.1", question_id),
        )
        controls = sorted(
            (
                question_id
                for question_id in members
                if e1[question_id]["overall_status"] == "adequate"
            ),
            key=lambda question_id: stable_rank("normalization-fallback-control-v0.1", question_id),
        )
        chosen = challenge + controls[: 4 - len(challenge)]
        if len(chosen) != 4:
            raise NormalizationError(f"cannot select four fallback records for {partition}")
        selected.extend(
            {
                "question_id": question_id,
                "original_e2_producer_partition": partition,
                "selection_role": (
                    "e1_challenge" if e1[question_id]["overall_status"] != "adequate" else "adequate_control"
                ),
            }
            for question_id in chosen
        )
    if sum(item["selection_role"] == "e1_challenge" for item in selected) != 7:
        raise NormalizationError("fallback selection must contain all seven E1 challenge records")
    return selected


def build_freeze_plan(args: argparse.Namespace) -> dict[str, Any]:
    for path in _outputs(args).values():
        if path.is_symlink() or path.exists():
            raise NormalizationError(f"planned output exists before freeze: {_relative(path)}")
    _schema_validator(args.schema)
    realizations, _ = _load_sources(args)
    implementation_commit = git_tracked_commit_identity(
        ROOT, _contract_inputs(args).values()
    )
    source_commit = git_tracked_commit_identity(ROOT, _source_inputs(args).values())
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "run_id": RUN_ID,
        "status": "frozen_after_e2_before_any_normalized_output",
        "implementation_commit": implementation_commit,
        "source_commit": source_commit,
        "contract_artifacts": {
            label: _binding(path) for label, path in _contract_inputs(args).items()
        },
        "source_artifacts": {
            label: _binding(path) for label, path in _source_inputs(args).items()
        },
        "expected_inputs": {
            "realization_records": EXPECTED_RECORDS,
            "target_variants": EXPECTED_VARIANTS,
            "candidates": EXPECTED_CANDIDATES,
            "families": EXPECTED_FAMILIES,
        },
        "visibility_contract": {
            "allowed": [
                "opaque_identifiers",
                "target_semantic_topology_and_roles",
                "operator_adjacency",
                "semantic_to_operator_mappings",
                "operator_backbone_or_environment_roles",
                "typed_unresolved_slot_modality_and_cardinality",
                "variation_axes",
                "producer_route",
            ],
            "excluded": [
                "question_text",
                "environment_text",
                "answers_and_traces",
                "e1_content",
                "operator_labels_and_descriptions",
                "preserved_operator_vocabularies",
                "grounding",
                "execution",
            ],
        },
        "normalization_contract": {
            "semantic_layer": "role_labeled_target_dag_quotient",
            "adapter_layer": "typed_slot_access_placement_fusion_and_output_arity_signature",
            "allowed_initial_equivalences": [
                "alpha_renaming",
                "independent_node_ordering",
                "transitive_reduction",
                "meaning_and_io_preserving_access_split_or_fuse",
            ],
            "grounding_dependent_cases": "provisionally_equivalent",
            "candidate1_preferred": False,
            "alternatives_compared_as_sets": True,
            "reversibility_required": True,
        },
        "frozen_branch_criteria": {
            "technical_loss_count_max": 0,
            "not_equivalent_count_max": 0,
            "provisionally_equivalent_fraction_max_for_direct_grounding": 0.05,
            "multi_question_family_semantic_set_instability_fraction_max": 0.10,
            "producer_attribution_required_for_direct_grounding": True,
            "branch_order": [
                "revise_contract_on_technical_loss_or_not_equivalence",
                "run_crossed_author_sensitivity_when_question_and_producer_effects_are_not_separable",
                "revise_contract_when_thresholds_fail",
                "allow_provisional_non_final_grounding_adapter_only_when_all_criteria_pass",
            ],
        },
        "precommitted_crossed_author_fallback": {
            "status": "planned_not_started",
            "fresh_reserve_ids_used": False,
            "authors": 2,
            "design": "fully_crossed_two_new_ai_authors_on_all_16_records",
            "purpose": "producer_confound_diagnostic_not_human_majority_review",
            "selection": _fallback_selection(args, realizations),
        },
        "planned_outputs": {
            label: {"repository_relative_path": _relative(path)}
            for label, path in _outputs(args).items()
        },
    }


def _validate_plan(args: argparse.Namespace) -> dict[str, Any]:
    plan = read_json(args.plan)
    if not isinstance(plan, dict) or plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise NormalizationError("normalization plan is missing or has the wrong version")
    if plan.get("status") != "frozen_after_e2_before_any_normalized_output":
        raise NormalizationError("normalization plan was not frozen before outputs")
    for label, path in _contract_inputs(args).items():
        if plan["contract_artifacts"][label] != _binding(path):
            raise NormalizationError(f"plan contract binding mismatch: {label}")
    for label, path in _source_inputs(args).items():
        if plan["source_artifacts"][label] != _binding(path):
            raise NormalizationError(f"plan source binding mismatch: {label}")
    for label, path in _outputs(args).items():
        if plan["planned_outputs"][label]["repository_relative_path"] != _relative(path):
            raise NormalizationError(f"plan output binding mismatch: {label}")
    return plan


def _normalized_sets(normalized: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in normalized:
        by_question[record["question_id"]].append(record)
    question_sets: list[dict[str, Any]] = []
    for question_id, records in sorted(by_question.items()):
        pairs: dict[tuple[str, str], list[str]] = defaultdict(list)
        for record in records:
            key = (
                record["semantic_quotient"]["signature_sha256"],
                record["environment_adapter_signature"]["signature_sha256"],
            )
            pairs[key].append(record["candidate_id"])
        members = [
            {
                "semantic_quotient_sha256": semantic,
                "environment_adapter_sha256": adapter,
                "candidate_ids": sorted(candidate_ids),
            }
            for (semantic, adapter), candidate_ids in sorted(pairs.items())
        ]
        semantic_set = sorted({item["semantic_quotient_sha256"] for item in members})
        adapter_set = sorted({item["environment_adapter_sha256"] for item in members})
        question_sets.append(
            {
                "schema_version": "operator_equivalence_question_set_v0_1",
                "question_id": question_id,
                "family_id": records[0]["family_id"],
                "producer_partition": records[0]["producer_partition"],
                "members": members,
                "semantic_set_sha256": canonical_json_sha256(semantic_set),
                "adapter_set_sha256": canonical_json_sha256(adapter_set),
                "candidate_set_sha256": canonical_json_sha256(members),
                "candidate1_preferred": False,
            }
        )

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in question_sets:
        by_family[record["family_id"]].append(record)
    family_sets = []
    for family_id, records in sorted(by_family.items()):
        semantic_profiles = Counter(record["semantic_set_sha256"] for record in records)
        adapter_profiles = Counter(record["adapter_set_sha256"] for record in records)
        family_sets.append(
            {
                "schema_version": "operator_equivalence_family_set_v0_1",
                "family_id": family_id,
                "question_count": len(records),
                "producer_partitions": sorted({record["producer_partition"] for record in records}),
                "semantic_set_profiles": [
                    {"set_sha256": key, "question_count": count}
                    for key, count in sorted(semantic_profiles.items())
                ],
                "adapter_set_profiles": [
                    {"set_sha256": key, "question_count": count}
                    for key, count in sorted(adapter_profiles.items())
                ],
                "semantic_set_stable": len(semantic_profiles) == 1,
                "adapter_set_stable": len(adapter_profiles) == 1,
            }
        )
    return question_sets, family_sets


def _metrics(
    normalized: list[dict[str, Any]],
    question_sets: list[dict[str, Any]],
    family_sets: list[dict[str, Any]],
    plan: dict[str, Any],
) -> dict[str, Any]:
    statuses = Counter(
        record["equivalence_assessment"]["status"] for record in normalized
    )
    multi = [record for record in family_sets if record["question_count"] > 1]
    unstable = [record for record in multi if not record["semantic_set_stable"]]
    provisional_fraction = statuses["provisionally_equivalent"] / len(normalized)
    instability_fraction = len(unstable) / len(multi) if multi else 0.0
    technical_loss = sum(
        not record["reversibility_ledger"]["reconstruction_verified"]
        or record["source_projection_sha256"]
        != record["reversibility_ledger"]["reconstruction_sha256"]
        for record in normalized
    )
    question_and_producer_effects_separable = False
    criteria = plan["frozen_branch_criteria"]
    if technical_loss > criteria["technical_loss_count_max"] or statuses["not_equivalent"] > criteria["not_equivalent_count_max"]:
        decision = "REVISE_NORMALIZATION_CONTRACT_TECHNICAL_OR_SEMANTIC_LOSS"
    elif not question_and_producer_effects_separable:
        decision = "RUN_PRECOMMITTED_CROSSED_AUTHOR_SENSITIVITY"
    elif provisional_fraction > criteria["provisionally_equivalent_fraction_max_for_direct_grounding"] or instability_fraction > criteria["multi_question_family_semantic_set_instability_fraction_max"]:
        decision = "REVISE_NORMALIZATION_CONTRACT_THRESHOLD_FAILURE"
    else:
        decision = "ALLOW_PROVISIONAL_NON_FINAL_GROUNDING_ADAPTER"
    return {
        "schema_version": "operator_equivalence_normalization_metrics_v0_1",
        "run_id": RUN_ID,
        "counts": {
            "normalized_candidates": len(normalized),
            "questions": len(question_sets),
            "families": len(family_sets),
            "distinct_semantic_quotients": len(
                {record["semantic_quotient"]["signature_sha256"] for record in normalized}
            ),
            "distinct_environment_adapters": len(
                {record["environment_adapter_signature"]["signature_sha256"] for record in normalized}
            ),
            "equivalence_status": dict(sorted(statuses.items())),
            "technical_loss": technical_loss,
            "multi_question_families": len(multi),
            "unstable_multi_question_semantic_sets": len(unstable),
        },
        "rates": {
            "provisionally_equivalent_fraction": provisional_fraction,
            "multi_question_family_semantic_set_instability_fraction": instability_fraction,
        },
        "producer_partition_sensitivity": {
            "fixed_question_producer_assignment": True,
            "question_and_producer_effects_separable": question_and_producer_effects_separable,
            "direct_attribution_authorized": False,
        },
        "frozen_criteria": criteria,
        "decision": decision,
        "grounding_authorized": decision == "ALLOW_PROVISIONAL_NON_FINAL_GROUNDING_ADAPTER",
        "fresh_reserve_ids_used": False,
        "human_evidence_created": False,
    }


def _report(metrics: dict[str, Any]) -> str:
    counts = metrics["counts"]
    statuses = counts["equivalence_status"]
    return "\n".join(
        [
            "# Operator equivalence normalization v0.1",
            "",
            "This deterministic run normalized all 93 open candidates without free-text",
            "operator labels/descriptions, question or environment text, E1 content, answers,",
            "traces, grounding, execution, or preserved operator vocabularies.",
            "",
            "## Results",
            "",
            f"- candidates: {counts['normalized_candidates']}",
            f"- semantic quotients: {counts['distinct_semantic_quotients']}",
            f"- environment-adapter signatures: {counts['distinct_environment_adapters']}",
            f"- equivalent: {statuses.get('equivalent', 0)}",
            f"- provisionally equivalent: {statuses.get('provisionally_equivalent', 0)}",
            f"- not equivalent: {statuses.get('not_equivalent', 0)}",
            f"- reversible projection loss: {counts['technical_loss']}",
            "",
            "## Frozen branch result",
            "",
            f"`{metrics['decision']}`",
            "",
            "The fixed one-question/one-producer assignment cannot separate question and",
            "producer effects. Grounding therefore remains unauthorized; the precommitted",
            "16-question, two-new-author fully crossed sensitivity run is the next gate.",
            "",
        ]
    )


def build_artifacts(args: argparse.Namespace) -> dict[str, tuple[Path, bytes]]:
    plan = _validate_plan(args)
    validator = _schema_validator(args.schema)
    realizations, views = _load_sources(args)
    projections: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for realization in realizations:
        view = views[realization["question_id"]]
        for candidate in realization["realization_candidates"]:
            projection = build_structural_projection(realization, candidate, view)
            record = normalize_projection(projection)
            errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
            if errors:
                raise NormalizationError(
                    f"normalized record schema failure {record['normalization_id']}: {errors[0].message}"
                )
            if canonical_json_sha256(record["reversibility_ledger"]["structural_projection"]) != record["source_projection_sha256"]:
                raise NormalizationError("reversibility ledger does not reconstruct projection")
            projections.append(projection)
            normalized.append(record)
            checks.append(
                {
                    "schema_version": "operator_equivalence_normalization_check_v0_1",
                    "normalization_id": record["normalization_id"],
                    "status": "pass",
                    "projection_label_free": True,
                    "schema_valid": True,
                    "reconstruction_verified": True,
                }
            )
    question_sets, family_sets = _normalized_sets(normalized)
    metrics = _metrics(normalized, question_sets, family_sets, plan)
    report = _report(metrics)

    preliminary = {
        "structural_projections": (args.projections_output, jsonl_file_bytes(projections)),
        "normalized_candidates": (args.normalized_output, jsonl_file_bytes(normalized)),
        "question_normalized_sets": (args.question_sets_output, jsonl_file_bytes(question_sets)),
        "family_normalized_sets": (args.family_sets_output, jsonl_file_bytes(family_sets)),
        "checks": (args.checks_output, jsonl_file_bytes(checks)),
        "metrics": (args.metrics_output, json_file_bytes(metrics)),
        "report": (args.report_output, report.encode("utf-8")),
    }
    manifest = {
        "schema_version": "operator_equivalence_normalization_run_manifest_v0_1",
        "run_id": RUN_ID,
        "plan": _binding(args.plan),
        "implementation_commit": plan["implementation_commit"],
        "source_commit": plan["source_commit"],
        "source_artifacts": plan["source_artifacts"],
        "contract_artifacts": plan["contract_artifacts"],
        "outputs": {
            label: {
                "repository_relative_path": _relative(path),
                "sha256": __import__("hashlib").sha256(payload).hexdigest(),
            }
            for label, (path, payload) in preliminary.items()
        },
        "counts": metrics["counts"],
        "decision": metrics["decision"],
        "grounding_authorized": metrics["grounding_authorized"],
        "validation_status": "pass",
    }
    return {
        **preliminary,
        "run_manifest": (args.manifest_output, json_file_bytes(manifest)),
    }


def validate_materialized(args: argparse.Namespace) -> dict[str, Any]:
    expected = build_artifacts(args)
    mismatches = []
    for label, (path, payload) in expected.items():
        if not path.is_file() or path.read_bytes() != payload:
            mismatches.append(label)
    if mismatches:
        raise NormalizationError(f"materialized artifacts differ from reconstruction: {mismatches}")
    metrics = read_json(args.metrics_output)
    return {
        "status": "pass",
        "mode": "validate_only",
        "candidates": metrics["counts"]["normalized_candidates"],
        "questions": metrics["counts"]["questions"],
        "families": metrics["counts"]["families"],
        "decision": metrics["decision"],
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.freeze_plan:
            plan = build_freeze_plan(args)
            write_output_batch(
                {"plan": (args.plan, json_file_bytes(plan))}, overwrite=args.overwrite
            )
            print(json.dumps({"status": "frozen", "plan": _relative(args.plan)}, sort_keys=True))
        elif args.build:
            statuses = write_output_batch(build_artifacts(args), overwrite=args.overwrite)
            print(json.dumps({"status": "built", "outputs": statuses}, sort_keys=True))
        else:
            print(json.dumps(validate_materialized(args), sort_keys=True))
    except (NormalizationError, ValueError, OSError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
