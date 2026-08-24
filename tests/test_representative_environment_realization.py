from __future__ import annotations

import copy
import hashlib
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction" / "tools"
sys.path.insert(0, str(TOOLS))

import _common
import _representative_environment_source as environment_source
import build_representative_environment_realization as builder


EXPECTED_SELECTION_ORDERED_SHA256 = (
    "5403debe2cbe9c7f55ded0a01b49d7c42bf03e53a71350efe269bbd3c0bdcb2e"
)
EXPECTED_SELECTION_SET_SHA256 = (
    "9b6e05650834871ce30acc1c2dfde18fc64910dcd238982f5d482f6a31e15680"
)
SELECTION_ARTIFACT_SHA256 = (
    "2600f22721216e0e804de88726e4fb6d8a9d99830e445cd278b1af8b383bbf2a"
)


def _recursive_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_recursive_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_recursive_keys(item) for item in value))
    return set()


def _recursive_values(value: object) -> list[object]:
    if isinstance(value, dict):
        return [item for child in value.values() for item in _recursive_values(child)]
    if isinstance(value, list):
        return [item for child in value for item in _recursive_values(child)]
    return [value]


def _property_schemas(value: object, property_name: str) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict) and isinstance(properties.get(property_name), dict):
            found.append(properties[property_name])
        for child in value.values():
            found.extend(_property_schemas(child, property_name))
    elif isinstance(value, list):
        for child in value:
            found.extend(_property_schemas(child, property_name))
    return found


def _semantic_graph(*, second_role: str = "COMPARE") -> dict[str, object]:
    return {
        "nodes": [
            {
                "node_id": "n1",
                "role": "ACQUIRE_PROPERTY",
                "other_role_description": None,
                "description": "Acquire the question-relevant property.",
                "source_cues": ["relevant property"],
                "implicit_rationale": None,
                "depends_on": [],
            },
            {
                "node_id": "n2",
                "role": second_role,
                "other_role_description": None,
                "description": "Produce the requested comparison or result.",
                "source_cues": ["requested result"],
                "implicit_rationale": None,
                "depends_on": ["n1"],
            },
        ],
        "entry_node_ids": ["n1"],
        "output_node_ids": ["n2"],
    }


def _scope_contract() -> dict[str, object]:
    return {
        "table_scope": "full_selected_question_table",
        "document_scope": "table_link_closure",
        "question_or_answer_guided_pruning": False,
        "oracle_document_selection": False,
        "truncation": "none",
        "external_retrieval": False,
        "dataset_provided_question_table_binding": True,
        "table_retrieval_evaluated": False,
        "full_table_link_closure_supplied": True,
    }


def _environment() -> dict[str, object]:
    return {
        "source_split": "dev",
        "table_id": "table_alpha",
        "title": "Synthetic table title",
        "section_title": "Synthetic section",
        "columns": [
            {"column_index": 0, "text": "Entity", "linked_document_ids": []},
            {
                "column_index": 1,
                "text": "Measured fact",
                "linked_document_ids": ["doc1"],
            },
        ],
        "rows": [
            {
                "row_index": 0,
                "cells": [
                    {
                        "column_index": 0,
                        "text": "Entity A",
                        "linked_document_ids": [],
                    },
                    {
                        "column_index": 1,
                        "text": "17 units",
                        "linked_document_ids": ["doc1"],
                    },
                ],
            }
        ],
        "linked_documents": [
            {"document_id": "doc1", "text": "Synthetic linked passage."}
        ],
        "scope_contract": _scope_contract(),
    }


def _view(*, include_alternative: bool = True) -> dict[str, object]:
    question_id = "q1"
    alternatives = (
        [
            {
                "alternative_id": "alt1",
                "reason": "The question admits a preserved alternative interpretation.",
                "graph": _semantic_graph(second_role="VERIFY"),
            }
        ]
        if include_alternative
        else []
    )
    payload = {
        "question_context": {
            "question": "Which entity has the requested property?",
            "question_view_sha256": "1" * 64,
        },
        "candidate_backbone_context": {
            "source_record_sha256": "2" * 64,
            "question_only_answer_spec": {
                "kind": "entity",
                "cardinality": "one",
                "description": "One entity.",
                "source_cues": ["Which entity"],
                "implicit_rationale": None,
            },
            "primary_graph": _semantic_graph(),
            "alternative_graphs": alternatives,
            "candidate_non_gold": True,
        },
        "environment": _environment(),
    }
    return {
        "schema_version": builder.VIEW_SCHEMA_VERSION,
        "view_id": f"representative_environment_view_v0_1:{question_id}",
        "run_id": builder.RUN_ID,
        "selection_id": builder.SELECTION_ID,
        "selection_index": 1,
        "question_id": question_id,
        "family_id": f"cbf_v0_1:{'3' * 64}",
        "contracted_signature_sha256": "4" * 64,
        "visibility": "question_candidate_backbone_full_table_and_table_link_closure_no_answer_trace_grounding_execution_or_operator_proposals",
        "payload": payload,
        "payload_sha256": _common.canonical_json_sha256(payload),
        "source_bindings": {
            "representative_selection": {
                "repository_relative_path": (
                    "data_construction/exploration/ai_question_structure_scale_v0_1/"
                    "candidate_backbone_library_v0_1/representative_selection_v0_1.json"
                ),
                "sha256": SELECTION_ARTIFACT_SHA256,
                "selected_question_count": 71,
                "selected_question_ids_ordered_sha256": EXPECTED_SELECTION_ORDERED_SHA256,
                "selected_question_ids_set_sha256": EXPECTED_SELECTION_SET_SHA256,
            },
            "semantic_backbone_records": {
                "repository_relative_path": (
                    "data_construction/exploration/ai_question_structure_scale_v0_1/"
                    "cumulative_n300_v0_1/records.jsonl"
                ),
                "sha256": "5" * 64,
            },
            "candidate_families": {
                "repository_relative_path": (
                    "data_construction/exploration/ai_question_structure_scale_v0_1/"
                    "candidate_backbone_library_v0_1/candidate_backbone_families_v0_1.jsonl"
                ),
                "sha256": "6" * 64,
            },
            "official_questions": {
                "source_id": "hybridqa_questions_and_code",
                "pinned_commit": "db22fda8c5951438fade3c69d75b350335ba93b3",
                "portable_path": "released_data/dev.json",
                "sha256": "424272b233735a70ed8ef5af4a615373d114f472168c686c4370d54c92d58ac1",
                "projection_allowlist": ["question_id", "question", "table_id"],
            },
            "table_file": {
                "source_id": "hybridqa_linked_tables_and_passages",
                "pinned_commit": "dc066e1a6d5281511d8b73a6107d5ad2824cc2b2",
                "portable_path": "tables_tok/table_alpha.json",
                "sha256": "7" * 64,
            },
            "request_file": {
                "source_id": "hybridqa_linked_tables_and_passages",
                "pinned_commit": "dc066e1a6d5281511d8b73a6107d5ad2824cc2b2",
                "portable_path": "request_tok/table_alpha.json",
                "sha256": "8" * 64,
            },
        },
        "evidence_boundary": {
            "evidence_class": "ai_exploratory_non_human_non_gold",
            "human_evidence_count": 0,
            "gold_claimed": False,
            "official_answer_annotation_in_view": False,
            "official_answer_or_trace_fields_in_view": False,
            "official_dev_blob_read_for_question_to_table_mapping": True,
            "answer_field_projected": False,
            "trace_or_reference_artifact_read": False,
            "official_trace_in_view": False,
            "historical_graph_in_view": False,
            "operator_proposal_in_view": False,
            "dataset_provided_question_table_binding": True,
            "table_retrieval_evaluated": False,
            "full_table_link_closure_supplied": True,
            "grounding_evaluated": False,
            "execution_evaluated": False,
            "answer_recovery_evaluated": False,
            "modeling_ready_claimed": False,
        },
    }


def _change(change_id: str = "change1") -> dict[str, object]:
    return {
        "change_id": change_id,
        "change_type": "revise_referent",
        "change_basis": "environment_disambiguation",
        "backbone_node_ids": ["n1"],
        "description": "The environment disambiguates the intended referent.",
    }


def _variant_assessment(variant_id: str, status: str) -> dict[str, object]:
    inadequate = status in {"partially_adequate", "inadequate"}
    return {
        "backbone_variant_id": variant_id,
        "status": status,
        "candidate_variant_adequate": (
            True if status == "adequate" else False if inadequate else None
        ),
        "environment_interpretation_effect": (
            "reveals_semantic_mismatch" if inadequate else "none"
        ),
        "required_changes": [_change()] if inadequate else [],
        "semantic_clarifications": [],
        "rationale": f"Synthetic {variant_id} adequacy rationale.",
    }


