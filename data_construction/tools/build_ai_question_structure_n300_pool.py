#!/usr/bin/env python3
"""Build the frozen cumulative N=300 selection-stage artifact batch.

The builder extends, but never rewrites, the frozen N=100 question-only pool.
It emits a cumulative four-field view, a v0.2 pool manifest, a truthful
selection-stage exposure ledger, a coordinator-only interleaved routing
manifest, five four-field producer inputs, and the combined generation/analysis
plan.  New model outputs are deliberately outside this builder's write set.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _common import (
    canonical_json_sha256,
    canonical_string_set_sha256,
    git_commit_identity,
    iter_json_records,
    json_file_bytes,
    jsonl_file_bytes,
    output_path_collision_errors,
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


TOOL_VERSION = "ai_question_structure_n300_pool_builder_v0_1"
POOL_SCHEMA_VERSION = "ai_question_structure_exploration_pool_manifest_v0_2"
EXPOSURE_SCHEMA_VERSION = "question_exposure_ledger_v0_2"
ROUTING_SCHEMA_VERSION = "ai_question_structure_n300_producer_routing_manifest_v0_1"
PLAN_SCHEMA_VERSION = "ai_question_structure_cumulative_n300_analysis_plan_v0_1"
VIEW_SCHEMA_VERSION = "question_only_semantic_view_v0_1"
VIEW_VISIBILITY = "question_only_no_environment_answer_or_proposals"
ANALYSIS_ID = "ai_question_structure_scale_v0_1_cumulative_n300_analysis_v0_1"
ROUTING_ID = "ai_question_structure_scale_v0_1_n300_routing_v0_1"
FROZEN_RECORD_RUN_ID = "ai_question_structure_scale_v0_1_run_001"
SEED = "hybridqa-semantic-topology-v0.1"
CUMULATIVE_TARGET = 300
PREFIX_RECORD_COUNT = 100
CONTRACT_DEVELOPMENT_PREFIX_COUNT = 30
EXPANSION_RECORD_COUNT = 200
EXPECTED_SOURCE_COUNT = 3466
EXPECTED_HISTORICAL_COUNT = 100
EXPECTED_LOCKED_COUNT = 15
EXPECTED_ELIGIBLE_COUNT = 3366
EXPECTED_RESERVE_COUNT = 3066
PRODUCER_PARTITIONS = tuple(f"partition_{index:02d}" for index in range(4, 9))

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data_construction/exploration/ai_question_structure_scale_v0_1"
DEFAULT_HISTORICAL = ROOT / "data_construction/manifests/historical_exposed_ids.json"
DEFAULT_LOCKED = ROOT / "evaluation/week3_locked_eval_ids.json"
DEFAULT_SOURCE_MANIFEST = ROOT / "data_construction/manifests/source_manifest_v0_1.json"
DEFAULT_SOURCE_IDS = ROOT / "data_construction/manifests/source_question_ids.json"
DEFAULT_SPLIT = ROOT / "data_construction/manifests/split_manifest_v0_1.json"
DEFAULT_STUDY_PLAN = ROOT / "data_construction/pilot/question_structure_study_plan_v0_2.json"
DEFAULT_N100_VIEWS = BASE / "pool/question_only_views_n100.jsonl"
DEFAULT_N100_POOL = ROOT / "data_construction/manifests/ai_question_structure_exploratory_pool_v0_1.json"
DEFAULT_N100_EXPOSURE = ROOT / "data_construction/manifests/question_exposure_ledger_v0_1.json"
DEFAULT_N100_RECORDS = BASE / "run_001/records.jsonl"
DEFAULT_N100_EXPLORATION_PLAN = BASE / "contracts/exploration_plan_v0_1.json"
DEFAULT_N100_RUN_MANIFEST = BASE / "run_001/run_manifest.json"
DEFAULT_PROMPT = BASE / "prompts/primary_extraction_v0_1.md"
DEFAULT_RECORD_SCHEMA = BASE / "contracts/semantic_backbone_record_schema_v0_1.json"
DEFAULT_FROZEN_ANALYZER = ROOT / "data_construction/tools/run_ai_question_structure_scale_exploration.py"
DEFAULT_BUILDER_TEST = ROOT / "tests/test_question_structure_n300_pool.py"
DEFAULT_CUMULATIVE_ANALYZER = ROOT / "data_construction/tools/analyze_ai_question_structure_cumulative_n300.py"
DEFAULT_CUMULATIVE_ANALYZER_TEST = ROOT / "tests/test_question_structure_cumulative_n300.py"

DEFAULT_VIEWS = BASE / "pool/question_only_views_n300.jsonl"
DEFAULT_POOL_MANIFEST = ROOT / "data_construction/manifests/ai_question_structure_exploratory_pool_v0_2.json"
DEFAULT_EXPOSURE = ROOT / "data_construction/manifests/question_exposure_ledger_v0_2.json"
DEFAULT_ROUTING = BASE / "n300_extension_v0_1/producer_routing_manifest_v0_1.json"
DEFAULT_PLAN = BASE / "contracts/cumulative_n300_analysis_plan_v0_1.json"
DEFAULT_INPUT_DIR = BASE / "n300_extension_v0_1/inputs"
DEFAULT_MODEL_PARTS_DIR = BASE / "n300_extension_v0_1/parts"
DEFAULT_CUMULATIVE_OUTPUT_DIR = BASE / "cumulative_n300_v0_1"
DEFAULT_COMPLETION_EXPOSURE = ROOT / "data_construction/manifests/question_exposure_ledger_v0_3.json"


class N300PoolContractError(ValueError):
    """Raised when a cumulative selection-stage contract is not reproducible."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--historical-manifest", type=Path, default=DEFAULT_HISTORICAL)
    parser.add_argument("--locked-eval-ids", type=Path, default=DEFAULT_LOCKED)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--source-question-ids", type=Path, default=DEFAULT_SOURCE_IDS)
    parser.add_argument("--split-manifest", type=Path, default=DEFAULT_SPLIT)
    parser.add_argument("--study-plan", type=Path, default=DEFAULT_STUDY_PLAN)
    parser.add_argument("--n100-views", type=Path, default=DEFAULT_N100_VIEWS)
    parser.add_argument("--n100-pool-manifest", type=Path, default=DEFAULT_N100_POOL)
    parser.add_argument("--n100-exposure-ledger", type=Path, default=DEFAULT_N100_EXPOSURE)
    parser.add_argument("--n100-records", type=Path, default=DEFAULT_N100_RECORDS)
    parser.add_argument(
        "--n100-exploration-plan", type=Path, default=DEFAULT_N100_EXPLORATION_PLAN
    )
    parser.add_argument("--n100-run-manifest", type=Path, default=DEFAULT_N100_RUN_MANIFEST)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--record-schema", type=Path, default=DEFAULT_RECORD_SCHEMA)
    parser.add_argument("--frozen-analyzer", type=Path, default=DEFAULT_FROZEN_ANALYZER)
    parser.add_argument("--builder-artifact", type=Path, default=Path(__file__))
    parser.add_argument("--builder-test", type=Path, default=DEFAULT_BUILDER_TEST)
    parser.add_argument("--cumulative-analyzer", type=Path, default=DEFAULT_CUMULATIVE_ANALYZER)
    parser.add_argument(
        "--cumulative-analyzer-test", type=Path, default=DEFAULT_CUMULATIVE_ANALYZER_TEST
    )
    parser.add_argument("--output-views", type=Path, default=DEFAULT_VIEWS)
    parser.add_argument("--output-pool-manifest", type=Path, default=DEFAULT_POOL_MANIFEST)
    parser.add_argument("--output-exposure-ledger", type=Path, default=DEFAULT_EXPOSURE)
    parser.add_argument("--output-routing-manifest", type=Path, default=DEFAULT_ROUTING)
    parser.add_argument("--output-plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--partition-input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--model-parts-dir", type=Path, default=DEFAULT_MODEL_PARTS_DIR)
    parser.add_argument(
        "--cumulative-output-dir", type=Path, default=DEFAULT_CUMULATIVE_OUTPUT_DIR
    )
    parser.add_argument(
        "--completion-exposure-ledger", type=Path, default=DEFAULT_COMPLETION_EXPOSURE
    )
    return parser.parse_args(argv)


