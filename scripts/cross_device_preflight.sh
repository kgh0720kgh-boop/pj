#!/bin/sh

# Non-destructive, repository-relative cross-device readiness check.
# Exit 0: ready; exit 1: validation/check failure; exit 2: declared readiness blocker(s).

set -u

LC_ALL=C
PYTHONDONTWRITEBYTECODE=1
export LC_ALL PYTHONDONTWRITEBYTECODE

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd -P) || {
    printf '%s\n' '[FAIL] PREFLIGHT_LOCATION: cannot resolve script directory'
    exit 1
}
PROJECT_ROOT=$(CDPATH= cd "$SCRIPT_DIR/.." 2>/dev/null && pwd -P) || {
    printf '%s\n' '[FAIL] PREFLIGHT_LOCATION: cannot resolve project root'
    exit 1
}

cd "$PROJECT_ROOT" || {
    printf '%s\n' '[FAIL] PREFLIGHT_LOCATION: cannot enter project root'
    exit 1
}

pass_count=0
warn_count=0
block_count=0
fail_count=0

pass_check() {
    printf '[PASS] %s\n' "$1"
    pass_count=$((pass_count + 1))
}

warn_check() {
    printf '[WARN] %s\n' "$1"
    warn_count=$((warn_count + 1))
}

block_check() {
    printf '[BLOCK] %s\n' "$1"
    block_count=$((block_count + 1))
}

fail_check() {
    printf '[FAIL] %s\n' "$1"
    fail_count=$((fail_count + 1))
}

check_required_file() {
    if [ -f "$1" ]; then
        pass_check "REQUIRED_FILE: $1"
    else
        fail_check "REQUIRED_FILE_MISSING: $1"
    fi
}

printf '%s\n' 'Cross-device preflight (non-destructive)'

for required_file in \
    AGENTS.md \
    HANDOFF_CURRENT.md \
    ENVIRONMENT.md \
    state/project_state.json \
    state/historical_recovery_provenance_v0_1.json \
    reports/cross_device_repo_audit.md \
    scripts/classify_handoff_head.sh \
    scripts/cross_device_preflight.sh \
    .python-version \
    requirements.txt \
    data_construction/README.md \
    data_construction/manifests/historical_exposed_ids.json \
    data_construction/manifests/source_manifest_v0_1.json \
    data_construction/manifests/source_question_ids.json \
    data_construction/manifests/split_manifest_v0_1.json \
    data_construction/pilot/README.md \
    data_construction/pilot/questions.jsonl \
    data_construction/pilot/question_structure_study_plan_v0_1.json \
    data_construction/pilot/question_structure_study_plan_v0_2.json \
    data_construction/pilot/question_only_semantic_views_v0_1.jsonl \
    data_construction/pilot/question_only_semantic_views_manifest_v0_1.json \
    data_construction/pilot/question_structure_review_packets/question_structure_calibration_batch_1_v0_1.html \
    data_construction/pilot/question_structure_review_packets/question_structure_calibration_batch_1_v0_1_manifest.json \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/README.md \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/diagnostic_plan_v0_1.json \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/stage1_observation_schema_v0_1.json \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/annotation_schema_v0_1.json \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/alignment_schema_v0_1.json \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/independent_topology_schema_v0_1.json \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/prompts/reviewer_stage1_v0_1.md \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/prompts/reviewer_stage2_v0_1.md \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/prompts/blinded_alignment_v0_1.md \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/prompts/independent_topology_v0_1.md \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/reviewer_01/stage1.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/reviewer_01/stage1_checks.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/reviewer_01/annotations.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/reviewer_01/annotation_checks.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/reviewer_02/stage1.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/reviewer_02/stage1_checks.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/reviewer_02/annotations.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/reviewer_02/annotation_checks.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/alignment/blinded_pairs.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/alignment/side_map.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/alignment/records.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/alignment/checks.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/independent_topology/records.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/independent_topology/checks.jsonl \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/analysis/metrics_v0_1.json \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/analysis/final_report_v0_1.md \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/analysis/interpretive_addendum_v0_1.md \
    data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/run_manifest.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/README.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/exploration_plan_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/semantic_backbone_record_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/prompts/primary_extraction_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/pool/question_only_views_n100.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/parts/partition_01.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/parts/partition_02.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/parts/partition_03.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/records.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/checks.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/analysis/derived_signatures_v0_1.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/analysis/structural_saturation_metrics_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/analysis/structural_saturation_report_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/analysis/partition_sensitivity_metrics_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/analysis/interpretive_addendum_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/run_001/run_manifest.json \
    data_construction/manifests/ai_question_structure_exploratory_pool_v0_1.json \
    data_construction/manifests/question_exposure_ledger_v0_1.json \
    data_construction/pilot/granularity_representation_plan_v0_1.json \
    data_construction/pilot/granularity_input_views.jsonl \
    data_construction/pilot/granularity_input_views_manifest_v0_1.json \
    data_construction/pilot/granularity_representations.jsonl \
    data_construction/pilot/granularity_deterministic_checks.jsonl \
    data_construction/pilot/review_packets/operator_granularity_coarse_v0_1.html \
    data_construction/pilot/review_packets/operator_granularity_coarse_v0_1_manifest.json \
    data_construction/pilot/review_packets/operator_granularity_medium_v0_1.html \
    data_construction/pilot/review_packets/operator_granularity_medium_v0_1_manifest.json \
    data_construction/pilot/review_packets/operator_granularity_fine_v0_1.html \
    data_construction/pilot/review_packets/operator_granularity_fine_v0_1_manifest.json \
    data_construction/schemas/common_definitions_v0_1.json \
    data_construction/schemas/semantic_skeleton_v0_1.json \
    data_construction/schemas/information_obligation_v0_1.json \
    data_construction/schemas/abstract_topology_v0_1.json \
    data_construction/schemas/operator_topology_v0_1.json \
    data_construction/schemas/grounding_v0_1.json \
    data_construction/schemas/hierarchical_annotation_v0_1.json \
    data_construction/schemas/operator_vocabulary_schema_v0_1.json \
    data_construction/schemas/operator_granularity_pilot_v0_1.json \
    data_construction/schemas/question_only_semantic_view_v0_1.json \
    data_construction/schemas/question_structure_annotation_v0_1.json \
    data_construction/operator_design/operator_vocabulary_coarse_v0_1.json \
    data_construction/operator_design/operator_vocabulary_medium_v0_1.json \
    data_construction/operator_design/operator_vocabulary_fine_v0_1.json \
    data_construction/reports/data_source_audit.md \
    data_construction/reports/annotation_schema_v0_1.md \
    data_construction/reports/operator_granularity_study_v0_1.md \
    data_construction/reports/pilot_annotation_report.md \
    data_construction/reports/corpus_statistics.md \
    data_construction/reports/DATA_CONSTRUCTION_RESEARCH_REPORT.md \
    data_construction/reports/research_sequencing_decision_v0_1.md \
    data_construction/reports/research_sequencing_decision_v0_2.md \
    data_construction/reports/operator_granularity_metrics_v0_1.json \
    data_construction/tools/_common.py \
    data_construction/tools/build_historical_manifest.py \
    data_construction/tools/build_sample.py \
    data_construction/tools/build_question_only_semantic_views.py \
    data_construction/tools/build_question_structure_annotation_packet.py \
    data_construction/tools/check_schema_bundle.py \
    data_construction/tools/fetch_official_hybridqa_sources.sh \
    data_construction/tools/validate_annotation.py \
    data_construction/tools/validate_question_structure_annotations.py \
    data_construction/tools/run_ai_question_structure_diagnostic.py \
    data_construction/tools/build_ai_question_structure_exploration_pool.py \
    data_construction/tools/run_ai_question_structure_scale_exploration.py \
    data_construction/tools/audit_ai_question_structure_partition_sensitivity.py \
    data_construction/tools/validate_ir_v0_2_reference.py \
    data_construction/tools/build_review_packet.py \
    data_construction/tools/build_granularity_views.py \
    data_construction/tools/build_granularity_representations.py \
    data_construction/tools/build_granularity_review_packet.py \
    data_construction/tools/validate_operator_granularity.py \
    data_construction/tools/compare_operator_granularity.py \
    data_construction/tools/compute_annotation_stats.py \
    tests/test_data_construction_tools.py \
    tests/test_ir_v0_2_reference.py \
    tests/test_question_structure_scale_exploration.py \
    tests/test_question_structure_partition_sensitivity.py \
    historical/README.md \
    historical/ir_v0_2/recovery_manifest_v0_1.json \
    historical/ir_v0_2/ir/spec_v0_2.md \
    historical/ir_v0_2/ir/execution_graph.schema.json \
    historical/ir_v0_2/ir/operator_registry_v0_2.json \
    historical/ir_v0_2/ir/type_registry_v0_2.json \
    historical/ir_v0_2/src/hybridqa_graph/ir.py \
    historical/ir_v0_2/src/hybridqa_graph/planning.py \
    historical/ir_v0_2/src/hybridqa_graph/registry.py \
    historical/ir_v0_2/src/hybridqa_graph/validator.py \
    historical/ir_v0_2/experiments/results/week2_pilot/condition_C.jsonl \
    historical/ir_v0_2/experiments/results/week2_pilot/run_manifest.json \
    data_analysis/week1_sample_100.jsonl \
    evaluation/week2_eval_ids.json \
    evaluation/week3_engineering_dev_ids.json \
    evaluation/week3_locked_eval_ids.json \
    evaluation/week3_split_manifest.json
do
    check_required_file "$required_file"
done

PYTHON_BIN=''
if [ -x .venv/bin/python ]; then
    PYTHON_BIN=$PROJECT_ROOT/.venv/bin/python
    printf '%s\n' '[INFO] PYTHON_RUNTIME_SOURCE: repository-local .venv'
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python3)
    printf '%s\n' '[INFO] PYTHON_RUNTIME_SOURCE: PATH python3'
else
    fail_check 'PYTHON3_NOT_FOUND'
fi