def _e1_record(view: dict[str, object]) -> dict[str, object]:
    alternatives = view["payload"]["candidate_backbone_context"]["alternative_graphs"]
    assessments = [_variant_assessment("primary", "inadequate")]
    if alternatives:
        assessments.append(_variant_assessment("alt1", "adequate"))
    else:
        assessments[0] = _variant_assessment("primary", "adequate")
    return {
        "schema_version": builder.ADEQUACY_SCHEMA_VERSION,
        "assessment_id": f"backbone_adequacy_v0_1:{view['question_id']}",
        "run_id": builder.RUN_ID,
        "evidence_class": "ai_exploratory_non_human_non_gold",
        "producer_partition": "e1_author_partition_01",
        "selection_id": builder.SELECTION_ID,
        "selection_index": view["selection_index"],
        "question_id": view["question_id"],
        "family_id": view["family_id"],
        "contracted_signature_sha256": view["contracted_signature_sha256"],
        "input_view_id": view["view_id"],
        "input_view_payload_sha256": view["payload_sha256"],
        "visibility": "question_candidate_backbone_and_environment_no_operator_realization_answer_trace_grounding_execution_or_prior_proposals",
        "input_delivery": {
            "view_fully_consumed": True,
            "completeness_status": "complete",
        },
        "author_prior_exposure_to_record_before_packet": "procedurally_attested_none",
        "global_nonexposure_machine_authenticated": False,
        "record_status": "complete",
        "overall_status": "adequate",
        "candidate_backbone_adequate": True,
        "variant_assessments": assessments,
        "additional_semantic_interpretations": [
            {
                "interpretation_id": "interpretation1",
                "description": "A preserved semantic interpretation was considered.",
                "related_backbone_variant_ids": [item["backbone_variant_id"] for item in assessments],
                "environment_resolves_interpretation": True,
                "contains_grounded_locator": False,
            }
        ],
        "rationale": "At least one frozen candidate variant is semantically adequate.",
        "operator_realization_seen": False,
        "downstream_status": copy.deepcopy(builder.E1_DOWNSTREAM_NOT_EVALUATED),
        "evidence_boundary": {
            "human_evidence_count": 0,
            "gold_claimed": False,
            "modeling_ready_claimed": False,
            "candidate_family_semantic_correctness_presupposed": False,
            "family_level_semantic_correctness_established": False,
            "official_answer_annotation_in_authoring_input": False,
            "official_trace_in_authoring_input": False,
            "historical_graph_in_authoring_input": False,
            "prior_operator_proposal_in_authoring_input": False,
            "formal_grounding_record_produced": False,
            "grounding_signal_evaluated": False,
            "external_execution_run": False,
            "execution_signal_evaluated": False,
            "answer_value_output_recorded": False,
            "answer_recovery_signal_evaluated": False,
            "latent_locator_or_answer_inference_machine_authenticated": False,
        },
        "limitations": ["Synthetic non-human exploratory fixture."],
    }


def _binding_slot(slot_id: str, modality: str) -> dict[str, object]:
    return {
        "slot_id": slot_id,
        "required_semantics": f"Synthetic input for {slot_id}.",
        "environment_modality": modality,
        "cardinality": "one",
        "grounding_status": "not_grounded_in_this_stage",
        "resolved_locator": None,
    }


def _classification(operator_id: str, roles: list[str]) -> dict[str, object]:
    is_extension = "environment_extension" in roles
    return {
        "operator_node_id": operator_id,
        "roles": roles,
        "extension_type": "linked_environment_access" if is_extension else None,
        "extension_description": (
            "Accesses evidence supplied by the selected environment."
            if is_extension
            else None
        ),
    }


def _operator_candidate(
    *,
    candidate_id: str = "candidate1",
    target_variant: str = "primary",
    coverage: str = "complete_for_target_variant",
    mapped_node: str | None = None,
) -> dict[str, object]:
    if coverage == "complete_for_target_variant":
        return {
            "candidate_id": candidate_id,
            "target_backbone_variant_id": target_variant,
            "coverage_status": coverage,
            "variation_axes": ["environment_access_path"],
            "distinguishing_assumptions": [],
            "binding_slots": [
                _binding_slot("slot1", "table_row_or_cell"),
                _binding_slot("slot2", "linked_document_text"),
            ],
            "graph": {
                "nodes": [
                    {
                        "node_id": "op1",
                        "record_local_label": "select relevant table value",
                        "operation_description": "Select the environment value needed by the question.",
                        "depends_on": [],
                        "input_slot_ids": ["slot1"],
                        "output_description": "Selected table evidence.",
                        "operator_boundary_rationale": "This is the table-access boundary.",
                        "label_is_cross_record_taxonomy_key": False,
                    },
                    {
                        "node_id": "op2",
                        "record_local_label": "read linked evidence",
                        "operation_description": "Read linked evidence associated with the selected value.",
                        "depends_on": ["op1"],
                        "input_slot_ids": ["slot2"],
                        "output_description": "Linked-document evidence.",
                        "operator_boundary_rationale": "This is an environment-only access extension.",
                        "label_is_cross_record_taxonomy_key": False,
                    },
                    {
                        "node_id": "op3",
                        "record_local_label": "produce requested result",
                        "operation_description": "Produce the requested result from the available evidence.",
                        "depends_on": ["op1", "op2"],
                        "input_slot_ids": [],
                        "output_description": "Requested result.",
                        "operator_boundary_rationale": "This realizes the final semantic obligation.",
                        "label_is_cross_record_taxonomy_key": False,
                    },
                ],
                "entry_node_ids": ["op1"],
                "output_node_ids": ["op3"],
            },
            "backbone_operator_mappings": [
                {
                    "mapping_id": "mapping1",
                    "backbone_node_ids": ["n1"],
                    "operator_node_ids": ["op1"],
                    "mapping_kind": "one_to_one",
                },
                {
                    "mapping_id": "mapping2",
                    "backbone_node_ids": ["n2"],
                    "operator_node_ids": ["op3"],
                    "mapping_kind": "one_to_one",
                },
            ],
            "operator_node_classifications": [
                _classification("op1", ["backbone_realization"]),
                _classification("op2", ["environment_extension"]),
                _classification("op3", ["backbone_realization"]),
            ],
            "unsupported_target_backbone_nodes": [],
            "limitations": [],
        }
    if coverage != "partial_for_target_variant" or mapped_node not in {"n1", "n2"}:
        raise ValueError("partial candidates require mapped_node n1 or n2")
    unsupported = "n2" if mapped_node == "n1" else "n1"
    roles = ["backbone_realization"]
    if mapped_node == "n1":
        roles.append("environment_extension")
    return {
        "candidate_id": candidate_id,
        "target_backbone_variant_id": target_variant,
        "coverage_status": coverage,
        "variation_axes": ["semantic_interpretation"],
        "distinguishing_assumptions": ["Only one semantic obligation is realized."],
        "binding_slots": [_binding_slot("slot1", "table_row_or_cell")],
        "graph": {
            "nodes": [
                {
                    "node_id": "op1",
                    "record_local_label": "partial environment operation",
                    "operation_description": "Realize one supported semantic obligation.",
                    "depends_on": [],
                    "input_slot_ids": ["slot1"],
                    "output_description": "Partial realization output.",
                    "operator_boundary_rationale": "Only the supported portion is represented.",
                    "label_is_cross_record_taxonomy_key": False,
                }
            ],
            "entry_node_ids": ["op1"],
            "output_node_ids": ["op1"],
        },
        "backbone_operator_mappings": [
            {
                "mapping_id": "mapping1",
                "backbone_node_ids": [mapped_node],
                "operator_node_ids": ["op1"],
                "mapping_kind": "one_to_one",
            }
        ],
        "operator_node_classifications": [_classification("op1", roles)],
        "unsupported_target_backbone_nodes": [
            {"node_id": unsupported, "reason": "This obligation remains unsupported."}
        ],
        "limitations": ["This is intentionally partial."],
    }


def _e2_evidence_boundary() -> dict[str, object]:
    return {
        "human_evidence_count": 0,
        "gold_claimed": False,
        "modeling_ready_claimed": False,
        "backbone_adequacy_content_in_authoring_input": False,
        "global_nonexposure_machine_authenticated": False,
        "official_answer_annotation_in_authoring_input": False,
        "official_trace_in_authoring_input": False,
        "historical_graph_in_authoring_input": False,
        "prior_operator_proposal_in_authoring_input": False,
        "formal_grounding_record_produced": False,
        "grounding_signal_evaluated": False,
        "external_execution_run": False,
        "execution_signal_evaluated": False,
        "answer_value_output_recorded": False,
        "answer_recovery_signal_evaluated": False,
        "latent_locator_or_answer_inference_machine_authenticated": False,
    }


