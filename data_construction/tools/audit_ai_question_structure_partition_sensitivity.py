#!/usr/bin/env python3
"""Emit a post-hoc partition-sensitivity audit for the frozen N=100 run.

This tool reads but never rewrites the frozen extraction records or their
primary metrics/report.  Its outputs are a separately versioned sensitivity
analysis and interpretive addendum.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _common import (
    canonical_json_sha256,
    iter_json_records,
    json_file_bytes,
    read_json,
    sha256_file,
    write_output_batch,
)
import run_ai_question_structure_scale_exploration as primary


TOOL_VERSION = "ai_question_structure_partition_sensitivity_audit_tool_v0_1"
METRICS_SCHEMA_VERSION = "ai_question_structure_partition_sensitivity_metrics_v0_1"
AUDIT_ID = "ai_question_structure_scale_v0_1_run_001_partition_sensitivity_v0_1"
EXPECTED_RUN_ID = "ai_question_structure_scale_v0_1_run_001"
EXPECTED_PRIMARY_DECISION = "EXPAND_UNCHANGED_TO_N300"
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
DEFAULT_RECORDS = BASE / "run_001/records.jsonl"
DEFAULT_PRIMARY_METRICS = (
    BASE / "run_001/analysis/structural_saturation_metrics_v0_1.json"
)
DEFAULT_METRICS_OUTPUT = (
    BASE / "run_001/analysis/partition_sensitivity_metrics_v0_1.json"
)
DEFAULT_ADDENDUM_OUTPUT = BASE / "run_001/analysis/interpretive_addendum_v0_1.md"


class AuditError(ValueError):
    """Raised when the post-hoc audit input contract is not satisfied."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--primary-metrics", type=Path, default=DEFAULT_PRIMARY_METRICS)
    parser.add_argument("--prefix-count", type=int, default=30)
    parser.add_argument("--metrics-output", type=Path, default=DEFAULT_METRICS_OUTPUT)
    parser.add_argument("--addendum-output", type=Path, default=DEFAULT_ADDENDUM_OUTPUT)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace differing audit outputs; frozen primary inputs are never writable.",
    )
    return parser.parse_args(argv)


def _require_regular_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise AuditError(f"{label} must be an existing regular non-symlink file: {path}")


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise AuditError(f"audit artifact is outside the repository: {path}") from exc


def _input_binding(path: Path, *, record_count: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "repository_relative_path": _relative(path),
        "sha256": sha256_file(path),
    }
    if record_count is not None:
        value["record_count"] = record_count
    return value


def _graph_parts(graph: dict[str, Any]) -> tuple[dict[str, str], set[tuple[str, str]]]:
    labels = {node["node_id"]: node["role"] for node in graph["nodes"]}
    edges = {
        (dependency, node["node_id"])
        for node in graph["nodes"]
        for dependency in node["depends_on"]
    }
    return labels, edges


def _signature(record: dict[str, Any], mode: str) -> str | None:
    graph = record.get("primary_graph")
    if not isinstance(graph, dict):
        return None
    return canonical_json_sha256(primary.canonical_graph(graph, mode))


