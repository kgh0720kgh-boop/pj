#!/usr/bin/env python3
"""Build the cumulative N=100 question-only AI exploration pool.

This builder is intentionally separate from the released v0.1 annotation-role
sampler.  It assigns no train/dev/locked-eval role, preserves the existing
30-question pilot as an exact prefix, and emits no answer, table, trace, or
environment field.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from _common import (
    canonical_json_sha256,
    canonical_string_set_sha256,
    git_commit_identity,
    iter_json_records,
    json_file_bytes,
    jsonl_file_bytes,
    read_json,
    sha256_bytes,
    sha256_file,
    stable_rank,
    write_output_batch,
)
from build_sample import (
    ID_KEYS,
    QUESTION_ID_SET_HASH_ALGORITHM,
    collect_ids,
    historical_release_errors,
    verify_source_manifest,
)


TOOL_VERSION = "ai_question_structure_exploration_pool_builder_v0_1"
POOL_SCHEMA_VERSION = "ai_question_structure_exploration_pool_manifest_v0_1"
VIEW_SCHEMA_VERSION = "question_only_semantic_view_v0_1"
VIEW_VISIBILITY = "question_only_no_environment_answer_or_proposals"
SEED = "hybridqa-semantic-topology-v0.1"
POOL_SIZE = 100
PREFIX_SIZE = 30
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HISTORICAL = ROOT / "data_construction/manifests/historical_exposed_ids.json"
DEFAULT_SOURCE_MANIFEST = ROOT / "data_construction/manifests/source_manifest_v0_1.json"
DEFAULT_SOURCE_IDS = ROOT / "data_construction/manifests/source_question_ids.json"
DEFAULT_SPLIT = ROOT / "data_construction/manifests/split_manifest_v0_1.json"
DEFAULT_PREFIX_VIEWS = ROOT / "data_construction/pilot/question_only_semantic_views_v0_1.jsonl"
DEFAULT_VIEWS = (
    ROOT
    / "data_construction/exploration/ai_question_structure_scale_v0_1/pool/question_only_views_n100.jsonl"
)
DEFAULT_MANIFEST = (
    ROOT / "data_construction/manifests/ai_question_structure_exploratory_pool_v0_1.json"
)


class PoolContractError(ValueError):
    """Raised when a source or prefix contract is not exactly reproducible."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--historical-manifest", type=Path, default=DEFAULT_HISTORICAL)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--source-question-ids", type=Path, default=DEFAULT_SOURCE_IDS)
    parser.add_argument("--split-manifest", type=Path, default=DEFAULT_SPLIT)
    parser.add_argument("--prefix-views", type=Path, default=DEFAULT_PREFIX_VIEWS)
    parser.add_argument("--output-views", type=Path, default=DEFAULT_VIEWS)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def _require_regular(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise PoolContractError(f"{label} must be an existing regular non-symlink file: {path}")


def _identifier(record: dict[str, Any]) -> str | None:
    for key in ID_KEYS:
        value = record.get(key)
        if isinstance(value, (str, int)) and str(value).strip():
            return str(value).strip()
    return None


def _question(record: dict[str, Any]) -> str | None:
    for key in ("question", "query", "text"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def ordered_ids_sha256(values: list[str]) -> str:
    """Hash an ordered ID list without confusing it with a set hash."""

    return canonical_json_sha256(values)


def build_pool(
    *,
    questions_path: Path,
    project_root: Path,
    historical_path: Path,
    source_manifest_path: Path,
    source_ids_path: Path,
    split_path: Path,
    prefix_views_path: Path,
    output_views_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    for label, path in {
        "questions": questions_path,
        "historical manifest": historical_path,
        "source manifest": source_manifest_path,
        "source question-ID inventory": source_ids_path,
        "split manifest": split_path,
        "prefix views": prefix_views_path,
    }.items():
        _require_regular(path, label)

    source_sha256 = sha256_file(questions_path)
    source_reference = verify_source_manifest(read_json(source_manifest_path), source_sha256)
    if source_reference is None or source_reference.get("artifact_path") != "released_data/dev.json":
        raise PoolContractError("questions are not the exact pinned official HybridQA dev artifact")

    historical = read_json(historical_path)
    if not isinstance(historical, dict):
        raise PoolContractError("historical manifest must be an object")
    history_errors = historical_release_errors(historical, project_root)
    if history_errors:
        raise PoolContractError(
            "historical manifest is not release-valid: " + "; ".join(history_errors)
        )
    historical_ids = collect_ids(historical)
    explicit_historical = historical.get("exposed_question_ids")
    if (
        not isinstance(explicit_historical, list)
        or any(not isinstance(value, str) for value in explicit_historical)
        or set(explicit_historical) != historical_ids
        or len(historical_ids) != 100
    ):
        raise PoolContractError("historical exposed-ID inventory is not the exact 100-ID union")

    source_inventory = read_json(source_ids_path)
    if not isinstance(source_inventory, dict):
        raise PoolContractError("source question-ID inventory must be an object")
    inventory_ids = source_inventory.get("question_ids")
    if (
        source_inventory.get("schema_version") != "hybridqa_source_question_ids_v0_1"
        or source_inventory.get("artifact_sha256") != source_sha256
        or source_inventory.get("question_id_set_hash_algorithm")
        != QUESTION_ID_SET_HASH_ALGORITHM
        or not isinstance(inventory_ids, list)
        or any(not isinstance(value, str) for value in inventory_ids)
        or len(inventory_ids) != source_reference.get("record_count")
        or len(set(inventory_ids)) != len(inventory_ids)
        or canonical_string_set_sha256(inventory_ids)
        != source_reference.get("question_id_set_sha256")
    ):
        raise PoolContractError("tracked source question-ID inventory is invalid")

    by_id: dict[str, dict[str, Any]] = {}
    for record in iter_json_records(questions_path):
        question_id = _identifier(record)
        question = _question(record)
        if not question_id or not question:
            raise PoolContractError("official dev contains a record without question ID/text")
        if question_id in by_id:
            raise PoolContractError(f"duplicate source question ID: {question_id}")
        by_id[question_id] = record
    if set(by_id) != set(inventory_ids):
        raise PoolContractError("official dev IDs differ from the tracked source inventory")

    eligible_ids = [question_id for question_id in by_id if question_id not in historical_ids]
    eligible_ids.sort(key=lambda question_id: stable_rank(SEED, question_id))
    if len(eligible_ids) != 3366:
        raise PoolContractError(f"expected 3366 eligible dev questions, observed {len(eligible_ids)}")
    selected_ids = eligible_ids[:POOL_SIZE]
    reserve_ids = eligible_ids[POOL_SIZE:]

    split = read_json(split_path)
    if not isinstance(split, dict):
        raise PoolContractError("split manifest must be an object")
    prefix_ids = split.get("roles", {}).get("annotation_schema_pilot")
    if (
        split.get("schema_version") != "split_manifest_v0_1"
        or split.get("release_eligible") is not True
        or split.get("override_used") is not False
        or split.get("counts")
        != {
            "annotation_dev": 0,
            "annotation_schema_pilot": 30,
            "annotation_train": 0,
            "locked_eval": 0,
        }
        or not isinstance(prefix_ids, list)
        or selected_ids[:PREFIX_SIZE] != prefix_ids
    ):
        raise PoolContractError("the immutable v0.1 30-question split is not the exact ranked prefix")

    prefix_views = list(iter_json_records(prefix_views_path))
    if len(prefix_views) != PREFIX_SIZE:
        raise PoolContractError("prefix view artifact must contain exactly 30 records")
    views: list[dict[str, Any]] = []
    for question_id in selected_ids:
        question = _question(by_id[question_id])
        if question is None:
            raise PoolContractError(f"source question text disappeared: {question_id}")
        views.append(
            {
                "schema_version": VIEW_SCHEMA_VERSION,
                "visibility": VIEW_VISIBILITY,
                "question_id": question_id,
                "question": question,
            }
        )
    if views[:PREFIX_SIZE] != prefix_views:
        raise PoolContractError("current 30 views are not the exact record prefix of N=100")
    view_bytes = jsonl_file_bytes(views)
    prefix_bytes = prefix_views_path.read_bytes()
    if not view_bytes.startswith(prefix_bytes):
        raise PoolContractError("current 30-view bytes are not an exact byte prefix of N=100")

    source_ids = set(by_id)
    if (
        set(selected_ids) & historical_ids
        or set(reserve_ids) & historical_ids
        or set(selected_ids) & set(reserve_ids)
        or historical_ids | set(selected_ids) | set(reserve_ids) != source_ids
        or len(reserve_ids) != 3266
    ):
        raise PoolContractError("historical/selected/reserve partition is not exact and disjoint")

    manifest = {
        "schema_version": POOL_SCHEMA_VERSION,
        "builder_version": TOOL_VERSION,
        "purpose": "ai_scale_first_question_structure_exploration_no_corpus_role_allocation",
        "status": "selected_n100_question_only_pool_materialized_model_processing_pending_for_new_70",
        "selection": {
            "dataset": "HybridQA",
            "source_split": "dev",
            "seed": SEED,
            "method": "ascending_sha256(seed + NUL + question_id)",
            "cumulative_targets": [30, 100, 300, 1000],
            "current_target": POOL_SIZE,
            "eligible_count": len(eligible_ids),
            "selected_count": len(selected_ids),
            "preserved_prefix_count": PREFIX_SIZE,
            "added_count": POOL_SIZE - PREFIX_SIZE,
            "unexposed_unallocated_reserve_count": len(reserve_ids),
            "selected_question_ids": selected_ids,
            "selected_question_ids_ordered_sha256": ordered_ids_sha256(selected_ids),
            "added_question_ids": selected_ids[PREFIX_SIZE:],
            "added_question_ids_ordered_sha256": ordered_ids_sha256(selected_ids[PREFIX_SIZE:]),
            "eligible_question_ids_set_sha256": canonical_string_set_sha256(eligible_ids),
            "reserve_question_ids_set_sha256": canonical_string_set_sha256(reserve_ids),
            "reserve_question_text_materialized": False,
        },
        "exposure_accounting_at_materialization": {
            "historical_exposed_count": len(historical_ids),
            "prior_ai_processed_prefix_count": PREFIX_SIZE,
            "newly_selected_pending_processing_count": POOL_SIZE - PREFIX_SIZE,
            "future_unseen_evaluation_eligible_for_selected_ids": False,
            "human_evidence_count": 0,
            "gold_claimed": False,
            "corpus_role_allocated": False,
        },
        "partition_check": {
            "official_dev_count": len(source_ids),
            "historical_count": len(historical_ids),
            "selected_ai_exploration_count": len(selected_ids),
            "unexposed_unallocated_reserve_count": len(reserve_ids),
            "pairwise_disjoint": True,
            "union_equals_official_dev": True,
        },
        "artifacts": {
            "views": {
                "repository_relative_path": output_views_path.resolve()
                .relative_to(project_root.resolve())
                .as_posix(),
                "record_count": len(views),
                "bytes": len(view_bytes),
                "sha256": sha256_bytes(view_bytes),
            },
            "prefix_views": {
                "repository_relative_path": prefix_views_path.resolve()
                .relative_to(project_root.resolve())
                .as_posix(),
                "record_count": len(prefix_views),
                "sha256": sha256_file(prefix_views_path),
                "exact_byte_prefix": True,
            },
            "split_manifest_v0_1": {
                "repository_relative_path": split_path.resolve()
                .relative_to(project_root.resolve())
                .as_posix(),
                "sha256": sha256_file(split_path),
                "modified": False,
            },
            "historical_manifest": {
                "repository_relative_path": historical_path.resolve()
                .relative_to(project_root.resolve())
                .as_posix(),
                "sha256": sha256_file(historical_path),
            },
            "source_manifest": {
                "repository_relative_path": source_manifest_path.resolve()
                .relative_to(project_root.resolve())
                .as_posix(),
                "sha256": sha256_file(source_manifest_path),
            },
            "source_question_ids": {
                "repository_relative_path": source_ids_path.resolve()
                .relative_to(project_root.resolve())
                .as_posix(),
                "sha256": sha256_file(source_ids_path),
            },
        },
        "source": {
            "source_id": source_reference["source_id"],
            "pinned_commit": source_reference["pinned_commit"],
            "artifact_path": source_reference["artifact_path"],
            "artifact_sha256": source_reference["artifact_sha256"],
            "record_count": source_reference["record_count"],
            "question_id_set_sha256": source_reference["question_id_set_sha256"],
            "machine_local_path_recorded": False,
        },
        "provenance": {
            "builder_code_commit": git_commit_identity(project_root),
            "builder_artifact": "data_construction/tools/build_ai_question_structure_exploration_pool.py",
            "builder_sha256": sha256_file(Path(__file__)),
        },
        "truthfulness_contract": {
            "selected_questions_are_gold": False,
            "selection_is_semantic_evidence": False,
            "selection_is_model_processing": False,
            "human_validation_required_as_current_gate": False,
            "supported_claim": "deterministic_leakage_reduced_question_only_pool_materialization",
        },
    }
    return views, manifest


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    for output in (args.output_views, args.output_manifest):
        try:
            output.resolve().relative_to(project_root)
        except ValueError as exc:
            raise PoolContractError("release outputs must remain inside the repository") from exc
    if args.output_views.resolve() == args.output_manifest.resolve():
        raise PoolContractError("views and manifest outputs must be distinct")
    views, manifest = build_pool(
        questions_path=args.questions,
        project_root=project_root,
        historical_path=args.historical_manifest,
        source_manifest_path=args.source_manifest,
        source_ids_path=args.source_question_ids,
        split_path=args.split_manifest,
        prefix_views_path=args.prefix_views,
        output_views_path=args.output_views,
    )
    statuses = write_output_batch(
        {
            "views": (args.output_views, jsonl_file_bytes(views)),
            "manifest": (args.output_manifest, json_file_bytes(manifest)),
        },
        overwrite=args.overwrite,
    )
    print(
        f"pool=100 prefix=30 added=70 reserve=3266 views={statuses['views']} "
        f"manifest={statuses['manifest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
