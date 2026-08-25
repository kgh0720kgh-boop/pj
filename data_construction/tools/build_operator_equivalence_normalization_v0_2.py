#!/usr/bin/env python3
"""Build candidate-sensitive operator-equivalence normalization v0.2.

Version 0.2 consumes only the 93 original and 34 crossed-author v0.1
normalization records.  It separates semantic-set eligibility from semantic
profile identity, makes partial support/output/dependency failures visible in
the profile hash, and factors environment adapters into four independently
comparable components.  No question/environment text, answer, trace,
grounding, execution, human evidence, or preserved vocabulary is consumed.
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
import build_operator_equivalence_normalization as v01


TOOL_VERSION = "operator_equivalence_normalizer_v0_2"
PLAN_SCHEMA_VERSION = "operator_equivalence_normalization_plan_v0_2"
PLAN_ID = "hybridqa_operator_equivalence_normalization_plan_v0_2"
RUN_ID = "hybridqa_operator_equivalence_normalization_v0_2_run_001"
NORMALIZATION_SCHEMA_VERSION = "operator_equivalence_normalization_v0_2"
EXPECTED_ORIGINAL_CANDIDATES = 93
EXPECTED_CROSSED_CANDIDATES = 34
EXPECTED_CANDIDATES = 127
EXPECTED_ORIGINAL_QUESTIONS = 71
EXPECTED_ORIGINAL_FAMILIES = 30
EXPECTED_CROSSED_QUESTIONS = 16
AUTHOR_BY_PRODUCER = {
    "e2_author_partition_05": "crossed_author_01",
    "e2_author_partition_06": "crossed_author_02",
}
COMPONENT_NAMES = (
    "modality_cardinality",
    "semantic_relative_placement",
    "split_fuse_boundary",
    "output_arity",
)

ROOT = Path(__file__).resolve().parents[2]
SCALE_BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
CONTRACTS = SCALE_BASE / "contracts"
ORIGINAL_BASE = SCALE_BASE / "operator_equivalence_normalization_v0_1"
CROSSED_BASE = SCALE_BASE / "operator_equivalence_crossed_author_sensitivity_v0_1"
RUN_BASE = SCALE_BASE / "operator_equivalence_normalization_v0_2"

DEFAULT_SCHEMA = CONTRACTS / "operator_equivalence_normalization_schema_v0_2.json"
DEFAULT_COMPARISON_SCHEMA = (
    CONTRACTS / "operator_equivalence_crossed_comparison_schema_v0_2.json"
)
DEFAULT_PLAN = CONTRACTS / "operator_equivalence_normalization_plan_v0_2.json"
DEFAULT_ORIGINAL_MANIFEST = ORIGINAL_BASE / "run_manifest.json"
DEFAULT_CROSSED_MANIFEST = CROSSED_BASE / "run_manifest.json"
DEFAULT_ORIGINAL_NORMALIZED = ORIGINAL_BASE / "normalized_candidates.jsonl"
DEFAULT_CROSSED_NORMALIZED = CROSSED_BASE / "normalized_candidates.jsonl"
DEFAULT_CROSSED_COMPARISONS = CROSSED_BASE / "question_comparisons.jsonl"
DEFAULT_NORMALIZED = RUN_BASE / "normalized_candidates.jsonl"
DEFAULT_ORIGINAL_QUESTION_SETS = RUN_BASE / "original_question_sets.jsonl"
DEFAULT_ORIGINAL_FAMILY_SETS = RUN_BASE / "original_family_sets.jsonl"
DEFAULT_CROSSED_V0_2_COMPARISONS = RUN_BASE / "crossed_question_comparisons.jsonl"
DEFAULT_CHECKS = RUN_BASE / "checks.jsonl"
DEFAULT_METRICS = RUN_BASE / "metrics_v0_2.json"
DEFAULT_REPORT = RUN_BASE / "report_v0_2.md"
DEFAULT_MANIFEST = RUN_BASE / "run_manifest.json"
COMMON_RUNTIME = ROOT / "data_construction/tools/_common.py"
V01_NORMALIZER = ROOT / "data_construction/tools/build_operator_equivalence_normalization.py"
TEST_ARTIFACT = ROOT / "tests/test_operator_equivalence_normalization_v0_2.py"

EVIDENCE_BOUNDARY = {
    "label_free_structural_inputs_only": True,
    "v0_1_artifacts_immutable": True,
    "question_text_excluded": True,
    "environment_text_excluded": True,
    "answer_and_trace_excluded": True,
    "e1_content_excluded": True,
    "operator_descriptions_excluded": True,
    "preserved_vocabularies_excluded": True,
    "fresh_question_ids_used": False,
    "grounding_evaluated": False,
    "execution_evaluated": False,
    "answer_recovery_evaluated": False,
    "human_evidence_created": False,
    "gold_claimed": False,
}


class NormalizationV02Error(ValueError):
    """Raised when the frozen v0.2 contract is violated."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze-plan", action="store_true")
    modes.add_argument("--build", action="store_true")
    modes.add_argument("--validate-only", action="store_true")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument(
        "--comparison-schema", type=Path, default=DEFAULT_COMPARISON_SCHEMA
    )
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument(
        "--original-manifest", type=Path, default=DEFAULT_ORIGINAL_MANIFEST
    )
    parser.add_argument(
        "--crossed-manifest", type=Path, default=DEFAULT_CROSSED_MANIFEST
    )
    parser.add_argument(
        "--original-normalized", type=Path, default=DEFAULT_ORIGINAL_NORMALIZED
    )
    parser.add_argument(
        "--crossed-normalized", type=Path, default=DEFAULT_CROSSED_NORMALIZED
    )
    parser.add_argument(
        "--crossed-comparisons", type=Path, default=DEFAULT_CROSSED_COMPARISONS
    )
    parser.add_argument("--normalized-output", type=Path, default=DEFAULT_NORMALIZED)
    parser.add_argument(
        "--original-question-sets-output",
        type=Path,
        default=DEFAULT_ORIGINAL_QUESTION_SETS,
    )
    parser.add_argument(
        "--original-family-sets-output",
        type=Path,
        default=DEFAULT_ORIGINAL_FAMILY_SETS,
    )
    parser.add_argument(
        "--crossed-comparisons-output",
        type=Path,
        default=DEFAULT_CROSSED_V0_2_COMPARISONS,
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
        raise NormalizationV02Error(f"path outside repository: {path}") from exc
    if path.is_symlink() or ".." in relative.parts or ":" in relative.as_posix():
        raise NormalizationV02Error(f"unsafe repository path: {relative.as_posix()}")
    return relative.as_posix()


def _binding(path: Path, *, record_count: int | None = None) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise NormalizationV02Error(f"bound artifact missing or symlink: {_relative(path)}")
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
        raise NormalizationV02Error(f"schema is not an object: {_relative(path)}")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise NormalizationV02Error(
            f"invalid schema {_relative(path)}: {exc.message}"
        ) from exc
    return Draft202012Validator(schema)


def _contract_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "normalization_schema_v0_2": args.schema,
        "crossed_comparison_schema_v0_2": args.comparison_schema,
        "normalizer_v0_2": Path(__file__).resolve(),
        "normalizer_v0_1_read_only_dependency": V01_NORMALIZER,
        "common_runtime": COMMON_RUNTIME,
        "tests": TEST_ARTIFACT,
    }


