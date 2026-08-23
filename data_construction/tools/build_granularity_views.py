#!/usr/bin/env python3
"""Build hash-bound, leakage-reduced input views for the granularity pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from _common import (
    canonical_json_sha256,
    git_tracked_commit_identity,
    historical_output_collision_errors,
    iter_json_records,
    json_file_bytes,
    jsonl_file_bytes,
    output_path_collision_errors,
    read_json,
    sha256_bytes,
    sha256_file,
    write_output_batch,
)


VIEW_BUILDER_VERSION = "granularity_view_builder_v0_1"
QUESTION_KEYS = {
    "annotation_visibility",
    "dataset_role",
    "question",
    "question_id",
    "source_split",
    "table_id",
}
VISIBLE_CAPABILITIES = {
    "table_access_available": True,
    "linked_document_lookup_available": True,
    "linked_document_text_available_to_later_layers": True,
    "linked_document_text_exposed_in_this_view": False,
    "lookup_scope": "pinned_linked_snapshot_for_current_table",
}


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
        "--source-manifest",
        type=Path,
        default=Path("data_construction/manifests/source_manifest_v0_1.json"),
    )
    parser.add_argument(
        "--wikitables-checkout",
        required=True,
        type=Path,
        help="Machine-local checkout of the pinned WikiTables-WithLinks repository",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data_construction/pilot/granularity_input_views.jsonl"),
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=Path("data_construction/pilot/granularity_input_views_manifest_v0_1.json"),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing view artifacts only when their bytes differ",
    )
    return parser.parse_args()


def run_git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ValueError(detail)
    return result.stdout.strip()


def linked_source_contract(source_manifest: dict[str, Any]) -> dict[str, Any]:
    upstreams = source_manifest.get("upstreams")
    if not isinstance(upstreams, list):
        raise ValueError("source manifest has no upstream list")
    matches = [
        item
        for item in upstreams
        if isinstance(item, dict)
        and item.get("source_id") == "hybridqa_linked_tables_and_passages"
    ]
    if len(matches) != 1:
        raise ValueError("source manifest must have exactly one linked-environment upstream")
    contract = matches[0]
    artifacts = contract.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("linked-environment upstream has no artifact list")
    artifacts_by_path = {
        item.get("path"): item
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    for path in ("tables_tok", "request_tok"):
        artifact = artifacts_by_path.get(path)
        if not isinstance(artifact, dict) or not isinstance(artifact.get("git_tree_sha1"), str):
            raise ValueError(f"source manifest has no Git tree identity for {path}")
    return {
        "source_id": contract.get("source_id"),
        "repository_url": contract.get("repository_url"),
        "pinned_commit": contract.get("pinned_commit"),
        "git_tree_sha1": contract.get("git_tree_sha1"),
        "tables_tree_sha1": artifacts_by_path["tables_tok"]["git_tree_sha1"],
        "request_tree_sha1": artifacts_by_path["request_tok"]["git_tree_sha1"],
        "tables_file_count": artifacts_by_path["tables_tok"].get("file_count"),
        "tables_canonical_content_list_sha256": artifacts_by_path["tables_tok"].get(
            "canonical_content_list_sha256"
        ),
        "request_file_count": artifacts_by_path["request_tok"].get("file_count"),
        "request_canonical_content_list_sha256": artifacts_by_path["request_tok"].get(
            "canonical_content_list_sha256"
        ),
    }


def verify_checkout(repository: Path, contract: dict[str, Any]) -> None:
    if repository.is_symlink() or not (repository / ".git").is_dir():
        raise ValueError(f"linked-environment checkout is not a Git repository: {repository}")
    if (repository / "tables_tok").is_symlink() or (repository / "request_tok").is_symlink():
        raise ValueError("linked-environment source directories must not be symlinks")
    expected_remote = contract.get("repository_url")
    observed_remote = run_git(repository, "remote", "get-url", "origin")
    if observed_remote not in {expected_remote, str(expected_remote).removesuffix(".git")}:
        raise ValueError(
            f"linked-environment origin mismatch: expected {expected_remote!r}, observed {observed_remote!r}"
        )
    dirty = run_git(repository, "status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise ValueError("linked-environment checkout has local changes")
    identities = {
        "pinned_commit": run_git(repository, "rev-parse", "HEAD"),
        "git_tree_sha1": run_git(repository, "show", "-s", "--format=%T", "HEAD"),
        "tables_tree_sha1": run_git(repository, "rev-parse", "HEAD:tables_tok"),
        "request_tree_sha1": run_git(repository, "rev-parse", "HEAD:request_tok"),
    }
    for field, observed in identities.items():
        expected = contract.get(field)
        if not isinstance(expected, str) or observed != expected:
            raise ValueError(
                f"linked-environment {field} mismatch: expected {expected!r}, observed {observed!r}"
            )


def validate_questions(
    questions: list[dict[str, Any]],
    questions_path: Path,
    split_manifest: dict[str, Any],
) -> None:
    role_artifacts = split_manifest.get("role_artifacts")
    roles = split_manifest.get("roles")
    if (
        split_manifest.get("schema_version") != "split_manifest_v0_1"
        or split_manifest.get("release_eligible") is not True
        or split_manifest.get("override_used") is not False
        or split_manifest.get("zero_overlap_verified") is not True
        or not isinstance(role_artifacts, dict)
        or not isinstance(roles, dict)
    ):
        raise ValueError("split manifest is not a release-eligible, zero-overlap v0.1 allocation")
    artifact = role_artifacts.get("annotation_schema_pilot")
    allocated_ids = roles.get("annotation_schema_pilot")
    if not isinstance(artifact, dict) or not isinstance(allocated_ids, list):
        raise ValueError("split manifest has no annotation_schema_pilot allocation")
    if artifact.get("sha256") != sha256_file(questions_path):
        raise ValueError("questions artifact SHA-256 does not match the split manifest")
    if artifact.get("record_count") != len(questions):
        raise ValueError("questions record count does not match the split manifest")
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
        if not isinstance(question_id, str) or not question_id or question_id in seen_ids:
            raise ValueError(f"question record {index} has a missing or duplicate question_id")
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
            not isinstance(question.get("question"), str)
            or not question["question"].strip()
            or question.get("annotation_visibility") != "question_and_table_identity_only"
            or question.get("dataset_role") != "annotation_schema_pilot"
        ):
            raise ValueError(f"question record {index} violates the pilot visibility/role contract")
        observed_ids.append(question_id)
        seen_ids.add(question_id)
        seen_tables.add(table_id)
    if observed_ids != allocated_ids:
        raise ValueError("questions are not in the exact allocated ID order from the split manifest")


def table_schema_view(table: Any, table_id: str) -> dict[str, Any]:
    if not isinstance(table, dict) or not isinstance(table.get("header"), list):
        raise ValueError(f"{table_id}: table has no header array")
    if not isinstance(table.get("data"), list):
        raise ValueError(f"{table_id}: table data has the wrong shape")
    if table.get("uid") != table_id:
        raise ValueError(f"{table_id}: table uid does not match its allocated table_id")
    header = table["header"]
    rows = table["data"]
    columns: list[dict[str, Any]] = []
    for index, cell in enumerate(header):
        if (
            not isinstance(cell, list)
            or len(cell) != 2
            or not isinstance(cell[0], str)
            or not isinstance(cell[1], list)
        ):
            raise ValueError(f"{table_id}: malformed header cell at column {index}")
        columns.append(
            {
                "index": index,
                "label": cell[0],
                "entity_link_capability": False,
            }
        )
    for row_index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(header):
            raise ValueError(f"{table_id}: malformed row width at row {row_index}")
        for column_index, cell in enumerate(row):
            if (
                not isinstance(cell, list)
                or len(cell) != 2
                or not isinstance(cell[0], str)
                or not isinstance(cell[1], list)
            ):
                raise ValueError(
                    f"{table_id}: malformed table cell at row {row_index}, column {column_index}"
                )
            if cell[1]:
                columns[column_index]["entity_link_capability"] = True
    title = table.get("title")
    section_title = table.get("section_title")
    if not isinstance(title, str) or not isinstance(section_title, str):
        raise ValueError(f"{table_id}: title or section_title has the wrong shape")
    return {
        "table_id": table_id,
        "title": title,
        "section_title": section_title,
        "columns": columns,
        "capabilities": dict(VISIBLE_CAPABILITIES),
    }


def selected_artifact_set_sha256(artifacts: list[dict[str, Any]]) -> str:
    lines = (
        f"{artifact['sha256']}  {artifact['portable_path']}\n".encode("utf-8")
        for artifact in sorted(artifacts, key=lambda value: value["portable_path"].encode("utf-8"))
    )
    return hashlib.sha256(b"".join(lines)).hexdigest()


def exact_view_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(record) != {
        "schema_version",
        "question_id",
        "question_view",
        "question_view_sha256",
        "operator_view",
        "operator_view_sha256",
    }:
        errors.append("view wrapper fields differ from the exact allowlist")
        return errors
    question_view = record.get("question_view")
    operator_view = record.get("operator_view")
    if not isinstance(question_view, dict) or set(question_view) != {
        "schema_version",
        "visibility",
        "question_id",
        "question",
    }:
        errors.append("question_view fields differ from the exact allowlist")
    if not isinstance(operator_view, dict) or set(operator_view) != {
        "schema_version",
        "visibility",
        "question_id",
        "question",
        "environment",
    }:
        errors.append("operator_view fields differ from the exact allowlist")
        return errors
    environment = operator_view.get("environment")
    if not isinstance(environment, dict) or set(environment) != {
        "table_id",
        "title",
        "section_title",
        "columns",
        "capabilities",
    }:
        errors.append("operator_view environment fields differ from the exact allowlist")
        return errors
    columns = environment.get("columns")
    if not isinstance(columns, list) or any(
        not isinstance(column, dict)
        or set(column) != {"index", "label", "entity_link_capability"}
        for column in columns
    ):
        errors.append("operator_view column fields differ from the exact allowlist")
    if environment.get("capabilities") != VISIBLE_CAPABILITIES:
        errors.append("operator_view capabilities differ from the exact source contract")
    if isinstance(question_view, dict):
        if record.get("question_view_sha256") != canonical_json_sha256(question_view):
            errors.append("question_view SHA-256 does not match")
        if "table_id" in question_view or "environment" in question_view:
            errors.append("question_view exposes environment identity")
    if record.get("operator_view_sha256") != canonical_json_sha256(operator_view):
        errors.append("operator_view SHA-256 does not match")
    return errors


def build_records(
    questions: list[dict[str, Any]],
    checkout: Path,
    contract: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    selected_artifacts: list[dict[str, Any]] = []
    for question in questions:
        question_id = question["question_id"]
        table_id = question["table_id"]
        table_path = checkout / "tables_tok" / f"{table_id}.json"
        request_path = checkout / "request_tok" / f"{table_id}.json"
        if (
            table_path.is_symlink()
            or request_path.is_symlink()
            or not table_path.is_file()
            or not request_path.is_file()
        ):
            raise ValueError(f"{question_id}: linked environment is missing table/request files")
        table = read_json(table_path)
        # request_tok contains document identifiers and passage text.  The clean
        # pinned Git tree and file digest bind it without parsing or projecting
        # any of those values into an early-layer view.
        environment = table_schema_view(table, table_id)
        question_view = {
            "schema_version": "granularity_question_view_v0_1",
            "visibility": "question_only_no_environment_or_answer",
            "question_id": question_id,
            "question": question["question"],
        }
        operator_view = {
            "schema_version": "granularity_operator_view_v0_1",
            "visibility": "question_plus_table_schema_and_capabilities_no_values",
            "question_id": question_id,
            "question": question["question"],
            "environment": environment,
        }
        selected_artifacts.extend(
            [
                {
                    "portable_path": f"tables_tok/{table_id}.json",
                    "sha256": sha256_file(table_path),
                },
                {
                    "portable_path": f"request_tok/{table_id}.json",
                    "sha256": sha256_file(request_path),
                },
            ]
        )
        record = {
            "schema_version": "granularity_input_views_v0_1",
            "question_id": question_id,
            "question_view": question_view,
            "question_view_sha256": canonical_json_sha256(question_view),
            "operator_view": operator_view,
            "operator_view_sha256": canonical_json_sha256(operator_view),
        }
        projection_errors = exact_view_errors(record)
        if projection_errors:
            raise ValueError(f"{question_id}: {'; '.join(projection_errors)}")
        records.append(record)
    return records, selected_artifacts


def portable_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return f"<external-artifact>/{path.name}"


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    collisions = output_path_collision_errors(
        {
            "questions": args.questions,
            "split_manifest": args.split_manifest,
            "source_manifest": args.source_manifest,
        },
        {"output": args.output, "manifest_output": args.manifest_output},
    )
    collisions.extend(
        historical_output_collision_errors(
            {"output": args.output, "manifest_output": args.manifest_output}, project_root
        )
    )
    checkout_root = args.wikitables_checkout.resolve()
    for label, path in {"output": args.output, "manifest_output": args.manifest_output}.items():
        try:
            path.resolve().relative_to(checkout_root)
        except ValueError:
            pass
        else:
            collisions.append(f"output {label!r} must not be inside the official-source checkout")
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    try:
        implementation_paths = [Path(__file__), Path(__file__).with_name("_common.py")]
        implementation_commit = git_tracked_commit_identity(project_root, implementation_paths)
        split_manifest = read_json(args.split_manifest)
        source_manifest = read_json(args.source_manifest)
        if not isinstance(split_manifest, dict) or not isinstance(source_manifest, dict):
            raise ValueError("manifests must be JSON objects")
        questions = list(iter_json_records(args.questions))
        validate_questions(questions, args.questions, split_manifest)
        contract = linked_source_contract(source_manifest)
        verify_checkout(args.wikitables_checkout, contract)
        records, selected_artifacts = build_records(
            questions,
            args.wikitables_checkout,
            contract,
        )
        # Catch source-cache mutation after the initial clean-tree check and
        # selected-file hashing, before any research artifact is written.
        verify_checkout(args.wikitables_checkout, contract)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot build granularity views: {exc}", file=sys.stderr)
        return 2
    output_payload = jsonl_file_bytes(records)
    output_sha256 = sha256_bytes(output_payload)
    manifest = {
        "schema_version": "granularity_input_views_manifest_v0_1",
        "builder_version": VIEW_BUILDER_VERSION,
        "provenance": {
            "code_commit": implementation_commit,
            "implementation_artifacts": [
                {
                    "repository_relative_path": portable_path(path, project_root),
                    "sha256": sha256_file(path),
                }
                for path in implementation_paths
            ],
        },
        "input_views_artifact": {
            "repository_relative_path": portable_path(args.output, project_root),
            "record_count": len(records),
            "sha256": output_sha256,
        },
        "questions_artifact": {
            "repository_relative_path": portable_path(args.questions, project_root),
            "record_count": len(records),
            "sha256": sha256_file(args.questions),
        },
        "split_manifest_artifact": {
            "repository_relative_path": portable_path(args.split_manifest, project_root),
            "sha256": sha256_file(args.split_manifest),
        },
        "source_manifest_artifact": {
            "repository_relative_path": portable_path(args.source_manifest, project_root),
            "sha256": sha256_file(args.source_manifest),
        },
        "linked_environment": contract,
        "selected_environment_artifacts": {
            "file_count": len(selected_artifacts),
            "canonicalization": "sha256_of_path_sorted_sha256sum_lines_v0_1",
            "canonical_sha256": selected_artifact_set_sha256(selected_artifacts),
            "tables_canonical_sha256": selected_artifact_set_sha256(
                [
                    artifact
                    for artifact in selected_artifacts
                    if artifact["portable_path"].startswith("tables_tok/")
                ]
            ),
            "requests_canonical_sha256": selected_artifact_set_sha256(
                [
                    artifact
                    for artifact in selected_artifacts
                    if artifact["portable_path"].startswith("request_tok/")
                ]
            ),
            "artifacts": sorted(selected_artifacts, key=lambda value: value["portable_path"]),
        },
        "view_contract": {
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
        },
    }
    manifest_payload = json_file_bytes(manifest)
    manifest_sha256 = sha256_bytes(manifest_payload)
    try:
        write_output_batch(
            {
                "output": (args.output, output_payload),
                "manifest_output": (args.manifest_output, manifest_payload),
            },
            overwrite=args.overwrite,
        )
    except (OSError, ValueError) as exc:
        print(f"cannot write granularity views: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "builder_version": VIEW_BUILDER_VERSION,
                "questions": len(records),
                "output": args.output.as_posix(),
                "output_sha256": output_sha256,
                "manifest_output": args.manifest_output.as_posix(),
                "manifest_sha256": manifest_sha256,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
