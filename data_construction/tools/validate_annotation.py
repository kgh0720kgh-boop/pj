#!/usr/bin/env python3
"""Validate hierarchical annotations and write auditable per-record checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

from _common import (
    canonical_json_sha256,
    canonical_string_set_sha256,
    first_string,
    git_commit_identity,
    historical_output_collision_errors,
    iter_json_records,
    output_path_collision_errors,
    read_json,
    sha256_file,
    write_jsonl,
)
from validate_ir_v0_2_reference import validate_ir_v0_2_reference


VALIDATOR_VERSION = "annotation_validator_v0_1"
IR_V0_2_SCHEMA_REPOSITORY_PATH = (
    "historical/ir_v0_2/ir/execution_graph.schema.json"
)
IR_V0_2_SCHEMA_SHA256 = (
    "55ccc7721cccba570a94cea94452eccbb6409a45606adf2d79764df783bbbb63"
)
IR_V0_2_REQUIRED_VALIDATION_CHECKS = (
    "parse",
    "json_schema",
    "operator_registry",
    "type_contract",
    "dependency_references",
    "acyclicity",
    "source_reachability",
)
LOWERCASE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EARLY_LAYER_FORBIDDEN_KEYS = {
    "answer",
    "answer_node",
    "answer_text",
    "column_index",
    "column_label",
    "document_id",
    "document_ids",
    "document_required",
    "entity_id",
    "execution_graph",
    "gold_answer",
    "gold_span",
    "grounding",
    "join_key",
    "link_id",
    "locator",
    "old_manual_graph",
    "operator",
    "operator_arguments",
    "oracle_document_id",
    "row_index",
    "row_predicate",
    "schema_id",
    "table_id",
    "tool",
    "weak_answer_node",
}
TOPOLOGY_FORBIDDEN_KEYS = {
    "arguments",
    "column_index",
    "column_label",
    "document_id",
    "gold_answer",
    "literal",
    "row_predicate",
    "schema_id",
    "table_id",
    "join_key",
}
PROHIBITED_GOLD_STATUSES = {"gold", "gold_program", "human_gold", "llm_gold"}
ABSTRACT_SEMANTIC_FUNCTIONS = {
    "SELECT_CANDIDATES",
    "RESTRICT_CANDIDATES",
    "RESOLVE_RELATION",
    "ACQUIRE_ATTRIBUTE",
    "PARSE_SEMANTIC_VALUE",
    "NORMALIZE_SEMANTIC_VALUE",
    "COMPARE_VALUES",
    "AGGREGATE_VALUES",
    "COMPUTE_VALUE",
    "APPLY_ORDINAL",
    "ARG_SELECT",
    "MAP_BACK_TO_ANSWER",
    "RETURN_ANSWER",
    "OTHER",
}

# Prediction views are part of the leakage boundary, not free-form metadata.  A
# contract may expose descendants of an allowed root, but it must explicitly
# prohibit its own target and every later supervised layer that could reveal it.
PREDICTION_VIEW_POLICIES: dict[str, dict[str, set[str]]] = {
    "question_to_semantics": {
        "allowed_inputs": {"/question", "/question_language"},
        "required_inputs": {"/question"},
        "allowed_targets": {"/semantic_skeleton", "/information_obligations"},
        "required_targets": {"/semantic_skeleton", "/information_obligations"},
        "required_prohibited": {
            "/semantic_skeleton",
            "/information_obligations",
            "/abstract_topology",
            "/operator_topology",
            "/grounding",
            "/execution_graph",
            "/execution_reference",
        },
    },
    "semantics_to_operator_topology": {
        "allowed_inputs": {
            "/question",
            "/question_language",
            "/table_id",
            "/semantic_skeleton",
            "/information_obligations",
            "/abstract_topology",
        },
        "required_inputs": {"/semantic_skeleton", "/information_obligations"},
        "allowed_targets": {"/abstract_topology", "/operator_topology"},
        "required_targets": {"/operator_topology"},
        "required_prohibited": {
            "/operator_topology",
            "/grounding",
            "/execution_graph",
            "/execution_reference",
        },
    },
    "operator_topology_to_grounding": {
        "allowed_inputs": {
            "/question",
            "/question_language",
            "/table_id",
            "/semantic_skeleton",
            "/information_obligations",
            "/abstract_topology",
            "/operator_topology",
        },
        "required_inputs": {"/operator_topology"},
        "allowed_targets": {"/grounding"},
        "required_targets": {"/grounding"},
        "required_prohibited": {"/grounding", "/execution_graph", "/execution_reference"},
    },
    "question_environment_to_execution_graph": {
        "allowed_inputs": {"/question", "/question_language", "/table_id"},
        "required_inputs": {"/question", "/table_id"},
        "allowed_targets": {"/execution_graph"},
        "required_targets": {"/execution_graph"},
        "required_prohibited": {
            "/semantic_skeleton",
            "/information_obligations",
            "/abstract_topology",
            "/operator_topology",
            "/grounding",
            "/execution_graph",
            "/execution_reference",
        },
    },
    "execution_evaluation": {
        "allowed_inputs": {
            "/question",
            "/question_id",
            "/execution_graph",
            "/execution_reference/expected_final_answer",
            "/execution_reference/expected_intermediates",
        },
        "required_inputs": {"/execution_graph"},
        "allowed_targets": {
            "/execution_reference/execution_trials",
            "/bundle_validation",
        },
        "required_targets": set(),
        "required_prohibited": {"/execution_reference/execution_trials"},
    },
}

STANDARD_LEAKAGE_BOUNDARIES = {
    "question_to_semantics",
    "semantics_to_abstract_topology",
    "abstract_to_operator_topology",
    "operator_topology_to_grounding",
    "grounding_to_execution_graph",
}

# A passed boundary audit must be tied to the exact materialized prediction
# view it inspected.  These are deep-key denylists for the output/later layers
# that must not occur in that input artifact.  The separately validated
# prediction-view contracts remain the source of truth for JSON-pointer roots.
BOUNDARY_INPUT_FORBIDDEN_KEYS: dict[str, set[str]] = {
    "question_to_semantics": EARLY_LAYER_FORBIDDEN_KEYS
    | {
        "semantic_skeleton",
        "information_obligations",
        "abstract_topology",
        "operator_topology",
        "execution_reference",
    },
    "semantics_to_abstract_topology": EARLY_LAYER_FORBIDDEN_KEYS
    | {"abstract_topology", "operator_topology", "execution_reference"},
    "abstract_to_operator_topology": TOPOLOGY_FORBIDDEN_KEYS
    | {"operator_topology", "grounding", "execution_graph", "execution_reference"},
    "operator_topology_to_grounding": TOPOLOGY_FORBIDDEN_KEYS
    | {"grounding", "execution_graph", "execution_reference"},
    "grounding_to_execution_graph": {
        "answer",
        "answer_node",
        "answer_text",
        "gold_answer",
        "gold_span",
        "execution_graph",
        "execution_reference",
        "old_manual_graph",
        "oracle_document_id",
        "weak_answer_node",
    },
    "locked_eval_isolation": {
        "answer",
        "answer_node",
        "answer_text",
        "gold_answer",
        "gold_span",
        "old_manual_graph",
        "oracle_document_id",
        "weak_answer_node",
    },
}

BOUNDARY_INPUT_VIEW_POLICIES: dict[str, dict[str, set[str]]] = {
    "question_to_semantics": {
        "required": {"question_id", "question"},
        "allowed": {"question_id", "question", "question_language"},
    },
    "semantics_to_abstract_topology": {
        "required": {
            "question_id",
            "question",
            "semantic_skeleton",
            "information_obligations",
        },
        "allowed": {
            "question_id",
            "question",
            "question_language",
            "semantic_skeleton",
            "information_obligations",
        },
    },
    "abstract_to_operator_topology": {
        "required": {
            "question_id",
            "question",
            "semantic_skeleton",
            "information_obligations",
            "abstract_topology",
        },
        "allowed": {
            "question_id",
            "question",
            "question_language",
            "table_id",
            "semantic_skeleton",
            "information_obligations",
            "abstract_topology",
        },
    },
    "operator_topology_to_grounding": {
        "required": {
            "question_id",
            "question",
            "operator_topology",
        },
        "allowed": {
            "question_id",
            "question",
            "question_language",
            "table_id",
            "semantic_skeleton",
            "information_obligations",
            "abstract_topology",
            "operator_topology",
        },
    },
    "grounding_to_execution_graph": {
        "required": {
            "question_id",
            "question",
            "operator_topology",
            "grounding",
        },
        "allowed": {
            "question_id",
            "question",
            "question_language",
            "table_id",
            "semantic_skeleton",
            "information_obligations",
            "abstract_topology",
            "operator_topology",
            "grounding",
        },
    },
}

RFC3339_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*$")


def is_rfc3339_datetime(value: Any) -> bool:
    if not isinstance(value, str) or RFC3339_DATETIME.fullmatch(value) is None:
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def is_absolute_uri(value: Any) -> bool:
    if not isinstance(value, str) or any(character.isspace() for character in value):
        return False
    parsed = urlsplit(value)
    if URI_SCHEME.fullmatch(parsed.scheme) is None:
        return False
    if parsed.scheme.lower() in {"http", "https"} and not parsed.netloc:
        return False
    return bool(parsed.netloc or parsed.path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("data_construction/schemas/hierarchical_annotation_v0_1.json"),
    )
    parser.add_argument(
        "--operator-vocabulary",
        type=Path,
        default=Path("data_construction/operator_design/operator_vocabulary_medium_v0_1.json"),
    )
    parser.add_argument(
        "--checks-output",
        type=Path,
        default=Path("data_construction/pilot/deterministic_checks.jsonl"),
    )
    parser.add_argument(
        "--structural-only",
        action="store_true",
        help="Run cross-field checks without the jsonschema dependency",
    )
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--allow-empty", action="store_true", help="Diagnostic-only: allow an empty input")
    return parser.parse_args()


def walk_keys(value: Any, prefix: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}"
            yield path, key
            yield from walk_keys(child, path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_keys(child, f"{prefix}[{index}]")


def canonical_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.casefold())


def canonical_key_variants(key: str) -> set[str]:
    canonical = canonical_key(key)
    variants = {canonical}
    if canonical.endswith("s") and len(canonical) > 1:
        variants.add(canonical[:-1])
    if canonical.endswith("ies") and len(canonical) > 3:
        variants.add(canonical[:-3] + "y")
    return variants


def pointer_is_within(path: Any, roots: set[str]) -> bool:
    """Return whether a JSON pointer is a root itself or one of its descendants."""
    if not isinstance(path, str) or not path.startswith("/"):
        return False
    return any(path == root or path.startswith(root + "/") for root in roots)


def pointers_overlap(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def vocabulary_names(value: Any) -> set[str]:
    if not isinstance(value, dict):
        return set()
    operators = value.get("operators")
    if not isinstance(operators, list) and isinstance(value.get("vocabulary"), dict):
        operators = value["vocabulary"].get("operators")
    names: set[str] = set()
    if isinstance(operators, list):
        for item in operators:
            if isinstance(item, str):
                names.add(item)
            elif isinstance(item, dict):
                name = first_string(item, ("name", "operator", "id"))
                if name:
                    names.add(name)
    return names


def vocabulary_definitions(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    operators = value.get("operators")
    if not isinstance(operators, list) and isinstance(value.get("vocabulary"), dict):
        operators = value["vocabulary"].get("operators")
    result: dict[str, dict[str, Any]] = {}
    if isinstance(operators, list):
        for item in operators:
            if isinstance(item, str):
                result[item] = {"name": item, "argument_slots": []}
            elif isinstance(item, dict):
                name = first_string(item, ("name", "operator", "id"))
                if name:
                    result[name] = item
    return result


def port_definitions(definition: dict[str, Any], direction: str) -> dict[str, dict[str, Any]]:
    raw_ports = definition.get(f"{direction}_ports", [])
    if not isinstance(raw_ports, list):
        return {}
    return {
        port["name"]: port
        for port in raw_ports
        if isinstance(port, dict) and isinstance(port.get("name"), str)
    }


def compatible_types(source_type: Any, expected_type: Any) -> bool:
    """Return true when two candidate union-type contracts overlap."""
    if not isinstance(source_type, str) or not isinstance(expected_type, str):
        return False
    source_members = {item.strip() for item in source_type.split("|") if item.strip()}
    expected_members = {item.strip() for item in expected_type.split("|") if item.strip()}
    return bool(source_members & expected_members)


def compatible_cardinalities(source: Any, expected: Any, expected_type: Any) -> bool:
    if source not in {"one", "optional", "one_or_more", "zero_or_more"}:
        return False
    if expected not in {"one", "optional", "one_or_more", "zero_or_more"}:
        return False
    if expected in {"optional", "zero_or_more"}:
        return True
    type_members = {
        item.strip() for item in expected_type.split("|")
    } if isinstance(expected_type, str) else set()
    collection_contract = any(
        item.endswith("Set") or item in {"Table", "GroupedValues", "ComparedValueSet"}
        for item in type_members
    )
    if expected == "one":
        return source == "one" or collection_contract
    return source in {"one", "one_or_more"} or collection_contract


def walk_objects(value: Any, prefix: str = "$") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield prefix, value
        for key, child in value.items():
            yield from walk_objects(child, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_objects(child, f"{prefix}[{index}]")


def source_span_errors(record: dict[str, Any], question: str | None) -> list[str]:
    errors: list[str] = []
    for path, value in walk_objects(record):
        if not {"text", "start_char", "end_char"}.issubset(value):
            continue
        text = value.get("text")
        start = value.get("start_char")
        end = value.get("end_char")
        if not isinstance(text, str) or type(start) is not int or type(end) is not int:
            errors.append(f"source_span:{path}: text/start_char/end_char have invalid types")
            continue
        if question is None:
            errors.append(f"source_span:{path}: cannot verify span without question text")
        elif start < 0 or end <= start or end > len(question):
            errors.append(f"source_span:{path}: offsets [{start}, {end}) are outside the question")
        elif question[start:end] != text:
            errors.append(f"source_span:{path}: text does not match the question substring")
    return errors


def artifact_reference_errors(record: dict[str, Any], project_root: Path) -> list[str]:
    errors: list[str] = []
    root = project_root.resolve()
    for path, value in walk_objects(record):
        if not {"artifact_id", "artifact_type"}.issubset(value):
            continue
        relative = value.get("repository_relative_path")
        if relative is None:
            continue
        if not isinstance(relative, str):
            errors.append(f"artifact:{path}: repository_relative_path must be a string")
            continue
        target = (root / relative).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(f"artifact:{path}: repository_relative_path escapes the project root")
            continue
        if not target.is_file():
            errors.append(f"artifact:{path}: referenced repository file does not exist: {relative!r}")
            continue
        expected_sha = value.get("sha256")
        if isinstance(expected_sha, str) and sha256_file(target).lower() != expected_sha.lower():
            errors.append(f"artifact:{path}: SHA-256 mismatch for {relative!r}")
    return errors


def concrete_binding_errors(binding: Any, label: str) -> list[str]:
    if not isinstance(binding, dict):
        return []
    if binding.get("binding_type") != "row_predicate":
        return []
    comparator = binding.get("comparator")
    values = binding.get("values")
    if not isinstance(values, list):
        return [f"{label}: row_predicate values must be an array"]
    errors: list[str] = []
    if comparator in {"is_null", "is_not_null"} and values:
        errors.append(f"{label}: comparator {comparator!r} requires zero literal values")
    elif comparator == "in" and not values:
        errors.append(f"{label}: comparator 'in' requires at least one literal value")
    elif comparator not in {"is_null", "is_not_null", "in"} and len(values) != 1:
        errors.append(f"{label}: comparator {comparator!r} requires exactly one literal value")
    value_types = {
        item.get("value_type") for item in values if isinstance(item, dict) and isinstance(item.get("value_type"), str)
    }
    if comparator in {"contains", "starts_with", "ends_with", "regex"} and value_types - {"string"}:
        errors.append(f"{label}: comparator {comparator!r} requires string literal values")
    if comparator in {"lt", "lte", "gt", "gte"} and value_types - {
        "number",
        "integer",
        "date",
        "datetime",
    }:
        errors.append(f"{label}: ordered comparison has a non-orderable literal type")
    return errors


def load_repository_artifact(
    artifact: Any,
    project_root: Path,
    label: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(artifact, dict):
        return None, [f"{label}: artifact reference is required"]
    relative = artifact.get("repository_relative_path")
    expected_sha = artifact.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected_sha, str):
        return None, [f"{label}: repository_relative_path and sha256 are required"]
    root = project_root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None, [f"{label}: artifact path escapes project root"]
    if not path.is_file():
        return None, [f"{label}: artifact file is missing"]
    if sha256_file(path).lower() != expected_sha.lower():
        return None, [f"{label}: artifact SHA-256 mismatch"]
    try:
        value = read_json(path)
    except (OSError, ValueError) as exc:
        return None, [f"{label}: artifact is not readable JSON: {exc}"]
    if not isinstance(value, dict):
        errors.append(f"{label}: artifact JSON must be an object")
        return None, errors
    return value, errors


def leakage_audit_artifact_errors(
    boundary: str,
    audit: dict[str, Any],
    project_root: Path,
    record: dict[str, Any] | None = None,
) -> list[str]:
    """Live-check a claimed passed audit and the exact input view it covers."""

    label = f"leakage_controls.boundary_audits[{boundary!r}]"
    errors: list[str] = []
    input_reference = audit.get("input_view_artifact")
    result_reference = audit.get("audit_result_artifact")
    if isinstance(input_reference, dict) and input_reference.get("artifact_type") != "prediction_view":
        errors.append(f"{label}.input_view_artifact: artifact_type must be 'prediction_view'")
    if isinstance(result_reference, dict) and result_reference.get("artifact_type") != "leakage_boundary_audit":
        errors.append(
            f"{label}.audit_result_artifact: artifact_type must be 'leakage_boundary_audit'"
        )
    input_view, input_errors = load_repository_artifact(
        input_reference,
        project_root,
        f"{label}.input_view_artifact",
    )
    audit_result, result_errors = load_repository_artifact(
        result_reference,
        project_root,
        f"{label}.audit_result_artifact",
    )
    errors.extend(input_errors)
    errors.extend(result_errors)
    if input_view is not None:
        check_forbidden_keys(
            input_view,
            BOUNDARY_INPUT_FORBIDDEN_KEYS.get(boundary, set()),
            f"boundary_input.{boundary}",
            errors,
        )
        view_policy = BOUNDARY_INPUT_VIEW_POLICIES.get(boundary)
        if view_policy is not None:
            if not isinstance(record, dict):
                errors.append(f"{label}.input_view_artifact: annotation record is required")
            else:
                input_keys = set(input_view)
                missing_keys = view_policy["required"] - input_keys
                unexpected_keys = input_keys - view_policy["allowed"]
                if missing_keys:
                    errors.append(
                        f"{label}.input_view_artifact: missing required projection keys "
                        f"{sorted(missing_keys)!r}"
                    )
                if unexpected_keys:
                    errors.append(
                        f"{label}.input_view_artifact: unexpected projection keys "
                        f"{sorted(unexpected_keys)!r}"
                    )
                for key in sorted(input_keys & view_policy["allowed"]):
                    if key not in record or input_view.get(key) != record.get(key):
                        errors.append(
                            f"{label}.input_view_artifact: field {key!r} does not match the annotation"
                        )
    if boundary == "locked_eval_isolation":
        controls = record.get("locked_eval_controls") if isinstance(record, dict) else None
        if not isinstance(record, dict) or record.get("dataset_role") != "locked_eval":
            errors.append(
                f"{label}: only a locked_eval annotation may claim a passed isolation audit; "
                "other roles must use not_run"
            )
        split_reference = (
            controls.get("split_manifest_artifact") if isinstance(controls, dict) else None
        )
        split_manifest, split_errors = load_repository_artifact(
            split_reference,
            project_root,
            f"{label}.split_manifest_artifact",
        )
        errors.extend(split_errors)
        tuning_ids = input_view.get("question_ids") if isinstance(input_view, dict) else None
        if (
            not isinstance(input_view, dict)
            or input_view.get("schema_version")
            != "locked_eval_tuning_input_inventory_v0_1"
            or not isinstance(tuning_ids, list)
            or not all(isinstance(identifier, str) for identifier in tuning_ids)
            or len(tuning_ids) != len(set(tuning_ids))
        ):
            errors.append(
                f"{label}.input_view_artifact: locked isolation requires a unique string "
                "question_ids inventory"
            )
            tuning_ids = []
        locked_ids = (
            split_manifest.get("roles", {}).get("locked_eval")
            if isinstance(split_manifest, dict)
            and isinstance(split_manifest.get("roles"), dict)
            else None
        )
        if not isinstance(locked_ids, list) or not all(
            isinstance(identifier, str) for identifier in locked_ids
        ):
            errors.append(f"{label}.split_manifest_artifact: locked_eval role IDs are unavailable")
            locked_ids = []
        split_roles = (
            split_manifest.get("roles") if isinstance(split_manifest, dict) else None
        )
        allowed_tuning_ids = {
            identifier
            for role in ("annotation_schema_pilot", "annotation_train", "annotation_dev")
            for identifier in (
                split_roles.get(role, []) if isinstance(split_roles, dict) else []
            )
            if isinstance(identifier, str)
        }
        unknown_tuning_ids = set(tuning_ids) - allowed_tuning_ids - set(locked_ids)
        if unknown_tuning_ids:
            errors.append(
                f"{label}: tuning input contains IDs outside the declared non-locked roles "
                f"{sorted(unknown_tuning_ids)!r}"
            )
        overlap = set(tuning_ids) & set(locked_ids)
        if overlap:
            errors.append(
                f"{label}: tuning input contains locked-eval question IDs {sorted(overlap)!r}"
            )
        if audit_result is not None:
            expected_split_sha = (
                split_reference.get("sha256") if isinstance(split_reference, dict) else None
            )
            if audit_result.get("split_manifest_sha256") != expected_split_sha:
                errors.append(
                    f"{label}.audit_result_artifact: split-manifest SHA-256 does not match"
                )
            if audit_result.get("tuning_question_id_set_sha256") != canonical_string_set_sha256(
                tuning_ids
            ):
                errors.append(
                    f"{label}.audit_result_artifact: tuning question-ID set hash does not match"
                )
            if audit_result.get("locked_eval_overlap_count") != len(overlap):
                errors.append(
                    f"{label}.audit_result_artifact: locked_eval_overlap_count does not match live overlap"
                )
            if audit_result.get("locked_eval_overlap_count") != 0:
                errors.append(
                    f"{label}.audit_result_artifact: locked_eval_overlap_count must be zero"
                )
        if isinstance(record, dict) and record.get("dataset_role") == "locked_eval":
            if not isinstance(controls, dict):
                errors.append(f"{label}: locked_eval_controls are required")
            else:
                errors.extend(locked_eval_membership_errors(record, controls, project_root))
    if audit_result is not None:
        expected_input_sha = (
            input_reference.get("sha256") if isinstance(input_reference, dict) else None
        )
        if audit_result.get("schema_version") != "leakage_boundary_audit_v0_1":
            errors.append(f"{label}.audit_result_artifact: unsupported schema_version")
        if audit_result.get("boundary") != boundary:
            errors.append(f"{label}.audit_result_artifact: boundary does not match")
        if audit_result.get("status") != "passed":
            errors.append(f"{label}.audit_result_artifact: status must be 'passed'")
        if audit_result.get("checker_id") != audit.get("checker_id"):
            errors.append(f"{label}.audit_result_artifact: checker_id does not match")
        if audit_result.get("checked_at") != audit.get("checked_at"):
            errors.append(f"{label}.audit_result_artifact: checked_at does not match")
        if audit_result.get("input_view_sha256") != expected_input_sha:
            errors.append(f"{label}.audit_result_artifact: input-view SHA-256 does not match")
        if audit_result.get("violations") != []:
            errors.append(f"{label}.audit_result_artifact: passed result must have no violations")
    return errors


def locked_eval_membership_errors(
    record: dict[str, Any],
    controls: dict[str, Any],
    project_root: Path,
) -> list[str]:
    errors: list[str] = []
    question_id = first_string(record, ("question_id", "qid", "id"))
    split, split_errors = load_repository_artifact(
        controls.get("split_manifest_artifact"), project_root, "locked_eval.split_manifest_artifact"
    )
    history, history_errors = load_repository_artifact(
        controls.get("historical_exposure_manifest_artifact"),
        project_root,
        "locked_eval.historical_exposure_manifest_artifact",
    )
    errors.extend(split_errors)
    errors.extend(history_errors)
    safe_roles: dict[str, list[str]] = {}
    if split is not None:
        if split.get("schema_version") != "split_manifest_v0_1" or split.get("release_eligible") is not True:
            errors.append("locked_eval: split manifest is not a release-eligible v0.1 allocation")
        if split.get("combined_role_output_written") is not False:
            errors.append("locked_eval: split manifest does not prove isolated role outputs")
        roles = split.get("roles")
        if not isinstance(roles, dict):
            errors.append("locked_eval: split manifest roles are missing")
        else:
            expected_roles = {
                "annotation_schema_pilot",
                "annotation_train",
                "annotation_dev",
                "locked_eval",
            }
            if set(roles) != expected_roles:
                errors.append("locked_eval: split manifest role names are not the canonical four-role set")
            for role in sorted(expected_roles):
                raw_role_ids = roles.get(role)
                if (
                    not isinstance(raw_role_ids, list)
                    or not all(isinstance(identifier, str) for identifier in raw_role_ids)
                    or len(raw_role_ids) != len(set(raw_role_ids))
                ):
                    errors.append(
                        f"locked_eval: split role {role!r} must be a unique string-ID array"
                    )
                    safe_roles[role] = []
                else:
                    safe_roles[role] = raw_role_ids
            locked_ids = safe_roles.get("locked_eval", [])
            if question_id not in locked_ids:
                errors.append("locked_eval: question_id is not assigned to the locked_eval role")
            all_role_ids = [
                identifier
                for identifiers in safe_roles.values()
                for identifier in identifiers
            ]
            if len(all_role_ids) != len(set(all_role_ids)):
                errors.append("locked_eval: split manifest role IDs overlap")
        source = split.get("source")
        if not isinstance(source, dict) or source.get("verified_against_pinned_manifest") is not True:
            errors.append("locked_eval: split source is not verified against the pinned official manifest")
        historical_summary = split.get("historical_manifest")
        if not isinstance(historical_summary, dict) or historical_summary.get("release_contract_errors") != []:
            errors.append("locked_eval: split manifest did not pass the historical release contract")
        role_artifacts = split.get("role_artifacts")
        locked_artifact = role_artifacts.get("locked_eval") if isinstance(role_artifacts, dict) else None
        if not isinstance(locked_artifact, dict) or locked_artifact.get("tuning_allowed") is not False:
            errors.append("locked_eval: locked role artifact is absent or permits tuning")
        elif isinstance(roles, dict):
            locked_path_value = locked_artifact.get("path")
            if not isinstance(locked_path_value, str):
                errors.append("locked_eval: locked role artifact path is missing")
            else:
                root = project_root.resolve()
                locked_path = (root / locked_path_value).resolve()
                try:
                    locked_path.relative_to(root)
                except ValueError:
                    errors.append("locked_eval: locked role artifact path escapes project root")
                else:
                    if not locked_path.is_file():
                        errors.append("locked_eval: locked role artifact file is missing")
                    elif sha256_file(locked_path) != locked_artifact.get("sha256"):
                        errors.append("locked_eval: locked role artifact SHA-256 mismatch")
                    else:
                        locked_records = list(iter_json_records(locked_path))
                        locked_record_ids = [
                            first_string(item, ("question_id", "qid", "id")) for item in locked_records
                        ]
                        if (
                            locked_artifact.get("record_count") != len(locked_records)
                            or locked_record_ids != safe_roles.get("locked_eval", [])
                            or len(locked_record_ids) != len(set(locked_record_ids))
                        ):
                            errors.append("locked_eval: locked role artifact contents disagree with split roles/count")
                        if any(item.get("dataset_role") != "locked_eval" for item in locked_records):
                            errors.append("locked_eval: locked role artifact contains a non-locked dataset_role")
                        matched_role_record = next(
                            (
                                item
                                for item in locked_records
                                if first_string(item, ("question_id", "qid", "id")) == question_id
                            ),
                            None,
                        )
                        if isinstance(matched_role_record, dict):
                            for field in ("question", "table_id"):
                                if record.get(field) != matched_role_record.get(field):
                                    errors.append(
                                        f"locked_eval: annotation {field} disagrees with its locked role record"
                                    )
                            if "source_split" in record and record.get("source_split") != matched_role_record.get(
                                "source_split"
                            ):
                                errors.append(
                                    "locked_eval: annotation source_split disagrees with its locked role record"
                                )
        if isinstance(source, dict):
            from build_sample import (
                OFFICIAL_HYBRIDQA_COMMIT,
                OFFICIAL_QUESTION_ARTIFACTS,
                QUESTION_ID_SET_HASH_ALGORITHM,
            )

            portable_reference = source.get("portable_reference")
            artifact_path = (
                portable_reference.get("artifact_path") if isinstance(portable_reference, dict) else None
            )
            canonical_source = OFFICIAL_QUESTION_ARTIFACTS.get(str(artifact_path))
            if (
                not isinstance(portable_reference, dict)
                or portable_reference.get("source_id") != "hybridqa_questions_and_code"
                or portable_reference.get("pinned_commit") != OFFICIAL_HYBRIDQA_COMMIT
                or canonical_source is None
                or portable_reference.get("artifact_sha256") != canonical_source["sha256"]
                or portable_reference.get("record_count") != canonical_source["record_count"]
                or portable_reference.get("question_id_set_sha256")
                != canonical_source["question_id_set_sha256"]
                or source.get("sha256") != canonical_source["sha256"]
                or source.get("record_count") != canonical_source["record_count"]
                or source.get("question_id_set_sha256") != canonical_source["question_id_set_sha256"]
            ):
                errors.append("locked_eval: split portable source reference is not the canonical HybridQA pin")
            inventory_artifact = source.get("question_id_inventory_artifact")
            if not isinstance(inventory_artifact, dict):
                errors.append("locked_eval: split source lacks a verifiable question-ID inventory")
            else:
                inventory_path_value = inventory_artifact.get("path")
                if not isinstance(inventory_path_value, str):
                    errors.append("locked_eval: source question-ID inventory path is missing")
                else:
                    root = project_root.resolve()
                    inventory_path = (root / inventory_path_value).resolve()
                    try:
                        inventory_path.relative_to(root)
                    except ValueError:
                        errors.append("locked_eval: source question-ID inventory escapes project root")
                    else:
                        if not inventory_path.is_file():
                            errors.append("locked_eval: source question-ID inventory is missing")
                        elif sha256_file(inventory_path) != inventory_artifact.get("sha256"):
                            errors.append("locked_eval: source question-ID inventory SHA-256 mismatch")
                        else:
                            inventory = read_json(inventory_path)
                            inventory_ids = (
                                inventory.get("question_ids") if isinstance(inventory, dict) else None
                            )
                            valid_inventory = (
                                isinstance(inventory, dict)
                                and inventory.get("schema_version")
                                == "hybridqa_source_question_ids_v0_1"
                                and inventory.get("source_id") == "hybridqa_questions_and_code"
                                and inventory.get("pinned_commit") == OFFICIAL_HYBRIDQA_COMMIT
                                and inventory.get("artifact_path") == artifact_path
                                and isinstance(canonical_source, dict)
                                and inventory.get("artifact_sha256") == canonical_source["sha256"]
                                and isinstance(inventory_ids, list)
                                and len(inventory_ids) == canonical_source["record_count"]
                                and all(isinstance(identifier, str) for identifier in inventory_ids)
                                and len(inventory_ids) == len(set(inventory_ids))
                                and inventory.get("question_id_set_hash_algorithm")
                                == QUESTION_ID_SET_HASH_ALGORITHM
                                and canonical_string_set_sha256(inventory_ids)
                                == canonical_source["question_id_set_sha256"]
                                and inventory.get("question_id_set_sha256")
                                == canonical_source["question_id_set_sha256"]
                                and inventory_artifact.get("record_count")
                                == canonical_source["record_count"]
                                and inventory_artifact.get("question_id_set_sha256")
                                == canonical_source["question_id_set_sha256"]
                            )
                            if not valid_inventory:
                                errors.append(
                                    "locked_eval: source question-ID inventory does not match the canonical pin"
                                )
                            elif question_id not in set(inventory_ids):
                                errors.append(
                                    "locked_eval: question_id is absent from the pinned source inventory"
                                )
                            elif isinstance(roles, dict):
                                allocated_ids = {
                                    identifier
                                    for role_ids in safe_roles.values()
                                    for identifier in role_ids
                                }
                                if not allocated_ids.issubset(set(inventory_ids)):
                                    errors.append(
                                        "locked_eval: one or more split role IDs are absent from the pinned source"
                                    )
    if history is not None:
        if (
            history.get("schema_version") != "historical_exposed_ids_v0_1"
            or history.get("is_complete") is not True
            or history.get("audit_status") != "complete"
        ):
            errors.append("locked_eval: historical exposure manifest is not complete")
        raw_exposed = history.get("exposed_question_ids")
        raw_forbidden = history.get("forbidden_future_training_ids")
        if not isinstance(raw_exposed, list) or not all(
            isinstance(identifier, str) for identifier in raw_exposed
        ) or len(raw_exposed) != len(set(raw_exposed)):
            errors.append("locked_eval: historical exposed_question_ids must be a unique string-ID array")
            raw_exposed = []
        if not isinstance(raw_forbidden, list) or not all(
            isinstance(identifier, str) for identifier in raw_forbidden
        ) or len(raw_forbidden) != len(set(raw_forbidden)):
            errors.append(
                "locked_eval: historical forbidden_future_training_ids must be a unique string-ID array"
            )
            raw_forbidden = []
        exposed = set(raw_exposed)
        forbidden = set(raw_forbidden)
        if question_id in exposed or question_id in forbidden:
            errors.append("locked_eval: question_id was historically exposed and is not fresh")
        if split is not None:
            allocated_ids = {
                identifier
                for role_ids in safe_roles.values()
                for identifier in role_ids
            }
            historical_overlap = allocated_ids & (exposed | forbidden)
            if historical_overlap:
                errors.append(
                    "locked_eval: split roles include historically exposed or forbidden IDs"
                )
            split_history = split.get("historical_manifest")
            history_artifact = controls.get("historical_exposure_manifest_artifact")
            if (
                isinstance(split_history, dict)
                and isinstance(history_artifact, dict)
                and split_history.get("sha256") != history_artifact.get("sha256")
            ):
                errors.append("locked_eval: split and annotation reference different historical manifests")
        try:
            from build_sample import historical_release_errors

            history_contract_errors = historical_release_errors(history, project_root)
        except (ImportError, OSError, TypeError, ValueError) as exc:
            history_contract_errors = [f"could not rerun historical release contract: {exc}"]
        if history_contract_errors:
            errors.append(
                "locked_eval: historical exposure artifact fails live release re-verification: "
                + "; ".join(history_contract_errors)
            )
    return errors


def check_forbidden_keys(
    value: Any,
    forbidden: set[str],
    layer: str,
    errors: list[str],
) -> None:
    canonical_forbidden = {
        variant for key in forbidden for variant in canonical_key_variants(key)
    }
    for path, key in walk_keys(value, f"$.{layer}"):
        if canonical_key_variants(key) & canonical_forbidden:
            errors.append(f"leakage:{layer}: forbidden key {key!r} at {path}")


def nested_string_values(value: Any, wanted_key: str) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == wanted_key and isinstance(child, str):
                result.add(child)
            result.update(nested_string_values(child, wanted_key))
    elif isinstance(value, list):
        for child in value:
            result.update(nested_string_values(child, wanted_key))
    return result


def reference_list_errors(
    node: dict[str, Any],
    field: str,
    allowed: set[str],
    label: str,
) -> list[str]:
    if field not in node:
        return []
    references = node[field]
    if not isinstance(references, list) or not all(isinstance(value, str) for value in references):
        return [f"{label}.{field}: expected string array"]
    return [f"{label}.{field}: unknown reference {value!r}" for value in references if value not in allowed]


def execution_reference_errors(value: Any, obligation_ids: set[str]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        return ["execution_reference: expected object"]

    errors: list[str] = []
    expected_intermediates = value.get("expected_intermediates")
    if not isinstance(expected_intermediates, list):
        errors.append("execution_reference.expected_intermediates: expected array")
    else:
        expectation_ids: set[str] = set()
        for index, expectation in enumerate(expected_intermediates):
            label = f"execution_reference.expected_intermediates[{index}]"
            if not isinstance(expectation, dict):
                errors.append(f"{label}: expected object")
                continue
            expectation_id = first_string(expectation, ("expectation_id",))
            if not expectation_id:
                errors.append(f"{label}: missing expectation_id")
            elif expectation_id in expectation_ids:
                errors.append(
                    f"execution_reference.expected_intermediates: duplicate expectation_id {expectation_id!r}"
                )
            else:
                expectation_ids.add(expectation_id)
            errors.extend(
                reference_list_errors(
                    expectation,
                    "obligation_ids",
                    obligation_ids,
                    label,
                )
            )

    execution_trials = value.get("execution_trials")
    if not isinstance(execution_trials, list):
        errors.append("execution_reference.execution_trials: expected array")
    else:
        trial_ids: set[str] = set()
        for index, trial in enumerate(execution_trials):
            label = f"execution_reference.execution_trials[{index}]"
            if not isinstance(trial, dict):
                errors.append(f"{label}: expected object")
                continue
            trial_id = first_string(trial, ("trial_id",))
            if not trial_id:
                errors.append(f"{label}: missing trial_id")
            elif trial_id in trial_ids:
                errors.append(f"execution_reference.execution_trials: duplicate trial_id {trial_id!r}")
            else:
                trial_ids.add(trial_id)
    return errors


def topology_errors(topology: Any, label: str, allowed_operators: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(topology, dict):
        return [f"{label}: expected object"]
    nodes = topology.get("nodes")
    if not isinstance(nodes, list):
        return [f"{label}.nodes: expected array"]

    identifiers: list[str] = []
    dependencies: dict[str, list[str]] = {}
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"{label}.nodes[{index}]: expected object")
            continue
        node_id = first_string(node, ("id", "node_id"))
        if not node_id:
            errors.append(f"{label}.nodes[{index}]: missing id")
            continue
        identifiers.append(node_id)
        raw_dependencies = node.get("depends_on", [])
        if not isinstance(raw_dependencies, list) or not all(isinstance(item, str) for item in raw_dependencies):
            errors.append(f"{label}.nodes[{index}].depends_on: expected string array")
            raw_dependencies = []
        elif len(raw_dependencies) != len(set(raw_dependencies)):
            errors.append(f"{label}.nodes[{index}].depends_on: duplicate dependency IDs")
        dependencies[node_id] = list(raw_dependencies)
        if allowed_operators is not None:
            operator = first_string(node, ("operator", "operation"))
            if not operator:
                errors.append(f"{label}.nodes[{index}]: missing operator")
            elif allowed_operators and operator not in allowed_operators:
                errors.append(f"{label}.nodes[{index}]: unknown operator {operator!r}")

    duplicates = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
    if duplicates:
        errors.append(f"{label}: duplicate node IDs: {', '.join(duplicates)}")
    known = set(identifiers)
    for node_id, node_dependencies in dependencies.items():
        for dependency in node_dependencies:
            if dependency not in known:
                errors.append(f"{label}: node {node_id!r} depends on missing node {dependency!r}")
            if dependency == node_id:
                errors.append(f"{label}: node {node_id!r} has a self-dependency")

    indegree = {identifier: 0 for identifier in known}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for node_id, node_dependencies in dependencies.items():
        for dependency in node_dependencies:
            if dependency in known and dependency != node_id:
                indegree[node_id] += 1
                outgoing[dependency].append(node_id)
    original_indegree = dict(indegree)
    queue = deque(sorted(identifier for identifier, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for target in outgoing[current]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(known):
        errors.append(f"{label}: dependency graph contains a cycle")

    declared_entries = topology.get("entry_node_ids")
    if declared_entries is not None and (
        not isinstance(declared_entries, list) or not all(isinstance(item, str) for item in declared_entries)
    ):
        errors.append(f"{label}.entry_node_ids: expected string array")
        declared_entries = []
    entry_ids = set(declared_entries or [identifier for identifier, degree in original_indegree.items() if degree == 0])
    for entry_id in sorted(entry_ids - known):
        errors.append(f"{label}: entry node {entry_id!r} is missing")
    for entry_id in sorted(entry_ids & known):
        if original_indegree[entry_id] != 0:
            errors.append(f"{label}: declared entry node {entry_id!r} has dependencies")
    reachable = set(entry_ids & known)
    reach_queue = deque(sorted(reachable))
    while reach_queue:
        current = reach_queue.popleft()
        for target in outgoing[current]:
            if target not in reachable:
                reachable.add(target)
                reach_queue.append(target)
    if declared_entries is not None:
        for node_id in sorted(known - reachable):
            errors.append(f"{label}: node {node_id!r} is unreachable from declared entries")

    declared_outputs = topology.get("output_node_ids")
    if declared_outputs is not None:
        if not isinstance(declared_outputs, list) or not all(isinstance(item, str) for item in declared_outputs):
            errors.append(f"{label}.output_node_ids: expected string array")
        else:
            for output_id in declared_outputs:
                if output_id not in known:
                    errors.append(f"{label}: output node {output_id!r} is missing")
                elif output_id not in reachable:
                    errors.append(f"{label}: output node {output_id!r} is not source-reachable")
    return errors


def jsonschema_errors(record: dict[str, Any], schema: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - environment-dependent branch
        raise RuntimeError("jsonschema is not installed; install requirements.txt or use --structural-only") from exc

    schema_uri = str(schema.get("$schema", ""))
    if "2020-12" in schema_uri and not hasattr(jsonschema, "Draft202012Validator"):
        raise RuntimeError(
            "the installed jsonschema is too old for Draft 2020-12; "
            "install the pinned requirements or use --structural-only"
        )
    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)
    resolver = jsonschema.RefResolver(base_uri=schema_path.resolve().as_uri(), referrer=schema)
    format_checker = jsonschema.FormatChecker()
    format_checker.checks("date-time")(is_rfc3339_datetime)
    format_checker.checks("uri")(is_absolute_uri)
    validator = validator_class(schema, resolver=resolver, format_checker=format_checker)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(record), key=lambda item: list(item.absolute_path)):
        location = "$"
        for part in error.absolute_path:
            location += f"[{part}]" if isinstance(part, int) else f".{part}"
        errors.append(f"schema:{location}: {error.message}")
    return errors


def validate_ir_v0_2_execution_graph_reference(
    execution_graph: Any,
    question_id: str | None,
    table_id: str | None,
    project_root: Path,
) -> tuple[list[str], list[str], list[str]]:
    """Validate a ``referenced_validated`` envelope against preserved IR v0.2.

    Declaration failures stop before historical code or graph bytes are loaded.
    A passing declaration is still only a reference claim: the hash-bound graph
    is selected and validated live by the current-side IR adapter, then its
    question/table identity is tied back to the annotation.
    """

    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []
    label = "execution_graph"

    if not isinstance(execution_graph, dict):
        return [f"{label}: referenced IR v0.2 envelope must be an object"], warnings, checks
    if execution_graph.get("graph_status") != "referenced_validated":
        errors.append(
            f"{label}.graph_status must be exactly 'referenced_validated' for live IR v0.2 validation"
        )
    if execution_graph.get("declared_target_ir_version") != "IR_v0.2":
        errors.append(
            f"{label}.declared_target_ir_version must be exactly 'IR_v0.2'"
        )
    if execution_graph.get("local_ir_definition_status") != "available":
        errors.append(
            f"{label}.local_ir_definition_status must be exactly 'available'"
        )
    if execution_graph.get("executable_status") == "executable":
        errors.append(
            f"{label}: executable is unsupported until live execution evidence validation is restored"
        )

    schema_artifact = execution_graph.get("ir_schema_artifact")
    if not isinstance(schema_artifact, dict):
        errors.append(f"{label}.ir_schema_artifact must be an object")
    else:
        if (
            schema_artifact.get("repository_relative_path")
            != IR_V0_2_SCHEMA_REPOSITORY_PATH
        ):
            errors.append(
                f"{label}.ir_schema_artifact.repository_relative_path must be exactly "
                f"{IR_V0_2_SCHEMA_REPOSITORY_PATH!r}"
            )
        if schema_artifact.get("sha256") != IR_V0_2_SCHEMA_SHA256:
            errors.append(
                f"{label}.ir_schema_artifact.sha256 must be exactly the preserved IR v0.2 schema digest"
            )

    graph_artifact = execution_graph.get("graph_artifact")
    graph_path: str | None = None
    graph_sha256: str | None = None
    if not isinstance(graph_artifact, dict):
        errors.append(f"{label}.graph_artifact must be an object")
    else:
        raw_path = graph_artifact.get("repository_relative_path")
        if not isinstance(raw_path, str) or not raw_path:
            errors.append(
                f"{label}.graph_artifact.repository_relative_path must be a non-empty repository path"
            )
        elif Path(raw_path).is_absolute():
            errors.append(
                f"{label}.graph_artifact.repository_relative_path must be repository-relative"
            )
        else:
            try:
                resolved_root = project_root.resolve()
                (resolved_root / raw_path).resolve().relative_to(resolved_root)
            except (OSError, RuntimeError, ValueError):
                errors.append(
                    f"{label}.graph_artifact.repository_relative_path escapes the project root"
                )
            else:
                graph_path = raw_path
        raw_sha256 = graph_artifact.get("sha256")
        if not isinstance(raw_sha256, str) or LOWERCASE_SHA256_RE.fullmatch(raw_sha256) is None:
            errors.append(
                f"{label}.graph_artifact.sha256 must be exactly 64 lowercase hexadecimal characters"
            )
        else:
            graph_sha256 = raw_sha256

    graph_id = execution_graph.get("graph_id")
    if not isinstance(graph_id, str) or not graph_id:
        errors.append(f"{label}.graph_id must be a non-empty string")

    raw_validation_checks = execution_graph.get("validation_checks")
    check_entries: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not isinstance(raw_validation_checks, list):
        errors.append(f"{label}.validation_checks must be an array")
    else:
        for index, validation_check in enumerate(raw_validation_checks):
            if not isinstance(validation_check, dict):
                errors.append(
                    f"{label}.validation_checks[{index}] must be an object"
                )
                continue
            check_name = validation_check.get("check")
            if check_name in IR_V0_2_REQUIRED_VALIDATION_CHECKS:
                check_entries[check_name].append(validation_check)
        for required_check in IR_V0_2_REQUIRED_VALIDATION_CHECKS:
            entries = check_entries[required_check]
            if len(entries) != 1:
                errors.append(
                    f"{label}.validation_checks must contain {required_check!r} exactly once; "
                    f"found {len(entries)}"
                )
            elif entries[0].get("status") != "passed":
                errors.append(
                    f"{label}.validation_checks[{required_check!r}] must have status 'passed'"
                )

    if errors:
        return errors, warnings, checks
    checks.append("execution_graph_ir_v0_2_reference_declarations")

    try:
        adapter_result = validate_ir_v0_2_reference(
            artifact=graph_path,
            sha256=graph_sha256,
            graph_id=graph_id,
            all_graphs=False,
            project_root=project_root,
        )
    except Exception as exc:
        errors.append(
            f"{label}: IR v0.2 reference adapter raised {type(exc).__name__}: {exc}"
        )
        return errors, warnings, checks

    if not isinstance(adapter_result, dict):
        errors.append(f"{label}: IR v0.2 reference adapter returned a non-object result")
        return errors, warnings, checks
    adapter_errors = adapter_result.get("errors")
    if not isinstance(adapter_errors, list):
        errors.append(f"{label}: IR v0.2 reference adapter returned malformed errors")
        return errors, warnings, checks
    for adapter_error in adapter_errors:
        if isinstance(adapter_error, dict):
            code = adapter_error.get("code", "UNKNOWN")
            message = adapter_error.get("message", "unspecified adapter error")
            errors.append(f"{label}: IR v0.2 adapter {code}: {message}")
        else:
            errors.append(f"{label}: IR v0.2 adapter error: {adapter_error!r}")
    if adapter_result.get("status") != "pass" and not adapter_errors:
        errors.append(f"{label}: IR v0.2 reference adapter status is not 'pass'")
    if errors:
        return errors, warnings, checks

    adapter_graphs = adapter_result.get("graphs")
    if not isinstance(adapter_graphs, list) or len(adapter_graphs) != 1:
        errors.append(
            f"{label}: IR v0.2 reference adapter must return exactly one selected graph"
        )
        return errors, warnings, checks
    adapter_graph = adapter_graphs[0]
    if not isinstance(adapter_graph, dict):
        errors.append(f"{label}: IR v0.2 reference adapter graph result must be an object")
        return errors, warnings, checks
    if adapter_graph.get("status") != "pass" or adapter_graph.get("errors"):
        errors.append(
            f"{label}: selected IR v0.2 graph did not pass live reference validation"
        )
    if adapter_graph.get("graph_id") != graph_id:
        errors.append(f"{label}: adapter graph_id does not match the declared graph_id")
    if adapter_graph.get("question_id") != question_id:
        errors.append(
            f"{label}: adapter question_id {adapter_graph.get('question_id')!r} does not match "
            f"annotation question_id {question_id!r}"
        )
    if adapter_graph.get("table_id") != table_id:
        errors.append(
            f"{label}: adapter table_id {adapter_graph.get('table_id')!r} does not match "
            f"annotation table_id {table_id!r}"
        )

    adapter_warnings = adapter_result.get("warnings")
    if isinstance(adapter_warnings, list) and adapter_warnings:
        warning_codes: dict[str, int] = defaultdict(int)
        for adapter_warning in adapter_warnings:
            code = (
                adapter_warning.get("code", "UNKNOWN")
                if isinstance(adapter_warning, dict)
                else "UNKNOWN"
            )
            warning_codes[str(code)] += 1
        warning_summary = ", ".join(
            f"{code}={count}" for code, count in sorted(warning_codes.items())
        )
        warnings.append(
            f"{label}: live IR v0.2 adapter reported {len(adapter_warnings)} warning(s): "
            f"{warning_summary}"
        )

    if not errors:
        checks.append("execution_graph_ir_v0_2_live_reference")
    return errors, warnings, checks


def validate_record(
    record: dict[str, Any],
    allowed_operators: set[str],
    operator_definitions: dict[str, dict[str, Any]],
    vocabulary_version: str | None,
    vocabulary_granularity: str | None,
    schema: dict[str, Any] | None,
    schema_path: Path,
) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []

    if schema is not None:
        errors.extend(jsonschema_errors(record, schema, schema_path))
        checks.append("json_schema")

    question_id = first_string(record, ("question_id", "qid", "id"))
    if not question_id:
        errors.append("identity: missing question_id")
    question_text = first_string(record, ("question", "query", "text"))
    errors.extend(source_span_errors(record, question_text))
    errors.extend(artifact_reference_errors(record, Path.cwd()))
    checks.extend(("source_span_offsets", "repository_artifact_references"))

    for layer in ("semantic_skeleton", "information_obligations", "abstract_topology"):
        if layer in record:
            check_forbidden_keys(record[layer], EARLY_LAYER_FORBIDDEN_KEYS, layer, errors)
    checks.append("early_layer_leakage")

    skeleton = record.get("semantic_skeleton", {})
    candidate_structure = skeleton.get("candidate_structure", {}) if isinstance(skeleton, dict) else {}
    candidate_variables = (
        candidate_structure.get("variables", []) if isinstance(candidate_structure, dict) else []
    )
    declared_variable_values = [
        first_string(variable, ("variable_id",))
        for variable in candidate_variables
        if isinstance(variable, dict)
    ] if isinstance(candidate_variables, list) else []
    skeleton_variable_ids = {value for value in declared_variable_values if value is not None}
    if len(declared_variable_values) != len(skeleton_variable_ids):
        errors.append("semantic_skeleton: candidate variable IDs are missing or duplicated")

    declared_requirement_values = [
        value.get("requirement_id")
        for _, value in walk_objects(skeleton)
        if isinstance(value.get("requirement_id"), str)
    ]
    skeleton_requirement_ids = set(declared_requirement_values)
    if len(declared_requirement_values) != len(skeleton_requirement_ids):
        errors.append("semantic_skeleton: requirement IDs are duplicated")
    for path, value in walk_objects(skeleton):
        for key, reference in value.items():
            if key != "variable_id" and (key.endswith("_variable_id") or key.endswith("_variable_ids")):
                references = reference if isinstance(reference, list) else [reference]
                for identifier in references:
                    if isinstance(identifier, str) and identifier not in skeleton_variable_ids:
                        errors.append(f"semantic_skeleton:{path}.{key}: unknown variable reference {identifier!r}")
            if key != "requirement_id" and (
                key.endswith("_requirement_id") or key.endswith("_requirement_ids")
            ):
                references = reference if isinstance(reference, list) else [reference]
                for identifier in references:
                    if isinstance(identifier, str) and identifier not in skeleton_requirement_ids:
                        errors.append(f"semantic_skeleton:{path}.{key}: unknown requirement reference {identifier!r}")
    checks.append("semantic_variable_and_requirement_references")
    obligation_container = record.get("information_obligations")
    if isinstance(obligation_container, dict):
        obligation_nodes = obligation_container.get("obligations", [])
        obligation_outputs = obligation_container.get("terminal_obligation_ids")
    elif isinstance(obligation_container, list):
        obligation_nodes = obligation_container
        obligation_outputs = None
    else:
        obligation_nodes = []
        if obligation_container is not None:
            errors.append("information_obligations: expected object or array")
        obligation_outputs = None
    obligation_topology_nodes: list[dict[str, Any]] = []
    obligation_output_role_ids: set[str] = set()
    for index, obligation in enumerate(obligation_nodes if isinstance(obligation_nodes, list) else []):
        if not isinstance(obligation, dict):
            errors.append(f"information_obligations.obligations[{index}]: expected object")
            continue
        obligation_topology_nodes.append(
            {
                "id": first_string(obligation, ("obligation_id", "id")),
                "depends_on": obligation.get("depends_on", []),
            }
        )
        errors.extend(
            reference_list_errors(
                obligation,
                "skeleton_requirement_refs",
                skeleton_requirement_ids,
                f"information_obligations.obligations[{index}]",
            )
        )
        semantic_outputs = obligation.get("semantic_outputs", [])
        if isinstance(semantic_outputs, list):
            for output in semantic_outputs:
                output_role_id = first_string(output, ("output_role_id",)) if isinstance(output, dict) else None
                if output_role_id in obligation_output_role_ids:
                    errors.append(
                        f"information_obligations.obligations[{index}]: duplicate semantic output role {output_role_id!r}"
                    )
                if output_role_id:
                    obligation_output_role_ids.add(output_role_id)
    obligation_topology: dict[str, Any] = {"nodes": obligation_topology_nodes}
    if obligation_outputs is not None:
        obligation_topology["output_node_ids"] = obligation_outputs
    if obligation_container is not None:
        errors.extend(topology_errors(obligation_topology, "information_obligations"))
        checks.append("obligation_dependency_dag")
    obligation_ids = {
        first_string(obligation, ("obligation_id", "id"))
        for obligation in obligation_nodes
        if isinstance(obligation, dict)
    } if isinstance(obligation_nodes, list) else set()
    obligation_ids.discard(None)

    execution_reference = record.get("execution_reference")
    if execution_reference is not None:
        errors.extend(execution_reference_errors(execution_reference, obligation_ids))
        checks.append("execution_reference_identifier_and_obligation_references")

    operator_topology = record.get("operator_topology")
    if operator_topology is not None:
        errors.extend(topology_errors(operator_topology, "operator_topology", allowed_operators))
        check_forbidden_keys(operator_topology, TOPOLOGY_FORBIDDEN_KEYS, "operator_topology", errors)
        if isinstance(operator_topology, dict):
            declared_vocabulary = operator_topology.get("operator_vocabulary")
            if isinstance(declared_vocabulary, dict):
                if vocabulary_version and declared_vocabulary.get("vocabulary_version") != vocabulary_version:
                    errors.append(
                        "operator_topology: declared vocabulary_version does not match the validator vocabulary"
                    )
                if vocabulary_granularity and declared_vocabulary.get("granularity") != vocabulary_granularity:
                    errors.append("operator_topology: declared granularity does not match the validator vocabulary")
            else:
                warnings.append("operator_topology has no operator_vocabulary declaration")
    else:
        warnings.append("operator_topology is absent")
    checks.extend(("operator_registry", "dependency_dag", "topology_grounding_separation"))

    abstract_topology = record.get("abstract_topology")
    if abstract_topology is not None:
        errors.extend(topology_errors(abstract_topology, "abstract_topology"))
    abstract_nodes = abstract_topology.get("nodes", []) if isinstance(abstract_topology, dict) else []
    if not isinstance(abstract_nodes, list):
        abstract_nodes = []
    abstract_node_ids = {
        first_string(node, ("node_id", "id")) for node in abstract_nodes if isinstance(node, dict)
    }
    abstract_node_ids.discard(None)
    for index, node in enumerate(abstract_nodes if isinstance(abstract_nodes, list) else []):
        if not isinstance(node, dict):
            continue
        semantic_function = first_string(node, ("semantic_function", "function"))
        if not semantic_function:
            errors.append(f"abstract_topology.nodes[{index}]: missing semantic_function")
        elif semantic_function not in ABSTRACT_SEMANTIC_FUNCTIONS:
            errors.append(f"abstract_topology.nodes[{index}]: unknown semantic function {semantic_function!r}")
        errors.extend(
            reference_list_errors(
                node,
                "fulfills_obligation_ids",
                obligation_ids,
                f"abstract_topology.nodes[{index}]",
            )
        )
        errors.extend(
            reference_list_errors(
                node,
                "realizes_skeleton_requirement_ids",
                skeleton_requirement_ids,
                f"abstract_topology.nodes[{index}]",
            )
        )
        semantic_variable_ids = skeleton_variable_ids | obligation_output_role_ids
        for variable_field in ("input_semantic_variable_ids", "output_semantic_variable_ids"):
            errors.extend(
                reference_list_errors(
                    node,
                    variable_field,
                    semantic_variable_ids,
                    f"abstract_topology.nodes[{index}]",
                )
            )
    abstract_constraint_signatures: dict[str, tuple[tuple[str, ...], str | None, str | None]] = {}
    abstract_constraints = (
        abstract_topology.get("required_dependency_constraints", [])
        if isinstance(abstract_topology, dict)
        else []
    )
    if isinstance(abstract_constraints, list):
        for constraint_index, constraint in enumerate(abstract_constraints):
            if not isinstance(constraint, dict):
                errors.append(
                    f"abstract_topology.required_dependency_constraints[{constraint_index}]: expected object"
                )
                continue
            constraint_id = first_string(constraint, ("constraint_id", "id"))
            if constraint_id in abstract_constraint_signatures:
                errors.append(f"abstract_topology: duplicate dependency constraint {constraint_id!r}")
            errors.extend(
                reference_list_errors(
                    constraint,
                    "predecessor_obligation_ids",
                    obligation_ids,
                    f"abstract_topology.required_dependency_constraints[{constraint_index}]",
                )
            )
            successor = constraint.get("successor_obligation_id")
            if isinstance(successor, str) and successor not in obligation_ids:
                errors.append(
                    f"abstract_topology.required_dependency_constraints[{constraint_index}]."
                    f"successor_obligation_id: unknown reference {successor!r}"
                )
            if constraint_id:
                predecessors = constraint.get("predecessor_obligation_ids", [])
                abstract_constraint_signatures[constraint_id] = (
                    tuple(sorted(predecessors)) if isinstance(predecessors, list) else (),
                    successor if isinstance(successor, str) else None,
                    constraint.get("dependency_kind") if isinstance(constraint.get("dependency_kind"), str) else None,
                )
    elif abstract_topology is not None:
        errors.append("abstract_topology.required_dependency_constraints: expected array")

    operator_nodes = operator_topology.get("nodes", []) if isinstance(operator_topology, dict) else []
    if not isinstance(operator_nodes, list):
        operator_nodes = []
    operator_nodes_by_id = {
        node_id: node
        for node in operator_nodes
        if isinstance(node, dict)
        if (node_id := first_string(node, ("node_id", "id"))) is not None
    }
    for index, node in enumerate(operator_nodes if isinstance(operator_nodes, list) else []):
        if not isinstance(node, dict):
            continue
        errors.extend(
            reference_list_errors(
                node,
                "fulfills_obligation_ids",
                obligation_ids,
                f"operator_topology.nodes[{index}]",
            )
        )
        errors.extend(
            reference_list_errors(
                node,
                "realizes_abstract_node_ids",
                abstract_node_ids,
                f"operator_topology.nodes[{index}]",
            )
        )
        semantic_role_registry = skeleton_variable_ids | skeleton_requirement_ids | obligation_output_role_ids
        input_slots_for_refs = node.get("input_slots", [])
        if isinstance(input_slots_for_refs, list):
            for slot_index, slot in enumerate(input_slots_for_refs):
                source = slot.get("source") if isinstance(slot, dict) else None
                if isinstance(source, dict) and source.get("source_kind") == "semantic_input":
                    semantic_variable_id = source.get("semantic_variable_id")
                    if semantic_variable_id not in semantic_role_registry:
                        errors.append(
                            f"operator_topology.nodes[{index}].input_slots[{slot_index}]: unknown "
                            f"semantic_variable_id {semantic_variable_id!r}"
                        )
        output_slots_for_refs = node.get("output_slots", [])
        if isinstance(output_slots_for_refs, list):
            for slot_index, slot in enumerate(output_slots_for_refs):
                if isinstance(slot, dict):
                    errors.extend(
                        reference_list_errors(
                            slot,
                            "semantic_variable_ids",
                            semantic_role_registry,
                            f"operator_topology.nodes[{index}].output_slots[{slot_index}]",
                        )
                    )
        topology_arguments_for_refs = node.get("argument_slots", [])
        if isinstance(topology_arguments_for_refs, list):
            for slot_index, slot in enumerate(topology_arguments_for_refs):
                semantic_role_ref = slot.get("semantic_role_ref") if isinstance(slot, dict) else None
                if isinstance(semantic_role_ref, str) and semantic_role_ref not in semantic_role_registry:
                    errors.append(
                        f"operator_topology.nodes[{index}].argument_slots[{slot_index}]: unknown "
                        f"semantic_role_ref {semantic_role_ref!r}"
                    )
        operator_name = first_string(node, ("operator", "operation"))
        definition = operator_definitions.get(operator_name or "")
        if not definition:
            continue

        declared_argument_slots = node.get("argument_slots")
        vocabulary_argument_slots = definition.get("argument_slots", [])
        if isinstance(declared_argument_slots, list) and isinstance(vocabulary_argument_slots, list):
            expected_arguments = {
                item.get("name"): item
                for item in vocabulary_argument_slots
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            }
            observed_arguments: dict[str, dict[str, Any]] = {}
            for argument in declared_argument_slots:
                if not isinstance(argument, dict):
                    continue
                slot_name = first_string(argument, ("slot_name", "name"))
                if not slot_name:
                    continue
                if slot_name in observed_arguments:
                    errors.append(
                        f"operator_topology.nodes[{index}].argument_slots: duplicate slot {slot_name!r}"
                    )
                observed_arguments[slot_name] = argument
                expected_argument = expected_arguments.get(slot_name)
                if expected_argument is None:
                    errors.append(
                        f"operator_topology.nodes[{index}].argument_slots: unknown {operator_name} slot {slot_name!r}"
                    )
                    continue
                if argument.get("expected_binding_kind") != expected_argument.get("binding_kind"):
                    errors.append(
                        f"operator_topology.nodes[{index}] argument {slot_name!r}: binding kind does not match vocabulary"
                    )
                if argument.get("required") is not expected_argument.get("required"):
                    errors.append(
                        f"operator_topology.nodes[{index}] argument {slot_name!r}: required flag does not match vocabulary"
                    )
            for missing_slot in sorted(set(expected_arguments) - set(observed_arguments)):
                errors.append(
                    f"operator_topology.nodes[{index}].argument_slots: missing vocabulary slot {missing_slot!r}"
                )

        for direction, node_key, type_key in (
            ("input", "input_slots", "expected_type"),
            ("output", "output_slots", "declared_type"),
        ):
            declared_ports = node.get(node_key)
            expected_ports = port_definitions(definition, direction)
            if not isinstance(declared_ports, list):
                continue
            observed_ports: dict[str, dict[str, Any]] = {}
            for port in declared_ports:
                if not isinstance(port, dict):
                    continue
                port_name = first_string(port, ("slot_name", "name"))
                if not port_name:
                    continue
                if port_name in observed_ports:
                    errors.append(
                        f"operator_topology.nodes[{index}].{node_key}: duplicate port {port_name!r}"
                    )
                observed_ports[port_name] = port
                expected_port = expected_ports.get(port_name)
                if expected_port is None:
                    errors.append(
                        f"operator_topology.nodes[{index}].{node_key}: unknown {operator_name} port {port_name!r}"
                    )
                    continue
                if port.get(type_key) != expected_port.get("type"):
                    errors.append(
                        f"operator_topology.nodes[{index}] {direction} port {port_name!r}: type does not match vocabulary"
                    )
                if port.get("cardinality") != expected_port.get("cardinality"):
                    errors.append(
                        f"operator_topology.nodes[{index}] {direction} port {port_name!r}: cardinality does not match vocabulary"
                    )
            for missing_port in sorted(set(expected_ports) - set(observed_ports)):
                errors.append(
                    f"operator_topology.nodes[{index}].{node_key}: missing vocabulary port {missing_port!r}"
                )

    for index, node in enumerate(operator_nodes if isinstance(operator_nodes, list) else []):
        if not isinstance(node, dict):
            continue
        depends_on = {
            dependency
            for dependency in node.get("depends_on", [])
            if isinstance(dependency, str)
        } if isinstance(node.get("depends_on"), list) else set()
        input_slots = node.get("input_slots", [])
        if not isinstance(input_slots, list):
            continue
        for slot_index, slot in enumerate(input_slots):
            if not isinstance(slot, dict) or not isinstance(slot.get("source"), dict):
                continue
            source = slot["source"]
            if source.get("source_kind") != "upstream_output":
                continue
            source_node_id = source.get("source_node_id")
            source_port_name = source.get("source_port")
            source_node = operator_nodes_by_id.get(source_node_id)
            label = f"operator_topology.nodes[{index}].input_slots[{slot_index}]"
            if source_node is None:
                errors.append(f"{label}: unknown source_node_id {source_node_id!r}")
                continue
            if source_node_id not in depends_on:
                errors.append(f"{label}: upstream source {source_node_id!r} is not a declared dependency")
            source_ports = {
                first_string(port, ("slot_name", "name")): port
                for port in source_node.get("output_slots", [])
                if isinstance(port, dict) and first_string(port, ("slot_name", "name"))
            } if isinstance(source_node.get("output_slots"), list) else {}
            source_port = source_ports.get(source_port_name)
            if source_port is None:
                errors.append(f"{label}: source port {source_port_name!r} does not exist on {source_node_id!r}")
                continue
            if not compatible_types(source_port.get("declared_type"), slot.get("expected_type")):
                errors.append(
                    f"{label}: source type {source_port.get('declared_type')!r} is incompatible with "
                    f"expected type {slot.get('expected_type')!r}"
                )
            if not compatible_cardinalities(
                source_port.get("cardinality"),
                slot.get("cardinality"),
                slot.get("expected_type"),
            ):
                errors.append(
                    f"{label}: source cardinality {source_port.get('cardinality')!r} is incompatible with "
                    f"expected cardinality {slot.get('cardinality')!r}"
                )
    checks.append("cross_layer_id_references")
    checks.append("operator_port_and_type_contracts")

    equivalence_required_obligation_ids: set[str] = set()
    equivalence_constraint_ids: set[str] = set()
    equivalence_constraint_signatures: dict[str, tuple[tuple[str, ...], str | None, str | None]] = {}
    equivalence_contract = record.get("plan_equivalence_contract")
    if isinstance(equivalence_contract, dict):
        raw_required_obligation_ids = equivalence_contract.get("required_obligation_ids", [])
        if isinstance(raw_required_obligation_ids, list):
            equivalence_required_obligation_ids = {
                identifier for identifier in raw_required_obligation_ids if isinstance(identifier, str)
            }
        errors.extend(
            reference_list_errors(
                equivalence_contract,
                "required_obligation_ids",
                obligation_ids,
                "plan_equivalence_contract",
            )
        )
        required_dependencies = equivalence_contract.get("required_dependencies", [])
        if isinstance(required_dependencies, list):
            for dependency_index, dependency in enumerate(required_dependencies):
                if not isinstance(dependency, dict):
                    errors.append(
                        f"plan_equivalence_contract.required_dependencies[{dependency_index}]: expected object"
                    )
                    continue
                constraint_id = first_string(dependency, ("constraint_id", "id"))
                if constraint_id and constraint_id in equivalence_constraint_ids:
                    errors.append(
                        f"plan_equivalence_contract.required_dependencies: duplicate constraint_id {constraint_id!r}"
                    )
                if constraint_id:
                    equivalence_constraint_ids.add(constraint_id)
                errors.extend(
                    reference_list_errors(
                        dependency,
                        "predecessor_obligation_ids",
                        obligation_ids,
                        f"plan_equivalence_contract.required_dependencies[{dependency_index}]",
                    )
                )
                successor = dependency.get("successor_obligation_id")
                if isinstance(successor, str) and successor not in obligation_ids:
                    errors.append(
                        f"plan_equivalence_contract.required_dependencies[{dependency_index}]."
                        f"successor_obligation_id: unknown reference {successor!r}"
                    )
                if constraint_id:
                    predecessors = dependency.get("predecessor_obligation_ids", [])
                    equivalence_constraint_signatures[constraint_id] = (
                        tuple(sorted(predecessors)) if isinstance(predecessors, list) else (),
                        successor if isinstance(successor, str) else None,
                        dependency.get("dependency_kind")
                        if isinstance(dependency.get("dependency_kind"), str)
                        else None,
                    )
        else:
            errors.append("plan_equivalence_contract.required_dependencies: expected array")
        if equivalence_constraint_signatures != abstract_constraint_signatures:
            errors.append(
                "plan_equivalence_contract.required_dependencies does not exactly match "
                "abstract_topology.required_dependency_constraints"
            )
        checks.append("plan_equivalence_obligation_references")
    elif equivalence_contract is not None:
        errors.append("plan_equivalence_contract: expected object")

    if record.get("bundle_status") in {
        "structurally_validated",
        "pending_human_review",
        "human_reviewed",
        "adjudicated",
        "ambiguous_preserved",
    }:
        obligation_requirement_coverage = {
            identifier
            for obligation in obligation_nodes if isinstance(obligation, dict)
            for identifier in obligation.get("skeleton_requirement_refs", [])
            if isinstance(identifier, str)
        } if isinstance(obligation_nodes, list) else set()
        abstract_obligation_coverage = {
            identifier
            for node in abstract_nodes if isinstance(node, dict)
            for identifier in node.get("fulfills_obligation_ids", [])
            if isinstance(identifier, str)
        } if isinstance(abstract_nodes, list) else set()
        operator_obligation_coverage = {
            identifier
            for node in operator_nodes if isinstance(node, dict)
            for identifier in node.get("fulfills_obligation_ids", [])
            if isinstance(identifier, str)
        } if isinstance(operator_nodes, list) else set()
        operator_abstract_coverage = {
            identifier
            for node in operator_nodes if isinstance(node, dict)
            for identifier in node.get("realizes_abstract_node_ids", [])
            if isinstance(identifier, str)
        } if isinstance(operator_nodes, list) else set()
        coverage_checks = (
            (skeleton_requirement_ids, obligation_requirement_coverage, "skeleton requirements by obligations"),
            (obligation_ids, abstract_obligation_coverage, "obligations by abstract topology"),
            (abstract_node_ids, operator_abstract_coverage, "abstract nodes by operator topology"),
            (
                equivalence_required_obligation_ids,
                abstract_obligation_coverage,
                "equivalence obligations by abstract topology",
            ),
            (
                equivalence_required_obligation_ids,
                operator_obligation_coverage,
                "equivalence obligations by operator topology",
            ),
        )
        for required_ids, observed_ids, description in coverage_checks:
            missing_ids = sorted(required_ids - observed_ids)
            if missing_ids:
                errors.append(f"cross_layer_coverage: missing {description}: {missing_ids}")
        checks.append("validated_bundle_cross_layer_coverage")

    execution_graph = record.get("execution_graph")
    if isinstance(execution_graph, dict):
        graph_status = execution_graph.get("graph_status")
        if graph_status == "referenced_validated":
            reference_errors, reference_warnings, reference_checks = (
                validate_ir_v0_2_execution_graph_reference(
                    execution_graph,
                    question_id,
                    first_string(record, ("table_id",)),
                    Path(__file__).resolve().parents[2],
                )
            )
            errors.extend(reference_errors)
            warnings.extend(reference_warnings)
            checks.extend(reference_checks)
            checks.append("execution_graph_reference_envelope")
        elif execution_graph.get("nodes") is not None:
            # Backward-compatible inline graph check; v0.1 normally uses an IR reference envelope.
            errors.extend(topology_errors(execution_graph, "execution_graph", allowed_operators))
            checks.append("execution_graph_dependency_dag")
        elif "graph_status" in execution_graph:
            if graph_status in {"not_constructed", "blocked_missing_ir_definition"}:
                warnings.append(f"execution graph envelope status is {graph_status}")
            if execution_graph.get("executable_status") == "executable":
                errors.append(
                    "execution_graph: executable is unsupported until live execution evidence validation is restored"
                )
            checks.append("execution_graph_reference_envelope")
        elif execution_graph:
            warnings.append("execution_graph object has neither inline nodes nor a graph_status envelope")
    elif execution_graph is None:
        warnings.append("grounded execution graph is not yet available")
    else:
        errors.append("execution_graph: expected object or null")

    topology_node_ids = {
        first_string(node, ("id", "node_id"))
        for node in operator_nodes
        if isinstance(node, dict)
    }
    topology_node_ids.discard(None)
    topology_operator_by_id = {
        node_id: first_string(node, ("operator", "operation"))
        for node in operator_nodes
        if isinstance(node, dict)
        and (node_id := first_string(node, ("id", "node_id"))) is not None
    }
    topology_argument_slots_by_id = {
        node_id: {
            slot_name: slot
            for slot in node.get("argument_slots", [])
            if isinstance(slot, dict)
            if (slot_name := first_string(slot, ("slot_name", "name"))) is not None
        }
        for node in operator_nodes
        if isinstance(node, dict)
        if (node_id := first_string(node, ("id", "node_id"))) is not None
        and isinstance(node.get("argument_slots"), list)
    }
    grounding = record.get("grounding")
    seen_binding_ids: set[str] = set()
    binding_coverage_by_node: dict[str, Any] = {}
    oracle_affected_node_ids: set[str] = set()
    if isinstance(grounding, dict):
        topology_id = operator_topology.get("topology_id") if isinstance(operator_topology, dict) else None
        if topology_id and grounding.get("operator_topology_id") != topology_id:
            errors.append("grounding.operator_topology_id does not match operator_topology.topology_id")
        bindings = grounding.get("node_bindings", grounding.get("bindings", []))
        if isinstance(bindings, list):
            for index, binding in enumerate(bindings):
                if not isinstance(binding, dict):
                    errors.append(f"grounding bindings[{index}]: expected object")
                    continue
                node_id = first_string(binding, ("topology_node_id", "node_id", "id"))
                if not node_id:
                    errors.append(f"grounding bindings[{index}]: missing topology_node_id")
                    continue
                if isinstance(operator_topology, dict) and node_id not in topology_node_ids:
                    errors.append(f"grounding bindings[{index}]: unknown topology node {node_id!r}")
                if node_id in seen_binding_ids:
                    errors.append(f"grounding: multiple binding records for node {node_id!r}")
                seen_binding_ids.add(node_id)
                binding_coverage_by_node[node_id] = binding.get("coverage_status")
                bound_operator = first_string(binding, ("operator",))
                expected_operator = topology_operator_by_id.get(node_id)
                if bound_operator and expected_operator and bound_operator != expected_operator:
                    errors.append(
                        f"grounding bindings[{index}]: operator {bound_operator!r} does not match "
                        f"topology operator {expected_operator!r}"
                    )
                definition = operator_definitions.get(expected_operator or bound_operator or "")
                if definition:
                    raw_slots = definition.get("argument_slots", [])
                    slot_definitions = {
                        slot.get("name"): slot
                        for slot in raw_slots
                        if isinstance(slot, dict) and isinstance(slot.get("name"), str)
                    } if isinstance(raw_slots, list) else {}
                    argument_groundings = binding.get("argument_groundings", [])
                    if not isinstance(argument_groundings, list):
                        errors.append(f"grounding bindings[{index}].argument_groundings: expected array")
                        argument_groundings = []
                    observed_slots: set[str] = set()
                    arguments_by_slot: dict[str, dict[str, Any]] = {}
                    topology_slot_definitions = topology_argument_slots_by_id.get(node_id, {})
                    for argument_index, argument in enumerate(argument_groundings):
                        if not isinstance(argument, dict):
                            errors.append(
                                f"grounding bindings[{index}].argument_groundings[{argument_index}]: expected object"
                            )
                            continue
                        slot_name = first_string(argument, ("slot_name", "name"))
                        if not slot_name:
                            errors.append(
                                f"grounding bindings[{index}].argument_groundings[{argument_index}]: missing slot_name"
                            )
                            continue
                        if slot_name in observed_slots:
                            errors.append(f"grounding bindings[{index}]: duplicate argument slot {slot_name!r}")
                        observed_slots.add(slot_name)
                        arguments_by_slot[slot_name] = argument
                        slot_definition = slot_definitions.get(slot_name)
                        topology_slot_definition = topology_slot_definitions.get(slot_name)
                        oracle_flag = argument.get("oracle_assistance_used") is True
                        oracle_provenance = argument.get("selection_provenance") == "oracle_annotation"
                        if oracle_flag or oracle_provenance:
                            oracle_affected_node_ids.add(node_id)
                        if oracle_flag != oracle_provenance:
                            errors.append(
                                f"grounding bindings[{index}] slot {slot_name!r}: oracle provenance and flag disagree"
                            )
                        if slot_definitions and slot_definition is None:
                            errors.append(
                                f"grounding bindings[{index}]: unknown {expected_operator} argument slot {slot_name!r}"
                            )
                        elif slot_definition is not None:
                            expected_kind = slot_definition.get("binding_kind")
                            if argument.get("expected_binding_kind") != expected_kind:
                                errors.append(
                                    f"grounding bindings[{index}] slot {slot_name!r}: expected_binding_kind does "
                                    f"not match vocabulary kind {expected_kind!r}"
                                )
                            if topology_slot_definition is not None:
                                if argument.get("semantic_role_ref") != topology_slot_definition.get("semantic_role_ref"):
                                    errors.append(
                                        f"grounding bindings[{index}] slot {slot_name!r}: semantic_role_ref does "
                                        "not match the topology slot"
                                    )
                                if argument.get("expected_binding_kind") != topology_slot_definition.get(
                                    "expected_binding_kind"
                                ):
                                    errors.append(
                                        f"grounding bindings[{index}] slot {slot_name!r}: expected_binding_kind "
                                        "does not match the topology slot"
                                    )
                            selected_binding = argument.get("selected_binding")
                            if isinstance(selected_binding, dict) and selected_binding.get("binding_type") != expected_kind:
                                errors.append(
                                    f"grounding bindings[{index}] slot {slot_name!r}: selected binding type "
                                    f"{selected_binding.get('binding_type')!r} does not match {expected_kind!r}"
                                )
                            errors.extend(
                                concrete_binding_errors(
                                    selected_binding,
                                    f"grounding bindings[{index}] slot {slot_name!r} selected_binding",
                                )
                            )
                            candidate_bindings = argument.get("candidate_bindings", [])
                            if isinstance(candidate_bindings, list):
                                selected_candidates: list[dict[str, Any]] = []
                                for candidate_index, candidate in enumerate(candidate_bindings):
                                    concrete = candidate.get("binding") if isinstance(candidate, dict) else None
                                    if isinstance(candidate, dict) and candidate.get("selection_status") == "selected":
                                        selected_candidates.append(candidate)
                                    if isinstance(concrete, dict) and concrete.get("binding_type") != expected_kind:
                                        errors.append(
                                            f"grounding bindings[{index}] slot {slot_name!r} candidate "
                                            f"{candidate_index}: binding type {concrete.get('binding_type')!r} "
                                            f"does not match {expected_kind!r}"
                                        )
                                    errors.extend(
                                        concrete_binding_errors(
                                            concrete,
                                            f"grounding bindings[{index}] slot {slot_name!r} candidate {candidate_index}",
                                        )
                                    )
                                if len(selected_candidates) > 1:
                                    errors.append(
                                        f"grounding bindings[{index}] slot {slot_name!r}: multiple candidates are selected"
                                    )
                                if selected_candidates and not isinstance(selected_binding, dict):
                                    errors.append(
                                        f"grounding bindings[{index}] slot {slot_name!r}: selected candidate lacks selected_binding"
                                    )
                                if isinstance(selected_binding, dict) and candidate_bindings:
                                    if len(selected_candidates) != 1:
                                        errors.append(
                                            f"grounding bindings[{index}] slot {slot_name!r}: selected_binding requires "
                                            "exactly one selected candidate when candidates are present"
                                        )
                                    elif selected_candidates[0].get("binding") != selected_binding:
                                        errors.append(
                                            f"grounding bindings[{index}] slot {slot_name!r}: selected candidate and "
                                            "selected_binding differ"
                                        )
                            if argument.get("status") == "grounded" and not isinstance(selected_binding, dict):
                                errors.append(
                                    f"grounding bindings[{index}] slot {slot_name!r}: grounded status requires selected_binding"
                                )
                    if binding.get("coverage_status") == "all_required_slots_grounded":
                        required_slots = {
                            name for name, slot in slot_definitions.items() if slot.get("required") is True
                        }
                        for missing_slot in sorted(required_slots - observed_slots):
                            errors.append(
                                f"grounding bindings[{index}]: required argument slot {missing_slot!r} is ungrounded"
                            )
                        for required_slot in sorted(required_slots & observed_slots):
                            required_argument = arguments_by_slot[required_slot]
                            if required_argument.get("status") != "grounded" or not isinstance(
                                required_argument.get("selected_binding"), dict
                            ):
                                errors.append(
                                    f"grounding bindings[{index}]: coverage claims all required slots grounded, "
                                    f"but slot {required_slot!r} lacks grounded status and selected_binding"
                                )
        else:
            errors.append("grounding.node_bindings: expected array")
        if grounding.get("grounding_status") == "fully_grounded":
            for unbound_node_id in sorted(topology_node_ids - seen_binding_ids):
                errors.append(f"grounding: fully_grounded but topology node {unbound_node_id!r} has no binding")
            for node_id in sorted(topology_node_ids & seen_binding_ids):
                if binding_coverage_by_node.get(node_id) != "all_required_slots_grounded":
                    errors.append(
                        f"grounding: fully_grounded but topology node {node_id!r} does not claim "
                        "all_required_slots_grounded"
                    )
        oracle_summary = grounding.get("oracle_assistance_summary")
        if isinstance(oracle_summary, dict):
            if oracle_summary.get("used") is not bool(oracle_affected_node_ids):
                errors.append("grounding.oracle_assistance_summary.used disagrees with slot-level provenance")
            summary_nodes = oracle_summary.get("affected_node_ids")
            if (
                not isinstance(summary_nodes, list)
                or not all(isinstance(identifier, str) for identifier in summary_nodes)
                or set(summary_nodes) != oracle_affected_node_ids
            ):
                errors.append(
                    "grounding.oracle_assistance_summary.affected_node_ids disagrees with slot-level provenance"
                )
        elif oracle_affected_node_ids:
            errors.append("grounding: oracle-assisted slots require oracle_assistance_summary")
        checks.append("grounding_node_references")
        checks.extend(("grounding_binding_semantics", "oracle_assistance_consistency"))

    review_status = record.get("review_status")
    if isinstance(review_status, dict):
        status = first_string(review_status, ("state", "status", "label", "stage"))
        if review_status.get("gold_claimed") is True:
            errors.append("review_status: gold_claimed must remain false in v0.1")
    elif isinstance(review_status, str):
        status = review_status
    else:
        status = None
    if status and status.lower() in PROHIBITED_GOLD_STATUSES:
        errors.append(f"review_status: prohibited unsupported gold label {status!r}")
    if not status:
        warnings.append("review status is missing")
    human_review_count = review_status.get("human_review_count") if isinstance(review_status, dict) else None
    if isinstance(review_status, dict):
        reviewer_records = review_status.get("reviewer_records")
        if isinstance(reviewer_records, list):
            reviewer_ids = [
                item.get("reviewer_id")
                for item in reviewer_records
                if isinstance(item, dict) and isinstance(item.get("reviewer_id"), str)
            ]
            if len(reviewer_ids) != len(reviewer_records):
                errors.append("review_status: every reviewer record requires a reviewer_id")
            if len(reviewer_ids) != len(set(reviewer_ids)):
                errors.append("review_status: reviewer identities must be unique")
            if human_review_count != len(set(reviewer_ids)):
                errors.append("review_status: human_review_count disagrees with unique reviewer records")
        else:
            errors.append("review_status: reviewer_records must be an array")
        expected_review_ranges = {
            "llm_proposed": (0, 0),
            "deterministic_validation_only": (0, 0),
            "llm_assisted_pending_human": (0, 0),
            "human_single_review": (1, 1),
            "human_double_review_unadjudicated": (2, None),
            "adjudicated": (2, None),
        }
        if status in expected_review_ranges and isinstance(human_review_count, int):
            minimum, maximum = expected_review_ranges[status]
            if human_review_count < minimum or (maximum is not None and human_review_count > maximum):
                errors.append(f"review_status: state {status!r} disagrees with human_review_count")
        if status == "adjudicated" and not isinstance(review_status.get("adjudication"), dict):
            errors.append("review_status: adjudicated state requires an adjudication record")
    bundle_status = record.get("bundle_status")
    if isinstance(human_review_count, int) and human_review_count == 0 and bundle_status in {
        "human_reviewed",
        "adjudicated",
    }:
        errors.append(f"review_status: zero human reviews cannot support bundle_status={bundle_status!r}")
    if status in {"llm_proposed", "deterministic_validation_only", "llm_assisted_pending_human"} and bundle_status in {
        "human_reviewed",
        "adjudicated",
    }:
        errors.append(f"review_status: state {status!r} is inconsistent with bundle_status={bundle_status!r}")
    if status == "adjudicated" and bundle_status not in {"adjudicated", "ambiguous_preserved", "rejected"}:
        errors.append("review_status: adjudicated state requires an adjudicated/ambiguous/rejected bundle status")
    if isinstance(execution_graph, dict):
        semantic_assessment = execution_graph.get("semantic_plan_assessment")
        if semantic_assessment == "human_accepted" and not (
            isinstance(human_review_count, int) and human_review_count >= 1
        ):
            errors.append("execution_graph: human_accepted requires at least one recorded human review")
        if semantic_assessment == "adjudicated_accepted" and status != "adjudicated":
            errors.append("execution_graph: adjudicated_accepted requires review_status.state=adjudicated")
    checks.append("truthful_review_status")

    alternatives = record.get("alternative_plans")
    if alternatives is None:
        warnings.append("alternative_plans is absent")
    elif not isinstance(alternatives, list):
        errors.append("alternative_plans: expected array")
    else:
        alternative_ids: set[str] = set()
        for index, alternative in enumerate(alternatives):
            if not isinstance(alternative, dict):
                errors.append(f"alternative_plans[{index}]: expected object")
                continue
            alternative_id = first_string(alternative, ("alternative_plan_id", "id"))
            if alternative_id and alternative_id in alternative_ids:
                errors.append(f"alternative_plans: duplicate alternative_plan_id {alternative_id!r}")
            if alternative_id:
                alternative_ids.add(alternative_id)
            errors.extend(
                reference_list_errors(
                    alternative,
                    "satisfies_obligation_ids",
                    obligation_ids,
                    f"alternative_plans[{index}]",
                )
            )
            errors.extend(
                reference_list_errors(
                    alternative,
                    "satisfies_dependency_constraint_ids",
                    equivalence_constraint_ids,
                    f"alternative_plans[{index}]",
                )
            )
            assessment = alternative.get("assessment")
            semantic_validity = (
                assessment.get("semantic_validity") if isinstance(assessment, dict) else None
            )
            if semantic_validity in {"proposed_valid", "human_accepted", "adjudicated_accepted"}:
                satisfied_obligations = {
                    identifier
                    for identifier in alternative.get("satisfies_obligation_ids", [])
                    if isinstance(identifier, str)
                } if isinstance(alternative.get("satisfies_obligation_ids"), list) else set()
                satisfied_constraints = {
                    identifier
                    for identifier in alternative.get("satisfies_dependency_constraint_ids", [])
                    if isinstance(identifier, str)
                } if isinstance(alternative.get("satisfies_dependency_constraint_ids"), list) else set()
                missing_obligations = sorted(
                    equivalence_required_obligation_ids - satisfied_obligations
                )
                missing_constraints = sorted(equivalence_constraint_ids - satisfied_constraints)
                if missing_obligations:
                    errors.append(
                        f"alternative_plans[{index}]: valid semantic claim omits required obligations "
                        f"{missing_obligations}"
                    )
                if missing_constraints:
                    errors.append(
                        f"alternative_plans[{index}]: valid semantic claim omits dependency constraints "
                        f"{missing_constraints}"
                    )
            alternative_abstract = alternative.get("abstract_topology")
            alternative_abstract_ids: set[str] = set()
            alternative_abstract_obligation_coverage: set[str] = set()
            if alternative_abstract is not None:
                check_forbidden_keys(
                    alternative_abstract,
                    EARLY_LAYER_FORBIDDEN_KEYS,
                    f"alternative_plans[{index}].abstract_topology",
                    errors,
                )
                errors.extend(
                    topology_errors(alternative_abstract, f"alternative_plans[{index}].abstract_topology")
                )
                alternative_abstract_nodes = (
                    alternative_abstract.get("nodes", [])
                    if isinstance(alternative_abstract, dict)
                    else []
                )
                if not isinstance(alternative_abstract_nodes, list):
                    alternative_abstract_nodes = []
                for node_index, node in enumerate(alternative_abstract_nodes):
                    if isinstance(node, dict):
                        alternative_node_id = first_string(node, ("node_id", "id"))
                        if alternative_node_id:
                            alternative_abstract_ids.add(alternative_node_id)
                        semantic_function = first_string(node, ("semantic_function", "function"))
                        if semantic_function not in ABSTRACT_SEMANTIC_FUNCTIONS:
                            errors.append(
                                f"alternative_plans[{index}].abstract_topology.nodes[{node_index}]: "
                                f"unknown semantic function {semantic_function!r}"
                            )
                        errors.extend(
                            reference_list_errors(
                                node,
                                "fulfills_obligation_ids",
                                obligation_ids,
                                f"alternative_plans[{index}].abstract_topology.nodes[{node_index}]",
                            )
                        )
                        if isinstance(node.get("fulfills_obligation_ids"), list):
                            alternative_abstract_obligation_coverage.update(
                                identifier
                                for identifier in node["fulfills_obligation_ids"]
                                if isinstance(identifier, str)
                            )
                        errors.extend(
                            reference_list_errors(
                                node,
                                "realizes_skeleton_requirement_ids",
                                skeleton_requirement_ids,
                                f"alternative_plans[{index}].abstract_topology.nodes[{node_index}]",
                            )
                        )
                        for variable_field in ("input_semantic_variable_ids", "output_semantic_variable_ids"):
                            errors.extend(
                                reference_list_errors(
                                    node,
                                    variable_field,
                                    skeleton_variable_ids | obligation_output_role_ids,
                                    f"alternative_plans[{index}].abstract_topology.nodes[{node_index}]",
                                )
                            )
                alternative_constraints = (
                    alternative_abstract.get("required_dependency_constraints", [])
                    if isinstance(alternative_abstract, dict)
                    else []
                )
                alternative_constraint_signatures: dict[
                    str, tuple[tuple[str, ...], str | None, str | None]
                ] = {}
                if isinstance(alternative_constraints, list):
                    for constraint_index, constraint in enumerate(alternative_constraints):
                        if not isinstance(constraint, dict):
                            errors.append(
                                f"alternative_plans[{index}].abstract_topology.required_dependency_constraints"
                                f"[{constraint_index}]: expected object"
                            )
                            continue
                        constraint_id = first_string(constraint, ("constraint_id", "id"))
                        if constraint_id in alternative_constraint_signatures:
                            errors.append(
                                f"alternative_plans[{index}].abstract_topology: duplicate constraint {constraint_id!r}"
                            )
                        errors.extend(
                            reference_list_errors(
                                constraint,
                                "predecessor_obligation_ids",
                                obligation_ids,
                                f"alternative_plans[{index}].abstract_topology.required_dependency_constraints"
                                f"[{constraint_index}]",
                            )
                        )
                        successor = constraint.get("successor_obligation_id")
                        if isinstance(successor, str) and successor not in obligation_ids:
                            errors.append(
                                f"alternative_plans[{index}].abstract_topology constraint has unknown "
                                f"successor {successor!r}"
                            )
                        if constraint_id:
                            predecessors = constraint.get("predecessor_obligation_ids", [])
                            alternative_constraint_signatures[constraint_id] = (
                                tuple(sorted(predecessors)) if isinstance(predecessors, list) else (),
                                successor if isinstance(successor, str) else None,
                                constraint.get("dependency_kind")
                                if isinstance(constraint.get("dependency_kind"), str)
                                else None,
                            )
                    if alternative_constraint_signatures != abstract_constraint_signatures:
                        errors.append(
                            f"alternative_plans[{index}].abstract_topology dependency constraints do not preserve "
                            "the representative plan invariants"
                        )
                else:
                    errors.append(
                        f"alternative_plans[{index}].abstract_topology.required_dependency_constraints: expected array"
                    )
                if semantic_validity in {"proposed_valid", "human_accepted", "adjudicated_accepted"}:
                    missing_abstract_obligations = sorted(
                        equivalence_required_obligation_ids - alternative_abstract_obligation_coverage
                    )
                    if missing_abstract_obligations:
                        errors.append(
                            f"alternative_plans[{index}].abstract_topology: valid claim does not fulfill "
                            f"required obligations {missing_abstract_obligations}"
                        )
            alternative_operator = alternative.get("operator_topology")
            if alternative_operator is not None:
                check_forbidden_keys(
                    alternative_operator,
                    TOPOLOGY_FORBIDDEN_KEYS,
                    f"alternative_plans[{index}].operator_topology",
                    errors,
                )
                errors.extend(
                    topology_errors(
                        alternative_operator,
                        f"alternative_plans[{index}].operator_topology",
                        allowed_operators,
                    )
                )
                if isinstance(alternative_operator, dict):
                    alternative_vocabulary = alternative_operator.get("operator_vocabulary")
                    if isinstance(alternative_vocabulary, dict):
                        if vocabulary_version and alternative_vocabulary.get(
                            "vocabulary_version"
                        ) != vocabulary_version:
                            errors.append(
                                f"alternative_plans[{index}].operator_topology: vocabulary_version "
                                "does not match the validator vocabulary"
                            )
                        if vocabulary_granularity and alternative_vocabulary.get(
                            "granularity"
                        ) != vocabulary_granularity:
                            errors.append(
                                f"alternative_plans[{index}].operator_topology: granularity does not "
                                "match the validator vocabulary"
                            )
                    elif semantic_validity in {
                        "proposed_valid",
                        "human_accepted",
                        "adjudicated_accepted",
                    }:
                        errors.append(
                            f"alternative_plans[{index}].operator_topology: a valid claim requires an "
                            "operator_vocabulary declaration"
                        )
                alternative_operator_nodes = (
                    alternative_operator.get("nodes", []) if isinstance(alternative_operator, dict) else []
                )
                if not isinstance(alternative_operator_nodes, list):
                    alternative_operator_nodes = []
                alternative_node_ids: set[str] = set()
                alternative_operator_by_id: dict[str, str | None] = {}
                alternative_slots_by_id: dict[str, dict[str, dict[str, Any]]] = {}
                alternative_operator_obligation_coverage: set[str] = set()
                alternative_operator_abstract_coverage: set[str] = set()
                for node_index, node in enumerate(alternative_operator_nodes):
                    if not isinstance(node, dict):
                        continue
                    node_id = first_string(node, ("node_id", "id"))
                    operator_name = first_string(node, ("operator", "operation"))
                    if node_id:
                        alternative_node_ids.add(node_id)
                        alternative_operator_by_id[node_id] = operator_name
                        raw_slots = node.get("argument_slots", [])
                        alternative_slots_by_id[node_id] = {
                            slot_name: slot
                            for slot in raw_slots
                            if isinstance(slot, dict)
                            if (slot_name := first_string(slot, ("slot_name", "name"))) is not None
                        } if isinstance(raw_slots, list) else {}
                    errors.extend(
                        reference_list_errors(
                            node,
                            "fulfills_obligation_ids",
                            obligation_ids,
                            f"alternative_plans[{index}].operator_topology.nodes[{node_index}]",
                        )
                    )
                    if isinstance(node.get("fulfills_obligation_ids"), list):
                        alternative_operator_obligation_coverage.update(
                            identifier
                            for identifier in node["fulfills_obligation_ids"]
                            if isinstance(identifier, str)
                        )
                    if isinstance(node.get("realizes_abstract_node_ids"), list):
                        alternative_operator_abstract_coverage.update(
                            identifier
                            for identifier in node["realizes_abstract_node_ids"]
                            if isinstance(identifier, str)
                        )
                    semantic_role_registry = (
                        skeleton_variable_ids | skeleton_requirement_ids | obligation_output_role_ids
                    )
                    input_slots_for_refs = node.get("input_slots", [])
                    if isinstance(input_slots_for_refs, list):
                        for slot_index, slot in enumerate(input_slots_for_refs):
                            source = slot.get("source") if isinstance(slot, dict) else None
                            if isinstance(source, dict) and source.get("source_kind") == "semantic_input":
                                semantic_variable_id = source.get("semantic_variable_id")
                                if semantic_variable_id not in semantic_role_registry:
                                    errors.append(
                                        f"alternative_plans[{index}].operator_topology.nodes[{node_index}]."
                                        f"input_slots[{slot_index}]: unknown semantic_variable_id "
                                        f"{semantic_variable_id!r}"
                                    )
                    output_slots_for_refs = node.get("output_slots", [])
                    if isinstance(output_slots_for_refs, list):
                        for slot_index, slot in enumerate(output_slots_for_refs):
                            if isinstance(slot, dict):
                                errors.extend(
                                    reference_list_errors(
                                        slot,
                                        "semantic_variable_ids",
                                        semantic_role_registry,
                                        f"alternative_plans[{index}].operator_topology.nodes[{node_index}]."
                                        f"output_slots[{slot_index}]",
                                    )
                                )
                    argument_slots_for_refs = node.get("argument_slots", [])
                    if isinstance(argument_slots_for_refs, list):
                        for slot_index, slot in enumerate(argument_slots_for_refs):
                            semantic_role_ref = (
                                slot.get("semantic_role_ref") if isinstance(slot, dict) else None
                            )
                            if (
                                isinstance(semantic_role_ref, str)
                                and semantic_role_ref not in semantic_role_registry
                            ):
                                errors.append(
                                    f"alternative_plans[{index}].operator_topology.nodes[{node_index}]."
                                    f"argument_slots[{slot_index}]: unknown semantic_role_ref "
                                    f"{semantic_role_ref!r}"
                                )
                    definition = operator_definitions.get(operator_name or "")
                    if definition:
                        for direction, node_key, type_key in (
                            ("input", "input_slots", "expected_type"),
                            ("output", "output_slots", "declared_type"),
                        ):
                            expected_ports = port_definitions(definition, direction)
                            declared_ports = node.get(node_key, [])
                            observed_ports = {
                                first_string(port, ("slot_name", "name")): port
                                for port in declared_ports
                                if isinstance(port, dict) and first_string(port, ("slot_name", "name"))
                            } if isinstance(declared_ports, list) else {}
                            if set(observed_ports) != set(expected_ports):
                                errors.append(
                                    f"alternative_plans[{index}].operator_topology.nodes[{node_index}]."
                                    f"{node_key}: ports do not exactly match {operator_name} vocabulary contract"
                                )
                            for port_name in set(observed_ports) & set(expected_ports):
                                if observed_ports[port_name].get(type_key) != expected_ports[port_name].get("type"):
                                    errors.append(
                                        f"alternative_plans[{index}].operator_topology.nodes[{node_index}] "
                                        f"{direction} port {port_name!r}: type does not match vocabulary"
                                    )
                                if observed_ports[port_name].get("cardinality") != expected_ports[port_name].get(
                                    "cardinality"
                                ):
                                    errors.append(
                                        f"alternative_plans[{index}].operator_topology.nodes[{node_index}] "
                                        f"{direction} port {port_name!r}: cardinality does not match vocabulary"
                                    )
                        expected_arguments = {
                            item.get("name"): item
                            for item in definition.get("argument_slots", [])
                            if isinstance(item, dict) and isinstance(item.get("name"), str)
                        } if isinstance(definition.get("argument_slots"), list) else {}
                        observed_arguments = alternative_slots_by_id.get(node_id or "", {})
                        if set(observed_arguments) != set(expected_arguments):
                            errors.append(
                                f"alternative_plans[{index}].operator_topology.nodes[{node_index}]."
                                "argument_slots: slots do not exactly match vocabulary contract"
                            )
                        for slot_name in set(observed_arguments) & set(expected_arguments):
                            if observed_arguments[slot_name].get("expected_binding_kind") != expected_arguments[
                                slot_name
                            ].get("binding_kind") or observed_arguments[slot_name].get("required") is not expected_arguments[
                                slot_name
                            ].get("required"):
                                errors.append(
                                    f"alternative_plans[{index}].operator_topology.nodes[{node_index}] "
                                    f"argument slot {slot_name!r}: contract differs from vocabulary"
                                )
                    errors.extend(
                        reference_list_errors(
                            node,
                            "realizes_abstract_node_ids",
                            alternative_abstract_ids or abstract_node_ids,
                            f"alternative_plans[{index}].operator_topology.nodes[{node_index}]",
                        )
                    )

                if semantic_validity in {"proposed_valid", "human_accepted", "adjudicated_accepted"}:
                    missing_operator_obligations = sorted(
                        equivalence_required_obligation_ids - alternative_operator_obligation_coverage
                    )
                    if missing_operator_obligations:
                        errors.append(
                            f"alternative_plans[{index}].operator_topology: valid claim does not realize "
                            f"required obligations {missing_operator_obligations}"
                        )
                    if alternative_abstract_ids:
                        missing_abstract_nodes = sorted(
                            alternative_abstract_ids - alternative_operator_abstract_coverage
                        )
                        if missing_abstract_nodes:
                            errors.append(
                                f"alternative_plans[{index}].operator_topology: valid claim does not realize "
                                f"abstract nodes {missing_abstract_nodes}"
                            )

                alternative_nodes_by_id = {
                    first_string(node, ("node_id", "id")): node
                    for node in alternative_operator_nodes
                    if isinstance(node, dict) and first_string(node, ("node_id", "id"))
                }
                for node_index, node in enumerate(alternative_operator_nodes):
                    if not isinstance(node, dict):
                        continue
                    dependencies = {
                        dependency
                        for dependency in node.get("depends_on", [])
                        if isinstance(dependency, str)
                    } if isinstance(node.get("depends_on"), list) else set()
                    input_slots = node.get("input_slots", [])
                    if not isinstance(input_slots, list):
                        continue
                    for slot_index, slot in enumerate(input_slots):
                        source = slot.get("source") if isinstance(slot, dict) else None
                        if not isinstance(source, dict) or source.get("source_kind") != "upstream_output":
                            continue
                        label = (
                            f"alternative_plans[{index}].operator_topology.nodes[{node_index}]."
                            f"input_slots[{slot_index}]"
                        )
                        source_node_id = source.get("source_node_id")
                        source_node = alternative_nodes_by_id.get(source_node_id)
                        if source_node is None:
                            errors.append(f"{label}: unknown upstream source node {source_node_id!r}")
                            continue
                        if source_node_id not in dependencies:
                            errors.append(f"{label}: upstream source is not a declared dependency")
                        source_ports = {
                            first_string(port, ("slot_name", "name")): port
                            for port in source_node.get("output_slots", [])
                            if isinstance(port, dict) and first_string(port, ("slot_name", "name"))
                        } if isinstance(source_node.get("output_slots"), list) else {}
                        source_port = source_ports.get(source.get("source_port"))
                        if source_port is None:
                            errors.append(f"{label}: upstream source port does not exist")
                        else:
                            if not compatible_types(source_port.get("declared_type"), slot.get("expected_type")):
                                errors.append(f"{label}: upstream type is incompatible")
                            if not compatible_cardinalities(
                                source_port.get("cardinality"),
                                slot.get("cardinality"),
                                slot.get("expected_type"),
                            ):
                                errors.append(f"{label}: upstream cardinality is incompatible")

                alternative_grounding = alternative.get("grounding")
                if isinstance(alternative_grounding, dict):
                    if isinstance(alternative_operator, dict) and alternative_grounding.get(
                        "operator_topology_id"
                    ) != alternative_operator.get("topology_id"):
                        errors.append(
                            f"alternative_plans[{index}].grounding.operator_topology_id does not match topology"
                        )
                    seen_alternative_bindings: set[str] = set()
                    alternative_binding_coverage: dict[str, Any] = {}
                    alternative_oracle_affected_node_ids: set[str] = set()
                    raw_bindings = alternative_grounding.get("node_bindings", [])
                    if isinstance(raw_bindings, list):
                        for binding_index, binding in enumerate(raw_bindings):
                            if not isinstance(binding, dict):
                                continue
                            node_id = first_string(binding, ("topology_node_id", "node_id", "id"))
                            label = f"alternative_plans[{index}].grounding.node_bindings[{binding_index}]"
                            if not node_id or node_id not in alternative_node_ids:
                                errors.append(f"{label}: unknown topology node {node_id!r}")
                                continue
                            if node_id in seen_alternative_bindings:
                                errors.append(f"{label}: duplicate topology-node binding")
                            seen_alternative_bindings.add(node_id)
                            alternative_binding_coverage[node_id] = binding.get("coverage_status")
                            if first_string(binding, ("operator",)) != alternative_operator_by_id.get(node_id):
                                errors.append(f"{label}: operator does not match topology")
                            topology_slots = alternative_slots_by_id.get(node_id, {})
                            argument_groundings = binding.get("argument_groundings", [])
                            if isinstance(argument_groundings, list):
                                arguments_by_slot: dict[str, dict[str, Any]] = {}
                                for argument_index, argument in enumerate(argument_groundings):
                                    if not isinstance(argument, dict):
                                        continue
                                    slot_name = first_string(argument, ("slot_name", "name"))
                                    if slot_name:
                                        arguments_by_slot[slot_name] = argument
                                    topology_slot = topology_slots.get(slot_name or "")
                                    argument_label = f"{label}.argument_groundings[{argument_index}]"
                                    if topology_slot is None:
                                        errors.append(f"{argument_label}: unknown topology argument slot {slot_name!r}")
                                        continue
                                    expected_kind = topology_slot.get("expected_binding_kind")
                                    if argument.get("expected_binding_kind") != expected_kind:
                                        errors.append(f"{argument_label}: binding kind does not match topology")
                                    if argument.get("semantic_role_ref") != topology_slot.get("semantic_role_ref"):
                                        errors.append(f"{argument_label}: semantic role does not match topology")
                                    oracle_flag = argument.get("oracle_assistance_used") is True
                                    oracle_provenance = (
                                        argument.get("selection_provenance") == "oracle_annotation"
                                    )
                                    if oracle_flag or oracle_provenance:
                                        alternative_oracle_affected_node_ids.add(node_id)
                                    if oracle_flag != oracle_provenance:
                                        errors.append(
                                            f"{argument_label}: oracle provenance and flag disagree"
                                        )
                                    selected_binding = argument.get("selected_binding")
                                    if isinstance(selected_binding, dict) and selected_binding.get(
                                        "binding_type"
                                    ) != expected_kind:
                                        errors.append(f"{argument_label}: selected binding type does not match slot")
                                    errors.extend(
                                        concrete_binding_errors(
                                            selected_binding,
                                            f"{argument_label}.selected_binding",
                                        )
                                    )
                                    candidate_bindings = argument.get("candidate_bindings", [])
                                    if isinstance(candidate_bindings, list):
                                        selected_candidates: list[dict[str, Any]] = []
                                        for candidate_index, candidate in enumerate(candidate_bindings):
                                            concrete = (
                                                candidate.get("binding")
                                                if isinstance(candidate, dict)
                                                else None
                                            )
                                            if (
                                                isinstance(candidate, dict)
                                                and candidate.get("selection_status") == "selected"
                                            ):
                                                selected_candidates.append(candidate)
                                            if (
                                                isinstance(concrete, dict)
                                                and concrete.get("binding_type") != expected_kind
                                            ):
                                                errors.append(
                                                    f"{argument_label}.candidate_bindings[{candidate_index}]: "
                                                    "binding type does not match slot"
                                                )
                                            errors.extend(
                                                concrete_binding_errors(
                                                    concrete,
                                                    f"{argument_label}.candidate_bindings[{candidate_index}]",
                                                )
                                            )
                                        if len(selected_candidates) > 1:
                                            errors.append(
                                                f"{argument_label}: multiple candidates are selected"
                                            )
                                        if selected_candidates and not isinstance(selected_binding, dict):
                                            errors.append(
                                                f"{argument_label}: selected candidate lacks selected_binding"
                                            )
                                        if isinstance(selected_binding, dict) and candidate_bindings:
                                            if len(selected_candidates) != 1:
                                                errors.append(
                                                    f"{argument_label}: selected_binding requires exactly one "
                                                    "selected candidate"
                                                )
                                            elif selected_candidates[0].get("binding") != selected_binding:
                                                errors.append(
                                                    f"{argument_label}: selected candidate and selected_binding differ"
                                                )
                                    if (
                                        argument.get("status") == "grounded"
                                        and not isinstance(selected_binding, dict)
                                    ):
                                        errors.append(
                                            f"{argument_label}: grounded status requires selected_binding"
                                        )
                                if binding.get("coverage_status") == "all_required_slots_grounded":
                                    required_slots = {
                                        name
                                        for name, slot in topology_slots.items()
                                        if slot.get("required") is True
                                    }
                                    for required_slot in sorted(required_slots):
                                        argument = arguments_by_slot.get(required_slot)
                                        if (
                                            not isinstance(argument, dict)
                                            or argument.get("status") != "grounded"
                                            or not isinstance(argument.get("selected_binding"), dict)
                                        ):
                                            errors.append(
                                                f"{label}: required slot {required_slot!r} is not fully grounded"
                                            )
                    else:
                        errors.append(f"alternative_plans[{index}].grounding.node_bindings: expected array")
                    if alternative_grounding.get("grounding_status") == "fully_grounded":
                        if seen_alternative_bindings != alternative_node_ids:
                            errors.append(
                                f"alternative_plans[{index}].grounding: fully_grounded node coverage is incomplete"
                            )
                        for node_id in sorted(alternative_node_ids & seen_alternative_bindings):
                            if alternative_binding_coverage.get(node_id) != "all_required_slots_grounded":
                                errors.append(
                                    f"alternative_plans[{index}].grounding: node {node_id!r} is not fully grounded"
                                )
                    alternative_oracle_summary = alternative_grounding.get("oracle_assistance_summary")
                    if isinstance(alternative_oracle_summary, dict):
                        if alternative_oracle_summary.get("used") is not bool(
                            alternative_oracle_affected_node_ids
                        ):
                            errors.append(
                                f"alternative_plans[{index}].grounding.oracle_assistance_summary.used "
                                "disagrees with slot-level provenance"
                            )
                        affected_nodes = alternative_oracle_summary.get("affected_node_ids")
                        if (
                            not isinstance(affected_nodes, list)
                            or not all(isinstance(identifier, str) for identifier in affected_nodes)
                            or set(affected_nodes) != alternative_oracle_affected_node_ids
                        ):
                            errors.append(
                                f"alternative_plans[{index}].grounding.oracle_assistance_summary."
                                "affected_node_ids disagrees with slot-level provenance"
                            )
                    elif alternative_oracle_affected_node_ids:
                        errors.append(
                            f"alternative_plans[{index}].grounding: oracle-assisted slots require "
                            "oracle_assistance_summary"
                        )
    checks.append("alternative_plan_dependencies")

    leakage_controls = record.get("leakage_controls")
    if isinstance(leakage_controls, dict):
        if leakage_controls.get("early_layer_answer_exposure") is not False:
            errors.append("leakage_controls: early_layer_answer_exposure must be false")
        view_contracts = leakage_controls.get("prediction_view_contracts", [])
        if isinstance(view_contracts, list):
            tasks = [
                item.get("task")
                for item in view_contracts
                if isinstance(item, dict) and isinstance(item.get("task"), str)
            ]
            required_tasks = set(PREDICTION_VIEW_POLICIES)
            if len(tasks) != len(set(tasks)):
                errors.append("leakage_controls: duplicate prediction-view task contracts")
            for task in sorted(required_tasks - set(tasks)):
                errors.append(f"leakage_controls: missing prediction-view contract {task!r}")
            for index, contract in enumerate(view_contracts):
                label = f"leakage_controls.prediction_view_contracts[{index}]"
                if not isinstance(contract, dict):
                    errors.append(f"{label}: expected object")
                    continue
                task = contract.get("task")
                if not isinstance(task, str):
                    errors.append(f"{label}: task must be a string")
                    continue
                policy = PREDICTION_VIEW_POLICIES.get(task)
                if policy is None:
                    errors.append(f"{label}: unknown task {task!r}")
                    continue
                path_groups: dict[str, list[str]] = {}
                for field in ("input_paths", "target_paths", "prohibited_input_paths"):
                    values = contract.get(field)
                    if not isinstance(values, list) or not values:
                        errors.append(f"{label}.{field}: expected non-empty array")
                        path_groups[field] = []
                        continue
                    paths = [value for value in values if isinstance(value, str)]
                    if len(paths) != len(values) or any(not value.startswith("/") for value in paths):
                        errors.append(f"{label}.{field}: expected JSON-pointer strings")
                    if len(paths) != len(set(paths)):
                        errors.append(f"{label}.{field}: duplicate paths are forbidden")
                    path_groups[field] = paths

                inputs = path_groups.get("input_paths", [])
                targets = path_groups.get("target_paths", [])
                prohibited = path_groups.get("prohibited_input_paths", [])
                for path in inputs:
                    if not pointer_is_within(path, policy["allowed_inputs"]):
                        errors.append(f"{label}.input_paths: path {path!r} is not allowed for task {task!r}")
                for required in sorted(policy["required_inputs"]):
                    if not any(pointer_is_within(path, {required}) for path in inputs):
                        errors.append(f"{label}.input_paths: required input root {required!r} is missing")
                for path in targets:
                    if not pointer_is_within(path, policy["allowed_targets"]):
                        errors.append(f"{label}.target_paths: path {path!r} is not allowed for task {task!r}")
                for required in sorted(policy["required_targets"]):
                    if not any(pointer_is_within(path, {required}) for path in targets):
                        errors.append(f"{label}.target_paths: required target root {required!r} is missing")
                missing_prohibited = policy["required_prohibited"] - set(prohibited)
                for path in sorted(missing_prohibited):
                    errors.append(f"{label}.prohibited_input_paths: required root {path!r} is missing")
                for input_path in inputs:
                    for prohibited_path in prohibited:
                        if pointers_overlap(input_path, prohibited_path):
                            errors.append(
                                f"{label}: input path {input_path!r} overlaps prohibited path {prohibited_path!r}"
                            )
                for input_path in inputs:
                    for target_path in targets:
                        if pointers_overlap(input_path, target_path):
                            errors.append(
                                f"{label}: input path {input_path!r} overlaps target path {target_path!r}"
                            )
        else:
            errors.append("leakage_controls.prediction_view_contracts: expected array")
        boundary_audits = leakage_controls.get("boundary_audits", [])
        if isinstance(boundary_audits, list):
            boundaries = [
                item.get("boundary")
                for item in boundary_audits
                if isinstance(item, dict) and isinstance(item.get("boundary"), str)
            ]
            required_boundaries = set(STANDARD_LEAKAGE_BOUNDARIES)
            # The schema keeps this sixth record in every bundle so absence cannot
            # be confused with a passed locked-eval isolation audit.
            required_boundaries.add("locked_eval_isolation")
            if record.get("dataset_role") == "locked_eval":
                status_boundaries = required_boundaries
            else:
                status_boundaries = STANDARD_LEAKAGE_BOUNDARIES
            if len(boundaries) != len(set(boundaries)):
                errors.append("leakage_controls: duplicate boundary audit records")
            for boundary in sorted(required_boundaries - set(boundaries)):
                errors.append(f"leakage_controls: missing boundary audit {boundary!r}")
            audit_by_boundary = {
                item.get("boundary"): item
                for item in boundary_audits
                if isinstance(item, dict) and isinstance(item.get("boundary"), str)
            }
            validated_statuses = {
                "structurally_validated",
                "pending_human_review",
                "human_reviewed",
                "adjudicated",
                "ambiguous_preserved",
            }
            for boundary, audit in audit_by_boundary.items():
                label = f"leakage_controls.boundary_audits[{boundary!r}]"
                status_value = audit.get("status")
                violations = audit.get("violations")
                if status_value not in {"not_run", "passed", "failed"}:
                    errors.append(f"{label}: invalid status {status_value!r}")
                if not isinstance(violations, list):
                    errors.append(f"{label}.violations: expected array")
                    violations = []
                if status_value == "passed" and violations:
                    errors.append(f"{label}: passed audit must have no violations")
                if status_value == "passed":
                    errors.extend(
                        leakage_audit_artifact_errors(boundary, audit, Path.cwd(), record)
                    )
                if status_value == "failed" and not violations:
                    errors.append(f"{label}: failed audit must record at least one violation")
                if status_value in {"passed", "failed"}:
                    if not isinstance(audit.get("checked_at"), str) or not audit.get("checked_at"):
                        errors.append(f"{label}: checked_at is required for a completed audit")
                    if not isinstance(audit.get("checker_id"), str) or not audit.get("checker_id"):
                        errors.append(f"{label}: checker_id is required for a completed audit")
                if status_value == "failed" and bundle_status not in {"blocked", "rejected"}:
                    errors.append(f"{label}: failed audit requires bundle_status blocked or rejected")
                if (
                    boundary in status_boundaries
                    and status_value == "not_run"
                    and bundle_status not in {"proposal", "blocked", "rejected"}
                ):
                    errors.append(f"{label}: unrun audit cannot support bundle_status {bundle_status!r}")
            if bundle_status in validated_statuses:
                for boundary in sorted(status_boundaries):
                    audit = audit_by_boundary.get(boundary)
                    if not isinstance(audit, dict) or audit.get("status") != "passed" or audit.get("violations"):
                        errors.append(
                            f"leakage_controls: bundle_status {bundle_status!r} requires passed audit {boundary!r}"
                        )
        else:
            errors.append("leakage_controls.boundary_audits: expected array")
        checks.append("leakage_control_completeness")
    elif leakage_controls is not None:
        errors.append("leakage_controls: expected object")
    else:
        warnings.append("leakage_controls is absent; full schema validation is required before release")

    locked_controls = record.get("locked_eval_controls")
    if record.get("dataset_role") == "locked_eval":
        if not isinstance(locked_controls, dict):
            errors.append("locked_eval: locked_eval_controls object is required")
        else:
            for tuning_key in (
                "prompt_tuning_allowed",
                "rubric_tuning_allowed",
                "operator_vocabulary_tuning_allowed",
            ):
                if locked_controls.get(tuning_key) is not False:
                    errors.append(f"locked_eval: {tuning_key} must be false")
            for check_key in ("split_membership_verified", "historical_exposure_checked"):
                if locked_controls.get(check_key) != "passed":
                    errors.append(f"locked_eval: {check_key} must be 'passed'")
            for artifact_key in (
                "split_manifest_artifact",
                "historical_exposure_manifest_artifact",
            ):
                if not isinstance(locked_controls.get(artifact_key), dict):
                    errors.append(f"locked_eval: {artifact_key} is required")
            errors.extend(locked_eval_membership_errors(record, locked_controls, Path.cwd()))
        checks.append("locked_eval_isolation")

    return errors, warnings, checks


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    outputs = {"checks_output": args.checks_output}
    collisions = output_path_collision_errors(
        {
            "annotations": args.annotations,
            "schema": args.schema,
            "operator_vocabulary": args.operator_vocabulary,
        },
        outputs,
    )
    collisions.extend(historical_output_collision_errors(outputs, project_root))
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    if not args.annotations.is_file():
        raise FileNotFoundError(args.annotations)
    if not args.operator_vocabulary.is_file():
        raise FileNotFoundError(args.operator_vocabulary)

    try:
        schema = None if args.structural_only else read_json(args.schema)
        vocabulary = read_json(args.operator_vocabulary)
    except (OSError, ValueError) as exc:
        print(f"invalid validator input JSON: {exc}", file=sys.stderr)
        return 2
    allowed_operators = vocabulary_names(vocabulary)
    operator_definitions = vocabulary_definitions(vocabulary)
    vocabulary_version = first_string(vocabulary, ("vocabulary_version",))
    vocabulary_granularity = first_string(vocabulary, ("granularity",))
    if not allowed_operators:
        print("operator vocabulary contains no readable operator names", file=sys.stderr)
        return 2

    validation_context = {
        "validator_version": VALIDATOR_VERSION,
        "annotations_artifact_sha256": sha256_file(args.annotations),
        "schema_artifact_sha256": sha256_file(args.schema) if args.schema.is_file() else None,
        "operator_vocabulary_artifact_sha256": sha256_file(args.operator_vocabulary),
        "operator_vocabulary_version": vocabulary_version,
        "operator_vocabulary_granularity": vocabulary_granularity,
        "validation_mode": "structural_only" if args.structural_only else "draft_2020_12_plus_structural",
        "code_commit": git_commit_identity(project_root),
    }

    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    try:
        for index, record in enumerate(iter_json_records(args.annotations)):
            question_id = first_string(record, ("question_id", "qid", "id")) or f"__record_{index}"
            if question_id in seen_ids:
                duplicate_ids.add(question_id)
            seen_ids.add(question_id)
            try:
                errors, warnings, checks = validate_record(
                    record,
                    allowed_operators,
                    operator_definitions,
                    vocabulary_version,
                    vocabulary_granularity,
                    schema,
                    args.schema,
                )
            except Exception as exc:  # fail the record without losing the corpus audit artifact
                errors = [
                    f"validator_internal_error:{type(exc).__name__}: {exc}"
                ]
                warnings = []
                checks = ["internal_error_captured"]
            results.append(
                {
                    "question_id": question_id,
                    "validator_version": VALIDATOR_VERSION,
                    "annotation_canonical_sha256": canonical_json_sha256(record),
                    "validation_context": validation_context,
                    "status": "fail" if errors or (args.fail_on_warning and warnings) else "pass",
                    "errors": errors,
                    "warnings": warnings,
                    "checks_run": sorted(set(checks)),
                }
            )
    except (OSError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2 if not isinstance(exc, RuntimeError) else 3

    if not results and not args.allow_empty:
        print("refusing to validate an empty annotation input", file=sys.stderr)
        return 2

    if duplicate_ids:
        for result in results:
            if result["question_id"] in duplicate_ids:
                result["errors"].append("corpus: duplicate question_id")
                result["status"] = "fail"

    write_jsonl(args.checks_output, results)
    failures = sum(result["status"] == "fail" for result in results)
    warning_count = sum(len(result["warnings"]) for result in results)
    print(
        json.dumps(
            {
                "records": len(results),
                "failures": failures,
                "warnings": warning_count,
                "checks_output": args.checks_output.as_posix(),
            },
            sort_keys=True,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