if [ -n "$PYTHON_BIN" ]; then
    expected_python=$(tr -d '\r\n' < .python-version 2>/dev/null || printf '%s' unknown)
    actual_python=$("$PYTHON_BIN" -B -c 'import platform; print(platform.python_version())' 2>/dev/null || printf '%s' unknown)
    if [ "$expected_python" = '3.10.12' ]; then
        pass_check 'PYTHON_VERSION_FILE: 3.10.12'
    else
        fail_check "PYTHON_VERSION_FILE_UNEXPECTED: expected project baseline 3.10.12, found $expected_python"
    fi
    if [ "$actual_python" = "$expected_python" ]; then
        pass_check "PYTHON_RUNTIME_VERSION: $actual_python"
    else
        block_check "PYTHON_RUNTIME_VERSION_MISMATCH: expected $expected_python, found $actual_python"
    fi

    json_parse_output=$("$PYTHON_BIN" -B - <<'PY'
import hashlib
import json
import sys
from pathlib import Path

paths = [
    Path("state/project_state.json"),
    Path("state/historical_recovery_provenance_v0_1.json"),
    Path("data_construction/manifests/historical_exposed_ids.json"),
    Path("data_construction/manifests/source_manifest_v0_1.json"),
    Path("data_construction/manifests/source_question_ids.json"),
    Path("data_construction/manifests/split_manifest_v0_1.json"),
    Path("historical/ir_v0_2/recovery_manifest_v0_1.json"),
    Path("data_construction/pilot/question_structure_study_plan_v0_1.json"),
    Path("data_construction/pilot/question_structure_study_plan_v0_2.json"),
    Path("data_construction/pilot/question_only_semantic_views_manifest_v0_1.json"),
    Path("data_construction/pilot/question_structure_review_packets/question_structure_calibration_batch_1_v0_1_manifest.json"),
    Path("data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/diagnostic_plan_v0_1.json"),
    Path("data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/stage1_observation_schema_v0_1.json"),
    Path("data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/annotation_schema_v0_1.json"),
    Path("data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/alignment_schema_v0_1.json"),
    Path("data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/independent_topology_schema_v0_1.json"),
    Path("data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/analysis/metrics_v0_1.json"),
    Path("data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/run_manifest.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/exploration_plan_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/semantic_backbone_record_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/pool/question_only_views_n100.jsonl"),
    Path("data_construction/manifests/ai_question_structure_exploratory_pool_v0_1.json"),
    Path("data_construction/manifests/question_exposure_ledger_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001/parts/partition_01.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001/parts/partition_02.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001/parts/partition_03.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001/records.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001/checks.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001/analysis/derived_signatures_v0_1.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001/analysis/structural_saturation_metrics_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001/analysis/partition_sensitivity_metrics_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001/run_manifest.json"),
    Path("data_construction/pilot/granularity_representation_plan_v0_1.json"),
    Path("data_construction/pilot/granularity_input_views_manifest_v0_1.json"),
    Path("data_construction/reports/operator_granularity_metrics_v0_1.json"),
    Path("data_construction/pilot/review_packets/operator_granularity_coarse_v0_1_manifest.json"),
    Path("data_construction/pilot/review_packets/operator_granularity_medium_v0_1_manifest.json"),
    Path("data_construction/pilot/review_packets/operator_granularity_fine_v0_1_manifest.json"),
]
paths.extend(sorted(Path("data_construction/schemas").glob("*.json")))
paths.extend(sorted(Path("data_construction/operator_design").glob("*.json")))
errors = []
for path in paths:
    try:
        if path.suffix == ".jsonl":
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if line.strip():
                    json.loads(line)
        else:
            json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: {exc}")
if errors:
    print(" | ".join(errors))
    raise SystemExit(1)
print(f"parsed={len(paths)}")
PY
    )
    json_parse_rc=$?
    if [ "$json_parse_rc" -eq 0 ]; then
        pass_check "JSON_PARSE_SET: $json_parse_output"
    else
        fail_check "JSON_PARSE_SET_FAILED: $json_parse_output"
    fi

    contract_output=$("$PYTHON_BIN" -B - <<'PY'
import hashlib
import json
import re
import sys
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def gate_codes(values):
    return {str(value).split(":", 1)[0] for value in values}

errors = []
state = load("state/project_state.json")
history_provenance = load("state/historical_recovery_provenance_v0_1.json")
history = load("data_construction/manifests/historical_exposed_ids.json")
source = load("data_construction/manifests/source_manifest_v0_1.json")
split = load("data_construction/manifests/split_manifest_v0_1.json")
ir_recovery = load("historical/ir_v0_2/recovery_manifest_v0_1.json")
handoff = Path("HANDOFF_CURRENT.md").read_text(encoding="utf-8")
state_gates = gate_codes(state.get("blocked_gates", []))

if state.get("schema_version") != "project_state_v0_1":
    errors.append("project_state schema_version mismatch")
repository = state.get("repository", {})
if state.get("active_branch") != repository.get("current_branch"):
    errors.append("active_branch disagrees with repository.current_branch")
if state.get("expected_head") != repository.get("head"):
    errors.append("expected_head disagrees with repository.head")
sync_state = state.get("synchronization_state")
if sync_state == "REMOTE_NOT_CONFIGURED":
    if repository.get("remotes") != []:
        errors.append("REMOTE_NOT_CONFIGURED disagrees with non-empty remotes")
    if "REMOTE_NOT_CONFIGURED" not in state_gates:
        errors.append("REMOTE_NOT_CONFIGURED missing from blocked_gates")
if sync_state != "SYNCED_TO_REMOTE" and sync_state not in state_gates:
    errors.append("non-synchronized state is absent from blocked_gates")
if sync_state == "SYNCED_TO_REMOTE" and not repository.get("remotes"):
    errors.append("SYNCED_TO_REMOTE disagrees with empty remotes")
if state.get("handoff_readiness") == "not_ready" and not state.get("blocked_gates"):
    errors.append("not_ready handoff has no blocked_gates")
if state.get("handoff_readiness") == "ready" and (
    state.get("blocked_gates") or sync_state != "SYNCED_TO_REMOTE"
):
    errors.append("ready handoff still has gates or is not synchronized")
for field in ("active_branch", "expected_head", "current_scientific_decision", "synchronization_state"):
    value = state.get(field)
    if not isinstance(value, str) or f"`{value}`" not in handoff:
        errors.append(f"HANDOFF_CURRENT.md disagrees with state field {field}")
state_gate_code_list = [str(value).split(":", 1)[0] for value in state.get("blocked_gates", [])]
for gate_code in set(state_gate_code_list):
    if handoff.count(f"`{gate_code}`") < state_gate_code_list.count(gate_code):
        errors.append(f"HANDOFF_CURRENT.md is missing declared gate {gate_code}")
if state.get("handoff_readiness") == "not_ready" and "Handoff readiness: Not ready" not in handoff:
    errors.append("HANDOFF_CURRENT.md readiness disagrees with state")
if state.get("handoff_readiness") == "ready" and "Handoff readiness: Ready" not in handoff:
    errors.append("HANDOFF_CURRENT.md readiness disagrees with state")
if state.get("handoff_readiness") not in {"ready", "not_ready"}:
    errors.append("project_state has unsupported handoff_readiness")

environment = state.get("environment_contract", {})
python_contract = environment.get("python", {})
if python_contract.get("required_version") != "3.10.12":
    errors.append("state Python required_version mismatch")
dependency_contract = environment.get("dependency_contract", {})
if dependency_contract.get("requirements_file") != "requirements.txt":
    errors.append("state requirements_file mismatch")
if dependency_contract.get("manager") != "pip":
    errors.append("state dependency manager must be pip")

expected_historical_paths = [
    "data_analysis/week1_sample_100.jsonl",
    "evaluation/week2_eval_ids.json",
    "evaluation/week3_engineering_dev_ids.json",
    "evaluation/week3_locked_eval_ids.json",
    "evaluation/week3_split_manifest.json",
]
expected_ir_paths = [
    "historical/ir_v0_2/ir/spec_v0_2.md",
    "historical/ir_v0_2/ir/execution_graph.schema.json",
    "historical/ir_v0_2/ir/operator_registry_v0_2.json",
    "historical/ir_v0_2/ir/type_registry_v0_2.json",
    "historical/ir_v0_2/src/hybridqa_graph/ir.py",
    "historical/ir_v0_2/src/hybridqa_graph/planning.py",
    "historical/ir_v0_2/src/hybridqa_graph/registry.py",
    "historical/ir_v0_2/src/hybridqa_graph/validator.py",
    "historical/ir_v0_2/experiments/results/week2_pilot/condition_C.jsonl",
    "historical/ir_v0_2/experiments/results/week2_pilot/run_manifest.json",
]
if state.get("historical_read_only_paths") != expected_historical_paths + expected_ir_paths:
    errors.append("project_state historical_read_only_paths mismatch")
if (
    history_provenance.get("schema_version") != "historical_recovery_provenance_v0_1"
    or history_provenance.get("status") != "researcher_approved_authoritative"
    or history_provenance.get("authority_kind") != "git_commit"
    or history_provenance.get("authority_identity") != "1995c0cf79ab8e987773041d456d4a1b8df19793"
    or [item.get("path") for item in history_provenance.get("files", [])] != expected_historical_paths
):
    errors.append("historical recovery provenance identity/inventory mismatch")
if (
    ir_recovery.get("schema_version") != "historical_ir_v0_2_recovery_manifest_v0_1"
    or ir_recovery.get("status") != "researcher_approved_authoritative"
    or ir_recovery.get("authority_kind") != "git_commit"
    or ir_recovery.get("authority_identity") != "dcc5ac5c14e9acb5c689b400a4046708b6837ac3"
    or [item.get("repository_relative_path") for item in ir_recovery.get("files", [])] != expected_ir_paths
):
    errors.append("IR v0.2 recovery identity/inventory mismatch")
if history.get("schema_version") != "historical_exposed_ids_v0_1":
    errors.append("historical manifest schema_version mismatch")
raw_source_files = history.get("source_files")
if isinstance(raw_source_files, list) and all(isinstance(item, str) for item in raw_source_files):
    historical_shape = "initial_audit"
    historical_paths = raw_source_files
    history_complete = history.get("completeness", {}).get("is_complete")
elif isinstance(raw_source_files, list) and all(isinstance(item, dict) for item in raw_source_files):
    historical_shape = "strict_builder"
    historical_paths = [item.get("path") for item in raw_source_files]
    history_complete = history.get("is_complete")
else:
    historical_shape = "unsupported"
    historical_paths = []
    history_complete = None
    errors.append("historical manifest source_files has unsupported shape")
if historical_paths != expected_historical_paths:
    errors.append("historical manifest source_files mismatch")
if not isinstance(history_complete, bool):
    errors.append("historical completeness must be boolean")
if historical_shape == "initial_audit":
    historical_artifacts_missing = any(
        check.get("current_project_root_exists") is not True
        for check in history.get("source_file_checks", [])
        if isinstance(check, dict)
    )
elif historical_shape == "strict_builder":
    historical_artifacts_missing = bool(history.get("missing_required_files"))
else:
    historical_artifacts_missing = True
if history_complete is False:
    if not str(history.get("audit_status", "")).startswith("incomplete"):
        errors.append("incomplete history has non-incomplete audit_status")
    if historical_shape == "initial_audit" and history.get("known_historical_exposure_count") is not None:
        errors.append("incomplete history must not assert a known exposure count")
    if historical_shape == "initial_audit":
        eligibility = history.get("eligibility", {})
        if eligibility.get("fresh_question_disjointness_verifiable") is not False:
            errors.append("incomplete history cannot verify fresh disjointness")
        if eligibility.get("new_split_release_allowed") is not False:
            errors.append("incomplete history cannot allow a new split release")
    elif historical_shape == "strict_builder":
        if history.get("recovery_provenance_status") == "verified" and not (
            history.get("missing_required_files")
            or history.get("required_files_with_no_question_ids")
            or history.get("known_expected_count_mismatches")
        ):
            errors.append("strict historical manifest is incomplete without a recorded blocking cause")
    required_history_gates = [
        "HISTORICAL_EXPOSED_ID_AUDIT_INCOMPLETE",
        "FRESH_QUESTION_DISJOINTNESS_NOT_VERIFIABLE",
    ]
    if historical_artifacts_missing:
        required_history_gates.append("HISTORICAL_ARTIFACTS_NOT_AVAILABLE")
    for required_gate in required_history_gates:
        if required_gate not in state_gates:
            errors.append(f"state blocked_gates missing {required_gate}")
elif history_complete is True and historical_shape == "strict_builder":
    if history.get("audit_status") != "complete":
        errors.append("complete strict historical manifest has non-complete audit_status")
    if history.get("recovery_provenance_status") != "verified":
        errors.append("complete strict historical manifest lacks verified provenance")
    if any(item.get("status") != "present" for item in raw_source_files):
        errors.append("complete strict historical manifest has a non-present source")
    if any(not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))) for item in raw_source_files):
        errors.append("complete strict historical manifest has an invalid source SHA-256")
    if history.get("missing_required_files") or history.get("required_files_with_no_question_ids"):
        errors.append("complete strict historical manifest retains missing/empty file markers")
    try:
        sys.path.insert(0, str(Path("data_construction/tools").resolve()))
        from build_sample import historical_release_errors
        strict_history_errors = historical_release_errors(history, Path(".").resolve())
    except Exception as exc:
        errors.append(f"strict historical release-contract check could not run: {exc}")
    else:
        errors.extend(f"strict historical release contract: {item}" for item in strict_history_errors)
elif history_complete is True:
    errors.append("complete historical audit must use the strict-builder manifest shape")

if source.get("schema_version") != "source_manifest_v0_1":
    errors.append("source manifest schema_version mismatch")
if source.get("dataset") != "HybridQA":
    errors.append("source manifest dataset must be HybridQA")
if source.get("source_policy") != "official_primary_sources_only":
    errors.append("source policy is not official_primary_sources_only")
if source.get("retrieval_status") != "available_and_locally_verified":
    errors.append("official source retrieval is not locally verified")
upstreams = {item.get("source_id"): item for item in source.get("upstreams", [])}
expected_upstreams = {
    "hybridqa_questions_and_code": (
        "https://github.com/wenhuchen/HybridQA.git",
        "db22fda8c5951438fade3c69d75b350335ba93b3",
    ),
    "hybridqa_linked_tables_and_passages": (
        "https://github.com/wenhuchen/WikiTables-WithLinks.git",
        "dc066e1a6d5281511d8b73a6107d5ad2824cc2b2",
    ),
}
for source_id in ("hybridqa_questions_and_code", "hybridqa_linked_tables_and_passages"):
    item = upstreams.get(source_id)
    if not item:
        errors.append(f"missing official upstream {source_id}")
        continue
    if not re.fullmatch(r"[0-9a-f]{40}", str(item.get("pinned_commit", ""))):
        errors.append(f"{source_id} has invalid pinned_commit")
    expected_repository, expected_commit = expected_upstreams[source_id]
    if item.get("repository_url") != expected_repository or item.get("pinned_commit") != expected_commit:
        errors.append(f"{source_id} does not match the audited v0.1 upstream identity")
    if not item.get("artifacts"):
        errors.append(f"{source_id} has no artifact identities")