def _source_inputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "normalization_v0_1_run_manifest": args.original_manifest,
        "crossed_author_v0_1_run_manifest": args.crossed_manifest,
        "original_v0_1_normalized_candidates": args.original_normalized,
        "crossed_author_v0_1_normalized_candidates": args.crossed_normalized,
        "crossed_author_v0_1_question_comparisons": args.crossed_comparisons,
    }


def _outputs(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "normalized_candidates": args.normalized_output,
        "original_question_sets": args.original_question_sets_output,
        "original_family_sets": args.original_family_sets_output,
        "crossed_question_comparisons": args.crossed_comparisons_output,
        "checks": args.checks_output,
        "metrics": args.metrics_output,
        "report": args.report_output,
        "run_manifest": args.manifest_output,
    }


def _verify_manifest_output(
    manifest: dict[str, Any], label: str, path: Path
) -> None:
    reference = manifest.get("outputs", {}).get(label)
    if not isinstance(reference, dict):
        raise NormalizationV02Error(f"source manifest lacks output binding: {label}")
    if reference.get("repository_relative_path") != _relative(path):
        raise NormalizationV02Error(f"source manifest path mismatch: {label}")
    if reference.get("sha256") != sha256_file(path):
        raise NormalizationV02Error(f"source manifest hash mismatch: {label}")


def _source_candidate_key(
    cohort: str, author_id: str | None, question_id: str, candidate_id: str
) -> str:
    if cohort == "original":
        return f"original:{question_id}:{candidate_id}"
    if author_id is None:
        raise NormalizationV02Error("crossed candidate lacks an author identity")
    return f"crossed:{author_id}:{question_id}:{candidate_id}"


def _candidate_binding(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_candidate_key": source["source_candidate_key"],
        "source_cohort": source["source_cohort"],
        "source_author_id": source["source_author_id"],
        "question_id": source["record"]["question_id"],
        "family_id": source["record"]["family_id"],
        "producer_partition": source["record"]["producer_partition"],
        "candidate_id": source["record"]["candidate_id"],
        "target_backbone_variant_id": source["record"][
            "target_backbone_variant_id"
        ],
        "source_v0_1_normalization_sha256": source[
            "source_v0_1_normalization_sha256"
        ],
        "source_projection_sha256": source["record"]["source_projection_sha256"],
    }


def _load_source_candidates(args: argparse.Namespace) -> list[dict[str, Any]]:
    original_manifest = read_json(args.original_manifest)
    crossed_manifest = read_json(args.crossed_manifest)
    if original_manifest.get("schema_version") != (
        "operator_equivalence_normalization_run_manifest_v0_1"
    ):
        raise NormalizationV02Error("original v0.1 manifest version mismatch")
    if crossed_manifest.get("schema_version") != (
        "operator_equivalence_crossed_author_sensitivity_run_manifest_v0_1"
    ):
        raise NormalizationV02Error("crossed-author v0.1 manifest version mismatch")
    _verify_manifest_output(
        original_manifest, "normalized_candidates", args.original_normalized
    )
    _verify_manifest_output(
        crossed_manifest, "normalized_candidates", args.crossed_normalized
    )
    _verify_manifest_output(
        crossed_manifest, "question_comparisons", args.crossed_comparisons
    )

    collections = (
        ("original", args.original_normalized),
        ("crossed_author", args.crossed_normalized),
    )
    sources: list[dict[str, Any]] = []
    for cohort, path in collections:
        for record in iter_json_records(path):
            if record.get("schema_version") != v01.NORMALIZATION_SCHEMA_VERSION:
                raise NormalizationV02Error("source v0.1 normalization version mismatch")
            projection = record.get("reversibility_ledger", {}).get(
                "structural_projection"
            )
            if not isinstance(projection, dict):
                raise NormalizationV02Error("source record lacks a structural projection")
            if canonical_json_sha256(projection) != record.get("source_projection_sha256"):
                raise NormalizationV02Error("source projection hash mismatch")
            v01._assert_label_free_projection(projection)
            author_id = None
            if cohort == "crossed_author":
                author_id = AUTHOR_BY_PRODUCER.get(record.get("producer_partition"))
                if author_id is None or f":{author_id}:" not in record.get(
                    "normalization_id", ""
                ):
                    raise NormalizationV02Error(
                        "crossed candidate producer/author identity mismatch"
                    )
            key = _source_candidate_key(
                cohort,
                author_id,
                record["question_id"],
                record["candidate_id"],
            )
            sources.append(
                {
                    "source_candidate_key": key,
                    "source_cohort": cohort,
                    "source_author_id": author_id,
                    "source_v0_1_normalization_sha256": canonical_json_sha256(record),
                    "record": record,
                    "projection": projection,
                }
            )
    counts = Counter(source["source_cohort"] for source in sources)
    if counts != Counter(
        {
            "original": EXPECTED_ORIGINAL_CANDIDATES,
            "crossed_author": EXPECTED_CROSSED_CANDIDATES,
        }
    ):
        raise NormalizationV02Error(f"source candidate count mismatch: {dict(counts)}")
    keys = [source["source_candidate_key"] for source in sources]
    if len(keys) != EXPECTED_CANDIDATES or len(keys) != len(set(keys)):
        raise NormalizationV02Error("source candidate keys are not 127 unique values")
    return sources


def _edge_records(
    edges: Iterable[tuple[str, str]], canonical_map: dict[str, str]
) -> list[dict[str, str]]:
    return [
        {
            "source_node_id": canonical_map[source],
            "target_node_id": canonical_map[target],
        }
        for source, target in sorted(
            edges, key=lambda edge: (canonical_map[edge[0]], canonical_map[edge[1]])
        )
    ]


def _mapping_indexes(
    projection: dict[str, Any], target_ids: set[str], operator_ids: set[str]
) -> tuple[dict[str, set[str]], dict[str, set[str]], Counter[str]]:
    backbone_to_operators: dict[str, set[str]] = defaultdict(set)
    operator_to_backbones: dict[str, set[str]] = defaultdict(set)
    mapping_kinds: Counter[str] = Counter()
    for mapping in projection["semantic_to_operator_mappings"]:
        mapping_kinds[mapping["mapping_kind"]] += 1
        for backbone in mapping["backbone_node_ids"]:
            if backbone not in target_ids:
                raise NormalizationV02Error("mapping references unknown semantic node")
            for operator in mapping["operator_node_ids"]:
                if operator not in operator_ids:
                    raise NormalizationV02Error("mapping references unknown operator node")
                backbone_to_operators[backbone].add(operator)
                operator_to_backbones[operator].add(backbone)
    return backbone_to_operators, operator_to_backbones, mapping_kinds


def _candidate_precedes(
    source: str,
    target: str,
    backbone_to_operators: dict[str, set[str]],
    operator_reachability: set[tuple[str, str]],
    *,
    allow_fusion: bool,
) -> bool:
    return any(
        (allow_fusion and source_operator == target_operator)
        or (source_operator, target_operator) in operator_reachability
        for source_operator in backbone_to_operators.get(source, set())
        for target_operator in backbone_to_operators.get(target, set())
    )