def partition_profiles(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for position, record in enumerate(records, start=1):
        grouped[str(record["producer_partition"])].append((position, record))
    output: list[dict[str, Any]] = []
    for partition in sorted(grouped):
        positioned = grouped[partition]
        partition_records = [record for _, record in positioned]
        node_counts = [
            len(record["primary_graph"]["nodes"])
            for record in partition_records
            if isinstance(record.get("primary_graph"), dict)
        ]
        descriptions = [
            node["description"]
            for record in partition_records
            if isinstance(record.get("primary_graph"), dict)
            for node in record["primary_graph"]["nodes"]
        ]
        uncertain_count = sum(record["status"] == "uncertain" for record in partition_records)
        output.append(
            {
                "producer_partition": partition,
                "committed_positions": [positioned[0][0], positioned[-1][0]],
                "record_count": len(partition_records),
                "uncertain_count": uncertain_count,
                "uncertain_rate": uncertain_count / len(partition_records),
                "mean_primary_node_count": statistics.mean(node_counts) if node_counts else None,
                "uppercase_initial_node_description_count": sum(
                    bool(text) and text[0].isupper() for text in descriptions
                ),
                "node_description_count": len(descriptions),
                "uppercase_initial_node_description_rate": (
                    sum(bool(text) and text[0].isupper() for text in descriptions)
                    / len(descriptions)
                    if descriptions
                    else None
                ),
            }
        )
    return output


def recurring_new_contracted_families(
    records: list[dict[str, Any]], prefix_count: int
) -> dict[str, Any]:
    signatures = [_signature(record, "contracted") for record in records]
    prefix = {value for value in signatures[:prefix_count] if isinstance(value, str)}
    new_counts = Counter(
        value
        for value in signatures[prefix_count:]
        if isinstance(value, str) and value not in prefix
    )
    qualifying = sorted(signature for signature, count in new_counts.items() if count >= 2)
    families: list[dict[str, Any]] = []
    for signature in qualifying:
        members = [
            (position, record)
            for position, (record, value) in enumerate(zip(records, signatures), start=1)
            if value == signature
        ]
        support = Counter(str(record["producer_partition"]) for _, record in members)
        families.append(
            {
                "signature": signature,
                "new_expansion_question_count": new_counts[signature],
                "question_ids": [record["question_id"] for _, record in members],
                "committed_positions": [position for position, _ in members],
                "partition_support": dict(sorted(support.items())),
                "partition_support_count": len(support),
                "recurs_across_partitions": len(support) >= 2,
            }
        )
    cross_partition = sum(family["recurs_across_partitions"] for family in families)
    return {
        "prefix_count": prefix_count,
        "new_expansion_count": len(records) - prefix_count,
        "recurring_new_contracted_family_count": len(families),
        "cross_partition_recurring_new_contracted_family_count": cross_partition,
        "all_recurring_new_contracted_families_are_partition_local": bool(families)
        and cross_partition == 0,
        "families": families,
    }


def _graph_profile(
    records: list[dict[str, Any]], *, reduce_transitive_edges: bool
) -> dict[str, Any]:
    edge_counts: list[int] = []
    branch_ids: list[str] = []
    join_ids: list[str] = []
    for record in records:
        graph = record.get("primary_graph")
        if not isinstance(graph, dict):
            continue
        _, edges = _graph_parts(graph)
        if reduce_transitive_edges:
            edges = primary.transitive_reduction(edges)
        edge_counts.append(len(edges))
        outdegree = Counter(source for source, _ in edges)
        indegree = Counter(target for _, target in edges)
        if any(value > 1 for value in outdegree.values()):
            branch_ids.append(record["question_id"])
        if any(value > 1 for value in indegree.values()):
            join_ids.append(record["question_id"])
    return {
        "representable_question_count": len(edge_counts),
        "mean_edge_count": statistics.mean(edge_counts) if edge_counts else None,
        "branch_question_count": len(branch_ids),
        "branch_question_ids": branch_ids,
        "join_question_count": len(join_ids),
        "join_question_ids": join_ids,
    }


def raw_vs_reduced_graph_profile(records: list[dict[str, Any]]) -> dict[str, Any]:
    raw = _graph_profile(records, reduce_transitive_edges=False)
    reduced = _graph_profile(records, reduce_transitive_edges=True)
    removed_ids: list[str] = []
    removed_count = 0
    for record in records:
        graph = record.get("primary_graph")
        if not isinstance(graph, dict):
            continue
        _, edges = _graph_parts(graph)
        reduced_edges = primary.transitive_reduction(edges)
        difference = len(edges) - len(reduced_edges)
        if difference:
            removed_ids.append(record["question_id"])
            removed_count += difference
    return {
        "raw_declared_dependencies": raw,
        "transitive_reduced_dependencies": reduced,
        "removed_transitive_edge_count": removed_count,
        "questions_with_removed_transitive_edges": removed_ids,
    }


def _dominant(signatures: list[str | None]) -> tuple[str | None, int]:
    counts = Counter(value for value in signatures if isinstance(value, str))
    if not counts:
        return None, 0
    signature, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    return signature, count


def dominant_family_inflation(records: list[dict[str, Any]]) -> dict[str, Any]:
    fine = [_signature(record, "fine") for record in records]
    contracted = [_signature(record, "contracted") for record in records]
    fine_signature, fine_count = _dominant(fine)
    contracted_signature, contracted_count = _dominant(contracted)
    fine_ids = {
        record["question_id"]
        for record, signature in zip(records, fine)
        if signature == fine_signature
    }
    contracted_ids = {
        record["question_id"]
        for record, signature in zip(records, contracted)
        if signature == contracted_signature
    }
    return {
        "representable_question_count": sum(isinstance(value, str) for value in fine),
        "fine_dominant_signature": fine_signature,
        "fine_dominant_family_count": fine_count,
        "fine_dominant_family_rate": fine_count / len(fine) if fine else None,
        "contracted_dominant_signature": contracted_signature,
        "contracted_dominant_family_count": contracted_count,
        "contracted_dominant_family_rate": contracted_count / len(contracted)
        if contracted
        else None,
        "dominant_signatures_identical": fine_signature == contracted_signature,
        "dominant_family_count_increase": contracted_count - fine_count,
        "dominant_family_rate_increase": (
            (contracted_count - fine_count) / len(records) if records else None
        ),
        "question_ids_added_to_contracted_dominant_beyond_fine_dominant": sorted(
            contracted_ids - fine_ids
        ),
        "same_role_contraction_establishes_semantic_equivalence": False,
    }


def build_metrics(
    records: list[dict[str, Any]],
    primary_metrics: dict[str, Any],
    *,
    prefix_count: int = 30,
    source_bindings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not records:
        raise AuditError("records must be nonempty")
    if not 0 < prefix_count < len(records):
        raise AuditError("prefix_count must be positive and smaller than record count")
    run_ids = {record.get("run_id") for record in records}
    if len(run_ids) != 1:
        raise AuditError("records must have exactly one run_id")
    primary_decision = (
        primary_metrics.get("n100_precommitted_decision", {}).get("decision")
    )
    if primary_decision != EXPECTED_PRIMARY_DECISION:
        raise AuditError(
            "primary metrics do not preserve the expected precommitted N=100 decision"
        )
    recurring = recurring_new_contracted_families(records, prefix_count)
    profiles = raw_vs_reduced_graph_profile(records)
    inflation = dominant_family_inflation(records)
    return {
        "schema_version": METRICS_SCHEMA_VERSION,
        "audit_id": AUDIT_ID,
        "run_id": next(iter(run_ids)),
        "tool_version": TOOL_VERSION,
        "audit_status": "complete_post_hoc_sensitivity",
        "evidence_class": "post_hoc_partition_sensitivity_non_primary_non_gold",
        "source_bindings": source_bindings or {},
        "partition_profiles": partition_profiles(records),
        "recurring_new_contracted_family_partition_sensitivity": recurring,
        "raw_vs_transitive_reduced_graph_profile": profiles,
        "fine_to_contracted_dominant_family_inflation": inflation,
        "primary_decision_preservation": {
            "precommitted_decision": primary_decision,
            "changed_by_post_hoc_audit": False,
            "operational_interpretation": "conservative_operational_decision",
            "semantic_novelty_interpretation": "partition_confounded_not_cross_partition_confirmed",
        },
        "interpretation_boundary": {
            "audit_is_post_hoc_not_precommitted": True,
            "primary_contract_tool_raw_metrics_or_report_modified": False,
            "supports": [
                "partition_level_style_sensitivity",
                "cross_partition_support_of_recurring_new_contracted_families",
                "raw_versus_transitive_reduced_graph_profile",
                "same_role_contraction_inflation_sensitivity",
            ],
            "does_not_support": [
                "replacement_of_the_precommitted_N100_decision",
                "semantic_correctness",
                "proof_that_partition_differences_are_only_worker_style",
                "proof_that_recurring_new_families_are_semantically_novel",
                "human_agreement_or_gold_status",
            ],
        },
    }


def render_addendum(metrics: dict[str, Any]) -> str:
    partitions = metrics["partition_profiles"]
    recurring = metrics[
        "recurring_new_contracted_family_partition_sensitivity"
    ]
    graph = metrics["raw_vs_transitive_reduced_graph_profile"]
    inflation = metrics["fine_to_contracted_dominant_family_inflation"]
    decision = metrics["primary_decision_preservation"]
    lines = [
        "# Post-hoc partition-sensitivity addendum v0.1",
        "",
        "This addendum is a separately versioned, post-hoc sensitivity audit. It does not modify or replace the frozen contract, extractor, raw records, primary metrics, primary report, or precommitted decision.",
        "",
        "## Decision preservation",
        "",
        f"The precommitted decision remains `{decision['precommitted_decision']}`. It is retained as a **conservative operational decision**. Evidence that the recurring families constitute semantic novelty is **partition-confounded and not cross-partition confirmed**.",
        "",
        "## Partition profiles",
        "",
        "| Partition | Positions | Records | Uncertain | Uncertain rate | Mean nodes | Uppercase node-description rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in partitions:
        lines.append(
            f"| {item['producer_partition']} | {item['committed_positions'][0]}–{item['committed_positions'][1]}"
            f" | {item['record_count']} | {item['uncertain_count']}"
            f" | {item['uncertain_rate']:.3f} | {item['mean_primary_node_count']:.3f}"
            f" | {item['uppercase_initial_node_description_rate']:.3f} |"
        )
    lines.extend(
        [
            "",
            "The first 30 contract-development questions occur only in `partition_01`; most of the new 70 occur in `partition_02` and `partition_03`. Consequently, new-question transfer and producer-context style are not separated by this run.",
            "",
            "## Recurring new contracted families",
            "",
            f"- First-30-unobserved families recurring at least twice in the new 70: {recurring['recurring_new_contracted_family_count']}",
            f"- Those supported by more than one producer partition: {recurring['cross_partition_recurring_new_contracted_family_count']}",
            "",
            "| Signature | Questions | Partition support | Question IDs |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for family in recurring["families"]:
        support = json.dumps(family["partition_support"], sort_keys=True)
        question_ids = ", ".join(f"`{value}`" for value in family["question_ids"])
        lines.append(
            f"| `{family['signature']}` | {family['new_expansion_question_count']}"
            f" | `{support}` | {question_ids} |"
        )
    raw = graph["raw_declared_dependencies"]
    reduced = graph["transitive_reduced_dependencies"]
    lines.extend(
        [
            "",
            "The cross-partition recurrence count is a post-hoc sensitivity diagnostic, not a replacement decision rule. A zero value means the primary trigger is not independently reproduced across producer contexts in this run.",
            "",
            "## Raw versus transitive-reduced graph profile",
            "",
            "| Dependency view | Mean edges | Branch questions | Join questions |",
            "| --- | ---: | ---: | ---: |",
            f"| Raw declared | {raw['mean_edge_count']:.3f} | {raw['branch_question_count']} | {raw['join_question_count']} |",
            f"| Transitive reduced | {reduced['mean_edge_count']:.3f} | {reduced['branch_question_count']} | {reduced['join_question_count']} |",
            "",
            f"Transitive reduction removes {graph['removed_transitive_edge_count']} edges from {len(graph['questions_with_removed_transitive_edges'])} questions. Raw branch/join counts therefore must not be presented as normalized topology counts.",
            "",
            "## Fine-to-contracted dominant-family sensitivity",
            "",
            f"- Fine dominant family: {inflation['fine_dominant_family_count']} questions ({inflation['fine_dominant_family_rate']:.3f})",
            f"- Contracted dominant family: {inflation['contracted_dominant_family_count']} questions ({inflation['contracted_dominant_family_rate']:.3f})",
            f"- Increase after same-role linear contraction: {inflation['dominant_family_count_increase']} questions ({inflation['dominant_family_rate_increase']:.3f} of N)",
            "",
            "Same-role contraction is a deterministic split/merge sensitivity view; it does not establish that distinct referential hops are semantically equivalent. Fine and contracted results must be reported together.",
            "",
            "## Interpretation boundary",
            "",
            "This audit supports a reproducible description of partition sensitivity and graph-normalization sensitivity only. It does not establish semantic correctness, prove that every partition difference is caused by worker style, overturn the frozen primary decision, or create human/gold evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        _require_regular_file(args.records, "records")
        _require_regular_file(args.primary_metrics, "primary metrics")
        if args.records.resolve() == args.primary_metrics.resolve():
            raise AuditError("records and primary metrics paths must differ")
        output_resolved = {args.metrics_output.resolve(), args.addendum_output.resolve()}
        if len(output_resolved) != 2:
            raise AuditError("audit output paths must differ")
        if args.records.resolve() in output_resolved or args.primary_metrics.resolve() in output_resolved:
            raise AuditError("audit outputs must not overwrite frozen primary inputs")
        records = list(iter_json_records(args.records))
        primary_metrics = read_json(args.primary_metrics)
        if len(records) != 100:
            raise AuditError(f"frozen audit expects exactly 100 records, observed {len(records)}")
        if primary_metrics.get("run_id") != EXPECTED_RUN_ID:
            raise AuditError("primary metrics run_id is unsupported")
        source_bindings = {
            "records": _input_binding(args.records, record_count=len(records)),
            "primary_metrics": _input_binding(args.primary_metrics),
            "primary_canonicalizer": _input_binding(Path(primary.__file__)),
            "audit_implementation": _input_binding(Path(__file__)),
        }
        metrics = build_metrics(
            records,
            primary_metrics,
            prefix_count=args.prefix_count,
            source_bindings=source_bindings,
        )
        addendum = render_addendum(metrics).encode("utf-8")
        write_output_batch(
            {
                "partition_sensitivity_metrics": (
                    args.metrics_output,
                    json_file_bytes(metrics),
                ),
                "interpretive_addendum": (args.addendum_output, addendum),
            },
            overwrite=args.overwrite,
        )
        print(
            "PASS partition sensitivity audit "
            f"records={len(records)} recurring_new="
            f"{metrics['recurring_new_contracted_family_partition_sensitivity']['recurring_new_contracted_family_count']} "
            f"cross_partition="
            f"{metrics['recurring_new_contracted_family_partition_sensitivity']['cross_partition_recurring_new_contracted_family_count']}"
        )
        return 0
    except (AuditError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
