#!/usr/bin/env python3
"""Build deterministic, leakage-reduced HybridQA annotation role splits.

The command deliberately refuses to allocate questions when the historical-ID
audit is incomplete, unless the researcher supplies an explicit override. An
override is recorded in the output manifest and is not suitable for a frozen
corpus release.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _common import (
    canonical_json_sha256,
    canonical_string_set_sha256,
    first_string,
    iter_json_records,
    read_json,
    sha256_file,
    stable_rank,
    write_json,
    write_jsonl,
)
from build_historical_manifest import EXPECTED as HISTORICAL_EXPECTED
from build_historical_manifest import ids_from_file, named_locked_ids


ROLE_ORDER = ("annotation_schema_pilot", "annotation_train", "annotation_dev", "locked_eval")
ID_KEYS = ("question_id", "qid", "id")
REQUIRED_HISTORICAL_PATHS = (
    "data_analysis/week1_sample_100.jsonl",
    "evaluation/week2_eval_ids.json",
    "evaluation/week3_engineering_dev_ids.json",
    "evaluation/week3_locked_eval_ids.json",
    "evaluation/week3_split_manifest.json",
)
KNOWN_HISTORICAL_COUNTS = {
    "data_analysis/week1_sample_100.jsonl": 100,
    "evaluation/week2_eval_ids.json": 50,
}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
OFFICIAL_HYBRIDQA_COMMIT = "db22fda8c5951438fade3c69d75b350335ba93b3"
OFFICIAL_HYBRIDQA_REPOSITORY = "https://github.com/wenhuchen/HybridQA.git"
QUESTION_ID_SET_HASH_ALGORITHM = (
    "Deduplicate IDs; reject CR/LF; sort by unsigned UTF-8 byte sequence; "
    "concatenate each UTF-8 ID followed by LF; SHA-256 the resulting bytes."
)
OFFICIAL_QUESTION_ARTIFACTS = {
    "released_data/train.json": {
        "sha256": "b33aa73638959a2383e1e1638fd6abe87818b7379c7a42eac1621475d2d959e2",
        "record_count": 62682,
        "question_id_set_sha256": "fede3106c7430f731a15bb466ebb4e1c7c74e7e9b11df0d3565ab989c1f68dd2",
    },
    "released_data/dev.json": {
        "sha256": "424272b233735a70ed8ef5af4a615373d114f472168c686c4370d54c92d58ac1",
        "record_count": 3466,
        "question_id_set_sha256": "70ee935abae8409251e0858a46d7a92f7875e2bfa0d8084f8ab3bb1cd591f584",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", required=True, type=Path, help="Official HybridQA question JSON/JSONL")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Canonical root containing the five historical artifacts and provenance receipt",
    )
    parser.add_argument(
        "--historical-manifest",
        type=Path,
        default=Path("data_construction/manifests/historical_exposed_ids.json"),
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=Path("data_construction/manifests/source_manifest_v0_1.json"),
        help="Manifest whose pinned artifact hash must match --questions",
    )
    parser.add_argument("--output", type=Path, default=Path("data_construction/pilot/questions.jsonl"))
    parser.add_argument(
        "--role-output-dir",
        type=Path,
        help="Directory for non-pilot role files; defaults to a role_splits directory beside --output",
    )
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("data_construction/manifests/split_manifest_v0_1.json"),
    )
    parser.add_argument("--seed", default="hybridqa-semantic-topology-v0.1")
    parser.add_argument("--source-split", choices=("train", "dev", "test"))
    parser.add_argument("--pilot-count", type=nonnegative_int, default=30)
    parser.add_argument("--train-count", type=nonnegative_int, default=0)
    parser.add_argument("--dev-count", type=nonnegative_int, default=0)
    parser.add_argument("--locked-eval-count", type=nonnegative_int, default=0)
    parser.add_argument(
        "--allow-incomplete-history",
        action="store_true",
        help="Diagnostic-only override; output is marked non-releaseable",
    )
    parser.add_argument(
        "--allow-unverified-source",
        action="store_true",
        help="Diagnostic-only override when source manifest/hash verification is unavailable",
    )
    return parser.parse_args()


def nonnegative_int(value: str) -> int:
    result = int(value)
    if result < 0:
        raise argparse.ArgumentTypeError("counts must be non-negative")
    return result


def collect_ids(value: Any) -> set[str]:
    """Collect explicit question IDs without mistaking counts or hashes for IDs."""

    collected: set[str] = set()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, (str, int)):
                collected.add(str(item))
            elif isinstance(item, dict):
                identifier = first_string(item, ID_KEYS)
                if identifier:
                    collected.add(identifier)
    elif isinstance(value, dict):
        identifier = first_string(value, ID_KEYS)
        if identifier:
            collected.add(identifier)
        for key, child in value.items():
            key_lower = key.lower()
            if key_lower.endswith("ids") or key_lower in {
                "records",
                "questions",
                "exposed",
                "forbidden",
                "locked_eval",
                "sources",
            }:
                collected.update(collect_ids(child))
    return collected


def historical_release_errors(manifest: dict[str, Any], project_root: Path) -> list[str]:
    """Validate the builder's complete-history contract before releasing a split."""
    errors: list[str] = []
    if manifest.get("schema_version") != "historical_exposed_ids_v0_1":
        errors.append("unsupported historical manifest schema_version")
    if manifest.get("audit_status") != "complete" or manifest.get("is_complete") is not True:
        errors.append("historical audit is not complete")
    if manifest.get("recovery_provenance_status") != "verified":
        errors.append("historical recovery provenance is not verified")
    for key in (
        "missing_required_files",
        "required_files_with_no_question_ids",
        "known_expected_count_mismatches",
        "recovery_provenance_errors",
    ):
        if manifest.get(key) not in ([], None):
            errors.append(f"historical manifest reports non-empty {key}")

    provenance = manifest.get("recovery_provenance")
    if not isinstance(provenance, dict):
        errors.append("historical manifest lacks recovery_provenance")
    else:
        if provenance.get("schema_version") != "historical_recovery_provenance_v0_1":
            errors.append("historical recovery provenance schema_version is invalid")
        if provenance.get("status") != "researcher_approved_authoritative":
            errors.append("historical recovery provenance is not researcher-approved")
        if provenance.get("verification") != "verified":
            errors.append("historical recovery provenance summary is not verified")
        if provenance.get("authority_kind") != "git_commit":
            errors.append("v0.1 historical release verification supports only authority_kind=git_commit")
        authority_identity = provenance.get("authority_identity")
        if not isinstance(authority_identity, str) or not authority_identity.strip():
            errors.append("historical recovery authority_identity is missing")
        elif provenance.get("authority_kind") == "git_commit" and not re.fullmatch(
            r"[0-9a-f]{40}", authority_identity
        ):
            errors.append("historical recovery git authority must be a full lowercase 40-hex commit OID")

    raw_sources = manifest.get("source_files")
    source_entries = {
        entry.get("path"): entry
        for entry in raw_sources
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    } if isinstance(raw_sources, list) else {}
    if set(source_entries) != set(REQUIRED_HISTORICAL_PATHS):
        errors.append("historical source file inventory is not the exact required five-file set")

    raw_source_ids = manifest.get("source_question_ids")
    source_ids = raw_source_ids if isinstance(raw_source_ids, dict) else {}
    safe_source_ids: dict[str, list[str]] = {}
    union_ids: set[str] = set()
    for path in REQUIRED_HISTORICAL_PATHS:
        entry = source_entries.get(path)
        identifiers = source_ids.get(path)
        if not isinstance(entry, dict):
            continue
        if entry.get("status") != "present":
            errors.append(f"historical source is not present and readable: {path}")
        if not isinstance(entry.get("sha256"), str) or not SHA256_PATTERN.fullmatch(entry["sha256"]):
            errors.append(f"historical source has invalid SHA-256: {path}")
        if not isinstance(identifiers, list) or not identifiers or not all(isinstance(item, str) for item in identifiers):
            errors.append(f"historical source has no explicit string ID inventory: {path}")
            continue
        safe_source_ids[path] = identifiers
        if len(identifiers) != len(set(identifiers)):
            errors.append(f"historical source has duplicate IDs: {path}")
        if entry.get("question_id_count") != len(identifiers):
            errors.append(f"historical source ID count disagrees with inventory: {path}")
        known_count = KNOWN_HISTORICAL_COUNTS.get(path)
        if known_count is not None and len(identifiers) != known_count:
            errors.append(f"historical source violates known expected ID count: {path}")
        union_ids.update(identifiers)

    exposed = manifest.get("exposed_question_ids")
    forbidden = manifest.get("forbidden_future_training_ids")
    exposed_is_string_list = isinstance(exposed, list) and all(
        isinstance(identifier, str) for identifier in exposed
    )
    forbidden_is_string_list = isinstance(forbidden, list) and all(
        isinstance(identifier, str) for identifier in forbidden
    )
    if (
        not exposed_is_string_list
        or set(exposed) != union_ids
        or len(exposed) != len(union_ids)
    ):
        errors.append("exposed_question_ids is not the exact union of historical source inventories")
    if (
        not forbidden_is_string_list
        or set(forbidden) != union_ids
        or len(forbidden) != len(union_ids)
    ):
        errors.append("forbidden_future_training_ids is not the exact historical union")
    locked = manifest.get("locked_eval_question_ids")
    locked_is_string_list = isinstance(locked, list) and all(
        isinstance(identifier, str) for identifier in locked
    )
    if not locked_is_string_list or not set(locked).issubset(union_ids):
        errors.append("locked_eval_question_ids is not a subset of historical exposure")

    root = project_root.resolve()
    observed_union: set[str] = set()
    observed_locked: set[str] = set()
    for path, _, locked_mode in HISTORICAL_EXPECTED:
        actual_path = (root / path).resolve()
        try:
            actual_path.relative_to(root)
        except ValueError:
            errors.append(f"historical source path escapes project root: {path}")
            continue
        entry = source_entries.get(path)
        if not actual_path.is_file():
            errors.append(f"historical source file is unavailable for re-verification: {path}")
            continue
        if not isinstance(entry, dict) or sha256_file(actual_path) != entry.get("sha256"):
            errors.append(f"historical source file hash changed or is unrecorded: {path}")
            continue
        try:
            actual_ids = ids_from_file(actual_path)
        except (OSError, ValueError) as exc:
            errors.append(f"historical source file cannot be re-read: {path}: {exc}")
            continue
        if set(safe_source_ids.get(path, [])) != actual_ids:
            errors.append(f"historical source ID inventory changed: {path}")
        observed_union.update(actual_ids)
        if locked_mode == "all":
            observed_locked.update(actual_ids)
        elif locked_mode == "named_only":
            observed_locked.update(named_locked_ids(read_json(actual_path)))
    observed_union.update(observed_locked)
    if observed_union != union_ids:
        errors.append("recomputed historical ID union disagrees with the manifest")
    if locked_is_string_list and set(locked) != observed_locked:
        errors.append("recomputed locked-eval IDs disagree with the manifest")

    provenance_artifact = provenance.get("artifact") if isinstance(provenance, dict) else None
    provenance_document: dict[str, Any] | None = None
    if not isinstance(provenance_artifact, dict):
        errors.append("historical recovery provenance has no verifiable repository artifact")
    else:
        provenance_relative = provenance_artifact.get("repository_relative_path")
        if not isinstance(provenance_relative, str):
            errors.append("historical recovery provenance artifact path is missing")
        else:
            provenance_path = (root / provenance_relative).resolve()
            try:
                provenance_path.relative_to(root)
            except ValueError:
                errors.append("historical recovery provenance artifact escapes project root")
            else:
                if not provenance_path.is_file():
                    errors.append("historical recovery provenance artifact is unavailable")
                elif sha256_file(provenance_path) != provenance_artifact.get("sha256"):
                    errors.append("historical recovery provenance artifact hash changed")
                else:
                    raw_provenance = read_json(provenance_path)
                    if isinstance(raw_provenance, dict):
                        provenance_document = raw_provenance
                    else:
                        errors.append("historical recovery provenance artifact is not an object")
    if provenance_document is not None:
        for key in ("schema_version", "status", "authority_kind", "authority_identity"):
            if provenance_document.get(key) != provenance.get(key):
                errors.append(f"historical recovery provenance summary disagrees on {key}")
        raw_files = provenance_document.get("files")
        provenance_files = {
            item.get("path"): item
            for item in raw_files
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        } if isinstance(raw_files, list) else {}
        if set(provenance_files) != set(REQUIRED_HISTORICAL_PATHS):
            errors.append("historical recovery provenance lacks the exact five-file inventory")
        for path in REQUIRED_HISTORICAL_PATHS:
            source_entry = source_entries.get(path)
            provenance_entry = provenance_files.get(path)
            if not isinstance(source_entry, dict) or not isinstance(provenance_entry, dict):
                continue
            if provenance_entry.get("sha256") != source_entry.get("sha256"):
                errors.append(f"historical recovery provenance hash mismatch: {path}")
            if provenance_entry.get("question_id_count") != source_entry.get("question_id_count"):
                errors.append(f"historical recovery provenance count mismatch: {path}")

        if provenance_document.get("authority_kind") == "git_commit":
            revision = provenance_document.get("authority_identity")
            git_probe = subprocess.run(
                ["git", "-C", str(root), "cat-file", "-e", f"{revision}^{{commit}}"],
                capture_output=True,
                check=False,
            )
            if git_probe.returncode != 0:
                errors.append("historical recovery git authority commit is unavailable in the project repository")
            else:
                for path in REQUIRED_HISTORICAL_PATHS:
                    committed = subprocess.run(
                        ["git", "-C", str(root), "show", f"{revision}:{path}"],
                        capture_output=True,
                        check=False,
                    )
                    if committed.returncode != 0:
                        errors.append(f"historical recovery git authority lacks {path}")
                    else:
                        if hashlib.sha256(committed.stdout).hexdigest() != source_entries[path].get("sha256"):
                            errors.append(f"historical source differs from git authority: {path}")
        else:
            errors.append("v0.1 historical release verification supports only a live git commit authority")
    return errors