def _semantic_profile(
    projection: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    target = projection["target_semantic_topology"]
    target_ids_list, target_edges = v01._graph_parts(target)
    target_ids = set(target_ids_list)
    target_reduced = v01.transitive_reduction(target_ids_list, target_edges)
    target_reachability = v01._reachability(target_ids_list, target_edges)
    target_quotient, canonical_map = v01.canonicalize_semantic_graph(target)

    operator_graph = projection["operator_topology"]
    operator_ids_list, operator_edges = v01._graph_parts(operator_graph)
    operator_ids = set(operator_ids_list)
    operator_reachability = v01._reachability(operator_ids_list, operator_edges)
    backbone_to_operators, operator_to_backbones, mapping_kinds = _mapping_indexes(
        projection, target_ids, operator_ids
    )

    declared_unsupported = set(projection["unsupported_target_backbone_node_ids"])
    if not declared_unsupported <= target_ids:
        raise NormalizationV02Error("unsupported semantic node is unknown")
    supported = set(backbone_to_operators) - declared_unsupported
    missing = target_ids - supported

    preserved_required = {
        edge
        for edge in target_reduced
        if edge[0] in supported
        and edge[1] in supported
        and _candidate_precedes(
            edge[0],
            edge[1],
            backbone_to_operators,
            operator_reachability,
            allow_fusion=True,
        )
    }
    missing_required = target_reduced - preserved_required
    extra_dependencies = {
        (source, target_node)
        for source in supported
        for target_node in supported
        if source != target_node
        and (source, target_node) not in target_reachability
        and _candidate_precedes(
            source,
            target_node,
            backbone_to_operators,
            operator_reachability,
            allow_fusion=False,
        )
    }

    operator_outputs = set(operator_graph["output_node_ids"])
    target_outputs = set(target["output_node_ids"])
    mapped_outputs = {
        semantic
        for semantic in target_outputs & supported
        if backbone_to_operators[semantic] & operator_outputs
    }
    missing_outputs = target_outputs - mapped_outputs
    semantic_operator_outputs = operator_outputs & set(operator_to_backbones)
    unmapped_operator_outputs = operator_outputs - set(operator_to_backbones)

    quotient_nodes = {node["node_id"]: node for node in target_quotient["nodes"]}
    supported_nodes = []
    for canonical_id in sorted(canonical_map[node] for node in supported):
        original_id = next(
            node for node, mapped in canonical_map.items() if mapped == canonical_id
        )
        dependencies = sorted(
            canonical_map[source]
            for source, target_node in preserved_required
            if target_node == original_id
        )
        supported_nodes.append(
            {
                "node_id": canonical_id,
                "role": quotient_nodes[canonical_id]["role"],
                "depends_on": dependencies,
            }
        )

    profile_payload = {
        "canonicalization": (
            "candidate_support_output_and_dependency_profile_over_canonical_target_v0_2"
        ),
        "target_semantic_quotient_sha256": target_quotient["signature_sha256"],
        "supported_semantic_nodes": supported_nodes,
        "supported_entry_node_ids": sorted(
            canonical_map[node] for node in set(target["entry_node_ids"]) & supported
        ),
        "supported_output_node_ids": sorted(
            canonical_map[node] for node in mapped_outputs
        ),
        "missing_semantic_node_ids": sorted(canonical_map[node] for node in missing),
        "missing_output_node_ids": sorted(
            canonical_map[node] for node in missing_outputs
        ),
        "preserved_required_dependencies": _edge_records(
            preserved_required, canonical_map
        ),
        "missing_required_dependencies": _edge_records(
            missing_required, canonical_map
        ),
        "extra_candidate_dependencies": _edge_records(
            extra_dependencies, canonical_map
        ),
    }
    profile = {
        **profile_payload,
        "signature_sha256": canonical_json_sha256(profile_payload),
    }
    facts = {
        "target_ids": target_ids,
        "target_outputs": target_outputs,
        "target_quotient": target_quotient,
        "canonical_map": canonical_map,
        "operator_ids": operator_ids,
        "operator_reachability": operator_reachability,
        "backbone_to_operators": backbone_to_operators,
        "operator_to_backbones": operator_to_backbones,
        "mapping_kinds": mapping_kinds,
        "supported": supported,
        "missing": missing,
        "missing_required": missing_required,
        "extra_dependencies": extra_dependencies,
        "mapped_outputs": mapped_outputs,
        "missing_outputs": missing_outputs,
        "semantic_operator_outputs": semantic_operator_outputs,
        "unmapped_operator_outputs": unmapped_operator_outputs,
    }
    return profile, facts, target_quotient


def _counted_records(counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {**json.loads(key), "count": count}
        for key, count in sorted(counter.items())
    ]


def _counter_key(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _canonical_semantic_ids(
    operator_ids: Iterable[str],
    operator_to_backbones: dict[str, set[str]],
    canonical_map: dict[str, str],
) -> list[str]:
    return sorted(
        {
            canonical_map[semantic]
            for operator in operator_ids
            for semantic in operator_to_backbones.get(operator, set())
        }
    )


def _factor_adapter(
    projection: dict[str, Any], facts: dict[str, Any]
) -> dict[str, Any]:
    operator_graph = projection["operator_topology"]
    operator_nodes = {node["node_id"]: node for node in operator_graph["nodes"]}
    roles = {node_id: set(node["roles"]) for node_id, node in operator_nodes.items()}
    operator_to_backbones = facts["operator_to_backbones"]
    canonical_map = facts["canonical_map"]
    reachability = facts["operator_reachability"]
    semantic_operators = set(operator_to_backbones)

    modality_counter: Counter[str] = Counter()
    for slot in projection["typed_unresolved_slots"]:
        modality_counter[
            _counter_key(
                {
                    "environment_modality": slot["environment_modality"],
                    "cardinality": slot["cardinality"],
                }
            )
        ] += 1
    modality_payload = {
        "typed_slot_multiset": _counted_records(modality_counter),
    }
    modality_component = {
        **modality_payload,
        "signature_sha256": canonical_json_sha256(modality_payload),
    }

    placement_counter: Counter[str] = Counter()
    access_operator_ids = {
        operator
        for operator, node_roles in roles.items()
        if "environment_extension" in node_roles
    }
    for operator in access_operator_ids:
        fused_semantics = _canonical_semantic_ids(
            [operator], operator_to_backbones, canonical_map
        )
        upstream_operators = {
            semantic_operator
            for semantic_operator in semantic_operators
            if semantic_operator != operator
            and (semantic_operator, operator) in reachability
        }
        downstream_operators = {
            semantic_operator
            for semantic_operator in semantic_operators
            if semantic_operator != operator
            and (operator, semantic_operator) in reachability
        }
        placement_counter[
            _counter_key(
                {
                    "access_mode": "fused" if fused_semantics else "explicit",
                    "fused_semantic_node_ids": fused_semantics,
                    "upstream_semantic_node_ids": _canonical_semantic_ids(
                        upstream_operators, operator_to_backbones, canonical_map
                    ),
                    "downstream_semantic_node_ids": _canonical_semantic_ids(
                        downstream_operators, operator_to_backbones, canonical_map
                    ),
                }
            )
        ] += 1
    placement_payload = {
        "semantic_relative_access_multiset": _counted_records(placement_counter),
    }
    placement_component = {
        **placement_payload,
        "signature_sha256": canonical_json_sha256(placement_payload),
    }

    boundary_counter: Counter[str] = Counter()
    for mapping in projection["semantic_to_operator_mappings"]:
        mapped_operators = mapping["operator_node_ids"]
        boundary_counter[
            _counter_key(
                {
                    "mapping_kind": mapping["mapping_kind"],
                    "semantic_node_ids": sorted(
                        canonical_map[node] for node in mapping["backbone_node_ids"]
                    ),
                    "operator_node_count": len(mapped_operators),
                    "environment_extension_operator_count": sum(
                        "environment_extension" in roles[operator]
                        for operator in mapped_operators
                    ),
                }
            )
        ] += 1
    boundary_payload = {
        "semantic_operator_boundary_multiset": _counted_records(boundary_counter),
    }
    boundary_component = {
        **boundary_payload,
        "signature_sha256": canonical_json_sha256(boundary_payload),
    }

    output_payload = {
        "target_output_node_ids": sorted(
            canonical_map[node] for node in facts["target_outputs"]
        ),
        "mapped_output_node_ids": sorted(
            canonical_map[node] for node in facts["mapped_outputs"]
        ),
        "operator_output_arity": len(operator_graph["output_node_ids"]),
        "semantic_operator_output_arity": len(facts["semantic_operator_outputs"]),
        "unmapped_operator_output_count": len(facts["unmapped_operator_outputs"]),
    }
    output_component = {
        **output_payload,
        "signature_sha256": canonical_json_sha256(output_payload),
    }

    components = {
        "modality_cardinality": modality_component,
        "semantic_relative_placement": placement_component,
        "split_fuse_boundary": boundary_component,
        "output_arity": output_component,
    }
    component_signatures = {
        name: components[name]["signature_sha256"] for name in COMPONENT_NAMES
    }
    coverage = {
        "typed_slot_source_count": len(projection["typed_unresolved_slots"]),
        "typed_slot_classified_count": sum(modality_counter.values()),
        "access_operator_source_count": len(access_operator_ids),
        "access_operator_classified_count": sum(placement_counter.values()),
        "mapping_source_count": len(projection["semantic_to_operator_mappings"]),
        "mapping_classified_count": sum(boundary_counter.values()),
        "operator_output_source_count": len(operator_graph["output_node_ids"]),
        "operator_output_classified_count": (
            len(facts["semantic_operator_outputs"])
            + len(facts["unmapped_operator_outputs"])
        ),
    }
    coverage["all_source_elements_classified"] = all(
        [
            coverage["typed_slot_source_count"]
            == coverage["typed_slot_classified_count"],
            coverage["access_operator_source_count"]
            == coverage["access_operator_classified_count"],
            coverage["mapping_source_count"] == coverage["mapping_classified_count"],
            coverage["operator_output_source_count"]
            == coverage["operator_output_classified_count"],
        ]
    )
    overall_payload = {"component_signatures": component_signatures}
    return {
        "components": components,
        "component_signatures": component_signatures,
        "overall_signature_sha256": canonical_json_sha256(overall_payload),
        "classification_coverage": coverage,
    }


def normalize_projection_v0_2(
    projection: dict[str, Any], source_metadata: dict[str, Any]
) -> dict[str, Any]:
    v01._assert_label_free_projection(projection)
    profile, facts, _ = _semantic_profile(projection)
    adapter = _factor_adapter(projection, facts)
    operator_graph = projection["operator_topology"]
    complete_node_coverage = (
        projection["coverage_status"] == "complete_for_target_variant"
        and not facts["missing"]
    )
    dependency_preserved = not facts["missing_required"]
    no_extra_dependencies = not facts["extra_dependencies"]
    mapped_output_coverage_complete = not facts["missing_outputs"]
    output_arity_preserved = (
        len(operator_graph["output_node_ids"]) == len(facts["target_outputs"])
        and len(facts["semantic_operator_outputs"]) == len(facts["target_outputs"])
        and not facts["unmapped_operator_outputs"]
    )

    ineligible_reasons: list[str] = []
    if not complete_node_coverage:
        ineligible_reasons.append("incomplete_semantic_node_coverage")
    if not dependency_preserved:
        ineligible_reasons.append("required_semantic_dependency_missing")
    if not mapped_output_coverage_complete:
        ineligible_reasons.append("mapped_semantic_output_coverage_incomplete")
    if not output_arity_preserved:
        ineligible_reasons.append("operator_output_arity_or_mapping_not_preserved")

    provisional_reasons: list[str] = []
    if not no_extra_dependencies:
        provisional_reasons.append("candidate_adds_non_target_semantic_dependency")
    if any(
        slot["cardinality"] == "unknown"
        for slot in projection["typed_unresolved_slots"]
    ):
        provisional_reasons.append("unknown_cardinality_requires_later_grounding")
    if any(
        item["access_mode"] == "explicit"
        and not item["upstream_semantic_node_ids"]
        and not item["downstream_semantic_node_ids"]
        for item in adapter["components"]["semantic_relative_placement"][
            "semantic_relative_access_multiset"
        ]
    ):
        provisional_reasons.append("disconnected_explicit_access_requires_review")
    if not adapter["classification_coverage"]["all_source_elements_classified"]:
        provisional_reasons.append("adapter_source_element_unclassified")

    if ineligible_reasons:
        status = "ineligible"
    elif provisional_reasons:
        status = "provisional_only"
    else:
        status = "full_eligible"
    included = status == "full_eligible"
    failure_payload = {
        "status": status,
        "ineligible_reasons": sorted(ineligible_reasons),
        "provisional_reasons": sorted(provisional_reasons),
        "missing_semantic_node_ids": profile["missing_semantic_node_ids"],
        "missing_output_node_ids": profile["missing_output_node_ids"],
        "missing_required_dependencies": profile["missing_required_dependencies"],
        "extra_candidate_dependencies": profile["extra_candidate_dependencies"],
    }
    eligibility = {
        "status": status,
        "included_in_full_eligible_semantic_set": included,
        "source_coverage_status": projection["coverage_status"],
        "complete_semantic_node_coverage": complete_node_coverage,
        "required_dependencies_preserved": dependency_preserved,
        "no_extra_candidate_dependencies": no_extra_dependencies,
        "mapped_output_coverage_complete": mapped_output_coverage_complete,
        "output_arity_preserved": output_arity_preserved,
        "ineligible_reasons": sorted(ineligible_reasons),
        "provisional_reasons": sorted(provisional_reasons),
        "failure_profile_sha256": canonical_json_sha256(failure_payload),
    }
    projection_sha256 = canonical_json_sha256(projection)
    if projection_sha256 != source_metadata["source_projection_sha256"]:
        raise NormalizationV02Error("v0.2 source projection binding mismatch")
    return {
        "schema_version": NORMALIZATION_SCHEMA_VERSION,
        "normalization_id": (
            f"operator_equivalence_normalization_v0_2:"
            f"{source_metadata['source_candidate_key']}"
        ),
        "source_candidate_key": source_metadata["source_candidate_key"],
        "source_cohort": source_metadata["source_cohort"],
        "source_author_id": source_metadata["source_author_id"],
        "question_id": projection["question_id"],
        "family_id": projection["family_id"],
        "producer_partition": projection["producer_partition"],
        "candidate_id": projection["candidate_id"],
        "target_backbone_variant_id": projection["target_backbone_variant_id"],
        "source_v0_1_normalization_sha256": source_metadata[
            "source_v0_1_normalization_sha256"
        ],
        "source_v0_1_equivalence_status": source_metadata[
            "source_v0_1_equivalence_status"
        ],
        "source_projection_sha256": projection_sha256,
        "candidate_semantic_profile": profile,
        "equivalence_eligibility": eligibility,
        "factorized_environment_adapter": adapter,
        "reversibility_ledger": {
            "source_structural_projection": projection,
            "reconstruction_sha256": projection_sha256,
            "reconstruction_verified": (
                canonical_json_sha256(projection) == projection_sha256
            ),
        },
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }


def _normalize_source(source: dict[str, Any]) -> dict[str, Any]:
    record = source["record"]
    metadata = {
        **_candidate_binding(source),
        "source_v0_1_equivalence_status": record["equivalence_assessment"]["status"],
    }
    return normalize_projection_v0_2(source["projection"], metadata)


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 1.0


def _record_sets(records: list[dict[str, Any]]) -> dict[str, Any]:
    full = [
        record
        for record in records
        if record["equivalence_eligibility"][
            "included_in_full_eligible_semantic_set"
        ]
    ]
    contamination = sum(
        record["equivalence_eligibility"]["status"] != "full_eligible"
        for record in full
    )
    return {
        "candidate_count": len(records),
        "full_eligible_candidate_count": len(full),
        "provisional_candidate_count": sum(
            record["equivalence_eligibility"]["status"] == "provisional_only"
            for record in records
        ),
        "ineligible_candidate_count": sum(
            record["equivalence_eligibility"]["status"] == "ineligible"
            for record in records
        ),
        "full_eligible_member_keys": sorted(
            record["source_candidate_key"] for record in full
        ),
        "full_eligible_semantic_set": sorted(
            {
                record["candidate_semantic_profile"]["signature_sha256"]
                for record in full
            }
        ),
        "provisional_semantic_profile_set": sorted(
            {
                record["candidate_semantic_profile"]["signature_sha256"]
                for record in records
                if record["equivalence_eligibility"]["status"]
                == "provisional_only"
            }
        ),
        "ineligible_failure_profile_set": sorted(
            {
                record["equivalence_eligibility"]["failure_profile_sha256"]
                for record in records
                if record["equivalence_eligibility"]["status"] == "ineligible"
            }
        ),
        "full_eligible_adapter_component_sets": {
            component: sorted(
                {
                    record["factorized_environment_adapter"][
                        "component_signatures"
                    ][component]
                    for record in full
                }
            )
            for component in COMPONENT_NAMES
        },
        "full_eligible_overall_adapter_set": sorted(
            {
                record["factorized_environment_adapter"][
                    "overall_signature_sha256"
                ]
                for record in full
            }
        ),
        "eligible_set_contamination_count": contamination,
    }


def _original_question_sets(
    normalized: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in normalized:
        if record["source_cohort"] == "original":
            grouped[record["question_id"]].append(record)
    question_sets = []
    for question_id, records in sorted(grouped.items()):
        sets = _record_sets(records)
        question_sets.append(
            {
                "schema_version": "operator_equivalence_original_question_set_v0_2",
                "question_id": question_id,
                "family_id": records[0]["family_id"],
                "producer_partition": records[0]["producer_partition"],
                **sets,
                "full_eligible_semantic_set_sha256": canonical_json_sha256(
                    sets["full_eligible_semantic_set"]
                ),
                "component_set_sha256": {
                    component: canonical_json_sha256(
                        sets["full_eligible_adapter_component_sets"][component]
                    )
                    for component in COMPONENT_NAMES
                },
                "candidate1_preferred": False,
            }
        )
    if len(question_sets) != EXPECTED_ORIGINAL_QUESTIONS:
        raise NormalizationV02Error("original question set count mismatch")
    return question_sets


def _original_family_sets(
    question_sets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in question_sets:
        grouped[record["family_id"]].append(record)
    families = []
    for family_id, records in sorted(grouped.items()):
        semantic_profiles = Counter(
            record["full_eligible_semantic_set_sha256"] for record in records
        )
        component_profiles = {
            component: Counter(
                record["component_set_sha256"][component] for record in records
            )
            for component in COMPONENT_NAMES
        }
        families.append(
            {
                "schema_version": "operator_equivalence_original_family_set_v0_2",
                "family_id": family_id,
                "question_count": len(records),
                "producer_partitions": sorted(
                    {record["producer_partition"] for record in records}
                ),
                "full_eligible_semantic_set_profiles": [
                    {"set_sha256": signature, "question_count": count}
                    for signature, count in sorted(semantic_profiles.items())
                ],
                "component_set_profiles": {
                    component: [
                        {"set_sha256": signature, "question_count": count}
                        for signature, count in sorted(profiles.items())
                    ]
                    for component, profiles in component_profiles.items()
                },
                "full_eligible_semantic_set_stable": len(semantic_profiles) == 1,
                "component_set_stable": {
                    component: len(profiles) == 1
                    for component, profiles in component_profiles.items()
                },
            }
        )
    if len(families) != EXPECTED_ORIGINAL_FAMILIES:
        raise NormalizationV02Error("original family set count mismatch")
    return families


def _crossed_metadata(args: argparse.Namespace) -> dict[str, dict[str, Any]]:
    records = list(iter_json_records(args.crossed_comparisons))
    if len(records) != EXPECTED_CROSSED_QUESTIONS:
        raise NormalizationV02Error("crossed v0.1 comparison count mismatch")
    result = {}
    for record in records:
        result[record["question_id"]] = {
            "selection_role": record["selection_role"],
            "original_e2_producer_partition": record[
                "original_e2_producer_partition"
            ],
        }
    if len(result) != EXPECTED_CROSSED_QUESTIONS:
        raise NormalizationV02Error("crossed comparison question IDs are duplicated")
    return result


def _crossed_question_comparisons(
    args: argparse.Namespace,
    normalized: list[dict[str, Any]],
    validator: Draft202012Validator,
) -> list[dict[str, Any]]:
    metadata = _crossed_metadata(args)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in normalized:
        if record["source_cohort"] == "crossed_author":
            grouped[(record["question_id"], record["source_author_id"])].append(
                record
            )
    comparisons = []
    for question_id, question_metadata in metadata.items():
        author_results = []
        sets_by_author = []
        for author_id in ("crossed_author_01", "crossed_author_02"):
            records = grouped.get((question_id, author_id), [])
            if not records:
                raise NormalizationV02Error(
                    f"crossed author lacks records for {question_id}: {author_id}"
                )
            sets = _record_sets(records)
            author_results.append({"author_id": author_id, **sets})
            sets_by_author.append(sets)
        left, right = sets_by_author
        left_semantic = set(left["full_eligible_semantic_set"])
        right_semantic = set(right["full_eligible_semantic_set"])
        component_agreement = {}
        for component in COMPONENT_NAMES:
            left_set = set(
                left["full_eligible_adapter_component_sets"][component]
            )
            right_set = set(
                right["full_eligible_adapter_component_sets"][component]
            )
            component_agreement[component] = {
                "exact_match": left_set == right_set,
                "jaccard": _jaccard(left_set, right_set),
            }
        comparison = {
            "schema_version": "operator_equivalence_crossed_comparison_v0_2",
            "question_id": question_id,
            **question_metadata,
            "author_results": author_results,
            "full_eligible_semantic_set_exact_match": (
                left_semantic == right_semantic
            ),
            "full_eligible_semantic_set_jaccard": _jaccard(
                left_semantic, right_semantic
            ),
            "component_agreement": component_agreement,
            "overall_adapter_exact_match": (
                set(left["full_eligible_overall_adapter_set"])
                == set(right["full_eligible_overall_adapter_set"])
            ),
            "overall_adapter_jaccard": _jaccard(
                set(left["full_eligible_overall_adapter_set"]),
                set(right["full_eligible_overall_adapter_set"]),
            ),
            "eligible_set_contamination_count": (
                left["eligible_set_contamination_count"]
                + right["eligible_set_contamination_count"]
            ),
            "candidate1_preferred": False,
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
        errors = sorted(validator.iter_errors(comparison), key=lambda e: list(e.path))
        if errors:
            raise NormalizationV02Error(
                f"crossed comparison schema failure {question_id}: {errors[0].message}"
            )
        comparisons.append(comparison)
    return comparisons


def _signature_concentration(
    normalized: list[dict[str, Any]], signature_getter: Any
) -> dict[str, Any]:
    by_signature: dict[str, Counter[str]] = defaultdict(Counter)
    producer_counts: Counter[str] = Counter()
    for record in normalized:
        producer = record["producer_partition"]
        signature = signature_getter(record)
        by_signature[signature][producer] += 1
        producer_counts[producer] += 1
    total = sum(producer_counts.values())
    weighted_purity = (
        sum(max(counts.values()) for counts in by_signature.values()) / total
    )
    majority_baseline = max(producer_counts.values()) / total
    normalized_lift = (
        (weighted_purity - majority_baseline) / (1.0 - majority_baseline)
        if majority_baseline < 1.0
        else 0.0
    )
    singleton_candidates = sum(
        sum(counts.values()) for counts in by_signature.values() if sum(counts.values()) == 1
    )
    return {
        "method": "weighted_signature_partition_purity_descriptive_not_causal",
        "candidate_count": total,
        "signature_count": len(by_signature),
        "producer_majority_baseline": majority_baseline,
        "weighted_partition_purity": weighted_purity,
        "normalized_purity_lift": normalized_lift,
        "singleton_signature_candidate_fraction": singleton_candidates / total,
    }


def _producer_predictiveness(normalized: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "candidate_semantic_profile": _signature_concentration(
            normalized,
            lambda record: record["candidate_semantic_profile"]["signature_sha256"],
        ),
        "overall_factorized_adapter": _signature_concentration(
            normalized,
            lambda record: record["factorized_environment_adapter"][
                "overall_signature_sha256"
            ],
        ),
        "adapter_components": {
            component: _signature_concentration(
                normalized,
                lambda record, component=component: record[
                    "factorized_environment_adapter"
                ]["component_signatures"][component],
            )
            for component in COMPONENT_NAMES
        },
        "interpretation": (
            "signature concentration reflects producer association under the observed "
            "design; it is not causal attribution or semantic correctness"
        ),
    }


def _component_record_max(record: dict[str, Any]) -> int:
    components = record["factorized_environment_adapter"]["components"]
    return max(
        len(components["modality_cardinality"]["typed_slot_multiset"]),
        len(
            components["semantic_relative_placement"][
                "semantic_relative_access_multiset"
            ]
        ),
        len(
            components["split_fuse_boundary"][
                "semantic_operator_boundary_multiset"
            ]
        ),
        1,
    )


def _metrics(
    normalized: list[dict[str, Any]],
    question_sets: list[dict[str, Any]],
    family_sets: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    plan: dict[str, Any],
) -> dict[str, Any]:
    statuses = Counter(
        record["equivalence_eligibility"]["status"] for record in normalized
    )
    cohort_statuses: dict[str, dict[str, int]] = {}
    for cohort in ("original", "crossed_author"):
        cohort_statuses[cohort] = dict(
            sorted(
                Counter(
                    record["equivalence_eligibility"]["status"]
                    for record in normalized
                    if record["source_cohort"] == cohort
                ).items()
            )
        )
    technical_loss = sum(
        not record["reversibility_ledger"]["reconstruction_verified"]
        or record["source_projection_sha256"]
        != record["reversibility_ledger"]["reconstruction_sha256"]
        for record in normalized
    )
    contamination = sum(
        record["eligible_set_contamination_count"] for record in question_sets
    ) + sum(
        record["eligible_set_contamination_count"] for record in comparisons
    )
    unclassified = sum(
        not record["factorized_environment_adapter"]["classification_coverage"][
            "all_source_elements_classified"
        ]
        for record in normalized
    )
    max_component_records = max(_component_record_max(record) for record in normalized)
    distinct_components = {
        component: len(
            {
                record["factorized_environment_adapter"]["component_signatures"][
                    component
                ]
                for record in normalized
            }
        )
        for component in COMPONENT_NAMES
    }

    semantic_exact = sum(
        record["full_eligible_semantic_set_exact_match"] for record in comparisons
    )
    mean_semantic_jaccard = sum(
        record["full_eligible_semantic_set_jaccard"] for record in comparisons
    ) / len(comparisons)
    challenge_exact = sum(
        record["full_eligible_semantic_set_exact_match"]
        and record["selection_role"] == "e1_challenge"
        for record in comparisons
    )
    control_exact = sum(
        record["full_eligible_semantic_set_exact_match"]
        and record["selection_role"] == "adequate_control"
        for record in comparisons
    )
    author_question_coverage = sum(
        author["full_eligible_candidate_count"] > 0
        for record in comparisons
        for author in record["author_results"]
    )
    component_agreement = {
        component: {
            "exact_match_count": sum(
                record["component_agreement"][component]["exact_match"]
                for record in comparisons
            ),
            "exact_match_rate": sum(
                record["component_agreement"][component]["exact_match"]
                for record in comparisons
            )
            / len(comparisons),
            "mean_jaccard": sum(
                record["component_agreement"][component]["jaccard"]
                for record in comparisons
            )
            / len(comparisons),
        }
        for component in COMPONENT_NAMES
    }
    multi_families = [record for record in family_sets if record["question_count"] > 1]
    unstable_families = [
        record
        for record in multi_families
        if not record["full_eligible_semantic_set_stable"]
    ]

    criteria = plan["frozen_decision_criteria"]
    adapter_contract_passed = all(
        [
            unclassified <= criteria["unclassified_adapter_candidate_count_max"],
            max_component_records
            <= criteria["component_records_per_candidate_max"],
            all(
                count <= criteria["distinct_signatures_per_component_max"]
                for count in distinct_components.values()
            ),
        ]
    )
    semantic_stability_passed = all(
        [
            author_question_coverage
            >= criteria["crossed_author_full_eligible_author_question_coverage_min"],
            semantic_exact / len(comparisons)
            >= criteria["crossed_full_eligible_semantic_exact_match_rate_min"],
            mean_semantic_jaccard
            >= criteria["crossed_mean_full_eligible_semantic_jaccard_min"],
            challenge_exact
            >= criteria["e1_challenge_full_eligible_semantic_exact_count_min"],
            control_exact
            >= criteria["adequate_control_full_eligible_semantic_exact_count_min"],
        ]
    )
    technical_contract_passed = all(
        [
            technical_loss <= criteria["technical_loss_count_max"],
            contamination <= criteria["eligible_set_contamination_count_max"],
        ]
    )
    if not technical_contract_passed:
        decision = criteria["branch_on_technical_or_contamination_failure"]
    elif not adapter_contract_passed:
        decision = criteria["branch_on_adapter_contract_failure"]
    elif not semantic_stability_passed:
        decision = criteria["branch_on_semantic_stability_failure"]
    else:
        decision = criteria["branch_on_pass"]

    return {
        "schema_version": "operator_equivalence_normalization_metrics_v0_2",
        "run_id": RUN_ID,
        "counts": {
            "normalized_candidates": len(normalized),
            "original_candidates": sum(
                record["source_cohort"] == "original" for record in normalized
            ),
            "crossed_author_candidates": sum(
                record["source_cohort"] == "crossed_author" for record in normalized
            ),
            "original_questions": len(question_sets),
            "original_families": len(family_sets),
            "crossed_questions": len(comparisons),
            "eligibility_status": dict(sorted(statuses.items())),
            "eligibility_status_by_cohort": cohort_statuses,
            "distinct_candidate_semantic_profiles": len(
                {
                    record["candidate_semantic_profile"]["signature_sha256"]
                    for record in normalized
                }
            ),
            "distinct_adapter_component_signatures": distinct_components,
            "distinct_overall_factorized_adapters": len(
                {
                    record["factorized_environment_adapter"][
                        "overall_signature_sha256"
                    ]
                    for record in normalized
                }
            ),
            "technical_loss": technical_loss,
            "eligible_set_contamination": contamination,
            "unclassified_adapter_candidates": unclassified,
            "max_component_records_per_candidate": max_component_records,
            "multi_question_original_families": len(multi_families),
            "unstable_multi_question_full_eligible_semantic_sets": len(
                unstable_families
            ),
            "crossed_full_eligible_semantic_exact_matches": semantic_exact,
            "crossed_e1_challenge_semantic_exact_matches": challenge_exact,
            "crossed_adequate_control_semantic_exact_matches": control_exact,
            "crossed_full_eligible_author_question_coverage": author_question_coverage,
        },
        "rates": {
            "crossed_full_eligible_semantic_exact_match": (
                semantic_exact / len(comparisons)
            ),
            "crossed_mean_full_eligible_semantic_jaccard": mean_semantic_jaccard,
            "original_multi_question_semantic_instability": (
                len(unstable_families) / len(multi_families)
                if multi_families
                else 0.0
            ),
        },
        "crossed_adapter_component_agreement": component_agreement,
        "producer_signature_concentration": _producer_predictiveness(normalized),
        "frozen_criteria": criteria,
        "criteria_results": {
            "technical_contract_passed": technical_contract_passed,
            "adapter_component_contract_passed": adapter_contract_passed,
            "crossed_semantic_stability_passed": semantic_stability_passed,
            "all_criteria_passed": (
                technical_contract_passed
                and adapter_contract_passed
                and semantic_stability_passed
            ),
        },
        "decision": decision,
        "grounding_started": False,
        "grounding_protocol_authorized_next": decision == criteria["branch_on_pass"],
        "fresh_question_ids_used": False,
        "human_evidence_created": False,
        "gold_claimed": False,
    }


def _report(metrics: dict[str, Any]) -> str:
    counts = metrics["counts"]
    statuses = counts["eligibility_status"]
    component_lines = [
        (
            f"- {component}: exact "
            f"{metrics['crossed_adapter_component_agreement'][component]['exact_match_count']}"
            f"/16, mean Jaccard "
            f"{metrics['crossed_adapter_component_agreement'][component]['mean_jaccard']:.6f}"
        )
        for component in COMPONENT_NAMES
    ]
    return "\n".join(
        [
            "# Operator equivalence normalization v0.2",
            "",
            "This deterministic revision uses only the already exposed 93 original and",
            "34 crossed-author candidates. It separates full semantic-set eligibility",
            "from candidate-sensitive semantic identity and factors adapters without",
            "using question/environment text, answers, traces, grounding, or execution.",
            "",
            "## Eligibility and integrity",
            "",
            f"- candidates: {counts['normalized_candidates']}",
            f"- full eligible: {statuses.get('full_eligible', 0)}",
            f"- provisional only: {statuses.get('provisional_only', 0)}",
            f"- ineligible: {statuses.get('ineligible', 0)}",
            f"- reversible projection loss: {counts['technical_loss']}",
            f"- eligible-set contamination: {counts['eligible_set_contamination']}",
            f"- unclassified adapter candidates: {counts['unclassified_adapter_candidates']}",
            "",
            "## Crossed-author semantic comparison",
            "",
            (
                "- full-eligible semantic-set exact match: "
                f"{counts['crossed_full_eligible_semantic_exact_matches']}/16"
            ),
            (
                "- mean full-eligible semantic-set Jaccard: "
                f"{metrics['rates']['crossed_mean_full_eligible_semantic_jaccard']:.6f}"
            ),
            (
                "- author-question pairs with a full-eligible candidate: "
                f"{counts['crossed_full_eligible_author_question_coverage']}/32"
            ),
            "",
            "## Crossed-author adapter components",
            "",
            *component_lines,
            "",
            "## Frozen branch result",
            "",
            f"`{metrics['decision']}`",
            "",
            "Grounding was not performed. Producer concentration is descriptive and",
            "does not establish causal producer effects or semantic correctness.",
            "",
        ]
    )


def _candidate_bindings(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_candidate_binding(source) for source in sources]


def build_freeze_plan(args: argparse.Namespace) -> dict[str, Any]:
    for path in _outputs(args).values():
        if path.is_symlink() or path.exists():
            raise NormalizationV02Error(
                f"planned v0.2 output exists before freeze: {_relative(path)}"
            )
    _validator(args.schema)
    _validator(args.comparison_schema)
    sources = _load_source_candidates(args)
    bindings = _candidate_bindings(sources)
    implementation_commit = git_tracked_commit_identity(
        ROOT, _contract_inputs(args).values()
    )
    source_commit = git_tracked_commit_identity(ROOT, _source_inputs(args).values())
    producer_counts = Counter(
        source["record"]["producer_partition"] for source in sources
    )
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": PLAN_ID,
        "run_id": RUN_ID,
        "status": "frozen_after_v0_1_diagnostics_before_any_v0_2_output",
        "implementation_commit": implementation_commit,
        "source_commit": source_commit,
        "contract_artifacts": {
            label: _binding(path) for label, path in _contract_inputs(args).items()
        },
        "source_artifacts": {
            label: _binding(path) for label, path in _source_inputs(args).items()
        },
        "expected_inputs": {
            "original_candidates": EXPECTED_ORIGINAL_CANDIDATES,
            "crossed_author_candidates": EXPECTED_CROSSED_CANDIDATES,
            "total_candidates": EXPECTED_CANDIDATES,
            "original_questions": EXPECTED_ORIGINAL_QUESTIONS,
            "original_families": EXPECTED_ORIGINAL_FAMILIES,
            "crossed_questions": EXPECTED_CROSSED_QUESTIONS,
            "producer_candidate_counts": dict(sorted(producer_counts.items())),
        },
        "candidate_bindings": bindings,
        "ordered_candidate_bindings_sha256": canonical_json_sha256(bindings),
        "candidate_identity_set_sha256": canonical_json_sha256(
            sorted(binding["source_candidate_key"] for binding in bindings)
        ),
        "visibility_contract": {
            "allowed": [
                "v0_1_label_free_structural_projections",
                "v0_1_deterministic_equivalence_status_for_audit",
                "opaque_candidate_question_family_and_producer_identifiers",
                "target_semantic_roles_and_topology",
                "semantic_to_operator_mappings",
                "operator_adjacency_and_backbone_or_environment_roles",
                "typed_unresolved_slot_modality_and_cardinality",
                "variation_axes",
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
                "fresh_question_ids",
            ],
        },
        "normalization_contract": {
            "semantic_identity": (
                "candidate_support_output_and_dependency_profile_over_canonical_target"
            ),
            "eligibility_states": [
                "full_eligible",
                "provisional_only",
                "ineligible",
            ],
            "full_eligible_set_membership_is_status_gated": True,
            "partial_or_output_incomplete_candidate_can_enter_full_set": False,
            "split_and_fuse_are_factorized_not_automatically_semantic_failure": True,
            "adapter_components": list(COMPONENT_NAMES),
            "modality_cardinality_referent_and_output_arity_preserved": True,
            "candidate1_preferred": False,
            "alternatives_compared_as_sets": True,
            "reversibility_required": True,
        },
        "frozen_decision_criteria": {
            "technical_loss_count_max": 0,
            "eligible_set_contamination_count_max": 0,
            "unclassified_adapter_candidate_count_max": 0,
            "component_records_per_candidate_max": 64,
            "distinct_signatures_per_component_max": 64,
            "crossed_author_full_eligible_author_question_coverage_min": 32,
            "crossed_full_eligible_semantic_exact_match_rate_min": 0.875,
            "crossed_mean_full_eligible_semantic_jaccard_min": 0.95,
            "e1_challenge_full_eligible_semantic_exact_count_min": 5,
            "adequate_control_full_eligible_semantic_exact_count_min": 8,
            "branch_on_technical_or_contamination_failure": (
                "REVISE_NORMALIZATION_V0_2_TECHNICAL_CONTRACT"
            ),
            "branch_on_adapter_contract_failure": (
                "REVISE_FACTORIZED_ADAPTER_COMPONENT_CONTRACT"
            ),
            "branch_on_semantic_stability_failure": (
                "NARROW_OR_REAUTHOR_BEFORE_GROUNDING"
            ),
            "branch_on_pass": (
                "FREEZE_FACTORIZED_ADAPTER_V0_2_FOR_GROUNDING_PROTOCOL"
            ),
        },
        "stopping_rules": [
            "never_materialize_when_any_source_or_candidate_binding_differs",
            "stop_before_grounding_on_reversible_loss_or_eligible_set_contamination",
            "stop_before_grounding_when_adapter_elements_are_unclassified_or_unbounded",
            "stop_or_narrow_before_grounding_when_crossed_full_eligible_semantics_are_unstable",
            "do_not_consume_fresh_ids_or_human_evidence_in_any_branch",
        ],
        "planned_outputs": {
            label: {"repository_relative_path": _relative(path)}
            for label, path in _outputs(args).items()
        },
    }


def _validate_plan(args: argparse.Namespace) -> dict[str, Any]:
    plan = read_json(args.plan)
    if not isinstance(plan, dict) or plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise NormalizationV02Error("v0.2 normalization plan has the wrong version")
    if plan.get("status") != (
        "frozen_after_v0_1_diagnostics_before_any_v0_2_output"
    ):
        raise NormalizationV02Error("v0.2 plan was not frozen before outputs")
    for label, path in _contract_inputs(args).items():
        if plan["contract_artifacts"].get(label) != _binding(path):
            raise NormalizationV02Error(f"plan contract binding mismatch: {label}")
    for label, path in _source_inputs(args).items():
        if plan["source_artifacts"].get(label) != _binding(path):
            raise NormalizationV02Error(f"plan source binding mismatch: {label}")
    sources = _load_source_candidates(args)
    bindings = _candidate_bindings(sources)
    if plan.get("candidate_bindings") != bindings:
        raise NormalizationV02Error("plan does not bind the exact 127 candidates")
    if plan.get("ordered_candidate_bindings_sha256") != canonical_json_sha256(
        bindings
    ):
        raise NormalizationV02Error("plan ordered candidate binding hash mismatch")
    for label, path in _outputs(args).items():
        if plan["planned_outputs"][label]["repository_relative_path"] != _relative(
            path
        ):
            raise NormalizationV02Error(f"plan output binding mismatch: {label}")
    return plan


def build_artifacts(args: argparse.Namespace) -> dict[str, tuple[Path, bytes]]:
    plan = _validate_plan(args)
    normalization_validator = _validator(args.schema)
    comparison_validator = _validator(args.comparison_schema)
    sources = _load_source_candidates(args)
    normalized = []
    checks = []
    for source in sources:
        record = _normalize_source(source)
        errors = sorted(
            normalization_validator.iter_errors(record), key=lambda e: list(e.path)
        )
        if errors:
            raise NormalizationV02Error(
                f"normalization schema failure {record['source_candidate_key']}: "
                f"{errors[0].message}"
            )
        if not record["reversibility_ledger"]["reconstruction_verified"]:
            raise NormalizationV02Error("v0.2 reversibility check failed")
        normalized.append(record)
        checks.append(
            {
                "schema_version": "operator_equivalence_normalization_check_v0_2",
                "source_candidate_key": record["source_candidate_key"],
                "status": "pass",
                "schema_valid": True,
                "projection_label_free": True,
                "reconstruction_verified": True,
                "adapter_source_elements_classified": record[
                    "factorized_environment_adapter"
                ]["classification_coverage"]["all_source_elements_classified"],
                "full_eligible_set_membership": record["equivalence_eligibility"][
                    "included_in_full_eligible_semantic_set"
                ],
            }
        )
    question_sets = _original_question_sets(normalized)
    family_sets = _original_family_sets(question_sets)
    comparisons = _crossed_question_comparisons(
        args, normalized, comparison_validator
    )
    metrics = _metrics(normalized, question_sets, family_sets, comparisons, plan)
    report = _report(metrics)

    preliminary = {
        "normalized_candidates": (args.normalized_output, jsonl_file_bytes(normalized)),
        "original_question_sets": (
            args.original_question_sets_output,
            jsonl_file_bytes(question_sets),
        ),
        "original_family_sets": (
            args.original_family_sets_output,
            jsonl_file_bytes(family_sets),
        ),
        "crossed_question_comparisons": (
            args.crossed_comparisons_output,
            jsonl_file_bytes(comparisons),
        ),
        "checks": (args.checks_output, jsonl_file_bytes(checks)),
        "metrics": (args.metrics_output, json_file_bytes(metrics)),
        "report": (args.report_output, report.encode("utf-8")),
    }
    manifest = {
        "schema_version": "operator_equivalence_normalization_run_manifest_v0_2",
        "run_id": RUN_ID,
        "plan": _binding(args.plan),
        "implementation_commit": plan["implementation_commit"],
        "source_commit": plan["source_commit"],
        "source_artifacts": plan["source_artifacts"],
        "contract_artifacts": plan["contract_artifacts"],
        "ordered_candidate_bindings_sha256": plan[
            "ordered_candidate_bindings_sha256"
        ],
        "outputs": {
            label: {
                "repository_relative_path": _relative(path),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for label, (path, payload) in preliminary.items()
        },
        "metrics_summary": metrics,
        "decision": metrics["decision"],
        "grounding_started": False,
        "validation_status": "pass",
    }
    return {
        **preliminary,
        "run_manifest": (args.manifest_output, json_file_bytes(manifest)),
    }


def validate_materialized(args: argparse.Namespace) -> dict[str, Any]:
    expected = build_artifacts(args)
    mismatches = [
        label
        for label, (path, payload) in expected.items()
        if not path.is_file() or path.read_bytes() != payload
    ]
    if mismatches:
        raise NormalizationV02Error(
            f"materialized v0.2 artifacts differ from reconstruction: {mismatches}"
        )
    metrics = read_json(args.metrics_output)
    return {
        "status": "pass",
        "mode": "validate_only",
        "candidates": metrics["counts"]["normalized_candidates"],
        "original_questions": metrics["counts"]["original_questions"],
        "crossed_questions": metrics["counts"]["crossed_questions"],
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
        elif args.build:
            statuses = write_output_batch(
                build_artifacts(args), overwrite=args.overwrite
            )
            print(json.dumps({"status": "built", "outputs": statuses}, sort_keys=True))
        else:
            print(json.dumps(validate_materialized(args), sort_keys=True))
    except (NormalizationV02Error, ValueError, OSError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