combined_ids = source.get("source_id_inventory", {}).get("question_id_sets", {}).get("combined", {})
if not isinstance(combined_ids.get("count"), int) or combined_ids.get("count", 0) <= 0:
    errors.append("source question ID inventory is empty")
if not re.fullmatch(r"[0-9a-f]{64}", str(combined_ids.get("canonical_sha256", ""))):
    errors.append("source combined question ID hash is invalid")
if source.get("local_materialization", {}).get("repository_tracked") is not False:
    errors.append("machine-local official source cache must not be repository-tracked")

if split.get("schema_version") != "split_manifest_v0_1":
    errors.append("split manifest schema_version mismatch")
role_order = ("annotation_schema_pilot", "annotation_train", "annotation_dev", "locked_eval")
if "source_manifest" in split or "historical_exposure_manifest" in split:
    split_shape = "blocked_placeholder"
    if split.get("source_manifest") != "data_construction/manifests/source_manifest_v0_1.json":
        errors.append("blocked split source_manifest reference mismatch")
    if split.get("historical_exposure_manifest") != "data_construction/manifests/historical_exposed_ids.json":
        errors.append("blocked split historical manifest reference mismatch")
    split_gates = gate_codes(split.get("blocked_gates", []))
    if split.get("allocation_performed") is not False:
        errors.append("blocked split cannot report allocation_performed")
    if split.get("release_eligible") is not False:
        errors.append("blocked split cannot be release eligible")
    if split.get("roles") is not None:
        errors.append("blocked split roles must be null")
    if not split_gates:
        errors.append("blocked split has no blocked_gates")
    for split_gate in split_gates:
        if split_gate not in state_gates:
            errors.append(f"state blocked_gates missing split gate {split_gate}")
    if history_complete is False:
        for required_gate in (
            "HISTORICAL_EXPOSED_ID_AUDIT_INCOMPLETE",
            "FRESH_QUESTION_DISJOINTNESS_NOT_VERIFIABLE",
        ):
            if required_gate not in split_gates:
                errors.append(f"blocked split missing {required_gate}")
        if source.get("annotation_release_status") != "blocked_pending_complete_historical_id_audit":
            errors.append("source release status does not reflect incomplete history")
        if source.get("data_availability", {}).get("historical_disjointness_verified") is not False:
            errors.append("source manifest incorrectly claims historical disjointness")
    else:
        errors.append("blocked placeholder split is stale after historical audit completion")
