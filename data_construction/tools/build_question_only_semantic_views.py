#!/usr/bin/env python3
"""Build isolated, hash-bound question-only views for blind semantic discovery."""

from __future__ import annotations

import argparse
import json
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
    jsonl_file_bytes,
    output_path_collision_errors,
    read_json,
    sha256_bytes,
    sha256_file,
    write_output_batch,
)


BUILDER_VERSION = "question_only_semantic_view_builder_v0_1"
VIEW_SCHEMA_VERSION = "question_only_semantic_view_v0_1"
MANIFEST_SCHEMA_VERSION = "question_only_semantic_view_manifest_v0_1"
VIEW_VISIBILITY = "question_only_no_environment_answer_or_proposals"
CANONICALIZATION = "sorted_compact_json_utf8_sha256_v0_1"
EXPECTED_QUESTION_COUNT = 30
QUESTION_KEYS = {
    "annotation_visibility",
    "dataset_role",
    "question",
    "question_id",
    "source_split",
    "table_id",
}
VIEW_KEYS = {"schema_version", "visibility", "question_id", "question"}
ALLOWED_FIELDS = ["schema_version", "visibility", "question_id", "question"]
EXCLUDED_CATEGORIES = [
    "dataset_role_or_source_split",
    "table_identity_schema_rows_cells_or_values",
    "environment_identity_schema_or_capabilities",
    "linked_document_identity_text_or_capabilities",
    "answer_text_span_or_execution_trace",
    "operator_vocabulary_topology_or_grounding",
    "llm_proposals_or_historical_labels",
    "other_annotator_or_adjudicated_outputs",
    "machine_local_paths",
]
CANONICAL_QUESTIONS_PATH = Path("data_construction/pilot/questions.jsonl")
CANONICAL_SPLIT_MANIFEST_PATH = Path(
    "data_construction/manifests/split_manifest_v0_1.json"
)
CANONICAL_HISTORICAL_MANIFEST_PATH = Path(
    "data_construction/manifests/historical_exposed_ids.json"
)
CANONICAL_SOURCE_INVENTORY_PATH = Path(
    "data_construction/manifests/source_question_ids.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        type=Path,
        default=Path("data_construction/pilot/questions.jsonl"),
    )
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("data_construction/manifests/split_manifest_v0_1.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data_construction/pilot/question_only_semantic_views_v0_1.jsonl"),
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=Path(
            "data_construction/pilot/question_only_semantic_views_manifest_v0_1.json"
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing outputs only when their bytes differ",
    )
    return parser.parse_args()


def portable_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return f"<external-artifact>/{path.name}"


def validate_questions(
    questions: list[dict[str, Any]],
    questions_path: Path,
    split_manifest: dict[str, Any],
) -> list[str]:
    expected_counts = {
        "annotation_schema_pilot": EXPECTED_QUESTION_COUNT,
        "annotation_train": 0,
        "annotation_dev": 0,
        "locked_eval": 0,
    }
    role_artifacts = split_manifest.get("role_artifacts")
    roles = split_manifest.get("roles")
    if (
        split_manifest.get("schema_version") != "split_manifest_v0_1"
        or split_manifest.get("release_eligible") is not True
        or split_manifest.get("override_used") is not False
        or split_manifest.get("zero_overlap_verified") is not True
        or split_manifest.get("counts") != expected_counts
        or not isinstance(role_artifacts, dict)
        or not isinstance(roles, dict)
    ):
        raise ValueError(
            "split manifest is not the exact release-eligible, zero-overlap pilot allocation"
        )
    if any(
        roles.get(role) != [] or role_artifacts.get(role) is not None
        for role in ("annotation_train", "annotation_dev", "locked_eval")
    ):
        raise ValueError("non-pilot roles must remain unallocated")
    artifact = role_artifacts.get("annotation_schema_pilot")
    allocated_ids = roles.get("annotation_schema_pilot")
    if not isinstance(artifact, dict) or not isinstance(allocated_ids, list):
        raise ValueError("split manifest has no annotation_schema_pilot allocation")
    if artifact.get("sha256") != sha256_file(questions_path):
        raise ValueError("questions artifact SHA-256 does not match the split manifest")
    if artifact.get("record_count") != len(questions):
        raise ValueError("questions record count does not match the split manifest")
    if len(questions) != EXPECTED_QUESTION_COUNT or len(allocated_ids) != EXPECTED_QUESTION_COUNT:
        raise ValueError(f"expected exactly {EXPECTED_QUESTION_COUNT} allocated pilot questions")

    observed_ids: list[str] = []
    seen_ids: set[str] = set()
    seen_tables: set[str] = set()
    for index, question in enumerate(questions):
        if set(question) != QUESTION_KEYS:
            raise ValueError(
                f"question record {index} has unexpected keys: "
                f"missing={sorted(QUESTION_KEYS - set(question))!r}, "
                f"extra={sorted(set(question) - QUESTION_KEYS)!r}"
            )
        question_id = question.get("question_id")
        table_id = question.get("table_id")
        text = question.get("question")
        if (
            not isinstance(question_id, str)
            or not question_id
            or question_id in seen_ids
            or "\r" in question_id
            or "\n" in question_id
        ):
            raise ValueError(f"question record {index} has an unsafe or duplicate question_id")
        if (
            not isinstance(table_id, str)
            or not table_id
            or table_id in seen_tables
            or "/" in table_id
            or "\\" in table_id
            or "\r" in table_id
            or "\n" in table_id
        ):
            raise ValueError(f"question record {index} has an unsafe or duplicate table_id")
        if (
            not isinstance(text, str)
            or not text.strip()
            or question.get("annotation_visibility") != "question_and_table_identity_only"
            or question.get("dataset_role") != "annotation_schema_pilot"
            or question.get("source_split") != "dev"
        ):
            raise ValueError(f"question record {index} violates the pilot source contract")
        observed_ids.append(question_id)
        seen_ids.add(question_id)
        seen_tables.add(table_id)
    if observed_ids != allocated_ids:
        raise ValueError("questions are not in the exact allocated ID order from the split manifest")
    return observed_ids


