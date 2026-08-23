#!/usr/bin/env python3
"""Build a hash-bound offline review packet for one operator granularity."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from _common import (
    canonical_json_sha256,
    git_tracked_commit_identity,
    historical_output_collision_errors,
    implementation_artifact_set_sha256,
    iter_json_records,
    json_file_bytes,
    output_path_collision_errors,
    read_json,
    sha256_bytes,
    sha256_file,
    write_output_batch,
)


GRANULARITIES = ("coarse", "medium", "fine")
EXPECTED_QUESTION_COUNT = 30
BUILDER_VERSION = "operator_granularity_review_packet_builder_v0_1"
VALIDATION_RECORD_VERSION = "operator_granularity_validation_record_v0_1"
VALIDATOR_VERSION = "operator_granularity_validator_v0_1"
VALIDATION_MODE = "draft_2020_12_plus_structural_plus_live_artifacts"
REPRESENTATION_SCHEMA_VERSION = "operator_granularity_pilot_v0_1"
REPRESENTATION_SCHEMA_PATH = Path(
    "data_construction/schemas/operator_granularity_pilot_v0_1.json"
)
CANONICALIZATION = "sorted_compact_json_utf8_sha256_v0_1"
HEX_DIGITS = frozenset("0123456789abcdef")

QUESTION_KEYS = {
    "annotation_visibility",
    "dataset_role",
    "question",
    "question_id",
    "source_split",
    "table_id",
}
VIEW_RECORD_KEYS = {
    "schema_version",
    "question_id",
    "question_view",
    "question_view_sha256",
    "operator_view",
    "operator_view_sha256",
}
QUESTION_VIEW_KEYS = {"schema_version", "visibility", "question_id", "question"}
OPERATOR_VIEW_KEYS = {
    "schema_version",
    "visibility",
    "question_id",
    "question",
    "environment",
}
ENVIRONMENT_KEYS = {"table_id", "title", "section_title", "columns", "capabilities"}
COLUMN_KEYS = {"index", "label", "entity_link_capability"}
VISIBLE_CAPABILITIES = {
    "table_access_available": True,
    "linked_document_lookup_available": True,
    "linked_document_text_available_to_later_layers": True,
    "linked_document_text_exposed_in_this_view": False,
    "lookup_scope": "pinned_linked_snapshot_for_current_table",
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
VOCABULARY_KEYS = {"vocabulary_version", "repository_relative_path", "sha256"}
TOPOLOGY_KEYS = {"nodes", "entry_node_ids", "output_node_ids"}
NODE_KEYS = {"id", "operator", "depends_on", "semantic_role"}
ALTERNATIVE_KEYS = {"plan_id", "condition", "rationale", "coverage_status", "topology"}
COVERAGE_GAP_KEYS = {"category", "description", "required_contract"}
COVERAGE_GAP_CATEGORIES = {
    "missing_semantic_operation",
    "missing_typed_contract",
    "missing_environment_capability",
    "granularity_mismatch",
    "other",
}
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
CANONICAL_ARTIFACT_PATHS = {
    "input_views_artifact": "data_construction/pilot/granularity_input_views.jsonl",
    "questions_artifact": "data_construction/pilot/questions.jsonl",
    "split_manifest_artifact": "data_construction/manifests/split_manifest_v0_1.json",
    "source_manifest_artifact": "data_construction/manifests/source_manifest_v0_1.json",
}

# These keys have no place in an abstract operator representation.  Exact
# allowlists do the main leakage work; this recursive denylist is defense in
# depth for nested values and future contract drift.
FORBIDDEN_REPRESENTATION_KEYS = {
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
    "doc",
    "docs",
    "doc_id",
    "doc_ids",
    "document",
    "documents",
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
    "oracle_doc_id",
    "passage",
    "passages",
    "reference_answer",
    "request",
    "requests",
    "row",
    "rows",
    "table_cell",
    "table_row",
    "sample_value",
    "target_answer",
    "trace",
    "traces",
    "value",
    "values",
    "weak_answer_node",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--input-views", required=True, type=Path)
    parser.add_argument("--input-views-manifest", required=True, type=Path)
    parser.add_argument("--representations", required=True, type=Path)
    parser.add_argument("--validation-checks", required=True, type=Path)
    parser.add_argument("--granularity", required=True, choices=GRANULARITIES)
    parser.add_argument("--output", required=True, type=Path, help="Self-contained HTML packet")
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing packet artifacts only when their bytes differ",
    )
    return parser.parse_args()


def is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in HEX_DIGITS for character in value)
    )


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def require_sha256(value: Any, label: str) -> str:
    if not is_sha256(value):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def canonical_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.casefold())


def forbidden_key_paths(value: Any, prefix: str = "$") -> list[str]:
    forbidden = {canonical_key(key) for key in FORBIDDEN_REPRESENTATION_KEYS}
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}"
            if canonical_key(key) in forbidden:
                paths.append(child_path)
            paths.extend(forbidden_key_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(forbidden_key_paths(child, f"{prefix}[{index}]"))
    return paths


def safe_repository_relative_path(value: Any, label: str) -> str:
    path_string = require_string(value, label)
    path = Path(path_string)
    if (
        path.is_absolute()
        or path_string.startswith(("~", "/"))
        or "\\" in path_string
        or "\r" in path_string
        or "\n" in path_string
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"{label} is not a safe repository-relative path")
    return path.as_posix()


def artifact_reference(
    value: Any,
    label: str,
    expected_sha256: str | None = None,
    expected_path: str | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != ARTIFACT_KEYS:
        raise ValueError(f"{label} fields differ from the exact artifact contract")
    observed_path = safe_repository_relative_path(
        value.get("repository_relative_path"), f"{label}.repository_relative_path"
    )
    digest = require_sha256(value.get("sha256"), f"{label}.sha256")
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"{label}.sha256 does not match the live artifact")
    if expected_path is not None and observed_path != expected_path:
        raise ValueError(f"{label}.repository_relative_path is not the canonical artifact path")
    return value


def portable_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return f"<external-artifact>/{path.name}"


def historical_tree_collision_errors(outputs: dict[str, Path], project_root: Path) -> list[str]:
    protected_roots = [project_root / "historical"]
    errors: list[str] = []
    for label, output in outputs.items():
        resolved = output.resolve()
        for protected in protected_roots:
            try:
                resolved.relative_to(protected.resolve())
            except ValueError:
                continue
            errors.append(f"output {label!r} targets read-only historical evidence: {resolved}")
            break
    return errors


def validate_questions(records: list[dict[str, Any]]) -> list[str]:
    if len(records) != EXPECTED_QUESTION_COUNT:
        raise ValueError(
            f"questions must contain exactly {EXPECTED_QUESTION_COUNT} records, observed {len(records)}"
        )
    identifiers: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        label = f"questions[{index}]"
        if set(record) != QUESTION_KEYS:
            raise ValueError(f"{label} fields differ from the exact pilot contract")
        question_id = require_string(record.get("question_id"), f"{label}.question_id")
        if question_id in seen:
            raise ValueError(f"{label}.question_id is duplicated")
        seen.add(question_id)
        identifiers.append(question_id)
        require_string(record.get("question"), f"{label}.question")
        require_string(record.get("table_id"), f"{label}.table_id")
        if record.get("source_split") != "dev":
            raise ValueError(f"{label}.source_split must be 'dev'")
        if record.get("dataset_role") != "annotation_schema_pilot":
            raise ValueError(f"{label}.dataset_role is not the pilot role")
        if record.get("annotation_visibility") != "question_and_table_identity_only":
            raise ValueError(f"{label}.annotation_visibility violates the pilot contract")
    return identifiers


def validate_input_views(
    records: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    expected_ids: list[str],
) -> list[dict[str, Any]]:
    if len(records) != EXPECTED_QUESTION_COUNT:
        raise ValueError(
            f"input views must contain exactly {EXPECTED_QUESTION_COUNT} records, observed {len(records)}"
        )
    operator_views: list[dict[str, Any]] = []
    for index, (record, question, expected_id) in enumerate(zip(records, questions, expected_ids)):
        label = f"input_views[{index}]"
        if not isinstance(record, dict) or set(record) != VIEW_RECORD_KEYS:
            raise ValueError(f"{label} fields differ from the exact view-wrapper contract")
        if record.get("schema_version") != "granularity_input_views_v0_1":
            raise ValueError(f"{label}.schema_version is unsupported")
        if record.get("question_id") != expected_id:
            raise ValueError(f"{label} is outside the exact pilot ID/order")

        question_view = record.get("question_view")
        if not isinstance(question_view, dict) or set(question_view) != QUESTION_VIEW_KEYS:
            raise ValueError(f"{label}.question_view fields differ from the exact contract")
        if (
            question_view.get("schema_version") != "granularity_question_view_v0_1"
            or question_view.get("visibility") != "question_only_no_environment_or_answer"
            or question_view.get("question_id") != expected_id
            or question_view.get("question") != question.get("question")
        ):
            raise ValueError(f"{label}.question_view does not match the live question")
        if record.get("question_view_sha256") != canonical_json_sha256(question_view):
            raise ValueError(f"{label}.question_view_sha256 does not match its live view")

        operator_view = record.get("operator_view")
        if not isinstance(operator_view, dict) or set(operator_view) != OPERATOR_VIEW_KEYS:
            raise ValueError(f"{label}.operator_view fields differ from the exact contract")
        if (
            operator_view.get("schema_version") != "granularity_operator_view_v0_1"
            or operator_view.get("visibility")
            != "question_plus_table_schema_and_capabilities_no_values"
            or operator_view.get("question_id") != expected_id
            or operator_view.get("question") != question.get("question")
        ):
            raise ValueError(f"{label}.operator_view does not match the live question")
        environment = operator_view.get("environment")
        if not isinstance(environment, dict) or set(environment) != ENVIRONMENT_KEYS:
            raise ValueError(f"{label}.operator_view.environment fields differ from the exact contract")
        if environment.get("table_id") != question.get("table_id"):
            raise ValueError(f"{label}.operator_view has the wrong table identity")
        for field in ("title", "section_title"):
            if not isinstance(environment.get(field), str):
                raise ValueError(f"{label}.operator_view.environment.{field} must be a string")
        columns = environment.get("columns")
        if not isinstance(columns, list) or not columns:
            raise ValueError(f"{label}.operator_view.environment.columns must be non-empty")
        for column_index, column in enumerate(columns):
            column_label = f"{label}.operator_view.environment.columns[{column_index}]"
            if not isinstance(column, dict) or set(column) != COLUMN_KEYS:
                raise ValueError(f"{column_label} fields differ from the exact schema projection")
            if column.get("index") != column_index:
                raise ValueError(f"{column_label}.index is not contiguous")
            if not isinstance(column.get("label"), str):
                raise ValueError(f"{column_label}.label must be a string")
            if not isinstance(column.get("entity_link_capability"), bool):
                raise ValueError(f"{column_label}.entity_link_capability must be boolean")
        if environment.get("capabilities") != VISIBLE_CAPABILITIES:
            raise ValueError(f"{label}.operator_view.environment.capabilities changed")
        if record.get("operator_view_sha256") != canonical_json_sha256(operator_view):
            raise ValueError(f"{label}.operator_view_sha256 does not match its live view")
        operator_views.append(operator_view)
    return operator_views


def validate_topology(value: Any, label: str, allowed_operators: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != TOPOLOGY_KEYS:
        raise ValueError(f"{label} fields differ from the exact topology contract")
    nodes = value.get("nodes")
    entries = value.get("entry_node_ids")
    outputs = value.get("output_node_ids")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError(f"{label}.nodes must be a non-empty list")
    if not isinstance(entries, list) or not entries or not isinstance(outputs, list) or not outputs:
        raise ValueError(f"{label} must declare non-empty entry/output node lists")
    identifiers: list[str] = []
    for index, node in enumerate(nodes):
        node_label = f"{label}.nodes[{index}]"
        if not isinstance(node, dict) or set(node) != NODE_KEYS:
            raise ValueError(f"{node_label} fields differ from the exact node contract")
        identifier = require_string(node.get("id"), f"{node_label}.id")
        operator = require_string(node.get("operator"), f"{node_label}.operator")
        if operator not in allowed_operators:
            raise ValueError(f"{node_label}.operator is outside the bound candidate vocabulary")
        require_string(node.get("semantic_role"), f"{node_label}.semantic_role")
        dependencies = node.get("depends_on")
        if (
            not isinstance(dependencies, list)
            or any(not isinstance(item, str) or not item for item in dependencies)
            or len(dependencies) != len(set(dependencies))
        ):
            raise ValueError(f"{node_label}.depends_on must be a unique string list")
        identifiers.append(identifier)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{label} has duplicate node IDs")
    identifier_set = set(identifiers)
    if (
        any(not isinstance(item, str) for item in entries + outputs)
        or len(entries) != len(set(entries))
        or len(outputs) != len(set(outputs))
        or not set(entries + outputs).issubset(identifier_set)
    ):
        raise ValueError(f"{label} has invalid entry/output references")
    by_id = {node["id"]: node for node in nodes}
    for node in nodes:
        if node["id"] in node["depends_on"] or not set(node["depends_on"]).issubset(identifier_set):
            raise ValueError(f"{label} has invalid dependency references")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise ValueError(f"{label} contains a dependency cycle")
        if identifier in visited:
            return
        visiting.add(identifier)
        for dependency in by_id[identifier]["depends_on"]:
            visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in identifiers:
        visit(identifier)
    expected_entries = {node["id"] for node in nodes if not node["depends_on"]}
    depended_on = {dependency for node in nodes for dependency in node["depends_on"]}
    expected_outputs = identifier_set - depended_on
    if set(entries) != expected_entries or set(outputs) != expected_outputs:
        raise ValueError(f"{label} entry/output declarations do not match the DAG")


def validate_representation(
    value: Any,
    granularity: str,
    label: str,
    allowed_operators: set[str],
) -> None:
    if not isinstance(value, dict) or set(value) != REPRESENTATION_KEYS:
        raise ValueError(f"{label} fields differ from the exact representation contract")
    contaminated = forbidden_key_paths(value)
    if contaminated:
        raise ValueError(f"{label} contains forbidden later-layer keys: {contaminated[:10]!r}")
    if value.get("granularity") != granularity:
        raise ValueError(f"{label}.granularity does not match its representation slot")
    vocabulary = value.get("vocabulary")
    if not isinstance(vocabulary, dict) or set(vocabulary) != VOCABULARY_KEYS:
        raise ValueError(f"{label}.vocabulary fields differ from the exact contract")
    expected_version = f"operator_vocabulary_{granularity}_v0_1"
    expected_path = f"data_construction/operator_design/{expected_version}.json"
    if (
        vocabulary.get("vocabulary_version") != expected_version
        or vocabulary.get("repository_relative_path") != expected_path
    ):
        raise ValueError(f"{label}.vocabulary identity is unsupported")
    require_sha256(vocabulary.get("sha256"), f"{label}.vocabulary.sha256")
    validate_topology(value.get("topology"), f"{label}.topology", allowed_operators)
    coverage_status = value.get("coverage_status")
    if coverage_status not in {"covered", "not_covered"}:
        raise ValueError(f"{label}.coverage_status is invalid")
    gaps = value.get("coverage_gaps")
    if not isinstance(gaps, list):
        raise ValueError(f"{label}.coverage_gaps must be a list")
    for index, gap in enumerate(gaps):
        gap_label = f"{label}.coverage_gaps[{index}]"
        if not isinstance(gap, dict) or set(gap) != COVERAGE_GAP_KEYS:
            raise ValueError(f"{gap_label} fields differ from the exact contract")
        if gap.get("category") not in COVERAGE_GAP_CATEGORIES:
            raise ValueError(f"{gap_label}.category is invalid")
        require_string(gap.get("description"), f"{gap_label}.description")
        require_string(gap.get("required_contract"), f"{gap_label}.required_contract")
    if len({canonical_json_sha256(gap) for gap in gaps}) != len(gaps):
        raise ValueError(f"{label}.coverage_gaps contains duplicate objects")
    new_operators = value.get("new_operators")
    if (
        not isinstance(new_operators, list)
        or any(
            not isinstance(item, str)
            or not item
            or item[0] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            or item.upper() != item
            or not set(item) <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
            or item in allowed_operators
            for item in new_operators
        )
        or len(new_operators) != len(set(new_operators))
    ):
        raise ValueError(
            f"{label}.new_operators must be unique reusable names absent from the vocabulary"
        )
    requires_new = value.get("requires_new_operator")
    if not isinstance(requires_new, bool) or requires_new != bool(new_operators):
        raise ValueError(f"{label}.requires_new_operator disagrees with new_operators")
    if coverage_status == "covered" and (gaps or new_operators):
        raise ValueError(f"{label} is covered but declares coverage gaps")
    if coverage_status == "not_covered" and (not gaps or not new_operators):
        raise ValueError(f"{label} is not covered but does not identify its gap")
    for field in (
        "coverage_rationale",
        "new_operator_rationale",
        "ambiguity_rationale",
        "hidden_reasoning_rationale",
        "fragmentation_rationale",
    ):
        require_string(value.get(field), f"{label}.{field}")
    for field in ("ambiguity_present", "hides_reasoning", "excessive_fragmentation"):
        if not isinstance(value.get(field), bool):
            raise ValueError(f"{label}.{field} must be boolean")
    alternatives = value.get("alternative_plans")
    if not isinstance(alternatives, list):
        raise ValueError(f"{label}.alternative_plans must be a list")
    seen_plan_ids: set[str] = set()
    for index, alternative in enumerate(alternatives):
        alternative_label = f"{label}.alternative_plans[{index}]"
        if not isinstance(alternative, dict) or set(alternative) != ALTERNATIVE_KEYS:
            raise ValueError(f"{alternative_label} fields differ from the exact contract")
        plan_id = require_string(alternative.get("plan_id"), f"{alternative_label}.plan_id")
        if plan_id in seen_plan_ids:
            raise ValueError(f"{label} has duplicate alternative plan IDs")
        seen_plan_ids.add(plan_id)
        require_string(alternative.get("condition"), f"{alternative_label}.condition")
        require_string(alternative.get("rationale"), f"{alternative_label}.rationale")
        if alternative.get("coverage_status") not in {"covered", "not_covered"}:
            raise ValueError(f"{alternative_label}.coverage_status is invalid")
        validate_topology(
            alternative.get("topology"),
            f"{alternative_label}.topology",
            allowed_operators,
        )


def vocabulary_operators(path: Path, granularity: str) -> set[str]:
    value = read_json(path)
    operators = value.get("operators") if isinstance(value, dict) else None
    if (
        not isinstance(value, dict)
        or value.get("granularity") != granularity
        or value.get("vocabulary_version") != f"operator_vocabulary_{granularity}_v0_1"
        or not isinstance(operators, list)
    ):
        raise ValueError(f"live {granularity} vocabulary has an invalid identity or inventory")
    names = {
        item.get("name")
        for item in operators
        if isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"]
    }
    if not names or len(names) != len(operators):
        raise ValueError(f"live {granularity} vocabulary has duplicate or malformed operators")
    return names


def validate_provenance(value: Any, label: str, project_root: Path) -> None:
    if not isinstance(value, dict) or set(value) != PROVENANCE_KEYS:
        raise ValueError(f"{label} fields differ from the exact provenance contract")
    if value.get("annotation_status") != "llm_proposed":
        raise ValueError(f"{label}.annotation_status must remain 'llm_proposed'")
    if value.get("creator_kind") != "model_assisted" or value.get("generation_status") != "completed":
        raise ValueError(f"{label} has invalid creator/generation status")
    for field in ("model_id", "model_revision", "run_id"):
        require_string(value.get(field), f"{label}.{field}")
    if value.get("model_revision_status") not in {"exact_revision_recorded", "revision_not_exposed"}:
        raise ValueError(f"{label}.model_revision_status is invalid")
    if value.get("model_revision_status") == "revision_not_exposed" and value.get(
        "model_revision"
    ) != "revision_not_exposed_to_session":
        raise ValueError(f"{label}.model_revision is not truthful for an unexposed revision")
    if value.get("raw_model_output_status") not in {
        "preserved_hash_bound",
        "not_exposed_by_interface",
        "not_recorded",
    }:
        raise ValueError(f"{label}.raw_model_output_status is invalid")
    code_commit = value.get("code_commit")
    if not isinstance(code_commit, str) or len(code_commit) != 40 or any(
        character not in HEX_DIGITS for character in code_commit
    ):
        raise ValueError(f"{label}.code_commit must be a full lowercase Git OID")
    exists = subprocess.run(
        ["git", "-C", str(project_root), "cat-file", "-e", f"{code_commit}^{{commit}}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if exists.returncode != 0:
        raise ValueError(f"{label}.code_commit is unavailable in local Git")
    ancestor = subprocess.run(
        ["git", "-C", str(project_root), "merge-base", "--is-ancestor", code_commit, "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if ancestor.returncode == 1:
        raise ValueError(f"{label}.code_commit is not an ancestor of current HEAD")
    if ancestor.returncode != 0:
        raise ValueError(f"{label}.code_commit ancestry cannot be verified")
    seed = value.get("seed")
    if not isinstance(seed, dict) or seed.get("status") not in {
        "specified",
        "not_supported",
        "not_exposed",
        "not_recorded",
    }:
        raise ValueError(f"{label}.seed is invalid")
    expected_seed_keys = {"status", "value"} if seed.get("status") == "specified" else {"status"}
    if set(seed) != expected_seed_keys or (
        seed.get("status") == "specified" and not isinstance(seed.get("value"), int)
    ):
        raise ValueError(f"{label}.seed fields disagree with its status")
    structured = artifact_reference(
        value.get("structured_proposal_artifact"),
        f"{label}.structured_proposal_artifact",
        expected_path="data_construction/pilot/granularity_representation_plan_v0_1.json",
    )
    structured_path = (project_root / structured["repository_relative_path"]).resolve()
    try:
        structured_path.relative_to(project_root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label}.structured_proposal_artifact escapes the project root") from exc
    if not structured_path.is_file() or sha256_file(structured_path) != structured["sha256"]:
        raise ValueError(f"{label}.structured_proposal_artifact does not match its live hash")


def validate_representation_records(
    records: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    views: list[dict[str, Any]],
    expected_ids: list[str],
    input_views_sha256: str,
    input_views_manifest_sha256: str,
    project_root: Path,
) -> None:
    if len(records) != EXPECTED_QUESTION_COUNT:
        raise ValueError(
            f"representations must contain exactly {EXPECTED_QUESTION_COUNT} records, observed {len(records)}"
        )
    vocabulary_paths = {
        granularity: project_root
        / f"data_construction/operator_design/operator_vocabulary_{granularity}_v0_1.json"
        for granularity in GRANULARITIES
    }
    allowed_operators = {
        granularity: vocabulary_operators(path, granularity)
        for granularity, path in vocabulary_paths.items()
    }
    for index, (record, question, view, expected_id) in enumerate(
        zip(records, questions, views, expected_ids)
    ):
        label = f"representations[{index}]"
        if not isinstance(record, dict) or set(record) != ROOT_REPRESENTATION_KEYS:
            raise ValueError(f"{label} fields differ from the exact root contract")
        if (
            record.get("schema_version") != REPRESENTATION_SCHEMA_VERSION
            or record.get("question_id") != expected_id
            or record.get("source_split") != question.get("source_split")
            or record.get("dataset_role") != question.get("dataset_role")
        ):
            raise ValueError(f"{label} does not match the exact pilot ID/order/role")
        binding = record.get("input_views")
        if not isinstance(binding, dict) or set(binding) != INPUT_BINDING_KEYS:
            raise ValueError(f"{label}.input_views fields differ from the exact binding contract")
        artifact_reference(
            binding.get("artifact"),
            f"{label}.input_views.artifact",
            input_views_sha256,
            CANONICAL_ARTIFACT_PATHS["input_views_artifact"],
        )
        artifact_reference(
            binding.get("manifest_artifact"),
            f"{label}.input_views.manifest_artifact",
            input_views_manifest_sha256,
            "data_construction/pilot/granularity_input_views_manifest_v0_1.json",
        )
        if (
            binding.get("question_view_sha256") != view.get("question_view_sha256")
            or binding.get("operator_view_sha256") != view.get("operator_view_sha256")
            or binding.get("representation_input") != "operator_environment"
        ):
            raise ValueError(f"{label}.input_views is not bound to the exact live views")
        validate_provenance(record.get("provenance"), f"{label}.provenance", project_root)
        representations = record.get("representations")
        if not isinstance(representations, dict) or set(representations) != set(GRANULARITIES):
            raise ValueError(f"{label}.representations must contain exactly coarse/medium/fine")
        for granularity in GRANULARITIES:
            representation = representations[granularity]
            validate_representation(
                representation,
                granularity,
                f"{label}.representations.{granularity}",
                allowed_operators[granularity],
            )
            vocabulary_path = vocabulary_paths[granularity]
            if not vocabulary_path.is_file() or representation["vocabulary"]["sha256"] != sha256_file(
                vocabulary_path
            ):
                raise ValueError(
                    f"{label}.representations.{granularity}.vocabulary does not match its live artifact"
                )


def validate_checks(
    checks: list[dict[str, Any]],
    records: list[dict[str, Any]],
    expected_ids: list[str],
    selected_granularity: str,
    live_hashes: dict[str, str],
    split_manifest_sha256: str,
    project_root: Path,
) -> int:
    import compare_operator_granularity as comparator

    validator_paths = comparator.validator_implementation_paths(project_root)
    validator_implementation_sha256 = implementation_artifact_set_sha256(
        project_root, validator_paths
    )
    expected_order = [
        (question_id, granularity)
        for question_id in expected_ids
        for granularity in GRANULARITIES
    ]
    if len(checks) != len(expected_order):
        raise ValueError(
            f"validation checks must contain exactly {len(expected_order)} q-by-granularity records"
        )
    schema_path = project_root / REPRESENTATION_SCHEMA_PATH
    if not schema_path.is_file():
        raise ValueError(f"live representation schema is missing: {REPRESENTATION_SCHEMA_PATH}")
    schema_sha256 = sha256_file(schema_path)
    selected_passes = 0
    for index, (check, expected) in enumerate(zip(checks, expected_order)):
        question_id, granularity = expected
        label = f"validation_checks[{index}]"
        if not isinstance(check, dict) or set(check) != CHECK_KEYS:
            raise ValueError(f"{label} fields differ from the exact validation-record contract")
        if (
            check.get("schema_version") != VALIDATION_RECORD_VERSION
            or check.get("question_id") != question_id
            or check.get("granularity") != granularity
            or check.get("validator_version") != VALIDATOR_VERSION
        ):
            raise ValueError(f"{label} is outside the exact q-by-granularity order/contract")
        representation = records[index // len(GRANULARITIES)]["representations"][granularity]
        if check.get("representation_canonical_sha256") != canonical_json_sha256(representation):
            raise ValueError(f"{label} is not bound to the exact representation")
        context = check.get("validation_context")
        if not isinstance(context, dict) or set(context) != CHECK_CONTEXT_KEYS:
            raise ValueError(f"{label}.validation_context fields differ from the exact contract")
        vocabulary_path = project_root / (
            f"data_construction/operator_design/operator_vocabulary_{granularity}_v0_1.json"
        )
        expected_context = {
            "representations_artifact_sha256": live_hashes["representations"],
            "questions_artifact_sha256": live_hashes["questions"],
            "split_manifest_artifact_sha256": split_manifest_sha256,
            "input_views_artifact_sha256": live_hashes["input_views"],
            "input_views_manifest_artifact_sha256": live_hashes["input_views_manifest"],
            "schema_artifact_sha256": schema_sha256,
            "operator_vocabulary_artifact_sha256": sha256_file(vocabulary_path),
            "validator_implementation_artifacts_sha256": validator_implementation_sha256,
            "validation_mode": VALIDATION_MODE,
        }
        commit_errors = comparator.implementation_commit_errors(
            context.get("validator_code_commit"),
            validator_paths,
            f"{label}.validation_context.validator_code_commit",
            project_root,
        )
        if commit_errors:
            raise ValueError("; ".join(commit_errors))
        comparable_context = dict(context)
        comparable_context.pop("validator_code_commit", None)
        if comparable_context != expected_context:
            raise ValueError(f"{label}.validation_context does not match the live artifact set")
        errors = check.get("errors")
        warnings = check.get("warnings")
        if not isinstance(errors, list) or any(not isinstance(item, str) for item in errors):
            raise ValueError(f"{label}.errors must be a string list")
        if not isinstance(warnings, list) or any(not isinstance(item, str) for item in warnings):
            raise ValueError(f"{label}.warnings must be a string list")
        if check.get("status") not in {"pass", "fail"}:
            raise ValueError(f"{label}.status is invalid")
        if check.get("status") == "pass" and errors:
            raise ValueError(f"{label} claims pass while recording errors")
        if check.get("status") == "fail" and not errors:
            raise ValueError(f"{label} claims failure without recording an error")
        if granularity == selected_granularity:
            if check.get("status") != "pass" or errors or warnings:
                raise ValueError(
                    f"{label} is not a warning-free pass for the selected granularity"
                )
            selected_passes += 1
    if selected_passes != EXPECTED_QUESTION_COUNT:
        raise ValueError(
            f"selected granularity has {selected_passes} pass checks; expected {EXPECTED_QUESTION_COUNT}"
        )
    return selected_passes


def build_payload(
    records: list[dict[str, Any]],
    operator_views: list[dict[str, Any]],
    granularity: str,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for record, operator_view in zip(records, operator_views):
        representation = record["representations"][granularity]
        items.append(
            {
                "question_id": record["question_id"],
                # Deliberately copy only the approved operator_view, never the
                # surrounding view wrapper or either source/view manifest.
                "operator_view": operator_view,
                "candidate_representation": representation,
                "reviewed_representation_sha256": canonical_json_sha256(representation),
            }
        )
    return {
        "schema_version": "operator_granularity_review_packet_payload_v0_1",
        "granularity": granularity,
        "reviewed_view": "operator_granularity_representation",
        "items": items,
    }


def render_html(payload: dict[str, Any], payload_sha256: str) -> str:
    granularity = payload["granularity"]
    embedded_payload = (
        json.dumps(payload, ensure_ascii=False, allow_nan=False)
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HybridQA operator review — {html.escape(granularity)}</title>
<style>
:root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
body {{ max-width: 1160px; margin: 2rem auto; padding: 0 1rem 5rem; line-height: 1.45; }}
.notice {{ border-left: .35rem solid #6b46c1; padding: .8rem 1rem; background: color-mix(in srgb, Canvas 92%, #805ad5 8%); }}
.card {{ border: 1px solid #a0aec0; border-radius: .6rem; padding: 1rem; margin: 1.25rem 0; }}
.schema {{ width: 100%; border-collapse: collapse; }} .schema th, .schema td {{ border: 1px solid #a0aec0; padding: .35rem .5rem; text-align: left; }}
pre, textarea {{ width: 100%; box-sizing: border-box; white-space: pre-wrap; overflow-wrap: anywhere; }}
pre {{ padding: .75rem; background: color-mix(in srgb, Canvas 94%, #718096 6%); }}
textarea {{ min-height: 9rem; }} label {{ display: block; margin-top: .8rem; font-weight: 650; }}
.graph {{ overflow-x: auto; margin: .75rem 0; }} .graph svg {{ border: 1px solid #a0aec0; background: Canvas; }}
.metrics dt {{ font-weight: 700; margin-top: .55rem; }} .metrics dd {{ margin-left: 1.2rem; }}
button {{ padding: .7rem 1rem; font-weight: 650; }} input, select, textarea {{ font: inherit; }}
</style>
</head>
<body>
<h1>HybridQA 연산자 표현 독립 검토 패킷</h1>
<p class="notice"><strong>세분성:</strong> {html.escape(granularity)}. 이 패킷은 질문, 표 schema/capability, 후보 추상 그래프와 측정 근거만 포함합니다. 표 row/cell 값, 문서 ID/본문, 정답, grounding, 실행 결과는 포함하지 않습니다. 생성 도구는 사람 검토를 만들거나 주장하지 않습니다.</p>
<p><strong>패킷 payload SHA-256:</strong> <code>{html.escape(payload_sha256)}</code></p>
<label for="reviewer-id">검토자 익명 ID (이름·이메일 금지)</label>
<input id="reviewer-id" type="text" autocomplete="off" required pattern="[A-Za-z0-9][A-Za-z0-9._-]{{2,127}}" maxlength="128" placeholder="reviewer-pseudonym">
<div id="items"></div>
<button id="download" type="button">원시 검토 record 다운로드</button>
<script>
'use strict';
const packet = {embedded_payload};
const packetPayloadSha256 = {json.dumps(payload_sha256)};
const root = document.getElementById('items');
const controls = [];

function addText(parent, tag, value) {{
  const element = document.createElement(tag); element.textContent = String(value); parent.appendChild(element); return element;
}}

function canonicalJson(value) {{
  if (Array.isArray(value)) return '[' + value.map(canonicalJson).join(',') + ']';
  if (value !== null && typeof value === 'object') {{
    return '{{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonicalJson(value[key])).join(',') + '}}';
  }}
  return JSON.stringify(value);
}}

async function sha256Canonical(value) {{
  const bytes = new TextEncoder().encode(canonicalJson(value));
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}}

function addReviewSelect(parent, labelText, values) {{
  const label = document.createElement('label'); label.textContent = labelText;
  const select = document.createElement('select');
  ['unreviewed', ...values].forEach(value => {{
    const option = document.createElement('option'); option.value = value; option.textContent = value; select.appendChild(option);
  }});
  label.appendChild(select); parent.appendChild(label); return select;
}}

function triState(value) {{
  if (value === 'true') return true;
  if (value === 'false') return false;
  return 'uncertain';
}}

function expectedAssessment(representation) {{
  return {{
    semantic_validity: 'valid',
    coverage_status: representation.coverage_status,
    ambiguity_present: representation.ambiguity_present,
    hides_reasoning: representation.hides_reasoning,
    excessive_fragmentation: representation.excessive_fragmentation,
  }};
}}

function sameAssessment(left, right) {{
  return canonicalJson(left) === canonicalJson(right);
}}

function forbiddenEditKey(value) {{
  const denied = new Set({json.dumps(sorted(canonical_key(key) for key in FORBIDDEN_REPRESENTATION_KEYS))});
  if (Array.isArray(value)) return value.some(forbiddenEditKey);
  if (value !== null && typeof value === 'object') {{
    return Object.entries(value).some(([key, child]) => denied.has(key.toLowerCase().replace(/[^a-z0-9]/g, '')) || forbiddenEditKey(child));
  }}
  return false;
}}

function hasExactKeys(value, expected) {{
  if (value === null || Array.isArray(value) || typeof value !== 'object') return false;
  const observed = Object.keys(value).sort(); const wanted = [...expected].sort();
  return observed.length === wanted.length && observed.every((key, index) => key === wanted[index]);
}}

function validEditedTopology(topology) {{
  if (!hasExactKeys(topology, {json.dumps(sorted(TOPOLOGY_KEYS))}) || !Array.isArray(topology.nodes) || !topology.nodes.length) return false;
  if (!Array.isArray(topology.entry_node_ids) || !topology.entry_node_ids.length || !Array.isArray(topology.output_node_ids) || !topology.output_node_ids.length) return false;
  return topology.nodes.every(node => hasExactKeys(node, {json.dumps(sorted(NODE_KEYS))}) && Array.isArray(node.depends_on));
}}

function validCorrectedRepresentation(value) {{
  if (!hasExactKeys(value, {json.dumps(sorted(REPRESENTATION_KEYS))}) || value.granularity !== packet.granularity || !validEditedTopology(value.topology)) return false;
  if (!hasExactKeys(value.vocabulary, {json.dumps(sorted(VOCABULARY_KEYS))}) || !Array.isArray(value.coverage_gaps) || !Array.isArray(value.new_operators) || !Array.isArray(value.alternative_plans)) return false;
  if (!value.coverage_gaps.every(gap => hasExactKeys(gap, {json.dumps(sorted(COVERAGE_GAP_KEYS))}))) return false;
  return value.alternative_plans.every(plan => hasExactKeys(plan, {json.dumps(sorted(ALTERNATIVE_KEYS))}) && validEditedTopology(plan.topology));
}}

function renderGraph(topology, heading) {{
  const section = document.createElement('section'); addText(section, 'h3', heading);
  const holder = document.createElement('div'); holder.className = 'graph'; section.appendChild(holder);
  const nodes = topology && Array.isArray(topology.nodes) ? topology.nodes : [];
  if (!nodes.length) return section;
  const byId = new Map(nodes.map(node => [String(node.id), node]));
  const levels = new Map([...byId.keys()].map(id => [id, 0]));
  for (let pass = 0; pass < nodes.length; pass += 1) {{
    for (const [id, node] of byId) {{
      const deps = node.depends_on.map(String);
      const next = deps.length ? 1 + Math.max(...deps.map(dep => levels.get(dep) || 0)) : 0;
      if (next > levels.get(id) && next < nodes.length) levels.set(id, next);
    }}
  }}
  const groups = new Map();
  for (const id of byId.keys()) {{ const level = levels.get(id); if (!groups.has(level)) groups.set(level, []); groups.get(level).push(id); }}
  const positions = new Map();
  for (const [level, ids] of [...groups.entries()].sort((a, b) => a[0] - b[0])) {{
    ids.sort().forEach((id, index) => positions.set(id, {{x: 30 + level * 230, y: 25 + index * 100}}));
  }}
  const width = Math.max(350, 100 + (Math.max(...levels.values()) + 1) * 230);
  const height = Math.max(130, 80 + Math.max(...[...groups.values()].map(ids => ids.length)) * 100);
  const ns = 'http://www.w3.org/2000/svg'; const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', width); svg.setAttribute('height', height); svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', heading);
  for (const [id, node] of byId) {{
    const target = positions.get(id);
    for (const dependency of node.depends_on.map(String)) {{
      const source = positions.get(dependency); const line = document.createElementNS(ns, 'line');
      line.setAttribute('x1', source.x + 165); line.setAttribute('y1', source.y + 28); line.setAttribute('x2', target.x); line.setAttribute('y2', target.y + 28); line.setAttribute('stroke', '#718096'); line.setAttribute('stroke-width', '2'); svg.appendChild(line);
    }}
  }}
  for (const [id, node] of byId) {{
    const point = positions.get(id); const rect = document.createElementNS(ns, 'rect');
    rect.setAttribute('x', point.x); rect.setAttribute('y', point.y); rect.setAttribute('width', '165'); rect.setAttribute('height', '58'); rect.setAttribute('rx', '7'); rect.setAttribute('fill', '#edf2f7'); rect.setAttribute('stroke', '#4a5568'); svg.appendChild(rect);
    const op = document.createElementNS(ns, 'text'); op.setAttribute('x', point.x + 82); op.setAttribute('y', point.y + 22); op.setAttribute('text-anchor', 'middle'); op.setAttribute('font-size', '12'); op.setAttribute('fill', '#1a202c'); op.textContent = node.operator; svg.appendChild(op);
    const idText = document.createElementNS(ns, 'text'); idText.setAttribute('x', point.x + 82); idText.setAttribute('y', point.y + 42); idText.setAttribute('text-anchor', 'middle'); idText.setAttribute('font-size', '10'); idText.setAttribute('fill', '#1a202c'); idText.textContent = id; svg.appendChild(idText);
  }}
  holder.appendChild(svg); return section;
}}

packet.items.forEach((item, index) => {{
  const card = document.createElement('article'); card.className = 'card';
  addText(card, 'h2', `${{index + 1}}. ${{item.question_id}}`);
  addText(card, 'p', item.operator_view.question);
  const environment = item.operator_view.environment;
  addText(card, 'h3', '표 schema / capability');
  addText(card, 'p', `${{environment.title}}${{environment.section_title ? ' — ' + environment.section_title : ''}}`);
  const table = document.createElement('table'); table.className = 'schema';
  const head = document.createElement('thead'); const headRow = document.createElement('tr');
  ['index', 'column', 'linked-document capability'].forEach(value => addText(headRow, 'th', value)); head.appendChild(headRow); table.appendChild(head);
  const body = document.createElement('tbody'); environment.columns.forEach(column => {{ const row = document.createElement('tr'); addText(row, 'td', column.index); addText(row, 'td', column.label); addText(row, 'td', column.entity_link_capability); body.appendChild(row); }}); table.appendChild(body); card.appendChild(table);
  const capability = document.createElement('pre'); capability.textContent = JSON.stringify(environment.capabilities, null, 2); card.appendChild(capability);

  const representation = item.candidate_representation;
  card.appendChild(renderGraph(representation.topology, '후보 graph'));
  const graphJson = document.createElement('pre'); graphJson.textContent = JSON.stringify(representation.topology, null, 2); card.appendChild(graphJson);
  addText(card, 'h3', '측정값과 근거'); const metrics = document.createElement('dl'); metrics.className = 'metrics';
  const metricValues = [
    ['coverage', `${{representation.coverage_status}} — ${{representation.coverage_rationale}}`],
    ['coverage gaps', JSON.stringify(representation.coverage_gaps)],
    ['new operator', `${{representation.requires_new_operator}} / ${{JSON.stringify(representation.new_operators)}} — ${{representation.new_operator_rationale}}`],
    ['ambiguity', `${{representation.ambiguity_present}} — ${{representation.ambiguity_rationale}}`],
    ['hidden reasoning', `${{representation.hides_reasoning}} — ${{representation.hidden_reasoning_rationale}}`],
    ['excessive fragmentation', `${{representation.excessive_fragmentation}} — ${{representation.fragmentation_rationale}}`],
  ];
  metricValues.forEach(([term, description]) => {{ addText(metrics, 'dt', term); addText(metrics, 'dd', description); }}); card.appendChild(metrics);
  addText(card, 'h3', '조건부 대안 계획');
  if (!representation.alternative_plans.length) addText(card, 'p', '기록된 대안 없음');
  representation.alternative_plans.forEach(alternative => {{ addText(card, 'h4', `${{alternative.plan_id}} — ${{alternative.condition}}`); addText(card, 'p', alternative.rationale); card.appendChild(renderGraph(alternative.topology, `대안 ${{alternative.plan_id}} graph`)); }});
  addText(card, 'p', `검토 대상 SHA-256: ${{item.reviewed_representation_sha256}}`);

  const decisionLabel = document.createElement('label'); decisionLabel.textContent = '판정';
  const decision = document.createElement('select');
  ['unreviewed', 'accept', 'accept_with_edits', 'reject', 'abstain'].forEach(value => {{ const option = document.createElement('option'); option.value = value; option.textContent = value; decision.appendChild(option); }});
  decisionLabel.appendChild(decision); card.appendChild(decisionLabel);
  const semanticValidity = addReviewSelect(card, '의미 계획 타당성', ['valid', 'invalid', 'uncertain']);
  const coverageAssessment = addReviewSelect(card, '어휘 coverage 판정', ['covered', 'not_covered', 'uncertain']);
  const ambiguityAssessment = addReviewSelect(card, '질문 모호성 판정', ['true', 'false', 'uncertain']);
  const hiddenAssessment = addReviewSelect(card, '추론 은닉 판정', ['true', 'false', 'uncertain']);
  const fragmentationAssessment = addReviewSelect(card, '과도한 파편화 판정', ['true', 'false', 'uncertain']);
  decision.addEventListener('change', () => {{
    if (decision.value === 'accept') {{
      semanticValidity.value = 'valid'; coverageAssessment.value = representation.coverage_status;
      ambiguityAssessment.value = String(representation.ambiguity_present);
      hiddenAssessment.value = String(representation.hides_reasoning);
      fragmentationAssessment.value = String(representation.excessive_fragmentation);
    }} else if (decision.value === 'reject') {{
      semanticValidity.value = 'invalid';
    }} else if (decision.value === 'abstain') {{
      semanticValidity.value = 'uncertain'; coverageAssessment.value = 'uncertain';
      ambiguityAssessment.value = 'uncertain'; hiddenAssessment.value = 'uncertain';
      fragmentationAssessment.value = 'uncertain';
    }}
  }});
  const editLabel = document.createElement('label'); editLabel.textContent = '수정 representation JSON (accept_with_edits일 때 필수)';
  const edit = document.createElement('textarea'); edit.placeholder = '정답/row/cell/document/grounding을 입력하지 마세요.'; editLabel.appendChild(edit); card.appendChild(editLabel);
  const notesLabel = document.createElement('label'); notesLabel.textContent = '검토 메모 (선택)'; const notes = document.createElement('textarea'); notesLabel.appendChild(notes); card.appendChild(notesLabel);
  controls.push({{item, decision, semanticValidity, coverageAssessment, ambiguityAssessment, hiddenAssessment, fragmentationAssessment, edit, notes}}); root.appendChild(card);
}});

document.getElementById('download').addEventListener('click', async () => {{
  const reviewerIdInput = document.getElementById('reviewer-id');
  const reviewerId = reviewerIdInput.value.trim();
  if (!reviewerIdInput.checkValidity() || reviewerId !== reviewerIdInput.value) {{ window.alert('이름이나 이메일이 아닌 3–128자의 안정된 익명 ID를 입력하세요.'); return; }}
  if (controls.some(control => [control.decision, control.semanticValidity, control.coverageAssessment, control.ambiguityAssessment, control.hiddenAssessment, control.fragmentationAssessment].some(select => select.value === 'unreviewed'))) {{ window.alert('모든 항목과 평가 차원의 판정을 완료하세요.'); return; }}
  const completedAt = new Date().toISOString(); const reviews = [];
  for (const control of controls) {{
    const decision = control.decision.value; let edit = null; let correctedHash;
    if (decision === 'accept_with_edits') {{
      try {{ edit = JSON.parse(control.edit.value); }} catch (error) {{ window.alert(`${{control.item.question_id}}: 수정본은 유효한 JSON이어야 합니다.`); return; }}
      if (!validCorrectedRepresentation(edit) || forbiddenEditKey(edit)) {{ window.alert(`${{control.item.question_id}}: 수정본은 같은 granularity의 exact leakage-safe representation 객체여야 합니다.`); return; }}
      correctedHash = await sha256Canonical(edit);
    }} else if (control.edit.value.trim()) {{
      window.alert(`${{control.item.question_id}}: accept_with_edits가 아니면 수정 representation을 비우세요.`); return;
    }}
    const assessment = {{
      semantic_validity: control.semanticValidity.value,
      coverage_status: control.coverageAssessment.value,
      ambiguity_present: triState(control.ambiguityAssessment.value),
      hides_reasoning: triState(control.hiddenAssessment.value),
      excessive_fragmentation: triState(control.fragmentationAssessment.value),
    }};
    if (decision === 'accept' && !sameAssessment(assessment, expectedAssessment(control.item.candidate_representation))) {{ window.alert(`${{control.item.question_id}}: accept는 원 표현의 평가 차원을 그대로 확인해야 합니다.`); return; }}
    if (decision === 'accept_with_edits' && !sameAssessment(assessment, expectedAssessment(edit))) {{ window.alert(`${{control.item.question_id}}: 수정 수락의 평가 차원은 수정 representation과 일치해야 합니다.`); return; }}
    if (decision === 'reject' && assessment.semantic_validity !== 'invalid') {{ window.alert(`${{control.item.question_id}}: reject는 의미 타당성을 invalid로 표시해야 합니다.`); return; }}
    if (decision === 'abstain' && Object.values(assessment).some(value => value !== 'uncertain')) {{ window.alert(`${{control.item.question_id}}: abstain은 모든 평가 차원을 uncertain으로 표시해야 합니다.`); return; }}
    const annotation = {{
      schema_version: 'operator_representation_review_v0_1',
      question_id: control.item.question_id,
      granularity: packet.granularity,
      reviewed_view: 'operator_granularity_representation',
      reviewed_representation_sha256: control.item.reviewed_representation_sha256,
      review_packet_payload_sha256: packetPayloadSha256,
      completed_at: completedAt,
      decision,
      assessment,
      edit,
      notes: control.notes.value.trim() || null,
      ...(correctedHash ? {{corrected_representation_sha256: correctedHash}} : {{}}),
    }};
    reviews.push({{reviewer_id: reviewerId, annotation, annotation_sha256: await sha256Canonical(annotation)}});
  }}
  const blob = new Blob([JSON.stringify(reviews, null, 2) + '\\n'], {{type: 'application/json'}});
  const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `operator_representation_reviews_${{packet.granularity}}.json`; link.click(); URL.revokeObjectURL(link.href);
}});
</script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    inputs = {
        "questions": args.questions,
        "input_views": args.input_views,
        "input_views_manifest": args.input_views_manifest,
        "representations": args.representations,
        "validation_checks": args.validation_checks,
    }
    outputs = {"output": args.output, "manifest_output": args.manifest_output}
    collisions = output_path_collision_errors(inputs, outputs)
    collisions.extend(historical_output_collision_errors(outputs, project_root))
    collisions.extend(historical_tree_collision_errors(outputs, project_root))
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    if args.output.suffix.lower() not in {".html", ".htm"}:
        print("--output must be an HTML path", file=sys.stderr)
        return 2
    if args.manifest_output.suffix.lower() != ".json":
        print("--manifest-output must be a JSON path", file=sys.stderr)
        return 2

    try:
        implementation_commit = git_tracked_commit_identity(
            project_root,
            [
                Path(__file__),
                Path(__file__).with_name("_common.py"),
                Path(__file__).with_name("validate_annotation.py"),
                Path(__file__).with_name("compare_operator_granularity.py"),
                Path(__file__).with_name("build_granularity_representations.py"),
                Path(__file__).with_name("validate_operator_granularity.py"),
            ],
        )
        live_hashes = {label: sha256_file(path) for label, path in inputs.items()}
        questions = list(iter_json_records(args.questions))
        views = list(iter_json_records(args.input_views))
        representations = list(iter_json_records(args.representations))
        checks = list(iter_json_records(args.validation_checks))
        view_manifest = read_json(args.input_views_manifest)
        question_ids = validate_questions(questions)
        operator_views = validate_input_views(views, questions, question_ids)
        import compare_operator_granularity as comparator

        manifest_errors, split_manifest_sha256 = comparator.validate_view_manifest(
            view_manifest,
            args.questions,
            questions,
            args.input_views,
            views,
            project_root,
        )
        if manifest_errors or split_manifest_sha256 is None:
            raise ValueError(
                "input-view manifest integrity failed: " + "; ".join(manifest_errors)
            )
        validate_representation_records(
            representations,
            questions,
            views,
            question_ids,
            live_hashes["input_views"],
            live_hashes["input_views_manifest"],
            project_root,
        )
        vocabulary_paths = {
            granularity: project_root
            / f"data_construction/operator_design/operator_vocabulary_{granularity}_v0_1.json"
            for granularity in GRANULARITIES
        }
        vocabulary_sets = {
            granularity: vocabulary_operators(path, granularity)
            for granularity, path in vocabulary_paths.items()
        }
        vocabulary_references = {
            granularity: {
                "vocabulary_version": f"operator_vocabulary_{granularity}_v0_1",
                "repository_relative_path": (
                    f"data_construction/operator_design/operator_vocabulary_{granularity}_v0_1.json"
                ),
                "sha256": sha256_file(path),
            }
            for granularity, path in vocabulary_paths.items()
        }
        representation_errors = comparator.validate_representation_records(
            representations,
            questions,
            views,
            args.input_views,
            args.input_views_manifest,
            vocabulary_sets,
            vocabulary_references,
            project_root,
        )
        if representation_errors:
            raise ValueError(
                "representation integrity failed: " + "; ".join(representation_errors)
            )
        selected_passes = validate_checks(
            checks,
            representations,
            question_ids,
            args.granularity,
            live_hashes,
            split_manifest_sha256,
            project_root,
        )
        # Fail if any input changed while the packet contract was being checked.
        if any(sha256_file(path) != live_hashes[label] for label, path in inputs.items()):
            raise ValueError("an input artifact changed during packet construction")
        payload = build_payload(representations, operator_views, args.granularity)
        payload_sha256 = canonical_json_sha256(payload)
        rendered = render_html(payload, payload_sha256)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot build granularity review packet: {exc}", file=sys.stderr)
        return 2

    packet_payload = rendered.encode("utf-8")
    packet_sha256 = sha256_bytes(packet_payload)
    manifest = {
        "schema_version": "operator_granularity_review_packet_manifest_v0_1",
        "builder_version": BUILDER_VERSION,
        "granularity": args.granularity,
        "question_count": EXPECTED_QUESTION_COUNT,
        "review_status": "packet_created_no_human_reviews",
        "human_reviews_created_by_builder": False,
        "packet_payload": {
            "canonicalization": CANONICALIZATION,
            "sha256": payload_sha256,
            "reviewed_view": "operator_granularity_representation",
            "contains_only_operator_view_and_candidate_representation": True,
        },
        "packet_artifact": {
            "repository_relative_path": portable_path(args.output, project_root),
            "sha256": packet_sha256,
        },
        "inputs": {
            label: {
                "repository_relative_path": portable_path(path, project_root),
                "sha256": live_hashes[label],
            }
            for label, path in inputs.items()
        },
        "validation": {
            "validation_record_version": VALIDATION_RECORD_VERSION,
            "validator_version": VALIDATOR_VERSION,
            "validation_mode": VALIDATION_MODE,
            "exact_question_id_order_verified": True,
            "selected_granularity_pass_check_count": selected_passes,
            "live_artifact_hashes_verified": True,
            "leakage_projection_verified": True,
        },
        "review_record_contract": {
            "schema_version": "operator_representation_review_v0_1",
            "canonicalization": CANONICALIZATION,
            "decisions": ["accept", "accept_with_edits", "reject", "abstain"],
            "assessment_fields": [
                "ambiguity_present",
                "coverage_status",
                "excessive_fragmentation",
                "hides_reasoning",
                "semantic_validity",
            ],
            "reviewer_identity": "stable_pseudonymous_id",
            "reviewer_authentication": "procedural_not_machine_verifiable",
            "reviews_included": 0,
        },
        "provenance": {
            "code_commit": implementation_commit,
            "builder_does_not_claim_human_review": True,
        },
    }
    manifest_payload = json_file_bytes(manifest)
    try:
        write_output_batch(
            {
                "output": (args.output, packet_payload),
                "manifest_output": (args.manifest_output, manifest_payload),
            },
            overwrite=args.overwrite,
        )
    except (OSError, ValueError) as exc:
        print(f"cannot write granularity review packet: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "granularity": args.granularity,
                "questions": EXPECTED_QUESTION_COUNT,
                "pass_checks": selected_passes,
                "packet_payload_sha256": payload_sha256,
                "human_reviews_created": 0,
                "output": args.output.as_posix(),
                "manifest_output": args.manifest_output.as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