elif all(key in split for key in ("source", "historical_manifest", "roles", "role_artifacts")):
    split_shape = "allocated_builder"
    split_gates = set()
    roles = split.get("roles")
    artifacts = split.get("role_artifacts")
    counts = split.get("counts")
    if not isinstance(roles, dict) or set(roles) != set(role_order):
        errors.append("allocated split roles must contain the exact four role names")
        roles = {}
    if not isinstance(artifacts, dict) or set(artifacts) != set(role_order):
        errors.append("allocated split role_artifacts must contain the exact four role names")
        artifacts = {}
    if not isinstance(counts, dict) or set(counts) != set(role_order):
        errors.append("allocated split counts must contain the exact four role names")
        counts = {}

    all_role_ids = []
    for role in role_order:
        identifiers = roles.get(role)
        if not isinstance(identifiers, list) or not all(isinstance(item, str) and item for item in identifiers):
            errors.append(f"allocated split role {role} has invalid IDs")
            identifiers = []
        if len(identifiers) != len(set(identifiers)):
            errors.append(f"allocated split role {role} has duplicate IDs")
        all_role_ids.extend(identifiers)
        if counts.get(role) != len(identifiers):
            errors.append(f"allocated split count mismatch for {role}")

        artifact = artifacts.get(role)
        if not identifiers:
            if artifact is not None:
                errors.append(f"empty role {role} must have a null artifact")
            continue
        if not isinstance(artifact, dict):
            errors.append(f"non-empty role {role} lacks an artifact")
            continue
        artifact_path = artifact.get("path")
        if (
            not isinstance(artifact_path, str)
            or not artifact_path
            or artifact_path.startswith(("/", "~", "<"))
            or (len(artifact_path) >= 2 and artifact_path[1] == ":")
        ):
            errors.append(f"role artifact path is not repository-relative for {role}")
            continue
        project_root = Path(".").resolve()
        local_artifact = (project_root / artifact_path).resolve()
        try:
            local_artifact.relative_to(project_root)
        except ValueError:
            errors.append(f"role artifact escapes the project root for {role}")
            continue
        if not local_artifact.is_file():
            errors.append(f"role artifact file is missing for {role}: {artifact_path}")
            continue
        actual_sha256 = hashlib.sha256(local_artifact.read_bytes()).hexdigest()
        if artifact.get("sha256") != actual_sha256:
            errors.append(f"role artifact SHA-256 mismatch for {role}")
        if artifact.get("record_count") != len(identifiers):
            errors.append(f"role artifact record_count mismatch for {role}")
        records = []
        try:
            for line in local_artifact.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    records.append(json.loads(line))
        except Exception as exc:
            errors.append(f"role artifact JSONL parse failed for {role}: {exc}")
            records = []
        artifact_ids = [record.get("question_id") for record in records if isinstance(record, dict)]
        if artifact_ids != identifiers:
            errors.append(f"role artifact ID order/content mismatch for {role}")
        if any(record.get("dataset_role") != role for record in records if isinstance(record, dict)):
            errors.append(f"role artifact dataset_role mismatch for {role}")
        allowed_question_only_keys = {
            "question_id",
            "question",
            "table_id",
            "dataset_role",
            "source_split",
            "annotation_visibility",
        }
        for record in records:
            if not isinstance(record, dict):
                errors.append(f"role artifact has a non-object record for {role}")
                continue
            if set(record) != allowed_question_only_keys:
                errors.append(f"role artifact has forbidden or missing question-only fields for {role}")
            if record.get("annotation_visibility") != "question_and_table_identity_only":
                errors.append(f"role artifact annotation_visibility mismatch for {role}")
        expected_tuning = role != "locked_eval"
        if artifact.get("tuning_allowed") is not expected_tuning:
            errors.append(f"role artifact tuning_allowed mismatch for {role}")
        expected_visibility = "evaluation_only" if role == "locked_eval" else "annotation_role_only"
        if artifact.get("visibility") != expected_visibility:
            errors.append(f"role artifact visibility mismatch for {role}")

    if len(all_role_ids) != len(set(all_role_ids)):
        errors.append("allocated split role IDs overlap")
    if not all_role_ids:
        errors.append("allocated split contains no questions")
    historical_forbidden = history.get("forbidden_future_training_ids")
    historical_exposed = history.get("exposed_question_ids")
    if not isinstance(historical_forbidden, list) or not all(isinstance(item, str) for item in historical_forbidden):
        errors.append("historical forbidden ID inventory is unavailable for allocated split")
        historical_forbidden = []
    if not isinstance(historical_exposed, list) or not all(isinstance(item, str) for item in historical_exposed):
        errors.append("historical exposed ID inventory is unavailable for allocated split")
        historical_exposed = []
    overlap = set(all_role_ids) & (set(historical_forbidden) | set(historical_exposed))
    if overlap:
        errors.append("allocated split includes historically exposed or forbidden IDs")
    if split.get("zero_overlap_verified") is not True:
        errors.append("allocated split does not verify zero overlap")
    if split.get("combined_role_output_written") is not False:
        errors.append("allocated split must keep isolated role artifacts")

    split_source = split.get("source", {})
    official_upstream = upstreams.get("hybridqa_questions_and_code", {})
    allowed_question_paths = {"released_data/train.json", "released_data/dev.json"}
    official_question_artifacts = {
        artifact.get("path"): artifact
        for artifact in official_upstream.get("artifacts", [])
        if isinstance(artifact, dict) and artifact.get("path") in allowed_question_paths
    }
    expected_question_artifacts = {
        "released_data/train.json": (
            "b33aa73638959a2383e1e1638fd6abe87818b7379c7a42eac1621475d2d959e2",
            62682,
            "fede3106c7430f731a15bb466ebb4e1c7c74e7e9b11df0d3565ab989c1f68dd2",
        ),
        "released_data/dev.json": (
            "424272b233735a70ed8ef5af4a615373d114f472168c686c4370d54c92d58ac1",
            3466,
            "70ee935abae8409251e0858a46d7a92f7875e2bfa0d8084f8ab3bb1cd591f584",
        ),
    }
    source_id_sets = source.get("source_id_inventory", {}).get("question_id_sets", {})
    for artifact_path, (expected_sha256, expected_count, expected_id_sha256) in expected_question_artifacts.items():
        artifact = official_question_artifacts.get(artifact_path)
        source_split_name = Path(artifact_path).stem
        id_set = source_id_sets.get(source_split_name) if isinstance(source_id_sets, dict) else None
        if (
            not isinstance(artifact, dict)
            or artifact.get("sha256") != expected_sha256
            or artifact.get("record_count") != expected_count
            or artifact.get("unique_question_id_count") != expected_count
            or not isinstance(id_set, dict)
            or id_set.get("count") != expected_count
            or id_set.get("canonical_sha256") != expected_id_sha256
        ):
            errors.append(f"official v0.1 question artifact identity mismatch: {artifact_path}")
    portable_reference = split_source.get("portable_reference")
    if split.get("allocation_method") != "ascending_sha256(seed + NUL + question_id)":
        errors.append("allocated split allocation_method mismatch")
    if not isinstance(split.get("seed"), str) or not split.get("seed"):
        errors.append("allocated split seed is missing")
    if split_source.get("verified_against_pinned_manifest") is not True:
        errors.append("allocated split source is not verified against the pinned manifest")
    if split_source.get("malformed_record_count") != 0:
        errors.append("allocated split source reports malformed records")
    if not isinstance(portable_reference, dict):
        errors.append("allocated split lacks a portable official source reference")
    else:
        artifact_path = portable_reference.get("artifact_path")
        official_artifact = official_question_artifacts.get(artifact_path)
        if portable_reference.get("source_id") != "hybridqa_questions_and_code":
            errors.append("allocated split portable source_id mismatch")
        if portable_reference.get("pinned_commit") != official_upstream.get("pinned_commit"):
            errors.append("allocated split portable pinned_commit mismatch")
        if not isinstance(official_artifact, dict):
            errors.append("allocated split source is not pinned train/dev data")
        else:
            expected_source = expected_question_artifacts.get(artifact_path)
            if portable_reference.get("artifact_sha256") != official_artifact.get("sha256"):
                errors.append("allocated split portable artifact SHA-256 mismatch")
            if split_source.get("sha256") != official_artifact.get("sha256"):
                errors.append("allocated split source SHA-256 mismatch")
            if split_source.get("record_count") != official_artifact.get("record_count"):
                errors.append("allocated split source record_count mismatch")
            if expected_source is None:
                errors.append("allocated split source lacks a canonical ID-set contract")
            else:
                expected_id_sha256 = expected_source[2]
                if portable_reference.get("record_count") != expected_source[1]:
                    errors.append("allocated split portable record_count mismatch")
                if portable_reference.get("question_id_set_sha256") != expected_id_sha256:
                    errors.append("allocated split portable question-ID set hash mismatch")
                if split_source.get("question_id_set_sha256") != expected_id_sha256:
                    errors.append("allocated split source question-ID set hash mismatch")
                inventory_artifact = split_source.get("question_id_inventory_artifact")
                if not isinstance(inventory_artifact, dict):
                    errors.append("allocated split lacks a source question-ID inventory artifact")
                else:
                    inventory_path_value = inventory_artifact.get("path")
                    project_root = Path(".").resolve()
                    if not isinstance(inventory_path_value, str):
                        errors.append("source question-ID inventory path is missing")
                    else:
                        inventory_path = (project_root / inventory_path_value).resolve()
                        try:
                            inventory_path.relative_to(project_root)
                        except ValueError:
                            errors.append("source question-ID inventory escapes project root")
                        else:
                            if not inventory_path.is_file():
                                errors.append("source question-ID inventory file is missing")
                            elif hashlib.sha256(inventory_path.read_bytes()).hexdigest() != inventory_artifact.get("sha256"):
                                errors.append("source question-ID inventory file hash mismatch")
                            else:
                                try:
                                    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
                                except Exception as exc:
                                    errors.append(f"source question-ID inventory parse failed: {exc}")
                                else:
                                    inventory_ids = inventory.get("question_ids") if isinstance(inventory, dict) else None
                                    if not isinstance(inventory_ids, list) or not all(
                                        isinstance(item, str) and "\n" not in item and "\r" not in item
                                        for item in inventory_ids
                                    ):
                                        errors.append("source question-ID inventory contains invalid IDs")
                                    else:
                                        canonical_payload = b"".join(
                                            item.encode("utf-8") + b"\n"
                                            for item in sorted(set(inventory_ids), key=lambda value: value.encode("utf-8"))
                                        )
                                        observed_id_sha256 = hashlib.sha256(canonical_payload).hexdigest()
                                        if (
                                            len(inventory_ids) != expected_source[1]
                                            or len(inventory_ids) != len(set(inventory_ids))
                                            or observed_id_sha256 != expected_id_sha256
                                            or inventory.get("question_id_set_sha256") != expected_id_sha256
                                            or inventory_artifact.get("record_count") != expected_source[1]
                                            or inventory_artifact.get("question_id_set_sha256") != expected_id_sha256
                                        ):
                                            errors.append("source question-ID inventory disagrees with canonical source")
                                        if not set(all_role_ids).issubset(set(inventory_ids)):
                                            errors.append("allocated split contains IDs outside the pinned source inventory")
            expected_source_split = Path(artifact_path).stem
            for role in role_order:
                artifact = artifacts.get(role)
                if not isinstance(artifact, dict):
                    continue
                artifact_path_value = artifact.get("path")
                if not isinstance(artifact_path_value, str) or artifact_path_value.startswith(("/", "~", "<")):
                    continue
                role_path = (Path(".").resolve() / artifact_path_value).resolve()
                try:
                    role_path.relative_to(Path(".").resolve())
                except ValueError:
                    continue
                if not role_path.is_file():
                    continue
                try:
                    role_records = [
                        json.loads(line)
                        for line in role_path.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
                except Exception:
                    continue
                if any(record.get("source_split") != expected_source_split for record in role_records):
                    errors.append(f"role artifact source_split mismatch for {role}")

    split_history = split.get("historical_manifest", {})
    current_history_sha256 = hashlib.sha256(
        Path("data_construction/manifests/historical_exposed_ids.json").read_bytes()
    ).hexdigest()
    if split_history.get("sha256") != current_history_sha256:
        errors.append("allocated split historical manifest SHA-256 mismatch")
    if split_history.get("audit_status") != "complete":
        errors.append("allocated split does not record a complete historical audit")
    if split_history.get("release_contract_errors") != []:
        errors.append("allocated split records historical release contract errors")
    if history_complete is not True:
        errors.append("allocated split exists while current historical audit is incomplete")
    if split.get("release_eligible") is not True:
        errors.append("allocated canonical split is not release eligible")
    if split.get("override_used") is not False:
        errors.append("allocated release split used a diagnostic override")
    if split.get("warnings") not in ([], None):
        errors.append("allocated release split retains warnings")
else:
    split_shape = "unsupported"
    split_gates = set()
    errors.append("split manifest has unsupported shape")

if state.get("current_scientific_decision") == "DATA_SOURCE_BLOCKED":
    required_source_gates = ["AUTHORITATIVE_PROJECT_PROVENANCE_NOT_AVAILABLE"]
    if historical_artifacts_missing:
        required_source_gates.append("HISTORICAL_ARTIFACTS_NOT_AVAILABLE")
    for required_gate in required_source_gates:
        if required_gate not in state_gates:
            errors.append(f"DATA_SOURCE_BLOCKED state missing {required_gate}")
elif state.get("current_scientific_decision") in {
    "DATA_SOURCE_READY_FOR_ANNOTATION_PILOT",
    "UNDECIDED_NEEDS_ANNOTATION_EVIDENCE",
    "UNDECIDED_NEEDS_SCALE_EVIDENCE",
}:
    if history_complete is not True or historical_shape != "strict_builder":
        errors.append("pilot-ready state requires a complete strict historical audit")
    if split_shape != "allocated_builder" or split.get("release_eligible") is not True:
        errors.append("pilot-ready state requires a release-eligible allocated split")
    expected_pilot_counts = {
        "annotation_schema_pilot": 30,
        "annotation_train": 0,
        "annotation_dev": 0,
        "locked_eval": 0,
    }
    if split.get("counts") != expected_pilot_counts:
        errors.append("pilot-ready split counts mismatch")
    resolved_gate_codes = {
        "AUTHORITATIVE_PROJECT_PROVENANCE_NOT_AVAILABLE",
        "HISTORICAL_ARTIFACTS_NOT_AVAILABLE",
        "HISTORICAL_EXPOSED_ID_AUDIT_INCOMPLETE",
        "FRESH_QUESTION_DISJOINTNESS_NOT_VERIFIABLE",
        "IR_V0_2_DEFINITION_AND_VALIDATOR_NOT_RECOVERED",
        "PROJECT_LOCAL_PINNED_ENVIRONMENT_NOT_RECONSTRUCTED",
    }
    if state_gates & resolved_gate_codes:
        errors.append("pilot-ready state retains a resolved recovery/environment gate")
    if state.get("current_scientific_decision") == "UNDECIDED_NEEDS_ANNOTATION_EVIDENCE":
        if state.get("active_phase") != "phase_2a_question_only_semantic_calibration":
            errors.append("question-first state has an unexpected active_phase")
        if state.get("scientific_decision_status") != (
            "question_only_calibration_required_phase_b_deferred"
        ):
            errors.append("question-first state has an unexpected scientific_decision_status")
        pilot = state.get("artifact_status", {}).get("operator_granularity_pilot", {})
        expected_pilot_summary = {
            "status": "structural_integrity_complete_phase_b_deferred",
            "question_count": 30,
            "representation_count": 90,
            "deterministic_check_count": 90,
            "deterministic_pass_count": 90,
            "deterministic_error_count": 0,
            "deterministic_warning_count": 0,
            "review_packet_count": 3,
            "human_review_record_count": 0,
            "integrity_complete": True,
            "human_calibration_complete": False,
            "evidence_complete": False,
            "semantic_confirmation_complete": False,
            "selection_ready": False,
            "selected_vocabulary": None,
            "reviewer_authentication_status": "procedural_not_machine_verifiable",
            "researcher_approved_reviewer_attestation": "not_recorded",
        }
        for key, expected_value in expected_pilot_summary.items():
            if pilot.get(key) != expected_value:
                errors.append(f"operator-granularity pilot state mismatch for {key}")
        for stale_gate in (
            "OPERATOR_GRANULARITY_PILOT_NOT_RUN",
            "ANNOTATION_PROPOSALS_NOT_CREATED",
            "HUMAN_REVIEW_NOT_PERFORMED",
        ):
            if stale_gate in state_gates:
                errors.append(f"completed pilot state retains stale gate {stale_gate}")
        if "QUESTION_ONLY_CALIBRATION_NOT_PERFORMED" not in state_gates:
            errors.append(
                "question-first calibration state lacks QUESTION_ONLY_CALIBRATION_NOT_PERFORMED"
            )

        calibration = state.get("artifact_status", {}).get(
            "question_only_semantic_calibration", {}
        )
        expected_calibration_summary = {
            "status": "phase_a0_materialized_phase_a1_human_collection_pending",
            "instrument_contract_frozen": True,
            "question_view_count": 30,
            "question_view_field_allowlist": [
                "schema_version",
                "visibility",
                "question_id",
                "question",
            ],
            "active_batch_id": "phase_a1_batch_01",
            "active_batch_question_count": 10,
            "required_reviewer_count": 2,
            "expected_raw_artifact_count": 2,
            "expected_records_per_raw_artifact": 10,
            "human_raw_artifact_count": 0,
            "human_raw_record_count": 0,
            "researcher_manual_signoff_recorded": False,
            "packet_only_validation": (
                "passed_exact_render_hash_order_and_provenance_contract"
            ),
            "raw_annotation_validation_status": "not_run_no_human_raw_files",
            "semantic_alignment_artifact_status": "not_created",
            "semantic_alignment_comparator_status": "not_implemented",
            "semantic_agreement_claimed": False,
            "held_out_confirmation_complete": False,
            "raw_representation_kind": "elicited_linked_representation",
            "raw_evidence_scope": "representability_and_instrument_operability_only",
            "question_structure_to_graph_relationship_claimed": False,
            "independent_blinded_topology_protocol_status": (
                "not_created_required_before_phase_b_normalization_or_cross_level_claim"
            ),
        }
        for key, expected_value in expected_calibration_summary.items():
            if calibration.get(key) != expected_value:
                errors.append(f"question-only calibration state mismatch for {key}")

        expected_calibration_artifacts = {
            "study_plan": "data_construction/pilot/question_structure_study_plan_v0_1.json",
            "sequencing_decision": (
                "data_construction/reports/research_sequencing_decision_v0_1.md"
            ),
            "question_views": (
                "data_construction/pilot/question_only_semantic_views_v0_1.jsonl"
            ),
            "question_views_manifest": (
                "data_construction/pilot/question_only_semantic_views_manifest_v0_1.json"
            ),
            "question_view_schema": (
                "data_construction/schemas/question_only_semantic_view_v0_1.json"
            ),
            "raw_annotation_schema": (
                "data_construction/schemas/question_structure_annotation_v0_1.json"
            ),
            "active_packet": (
                "data_construction/pilot/question_structure_review_packets/"
                "question_structure_calibration_batch_1_v0_1.html"
            ),
            "active_packet_manifest": (
                "data_construction/pilot/question_structure_review_packets/"
                "question_structure_calibration_batch_1_v0_1_manifest.json"
            ),
        }
        calibration_artifacts = calibration.get("artifacts", {})
        if not isinstance(calibration_artifacts, dict) or set(calibration_artifacts) != set(
            expected_calibration_artifacts
        ):
            errors.append("question-only calibration artifact inventory mismatch")
            calibration_artifacts = (
                calibration_artifacts if isinstance(calibration_artifacts, dict) else {}
            )
        project_root = Path(".").resolve()
        for label, expected_path in expected_calibration_artifacts.items():
            reference = calibration_artifacts.get(label)
            if not isinstance(reference, dict) or reference.get("path") != expected_path:
                errors.append(f"question-only calibration state lacks artifact {label}")
                continue
            artifact_path = (project_root / expected_path).resolve()
            try:
                artifact_path.relative_to(project_root)
            except ValueError:
                errors.append(f"question-only calibration artifact escapes repository: {label}")
                continue
            if not artifact_path.is_file():
                errors.append(f"question-only calibration artifact is missing: {label}")
                continue
            if reference.get("sha256") != hashlib.sha256(artifact_path.read_bytes()).hexdigest():
                errors.append(f"question-only calibration artifact hash mismatch: {label}")
        packet_reference = calibration_artifacts.get("active_packet", {})
        packet_manifest_path = Path(
            expected_calibration_artifacts["active_packet_manifest"]
        )
        try:
            packet_manifest = load(packet_manifest_path)
        except Exception as exc:
            errors.append(f"cannot inspect active question-only packet manifest: {exc}")
        else:
            if packet_reference.get("payload_sha256") != packet_manifest.get(
                "packet_payload", {}
            ).get("sha256"):
                errors.append("question-only calibration packet payload hash mismatch")

        diagnostic = state.get("artifact_status", {}).get(
            "ai_question_structure_pipeline_diagnostic", {}
        )
        expected_diagnostic_summary = {
            "status": "complete_non_evidentiary_shadow_run",
            "run_id": "ai_question_structure_pipeline_v0_1_run_001",
            "purpose": "engineering_pipeline_rehearsal_only",
            "contract_freeze_commit": "fb2ba9e29221c16dd8e1ee71439339d17a92818a",
            "question_count": 30,
            "reviewer_count": 2,
            "stage1_record_count": 60,
            "structured_record_count": 60,
            "blinded_alignment_record_count": 30,
            "independent_topology_record_count": 20,
            "pipeline_execution_status": "complete",
            "scientific_gate_status": "NOT_EVALUATED_AI_SUBSTITUTE",
        }
        for key, expected_value in expected_diagnostic_summary.items():
            if diagnostic.get(key) != expected_value:
                errors.append(f"AI diagnostic state mismatch for {key}")
        expected_diagnostic_effects = {
            "human_evidence_count": 0,
            "human_agreement_observation_count": 0,
            "phase_a1_pass_claimed": False,
            "phase_a2_entry_claimed": False,
            "phase_b_entry_claimed": False,
            "gold_claimed": False,
            "modeling_ready_claimed": False,
            "common_executable_graph_claimed": False,
            "grounding_or_execution_evaluated": False,
        }
        if diagnostic.get("canonical_effects") != expected_diagnostic_effects:
            errors.append("AI diagnostic canonical effects are not the exact non-evidentiary boundary")
        expected_diagnostic_findings = {
            "full_equivalence_question_count": 10,
            "compatible_variation_question_count": 20,
            "calibration_compatible_or_full_rate": 1.0,
            "shadow_holdout_compatible_or_full_rate": 1.0,
            "reviewer_01_instrument_issue_count": 19,
            "reviewer_02_instrument_issue_count": 0,
            "ambiguity_flag_exact_match_count": 25,
            "alternative_plan_presence_exact_match_count": 20,
            "scalar_alternative_plan_conflict_count": 2,
            "independent_topology_exact_signature_rate_reviewer_01": 0.85,
            "independent_topology_exact_signature_rate_reviewer_02": 0.9,
            "interpretation": "core_linked_dag_concordance_high_but_instrument_issue_ambiguity_and_alternative_plan_sensitivity_remain_and_ai_alignment_is_not_correctness",
        }
        if diagnostic.get("diagnostic_findings") != expected_diagnostic_findings:
            errors.append("AI diagnostic finding summary mismatch")
        expected_diagnostic_artifacts = {
            "plan": "data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/diagnostic_plan_v0_1.json",
            "run_manifest": "data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/run_manifest.json",
            "metrics": "data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/analysis/metrics_v0_1.json",
            "generated_report": "data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/analysis/final_report_v0_1.md",
            "interpretive_addendum": "data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/analysis/interpretive_addendum_v0_1.md",
        }
        diagnostic_artifacts = diagnostic.get("artifacts", {})
        if not isinstance(diagnostic_artifacts, dict) or set(diagnostic_artifacts) != set(
            expected_diagnostic_artifacts
        ):
            errors.append("AI diagnostic artifact inventory mismatch")
            diagnostic_artifacts = (
                diagnostic_artifacts if isinstance(diagnostic_artifacts, dict) else {}
            )
        for label, expected_path in expected_diagnostic_artifacts.items():
            reference = diagnostic_artifacts.get(label)
            path = Path(expected_path)
            if not isinstance(reference, dict) or reference.get("path") != expected_path:
                errors.append(f"AI diagnostic state lacks artifact {label}")
            elif not path.is_file():
                errors.append(f"AI diagnostic artifact is missing: {label}")
            elif reference.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append(f"AI diagnostic artifact hash mismatch: {label}")
        try:
            diagnostic_metrics = load(expected_diagnostic_artifacts["metrics"])
            diagnostic_manifest = load(expected_diagnostic_artifacts["run_manifest"])
        except Exception as exc:
            errors.append(f"cannot inspect AI diagnostic outputs: {exc}")
        else:
            if (
                diagnostic_metrics.get("pipeline_execution_status") != "complete"
                or diagnostic_metrics.get("scientific_gate_status")
                != "NOT_EVALUATED_AI_SUBSTITUTE"
                or diagnostic_metrics.get("canonical_research_status", {}).get(
                    "human_evidence_count"
                )
                != 0
                or diagnostic_metrics.get("canonical_research_status", {}).get(
                    "phase_a1_pass_claimed"
                )
                is not False
            ):
                errors.append("AI diagnostic metrics overstate their scientific status")
            if (
                diagnostic_manifest.get("run_status") != "complete"
                or diagnostic_manifest.get("contract_freeze_commit")
                != "fb2ba9e29221c16dd8e1ee71439339d17a92818a"
                or diagnostic_manifest.get("canonical_effects")
                != diagnostic_metrics.get("canonical_research_status")
            ):
                errors.append("AI diagnostic manifest status or evidence boundary mismatch")
    elif state.get("current_scientific_decision") == "UNDECIDED_NEEDS_SCALE_EVIDENCE":
        if state.get("active_phase") != "phase_2a_ai_scale_first_question_structure_exploration":
            errors.append("scale-first state has an unexpected active_phase")
        if state.get("scientific_decision_status") != (
            "n100_complete_n300_expansion_required_human_validation_deferred"
        ):
            errors.append("scale-first state has an unexpected scientific_decision_status")
        if "N300_SCALE_EXPANSION_NOT_PERFORMED" not in state_gates:
            errors.append("scale-first state lacks N300_SCALE_EXPANSION_NOT_PERFORMED")
        if "QUESTION_ONLY_CALIBRATION_NOT_PERFORMED" in state_gates:
            errors.append("scale-first state retains the deferred human-calibration gate")

        calibration = state.get("artifact_status", {}).get(
            "question_only_semantic_calibration", {}
        )
        expected_deferred_calibration = {
            "status": "phase_a0_materialized_human_collection_deferred",
            "active_gate": False,
            "workflow_disposition": "preserved_deferred_not_active_gate",
            "human_raw_artifact_count": 0,
            "human_raw_record_count": 0,
            "semantic_agreement_claimed": False,
            "held_out_confirmation_complete": False,
        }
        for key, expected_value in expected_deferred_calibration.items():
            if calibration.get(key) != expected_value:
                errors.append(f"deferred question-only calibration state mismatch for {key}")

        expected_calibration_artifacts = {
            "study_plan": "data_construction/pilot/question_structure_study_plan_v0_1.json",
            "sequencing_decision": (
                "data_construction/reports/research_sequencing_decision_v0_1.md"
            ),
            "question_views": (
                "data_construction/pilot/question_only_semantic_views_v0_1.jsonl"
            ),
            "question_views_manifest": (
                "data_construction/pilot/question_only_semantic_views_manifest_v0_1.json"
            ),
            "question_view_schema": (
                "data_construction/schemas/question_only_semantic_view_v0_1.json"
            ),
            "raw_annotation_schema": (
                "data_construction/schemas/question_structure_annotation_v0_1.json"
            ),
            "active_packet": (
                "data_construction/pilot/question_structure_review_packets/"
                "question_structure_calibration_batch_1_v0_1.html"
            ),
            "active_packet_manifest": (
                "data_construction/pilot/question_structure_review_packets/"
                "question_structure_calibration_batch_1_v0_1_manifest.json"
            ),
        }
        calibration_artifacts = calibration.get("artifacts", {})
        if not isinstance(calibration_artifacts, dict) or set(calibration_artifacts) != set(
            expected_calibration_artifacts
        ):
            errors.append("deferred question-only calibration artifact inventory mismatch")
            calibration_artifacts = (
                calibration_artifacts if isinstance(calibration_artifacts, dict) else {}
            )
        for label, expected_path in expected_calibration_artifacts.items():
            reference = calibration_artifacts.get(label)
            path = Path(expected_path)
            if not isinstance(reference, dict) or reference.get("path") != expected_path:
                errors.append(f"deferred question-only calibration lacks artifact {label}")
            elif not path.is_file():
                errors.append(f"deferred question-only calibration artifact is missing: {label}")
            elif reference.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append(f"deferred question-only calibration artifact hash mismatch: {label}")

        scale = state.get("artifact_status", {}).get(
            "ai_question_structure_scale_exploration", {}
        )
        expected_scale_summary = {
            "status": "n100_complete_n300_expansion_required_partition_sensitivity_audited",
            "active_gate": True,
            "run_id": "ai_question_structure_scale_v0_1_run_001",
            "evidence_class": "ai_exploratory_non_human_non_gold",
            "contract_freeze_commit": "5adb85277928676eb82fa5189390c442fd6c70bc",
            "question_count": 100,
            "prefix_contract_development_count": 30,
            "new_expansion_count": 70,
            "valid_record_count": 100,
            "invalid_record_count": 0,
            "contracted_family_count": 17,
            "contracted_singleton_question_mass": 0.09,
            "contracted_new70_transfer_rate": 0.7142857142857143,
            "uncertain_record_count": 29,
            "other_question_count": 0,
            "precommitted_decision": "EXPAND_UNCHANGED_TO_N300",
            "decision_trigger": (
                "at_least_2_new_contracted_families_each_recur_at_least_twice_in_new70"
            ),
            "ai_exposed_question_count": 100,
            "unexposed_unallocated_reserve_count": 3266,
            "human_evidence_count": 0,
            "gold_claimed": False,
            "semantic_correctness_claimed": False,
            "human_agreement_claimed": False,
            "universal_saturation_claimed": False,
            "common_executable_graph_claimed": False,
            "grounding_or_execution_evaluated": False,
            "modeling_ready_claimed": False,
        }
        for key, expected_value in expected_scale_summary.items():
            if scale.get(key) != expected_value:
                errors.append(f"AI scale-exploration state mismatch for {key}")

        expected_partition_sensitivity = {
            "status": "post_hoc_audit_complete",
            "recurring_new_contracted_family_count": 5,
            "cross_partition_recurring_new_contracted_family_count": 0,
            "partition_confounding_detected": True,
            "raw_branch_question_count": 5,
            "reduced_branch_question_count": 0,
            "raw_join_question_count": 6,
            "reduced_join_question_count": 1,
            "operational_decision_changed": False,
        }
        if scale.get("partition_sensitivity") != expected_partition_sensitivity:
            errors.append("AI scale-exploration partition-sensitivity summary mismatch")

        expected_scale_artifacts = {
            "study_plan": "data_construction/pilot/question_structure_study_plan_v0_2.json",
            "sequencing_decision": (
                "data_construction/reports/research_sequencing_decision_v0_2.md"
            ),
            "exploration_plan": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "contracts/exploration_plan_v0_1.json"
            ),
            "record_schema": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "contracts/semantic_backbone_record_schema_v0_1.json"
            ),
            "prompt": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "prompts/primary_extraction_v0_1.md"
            ),
            "pool_views": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "pool/question_only_views_n100.jsonl"
            ),
            "pool_manifest": (
                "data_construction/manifests/"
                "ai_question_structure_exploratory_pool_v0_1.json"
            ),
            "records": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "run_001/records.jsonl"
            ),
            "checks": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "run_001/checks.jsonl"
            ),
            "derived_signatures": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "run_001/analysis/derived_signatures_v0_1.jsonl"
            ),
            "metrics": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "run_001/analysis/structural_saturation_metrics_v0_1.json"
            ),
            "generated_report": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "run_001/analysis/structural_saturation_report_v0_1.md"
            ),
            "exposure_ledger": (
                "data_construction/manifests/question_exposure_ledger_v0_1.json"
            ),
            "run_manifest": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "run_001/run_manifest.json"
            ),
            "partition_sensitivity_tool": (
                "data_construction/tools/"
                "audit_ai_question_structure_partition_sensitivity.py"
            ),
            "partition_sensitivity_metrics": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "run_001/analysis/partition_sensitivity_metrics_v0_1.json"
            ),
            "interpretive_addendum": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "run_001/analysis/interpretive_addendum_v0_1.md"
            ),
        }
        scale_artifacts = scale.get("artifacts", {})
        if not isinstance(scale_artifacts, dict) or set(scale_artifacts) != set(
            expected_scale_artifacts
        ):
            errors.append("AI scale-exploration artifact inventory mismatch")
            scale_artifacts = scale_artifacts if isinstance(scale_artifacts, dict) else {}
        for label, expected_path in expected_scale_artifacts.items():
            reference = scale_artifacts.get(label)
            path = Path(expected_path)
            if not isinstance(reference, dict) or reference.get("path") != expected_path:
                errors.append(f"AI scale-exploration state lacks artifact {label}")
            elif not path.is_file():
                errors.append(f"AI scale-exploration artifact is missing: {label}")
            elif reference.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append(f"AI scale-exploration artifact hash mismatch: {label}")
