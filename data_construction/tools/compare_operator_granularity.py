#!/usr/bin/env python3
"""Compare coarse, medium, and fine operator representations for a pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from _common import (
    first_string,
    git_commit_identity,
    historical_output_collision_errors,
    iter_json_records,
    output_path_collision_errors,
    read_json,
    sha256_file,
    write_json,
)
from validate_annotation import topology_errors, vocabulary_names


GRANULARITIES = ("coarse", "medium", "fine")
MIN_PILOT_QUESTIONS = 20
GRANULARITY_TOOL_VERSION = "operator_granularity_comparator_v0_1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pilot_representations",
        type=Path,
        help="JSONL with question_id and representations.{coarse,medium,fine}",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("data_construction/reports/operator_granularity_metrics_v0_1.json"),
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=Path("data_construction/reports/operator_granularity_study_v0_1.md"),
    )
    parser.add_argument("--selected", choices=GRANULARITIES)
    parser.add_argument("--selection-rationale", default="")
    parser.add_argument("--min-questions", type=int, default=MIN_PILOT_QUESTIONS)
    parser.add_argument(
        "--vocabulary-dir",
        type=Path,
        default=Path("data_construction/operator_design"),
    )
    return parser.parse_args()


def topology_nodes(representation: dict[str, Any]) -> list[dict[str, Any]]:
    topology = representation.get("topology", representation)
    nodes = topology.get("nodes", []) if isinstance(topology, dict) else []
    return [node for node in nodes if isinstance(node, dict)] if isinstance(nodes, list) else []


def boolean_flag(value: Any, *keys: str) -> bool:
    for key in keys:
        candidate = value.get(key) if isinstance(value, dict) else None
        if isinstance(candidate, bool):
            return candidate
        if isinstance(candidate, str):
            return candidate.lower() in {"true", "yes", "covered", "required", "present"}
    return False


def observed_boolean(value: Any, *keys: str) -> tuple[bool, bool]:
    if not isinstance(value, dict):
        return False, False
    for key in keys:
        if key not in value:
            continue
        candidate = value[key]
        if isinstance(candidate, bool):
            return True, candidate
        if isinstance(candidate, str):
            normalized = candidate.strip().lower()
            if normalized in {"true", "yes", "covered", "required", "present"}:
                return True, True
            if normalized in {"false", "no", "not_covered", "not_required", "absent"}:
                return True, False
            # Unknown/not-observed tokens are deliberately not interpreted as
            # negative measurements.
            return False, False
    return False, False


def observed_human_disagreement(
    value: Any,
    expected_question_id: str | None = None,
    expected_granularity: str | None = None,
) -> tuple[bool, bool]:
    """Derive disagreement only from two auditable independent human reviews."""
    if not isinstance(value, dict):
        return False, False
    evidence = value.get("human_review_evidence")
    if not isinstance(evidence, dict) or evidence.get("canonicalization") != "sorted_compact_json_utf8_sha256_v0_1":
        return False, False
    reviews = evidence.get("independent_reviews") if isinstance(evidence, dict) else None
    if not isinstance(reviews, list) or len(reviews) < 2:
        return False, False
    reviewer_ids: list[str] = []
    judgments: list[str] = []
    packet_hashes: list[str] = []
    representation_without_reviews = dict(value)
    representation_without_reviews.pop("human_review_evidence", None)
    reviewed_representation_sha256 = hashlib.sha256(
        json.dumps(
            representation_without_reviews,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    for review in reviews:
        if not isinstance(review, dict):
            return False, False
        reviewer_id = review.get("reviewer_id")
        fingerprint = review.get("annotation_sha256")
        annotation = review.get("annotation")
        if not isinstance(annotation, dict) or not annotation:
            return False, False
        computed_fingerprint = hashlib.sha256(
            json.dumps(annotation, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if (
            not isinstance(reviewer_id, str)
            or not reviewer_id.strip()
            or not isinstance(fingerprint, str)
            or len(fingerprint) != 64
            or any(character not in "0123456789abcdef" for character in fingerprint)
            or fingerprint != computed_fingerprint
        ):
            return False, False
        decision = annotation.get("decision")
        packet_sha256 = annotation.get("review_packet_sha256")
        corrected_sha256 = annotation.get("corrected_representation_sha256")
        if (
            annotation.get("schema_version") != "operator_representation_review_v0_1"
            or annotation.get("question_id") != expected_question_id
            or annotation.get("granularity") != expected_granularity
            or annotation.get("reviewed_view") != "operator_granularity_representation"
            or annotation.get("reviewed_representation_sha256")
            != reviewed_representation_sha256
            or decision not in {"accept", "accept_with_edits", "reject", "abstain"}
            or not isinstance(packet_sha256, str)
            or len(packet_sha256) != 64
            or any(character not in "0123456789abcdef" for character in packet_sha256)
            or (
                decision == "accept_with_edits"
                and (
                    not isinstance(corrected_sha256, str)
                    or len(corrected_sha256) != 64
                    or any(character not in "0123456789abcdef" for character in corrected_sha256)
                )
            )
            or (decision != "accept_with_edits" and corrected_sha256 is not None)
        ):
            return False, False
        reviewer_ids.append(reviewer_id)
        packet_hashes.append(packet_sha256)
        judgments.append(f"{decision}:{corrected_sha256 or ''}")
    if len(set(reviewer_ids)) < 2 or len(set(packet_hashes)) != 1:
        return False, False
    return True, len(set(judgments)) > 1


def summarize(
    records: list[dict[str, Any]],
    granularity: str,
    allowed_operators: set[str],
) -> dict[str, Any]:
    lengths: list[int] = []
    distinct_counts: list[int] = []
    covered = 0
    coverage_observed = 0
    new_operator = 0
    new_operator_observed = 0
    disagreement = 0
    disagreement_observed = 0
    ambiguity = 0
    ambiguity_observed = 0
    hidden_reasoning = 0
    hidden_reasoning_observed = 0
    fragmentation = 0
    fragmentation_observed = 0
    present = 0
    valid_topology_observed = 0
    operators: Counter[str] = Counter()
    invalid_topology_examples: list[dict[str, Any]] = []
    examples: dict[str, list[str]] = {"hidden_reasoning": [], "excessive_fragmentation": []}

    for record in records:
        representations = record.get("representations", {})
        representation = representations.get(granularity) if isinstance(representations, dict) else None
        if not isinstance(representation, dict):
            continue
        present += 1
        question_id = first_string(record, ("question_id", "qid", "id")) or "unknown"
        nodes = topology_nodes(representation)
        node_names = [first_string(node, ("operator", "operation", "function")) for node in nodes]
        names = {name for name in node_names if name}
        topology = representation.get("topology", representation)
        structural_errors = topology_errors(
            topology,
            f"representations.{granularity}.topology",
            allowed_operators,
        )
        if nodes and not structural_errors:
            valid_topology_observed += 1
        elif len(invalid_topology_examples) < 10:
            invalid_topology_examples.append(
                {"question_id": question_id, "errors": structural_errors or ["topology has no nodes"]}
            )
        for node in nodes:
            name = first_string(node, ("operator", "operation", "function"))
            if name:
                operators[name] += 1
        lengths.append(len(nodes))
        distinct_counts.append(len(names))

        coverage_status = representation.get("coverage_status")
        coverage_seen, is_covered = observed_boolean(representation, "covered", "coverage")
        if isinstance(coverage_status, str):
            normalized_coverage = coverage_status.strip().lower()
            if normalized_coverage in {"covered", "not_covered"}:
                coverage_seen = True
                is_covered = normalized_coverage == "covered"
        coverage_observed += int(coverage_seen)
        covered += int(coverage_seen and is_covered)
        new_seen, needs_new = observed_boolean(representation, "requires_new_operator", "new_operator_required")
        if isinstance(representation.get("new_operators"), list):
            new_seen = True
            needs_new = bool(representation["new_operators"])
        new_operator_observed += int(new_seen)
        new_operator += int(new_seen and needs_new)
        disagreement_seen, has_disagreement = observed_human_disagreement(
            representation,
            question_id,
            granularity,
        )
        disagreement_observed += int(disagreement_seen)
        disagreement += int(disagreement_seen and has_disagreement)
        ambiguity_seen, has_ambiguity = observed_boolean(
            representation, "ambiguous", "ambiguity_present"
        )
        ambiguity_observed += int(ambiguity_seen)
        ambiguity += int(ambiguity_seen and has_ambiguity)

        hides_seen, hides = observed_boolean(representation, "hides_reasoning", "coarse_hides_reasoning")
        fragments_seen, fragments = observed_boolean(
            representation, "excessive_fragmentation", "fine_fragments_reasoning"
        )
        hidden_reasoning_observed += int(hides_seen)
        fragmentation_observed += int(fragments_seen)
        hidden_reasoning += int(hides_seen and hides)
        fragmentation += int(fragments_seen and fragments)
        if hides and len(examples["hidden_reasoning"]) < 5:
            examples["hidden_reasoning"].append(question_id)
        if fragments and len(examples["excessive_fragmentation"]) < 5:
            examples["excessive_fragmentation"].append(question_id)

    return {
        "representation_count": present,
        "valid_topology_observation_count": valid_topology_observed,
        "coverage_observation_count": coverage_observed,
        "coverage_count": covered,
        "coverage_rate": covered / coverage_observed if coverage_observed else None,
        "mean_graph_length": statistics.fmean(lengths) if lengths else None,
        "median_graph_length": statistics.median(lengths) if lengths else None,
        "min_graph_length": min(lengths) if lengths else None,
        "max_graph_length": max(lengths) if lengths else None,
        "mean_distinct_operators_per_question": statistics.fmean(distinct_counts) if distinct_counts else None,
        "new_operator_observation_count": new_operator_observed,
        "new_operator_required_count": new_operator,
        "new_operator_required_rate": new_operator / new_operator_observed if new_operator_observed else None,
        "annotation_disagreement_observation_count": disagreement_observed,
        "annotation_disagreement_count": disagreement,
        "annotation_disagreement_rate": disagreement / disagreement_observed if disagreement_observed else None,
        "ambiguity_count": ambiguity,
        "ambiguity_observation_count": ambiguity_observed,
        "ambiguity_rate": ambiguity / ambiguity_observed if ambiguity_observed else None,
        "hidden_reasoning_count": hidden_reasoning,
        "hidden_reasoning_observation_count": hidden_reasoning_observed,
        "excessive_fragmentation_count": fragmentation,
        "excessive_fragmentation_observation_count": fragmentation_observed,
        "operator_node_frequency": dict(sorted(operators.items())),
        "invalid_topology_examples": invalid_topology_examples,
        "example_question_ids": examples,
    }


def fmt(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_markdown(summary: dict[str, Any]) -> str:
    rows = []
    for granularity in GRANULARITIES:
        metrics = summary["metrics"][granularity]
        rows.append(
            "| {name} | {count} | {coverage} | {length} | {operators} | {new} | {disagreement} | {ambiguity} | {hidden} | {fragmented} |".format(
                name=granularity,
                count=metrics["representation_count"],
                coverage=fmt(metrics["coverage_rate"]),
                length=fmt(metrics["mean_graph_length"]),
                operators=fmt(metrics["mean_distinct_operators_per_question"]),
                new=fmt(metrics["new_operator_required_rate"]),
                disagreement=fmt(metrics["annotation_disagreement_rate"]),
                ambiguity=fmt(metrics["ambiguity_rate"]),
                hidden=fmt(
                    metrics["hidden_reasoning_count"]
                    if metrics["hidden_reasoning_observation_count"]
                    else None
                ),
                fragmented=fmt(
                    metrics["excessive_fragmentation_count"]
                    if metrics["excessive_fragmentation_observation_count"]
                    else None
                ),
            )
        )
    decision = summary["provisional_decision"]
    if summary["missing_question_id_count"] or summary["duplicate_question_ids"]:
        caveat = "파일럿 question_id가 누락되거나 중복되어 독립 질문 수를 증명할 수 없다."
    elif summary["question_count"] < summary["minimum_question_count"]:
        caveat = (
            f"파일럿 질문 수가 최소 {summary['minimum_question_count']}개에 미달하므로 "
            "어휘를 동결할 수 없다."
        )
    elif not summary["evidence_complete"]:
        caveat = "세 표현의 필수 측정값이 모든 파일럿 질문에 기록되지 않아 어휘를 동결할 수 없다."
    else:
        caveat = "정량 지표와 사례 검토를 함께 사용해야 하며 coverage만으로 선택하지 않는다."
    return "\n".join(
        [
            "# Operator granularity study v0.1",
            "",
            f"상태: `{summary['study_status']}`",
            "",
            "## 비교 지표",
            "",
            "| 표현 | 질문 수 | coverage | 평균 노드 수 | 평균 고유 연산자 수 | 새 연산자 필요율 | 불일치율 | 모호성률 | 추론 은닉 | 과도한 파편화 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            *rows,
            "",
            "## 잠정 결정",
            "",
            f"`{decision}`",
            "",
            summary.get("selection_rationale") or "선택 근거가 아직 기록되지 않았다.",
            "",
            "## 해석 제한",
            "",
            caveat,
            "LLM 제안만으로 annotation stability를 주장하지 않으며, 사람 검토가 없으면 불일치 지표는 관측 불가로 해석한다.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    vocabulary_inputs = {
        f"{granularity}_vocabulary": (
            args.vocabulary_dir / f"operator_vocabulary_{granularity}_v0_1.json"
        )
        for granularity in GRANULARITIES
    }
    project_root = Path(__file__).resolve().parents[2]
    outputs = {"json_output": args.json_output, "report_output": args.report_output}
    collisions = output_path_collision_errors(
        {"pilot_representations": args.pilot_representations, **vocabulary_inputs},
        outputs,
    )
    collisions.extend(historical_output_collision_errors(outputs, project_root))
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    if args.min_questions < MIN_PILOT_QUESTIONS:
        print(
            f"--min-questions cannot be lower than the research minimum of {MIN_PILOT_QUESTIONS}",
            file=sys.stderr,
        )
        return 2
    try:
        records = list(iter_json_records(args.pilot_representations))
    except (OSError, ValueError) as exc:
        print(f"invalid granularity input JSON: {exc}", file=sys.stderr)
        return 2
    question_ids = [first_string(record, ("question_id", "qid", "id")) for record in records]
    missing_question_id_count = sum(identifier is None for identifier in question_ids)
    present_question_ids = [identifier for identifier in question_ids if identifier is not None]
    duplicate_question_ids = sorted(
        {identifier for identifier in present_question_ids if present_question_ids.count(identifier) > 1}
    )
    identity_valid = missing_question_id_count == 0 and not duplicate_question_ids
    vocabularies: dict[str, set[str]] = {}
    vocabulary_provenance: dict[str, dict[str, Any]] = {}
    for granularity in GRANULARITIES:
        vocabulary_path = args.vocabulary_dir / f"operator_vocabulary_{granularity}_v0_1.json"
        if not vocabulary_path.is_file():
            print(f"missing operator vocabulary: {vocabulary_path}", file=sys.stderr)
            return 2
        try:
            vocabulary = read_json(vocabulary_path)
            vocabularies[granularity] = vocabulary_names(vocabulary)
        except (OSError, ValueError) as exc:
            print(f"invalid operator vocabulary {vocabulary_path}: {exc}", file=sys.stderr)
            return 2
        if not vocabularies[granularity]:
            print(f"operator vocabulary is empty: {vocabulary_path}", file=sys.stderr)
            return 2
        vocabulary_provenance[granularity] = {
            "artifact_sha256": sha256_file(vocabulary_path),
            "vocabulary_version": first_string(vocabulary, ("vocabulary_version",)),
            "granularity": first_string(vocabulary, ("granularity",)),
        }
    metrics = {
        granularity: summarize(records, granularity, vocabularies[granularity])
        for granularity in GRANULARITIES
    }
    evidence_complete = len(records) >= args.min_questions and identity_valid and all(
        metrics[granularity]["representation_count"] == len(records)
        and metrics[granularity]["valid_topology_observation_count"] == len(records)
        and metrics[granularity]["coverage_observation_count"] == len(records)
        and metrics[granularity]["new_operator_observation_count"] == len(records)
        and metrics[granularity]["annotation_disagreement_observation_count"] == len(records)
        and metrics[granularity]["ambiguity_observation_count"] == len(records)
        and metrics[granularity]["hidden_reasoning_observation_count"] == len(records)
        and metrics[granularity]["excessive_fragmentation_observation_count"] == len(records)
        for granularity in GRANULARITIES
    )
    selection_accepted = bool(args.selected and evidence_complete and args.selection_rationale.strip())
    summary = {
        "schema_version": "operator_granularity_study_v0_1",
        "question_count": len(records),
        "minimum_question_count": args.min_questions,
        "missing_question_id_count": missing_question_id_count,
        "duplicate_question_ids": duplicate_question_ids,
        "study_status": "complete" if evidence_complete else "incomplete",
        "evidence_complete": evidence_complete,
        "metrics": metrics,
        "provisional_decision": (
            args.selected.upper() if selection_accepted else "UNDECIDED_NEEDS_ANNOTATION_EVIDENCE"
        ),
        "selection_rationale": args.selection_rationale if selection_accepted else "",
        "selection_request_accepted": selection_accepted,
        "selection_request_rejection_reason": (
            None
            if not args.selected or selection_accepted
            else "Selection requires complete minimum-size evidence and a non-empty rationale."
        ),
        "scientific_caution": "Coverage alone is not a sufficient selection criterion.",
        "provenance": {
            "tool_version": GRANULARITY_TOOL_VERSION,
            "representations_artifact_sha256": sha256_file(args.pilot_representations),
            "vocabularies": vocabulary_provenance,
            "code_commit": git_commit_identity(project_root),
        },
    }
    write_json(args.json_output, summary)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(render_markdown(summary), encoding="utf-8", newline="\n")
    print(json.dumps({"questions": len(records), "evidence_complete": evidence_complete}, sort_keys=True))
    return 0 if evidence_complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
