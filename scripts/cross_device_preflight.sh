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
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/candidate_backbone_library_plan_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/candidate_backbone_family_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/representative_selection_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/environment_realization_outcome_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/backbone_adequacy_assessment_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/environment_realization_outcome_schema_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/environment_realization_outcome_v0_1_to_v0_2_migration.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/open_operator_realization_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/representative_environment_realization_plan_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/representative_environment_view_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_normalization_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_normalization_plan_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_crossed_author_sensitivity_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_crossed_author_sensitivity_plan_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_normalization_schema_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_crossed_comparison_schema_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_normalization_plan_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_reauthor_normalization_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_reauthor_comparison_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_reauthor_plan_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_instrument_feedback_schema_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_instrument_normalization_schema_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_instrument_comparison_schema_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_instrument_plan_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_design_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_plan_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/prompts/narrowed_grounding_v0_1.md \
    data_construction/tools/freeze_narrowed_grounding_plan_v0_1.py \
    tests/test_narrowed_grounding_plan_v0_1.py \
    data_construction/reports/research_sequencing_decision_v0_10.md \
    data_construction/tools/narrowed_grounding_runtime_v0_1.py \
    tests/test_narrowed_grounding_runtime_v0_1.py \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_packet_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_raw_schema_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_runtime_freeze_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/prompts/narrowed_grounding_author_guide_v0_1.md \
    data_construction/reports/research_sequencing_decision_v0_11.md \
    data_construction/reports/research_sequencing_decision_v0_12.md \
    state/narrowed_grounding_author_dispatch_v0_1.json \
    tests/test_narrowed_grounding_collection_v0_1.py \
    data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/candidate_backbone_families_v0_1.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/representative_selection_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/checks.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/report_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/run_manifest.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/prompts/backbone_adequacy_assessment_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/prompts/open_operator_realization_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/prompts/operator_equivalence_crossed_author_sensitivity_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/prompts/operator_equivalence_targeted_reauthor_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/prompts/operator_equivalence_targeted_instrument_v0_2.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/inputs/environment_views.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/inputs/environment_views_manifest_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/inputs/producer_routing_manifest_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/stage_e1/backbone_adequacy_assessments.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/stage_e1/assessment_bindings_for_e2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/stage_e2/open_operator_realizations.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/outcomes.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/checks.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/metrics_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/report_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/interpretive_addendum_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/environment_exposure_ledger_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/run_manifest.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/structural_projections.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/normalized_candidates.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/question_normalized_sets.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/family_normalized_sets.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/checks.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/metrics_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/report_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/run_manifest.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/authoring_packets/crossed_author_01.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/authoring_packets/crossed_author_02.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/author_outputs/crossed_author_01.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/author_outputs/crossed_author_02.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/combined_author_records.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/normalized_candidates.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/question_comparisons.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/checks.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/metrics_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/report_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/run_manifest.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/normalized_candidates.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/original_question_sets.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/original_family_sets.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/crossed_question_comparisons.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/checks.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/metrics_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/report_v0_2.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/run_manifest.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/authoring_packets/targeted_author_01.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/authoring_packets/targeted_author_02.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/author_outputs/targeted_author_01.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/author_outputs/targeted_author_02.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/combined_author_records.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/normalized_candidates.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/question_comparisons.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/checks.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/metrics_v0_1.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/report_v0_1.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/run_manifest.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/authoring_packets/instrument_author_01.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/authoring_packets/instrument_author_02.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/draft_outputs/instrument_author_01.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/draft_outputs/instrument_author_02.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/feedback_round_01/instrument_author_01.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/feedback_round_01/instrument_author_02.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/final_outputs/instrument_author_01.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/final_outputs/instrument_author_02.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/combined_draft_records.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/draft_normalized_candidates.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/combined_final_records.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/final_normalized_candidates.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/question_comparisons.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/checks.jsonl \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/metrics_v0_2.json \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/report_v0_2.md \
    data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/run_manifest.json \
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
    data_construction/reports/research_sequencing_decision_v0_3.md \
    data_construction/reports/research_sequencing_decision_v0_4.md \
    data_construction/reports/research_sequencing_decision_v0_5.md \
    data_construction/reports/research_sequencing_decision_v0_6.md \
    data_construction/reports/research_sequencing_decision_v0_7.md \
    data_construction/reports/research_sequencing_decision_v0_8.md \
    data_construction/reports/research_sequencing_decision_v0_9.md \
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
    data_construction/tools/build_candidate_backbone_library.py \
    data_construction/tools/_representative_environment_source.py \
    data_construction/tools/build_representative_environment_realization.py \
    data_construction/tools/build_operator_equivalence_normalization.py \
    data_construction/tools/build_operator_equivalence_crossed_author_sensitivity.py \
    data_construction/tools/build_operator_equivalence_normalization_v0_2.py \
    data_construction/tools/build_operator_equivalence_targeted_reauthor.py \
    data_construction/tools/build_operator_equivalence_targeted_instrument_v0_2.py \
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
    tests/test_candidate_backbone_library.py \
    tests/test_representative_environment_realization.py \
    tests/test_operator_equivalence_normalization.py \
    tests/test_operator_equivalence_crossed_author_sensitivity.py \
    tests/test_operator_equivalence_normalization_v0_2.py \
    tests/test_operator_equivalence_targeted_reauthor.py \
    tests/test_operator_equivalence_targeted_instrument_v0_2.py \
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
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/candidate_backbone_library_plan_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/candidate_backbone_family_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/representative_selection_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/environment_realization_outcome_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/backbone_adequacy_assessment_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/environment_realization_outcome_schema_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/open_operator_realization_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/representative_environment_realization_plan_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/representative_environment_view_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/candidate_backbone_families_v0_1.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/representative_selection_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/checks.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/run_manifest.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/inputs/environment_views.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/inputs/environment_views_manifest_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/inputs/producer_routing_manifest_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/stage_e1/backbone_adequacy_assessments.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/stage_e1/assessment_bindings_for_e2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/stage_e2/open_operator_realizations.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/outcomes.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/checks.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/metrics_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/environment_exposure_ledger_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/run_manifest.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_normalization_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_normalization_plan_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_crossed_author_sensitivity_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_crossed_author_sensitivity_plan_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_normalization_schema_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_crossed_comparison_schema_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_normalization_plan_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_reauthor_normalization_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_reauthor_comparison_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_reauthor_plan_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/structural_projections.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/normalized_candidates.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/question_normalized_sets.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/family_normalized_sets.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/checks.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/metrics_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_1/run_manifest.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/authoring_packets/crossed_author_01.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/authoring_packets/crossed_author_02.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/author_outputs/crossed_author_01.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/author_outputs/crossed_author_02.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/combined_author_records.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/normalized_candidates.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/question_comparisons.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/checks.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/metrics_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_crossed_author_sensitivity_v0_1/run_manifest.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/normalized_candidates.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/original_question_sets.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/original_family_sets.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/crossed_question_comparisons.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/checks.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/metrics_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_normalization_v0_2/run_manifest.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/authoring_packets/targeted_author_01.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/authoring_packets/targeted_author_02.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/author_outputs/targeted_author_01.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/author_outputs/targeted_author_02.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/combined_author_records.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/normalized_candidates.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/question_comparisons.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/checks.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/metrics_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_reauthor_v0_1/run_manifest.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_instrument_feedback_schema_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_instrument_normalization_schema_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_instrument_comparison_schema_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/operator_equivalence_targeted_instrument_plan_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/authoring_packets/instrument_author_01.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/authoring_packets/instrument_author_02.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/draft_outputs/instrument_author_01.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/draft_outputs/instrument_author_02.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/feedback_round_01/instrument_author_01.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/feedback_round_01/instrument_author_02.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/final_outputs/instrument_author_01.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/final_outputs/instrument_author_02.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/combined_draft_records.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/draft_normalized_candidates.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/combined_final_records.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/final_normalized_candidates.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/question_comparisons.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/checks.jsonl"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/metrics_v0_2.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/operator_equivalence_targeted_instrument_v0_2/run_manifest.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_design_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_plan_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_packet_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_raw_schema_v0_1.json"),
    Path("data_construction/exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_runtime_freeze_v0_1.json"),
    Path("state/narrowed_grounding_author_dispatch_v0_1.json"),
    *[Path("data_construction/exploration/ai_question_structure_scale_v0_1/narrowed_grounding_v0_1") / name for name in (
        "packets/question_01.json", "packets/question_02.json", "packets/question_03.json",
        "packets/question_04.json", "packets/question_05.json", "packets/question_06.json",
        "packet_manifest.json", "grounding_records.jsonl", "checks.jsonl", "question_comparisons.jsonl",
        "metrics_v0_1.json", "run_manifest.json", "grounding_exposure_ledger_v0_1.json",
    )],
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