else:
    errors.append("project_state has an unsupported current scientific decision")

draft_status = environment.get("draft_2020_12_validation", {}).get("status")
draft_contract = environment.get("draft_2020_12_validation", {})
if draft_status == "passed_in_ephemeral_exact_pin_environment":
    expected_result = {
        "schemas_checked": 8,
        "vocabularies_checked": 3,
        "errors": 0,
        "warnings": 0,
    }
    if draft_contract.get("ephemeral_validation_result") != expected_result:
        errors.append("ephemeral Draft 2020-12 result summary mismatch")
    if draft_contract.get("project_local_environment_status") != "not_reconstructed":
        errors.append("ephemeral validation status disagrees with project-local environment status")
    if "PROJECT_LOCAL_PINNED_ENVIRONMENT_NOT_RECONSTRUCTED" not in state_gates:
        errors.append("missing project-local pinned environment gate")
elif draft_status == "complete_in_project_local_pinned_environment":
    if draft_contract.get("project_local_environment_status") != "reconstructed":
        errors.append("project-local full validation lacks reconstructed environment status")
    expected_result = {
        "schemas_checked": 11,
        "vocabularies_checked": 3,
        "errors": 0,
        "warnings": 0,
    }
    if draft_contract.get("project_local_validation_result") != expected_result:
        errors.append("project-local Draft 2020-12 result summary mismatch")
else:
    if "DRAFT_2020_12_FULL_VALIDATION_NOT_RUN_IN_PINNED_ENVIRONMENT" not in state_gates:
        errors.append("unvalidated Draft 2020-12 state is absent from blocked_gates")

