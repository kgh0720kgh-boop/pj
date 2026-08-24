"""Pinned-source helpers for representative HybridQA environment views.

This module is deliberately side-effect free at import time.  Its public
functions verify the two official source checkouts and project only the
question, table, and linked-passage fields needed by the representative
environment-realization stage.  Official answers, traces, references, and
machine-local cache paths are never returned.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from _common import canonical_json_sha256, canonical_string_set_sha256, sha256_bytes, strict_json_loads


class RepresentativeEnvironmentSourceError(ValueError):
    """The pinned source or its leakage-safe projection violates the contract."""


QUESTION_SOURCE_ID = "hybridqa_questions_and_code"
LINKED_SOURCE_ID = "hybridqa_linked_tables_and_passages"
HYBRIDQA_CHECKOUT_DIRECTORY = "HybridQA-db22fda"
WIKITABLES_CHECKOUT_DIRECTORY = "WikiTables-WithLinks-dc066e1"
DEV_ARTIFACT_PATH = "released_data/dev.json"

EXPECTED_QUESTION_SOURCE = {
    "repository_url": "https://github.com/wenhuchen/HybridQA.git",
    "pinned_commit": "db22fda8c5951438fade3c69d75b350335ba93b3",
    "git_tree_sha1": "1e1ef6a6168ef6c6cf362264d8f7b75859ce8fdf",
    "released_data_tree_sha1": "e3746c1ae9de9b8ecc85f8a6326faa1edf58a90f",
    "dev_sha256": "424272b233735a70ed8ef5af4a615373d114f472168c686c4370d54c92d58ac1",
    "dev_record_count": 3466,
    "dev_question_id_set_sha256": "70ee935abae8409251e0858a46d7a92f7875e2bfa0d8084f8ab3bb1cd591f584",
}
EXPECTED_LINKED_SOURCE = {
    "repository_url": "https://github.com/wenhuchen/WikiTables-WithLinks.git",
    "pinned_commit": "dc066e1a6d5281511d8b73a6107d5ad2824cc2b2",
    "git_tree_sha1": "b4f2d5e0eeb2d18cf95bf6e6a583bc499c53b68c",
    "tables_tree_sha1": "772e97624b08e0bd5534b8991a8c2dd8fb6b153f",
    "request_tree_sha1": "f1c1a1dab31b2341f338a6a7bf626b5b8c569f20",
    "tables_file_count": 15316,
    "request_file_count": 15316,
    "tables_canonical_content_list_sha256": (
        "3969fcf6c0192d6085ad999e3abd41f0039a73c878ffd30d7cd8b7786ea62c92"
    ),
    "request_canonical_content_list_sha256": (
        "bc289b9aa6d397369b44cbf9b54250539a5a0cf01287f94c9a5572e79e8cd916"
    ),
}


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RepresentativeEnvironmentSourceError(f"{label} must be a JSON object")
    return value


def _exact_value(value: Any, expected: Any, label: str) -> Any:
    if value != expected:
        raise RepresentativeEnvironmentSourceError(f"{label} differs from the official pin")
    return value


def _one_upstream(source_manifest: dict[str, Any], source_id: str) -> dict[str, Any]:
    upstreams = source_manifest.get("upstreams")
    if not isinstance(upstreams, list):
        raise RepresentativeEnvironmentSourceError("source manifest has no upstream list")
    matches = [
        item
        for item in upstreams
        if isinstance(item, dict) and item.get("source_id") == source_id
    ]
    if len(matches) != 1:
        raise RepresentativeEnvironmentSourceError(
            f"source manifest must contain exactly one {source_id!r} upstream"
        )
    return matches[0]


def _one_artifact(upstream: dict[str, Any], path: str) -> dict[str, Any]:
    artifacts = upstream.get("artifacts")
    if not isinstance(artifacts, list):
        raise RepresentativeEnvironmentSourceError("source upstream has no artifact list")
    matches = [
        item for item in artifacts if isinstance(item, dict) and item.get("path") == path
    ]
    if len(matches) != 1:
        raise RepresentativeEnvironmentSourceError(
            f"source upstream must contain exactly one {path!r} artifact"
        )
    return matches[0]


def extract_source_contract(source_manifest: dict[str, Any]) -> dict[str, Any]:
    """Extract and authenticate the exact official source identities.

    The returned contract is portable: it contains fixed checkout child names,
    Git identities, repository-relative paths, hashes, and counts, but no local
    filesystem locator.
    """

    manifest = _object(source_manifest, "source manifest")
    for key, expected in (
        ("schema_version", "source_manifest_v0_1"),
        ("dataset", "HybridQA"),
        ("source_policy", "official_primary_sources_only"),
        ("retrieval_status", "available_and_locally_verified"),
    ):
        _exact_value(manifest.get(key), expected, f"source manifest {key}")

    question_upstream = _one_upstream(manifest, QUESTION_SOURCE_ID)
    linked_upstream = _one_upstream(manifest, LINKED_SOURCE_ID)
    dev_artifact = _one_artifact(question_upstream, DEV_ARTIFACT_PATH)
    tables_artifact = _one_artifact(linked_upstream, "tables_tok")
    request_artifact = _one_artifact(linked_upstream, "request_tok")

    question_inventory = _object(manifest.get("source_id_inventory"), "source ID inventory")
    question_sets = _object(
        question_inventory.get("question_id_sets"), "source question-ID sets"
    )
    dev_id_set = _object(question_sets.get("dev"), "official dev question-ID set")

    question_checks = {
        "repository_url": question_upstream.get("repository_url"),
        "pinned_commit": question_upstream.get("pinned_commit"),
        "git_tree_sha1": question_upstream.get("git_tree_sha1"),
        "released_data_tree_sha1": question_upstream.get("released_data_tree_sha1"),
        "dev_sha256": dev_artifact.get("sha256"),
        "dev_record_count": dev_artifact.get("record_count"),
        "dev_question_id_set_sha256": dev_id_set.get("canonical_sha256"),
    }
    for key, expected in EXPECTED_QUESTION_SOURCE.items():
        _exact_value(question_checks.get(key), expected, f"question source {key}")
    _exact_value(
        dev_artifact.get("unique_question_id_count"),
        EXPECTED_QUESTION_SOURCE["dev_record_count"],
        "question source dev unique-question count",
    )
    _exact_value(
        dev_id_set.get("count"),
        EXPECTED_QUESTION_SOURCE["dev_record_count"],
        "question source dev ID-set count",
    )

    linked_checks = {
        "repository_url": linked_upstream.get("repository_url"),
        "pinned_commit": linked_upstream.get("pinned_commit"),
        "git_tree_sha1": linked_upstream.get("git_tree_sha1"),
        "tables_tree_sha1": tables_artifact.get("git_tree_sha1"),
        "request_tree_sha1": request_artifact.get("git_tree_sha1"),
        "tables_file_count": tables_artifact.get("file_count"),
        "request_file_count": request_artifact.get("file_count"),
        "tables_canonical_content_list_sha256": tables_artifact.get(
            "canonical_content_list_sha256"
        ),
        "request_canonical_content_list_sha256": request_artifact.get(
            "canonical_content_list_sha256"
        ),
    }
    for key, expected in EXPECTED_LINKED_SOURCE.items():
        _exact_value(linked_checks.get(key), expected, f"linked source {key}")

    return {
        "schema_version": "representative_environment_source_contract_v0_1",
        "question_source": {
            "source_id": QUESTION_SOURCE_ID,
            "checkout_directory": HYBRIDQA_CHECKOUT_DIRECTORY,
            "repository_url": question_checks["repository_url"],
            "pinned_commit": question_checks["pinned_commit"],
            "git_tree_sha1": question_checks["git_tree_sha1"],
            "released_data_tree_sha1": question_checks["released_data_tree_sha1"],
            "dev_artifact": {
                "repository_relative_path": DEV_ARTIFACT_PATH,
                "sha256": question_checks["dev_sha256"],
                "record_count": question_checks["dev_record_count"],
                "question_id_set_sha256": question_checks[
                    "dev_question_id_set_sha256"
                ],
            },
        },
        "linked_environment_source": {
            "source_id": LINKED_SOURCE_ID,
            "checkout_directory": WIKITABLES_CHECKOUT_DIRECTORY,
            "repository_url": linked_checks["repository_url"],
            "pinned_commit": linked_checks["pinned_commit"],
            "git_tree_sha1": linked_checks["git_tree_sha1"],
            "tables_artifact": {
                "repository_relative_path": "tables_tok",
                "git_tree_sha1": linked_checks["tables_tree_sha1"],
                "file_count": linked_checks["tables_file_count"],
                "canonical_content_list_sha256": linked_checks[
                    "tables_canonical_content_list_sha256"
                ],
            },
            "request_artifact": {
                "repository_relative_path": "request_tok",
                "git_tree_sha1": linked_checks["request_tree_sha1"],
                "file_count": linked_checks["request_file_count"],
                "canonical_content_list_sha256": linked_checks[
                    "request_canonical_content_list_sha256"
                ],
            },
        },
    }


def _absolute_without_symlinks(path: Path, label: str) -> Path:
    absolute = Path(os.path.abspath(path))
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise RepresentativeEnvironmentSourceError(f"{label} does not exist") from exc
    if path.is_symlink() or absolute != resolved:
        raise RepresentativeEnvironmentSourceError(f"{label} must not use symlinks")
    return resolved


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _cache_checkouts(cache_root: Path, project_root: Path) -> tuple[Path, Path]:
    cache = _absolute_without_symlinks(cache_root, "official source cache root")
    project = _absolute_without_symlinks(project_root, "project root")
    if (
        cache == project
        or _is_relative_to(cache, project)
        or _is_relative_to(project, cache)
    ):
        raise RepresentativeEnvironmentSourceError(
            "official source cache and project root must be disjoint"
        )
    if not cache.is_dir():
        raise RepresentativeEnvironmentSourceError("official source cache root is not a directory")

    hybridqa = _absolute_without_symlinks(
        cache / HYBRIDQA_CHECKOUT_DIRECTORY, "HybridQA checkout"
    )
    wikitables = _absolute_without_symlinks(
        cache / WIKITABLES_CHECKOUT_DIRECTORY, "WikiTables checkout"
    )
    for checkout, label in ((hybridqa, "HybridQA"), (wikitables, "WikiTables")):
        if checkout.parent != cache or not checkout.is_dir():
            raise RepresentativeEnvironmentSourceError(
                f"{label} checkout is not the fixed child of the source cache"
            )
        git_directory = checkout / ".git"
        if git_directory.is_symlink() or not git_directory.is_dir():
            raise RepresentativeEnvironmentSourceError(
                f"{label} checkout is not a nonsymlink Git repository"
            )

    required_directories = (
        (hybridqa / "released_data", "HybridQA released_data"),
        (wikitables / "tables_tok", "WikiTables tables_tok"),
        (wikitables / "request_tok", "WikiTables request_tok"),
    )
    for directory, label in required_directories:
        resolved = _absolute_without_symlinks(directory, label)
        if not resolved.is_dir():
            raise RepresentativeEnvironmentSourceError(f"{label} is not a directory")
    return hybridqa, wikitables


def _run_git_text(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
    )
    if result.returncode != 0:
        raise RepresentativeEnvironmentSourceError(
            f"Git metadata check failed ({' '.join(arguments)})"
        )
    return result.stdout.strip()


def _git_blob(repository: Path, commit: str, repository_relative_path: str) -> bytes:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "cat-file",
            "blob",
            f"{commit}:{repository_relative_path}",
        ],
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
    )
    if result.returncode != 0:
        raise RepresentativeEnvironmentSourceError(
            f"pinned Git blob is unavailable: {repository_relative_path}"
        )
    return result.stdout


def _verify_repository(
    repository: Path,
    source: dict[str, Any],
    subtree_fields: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    expected_remote = source.get("repository_url")
    observed_remote = _run_git_text(repository, "remote", "get-url", "origin")
    if observed_remote not in {expected_remote, str(expected_remote).removesuffix(".git")}:
        raise RepresentativeEnvironmentSourceError("official source origin differs from the pin")
    if _run_git_text(repository, "status", "--porcelain", "--untracked-files=all"):
        raise RepresentativeEnvironmentSourceError("official source checkout has local changes")

    observed = {
        "pinned_commit": _run_git_text(repository, "rev-parse", "HEAD"),
        "git_tree_sha1": _run_git_text(repository, "show", "-s", "--format=%T", "HEAD"),
    }
    for source_field, repository_path in subtree_fields:
        observed[source_field] = _run_git_text(
            repository, "rev-parse", f"HEAD:{repository_path}"
        )
    for field, value in observed.items():
        expected = source.get(field)
        if value != expected:
            raise RepresentativeEnvironmentSourceError(
                f"official source {field} differs from the pin"
            )
    return observed


def _validate_extracted_contract(contract: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    _exact_value(
        contract.get("schema_version"),
        "representative_environment_source_contract_v0_1",
        "representative environment source-contract version",
    )
    question_source = _object(contract.get("question_source"), "question source")
    linked_source = _object(
        contract.get("linked_environment_source"), "linked environment source"
    )
    for field, expected in (
        ("source_id", QUESTION_SOURCE_ID),
        ("checkout_directory", HYBRIDQA_CHECKOUT_DIRECTORY),
        ("repository_url", EXPECTED_QUESTION_SOURCE["repository_url"]),
        ("pinned_commit", EXPECTED_QUESTION_SOURCE["pinned_commit"]),
        ("git_tree_sha1", EXPECTED_QUESTION_SOURCE["git_tree_sha1"]),
        (
            "released_data_tree_sha1",
            EXPECTED_QUESTION_SOURCE["released_data_tree_sha1"],
        ),
    ):
        _exact_value(question_source.get(field), expected, f"question source {field}")
    dev_artifact = _object(question_source.get("dev_artifact"), "official dev artifact")
    for field, expected in (
        ("repository_relative_path", DEV_ARTIFACT_PATH),
        ("sha256", EXPECTED_QUESTION_SOURCE["dev_sha256"]),
        ("record_count", EXPECTED_QUESTION_SOURCE["dev_record_count"]),
        (
            "question_id_set_sha256",
            EXPECTED_QUESTION_SOURCE["dev_question_id_set_sha256"],
        ),
    ):
        _exact_value(dev_artifact.get(field), expected, f"official dev artifact {field}")

    for field, expected in (
        ("source_id", LINKED_SOURCE_ID),
        ("checkout_directory", WIKITABLES_CHECKOUT_DIRECTORY),
        ("repository_url", EXPECTED_LINKED_SOURCE["repository_url"]),
        ("pinned_commit", EXPECTED_LINKED_SOURCE["pinned_commit"]),
        ("git_tree_sha1", EXPECTED_LINKED_SOURCE["git_tree_sha1"]),
    ):
        _exact_value(linked_source.get(field), expected, f"linked source {field}")
    for artifact_field, path, tree_field, count_field, content_hash_field in (
        (
            "tables_artifact",
            "tables_tok",
            "tables_tree_sha1",
            "tables_file_count",
            "tables_canonical_content_list_sha256",
        ),
        (
            "request_artifact",
            "request_tok",
            "request_tree_sha1",
            "request_file_count",
            "request_canonical_content_list_sha256",
        ),
    ):
        artifact = _object(linked_source.get(artifact_field), artifact_field)
        for field, expected in (
            ("repository_relative_path", path),
            ("git_tree_sha1", EXPECTED_LINKED_SOURCE[tree_field]),
            ("file_count", EXPECTED_LINKED_SOURCE[count_field]),
            (
                "canonical_content_list_sha256",
                EXPECTED_LINKED_SOURCE[content_hash_field],
            ),
        ):
            _exact_value(artifact.get(field), expected, f"{artifact_field} {field}")
    return question_source, linked_source


def verify_source_cache(
    cache_root: Path | str,
    contract: dict[str, Any],
    project_root: Path | str,
) -> dict[str, Any]:
    """Verify both fixed source checkouts without exposing their local paths."""

    source_contract = _object(contract, "representative environment source contract")
    question_source, linked_source = _validate_extracted_contract(source_contract)
    hybridqa, wikitables = _cache_checkouts(Path(cache_root), Path(project_root))

    question_identity = _verify_repository(
        hybridqa,
        question_source,
        (("released_data_tree_sha1", "released_data"),),
    )
    linked_identity = _verify_repository(
        wikitables,
        {
            **linked_source,
            "tables_tree_sha1": _object(
                linked_source.get("tables_artifact"), "tables artifact"
            ).get("git_tree_sha1"),
            "request_tree_sha1": _object(
                linked_source.get("request_artifact"), "request artifact"
            ).get("git_tree_sha1"),
        },
        (("tables_tree_sha1", "tables_tok"), ("request_tree_sha1", "request_tok")),
    )
    dev_artifact = _object(question_source.get("dev_artifact"), "official dev artifact")
    dev_bytes = _git_blob(
        hybridqa,
        str(question_source.get("pinned_commit")),
        str(dev_artifact.get("repository_relative_path")),
    )
    if sha256_bytes(dev_bytes) != dev_artifact.get("sha256"):
        raise RepresentativeEnvironmentSourceError("official dev blob SHA-256 differs from the pin")

    return {
        "status": "verified_exact_official_pins",
        "question_source": {
            "source_id": question_source.get("source_id"),
            **question_identity,
            "dev_artifact": {
                "repository_relative_path": dev_artifact.get("repository_relative_path"),
                "sha256": dev_artifact.get("sha256"),
            },
        },
        "linked_environment_source": {
            "source_id": linked_source.get("source_id"),
            **linked_identity,
        },
    }


def _decode_json_blob(payload: bytes, label: str) -> Any:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RepresentativeEnvironmentSourceError(f"{label} is not UTF-8 JSON") from exc
    try:
        return strict_json_loads(text)
    except (ValueError, TypeError) as exc:
        raise RepresentativeEnvironmentSourceError(f"{label} is not strict JSON") from exc


def _safe_question_id(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\r" in value
        or "\n" in value
        or "\x00" in value
    ):
        raise RepresentativeEnvironmentSourceError(f"{label} is not a safe question ID")
    return value


def _safe_table_id(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(character in value for character in ("/", "\\", "\r", "\n", "\x00"))
    ):
        raise RepresentativeEnvironmentSourceError(f"{label} is not a safe table ID")
    return value


def _safe_document_id(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\r" in value
        or "\n" in value
        or "\x00" in value
    ):
        raise RepresentativeEnvironmentSourceError(
            f"{label} is not a safe linked-document ID"
        )
    return value


def _cell_parts(cell: Any, label: str) -> tuple[str, list[str]]:
    if (
        not isinstance(cell, list)
        or len(cell) != 2
        or not isinstance(cell[0], str)
        or not isinstance(cell[1], list)
    ):
        raise RepresentativeEnvironmentSourceError(f"{label} has the wrong cell shape")
    links: list[str] = []
    for link_index, document_id in enumerate(cell[1]):
        links.append(
            _safe_document_id(document_id, f"{label} linked document {link_index}")
        )
    return cell[0], links


def project_environment(table_id: str, table: Any, request: Any) -> dict[str, Any]:
    """Purely project one table plus its linked-document closure.

    Row/cell order, scalar text, and each cell's link order are preserved.  The
    linked-document array is deduplicated and sorted by unsigned UTF-8 bytes.
    Unlinked request entries and non-allowlisted table metadata are excluded.
    """

    safe_table_id = _safe_table_id(table_id, "table ID")
    table_object = _object(table, f"{safe_table_id} table")
    request_object = _object(request, f"{safe_table_id} request")
    if table_object.get("uid") != safe_table_id:
        raise RepresentativeEnvironmentSourceError("table uid differs from its selected table ID")
    title = table_object.get("title")
    section_title = table_object.get("section_title")
    header = table_object.get("header")
    data = table_object.get("data")
    if not isinstance(title, str) or not isinstance(section_title, str):
        raise RepresentativeEnvironmentSourceError("table title/section_title must be strings")
    if not isinstance(header, list) or not header or not isinstance(data, list) or not data:
        raise RepresentativeEnvironmentSourceError("table header/data must be nonempty arrays")
    for key, value in request_object.items():
        _safe_document_id(key, "request document ID")
        if not isinstance(value, str):
            raise RepresentativeEnvironmentSourceError(
                "request must map document-ID strings to passage-text strings"
            )

    linked_document_ids: set[str] = set()
    columns: list[dict[str, Any]] = []
    for column_index, header_cell in enumerate(header):
        label, links = _cell_parts(header_cell, f"header column {column_index}")
        linked_document_ids.update(links)
        columns.append(
            {
                "column_index": column_index,
                "label": label,
                "linked_document_ids": links,
            }
        )

    rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(data):
        if not isinstance(row, list) or len(row) != len(header):
            raise RepresentativeEnvironmentSourceError(
                f"table row {row_index} width differs from the header"
            )
        cells: list[dict[str, Any]] = []
        for column_index, cell in enumerate(row):
            text, links = _cell_parts(cell, f"row {row_index} column {column_index}")
            linked_document_ids.update(links)
            cells.append(
                {
                    "column_index": column_index,
                    "text": text,
                    "linked_document_ids": links,
                }
            )
        rows.append({"row_index": row_index, "cells": cells})

    missing = sorted(
        linked_document_ids - set(request_object), key=lambda value: value.encode("utf-8")
    )
    if missing:
        raise RepresentativeEnvironmentSourceError(
            f"table link closure has {len(missing)} document(s) absent from request"
        )
    linked_documents = [
        {"document_id": document_id, "text": request_object[document_id]}
        for document_id in sorted(linked_document_ids, key=lambda value: value.encode("utf-8"))
    ]
    return {
        "source_split": "dev",
        "table_id": safe_table_id,
        "title": title,
        "section_title": section_title,
        "columns": [
            {
                "column_index": column["column_index"],
                "text": column["label"],
                "linked_document_ids": column["linked_document_ids"],
            }
            for column in columns
        ],
        "rows": rows,
        "linked_documents": linked_documents,
        "scope_contract": {
            "table_scope": "full_selected_question_table",
            "document_scope": "table_link_closure",
            "question_or_answer_guided_pruning": False,
            "oracle_document_selection": False,
            "truncation": "none",
            "external_retrieval": False,
            "dataset_provided_question_table_binding": True,
            "table_retrieval_evaluated": False,
            "full_table_link_closure_supplied": True,
        },
    }


def _expected_question_map(expected_questions: Any) -> dict[str, str]:
    if isinstance(expected_questions, Mapping):
        records: Iterable[Any]
        if "question_id" in expected_questions and "question" in expected_questions:
            records = [expected_questions]
        elif all(isinstance(value, str) for value in expected_questions.values()):
            result: dict[str, str] = {}
            for question_id, question in expected_questions.items():
                safe_id = _safe_question_id(question_id, "expected question ID")
                if not question.strip():
                    raise RepresentativeEnvironmentSourceError(
                        "expected question text must be nonempty"
                    )
                result[safe_id] = question
            return result
        else:
            records = expected_questions.values()
    elif isinstance(expected_questions, Iterable) and not isinstance(
        expected_questions, (str, bytes)
    ):
        records = expected_questions
    else:
        raise RepresentativeEnvironmentSourceError(
            "expected questions must be records or a question-ID/text mapping"
        )

    result = {}
    for index, record in enumerate(records):
        item = _object(record, f"expected question {index}")
        question_id = _safe_question_id(
            item.get("question_id"), f"expected question {index} ID"
        )
        question = item.get("question")
        if not isinstance(question, str) or not question.strip():
            raise RepresentativeEnvironmentSourceError(
                f"expected question {index} text must be nonempty"
            )
        if question_id in result:
            raise RepresentativeEnvironmentSourceError("expected question IDs are not unique")
        result[question_id] = question
    return result


def _selected_ids(values: Sequence[str] | Iterable[str]) -> list[str]:
    if isinstance(values, (str, bytes)):
        raise RepresentativeEnvironmentSourceError("selected question IDs must be an array")
    result: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        question_id = _safe_question_id(value, f"selected question ID {index}")
        if question_id in seen:
            raise RepresentativeEnvironmentSourceError("selected question IDs are not unique")
        seen.add(question_id)
        result.append(question_id)
    if not result:
        raise RepresentativeEnvironmentSourceError("selected question ID array is empty")
    return result


def _source_artifact(source_id: str, path: str, payload: bytes) -> dict[str, str]:
    return {
        "source_id": source_id,
        "repository_relative_path": path,
        "sha256": sha256_bytes(payload),
    }


def deduplicate_source_artifacts(artifacts: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Canonicalize a portable selected-source inventory.

    Repeated bindings to the same source/path/hash collapse.  Conflicting hashes
    for one logical source path are rejected rather than silently overwritten.
    """

    by_path: dict[tuple[str, str], dict[str, str]] = {}
    for index, artifact in enumerate(artifacts):
        item = _object(artifact, f"selected source artifact {index}")
        if set(item) != {"source_id", "repository_relative_path", "sha256"}:
            raise RepresentativeEnvironmentSourceError(
                f"selected source artifact {index} fields differ from the allowlist"
            )
        source_id = item.get("source_id")
        path = item.get("repository_relative_path")
        digest = item.get("sha256")
        if not isinstance(source_id, str) or not source_id or "\r" in source_id or "\n" in source_id:
            raise RepresentativeEnvironmentSourceError(
                f"selected source artifact {index} has an invalid source ID"
            )
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or "\\" in path
            or "\r" in path
            or "\n" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
        ):
            raise RepresentativeEnvironmentSourceError(
                f"selected source artifact {index} has a nonportable path"
            )
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise RepresentativeEnvironmentSourceError(
                f"selected source artifact {index} has an invalid SHA-256"
            )
        key = (source_id, path)
        previous = by_path.get(key)
        if previous is not None and previous["sha256"] != digest:
            raise RepresentativeEnvironmentSourceError(
                "one selected source path has conflicting SHA-256 values"
            )
        by_path[key] = {
            "source_id": source_id,
            "repository_relative_path": path,
            "sha256": digest,
        }
    return sorted(
        by_path.values(),
        key=lambda item: (
            item["source_id"].encode("utf-8"),
            item["repository_relative_path"].encode("utf-8"),
        ),
    )