def _e2_record(
    view: dict[str, object], assessment: dict[str, object]
) -> dict[str, object]:
    has_alternative = bool(
        view["payload"]["candidate_backbone_context"]["alternative_graphs"]
    )
    if has_alternative:
        candidates = [
            _operator_candidate(
                candidate_id="candidate1",
                target_variant="primary",
                coverage="partial_for_target_variant",
                mapped_node="n2",
            ),
            _operator_candidate(candidate_id="candidate2", target_variant="alt1"),
        ]
        results = [
            {
                "backbone_variant_id": "primary",
                "status": "partially_realized",
                "candidate_ids": ["candidate1"],
                "blocking_unsupported_node_ids": ["n1"],
                "reason": "The primary variant has only a partial realization.",
            },
            {
                "backbone_variant_id": "alt1",
                "status": "fully_realized",
                "candidate_ids": ["candidate2"],
                "blocking_unsupported_node_ids": [],
                "reason": "The alternative variant has a complete realization.",
            },
        ]
        preferred = "candidate2"
    else:
        candidates = [_operator_candidate()]
        results = [
            {
                "backbone_variant_id": "primary",
                "status": "fully_realized",
                "candidate_ids": ["candidate1"],
                "blocking_unsupported_node_ids": [],
                "reason": "The primary variant has a complete realization.",
            }
        ]
        preferred = "candidate1"
    return {
        "schema_version": builder.REALIZATION_SCHEMA_VERSION,
        "realization_id": f"open_operator_realization_v0_1:{view['question_id']}",
        "run_id": builder.RUN_ID,
        "evidence_class": "ai_exploratory_non_human_non_gold",
        "producer_partition": "e2_author_partition_01",
        "selection_id": builder.SELECTION_ID,
        "selection_index": view["selection_index"],
        "question_id": view["question_id"],
        "family_id": view["family_id"],
        "contracted_signature_sha256": view["contracted_signature_sha256"],
        "input_view_id": view["view_id"],
        "input_view_payload_sha256": view["payload_sha256"],
        "backbone_assessment_binding": {
            "binding_mode": "hash_only",
            "assessment_artifact_sha256": "9" * 64,
            "assessment_record_sha256": _common.canonical_json_sha256(assessment),
            "assessment_content_in_authoring_input": False,
        },
        "visibility": "question_candidate_backbone_and_environment_with_adequacy_hash_only_no_adequacy_content_answer_trace_grounding_execution_or_prior_proposals",
        "input_delivery": {
            "view_fully_consumed": True,
            "completeness_status": "complete",
        },
        "author_prior_exposure_to_record_before_packet": "procedurally_attested_none",
        "author_prior_exposure_to_backbone_adequacy": "procedurally_attested_none",
        "global_nonexposure_machine_authenticated": False,
        "record_status": "complete",
        "realization_status": "available",
        "authoring_contract": builder.open_operator_authoring_contract(),
        "realization_candidates": candidates,
        "variant_realization_results": results,
        "preferred_candidate_id": preferred,
        "preference_reason": "This candidate provides a complete realization.",
        "unresolved_issues": [],
        "downstream_status": copy.deepcopy(builder.E2_DOWNSTREAM_NOT_EVALUATED),
        "evidence_boundary": _e2_evidence_boundary(),
        "limitations": ["Synthetic non-human exploratory fixture."],
    }


def _e2_semantic_errors(
    record: dict[str, object],
    view: dict[str, object],
    assessment: dict[str, object],
) -> list[str]:
    parameters = inspect.signature(builder._validate_e2_semantics).parameters
    arguments: list[object] = [record, view, assessment, "9" * 64]
    if "e1_artifact_path" in parameters:
        arguments.append(Path("unused_e1_artifact.jsonl"))
    return builder._validate_e2_semantics(*arguments)


def _freeze_args(base: Path) -> object:
    e1_packets = [base / f"e1_packet_{index:02d}.jsonl" for index in range(1, 5)]
    e1_parts = [base / f"e1_part_{index:02d}.jsonl" for index in range(1, 5)]
    e2_packets = [base / f"e2_packet_{index:02d}.jsonl" for index in range(1, 5)]
    e2_parts = [base / f"e2_part_{index:02d}.jsonl" for index in range(1, 5)]
    return builder.parse_args(
        [
            "--freeze-plan",
            "--plan",
            str(base / "plan.json"),
            "--views-output",
            str(base / "views.jsonl"),
            "--views-manifest-output",
            str(base / "views_manifest.json"),
            "--routing-output",
            str(base / "routing.json"),
            "--e1-packets",
            *(str(path) for path in e1_packets),
            "--e1-parts",
            *(str(path) for path in e1_parts),
            "--e1-output",
            str(base / "e1.jsonl"),
            "--e1-bindings-output",
            str(base / "e1_bindings_for_e2.json"),
            "--e2-packets",
            *(str(path) for path in e2_packets),
            "--e2-parts",
            *(str(path) for path in e2_parts),
            "--e2-output",
            str(base / "e2.jsonl"),
            "--outcomes-output",
            str(base / "outcomes.jsonl"),
            "--checks-output",
            str(base / "checks.jsonl"),
            "--report-output",
            str(base / "report.md"),
            "--metrics-output",
            str(base / "metrics.json"),
            "--exposure-ledger-output",
            str(base / "exposure_ledger.json"),
            "--run-manifest-output",
            str(base / "run_manifest.json"),
        ]
    )


