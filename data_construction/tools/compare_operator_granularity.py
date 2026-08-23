#!/usr/bin/env python3
"""Compare coarse, medium, and fine operator representations for a pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_granularity_representations as representation_builder
from _common import (
    canonical_json_sha256,
    first_string,
    git_tracked_commit_identity,
    historical_output_collision_errors,
    implementation_artifact_set_sha256,
    iter_json_records,
    json_file_bytes,
    output_path_collision_errors,
    read_json,
    sha256_file,
    write_output_batch,
)
from validate_annotation import topology_errors, vocabulary_names


GRANULARITIES = ("coarse", "medium", "fine")
EXPECTED_PILOT_QUESTIONS = 30
GRANULARITY_TOOL_VERSION = "operator_granularity_comparator_v0_2"
VALIDATOR_VERSION = "operator_granularity_validator_v0_1"
VALIDATION_RECORD_VERSION = "operator_granularity_validation_record_v0_1"
VALIDATION_MODE = "draft_2020_12_plus_structural_plus_live_artifacts"
HEX_DIGITS = frozenset("0123456789abcdef")

QUESTION_KEYS = {
    "annotation_visibility",
    "dataset_role",
    "question",
    "question_id",
    "source_split",
    "table_id",
}
ROOT_REPRESENTATION_KEYS = {
    "schema_version",
    "question_id",
    "source_split",
    "dataset_role",
    "input_views",
    "provenance",
    "representations",
}
REPRESENTATION_KEYS = {
    "granularity",
    "vocabulary",
    "topology",
    "coverage_status",
    "coverage_gaps",
    "requires_new_operator",
    "new_operators",
    "coverage_rationale",
    "new_operator_rationale",
    "ambiguity_present",
    "ambiguity_rationale",
    "hides_reasoning",
    "hidden_reasoning_rationale",
    "excessive_fragmentation",
    "fragmentation_rationale",
    "alternative_plans",
}
TOPOLOGY_KEYS = {"nodes", "entry_node_ids", "output_node_ids"}
NODE_KEYS = {"id", "operator", "depends_on", "semantic_role"}
ALTERNATIVE_KEYS = {"plan_id", "condition", "rationale", "coverage_status", "topology"}
INPUT_BINDING_KEYS = {
    "artifact",
    "manifest_artifact",
    "question_view_sha256",
    "operator_view_sha256",
    "representation_input",
}
ARTIFACT_KEYS = {"repository_relative_path", "sha256"}
PROVENANCE_KEYS = {
    "annotation_status",
    "creator_kind",
    "model_id",
    "model_revision",
    "model_revision_status",
    "run_id",
    "seed",
    "code_commit",
    "structured_proposal_artifact",
    "raw_model_output_status",
    "generation_status",
}
VOCABULARY_KEYS = {"vocabulary_version", "repository_relative_path", "sha256"}
COVERAGE_GAP_KEYS = {"category", "description", "required_contract"}
VIEW_RECORD_KEYS = {
    "schema_version",
    "question_id",
    "question_view",
    "question_view_sha256",
    "operator_view",
    "operator_view_sha256",
}
QUESTION_VIEW_KEYS = {"schema_version", "visibility", "question_id", "question"}
OPERATOR_VIEW_KEYS = {"schema_version", "visibility", "question_id", "question", "environment"}
ENVIRONMENT_KEYS = {"table_id", "title", "section_title", "columns", "capabilities"}
COLUMN_KEYS = {"index", "label", "entity_link_capability"}
CHECK_KEYS = {
    "schema_version",
    "question_id",
    "granularity",
    "validator_version",
    "representation_canonical_sha256",
    "validation_context",
    "status",
    "errors",
    "warnings",
}
CHECK_CONTEXT_KEYS = {
    "representations_artifact_sha256",
    "questions_artifact_sha256",
    "split_manifest_artifact_sha256",
    "input_views_artifact_sha256",
    "input_views_manifest_artifact_sha256",
    "schema_artifact_sha256",
    "operator_vocabulary_artifact_sha256",
    "validator_code_commit",
    "validator_implementation_artifacts_sha256",
    "validation_mode",
}
REVIEW_PACKET_MANIFEST_KEYS = {
    "schema_version",
    "builder_version",
    "granularity",
    "question_count",
    "review_status",
    "human_reviews_created_by_builder",
    "packet_payload",
    "packet_artifact",
    "inputs",
    "validation",
    "review_record_contract",
    "provenance",
}
REVIEW_PACKET_INPUT_KEYS = {
    "questions",
    "input_views",
    "input_views_manifest",
    "representations",
    "validation_checks",
}
REVIEW_PACKET_PAYLOAD_KEYS = {
    "canonicalization",
    "sha256",
    "reviewed_view",
    "contains_only_operator_view_and_candidate_representation",
}
REVIEW_PACKET_VALIDATION_KEYS = {
    "validation_record_version",
    "validator_version",
    "validation_mode",
    "exact_question_id_order_verified",
    "selected_granularity_pass_check_count",
    "live_artifact_hashes_verified",
    "leakage_projection_verified",
}
REVIEW_RECORD_CONTRACT_KEYS = {
    "schema_version",
    "canonicalization",
    "decisions",
    "assessment_fields",
    "reviewer_identity",
    "reviewer_authentication",
    "reviews_included",
}
REVIEW_ENVELOPE_KEYS = {"reviewer_id", "annotation", "annotation_sha256"}
REVIEW_ANNOTATION_KEYS = {
    "schema_version",
    "question_id",
    "granularity",
    "reviewed_view",
    "reviewed_representation_sha256",
    "review_packet_payload_sha256",
    "completed_at",
    "decision",
    "assessment",
    "edit",
    "notes",
}
REVIEW_ASSESSMENT_KEYS = {
    "semantic_validity",
    "coverage_status",
    "ambiguity_present",
    "hides_reasoning",
    "excessive_fragmentation",
}
REVIEW_DECISIONS = ("accept", "accept_with_edits", "reject", "abstain")
CANONICALIZATION = "sorted_compact_json_utf8_sha256_v0_1"
VIEW_MANIFEST_KEYS = {
    "schema_version",
    "builder_version",
    "provenance",
    "input_views_artifact",
    "questions_artifact",
    "split_manifest_artifact",
    "source_manifest_artifact",
    "linked_environment",
    "selected_environment_artifacts",
    "view_contract",
}
VIEW_MANIFEST_PROVENANCE_KEYS = {"code_commit", "implementation_artifacts"}
LINKED_ENVIRONMENT_KEYS = {
    "source_id",
    "repository_url",
    "pinned_commit",
    "git_tree_sha1",
    "tables_tree_sha1",
    "request_tree_sha1",
    "tables_file_count",
    "tables_canonical_content_list_sha256",
    "request_file_count",
    "request_canonical_content_list_sha256",
}
SELECTED_ENVIRONMENT_KEYS = {
    "file_count",
    "canonicalization",
    "canonical_sha256",
    "tables_canonical_sha256",
    "requests_canonical_sha256",
    "artifacts",
}
SELECTED_ARTIFACT_KEYS = {"portable_path", "sha256"}
EXPECTED_SELECTED_ENVIRONMENT_HASHES = {
    "tables_canonical_sha256": "0f33966dccd1ee627bdfdddc667bc9a27e278984a226b37b2f2b4e9c565069fc",
    "requests_canonical_sha256": "bed0f41af2cc4497335a82ca06c9c6d00548ca056a8c422774ad6a5a721ed1e8",
    "canonical_sha256": "9e7055ad0e9e351f597237d9bff9edb77b2b58acf8ae8bbd653aeb88dafe69c3",
}
EXPECTED_VIEW_CONTRACT = {
    "question_view_allowed_categories": ["question_text", "question_id"],
    "operator_view_allowed_categories": [
        "question_text",
        "question_id",
        "table_identity",
        "table_title_and_section_title",
        "column_schema",
        "environment_capabilities",
    ],
    "excluded_categories": [
        "answer_text_or_span",
        "table_row_or_cell_values_or_counts",
        "inferred_cell_types",
        "linked_document_ids_or_text_or_counts",
        "weak_answer_nodes_or_traces",
        "historical_graphs_or_semantic_labels",
        "oracle_grounding",
        "evaluator_outputs",
        "later_layer_labels",
        "machine_local_absolute_paths",
    ],
    "leakage_audit_status": "pass_by_exact_projection",
}
VISIBLE_CAPABILITIES = {
    "table_access_available": True,
    "linked_document_lookup_available": True,
    "linked_document_text_available_to_later_layers": True,
    "linked_document_text_exposed_in_this_view": False,
    "lookup_scope": "pinned_linked_snapshot_for_current_table",
}
CANONICAL_ARTIFACT_PATHS = {
    "input_views_artifact": "data_construction/pilot/granularity_input_views.jsonl",
    "questions_artifact": "data_construction/pilot/questions.jsonl",
    "split_manifest_artifact": "data_construction/manifests/split_manifest_v0_1.json",
    "source_manifest_artifact": "data_construction/manifests/source_manifest_v0_1.json",
    "structured_proposal_artifact": (
        "data_construction/pilot/granularity_representation_plan_v0_1.json"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pilot_representations",
        type=Path,
        help="JSONL with question_id and representations.{coarse,medium,fine}",
    )
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--input-views", required=True, type=Path)
    parser.add_argument("--input-views-manifest", required=True, type=Path)
    parser.add_argument("--validation-checks", required=True, type=Path)
    parser.add_argument(
        "--human-review",
        action="append",
        default=[],
        type=Path,
        help="Raw 30-record review array; repeat once per reviewer and granularity",
    )
    parser.add_argument(
        "--review-packet-manifest",
        action="append",
        default=[],
        type=Path,
        help="Review-packet manifest; when reviews are supplied, provide one per granularity",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("data_construction/reports/operator_granularity_metrics_v0_1.json"),
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=None,
        help="Optional generated Markdown output; omitted by default to preserve the curated study report",
    )
    parser.add_argument("--selected", choices=GRANULARITIES)
    parser.add_argument("--selection-rationale", default="")
    parser.add_argument("--min-questions", type=int, default=EXPECTED_PILOT_QUESTIONS)
    parser.add_argument(
        "--vocabulary-dir",
        type=Path,
        default=Path("data_construction/operator_design"),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing metric/report artifacts only when their bytes differ",
    )
    return parser.parse_args()


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX_DIGITS


def portable_path(path: Path, project_root: Path) -> str | None:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return None


def artifact_reference_errors(value: Any, label: str) -> list[str]:
    if not isinstance(value, dict) or set(value) != ARTIFACT_KEYS:
        return [f"{label}: fields differ from the exact artifact-reference contract"]
    errors: list[str] = []
    path = value.get("repository_relative_path")
    if (
        not isinstance(path, str)
        or not path
        or path.startswith("/")
        or "\\" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
    ):
        errors.append(f"{label}.repository_relative_path: expected a safe repository-relative path")
    if not is_sha256(value.get("sha256")):
        errors.append(f"{label}.sha256: expected lowercase SHA-256")
    return errors


def validate_question_records(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        label = f"questions[{index}]"
        if set(record) != QUESTION_KEYS:
            errors.append(f"{label}: fields differ from the exact pilot-question contract")
            continue
        question_id = record.get("question_id")
        if not isinstance(question_id, str) or not question_id or question_id in seen:
            errors.append(f"{label}.question_id: expected a unique non-empty string")
        else:
            seen.add(question_id)
        if not isinstance(record.get("question"), str) or not record["question"].strip():
            errors.append(f"{label}.question: expected a non-empty string")
        if not isinstance(record.get("table_id"), str) or not record["table_id"]:
            errors.append(f"{label}.table_id: expected a non-empty string")
        if record.get("annotation_visibility") != "question_and_table_identity_only":
            errors.append(f"{label}.annotation_visibility: unexpected visibility")
        if record.get("dataset_role") != "annotation_schema_pilot":
            errors.append(f"{label}.dataset_role: unexpected role")
        if not isinstance(record.get("source_split"), str) or not record["source_split"]:
            errors.append(f"{label}.source_split: expected a non-empty string")
    return errors


def live_manifest_artifact_errors(
    value: Any,
    label: str,
    project_root: Path,
) -> tuple[list[str], Path | None]:
    errors = artifact_reference_errors(value, label)
    if errors or not isinstance(value, dict):
        return errors, None
    candidate = (project_root / value["repository_relative_path"]).resolve()
    try:
        candidate.relative_to(project_root.resolve())
    except ValueError:
        return [*errors, f"{label}: path escapes the project root"], None
    if not candidate.is_file():
        errors.append(f"{label}: referenced repository artifact is missing")
    elif sha256_file(candidate) != value["sha256"]:
        errors.append(f"{label}: referenced repository artifact SHA-256 mismatch")
    return errors, candidate


def validate_input_views(
    questions: list[dict[str, Any]],
    views: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    if len(views) != len(questions):
        errors.append("input views and questions must have the same record count")
        return errors
    for index, (question, record) in enumerate(zip(questions, views, strict=True)):
        label = f"input_views[{index}]"
        question_id = question.get("question_id")
        if set(record) != VIEW_RECORD_KEYS:
            errors.append(f"{label}: fields differ from the exact input-view wrapper contract")
            continue
        if record.get("schema_version") != "granularity_input_views_v0_1":
            errors.append(f"{label}.schema_version: unexpected value")
        if record.get("question_id") != question_id:
            errors.append(f"{label}.question_id: not in exact pilot order")
        question_view = record.get("question_view")
        operator_view = record.get("operator_view")
        if not isinstance(question_view, dict) or set(question_view) != QUESTION_VIEW_KEYS:
            errors.append(f"{label}.question_view: fields differ from the exact allowlist")
        else:
            if (
                question_view.get("schema_version") != "granularity_question_view_v0_1"
                or question_view.get("visibility") != "question_only_no_environment_or_answer"
                or question_view.get("question_id") != question_id
                or question_view.get("question") != question.get("question")
            ):
                errors.append(f"{label}.question_view: identity, text, schema, or visibility mismatch")
            if record.get("question_view_sha256") != canonical_json_sha256(question_view):
                errors.append(f"{label}.question_view_sha256: canonical hash mismatch")
        if not isinstance(operator_view, dict) or set(operator_view) != OPERATOR_VIEW_KEYS:
            errors.append(f"{label}.operator_view: fields differ from the exact allowlist")
            continue
        if (
            operator_view.get("schema_version") != "granularity_operator_view_v0_1"
            or operator_view.get("visibility")
            != "question_plus_table_schema_and_capabilities_no_values"
            or operator_view.get("question_id") != question_id
            or operator_view.get("question") != question.get("question")
        ):
            errors.append(f"{label}.operator_view: identity, text, schema, or visibility mismatch")
        if record.get("operator_view_sha256") != canonical_json_sha256(operator_view):
            errors.append(f"{label}.operator_view_sha256: canonical hash mismatch")
        environment = operator_view.get("environment")
        if not isinstance(environment, dict) or set(environment) != ENVIRONMENT_KEYS:
            errors.append(f"{label}.operator_view.environment: fields differ from the exact allowlist")
            continue
        if environment.get("table_id") != question.get("table_id"):
            errors.append(f"{label}.operator_view.environment.table_id: question binding mismatch")
        if not all(isinstance(environment.get(key), str) for key in ("title", "section_title")):
            errors.append(f"{label}.operator_view.environment: title fields must be strings")
        if environment.get("capabilities") != VISIBLE_CAPABILITIES:
            errors.append(f"{label}.operator_view.environment.capabilities: contract mismatch")
        columns = environment.get("columns")
        if not isinstance(columns, list) or not columns:
            errors.append(f"{label}.operator_view.environment.columns: expected a non-empty array")
        else:
            for column_index, column in enumerate(columns):
                if (
                    not isinstance(column, dict)
                    or set(column) != COLUMN_KEYS
                    or column.get("index") != column_index
                    or not isinstance(column.get("label"), str)
                    or not isinstance(column.get("entity_link_capability"), bool)
                ):
                    errors.append(
                        f"{label}.operator_view.environment.columns[{column_index}]: invalid projection"
                    )
    return errors


def selected_artifact_set_sha256(artifacts: list[dict[str, Any]]) -> str:
    lines = (
        f"{artifact['sha256']}  {artifact['portable_path']}\n".encode("utf-8")
        for artifact in sorted(
            artifacts,
            key=lambda value: value["portable_path"].encode("utf-8"),
        )
    )
    return hashlib.sha256(b"".join(lines)).hexdigest()


def expected_linked_environment(source: Any) -> dict[str, Any] | None:
    if not isinstance(source, dict) or not isinstance(source.get("upstreams"), list):
        return None
    matches = [
        item
        for item in source["upstreams"]
        if isinstance(item, dict)
        and item.get("source_id") == "hybridqa_linked_tables_and_passages"
    ]
    if len(matches) != 1:
        return None
    upstream = matches[0]
    artifacts = upstream.get("artifacts")
    if not isinstance(artifacts, list):
        return None
    by_path = {
        item.get("path"): item
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    tables = by_path.get("tables_tok")
    requests = by_path.get("request_tok")
    if not isinstance(tables, dict) or not isinstance(requests, dict):
        return None
    return {
        "source_id": upstream.get("source_id"),
        "repository_url": upstream.get("repository_url"),
        "pinned_commit": upstream.get("pinned_commit"),
        "git_tree_sha1": upstream.get("git_tree_sha1"),
        "tables_tree_sha1": tables.get("git_tree_sha1"),
        "request_tree_sha1": requests.get("git_tree_sha1"),
        "tables_file_count": tables.get("file_count"),
        "tables_canonical_content_list_sha256": tables.get(
            "canonical_content_list_sha256"
        ),
        "request_file_count": requests.get("file_count"),
        "request_canonical_content_list_sha256": requests.get(
            "canonical_content_list_sha256"
        ),
    }


def validate_view_manifest(
    manifest: Any,
    questions_path: Path,
    questions: list[dict[str, Any]],
    views_path: Path,
    views: list[dict[str, Any]],
    project_root: Path,
) -> tuple[list[str], str | None]:
    if not isinstance(manifest, dict) or set(manifest) != VIEW_MANIFEST_KEYS:
        return ["input-views manifest fields differ from the exact v0.1 contract"], None
    errors: list[str] = []
    if manifest.get("schema_version") != "granularity_input_views_manifest_v0_1":
        errors.append("input-views manifest schema_version mismatch")
    if manifest.get("builder_version") != "granularity_view_builder_v0_1":
        errors.append("input-views manifest builder_version mismatch")
    provenance = manifest.get("provenance")
    expected_implementation_paths = [
        "data_construction/tools/build_granularity_views.py",
        "data_construction/tools/_common.py",
    ]
    if not isinstance(provenance, dict) or set(provenance) != VIEW_MANIFEST_PROVENANCE_KEYS:
        errors.append("input-views manifest provenance fields differ from the exact contract")
    else:
        code_commit = provenance.get("code_commit")
        errors.extend(
            git_commit_reference_errors(
                code_commit,
                "input-views manifest provenance.code_commit",
                project_root,
            )
        )
        implementations = provenance.get("implementation_artifacts")
        if not isinstance(implementations, list) or len(implementations) != len(
            expected_implementation_paths
        ):
            errors.append("input-views manifest implementation inventory mismatch")
        else:
            for index, (reference, expected_path) in enumerate(
                zip(implementations, expected_implementation_paths, strict=True)
            ):
                label = f"input-views manifest implementation_artifacts[{index}]"
                errors.extend(artifact_reference_errors(reference, label))
                if not isinstance(reference, dict):
                    continue
                if reference.get("repository_relative_path") != expected_path:
                    errors.append(f"{label}: non-canonical implementation path")
                    continue
                live_path = project_root / expected_path
                if not live_path.is_file() or sha256_file(live_path) != reference.get("sha256"):
                    errors.append(f"{label}: live implementation SHA-256 mismatch")
                if isinstance(code_commit, str):
                    committed = subprocess.run(
                        ["git", "-C", str(project_root), "show", f"{code_commit}:{expected_path}"],
                        capture_output=True,
                        check=False,
                    )
                    if (
                        committed.returncode != 0
                        or hashlib.sha256(committed.stdout).hexdigest() != reference.get("sha256")
                    ):
                        errors.append(f"{label}: implementation is not reproduced by code_commit")
    input_artifact = manifest.get("input_views_artifact")
    question_artifact = manifest.get("questions_artifact")
    for value, label, path, count in (
        (input_artifact, "input_views_artifact", views_path, len(views)),
        (question_artifact, "questions_artifact", questions_path, len(questions)),
    ):
        if not isinstance(value, dict) or set(value) != ARTIFACT_KEYS | {"record_count"}:
            errors.append(f"input-views manifest {label}: fields differ from the exact contract")
            continue
        errors.extend(artifact_reference_errors({key: value.get(key) for key in ARTIFACT_KEYS}, label))
        if value.get("record_count") != count:
            errors.append(f"input-views manifest {label}: record count mismatch")
        if value.get("sha256") != sha256_file(path):
            errors.append(f"input-views manifest {label}: live artifact SHA-256 mismatch")
        if value.get("repository_relative_path") != CANONICAL_ARTIFACT_PATHS[label]:
            errors.append(f"input-views manifest {label}: non-canonical repository path")
    split_artifact = manifest.get("split_manifest_artifact")
    source_artifact = manifest.get("source_manifest_artifact")
    split_errors, split_path = live_manifest_artifact_errors(
        split_artifact, "split_manifest_artifact", project_root
    )
    source_errors, source_path = live_manifest_artifact_errors(
        source_artifact, "source_manifest_artifact", project_root
    )
    errors.extend(split_errors)
    errors.extend(source_errors)
    for value, label in (
        (split_artifact, "split_manifest_artifact"),
        (source_artifact, "source_manifest_artifact"),
    ):
        if (
            isinstance(value, dict)
            and value.get("repository_relative_path") != CANONICAL_ARTIFACT_PATHS[label]
        ):
            errors.append(f"input-views manifest {label}: non-canonical repository path")
    split_sha256 = split_artifact.get("sha256") if isinstance(split_artifact, dict) else None
    if split_path is not None and split_path.is_file():
        try:
            split = read_json(split_path)
        except (OSError, ValueError) as exc:
            errors.append(f"cannot read split manifest: {exc}")
        else:
            roles = split.get("roles") if isinstance(split, dict) else None
            role_artifacts = split.get("role_artifacts") if isinstance(split, dict) else None
            pilot_ids = roles.get("annotation_schema_pilot") if isinstance(roles, dict) else None
            pilot_artifact = (
                role_artifacts.get("annotation_schema_pilot") if isinstance(role_artifacts, dict) else None
            )
            observed_ids = [record.get("question_id") for record in questions]
            if pilot_ids != observed_ids:
                errors.append("questions are not in the exact committed annotation-pilot order")
            if (
                not isinstance(pilot_artifact, dict)
                or pilot_artifact.get("sha256") != sha256_file(questions_path)
                or pilot_artifact.get("record_count") != len(questions)
            ):
                errors.append("questions do not match the committed split role artifact")
    linked_environment = manifest.get("linked_environment")
    if not isinstance(linked_environment, dict) or set(linked_environment) != LINKED_ENVIRONMENT_KEYS:
        errors.append("input-views manifest linked_environment fields differ from the exact contract")
    elif source_path is None:
        errors.append("input-views manifest linked_environment cannot be checked without its source")
    else:
        try:
            source = read_json(source_path)
        except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read linked-environment source manifest: {exc}")
        else:
            expected_linked = expected_linked_environment(source)
            if expected_linked is None or linked_environment != expected_linked:
                errors.append("input-views manifest linked_environment disagrees with pinned source")

    selected = manifest.get("selected_environment_artifacts")
    if not isinstance(selected, dict) or set(selected) != SELECTED_ENVIRONMENT_KEYS:
        errors.append("input-views manifest selected_environment_artifacts fields differ")
    else:
        artifacts = selected.get("artifacts")
        expected_paths = sorted(
            [
                f"{prefix}/{question.get('table_id')}.json"
                for question in questions
                for prefix in ("tables_tok", "request_tok")
            ],
            key=lambda value: value.encode("utf-8"),
        )
        if not isinstance(artifacts, list) or len(artifacts) != len(expected_paths):
            errors.append("selected environment must contain exactly 60 table/request artifacts")
        else:
            observed_paths: list[Any] = []
            valid_artifacts = True
            for index, artifact in enumerate(artifacts):
                if (
                    not isinstance(artifact, dict)
                    or set(artifact) != SELECTED_ARTIFACT_KEYS
                    or not isinstance(artifact.get("portable_path"), str)
                    or not is_sha256(artifact.get("sha256"))
                ):
                    errors.append(f"selected environment artifact {index} is malformed")
                    valid_artifacts = False
                    continue
                observed_paths.append(artifact["portable_path"])
            if observed_paths != expected_paths:
                errors.append("selected environment paths do not match the exact pilot tables")
            if valid_artifacts:
                tables = [
                    artifact
                    for artifact in artifacts
                    if artifact["portable_path"].startswith("tables_tok/")
                ]
                requests = [
                    artifact
                    for artifact in artifacts
                    if artifact["portable_path"].startswith("request_tok/")
                ]
                recomputed = {
                    "tables_canonical_sha256": selected_artifact_set_sha256(tables),
                    "requests_canonical_sha256": selected_artifact_set_sha256(requests),
                    "canonical_sha256": selected_artifact_set_sha256(artifacts),
                }
                if recomputed != EXPECTED_SELECTED_ENVIRONMENT_HASHES:
                    errors.append("selected environment hashes differ from the audited v0.1 subset")
                for field, expected in recomputed.items():
                    if selected.get(field) != expected:
                        errors.append(f"selected environment {field} is internally inconsistent")
        if selected.get("file_count") != len(expected_paths):
            errors.append("selected environment file_count mismatch")
        if selected.get("canonicalization") != "sha256_of_path_sorted_sha256sum_lines_v0_1":
            errors.append("selected environment canonicalization mismatch")

    if manifest.get("view_contract") != EXPECTED_VIEW_CONTRACT:
        errors.append("input-views manifest leakage projection contract mismatch")
    return errors, split_sha256 if is_sha256(split_sha256) else None


def validate_topology(
    topology: Any,
    label: str,
    allowed_operators: set[str],
) -> list[str]:
    if not isinstance(topology, dict) or set(topology) != TOPOLOGY_KEYS:
        return [f"{label}: fields differ from the exact topology contract"]
    errors: list[str] = []
    nodes = topology.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append(f"{label}.nodes: expected a non-empty array")
    else:
        for index, node in enumerate(nodes):
            if not isinstance(node, dict) or set(node) != NODE_KEYS:
                errors.append(f"{label}.nodes[{index}]: fields differ from the exact node contract")
                continue
            if not isinstance(node.get("id"), str) or not node["id"]:
                errors.append(f"{label}.nodes[{index}].id: expected a non-empty string")
            if node.get("operator") not in allowed_operators:
                errors.append(f"{label}.nodes[{index}].operator: not in the bound vocabulary")
            depends_on = node.get("depends_on")
            if (
                not isinstance(depends_on, list)
                or not all(isinstance(value, str) and value for value in depends_on)
                or len(depends_on) != len(set(depends_on))
            ):
                errors.append(f"{label}.nodes[{index}].depends_on: invalid dependency array")
            if not isinstance(node.get("semantic_role"), str) or not node["semantic_role"].strip():
                errors.append(f"{label}.nodes[{index}].semantic_role: expected a non-empty string")
    for field in ("entry_node_ids", "output_node_ids"):
        identifiers = topology.get(field)
        if (
            not isinstance(identifiers, list)
            or not identifiers
            or not all(isinstance(value, str) and value for value in identifiers)
            or len(identifiers) != len(set(identifiers))
        ):
            errors.append(f"{label}.{field}: expected a non-empty unique string array")
    if isinstance(nodes, list) and nodes and all(
        isinstance(node, dict)
        and isinstance(node.get("id"), str)
        and isinstance(node.get("depends_on"), list)
        and all(isinstance(value, str) for value in node["depends_on"])
        for node in nodes
    ):
        node_ids = {node["id"] for node in nodes}
        expected_entries = {node["id"] for node in nodes if not node["depends_on"]}
        depended_on = {
            dependency
            for node in nodes
            for dependency in node["depends_on"]
            if dependency in node_ids
        }
        expected_outputs = node_ids - depended_on
        declared_entries = topology.get("entry_node_ids")
        declared_outputs = topology.get("output_node_ids")
        if (
            isinstance(declared_entries, list)
            and all(isinstance(value, str) for value in declared_entries)
            and set(declared_entries) != expected_entries
        ):
            errors.append(f"{label}.entry_node_ids: must declare every and only DAG root")
        if (
            isinstance(declared_outputs, list)
            and all(isinstance(value, str) for value in declared_outputs)
            and set(declared_outputs) != expected_outputs
        ):
            errors.append(f"{label}.output_node_ids: must declare every and only DAG sink")
    errors.extend(topology_errors(topology, label, allowed_operators))
    return errors


def validate_representation(
    representation: Any,
    label: str,
    granularity: str,
    allowed_operators: set[str],
    vocabulary_reference: dict[str, str],
) -> list[str]:
    if not isinstance(representation, dict):
        return [f"{label}: expected an object"]
    if set(representation) != REPRESENTATION_KEYS:
        return [f"{label}: fields differ from the exact representation contract"]
    errors: list[str] = []
    if representation.get("granularity") != granularity:
        errors.append(f"{label}.granularity: key/value mismatch")
    vocabulary = representation.get("vocabulary")
    if not isinstance(vocabulary, dict) or set(vocabulary) != VOCABULARY_KEYS:
        errors.append(f"{label}.vocabulary: fields differ from the exact binding contract")
    elif vocabulary != vocabulary_reference:
        errors.append(f"{label}.vocabulary: does not match the live candidate vocabulary")
    errors.extend(
        validate_topology(representation.get("topology"), f"{label}.topology", allowed_operators)
    )
    coverage_status = representation.get("coverage_status")
    gaps = representation.get("coverage_gaps")
    requires_new = representation.get("requires_new_operator")
    new_operators = representation.get("new_operators")
    if coverage_status not in {"covered", "not_covered"}:
        errors.append(f"{label}.coverage_status: unexpected value")
    if not isinstance(gaps, list):
        errors.append(f"{label}.coverage_gaps: expected an array")
    else:
        gap_hashes: list[str] = []
        for index, gap in enumerate(gaps):
            if not isinstance(gap, dict) or set(gap) != COVERAGE_GAP_KEYS:
                errors.append(f"{label}.coverage_gaps[{index}]: fields differ from the exact gap contract")
                continue
            if gap.get("category") not in {
                "missing_semantic_operation",
                "missing_typed_contract",
                "missing_environment_capability",
                "granularity_mismatch",
                "other",
            }:
                errors.append(f"{label}.coverage_gaps[{index}].category: unexpected value")
            for field in ("description", "required_contract"):
                if not isinstance(gap.get(field), str) or not gap[field].strip():
                    errors.append(f"{label}.coverage_gaps[{index}].{field}: expected non-empty string")
            gap_hashes.append(canonical_json_sha256(gap))
        if len(gap_hashes) != len(set(gap_hashes)):
            errors.append(f"{label}.coverage_gaps: duplicate gap objects")
    if not isinstance(requires_new, bool):
        errors.append(f"{label}.requires_new_operator: expected boolean")
    if (
        not isinstance(new_operators, list)
        or not all(
            isinstance(value, str)
            and value
            and value[0] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            and value.upper() == value
            and set(value) <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
            and value not in allowed_operators
            for value in new_operators
        )
        or len(new_operators) != len(set(new_operators))
    ):
        errors.append(f"{label}.new_operators: expected unique reusable names absent from the vocabulary")
    if coverage_status == "covered" and (gaps != [] or requires_new is not False or new_operators != []):
        errors.append(f"{label}: covered representations cannot declare gaps or new operators")
    if coverage_status == "not_covered" and (
        not gaps or requires_new is not True or not new_operators
    ):
        errors.append(f"{label}: not_covered representations require gaps and new operators")
    for field in (
        "coverage_rationale",
        "new_operator_rationale",
        "ambiguity_rationale",
        "hidden_reasoning_rationale",
        "fragmentation_rationale",
    ):
        if not isinstance(representation.get(field), str) or not representation[field].strip():
            errors.append(f"{label}.{field}: expected a non-empty string")
    for field in ("ambiguity_present", "hides_reasoning", "excessive_fragmentation"):
        if not isinstance(representation.get(field), bool):
            errors.append(f"{label}.{field}: expected boolean")
    alternatives = representation.get("alternative_plans")
    if not isinstance(alternatives, list):
        errors.append(f"{label}.alternative_plans: expected an array")
    else:
        plan_ids: list[str] = []
        for index, alternative in enumerate(alternatives):
            alternative_label = f"{label}.alternative_plans[{index}]"
            if not isinstance(alternative, dict) or set(alternative) != ALTERNATIVE_KEYS:
                errors.append(f"{alternative_label}: fields differ from the exact alternative contract")
                continue
            plan_id = alternative.get("plan_id")
            if not isinstance(plan_id, str) or not plan_id:
                errors.append(f"{alternative_label}.plan_id: expected a non-empty string")
            else:
                plan_ids.append(plan_id)
            for field in ("condition", "rationale"):
                if not isinstance(alternative.get(field), str) or not alternative[field].strip():
                    errors.append(f"{alternative_label}.{field}: expected a non-empty string")
            if alternative.get("coverage_status") not in {"covered", "not_covered"}:
                errors.append(f"{alternative_label}.coverage_status: unexpected value")
            errors.extend(
                validate_topology(
                    alternative.get("topology"),
                    f"{alternative_label}.topology",
                    allowed_operators,
                )
            )
        if len(plan_ids) != len(set(plan_ids)):
            errors.append(f"{label}.alternative_plans: duplicate plan_id values")
    return errors


def validate_provenance(value: Any, label: str, project_root: Path) -> list[str]:
    if not isinstance(value, dict) or set(value) != PROVENANCE_KEYS:
        return [f"{label}: fields differ from the exact provenance contract"]
    errors: list[str] = []
    for field in (
        "annotation_status",
        "creator_kind",
        "model_id",
        "model_revision",
        "model_revision_status",
        "run_id",
        "code_commit",
        "raw_model_output_status",
        "generation_status",
    ):
        if not isinstance(value.get(field), str) or not value[field].strip():
            errors.append(f"{label}.{field}: expected a non-empty string")
    if value.get("annotation_status") != "llm_proposed":
        errors.append(f"{label}.annotation_status: must remain llm_proposed")
    if value.get("creator_kind") != "model_assisted":
        errors.append(f"{label}.creator_kind: unexpected value")
    if value.get("model_revision_status") not in {
        "exact_revision_recorded",
        "revision_not_exposed",
    }:
        errors.append(f"{label}.model_revision_status: unexpected value")
    if (
        value.get("model_revision_status") == "revision_not_exposed"
        and value.get("model_revision") != "revision_not_exposed_to_session"
    ):
        errors.append(f"{label}.model_revision: must record the unexposed-revision sentinel")
    if value.get("raw_model_output_status") not in {
        "preserved_hash_bound",
        "not_exposed_by_interface",
        "not_recorded",
    }:
        errors.append(f"{label}.raw_model_output_status: unexpected value")
    if value.get("generation_status") != "completed":
        errors.append(f"{label}.generation_status: unexpected value")
    code_commit = value.get("code_commit")
    if not isinstance(code_commit, str) or len(code_commit) != 40 or not set(code_commit) <= HEX_DIGITS:
        errors.append(f"{label}.code_commit: expected a full lowercase Git OID")
    else:
        exists = subprocess.run(
            ["git", "-C", str(project_root), "cat-file", "-e", f"{code_commit}^{{commit}}"],
            text=True,
            capture_output=True,
            check=False,
        )
        if exists.returncode != 0:
            errors.append(f"{label}.code_commit: commit object is unavailable in local Git")
        else:
            ancestor = subprocess.run(
                ["git", "-C", str(project_root), "merge-base", "--is-ancestor", code_commit, "HEAD"],
                text=True,
                capture_output=True,
                check=False,
            )
            if ancestor.returncode == 1:
                errors.append(f"{label}.code_commit: commit is not an ancestor of current HEAD")
            elif ancestor.returncode != 0:
                errors.append(f"{label}.code_commit: cannot verify Git ancestry")
    seed = value.get("seed")
    if not isinstance(seed, dict) or set(seed) not in ({"status"}, {"status", "value"}):
        errors.append(f"{label}.seed: fields differ from the exact seed contract")
    else:
        status = seed.get("status")
        if status not in {"specified", "not_supported", "not_exposed", "not_recorded"}:
            errors.append(f"{label}.seed.status: unexpected value")
        if status == "specified" and "value" not in seed:
            errors.append(f"{label}.seed: specified seed lacks a value")
        if status != "specified" and "value" in seed:
            errors.append(f"{label}.seed: non-specified seed cannot contain a value")
        if "value" in seed and not isinstance(seed["value"], int):
            errors.append(f"{label}.seed.value: expected an integer")
    structured = value.get("structured_proposal_artifact")
    structured_label = f"{label}.structured_proposal_artifact"
    structured_errors, _ = live_manifest_artifact_errors(
        structured,
        structured_label,
        project_root,
    )
    errors.extend(structured_errors)
    if (
        isinstance(structured, dict)
        and structured.get("repository_relative_path")
        != CANONICAL_ARTIFACT_PATHS["structured_proposal_artifact"]
    ):
        errors.append(f"{structured_label}: non-canonical repository path")
    errors.extend(
        implementation_commit_errors(
            code_commit,
            [
                project_root / "data_construction/tools/_common.py",
                project_root
                / "data_construction/tools/build_granularity_representations.py",
            ],
            f"{label}.code_commit",
            project_root,
        )
    )
    return errors


def validate_plan_materialization(
    records: list[dict[str, Any]],
    vocabularies: dict[str, set[str]],
    vocabulary_references: dict[str, dict[str, str]],
    plan_path: Path,
) -> list[str]:
    """Require every proposal to be the exact deterministic projection of the bound plan."""

    try:
        plan = read_json(plan_path)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot read structured proposal plan: {exc}"]
    if not isinstance(plan, dict) or set(plan) != representation_builder.PLAN_ROOT_KEYS:
        return ["structured proposal plan fields differ from the exact v0.1 contract"]
    if plan.get("schema_version") != "granularity_representation_plan_v0_1":
        return ["structured proposal plan schema_version mismatch"]
    plan_provenance = plan.get("provenance")
    if (
        not isinstance(plan_provenance, dict)
        or set(plan_provenance) != representation_builder.PLAN_PROVENANCE_KEYS
    ):
        return ["structured proposal provenance fields differ from the exact contract"]
    plan_records = plan.get("records")
    gap_catalog = plan.get("gap_catalog")
    if not isinstance(plan_records, list) or len(plan_records) != len(records):
        return ["structured proposal plan does not contain the exact representation count"]
    if not isinstance(gap_catalog, dict):
        return ["structured proposal gap catalog must be an object"]
    errors: list[str] = []
    for index, (record, plan_record) in enumerate(zip(records, plan_records, strict=True)):
        label = f"structured_plan.records[{index}]"
        if not isinstance(plan_record, dict) or set(plan_record) != {
            "question_id",
            "ambiguity_present",
            "ambiguity_rationale",
            "representations",
        }:
            errors.append(f"{label}: fields differ from the exact plan-record contract")
            continue
        if plan_record.get("question_id") != record.get("question_id"):
            errors.append(f"{label}.question_id: representation order/binding mismatch")
            continue
        ambiguity_present = plan_record.get("ambiguity_present")
        ambiguity_rationale = plan_record.get("ambiguity_rationale")
        planned = plan_record.get("representations")
        if not isinstance(ambiguity_present, bool) or not isinstance(
            ambiguity_rationale, str
        ) or not ambiguity_rationale.strip():
            errors.append(f"{label}: ambiguity declaration is invalid")
            continue
        if not isinstance(planned, dict) or set(planned) != set(GRANULARITIES):
            errors.append(f"{label}.representations: expected exactly coarse, medium, and fine")
            continue
        actual = record.get("representations")
        if not isinstance(actual, dict):
            continue
        for granularity in GRANULARITIES:
            try:
                expected = representation_builder.materialize_representation(
                    planned[granularity],
                    granularity,
                    vocabularies[granularity],
                    vocabulary_references[granularity],
                    f"{label}.representations.{granularity}",
                    ambiguity_present,
                    ambiguity_rationale,
                    gap_catalog,
                )
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if actual.get(granularity) != expected:
                errors.append(
                    f"representations[{index}].representations.{granularity}: "
                    "does not equal deterministic structured-plan materialization"
                )
        provenance = record.get("provenance")
        if isinstance(provenance, dict):
            for field, expected in plan_provenance.items():
                if provenance.get(field) != expected:
                    errors.append(
                        f"representations[{index}].provenance.{field}: "
                        "does not match structured proposal provenance"
                    )
    return errors


def validate_representation_records(
    records: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    views: list[dict[str, Any]],
    input_views_path: Path,
    input_views_manifest_path: Path,
    vocabularies: dict[str, set[str]],
    vocabulary_references: dict[str, dict[str, str]],
    project_root: Path,
    plan_path: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if len(records) != len(questions):
        return ["representations and questions must have the same record count"]
    input_views_sha256 = sha256_file(input_views_path)
    input_views_manifest_sha256 = sha256_file(input_views_manifest_path)
    expected_input_path = portable_path(input_views_path, project_root)
    expected_manifest_path = portable_path(input_views_manifest_path, project_root)
    for index, (record, question, view_record) in enumerate(
        zip(records, questions, views, strict=True)
    ):
        label = f"representations[{index}]"
        question_id = question.get("question_id")
        if set(record) != ROOT_REPRESENTATION_KEYS:
            errors.append(f"{label}: fields differ from the exact root representation contract")
            continue
        if record.get("schema_version") != "operator_granularity_pilot_v0_1":
            errors.append(f"{label}.schema_version: unexpected value")
        if record.get("question_id") != question_id:
            errors.append(f"{label}.question_id: not in exact pilot order")
        if record.get("source_split") != question.get("source_split"):
            errors.append(f"{label}.source_split: question binding mismatch")
        if record.get("dataset_role") != question.get("dataset_role"):
            errors.append(f"{label}.dataset_role: question binding mismatch")
        binding = record.get("input_views")
        if not isinstance(binding, dict) or set(binding) != INPUT_BINDING_KEYS:
            errors.append(f"{label}.input_views: fields differ from the exact input binding contract")
        else:
            artifact = binding.get("artifact")
            manifest_artifact = binding.get("manifest_artifact")
            errors.extend(artifact_reference_errors(artifact, f"{label}.input_views.artifact"))
            errors.extend(
                artifact_reference_errors(
                    manifest_artifact, f"{label}.input_views.manifest_artifact"
                )
            )
            if isinstance(artifact, dict) and (
                artifact.get("sha256") != input_views_sha256
                or (expected_input_path is not None and artifact.get("repository_relative_path") != expected_input_path)
            ):
                errors.append(f"{label}.input_views.artifact: live input-view binding mismatch")
            if isinstance(manifest_artifact, dict) and (
                manifest_artifact.get("sha256") != input_views_manifest_sha256
                or (
                    expected_manifest_path is not None
                    and manifest_artifact.get("repository_relative_path") != expected_manifest_path
                )
            ):
                errors.append(f"{label}.input_views.manifest_artifact: live manifest binding mismatch")
            if binding.get("question_view_sha256") != view_record.get("question_view_sha256"):
                errors.append(f"{label}.input_views.question_view_sha256: view binding mismatch")
            if binding.get("operator_view_sha256") != view_record.get("operator_view_sha256"):
                errors.append(f"{label}.input_views.operator_view_sha256: view binding mismatch")
            if binding.get("representation_input") != "operator_environment":
                errors.append(f"{label}.input_views.representation_input: must be operator_environment")
        errors.extend(
            validate_provenance(record.get("provenance"), f"{label}.provenance", project_root)
        )
        representations = record.get("representations")
        if not isinstance(representations, dict) or set(representations) != set(GRANULARITIES):
            errors.append(f"{label}.representations: expected exactly coarse, medium, and fine")
            continue
        for granularity in GRANULARITIES:
            errors.extend(
                validate_representation(
                    representations.get(granularity),
                    f"{label}.representations.{granularity}",
                    granularity,
                    vocabularies[granularity],
                    vocabulary_references[granularity],
                )
            )
    errors.extend(
        validate_plan_materialization(
            records,
            vocabularies,
            vocabulary_references,
            plan_path
            if plan_path is not None
            else project_root / CANONICAL_ARTIFACT_PATHS["structured_proposal_artifact"],
        )
    )
    return errors


def validator_implementation_paths(project_root: Path) -> list[Path]:
    tool_dir = project_root / "data_construction/tools"
    return [
        tool_dir / name
        for name in (
            "_common.py",
            "build_granularity_representations.py",
            "compare_operator_granularity.py",
            "validate_annotation.py",
            "validate_operator_granularity.py",
        )
    ]


def implementation_commit_errors(
    commit: Any,
    paths: list[Path],
    label: str,
    project_root: Path,
) -> list[str]:
    errors = git_commit_reference_errors(commit, label, project_root)
    if errors or not isinstance(commit, str):
        return errors
    for path in paths:
        try:
            relative = path.resolve().relative_to(project_root.resolve()).as_posix()
        except ValueError:
            errors.append(f"{label}: implementation path escapes the project root")
            continue
        committed = subprocess.run(
            ["git", "-C", str(project_root), "show", f"{commit}:{relative}"],
            capture_output=True,
            check=False,
        )
        if (
            not path.is_file()
            or committed.returncode != 0
            or hashlib.sha256(committed.stdout).hexdigest() != sha256_file(path)
        ):
            errors.append(f"{label}: commit does not reproduce live implementation {relative}")
    return errors


def validate_checks(
    checks: list[dict[str, Any]],
    records: list[dict[str, Any]],
    questions_path: Path,
    representations_path: Path,
    input_views_path: Path,
    input_views_manifest_path: Path,
    split_manifest_sha256: str | None,
    vocabulary_references: dict[str, dict[str, str]],
    schema_sha256: str,
) -> list[str]:
    errors: list[str] = []
    project_root = Path(__file__).resolve().parents[2]
    validator_paths = validator_implementation_paths(project_root)
    validator_implementation_sha256 = implementation_artifact_set_sha256(
        project_root, validator_paths
    )
    expected_count = len(records) * len(GRANULARITIES)
    if len(checks) != expected_count:
        return [
            f"validation checks must contain exactly {expected_count} ordered records; observed {len(checks)}"
        ]
    common_context = {
        "representations_artifact_sha256": sha256_file(representations_path),
        "questions_artifact_sha256": sha256_file(questions_path),
        "split_manifest_artifact_sha256": split_manifest_sha256,
        "input_views_artifact_sha256": sha256_file(input_views_path),
        "input_views_manifest_artifact_sha256": sha256_file(input_views_manifest_path),
        "schema_artifact_sha256": schema_sha256,
        "validator_implementation_artifacts_sha256": validator_implementation_sha256,
        "validation_mode": VALIDATION_MODE,
    }
    check_index = 0
    for record in records:
        representations = record.get("representations")
        for granularity in GRANULARITIES:
            check = checks[check_index]
            label = f"validation_checks[{check_index}]"
            check_index += 1
            if set(check) != CHECK_KEYS:
                errors.append(f"{label}: fields differ from the exact validation-record contract")
                continue
            if check.get("schema_version") != VALIDATION_RECORD_VERSION:
                errors.append(f"{label}.schema_version: unexpected value")
            if check.get("validator_version") != VALIDATOR_VERSION:
                errors.append(f"{label}.validator_version: unexpected value")
            if check.get("question_id") != record.get("question_id"):
                errors.append(f"{label}.question_id: not in exact representation order")
            if check.get("granularity") != granularity:
                errors.append(f"{label}.granularity: not in coarse/medium/fine order")
            representation = (
                representations.get(granularity) if isinstance(representations, dict) else None
            )
            if check.get("representation_canonical_sha256") != canonical_json_sha256(representation):
                errors.append(f"{label}.representation_canonical_sha256: canonical hash mismatch")
            context = check.get("validation_context")
            if not isinstance(context, dict) or set(context) != CHECK_CONTEXT_KEYS:
                errors.append(f"{label}.validation_context: fields differ from the exact contract")
            else:
                expected_context = {
                    **common_context,
                    "operator_vocabulary_artifact_sha256": vocabulary_references[granularity][
                        "sha256"
                    ],
                }
                validator_commit = context.get("validator_code_commit")
                errors.extend(
                    implementation_commit_errors(
                        validator_commit,
                        validator_paths,
                        f"{label}.validation_context.validator_code_commit",
                        project_root,
                    )
                )
                comparable_context = dict(context)
                comparable_context.pop("validator_code_commit", None)
                if comparable_context != expected_context:
                    errors.append(f"{label}.validation_context: live artifact binding mismatch")
            if check.get("status") != "pass" or check.get("errors") != [] or check.get("warnings") != []:
                errors.append(f"{label}: expected a warning-free pass record")
    return errors


def expected_artifact_path(path: Path, project_root: Path) -> str:
    relative = portable_path(path, project_root)
    return relative if relative is not None else f"<external-artifact>/{path.name}"


def resolve_manifest_artifact(
    reference: dict[str, Any],
    manifest_path: Path,
    project_root: Path,
) -> Path | None:
    path_value = reference.get("repository_relative_path")
    if not isinstance(path_value, str):
        return None
    if path_value.startswith("<external-artifact>/"):
        parts = path_value.split("/")
        if len(parts) != 2 or not parts[1]:
            return None
        raw_candidate = manifest_path.resolve().parent / parts[1]
    else:
        raw_candidate = project_root.resolve() / path_value
    if raw_candidate.is_symlink() or not raw_candidate.is_file():
        return None
    candidate = raw_candidate.resolve()
    if not path_value.startswith("<external-artifact>/"):
        try:
            candidate.relative_to(project_root.resolve())
        except ValueError:
            return None
    return candidate


def review_packet_payload(
    records: list[dict[str, Any]],
    views: list[dict[str, Any]],
    granularity: str,
) -> dict[str, Any]:
    return {
        "schema_version": "operator_granularity_review_packet_payload_v0_1",
        "granularity": granularity,
        "reviewed_view": "operator_granularity_representation",
        "items": [
            {
                "question_id": record["question_id"],
                "operator_view": view["operator_view"],
                "candidate_representation": record["representations"][granularity],
                "reviewed_representation_sha256": canonical_json_sha256(
                    record["representations"][granularity]
                ),
            }
            for record, view in zip(records, views, strict=True)
        ],
    }


def git_commit_reference_errors(value: Any, label: str, project_root: Path) -> list[str]:
    if not isinstance(value, str) or len(value) != 40 or not set(value) <= HEX_DIGITS:
        return [f"{label}: expected a full lowercase Git OID"]
    exists = subprocess.run(
        ["git", "-C", str(project_root), "cat-file", "-e", f"{value}^{{commit}}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if exists.returncode != 0:
        return [f"{label}: commit object is unavailable in local Git"]
    ancestor = subprocess.run(
        ["git", "-C", str(project_root), "merge-base", "--is-ancestor", value, "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if ancestor.returncode == 1:
        return [f"{label}: commit is not an ancestor of current HEAD"]
    if ancestor.returncode != 0:
        return [f"{label}: cannot verify Git ancestry"]
    return []


def validate_review_packet_manifests(
    paths: list[Path],
    records: list[dict[str, Any]],
    views: list[dict[str, Any]],
    artifact_paths: dict[str, Path],
    project_root: Path,
) -> tuple[list[str], dict[str, str], list[dict[str, Any]]]:
    errors: list[str] = []
    payload_hashes: dict[str, str] = {}
    provenance: list[dict[str, Any]] = []
    if len(paths) != len(GRANULARITIES):
        return ["human calibration requires exactly one review-packet manifest per granularity"], {}, []
    if len({path.resolve() for path in paths}) != len(paths):
        return ["review-packet manifest paths must be unique"], {}, []
    expected_inputs = {
        label: {
            "repository_relative_path": expected_artifact_path(path, project_root),
            "sha256": sha256_file(path),
        }
        for label, path in artifact_paths.items()
    }
    for manifest_index, path in enumerate(paths):
        label = f"review_packet_manifests[{manifest_index}]"
        if path.is_symlink():
            errors.append(f"{label}: manifest path must not be a symlink")
            continue
        try:
            manifest = read_json(path)
        except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{label}: cannot read strict JSON: {exc}")
            continue
        if not isinstance(manifest, dict) or set(manifest) != REVIEW_PACKET_MANIFEST_KEYS:
            errors.append(f"{label}: fields differ from the exact packet-manifest contract")
            continue
        granularity = manifest.get("granularity")
        if granularity not in GRANULARITIES or granularity in payload_hashes:
            errors.append(f"{label}.granularity: expected one unique coarse/medium/fine manifest")
            continue
        if (
            manifest.get("schema_version")
            != "operator_granularity_review_packet_manifest_v0_1"
            or manifest.get("builder_version")
            != "operator_granularity_review_packet_builder_v0_1"
            or manifest.get("question_count") != EXPECTED_PILOT_QUESTIONS
            or manifest.get("review_status") != "packet_created_no_human_reviews"
            or manifest.get("human_reviews_created_by_builder") is not False
        ):
            errors.append(f"{label}: schema, count, or truthful builder status mismatch")
        expected_payload = review_packet_payload(records, views, granularity)
        expected_payload_sha256 = canonical_json_sha256(expected_payload)
        packet_payload = manifest.get("packet_payload")
        if not isinstance(packet_payload, dict) or set(packet_payload) != REVIEW_PACKET_PAYLOAD_KEYS:
            errors.append(f"{label}.packet_payload: fields differ from the exact contract")
        elif packet_payload != {
            "canonicalization": CANONICALIZATION,
            "sha256": expected_payload_sha256,
            "reviewed_view": "operator_granularity_representation",
            "contains_only_operator_view_and_candidate_representation": True,
        }:
            errors.append(f"{label}.packet_payload: does not match the reconstructed live payload")
        packet_artifact = manifest.get("packet_artifact")
        packet_errors = artifact_reference_errors(packet_artifact, f"{label}.packet_artifact")
        errors.extend(packet_errors)
        packet_path = (
            resolve_manifest_artifact(packet_artifact, path, project_root)
            if isinstance(packet_artifact, dict) and not packet_errors
            else None
        )
        if packet_path is None:
            errors.append(f"{label}.packet_artifact: live packet is missing or unsafe")
        elif sha256_file(packet_path) != packet_artifact.get("sha256"):
            errors.append(f"{label}.packet_artifact: live packet SHA-256 mismatch")
        else:
            try:
                packet_text = packet_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"{label}.packet_artifact: cannot read packet: {exc}")
            else:
                # The file digest alone binds only arbitrary bytes. Re-render the
                # approved v0.1 packet so a manifest cannot bless an HTML file
                # that merely contains the expected hash while showing altered
                # questions or representations to reviewers.
                from build_granularity_review_packet import render_html

                expected_packet_text = render_html(expected_payload, expected_payload_sha256)
                if packet_text != expected_packet_text:
                    errors.append(
                        f"{label}.packet_artifact: live HTML differs from the deterministic "
                        "approved rendering"
                    )
        inputs = manifest.get("inputs")
        if not isinstance(inputs, dict) or set(inputs) != REVIEW_PACKET_INPUT_KEYS:
            errors.append(f"{label}.inputs: fields differ from the exact input contract")
        else:
            for input_label in sorted(REVIEW_PACKET_INPUT_KEYS):
                reference = inputs.get(input_label)
                errors.extend(
                    artifact_reference_errors(reference, f"{label}.inputs.{input_label}")
                )
                if reference != expected_inputs[input_label]:
                    errors.append(f"{label}.inputs.{input_label}: live artifact binding mismatch")
        validation = manifest.get("validation")
        expected_validation = {
            "validation_record_version": VALIDATION_RECORD_VERSION,
            "validator_version": VALIDATOR_VERSION,
            "validation_mode": VALIDATION_MODE,
            "exact_question_id_order_verified": True,
            "selected_granularity_pass_check_count": EXPECTED_PILOT_QUESTIONS,
            "live_artifact_hashes_verified": True,
            "leakage_projection_verified": True,
        }
        if (
            not isinstance(validation, dict)
            or set(validation) != REVIEW_PACKET_VALIDATION_KEYS
            or validation != expected_validation
        ):
            errors.append(f"{label}.validation: exact validation evidence mismatch")
        contract = manifest.get("review_record_contract")
        expected_contract = {
            "schema_version": "operator_representation_review_v0_1",
            "canonicalization": CANONICALIZATION,
            "decisions": list(REVIEW_DECISIONS),
            "assessment_fields": sorted(REVIEW_ASSESSMENT_KEYS),
            "reviewer_identity": "stable_pseudonymous_id",
            "reviewer_authentication": "procedural_not_machine_verifiable",
            "reviews_included": 0,
        }
        if (
            not isinstance(contract, dict)
            or set(contract) != REVIEW_RECORD_CONTRACT_KEYS
            or contract != expected_contract
        ):
            errors.append(f"{label}.review_record_contract: exact contract mismatch")
        manifest_provenance = manifest.get("provenance")
        if not isinstance(manifest_provenance, dict) or set(manifest_provenance) != {
            "code_commit",
            "builder_does_not_claim_human_review",
        }:
            errors.append(f"{label}.provenance: fields differ from the exact contract")
        else:
            if manifest_provenance.get("builder_does_not_claim_human_review") is not True:
                errors.append(f"{label}.provenance: builder human-review claim is not truthful")
            errors.extend(
                implementation_commit_errors(
                    manifest_provenance.get("code_commit"),
                    [
                        project_root / "data_construction/tools/_common.py",
                        project_root
                        / "data_construction/tools/build_granularity_representations.py",
                        project_root
                        / "data_construction/tools/build_granularity_review_packet.py",
                        project_root
                        / "data_construction/tools/compare_operator_granularity.py",
                        project_root / "data_construction/tools/validate_annotation.py",
                        project_root
                        / "data_construction/tools/validate_operator_granularity.py",
                    ],
                    f"{label}.provenance.code_commit",
                    project_root,
                )
            )
        payload_hashes[granularity] = expected_payload_sha256
        provenance.append(
            {
                "granularity": granularity,
                "manifest_artifact_sha256": sha256_file(path),
                "packet_artifact_sha256": (
                    packet_artifact.get("sha256") if isinstance(packet_artifact, dict) else None
                ),
                "packet_payload_sha256": expected_payload_sha256,
            }
        )
    if set(payload_hashes) != set(GRANULARITIES):
        errors.append("review-packet manifests do not cover exactly coarse, medium, and fine")
    return errors, payload_hashes, sorted(provenance, key=lambda value: value["granularity"])


def valid_reviewer_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 3 <= len(value) <= 128
        and value[0] in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        and set(value)
        <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")
    )


def valid_completed_at(value: Any) -> bool:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def expected_assessment(representation: dict[str, Any]) -> dict[str, Any]:
    return {
        "semantic_validity": "valid",
        "coverage_status": representation.get("coverage_status"),
        "ambiguity_present": representation.get("ambiguity_present"),
        "hides_reasoning": representation.get("hides_reasoning"),
        "excessive_fragmentation": representation.get("excessive_fragmentation"),
    }


def review_assessment_errors(
    value: Any,
    decision: Any,
    original: dict[str, Any],
    edit: Any,
    label: str,
) -> list[str]:
    if not isinstance(value, dict) or set(value) != REVIEW_ASSESSMENT_KEYS:
        return [f"{label}: fields differ from the exact assessment contract"]
    errors: list[str] = []
    if value.get("semantic_validity") not in {"valid", "invalid", "uncertain"}:
        errors.append(f"{label}.semantic_validity: unexpected value")
    if value.get("coverage_status") not in {"covered", "not_covered", "uncertain"}:
        errors.append(f"{label}.coverage_status: unexpected value")
    for field in ("ambiguity_present", "hides_reasoning", "excessive_fragmentation"):
        candidate = value.get(field)
        if not isinstance(candidate, bool) and candidate != "uncertain":
            errors.append(f"{label}.{field}: expected boolean or 'uncertain'")
    uncertain = {
        "semantic_validity": "uncertain",
        "coverage_status": "uncertain",
        "ambiguity_present": "uncertain",
        "hides_reasoning": "uncertain",
        "excessive_fragmentation": "uncertain",
    }
    if decision == "abstain" and value != uncertain:
        errors.append(f"{label}: abstention must mark every assessment dimension uncertain")
    elif decision == "accept" and value != expected_assessment(original):
        errors.append(f"{label}: accept must confirm the exact original assessment")
    elif decision == "accept_with_edits" and isinstance(edit, dict):
        if value != expected_assessment(edit):
            errors.append(f"{label}: edited acceptance must match the corrected representation")
    elif decision == "reject" and value.get("semantic_validity") != "invalid":
        errors.append(f"{label}: reject must mark semantic_validity invalid")
    return errors


def validate_human_reviews(
    paths: list[Path],
    records: list[dict[str, Any]],
    payload_hashes: dict[str, str],
    vocabularies: dict[str, set[str]],
    vocabulary_references: dict[str, dict[str, str]],
) -> tuple[
    list[str],
    dict[tuple[str, str], tuple[bool, bool, bool, int, int]],
    list[dict[str, Any]],
]:
    errors: list[str] = []
    judgments: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    provenance: list[dict[str, Any]] = []
    reviewer_sets: dict[str, set[str]] = {granularity: set() for granularity in GRANULARITIES}
    seen_reviewer_granularity: set[tuple[str, str]] = set()
    expected_ids = [record["question_id"] for record in records]
    if len({path.resolve() for path in paths}) != len(paths):
        return ["human-review paths must be unique"], {}, []
    for file_index, path in enumerate(paths):
        label = f"human_reviews[{file_index}]"
        if path.is_symlink():
            errors.append(f"{label}: review path must not be a symlink")
            continue
        try:
            raw_reviews = read_json(path)
        except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{label}: cannot read strict JSON review array: {exc}")
            continue
        if not isinstance(raw_reviews, list) or len(raw_reviews) != EXPECTED_PILOT_QUESTIONS:
            errors.append(f"{label}: expected an exact {EXPECTED_PILOT_QUESTIONS}-record array")
            continue
        file_reviewer_id: str | None = None
        file_granularity: str | None = None
        for review_index, (envelope, expected_question_id) in enumerate(
            zip(raw_reviews, expected_ids, strict=True)
        ):
            review_label = f"{label}[{review_index}]"
            if not isinstance(envelope, dict) or set(envelope) != REVIEW_ENVELOPE_KEYS:
                errors.append(f"{review_label}: fields differ from the exact review envelope")
                continue
            reviewer_id = envelope.get("reviewer_id")
            if not valid_reviewer_id(reviewer_id):
                errors.append(f"{review_label}.reviewer_id: invalid stable pseudonymous ID")
            elif file_reviewer_id is None:
                file_reviewer_id = reviewer_id
            elif reviewer_id != file_reviewer_id:
                errors.append(f"{review_label}.reviewer_id: one file must contain one reviewer")
            annotation = envelope.get("annotation")
            if not isinstance(annotation, dict):
                errors.append(f"{review_label}.annotation: expected an object")
                continue
            expected_annotation_keys = REVIEW_ANNOTATION_KEYS | (
                {"corrected_representation_sha256"}
                if annotation.get("decision") == "accept_with_edits"
                else set()
            )
            if set(annotation) != expected_annotation_keys:
                errors.append(f"{review_label}.annotation: fields differ from the exact decision contract")
                continue
            annotation_sha256 = envelope.get("annotation_sha256")
            if not is_sha256(annotation_sha256) or annotation_sha256 != canonical_json_sha256(
                annotation
            ):
                errors.append(f"{review_label}.annotation_sha256: canonical hash mismatch")
            granularity = annotation.get("granularity")
            if granularity not in GRANULARITIES:
                errors.append(f"{review_label}.annotation.granularity: unexpected value")
                continue
            if file_granularity is None:
                file_granularity = granularity
            elif granularity != file_granularity:
                errors.append(f"{review_label}.annotation.granularity: one file must cover one granularity")
            representation = records[review_index]["representations"][granularity]
            if (
                annotation.get("schema_version") != "operator_representation_review_v0_1"
                or annotation.get("question_id") != expected_question_id
                or annotation.get("reviewed_view") != "operator_granularity_representation"
                or annotation.get("reviewed_representation_sha256")
                != canonical_json_sha256(representation)
                or annotation.get("review_packet_payload_sha256")
                != payload_hashes.get(granularity)
            ):
                errors.append(f"{review_label}.annotation: question/representation/packet binding mismatch")
            if not valid_completed_at(annotation.get("completed_at")):
                errors.append(f"{review_label}.annotation.completed_at: expected a UTC ISO-8601 timestamp")
            decision = annotation.get("decision")
            edit = annotation.get("edit")
            notes = annotation.get("notes")
            if decision not in REVIEW_DECISIONS:
                errors.append(f"{review_label}.annotation.decision: unexpected value")
            if notes is not None and not isinstance(notes, str):
                errors.append(f"{review_label}.annotation.notes: expected string or null")
            corrected_sha256 = annotation.get("corrected_representation_sha256")
            if decision == "accept_with_edits":
                if not isinstance(edit, dict):
                    errors.append(f"{review_label}.annotation.edit: edited decision requires an object")
                else:
                    errors.extend(
                        validate_representation(
                            edit,
                            f"{review_label}.annotation.edit",
                            granularity,
                            vocabularies[granularity],
                            vocabulary_references[granularity],
                        )
                    )
                    if (
                        not is_sha256(corrected_sha256)
                        or corrected_sha256 != canonical_json_sha256(edit)
                    ):
                        errors.append(
                            f"{review_label}.annotation.corrected_representation_sha256: mismatch"
                        )
            elif edit is not None or corrected_sha256 is not None:
                errors.append(f"{review_label}.annotation: only accept_with_edits may carry an edit")
            assessment = annotation.get("assessment")
            errors.extend(
                review_assessment_errors(
                    assessment,
                    decision,
                    representation,
                    edit,
                    f"{review_label}.annotation.assessment",
                )
            )
            if (
                valid_reviewer_id(reviewer_id)
                and decision in REVIEW_DECISIONS
                and isinstance(assessment, dict)
                and set(assessment) == REVIEW_ASSESSMENT_KEYS
            ):
                judgments.setdefault((expected_question_id, granularity), []).append(
                    (reviewer_id, decision, canonical_json_sha256(assessment))
                )
        if file_reviewer_id is not None and file_granularity in GRANULARITIES:
            pair = (file_reviewer_id, file_granularity)
            if pair in seen_reviewer_granularity:
                errors.append(f"{label}: duplicate complete reviewer/granularity submission")
            else:
                seen_reviewer_granularity.add(pair)
                reviewer_sets[file_granularity].add(file_reviewer_id)
                provenance.append(
                    {
                        "reviewer_id": file_reviewer_id,
                        "granularity": file_granularity,
                        "record_count": len(raw_reviews),
                        "artifact_sha256": sha256_file(path),
                    }
                )
    for granularity in GRANULARITIES:
        if len(reviewer_sets[granularity]) < 2:
            errors.append(f"{granularity}: fewer than two distinct complete reviewer sets")
    observations: dict[tuple[str, str], tuple[bool, bool, bool, int, int]] = {}
    for question_id in expected_ids:
        for granularity in GRANULARITIES:
            values = judgments.get((question_id, granularity), [])
            abstention_count = sum(decision == "abstain" for _, decision, _ in values)
            substantive = [value for value in values if value[1] != "abstain"]
            reviewer_ids = {reviewer_id for reviewer_id, _, _ in substantive}
            observed = len(reviewer_ids) >= 2
            assessment_hashes = {assessment for _, _, assessment in substantive}
            unanimous_original_acceptance = observed and all(
                decision == "accept" for _, decision, _ in substantive
            )
            observations[(question_id, granularity)] = (
                observed,
                observed and len(assessment_hashes) > 1,
                unanimous_original_acceptance,
                abstention_count,
                len(values),
            )
    return errors, observations, sorted(
        provenance,
        key=lambda value: (value["granularity"], value["reviewer_id"]),
    )


def topology_nodes(representation: dict[str, Any]) -> list[dict[str, Any]]:
    topology = representation.get("topology")
    nodes = topology.get("nodes", []) if isinstance(topology, dict) else []
    return [node for node in nodes if isinstance(node, dict)] if isinstance(nodes, list) else []


def observed_boolean(value: Any, key: str) -> tuple[bool, bool]:
    if not isinstance(value, dict):
        return False, False
    candidate = value.get(key)
    if isinstance(candidate, bool):
        return True, candidate
    return False, False


def summarize(
    records: list[dict[str, Any]],
    granularity: str,
    allowed_operators: set[str],
    human_review_observations: dict[
        tuple[str, str], tuple[bool, bool, bool, int, int]
    ],
) -> dict[str, Any]:
    lengths: list[int] = []
    distinct_counts: list[int] = []
    covered = 0
    coverage_observed = 0
    new_operator = 0
    new_operator_observed = 0
    disagreement = 0
    disagreement_observed = 0
    unanimous_original_acceptance = 0
    original_acceptance_observed = 0
    abstentions = 0
    review_records = 0
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
        question_id = record.get("question_id") if isinstance(record.get("question_id"), str) else "unknown"
        nodes = topology_nodes(representation)
        node_names = [node.get("operator") if isinstance(node.get("operator"), str) else None for node in nodes]
        names = {name for name in node_names if name}
        topology = representation.get("topology")
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
            name = node.get("operator") if isinstance(node.get("operator"), str) else None
            if name:
                operators[name] += 1
        lengths.append(len(nodes))
        distinct_counts.append(len(names))

        coverage_status = representation.get("coverage_status")
        coverage_seen = False
        is_covered = False
        if isinstance(coverage_status, str):
            normalized_coverage = coverage_status.strip().lower()
            if normalized_coverage in {"covered", "not_covered"}:
                coverage_seen = True
                is_covered = normalized_coverage == "covered"
        coverage_observed += int(coverage_seen)
        covered += int(coverage_seen and is_covered)
        new_seen, needs_new = observed_boolean(representation, "requires_new_operator")
        new_operator_observed += int(new_seen)
        new_operator += int(new_seen and needs_new)
        (
            disagreement_seen,
            has_disagreement,
            original_accepted,
            abstention_count,
            review_count,
        ) = human_review_observations.get(
            (question_id, granularity),
            (False, False, False, 0, 0),
        )
        disagreement_observed += int(disagreement_seen)
        disagreement += int(disagreement_seen and has_disagreement)
        original_acceptance_observed += int(disagreement_seen)
        unanimous_original_acceptance += int(disagreement_seen and original_accepted)
        abstentions += abstention_count
        review_records += review_count
        ambiguity_seen, has_ambiguity = observed_boolean(representation, "ambiguity_present")
        ambiguity_observed += int(ambiguity_seen)
        ambiguity += int(ambiguity_seen and has_ambiguity)

        hides_seen, hides = observed_boolean(representation, "hides_reasoning")
        fragments_seen, fragments = observed_boolean(representation, "excessive_fragmentation")
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
        "human_review_record_count": review_records,
        "human_abstention_count": abstentions,
        "unanimous_original_acceptance_observation_count": original_acceptance_observed,
        "unanimous_original_acceptance_count": unanimous_original_acceptance,
        "unanimous_original_acceptance_rate": (
            unanimous_original_acceptance / original_acceptance_observed
            if original_acceptance_observed
            else None
        ),
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
    if not summary["integrity_complete"]:
        caveat = "입력 및 결정론적 검증 무결성이 완전하지 않아 지표를 해석할 수 없다."
    elif not summary["human_calibration_complete"]:
        caveat = (
            "30개 질문의 90개 표현은 구조적으로 검증되었지만 독립적인 실제 사람 검토가 "
            "완료되지 않아 어휘를 동결할 수 없다."
        )
    elif not summary["semantic_confirmation_complete"]:
        caveat = (
            "독립 검토 기록은 완전하지만 거절, 수정, 또는 평가 차원 불일치가 남아 "
            "adjudication 전에는 어휘를 선택할 수 없다."
        )
    else:
        caveat = "정량 지표와 사례 검토를 함께 사용해야 하며 coverage만으로 선택하지 않는다."
    return "\n".join(
        [
            "# Operator granularity study v0.1",
            "",
            f"상태: `{summary['study_status']}`",
            f"구조 무결성: `{str(summary['integrity_complete']).lower()}`",
            f"사람 보정 완료: `{str(summary['human_calibration_complete']).lower()}`",
            f"원 표현 의미 확인 완료: `{str(summary['semantic_confirmation_complete']).lower()}`",
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
    schema_path = project_root / "data_construction/schemas/operator_granularity_pilot_v0_1.json"
    outputs = {"json_output": args.json_output, "report_output": args.report_output}
    optional_review_inputs = {
        **{
            f"human_review_{index}": path
            for index, path in enumerate(args.human_review)
        },
        **{
            f"review_packet_manifest_{index}": path
            for index, path in enumerate(args.review_packet_manifest)
        },
    }
    collisions = output_path_collision_errors(
        {
            "pilot_representations": args.pilot_representations,
            "questions": args.questions,
            "input_views": args.input_views,
            "input_views_manifest": args.input_views_manifest,
            "validation_checks": args.validation_checks,
            "schema": schema_path,
            **vocabulary_inputs,
            **optional_review_inputs,
        },
        outputs,
    )
    collisions.extend(historical_output_collision_errors(outputs, project_root))
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    if bool(args.human_review) != bool(args.review_packet_manifest):
        print(
            "--human-review and --review-packet-manifest must be supplied together",
            file=sys.stderr,
        )
        return 2
    if args.min_questions != EXPECTED_PILOT_QUESTIONS:
        print(
            f"--min-questions must equal the committed pilot count of {EXPECTED_PILOT_QUESTIONS}",
            file=sys.stderr,
        )
        return 2
    try:
        implementation_commit = git_tracked_commit_identity(
            project_root,
            [
                Path(__file__),
                Path(__file__).with_name("_common.py"),
                Path(__file__).with_name("validate_annotation.py"),
                Path(__file__).with_name("build_granularity_review_packet.py"),
                Path(__file__).with_name("build_granularity_representations.py"),
                Path(__file__).with_name("validate_operator_granularity.py"),
            ],
        )
        records = list(iter_json_records(args.pilot_representations))
        questions = list(iter_json_records(args.questions))
        input_views = list(iter_json_records(args.input_views))
        input_views_manifest = read_json(args.input_views_manifest)
        validation_checks = list(iter_json_records(args.validation_checks))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid granularity input JSON: {exc}", file=sys.stderr)
        return 2
    if len(questions) != EXPECTED_PILOT_QUESTIONS:
        print(
            f"questions artifact must contain exactly {EXPECTED_PILOT_QUESTIONS} committed records",
            file=sys.stderr,
        )
        return 2
    if not schema_path.is_file():
        print(f"missing operator-granularity pilot schema: {schema_path}", file=sys.stderr)
        return 2
    vocabularies: dict[str, set[str]] = {}
    vocabulary_provenance: dict[str, dict[str, Any]] = {}
    vocabulary_references: dict[str, dict[str, str]] = {}
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
        expected_version = f"operator_vocabulary_{granularity}_v0_1"
        if (
            first_string(vocabulary, ("vocabulary_version",)) != expected_version
            or first_string(vocabulary, ("granularity",)) != granularity
        ):
            print(f"operator vocabulary identity mismatch: {vocabulary_path}", file=sys.stderr)
            return 2
        vocabulary_repository_path = portable_path(vocabulary_path, project_root)
        if vocabulary_repository_path is None:
            print(f"operator vocabulary must be inside the project: {vocabulary_path}", file=sys.stderr)
            return 2
        vocabulary_references[granularity] = {
            "vocabulary_version": expected_version,
            "repository_relative_path": vocabulary_repository_path,
            "sha256": sha256_file(vocabulary_path),
        }
        vocabulary_provenance[granularity] = {
            "artifact_sha256": sha256_file(vocabulary_path),
            "vocabulary_version": first_string(vocabulary, ("vocabulary_version",)),
            "granularity": first_string(vocabulary, ("granularity",)),
        }
    integrity_errors: list[str] = []
    integrity_errors.extend(validate_question_records(questions))
    integrity_errors.extend(validate_input_views(questions, input_views))
    manifest_errors, split_manifest_sha256 = validate_view_manifest(
        input_views_manifest,
        args.questions,
        questions,
        args.input_views,
        input_views,
        project_root,
    )
    integrity_errors.extend(manifest_errors)
    integrity_errors.extend(
        validate_representation_records(
            records,
            questions,
            input_views,
            args.input_views,
            args.input_views_manifest,
            vocabularies,
            vocabulary_references,
            project_root,
        )
    )
    integrity_errors.extend(
        validate_checks(
            validation_checks,
            records,
            args.questions,
            args.pilot_representations,
            args.input_views,
            args.input_views_manifest,
            split_manifest_sha256,
            vocabulary_references,
            sha256_file(schema_path),
        )
    )
    human_review_observations: dict[
        tuple[str, str], tuple[bool, bool, bool, int, int]
    ] = {}
    human_review_provenance: list[dict[str, Any]] = []
    review_packet_provenance: list[dict[str, Any]] = []
    if args.human_review and not integrity_errors:
        packet_errors, packet_payload_hashes, review_packet_provenance = (
            validate_review_packet_manifests(
                args.review_packet_manifest,
                records,
                input_views,
                {
                    "questions": args.questions,
                    "input_views": args.input_views,
                    "input_views_manifest": args.input_views_manifest,
                    "representations": args.pilot_representations,
                    "validation_checks": args.validation_checks,
                },
                project_root,
            )
        )
        integrity_errors.extend(packet_errors)
        if not packet_errors:
            review_errors, human_review_observations, human_review_provenance = (
                validate_human_reviews(
                    args.human_review,
                    records,
                    packet_payload_hashes,
                    vocabularies,
                    vocabulary_references,
                )
            )
            integrity_errors.extend(review_errors)
    if integrity_errors:
        print(
            "granularity integrity validation failed:\n- " + "\n- ".join(integrity_errors),
            file=sys.stderr,
        )
        return 2
    metrics = {
        granularity: summarize(
            records,
            granularity,
            vocabularies[granularity],
            human_review_observations,
        )
        for granularity in GRANULARITIES
    }
    integrity_complete = len(records) == args.min_questions and all(
        metrics[granularity]["representation_count"] == len(records)
        and metrics[granularity]["valid_topology_observation_count"] == len(records)
        and metrics[granularity]["coverage_observation_count"] == len(records)
        and metrics[granularity]["new_operator_observation_count"] == len(records)
        and metrics[granularity]["ambiguity_observation_count"] == len(records)
        and metrics[granularity]["hidden_reasoning_observation_count"] == len(records)
        and metrics[granularity]["excessive_fragmentation_observation_count"] == len(records)
        for granularity in GRANULARITIES
    )
    human_calibration_complete = integrity_complete and all(
        metrics[granularity]["annotation_disagreement_observation_count"] == len(records)
        for granularity in GRANULARITIES
    )
    evidence_complete = integrity_complete and human_calibration_complete
    semantic_confirmation_complete = evidence_complete and all(
        metrics[granularity]["unanimous_original_acceptance_count"] == len(records)
        for granularity in GRANULARITIES
    )
    selection_ready = semantic_confirmation_complete
    selection_accepted = bool(
        args.selected and selection_ready and args.selection_rationale.strip()
    )
    summary = {
        "schema_version": "operator_granularity_study_v0_1",
        "question_count": len(records),
        "minimum_question_count": args.min_questions,
        "missing_question_id_count": 0,
        "duplicate_question_ids": [],
        "study_status": (
            "complete"
            if semantic_confirmation_complete
            else "human_calibration_complete_adjudication_pending"
            if evidence_complete
            else "structural_integrity_complete_human_calibration_pending"
            if integrity_complete
            else "integrity_incomplete"
        ),
        "integrity_complete": integrity_complete,
        "human_calibration_complete": human_calibration_complete,
        "evidence_complete": evidence_complete,
        "semantic_confirmation_complete": semantic_confirmation_complete,
        "selection_ready": selection_ready,
        "reviewer_authentication_status": "procedural_not_machine_verifiable",
        "metrics": metrics,
        "provisional_decision": (
            args.selected.upper() if selection_accepted else "UNDECIDED_NEEDS_ANNOTATION_EVIDENCE"
        ),
        "selection_rationale": args.selection_rationale if selection_accepted else "",
        "selection_request_accepted": selection_accepted,
        "selection_request_rejection_reason": (
            None
            if not args.selected or selection_accepted
            else (
                "Selection requires complete substantive review assessments, unanimous acceptance "
                "of the original representations or adjudicated replacements, and a non-empty rationale."
            )
        ),
        "scientific_caution": "Coverage alone is not a sufficient selection criterion.",
        "provenance": {
            "tool_version": GRANULARITY_TOOL_VERSION,
            "representations_artifact_sha256": sha256_file(args.pilot_representations),
            "questions_artifact_sha256": sha256_file(args.questions),
            "input_views_artifact_sha256": sha256_file(args.input_views),
            "input_views_manifest_artifact_sha256": sha256_file(args.input_views_manifest),
            "validation_checks_artifact_sha256": sha256_file(args.validation_checks),
            "validation_checks_record_count": len(validation_checks),
            "validation_checks_verified": True,
            "operator_granularity_schema_artifact_sha256": sha256_file(schema_path),
            "split_manifest_artifact_sha256": split_manifest_sha256,
            "human_review_artifacts": human_review_provenance,
            "review_packet_artifacts": review_packet_provenance,
            "vocabularies": vocabulary_provenance,
            "code_commit": implementation_commit,
        },
    }
    output_payloads = {"json_output": (args.json_output, json_file_bytes(summary))}
    if args.report_output is not None:
        output_payloads["report_output"] = (
            args.report_output,
            render_markdown(summary).encode("utf-8"),
        )
    try:
        write_output_batch(output_payloads, overwrite=args.overwrite)
    except (OSError, ValueError) as exc:
        print(f"cannot write operator-granularity comparison: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "questions": len(records),
                "integrity_complete": integrity_complete,
                "human_calibration_complete": human_calibration_complete,
                "evidence_complete": evidence_complete,
                "semantic_confirmation_complete": semantic_confirmation_complete,
            },
            sort_keys=True,
        )
    )
    return 0 if semantic_confirmation_complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