def validate_split_provenance(
    split_manifest: dict[str, Any], project_root: Path
) -> None:
    historical_reference = split_manifest.get("historical_manifest")
    source = split_manifest.get("source")
    if not isinstance(historical_reference, dict) or not isinstance(source, dict):
        raise ValueError("split manifest omits historical or official-source provenance")

    historical_path = project_root / CANONICAL_HISTORICAL_MANIFEST_PATH
    if (
        historical_reference.get("path") != CANONICAL_HISTORICAL_MANIFEST_PATH.as_posix()
        or historical_reference.get("sha256") != sha256_file(historical_path)
        or historical_reference.get("audit_status") != "complete"
        or historical_reference.get("release_contract_errors") != []
    ):
        raise ValueError("split manifest does not bind the canonical complete historical audit")
    historical = read_json(historical_path)
    if (
        not isinstance(historical, dict)
        or historical.get("audit_status") != "complete"
        or historical.get("is_complete") is not True
        or historical.get("recovery_provenance_status") != "verified"
        or historical.get("recovery_provenance_errors") != []
        or historical.get("missing_required_files") != []
        or historical.get("required_files_with_no_question_ids") != []
        or historical.get("known_expected_count_mismatches") != []
    ):
        raise ValueError("canonical historical audit is not strict-complete and release-safe")

    inventory_reference = source.get("question_id_inventory_artifact")
    inventory_path = project_root / CANONICAL_SOURCE_INVENTORY_PATH
    if (
        source.get("verified_against_pinned_manifest") is not True
        or not isinstance(inventory_reference, dict)
        or inventory_reference.get("path") != CANONICAL_SOURCE_INVENTORY_PATH.as_posix()
        or inventory_reference.get("sha256") != sha256_file(inventory_path)
        or inventory_reference.get("record_count") != source.get("record_count")
        or inventory_reference.get("question_id_set_sha256")
        != source.get("question_id_set_sha256")
    ):
        raise ValueError("split manifest does not bind the canonical pinned source inventory")