if errors:
    print(" | ".join(errors))
    raise SystemExit(1)
print(
    "official_source=verified;"
    f"historical_shape={historical_shape};"
    f"historical_complete={str(history_complete).lower()};"
    f"split_shape={split_shape};"
    f"split_release_eligible={str(split.get('release_eligible')).lower()}"
)
PY
    )
    contract_rc=$?
    if [ "$contract_rc" -eq 0 ]; then
        pass_check "STATE_AND_MANIFEST_CONTRACT: $contract_output"
    else
        fail_check "STATE_AND_MANIFEST_CONTRACT_FAILED: $contract_output"
    fi

    declared_gates=$("$PYTHON_BIN" -B - <<'PY'
import json
from pathlib import Path
state = json.loads(Path("state/project_state.json").read_text(encoding="utf-8"))
print(" | ".join(str(item) for item in state.get("blocked_gates", [])))
PY
    )
    declared_gates_rc=$?
    if [ "$declared_gates_rc" -ne 0 ]; then
        fail_check 'DECLARED_BLOCKED_GATES_UNREADABLE'
    elif [ -n "$declared_gates" ]; then
        block_check "DECLARED_PROJECT_GATES: $declared_gates"
    else
        pass_check 'DECLARED_PROJECT_GATES: none'
    fi

    dependency_output=$("$PYTHON_BIN" -B - <<'PY'
import importlib.metadata
import json
import re
from pathlib import Path

state = json.loads(Path("state/project_state.json").read_text(encoding="utf-8"))
expected = state["environment_contract"]["dependency_contract"]["pinned_packages"]
parsed = {}
contract_errors = []
for number, raw in enumerate(Path("requirements.txt").read_text(encoding="utf-8").splitlines(), 1):
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s]+)", line)
    if not match:
        contract_errors.append(f"requirements.txt:{number} is not an exact pin")
        continue
    name, version = match.groups()
    canonical = name.lower().replace("_", "-").replace(".", "-")
    if canonical in parsed:
        contract_errors.append(f"duplicate requirement {canonical}")
    parsed[canonical] = version
expected = {name.lower().replace("_", "-").replace(".", "-"): version for name, version in expected.items()}
if parsed != expected:
    contract_errors.append(f"requirements/state pin mismatch: requirements={parsed}, state={expected}")
if contract_errors:
    print(" | ".join(contract_errors))
    raise SystemExit(1)

mismatches = []
for name, expected_version in sorted(expected.items()):
    try:
        actual = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        mismatches.append(f"{name}: missing (expected {expected_version})")
        continue
    if actual != expected_version:
        mismatches.append(f"{name}: {actual} (expected {expected_version})")
if mismatches:
    print(" | ".join(mismatches))
    raise SystemExit(2)
