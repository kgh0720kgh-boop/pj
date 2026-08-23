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
    data_construction/pilot/question_only_semantic_views_v0_1.jsonl \
    data_construction/pilot/question_only_semantic_views_manifest_v0_1.json \
    data_construction/pilot/question_structure_review_packets/question_structure_calibration_batch_1_v0_1.html \
    data_construction/pilot/question_structure_review_packets/question_structure_calibration_batch_1_v0_1_manifest.json \
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
    Path("data_construction/pilot/question_only_semantic_views_manifest_v0_1.json"),
    Path("data_construction/pilot/question_structure_review_packets/question_structure_calibration_batch_1_v0_1_manifest.json"),
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
