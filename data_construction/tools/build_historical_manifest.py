#!/usr/bin/env python3
"""Inventory all question IDs exposed by the historical Week 1–3 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _common import first_string, iter_json_records, read_json, sha256_file, write_json


EXPECTED = (
    ("data_analysis/week1_sample_100.jsonl", "historical_feasibility", "none"),
    ("evaluation/week2_eval_ids.json", "historical_evaluation", "none"),
    ("evaluation/week3_engineering_dev_ids.json", "historical_engineering_dev", "none"),
    ("evaluation/week3_locked_eval_ids.json", "historical_locked_eval", "all"),
    ("evaluation/week3_split_manifest.json", "historical_split_manifest", "named_only"),
)
KNOWN_EXPECTED_UNIQUE_COUNTS = {
    "data_analysis/week1_sample_100.jsonl": 100,
    "evaluation/week2_eval_ids.json": 50,
}
ID_KEYS = ("question_id", "qid", "id")
ROLE_CONTAINER_KEYS = {
    "roles",
    "annotation_schema_pilot",
    "annotation_train",
    "annotation_dev",
    "locked_eval",
    "engineering_dev",
    "historical_feasibility",
    "historical_evaluation",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data_construction/manifests/historical_exposed_ids.json"),
    )
    parser.add_argument(
        "--recovery-provenance",
        type=Path,
        help="Researcher-approved authoritative file hashes/counts required before audit_status=complete",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero if any expected source is absent")
    parser.add_argument("--overwrite", action="store_true", help="Explicitly replace an existing manifest output")
    return parser.parse_args()


def collect_explicit_ids(value: Any, parent_key: str = "") -> set[str]:
    ids: set[str] = set()
    if isinstance(value, list):
        if (
            parent_key.lower().endswith(("ids", "eval", "train", "dev", "test"))
            or parent_key.lower() in ROLE_CONTAINER_KEYS
        ):
            ids.update(str(item) for item in value if isinstance(item, (str, int)))
        for item in value:
            if isinstance(item, dict):
                identifier = first_string(item, ID_KEYS)
                if identifier:
                    ids.add(identifier)
                ids.update(collect_explicit_ids(item, parent_key))
    elif isinstance(value, dict):
        identifier = first_string(value, ID_KEYS)
        if identifier:
            ids.add(identifier)
        for key, child in value.items():
            lowered = key.lower()
            if lowered.endswith("ids") or lowered in {
                "records",
                "questions",
                "pilot",
                "train",
                "dev",
                "locked_eval",
                "test",
                "splits",
            } | ROLE_CONTAINER_KEYS:
                ids.update(collect_explicit_ids(child, key))
    return ids


def ids_from_file(path: Path) -> set[str]:
    if path.suffix.lower() == ".jsonl":
        ids: set[str] = set()
        for record in iter_json_records(path):
            identifier = first_string(record, ID_KEYS)
            if identifier:
                ids.add(identifier)
        return ids
    return collect_explicit_ids(read_json(path), path.stem)


def named_locked_ids(value: Any) -> set[str]:
    """Collect only subtrees explicitly labelled as locked evaluation/test."""

    ids: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in {"locked_eval", "locked_eval_ids", "locked_test", "locked_test_ids"}:
                ids.update(collect_explicit_ids(child, key))
            elif isinstance(child, (dict, list)):
                ids.update(named_locked_ids(child))
    elif isinstance(value, list):
        for child in value:
            ids.update(named_locked_ids(child))
    return ids


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    output = (args.output if args.output.is_absolute() else root / args.output).resolve()
    try:
        output.relative_to(root)
    except ValueError:
        print("refusing historical audit output outside --project-root", file=sys.stderr)
        return 2
    protected_inputs = {(root / relative).resolve() for relative, _, _ in EXPECTED}
    if args.recovery_provenance:
        protected_inputs.add(args.recovery_provenance.resolve())
    if output in protected_inputs:
        print("refusing to overwrite a historical source or recovery-provenance input", file=sys.stderr)
        return 2
    if output.exists():
        if not args.overwrite:
            print("refusing to overwrite an existing historical manifest without --overwrite", file=sys.stderr)
            return 2
        try:
            previous_manifest = read_json(output)
        except (OSError, ValueError) as exc:
            print(
                f"refusing to overwrite an unreadable existing manifest; choose a new versioned path: {exc}",
                file=sys.stderr,
            )
            return 2
        replaceable_incomplete = (
            isinstance(previous_manifest, dict)
            and previous_manifest.get("schema_version") == "historical_exposed_ids_v0_1"
            and previous_manifest.get("is_complete") is False
            and isinstance(previous_manifest.get("audit_status"), str)
            and previous_manifest["audit_status"].startswith("incomplete_")
        )
        if not replaceable_incomplete:
            print(
                "refusing to overwrite a complete, released, unknown, or unversioned historical manifest; "
                "write a new versioned output path",
                file=sys.stderr,
            )
            return 2
    source_files: list[dict[str, Any]] = []
    source_question_ids: dict[str, list[str] | None] = {}
    all_ids: set[str] = set()
    locked_ids: set[str] = set()
    missing: list[str] = []
    empty_or_unreadable_role_files: list[str] = []
    known_count_mismatches: list[dict[str, Any]] = []

    for relative, historical_role, locked_mode in EXPECTED:
        path = root / relative
        if not path.is_file():
            source_files.append(
                {
                    "path": relative,
                    "historical_role": historical_role,
                    "locked_id_extraction": locked_mode,
                    "status": "missing",
                    "question_id_count": None,
                    "sha256": None,
                }
            )
            missing.append(relative)
            source_question_ids[relative] = None
            continue
        identifiers = ids_from_file(path)
        source_question_ids[relative] = sorted(identifiers)
        if not identifiers:
            empty_or_unreadable_role_files.append(relative)
        expected_count = KNOWN_EXPECTED_UNIQUE_COUNTS.get(relative)
        if expected_count is not None and len(identifiers) != expected_count:
            known_count_mismatches.append(
                {"path": relative, "expected_unique_count": expected_count, "observed_unique_count": len(identifiers)}
            )
        all_ids.update(identifiers)
        if locked_mode == "all":
            locked_ids.update(identifiers)
        elif locked_mode == "named_only":
            locked_ids.update(named_locked_ids(read_json(path)))
        source_files.append(
            {
                "path": relative,
                "historical_role": historical_role,
                "locked_id_extraction": locked_mode,
                "status": "present" if identifiers else "present_but_no_question_ids",
                "question_id_count": len(identifiers),
                "sha256": sha256_file(path),
            }
        )

    # A locked role is necessarily historically exposed even if a future
    # split-manifest layout is recognized only by the narrower locked parser.
    all_ids.update(locked_ids)

    provenance_status = "missing"
    provenance_summary: dict[str, Any] | None = None
    provenance_errors: list[str] = []
    if args.recovery_provenance:
        if not args.recovery_provenance.is_file():
            provenance_errors.append("recovery provenance file is missing")
        else:
            provenance = read_json(args.recovery_provenance)
            if provenance.get("schema_version") != "historical_recovery_provenance_v0_1":
                provenance_errors.append("unsupported recovery provenance schema_version")
            if provenance.get("status") != "researcher_approved_authoritative":
                provenance_errors.append("recovery provenance is not researcher-approved authoritative evidence")
            authority_kind = provenance.get("authority_kind")
            authority_identity = provenance.get("authority_identity")
            if authority_kind != "git_commit":
                provenance_errors.append(
                    "v0.1 release verification supports only authority_kind=git_commit; "
                    "verified backups/artifact stores must first be preserved in an approved canonical commit"
                )
            if not isinstance(authority_identity, str) or not authority_identity.strip():
                provenance_errors.append("authority_identity is missing")
            elif authority_identity.startswith(("/", "~")) or (
                len(authority_identity) >= 2 and authority_identity[1] == ":"
            ):
                provenance_errors.append("authority_identity must be portable, not a machine-local absolute path")
            elif authority_kind == "git_commit" and not re.fullmatch(r"[0-9a-f]{40}", authority_identity):
                provenance_errors.append("git authority_identity must be a full lowercase 40-hex commit OID")
            raw_files = provenance.get("files", [])
            entries = {
                entry.get("path"): entry
                for entry in raw_files
                if isinstance(entry, dict) and isinstance(entry.get("path"), str)
            } if isinstance(raw_files, list) else {}
            observed_by_path = {entry["path"]: entry for entry in source_files if entry.get("status") != "missing"}
            for relative, _, _ in EXPECTED:
                expected_entry = entries.get(relative)
                observed_entry = observed_by_path.get(relative)
                if not expected_entry:
                    provenance_errors.append(f"provenance lacks {relative}")
                    continue
                if not observed_entry:
                    continue
                if expected_entry.get("sha256") != observed_entry.get("sha256"):
                    provenance_errors.append(f"provenance SHA-256 mismatch for {relative}")
                if expected_entry.get("question_id_count") != observed_entry.get("question_id_count"):
                    provenance_errors.append(f"provenance ID-count mismatch for {relative}")
            if authority_kind == "git_commit" and isinstance(authority_identity, str):
                git_probe = subprocess.run(
                    ["git", "-C", str(root), "cat-file", "-e", f"{authority_identity}^{{commit}}"],
                    capture_output=True,
                    check=False,
                )
                if git_probe.returncode != 0:
                    provenance_errors.append("recovery authority commit is unavailable in the project repository")
                else:
                    for relative, _, _ in EXPECTED:
                        committed = subprocess.run(
                            ["git", "-C", str(root), "show", f"{authority_identity}:{relative}"],
                            capture_output=True,
                            check=False,
                        )
                        observed_entry = observed_by_path.get(relative)
                        if committed.returncode != 0:
                            provenance_errors.append(f"recovery authority commit lacks {relative}")
                        elif (
                            isinstance(observed_entry, dict)
                            and hashlib.sha256(committed.stdout).hexdigest() != observed_entry.get("sha256")
                        ):
                            provenance_errors.append(f"historical source differs from git authority: {relative}")
            provenance_status = "verified" if not provenance_errors else "invalid"
            try:
                provenance_relative_path = args.recovery_provenance.resolve().relative_to(root).as_posix()
            except ValueError:
                provenance_relative_path = None
                provenance_errors.append("recovery provenance must be stored under the project root")
                provenance_status = "invalid"
            provenance_summary = {
                "schema_version": provenance.get("schema_version"),
                "status": provenance.get("status"),
                "authority_kind": authority_kind,
                "authority_identity": authority_identity,
                "verification": provenance_status,
                "artifact": (
                    {
                        "repository_relative_path": provenance_relative_path,
                        "sha256": sha256_file(args.recovery_provenance),
                    }
                    if provenance_relative_path is not None
                    else None
                ),
            }

    complete = (
        not missing
        and not empty_or_unreadable_role_files
        and not known_count_mismatches
        and provenance_status == "verified"
    )
    manifest = {
        "schema_version": "historical_exposed_ids_v0_1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_status": (
            "complete"
            if complete
            else (
                "incomplete_missing_historical_artifacts"
                if missing
                else (
                    "incomplete_historical_artifacts_contain_no_question_ids"
                    if empty_or_unreadable_role_files
                    else "incomplete_unverified_historical_provenance_or_counts"
                )
            )
        ),
        "is_complete": complete,
        "source_files": source_files,
        "source_question_ids": source_question_ids,
        "missing_required_files": missing,
        "required_files_with_no_question_ids": empty_or_unreadable_role_files,
        "known_expected_count_mismatches": known_count_mismatches,
        "recovery_provenance": provenance_summary,
        "recovery_provenance_status": provenance_status,
        "recovery_provenance_errors": provenance_errors,
        "exposed_question_ids": sorted(all_ids),
        "week1_sample_question_ids": source_question_ids.get("data_analysis/week1_sample_100.jsonl"),
        "week2_eval_question_ids": source_question_ids.get("evaluation/week2_eval_ids.json"),
        "engineering_dev_question_ids": source_question_ids.get("evaluation/week3_engineering_dev_ids.json"),
        "locked_eval_question_ids": sorted(locked_ids),
        "forbidden_future_training_ids": sorted(all_ids),
        "counts": {
            "exposed_unique": len(all_ids),
            "locked_eval_unique": len(locked_ids),
            "missing_required_files": len(missing),
            "required_files_with_no_question_ids": len(empty_or_unreadable_role_files),
            "known_expected_count_mismatches": len(known_count_mismatches),
        },
        "interpretation": (
            "Complete inventory of the five required historical artifacts."
            if complete
            else (
                "BLOCKED: missing/empty artifacts, unexpected known counts, or absent researcher-approved provenance "
                "do not prove a complete historical inventory."
            )
        ),
    }
    write_json(output, manifest)
    print(f"wrote {output} (status={manifest['audit_status']}, ids={len(all_ids)})")
    return 2 if args.strict and not complete else 0


if __name__ == "__main__":
    raise SystemExit(main())