def build_records(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for question in questions:
        record = {
            "schema_version": VIEW_SCHEMA_VERSION,
            "visibility": VIEW_VISIBILITY,
            "question_id": question["question_id"],
            "question": question["question"],
        }
        if set(record) != VIEW_KEYS:
            raise ValueError(f"{question['question_id']}: view fields differ from the exact allowlist")
        if (
            record["schema_version"] != VIEW_SCHEMA_VERSION
            or record["visibility"] != VIEW_VISIBILITY
            or not isinstance(record["question_id"], str)
            or not isinstance(record["question"], str)
        ):
            raise ValueError(f"{question['question_id']}: invalid question-only projection")
        records.append(record)
    return records


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    canonical_questions = project_root / CANONICAL_QUESTIONS_PATH
    canonical_split_manifest = project_root / CANONICAL_SPLIT_MANIFEST_PATH
    if (
        args.questions.resolve() != canonical_questions.resolve()
        or args.split_manifest.resolve() != canonical_split_manifest.resolve()
    ):
        print(
            "cannot build question-only semantic views: canonical release inputs are required",
            file=sys.stderr,
        )
        return 2
    try:
        args.output.resolve().relative_to(project_root.resolve())
        args.manifest_output.resolve().relative_to(project_root.resolve())
    except ValueError:
        print(
            "cannot build question-only semantic views: canonical outputs must remain inside the repository",
            file=sys.stderr,
        )
        return 2
    schema_path = project_root / "data_construction/schemas/question_only_semantic_view_v0_1.json"
    common_path = Path(__file__).with_name("_common.py")
    implementation_paths = [schema_path, common_path, Path(__file__)]
    release_contract_paths = [
        canonical_questions,
        canonical_split_manifest,
        project_root / CANONICAL_HISTORICAL_MANIFEST_PATH,
        project_root / CANONICAL_SOURCE_INVENTORY_PATH,
    ]
    collisions = output_path_collision_errors(
        {
            "questions": args.questions,
            "split_manifest": args.split_manifest,
            "view_schema": schema_path,
            "common_implementation": common_path,
            "builder_implementation": Path(__file__),
            "historical_manifest": project_root / CANONICAL_HISTORICAL_MANIFEST_PATH,
            "source_question_inventory": project_root / CANONICAL_SOURCE_INVENTORY_PATH,
        },
        {"output": args.output, "manifest_output": args.manifest_output},
    )
    collisions.extend(
        historical_output_collision_errors(
            {"output": args.output, "manifest_output": args.manifest_output}, project_root
        )
    )
    protected_historical_tree = (project_root / "historical").resolve()
    for label, path in {"output": args.output, "manifest_output": args.manifest_output}.items():
        try:
            path.resolve().relative_to(protected_historical_tree)
        except ValueError:
            continue
        collisions.append(
            f"output {label!r} targets the read-only historical tree: {path.resolve()}"
        )
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2

    try:
        for label, path in {
            "questions": args.questions,
            "split manifest": args.split_manifest,
        }.items():
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"{label} must be an existing regular non-symlink file: {path}")
        read_paths = implementation_paths + release_contract_paths
        read_hashes = {path.resolve(): sha256_file(path) for path in read_paths}
        implementation_commit = git_tracked_commit_identity(project_root, read_paths)
        split_manifest = read_json(args.split_manifest)
        if not isinstance(split_manifest, dict):
            raise ValueError("split manifest must be a JSON object")
        validate_split_provenance(split_manifest, project_root)
        questions = list(iter_json_records(args.questions))
        question_ids = validate_questions(questions, args.questions, split_manifest)
        records = build_records(questions)
        if any(sha256_file(path) != read_hashes[path.resolve()] for path in read_paths):
            raise ValueError("an input or provenance artifact changed during view construction")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot build question-only semantic views: {exc}", file=sys.stderr)
        return 2

    output_payload = jsonl_file_bytes(records)
    output_sha256 = sha256_bytes(output_payload)
    record_hashes = [
        {
            "question_id": record["question_id"],
            "canonical_sha256": canonical_json_sha256(record),
        }
        for record in records
    ]
    implementation_artifacts = sorted(
        [
            {
                "repository_relative_path": portable_path(path, project_root),
                "sha256": read_hashes[path.resolve()],
            }
            for path in implementation_paths
        ],
        key=lambda value: value["repository_relative_path"].encode("utf-8"),
    )
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "builder_version": BUILDER_VERSION,
        "provenance": {
            "code_commit": implementation_commit,
            "implementation_artifacts": implementation_artifacts,
            "implementation_artifact_set_sha256": implementation_artifact_set_sha256(
                project_root, implementation_paths
            ),
        },
        "views_artifact": {
            "repository_relative_path": portable_path(args.output, project_root),
            "record_count": len(records),
            "sha256": output_sha256,
        },
        "questions_artifact": {
            "repository_relative_path": portable_path(args.questions, project_root),
            "record_count": len(questions),
            "sha256": read_hashes[args.questions.resolve()],
        },
        "split_manifest_artifact": {
            "repository_relative_path": portable_path(args.split_manifest, project_root),
            "sha256": read_hashes[args.split_manifest.resolve()],
        },
        "allocation_contract": {
            "dataset_role": "annotation_schema_pilot",
            "source_split": "dev",
            "question_count": len(records),
            "release_eligible": True,
            "zero_overlap_verified": True,
            "override_used": False,
            "question_order_matches_split_manifest": True,
        },
        "record_hash_contract": {
            "canonicalization": CANONICALIZATION,
            "ordered_question_ids_sha256": canonical_json_sha256(question_ids),
            "ordered_record_hashes_sha256": canonical_json_sha256(record_hashes),
            "records": record_hashes,
        },
        "view_contract": {
            "allowed_fields": ALLOWED_FIELDS,
            "visible_input_categories": ["question_id", "question_text"],
            "excluded_categories": EXCLUDED_CATEGORIES,
            "environment_exposed": False,
            "answer_or_execution_evidence_exposed": False,
            "proposal_or_historical_label_exposed": False,
            "other_annotator_output_exposed": False,
            "leakage_audit_status": "pass_by_exact_projection",
        },
    }
    manifest_payload = json_file_bytes(manifest)
    manifest_sha256 = sha256_bytes(manifest_payload)
    try:
        if any(sha256_file(path) != read_hashes[path.resolve()] for path in read_paths):
            raise ValueError("an input or provenance artifact changed before output commit")
        write_status = write_output_batch(
            {
                "output": (args.output, output_payload),
                "manifest_output": (args.manifest_output, manifest_payload),
            },
            overwrite=args.overwrite,
        )
    except (OSError, ValueError) as exc:
        print(f"cannot write question-only semantic views: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "builder_version": BUILDER_VERSION,
                "questions": len(records),
                "output": args.output.as_posix(),
                "output_sha256": output_sha256,
                "manifest_output": args.manifest_output.as_posix(),
                "manifest_sha256": manifest_sha256,
                "write_status": write_status,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
