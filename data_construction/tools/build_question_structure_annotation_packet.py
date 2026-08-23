#!/usr/bin/env python3
"""Build a deterministic blind question-only structure-annotation packet."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_question_only_semantic_views as view_builder
from _common import (
    canonical_json_sha256,
    git_tracked_commit_identity,
    historical_output_collision_errors,
    implementation_artifact_set_sha256,
    iter_json_records,
    json_file_bytes,
    output_path_collision_errors,
    read_json,
    sha256_bytes,
    sha256_file,
    write_output_batch,
)


BUILDER_VERSION = "question_structure_annotation_packet_builder_v0_1"
PACKET_SCHEMA_VERSION = "question_structure_annotation_packet_payload_v0_1"
MANIFEST_SCHEMA_VERSION = "question_structure_annotation_packet_manifest_v0_1"
ANNOTATION_SCHEMA_VERSION = "question_structure_annotation_v0_1"
VIEW_SCHEMA_VERSION = "question_only_semantic_view_v0_1"
VIEW_MANIFEST_SCHEMA_VERSION = "question_only_semantic_view_manifest_v0_1"
VIEW_VISIBILITY = "question_only_no_environment_answer_or_proposals"
STUDY_PLAN_SCHEMA_VERSION = "question_structure_study_plan_v0_1"
CANONICALIZATION = "sorted_compact_json_utf8_sha256_v0_1"
RUBRIC_VERSION = "question_structure_open_coding_rubric_v0_1"
EXPECTED_VIEW_COUNT = 30
EXPECTED_BATCH_QUESTION_COUNT = 10
EXPECTED_REVIEWERS_PER_QUESTION = 2
HEX_DIGITS = frozenset("0123456789abcdef")
CANONICAL_QUESTIONS_PATH = Path("data_construction/pilot/questions.jsonl")
CANONICAL_SPLIT_MANIFEST_PATH = Path(
    "data_construction/manifests/split_manifest_v0_1.json"
)

VIEW_KEYS = {"schema_version", "visibility", "question_id", "question"}
VIEW_MANIFEST_KEYS = {
    "schema_version",
    "builder_version",
    "provenance",
    "views_artifact",
    "questions_artifact",
    "split_manifest_artifact",
    "allocation_contract",
    "record_hash_contract",
    "view_contract",
}
ARTIFACT_KEYS = {"repository_relative_path", "sha256"}
RECORD_ARTIFACT_KEYS = ARTIFACT_KEYS | {"record_count"}
RECORD_HASH_KEYS = {"question_id", "canonical_sha256"}
BATCH_KEYS = {
    "batch_id",
    "role",
    "committed_order_start",
    "committed_order_end",
    "question_ids",
    "expected_record_count",
}
STUDY_PLAN_KEYS = {
    "schema_version",
    "status",
    "decision_date",
    "decision_artifact",
    "source_questions",
    "truthfulness_contract",
    "phase_order",
    "phase_a0",
    "phase_a1",
    "phase_a2",
    "phase_b",
    "phase_c",
    "immediate_next_human_task",
}
PHASE_A0_KEYS = {
    "status",
    "hypothesis",
    "structural_hypothesis_under_test",
    "scope",
    "out_of_scope",
    "required_outputs",
    "shown_inputs",
    "reviewer_hidden_category_systems",
    "hidden_inputs",
    "gate",
}
PHASE_A0_GATE_KEYS = {
    "exact_input_allowlist_required",
    "prefilled_model_content_allowed",
    "reviewer_visible_semantic_enum_allowed",
    "raw_record_schema_validation_required",
    "layer_separation_validation_required",
    "hash_binding_required",
    "reviewer_attestation_required",
    "locked_free_observation_before_scaffold_attestation_required",
    "free_observation_lock_scope",
    "locked_free_observation_editable_after_scaffold_reveal",
    "stage_transition_machine_enforced_against_source_or_dom_inspection",
    "free_text_semantic_leakage_detection_claimed",
    "source_cue_check_may_claim_semantic_correctness_or_agreement",
    "raw_validation_may_claim_semantic_agreement",
}
PHASE_A1_KEYS = {
    "status",
    "hypothesis",
    "active_batch_id",
    "reviewer_count_per_question",
    "reviewer_contract",
    "open_coding_components",
    "reviewer_visible_enum_prohibition",
    "calibration_batches",
    "raw_collection_gate",
    "post_raw_collection_exact_task",
    "removed_non_executable_gates",
    "stopping_rules",
}
ANNOTATION_COMPONENTS = {
    "unconstrained_question_paraphrase",
    "semantic_skeleton",
    "information_obligations",
    "abstract_topology",
    "ambiguity",
    "alternative_topology_plans",
    "representation_assessment",
    "instrument_issues",
}
REQUIRED_SHOWN_INPUTS = [
    "opaque_question_id",
    "question_text",
    "pre_observation_prior_exposure_screen_that_blocks_ineligible_reviewers",
    "ten_question_unconstrained_free_observation_fields_before_scaffold",
    "single_batch_wide_lock_action_after_all_ten_observations_are_nonempty",
    "all_ten_free_observations_readonly_after_lock",
    "stage_two_free_text_answer_request_candidate_structure_required_information_unit_and_dependency_scaffolds_for_all_ten_displayed_by_the_normal_ui_only_after_batch_wide_lock",
    "stable_local_id_and_dependency_reference_controls_without_semantic_category_menu",
]
STAGE1_VISIBLE_INSTRUCTIONS = [
    "Answer the prior-exposure screen before writing any observation; an exposed reviewer must stop and notify the researcher.",
    "Use only the opaque question ID and question text shown in this packet; do not use external lookup or consult another annotator.",
    "Before any later instrument is shown, describe in your own words what each question is asking for; do not force the observation into named fields or labels.",
    "All ten free observations must be non-empty and are locked read-only together before the next stage is revealed.",
    "This self-contained file provides procedural UI staging, not adversarial blinding: do not inspect or alter page source, developer tools, or the DOM to expose stage two before locking.",
]
STAGE2_VISIBLE_INSTRUCTIONS = [
    "The free observations were locked before this open-coding scaffold was revealed; do not try to revise them after seeing the scaffold.",
    "Write answer request, candidate structure, required information units, obligations, and semantic operations as open descriptions; no closed semantic-label or executable-operator ontology is supplied.",
    "Distinguish a required information unit (a free description of an information kind, relation, or value requested by the wording) from an information obligation (a subgoal or proposition that must be established as true to answer, with only its required predecessors declared).",
    "Copy the smallest local exact case-sensitive question span that supports each observation, one cue per line; use the whole question only when genuinely all of its wording supports that observation. When no direct cue exists, leave cues empty and explain the implicit inference.",
    "Exact-substring checking establishes cue-localization integrity only; it is not evidence that the cue is semantically aligned or that the observation is correct.",
    "Declare only required depends_on edges; multiple roots, multiple sinks, and disconnected components are allowed, while declared edges must be acyclic and reference existing IDs.",
    "Choose complete only when the scaffold expresses the observation with no schema gaps and no instrument issues; incomplete_schema_gap may preserve only gap descriptions and issues without a forced triple.",
    "Raw annotations are not gold and cannot self-claim researcher approval; approval remains an unimplemented procedural manual registry/signoff gate outside this packet.",
]
FIELD_SYNTAX_HELP = [
    "IDs use letters or digits first, followed by letters, digits, underscore, dot, colon, or hyphen; examples such as u1, o1, and n1 are syntax examples only.",
    "For the unrelated synthetic text ‘Did Alpha open before Beta?’, ‘before’ is an exact cue while ‘Before’ is not; this demonstrates substring syntax, not a decomposition or answer.",
    "Enter depends_on, fulfills-obligation references, entry IDs, output IDs, gaps, interpretations, and cues one item per line without duplicates.",
]
REQUIRED_HIDDEN_INPUTS = {
    "table_id_title_section_schema_rows_cells_or_values",
    "environment_or_linked_document_identity_schema_capabilities_or_text",
    "candidate_operator_graphs",
    "model_proposals_assessments_or_rationales",
    "official_answers_spans_or_execution_traces",
    "weak_traces_or_answer_nodes",
    "historical_graphs_or_labels",
    "grounding_or_execution_graphs",
    "granularity_metrics",
    "other_annotator_or_adjudicated_outputs",
}
PROHIBITED_VISIBLE_ENUMS = {
    "closed_semantic_label_ontology",
    "closed_answer_type_enum",
    "closed_answer_cardinality_enum",
    "closed_candidate_structure_kind_enum",
    "closed_semantic_function_enum",
}
REVIEWER_HIDDEN_CATEGORY_SYSTEMS = PROHIBITED_VISIBLE_ENUMS | {"operator_vocabulary"}
ANNOTATION_KEYS = {
    "schema_version",
    "annotator_id",
    "batch_id",
    "question_id",
    "question",
    "question_view_sha256",
    "annotation_packet_payload_sha256",
    "completed_at",
    "prior_exposure_declared",
    "researcher_approval_self_claimed",
    "submission_status",
    "abstention_reason",
    "attestation",
    "unconstrained_question_paraphrase",
    "representation_assessment",
    "instrument_issues",
    "semantic_skeleton",
    "information_obligations",
    "abstract_topology",
    "ambiguity",
    "alternative_topology_plans",
    "notes",
    "gold_claimed",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--views",
        type=Path,
        default=Path("data_construction/pilot/question_only_semantic_views_v0_1.jsonl"),
    )
    parser.add_argument(
        "--views-manifest",
        type=Path,
        default=Path(
            "data_construction/pilot/question_only_semantic_views_manifest_v0_1.json"
        ),
    )
    parser.add_argument(
        "--study-plan",
        type=Path,
        default=Path("data_construction/pilot/question_structure_study_plan_v0_1.json"),
    )
    parser.add_argument("--batch-id", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data_construction/pilot/question_structure_review_packets/"
            "question_structure_calibration_batch_1_v0_1.html"
        ),
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=Path(
            "data_construction/pilot/question_structure_review_packets/"
            "question_structure_calibration_batch_1_v0_1_manifest.json"
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing packet artifacts only when their bytes differ",
    )
    return parser.parse_args()


def is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in HEX_DIGITS for character in value)
    )


def require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a trimmed non-empty string")
    return value


def require_sha256(value: Any, label: str) -> str:
    if not is_sha256(value):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def portable_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return f"<external-artifact>/{path.name}"


def safe_repository_path(value: Any, label: str) -> str:
    text = require_nonempty_string(value, label)
    path = Path(text)
    if (
        path.is_absolute()
        or text.startswith(("~", "/", "<external-artifact>/"))
        or "\\" in text
        or "\r" in text
        or "\n" in text
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"{label} is not a safe repository-relative path")
    return path.as_posix()


def exact_artifact(
    value: Any,
    label: str,
    *,
    record_count: int | None = None,
) -> tuple[str, str]:
    expected_keys = RECORD_ARTIFACT_KEYS if record_count is not None else ARTIFACT_KEYS
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise ValueError(f"{label} fields differ from the exact artifact contract")
    path = safe_repository_path(value.get("repository_relative_path"), f"{label}.path")
    digest = require_sha256(value.get("sha256"), f"{label}.sha256")
    if record_count is not None and value.get("record_count") != record_count:
        raise ValueError(f"{label}.record_count must be {record_count}")
    return path, digest


def live_artifact(
    project_root: Path,
    value: Any,
    label: str,
    *,
    record_count: int | None = None,
) -> Path:
    relative, digest = exact_artifact(value, label, record_count=record_count)
    path = project_root / relative
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} does not resolve to a regular live repository file")
    if sha256_file(path) != digest:
        raise ValueError(f"{label}.sha256 does not match the live repository file")
    return path


def validate_views(records: list[dict[str, Any]]) -> list[str]:
    if len(records) != EXPECTED_VIEW_COUNT:
        raise ValueError(
            f"views must contain exactly {EXPECTED_VIEW_COUNT} records, observed {len(records)}"
        )
    identifiers: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        label = f"views[{index}]"
        if set(record) != VIEW_KEYS:
            raise ValueError(f"{label} differs from the exact four-field allowlist")
        if (
            record.get("schema_version") != VIEW_SCHEMA_VERSION
            or record.get("visibility") != VIEW_VISIBILITY
        ):
            raise ValueError(f"{label} is not a blind question-only v0.1 view")
        question_id = require_nonempty_string(record.get("question_id"), f"{label}.question_id")
        require_nonempty_string(record.get("question"), f"{label}.question")
        if question_id in seen:
            raise ValueError(f"{label}.question_id is duplicated")
        seen.add(question_id)
        identifiers.append(question_id)
    return identifiers


def _git_commit_exists(project_root: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(project_root), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _git_blob_sha256(project_root: Path, commit: str, relative_path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "show", f"{commit}:{relative_path}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            f"views manifest implementation artifact is absent from recorded commit: {relative_path}"
        )
    return sha256_bytes(result.stdout)


def validate_views_manifest(
    manifest: Any,
    views_path: Path,
    views: list[dict[str, Any]],
    question_ids: list[str],
    project_root: Path,
) -> dict[str, Any]:
    if not isinstance(manifest, dict) or set(manifest) != VIEW_MANIFEST_KEYS:
        raise ValueError("views manifest fields differ from the exact v0.1 contract")
    if (
        manifest.get("schema_version") != VIEW_MANIFEST_SCHEMA_VERSION
        or manifest.get("builder_version") != "question_only_semantic_view_builder_v0_1"
    ):
        raise ValueError("views manifest version is unsupported")

    views_reference = manifest.get("views_artifact")
    expected_views_path = portable_path(views_path, project_root)
    if expected_views_path.startswith("<external-artifact>/"):
        raise ValueError("canonical question-only views must be inside the repository")
    observed_views_path, observed_views_sha256 = exact_artifact(
        views_reference, "views_manifest.views_artifact", record_count=EXPECTED_VIEW_COUNT
    )
    if observed_views_path != expected_views_path or observed_views_sha256 != sha256_file(views_path):
        raise ValueError("views manifest does not bind the live --views artifact")

    questions_path = live_artifact(
        project_root,
        manifest.get("questions_artifact"),
        "views_manifest.questions_artifact",
        record_count=EXPECTED_VIEW_COUNT,
    )
    split_path = live_artifact(
        project_root,
        manifest.get("split_manifest_artifact"),
        "views_manifest.split_manifest_artifact",
    )
    if questions_path.resolve() != (project_root / CANONICAL_QUESTIONS_PATH).resolve():
        raise ValueError("views manifest does not bind the canonical source questions")
    if split_path.resolve() != (project_root / CANONICAL_SPLIT_MANIFEST_PATH).resolve():
        raise ValueError("views manifest does not bind the canonical split manifest")
    nested_paths = [
        questions_path,
        split_path,
        project_root / view_builder.CANONICAL_HISTORICAL_MANIFEST_PATH,
        project_root / view_builder.CANONICAL_SOURCE_INVENTORY_PATH,
    ]
    nested_hashes = {path.resolve(): sha256_file(path) for path in nested_paths}
    source_questions = list(iter_json_records(questions_path))
    split_manifest = read_json(split_path)
    if not isinstance(split_manifest, dict):
        raise ValueError("canonical split manifest must be a JSON object")
    view_builder.validate_split_provenance(split_manifest, project_root)
    source_question_ids = view_builder.validate_questions(
        source_questions, questions_path, split_manifest
    )
    if source_question_ids != question_ids or view_builder.build_records(source_questions) != views:
        raise ValueError(
            "question-only views are not the exact ordered four-field projection of canonical questions"
        )
    if any(sha256_file(path) != nested_hashes[path.resolve()] for path in nested_paths):
        raise ValueError("a nested source/provenance artifact changed during view validation")

    allocation = manifest.get("allocation_contract")
    expected_allocation = {
        "dataset_role": "annotation_schema_pilot",
        "source_split": "dev",
        "question_count": EXPECTED_VIEW_COUNT,
        "release_eligible": True,
        "zero_overlap_verified": True,
        "override_used": False,
        "question_order_matches_split_manifest": True,
    }
    if allocation != expected_allocation:
        raise ValueError("views manifest allocation contract is not the exact safe pilot contract")

    record_contract = manifest.get("record_hash_contract")
    if not isinstance(record_contract, dict) or set(record_contract) != {
        "canonicalization",
        "ordered_question_ids_sha256",
        "ordered_record_hashes_sha256",
        "records",
    }:
        raise ValueError("views manifest record-hash fields differ from the exact contract")
    record_hashes = record_contract.get("records")
    expected_record_hashes = [
        {"question_id": record["question_id"], "canonical_sha256": canonical_json_sha256(record)}
        for record in views
    ]
    if (
        record_contract.get("canonicalization") != CANONICALIZATION
        or record_contract.get("ordered_question_ids_sha256")
        != canonical_json_sha256(question_ids)
        or record_contract.get("ordered_record_hashes_sha256")
        != canonical_json_sha256(expected_record_hashes)
        or record_hashes != expected_record_hashes
        or any(set(item) != RECORD_HASH_KEYS for item in record_hashes)
    ):
        raise ValueError("views manifest record hashes/order do not match the live views")

    view_contract = manifest.get("view_contract")
    if not isinstance(view_contract, dict) or set(view_contract) != {
        "allowed_fields",
        "visible_input_categories",
        "excluded_categories",
        "environment_exposed",
        "answer_or_execution_evidence_exposed",
        "proposal_or_historical_label_exposed",
        "other_annotator_output_exposed",
        "leakage_audit_status",
    }:
        raise ValueError("views manifest view contract fields differ from v0.1")
    if (
        view_contract.get("allowed_fields")
        != ["schema_version", "visibility", "question_id", "question"]
        or view_contract.get("visible_input_categories") != ["question_id", "question_text"]
        or view_contract.get("environment_exposed") is not False
        or view_contract.get("answer_or_execution_evidence_exposed") is not False
        or view_contract.get("proposal_or_historical_label_exposed") is not False
        or view_contract.get("other_annotator_output_exposed") is not False
        or view_contract.get("leakage_audit_status") != "pass_by_exact_projection"
    ):
        raise ValueError("views manifest does not attest the exact blind projection")

    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != {
        "code_commit",
        "implementation_artifacts",
        "implementation_artifact_set_sha256",
    }:
        raise ValueError("views manifest provenance fields differ from v0.1")
    code_commit = provenance.get("code_commit")
    if (
        not isinstance(code_commit, str)
        or not re.fullmatch(r"[0-9a-f]{40}", code_commit)
        or not _git_commit_exists(project_root, code_commit)
    ):
        raise ValueError("views manifest code commit is unavailable")
    implementation_artifacts = provenance.get("implementation_artifacts")
    if not isinstance(implementation_artifacts, list) or len(implementation_artifacts) != 3:
        raise ValueError("views manifest must bind exactly three implementation artifacts")
    expected_implementation_paths = {
        "data_construction/schemas/question_only_semantic_view_v0_1.json",
        "data_construction/tools/_common.py",
        "data_construction/tools/build_question_only_semantic_views.py",
    }
    if {
        reference.get("repository_relative_path")
        for reference in implementation_artifacts
        if isinstance(reference, dict)
    } != expected_implementation_paths:
        raise ValueError("views manifest implementation artifact allowlist is invalid")
    live_references: list[dict[str, str]] = []
    for index, reference in enumerate(implementation_artifacts):
        path = live_artifact(
            project_root, reference, f"views_manifest.provenance.implementation_artifacts[{index}]"
        )
        live_references.append(
            {
                "repository_relative_path": path.relative_to(project_root).as_posix(),
                "sha256": sha256_file(path),
            }
        )
        relative = path.relative_to(project_root).as_posix()
        if _git_blob_sha256(project_root, code_commit, relative) != sha256_file(path):
            raise ValueError(
                "views manifest implementation artifact differs from its recorded commit blob: "
                + relative
            )
    live_references.sort(key=lambda item: item["repository_relative_path"].encode("utf-8"))
    if implementation_artifacts != live_references:
        raise ValueError("views manifest implementation artifact order/hash is not canonical")
    if provenance.get("implementation_artifact_set_sha256") != canonical_json_sha256(
        live_references
    ):
        raise ValueError("views manifest implementation artifact-set hash is invalid")
    return {
        "questions_path": questions_path,
        "split_path": split_path,
        "questions_artifact": manifest["questions_artifact"],
    }


def validate_study_plan(
    plan: Any,
    batch_id: str,
    question_ids: list[str],
    questions_artifact: dict[str, Any],
) -> list[str]:
    if not isinstance(plan, dict) or set(plan) != STUDY_PLAN_KEYS:
        raise ValueError("study plan fields differ from the exact v0.1 contract")
    if plan.get("schema_version") != STUDY_PLAN_SCHEMA_VERSION:
        raise ValueError("study plan schema version is unsupported")
    if plan.get("status") != "phase_a0_instrument_contract_frozen_human_evidence_not_collected":
        raise ValueError("study plan has not frozen the phase-a0 instrument without human evidence")
    source = plan.get("source_questions")
    if not isinstance(source, dict) or set(source) != {
        "repository_relative_path",
        "sha256",
        "question_count",
        "order_contract",
    }:
        raise ValueError("study plan source_questions contract is malformed")
    if (
        source.get("repository_relative_path")
        != questions_artifact.get("repository_relative_path")
        or source.get("sha256") != questions_artifact.get("sha256")
        or source.get("question_count") != EXPECTED_VIEW_COUNT
        or source.get("order_contract") != "exact_committed_jsonl_order"
    ):
        raise ValueError("study plan does not bind the source questions behind the views")
    truth = plan.get("truthfulness_contract")
    if not isinstance(truth, dict) or (
        truth.get("human_annotation_record_count") != 0
        or truth.get("human_review_record_count") != 0
        or truth.get("gold_claimed") is not False
        or truth.get("semantic_confirmation_claimed") is not False
    ):
        raise ValueError("study plan truthfulness contract is not pre-human and non-gold")
    phase_a0 = plan.get("phase_a0")
    if not isinstance(phase_a0, dict) or set(phase_a0) != PHASE_A0_KEYS:
        raise ValueError("study plan phase_a0 fields differ from the exact frozen contract")
    if (
        phase_a0.get("status")
        != "raw_instrument_contract_frozen_packet_materialization_pending_or_complete"
    ):
        raise ValueError("study plan phase_a0 has not frozen the raw instrument contract")
    gate = phase_a0.get("gate")
    if not isinstance(gate, dict) or set(gate) != PHASE_A0_GATE_KEYS or any(
        gate.get(field) is not True
        for field in (
            "exact_input_allowlist_required",
            "raw_record_schema_validation_required",
            "layer_separation_validation_required",
            "hash_binding_required",
            "reviewer_attestation_required",
            "locked_free_observation_before_scaffold_attestation_required",
        )
    ) or any(
        gate.get(field) is not False
        for field in (
            "prefilled_model_content_allowed",
            "reviewer_visible_semantic_enum_allowed",
            "locked_free_observation_editable_after_scaffold_reveal",
            "stage_transition_machine_enforced_against_source_or_dom_inspection",
            "free_text_semantic_leakage_detection_claimed",
            "source_cue_check_may_claim_semantic_correctness_or_agreement",
            "raw_validation_may_claim_semantic_agreement",
        )
    ) or gate.get("free_observation_lock_scope") != (
        "single_html_normal_ui_batch_wide_lock_after_all_ten_nonempty_then_display_all_stage_two_scaffolds_procedural_not_adversarial_blinding"
    ):
        raise ValueError("study plan phase_a0 gate does not authorize a blank blind instrument")
    shown = phase_a0.get("shown_inputs")
    hidden = phase_a0.get("hidden_inputs")
    if shown != REQUIRED_SHOWN_INPUTS:
        raise ValueError("study plan phase_a0 staged shown-input contract has drifted")
    hidden_categories = phase_a0.get("reviewer_hidden_category_systems")
    if (
        not isinstance(hidden_categories, list)
        or any(not isinstance(value, str) for value in hidden_categories)
        or set(hidden_categories) != REVIEWER_HIDDEN_CATEGORY_SYSTEMS
    ):
        raise ValueError("study plan phase_a0 hidden category-system contract has drifted")
    if (
        not isinstance(hidden, list)
        or any(not isinstance(value, str) for value in hidden)
        or set(hidden) != REQUIRED_HIDDEN_INPUTS
    ):
        raise ValueError("study plan phase_a0 hidden-input contract has drifted")

    phase_a1 = plan.get("phase_a1")
    if not isinstance(phase_a1, dict) or set(phase_a1) != PHASE_A1_KEYS:
        raise ValueError("study plan phase_a1 fields differ from v0.1")
    if phase_a1.get("active_batch_id") != batch_id:
        raise ValueError("--batch-id is not the study plan's active calibration batch")
    if phase_a1.get("reviewer_count_per_question") != EXPECTED_REVIEWERS_PER_QUESTION:
        raise ValueError("study plan must require two independent reviewers per question")
    components = phase_a1.get("open_coding_components")
    if not isinstance(components, list) or set(components) != ANNOTATION_COMPONENTS:
        raise ValueError("study plan phase_a1 annotation components have drifted")
    prohibited = phase_a1.get("reviewer_visible_enum_prohibition")
    if not isinstance(prohibited, list) or set(prohibited) != PROHIBITED_VISIBLE_ENUMS:
        raise ValueError("study plan reviewer-visible enum prohibition has drifted")
    reviewer = phase_a1.get("reviewer_contract")
    if not isinstance(reviewer, dict) or set(reviewer) != {
        "real_human_required",
        "mutual_independence_required",
        "stable_pseudonymous_id_required",
        "researcher_approval_required",
        "researcher_approval_verification",
        "external_lookup_allowed",
        "reviewer_consultation_allowed",
        "prior_phase_b_artifact_exposure_allowed",
        "locked_free_observation_before_scaffold_attestation_required",
        "undeclared_prior_exposure_disposition",
    } or any(
        reviewer.get(field) is not True
        for field in (
            "real_human_required",
            "mutual_independence_required",
            "stable_pseudonymous_id_required",
            "researcher_approval_required",
            "locked_free_observation_before_scaffold_attestation_required",
        )
    ) or any(
        reviewer.get(field) is not False
        for field in (
            "external_lookup_allowed",
            "reviewer_consultation_allowed",
            "prior_phase_b_artifact_exposure_allowed",
        )
    ) or reviewer.get("researcher_approval_verification") != (
        "procedural_manual_sign_off_not_machine_executable_or_authenticatable_no_hash_bound_registry"
    ) or reviewer.get("undeclared_prior_exposure_disposition") != (
        "invalidate_and_exclude_affected_submission"
    ):
        raise ValueError("study plan reviewer contract is not the blind independent-human contract")
    raw_gate = phase_a1.get("raw_collection_gate")
    manual_signoff = raw_gate.get("procedural_manual_signoff") if isinstance(raw_gate, dict) else None
    if (
        not isinstance(raw_gate, dict)
        or raw_gate.get("required_representation_assessment_outcome") != "complete"
        or raw_gate.get("required_representation_assessment_schema_gap_descriptions") != []
        or raw_gate.get("required_instrument_issues") != []
        or raw_gate.get("required_attestation_values")
        != {"locked_free_observation_before_scaffold": True}
        or raw_gate.get("source_cue_check_scope")
        != "minimal_localization_integrity_only_not_semantic_correctness_agreement_or_cross_level_prediction"
        or raw_gate.get("semantic_agreement_pass_allowed") is not False
        or not isinstance(manual_signoff, dict)
        or manual_signoff.get("required") is not True
        or manual_signoff.get("machine_executable") is not False
        or manual_signoff.get("machine_authenticatable") is not False
    ):
        raise ValueError("study plan raw collection/manual-signoff gate has drifted")

    batches = phase_a1.get("calibration_batches")
    if not isinstance(batches, list) or len(batches) != 3:
        raise ValueError("study plan must contain three disjoint 10-question calibration batches")
    selected: list[str] | None = None
    concatenated: list[str] = []
    seen_batch_ids: set[str] = set()
    for index, batch in enumerate(batches):
        label = f"study_plan.phase_a1.calibration_batches[{index}]"
        if not isinstance(batch, dict) or set(batch) != BATCH_KEYS:
            raise ValueError(f"{label} fields differ from the exact batch contract")
        observed_batch_id = require_nonempty_string(batch.get("batch_id"), f"{label}.batch_id")
        ids = batch.get("question_ids")
        start = batch.get("committed_order_start")
        end = batch.get("committed_order_end")
        if observed_batch_id in seen_batch_ids:
            raise ValueError(f"{label}.batch_id is duplicated")
        seen_batch_ids.add(observed_batch_id)
        if (
            not isinstance(ids, list)
            or any(not isinstance(question_id, str) for question_id in ids)
            or len(ids) != EXPECTED_BATCH_QUESTION_COUNT
            or len(set(ids)) != len(ids)
            or start != index * EXPECTED_BATCH_QUESTION_COUNT + 1
            or end != (index + 1) * EXPECTED_BATCH_QUESTION_COUNT
            or ids != question_ids[start - 1 : end]
            or batch.get("expected_record_count")
            != EXPECTED_BATCH_QUESTION_COUNT * EXPECTED_REVIEWERS_PER_QUESTION
        ):
            raise ValueError(f"{label} does not match its exact committed view-order slice")
        concatenated.extend(ids)
        if observed_batch_id == batch_id:
            selected = ids
    if concatenated != question_ids or selected is None:
        raise ValueError("study plan calibration batches do not partition the 30 views")
    immediate = plan.get("immediate_next_human_task")
    if not isinstance(immediate, dict) or (
        immediate.get("batch_id") != batch_id
        or immediate.get("question_count") != EXPECTED_BATCH_QUESTION_COUNT
        or immediate.get("reviewer_count") != EXPECTED_REVIEWERS_PER_QUESTION
        or immediate.get("records_per_artifact") != EXPECTED_BATCH_QUESTION_COUNT
        or immediate.get("expected_raw_artifacts") != EXPECTED_REVIEWERS_PER_QUESTION
    ):
        raise ValueError("study plan immediate task does not match the selected active batch")
    return selected


def blank_annotation_form() -> dict[str, Any]:
    """Return schema-shaped, deliberately invalid blank content with no semantic proposal."""

    form = {
        "schema_version": ANNOTATION_SCHEMA_VERSION,
        "annotator_id": "",
        "batch_id": "",
        "question_id": "",
        "question": "",
        "question_view_sha256": "",
        "annotation_packet_payload_sha256": None,
        "completed_at": None,
        "prior_exposure_declared": False,
        "researcher_approval_self_claimed": False,
        "submission_status": None,
        "abstention_reason": None,
        "attestation": {
            "human_authored": False,
            "worked_independently": False,
            "used_only_packet_question_view": False,
            "did_not_use_answers_grounding_environment_or_proposals": False,
            "locked_free_observation_before_scaffold": False,
        },
        "unconstrained_question_paraphrase": None,
        "representation_assessment": None,
        "instrument_issues": [],
        "semantic_skeleton": {
            "answer_target": {
                "description": "",
                "source_cues": [],
                "implicit_rationale": "",
            },
            "answer_shape_description": "",
            "answer_shape_source_cues": [],
            "answer_shape_implicit_rationale": "",
            "candidate_structure": {
                "description": "",
                "source_cues": [],
                "implicit_rationale": "",
            },
            "required_information_units": [],
            "selection_requirement": None,
            "back_mapping_requirement": None,
        },
        "information_obligations": [],
        "abstract_topology": {"nodes": [], "entry_node_ids": [], "output_node_ids": []},
        "ambiguity": {"present": None, "description": None, "alternative_interpretations": []},
        "alternative_topology_plans": [],
        "notes": None,
        "gold_claimed": False,
    }
    if set(form) != ANNOTATION_KEYS:
        raise ValueError("internal blank form fields differ from the annotation contract")
    return form


def build_payload(
    views: list[dict[str, Any]],
    selected_question_ids: list[str],
    batch_id: str,
    annotation_schema_sha256: str,
) -> dict[str, Any]:
    by_id = {record["question_id"]: record for record in views}
    items = [
        {
            "question_view": by_id[question_id],
            "question_view_sha256": canonical_json_sha256(by_id[question_id]),
        }
        for question_id in selected_question_ids
    ]
    return {
        "schema_version": PACKET_SCHEMA_VERSION,
        "batch_id": batch_id,
        "reviewed_view": "blind_question_only_semantic_structure",
        "annotation_schema_version": ANNOTATION_SCHEMA_VERSION,
        "instrument_contract": {
            "rubric_version": RUBRIC_VERSION,
            "annotation_schema_sha256": annotation_schema_sha256,
            "stage1_visible_instructions": STAGE1_VISIBLE_INSTRUCTIONS,
            "stage2_visible_instructions": STAGE2_VISIBLE_INSTRUCTIONS,
            "stage2_field_syntax_help": FIELD_SYNTAX_HELP,
            "stage_transition_contract": (
                "all_ten_nonempty_then_normal_ui_readonly_lock_before_scaffold_display_procedural_attestation_not_adversarial_blinding"
            ),
            "closed_semantic_label_ontology_exposed": False,
            "prefilled_semantic_decomposition_exposed": False,
            "researcher_approval_authority": (
                "unimplemented_procedural_manual_registry_or_signoff_outside_raw_packet"
            ),
        },
        "blank_annotation_form": blank_annotation_form(),
        "items": items,
    }


def render_html(payload: dict[str, Any], payload_sha256: str) -> str:
    embedded_payload = (
        json.dumps(payload, ensure_ascii=False, allow_nan=False)
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    stage1_instruction_items = "".join(
        f"<li>{html.escape(value)}</li>"
        for value in payload["instrument_contract"]["stage1_visible_instructions"]
    )
    stage2_instruction_items = "".join(
        f"<li>{html.escape(value)}</li>"
        for value in payload["instrument_contract"]["stage2_visible_instructions"]
    )
    syntax_items = "".join(
        f"<li>{html.escape(value)}</li>"
        for value in payload["instrument_contract"]["stage2_field_syntax_help"]
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HybridQA blind free observation — {html.escape(payload['batch_id'])}</title>
<style>
:root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
body {{ max-width: 1050px; margin: 2rem auto; padding: 0 1rem 5rem; line-height: 1.5; }}
.notice {{ border-left: .35rem solid #6b46c1; padding: .8rem 1rem; background: color-mix(in srgb, Canvas 92%, #805ad5 8%); }}
.card, .unit {{ border: 1px solid #a0aec0; border-radius: .6rem; padding: 1rem; margin: 1.25rem 0; }}
.unit {{ margin: .7rem 0; border-style: dashed; }}
label {{ display: block; margin-top: .8rem; font-weight: 650; }}
input[type=text], select, textarea {{ box-sizing: border-box; font: inherit; width: 100%; }}
textarea {{ min-height: 5rem; }} .attestation label {{ font-weight: 500; }}
code {{ overflow-wrap: anywhere; }} button {{ padding: .55rem .8rem; margin: .35rem .2rem .35rem 0; font-weight: 650; }}
.example {{ background: color-mix(in srgb, Canvas 92%, #38a169 8%); padding: 1rem; }}
.error {{ color: #c53030; font-weight: 700; }} .hint {{ font-size: .92rem; color: color-mix(in srgb, CanvasText 75%, Canvas 25%); }}
[hidden] {{ display: none !important; }}
</style>
</head>
<body>
<h1>HybridQA 질문 자유 관찰</h1>
<section id="stage-1">
<p class="notice">첫 단계에서는 아래 질문 ID와 질문 텍스트만 읽고, 각 질문이 무엇을 요구하는지 제한 없이 자기 말로 기록하세요. 외부 자료·검색·다른 사람의 도움을 사용하지 마세요. 열 개 관찰을 모두 기록해 잠그기 전에는 다음 단계가 표시되지 않으며, 잠근 관찰은 이 세션에서 수정할 수 없습니다. 이 기록은 <strong>gold가 아닙니다</strong>.</p>
<ul>{stage1_instruction_items}</ul>
<label for="prior-exposure">관찰을 시작하기 전: 이 10개 질문의 정답·표/문서 환경·모델/역사 제안·후속 그래프를 이전에 본 적이 있습니까?</label>
<select id="prior-exposure"><option value="unanswered">선택하세요</option><option value="no">아니요 — 관찰 시작 가능</option><option value="yes">예 — 작성하지 말고 연구자에게 exclusion을 알림</option></select>
<div id="stage1-items"></div>
<button id="lock-observations" type="button">자유 관찰 잠금 후 다음 단계 표시</button>
<p id="stage1-status" class="hint"></p>
</section>
<section id="stage-2" hidden>
<h1>2단계: open-coding scaffold</h1>
<p class="notice">이 단계는 분해 필드를 제시하는 <strong>open-coding scaffold</strong>이며 완전히 비구조적인 관찰은 아닙니다. 어떤 answer type, cardinality, candidate kind, semantic-function 또는 executable-operator ontology도 제공하지 않습니다. 표·문서 환경, 정답, 모델 제안, 연산자 그래프, grounding 또는 실행 증거를 사용하지 마세요.</p>
<p><strong>배치:</strong> <code>{html.escape(payload['batch_id'])}</code><br><strong>payload SHA-256:</strong> <code>{html.escape(payload_sha256)}</code></p>
<section class="example"><h2>고정 2단계 rubric / instruction contract</h2><p><code>{html.escape(payload['instrument_contract']['rubric_version'])}</code></p><ul>{stage2_instruction_items}</ul><h3>필드 문법 도움 (완성 decomposition 예시 아님)</h3><ul>{syntax_items}</ul></section>
<label for="annotator-id">안정된 익명 annotator ID (이름·이메일 금지)</label>
<input id="annotator-id" type="text" required pattern="[A-Za-z0-9][A-Za-z0-9._-]{{2,127}}" maxlength="128" placeholder="reviewer-pseudonym" autocomplete="off">
<p class="hint">연구자 승인 여부는 이 raw 파일에서 본인이 입력하거나 주장할 수 없습니다. 별도 연구자 관리 registry/manifest만 승인 권한을 가집니다.</p>
<fieldset class="attestation"><legend>필수 절차 확인</legend>
<label><input type="checkbox" data-attestation="human_authored"> 실제 사람이 직접 작성했습니다.</label>
<label><input type="checkbox" data-attestation="worked_independently"> 다른 annotator와 상의하지 않고 독립적으로 작성했습니다.</label>
<label><input type="checkbox" data-attestation="used_only_packet_question_view"> 이 패킷의 질문 전용 view만 사용했습니다.</label>
<label><input type="checkbox" data-attestation="did_not_use_answers_grounding_environment_or_proposals"> 정답, 환경, grounding, 실행 정보 또는 모델 제안을 사용하지 않았습니다.</label>
<label><input id="locked-free-observation-attestation" type="checkbox" data-attestation="locked_free_observation_before_scaffold" disabled> 열 개 자유 관찰을 모두 잠근 뒤에 이 scaffold가 표시되었습니다.</label>
</fieldset>
<p id="crypto-status"></p>
<div id="items"></div>
<button id="download" type="button">hash-bound 원시 주석 JSON 다운로드</button>
</section>
<script>
'use strict';
const packet = {embedded_payload};
const packetPayloadSha256 = {json.dumps(payload_sha256)};
const stage1Root = document.getElementById('stage1-items');
const stage2 = document.getElementById('stage-2');
const root = document.getElementById('items');
const controls = [];
const freeObservationControls = [];
let freeObservationsLocked = false;
let lockedFreeObservationValues = [];
const idPattern = /^[A-Za-z0-9][A-Za-z0-9_.:-]*$/;
const cryptoReady = Boolean(globalThis.crypto && globalThis.crypto.subtle && globalThis.TextEncoder);
const downloadButton = document.getElementById('download'); const cryptoStatus = document.getElementById('crypto-status');
if (!cryptoReady) {{ cryptoStatus.className = 'error'; cryptoStatus.textContent = '이 browser/local-file context에는 Web Crypto SHA-256이 없어 export를 차단했습니다. Web Crypto를 지원하는 최신 browser의 안전한 local context에서 이 파일을 다시 여세요.'; downloadButton.disabled = true; }} else {{ cryptoStatus.textContent = 'Browser Web Crypto SHA-256 사용 가능: export 시 canonical annotation hash를 계산합니다.'; }}

function addText(parent, tag, value) {{ const element = document.createElement(tag); element.textContent = String(value); parent.appendChild(element); return element; }}
function canonicalJson(value) {{
  if (Array.isArray(value)) return '[' + value.map(canonicalJson).join(',') + ']';
  if (value !== null && typeof value === 'object') return '{{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonicalJson(value[key])).join(',') + '}}';
  return JSON.stringify(value);
}}
async function sha256Canonical(value) {{
  if (!cryptoReady) throw new Error('Web Crypto SHA-256을 사용할 수 없습니다.');
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonicalJson(value)));
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}}
function makeField(parent, labelText, multiline = false, hint = '') {{
  const label = document.createElement('label'); label.textContent = labelText;
  const control = document.createElement(multiline ? 'textarea' : 'input'); if (!multiline) control.type = 'text'; control.maxLength = 4096;
  label.appendChild(control); parent.appendChild(label); if (hint) addText(parent, 'p', hint).className = 'hint'; return control;
}}
function makeSelect(parent, labelText, values) {{
  const label = document.createElement('label'); label.textContent = labelText; const select = document.createElement('select');
  values.forEach(([value, text]) => {{ const option = document.createElement('option'); option.value = value; option.textContent = text; select.appendChild(option); }});
  label.appendChild(select); parent.appendChild(label); return select;
}}
function trimmed(control, label, required = true) {{ const value = control.value.trim(); if (required && !value) throw new Error(`${{label}}: 값이 필요합니다.`); if (value.length > 4096) throw new Error(`${{label}}: 4096자를 초과합니다.`); return value; }}
function lines(control, label) {{ const values = control.value.split(/\\r?\\n/).map(value => value.trim()).filter(Boolean); if (new Set(values).size !== values.length) throw new Error(`${{label}}: 중복 줄이 있습니다.`); values.forEach(value => {{ if (value.length > 4096) throw new Error(`${{label}}: 한 항목이 4096자를 초과합니다.`); }}); return values; }}
function identifier(control, label) {{ const value = trimmed(control, label); if (!idPattern.test(value) || value.length > 256) throw new Error(`${{label}}: 안전한 ID 형식이 아닙니다.`); return value; }}
function identifierLines(control, label) {{ const values = lines(control, label); values.forEach(value => {{ if (!idPattern.test(value) || value.length > 256) throw new Error(`${{label}}: ${{value}}는 안전한 ID가 아닙니다.`); }}); return values; }}
function sameSet(left, right) {{ return left.length === right.length && left.every(value => right.includes(value)); }}
function validateCueEvidence(question, cues, implicit, label) {{
  cues.forEach(cue => {{ if (cue.length > 1024) throw new Error(`${{label}}: cue가 1024자를 초과합니다.`); if (!question.includes(cue)) throw new Error(`${{label}}: cue “${{cue}}”는 질문의 정확한 case-sensitive substring이 아닙니다.`); }});
  if (implicit.length > 4096) throw new Error(`${{label}}: implicit rationale이 4096자를 초과합니다.`);
  if (cues.length && implicit) throw new Error(`${{label}}: 직접 cue가 있으면 implicit rationale을 비우세요.`);
  if (!cues.length && !implicit) throw new Error(`${{label}}: cue가 없으면 implicit rationale이 필요합니다.`);
  return {{source_cues: cues, implicit_rationale: cues.length ? null : implicit}};
}}
function cueEditor(parent, heading, descriptionLabel = '자유 설명') {{
  const box = document.createElement('section'); box.className = 'unit'; addText(box, 'h4', heading); parent.appendChild(box);
  const description = makeField(box, descriptionLabel, true); const cues = makeField(box, '최소·국소 exact source cues (한 줄에 하나)', true, '가능한 가장 작은 case-sensitive 질문 substring을 쓰세요. 전체 문장은 그 모든 표현이 실제로 뒷받침할 때만 사용합니다. 이 검사는 위치 무결성만 확인하며 의미 정답을 보증하지 않습니다.'); const implicit = makeField(box, 'cue가 없을 때 implicit rationale', true);
  return {{ value(question, label) {{ const descriptionValue = trimmed(description, `${{label}} description`); const evidence = validateCueEvidence(question, lines(cues, `${{label}} cues`), implicit.value.trim(), label); return {{description: descriptionValue, ...evidence}}; }} }};
}}
function removableUnit(holder, heading) {{ const box = document.createElement('section'); box.className = 'unit'; addText(box, 'h4', heading); const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = '이 항목 제거'; remove.addEventListener('click', () => box.remove()); box.appendChild(remove); holder.appendChild(box); return box; }}
function informationUnitList(parent) {{
  const title = 'Required information units (closed relation/attribute 분류 없음)'; addText(parent, 'h3', title); const holder = document.createElement('div'); parent.appendChild(holder); const rows = [];
  const add = document.createElement('button'); add.type = 'button'; add.textContent = 'Free information unit 추가'; add.addEventListener('click', () => {{
    const box = removableUnit(holder, 'Required information unit'); const id = makeField(box, 'unit_id'); const evidence = cueEditor(box, '관찰', '필요한 관계·속성·사실 등을 분류 없이 자유 설명'); rows.push({{box, id, evidence}});
  }}); parent.appendChild(add);
  return {{ value(question, label) {{ const values = rows.filter(row => row.box.isConnected).map((row, index) => ({{unit_id: identifier(row.id, `${{label}}[${{index}}].unit_id`), ...row.evidence.value(question, `${{label}}[${{index}}]`)}})); if (new Set(values.map(value => value.unit_id)).size !== values.length) throw new Error(`${{label}}: unit_id가 중복됩니다.`); return values; }} }};
}}
function optionalCue(parent, title) {{
  const enabled = document.createElement('input'); enabled.type = 'checkbox'; const label = document.createElement('label'); label.appendChild(enabled); label.append(' 해당 요구가 있음'); parent.appendChild(label); const editor = cueEditor(parent, title);
  return {{ value(question, path) {{ return enabled.checked ? editor.value(question, path) : null; }} }};
}}
function obligationList(parent) {{
  addText(parent, 'h3', 'Information obligations — 답을 위해 참으로 확립할 subgoal/proposition'); const holder = document.createElement('div'); parent.appendChild(holder); const rows = [];
  const addRow = () => {{ const box = removableUnit(holder, 'Obligation'); const id = makeField(box, 'obligation_id'); const description = makeField(box, '답을 위해 참으로 확립해야 하는 subgoal/proposition 자유 설명', true); const depends = makeField(box, '반드시 선행하는 obligation IDs (한 줄에 하나; 불명확하면 비움)', true); const cues = makeField(box, '최소·국소 exact source cues (한 줄에 하나)', true, '전체 질문은 그 모든 표현이 실제로 뒷받침할 때만 사용합니다. substring 검사는 위치 무결성만 확인합니다.'); const implicit = makeField(box, 'cue가 없을 때 implicit rationale', true); rows.push({{box,id,description,depends,cues,implicit}}); }};
  const add = document.createElement('button'); add.type = 'button'; add.textContent = 'Obligation 추가'; add.addEventListener('click', addRow); parent.appendChild(add); addRow();
  return {{ value(question, label) {{
    const values = rows.filter(row => row.box.isConnected).map((row,index) => {{ const evidence = validateCueEvidence(question, lines(row.cues, `${{label}}[${{index}}] cues`), row.implicit.value.trim(), `${{label}}[${{index}}]`); return {{obligation_id: identifier(row.id, `${{label}}[${{index}}].obligation_id`), description: trimmed(row.description, `${{label}}[${{index}}].description`), depends_on: identifierLines(row.depends, `${{label}}[${{index}}].depends_on`), ...evidence}}; }});
    if (!values.length) throw new Error(`${{label}}: 하나 이상 필요합니다.`); validateDependencyGraph(values.map(value => value.obligation_id), values.map(value => value.depends_on), label); return values;
  }} }};
}}
function validateDependencyGraph(ids, dependencies, label) {{
  if (new Set(ids).size !== ids.length) throw new Error(`${{label}}: ID가 중복됩니다.`); const known = new Set(ids);
  dependencies.forEach((deps,index) => deps.forEach(dep => {{ if (!known.has(dep)) throw new Error(`${{label}}: ${{ids[index]}}의 참조 ${{dep}}가 없습니다.`); if (dep === ids[index]) throw new Error(`${{label}}: self dependency가 있습니다.`); }}));
  const state = new Map(); const byId = new Map(ids.map((id,index) => [id, dependencies[index]]));
  function visit(id) {{ if (state.get(id) === 1) throw new Error(`${{label}}: declared depends_on edge에 cycle이 있습니다.`); if (state.get(id) === 2) return; state.set(id,1); byId.get(id).forEach(visit); state.set(id,2); }} ids.forEach(visit);
}}
function topologyEditor(parent, title) {{
  const section = document.createElement('section'); section.className = 'unit'; addText(section, 'h3', title); parent.appendChild(section); const holder = document.createElement('div'); section.appendChild(holder); const rows = [];
  const addRow = () => {{ const box = removableUnit(holder, 'Semantic operation node (free text)'); const id = makeField(box, 'node_id'); const operation = makeField(box, 'storage-neutral operation_description (자유 문장)', true); const depends = makeField(box, '반드시 선행하는 node IDs (한 줄에 하나)', true); const fulfills = makeField(box, '이 node가 충족하는 obligation IDs (한 줄에 하나)', true); const cues = makeField(box, '최소·국소 exact source cues (한 줄에 하나)', true, '전체 질문은 그 모든 표현이 실제로 뒷받침할 때만 사용합니다. substring 검사는 위치 무결성만 확인합니다.'); const implicit = makeField(box, 'cue가 없을 때 implicit rationale', true); rows.push({{box,id,operation,depends,fulfills,cues,implicit}}); }};
  const add = document.createElement('button'); add.type = 'button'; add.textContent = 'Free-text operation node 추가'; add.addEventListener('click', addRow); section.appendChild(add); addRow();
  const entries = makeField(section, 'entry node IDs (모든 root를 한 줄에 하나)', true); const outputs = makeField(section, 'output node IDs (모든 sink를 한 줄에 하나)', true);
  return {{ value(question, obligationIds, label) {{
    const nodes = rows.filter(row => row.box.isConnected).map((row,index) => {{ const evidence = validateCueEvidence(question, lines(row.cues, `${{label}}.nodes[${{index}}] cues`), row.implicit.value.trim(), `${{label}}.nodes[${{index}}]`); const fulfillsIds = identifierLines(row.fulfills, `${{label}}.nodes[${{index}}].fulfills`); return {{node_id: identifier(row.id, `${{label}}.nodes[${{index}}].node_id`), operation_description: trimmed(row.operation, `${{label}}.nodes[${{index}}].operation_description`), depends_on: identifierLines(row.depends, `${{label}}.nodes[${{index}}].depends_on`), fulfills_obligation_ids: fulfillsIds, ...evidence}}; }});
    if (!nodes.length) throw new Error(`${{label}}: node가 하나 이상 필요합니다.`); const ids = nodes.map(node => node.node_id); validateDependencyGraph(ids, nodes.map(node => node.depends_on), `${{label}}.nodes`); const obligationSet = new Set(obligationIds); nodes.forEach(node => {{ if (!node.fulfills_obligation_ids.length) throw new Error(`${{label}}: 모든 node는 하나 이상의 obligation을 충족해야 합니다.`); node.fulfills_obligation_ids.forEach(id => {{ if (!obligationSet.has(id)) throw new Error(`${{label}}: 없는 obligation ${{id}}를 참조합니다.`); }}); }}); const fulfilledSet = new Set(nodes.flatMap(node => node.fulfills_obligation_ids)); if (!sameSet([...fulfilledSet], obligationIds)) throw new Error(`${{label}}: 모든 obligation이 하나 이상의 node에 연결되어야 합니다.`);
    const entryIds = identifierLines(entries, `${{label}}.entry_node_ids`); const outputIds = identifierLines(outputs, `${{label}}.output_node_ids`); const roots = nodes.filter(node => !node.depends_on.length).map(node => node.node_id); const depended = new Set(nodes.flatMap(node => node.depends_on)); const sinks = nodes.filter(node => !depended.has(node.node_id)).map(node => node.node_id); if (!sameSet(entryIds, roots)) throw new Error(`${{label}}: entry IDs는 모든 root의 정확한 집합이어야 합니다.`); if (!sameSet(outputIds, sinks)) throw new Error(`${{label}}: output IDs는 모든 sink의 정확한 집합이어야 합니다.`); return {{nodes, entry_node_ids: entryIds, output_node_ids: outputIds}};
  }} }};
}}
function issueList(parent) {{
  addText(parent, 'h3', 'Instrument issues'); const holder = document.createElement('div'); parent.appendChild(holder); const rows = []; const add = document.createElement('button'); add.type = 'button'; add.textContent = 'Instrument issue 추가'; add.addEventListener('click', () => {{ const box = removableUnit(holder, 'Instrument issue'); const type = makeSelect(box, 'type', [['cannot_express','cannot_express'],['multiple_equally_valid_encodings','multiple_equally_valid_encodings'],['rubric_unclear','rubric_unclear'],['burden','burden'],['other','other']]); const severity = makeSelect(box, 'severity', [['minor','minor'],['major','major'],['critical','critical']]); const rationale = makeField(box, 'rationale', true); rows.push({{box,type,severity,rationale}}); }}); parent.appendChild(add); return {{ value(label) {{ return rows.filter(row => row.box.isConnected).map((row,index) => ({{type: row.type.value, severity: row.severity.value, rationale: trimmed(row.rationale, `${{label}}[${{index}}].rationale`)}})); }} }};
}}
function alternativeList(parent) {{
  addText(parent, 'h3', '조건부 대안 topology plans'); const holder = document.createElement('div'); parent.appendChild(holder); const rows = []; const add = document.createElement('button'); add.type = 'button'; add.textContent = '대안 plan 추가'; add.addEventListener('click', () => {{ const box = removableUnit(holder, 'Alternative plan'); const planId = makeField(box, 'plan_id'); const condition = makeField(box, '이 대안이 유효한 조건', true); const rationale = makeField(box, '대안인 이유', true); const topology = topologyEditor(box, 'Alternative free-text topology'); rows.push({{box,planId,condition,rationale,topology}}); }}); parent.appendChild(add); return {{ value(question, obligationIds, label) {{ const values = rows.filter(row => row.box.isConnected).map((row,index) => ({{plan_id: identifier(row.planId, `${{label}}[${{index}}].plan_id`), condition: trimmed(row.condition, `${{label}}[${{index}}].condition`), rationale: trimmed(row.rationale, `${{label}}[${{index}}].rationale`), topology: row.topology.value(question, obligationIds, `${{label}}[${{index}}].topology`)}})); if (new Set(values.map(value => value.plan_id)).size !== values.length) throw new Error(`${{label}}: plan_id가 중복됩니다.`); return values; }} }};
}}

packet.items.forEach((item, index) => {{
  const card = document.createElement('article'); card.className = 'card';
  addText(card, 'h2', `${{index + 1}}. ${{item.question_view.question_id}}`);
  addText(card, 'p', item.question_view.question);
  const paraphrase = makeField(card, '제한 없는 question paraphrase / 자유 관찰', true, '아직 다른 필드나 분류를 보지 않은 상태에서 자기 말로 기록하세요.');
  paraphrase.disabled = true;
  freeObservationControls.push({{item, paraphrase}}); stage1Root.appendChild(card);
}});

const priorExposureControl = document.getElementById('prior-exposure');
priorExposureControl.addEventListener('change', () => {{
  const eligible = priorExposureControl.value === 'no';
  freeObservationControls.forEach(control => {{
    if (!eligible) control.paraphrase.value = '';
    control.paraphrase.disabled = !eligible;
  }});
  if (priorExposureControl.value === 'yes') window.alert('사전 노출이 선언되었습니다. 관찰을 시작하지 말고 연구자에게 exclusion을 알리세요.');
}});

packet.items.forEach((item, index) => {{
  const card = document.createElement('article'); card.className = 'card';
  addText(card, 'h2', `${{index + 1}}. ${{item.question_view.question_id}}`);
  addText(card, 'p', item.question_view.question);
  addText(card, 'p', `question view SHA-256: ${{item.question_view_sha256}}`);
  const paraphrase = freeObservationControls[index].paraphrase;
  const submission = makeSelect(card, 'submission_status', [['unreviewed','선택하세요'],['annotated','annotated'],['abstained','abstained']]); const abstention = makeField(card, 'abstention reason (abstained일 때만)', true);
  const outcome = makeSelect(card, 'representation assessment', [['unreviewed','선택하세요'],['complete','complete'],['incomplete_schema_gap','incomplete_schema_gap'],['not_annotatable','not_annotatable']]); const assessmentRationale = makeField(card, 'assessment rationale', true); const gaps = makeField(card, 'schema gap descriptions (한 줄에 하나)', true);
  const issues = issueList(card); addText(card, 'h3', 'Reduced semantic skeleton — 모두 자유 문장'); const answerTarget = cueEditor(card, 'Answer target'); const answerShape = cueEditor(card, 'Answer shape / cardinality (free description)'); const candidates = cueEditor(card, 'Candidate structure (free description)'); const informationUnits = informationUnitList(card); const selection = optionalCue(card, 'Selection requirement'); const backMapping = optionalCue(card, 'Back-mapping requirement'); const obligations = obligationList(card); const topology = topologyEditor(card, 'Environment-independent abstract topology — operation names are free text');
  const ambiguityPresent = makeSelect(card, 'ambiguity present?', [['unreviewed','선택하세요'],['false','아니요'],['true','예']]); const ambiguityDescription = makeField(card, 'ambiguity description (예일 때)', true); const interpretations = makeField(card, 'alternative interpretations (한 줄에 하나; 예일 때)', true); const alternatives = alternativeList(card); const notes = makeField(card, '메모 (선택)', true);
  controls.push({{item, paraphrase, submission, abstention, outcome, assessmentRationale, gaps, issues, answerTarget, answerShape, candidates, informationUnits, selection, backMapping, obligations, topology, ambiguityPresent, ambiguityDescription, interpretations, alternatives, notes}}); root.appendChild(card);
}});

document.getElementById('lock-observations').addEventListener('click', () => {{
  const priorExposure = document.getElementById('prior-exposure').value; if (priorExposure === 'unanswered') {{ window.alert('관찰을 시작하기 전 prior exposure 질문에 답하세요.'); return; }} if (priorExposure === 'yes') {{ window.alert('사전 노출이 선언되었습니다. 관찰을 제출하지 말고 연구자에게 exclusion을 알리세요.'); return; }}
  try {{
    lockedFreeObservationValues = freeObservationControls.map((control, index) =>
      trimmed(control.paraphrase, `${{control.item.question_view.question_id}} 자유 관찰`)
    );
  }} catch (error) {{ window.alert(error.message); return; }}
  freeObservationControls.forEach(control => {{ control.paraphrase.readOnly = true; control.paraphrase.setAttribute('aria-readonly', 'true'); }});
  priorExposureControl.disabled = true;
  freeObservationsLocked = true;
  document.getElementById('locked-free-observation-attestation').checked = true;
  const lockButton = document.getElementById('lock-observations'); lockButton.disabled = true;
  document.getElementById('stage1-status').textContent = '열 개 자유 관찰이 잠겼습니다. 아래 2단계에서 raw annotation을 완료하세요.';
  stage2.hidden = false; stage2.scrollIntoView({{behavior: 'smooth', block: 'start'}});
}});

document.getElementById('download').addEventListener('click', async () => {{
  if (!freeObservationsLocked) {{ window.alert('열 개 자유 관찰을 먼저 잠그고 2단계를 표시하세요.'); return; }}
  if (freeObservationControls.some((control, index) => control.paraphrase.value.trim() !== lockedFreeObservationValues[index])) {{ window.alert('잠긴 자유 관찰 값이 변경되어 export를 차단했습니다. 패킷을 새로 열어 다시 작성하세요.'); return; }}
  const annotatorInput = document.getElementById('annotator-id'); const annotatorId = annotatorInput.value.trim();
  if (!annotatorInput.checkValidity() || annotatorId !== annotatorInput.value) {{ window.alert('이름·이메일이 아닌 3–128자의 안정된 익명 ID를 입력하세요.'); return; }}
  const priorExposure = document.getElementById('prior-exposure').value; if (priorExposure === 'unanswered') {{ window.alert('prior exposure 질문에 답하세요.'); return; }} if (priorExposure === 'yes') {{ window.alert('사전 노출이 선언되어 exposure-naive 제출을 만들 수 없습니다. 연구자에게 알려 별도 exclusion 기록을 남기세요.'); return; }}
  const attestations = [...document.querySelectorAll('[data-attestation]')];
  if (attestations.some(control => !control.checked)) {{ window.alert('모든 절차 확인에 동의해야 합니다. 해당하지 않으면 제출하지 마세요.'); return; }}
  if (controls.some(control => control.submission.value === 'unreviewed')) {{ window.alert('모든 질문의 submission status를 선택하세요.'); return; }}
  const completedAt = new Date().toISOString(); const output = [];
  try {{
    for (const control of controls) {{
      const annotated = control.submission.value === 'annotated'; const questionId = control.item.question_view.question_id; const question = control.item.question_view.question;
      const abstentionReason = trimmed(control.abstention, `${{questionId}} abstention reason`, !annotated); if (annotated && abstentionReason) throw new Error(`${{questionId}}: annotated이면 abstention reason을 비우세요.`);
      let assessment = null, instrumentIssues = [], semanticSkeleton = null, informationObligations = [], abstractTopology = null, ambiguity = null, alternativePlans = [];
      const freeObservation = lockedFreeObservationValues[controls.indexOf(control)];
      if (annotated) {{
        if (control.outcome.value === 'unreviewed') throw new Error(`${{questionId}}: representation assessment가 필요합니다.`); const gapValues = lines(control.gaps, `${{questionId}} schema gaps`); assessment = {{outcome: control.outcome.value, rationale: trimmed(control.assessmentRationale, `${{questionId}} assessment rationale`), schema_gap_descriptions: gapValues}}; instrumentIssues = control.issues.value(`${{questionId}} instrument issues`);
        if (assessment.outcome === 'complete' && (gapValues.length || instrumentIssues.length)) throw new Error(`${{questionId}}: complete이면 schema gaps와 instrument issues가 모두 비어야 합니다.`); if (assessment.outcome === 'incomplete_schema_gap' && (!gapValues.length || !instrumentIssues.some(issue => ['cannot_express','rubric_unclear'].includes(issue.type)))) throw new Error(`${{questionId}}: incomplete_schema_gap에는 gap과 cannot_express/rubric_unclear issue가 필요합니다.`); if (assessment.outcome === 'not_annotatable' && gapValues.length) throw new Error(`${{questionId}}: not_annotatable은 schema-gap 판정이 아니므로 gap 목록을 비우세요.`);
        if (assessment.outcome === 'complete') {{
          const answerTarget = control.answerTarget.value(question, `${{questionId}} answer target`); const answerShape = control.answerShape.value(question, `${{questionId}} answer shape`); const candidateStructure = control.candidates.value(question, `${{questionId}} candidates`); semanticSkeleton = {{answer_target: answerTarget, answer_shape_description: answerShape.description, answer_shape_source_cues: answerShape.source_cues, answer_shape_implicit_rationale: answerShape.implicit_rationale, candidate_structure: candidateStructure, required_information_units: control.informationUnits.value(question, `${{questionId}} information units`), selection_requirement: control.selection.value(question, `${{questionId}} selection`), back_mapping_requirement: control.backMapping.value(question, `${{questionId}} back mapping`)}};
          informationObligations = control.obligations.value(question, `${{questionId}} obligations`); const obligationIds = informationObligations.map(value => value.obligation_id); abstractTopology = control.topology.value(question, obligationIds, `${{questionId}} topology`); if (control.ambiguityPresent.value === 'unreviewed') throw new Error(`${{questionId}}: ambiguity 여부를 선택하세요.`); const present = control.ambiguityPresent.value === 'true'; const ambiguityText = trimmed(control.ambiguityDescription, `${{questionId}} ambiguity description`, present); const altInterpretations = lines(control.interpretations, `${{questionId}} alternative interpretations`); if (present && !altInterpretations.length) throw new Error(`${{questionId}}: ambiguity가 있으면 설명과 대안 해석이 필요합니다.`); if (!present && (ambiguityText || altInterpretations.length)) throw new Error(`${{questionId}}: ambiguity가 없으면 설명/대안 해석을 비우세요.`); ambiguity = {{present, description: present ? ambiguityText : null, alternative_interpretations: present ? altInterpretations : []}}; alternativePlans = control.alternatives.value(question, obligationIds, `${{questionId}} alternatives`);
        }}
      }}
      const annotation = {{
        schema_version: packet.annotation_schema_version,
        annotator_id: annotatorId,
        batch_id: packet.batch_id,
        question_id: questionId,
        question: control.item.question_view.question,
        question_view_sha256: control.item.question_view_sha256,
        annotation_packet_payload_sha256: packetPayloadSha256,
        completed_at: completedAt,
        prior_exposure_declared: false,
        researcher_approval_self_claimed: false,
        submission_status: control.submission.value,
        abstention_reason: annotated ? null : abstentionReason,
        attestation: Object.fromEntries(attestations.map(element => [element.dataset.attestation, true])),
        unconstrained_question_paraphrase: freeObservation,
        representation_assessment: assessment,
        instrument_issues: instrumentIssues,
        semantic_skeleton: semanticSkeleton,
        information_obligations: informationObligations,
        abstract_topology: abstractTopology,
        ambiguity,
        alternative_topology_plans: alternativePlans,
        notes: trimmed(control.notes, `${{questionId}} notes`, false) || null,
        gold_claimed: false,
      }};
      output.push({{annotation, annotation_sha256: await sha256Canonical(annotation)}});
    }}
  }} catch (error) {{ window.alert(error.message); return; }}
  const blob = new Blob([JSON.stringify(output, null, 2) + '\\n'], {{type: 'application/json'}}); const link = document.createElement('a');
  link.href = URL.createObjectURL(blob); link.download = `question_structure_annotations_${{packet.batch_id}}_${{annotatorId}}.json`; link.click(); URL.revokeObjectURL(link.href);
}});
</script>
</body>
</html>
"""


