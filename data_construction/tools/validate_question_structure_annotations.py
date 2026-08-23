#!/usr/bin/env python3
"""Validate a blind question-structure packet and optional raw annotation array."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import build_question_structure_annotation_packet as packet_builder
from _common import (
    canonical_json_sha256,
    git_tracked_commit_identity,
    historical_output_collision_errors,
    implementation_artifact_set_sha256,
    jsonl_file_bytes,
    output_path_collision_errors,
    read_json,
    sha256_bytes,
    sha256_file,
    write_output_batch,
)


VALIDATOR_VERSION = "question_structure_annotation_validator_v0_1"
VALIDATION_RECORD_VERSION = "question_structure_annotation_validation_record_v0_1"
VALIDATION_MODE = (
    "exact_packet_render_plus_draft_2020_12_plus_hash_cue_reference_dag_root_sink_v0_1"
)
EXPECTED_BATCH_QUESTION_COUNT = 10
PSEUDONYM_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
UTC_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_LATER_LAYER_KEYS = {
    "answer",
    "answers",
    "answer_node",
    "answer_span",
    "answer_text",
    "candidate_operator_graph",
    "cell",
    "cells",
    "column_schema",
    "document_id",
    "document_ids",
    "document_text",
    "environment",
    "execution_graph",
    "execution_trace",
    "gold_answer",
    "gold_span",
    "grounding",
    "linked_document",
    "linked_documents",
    "llm_proposal",
    "model_proposal",
    "operator",
    "operator_topology",
    "oracle_document_id",
    "passage",
    "passages",
    "row",
    "rows",
    "table_id",
    "table_schema",
    "trace",
    "traces",
    "weak_answer_node",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "annotations",
        nargs="?",
        type=Path,
        help="Raw JSON array exported by one annotator; omit with --packet-only",
    )
    parser.add_argument(
        "--views",
        type=Path,
        default=Path("data_construction/pilot/question_only_semantic_views_v0_1.jsonl"),
    )
    parser.add_argument(
        "--views-manifest",
        type=Path,
        default=Path(
            "data_construction/pilot/question_only_semantic_views_manifest_v0_1.json"
        ),
    )
    parser.add_argument(
        "--study-plan",
        type=Path,
        default=Path("data_construction/pilot/question_structure_study_plan_v0_1.json"),
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("data_construction/schemas/question_structure_annotation_v0_1.json"),
    )
    parser.add_argument("--batch-id", required=True)
    parser.add_argument(
        "--packet",
        type=Path,
        default=Path(
            "data_construction/pilot/question_structure_review_packets/"
            "question_structure_calibration_batch_1_v0_1.html"
        ),
    )
    parser.add_argument(
        "--packet-manifest",
        type=Path,
        default=Path(
            "data_construction/pilot/question_structure_review_packets/"
            "question_structure_calibration_batch_1_v0_1_manifest.json"
        ),
    )
    parser.add_argument(
        "--packet-only",
        action="store_true",
        help="Validate exact packet/manifest rendering without reading or writing annotations",
    )
    parser.add_argument(
        "--checks-output",
        type=Path,
        help=(
            "Required outside --packet-only; write one deterministic JSONL check per raw "
            "record plus one batch-scope failure check when global contract errors exist"
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace a differing existing checks output only when explicitly authorized",
    )
    return parser.parse_args()


def canonical_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def forbidden_key_paths(value: Any, prefix: str = "$") -> list[str]:
    forbidden = {canonical_key(key) for key in FORBIDDEN_LATER_LAYER_KEYS}
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


def _git_commit_exists(project_root: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(project_root), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _git_blob_sha256(project_root: Path, commit: str, relative_path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "show", f"{commit}:{relative_path}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"artifact is absent from recorded builder commit: {relative_path}")
    return sha256_bytes(result.stdout)


def validator_implementation_paths(project_root: Path) -> list[Path]:
    return [
        project_root / "data_construction/schemas/question_only_semantic_view_v0_1.json",
        project_root / "data_construction/schemas/question_structure_annotation_v0_1.json",
        Path(__file__).with_name("_common.py"),
        Path(__file__).with_name("build_question_only_semantic_views.py"),
        Path(__file__).with_name("build_question_structure_annotation_packet.py"),
        Path(__file__),
    ]


def load_schema_validator(schema_path: Path) -> Any:
    try:
        import jsonschema
    except ImportError as exc:
        raise ValueError(
            "jsonschema is unavailable; exact Draft 2020-12 validation is required"
        ) from exc
    validator_class = getattr(jsonschema, "Draft202012Validator", None)
    if validator_class is None:
        raise ValueError("installed jsonschema has no Draft 2020-12 validator")
    schema = read_json(schema_path)
    if not isinstance(schema, dict) or schema.get("$id") != (
        "question_structure_annotation_v0_1.json"
    ):
        raise ValueError("raw annotation schema identity is unsupported")
    validator_class.check_schema(schema)
    return validator_class(schema, format_checker=jsonschema.FormatChecker())


def schema_error_messages(validator: Any, record: Any, label: str) -> list[str]:
    messages: list[str] = []
    for error in sorted(
        validator.iter_errors(record),
        key=lambda item: [str(component) for component in item.absolute_path],
    ):
        location = ".".join(str(component) for component in error.absolute_path) or "$"
        messages.append(f"{label}.{location}: {error.message}")
    return messages


def _validate_builder_commit_bindings(
    project_root: Path,
    manifest: dict[str, Any],
    inputs: dict[str, Path],
) -> str:
    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("packet manifest provenance must be an object")
    commit = provenance.get("code_commit")
    if (
        not isinstance(commit, str)
        or not re.fullmatch(r"[0-9a-f]{40}", commit)
        or not _git_commit_exists(project_root, commit)
    ):
        raise ValueError("packet manifest builder commit is unavailable")
    for label, path in inputs.items():
        try:
            relative = path.resolve().relative_to(project_root.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError(f"canonical packet input is outside the repository: {label}") from exc
        if _git_blob_sha256(project_root, commit, relative) != sha256_file(path):
            raise ValueError(
                f"packet input {label} differs from the blob at recorded builder commit"
            )
    for path in packet_builder.implementation_paths(project_root):
        relative = path.resolve().relative_to(project_root.resolve()).as_posix()
        if _git_blob_sha256(project_root, commit, relative) != sha256_file(path):
            raise ValueError(
                f"packet implementation differs from recorded builder commit: {relative}"
            )
    return commit


def validate_packet_contract(
    *,
    views_path: Path,
    views_manifest_path: Path,
    study_plan_path: Path,
    schema_path: Path,
    packet_path: Path,
    packet_manifest_path: Path,
    batch_id: str,
    project_root: Path,
) -> dict[str, Any]:
    view_schema_path = (
        project_root / "data_construction/schemas/question_only_semantic_view_v0_1.json"
    )
    inputs = {
        "views": views_path,
        "views_manifest": views_manifest_path,
        "study_plan": study_plan_path,
        "annotation_schema": schema_path,
        "view_schema": view_schema_path,
    }
    for label, path in {
        **inputs,
        "packet": packet_path,
        "packet_manifest": packet_manifest_path,
    }.items():
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"{label} must be an existing regular non-symlink file: {path}")

    views = list(packet_builder.iter_json_records(views_path))
    question_ids = packet_builder.validate_views(views)
    views_manifest = read_json(views_manifest_path)
    bindings = packet_builder.validate_views_manifest(
        views_manifest, views_path, views, question_ids, project_root
    )
    study_plan = read_json(study_plan_path)
    selected_ids = packet_builder.validate_study_plan(
        study_plan,
        batch_id,
        question_ids,
        bindings["questions_artifact"],
    )
    if len(selected_ids) != EXPECTED_BATCH_QUESTION_COUNT:
        raise ValueError("selected active batch must contain exactly 10 ordered questions")
    live_hashes = {label: sha256_file(path) for label, path in inputs.items()}
    payload = packet_builder.build_payload(
        views,
        selected_ids,
        batch_id,
        live_hashes["annotation_schema"],
    )
    payload_sha256 = canonical_json_sha256(payload)
    expected_packet_bytes = packet_builder.render_html(payload, payload_sha256).encode("utf-8")
    observed_packet_bytes = packet_path.read_bytes()
    if observed_packet_bytes != expected_packet_bytes:
        raise ValueError("packet HTML differs from the exact deterministic rendering")

    manifest = read_json(packet_manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("packet manifest must be a JSON object")
    builder_commit = _validate_builder_commit_bindings(project_root, manifest, inputs)
    expected_manifest = packet_builder.build_manifest(
        payload=payload,
        payload_sha256=payload_sha256,
        packet_bytes=expected_packet_bytes,
        batch_id=batch_id,
        selected_ids=selected_ids,
        inputs=inputs,
        live_hashes=live_hashes,
        output_path=packet_path,
        project_root=project_root,
        code_commit=builder_commit,
        paths=packet_builder.implementation_paths(project_root),
    )
    if manifest != expected_manifest:
        raise ValueError("packet manifest differs from the exact reconstructed contract")
    if sha256_file(packet_path) != manifest["packet_artifact"]["sha256"]:
        raise ValueError("packet HTML SHA-256 does not match its manifest")
    if payload_sha256 != manifest["packet_payload"]["sha256"]:
        raise ValueError("packet payload SHA-256 does not match its manifest")
    return {
        "views": views,
        "selected_ids": selected_ids,
        "selected_views": [
            view for view in views if view["question_id"] in set(selected_ids)
        ],
        "payload": payload,
        "payload_sha256": payload_sha256,
        "packet_sha256": sha256_file(packet_path),
        "packet_manifest_sha256": sha256_file(packet_manifest_path),
        "live_hashes": live_hashes,
        "builder_commit": builder_commit,
    }


def is_utc_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not UTC_PATTERN.fullmatch(value):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0


def cue_errors(value: Any, question: str, prefix: str = "annotation") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        if "source_cues" in value:
            cues = value.get("source_cues")
            implicit = value.get("implicit_rationale")
            if isinstance(cues, list):
                for index, cue in enumerate(cues):
                    if not isinstance(cue, str) or not cue or cue not in question:
                        errors.append(
                            f"{prefix}.source_cues[{index}] is not an exact case-sensitive question substring"
                        )
                if cues and implicit is not None:
                    errors.append(f"{prefix}.implicit_rationale must be null when cues exist")
                if not cues and (not isinstance(implicit, str) or not implicit.strip()):
                    errors.append(f"{prefix}.implicit_rationale is required when cues are empty")
        if "answer_shape_source_cues" in value:
            cues = value.get("answer_shape_source_cues")
            implicit = value.get("answer_shape_implicit_rationale")
            if isinstance(cues, list):
                for index, cue in enumerate(cues):
                    if not isinstance(cue, str) or not cue or cue not in question:
                        errors.append(
                            f"{prefix}.answer_shape_source_cues[{index}] is not an exact case-sensitive question substring"
                        )
                if cues and implicit is not None:
                    errors.append(
                        f"{prefix}.answer_shape_implicit_rationale must be null when cues exist"
                    )
                if not cues and (not isinstance(implicit, str) or not implicit.strip()):
                    errors.append(
                        f"{prefix}.answer_shape_implicit_rationale is required when cues are empty"
                    )
        for key, child in value.items():
            errors.extend(cue_errors(child, question, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(cue_errors(child, question, f"{prefix}[{index}]"))
    return errors


def dependency_errors(
    identifiers: list[Any],
    dependencies: list[Any],
    label: str,
) -> list[str]:
    errors: list[str] = []
    if any(not isinstance(identifier, str) for identifier in identifiers):
        return [f"{label}: every ID must be a string"]
    if len(set(identifiers)) != len(identifiers):
        errors.append(f"{label}: IDs are not unique")
    known = {identifier for identifier in identifiers if isinstance(identifier, str)}
    normalized: dict[str, list[str]] = {}
    for identifier, deps in zip(identifiers, dependencies):
        if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps):
            errors.append(f"{label}.{identifier}: depends_on must be a string array")
            normalized[identifier] = []
            continue
        normalized[identifier] = deps
        if identifier in deps:
            errors.append(f"{label}.{identifier}: self dependency")
        for dependency in deps:
            if dependency not in known:
                errors.append(f"{label}.{identifier}: missing dependency {dependency!r}")
    state: dict[str, int] = {}

    def visit(identifier: str) -> None:
        if state.get(identifier) == 1:
            errors.append(f"{label}: declared depends_on edges contain a cycle")
            return
        if state.get(identifier) == 2:
            return
        state[identifier] = 1
        for dependency in normalized.get(identifier, []):
            if dependency in known:
                visit(dependency)
        state[identifier] = 2

    for identifier in identifiers:
        visit(identifier)
    return sorted(set(errors))


def topology_errors(
    topology: Any,
    obligation_ids: set[str],
    label: str,
    *,
    require_full_obligation_coverage: bool = False,
) -> list[str]:
    if not isinstance(topology, dict):
        return []
    nodes = topology.get("nodes")
    if not isinstance(nodes, list):
        return [f"{label}.nodes must be an array"]
    identifiers = [node.get("node_id") for node in nodes if isinstance(node, dict)]
    dependencies = [node.get("depends_on") for node in nodes if isinstance(node, dict)]
    errors = dependency_errors(identifiers, dependencies, f"{label}.nodes")
    if len(identifiers) != len(nodes):
        errors.append(f"{label}.nodes contains a non-object")
        return sorted(set(errors))
    known = {identifier for identifier in identifiers if isinstance(identifier, str)}
    fulfilled_obligation_ids: set[str] = set()
    for index, node in enumerate(nodes):
        fulfills = node.get("fulfills_obligation_ids")
        if isinstance(fulfills, list):
            if not fulfills:
                errors.append(
                    f"{label}.nodes[{index}] must fulfill at least one declared obligation"
                )
            for obligation_id in fulfills:
                if not isinstance(obligation_id, str) or obligation_id not in obligation_ids:
                    errors.append(
                        f"{label}.nodes[{index}] references missing obligation {obligation_id!r}"
                    )
                else:
                    fulfilled_obligation_ids.add(obligation_id)
    if require_full_obligation_coverage and fulfilled_obligation_ids != obligation_ids:
        missing = sorted(obligation_ids - fulfilled_obligation_ids)
        errors.append(f"{label} does not cover every declared obligation: missing={missing!r}")
    roots = [
        node["node_id"]
        for node in nodes
        if isinstance(node.get("node_id"), str)
        and isinstance(node.get("depends_on"), list)
        and not node["depends_on"]
    ]
    depended_on = {
        dependency
        for node in nodes
        if isinstance(node.get("depends_on"), list)
        for dependency in node["depends_on"]
        if isinstance(dependency, str)
    }
    sinks = [
        identifier
        for identifier in identifiers
        if isinstance(identifier, str) and identifier not in depended_on
    ]
    entries = topology.get("entry_node_ids")
    outputs = topology.get("output_node_ids")
    if (
        not isinstance(entries, list)
        or any(not isinstance(identifier, str) for identifier in entries)
        or set(entries) != set(roots)
        or len(entries) != len(roots)
    ):
        errors.append(f"{label}.entry_node_ids is not the exact set of all roots")
    if (
        not isinstance(outputs, list)
        or any(not isinstance(identifier, str) for identifier in outputs)
        or set(outputs) != set(sinks)
        or len(outputs) != len(sinks)
    ):
        errors.append(f"{label}.output_node_ids is not the exact set of all sinks")
    if (
        isinstance(entries, list)
        and all(isinstance(identifier, str) for identifier in entries)
        and any(identifier not in known for identifier in entries)
    ):
        errors.append(f"{label}.entry_node_ids contains a missing node")
    if (
        isinstance(outputs, list)
        and all(isinstance(identifier, str) for identifier in outputs)
        and any(identifier not in known for identifier in outputs)
    ):
        errors.append(f"{label}.output_node_ids contains a missing node")
    return sorted(set(errors))


def structural_errors(annotation: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    skeleton = annotation.get("semantic_skeleton")
    if isinstance(skeleton, dict):
        units = skeleton.get("required_information_units")
        if isinstance(units, list):
            unit_ids = [unit.get("unit_id") for unit in units if isinstance(unit, dict)]
            if (
                len(unit_ids) != len(units)
                or any(not isinstance(identifier, str) for identifier in unit_ids)
                or len(set(unit_ids)) != len(unit_ids)
            ):
                errors.append(f"{label}.semantic_skeleton required information unit IDs are invalid")
    obligations = annotation.get("information_obligations")
    obligation_ids: set[str] = set()
    if isinstance(obligations, list):
        identifiers = [
            obligation.get("obligation_id")
            for obligation in obligations
            if isinstance(obligation, dict)
        ]
        dependencies = [
            obligation.get("depends_on")
            for obligation in obligations
            if isinstance(obligation, dict)
        ]
        if len(identifiers) != len(obligations):
            errors.append(f"{label}.information_obligations contains a non-object")
        else:
            errors.extend(
                dependency_errors(
                    identifiers,
                    dependencies,
                    f"{label}.information_obligations",
                )
            )
            obligation_ids = {
                identifier for identifier in identifiers if isinstance(identifier, str)
            }
    assessment = annotation.get("representation_assessment")
    require_full_coverage = bool(
        annotation.get("submission_status") == "annotated"
        and isinstance(assessment, dict)
        and assessment.get("outcome") == "complete"
    )
    errors.extend(
        topology_errors(
            annotation.get("abstract_topology"),
            obligation_ids,
            f"{label}.abstract_topology",
            require_full_obligation_coverage=require_full_coverage,
        )
    )
    alternatives = annotation.get("alternative_topology_plans")
    if isinstance(alternatives, list):
        plan_ids = [plan.get("plan_id") for plan in alternatives if isinstance(plan, dict)]
        if (
            len(plan_ids) != len(alternatives)
            or any(not isinstance(identifier, str) for identifier in plan_ids)
            or len(set(plan_ids)) != len(plan_ids)
        ):
            errors.append(f"{label}.alternative_topology_plans plan IDs are invalid")
        for index, plan in enumerate(alternatives):
            if isinstance(plan, dict):
                errors.extend(
                    topology_errors(
                        plan.get("topology"),
                        obligation_ids,
                        f"{label}.alternative_topology_plans[{index}].topology",
                        require_full_obligation_coverage=require_full_coverage,
                    )
                )
    return sorted(set(errors))


def raw_gate_eligible(annotation: dict[str, Any]) -> bool:
    assessment = annotation.get("representation_assessment")
    return bool(
        annotation.get("submission_status") == "annotated"
        and isinstance(assessment, dict)
        and assessment.get("outcome") == "complete"
        and assessment.get("schema_gap_descriptions") == []
        and annotation.get("instrument_issues") == []
    )


def validate_raw_records(
    records: list[Any],
    packet_context: dict[str, Any],
    validator: Any,
) -> tuple[list[dict[str, Any]], list[str]]:
    selected_ids = packet_context["selected_ids"]
    selected_views = {
        view["question_id"]: view for view in packet_context["selected_views"]
    }
    global_errors: list[str] = []
    if len(records) != EXPECTED_BATCH_QUESTION_COUNT:
        global_errors.append(
            f"raw annotation array must contain exactly {EXPECTED_BATCH_QUESTION_COUNT} records"
        )
    observed_ids: list[Any] = []
    annotators: set[str] = set()
    for record in records:
        annotation = record.get("annotation") if isinstance(record, dict) else None
        if isinstance(annotation, dict):
            observed_ids.append(annotation.get("question_id"))
            annotator = annotation.get("annotator_id")
            if isinstance(annotator, str):
                annotators.add(annotator)
    if observed_ids != selected_ids:
        global_errors.append("raw records do not match the exact active-batch question ID order")
    if len(annotators) != 1:
        global_errors.append("one raw array must contain exactly one stable annotator pseudonym")

    results: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        label = f"annotations[{index}]"
        errors: list[str] = []
        errors.extend(schema_error_messages(validator, record, label))
        if not isinstance(record, dict):
            results.append({"record": record, "annotation": None, "errors": sorted(set(errors))})
            continue
        annotation = record.get("annotation")
        if not isinstance(annotation, dict):
            results.append({"record": record, "annotation": None, "errors": sorted(set(errors))})
            continue
        if record.get("annotation_sha256") != canonical_json_sha256(annotation):
            errors.append(f"{label}.annotation_sha256 does not match canonical annotation bytes")
        question_id = annotation.get("question_id")
        expected_view = selected_views.get(question_id) if isinstance(question_id, str) else None
        if expected_view is None:
            errors.append(f"{label}.annotation.question_id is outside the selected batch")
        else:
            if annotation.get("question") != expected_view.get("question"):
                errors.append(f"{label}.annotation.question differs from the exact question view")
            if annotation.get("question_view_sha256") != canonical_json_sha256(expected_view):
                errors.append(f"{label}.annotation.question_view_sha256 is invalid")
        if annotation.get("batch_id") != packet_context["payload"]["batch_id"]:
            errors.append(f"{label}.annotation.batch_id is invalid")
        if (
            annotation.get("annotation_packet_payload_sha256")
            != packet_context["payload_sha256"]
        ):
            errors.append(f"{label}.annotation packet-payload hash is invalid")
        annotator_id = annotation.get("annotator_id")
        if not isinstance(annotator_id, str) or not PSEUDONYM_PATTERN.fullmatch(annotator_id):
            errors.append(f"{label}.annotation.annotator_id is not a valid stable pseudonym")
        if not is_utc_timestamp(annotation.get("completed_at")):
            errors.append(f"{label}.annotation.completed_at must be an RFC 3339 UTC Z timestamp")
        if annotation.get("prior_exposure_declared") is not False:
            errors.append(f"{label}.annotation declares disqualifying prior exposure")
        if annotation.get("researcher_approval_self_claimed") is not False:
            errors.append(f"{label}.annotation improperly self-claims researcher approval")
        attestation = annotation.get("attestation")
        expected_attestation_keys = {
            "human_authored",
            "worked_independently",
            "used_only_packet_question_view",
            "did_not_use_answers_grounding_environment_or_proposals",
            "locked_free_observation_before_scaffold",
        }
        if (
            not isinstance(attestation, dict)
            or set(attestation) != expected_attestation_keys
            or any(value is not True for value in attestation.values())
        ):
            errors.append(f"{label}.annotation attestation is incomplete")
        contaminated = forbidden_key_paths(annotation)
        if contaminated:
            errors.append(
                f"{label}.annotation contains forbidden later-layer keys at {contaminated[:20]!r}"
            )
        question = annotation.get("question")
        if isinstance(question, str):
            errors.extend(cue_errors(annotation, question, f"{label}.annotation"))
        errors.extend(structural_errors(annotation, f"{label}.annotation"))
        results.append(
            {
                "record": record,
                "annotation": annotation,
                "errors": sorted(set(errors)),
            }
        )
    return results, sorted(set(global_errors))


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    validator_paths = validator_implementation_paths(project_root)
    if args.packet_only:
        if args.annotations is not None or args.checks_output is not None or args.overwrite:
            print(
                "--packet-only does not accept annotations, --checks-output, or --overwrite",
                file=sys.stderr,
            )
            return 2
    elif args.annotations is None or args.checks_output is None:
        print(
            "raw validation requires positional annotations and --checks-output",
            file=sys.stderr,
        )
        return 2

    inputs: dict[str, Path | None] = {
        "annotations": args.annotations,
        "views": args.views,
        "views_manifest": args.views_manifest,
        "study_plan": args.study_plan,
        "schema": args.schema,
        "packet": args.packet,
        "packet_manifest": args.packet_manifest,
        "view_schema": project_root
        / "data_construction/schemas/question_only_semantic_view_v0_1.json",
        "common_implementation": Path(__file__).with_name("_common.py"),
        "view_builder_implementation": Path(__file__).with_name(
            "build_question_only_semantic_views.py"
        ),
        "packet_builder_implementation": Path(__file__).with_name(
            "build_question_structure_annotation_packet.py"
        ),
        "validator_implementation": Path(__file__),
        "source_questions": project_root / "data_construction/pilot/questions.jsonl",
        "split_manifest": project_root
        / "data_construction/manifests/split_manifest_v0_1.json",
        "historical_manifest": project_root
        / packet_builder.view_builder.CANONICAL_HISTORICAL_MANIFEST_PATH,
        "source_question_inventory": project_root
        / packet_builder.view_builder.CANONICAL_SOURCE_INVENTORY_PATH,
    }
    outputs = {"checks_output": args.checks_output}
    collisions = output_path_collision_errors(inputs, outputs)
    collisions.extend(historical_output_collision_errors(outputs, project_root))
    if args.checks_output is not None:
        collisions.extend(
            packet_builder.historical_tree_collision_errors(
                {"checks_output": args.checks_output}, project_root
            )
        )
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2

    try:
        validator_commit = git_tracked_commit_identity(project_root, validator_paths)
        validator_implementation_sha256 = implementation_artifact_set_sha256(
            project_root, validator_paths
        )
        packet_context = validate_packet_contract(
            views_path=args.views,
            views_manifest_path=args.views_manifest,
            study_plan_path=args.study_plan,
            schema_path=args.schema,
            packet_path=args.packet,
            packet_manifest_path=args.packet_manifest,
            batch_id=args.batch_id,
            project_root=project_root,
        )
        validator = load_schema_validator(args.schema)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot validate question-structure packet: {exc}", file=sys.stderr)
        return 2

    packet_summary = {
        "validator_version": VALIDATOR_VERSION,
        "validation_mode": VALIDATION_MODE,
        "batch_id": args.batch_id,
        "questions": len(packet_context["selected_ids"]),
        "packet_payload_sha256": packet_context["payload_sha256"],
        "packet_sha256": packet_context["packet_sha256"],
        "packet_manifest_sha256": packet_context["packet_manifest_sha256"],
        "exact_packet_contract_valid": True,
        "human_annotations_created_by_packet": 0,
        "researcher_approval_verified": False,
        "researcher_approval_status": (
            "not_machine_verified_unimplemented_procedural_manual_registry_gate"
        ),
        "semantic_agreement_claimed": False,
        "stage_transition_machine_authenticated": False,
        "raw_free_text_semantic_leakage_absence_claimed": False,
    }
    if args.packet_only:
        print(json.dumps(packet_summary, sort_keys=True))
        return 0

    try:
        if args.annotations is None or args.annotations.is_symlink() or not args.annotations.is_file():
            raise ValueError("annotations must be an existing regular non-symlink JSON file")
        raw_value = read_json(args.annotations)
        if not isinstance(raw_value, list):
            raise ValueError("annotations must be one raw JSON array, not JSONL or a wrapper object")
        results, global_errors = validate_raw_records(raw_value, packet_context, validator)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot read raw question-structure annotations: {exc}", file=sys.stderr)
        return 2

    context = {
        "annotations_artifact_sha256": sha256_file(args.annotations),
        "packet_artifact_sha256": packet_context["packet_sha256"],
        "packet_manifest_artifact_sha256": packet_context["packet_manifest_sha256"],
        "packet_payload_sha256": packet_context["payload_sha256"],
        "views_artifact_sha256": packet_context["live_hashes"]["views"],
        "views_manifest_artifact_sha256": packet_context["live_hashes"]["views_manifest"],
        "study_plan_artifact_sha256": packet_context["live_hashes"]["study_plan"],
        "annotation_schema_artifact_sha256": packet_context["live_hashes"][
            "annotation_schema"
        ],
        "validator_code_commit": validator_commit,
        "validator_implementation_artifact_set_sha256": validator_implementation_sha256,
        "validation_mode": VALIDATION_MODE,
        "researcher_approval_validation": (
            "not_performed_unimplemented_procedural_manual_registry_gate"
        ),
    }
    batch_checks: list[dict[str, Any]] = []
    if global_errors:
        batch_checks.append(
            {
                "schema_version": VALIDATION_RECORD_VERSION,
                "validator_version": VALIDATOR_VERSION,
                "validation_scope": "batch",
                "record_index": None,
                "question_id": None,
                "annotator_id": None,
                "annotation_canonical_sha256": None,
                "submission_status": None,
                "representation_assessment_outcome": None,
                "raw_collection_gate_eligible": False,
                "validation_context": context,
                "status": "fail",
                "errors": global_errors,
                "warnings": [],
            }
        )
    record_checks: list[dict[str, Any]] = []
    for index, result in enumerate(results):
        annotation = result["annotation"]
        errors = result["errors"]
        record_checks.append(
            {
                "schema_version": VALIDATION_RECORD_VERSION,
                "validator_version": VALIDATOR_VERSION,
                "validation_scope": "record",
                "record_index": index,
                "question_id": annotation.get("question_id") if isinstance(annotation, dict) else None,
                "annotator_id": annotation.get("annotator_id") if isinstance(annotation, dict) else None,
                "annotation_canonical_sha256": (
                    canonical_json_sha256(annotation) if isinstance(annotation, dict) else None
                ),
                "submission_status": (
                    annotation.get("submission_status") if isinstance(annotation, dict) else None
                ),
                "representation_assessment_outcome": (
                    annotation.get("representation_assessment", {}).get("outcome")
                    if isinstance(annotation, dict)
                    and isinstance(annotation.get("representation_assessment"), dict)
                    else None
                ),
                "raw_collection_gate_eligible": bool(
                    not global_errors
                    and not errors
                    and isinstance(annotation, dict)
                    and raw_gate_eligible(annotation)
                ),
                "validation_context": context,
                "status": "fail" if errors else "pass",
                "errors": errors,
                "warnings": [],
            }
        )
    checks = [*batch_checks, *record_checks]
    checks_bytes = jsonl_file_bytes(checks)
    try:
        if args.checks_output is None:
            raise ValueError("--checks-output is required")
        write_status = write_output_batch(
            {"checks_output": (args.checks_output, checks_bytes)},
            overwrite=args.overwrite,
        )
    except (OSError, ValueError) as exc:
        print(f"cannot write question-structure checks: {exc}", file=sys.stderr)
        return 2

    error_count = sum(len(check["errors"]) for check in record_checks)
    summary = {
        **packet_summary,
        "raw_records": len(raw_value),
        "pass_records": sum(check["status"] == "pass" for check in record_checks),
        "fail_records": sum(check["status"] == "fail" for check in record_checks),
        "batch_fail_checks": len(batch_checks),
        "raw_collection_gate_eligible_records": sum(
            check["raw_collection_gate_eligible"] and check["status"] == "pass"
            for check in record_checks
        ),
        "global_error_count": len(global_errors),
        "record_error_count": error_count,
        "checks_output": args.checks_output.as_posix(),
        "checks_output_sha256": sha256_bytes(checks_bytes),
        "write_status": write_status,
    }
    print(json.dumps(summary, sort_keys=True))
    return 1 if global_errors or error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