class RepresentativeEnvironmentSelectionAndSchemaTests(unittest.TestCase):
    def test_live_selection_is_exact_ordered_71_id_contract(self) -> None:
        selection = _common.read_json(builder.DEFAULT_SELECTION)
        question_ids = selection["selected_question_ids"]
        self.assertEqual(selection["selection_id"], builder.SELECTION_ID)
        self.assertEqual(selection["selected_question_count"], 71)
        self.assertEqual(selection["selected_family_count"], 30)
        self.assertEqual(len(question_ids), 71)
        self.assertEqual(len(set(question_ids)), 71)
        self.assertEqual(
            [item["selection_index"] for item in selection["selections"]],
            list(range(1, 72)),
        )
        self.assertEqual(
            [item["question_id"] for item in selection["selections"]], question_ids
        )
        self.assertEqual(
            _common.canonical_json_sha256(question_ids),
            EXPECTED_SELECTION_ORDERED_SHA256,
        )
        self.assertEqual(
            _common.canonical_string_set_sha256(question_ids),
            EXPECTED_SELECTION_SET_SHA256,
        )

    def test_all_four_schemas_are_draft_2020_12_and_locally_versioned(self) -> None:
        contracts = (
            (builder.DEFAULT_VIEW_SCHEMA, builder.VIEW_SCHEMA_VERSION),
            (builder.DEFAULT_ADEQUACY_SCHEMA, builder.ADEQUACY_SCHEMA_VERSION),
            (builder.DEFAULT_REALIZATION_SCHEMA, builder.REALIZATION_SCHEMA_VERSION),
            (builder.DEFAULT_OUTCOME_SCHEMA, "environment_realization_outcome_v0_2"),
        )
        for path, schema_version in contracts:
            with self.subTest(path=path.name):
                schema = _common.read_json(path)
                self.assertEqual(
                    schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
                )
                self.assertEqual(schema["$id"], path.name)
                self.assertEqual(
                    schema["properties"]["schema_version"]["const"], schema_version
                )
                self.assertFalse(schema["additionalProperties"])
                builder._schema_validator(path)

    def test_variant_result_conditions_are_attached_to_the_correct_definitions(self) -> None:
        realization_schema = _common.read_json(builder.DEFAULT_REALIZATION_SCHEMA)
        outcome_schema = _common.read_json(builder.DEFAULT_OUTCOME_SCHEMA)
        self.assertIn(
            "allOf", realization_schema["$defs"]["variant_realization_result"]
        )
        self.assertNotIn(
            "allOf",
            realization_schema["$defs"]["unsupported_target_backbone_node"],
        )
        self.assertIn("allOf", outcome_schema["$defs"]["variant_realization_result"])

    def test_positive_view_e1_e2_fixtures_are_schema_and_semantic_valid(self) -> None:
        view = _view()
        assessment = _e1_record(view)
        realization = _e2_record(view, assessment)
        fixtures = (
            (builder.DEFAULT_VIEW_SCHEMA, view, "view"),
            (builder.DEFAULT_ADEQUACY_SCHEMA, assessment, "e1"),
            (builder.DEFAULT_REALIZATION_SCHEMA, realization, "e2"),
        )
        for path, fixture, label in fixtures:
            with self.subTest(label=label):
                self.assertEqual(
                    builder._validation_errors(
                        builder._schema_validator(path), fixture, label
                    ),
                    [],
                )
        self.assertEqual(
            builder._environment_projection_errors(view["payload"]["environment"]), []
        )
        self.assertEqual(builder._validate_e1_semantics(assessment, view), [])
        self.assertEqual(_e2_semantic_errors(realization, view, assessment), [])

    def test_vocabulary_remains_unselected_and_only_e1_e2_are_evaluated(self) -> None:
        schemas = [
            _common.read_json(builder.DEFAULT_ADEQUACY_SCHEMA),
            _common.read_json(builder.DEFAULT_REALIZATION_SCHEMA),
            _common.read_json(builder.DEFAULT_OUTCOME_SCHEMA),
        ]
        serialized = json.dumps(schemas, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("operator_design/", serialized)
        self.assertNotIn("operator_vocabulary_v0_1", serialized)
        for property_name in (
            "operator_vocabulary_selected",
            "final_operator_vocabulary_selected",
        ):
            found = [
                item
                for schema in schemas
                for item in _property_schemas(schema, property_name)
            ]
            self.assertTrue(found, property_name)
            self.assertTrue(all(item.get("const") is False for item in found))
        for schema in schemas[:2]:
            for signal in ("grounding", "execution", "answer_recovery"):
                found = _property_schemas(schema, signal)
                self.assertTrue(found, signal)
                self.assertTrue(
                    all("not_evaluated" in _recursive_values(item) for item in found),
                    signal,
                )


class RepresentativeEnvironmentSourceProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.table = {
            "uid": "table_alpha",
            "title": "Pinned table title",
            "section_title": "Pinned section",
            "header": [
                ["Entity", ["doc_b", "doc_a"]],
                ["Measured fact", []],
            ],
            "data": [
                [["Entity A", ["doc_a"]], ["17 units", []]],
                [["Entity B", ["doc_b"]], ["23 units", []]],
            ],
            "answer": "FORBIDDEN_ANSWER",
            "trace": {"document": "doc_a"},
            "operator_proposal": {"kind": "FORBIDDEN_PROPOSAL"},
        }
        self.request = {
            "doc_a": "Pinned passage A.",
            "doc_b": "Pinned passage B.",
            "doc_unlinked": "UNLINKED_PASSAGE_MUST_NOT_APPEAR",
        }

    def test_projection_preserves_table_and_linked_facts_but_excludes_leakage(self) -> None:
        projected = environment_source.project_environment(
            "table_alpha", self.table, self.request
        )
        self.assertEqual(projected["scope_contract"], _scope_contract())
        values = _recursive_values(projected)
        for expected in (
            "Pinned table title",
            "Pinned section",
            "Entity",
            "Measured fact",
            "Entity A",
            "17 units",
            "Entity B",
            "23 units",
            "Pinned passage A.",
            "Pinned passage B.",
        ):
            self.assertIn(expected, values)
        self.assertEqual(
            [item["document_id"] for item in projected["linked_documents"]],
            ["doc_a", "doc_b"],
        )
        for forbidden_value in (
            "FORBIDDEN_ANSWER",
            "FORBIDDEN_PROPOSAL",
            "UNLINKED_PASSAGE_MUST_NOT_APPEAR",
        ):
            self.assertNotIn(forbidden_value, values)
        self.assertFalse(
            {"answer", "trace", "operator_proposal", "grounding", "execution"}
            & _recursive_keys(projected)
        )

    def test_duplicate_table_is_allowed_and_source_inventory_is_deduplicated(self) -> None:
        dev_records = [
            {
                "question_id": "q1",
                "question": "Question one?",
                "table_id": "table_alpha",
                "answer-text": "NEVER_PROJECT_THIS_1",
                "answer-node": ["trace_1"],
            },
            {
                "question_id": "q2",
                "question": "Question two?",
                "table_id": "table_alpha",
                "answer-text": "NEVER_PROJECT_THIS_2",
                "answer-node": ["trace_2"],
            },
        ]
        dev_bytes = _common.json_file_bytes(dev_records)
        table_bytes = _common.json_file_bytes(self.table)
        request_bytes = _common.json_file_bytes(self.request)
        contract = {
            "schema_version": "representative_environment_source_contract_v0_1",
            "question_source": {
                "pinned_commit": "1" * 40,
                "dev_artifact": {
                    "repository_relative_path": "released_data/dev.json",
                    "sha256": hashlib.sha256(dev_bytes).hexdigest(),
                    "record_count": 2,
                    "question_id_set_sha256": _common.canonical_string_set_sha256(
                        ["q1", "q2"]
                    ),
                },
            },
            "linked_environment_source": {"pinned_commit": "2" * 40},
        }
        verification = {
            "status": "verified",
            "machine_local_absolute_path_recorded": False,
        }
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            hybridqa = base / "hybridqa"
            wikitables = base / "wikitables"
            for relative in (
                "tables_tok/table_alpha.json",
                "request_tok/table_alpha.json",
            ):
                path = wikitables / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n", encoding="utf-8")

            def blob(_repository: Path, _commit: str, relative: str) -> bytes:
                return {
                    "released_data/dev.json": dev_bytes,
                    "tables_tok/table_alpha.json": table_bytes,
                    "request_tok/table_alpha.json": request_bytes,
                }[relative]

            with mock.patch.object(
                environment_source,
                "verify_source_cache",
                side_effect=[verification, verification],
            ), mock.patch.object(
                environment_source,
                "_cache_checkouts",
                return_value=(hybridqa, wikitables),
            ), mock.patch.object(environment_source, "_git_blob", side_effect=blob):
                bundle = environment_source.load_selected_environment_bundle(
                    base,
                    contract,
                    ["q1", "q2"],
                    {"q1": "Question one?", "q2": "Question two?"},
                    ROOT,
                )
        self.assertEqual(
            [item["question_id"] for item in bundle["questions"]], ["q1", "q2"]
        )
        self.assertEqual(len(bundle["environment_resources"]), 1)
        self.assertEqual(
            bundle["environment_resources"][0]["scope_contract"], _scope_contract()
        )
        paths = [
            item["repository_relative_path"]
            for item in bundle["selected_source_artifacts"]
        ]
        self.assertEqual(
            set(paths),
            {
                "released_data/dev.json",
                "tables_tok/table_alpha.json",
                "request_tok/table_alpha.json",
            },
        )
        self.assertEqual(len(paths), len(set(paths)))
        self.assertFalse(
            {"answer-text", "answer-node", "trace", "operator_proposal"}
            & _recursive_keys(bundle)
        )
        duplicate = {
            "source_id": "hybridqa_linked_tables_and_passages",
            "repository_relative_path": "tables_tok/table_alpha.json",
            "sha256": "a" * 64,
        }
        self.assertEqual(
            environment_source.deduplicate_source_artifacts([duplicate, duplicate]),
            [duplicate],
        )
        conflicting = {**duplicate, "sha256": "b" * 64}
        with self.assertRaises(environment_source.RepresentativeEnvironmentSourceError):
            environment_source.deduplicate_source_artifacts([duplicate, conflicting])


class RepresentativeEnvironmentGraphAndStageSemanticTests(unittest.TestCase):
    def test_environment_extension_operator_need_not_map_to_a_semantic_node(self) -> None:
        candidate = _operator_candidate()
        self.assertEqual(
            builder.validate_e1_e2_graph_contract(
                backbone_variants={"primary": _semantic_graph()},
                realization_candidates=[candidate],
            ),
            [],
        )
        mapped = {
            operator_id
            for mapping in candidate["backbone_operator_mappings"]
            for operator_id in mapping["operator_node_ids"]
        }
        self.assertNotIn("op2", mapped)
        self.assertEqual(
            candidate["operator_node_classifications"][1]["roles"],
            ["environment_extension"],
        )

    def test_candidate_mapping_members_are_an_exact_operator_partition(self) -> None:
        candidate = _operator_candidate()
        candidate["backbone_operator_mappings"][1]["operator_node_ids"] = ["op1", "op3"]
        candidate["backbone_operator_mappings"][1]["mapping_kind"] = "one_to_many"
        errors = builder.validate_e1_e2_graph_contract(
            backbone_variants={"primary": _semantic_graph()},
            realization_candidates=[candidate],
        )
        self.assertTrue(any("repeats an operator node" in error for error in errors))

    def test_duplicate_operator_classification_id_is_rejected(self) -> None:
        candidate = _operator_candidate()
        candidate["operator_node_classifications"][1]["operator_node_id"] = "op1"
        errors = builder.validate_e1_e2_graph_contract(
            backbone_variants={"primary": _semantic_graph()},
            realization_candidates=[candidate],
        )
        self.assertTrue(
            any("classify every operator exactly once" in error for error in errors)
        )

    def test_environment_extension_role_and_metadata_must_agree_both_directions(self) -> None:
        view = _view(include_alternative=False)
        assessment = _e1_record(view)
        realization_validator = builder._schema_validator(
            builder.DEFAULT_REALIZATION_SCHEMA
        )

        extension_without_metadata = _e2_record(view, assessment)
        extension_classification = extension_without_metadata[
            "realization_candidates"
        ][0]["operator_node_classifications"][1]
        extension_classification["extension_type"] = None
        extension_classification["extension_description"] = None
        self.assertTrue(
            builder._validation_errors(
                realization_validator,
                extension_without_metadata,
                "extension_without_metadata",
            )
        )
        self.assertTrue(
            any(
                "extension detail disagrees" in error
                for error in _e2_semantic_errors(
                    extension_without_metadata, view, assessment
                )
            )
        )

        metadata_without_extension = _e2_record(view, assessment)
        backbone_classification = metadata_without_extension[
            "realization_candidates"
        ][0]["operator_node_classifications"][0]
        backbone_classification["extension_type"] = "spurious_extension"
        backbone_classification[
            "extension_description"
        ] = "Metadata is present without the environment_extension role."
        self.assertTrue(
            builder._validation_errors(
                realization_validator,
                metadata_without_extension,
                "metadata_without_extension",
            )
        )
        self.assertTrue(
            any(
                "extension detail disagrees" in error
                for error in _e2_semantic_errors(
                    metadata_without_extension, view, assessment
                )
            )
        )

    def test_many_to_many_mapping_is_valid_when_membership_is_unambiguous(self) -> None:
        candidate = _operator_candidate()
        candidate["backbone_operator_mappings"] = [
            {
                "mapping_id": "mapping1",
                "backbone_node_ids": ["n1", "n2"],
                "operator_node_ids": ["op1", "op3"],
                "mapping_kind": "many_to_many",
            }
        ]
        self.assertEqual(
            builder.validate_e1_e2_graph_contract(
                backbone_variants={"primary": _semantic_graph()},
                realization_candidates=[candidate],
            ),
            [],
        )

    def test_dependency_direction_and_reachability_are_enforced(self) -> None:
        candidate = _operator_candidate()
        candidate["backbone_operator_mappings"][0]["backbone_node_ids"] = ["n2"]
        candidate["backbone_operator_mappings"][1]["backbone_node_ids"] = ["n1"]
        errors = builder.validate_e1_e2_graph_contract(
            backbone_variants={"primary": _semantic_graph()},
            realization_candidates=[candidate],
        )
        self.assertTrue(
            any("reverses or loses backbone dependency n1->n2" in error for error in errors)
        )
        broken_reference = _operator_candidate()
        broken_reference["graph"]["nodes"][1]["depends_on"] = ["op9"]
        errors = builder.validate_e1_e2_graph_contract(
            backbone_variants={"primary": _semantic_graph()},
            realization_candidates=[broken_reference],
        )
        self.assertTrue(any("op9" in error for error in errors))

    def test_partial_candidate_union_cannot_be_promoted_to_complete(self) -> None:
        view = _view(include_alternative=False)
        assessment = _e1_record(view)
        realization = _e2_record(view, assessment)
        realization["realization_candidates"] = [
            _operator_candidate(
                candidate_id="candidate1",
                coverage="partial_for_target_variant",
                mapped_node="n1",
            ),
            _operator_candidate(
                candidate_id="candidate2",
                coverage="partial_for_target_variant",
                mapped_node="n2",
            ),
        ]
        realization["variant_realization_results"] = [
            {
                "backbone_variant_id": "primary",
                "status": "fully_realized",
                "candidate_ids": ["candidate1", "candidate2"],
                "blocking_unsupported_node_ids": [],
                "reason": "Invalid union-based completeness claim.",
            }
        ]
        realization["preferred_candidate_id"] = "candidate1"
        self.assertEqual(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_REALIZATION_SCHEMA),
                realization,
                "candidate_union",
            ),
            [],
        )
        errors = _e2_semantic_errors(realization, view, assessment)
        self.assertTrue(any("lacks a complete candidate" in error for error in errors))

    def test_complementary_partial_candidates_use_blocker_intersection_not_union(self) -> None:
        view = _view(include_alternative=False)
        assessment = _e1_record(view)
        realization = _e2_record(view, assessment)
        realization["realization_status"] = "partial"
        realization["realization_candidates"] = [
            _operator_candidate(
                candidate_id="candidate1",
                coverage="partial_for_target_variant",
                mapped_node="n1",
            ),
            _operator_candidate(
                candidate_id="candidate2",
                coverage="partial_for_target_variant",
                mapped_node="n2",
            ),
        ]
        realization["variant_realization_results"] = [
            {
                "backbone_variant_id": "primary",
                "status": "partially_realized",
                "candidate_ids": ["candidate1", "candidate2"],
                "blocking_unsupported_node_ids": [],
                "reason": "The candidates have no blocker shared by every alternative.",
            }
        ]
        realization["preferred_candidate_id"] = "candidate1"
        realization["preference_reason"] = "A partial candidate is preferred provisionally."
        self.assertEqual(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_REALIZATION_SCHEMA),
                realization,
                "complementary_partial",
            ),
            [],
        )
        self.assertEqual(_e2_semantic_errors(realization, view, assessment), [])

        union_blockers = copy.deepcopy(realization)
        union_blockers["variant_realization_results"][0][
            "blocking_unsupported_node_ids"
        ] = ["n1", "n2"]
        errors = _e2_semantic_errors(union_blockers, view, assessment)
        self.assertTrue(
            any("disagrees with candidate coverage/blockers" in error for error in errors)
        )

    def test_alternative_variant_can_rescue_top_level_e1_and_e2(self) -> None:
        view = _view()
        assessment = _e1_record(view)
        realization = _e2_record(view, assessment)
        self.assertEqual(assessment["variant_assessments"][0]["status"], "inadequate")
        self.assertEqual(assessment["variant_assessments"][1]["status"], "adequate")
        self.assertEqual(assessment["overall_status"], "adequate")
        self.assertEqual(builder._validate_e1_semantics(assessment, view), [])
        self.assertEqual(
            realization["variant_realization_results"][0]["status"],
            "partially_realized",
        )
        self.assertEqual(
            realization["variant_realization_results"][1]["status"],
            "fully_realized",
        )
        self.assertEqual(realization["realization_status"], "available")
        self.assertEqual(_e2_semantic_errors(realization, view, assessment), [])

    def test_e1_reference_integrity_and_variant_aggregation_are_enforced(self) -> None:
        view = _view()
        assessment = _e1_record(view)
        bad_reference = copy.deepcopy(assessment)
        bad_reference["variant_assessments"][0]["required_changes"][0][
            "backbone_node_ids"
        ] = ["n9"]
        self.assertEqual(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_ADEQUACY_SCHEMA),
                bad_reference,
                "bad_reference",
            ),
            [],
        )
        self.assertTrue(
            any(
                "required change references an unknown node" in error
                for error in builder._validate_e1_semantics(bad_reference, view)
            )
        )
        bad_aggregation = copy.deepcopy(assessment)
        bad_aggregation["overall_status"] = "partially_adequate"
        bad_aggregation["candidate_backbone_adequate"] = False
        self.assertTrue(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_ADEQUACY_SCHEMA),
                bad_aggregation,
                "bad_aggregation",
            )
        )
        self.assertTrue(
            any(
                "does not follow the frozen variant aggregation" in error
                for error in builder._validate_e1_semantics(bad_aggregation, view)
            )
        )

    def test_e1_adequate_variant_cannot_reveal_a_semantic_mismatch(self) -> None:
        view = _view()
        assessment = _e1_record(view)
        assessment["variant_assessments"][1][
            "environment_interpretation_effect"
        ] = "reveals_semantic_mismatch"
        self.assertTrue(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_ADEQUACY_SCHEMA),
                assessment,
                "adequate_reveals_mismatch",
            )
        )
        self.assertTrue(
            any(
                "cannot be adequate" in error
                for error in builder._validate_e1_semantics(assessment, view)
            )
        )

    def test_prior_exposure_non_none_requires_indeterminate_status(self) -> None:
        view = _view()
        assessment = _e1_record(view)
        exposed_e1 = copy.deepcopy(assessment)
        exposed_e1["author_prior_exposure_to_record_before_packet"] = "known_exposed"
        self.assertTrue(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_ADEQUACY_SCHEMA),
                exposed_e1,
                "exposed_e1",
            )
        )

        realization = _e2_record(view, assessment)
        exposed_record = copy.deepcopy(realization)
        exposed_record["author_prior_exposure_to_record_before_packet"] = "unknown"
        self.assertTrue(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_REALIZATION_SCHEMA),
                exposed_record,
                "exposed_e2_record",
            )
        )

        exposed_to_adequacy = copy.deepcopy(realization)
        exposed_to_adequacy[
            "author_prior_exposure_to_backbone_adequacy"
        ] = "known_exposed"
        self.assertTrue(
            any(
                "permits only an indeterminate result" in error
                for error in _e2_semantic_errors(
                    exposed_to_adequacy, view, assessment
                )
            )
        )

    def test_e2_unavailable_with_truncated_input_is_schema_and_semantic_invalid(self) -> None:
        view = _view(include_alternative=False)
        assessment = _e1_record(view)
        realization = _e2_record(view, assessment)
        realization.update(
            {
                "input_delivery": {
                    "view_fully_consumed": False,
                    "completeness_status": "possibly_truncated",
                },
                "record_status": "unable_to_realize",
                "realization_status": "unavailable",
                "realization_candidates": [],
                "variant_realization_results": [
                    {
                        "backbone_variant_id": "primary",
                        "status": "unavailable",
                        "candidate_ids": [],
                        "blocking_unsupported_node_ids": ["n1", "n2"],
                        "reason": "No realization is claimed from a truncated input.",
                    }
                ],
                "preferred_candidate_id": None,
                "preference_reason": None,
            }
        )
        self.assertTrue(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_REALIZATION_SCHEMA),
                realization,
                "unavailable_truncated",
            )
        )
        self.assertTrue(
            any(
                "incomplete E2 input delivery requires an indeterminate result"
                in error
                for error in _e2_semantic_errors(realization, view, assessment)
            )
        )

    def test_e2_unavailable_with_complete_input_is_schema_and_semantic_valid(self) -> None:
        view = _view(include_alternative=False)
        assessment = _e1_record(view)
        realization = _e2_record(view, assessment)
        realization.update(
            {
                "input_delivery": {
                    "view_fully_consumed": True,
                    "completeness_status": "complete",
                },
                "record_status": "unable_to_realize",
                "realization_status": "unavailable",
                "realization_candidates": [],
                "variant_realization_results": [
                    {
                        "backbone_variant_id": "primary",
                        "status": "unavailable",
                        "candidate_ids": [],
                        "blocking_unsupported_node_ids": ["n1", "n2"],
                        "reason": "No environment-supported realization was found.",
                    }
                ],
                "preferred_candidate_id": None,
                "preference_reason": None,
            }
        )
        self.assertEqual(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_REALIZATION_SCHEMA),
                realization,
                "unavailable_complete",
            ),
            [],
        )
        self.assertEqual(_e2_semantic_errors(realization, view, assessment), [])

    def test_authoring_packets_bind_exact_fixed_output_identity(self) -> None:
        view = _view()
        assessment = _e1_record(view)
        partitions = []
        for index in range(1, 5):
            partitions.append(
                {
                    "routing_partition_id": f"routing_partition_{index:02d}",
                    "question_ids": ["q1"] if index == 1 else [],
                    "e1_producer_partition": f"e1_author_partition_{index:02d}",
                    "e2_producer_partition": f"e2_author_partition_{index:02d}",
                }
            )
        routing = {"partitions": partitions}

        e1_packet = builder.build_e1_authoring_packets([view], routing)[0][0]
        self.assertEqual(
            set(e1_packet),
            {
                "schema_version",
                "producer_partition",
                "view",
                "fixed_output_fields",
                "authoring_context_contract",
            },
        )
        self.assertEqual(
            e1_packet["fixed_output_fields"],
            builder._e1_fixed_output_fields(view, "e1_author_partition_01"),
        )
        self.assertTrue(e1_packet["authoring_context_contract"]["fresh_context_required"])
        self.assertFalse(
            e1_packet["authoring_context_contract"]["inherits_prior_conversation"]
        )

        assessment_sha = "a" * 64
        binding = {
            "binding_mode": "hash_only",
            "assessment_artifact_sha256": assessment_sha,
            "assessment_record_sha256": _common.canonical_json_sha256(assessment),
            "assessment_content_in_authoring_input": False,
        }
        e2_packet = builder.build_e2_authoring_packets(
            [view],
            [assessment],
            combined_e1_sha256=assessment_sha,
            routing=routing,
        )[0][0]
        self.assertEqual(
            e2_packet["fixed_output_fields"],
            builder._e2_fixed_output_fields(
                view, "e2_author_partition_01", binding
            ),
        )
        self.assertTrue(e2_packet["authoring_context_contract"]["fresh_context_required"])
        self.assertFalse(e2_packet["authoring_context_contract"]["inherits_e1_conversation"])
        self.assertFalse(
            e2_packet["authoring_context_contract"]["inherits_prior_conversation"]
        )

    def test_record_local_operator_labels_cannot_claim_a_final_vocabulary(self) -> None:
        candidate = _operator_candidate()
        self.assertTrue(
            all(
                node["label_is_cross_record_taxonomy_key"] is False
                for node in candidate["graph"]["nodes"]
            )
        )
        authoring_contract = builder.open_operator_authoring_contract()
        self.assertFalse(authoring_contract["operator_vocabulary_selected"])
        self.assertFalse(authoring_contract["final_operator_vocabulary_selected"])
        self.assertEqual(authoring_contract["notation_id"], builder.OPEN_NOTATION_ID)

    def test_e1_to_e2_sidecar_contains_hash_bindings_not_assessment_content(self) -> None:
        first = _e1_record(_view())
        first["rationale"] = "E1_PRIVATE_CONTENT_MUST_NOT_APPEAR"
        second = copy.deepcopy(first)
        second["assessment_id"] = "backbone_adequacy_v0_1:q2"
        second["question_id"] = "q2"
        second["rationale"] = "SECOND_PRIVATE_CONTENT_MUST_NOT_APPEAR"
        assessments = [first, second]
        combined_payload = _common.jsonl_file_bytes(assessments)
        sidecar = builder.build_e1_assessment_bindings_for_e2(
            assessments,
            combined_artifact_path=Path(
                "data_construction/exploration/ai_question_structure_scale_v0_1/"
                "representative_environment_realization_v0_1/stage_e1/"
                "backbone_adequacy_assessments.jsonl"
            ),
            combined_artifact_sha256=hashlib.sha256(combined_payload).hexdigest(),
        )
        self.assertEqual(
            sidecar["assessment_bindings"],
            [
                {
                    "assessment_id": record["assessment_id"],
                    "assessment_record_sha256": _common.canonical_json_sha256(record),
                }
                for record in assessments
            ],
        )
        values = _recursive_values(sidecar)
        self.assertNotIn("E1_PRIVATE_CONTENT_MUST_NOT_APPEAR", values)
        self.assertNotIn("SECOND_PRIVATE_CONTENT_MUST_NOT_APPEAR", values)
        self.assertFalse(
            {"question_id", "candidate_backbone_adequate", "rationale"}
            & _recursive_keys(sidecar)
        )