def historical_tree_collision_errors(outputs: dict[str, Path], project_root: Path) -> list[str]:
    errors: list[str] = []
    protected = (project_root / "historical").resolve()
    for label, path in outputs.items():
        try:
            path.resolve().relative_to(protected)
        except ValueError:
            continue
        errors.append(f"output {label!r} targets the read-only historical tree: {path.resolve()}")
    return errors


def implementation_paths(project_root: Path) -> list[Path]:
    return [
        project_root / "data_construction/schemas/question_only_semantic_view_v0_1.json",
        project_root / "data_construction/schemas/question_structure_annotation_v0_1.json",
        Path(__file__).with_name("_common.py"),
        Path(__file__).with_name("build_question_only_semantic_views.py"),
        Path(__file__),
    ]


def build_manifest(
    *,
    payload: dict[str, Any],
    payload_sha256: str,
    packet_bytes: bytes,
    batch_id: str,
    selected_ids: list[str],
    inputs: dict[str, Path],
    live_hashes: dict[str, str],
    output_path: Path,
    project_root: Path,
    code_commit: str,
    paths: list[Path],
) -> dict[str, Any]:
    implementation_artifacts = sorted(
        [
            {
                "repository_relative_path": path.resolve().relative_to(project_root).as_posix(),
                "sha256": sha256_file(path),
            }
            for path in paths
        ],
        key=lambda item: item["repository_relative_path"].encode("utf-8"),
    )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "builder_version": BUILDER_VERSION,
        "batch_id": batch_id,
        "question_count": len(selected_ids),
        "annotation_status": "packet_created_no_human_annotations",
        "human_annotations_created_by_builder": False,
        "packet_payload": {
            "schema_version": PACKET_SCHEMA_VERSION,
            "canonicalization": CANONICALIZATION,
            "sha256": payload_sha256,
            "reviewed_view": "blind_question_only_semantic_structure",
            "contains_only_selected_question_views_blank_form_and_instrument_contract": True,
            "instrument_contract_sha256": canonical_json_sha256(
                payload["instrument_contract"]
            ),
            "rubric_version": RUBRIC_VERSION,
        },
        "packet_artifact": {
            "repository_relative_path": portable_path(output_path, project_root),
            "sha256": sha256_bytes(packet_bytes),
        },
        "inputs": {
            label: {
                "repository_relative_path": portable_path(path, project_root),
                "sha256": live_hashes[label],
            }
            for label, path in inputs.items()
        },
        "selection": {
            "active_batch_id_verified": True,
            "exact_view_order_verified": True,
            "question_ids": selected_ids,
            "question_id_order_sha256": canonical_json_sha256(selected_ids),
            "reviewers_per_question_required": EXPECTED_REVIEWERS_PER_QUESTION,
        },
        "annotation_record_contract": {
            "schema_version": ANNOTATION_SCHEMA_VERSION,
            "wrapper_fields": ["annotation", "annotation_sha256"],
            "canonicalization": CANONICALIZATION,
            "submission_statuses": ["annotated", "abstained"],
            "representation_assessment_outcomes": [
                "complete",
                "incomplete_schema_gap",
                "not_annotatable",
            ],
            "gold_claimed": False,
            "prior_exposure_declared": False,
            "researcher_approval_self_claimed": False,
            "researcher_approval_authority": (
                "unimplemented_procedural_manual_registry_or_signoff_outside_raw_packet"
            ),
            "annotator_identity": "stable_pseudonymous_id",
            "annotator_authentication": "procedural_not_machine_verifiable",
            "annotations_included": 0,
        },
        "validation": {
            "exact_four_field_view_allowlist_verified": True,
            "view_manifest_hashes_and_order_verified": True,
            "study_plan_active_batch_verified": True,
            "later_layer_input_exposure": False,
            "prefilled_semantic_content": False,
            "closed_semantic_label_ontology_exposed": False,
            "schema_equivalent_client_validation_before_export": True,
            "web_crypto_sha256_required_for_export": True,
            "stage_transition_enforcement": (
                "normal_ui_and_procedural_attestation_not_server_enforced_or_adversarial"
            ),
            "raw_free_text_semantic_leakage_detection": False,
        },
        "provenance": {
            "code_commit": code_commit,
            "implementation_artifacts": implementation_artifacts,
            "implementation_artifact_set_sha256": implementation_artifact_set_sha256(
                project_root, paths
            ),
            "builder_does_not_claim_human_annotation": True,
        },
    }