def normalize_question(record: dict[str, Any], role: str, source_split: str) -> dict[str, Any]:
    question_id = first_string(record, ID_KEYS)
    question = first_string(record, ("question", "query", "text"))
    table_id = first_string(record, ("table_id", "table", "tableId"))
    if not question_id or not question:
        raise ValueError("source record lacks question_id/id or question text")
    # Do not copy answer, answer-node, document locator, or model/evaluator labels.
    return {
        "question_id": question_id,
        "question": question,
        "table_id": table_id,
        "dataset_role": role,
        "source_split": first_string(record, ("split", "source_split")) or source_split,
        "annotation_visibility": "question_and_table_identity_only",
    }


def verify_source_manifest(manifest: dict[str, Any], source_sha256: str) -> dict[str, Any] | None:
    if (
        manifest.get("schema_version") != "source_manifest_v0_1"
        or manifest.get("dataset") != "HybridQA"
        or manifest.get("source_policy") != "official_primary_sources_only"
        or manifest.get("retrieval_status") != "available_and_locally_verified"
    ):
        return None
    source_id_inventory = manifest.get("source_id_inventory")
    inventory_sets = (
        source_id_inventory.get("question_id_sets", {})
        if isinstance(source_id_inventory, dict)
        else {}
    )
    if (
        not isinstance(source_id_inventory, dict)
        or source_id_inventory.get("canonical_set_hash_algorithm")
        != QUESTION_ID_SET_HASH_ALGORITHM
    ):
        return None
    for upstream in manifest.get("upstreams", []):
        if (
            not isinstance(upstream, dict)
            or upstream.get("source_id") != "hybridqa_questions_and_code"
            or upstream.get("repository_url") != OFFICIAL_HYBRIDQA_REPOSITORY
            or upstream.get("pinned_commit") != OFFICIAL_HYBRIDQA_COMMIT
        ):
            continue
        for artifact in upstream.get("artifacts", []):
            artifact_path = artifact.get("path") if isinstance(artifact, dict) else None
            canonical = OFFICIAL_QUESTION_ARTIFACTS.get(str(artifact_path))
            split_name = Path(str(artifact_path)).stem
            inventory_entry = inventory_sets.get(split_name) if isinstance(inventory_sets, dict) else None
            if (
                isinstance(artifact, dict)
                and canonical is not None
                and artifact.get("sha256") == canonical["sha256"]
                and artifact.get("record_count") == canonical["record_count"]
                and artifact.get("unique_question_id_count") == canonical["record_count"]
                and artifact.get("sha256") == source_sha256
                and isinstance(inventory_entry, dict)
                and inventory_entry.get("count") == canonical["record_count"]
                and inventory_entry.get("canonical_sha256") == canonical["question_id_set_sha256"]
            ):
                return {
                    "source_id": upstream.get("source_id"),
                    "pinned_commit": upstream.get("pinned_commit"),
                    "artifact_path": artifact_path,
                    "artifact_sha256": source_sha256,
                    "record_count": canonical["record_count"],
                    "question_id_set_sha256": canonical["question_id_set_sha256"],
                    "question_id_set_hash_algorithm": QUESTION_ID_SET_HASH_ALGORITHM,
                }
    return None