def _require_regular(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise N300PoolContractError(
            f"{label} must be an existing regular non-symlink file: {path}"
        )


def _relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise N300PoolContractError(f"path is outside project root: {path}") from exc


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


def _view(question_id: str, question: str) -> dict[str, Any]:
    return {
        "schema_version": VIEW_SCHEMA_VERSION,
        "visibility": VIEW_VISIBILITY,
        "question_id": question_id,
        "question": question,
    }


def _file_binding(
    path: Path,
    project_root: Path,
    *,
    record_count: int | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "repository_relative_path": _relative(path, project_root),
        "sha256": sha256_file(path),
    }
    if record_count is not None:
        value["record_count"] = record_count
    return value


def _payload_binding(
    path: Path,
    payload: bytes,
    project_root: Path,
    *,
    record_count: int | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "repository_relative_path": _relative(path, project_root),
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }
    if record_count is not None:
        value["record_count"] = record_count
    return value


def _locked_ids(value: Any) -> set[str]:
    if not isinstance(value, dict):
        raise N300PoolContractError("locked-evaluation artifact must be an object")
    identifiers = value.get("ids")
    if (
        value.get("role") != "locked_eval"
        or value.get("size") != EXPECTED_LOCKED_COUNT
        or not isinstance(identifiers, list)
        or len(identifiers) != EXPECTED_LOCKED_COUNT
        or len(set(identifiers)) != EXPECTED_LOCKED_COUNT
        or any(not isinstance(item, str) for item in identifiers)
    ):
        raise N300PoolContractError("locked-evaluation artifact is not the exact 15-ID set")
    return set(identifiers)


def _partition_input_paths(directory: Path) -> dict[str, Path]:
    return {partition: directory / f"{partition}.jsonl" for partition in PRODUCER_PARTITIONS}


def _planned_model_output_paths(directory: Path) -> dict[str, Path]:
    return {partition: directory / f"{partition}.jsonl" for partition in PRODUCER_PARTITIONS}


def _cumulative_output_paths(
    directory: Path, completion_exposure_path: Path
) -> dict[str, Path]:
    return {
        "records": directory / "records.jsonl",
        "checks": directory / "checks.jsonl",
        "derived_signatures": directory / "analysis/derived_signatures_v0_1.jsonl",
        "metrics": directory
        / "analysis/cumulative_n300_structural_saturation_metrics_v0_1.json",
        "report": directory
        / "analysis/cumulative_n300_structural_saturation_report_v0_1.md",
        "run_manifest": directory / "run_manifest.json",
        "completion_exposure_ledger": completion_exposure_path,
    }


def build_n300_bundle(
    *,
    questions_path: Path,
    project_root: Path,
    historical_path: Path,
    locked_path: Path,
    source_manifest_path: Path,
    source_ids_path: Path,
    split_path: Path,
    study_plan_path: Path,
    n100_views_path: Path,
    n100_pool_path: Path,
    n100_exposure_path: Path,
    n100_records_path: Path,
    n100_exploration_plan_path: Path,
    n100_run_manifest_path: Path,
    prompt_path: Path,
    record_schema_path: Path,
    frozen_analyzer_path: Path,
    builder_path: Path,
    builder_test_path: Path,
    cumulative_analyzer_path: Path,
    cumulative_analyzer_test_path: Path,
    output_views_path: Path,
    output_pool_path: Path,
    output_exposure_path: Path,
    output_routing_path: Path,
    output_plan_path: Path,
    partition_input_paths: dict[str, Path],
    planned_model_output_paths: dict[str, Path],
    cumulative_output_paths: dict[str, Path],
) -> dict[str, tuple[Path, bytes]]:
    project_root = project_root.resolve()
    inputs = {
        "questions": questions_path,
        "historical manifest": historical_path,
        "locked-evaluation IDs": locked_path,
        "source manifest": source_manifest_path,
        "source question-ID inventory": source_ids_path,
        "split manifest": split_path,
        "study plan": study_plan_path,
        "N=100 views": n100_views_path,
        "N=100 pool manifest": n100_pool_path,
        "N=100 exposure ledger": n100_exposure_path,
        "N=100 records": n100_records_path,
        "N=100 exploration plan": n100_exploration_plan_path,
        "N=100 run manifest": n100_run_manifest_path,
        "frozen prompt": prompt_path,
        "frozen record schema": record_schema_path,
        "frozen N=100 analyzer": frozen_analyzer_path,
        "N=300 builder test": builder_test_path,
        "cumulative N=300 analyzer": cumulative_analyzer_path,
        "cumulative N=300 analyzer test": cumulative_analyzer_test_path,
        "N=300 builder": builder_path,
    }
    for label, path in inputs.items():
        _require_regular(path, label)

    if set(partition_input_paths) != set(PRODUCER_PARTITIONS):
        raise N300PoolContractError("partition input paths must cover partition_04 through partition_08")
    if set(planned_model_output_paths) != set(PRODUCER_PARTITIONS):
        raise N300PoolContractError("planned model outputs must cover partition_04 through partition_08")
    expected_cumulative_outputs = {
        "records",
        "checks",
        "derived_signatures",
        "metrics",
        "report",
        "run_manifest",
        "completion_exposure_ledger",
    }
    if set(cumulative_output_paths) != expected_cumulative_outputs:
        raise N300PoolContractError("cumulative output inventory is incomplete")

    outputs = {
        "views": output_views_path,
        "pool_manifest": output_pool_path,
        "exposure_ledger": output_exposure_path,
        "routing_manifest": output_routing_path,
        "combined_plan": output_plan_path,
        **{f"input_{key}": value for key, value in partition_input_paths.items()},
    }
    collisions = output_path_collision_errors(inputs, outputs)
    if collisions:
        raise N300PoolContractError(" | ".join(collisions))
    for label, path in {**outputs, **planned_model_output_paths, **cumulative_output_paths}.items():
        try:
            path.resolve().relative_to(project_root)
        except ValueError as exc:
            raise N300PoolContractError(
                f"release or planned output {label!r} is outside project root: {path}"
            ) from exc
    planned_paths = list(planned_model_output_paths.values()) + list(
        cumulative_output_paths.values()
    )
    if len({path.resolve() for path in planned_paths}) != len(planned_paths):
        raise N300PoolContractError("planned model/analysis outputs collide")
    if {path.resolve() for path in planned_paths} & {
        path.resolve() for path in inputs.values()
    }:
        raise N300PoolContractError("a planned model/analysis output collides with an input")
    if {path.resolve() for path in planned_paths} & {
        path.resolve() for path in outputs.values()
    }:
        raise N300PoolContractError("a planned model/analysis output collides with a builder output")
    for label, path in {
        **{f"model part {key}": value for key, value in planned_model_output_paths.items()},
        **{f"cumulative output {key}": value for key, value in cumulative_output_paths.items()},
    }.items():
        if path.is_symlink() or path.exists():
            raise N300PoolContractError(
                f"planned output must not exist at selection-contract freeze ({label}): {path}"
            )

    source_sha256 = sha256_file(questions_path)
    source_reference = verify_source_manifest(read_json(source_manifest_path), source_sha256)
    if source_reference is None or source_reference.get("artifact_path") != "released_data/dev.json":
        raise N300PoolContractError(
            "questions are not the exact pinned official HybridQA dev artifact"
        )

    historical = read_json(historical_path)
    if not isinstance(historical, dict):
        raise N300PoolContractError("historical manifest must be an object")
    history_errors = historical_release_errors(historical, project_root)
    if history_errors:
        raise N300PoolContractError(
            "historical manifest is not release-valid: " + "; ".join(history_errors)
        )
    historical_ids = collect_ids(historical)
    if (
        historical.get("is_complete") is not True
        or historical.get("audit_status") != "complete"
        or historical.get("counts", {}).get("exposed_unique") != EXPECTED_HISTORICAL_COUNT
        or len(historical_ids) != EXPECTED_HISTORICAL_COUNT
        or set(historical.get("exposed_question_ids", [])) != historical_ids
    ):
        raise N300PoolContractError("historical manifest is not the exact complete 100-ID union")
    locked_ids = _locked_ids(read_json(locked_path))
    if locked_ids != set(historical.get("locked_eval_question_ids", [])):
        raise N300PoolContractError("locked-evaluation IDs disagree with the historical manifest")

    source_inventory = read_json(source_ids_path)
    inventory_ids = source_inventory.get("question_ids") if isinstance(source_inventory, dict) else None
    if (
        not isinstance(source_inventory, dict)
        or source_inventory.get("schema_version") != "hybridqa_source_question_ids_v0_1"
        or source_inventory.get("artifact_sha256") != source_sha256
        or source_inventory.get("question_id_set_hash_algorithm")
        != QUESTION_ID_SET_HASH_ALGORITHM
        or not isinstance(inventory_ids, list)
        or len(inventory_ids) != EXPECTED_SOURCE_COUNT
        or len(set(inventory_ids)) != EXPECTED_SOURCE_COUNT
        or any(not isinstance(value, str) for value in inventory_ids)
        or canonical_string_set_sha256(inventory_ids)
        != source_reference.get("question_id_set_sha256")
    ):
        raise N300PoolContractError("tracked source question-ID inventory is invalid")

    by_id: dict[str, dict[str, Any]] = {}
    for record in iter_json_records(questions_path):
        question_id = _identifier(record)
        question = _question(record)
        if not question_id or not question:
            raise N300PoolContractError("official dev contains a record without question ID/text")
        if question_id in by_id:
            raise N300PoolContractError(f"duplicate source question ID: {question_id}")
        by_id[question_id] = record
    if len(by_id) != EXPECTED_SOURCE_COUNT or set(by_id) != set(inventory_ids):
        raise N300PoolContractError("official dev IDs differ from the tracked source inventory")

    eligible_ids = [question_id for question_id in by_id if question_id not in historical_ids]
    eligible_ids.sort(key=lambda question_id: stable_rank(SEED, question_id))
    if len(eligible_ids) != EXPECTED_ELIGIBLE_COUNT:
        raise N300PoolContractError(
            f"expected {EXPECTED_ELIGIBLE_COUNT} eligible questions, observed {len(eligible_ids)}"
        )
    selected_ids = eligible_ids[:CUMULATIVE_TARGET]
    added_ids = selected_ids[PREFIX_RECORD_COUNT:]
    reserve_ids = eligible_ids[CUMULATIVE_TARGET:]

    split = read_json(split_path)
    prefix30 = split.get("roles", {}).get("annotation_schema_pilot") if isinstance(split, dict) else None
    if (
        not isinstance(split, dict)
        or split.get("schema_version") != "split_manifest_v0_1"
        or split.get("release_eligible") is not True
        or split.get("override_used") is not False
        or split.get("counts")
        != {
            "annotation_dev": 0,
            "annotation_schema_pilot": 30,
            "annotation_train": 0,
            "locked_eval": 0,
        }
        or not isinstance(prefix30, list)
        or selected_ids[:CONTRACT_DEVELOPMENT_PREFIX_COUNT] != prefix30
    ):
        raise N300PoolContractError("immutable split_manifest_v0_1 is not the exact ranked prefix")

    n100_views = list(iter_json_records(n100_views_path))
    n100_pool = read_json(n100_pool_path)
    n100_exposure = read_json(n100_exposure_path)
    n100_records = list(iter_json_records(n100_records_path))
    n100_exploration_plan = read_json(n100_exploration_plan_path)
    n100_run_manifest = read_json(n100_run_manifest_path)
    n100_ids = [view.get("question_id") for view in n100_views]
    if (
        len(n100_views) != PREFIX_RECORD_COUNT
        or any(
            set(view) != {"schema_version", "visibility", "question_id", "question"}
            for view in n100_views
        )
        or n100_ids != selected_ids[:PREFIX_RECORD_COUNT]
        or not isinstance(n100_pool, dict)
        or n100_pool.get("schema_version")
        != "ai_question_structure_exploration_pool_manifest_v0_1"
        or n100_pool.get("selection", {}).get("selected_question_ids") != n100_ids
        or n100_pool.get("selection", {}).get("selected_count") != PREFIX_RECORD_COUNT
        or n100_pool.get("artifacts", {}).get("views", {}).get("sha256")
        != sha256_file(n100_views_path)
        or not isinstance(n100_exposure, dict)
        or n100_exposure.get("schema_version") != "question_exposure_ledger_v0_1"
        or n100_exposure.get("ai_question_structure_exploration", {}).get("question_ids")
        != n100_ids
        or n100_exposure.get("ai_question_structure_exploration", {}).get("count")
        != PREFIX_RECORD_COUNT
        or n100_exposure.get("ai_question_structure_exploration", {}).get(
            "future_unseen_evaluation_allowed"
        )
        is not False
        or len(n100_records) != PREFIX_RECORD_COUNT
        or [record.get("question_id") for record in n100_records] != n100_ids
        or not isinstance(n100_exploration_plan, dict)
        or n100_exploration_plan.get("schema_version")
        != "ai_question_structure_scale_exploration_plan_v0_1"
        or n100_exploration_plan.get("run_id") != FROZEN_RECORD_RUN_ID
        or n100_exploration_plan.get("status") != "contract_frozen_before_model_outputs"
        or not isinstance(n100_run_manifest, dict)
        or n100_run_manifest.get("schema_version")
        != "ai_question_structure_scale_run_manifest_v0_1"
        or n100_run_manifest.get("run_id") != FROZEN_RECORD_RUN_ID
        or n100_run_manifest.get("run_status") != "complete"
    ):
        raise N300PoolContractError("frozen N=100 views/pool/exposure/records are inconsistent")

    views = [_view(question_id, _question(by_id[question_id]) or "") for question_id in selected_ids]
    if views[:PREFIX_RECORD_COUNT] != n100_views:
        raise N300PoolContractError("N=100 views are not the exact object prefix of N=300")
    views_bytes = jsonl_file_bytes(views)
    if not views_bytes.startswith(n100_views_path.read_bytes()):
        raise N300PoolContractError("N=100 view bytes are not the exact byte prefix of N=300")

    source_ids = set(by_id)
    if (
        set(selected_ids) & historical_ids
        or set(selected_ids) & locked_ids
        or set(reserve_ids) & historical_ids
        or set(selected_ids) & set(reserve_ids)
        or historical_ids | set(selected_ids) | set(reserve_ids) != source_ids
        or len(added_ids) != EXPANSION_RECORD_COUNT
        or len(reserve_ids) != EXPECTED_RESERVE_COUNT
    ):
        raise N300PoolContractError("historical/selected/reserve partition is not exact and disjoint")

    partition_views: dict[str, list[dict[str, Any]]] = {
        partition: [] for partition in PRODUCER_PARTITIONS
    }
    assignments: list[dict[str, Any]] = []
    positions_by_partition: dict[str, list[int]] = {
        partition: [] for partition in PRODUCER_PARTITIONS
    }
    for offset, position in enumerate(range(PREFIX_RECORD_COUNT + 1, CUMULATIVE_TARGET + 1)):
        partition = PRODUCER_PARTITIONS[offset % len(PRODUCER_PARTITIONS)]
        view = views[position - 1]
        partition_views[partition].append(view)
        positions_by_partition[partition].append(position)
        assignments.append(
            {
                "committed_position": position,
                "question_id": view["question_id"],
                "question_view_sha256": canonical_json_sha256(view),
                "producer_partition": partition,
            }
        )
    if any(len(partition_views[partition]) != 40 for partition in PRODUCER_PARTITIONS):
        raise N300PoolContractError("five-way routing is not exactly balanced at 40 records each")
    for block_start in range(PREFIX_RECORD_COUNT + 1, CUMULATIVE_TARGET + 1, 10):
        counts = {
            partition: sum(
                assignment["producer_partition"] == partition
                for assignment in assignments
                if block_start <= assignment["committed_position"] < block_start + 10
            )
            for partition in PRODUCER_PARTITIONS
        }
        if set(counts.values()) != {2}:
            raise N300PoolContractError("a ten-question block is not 2-per-producer balanced")

    partition_bytes = {
        partition: jsonl_file_bytes(partition_views[partition])
        for partition in PRODUCER_PARTITIONS
    }
    partition_artifacts = {
        partition: {
            **_payload_binding(
                partition_input_paths[partition],
                partition_bytes[partition],
                project_root,
                record_count=40,
            ),
            "committed_positions": positions_by_partition[partition],
            "committed_positions_ordered_sha256": canonical_json_sha256(
                positions_by_partition[partition]
            ),
        }
        for partition in PRODUCER_PARTITIONS
    }

    routing_manifest = {
        "schema_version": ROUTING_SCHEMA_VERSION,
        "routing_id": ROUTING_ID,
        "status": "contract_frozen_before_positions_101_300_model_outputs",
        "cumulative_target": CUMULATIVE_TARGET,
        "prefix_record_count": PREFIX_RECORD_COUNT,
        "expansion_record_count": EXPANSION_RECORD_COUNT,
        "algorithm": {
            "name": "committed_position_round_robin_v0_1",
            "formula": "partition_index=4+((committed_position-101)%5)",
            "producer_partitions": list(PRODUCER_PARTITIONS),
            "records_per_partition": 40,
            "records_per_ten_question_block_per_partition": 2,
            "committed_order_reordered": False,
            "statistical_independence_claimed": False,
        },
        "model_visible_input_contract": {
            "visible_fields": ["schema_version", "visibility", "question_id", "question"],
            "routing_manifest_exposed": False,
            "producer_administrative_wrapper_exposed": True,
            "environment_answer_grounding_or_other_record_exposed": False,
            "shared_workspace_access_is_not_server_enforced": True,
            "worker_compliance_is_procedural": True,
        },
        "source_bindings": {
            "cumulative_views": _payload_binding(
                output_views_path, views_bytes, project_root, record_count=CUMULATIVE_TARGET
            ),
            "frozen_n100_views": _file_binding(
                n100_views_path, project_root, record_count=PREFIX_RECORD_COUNT
            ),
            "frozen_n100_pool_manifest": _file_binding(n100_pool_path, project_root),
        },
        "assignments": assignments,
        "partition_artifacts": partition_artifacts,
        "planned_model_outputs": {
            partition: {
                "repository_relative_path": _relative(
                    planned_model_output_paths[partition], project_root
                ),
                "expected_record_count": 40,
                "write_status": "not_created_selection_stage",
            }
            for partition in PRODUCER_PARTITIONS
        },
        "evidence_boundary": {
            "routing_is_reviewer_multiplicity": False,
            "routing_is_semantic_evidence": False,
            "human_evidence_count": 0,
            "gold_claimed": False,
        },
    }
    routing_bytes = json_file_bytes(routing_manifest)

    selected_ordered_sha = canonical_json_sha256(selected_ids)
    added_ordered_sha = canonical_json_sha256(added_ids)
    pool_manifest = {
        "schema_version": POOL_SCHEMA_VERSION,
        "builder_version": TOOL_VERSION,
        "purpose": "cumulative_n300_ai_question_structure_selection_no_corpus_role_allocation",
        "status": "selected_n300_materialized_n100_processed_n200_pending",
        "predecessor_manifest": _file_binding(n100_pool_path, project_root),
        "selection": {
            "dataset": "HybridQA",
            "source_split": "dev",
            "seed": SEED,
            "method": "ascending_sha256(seed + NUL + question_id)",
            "cumulative_targets": [30, 100, 300, 1000],
            "current_target": CUMULATIVE_TARGET,
            "eligible_count": len(eligible_ids),
            "selected_count": len(selected_ids),
            "preserved_prefix_count": PREFIX_RECORD_COUNT,
            "contract_development_prefix_count": CONTRACT_DEVELOPMENT_PREFIX_COUNT,
            "added_count": len(added_ids),
            "unexposed_unallocated_reserve_count": len(reserve_ids),
            "selected_question_ids": selected_ids,
            "selected_question_ids_ordered_sha256": selected_ordered_sha,
            "selected_question_ids_set_sha256": canonical_string_set_sha256(selected_ids),
            "added_question_ids": added_ids,
            "added_question_ids_ordered_sha256": added_ordered_sha,
            "added_question_ids_set_sha256": canonical_string_set_sha256(added_ids),
            "eligible_question_ids_set_sha256": canonical_string_set_sha256(eligible_ids),
            "reserve_question_ids_set_sha256": canonical_string_set_sha256(reserve_ids),
            "reserve_question_text_materialized": False,
        },
        "exposure_accounting_at_materialization": {
            "historical_exposed_count": len(historical_ids),
            "prior_ai_processed_prefix_count": PREFIX_RECORD_COUNT,
            "newly_selected_pending_processing_count": len(added_ids),
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
            "locked_eval_overlap_count": 0,
        },
        "artifacts": {
            "views": _payload_binding(
                output_views_path, views_bytes, project_root, record_count=CUMULATIVE_TARGET
            ),
            "prefix_views_n100": {
                **_file_binding(
                    n100_views_path, project_root, record_count=PREFIX_RECORD_COUNT
                ),
                "exact_byte_prefix": True,
            },
            "predecessor_pool_manifest_v0_1": _file_binding(n100_pool_path, project_root),
            "predecessor_exposure_ledger_v0_1": _file_binding(
                n100_exposure_path, project_root
            ),
            "routing_manifest": _payload_binding(
                output_routing_path, routing_bytes, project_root
            ),
            "partition_inputs": partition_artifacts,
            "split_manifest_v0_1": {
                **_file_binding(split_path, project_root),
                "modified": False,
            },
            "historical_manifest": _file_binding(historical_path, project_root),
            "locked_eval_ids": _file_binding(locked_path, project_root),
            "source_manifest": _file_binding(source_manifest_path, project_root),
            "source_question_ids": _file_binding(source_ids_path, project_root),
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
            "builder_artifact": _relative(builder_path, project_root),
            "builder_sha256": sha256_file(builder_path),
        },
        "truthfulness_contract": {
            "selected_questions_are_gold": False,
            "selection_is_semantic_evidence": False,
            "selection_is_model_processing": False,
            "newly_selected_processing_status": "pending",
            "human_validation_required_as_current_gate": False,
            "supported_claim": "deterministic_question_only_cumulative_selection_and_routing",
        },
    }
    pool_bytes = json_file_bytes(pool_manifest)

    exposure_ledger = {
        "schema_version": EXPOSURE_SCHEMA_VERSION,
        "dataset": "HybridQA",
        "source_split": "dev",
        "status": "n300_selection_frozen_n100_processed_n200_pending",
        "predecessor_ledger": _file_binding(n100_exposure_path, project_root),
        "historical_exposure": {
            "manifest": _relative(historical_path, project_root),
            "count": len(historical_ids),
            "future_training_allowed": False,
            "future_unseen_evaluation_allowed": False,
        },
        "ai_question_structure_exploration": {
            "pool_manifest": _relative(output_pool_path, project_root),
            "pool_manifest_sha256": sha256_bytes(pool_bytes),
            "routing_manifest": _relative(output_routing_path, project_root),
            "routing_manifest_sha256": sha256_bytes(routing_bytes),
            "question_ids": selected_ids,
            "question_ids_ordered_sha256": selected_ordered_sha,
            "cumulative_selected_count": len(selected_ids),
            "processed_prefix_count": PREFIX_RECORD_COUNT,
            "selected_pending_processing_count": len(added_ids),
            "processing_segments": [
                {
                    "committed_positions": [1, PREFIX_RECORD_COUNT],
                    "count": PREFIX_RECORD_COUNT,
                    "status": "complete_one_ai_record_per_question",
                    "source_ledger": _relative(n100_exposure_path, project_root),
                },
                {
                    "committed_positions": [PREFIX_RECORD_COUNT + 1, CUMULATIVE_TARGET],
                    "count": len(added_ids),
                    "status": "selected_question_text_materialized_ai_processing_pending",
                },
            ],
            "future_unseen_evaluation_allowed": False,
            "corpus_role_allocated": False,
        },
        "unexposed_unallocated_reserve": {
            "count": len(reserve_ids),
            "question_id_set_sha256": canonical_string_set_sha256(reserve_ids),
            "question_text_materialized": False,
            "role_allocated": False,
        },
        "partition_check": pool_manifest["partition_check"],
        "completion_versioning_policy": {
            "this_selection_stage_ledger_is_immutable": True,
            "all_300_processed_requires_new_ledger_version": "question_exposure_ledger_v0_3",
            "overwrite_v0_2_on_completion": False,
        },
        "evidence_boundary": {
            "human_evidence_count": 0,
            "gold_claimed": False,
            "semantic_correctness_claimed": False,
            "unseen_evaluation_exclusion_is_exposure_accounting_not_correctness": True,
        },
    }
    exposure_bytes = json_file_bytes(exposure_ledger)

    study_plan = read_json(study_plan_path)
    n1000_gate = study_plan.get("stage_gates", {}).get("n1000") if isinstance(study_plan, dict) else None
    if (
        not isinstance(study_plan, dict)
        or study_plan.get("schema_version") != "question_structure_study_plan_v0_2"
        or study_plan.get("sampling_contract", {}).get("cumulative_targets")
        != [30, 100, 300, 1000]
        or not isinstance(n1000_gate, dict)
        or n1000_gate.get("trigger")
        != "material_recurring_new_families_OR_high_singleton_mass_OR_nonflattening_curve_at_n300"
        or n1000_gate.get("same_extractor_and_normalizer_required") is not True
    ):
        raise N300PoolContractError("study plan does not preserve the N=300/N=1000 contract")
    record_schema = read_json(record_schema_path)
    if (
        not isinstance(record_schema, dict)
        or record_schema.get("properties", {}).get("run_id", {}).get("const")
        != FROZEN_RECORD_RUN_ID
    ):
        raise N300PoolContractError("record schema no longer preserves the frozen run_id")
    prompt_text = prompt_path.read_text(encoding="utf-8")
    if "frozen N=100 question-only view" not in prompt_text:
        raise N300PoolContractError("frozen prompt no longer contains the legacy N=100 wording")

    source_artifacts = [
        _file_binding(study_plan_path, project_root),
        _file_binding(historical_path, project_root),
        _file_binding(locked_path, project_root),
        _file_binding(source_manifest_path, project_root),
        _file_binding(source_ids_path, project_root),
        _file_binding(split_path, project_root),
        _file_binding(n100_views_path, project_root, record_count=PREFIX_RECORD_COUNT),
        _file_binding(n100_pool_path, project_root),
        _file_binding(n100_exposure_path, project_root),
        _file_binding(n100_records_path, project_root, record_count=PREFIX_RECORD_COUNT),
        _file_binding(n100_exploration_plan_path, project_root),
        _file_binding(n100_run_manifest_path, project_root),
        _payload_binding(
            output_views_path, views_bytes, project_root, record_count=CUMULATIVE_TARGET
        ),
        _payload_binding(output_pool_path, pool_bytes, project_root),
        _payload_binding(output_exposure_path, exposure_bytes, project_root),
        _payload_binding(output_routing_path, routing_bytes, project_root),
        *[
            _payload_binding(
                partition_input_paths[partition],
                partition_bytes[partition],
                project_root,
                record_count=40,
            )
            for partition in PRODUCER_PARTITIONS
        ],
    ]
    contract_artifacts = [
        _file_binding(prompt_path, project_root),
        _file_binding(record_schema_path, project_root),
        _file_binding(frozen_analyzer_path, project_root),
        _file_binding(builder_path, project_root),
        _file_binding(builder_test_path, project_root),
        _file_binding(cumulative_analyzer_path, project_root),
        _file_binding(cumulative_analyzer_test_path, project_root),
    ]
    producer_wrapper_template = (
        "Fresh fork-none producer assignment: {producer_partition}.\n"
        f"Read only the frozen prompt at {_relative(prompt_path, project_root)}, "
        f"the frozen record schema at {_relative(record_schema_path, project_root)}, "
        "and the assigned four-field JSONL input at {input_path}.\n"
        "The prompt phrase 'frozen N=100 question-only view' is legacy scope wording; "
        "the assigned input is the authorized positions 101-300 extension, so process it "
        "without changing any semantic instruction.\n"
        "Do not inspect any other repository artifact, prior or current worker record, "
        "metric, environment/table/document, answer/trace, or external source.\n"
        "Apply the frozen prompt, schema, provisional roles, and deterministic-normalizer "
        "contract unchanged. Preserve input order and produce exactly one JSONL record per "
        "question. Set producer_partition to the coordinator-supplied constant "
        "{producer_partition} in every record. Compute question_view_sha256 as SHA-256 of the "
        "UTF-8 compact canonical JSON of the exact four-field input object, with keys sorted, "
        "ensure_ascii=false, and comma/colon separators. Do not supply factual answers or model-derived "
        "family/signature fields. Write only the assigned output at {output_path}."
    )
    combined_plan = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "analysis_id": ANALYSIS_ID,
        "status": "contract_frozen_before_positions_101_300_model_outputs",
        "cumulative_target": CUMULATIVE_TARGET,
        "prefix_record_count": PREFIX_RECORD_COUNT,
        "expansion_record_count": EXPANSION_RECORD_COUNT,
        "record_run_id": FROZEN_RECORD_RUN_ID,
        "question_ids": selected_ids,
        "assignments": assignments,
        "source_artifacts": source_artifacts,
        "contract_artifacts": contract_artifacts,
        "selection_contract": {
            "seed": SEED,
            "method": "ascending_sha256(seed + NUL + question_id)",
            "selected_question_ids_ordered_sha256": selected_ordered_sha,
            "selected_question_ids_set_sha256": canonical_string_set_sha256(selected_ids),
            "added_question_ids_ordered_sha256": added_ordered_sha,
            "added_question_ids_set_sha256": canonical_string_set_sha256(added_ids),
            "reserve_count": len(reserve_ids),
            "reserve_question_ids_set_sha256": canonical_string_set_sha256(reserve_ids),
            "n100_exact_object_and_byte_prefix": True,
            "historical_and_locked_overlap_count": 0,
            "split_manifest_modified": False,
        },
        "routing_contract": {
            "routing_id": ROUTING_ID,
            "producer_partitions": list(PRODUCER_PARTITIONS),
            "assignment_formula": "partition_index=4+((committed_position-101)%5)",
            "records_per_partition": 40,
            "records_per_ten_question_block_per_partition": 2,
            "model_visible_inputs_are_exact_four_field_views": True,
            "committed_order_reordered": False,
            "statistical_independence_claimed": False,
        },
        "generation_contract": {
            "one_record_per_question": True,
            "duplicate_reviewer_lanes": False,
            "single_frozen_prompt_and_schema_for_all_300": True,
            "same_frozen_prompt_as_n100": True,
            "same_frozen_record_schema_as_n100": True,
            "same_provisional_roles_as_n100": True,
            "same_deterministic_normalizer_as_n100": True,
            "partitioning_is_throughput_only_not_reviewer_multiplicity": True,
            "partition_workers_share_one_model_identity_contract": True,
            "provisional_roles": [
                "RESOLVE_REFERENT",
                "ACQUIRE_PROPERTY",
                "COMPARE",
                "AGGREGATE",
                "ORDER_OR_EXTREMUM",
                "DERIVE",
                "VERIFY",
                "COMBINE",
                "OTHER",
            ],
            "model_id": "codex_gpt-5",
            "exact_model_revision_status": "revision_not_exposed",
            "seed_status": "not_supported",
            "structured_jsonl_parts_are_primary_capture": True,
            "separate_raw_response_status": (
                "structured_JSONL_parts_are_primary_capture_no_separate_raw_response"
            ),
            "statistical_independence_claimed": False,
            "in_run_prompt_schema_role_or_normalizer_change_allowed": False,
            "other_worker_record_exposed": False,
            "downstream_metric_or_family_exposed": False,
            "environment_exposed": False,
            "answer_or_trace_exposed": False,
            "external_lookup_allowed": False,
            "factual_answer_allowed_in_output": False,
            "model_generated_family_or_signature_allowed": False,
        },
        "normalization_contract": {
            "transitive_reduction": True,
            "exact_node_ID_and_array_order_invariant_canonicalization": True,
            "signature_levels": [
                "fine_semantic_dag",
                "contracted_semantic_dag",
                "topology_shape",
                "task",
            ],
            "same_role_linear_split_merge_contraction": True,
            "model_output_trusted_for_signature": False,
            "post_hoc_semantic_cluster_merging_in_primary_metrics": False,
        },
        "producer_administrative_wrapper": {
            "status": "frozen_before_positions_101_300_model_outputs",
            "worker_context": "fresh_fork_none_no_inherited_conversation_context",
            "required_placeholders": [
                "{producer_partition}",
                "{input_path}",
                "{output_path}",
            ],
            "template": producer_wrapper_template,
        },
        "legacy_prompt_wording_caveat": {
            "prompt_mentions_frozen_n100_view": True,
            "prompt_bytes_changed_for_n300": False,
            "operational_interpretation": (
                "N=100 is legacy scope wording; for this unchanged-contract extension, "
                "assigned records are positions 101-300 from the cumulative N=300 view"
            ),
            "semantic_instruction_change_claimed": False,
        },
        "planned_outputs": {
            "new_model_parts": {
                partition: {
                    "repository_relative_path": _relative(
                        planned_model_output_paths[partition], project_root
                    ),
                    "expected_record_count": 40,
                }
                for partition in PRODUCER_PARTITIONS
            },
            "cumulative_analysis": {
                label: {"repository_relative_path": _relative(path, project_root)}
                for label, path in cumulative_output_paths.items()
            },
        },
        "predecessor_n1000_gate": n1000_gate,
        "precommitted_n1000_decision": {
            "trigger_composition": "ANY",
            "trigger_conditions": {
                "cumulative_contracted_singleton_question_mass": {
                    "operator": ">",
                    "threshold": 0.05,
                },
                "cumulative_OTHER_question_rate_above_0_05": {
                    "operator": ">",
                    "threshold": 0.05,
                },
                "tail_50_sequential_contracted_novelty": {
                    "positions": [251, 300],
                    "novelty_operator": ">",
                    "novelty_threshold": 0.10,
                    "minimum_tail_new_family_count": 2,
                },
                "material_cross_partition_new_contracted_families": {
                    "minimum_family_count": 2,
                    "minimum_new200_question_count_per_family": 3,
                    "minimum_new_partition_support_per_family": 2,
                    "minimum_fixed_ten_question_block_support_per_family": 2,
                },
            },
            "triggered_decision": "EXPAND_UNCHANGED_TO_N1000",
            "no_trigger_decision": (
                "FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_"
                "ENVIRONMENT_REALIZATION"
            ),
            "invalid_run_decision": "NO_DECISION_INVALID_CONTRACT_OR_RECORDS",
            "thresholds_are_design_choices_not_universal_statistical_laws": True,
        },
        "contract_freeze": {
            "builder_code_commit": git_commit_identity(project_root),
            "plan_artifact_commit_status": "pending_commit_of_this_generated_plan",
            "no_circular_plan_binding": True,
        },
        "truthfulness_contract": {
            "human_evidence_count": 0,
            "gold_claimed": False,
            "semantic_correctness_claimed": False,
            "human_agreement_claimed": False,
            "universal_saturation_claimed": False,
            "common_executable_graph_claimed": False,
            "grounding_or_execution_evaluated": False,
            "modeling_ready_claimed": False,
            "positions_101_300_processing_status": "not_started_selection_stage",
        },
    }
    plan_bytes = json_file_bytes(combined_plan)

    return {
        "views": (output_views_path, views_bytes),
        "pool_manifest": (output_pool_path, pool_bytes),
        "exposure_ledger": (output_exposure_path, exposure_bytes),
        "routing_manifest": (output_routing_path, routing_bytes),
        **{
            f"input_{partition}": (
                partition_input_paths[partition],
                partition_bytes[partition],
            )
            for partition in PRODUCER_PARTITIONS
        },
        "combined_plan": (output_plan_path, plan_bytes),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    partition_inputs = _partition_input_paths(args.partition_input_dir)
    planned_parts = _planned_model_output_paths(args.model_parts_dir)
    cumulative_outputs = _cumulative_output_paths(
        args.cumulative_output_dir, args.completion_exposure_ledger
    )
    try:
        batch = build_n300_bundle(
            questions_path=args.questions,
            project_root=args.project_root,
            historical_path=args.historical_manifest,
            locked_path=args.locked_eval_ids,
            source_manifest_path=args.source_manifest,
            source_ids_path=args.source_question_ids,
            split_path=args.split_manifest,
            study_plan_path=args.study_plan,
            n100_views_path=args.n100_views,
            n100_pool_path=args.n100_pool_manifest,
            n100_exposure_path=args.n100_exposure_ledger,
            n100_records_path=args.n100_records,
            n100_exploration_plan_path=args.n100_exploration_plan,
            n100_run_manifest_path=args.n100_run_manifest,
            prompt_path=args.prompt,
            record_schema_path=args.record_schema,
            frozen_analyzer_path=args.frozen_analyzer,
            builder_path=args.builder_artifact,
            builder_test_path=args.builder_test,
            cumulative_analyzer_path=args.cumulative_analyzer,
            cumulative_analyzer_test_path=args.cumulative_analyzer_test,
            output_views_path=args.output_views,
            output_pool_path=args.output_pool_manifest,
            output_exposure_path=args.output_exposure_ledger,
            output_routing_path=args.output_routing_manifest,
            output_plan_path=args.output_plan,
            partition_input_paths=partition_inputs,
            planned_model_output_paths=planned_parts,
            cumulative_output_paths=cumulative_outputs,
        )
        statuses = write_output_batch(batch)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "target": CUMULATIVE_TARGET,
                    "prefix": PREFIX_RECORD_COUNT,
                    "added": EXPANSION_RECORD_COUNT,
                    "reserve": EXPECTED_RESERVE_COUNT,
                    "outputs": statuses,
                },
                sort_keys=True,
            )
        )
        return 0
    except (N300PoolContractError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
