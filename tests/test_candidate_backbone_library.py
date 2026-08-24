from __future__ import annotations

import copy
import math
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction" / "tools"
sys.path.insert(0, str(TOOLS))

import _common
import build_candidate_backbone_library as builder


class CandidateBackboneLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records, cls.derived, cls.metrics = builder.load_source_bundle(
            builder.DEFAULT_RECORDS,
            builder.DEFAULT_SIGNATURES,
            builder.DEFAULT_METRICS,
            builder.DEFAULT_N300_RUN_MANIFEST,
            builder.DEFAULT_EXPOSURE,
        )
        cls.source_bindings = builder._source_bindings(
            builder.DEFAULT_RECORDS,
            builder.DEFAULT_SIGNATURES,
            builder.DEFAULT_METRICS,
            builder.DEFAULT_N300_RUN_MANIFEST,
            builder.DEFAULT_EXPOSURE,
        )
        cls.families, cls.selection = builder.build_library_and_selection(
            cls.records,
            cls.derived,
            source_bindings=cls.source_bindings,
        )

    def test_quota_evidence_tiers_and_frequency_strata_are_exact(self) -> None:
        for count in (1, 2, 3, 5, 8, 10, 14, 20, 201, 300):
            self.assertEqual(
                builder.representative_quota(count),
                min(count, 1 + math.ceil(math.log2(count))),
            )
        self.assertEqual(builder.evidence_tier(1), "singleton")
        self.assertEqual(builder.evidence_tier(2), "doubleton")
        self.assertEqual(builder.evidence_tier(3), "recurrent")
        self.assertEqual(builder.frequency_stratum(1), "singleton_1")
        self.assertEqual(builder.frequency_stratum(2), "doubleton_2")
        self.assertEqual(builder.frequency_stratum(9), "low_recurrent_3_9")
        self.assertEqual(builder.frequency_stratum(10), "medium_recurrent_10_19")
        self.assertEqual(builder.frequency_stratum(20), "high_recurrent_20_99")
        self.assertEqual(builder.frequency_stratum(100), "dominant_100_plus")
        with self.assertRaises(builder.CandidateLibraryError):
            builder.representative_quota(0)

    def test_live_n300_reconstructs_30_families_300_members_and_71_selections(self) -> None:
        self.assertEqual(len(self.families), 30)
        self.assertEqual(sum(len(item["members"]) for item in self.families), 300)
        self.assertEqual(
            Counter(item["evidence_tier"] for item in self.families),
            Counter({"singleton": 14, "doubleton": 7, "recurrent": 9}),
        )
        self.assertEqual(self.selection["selected_question_count"], 71)
        self.assertEqual(self.selection["selected_family_count"], 30)
        self.assertEqual(len(set(self.selection["selected_question_ids"])), 71)
        self.assertEqual(
            self.selection["selected_question_ids_ordered_sha256"],
            _common.canonical_json_sha256(self.selection["selected_question_ids"]),
        )
        self.assertEqual(
            self.selection["selected_question_ids_set_sha256"],
            _common.canonical_string_set_sha256(self.selection["selected_question_ids"]),
        )
        self.assertEqual(
            self.selection["selected_question_ids_ordered_sha256"],
            "5403debe2cbe9c7f55ded0a01b49d7c42bf03e53a71350efe269bbd3c0bdcb2e",
        )
        self.assertEqual(
            self.selection["selected_question_ids_set_sha256"],
            "9b6e05650834871ce30acc1c2dfde18fc64910dcd238982f5d482f6a31e15680",
        )
        self.assertEqual(
            [
                (
                    item["family_count"],
                    item["source_member_question_count"],
                    item["selected_question_count"],
                )
                for item in self.selection["strata_summary"]
            ],
            [
                (14, 14, 14),
                (7, 14, 14),
                (5, 27, 18),
                (2, 24, 10),
                (1, 20, 6),
                (1, 201, 9),
            ],
        )

    def test_family_members_are_an_exhaustive_disjoint_partition(self) -> None:
        observed = [
            member["question_id"]
            for family in self.families
            for member in family["members"]
        ]
        expected = [record["question_id"] for record in self.records]
        self.assertEqual(len(observed), len(set(observed)))
        self.assertEqual(set(observed), set(expected))
        for family in self.families:
            count = family["frequency"]["cumulative_n300_question_count"]
            self.assertEqual(count, len(family["members"]))
            self.assertEqual(
                count,
                family["frequency"]["n100_prefix_question_count"]
                + family["frequency"]["new200_expansion_question_count"],
            )
            self.assertEqual(
                sum(family["support"]["producer_partition_counts"].values()), count
            )
            self.assertEqual(
                sum(
                    value["question_count"]
                    for value in family["support"]["cumulative_ten_question_block_counts"]
                ),
                count,
            )

    def test_signatures_canonical_payloads_and_crosswalks_are_exact(self) -> None:
        by_question = {item["question_id"]: item for item in self.derived}
        for family in self.families:
            signature = family["contracted_signature_sha256"]
            self.assertEqual(
                _common.canonical_json_sha256(family["canonical_contracted_graph"]),
                signature,
            )
            member_ids = [member["question_id"] for member in family["members"]]
            for kind in ("fine_semantic_dag", "topology_shape", "task"):
                crosswalk_ids: list[str] = []
                for item in family["crosswalks"][kind]:
                    self.assertEqual(
                        _common.canonical_json_sha256(item["canonical"]),
                        item["signature_sha256"],
                    )
                    self.assertEqual(item["question_count"], len(item["question_ids"]))
                    crosswalk_ids.extend(item["question_ids"])
                    for question_id in item["question_ids"]:
                        self.assertEqual(
                            by_question[question_id]["signatures"][kind],
                            item["signature_sha256"],
                        )
                self.assertEqual(Counter(crosswalk_ids), Counter(member_ids))

    def test_greedy_selection_is_input_order_invariant(self) -> None:
        family = self.families[0]
        signature = family["contracted_signature_sha256"]
        family_ids = {member["question_id"] for member in family["members"]}
        items = [
            {"position": index, "record": record, "derived": derived}
            for index, (record, derived) in enumerate(zip(self.records, self.derived), start=1)
            if record["question_id"] in family_ids
        ]
        forward = builder.select_family_members(signature, items)
        reverse = builder.select_family_members(signature, list(reversed(items)))
        self.assertEqual(
            [item["item"]["record"]["question_id"] for item in forward],
            [item["item"]["record"]["question_id"] for item in reverse],
        )

    def test_question_text_does_not_affect_representative_selection(self) -> None:
        changed = copy.deepcopy(self.records)
        for index, record in enumerate(changed):
            record["question"] = f"deliberately changed text {index}"
        _, changed_selection = builder.build_library_and_selection(
            changed,
            self.derived,
            source_bindings=self.source_bindings,
        )
        self.assertEqual(
            changed_selection["selected_question_ids"],
            self.selection["selected_question_ids"],
        )

    def test_selection_exposes_no_question_or_environment_payload(self) -> None:
        forbidden = {
            "question",
            "table_id",
            "table",
            "rows",
            "cells",
            "linked_document",
            "document_text",
            "answer_text",
            "grounding",
            "execution_trace",
        }

        def keys(value: object) -> set[str]:
            if isinstance(value, dict):
                return set(value) | set().union(*(keys(item) for item in value.values()))
            if isinstance(value, list):
                return set().union(*(keys(item) for item in value))
            return set()

        self.assertFalse(forbidden & keys(self.selection))
        self.assertFalse(self.selection["selection_contract"]["question_text_used_for_ranking"])
        self.assertFalse(
            self.selection["selection_contract"]["environment_or_outcome_used_for_ranking"]
        )

    def test_live_records_match_frozen_normalizer_and_no_family_is_silently_excluded(self) -> None:
        self.assertEqual(builder.n300.derive_signatures(self.records), self.derived)
        all_uncertain = [
            family
            for family in self.families
            if family["evidence"]["all_members_uncertain"]
        ]
        selected_families = {item["family_id"] for item in self.selection["selections"]}
        self.assertEqual(len(all_uncertain), 5)
        self.assertTrue(all(family["family_id"] in selected_families for family in all_uncertain))

    def test_source_contract_rejects_trigger_exposure_and_record_contamination(self) -> None:
        decision = copy.deepcopy(self.metrics["n1000_precommitted_decision"])
        builder._validate_n300_decision(decision)
        del decision["trigger_values"][
            "at_least_2_material_cross_partition_new_contracted_families"
        ]
        with self.assertRaises(builder.CandidateLibraryError):
            builder._validate_n300_decision(decision)

        exposure = _common.read_json(builder.DEFAULT_EXPOSURE)
        record_ids = [record["question_id"] for record in self.records]
        builder._validate_exposure_ledger(exposure, record_ids)
        exposure["ai_question_structure_exploration"]["question_ids"][0] = "wrong_id"
        with self.assertRaises(builder.CandidateLibraryError):
            builder._validate_exposure_ledger(exposure, record_ids)

        contaminated = copy.deepcopy(self.records[0])
        contaminated["table_id"] = "forbidden_environment_identity"
        validator = builder._schema_validator(builder.DEFAULT_RECORD_SCHEMA)
        self.assertTrue(
            builder._validation_errors(validator, contaminated, "contaminated_record")
        )

    def test_schemas_are_draft_2020_12_and_outcomes_are_independent_fields(self) -> None:
        family_validator = builder._schema_validator(builder.DEFAULT_FAMILY_SCHEMA)
        selection_validator = builder._schema_validator(builder.DEFAULT_SELECTION_SCHEMA)
        outcome_validator = builder._outcome_schema_validator(builder.DEFAULT_OUTCOME_SCHEMA)
        self.assertEqual(
            [
                error
                for index, family in enumerate(self.families)
                for error in builder._validation_errors(
                    family_validator, family, f"family[{index}]"
                )
            ],
            [],
        )
        self.assertEqual(
            builder._validation_errors(selection_validator, self.selection, "selection"),
            [],
        )
        inconsistent_family = copy.deepcopy(self.families[0])
        inconsistent_member = inconsistent_family["members"][0]
        inconsistent_member.update(
            {
                "source_slice": "n100_prefix",
                "committed_position": 101,
                "cumulative_ten_question_block_number": 11,
                "new200_relative_ten_question_block_number": 1,
            }
        )
        self.assertTrue(
            builder._validation_errors(
                family_validator, inconsistent_family, "inconsistent_family"
            )
        )
        inconsistent_selection = copy.deepcopy(self.selection)
        inconsistent_selection["strata_summary"][1] = copy.deepcopy(
            inconsistent_selection["strata_summary"][0]
        )
        self.assertTrue(
            builder._validation_errors(
                selection_validator, inconsistent_selection, "inconsistent_selection"
            )
        )
        outcome_schema = _common.read_json(builder.DEFAULT_OUTCOME_SCHEMA)
        required = set(outcome_schema["required"])
        self.assertTrue(
            {
                "backbone_adequacy",
                "environment_operator_realization",
                "grounding",
                "execution",
                "answer_recovery",
            }
            <= required
        )
        artifact = {
            "artifact_role": "future_evidence",
            "repository_relative_path": "future/evidence.json",
            "sha256": "0" * 64,
            "record_id": None,
        }
        outcome = {
            "schema_version": "environment_realization_outcome_v0_1",
            "outcome_id": "outcome:1",
            "run_id": "run:1",
            "selection_id": builder.SELECTION_ID,
            "selection_index": 1,
            "question_id": "question:1",
            "family_id": "cbf_v0_1:" + "1" * 64,
            "contracted_signature_sha256": "1" * 64,
            "record_status": "in_progress",
            "assessment_scope": "selected_question_environment_instance_only",
            "source_bindings": [artifact],
            "backbone_adequacy": {
                "status": "fail",
                "candidate_backbone_adequate": False,
                "required_change_codes": ["missing_obligation"],
                "evidence_references": [],
                "notes": None,
            },
            "environment_operator_realization": {
                "status": "partial",
                "realization_available": True,
                "operator_vocabulary_version": "operator_vocabulary_v0_1",
                "realization_record_id": "realization:1",
                "unsupported_backbone_node_indices": [0],
                "evidence_references": [],
                "notes": None,
            },
            "grounding": {
                "status": "not_evaluated",
                "all_required_inputs_grounded": None,
                "grounding_record_id": None,
                "grounded_item_count": None,
                "ungrounded_item_count": None,
                "failure_codes": [],
                "evidence_references": [],
                "notes": None,
            },
            "execution": {
                "status": "pass",
                "executable": True,
                "execution_succeeded": True,
                "execution_record_id": "execution:1",
                "failure_codes": [],
                "evidence_references": [],
                "notes": None,
            },
            "answer_recovery": {
                "status": "fail",
                "answer_recovered": False,
                "answer_match_assessment": "mismatch",
                "answer_record_id": "answer:1",
                "comparison_provenance": {
                    "reference_answer_binding": artifact,
                    "reference_answer_evidence_class": "official_dataset_reference_non_gold",
                    "reference_answer_is_gold": False,
                    "comparator_id": "answer_comparator",
                    "comparator_version": "v0_1",
                },
                "failure_codes": ["mismatch"],
                "evidence_references": [],
                "notes": None,
            },
            "independence_contract": {
                "all_five_signals_required_and_independently_scored": True,
                "one_signal_status_derived_from_another_signal": False,
                "execution_success_implies_backbone_adequacy": False,
                "execution_failure_implies_backbone_inadequacy": False,
                "answer_recovery_implies_prior_stage_success": False,
                "downstream_failure_overwrites_upstream_assessment": False,
            },
            "evidence_boundary": {
                "human_evidence_count": 0,
                "gold_claimed": False,
                "modeling_ready_claimed": False,
                "candidate_family_semantic_correctness_presupposed": False,
                "family_level_semantic_correctness_established": False,
            },
            "limitations": [],
        }
        self.assertEqual(
            builder._validation_errors(outcome_validator, outcome, "outcome"), []
        )
        missing_signal = copy.deepcopy(outcome)
        del missing_signal["grounding"]
        self.assertTrue(
            builder._validation_errors(outcome_validator, missing_signal, "outcome")
        )
        impossible_execution = copy.deepcopy(outcome)
        impossible_execution["execution"]["executable"] = False
        self.assertTrue(
            builder._validation_errors(
                outcome_validator, impossible_execution, "impossible_execution"
            )
        )
        impossible_answer = copy.deepcopy(outcome)
        impossible_answer["answer_recovery"]["answer_match_assessment"] = "exact_match"
        self.assertTrue(
            builder._validation_errors(
                outcome_validator, impossible_answer, "impossible_answer"
            )
        )
        incomplete_complete = copy.deepcopy(outcome)
        incomplete_complete["record_status"] = "complete"
        self.assertTrue(
            builder._validation_errors(
                outcome_validator, incomplete_complete, "incomplete_complete"
            )
        )
        initialized = copy.deepcopy(outcome)
        initialized["record_status"] = "initialized_not_evaluated"
        initialized["backbone_adequacy"] = {
            "status": "not_evaluated",
            "candidate_backbone_adequate": None,
            "required_change_codes": [],
            "evidence_references": [],
            "notes": None,
        }
        initialized["environment_operator_realization"] = {
            "status": "not_evaluated",
            "realization_available": None,
            "operator_vocabulary_version": None,
            "realization_record_id": None,
            "unsupported_backbone_node_indices": [],
            "evidence_references": [],
            "notes": None,
        }
        initialized["grounding"] = {
            "status": "not_evaluated",
            "all_required_inputs_grounded": None,
            "grounding_record_id": None,
            "grounded_item_count": None,
            "ungrounded_item_count": None,
            "failure_codes": [],
            "evidence_references": [],
            "notes": None,
        }
        initialized["execution"] = {
            "status": "not_evaluated",
            "executable": None,
            "execution_succeeded": None,
            "execution_record_id": None,
            "failure_codes": [],
            "evidence_references": [],
            "notes": None,
        }
        initialized["answer_recovery"] = {
            "status": "not_evaluated",
            "answer_recovered": None,
            "answer_match_assessment": None,
            "answer_record_id": None,
            "comparison_provenance": {
                "reference_answer_binding": None,
                "reference_answer_evidence_class": None,
                "reference_answer_is_gold": False,
                "comparator_id": None,
                "comparator_version": None,
            },
            "failure_codes": [],
            "evidence_references": [],
            "notes": None,
        }
        self.assertEqual(
            builder._validation_errors(outcome_validator, initialized, "initialized"),
            [],
        )

    def test_freeze_plan_reconstructs_exact_result_and_strict_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            base = Path(temporary)
            args = builder.parse_args(
                [
                    "--plan",
                    str(base / "plan.json"),
                    "--families-output",
                    str(base / "families.jsonl"),
                    "--selection-output",
                    str(base / "selection.json"),
                    "--checks-output",
                    str(base / "checks.jsonl"),
                    "--report-output",
                    str(base / "report.md"),
                    "--run-manifest-output",
                    str(base / "run_manifest.json"),
                ]
            )
            with mock.patch.object(
                builder, "git_tracked_commit_identity", return_value="a" * 40
            ):
                plan = builder.build_freeze_plan(args)
        self.assertEqual(set(plan), builder.PLAN_TOP_LEVEL_KEYS)
        self.assertEqual(plan["source_scope"], builder.SOURCE_SCOPE)
        self.assertEqual(
            plan["outcome_separation_contract"]["required_independent_signals"],
            list(builder.OUTCOME_REQUIRED_SIGNALS),
        )
        self.assertEqual(
            plan["expected_result"]["selected_question_ids_ordered_sha256"],
            "5403debe2cbe9c7f55ded0a01b49d7c42bf03e53a71350efe269bbd3c0bdcb2e",
        )

    def test_external_input_path_is_rejected_before_reading(self) -> None:
        args = builder.parse_args(["--records", "/tmp/outside-candidate-records.jsonl"])
        with self.assertRaises(builder.CandidateLibraryError):
            builder._validate_paths(args)


if __name__ == "__main__":
    unittest.main()
