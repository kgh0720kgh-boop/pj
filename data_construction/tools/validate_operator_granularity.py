#!/usr/bin/env python3
"""Validate the 30-question, three-way operator-granularity pilot."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Any

import compare_operator_granularity as comparator
from _common import (
    canonical_json_sha256,
    git_tracked_commit_identity,
    historical_output_collision_errors,
    implementation_artifact_set_sha256,
    iter_json_records,
    output_path_collision_errors,
    read_json,
    sha256_file,
    write_jsonl,
)
from validate_annotation import vocabulary_names


VALIDATOR_VERSION = "operator_granularity_validator_v0_1"
VALIDATION_RECORD_VERSION = "operator_granularity_validation_record_v0_1"
VALIDATION_MODE = "draft_2020_12_plus_structural_plus_live_artifacts"
GRANULARITIES = ("coarse", "medium", "fine")
EXPECTED_QUESTION_COUNT = 30
FORBIDDEN_KEYS = {
    "answer",
    "answers",
    "answer_node",
    "answer_span",
    "answer_text",
    "cell",
    "cells",
    "condition_c",
    "correct_response",
    "data",
    "document_id",
    "document_ids",
    "em",
    "evaluator_output",
    "execution_graph",
    "f1",
    "final_answer",
    "gold_answer",
    "gold_span",
    "grounding",
    "linked_passage",
    "linked_passages",
    "old_manual_graph",
    "oracle_document_id",
    "passage",
    "passages",
    "reference_answer",
    "request",
    "requests",
    "row",
    "rows",
    "sample_value",
    "target_answer",
    "trace",
    "traces",
    "weak_answer_node",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("representations", type=Path)
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
        "--plan",
        type=Path,
        default=Path("data_construction/pilot/granularity_representation_plan_v0_1.json"),
    )
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("data_construction/manifests/split_manifest_v0_1.json"),
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("data_construction/schemas/operator_granularity_pilot_v0_1.json"),
    )
    parser.add_argument(
        "--vocabulary-dir",
        type=Path,
        default=Path("data_construction/operator_design"),
    )
    parser.add_argument(
        "--checks-output",
        type=Path,
        default=Path("data_construction/pilot/granularity_deterministic_checks.jsonl"),
    )
    return parser.parse_args()


def canonical_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def forbidden_key_paths(value: Any, prefix: str = "$") -> list[str]:
    forbidden = {canonical_key(key) for key in FORBIDDEN_KEYS}
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}"
            if canonical_key(key) in forbidden:
                paths.append(path)
            paths.extend(forbidden_key_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(forbidden_key_paths(child, f"{prefix}[{index}]"))
    return paths


def load_draft_2020_12_validator(schema_path: Path) -> Any:
    try:
        import jsonschema
    except ImportError as exc:
        raise ValueError("jsonschema is unavailable; exact Draft 2020-12 validation is required") from exc
    validator_class = getattr(jsonschema, "Draft202012Validator", None)
    if validator_class is None:
        raise ValueError("installed jsonschema has no Draft 2020-12 validator")
    schema = read_json(schema_path)
    if not isinstance(schema, dict):
        raise ValueError("operator-granularity schema is not a JSON object")
    validator_class.check_schema(schema)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        resolver = jsonschema.RefResolver(
            base_uri=schema_path.resolve().as_uri(),
            referrer=schema,
        )
    return validator_class(schema, resolver=resolver)


def schema_errors(validator: Any, record: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for error in sorted(
        validator.iter_errors(record),
        key=lambda item: [str(component) for component in item.absolute_path],
    ):
        location = ".".join(str(component) for component in error.absolute_path) or "$"
        errors.append(f"{label}.{location}: {error.message}")
    return errors


def split_contract_errors(
    split: Any,
    split_path: Path,
    questions: list[dict[str, Any]],
    questions_path: Path,
) -> list[str]:
    if not isinstance(split, dict):
        return ["split manifest must be a JSON object"]
    errors: list[str] = []
    if (
        split.get("schema_version") != "split_manifest_v0_1"
        or split.get("release_eligible") is not True
        or split.get("override_used") is not False
        or split.get("zero_overlap_verified") is not True
    ):
        errors.append("split manifest is not the release-eligible zero-overlap v0.1 allocation")
    roles = split.get("roles")
    artifacts = split.get("role_artifacts")
    expected_ids = roles.get("annotation_schema_pilot") if isinstance(roles, dict) else None
    artifact = artifacts.get("annotation_schema_pilot") if isinstance(artifacts, dict) else None
    observed_ids = [record.get("question_id") for record in questions]
    if expected_ids != observed_ids:
        errors.append("questions do not match the exact annotation-schema-pilot ID order")
    if (
        not isinstance(artifact, dict)
        or artifact.get("sha256") != sha256_file(questions_path)
        or artifact.get("record_count") != len(questions)
    ):
        errors.append("questions artifact does not match the split-manifest role binding")
    if not split_path.is_file():
        errors.append("split manifest is missing")
    return errors


def provenance_live_errors(
    records: list[dict[str, Any]],
    plan_path: Path,
    project_root: Path,
) -> list[str]:
    errors: list[str] = []
    expected_plan_path = comparator.portable_path(plan_path, project_root)
    expected_plan_sha256 = sha256_file(plan_path)
    observed_commits: set[str] = set()
    for index, record in enumerate(records):
        provenance = record.get("provenance")
        if not isinstance(provenance, dict):
            continue
        artifact = provenance.get("structured_proposal_artifact")
        if not isinstance(artifact, dict) or artifact != {
            "repository_relative_path": expected_plan_path,
            "sha256": expected_plan_sha256,
        }:
            errors.append(f"representations[{index}].provenance: structured proposal binding mismatch")
        code_commit = provenance.get("code_commit")
        if isinstance(code_commit, str):
            observed_commits.add(code_commit)
    if len(observed_commits) != 1:
        errors.append("all representation records must bind one code commit")
    for commit in sorted(observed_commits):
        exists = subprocess.run(
            ["git", "-C", str(project_root), "cat-file", "-e", f"{commit}^{{commit}}"],
            capture_output=True,
            check=False,
        )
        if exists.returncode != 0:
            errors.append("representation provenance code commit is unavailable")
    return errors


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    vocabulary_paths = {
        granularity: args.vocabulary_dir / f"operator_vocabulary_{granularity}_v0_1.json"
        for granularity in GRANULARITIES
    }
    inputs = {
        "representations": args.representations,
        "questions": args.questions,
        "input_views": args.input_views,
        "input_views_manifest": args.input_views_manifest,
        "plan": args.plan,
        "split_manifest": args.split_manifest,
        "schema": args.schema,
        **{f"{key}_vocabulary": path for key, path in vocabulary_paths.items()},
    }
    outputs = {"checks_output": args.checks_output}
    collisions = output_path_collision_errors(inputs, outputs)
    collisions.extend(historical_output_collision_errors(outputs, project_root))
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    validator_paths = comparator.validator_implementation_paths(project_root)
    try:
        validator_commit = git_tracked_commit_identity(project_root, validator_paths)
        validator_implementation_sha256 = implementation_artifact_set_sha256(
            project_root, validator_paths
        )
        records = list(iter_json_records(args.representations))
        questions = list(iter_json_records(args.questions))
        views = list(iter_json_records(args.input_views))
        view_manifest = read_json(args.input_views_manifest)
        split = read_json(args.split_manifest)
        validator = load_draft_2020_12_validator(args.schema)
        vocabularies: dict[str, set[str]] = {}
        vocabulary_references: dict[str, dict[str, str]] = {}
        for granularity, path in vocabulary_paths.items():
            value = read_json(path)
            if not isinstance(value, dict):
                raise ValueError(f"{granularity} vocabulary must be a JSON object")
            names = vocabulary_names(value)
            if not names:
                raise ValueError(f"{granularity} vocabulary is empty")
            vocabularies[granularity] = names
            repository_path = comparator.portable_path(path, project_root)
            if repository_path is None:
                raise ValueError(f"{granularity} vocabulary is outside the project")
            vocabulary_references[granularity] = {
                "vocabulary_version": f"operator_vocabulary_{granularity}_v0_1",
                "repository_relative_path": repository_path,
                "sha256": sha256_file(path),
            }
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot validate operator granularity: {exc}", file=sys.stderr)
        return 2

    global_errors: list[str] = []
    if not (len(records) == len(questions) == len(views) == EXPECTED_QUESTION_COUNT):
        global_errors.append(
            "representations, questions, and views must each contain exactly 30 ordered records"
        )
    global_errors.extend(comparator.validate_question_records(questions))
    global_errors.extend(comparator.validate_input_views(questions, views))
    manifest_errors, manifest_split_sha256 = comparator.validate_view_manifest(
        view_manifest,
        args.questions,
        questions,
        args.input_views,
        views,
        project_root,
    )
    global_errors.extend(manifest_errors)
    global_errors.extend(split_contract_errors(split, args.split_manifest, questions, args.questions))
    if manifest_split_sha256 != sha256_file(args.split_manifest):
        global_errors.append("input-view manifest does not bind the live split manifest")
    global_errors.extend(
        comparator.validate_representation_records(
            records,
            questions,
            views,
            args.input_views,
            args.input_views_manifest,
            vocabularies,
            vocabulary_references,
            project_root,
            args.plan,
        )
    )
    global_errors.extend(provenance_live_errors(records, args.plan, project_root))
    for index, record in enumerate(records):
        global_errors.extend(schema_errors(validator, record, f"representations[{index}]"))
        contaminated = forbidden_key_paths(record)
        if contaminated:
            global_errors.append(
                f"representations[{index}] contains forbidden early-layer keys at {contaminated[:20]!r}"
            )
    global_errors = sorted(set(global_errors))

    common_context = {
        "representations_artifact_sha256": sha256_file(args.representations),
        "questions_artifact_sha256": sha256_file(args.questions),
        "split_manifest_artifact_sha256": sha256_file(args.split_manifest),
        "input_views_artifact_sha256": sha256_file(args.input_views),
        "input_views_manifest_artifact_sha256": sha256_file(args.input_views_manifest),
        "schema_artifact_sha256": sha256_file(args.schema),
        "validator_code_commit": validator_commit,
        "validator_implementation_artifacts_sha256": validator_implementation_sha256,
        "validation_mode": VALIDATION_MODE,
    }
    checks: list[dict[str, Any]] = []
    for record in records:
        representations = record.get("representations")
        for granularity in GRANULARITIES:
            representation = (
                representations.get(granularity) if isinstance(representations, dict) else None
            )
            checks.append(
                {
                    "schema_version": VALIDATION_RECORD_VERSION,
                    "question_id": record.get("question_id"),
                    "granularity": granularity,
                    "validator_version": VALIDATOR_VERSION,
                    "representation_canonical_sha256": canonical_json_sha256(representation),
                    "validation_context": {
                        **common_context,
                        "operator_vocabulary_artifact_sha256": vocabulary_references[granularity][
                            "sha256"
                        ],
                    },
                    "status": "fail" if global_errors else "pass",
                    "errors": global_errors,
                    "warnings": [],
                }
            )
    write_jsonl(args.checks_output, checks)
    result = {
        "validator_version": VALIDATOR_VERSION,
        "questions": len(records),
        "representations": len(checks),
        "errors": len(global_errors),
        "warnings": 0,
        "checks_output": args.checks_output.as_posix(),
        "checks_output_sha256": sha256_file(args.checks_output),
    }
    print(json.dumps(result, sort_keys=True))
    return 1 if global_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