def portable_input_locator(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return f"<machine-local-input>/{path.name}"


def repository_relative_output_locator(path: Path, project_root: Path) -> str | None:
    """Return a portable output locator only when the path is inside the project."""

    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return None


def main() -> int:
    args = parse_args()
    if not args.questions.is_file():
        raise FileNotFoundError(args.questions)
    if not args.historical_manifest.is_file():
        raise FileNotFoundError(args.historical_manifest)

    source_sha256 = sha256_file(args.questions)
    source_reference = None
    if args.source_manifest.is_file():
        source_reference = verify_source_manifest(read_json(args.source_manifest), source_sha256)
    source_verified = source_reference is not None
    if not source_verified and not args.allow_unverified_source:
        print(
            "Refusing split allocation: question source hash is not present in the official pinned source manifest. "
            "Use --allow-unverified-source only for a diagnostic engineering fixture.",
            file=sys.stderr,
        )
        return 2
    manifest_split = None
    if source_reference:
        artifact_name = Path(str(source_reference.get("artifact_path", ""))).name
        manifest_split = Path(artifact_name).stem if Path(artifact_name).stem in {"train", "dev"} else None
    if args.source_split and manifest_split and args.source_split != manifest_split:
        print(
            f"Refusing split allocation: --source-split={args.source_split!r} conflicts with "
            f"the pinned artifact split {manifest_split!r}.",
            file=sys.stderr,
        )
        return 2

    historical = read_json(args.historical_manifest)
    completeness = historical.get("audit_status") or historical.get("completeness")
    history_errors = historical_release_errors(historical, args.project_root)
    history_complete = not history_errors
    if not history_complete and not args.allow_incomplete_history:
        print(
            "Refusing split allocation: historical exposed-ID audit is incomplete. "
            "Recover the historical manifests or use --allow-incomplete-history for a diagnostic-only sample. "
            f"Validation errors: {'; '.join(history_errors)}",
            file=sys.stderr,
        )
        return 2

    forbidden_ids = collect_ids(historical)
    by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: set[str] = set()
    malformed = 0
    for record in iter_json_records(args.questions):
        identifier = first_string(record, ID_KEYS)
        question = first_string(record, ("question", "query", "text"))
        if not identifier or not question:
            malformed += 1
            continue
        if identifier in by_id:
            duplicate_ids.add(identifier)
            continue
        by_id[identifier] = record

    if duplicate_ids:
        preview = ", ".join(sorted(duplicate_ids)[:5])
        raise ValueError(f"duplicate question IDs in source ({len(duplicate_ids)}): {preview}")
    observed_question_id_set_sha256 = canonical_string_set_sha256(by_id)
    if source_reference and (
        len(by_id) != source_reference.get("record_count")
        or observed_question_id_set_sha256 != source_reference.get("question_id_set_sha256")
    ):
        print(
            "Refusing split allocation: source question-ID inventory does not match the canonical pinned artifact.",
            file=sys.stderr,
        )
        return 2

    candidates = [record for identifier, record in by_id.items() if identifier not in forbidden_ids]
    candidates.sort(key=lambda record: stable_rank(args.seed, first_string(record, ID_KEYS) or ""))

    requested = {
        "annotation_schema_pilot": args.pilot_count,
        "annotation_train": args.train_count,
        "annotation_dev": args.dev_count,
        "locked_eval": args.locked_eval_count,
    }
    total_requested = sum(requested.values())
    if total_requested == 0:
        print("Refusing split allocation: at least one role count must be positive.", file=sys.stderr)
        return 2
    if total_requested > len(candidates):
        raise ValueError(f"requested {total_requested} records but only {len(candidates)} are eligible")

    selected_by_role: dict[str, list[dict[str, Any]]] = {role: [] for role in ROLE_ORDER}
    roles: dict[str, list[str]] = {role: [] for role in ROLE_ORDER}
    offset = 0
    inferred_split = args.source_split or manifest_split or "unknown"
    for role in ROLE_ORDER:
        count = requested[role]
        for record in candidates[offset : offset + count]:
            normalized = normalize_question(record, role, inferred_split)
            selected_by_role[role].append(normalized)
            roles[role].append(normalized["question_id"])
        offset += count

    all_role_ids = [identifier for role in ROLE_ORDER for identifier in roles[role]]
    if len(all_role_ids) != len(set(all_role_ids)):
        raise AssertionError("internal error: role overlap detected")

    role_output_dir = args.role_output_dir or (args.output.parent / "role_splits")
    output_paths = {
        "annotation_schema_pilot": args.output,
        "annotation_train": role_output_dir / "annotation_train.questions.jsonl",
        "annotation_dev": role_output_dir / "annotation_dev.questions.jsonl",
        "locked_eval": role_output_dir / "locked_eval.questions.jsonl",
    }
    resolved_outputs = {role: path.resolve() for role, path in output_paths.items()}
    split_output = args.split_manifest.resolve()
    source_inventory_output = split_output.parent / "source_question_ids.json"
    all_output_paths = set(resolved_outputs.values()) | {split_output, source_inventory_output}
    if len(all_output_paths) != len(resolved_outputs) + 2:
        print("Refusing split allocation: role outputs and split manifest must use distinct paths.", file=sys.stderr)
        return 2
    release_eligible = history_complete and source_verified
    if release_eligible:
        nonportable_outputs = [
            str(resolved_outputs[role])
            for role in ROLE_ORDER
            if selected_by_role[role]
            and repository_relative_output_locator(resolved_outputs[role], args.project_root) is None
        ]
        if repository_relative_output_locator(split_output, args.project_root) is None:
            nonportable_outputs.append(str(split_output))
        if repository_relative_output_locator(source_inventory_output, args.project_root) is None:
            nonportable_outputs.append(str(source_inventory_output))
        if nonportable_outputs:
            print(
                "Refusing release split allocation: the split manifest and every non-empty role output "
                "must remain inside --project-root and use repository-relative locators: "
                f"{nonportable_outputs}",
                file=sys.stderr,
            )
            return 2
    input_paths = {
        args.questions.resolve(),
        args.historical_manifest.resolve(),
        args.source_manifest.resolve(),
    }
    protected_historical_paths = {
        (args.project_root.resolve() / relative).resolve()
        for relative in REQUIRED_HISTORICAL_PATHS
    }
    recovery_artifact = historical.get("recovery_provenance")
    if isinstance(recovery_artifact, dict) and isinstance(recovery_artifact.get("artifact"), dict):
        recovery_path = recovery_artifact["artifact"].get("repository_relative_path")
        if isinstance(recovery_path, str):
            protected_historical_paths.add((args.project_root.resolve() / recovery_path).resolve())
    if (input_paths | protected_historical_paths) & all_output_paths:
        print("Refusing split allocation: an output path collides with an input artifact.", file=sys.stderr)
        return 2
    existing_role_outputs = [
        str(path)
        for path in (*resolved_outputs.values(), source_inventory_output)
        if path.exists()
    ]
    if existing_role_outputs:
        print(
            "Refusing split allocation: role output targets already exist; choose a new run directory to avoid "
            f"overwrites or stale role files: {existing_role_outputs}",
            file=sys.stderr,
        )
        return 2
    if split_output.exists():
        try:
            existing_split = read_json(split_output)
        except (OSError, ValueError):
            existing_split = None
        if not isinstance(existing_split, dict) or existing_split.get("status") != "blocked_not_allocated":
            print(
                "Refusing split allocation: split manifest target already contains a non-placeholder allocation.",
                file=sys.stderr,
            )
            return 2
    role_artifacts: dict[str, dict[str, Any] | None] = {}
    for role in ROLE_ORDER:
        role_records = selected_by_role[role]
        if not role_records:
            role_artifacts[role] = None
            continue
        output_path = output_paths[role]
        write_jsonl(output_path, role_records)
        repository_relative_path = repository_relative_output_locator(output_path, args.project_root)
        role_artifacts[role] = {
            "path": repository_relative_path or f"<machine-local-output>/{output_path.name}",
            "sha256": sha256_file(output_path),
            "record_count": len(role_records),
            "visibility": "evaluation_only" if role == "locked_eval" else "annotation_role_only",
            "tuning_allowed": role != "locked_eval",
        }
    source_inventory_artifact: dict[str, Any] | None = None
    if release_eligible:
        source_inventory = {
            "schema_version": "hybridqa_source_question_ids_v0_1",
            "source_id": source_reference["source_id"],
            "pinned_commit": source_reference["pinned_commit"],
            "artifact_path": source_reference["artifact_path"],
            "artifact_sha256": source_reference["artifact_sha256"],
            "question_id_set_sha256": observed_question_id_set_sha256,
            "question_id_set_hash_algorithm": QUESTION_ID_SET_HASH_ALGORITHM,
            "question_ids": sorted(by_id),
        }
        write_json(source_inventory_output, source_inventory)
        source_inventory_artifact = {
            "path": repository_relative_output_locator(source_inventory_output, args.project_root),
            "sha256": sha256_file(source_inventory_output),
            "record_count": len(by_id),
            "question_id_set_sha256": observed_question_id_set_sha256,
        }
    manifest = {
        "schema_version": "split_manifest_v0_1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "allocation_method": "ascending_sha256(seed + NUL + question_id)",
        "seed": args.seed,
        "source": {
            "path": portable_input_locator(args.questions),
            "location_kind": "repository_relative_or_machine_local_placeholder",
            "sha256": source_sha256,
            "record_count": len(by_id),
            "malformed_record_count": malformed,
            "verified_against_pinned_manifest": source_verified,
            "portable_reference": source_reference,
            "question_id_set_sha256": observed_question_id_set_sha256,
            "question_id_inventory_artifact": source_inventory_artifact,
        },
        "historical_manifest": {
            "path": portable_input_locator(args.historical_manifest),
            "sha256": sha256_file(args.historical_manifest),
            "audit_status": completeness or "unknown",
            "forbidden_id_count": len(forbidden_ids),
            "release_contract_errors": history_errors,
        },
        "roles": roles,
        "role_artifacts": role_artifacts,
        "combined_role_output_written": False,
        "counts": {role: len(roles[role]) for role in ROLE_ORDER},
        "zero_overlap_verified": True,
        "release_eligible": release_eligible,
        "override_used": bool(
            (args.allow_incomplete_history and not history_complete)
            or (args.allow_unverified_source and not source_verified)
        ),
        "warnings": [
            *([] if history_complete else ["Historical exposed-ID inventory is incomplete; this split is diagnostic only."]),
            *([] if source_verified else ["Question source hash was not verified against the pinned official manifest."]),
        ],
    }
    write_json(args.split_manifest, manifest)
    count_summary = Counter({role: len(records) for role, records in selected_by_role.items() if records})
    print(f"wrote {sum(count_summary.values())} records to isolated role files: {dict(count_summary)}")
    print(f"wrote split manifest to {args.split_manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