def main() -> int:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[2]
    annotation_schema_path = (
        project_root / "data_construction/schemas/question_structure_annotation_v0_1.json"
    )
    view_schema_path = (
        project_root / "data_construction/schemas/question_only_semantic_view_v0_1.json"
    )
    inputs = {
        "views": args.views,
        "views_manifest": args.views_manifest,
        "study_plan": args.study_plan,
        "annotation_schema": annotation_schema_path,
        "view_schema": view_schema_path,
    }
    collision_inputs = {
        **inputs,
        "common_implementation": Path(__file__).with_name("_common.py"),
        "view_builder_implementation": Path(__file__).with_name(
            "build_question_only_semantic_views.py"
        ),
        "builder_implementation": Path(__file__),
        "source_questions": project_root / CANONICAL_QUESTIONS_PATH,
        "split_manifest": project_root / CANONICAL_SPLIT_MANIFEST_PATH,
        "historical_manifest": project_root
        / view_builder.CANONICAL_HISTORICAL_MANIFEST_PATH,
        "source_question_inventory": project_root
        / view_builder.CANONICAL_SOURCE_INVENTORY_PATH,
    }
    outputs = {"output": args.output, "manifest_output": args.manifest_output}
    collisions = output_path_collision_errors(collision_inputs, outputs)
    collisions.extend(historical_output_collision_errors(outputs, project_root))
    collisions.extend(historical_tree_collision_errors(outputs, project_root))
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    if args.output.suffix.lower() not in {".html", ".htm"}:
        print("--output must be an HTML path", file=sys.stderr)
        return 2
    if args.manifest_output.suffix.lower() != ".json":
        print("--manifest-output must be a JSON path", file=sys.stderr)
        return 2
    try:
        batch_id = require_nonempty_string(args.batch_id, "--batch-id")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}", batch_id):
            raise ValueError("--batch-id is not a safe identifier")
        for label, path in inputs.items():
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"{label} must be an existing regular non-symlink file")
        paths = implementation_paths(project_root)
        code_commit = git_tracked_commit_identity(
            project_root,
            [*paths, args.views, args.views_manifest, args.study_plan],
        )
        views = list(iter_json_records(args.views))
        question_ids = validate_views(views)
        views_manifest = read_json(args.views_manifest)
        manifest_bindings = validate_views_manifest(
            views_manifest, args.views, views, question_ids, project_root
        )
        study_plan = read_json(args.study_plan)
        selected_ids = validate_study_plan(
            study_plan,
            batch_id,
            question_ids,
            manifest_bindings["questions_artifact"],
        )
        annotation_schema = read_json(annotation_schema_path)
        if not isinstance(annotation_schema, dict) or (
            annotation_schema.get("$id") != "question_structure_annotation_v0_1.json"
            or set(annotation_schema.get("required", [])) != {"annotation", "annotation_sha256"}
        ):
            raise ValueError("annotation schema does not expose the expected raw wrapper")
        live_hashes = {label: sha256_file(path) for label, path in inputs.items()}
        payload = build_payload(
            views,
            selected_ids,
            batch_id,
            live_hashes["annotation_schema"],
        )
        payload_sha256 = canonical_json_sha256(payload)
        rendered = render_html(payload, payload_sha256)
        if any(sha256_file(path) != live_hashes[label] for label, path in inputs.items()):
            raise ValueError("an input artifact changed during packet construction")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"cannot build question-structure annotation packet: {exc}", file=sys.stderr)
        return 2

    packet_bytes = rendered.encode("utf-8")
    manifest = build_manifest(
        payload=payload,
        payload_sha256=payload_sha256,
        packet_bytes=packet_bytes,
        batch_id=batch_id,
        selected_ids=selected_ids,
        inputs=inputs,
        live_hashes=live_hashes,
        output_path=args.output,
        project_root=project_root,
        code_commit=code_commit,
        paths=paths,
    )
    manifest_bytes = json_file_bytes(manifest)
    try:
        write_status = write_output_batch(
            {
                "output": (args.output, packet_bytes),
                "manifest_output": (args.manifest_output, manifest_bytes),
            },
            overwrite=args.overwrite,
        )
    except (OSError, ValueError) as exc:
        print(f"cannot write question-structure annotation packet: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "builder_version": BUILDER_VERSION,
                "batch_id": batch_id,
                "questions": len(selected_ids),
                "packet_payload_sha256": payload_sha256,
                "human_annotations_created": 0,
                "output": args.output.as_posix(),
                "manifest_output": args.manifest_output.as_posix(),
                "write_status": write_status,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