def load_selected_environment_bundle(
    cache_root: Path | str,
    contract: dict[str, Any],
    selected_question_ids: Sequence[str] | Iterable[str],
    expected_questions: Any,
    project_root: Path | str,
) -> dict[str, Any]:
    """Load the exact selected environments from pinned Git blobs.

    The result contains only safe portable source references.  It never returns
    raw official-dev records and therefore cannot return their answer fields.
    """

    selected_ids = _selected_ids(selected_question_ids)
    expected_by_id = _expected_question_map(expected_questions)
    before = verify_source_cache(cache_root, contract, project_root)
    hybridqa, wikitables = _cache_checkouts(Path(cache_root), Path(project_root))
    source_contract = _object(contract, "representative environment source contract")
    question_source = _object(source_contract.get("question_source"), "question source")
    linked_source = _object(
        source_contract.get("linked_environment_source"), "linked environment source"
    )
    dev_artifact = _object(question_source.get("dev_artifact"), "official dev artifact")

    dev_bytes = _git_blob(
        hybridqa,
        str(question_source.get("pinned_commit")),
        str(dev_artifact.get("repository_relative_path")),
    )
    if sha256_bytes(dev_bytes) != dev_artifact.get("sha256"):
        raise RepresentativeEnvironmentSourceError("official dev blob changed during extraction")
    dev_records = _decode_json_blob(dev_bytes, "official dev blob")
    if not isinstance(dev_records, list) or len(dev_records) != dev_artifact.get("record_count"):
        raise RepresentativeEnvironmentSourceError("official dev record count differs from the pin")

    source_questions: dict[str, tuple[str, str]] = {}
    for index, raw_record in enumerate(dev_records):
        record = _object(raw_record, f"official dev record {index}")
        question_id = _safe_question_id(
            record.get("question_id"), f"official dev record {index} question ID"
        )
        question = record.get("question")
        table_id = _safe_table_id(
            record.get("table_id"), f"official dev record {index} table ID"
        )
        if not isinstance(question, str) or not question.strip():
            raise RepresentativeEnvironmentSourceError(
                f"official dev record {index} question text is invalid"
            )
        if question_id in source_questions:
            raise RepresentativeEnvironmentSourceError("official dev question IDs are not unique")
        # Deliberately retain only the exact three-field safe projection.  The
        # source record's official answer and any other metadata are discarded.
        source_questions[question_id] = (question, table_id)
    del dev_records
    if canonical_string_set_sha256(source_questions) != dev_artifact.get(
        "question_id_set_sha256"
    ):
        raise RepresentativeEnvironmentSourceError(
            "official dev question-ID set differs from the pin"
        )

    selected_source_questions: list[tuple[str, str, str]] = []
    for question_id in selected_ids:
        if question_id not in expected_by_id:
            raise RepresentativeEnvironmentSourceError(
                "selected question is absent from the expected question projection"
            )
        source_value = source_questions.get(question_id)
        if source_value is None:
            raise RepresentativeEnvironmentSourceError(
                "selected question is absent from the official dev source"
            )
        source_question, table_id = source_value
        if source_question != expected_by_id[question_id]:
            raise RepresentativeEnvironmentSourceError(
                "selected question text differs between the expected view and official dev"
            )
        selected_source_questions.append((question_id, source_question, table_id))

    source_artifacts: list[dict[str, str]] = []
    dev_reference = _source_artifact(QUESTION_SOURCE_ID, DEV_ARTIFACT_PATH, dev_bytes)
    source_artifacts.append(dev_reference)
    resources_by_table: dict[str, dict[str, Any]] = {}
    environment_resources: list[dict[str, Any]] = []
    for _, _, table_id in selected_source_questions:
        if table_id in resources_by_table:
            continue
        table_path = f"tables_tok/{table_id}.json"
        request_path = f"request_tok/{table_id}.json"
        for working_path, label in (
            (wikitables / table_path, "selected table source file"),
            (wikitables / request_path, "selected request source file"),
        ):
            if working_path.is_symlink() or not working_path.is_file():
                raise RepresentativeEnvironmentSourceError(f"{label} is missing or a symlink")
        table_bytes = _git_blob(
            wikitables, str(linked_source.get("pinned_commit")), table_path
        )
        request_bytes = _git_blob(
            wikitables, str(linked_source.get("pinned_commit")), request_path
        )
        table = _decode_json_blob(table_bytes, "selected table blob")
        request = _decode_json_blob(request_bytes, "selected request blob")
        resource = project_environment(table_id, table, request)
        resources_by_table[table_id] = resource
        environment_resources.append(resource)
        source_artifacts.append(_source_artifact(LINKED_SOURCE_ID, table_path, table_bytes))
        source_artifacts.append(
            _source_artifact(LINKED_SOURCE_ID, request_path, request_bytes)
        )

    questions = [
        {
            "selection_index": selection_index,
            "question_id": question_id,
            "question": question,
            "table_id": table_id,
        }
        for selection_index, (question_id, question, table_id) in enumerate(
            selected_source_questions, start=1
        )
    ]
    selected_source_artifacts = deduplicate_source_artifacts(source_artifacts)
    after = verify_source_cache(cache_root, contract, project_root)
    if after != before:
        raise RepresentativeEnvironmentSourceError(
            "official source identity changed during extraction"
        )
    # Hash construction here is intentional even though the caller may bind the
    # complete list again.  It ensures every element is JSON-canonicalizable and
    # catches nonportable values before the bundle leaves this trust boundary.
    canonical_json_sha256(selected_source_artifacts)
    return {
        "questions": questions,
        "environment_resources": environment_resources,
        "selected_source_artifacts": selected_source_artifacts,
        "source_verification": after,
    }
