#!/usr/bin/env python3
"""Bind normalized granularity proposals to live pilot views and vocabularies."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _common import (
    git_tracked_commit_identity,
    historical_output_collision_errors,
    iter_json_records,
    jsonl_file_bytes,
    output_path_collision_errors,
    read_json,
    sha256_bytes,
    sha256_file,
    write_output_batch,
)


GRANULARITIES = ("coarse", "medium", "fine")
BUILDER_VERSION = "operator_granularity_representation_builder_v0_1"
PLAN_ROOT_KEYS = {"schema_version", "provenance", "gap_catalog", "records"}
PLAN_PROVENANCE_KEYS = {
    "model_id",
    "model_revision",
    "model_revision_status",
    "run_id",
    "seed",
    "raw_model_output_status",
}
PLAN_REPRESENTATION_KEYS = {
    "topology",
    "coverage_status",
    "coverage_gaps",
    "assessment_profile",
    "alternative_plans",
}
ALTERNATIVE_KEYS = {"plan_id", "condition", "rationale", "coverage_status", "topology"}
ASSESSMENT_PROFILES = {
    "coarse_macro": {
        "granularity": "coarse",
        "hides_reasoning": True,
        "hidden_reasoning_rationale": (
            "Macro operators combine selection, projection, retrieval, extraction, or parsing "
            "steps that remain explicit at finer granularities."
        ),
        "excessive_fragmentation": False,
        "fragmentation_rationale": "The coarse plan fuses steps rather than fragmenting them.",
    },
    "medium_balanced": {
        "granularity": "medium",
        "hides_reasoning": False,
        "hidden_reasoning_rationale": (
            "The plan exposes table selection and projection plus document retrieval and extraction "
            "at the intended medium boundary."
        ),
        "excessive_fragmentation": False,
        "fragmentation_rationale": (
            "The medium nodes preserve the major dependencies without splitting evidence handling "
            "into sentence and span operations."
        ),
    },
    "fine_compact": {
        "granularity": "fine",
        "hides_reasoning": False,
        "hidden_reasoning_rationale": (
            "The plan exposes evidence access, extraction, transformation, and reasoning as "
            "separate nodes where they are needed."
        ),
        "excessive_fragmentation": False,
        "fragmentation_rationale": (
            "The fine-grained distinctions in this plan remain necessary to expose its typed "
            "reasoning dependencies."
        ),
    },
    "fine_fragmented": {
        "granularity": "fine",
        "hides_reasoning": False,
        "hidden_reasoning_rationale": (
            "The plan exposes evidence access, extraction, transformation, and reasoning as "
            "separate nodes."
        ),
        "excessive_fragmentation": True,
        "fragmentation_rationale": (
            "The long retrieval, sentence-selection, span-extraction, parsing, and reasoning chain "
            "adds distinctions likely to raise annotation cost for this question."
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        type=Path,
        default=Path("data_construction/pilot/granularity_representation_plan_v0_1.json"),
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=Path("data_construction/pilot/questions.jsonl"),
    )
    parser.add_argument(
        "--input-views",
        type=Path,
        default=Path("data_construction/pilot/granularity_input_views.jsonl"),
    )
    parser.add_argument(
        "--input-views-manifest",
        type=Path,
        default=Path("data_construction/pilot/granularity_input_views_manifest_v0_1.json"),
    )
    parser.add_argument(
        "--vocabulary-dir",
        type=Path,
        default=Path("data_construction/operator_design"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data_construction/pilot/granularity_representations.jsonl"),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output only when its bytes differ",
    )
    return parser.parse_args()


def require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def repository_relative_path(path: Path, project_root: Path, label: str) -> str:
    try:
        relative = path.resolve().relative_to(project_root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} must be inside the repository") from exc
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"{label} is not a safe repository-relative path")
    return relative.as_posix()


def validate_topology(value: Any, allowed_operators: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty linear step list")
    nodes: list[dict[str, Any]] = []
    for index, step in enumerate(value):
        step_label = f"{label}[{index}]"
        if not isinstance(step, list) or len(step) != 2:
            raise ValueError(f"{step_label} must be [operator, semantic_role]")
        operator = require_nonempty_string(step[0], f"{step_label}[0]")
        semantic_role = require_nonempty_string(step[1], f"{step_label}[1]")
        if operator not in allowed_operators:
            raise ValueError(f"{step_label} operator is outside its candidate vocabulary")
        nodes.append(
            {
                "id": f"n{index + 1}",
                "operator": operator,
                "depends_on": [] if index == 0 else [f"n{index}"],
                "semantic_role": semantic_role,
            }
        )
    return {
        "nodes": nodes,
        "entry_node_ids": ["n1"],
        "output_node_ids": [f"n{len(nodes)}"],
    }


def vocabulary_contract(path: Path, granularity: str) -> tuple[set[str], dict[str, Any]]:
    value = read_json(path)
    if not isinstance(value, dict) or value.get("granularity") != granularity:
        raise ValueError(f"invalid {granularity} vocabulary")
    expected_version = f"operator_vocabulary_{granularity}_v0_1"
    if value.get("vocabulary_version") != expected_version:
        raise ValueError(f"{granularity} vocabulary version mismatch")
    operators = value.get("operators")
    if not isinstance(operators, list):
        raise ValueError(f"{granularity} vocabulary has no operators")
    names = {
        item.get("name")
        for item in operators
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if len(names) != len(operators) or not names:
        raise ValueError(f"{granularity} vocabulary operator inventory is invalid")
    return names, {
        "vocabulary_version": expected_version,
        "repository_relative_path": path.as_posix(),
        "sha256": sha256_file(path),
    }


def materialize_representation(
    value: Any,
    granularity: str,
    allowed_operators: set[str],
    vocabulary: dict[str, Any],
    label: str,
    ambiguity_present: bool,
    ambiguity_rationale: str,
    gap_catalog: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != PLAN_REPRESENTATION_KEYS:
        raise ValueError(f"{label} fields differ from the exact plan contract")
    coverage_status = value.get("coverage_status")
    coverage_gap_ids = value.get("coverage_gaps")
    if coverage_status not in {"covered", "not_covered"}:
        raise ValueError(f"{label}.coverage_status is invalid")
    if (
        not isinstance(coverage_gap_ids, list)
        or any(not isinstance(item, str) or not item for item in coverage_gap_ids)
        or len(coverage_gap_ids) != len(set(coverage_gap_ids))
    ):
        raise ValueError(f"{label}.coverage_gaps must be a unique catalog-ID list")
    if coverage_status == "covered" and coverage_gap_ids:
        raise ValueError(f"{label} covered plans cannot claim a vocabulary gap")
    if coverage_status == "not_covered" and not coverage_gap_ids:
        raise ValueError(f"{label} uncovered plans must identify gaps and reusable extensions")
    materialized_gaps: list[dict[str, str]] = []
    new_operators: list[str] = []
    for index, gap_id in enumerate(coverage_gap_ids):
        gap = gap_catalog.get(gap_id)
        if not isinstance(gap, dict) or set(gap) != {
            "category",
            "description",
            "required_contract",
            "new_operators",
        }:
            raise ValueError(f"{label}.coverage_gaps[{index}] references an invalid catalog entry")
        category = require_nonempty_string(gap.get("category"), f"gap_catalog.{gap_id}.category")
        description = require_nonempty_string(
            gap.get("description"), f"gap_catalog.{gap_id}.description"
        )
        required_contract = require_nonempty_string(
            gap.get("required_contract"), f"gap_catalog.{gap_id}.required_contract"
        )
        if category not in {
            "missing_semantic_operation",
            "missing_typed_contract",
            "missing_environment_capability",
            "granularity_mismatch",
            "other",
        }:
            raise ValueError(f"{label}.coverage_gaps[{index}] has an unsupported category")
        materialized_gaps.append(
            {
                "category": category,
                "description": description,
                "required_contract": required_contract,
            }
        )
        catalog_operators = gap.get("new_operators")
        if not isinstance(catalog_operators, list) or not catalog_operators:
            raise ValueError(f"gap_catalog.{gap_id}.new_operators must be non-empty")
        for name in catalog_operators:
            if name not in new_operators:
                new_operators.append(name)
    for index, name in enumerate(new_operators):
        if (
            not isinstance(name, str)
            or not name
            or not name.replace("_", "").isalnum()
            or name.upper() != name
        ):
            raise ValueError(f"{label}.new_operators[{index}] is not a reusable uppercase name")
        if name in allowed_operators:
            raise ValueError(f"{label}.new_operators[{index}] already exists in the vocabulary")
    profile_name = value.get("assessment_profile")
    profile = ASSESSMENT_PROFILES.get(profile_name)
    if not isinstance(profile, dict) or profile.get("granularity") != granularity:
        raise ValueError(f"{label}.assessment_profile is invalid for {granularity}")
    topology = validate_topology(value.get("topology"), allowed_operators, f"{label}.topology")
    alternatives = value.get("alternative_plans")
    if not isinstance(alternatives, list):
        raise ValueError(f"{label}.alternative_plans must be a list")
    materialized_alternatives: list[dict[str, Any]] = []
    seen_plan_ids: set[str] = set()
    for index, alternative in enumerate(alternatives):
        alternative_label = f"{label}.alternative_plans[{index}]"
        if not isinstance(alternative, dict) or set(alternative) != ALTERNATIVE_KEYS:
            raise ValueError(f"{alternative_label} fields differ from the exact plan contract")
        plan_id = require_nonempty_string(alternative.get("plan_id"), f"{alternative_label}.plan_id")
        if plan_id in seen_plan_ids:
            raise ValueError(f"{label} has duplicate alternative plan IDs")
        seen_plan_ids.add(plan_id)
        condition = require_nonempty_string(alternative.get("condition"), f"{alternative_label}.condition")
        rationale = require_nonempty_string(alternative.get("rationale"), f"{alternative_label}.rationale")
        alternative_coverage = alternative.get("coverage_status")
        if alternative_coverage not in {"covered", "not_covered"}:
            raise ValueError(f"{alternative_label}.coverage_status is invalid")
        materialized_alternatives.append(
            {
                "plan_id": plan_id,
                "condition": condition,
                "rationale": rationale,
                "coverage_status": alternative_coverage,
                "topology": validate_topology(
                    alternative.get("topology"),
                    allowed_operators,
                    f"{alternative_label}.topology",
                ),
            }
        )
    return {
        "granularity": granularity,
        "vocabulary": vocabulary,
        "topology": topology,
        "coverage_status": coverage_status,
        "coverage_gaps": materialized_gaps,
        "requires_new_operator": coverage_status == "not_covered",
        "new_operators": new_operators,
        "coverage_rationale": (
            f"All declared semantic steps in this {granularity} candidate plan use v0.1 "
            "operators; concrete grounding remains deferred."
            if coverage_status == "covered"
            else "The supported nodes form only a partial DAG; the listed reusable contract gaps "
            "prevent a typed complete plan."
        ),
        "new_operator_rationale": (
            "No new operator is required for this candidate plan."
            if coverage_status == "covered"
            else "A complete typed plan requires the listed reusable extension contracts; no "
            "question-specific pseudo-operator is inserted."
        ),
        "ambiguity_present": ambiguity_present,
        "ambiguity_rationale": ambiguity_rationale,
        "hides_reasoning": profile["hides_reasoning"],
        "hidden_reasoning_rationale": profile["hidden_reasoning_rationale"],
        "excessive_fragmentation": profile["excessive_fragmentation"],
        "fragmentation_rationale": profile["fragmentation_rationale"],
        "alternative_plans": materialized_alternatives,
    }


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    vocabulary_paths = {
        granularity: args.vocabulary_dir / f"operator_vocabulary_{granularity}_v0_1.json"
        for granularity in GRANULARITIES
    }
    collisions = output_path_collision_errors(
        {
            "plan": args.plan,
            "questions": args.questions,
            "input_views": args.input_views,
            "input_views_manifest": args.input_views_manifest,
            **{f"{key}_vocabulary": value for key, value in vocabulary_paths.items()},
        },
        {"output": args.output},
    )
    collisions.extend(historical_output_collision_errors({"output": args.output}, project_root))
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    try:
        implementation_commit = git_tracked_commit_identity(
            project_root,
            [Path(__file__), Path(__file__).with_name("_common.py")],
        )
        plan = read_json(args.plan)
        if not isinstance(plan, dict) or set(plan) != PLAN_ROOT_KEYS:
            raise ValueError("proposal plan fields differ from the exact v0.1 contract")
        if plan.get("schema_version") != "granularity_representation_plan_v0_1":
            raise ValueError("proposal plan schema_version is unsupported")
        plan_provenance = plan.get("provenance")
        if not isinstance(plan_provenance, dict) or set(plan_provenance) != PLAN_PROVENANCE_KEYS:
            raise ValueError("proposal provenance fields differ from the exact v0.1 contract")
        for key in ("model_id", "model_revision", "model_revision_status", "run_id", "raw_model_output_status"):
            require_nonempty_string(plan_provenance.get(key), f"provenance.{key}")
        seed = plan_provenance.get("seed")
        if not isinstance(seed, dict) or set(seed) != {"status"} or seed.get("status") != "not_supported":
            raise ValueError("interactive proposal seed must be exactly {'status': 'not_supported'}")
        if plan_provenance.get("model_revision_status") not in {
            "exact_revision_recorded",
            "revision_not_exposed",
        }:
            raise ValueError("proposal model_revision_status is unsupported")
        if plan_provenance.get("raw_model_output_status") not in {
            "preserved_hash_bound",
            "not_exposed_by_interface",
            "not_recorded",
        }:
            raise ValueError("proposal raw_model_output_status is unsupported")
        plan_records = plan.get("records")
        gap_catalog = plan.get("gap_catalog")
        if not isinstance(gap_catalog, dict):
            raise ValueError("proposal plan gap_catalog must be an object")
        if not isinstance(plan_records, list) or not plan_records:
            raise ValueError("proposal plan contains no records")
        questions = list(iter_json_records(args.questions))
        views = list(iter_json_records(args.input_views))
        view_manifest = read_json(args.input_views_manifest)
        if not isinstance(view_manifest, dict):
            raise ValueError("input-view manifest must be an object")
        view_artifact = view_manifest.get("input_views_artifact")
        if (
            not isinstance(view_artifact, dict)
            or view_artifact.get("sha256") != sha256_file(args.input_views)
            or view_artifact.get("record_count") != len(views)
        ):
            raise ValueError("input views are not bound to their manifest")
        if not (len(plan_records) == len(questions) == len(views)):
            raise ValueError("proposal plan, questions, and input views differ in record count")
        vocabularies = {
            granularity: vocabulary_contract(path, granularity)
            for granularity, path in vocabulary_paths.items()
        }
        input_views_repository_path = repository_relative_path(
            args.input_views, project_root, "input views"
        )
        input_views_manifest_repository_path = repository_relative_path(
            args.input_views_manifest, project_root, "input-view manifest"
        )
        plan_repository_path = repository_relative_path(
            args.plan, project_root, "structured proposal plan"
        )
        output_records: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for index, (plan_record, question, view) in enumerate(zip(plan_records, questions, views)):
            if not isinstance(plan_record, dict) or set(plan_record) != {
                "question_id",
                "ambiguity_present",
                "ambiguity_rationale",
                "representations",
            }:
                raise ValueError(f"proposal record {index} fields differ from the exact contract")
            question_id = plan_record.get("question_id")
            if (
                not isinstance(question_id, str)
                or not question_id
                or question_id in seen_ids
                or question.get("question_id") != question_id
                or view.get("question_id") != question_id
            ):
                raise ValueError(f"proposal record {index} does not match the exact pilot order")
            seen_ids.add(question_id)
            ambiguity_present = plan_record.get("ambiguity_present")
            ambiguity_rationale = require_nonempty_string(
                plan_record.get("ambiguity_rationale"),
                f"proposal record {index}.ambiguity_rationale",
            )
            if not isinstance(ambiguity_present, bool):
                raise ValueError(f"proposal record {index}.ambiguity_present must be boolean")
            question_view = view.get("question_view")
            operator_view = view.get("operator_view")
            if (
                not isinstance(question_view, dict)
                or not isinstance(operator_view, dict)
                or view.get("question_view_sha256") is None
                or view.get("operator_view_sha256") is None
            ):
                raise ValueError(f"input view {index} is incomplete")
            planned_representations = plan_record.get("representations")
            if not isinstance(planned_representations, dict) or set(planned_representations) != set(
                GRANULARITIES
            ):
                raise ValueError(f"proposal record {index} does not contain exactly three representations")
            materialized = {
                granularity: materialize_representation(
                    planned_representations[granularity],
                    granularity,
                    vocabularies[granularity][0],
                    vocabularies[granularity][1],
                    f"records[{index}].representations.{granularity}",
                    ambiguity_present,
                    ambiguity_rationale,
                    gap_catalog,
                )
                for granularity in GRANULARITIES
            }
            output_records.append(
                {
                    "schema_version": "operator_granularity_pilot_v0_1",
                    "question_id": question_id,
                    "source_split": question.get("source_split"),
                    "dataset_role": question.get("dataset_role"),
                    "input_views": {
                        "artifact": {
                            "repository_relative_path": input_views_repository_path,
                            "sha256": sha256_file(args.input_views),
                        },
                        "manifest_artifact": {
                            "repository_relative_path": input_views_manifest_repository_path,
                            "sha256": sha256_file(args.input_views_manifest),
                        },
                        "question_view_sha256": view["question_view_sha256"],
                        "operator_view_sha256": view["operator_view_sha256"],
                        "representation_input": "operator_environment",
                    },
                    "provenance": {
                        "annotation_status": "llm_proposed",
                        "creator_kind": "model_assisted",
                        **plan_provenance,
                        "code_commit": implementation_commit,
                        "structured_proposal_artifact": {
                            "repository_relative_path": plan_repository_path,
                            "sha256": sha256_file(args.plan),
                        },
                        "generation_status": "completed",
                    },
                    "representations": materialized,
                }
            )
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot build granularity representations: {exc}", file=sys.stderr)
        return 2
    output_payload = jsonl_file_bytes(output_records)
    try:
        write_output_batch(
            {"output": (args.output, output_payload)},
            overwrite=args.overwrite,
        )
    except (OSError, ValueError) as exc:
        print(f"cannot write granularity representations: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "builder_version": BUILDER_VERSION,
                "questions": len(output_records),
                "representations": len(output_records) * len(GRANULARITIES),
                "output": args.output.as_posix(),
                "output_sha256": sha256_bytes(output_payload),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