class RepresentativeEnvironmentOutcomeTests(unittest.TestCase):
    @staticmethod
    def _base_outcome() -> dict[str, object]:
        view = _view()
        assessment = _e1_record(view)
        realization = _e2_record(view, assessment)
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            args = _freeze_args(Path(temporary))
            args.views_output.write_bytes(_common.jsonl_file_bytes([view]))
            args.e1_output.write_bytes(_common.jsonl_file_bytes([assessment]))
            return builder.build_outcomes(
                args, [view], [assessment], [realization]
            )[0]

    def test_v0_2_rejects_grounding_and_execution_cross_field_contradictions(self) -> None:
        base = self._base_outcome()
        validator = builder._schema_validator(builder.DEFAULT_OUTCOME_SCHEMA)

        grounding_fail_claims_all_grounded = copy.deepcopy(base)
        grounding_fail_claims_all_grounded["grounding"].update(
            {
                "status": "fail",
                "all_required_inputs_grounded": True,
                "grounding_record_id": "grounding1",
                "grounded_item_count": 1,
                "ungrounded_item_count": 0,
                "failure_codes": ["grounding_failure"],
            }
        )

        execution_fail_claims_success = copy.deepcopy(base)
        execution_fail_claims_success["execution"].update(
            {
                "status": "fail",
                "executable": True,
                "execution_succeeded": True,
                "execution_record_id": "execution1",
                "failure_codes": ["runtime_failure"],
            }
        )

        success_claimed_non_executable = copy.deepcopy(base)
        success_claimed_non_executable["execution"].update(
            {
                "status": "partial",
                "executable": False,
                "execution_succeeded": True,
                "execution_record_id": "execution1",
            }
        )

        for label, outcome in (
            (
                "grounding_fail_claims_all_grounded",
                grounding_fail_claims_all_grounded,
            ),
            ("execution_fail_claims_success", execution_fail_claims_success),
            ("success_claimed_non_executable", success_claimed_non_executable),
        ):
            with self.subTest(label=label):
                self.assertTrue(builder._validation_errors(validator, outcome, label))

    def test_v0_2_rejects_duplicate_variant_ids_and_inconsistent_candidate_totals(self) -> None:
        base = self._base_outcome()
        validator = builder._schema_validator(builder.DEFAULT_OUTCOME_SCHEMA)

        duplicate_variant = copy.deepcopy(base)
        duplicate_results = duplicate_variant["environment_operator_realization"][
            "variant_realization_results"
        ]
        self.assertGreaterEqual(len(duplicate_results), 2)
        duplicate_results[1]["backbone_variant_id"] = duplicate_results[0][
            "backbone_variant_id"
        ]
        schema_errors = builder._validation_errors(
            validator, duplicate_variant, "duplicate_variant"
        )
        semantic_errors = builder._validate_outcome_semantics(duplicate_variant)
        self.assertTrue(schema_errors or semantic_errors)
        self.assertTrue(
            any("variant realization IDs are not unique" in error for error in semantic_errors)
        )

        wrong_total = copy.deepcopy(base)
        wrong_total_signal = wrong_total["environment_operator_realization"]
        wrong_total_signal["realization_candidate_count"] += 1
        self.assertTrue(
            any(
                "does not equal the variant-level sum" in error
                for error in builder._validate_outcome_semantics(wrong_total)
            )
        )

        zero_count_with_notation = copy.deepcopy(base)
        zero_signal = zero_count_with_notation["environment_operator_realization"]
        zero_signal["realization_candidate_count"] = 0
        for result in zero_signal["variant_realization_results"]:
            result["candidate_count"] = 0
        self.assertIsNotNone(zero_signal["operator_notation_id"])
        self.assertTrue(
            any(
                "notation presence disagrees" in error
                for error in builder._validate_outcome_semantics(
                    zero_count_with_notation
                )
            )
        )

        positive_count_without_notation = copy.deepcopy(base)
        positive_signal = positive_count_without_notation[
            "environment_operator_realization"
        ]
        self.assertGreater(positive_signal["realization_candidate_count"], 0)
        positive_signal["operator_notation_id"] = None
        self.assertTrue(
            any(
                "notation presence disagrees" in error
                for error in builder._validate_outcome_semantics(
                    positive_count_without_notation
                )
            )
        )

    def test_v0_2_rejects_answer_recovery_and_provenance_contradictions(self) -> None:
        base = self._base_outcome()
        validator = builder._schema_validator(builder.DEFAULT_OUTCOME_SCHEMA)
        valid_provenance = {
            "reference_answer_binding": {
                "artifact_role": "reference_answer",
                "repository_relative_path": "data/reference.json",
                "sha256": "b" * 64,
                "record_id": "reference1",
            },
            "reference_answer_evidence_class": "official_dataset_reference_non_gold",
            "reference_answer_is_gold": False,
            "comparator_id": "answer_comparator",
            "comparator_version": "comparator_v1",
        }

        not_evaluated_with_provenance = copy.deepcopy(base)
        not_evaluated_with_provenance["answer_recovery"]["comparison_provenance"].update(
            {
                "comparator_id": "answer_comparator",
                "comparator_version": "comparator_v1",
            }
        )

        false_recovery_with_exact_match = copy.deepcopy(base)
        false_recovery_with_exact_match["answer_recovery"].update(
            {
                "status": "partial",
                "answer_recovered": False,
                "answer_match_assessment": "exact_match",
                "answer_record_id": "answer1",
                "comparison_provenance": valid_provenance,
            }
        )

        true_recovery_with_mismatch = copy.deepcopy(base)
        true_recovery_with_mismatch["answer_recovery"].update(
            {
                "status": "partial",
                "answer_recovered": True,
                "answer_match_assessment": "mismatch",
                "answer_record_id": "answer1",
                "comparison_provenance": valid_provenance,
            }
        )

        scored_match_without_provenance = copy.deepcopy(base)
        scored_match_without_provenance["answer_recovery"].update(
            {
                "status": "partial",
                "answer_recovered": True,
                "answer_match_assessment": "exact_match",
                "answer_record_id": "answer1",
            }
        )

        for label, outcome in (
            ("not_evaluated_with_provenance", not_evaluated_with_provenance),
            ("false_recovery_with_exact_match", false_recovery_with_exact_match),
            ("true_recovery_with_mismatch", true_recovery_with_mismatch),
            ("scored_match_without_provenance", scored_match_without_provenance),
        ):
            with self.subTest(label=label):
                self.assertTrue(builder._validation_errors(validator, outcome, label))

    def test_v0_2_partial_or_failed_backbone_requires_change_codes(self) -> None:
        base = self._base_outcome()
        validator = builder._schema_validator(builder.DEFAULT_OUTCOME_SCHEMA)
        for status in ("partial", "fail"):
            with self.subTest(status=status):
                outcome = copy.deepcopy(base)
                outcome["backbone_adequacy"].update(
                    {
                        "status": status,
                        "candidate_backbone_adequate": False,
                        "required_change_codes": [],
                    }
                )
                self.assertTrue(
                    builder._validation_errors(
                        validator, outcome, f"empty_change_codes_{status}"
                    )
                )

    def test_v0_2_statuses_require_consistent_variant_results(self) -> None:
        view = _view()
        assessment = _e1_record(view)
        realization = _e2_record(view, assessment)
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            args = _freeze_args(Path(temporary))
            args.views_output.write_bytes(_common.jsonl_file_bytes([view]))
            args.e1_output.write_bytes(_common.jsonl_file_bytes([assessment]))
            base = builder.build_outcomes(
                args, [view], [assessment], [realization]
            )[0]

        pass_signal = copy.deepcopy(base["environment_operator_realization"])
        partial_signal = copy.deepcopy(pass_signal)
        partial_signal.update(
            {
                "status": "partial",
                "complete_realization_available": False,
                "variant_realization_results": [
                    {
                        "backbone_variant_id": "primary",
                        "status": "partially_realized",
                        "blocking_unsupported_node_ids": ["n1"],
                        "candidate_count": 1,
                    }
                ],
                "realization_candidate_count": 1,
            }
        )
        fail_signal = copy.deepcopy(pass_signal)
        fail_signal.update(
            {
                "status": "fail",
                "complete_realization_available": False,
                "operator_notation_id": None,
                "variant_realization_results": [
                    {
                        "backbone_variant_id": "primary",
                        "status": "unavailable",
                        "blocking_unsupported_node_ids": ["n1", "n2"],
                        "candidate_count": 0,
                    }
                ],
                "realization_candidate_count": 0,
            }
        )
        indeterminate_signal = copy.deepcopy(pass_signal)
        indeterminate_signal.update(
            {
                "status": "indeterminate",
                "complete_realization_available": None,
                "operator_notation_id": None,
                "variant_realization_results": [
                    {
                        "backbone_variant_id": "primary",
                        "status": "indeterminate",
                        "blocking_unsupported_node_ids": [],
                        "candidate_count": 0,
                    }
                ],
                "realization_candidate_count": 0,
            }
        )
        validator = builder._schema_validator(builder.DEFAULT_OUTCOME_SCHEMA)

        def signal_errors(signal: dict[str, object], label: str) -> list[str]:
            outcome = copy.deepcopy(base)
            outcome["environment_operator_realization"] = signal
            return builder._validation_errors(validator, outcome, label)

        for label, signal in (
            ("pass", pass_signal),
            ("partial", partial_signal),
            ("fail", fail_signal),
            ("indeterminate", indeterminate_signal),
        ):
            with self.subTest(valid=label):
                self.assertEqual(signal_errors(signal, label), [])

        invalid_pass = copy.deepcopy(partial_signal)
        invalid_pass["status"] = "pass"
        invalid_pass["complete_realization_available"] = True
        invalid_partial = copy.deepcopy(pass_signal)
        invalid_partial["status"] = "partial"
        invalid_partial["complete_realization_available"] = False
        invalid_fail = copy.deepcopy(fail_signal)
        invalid_fail["variant_realization_results"][0]["status"] = "indeterminate"
        invalid_fail["variant_realization_results"][0][
            "blocking_unsupported_node_ids"
        ] = []
        invalid_indeterminate = copy.deepcopy(indeterminate_signal)
        invalid_indeterminate["variant_realization_results"][0].update(
            {
                "status": "partially_realized",
                "blocking_unsupported_node_ids": ["n1"],
                "candidate_count": 1,
            }
        )
        invalid_indeterminate["realization_candidate_count"] = 1
        for label, signal in (
            ("pass_without_full_variant", invalid_pass),
            ("partial_with_full_variant", invalid_partial),
            ("fail_with_non_unavailable_variant", invalid_fail),
            ("indeterminate_with_partial_variant", invalid_indeterminate),
        ):
            with self.subTest(invalid=label):
                self.assertTrue(signal_errors(signal, label))

    def test_v0_2_outcome_preserves_variant_results_and_bounds_notes(self) -> None:
        view = _view()
        assessment = _e1_record(view)
        realization = _e2_record(view, assessment)
        first_issue = "x" * 4096
        realization["preferred_candidate_id"] = None
        realization["preference_reason"] = None
        realization["unresolved_issues"] = [first_issue, "y" * 4096]
        self.assertEqual(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_REALIZATION_SCHEMA),
                realization,
                "e2_for_outcome",
            ),
            [],
        )
        self.assertEqual(_e2_semantic_errors(realization, view, assessment), [])
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            args = _freeze_args(Path(temporary))
            args.views_output.write_bytes(_common.jsonl_file_bytes([view]))
            args.e1_output.write_bytes(_common.jsonl_file_bytes([assessment]))
            outcomes = builder.build_outcomes(
                args, [view], [assessment], [realization]
            )
        self.assertEqual(len(outcomes), 1)
        outcome = outcomes[0]
        self.assertEqual(outcome["schema_version"], "environment_realization_outcome_v0_2")
        signal = outcome["environment_operator_realization"]
        self.assertEqual(
            [item["backbone_variant_id"] for item in signal["variant_realization_results"]],
            ["primary", "alt1"],
        )
        self.assertEqual(signal["notes"], first_issue)
        self.assertEqual(len(signal["notes"]), 4096)
        self.assertNotIn("y", signal["notes"])
        self.assertFalse(signal["final_operator_vocabulary_selected"])
        self.assertEqual(
            builder._validation_errors(
                builder._schema_validator(builder.DEFAULT_OUTCOME_SCHEMA),
                outcome,
                "outcome",
            ),
            [],
        )

    def test_v0_1_outcome_contract_is_preserved_and_v0_2_is_separate(self) -> None:
        old_schema = builder.CONTRACTS / "environment_realization_outcome_schema_v0_1.json"
        self.assertTrue(old_schema.is_file())
        self.assertNotEqual(old_schema, builder.DEFAULT_OUTCOME_SCHEMA)
        self.assertEqual(
            _common.read_json(old_schema)["properties"]["schema_version"]["const"],
            "environment_realization_outcome_v0_1",
        )
        self.assertEqual(
            _common.read_json(builder.DEFAULT_OUTCOME_SCHEMA)["properties"][
                "schema_version"
            ]["const"],
            "environment_realization_outcome_v0_2",
        )