print("all exact pins installed")
PY
    )
    dependency_rc=$?
    case "$dependency_rc" in
        0)
            pass_check "PINNED_DEPENDENCY_VERSIONS: $dependency_output"
            if "$PYTHON_BIN" -B -m pip check >/dev/null 2>&1; then
                pass_check 'PIP_DEPENDENCY_COMPATIBILITY: pip check passed'
            else
                fail_check 'PIP_DEPENDENCY_COMPATIBILITY_FAILED'
            fi
            ;;
        1)
            fail_check "DEPENDENCY_CONTRACT_INVALID: $dependency_output"
            ;;
        *)
            block_check "PINNED_DEPENDENCY_ENVIRONMENT_MISMATCH: $dependency_output"
            ;;
    esac

    schema_output=$("$PYTHON_BIN" -B data_construction/tools/check_schema_bundle.py 2>&1)
    schema_rc=$?
    printf '[INFO] SCHEMA_BUNDLE_CHECK_OUTPUT: %s\n' "$schema_output"
    if [ "$schema_rc" -eq 0 ]; then
        pass_check 'SCHEMA_BUNDLE_STRUCTURE: 11 schemas and 3 vocabularies passed JSON/local-ref checks'
    else
        fail_check 'SCHEMA_BUNDLE_STRUCTURE_FAILED'
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        full_schema_output=$("$PYTHON_BIN" -B data_construction/tools/check_schema_bundle.py --require-jsonschema 2>&1)
        full_schema_rc=$?
        printf '[INFO] DRAFT_2020_12_CHECK_OUTPUT: %s\n' "$full_schema_output"
        if [ "$full_schema_rc" -eq 0 ]; then
            pass_check 'DRAFT_2020_12_FULL_VALIDATION: passed in pinned environment'
        else
            fail_check 'DRAFT_2020_12_FULL_VALIDATION_FAILED_IN_PINNED_ENVIRONMENT'
        fi
    else
        block_check 'PROJECT_LOCAL_PINNED_ENVIRONMENT_NOT_RECONSTRUCTED: recorded ephemeral exact-pin validation was not reproduced by the selected runtime'
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        question_structure_output=$(
            "$PYTHON_BIN" -B \
                data_construction/tools/validate_question_structure_annotations.py \
                --batch-id phase_a1_batch_01 \
                --packet-only 2>&1
        )
        question_structure_rc=$?
        printf '[INFO] QUESTION_ONLY_PHASE_A0_CHECK_OUTPUT: %s\n' "$question_structure_output"
        if [ "$question_structure_rc" -eq 0 ]; then
            pass_check 'QUESTION_ONLY_PHASE_A0_PACKET: 30-view projection and 10-question packet passed exact render/hash/order/provenance validation'
        else
            fail_check 'QUESTION_ONLY_PHASE_A0_PACKET_FAILED'
        fi
    else
        block_check 'QUESTION_ONLY_PHASE_A0_PACKET_VALIDATION_NOT_RUN: exact pinned dependencies are unavailable in the selected runtime'
    fi

    granularity_output=$("$PYTHON_BIN" -B - <<'PY' 2>&1
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

project_root = Path.cwd().resolve()
tool_dir = project_root / "data_construction/tools"
sys.path.insert(0, str(tool_dir))

import compare_operator_granularity as comparator


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


questions = project_root / "data_construction/pilot/questions.jsonl"
plan = project_root / "data_construction/pilot/granularity_representation_plan_v0_1.json"
views = project_root / "data_construction/pilot/granularity_input_views.jsonl"
view_manifest = project_root / "data_construction/pilot/granularity_input_views_manifest_v0_1.json"
representations = project_root / "data_construction/pilot/granularity_representations.jsonl"
committed_checks = project_root / "data_construction/pilot/granularity_deterministic_checks.jsonl"
committed_metrics_path = project_root / "data_construction/reports/operator_granularity_metrics_v0_1.json"
schema = project_root / "data_construction/schemas/operator_granularity_pilot_v0_1.json"
packet_manifests = [
    project_root / f"data_construction/pilot/review_packets/operator_granularity_{granularity}_v0_1_manifest.json"
    for granularity in ("coarse", "medium", "fine")
]

with tempfile.TemporaryDirectory(prefix="granularity-preflight-") as temporary_directory:
    temporary_root = Path(temporary_directory)
    reproduced_checks = temporary_root / "checks.jsonl"
    validator = subprocess.run(
        [
            sys.executable,
            "-B",
            str(tool_dir / "validate_operator_granularity.py"),
            str(representations),
            "--checks-output",
            str(reproduced_checks),
        ],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if validator.returncode != 0:
        raise SystemExit(
            f"validator rc={validator.returncode}; stdout={validator.stdout.strip()}; "
            f"stderr={validator.stderr.strip()}"
        )
    reproduced_records = jsonl(reproduced_checks)
    if (
        len(reproduced_records) != 90
        or any(record.get("status") != "pass" for record in reproduced_records)
        or any(record.get("errors") != [] for record in reproduced_records)
        or any(record.get("warnings") != [] for record in reproduced_records)
    ):
        raise SystemExit("live validator did not reproduce 90 warning-free pass checks")

    reproduced_metrics_path = temporary_root / "metrics.json"
    comparison = subprocess.run(
        [
            sys.executable,
            "-B",
            str(tool_dir / "compare_operator_granularity.py"),
            str(representations),
            "--questions",
            str(questions),
            "--input-views",
            str(views),
            "--input-views-manifest",
            str(view_manifest),
            "--validation-checks",
            str(committed_checks),
            "--json-output",
            str(reproduced_metrics_path),
        ],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if comparison.returncode != 2:
        raise SystemExit(
            f"human-pending comparator expected rc=2, observed {comparison.returncode}; "
            f"stdout={comparison.stdout.strip()}; stderr={comparison.stderr.strip()}"
        )
    reproduced_metrics = json.loads(reproduced_metrics_path.read_text(encoding="utf-8"))

committed_metrics = json.loads(committed_metrics_path.read_text(encoding="utf-8"))
expected_status = {
    "study_status": "structural_integrity_complete_human_calibration_pending",
    "integrity_complete": True,
    "human_calibration_complete": False,
    "evidence_complete": False,
    "semantic_confirmation_complete": False,
    "selection_ready": False,
    "provisional_decision": "UNDECIDED_NEEDS_ANNOTATION_EVIDENCE",
    "question_count": 30,
}
for label, summary in (("committed", committed_metrics), ("reproduced", reproduced_metrics)):
    for key, expected in expected_status.items():
        if summary.get(key) != expected:
            raise SystemExit(f"{label} metrics mismatch for {key}")
    if summary.get("metrics") != committed_metrics.get("metrics"):
        raise SystemExit(f"{label} metrics table differs from the committed study result")
    if summary.get("reviewer_authentication_status") != "procedural_not_machine_verifiable":
        raise SystemExit(f"{label} metrics overstates reviewer authentication")

for granularity in ("coarse", "medium", "fine"):
    metric = committed_metrics["metrics"].get(granularity, {})
    if (
        metric.get("representation_count") != 30
        or metric.get("valid_topology_observation_count") != 30
        or metric.get("human_review_record_count") != 0
        or metric.get("annotation_disagreement_observation_count") != 0
        or metric.get("annotation_disagreement_rate") is not None
    ):
        raise SystemExit(f"{granularity} metrics do not preserve the 30/0/N/A evidence boundary")

live_bindings = {
    "questions_artifact_sha256": questions,
    "input_views_artifact_sha256": views,
    "input_views_manifest_artifact_sha256": view_manifest,
    "representations_artifact_sha256": representations,
    "validation_checks_artifact_sha256": committed_checks,
    "operator_granularity_schema_artifact_sha256": schema,
}
provenance = committed_metrics.get("provenance", {})
for field, path in live_bindings.items():
    if provenance.get(field) != sha256_file(path):
        raise SystemExit(f"committed metrics live hash mismatch for {field}")
if (
    provenance.get("validation_checks_record_count") != 90
    or provenance.get("validation_checks_verified") is not True
    or provenance.get("human_review_artifacts") != []
    or provenance.get("review_packet_artifacts") != []
):
    raise SystemExit("committed metrics provenance overstates review evidence or checks")

records = jsonl(representations)
input_views = jsonl(views)
packet_errors, payload_hashes, packet_provenance = comparator.validate_review_packet_manifests(
    packet_manifests,
    records,
    input_views,
    {
        "questions": questions,
        "input_views": views,
        "input_views_manifest": view_manifest,
        "representations": representations,
        "validation_checks": committed_checks,
    },
    project_root,
)
if packet_errors:
    raise SystemExit("review packet validation failed: " + " | ".join(packet_errors))
if set(payload_hashes) != {"coarse", "medium", "fine"} or len(packet_provenance) != 3:
    raise SystemExit("review packets do not cover exactly three granularities")

state = json.loads((project_root / "state/project_state.json").read_text(encoding="utf-8"))
pilot = state.get("artifact_status", {}).get("operator_granularity_pilot", {})
state_artifacts = pilot.get("artifacts", {})
expected_state_artifacts = {
    "representation_plan": plan,
    "input_views": views,
    "input_views_manifest": view_manifest,
    "representations": representations,
    "deterministic_checks": committed_checks,
    "metrics": committed_metrics_path,
}
for label, path in expected_state_artifacts.items():
    reference = state_artifacts.get(label)
    if not isinstance(reference, dict) or reference.get("path") != path.relative_to(project_root).as_posix():
        raise SystemExit(f"project state lacks canonical pilot artifact {label}")
    if reference.get("sha256") != sha256_file(path):
        raise SystemExit(f"project state hash mismatch for pilot artifact {label}")

state_packets = pilot.get("review_packets", {})
for reference in packet_provenance:
    granularity = reference["granularity"]
    expected_reference = {
        "html_sha256": reference["packet_artifact_sha256"],
        "manifest_sha256": reference["manifest_artifact_sha256"],
        "payload_sha256": reference["packet_payload_sha256"],
    }
    if state_packets.get(granularity) != expected_reference:
        raise SystemExit(f"project state hash mismatch for {granularity} review packet")

print(
    "questions=30;representations=90;checks=90_pass_0_error_0_warning;"
    "packets=3;human_reviews=0;disagreement=N/A;selection_ready=false"
)
PY
    )
    granularity_rc=$?
    if [ "$granularity_rc" -eq 0 ]; then
        pass_check "OPERATOR_GRANULARITY_PILOT: $granularity_output"
    else
        fail_check "OPERATOR_GRANULARITY_PILOT_FAILED: $granularity_output"
    fi

    ai_diagnostic_output=$("$PYTHON_BIN" -B - <<'PY' 2>&1
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("data_construction/tools").resolve()))
from _common import iter_json_records, jsonl_file_bytes, read_json
from run_ai_question_structure_diagnostic import (
    REVIEWER_SLOTS,
    build_alignment_packet,
    build_metrics,
    render_report,
    validate_alignment_records,
    validate_annotation_records,
    validate_contract,
    validate_stage1_records,
    validate_topology_records,
)

base = Path("data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001")
stage1_paths = [
    base / "reviewer_01/stage1.jsonl",
    base / "reviewer_02/stage1.jsonl",
]
stage1_check_paths = [
    base / "reviewer_01/stage1_checks.jsonl",
    base / "reviewer_02/stage1_checks.jsonl",
]
annotation_paths = [
    base / "reviewer_01/annotations.jsonl",
    base / "reviewer_02/annotations.jsonl",
]
annotation_check_paths = [
    base / "reviewer_01/annotation_checks.jsonl",
    base / "reviewer_02/annotation_checks.jsonl",
]
packet_path = base / "alignment/blinded_pairs.jsonl"
side_map_path = base / "alignment/side_map.jsonl"
alignment_path = base / "alignment/records.jsonl"
alignment_checks_path = base / "alignment/checks.jsonl"
topology_path = base / "independent_topology/records.jsonl"
topology_checks_path = base / "independent_topology/checks.jsonl"
metrics_path = base / "analysis/metrics_v0_1.json"
report_path = base / "analysis/final_report_v0_1.md"

validate_contract()
all_errors = []
stage1_records = []
annotation_records = []
for index, slot in enumerate(REVIEWER_SLOTS):
    records, checks, errors = validate_stage1_records(stage1_paths[index], slot)
    stage1_records.append(records)
    all_errors.extend(errors)
    if jsonl_file_bytes(checks) != stage1_check_paths[index].read_bytes():
        all_errors.append(f"{slot} stage-1 check artifact differs from live validation")
    records, checks, errors = validate_annotation_records(
        annotation_paths[index], stage1_paths[index], slot
    )
    annotation_records.append(records)
    all_errors.extend(errors)
    if jsonl_file_bytes(checks) != annotation_check_paths[index].read_bytes():
        all_errors.append(f"{slot} annotation check artifact differs from live validation")

expected_packet, expected_side_map = build_alignment_packet(
    annotation_records[0], annotation_records[1]
)
if jsonl_file_bytes(expected_packet) != packet_path.read_bytes():
    all_errors.append("blinded alignment packet differs from deterministic reconstruction")
if jsonl_file_bytes(expected_side_map) != side_map_path.read_bytes():
    all_errors.append("alignment side map differs from deterministic reconstruction")

alignments, alignment_checks, errors = validate_alignment_records(
    alignment_path, packet_path
)
all_errors.extend(errors)
if jsonl_file_bytes(alignment_checks) != alignment_checks_path.read_bytes():
    all_errors.append("alignment checks differ from live validation")
topologies, topology_checks, errors = validate_topology_records(topology_path)
all_errors.extend(errors)
if jsonl_file_bytes(topology_checks) != topology_checks_path.read_bytes():
    all_errors.append("independent topology checks differ from live validation")

live_metrics = build_metrics(
    annotation_records[0],
    annotation_records[1],
    expected_packet,
    alignments,
    topologies,
)
if live_metrics != read_json(metrics_path):
    all_errors.append("AI diagnostic metrics differ from deterministic reconstruction")
if render_report(live_metrics).encode("utf-8") != report_path.read_bytes():
    all_errors.append("AI diagnostic report differs from deterministic reconstruction")
if all_errors:
    print(" | ".join(all_errors))
    raise SystemExit(1)
print(
    "stage1=60_pass;structured=60_pass;alignment=30_pass;"
    "independent_topology=20_pass;status=NOT_EVALUATED_AI_SUBSTITUTE"
)
PY
    )
    ai_diagnostic_rc=$?
    if [ "$ai_diagnostic_rc" -eq 0 ]; then
        pass_check "AI_QUESTION_STRUCTURE_PIPELINE_DIAGNOSTIC: $ai_diagnostic_output"
    else
        fail_check "AI_QUESTION_STRUCTURE_PIPELINE_DIAGNOSTIC_FAILED: $ai_diagnostic_output"
    fi

    ai_scale_output=$("$PYTHON_BIN" -B - <<'PY' 2>&1
import sys
from pathlib import Path

sys.path.insert(0, str(Path("data_construction/tools").resolve()))
from _common import iter_json_records, json_file_bytes, jsonl_file_bytes
import run_ai_question_structure_scale_exploration as analyzer

base = Path("data_construction/exploration/ai_question_structure_scale_v0_1")
run = base / "run_001"
records_path = run / "records.jsonl"
checks_path = run / "checks.jsonl"
signatures_path = run / "analysis/derived_signatures_v0_1.jsonl"
metrics_path = run / "analysis/structural_saturation_metrics_v0_1.json"
report_path = run / "analysis/structural_saturation_report_v0_1.md"
exposure_path = Path("data_construction/manifests/question_exposure_ledger_v0_1.json")
manifest_path = run / "run_manifest.json"

plan, views, pool = analyzer.validate_contract()
records = []
partition_counts = {}
for partition in plan["partitions"]:
    part_path = Path(partition["output"])
    part_records = list(iter_json_records(part_path))
    expected_count = partition["expected_record_count"]
    expected_ids = plan["question_ids"][
        partition["committed_order_start"] - 1 : partition["committed_order_end"]
    ]
    if len(part_records) != expected_count:
        raise SystemExit(
            f"{partition['producer_partition']} count mismatch: "
            f"expected {expected_count}, observed {len(part_records)}"
        )
    if [record.get("question_id") for record in part_records] != expected_ids:
        raise SystemExit(f"{partition['producer_partition']} committed-order mismatch")
    if any(
        record.get("producer_partition") != partition["producer_partition"]
        for record in part_records
    ):
        raise SystemExit(f"{partition['producer_partition']} producer binding mismatch")
    partition_counts[partition["producer_partition"]] = len(part_records)
    records.extend(part_records)

checks, errors = analyzer.validate_records(records, views)
if errors:
    raise SystemExit("live N=100 validation failed: " + " | ".join(errors))
if len(checks) != 100 or any(check.get("status") != "pass" for check in checks):
    raise SystemExit("live N=100 checks are not exactly 100 passing records")
derived = [analyzer.signature_bundle(record) for record in records]
metrics = analyzer.build_metrics(records, derived)
exposure = analyzer.build_exposure_ledger(plan, pool, records)

expected_payloads = {
    "records": (jsonl_file_bytes(records), records_path),
    "checks": (jsonl_file_bytes(checks), checks_path),
    "derived signatures": (jsonl_file_bytes(derived), signatures_path),
    "metrics": (json_file_bytes(metrics), metrics_path),
    "report": (analyzer.render_report(metrics).encode("utf-8"), report_path),
    "exposure ledger": (json_file_bytes(exposure), exposure_path),
}
for label, (reconstructed, committed_path) in expected_payloads.items():
    if reconstructed != committed_path.read_bytes():
        raise SystemExit(f"{label} differs from frozen-analyzer reconstruction")

manifest = analyzer.build_run_manifest(
    plan=plan,
    records_path=records_path,
    checks_path=checks_path,
    signatures_path=signatures_path,
    metrics_path=metrics_path,
    report_path=report_path,
    exposure_path=exposure_path,
)
if json_file_bytes(manifest) != manifest_path.read_bytes():
    raise SystemExit("run manifest differs from frozen-analyzer reconstruction")

contracted = metrics["family_metrics"]["contracted_semantic_dag"]
validation = metrics["validation"]
decision = metrics["n100_precommitted_decision"]
last_blocks = contracted["block_novelty_committed_order"][-2:]
if (
    validation != {
        "valid_record_count": 100,
        "invalid_record_count": 0,
        "human_evidence_count": 0,
        "gold_claimed": False,
        "semantic_correctness_evaluated": False,
        "grounding_or_execution_evaluated": False,
    }
    or contracted["observed_family_count"] != 17
    or contracted["singleton_question_mass"] != 0.09
    or contracted["new_70_transfer"]["transfer_rate"] != 0.7142857142857143
    or [block["question_novelty_rate"] for block in last_blocks] != [0.3, 0.0]
    or metrics["uncertainty"]["question_count"] != 29
    or metrics["provisional_role_escape_hatch"]["other_question_count"] != 0
    or decision["recurring_new_contracted_family_count"] != 5
    or decision["decision"] != "EXPAND_UNCHANGED_TO_N300"
    or exposure["ai_question_structure_exploration"]["count"] != 100
    or exposure["unexposed_unallocated_reserve"]["count"] != 3266
):
    raise SystemExit("live N=100 core scale metrics or evidence boundary mismatch")

print(
    "records=100;checks=100_pass;signatures=100;families=17;"
    "singleton_mass=0.09;new70_transfer=0.7142857142857143;"
    "final_novelty=0.3,0.0;uncertain=29;OTHER=0;"
    "decision=EXPAND_UNCHANGED_TO_N300;"
    f"partitions={partition_counts}"
)
PY
    )
    ai_scale_rc=$?
    if [ "$ai_scale_rc" -eq 0 ]; then
        pass_check "AI_QUESTION_STRUCTURE_SCALE_EXPLORATION_LIVE: $ai_scale_output"
    else
        fail_check "AI_QUESTION_STRUCTURE_SCALE_EXPLORATION_LIVE_FAILED: $ai_scale_output"
    fi

    sensitivity_cli_output=$("$PYTHON_BIN" -B \
        data_construction/tools/audit_ai_question_structure_partition_sensitivity.py \
        2>&1)
    sensitivity_cli_rc=$?
    if [ "$sensitivity_cli_rc" -eq 0 ]; then
        pass_check "AI_SCALE_PARTITION_SENSITIVITY_CLI: $sensitivity_cli_output"
    else
        fail_check "AI_SCALE_PARTITION_SENSITIVITY_CLI_FAILED: $sensitivity_cli_output"
    fi

    sensitivity_live_output=$("$PYTHON_BIN" -B - <<'PY' 2>&1
import sys
from pathlib import Path

sys.path.insert(0, str(Path("data_construction/tools").resolve()))
from _common import iter_json_records, json_file_bytes, read_json
import audit_ai_question_structure_partition_sensitivity as audit
import run_ai_question_structure_scale_exploration as primary

base = Path("data_construction/exploration/ai_question_structure_scale_v0_1/run_001")
records_path = base / "records.jsonl"
primary_metrics_path = base / "analysis/structural_saturation_metrics_v0_1.json"
metrics_path = base / "analysis/partition_sensitivity_metrics_v0_1.json"
addendum_path = base / "analysis/interpretive_addendum_v0_1.md"
records = list(iter_json_records(records_path))
primary_metrics = read_json(primary_metrics_path)
source_bindings = {
    "records": audit._input_binding(records_path, record_count=len(records)),
    "primary_metrics": audit._input_binding(primary_metrics_path),
    "primary_canonicalizer": audit._input_binding(Path(primary.__file__)),
    "audit_implementation": audit._input_binding(Path(audit.__file__)),
}
metrics = audit.build_metrics(
    records,
    primary_metrics,
    prefix_count=30,
    source_bindings=source_bindings,
)
if json_file_bytes(metrics) != metrics_path.read_bytes():
    raise SystemExit("partition-sensitivity metrics differ from function reconstruction")
if audit.render_addendum(metrics).encode("utf-8") != addendum_path.read_bytes():
    raise SystemExit("partition-sensitivity addendum differs from function reconstruction")

recurring = metrics["recurring_new_contracted_family_partition_sensitivity"]
profile = metrics["raw_vs_transitive_reduced_graph_profile"]
raw = profile["raw_declared_dependencies"]
reduced = profile["transitive_reduced_dependencies"]
decision = metrics["primary_decision_preservation"]
if (
    recurring["recurring_new_contracted_family_count"] != 5
    or recurring["cross_partition_recurring_new_contracted_family_count"] != 0
    or recurring["all_recurring_new_contracted_families_are_partition_local"] is not True
    or raw["branch_question_count"] != 5
    or reduced["branch_question_count"] != 0
    or raw["join_question_count"] != 6
    or reduced["join_question_count"] != 1
    or decision["precommitted_decision"] != "EXPAND_UNCHANGED_TO_N300"
    or decision["changed_by_post_hoc_audit"] is not False
):
    raise SystemExit("partition-sensitivity core audit values mismatch")
print(
    "recurring_new=5;cross_partition=0;branch_raw_to_reduced=5_to_0;"
    "join_raw_to_reduced=6_to_1;decision_unchanged=true"
)
PY
    )
    sensitivity_live_rc=$?
    if [ "$sensitivity_live_rc" -eq 0 ]; then
        pass_check "AI_SCALE_PARTITION_SENSITIVITY_LIVE: $sensitivity_live_output"
    else
        fail_check "AI_SCALE_PARTITION_SENSITIVITY_LIVE_FAILED: $sensitivity_live_output"
    fi

    ir_reference_output=$("$PYTHON_BIN" -B - <<'PY' 2>&1
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("data_construction/tools").resolve()))
from validate_ir_v0_2_reference import validate_ir_v0_2_reference