grounding_result_decisions = {
    "STOP_TECHNICAL_OR_LEAKAGE_FAILURE", "BLOCKED_PINNED_ENVIRONMENT_UNAVAILABLE",
    "INCOMPLETE_GROUNDING_COLLECTION", "REVIEW_AMBIGUITY_OR_COVERAGE_BEFORE_EXECUTION_PLAN",
    "FREEZE_GROUNDING_EVIDENCE_FOR_SEPARATE_EXECUTION_PLAN",
}
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
    "FREEZE_EQUIVALENCE_AWARE_OPERATOR_NORMALIZATION_BEFORE_GROUNDING",
    "REVISE_EQUIVALENCE_NORMALIZATION_CONTRACT",
    "NARROW_OR_REAUTHOR_BEFORE_GROUNDING",
    "REVISE_TARGETED_AUTHORING_INSTRUMENT_BEFORE_GROUNDING",
    "FREEZE_INSTRUMENT_REAUTHOR_EVIDENCE_FOR_SEPARATE_NARROWED_GROUNDING_PLAN",
    "IMPLEMENT_FROZEN_NARROWED_GROUNDING_PROTOCOL",
    "MATERIALIZE_FROZEN_NARROWED_GROUNDING_PACKETS",
    *grounding_result_decisions,
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
    elif state.get("current_scientific_decision") in {
        "NARROW_OR_REAUTHOR_BEFORE_GROUNDING",
        "REVISE_TARGETED_AUTHORING_INSTRUMENT_BEFORE_GROUNDING",
        "FREEZE_INSTRUMENT_REAUTHOR_EVIDENCE_FOR_SEPARATE_NARROWED_GROUNDING_PLAN",
        "IMPLEMENT_FROZEN_NARROWED_GROUNDING_PROTOCOL",
        "MATERIALIZE_FROZEN_NARROWED_GROUNDING_PACKETS",
        *grounding_result_decisions,
    }:
        grounding_result_complete = state.get("current_scientific_decision") in grounding_result_decisions
        grounding_runtime_complete = grounding_result_complete or state.get("current_scientific_decision") == (
            "MATERIALIZE_FROZEN_NARROWED_GROUNDING_PACKETS"
        )
        grounding_plan_complete = grounding_runtime_complete or state.get("current_scientific_decision") == (
            "IMPLEMENT_FROZEN_NARROWED_GROUNDING_PROTOCOL"
        )
        instrument_result_complete = grounding_plan_complete or state.get("current_scientific_decision") == (
            "FREEZE_INSTRUMENT_REAUTHOR_EVIDENCE_FOR_SEPARATE_NARROWED_GROUNDING_PLAN"
        )
        targeted_result_complete = state.get("current_scientific_decision") in {
            "REVISE_TARGETED_AUTHORING_INSTRUMENT_BEFORE_GROUNDING",
            "FREEZE_INSTRUMENT_REAUTHOR_EVIDENCE_FOR_SEPARATE_NARROWED_GROUNDING_PLAN",
            "IMPLEMENT_FROZEN_NARROWED_GROUNDING_PROTOCOL",
            "MATERIALIZE_FROZEN_NARROWED_GROUNDING_PACKETS",
            *grounding_result_decisions,
        }
        if grounding_plan_complete:
            expected_phase = ("phase_2j_narrowed_grounding_packet_materialization" if grounding_runtime_complete
                              else "phase_2i_narrowed_grounding_runtime_implementation")
            expected_status = ("narrowed_grounding_runtime_frozen_all_outputs_absent_packets_pending" if grounding_runtime_complete
                               else "narrowed_grounding_plan_frozen_runtime_implementation_and_output_absent_receipt_pending")
            expected_gate = ("NARROWED_GROUNDING_PACKETS_NOT_MATERIALIZED" if grounding_runtime_complete
                             else "NARROWED_GROUNDING_RUNTIME_NOT_FROZEN")
            if grounding_result_complete:
                expected_phase = "phase_2k_narrowed_grounding_result_review"
                expected_status = "narrowed_grounding_results_frozen_no_execution_or_answer_recovery"
                expected_gate = "NARROWED_GROUNDING_NEXT_VERSIONED_DECISION_REQUIRED"
            if state.get("active_phase") != expected_phase:
                errors.append("grounding runtime state has an unexpected active_phase")
            if state.get("scientific_decision_status") != expected_status:
                errors.append("grounding runtime state has an unexpected status")
            if expected_gate not in state_gates:
                errors.append("grounding runtime state lacks its active gate")
            if grounding_runtime_complete and "NARROWED_GROUNDING_RUNTIME_NOT_FROZEN" in state_gates:
                errors.append("grounding packet state retains the superseded runtime gate")
            if grounding_result_complete and "NARROWED_GROUNDING_PACKETS_NOT_MATERIALIZED" in state_gates:
                errors.append("grounding result state retains the superseded packet gate")
            if "NARROWED_GROUNDING_PLAN_NOT_FROZEN" in state_gates:
                errors.append("grounding runtime state retains the superseded plan gate")
            grounding_state = state.get("artifact_status", {}).get("narrowed_grounding_v0_1", {})
            expected_grounding = {
                "status": ("runtime_frozen_packets_pending_no_grounding_outputs" if grounding_runtime_complete
                           else "plan_frozen_runtime_pending_no_grounding_outputs"),
                "active_gate": True,
                "implementation_commit": "6bd9c36ddc6207552b778cf5b20b16946975ef05",
                "plan_freeze_commit": "b2ca1fbc413336fa330b11a14649735acc25f0df",
                "source_commit": "aa380e69b534e475f09d496955ebcbac69531309",
                "question_count": 6, "author_question_pairs": 12, "candidate_count": 14,
                "source_binding_slot_count": 52, "planned_output_file_count": 20,
                "candidate_selection": "all_final_full_eligible_observations_no_deduplication",
                "plan_validation": "passed_exact_reconstruction_hashes_ancestry_and_output_absence",
                "runtime_freeze_receipt_status": "committed_output_absent" if grounding_runtime_complete else "not_created",
                "grounding_output_count": 0, "grounding_started": False,
                "execution_started": False, "answer_recovery_started": False,
                "human_evidence_count": 0, "gold_claimed": False,
                "fresh_or_locked_question_ids_used": False,
            }
            if grounding_result_complete:
                expected_grounding.update(status="static_results_materialized_non_human_non_gold",
                                          grounding_started=True)
                expected_grounding.pop("grounding_output_count")
            for key, value in expected_grounding.items():
                if grounding_state.get(key) != value:
                    errors.append(f"narrowed grounding state mismatch for {key}")
            receipt = Path(
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "contracts/narrowed_grounding_runtime_freeze_v0_1.json"
            )
            if grounding_runtime_complete:
                runtime_expected = {
                    "runtime_implementation_commit": "2983168f48689e8e7129a9bdecde4787a4ecb8cf",
                    "runtime_freeze_commit": "6c7487beddb03625b9fd23ef7514eebe307d397b",
                    "runtime_unit_tests_passed": 26,
                    "runtime_validation": "passed_exact_pins_schemas_hashes_git_order_and_current_output_absence",
                    "packet_output_count": 0,
                }
                if grounding_result_complete:
                    runtime_expected.update(
                        runtime_validation="passed_exact_pins_schemas_hashes_and_historical_freeze_absence",
                        packet_output_count=6,
                    )
                for key, value in runtime_expected.items():
                    if grounding_state.get(key) != value:
                        errors.append(f"narrowed grounding runtime state mismatch for {key}")
                if not receipt.is_file() or receipt.is_symlink():
                    errors.append("grounding runtime receipt missing or unsafe")
                for label, reference in grounding_state.get("artifacts", {}).items():
                    artifact = Path(reference.get("path", ""))
                    if not artifact.is_file() or reference.get("sha256") != hashlib.sha256(artifact.read_bytes()).hexdigest():
                        errors.append(f"narrowed grounding artifact hash mismatch: {label}")
                if set(grounding_state.get("artifacts", {})) != {"plan", "design", "protocol", "runtime_receipt", "packet_schema", "raw_schema"}:
                    errors.append("narrowed grounding artifact inventory mismatch")
                if grounding_result_complete:
                    import subprocess
                    import narrowed_grounding_runtime_v0_1 as grounding_runtime
                    output_paths = grounding_runtime.freeze.planned_outputs()
                    results = grounding_state.get("results", {})
                    references = results.get("artifacts", {})
                    expected_present = {label for label, name in output_paths.items() if Path(name).is_file()}
                    if set(references) != expected_present:
                        errors.append("grounding result artifact inventory mismatch")
                    for label in expected_present:
                        path = Path(output_paths[label])
                        reference = references.get(label, {})
                        if (reference.get("path") != str(path) or path.is_symlink() or
                                reference.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest()):
                            errors.append(f"grounding result artifact identity mismatch: {label}")
                    metric_path = Path(output_paths["metrics"])
                    if metric_path.is_file():
                        metrics = json.loads(metric_path.read_text())
                        if results.get("metrics") != metrics or state.get("current_scientific_decision") != metrics.get("decision"):
                            errors.append("grounding decision/counts do not match frozen metrics")
                        if grounding_state.get("grounding_output_count") != metrics.get("delivered_valid_candidate_records"):
                            errors.append("grounding validated-record count mismatch")
                        if metrics.get("denominators") != {"questions": 6, "author_question_pairs": 12, "candidates": 14, "source_slots": 52}:
                            errors.append("grounding denominator drift")
                        if metrics.get("evidence_boundary") != grounding_runtime.EVIDENCE:
                            errors.append("grounding evidence boundary mismatch")
                    if results.get("packet_freeze_commit") != "861b3cfd69fd622cfc67faaa7856f7e60f8ac872":
                        errors.append("grounding packet freeze identity mismatch")
                    if results.get("raw_file_count") != sum(label in expected_present for label in grounding_runtime.RAW_LABELS):
                        errors.append("grounding raw file count mismatch")
                    dispatch_path = Path("state/narrowed_grounding_author_dispatch_v0_1.json")
                    dispatch_ref = results.get("dispatch_receipt", {})
                    if (dispatch_ref.get("path") != str(dispatch_path) or not dispatch_path.is_file() or
                            dispatch_ref.get("sha256") != hashlib.sha256(dispatch_path.read_bytes()).hexdigest()):
                        errors.append("grounding dispatch receipt identity mismatch")
                    else:
                        dispatch = json.loads(dispatch_path.read_text())
                        authors = dispatch.get("authors", [])
                        if (dispatch.get("fork_context") is not False or dispatch.get("model_override_requested") is not False or
                                dispatch.get("packet_freeze_commit") != results.get("packet_freeze_commit") or
                                [a.get("question_index") for a in authors] != list(range(1, 7)) or
                                len({a.get("agent_id") for a in authors}) != 6 or
                                len({a.get("procedural_context_id") for a in authors}) != 6):
                            errors.append("grounding dispatch routing mismatch")
                        for author in authors:
                            packet = author.get("packet", {})
                            index = author.get("question_index", 0)
                            name = output_paths.get(f"packet_{index:02}")
                            if (packet.get("path") != name or not name or
                                    packet.get("sha256") != hashlib.sha256(Path(name).read_bytes()).hexdigest() or
                                    author.get("raw_output") != output_paths.get(f"raw_{index:02}")):
                                errors.append("grounding dispatched packet identity mismatch")
                        for shared in dispatch.get("shared_author_inputs", []):
                            path = Path(shared.get("path", ""))
                            if not path.is_file() or shared.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                                errors.append("grounding shared author input changed")
                    for key, label in (("raw_capture_commit", "raw_01"), ("result_commit", "run_manifest")):
                        commit = results.get(key, "")
                        introduced = subprocess.run(
                            ["git", "log", "--diff-filter=A", "--format=%H", "HEAD", "--", output_paths[label]],
                            capture_output=True, text=True, check=True,
                        ).stdout.splitlines()
                        if introduced != [commit]:
                            errors.append(f"grounding capture/result commit mismatch: {key}")
            elif receipt.exists() or receipt.is_symlink():
                errors.append("runtime receipt exists but state still declares it absent")
        elif instrument_result_complete:
            if state.get("active_phase") != "phase_2h_narrowed_grounding_protocol_freeze":
                errors.append("narrowed-grounding-plan state has an unexpected active_phase")
            if state.get("scientific_decision_status") != (
                "targeted_instrument_v0_2_complete_all_frozen_technical_isolation_"
                "coverage_semantic_reference_and_retention_criteria_passed_"
                "grounding_blocked_pending_separate_plan"
            ):
                errors.append("narrowed-grounding-plan state has an unexpected status")
            if "NARROWED_GROUNDING_PLAN_NOT_FROZEN" not in state_gates:
                errors.append("narrowed-grounding-plan state lacks its active gate")
            if "TARGETED_REAUTHOR_FULL_ELIGIBILITY_COVERAGE_FAILED" in state_gates:
                errors.append("instrument-pass state retains the superseded coverage gate")
        elif targeted_result_complete:
            if state.get("active_phase") != (
                "phase_2g_targeted_authoring_instrument_revision_protocol_freeze"
            ):
                errors.append("targeted instrument-revision state has an unexpected active_phase")
            if state.get("scientific_decision_status") != (
                "targeted_reauthor_v0_1_complete_technical_contract_passed_"
                "full_eligibility_coverage_and_semantic_stability_failed_"
                "grounding_blocked"
            ):
                errors.append("targeted instrument-revision state has an unexpected status")
            if "TARGETED_REAUTHOR_FULL_ELIGIBILITY_COVERAGE_FAILED" not in state_gates:
                errors.append("targeted instrument-revision state lacks its active gate")
            if "CROSSED_FULL_ELIGIBLE_SEMANTIC_STABILITY_FAILED" in state_gates:
                errors.append("targeted instrument-revision state retains the superseded crossed gate")
        else:
            if state.get("active_phase") != (
                "phase_2f_targeted_crossed_author_reauthor_protocol_freeze"
            ):
                errors.append("targeted re-authoring state has an unexpected active_phase")
            if state.get("scientific_decision_status") != (
                "normalization_v0_2_complete_technical_and_adapter_contracts_passed_"
                "crossed_semantic_stability_failed_grounding_blocked"
            ):
                errors.append("targeted re-authoring state has an unexpected status")
            if "CROSSED_FULL_ELIGIBLE_SEMANTIC_STABILITY_FAILED" not in state_gates:
                errors.append("targeted re-authoring state lacks its active gate")
        for stale_gate in (
            "EQUIVALENCE_NORMALIZATION_V0_2_REVISION_REQUIRED",
            "OPERATOR_EQUIVALENCE_NORMALIZATION_NOT_STARTED",
            "REPRESENTATIVE_ENVIRONMENT_REALIZATION_NOT_STARTED",
            "CANDIDATE_BACKBONE_LIBRARY_NOT_FROZEN",
        ):
            if stale_gate in state_gates:
                errors.append(f"targeted re-authoring state retains stale gate {stale_gate}")

        artifact_status = state.get("artifact_status", {})
        normalization = artifact_status.get("operator_equivalence_normalization_v0_1", {})
        expected_normalization = {
            "status": "complete_reversible_label_free_two_layer_normalization",
            "active_gate": False,
            "source_question_count": 71,
            "target_variant_count": 72,
            "candidate_count": 93,
            "equivalence_status_counts": {
                "equivalent": 89,
                "provisionally_equivalent": 4,
                "not_equivalent": 0,
            },
            "reversible_projection_loss_count": 0,
            "distinct_semantic_quotient_count": 39,
            "distinct_environment_adapter_signature_count": 19,
            "multi_question_family_count": 16,
            "unstable_multi_question_semantic_set_count": 6,
            "producer_question_effects_separable": False,
            "decision": "RUN_PRECOMMITTED_CROSSED_AUTHOR_SENSITIVITY",
            "grounding_authorized": False,
            "fresh_reserve_ids_used": False,
            "human_evidence_count": 0,
            "gold_claimed": False,
        }
        for key, expected_value in expected_normalization.items():
            if normalization.get(key) != expected_value:
                errors.append(f"normalization v0.1 state mismatch for {key}")

        sensitivity = artifact_status.get(
            "operator_equivalence_crossed_author_sensitivity_v0_1", {}
        )
        expected_sensitivity = {
            "status": "complete_frozen_criteria_failed_revision_required",
            "active_gate": False,
            "author_count": 2,
            "question_count": 16,
            "author_record_count": 32,
            "candidate_count": 34,
            "semantic_set_exact_match_count": 16,
            "semantic_set_exact_match_rate": 1.0,
            "mean_semantic_set_jaccard": 1.0,
            "adapter_set_exact_match_count": 0,
            "adapter_set_exact_match_rate": 0.0,
            "mean_adapter_set_jaccard": 0.0,
            "distinct_adapter_signature_count": 25,
            "normalization_status_counts": {
                "equivalent": 20,
                "provisionally_equivalent": 9,
                "not_equivalent": 5,
            },
            "criteria_passed": False,
            "decision": "REVISE_EQUIVALENCE_NORMALIZATION_CONTRACT",
            "grounding_started": False,
            "fresh_reserve_ids_used": False,
            "human_evidence_count": 0,
            "gold_claimed": False,
        }
        for key, expected_value in expected_sensitivity.items():
            if sensitivity.get(key) != expected_value:
                errors.append(f"crossed-author sensitivity state mismatch for {key}")

        normalization_v0_2 = artifact_status.get(
            "operator_equivalence_normalization_v0_2", {}
        )
        expected_normalization_v0_2 = {
            "status": (
                "complete_technical_and_adapter_contracts_passed_"
                "crossed_semantic_stability_failed"
            ),
            "active_gate": False,
            "implementation_commit": "16868477069f4413392c4f968c3e94c510fcb7a8",
            "plan_freeze_commit": "3d636e57b88da4469540a8ed47fa413147857060",
            "materialization_commit": "a13fa72c75049e09a966a9ea11e514c4a961841e",
            "original_candidate_count": 93,
            "crossed_author_candidate_count": 34,
            "candidate_count": 127,
            "original_question_count": 71,
            "original_family_count": 30,
            "crossed_question_count": 16,
            "eligibility_status_counts": {
                "full_eligible": 121,
                "provisional_only": 1,
                "ineligible": 5,
            },
            "technical_loss_count": 0,
            "eligible_set_contamination_count": 0,
            "unclassified_adapter_candidate_count": 0,
            "max_component_records_per_candidate": 7,
            "distinct_candidate_semantic_profile_count": 44,
            "distinct_overall_factorized_adapter_count": 65,
            "distinct_adapter_component_signature_counts": {
                "modality_cardinality": 32,
                "semantic_relative_placement": 38,
                "split_fuse_boundary": 24,
                "output_arity": 9,
            },
            "crossed_full_eligible_semantic_exact_match_count": 10,
            "crossed_full_eligible_semantic_exact_match_rate": 0.625,
            "crossed_mean_full_eligible_semantic_jaccard": 0.65625,
            "crossed_full_eligible_author_question_coverage": 27,
            "crossed_e1_challenge_semantic_exact_match_count": 1,
            "crossed_adequate_control_semantic_exact_match_count": 9,
            "unstable_multi_question_original_family_count": 6,
            "technical_contract_passed": True,
            "adapter_component_contract_passed": True,
            "crossed_semantic_stability_passed": False,
            "all_criteria_passed": False,
            "decision": "NARROW_OR_REAUTHOR_BEFORE_GROUNDING",
            "grounding_protocol_authorized_next": False,
            "grounding_started": False,
            "fresh_question_ids_used": False,
            "human_evidence_count": 0,
            "gold_claimed": False,
            "mismatch_question_ids": [
                "0d48bffa70ef4acf",
                "cc681cfdba9badd5",
                "1e2e4e4f72a64bbf",
                "1e674ae4b655c1a1",
                "1ca8ffcd3e20e498",
                "ba563b015b09bf21",
            ],
        }
        for key, expected_value in expected_normalization_v0_2.items():
            if normalization_v0_2.get(key) != expected_value:
                errors.append(f"normalization v0.2 state mismatch for {key}")

        targeted_reauthor = artifact_status.get(
            "operator_equivalence_targeted_reauthor_v0_1", {}
        )
        if targeted_result_complete:
            expected_targeted_reauthor = {
                "status": (
                    "complete_technical_contract_passed_full_eligibility_"
                    "coverage_and_semantic_stability_failed"
                ),
                "active_gate": False,
                "implementation_commit": "51b5204d568efc55f6d1fdff3d7d1b2bf1f6f008",
                "plan_freeze_commit": "4fa67b5f908a3b323610451964aeedcaaef06a2f",
                "packet_materialization_commit": "5e45170f86c8f9b540003d2ffeb896407f26594f",
                "author_01_commit": "c83bb1c8583fbd9ce1fa394f92f092889244b156",
                "author_02_commit": "a2610732d7b23fb6ad0e88698c19e7d4ebf37af9",
                "materialization_commit": "f9377db09ef8d34cc846801730980e933e4e8331",
                "author_count": 2,
                "question_count": 6,
                "author_record_count": 12,
                "candidate_count": 14,
                "eligibility_status_counts": {
                    "full_eligible": 9,
                    "provisional_only": 0,
                    "ineligible": 5,
                },
                "technical_loss_count": 0,
                "eligible_set_contamination_count": 0,
                "unclassified_adapter_candidate_count": 0,
                "preferred_candidate_count": 0,
                "fresh_question_id_count": 0,
                "profile_inventory_loss_count": 0,
                "full_eligible_author_question_coverage": 8,
                "nonempty_new_author_semantic_intersection_count": 2,
                "new_author_semantic_exact_match_count": 1,
                "new_author_semantic_exact_match_rate": 1 / 6,
                "mean_new_author_semantic_jaccard": 0.25,
                "reference_compatible_author_question_count": 8,
                "distinct_observed_semantic_profile_count": 11,
                "technical_contract_passed": True,
                "full_eligibility_coverage_passed": False,
                "semantic_stability_and_reference_compatibility_passed": False,
                "all_criteria_passed": False,
                "decision": "REVISE_TARGETED_AUTHORING_INSTRUMENT_BEFORE_GROUNDING",
                "grounding_protocol_authorized_next": False,
                "separate_narrowed_grounding_plan_may_be_frozen_next": False,
                "grounding_started": False,
                "fresh_question_ids_used": False,
                "human_evidence_count": 0,
                "gold_claimed": False,
                "ineligible_question_ids": [
                    "0d48bffa70ef4acf",
                    "cc681cfdba9badd5",
                    "1e674ae4b655c1a1",
                    "1ca8ffcd3e20e498",
                    "ba563b015b09bf21",
                ],
            }
            for key, expected_value in expected_targeted_reauthor.items():
                if targeted_reauthor.get(key) != expected_value:
                    errors.append(f"targeted re-author state mismatch for {key}")

        targeted_instrument = artifact_status.get(
            "operator_equivalence_targeted_instrument_v0_2", {}
        )
        if instrument_result_complete:
            expected_targeted_instrument = {
                "status": (
                    "complete_all_frozen_technical_isolation_coverage_semantic_"
                    "reference_and_retention_criteria_passed"
                ),
                "active_gate": False,
                "implementation_commit": "6703293a3b73539940864d681a034abfd939707b",
                "plan_freeze_commit": "3caedbe7a84ee2cac15cf24a33c7f0ff26177f21",
                "packet_materialization_commit": "50801e80caa86fc771be0bed85c6ba687e835539",
                "draft_commit": "2df347a76f381c2d1e6deec02f34e4f38bd4ea4a",
                "feedback_commit": "1a92e63d9e7abd12f4ae70c0b250512f42f61601",
                "final_author_commit": "3de0a547770e3c225ce0cb9f8990cf00558af308",
                "materialization_commit": "d22a9beca223f49d7af17c8657aafdbf8753de4f",
                "author_count": 2,
                "question_count": 6,
                "draft_record_count": 12,
                "final_record_count": 12,
                "draft_candidate_count": 14,
                "final_candidate_count": 14,
                "feedback_record_count": 12,
                "feedback_rounds_per_author": 1,
                "feedback_binding_error_count": 0,
                "feedback_reference_leakage_count": 0,
                "final_eligibility_status_counts": {
                    "full_eligible": 14,
                    "provisional_only": 0,
                    "ineligible": 0,
                },
                "technical_loss_count": 0,
                "eligible_set_contamination_count": 0,
                "unclassified_adapter_candidate_count": 0,
                "preferred_candidate_count": 0,
                "fresh_question_id_count": 0,
                "profile_inventory_loss_count": 0,
                "final_candidate_local_author_question_coverage": 12,
                "full_eligible_author_question_coverage": 12,
                "nonempty_final_author_semantic_intersection_count": 6,
                "final_author_semantic_exact_match_count": 6,
                "final_author_semantic_exact_match_rate": 1.0,
                "mean_final_author_semantic_jaccard": 1.0,
                "targeted_v0_1_reference_compatible_author_question_count": 12,
                "distinct_observed_semantic_profile_count": 10,
                "draft_to_final_changed_record_count": 0,
                "technical_and_isolation_contract_passed": True,
                "repeated_complete_coverage_gate_passed": True,
                "semantic_stability_and_reference_compatibility_passed": True,
                "all_criteria_passed": True,
                "decision": (
                    "FREEZE_INSTRUMENT_REAUTHOR_EVIDENCE_FOR_SEPARATE_"
                    "NARROWED_GROUNDING_PLAN"
                ),
                "separate_narrowed_grounding_plan_may_be_frozen_next": True,
                "grounding_authorized_without_separate_plan": False,
                "grounding_started": False,
                "execution_started": False,
                "answer_recovery_started": False,
                "fresh_or_locked_question_ids_used": False,
                "human_evidence_count": 0,
                "gold_claimed": False,
            }
            for key, expected_value in expected_targeted_instrument.items():
                if targeted_instrument.get(key) != expected_value:
                    errors.append(f"targeted instrument state mismatch for {key}")

        artifact_sections = [
            ("normalization", normalization),
            ("crossed-author sensitivity", sensitivity),
            ("normalization v0.2", normalization_v0_2),
        ]
        if targeted_result_complete:
            artifact_sections.append(("targeted re-author", targeted_reauthor))
        if instrument_result_complete:
            artifact_sections.append(("targeted instrument", targeted_instrument))
        if grounding_plan_complete:
            artifact_sections.append(("narrowed grounding", grounding_state))
        for section_name, section in artifact_sections:
            artifacts = section.get("artifacts", {})
            if not isinstance(artifacts, dict) or not artifacts:
                errors.append(f"{section_name} state lacks artifacts")
                continue
            for label, reference in artifacts.items():
                if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
                    errors.append(f"{section_name} artifact reference malformed: {label}")
                    continue
                path = Path(reference["path"])
                if not path.is_file():
                    errors.append(f"{section_name} artifact missing: {label}")
                elif reference.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                    errors.append(f"{section_name} artifact hash mismatch: {label}")

    elif state.get("current_scientific_decision") == (
        "FREEZE_EQUIVALENCE_AWARE_OPERATOR_NORMALIZATION_BEFORE_GROUNDING"
    ):
        if state.get("active_phase") != (
            "phase_2d_operator_equivalence_normalization_contract_freeze"
        ):
            errors.append("operator-normalization state has an unexpected active_phase")
        if state.get("scientific_decision_status") != (
            "representative_environment_e1_e2_complete_equivalence_normalization_"
            "required_before_grounding_or_common_graph_claim"
        ):
            errors.append(
                "operator-normalization state has an unexpected scientific_decision_status"
            )
        if "CANDIDATE_BACKBONE_LIBRARY_NOT_FROZEN" in state_gates:
            errors.append("materialized candidate-library state retains its stale freeze gate")
        if "OPERATOR_EQUIVALENCE_NORMALIZATION_NOT_STARTED" not in state_gates:
            errors.append("operator-normalization state lacks its active next-stage gate")
        if "REPRESENTATIVE_ENVIRONMENT_REALIZATION_NOT_STARTED" in state_gates:
            errors.append("operator-normalization state retains the completed realization gate")
        if "N300_SCALE_EXPANSION_NOT_PERFORMED" in state_gates:
            errors.append("candidate-library state retains the completed N300 gate")
        if "QUESTION_ONLY_CALIBRATION_NOT_PERFORMED" in state_gates:
            errors.append("candidate-library state retains the deferred human-calibration gate")

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

        scale = state.get("artifact_status", {}).get(
            "ai_question_structure_scale_exploration", {}
        )
        expected_scale_summary = {
            "status": "cumulative_n300_complete_candidate_library_branch_selected",
            "active_gate": False,
            "run_id": "ai_question_structure_scale_v0_1_run_001",
            "evidence_class": "ai_exploratory_non_human_non_gold",
            "contract_freeze_commit": "98a162708104877129a46a6a4a88c555ffe20be4",
            "question_count": 300,
            "prefix_contract_development_count": 30,
            "new_expansion_count": 200,
            "valid_record_count": 300,
            "invalid_record_count": 0,
            "fine_family_count": 39,
            "contracted_family_count": 30,
            "topology_family_count": 10,
            "task_family_count": 70,
            "contracted_singleton_question_mass": 0.04666666666666667,
            "contracted_n100_to_new200_transfer_rate": 0.915,
            "contracted_top_10_coverage": 0.9133333333333333,
            "uncertain_record_count": 94,
            "other_question_count": 0,
            "alternative_graph_question_count": 1,
            "precommitted_decision": (
                "FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_"
                "REPRESENTATIVE_ENVIRONMENT_REALIZATION"
            ),
            "decision_trigger": "none_of_four_precommitted_n1000_conditions_true",
            "ai_exposed_question_count": 300,
            "unexposed_unallocated_reserve_count": 3066,
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
                errors.append(f"cumulative N300 state mismatch for {key}")
        expected_trigger_values = {
            "cumulative_contracted_singleton_question_mass_above_0_05": False,
            "cumulative_OTHER_question_rate_above_0_05": False,
            "tail_50_sequential_contracted_novelty_above_0_10_with_at_least_2_new_families": False,
            "at_least_2_material_cross_partition_new_contracted_families": False,
        }
        if scale.get("n1000_trigger_values") != expected_trigger_values:
            errors.append("cumulative N300 trigger-value summary mismatch")
        expected_trigger_observations = {
            "contracted_singleton_question_mass": 0.04666666666666667,
            "other_question_rate": 0.0,
            "tail_50_sequential_question_novelty_rate": 0.1,
            "tail_50_sequential_new_family_count": 5,
            "material_cross_partition_new_contracted_family_count": 1,
        }
        if scale.get("n1000_trigger_observations") != expected_trigger_observations:
            errors.append("cumulative N300 trigger-observation summary mismatch")
        expected_partition_sensitivity = {
            "status": "precommitted_cumulative_analysis_complete",
            "recurring_new_contracted_family_count": 3,
            "cross_partition_recurring_new_contracted_family_count": 2,
            "material_cross_partition_new_contracted_family_count": 1,
            "partition_confounding_detected": False,
            "producer_context_sensitivity_present": True,
            "raw_branch_question_count": 6,
            "reduced_branch_question_count": 1,
            "raw_join_question_count": 11,
            "reduced_join_question_count": 6,
            "operational_decision_changed": False,
        }
        if scale.get("partition_sensitivity") != expected_partition_sensitivity:
            errors.append("cumulative N300 partition-sensitivity summary mismatch")

        required_n300_artifacts = {
            "sequencing_decision": (
                "data_construction/reports/research_sequencing_decision_v0_3.md"
            ),
            "n300_pool_builder": (
                "data_construction/tools/build_ai_question_structure_n300_pool.py"
            ),
            "n300_analyzer": (
                "data_construction/tools/analyze_ai_question_structure_cumulative_n300.py"
            ),
            "n300_analysis_plan": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "contracts/cumulative_n300_analysis_plan_v0_1.json"
            ),
            "n300_pool_views": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "pool/question_only_views_n300.jsonl"
            ),
            "n300_pool_manifest": (
                "data_construction/manifests/"
                "ai_question_structure_exploratory_pool_v0_2.json"
            ),
            "n300_selection_exposure_ledger": (
                "data_construction/manifests/question_exposure_ledger_v0_2.json"
            ),
            "n300_routing_manifest": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "n300_extension_v0_1/producer_routing_manifest_v0_1.json"
            ),
            "n300_records": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "cumulative_n300_v0_1/records.jsonl"
            ),
            "n300_checks": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "cumulative_n300_v0_1/checks.jsonl"
            ),
            "n300_derived_signatures": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "cumulative_n300_v0_1/analysis/derived_signatures_v0_1.jsonl"
            ),
            "n300_metrics": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "cumulative_n300_v0_1/analysis/"
                "cumulative_n300_structural_saturation_metrics_v0_1.json"
            ),
            "n300_generated_report": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "cumulative_n300_v0_1/analysis/"
                "cumulative_n300_structural_saturation_report_v0_1.md"
            ),
            "n300_run_manifest": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "cumulative_n300_v0_1/run_manifest.json"
            ),
            "n300_completion_exposure_ledger": (
                "data_construction/manifests/question_exposure_ledger_v0_3.json"
            ),
        }
        scale_artifacts = scale.get("artifacts", {})
        if not isinstance(scale_artifacts, dict):
            errors.append("cumulative N300 artifact inventory must be an object")
            scale_artifacts = {}
        for label, expected_path in required_n300_artifacts.items():
            reference = scale_artifacts.get(label)
            path = Path(expected_path)
            if not isinstance(reference, dict) or reference.get("path") != expected_path:
                errors.append(f"cumulative N300 state lacks artifact {label}")
            elif not path.is_file():
                errors.append(f"cumulative N300 artifact is missing: {label}")
            elif reference.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append(f"cumulative N300 artifact hash mismatch: {label}")

        candidate = state.get("artifact_status", {}).get(
            "candidate_backbone_library", {}
        )
        expected_candidate_summary = {
            "status": "complete_candidate_non_gold_not_established",
            "active_gate": False,
            "library_id": "hybridqa_n300_contracted_candidate_backbone_library_v0_1",
            "selection_id": "hybridqa_n300_candidate_backbone_coverage_sample_v0_1",
            "implementation_commit": "66bd21948d5269f75d5f816e3f7cfba3941229d5",
            "contract_freeze_commit": "f3ac5c47527b46234543d89bc1d7d8034f2723f1",
            "materialization_commit": "80ce8c2e992e56b1175cf144ff52b0765755dcd2",
            "source_record_count": 300,
            "candidate_family_count": 30,
            "member_question_count": 300,
            "all_source_members_assigned_exactly_once": True,
            "post_hoc_semantic_family_merging_allowed": False,
            "evidence_tier_family_counts": {
                "recurrent": 9,
                "doubleton": 7,
                "singleton": 14,
            },
            "representative_selection_status": "complete_committed_before_environment_inspection",
            "representative_selection_kind": (
                "deterministic_family_complete_frequency_rarity_coverage_stress_sample"
            ),
            "representative_question_count": 71,
            "selected_family_count": 30,
            "deterministic_check_count": 102,
            "selected_question_ids_ordered_sha256": (
                "5403debe2cbe9c7f55ded0a01b49d7c42bf03e53a71350efe269bbd3c0bdcb2e"
            ),
            "selected_question_ids_set_sha256": (
                "9b6e05650834871ce30acc1c2dfde18fc64910dcd238982f5d482f6a31e15680"
            ),
            "probability_sample": False,
            "prevalence_estimation_supported": False,
            "environment_or_outcome_used_for_ranking": False,
            "question_text_used_for_ranking": False,
            "environment_content_inspected_for_selection": False,
            "environment_noninspection_claim_basis": (
                "tool_input_allowlist_plus_procedural_research_boundary_not_global_authentication"
            ),
            "environment_noninspection_machine_authenticated": False,
            "actual_environment_realization_status": "complete_first_two_signals_evaluated",
            "grounding_evaluated": False,
            "execution_evaluated": False,
            "answer_recovery_evaluated": False,
            "human_evidence_count": 0,
            "gold_claimed": False,
            "semantic_correctness_evaluated": False,
            "modeling_ready_claimed": False,
        }
        for key, expected_value in expected_candidate_summary.items():
            if candidate.get(key) != expected_value:
                errors.append(f"candidate-backbone library state mismatch for {key}")

        expected_candidate_artifacts = {
            "sequencing_decision": "data_construction/reports/research_sequencing_decision_v0_4.md",
            "builder": "data_construction/tools/build_candidate_backbone_library.py",
            "freeze_plan": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "contracts/candidate_backbone_library_plan_v0_1.json"
            ),
            "family_schema": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "contracts/candidate_backbone_family_schema_v0_1.json"
            ),
            "selection_schema": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "contracts/representative_selection_schema_v0_1.json"
            ),
            "environment_outcome_schema": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "contracts/environment_realization_outcome_schema_v0_1.json"
            ),
            "families": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "candidate_backbone_library_v0_1/"
                "candidate_backbone_families_v0_1.jsonl"
            ),
            "representative_selection": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "candidate_backbone_library_v0_1/representative_selection_v0_1.json"
            ),
            "checks": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "candidate_backbone_library_v0_1/checks.jsonl"
            ),
            "generated_report": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "candidate_backbone_library_v0_1/report_v0_1.md"
            ),
            "run_manifest": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "candidate_backbone_library_v0_1/run_manifest.json"
            ),
        }
        candidate_artifacts = candidate.get("artifacts", {})
        if not isinstance(candidate_artifacts, dict) or set(candidate_artifacts) != set(
            expected_candidate_artifacts
        ):
            errors.append("candidate-backbone artifact inventory mismatch")
            candidate_artifacts = (
                candidate_artifacts if isinstance(candidate_artifacts, dict) else {}
            )
        for label, expected_path in expected_candidate_artifacts.items():
            reference = candidate_artifacts.get(label)
            path = Path(expected_path)
            if not isinstance(reference, dict) or reference.get("path") != expected_path:
                errors.append(f"candidate-backbone state lacks artifact {label}")
            elif not path.is_file():
                errors.append(f"candidate-backbone artifact is missing: {label}")
            elif reference.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append(f"candidate-backbone artifact hash mismatch: {label}")

        realization = state.get("artifact_status", {}).get(
            "representative_environment_realization", {}
        )
        expected_realization_summary = {
            "status": "complete_first_two_signals_evaluated_non_human_non_gold",
            "active_gate": False,
            "run_id": "hybridqa_n300_representative_environment_realization_v0_1_run_001",
            "selection_id": "hybridqa_n300_candidate_backbone_coverage_sample_v0_1",
            "implementation_commit": "78fe487327d2fda43cc2ec79203c0a3223d1645b",
            "contract_freeze_commit": "2e8f6a2c8ee2eb7a3d8a175ea7b8d7f94213175c",
            "environment_view_freeze_commit": "1ff98d3a9cbd7cdd7ae5c7de6676818a57481ec7",
            "e1_freeze_commit": "c3ed836c633859d3575bab1f29d7cf0274df6780",
            "materialization_commit": "4d4d86885a5294af40653a48cbf12346f699db53",
            "required_question_count": 71,
            "required_family_count": 30,
            "input_view_and_visibility_contract_status": (
                "frozen_before_selected_raw_environment_access"
            ),
            "operator_realization_protocol_status": "frozen_before_authoring",
            "run_plan_status": "frozen_before_all_planned_outputs",
            "outcome_record_schema_status": (
                "v0_2_frozen_five_signal_separation_and_validated"
            ),
            "actual_environment_view_count": 71,
            "e1_assessment_count": 71,
            "e2_realization_record_count": 71,
            "target_variant_count": 72,
            "realization_candidate_count": 93,
            "outcome_record_count": 71,
            "deterministic_check_count": 285,
            "backbone_adequacy_status_counts": {
                "adequate": 64,
                "partially_adequate": 5,
                "indeterminate": 2,
                "inadequate": 0,
            },
            "environment_operator_realization_status_counts": {
                "available": 71,
                "partially_available": 0,
                "unavailable": 0,
                "indeterminate": 0,
            },
            "candidate_count_distribution": {"one": 49, "two": 22},
            "semantic_to_operator_mapping_counts": {
                "one_to_one": 278,
                "many_to_one": 4,
                "one_to_many": 1,
                "many_to_many": 0,
            },
            "producer_partition_sensitivity": {
                "question_and_producer_effects_separable": False,
                "candidate_counts": [36, 19, 21, 17],
                "records_with_multiple_candidates": [18, 1, 3, 0],
                "environment_extension_node_counts": [95, 2, 47, 0],
                "raw_family_heterogeneity_is_intrinsic_question_property": False,
            },
            "grounding_evaluated_count": 0,
            "execution_evaluated_count": 0,
            "answer_recovery_evaluated_count": 0,
            "operator_vocabulary_selected": False,
            "common_exact_graph_claimed": False,
            "human_evidence_count": 0,
            "gold_claimed": False,
            "modeling_ready_claimed": False,
        }
        for key, expected_value in expected_realization_summary.items():
            if realization.get(key) != expected_value:
                errors.append(
                    f"representative environment-realization state mismatch for {key}"
                )

        expected_realization_artifacts = {
            "freeze_plan": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "contracts/representative_environment_realization_plan_v0_1.json"
            ),
            "environment_views": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/inputs/"
                "environment_views.jsonl"
            ),
            "environment_views_manifest": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/inputs/"
                "environment_views_manifest_v0_1.json"
            ),
            "producer_routing_manifest": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/inputs/"
                "producer_routing_manifest_v0_1.json"
            ),
            "e1_assessments": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/stage_e1/"
                "backbone_adequacy_assessments.jsonl"
            ),
            "e1_hash_bindings_for_e2": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/stage_e1/"
                "assessment_bindings_for_e2.json"
            ),
            "e2_realizations": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/stage_e2/"
                "open_operator_realizations.jsonl"
            ),
            "outcomes": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/outcomes.jsonl"
            ),
            "checks": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/checks.jsonl"
            ),
            "metrics": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/metrics_v0_1.json"
            ),
            "generated_report": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/report_v0_1.md"
            ),
            "environment_exposure_ledger": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/"
                "environment_exposure_ledger_v0_1.json"
            ),
            "run_manifest": (
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/run_manifest.json"
            ),
        }
        realization_artifacts = realization.get("artifacts", {})
        if not isinstance(realization_artifacts, dict) or set(
            realization_artifacts
        ) != set(expected_realization_artifacts):
            errors.append("representative environment-realization artifact inventory mismatch")
            realization_artifacts = (
                realization_artifacts
                if isinstance(realization_artifacts, dict)
                else {}
            )
        for label, expected_path in expected_realization_artifacts.items():
            reference = realization_artifacts.get(label)
            path = Path(expected_path)
            if not isinstance(reference, dict) or reference.get("path") != expected_path:
                errors.append(
                    f"representative environment-realization state lacks artifact {label}"
                )
            elif not path.is_file():
                errors.append(
                    f"representative environment-realization artifact is missing: {label}"
                )
            elif reference.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append(
                    f"representative environment-realization artifact hash mismatch: {label}"
                )
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

    n300_cli_output=$("$PYTHON_BIN" -B \
        data_construction/tools/analyze_ai_question_structure_cumulative_n300.py \
        --validate-only 2>&1)
    n300_cli_rc=$?
    if [ "$n300_cli_rc" -eq 0 ]; then
        pass_check "AI_QUESTION_STRUCTURE_CUMULATIVE_N300_CLI: $n300_cli_output"
    else
        fail_check "AI_QUESTION_STRUCTURE_CUMULATIVE_N300_CLI_FAILED: $n300_cli_output"
    fi

    n300_live_output=$("$PYTHON_BIN" -B - <<'PY' 2>&1
import sys
from pathlib import Path

sys.path.insert(0, str(Path("data_construction/tools").resolve()))
from _common import json_file_bytes, jsonl_file_bytes
import analyze_ai_question_structure_cumulative_n300 as analyzer

plan, views, routing, _, pool = analyzer.validate_contract(
    analyzer.DEFAULT_PLAN,
    analyzer.DEFAULT_SCHEMA,
    analyzer.DEFAULT_PROMPT,
    analyzer.DEFAULT_VIEWS,
    analyzer.DEFAULT_ROUTING,
    analyzer.DEFAULT_POOL_MANIFEST,
    analyzer.DEFAULT_PRIOR_EXPOSURE,
    analyzer.DEFAULT_PREFIX_RECORDS,
)
planned_parts = analyzer._validate_planned_paths(
    plan,
    part_paths=list(analyzer.DEFAULT_PARTS),
    cumulative_outputs={
        "records": analyzer.DEFAULT_RECORDS_OUTPUT,
        "checks": analyzer.DEFAULT_CHECKS,
        "derived_signatures": analyzer.DEFAULT_SIGNATURES,
        "metrics": analyzer.DEFAULT_METRICS,
        "report": analyzer.DEFAULT_REPORT,
        "run_manifest": analyzer.DEFAULT_RUN_MANIFEST,
        "completion_exposure_ledger": analyzer.DEFAULT_EXPOSURE_OUTPUT,
    },
)
contract_freeze_commit = analyzer.verify_contract_freeze(
    analyzer.DEFAULT_PLAN, plan
)
new_records, part_bindings = analyzer.merge_partition_parts(
    list(analyzer.DEFAULT_PARTS), routing, planned_parts
)
records_payload, records, prefix_preservation = analyzer.build_cumulative_records_payload(
    analyzer.DEFAULT_PREFIX_RECORDS, new_records
)
checks, errors = analyzer.validate_records(
    records, views, routing, analyzer.DEFAULT_SCHEMA
)
if errors or len(checks) != 300 or any(item["status"] != "pass" for item in checks):
    raise SystemExit("cumulative N300 live validation is not exactly 300 passes")
derived = analyzer.derive_signatures(records)
source_bindings = {
    "analysis_plan": analyzer._binding(analyzer.DEFAULT_PLAN),
    "record_schema": analyzer._binding(analyzer.DEFAULT_SCHEMA),
    "extraction_prompt": analyzer._binding(analyzer.DEFAULT_PROMPT),
    "question_only_views": analyzer._binding(
        analyzer.DEFAULT_VIEWS, record_count=analyzer.TARGET_COUNT
    ),
    "producer_routing": analyzer._binding(analyzer.DEFAULT_ROUTING),
    "pool_manifest": analyzer._binding(analyzer.DEFAULT_POOL_MANIFEST),
    "prior_exposure_ledger_v0_2": analyzer._binding(
        analyzer.DEFAULT_PRIOR_EXPOSURE
    ),
    "frozen_n100_records": analyzer._binding(
        analyzer.DEFAULT_PREFIX_RECORDS, record_count=analyzer.PREFIX_COUNT
    ),
    "n300_model_parts": part_bindings,
    "cumulative_n300_records": analyzer._planned_artifact(
        analyzer.DEFAULT_RECORDS_OUTPUT,
        records_payload,
        record_count=analyzer.TARGET_COUNT,
    ),
    "frozen_n100_analyzer_and_normalizer": analyzer._binding(
        analyzer.FROZEN_ANALYZER
    ),
    "analysis_implementation": analyzer._binding(Path(analyzer.__file__)),
}
metrics = analyzer.build_metrics(
    records,
    derived,
    prefix_preservation=prefix_preservation,
    source_bindings=source_bindings,
)
exposure = analyzer.build_completion_exposure_ledger(
    question_ids=plan["question_ids"],
    pool=pool,
    prior_exposure_path=analyzer.DEFAULT_PRIOR_EXPOSURE,
    plan_path=analyzer.DEFAULT_PLAN,
    pool_manifest_path=analyzer.DEFAULT_POOL_MANIFEST,
    routing_path=analyzer.DEFAULT_ROUTING,
    cumulative_records_path=analyzer.DEFAULT_RECORDS_OUTPUT,
    cumulative_records_payload=records_payload,
    contract_freeze_commit=contract_freeze_commit,
)
payloads = {
    "records": (analyzer.DEFAULT_RECORDS_OUTPUT, records_payload),
    "checks": (analyzer.DEFAULT_CHECKS, jsonl_file_bytes(checks)),
    "derived_signatures": (
        analyzer.DEFAULT_SIGNATURES,
        jsonl_file_bytes(derived),
    ),
    "metrics": (analyzer.DEFAULT_METRICS, json_file_bytes(metrics)),
    "report": (
        analyzer.DEFAULT_REPORT,
        analyzer.render_report(metrics).encode("utf-8"),
    ),
    "completion_exposure_ledger": (
        analyzer.DEFAULT_EXPOSURE_OUTPUT,
        json_file_bytes(exposure),
    ),
}
run_manifest = analyzer.build_run_manifest(
    source_bindings=source_bindings,
    output_payloads=payloads,
    contract_freeze_commit=contract_freeze_commit,
)
payloads["run_manifest"] = (
    analyzer.DEFAULT_RUN_MANIFEST,
    json_file_bytes(run_manifest),
)
for label, (path, expected_bytes) in payloads.items():
    if path.read_bytes() != expected_bytes:
        raise SystemExit(f"cumulative N300 {label} differs from reconstruction")

contracted = metrics["signature_levels"]["contracted_semantic_dag"]
decision = metrics["n1000_precommitted_decision"]
profile = metrics["segment_record_profiles"]["cumulative_n300"]
graph = metrics["graph_profiles"]["cumulative_n300"]
if (
    contracted["cumulative_n300"]["observed_family_count"] != 30
    or contracted["cumulative_n300"]["singleton_question_mass"]
    != 0.04666666666666667
    or contracted["new_200_transfer_from_n100"]["transfer_rate"] != 0.915
    or decision["decision"]
    != "FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_ENVIRONMENT_REALIZATION"
    or any(decision["trigger_values"].values())
    or profile["uncertain_count"] != 94
    or profile["other_question_count"] != 0
    or graph["transitive_reduced_normalized_dependencies"]["branch_question_count"]
    != 1
    or graph["transitive_reduced_normalized_dependencies"]["join_question_count"]
    != 6
    or exposure["ai_question_structure_exploration"]["processed_count"] != 300
    or exposure["unexposed_unallocated_reserve"]["count"] != 3066
):
    raise SystemExit("cumulative N300 core metrics or evidence boundary mismatch")
print(
    "records=300;checks=300_pass;contracted_families=30;"
    "singleton_mass=0.04666666666666667;new200_transfer=0.915;"
    "uncertain=94;OTHER=0;normalized_branch_join=1,6;"
    "decision=FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_"
    "REPRESENTATIVE_ENVIRONMENT_REALIZATION"
)
PY
    )
    n300_live_rc=$?
    if [ "$n300_live_rc" -eq 0 ]; then
        pass_check "AI_QUESTION_STRUCTURE_CUMULATIVE_N300_LIVE: $n300_live_output"
    else
        fail_check "AI_QUESTION_STRUCTURE_CUMULATIVE_N300_LIVE_FAILED: $n300_live_output"
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        candidate_backbone_output=$("$PYTHON_BIN" -B \
            data_construction/tools/build_candidate_backbone_library.py \
            --validate-only 2>&1)
        candidate_backbone_rc=$?
        if [ "$candidate_backbone_rc" -eq 0 ]; then
            pass_check "CANDIDATE_BACKBONE_LIBRARY_LIVE: $candidate_backbone_output"
        else
            fail_check "CANDIDATE_BACKBONE_LIBRARY_LIVE_FAILED: $candidate_backbone_output"
        fi
    else
        block_check 'CANDIDATE_BACKBONE_LIBRARY_VALIDATION_NOT_RUN: exact pinned dependencies are unavailable in the selected runtime'
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        representative_realization_output=$("$PYTHON_BIN" -B \
            data_construction/tools/build_representative_environment_realization.py \
            --validate-only 2>&1)
        representative_realization_rc=$?
        if [ "$representative_realization_rc" -eq 0 ]; then
            pass_check "REPRESENTATIVE_ENVIRONMENT_REALIZATION_LIVE: $representative_realization_output"
        else
            fail_check "REPRESENTATIVE_ENVIRONMENT_REALIZATION_LIVE_FAILED: $representative_realization_output"
        fi
    else
        block_check 'REPRESENTATIVE_ENVIRONMENT_REALIZATION_VALIDATION_NOT_RUN: exact pinned dependencies are unavailable in the selected runtime'
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        equivalence_normalization_output=$("$PYTHON_BIN" -B \
            data_construction/tools/build_operator_equivalence_normalization.py \
            --validate-only 2>&1)
        equivalence_normalization_rc=$?
        if [ "$equivalence_normalization_rc" -eq 0 ]; then
            pass_check "OPERATOR_EQUIVALENCE_NORMALIZATION_LIVE: $equivalence_normalization_output"
        else
            fail_check "OPERATOR_EQUIVALENCE_NORMALIZATION_LIVE_FAILED: $equivalence_normalization_output"
        fi
    else
        block_check 'OPERATOR_EQUIVALENCE_NORMALIZATION_VALIDATION_NOT_RUN: exact pinned dependencies are unavailable in the selected runtime'
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        crossed_author_output=$("$PYTHON_BIN" -B \
            data_construction/tools/build_operator_equivalence_crossed_author_sensitivity.py \
            --validate-only 2>&1)
        crossed_author_rc=$?
        if [ "$crossed_author_rc" -eq 0 ]; then
            pass_check "OPERATOR_EQUIVALENCE_CROSSED_AUTHOR_SENSITIVITY_LIVE: $crossed_author_output"
        else
            fail_check "OPERATOR_EQUIVALENCE_CROSSED_AUTHOR_SENSITIVITY_LIVE_FAILED: $crossed_author_output"
        fi
    else
        block_check 'OPERATOR_EQUIVALENCE_CROSSED_AUTHOR_SENSITIVITY_VALIDATION_NOT_RUN: exact pinned dependencies are unavailable in the selected runtime'
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        equivalence_normalization_v0_2_output=$("$PYTHON_BIN" -B \
            data_construction/tools/build_operator_equivalence_normalization_v0_2.py \
            --validate-only 2>&1)
        equivalence_normalization_v0_2_rc=$?
        if [ "$equivalence_normalization_v0_2_rc" -eq 0 ]; then
            pass_check "OPERATOR_EQUIVALENCE_NORMALIZATION_V0_2_LIVE: $equivalence_normalization_v0_2_output"
        else
            fail_check "OPERATOR_EQUIVALENCE_NORMALIZATION_V0_2_LIVE_FAILED: $equivalence_normalization_v0_2_output"
        fi
    else
        block_check 'OPERATOR_EQUIVALENCE_NORMALIZATION_V0_2_VALIDATION_NOT_RUN: exact pinned dependencies are unavailable in the selected runtime'
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        targeted_reauthor_output=$("$PYTHON_BIN" -B \
            data_construction/tools/build_operator_equivalence_targeted_reauthor.py \
            --validate-only 2>&1)
        targeted_reauthor_rc=$?
        if [ "$targeted_reauthor_rc" -eq 0 ]; then
            pass_check "OPERATOR_EQUIVALENCE_TARGETED_REAUTHOR_LIVE: $targeted_reauthor_output"
        else
            fail_check "OPERATOR_EQUIVALENCE_TARGETED_REAUTHOR_LIVE_FAILED: $targeted_reauthor_output"
        fi
    else
        block_check 'OPERATOR_EQUIVALENCE_TARGETED_REAUTHOR_VALIDATION_NOT_RUN: exact pinned dependencies are unavailable in the selected runtime'
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        targeted_instrument_output=$("$PYTHON_BIN" -B \
            data_construction/tools/build_operator_equivalence_targeted_instrument_v0_2.py \
            --validate-only 2>&1)
        targeted_instrument_rc=$?
        if [ "$targeted_instrument_rc" -eq 0 ]; then
            pass_check "OPERATOR_EQUIVALENCE_TARGETED_INSTRUMENT_V0_2_LIVE: $targeted_instrument_output"
        else
            fail_check "OPERATOR_EQUIVALENCE_TARGETED_INSTRUMENT_V0_2_LIVE_FAILED: $targeted_instrument_output"
        fi
    else
        block_check 'OPERATOR_EQUIVALENCE_TARGETED_INSTRUMENT_V0_2_VALIDATION_NOT_RUN: exact pinned dependencies are unavailable in the selected runtime'
    fi

    narrowed_grounding_output=$("$PYTHON_BIN" -B \
        data_construction/tools/freeze_narrowed_grounding_plan_v0_1.py \
        --validate-only 2>&1)
    narrowed_grounding_rc=$?
    if [ "$narrowed_grounding_rc" -eq 0 ]; then
        pass_check "NARROWED_GROUNDING_PLAN_LIVE: $narrowed_grounding_output"
    else
        fail_check "NARROWED_GROUNDING_PLAN_LIVE_FAILED: $narrowed_grounding_output"
    fi

    if [ "$dependency_rc" -eq 0 ]; then
        grounding_runtime_output=$("$PYTHON_BIN" -B \
            data_construction/tools/narrowed_grounding_runtime_v0_1.py \
            --validate-only 2>&1)
        grounding_runtime_rc=$?
        if [ "$grounding_runtime_rc" -eq 0 ]; then
            pass_check "NARROWED_GROUNDING_RUNTIME_LIVE: $grounding_runtime_output"
        elif [ "$grounding_runtime_rc" -eq 2 ]; then
            block_check "NARROWED_GROUNDING_RUNTIME_SOURCE_UNAVAILABLE: $grounding_runtime_output"
        else
            fail_check "NARROWED_GROUNDING_RUNTIME_LIVE_FAILED: $grounding_runtime_output"
        fi
        grounding_results_output=$("$PYTHON_BIN" -B \
            data_construction/tools/narrowed_grounding_runtime_v0_1.py --validate-results 2>&1)
        grounding_results_rc=$?
        if [ "$grounding_results_rc" -eq 0 ]; then
            pass_check "NARROWED_GROUNDING_RESULTS_RECONSTRUCTED: $grounding_results_output"
        elif [ "$grounding_results_rc" -eq 2 ]; then
            block_check "NARROWED_GROUNDING_RESULTS_SOURCE_UNAVAILABLE: $grounding_results_output"
        else
            fail_check "NARROWED_GROUNDING_RESULTS_RECONSTRUCTION_FAILED: $grounding_results_output"
        fi
    else
        block_check 'NARROWED_GROUNDING_RUNTIME_VALIDATION_NOT_RUN: exact pinned dependencies unavailable'
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
        declared_unit_test_count=$("$PYTHON_BIN" -B -c 'import json; s = json.load(open("state/project_state.json", encoding="utf-8"))["preflight_status"]; print(s.get("expected_unit_test_count", s["unit_tests_passed"]))' 2>/dev/null || printf '%s' unknown)
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