class RepresentativeEnvironmentValidateExistingTests(unittest.TestCase):
    @staticmethod
    def _view_paths(args: object) -> list[Path]:
        return [
            args.views_output,
            args.views_manifest_output,
            args.routing_output,
            *args.e1_packets,
        ]

    @staticmethod
    def _e1_paths(args: object) -> list[Path]:
        return [
            *args.e1_parts,
            args.e1_output,
            args.e1_bindings_output,
            *args.e2_packets,
        ]

    @staticmethod
    def _final_paths(args: object) -> list[Path]:
        return [
            *args.e2_parts,
            args.e2_output,
            args.outcomes_output,
            args.checks_output,
            args.report_output,
            args.metrics_output,
            args.exposure_ledger_output,
            args.run_manifest_output,
        ]

    @staticmethod
    def _write_all(paths: list[Path]) -> None:
        for index, path in enumerate(paths, 1):
            path.write_bytes(f"fixture-{index}\n".encode("utf-8"))

    def test_views_absent_rejects_complete_orphan_e1_or_final_bundle(self) -> None:
        for orphan_kind in ("e1", "final"):
            with self.subTest(orphan_kind=orphan_kind), tempfile.TemporaryDirectory(
                dir=ROOT
            ) as temporary:
                args = _freeze_args(Path(temporary))
                orphan_paths = (
                    self._e1_paths(args)
                    if orphan_kind == "e1"
                    else self._final_paths(args)
                )
                self._write_all(orphan_paths)
                with mock.patch.object(
                    builder, "validate_plan", return_value={}
                ), mock.patch.object(
                    builder, "verify_plan_freeze", return_value="p" * 40
                ):
                    with self.assertRaisesRegex(
                        builder.EnvironmentRealizationError,
                        "downstream artifacts exist without the environment view bundle",
                    ):
                        builder.validate_existing(args)

    def test_views_present_e1_absent_rejects_orphan_final_bundle(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            args = _freeze_args(Path(temporary))
            self._write_all(self._view_paths(args))
            self._write_all(self._final_paths(args))
            with mock.patch.object(
                builder, "validate_plan", return_value={}
            ), mock.patch.object(
                builder, "verify_plan_freeze", return_value="p" * 40
            ), mock.patch.object(
                builder,
                "load_materialized_views",
                return_value=([{"question_id": "q1"}], {}, {}),
            ), mock.patch.object(
                builder, "verify_view_freeze", return_value="v" * 40
            ):
                with self.assertRaisesRegex(
                    builder.EnvironmentRealizationError,
                    "E2/final artifacts exist without the complete E1 bundle",
                ):
                    builder.validate_existing(args)

    def test_complete_e1_always_verifies_freeze_before_reporting_final_absent(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            args = _freeze_args(Path(temporary))
            self._write_all(self._view_paths(args))
            self._write_all(self._e1_paths(args))
            with mock.patch.object(
                builder, "validate_plan", return_value={}
            ), mock.patch.object(
                builder, "verify_plan_freeze", return_value="p" * 40
            ), mock.patch.object(
                builder,
                "load_materialized_views",
                return_value=([{"question_id": "q1"}], {}, {}),
            ), mock.patch.object(
                builder, "verify_view_freeze", return_value="v" * 40
            ), mock.patch.object(
                builder,
                "load_e1_records",
                return_value=([{"question_id": "q1"}], "a" * 64),
            ), mock.patch.object(
                builder,
                "verify_e1_freeze",
                side_effect=builder.EnvironmentRealizationError(
                    "synthetic E1 freeze failure"
                ),
            ) as verify_e1:
                with self.assertRaisesRegex(
                    builder.EnvironmentRealizationError,
                    "synthetic E1 freeze failure",
                ):
                    builder.validate_existing(args)
                verify_e1.assert_called_once_with(args, "v" * 40)

    def test_presence_counts_a_broken_symlink_as_contamination(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            base = Path(temporary)
            broken = base / "broken.jsonl"
            broken.symlink_to(base / "does_not_exist.jsonl")
            self.assertFalse(broken.exists())
            self.assertTrue(broken.is_symlink())
            self.assertEqual(builder._presence([broken]), (False, True))


class RepresentativeEnvironmentFreezeAndWriteTests(unittest.TestCase):
    def test_freeze_plan_uses_metadata_only_and_never_calls_raw_source_loader(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            args = builder.parse_args(["--freeze-plan"])
            synthetic_outputs = {
                "environment_views": Path(temporary) / "views.jsonl",
                "e1_assessment_bindings_for_e2": Path(temporary) / "bindings.json",
                "metrics": Path(temporary) / "metrics.json",
                "environment_exposure_ledger": Path(temporary) / "exposure.json",
            }
            with mock.patch.object(
                builder, "git_tracked_commit_identity", return_value="a" * 40
            ), mock.patch.object(
                builder, "_validate_paths"
            ), mock.patch.object(
                builder, "_planned_outputs", return_value=synthetic_outputs
            ), mock.patch.object(
                builder.environment_source,
                "load_selected_environment_bundle",
                side_effect=AssertionError("freeze touched raw environment source"),
            ) as raw_loader:
                plan = builder.build_freeze_plan(args)
        raw_loader.assert_not_called()
        self.assertEqual(plan["expected_result"]["selected_question_count"], 71)
        self.assertEqual(
            plan["expected_result"]["selected_question_ids_ordered_sha256"],
            EXPECTED_SELECTION_ORDERED_SHA256,
        )
        self.assertFalse(plan["stage_contract"]["operator_vocabulary_selected"])
        self.assertIn("e1_assessment_bindings_for_e2", plan["planned_outputs"])
        self.assertIn("metrics", plan["planned_outputs"])
        self.assertIn("environment_exposure_ledger", plan["planned_outputs"])

    def test_view_freeze_detects_post_commit_byte_tampering(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            args = _freeze_args(Path(temporary))
            prerequisite_paths = [
                args.views_output,
                args.views_manifest_output,
                args.routing_output,
                *args.e1_packets,
            ]
            for index, path in enumerate(prerequisite_paths, 1):
                path.write_bytes(f"committed-{index}\n".encode("utf-8"))
            committed = {
                builder._relative(path): path.read_bytes() for path in prerequisite_paths
            }

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
                if "merge-base" in command:
                    return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")
                if "show" in command:
                    relative = command[-1].split(":", 1)[1]
                    return subprocess.CompletedProcess(
                        command, 0, stdout=committed[relative], stderr=b""
                    )
                raise AssertionError(f"unexpected git command: {command}")

            with mock.patch.object(
                builder, "_latest_artifact_commit", return_value="c" * 40
            ), mock.patch.object(
                builder.subprocess, "run", side_effect=fake_run
            ), mock.patch.object(builder, "_commit_path_absent"):
                self.assertEqual(
                    builder.verify_view_freeze(args, "b" * 40), "c" * 40
                )
                args.views_output.write_bytes(b"tampered-after-commit\n")
                with self.assertRaisesRegex(
                    builder.EnvironmentRealizationError,
                    "current prerequisite bytes",
                ):
                    builder.verify_view_freeze(args, "b" * 40)

    def test_e1_freeze_rejects_symlink_even_when_target_bytes_match_commit(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            base = Path(temporary)
            args = _freeze_args(base)
            prerequisite_paths = [
                *args.e1_parts,
                args.e1_output,
                args.e1_bindings_output,
                *args.e2_packets,
                args.views_output,
                args.views_manifest_output,
                args.routing_output,
                *args.e1_packets,
            ]
            symlink_target = base / "matching_e1_target.jsonl"
            symlink_target.write_bytes(b"byte-identical-prerequisite\n")
            for index, path in enumerate(prerequisite_paths, 1):
                if path == args.e1_output:
                    path.symlink_to(symlink_target)
                else:
                    path.write_bytes(f"committed-{index}\n".encode("utf-8"))

            def portable_relative(path: Path) -> str:
                return path.absolute().relative_to(ROOT.absolute()).as_posix()

            committed = {
                portable_relative(path): path.read_bytes()
                for path in prerequisite_paths
            }
            self.assertTrue(args.e1_output.is_symlink())
            self.assertEqual(
                args.e1_output.read_bytes(),
                committed[portable_relative(args.e1_output)],
            )

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
                if "merge-base" in command:
                    return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")
                if "show" in command:
                    relative = command[-1].split(":", 1)[1]
                    return subprocess.CompletedProcess(
                        command, 0, stdout=committed[relative], stderr=b""
                    )
                raise AssertionError(f"unexpected git command: {command}")

            with mock.patch.object(
                builder, "_latest_artifact_commit", return_value="c" * 40
            ), mock.patch.object(
                builder, "_relative", side_effect=portable_relative
            ), mock.patch.object(
                builder.subprocess, "run", side_effect=fake_run
            ), mock.patch.object(builder, "_commit_path_absent"):
                with self.assertRaisesRegex(
                    builder.EnvironmentRealizationError,
                    "E1 freeze does not contain current prerequisite bytes",
                ):
                    builder.verify_e1_freeze(args, "b" * 40)

    def test_path_guard_requires_exact_canonical_plan_and_output_paths(self) -> None:
        canonical = builder.parse_args(["--freeze-plan"])
        builder._validate_paths(canonical)
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            overrides = _freeze_args(Path(temporary))
            with self.assertRaisesRegex(
                builder.EnvironmentRealizationError,
                "canonical|versioned run requires",
            ):
                builder._validate_paths(overrides)

        outside = copy.copy(canonical)
        outside.views_output = Path("/tmp/representative_environment_escape.jsonl")
        with self.assertRaises(builder.EnvironmentRealizationError):
            builder._validate_paths(outside)

        reordered = copy.copy(canonical)
        reordered.e1_packets = tuple(reversed(canonical.e1_packets))
        with self.assertRaisesRegex(
            builder.EnvironmentRealizationError,
            "canonical|versioned run requires",
        ):
            builder._validate_paths(reordered)

    def test_write_once_collision_cannot_change_other_environment_outputs(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            base = Path(temporary)
            batch = {
                "views": (base / "views.jsonl", b'{"question_id":"q1"}\n'),
                "manifest": (base / "manifest.json", b'{"record_count":1}\n'),
            }
            statuses = _common.write_output_batch(batch)
            self.assertEqual(set(statuses.values()), {"written"})
            view_bytes = batch["views"][0].read_bytes()
            manifest_path = batch["manifest"][0]
            manifest_path.write_bytes(b"collision\n")
            with self.assertRaisesRegex(ValueError, "different bytes"):
                _common.write_output_batch(batch)
            self.assertEqual(batch["views"][0].read_bytes(), view_bytes)
            self.assertEqual(manifest_path.read_bytes(), b"collision\n")


if __name__ == "__main__":
    unittest.main()