result = validate_ir_v0_2_reference(all_graphs=True)
expected_counts = {
    "records": 50,
    "graphs_selected": 50,
    "graphs_validated": 50,
    "preserved_files_verified": 10,
    "nodes": 520,
    "parse_errors": 0,
    "schema_errors": 0,
    "validator_errors": 0,
    "validator_warnings": 455,
    "dead_node_warnings": 455,
}
compact = {
    "status": result.get("status"),
    "counts": result.get("counts"),
    "error_code_counts": result.get("error_code_counts"),
    "warning_code_counts": result.get("warning_code_counts"),
}
print(json.dumps(compact, sort_keys=True))
if (
    result.get("status") != "pass"
    or result.get("counts") != expected_counts
    or result.get("error_code_counts") != {}
    or result.get("warning_code_counts") != {"DEAD_NODE": 455}
    or "preserved_bundle_git_authority" not in result.get("checks", [])
):
    raise SystemExit(1)
PY
    )
    ir_reference_rc=$?
    if [ "$ir_reference_rc" -eq 0 ]; then
        pass_check "IR_V0_2_REFERENCE_VALIDATION: $ir_reference_output"
    else
        fail_check "IR_V0_2_REFERENCE_VALIDATION_FAILED: $ir_reference_output"
    fi

    printf '%s\n' '[INFO] UNIT_TEST_COMMAND: python -B -m unittest discover -s tests -v'
    unit_test_output=$("$PYTHON_BIN" -B -m unittest discover -s tests -v 2>&1)
    unit_test_rc=$?
    printf '%s\n' "$unit_test_output"
    if [ "$unit_test_rc" -eq 0 ]; then
        pass_check 'UNIT_TESTS: passed'
        unit_test_count=$(printf '%s\n' "$unit_test_output" | sed -n 's/^Ran \([0-9][0-9]*\) tests.*$/\1/p' | tail -n 1)
        declared_unit_test_count=$("$PYTHON_BIN" -B -c 'import json; print(json.load(open("state/project_state.json", encoding="utf-8"))["preflight_status"]["unit_tests_passed"])' 2>/dev/null || printf '%s' unknown)
        if [ -n "$unit_test_count" ] && [ "$unit_test_count" = "$declared_unit_test_count" ]; then
            pass_check "UNIT_TEST_COUNT_MATCH: $unit_test_count"
        else
            fail_check "UNIT_TEST_COUNT_MISMATCH: observed=${unit_test_count:-unknown}; declared=$declared_unit_test_count"
        fi
    else
        fail_check 'UNIT_TESTS_FAILED'
    fi
fi

if command -v git >/dev/null 2>&1; then
    git_version=$(git --version 2>/dev/null | sed 's/^git version //')
    if [ "$git_version" = '2.34.1' ]; then
        pass_check 'GIT_VERSION_OBSERVED_BASELINE: 2.34.1'
    else
        warn_check "GIT_VERSION_DIFFERS_FROM_OBSERVED_BASELINE: observed 2.34.1, found $git_version"
    fi

    if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        git_root=$(git -C "$PROJECT_ROOT" rev-parse --show-toplevel 2>/dev/null || printf '%s' unknown)
        if [ "$git_root" = "$PROJECT_ROOT" ]; then
            pass_check 'GIT_ROOT: project root'
        else
            block_check 'GIT_ROOT_MISMATCH: script project root is not the Git top level'
        fi

        branch=$(git -C "$PROJECT_ROOT" symbolic-ref --quiet --short HEAD 2>/dev/null || printf '%s' DETACHED_HEAD)
        head=$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || printf '%s' unknown)
        printf '[INFO] GIT_BRANCH: %s\n' "$branch"
        printf '[INFO] GIT_HEAD: %s\n' "$head"

        if [ -n "$PYTHON_BIN" ]; then
            expected_branch=$("$PYTHON_BIN" -B -c 'import json; print(json.load(open("state/project_state.json", encoding="utf-8")).get("active_branch", "unknown"))' 2>/dev/null || printf '%s' unknown)
            expected_head=$("$PYTHON_BIN" -B -c 'import json; print(json.load(open("state/project_state.json", encoding="utf-8")).get("expected_head", "unknown"))' 2>/dev/null || printf '%s' unknown)
            if [ "$branch" = "$expected_branch" ]; then
                pass_check 'EXPECTED_BRANCH_MATCH'
            else
                block_check 'STOP_AND_REPORT_BRANCH_DIVERGENCE: branch differs from handoff'
            fi
            head_relation=$(sh "$SCRIPT_DIR/classify_handoff_head.sh" "$PROJECT_ROOT" "$expected_head" "$head" 2>&1)
            head_relation_rc=$?
            case "$head_relation_rc:$head_relation" in
                0:exact)
                    pass_check 'EXPECTED_HEAD_MATCH'
                    ;;
                0:descendant:*)
                    commits_after_handoff=${head_relation#descendant:}
                    warn_check "EXPECTED_HEAD_BASELINE_ANCESTOR: HEAD is $commits_after_handoff commit(s) after the recorded handoff baseline"
                    ;;
                2:diverged)
                    block_check 'STOP_AND_REPORT_BRANCH_DIVERGENCE: HEAD and handoff baseline are on different histories'
                    ;;
                2:missing-baseline)
                    block_check 'STOP_AND_REPORT_BRANCH_DIVERGENCE: handoff baseline commit is unavailable'
                    ;;
                2:invalid-baseline)
                    block_check 'STOP_AND_REPORT_BRANCH_DIVERGENCE: handoff baseline is not a full lowercase 40-hex commit OID'
                    ;;
                *)
                    fail_check "GIT_HANDOFF_RELATION_CHECK_FAILED: $head_relation"
                    ;;
            esac
        fi

        remotes=$(git -C "$PROJECT_ROOT" remote 2>/dev/null || printf '')
        if [ -n "$remotes" ]; then
            pass_check 'GIT_REMOTE: configured'
            upstream=$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || printf '')
            if [ -n "$upstream" ]; then
                printf '[INFO] GIT_UPSTREAM_TRACKING_REF: %s\n' "$upstream"
                ahead_behind=$(git -C "$PROJECT_ROOT" rev-list --left-right --count "HEAD...$upstream" 2>/dev/null || printf '')
                if [ -n "$ahead_behind" ]; then
                    ahead=$(printf '%s\n' "$ahead_behind" | awk '{print $1}')
                    behind=$(printf '%s\n' "$ahead_behind" | awk '{print $2}')
                    if [ "$ahead" -gt 0 ] && [ "$behind" -gt 0 ]; then
                        block_check 'STOP_AND_REPORT_BRANCH_DIVERGENCE: tracking refs diverged'
                    elif [ "$ahead" -gt 0 ]; then
                        block_check "LOCAL_COMMIT_NOT_PUSHED: $ahead commit(s) ahead of local tracking ref"
                    elif [ "$behind" -gt 0 ]; then
                        block_check "LOCAL_HEAD_BEHIND_TRACKING_REF: $behind commit(s)"
                    else
                        pass_check 'GIT_TRACKING_REF_COMPARISON: no known ahead/behind commits'
                    fi
                    warn_check 'GIT_TRACKING_REF_FRESHNESS: comparison uses local refs; fetch separately when authorized'
                else
                    fail_check 'GIT_TRACKING_REF_COMPARISON_UNAVAILABLE'
                fi
            else
                block_check 'GIT_UPSTREAM_TRACKING_REF_NOT_CONFIGURED'
            fi
        else
            block_check 'REMOTE_NOT_CONFIGURED'
        fi

        worktree_state=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null || printf '%s' STATUS_UNAVAILABLE)
        if [ -z "$worktree_state" ]; then
            pass_check 'GIT_WORKTREE: clean'
        elif [ "$worktree_state" = 'STATUS_UNAVAILABLE' ]; then
            fail_check 'GIT_WORKTREE_STATUS_UNAVAILABLE'
        else
            block_check 'STOP_AND_REPORT_LOCAL_CHANGES'
        fi

        stash_entries=$(git -C "$PROJECT_ROOT" stash list 2>/dev/null || printf '')
        if [ -z "$stash_entries" ]; then
            pass_check 'GIT_STASH: empty'
        else
            warn_check 'LOCAL_STASH_PRESENT: stash is not portable and cannot be a handoff dependency'
        fi

        tracked_secret=$(git -C "$PROJECT_ROOT" ls-files 2>/dev/null | grep -E '(^|/)(\.env|\.env\.local|id_rsa|id_ed25519)$' || printf '')
        if [ -z "$tracked_secret" ]; then
            pass_check 'TRACKED_SECRET_FILENAME_CHECK: none detected'
        else
            fail_check 'TRACKED_SECRET_FILENAME_DETECTED'
        fi
    else
        block_check 'GIT_ROOT: NOT_A_GIT_REPOSITORY'
        block_check 'REMOTE_NOT_CONFIGURED'
        warn_check 'GIT_BRANCH: NOT_A_GIT_REPOSITORY'
        warn_check 'GIT_HEAD: unknown'
    fi
else
    fail_check 'GIT_NOT_FOUND'
fi

missing_historical=''
for historical_file in \
    data_analysis/week1_sample_100.jsonl \
    evaluation/week2_eval_ids.json \
    evaluation/week3_engineering_dev_ids.json \
    evaluation/week3_locked_eval_ids.json \
    evaluation/week3_split_manifest.json
do
    if [ ! -f "$historical_file" ]; then
        missing_historical="$missing_historical $historical_file"
    fi
done
if [ -z "$missing_historical" ]; then
    pass_check 'HISTORICAL_ARTIFACT_PATHS: all five present; provenance/content checked separately'
else
    block_check "HISTORICAL_ARTIFACTS_MISSING:$missing_historical"
fi

printf '%s\n' '[INFO] MODEL_IDENTITY: deterministic validation requires no model runtime; pilot representations are llm_proposed with model_id=codex_gpt-5, while exact revision and raw model output were not exposed by the interface'

local_secret_present=0
for secret_file in .env .env.local
do
    if [ -f "$secret_file" ]; then
        warn_check "MACHINE_LOCAL_SECRET_FILE_PRESENT: $secret_file (must remain untracked)"
        local_secret_present=1
    fi
done
if [ "$local_secret_present" -eq 0 ]; then
    pass_check 'MACHINE_LOCAL_SECRET_FILES: none present at project root'
fi

portable_path_hit=$(grep -E '/home/[^[:space:]]+|[A-Za-z]:\\\\' \
    AGENTS.md HANDOFF_CURRENT.md ENVIRONMENT.md state/project_state.json \
    reports/cross_device_repo_audit.md 2>/dev/null || printf '')
if [ -z "$portable_path_hit" ]; then
    pass_check 'PORTABLE_PATH_CHECK: no machine-specific project path detected'
else
    fail_check 'PORTABLE_PATH_CHECK: machine-specific project path detected'
fi

printf 'Summary: pass=%s warn=%s block=%s fail=%s\n' \
    "$pass_count" "$warn_count" "$block_count" "$fail_count"

if [ "$fail_count" -gt 0 ]; then
    printf '%s\n' 'RESULT=CHECK_FAILED'
    exit 1
fi

if [ "$block_count" -gt 0 ]; then
    printf '%s\n' 'RESULT=NOT_READY'
    exit 2
fi

printf '%s\n' 'RESULT=READY'
exit 0
