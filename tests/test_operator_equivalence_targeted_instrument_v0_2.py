from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction/tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_operator_equivalence_targeted_instrument_v0_2 as instrument
from _common import canonical_json_sha256, iter_json_records


class TargetedInstrumentV02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.args = instrument.parse_args(["--validate-plan-only"])
        cls.packets = instrument.build_packets(cls.args)
        cls.targeted_author_01 = list(
            iter_json_records(cls.args.targeted_author_outputs[0])
        )
        cls.targeted_author_02 = list(
            iter_json_records(cls.args.targeted_author_outputs[1])
        )

    def _adapt_record(
        self, source: dict, author_index: int, question_index: int
    ) -> tuple[dict, dict]:
        packet = self.packets[author_index][question_index]
        record = copy.deepcopy(source)
        for key, value in packet["fixed_output_fields"].items():
            record[key] = copy.deepcopy(value)
        return record, packet

    def test_source_run_and_selection_remain_exact(self) -> None:
        instrument._validate_targeted_v01_source(self.args)
        self.assertEqual(
            tuple(item["question_id"] for item in instrument._selection(self.args)),
            instrument.EXPECTED_QUESTION_IDS,
        )

    def test_packets_have_equal_views_and_only_author_specific_routing_differs(self) -> None:
        left, right = self.packets
        self.assertEqual(len(left), 6)
        self.assertEqual(len(right), 6)
        for left_record, right_record in zip(left, right):
            self.assertEqual(left_record["view"], right_record["view"])
            self.assertEqual(
                left_record["author_fill_fields"], right_record["author_fill_fields"]
            )
            self.assertEqual(left_record["feedback_contract"], right_record["feedback_contract"])
            self.assertNotEqual(left_record["author_id"], right_record["author_id"])
            self.assertNotEqual(
                left_record["fixed_output_fields"]["producer_partition"],
                right_record["fixed_output_fields"]["producer_partition"],
            )

    def test_partial_candidate_gets_only_candidate_local_failure_facts(self) -> None:
        record, packet = self._adapt_record(self.targeted_author_02[0], 1, 0)
        candidate = record["realization_candidates"][0]
        feedback = instrument.candidate_local_feedback(record, candidate, packet["view"])
        self.assertFalse(feedback["complete_target_node_coverage"])
        self.assertFalse(feedback["required_dependencies_preserved"])
        self.assertFalse(feedback["mapped_target_output_coverage_complete"])
        self.assertFalse(feedback["all_four_obligations_preserved"])
        self.assertEqual(feedback["missing_target_node_ids"], ["n3", "n4"])
        serialized = json.dumps(feedback, sort_keys=True)
        self.assertNotIn("signature_sha256", serialized)
        self.assertNotIn("full_eligible", serialized)
        self.assertNotIn("preferred_candidate_id", serialized)

    def test_complete_candidate_passes_all_four_obligations(self) -> None:
        record, packet = self._adapt_record(self.targeted_author_01[0], 0, 0)
        feedbacks = [
            instrument.candidate_local_feedback(record, candidate, packet["view"])
            for candidate in record["realization_candidates"]
        ]
        self.assertTrue(any(item["all_four_obligations_preserved"] for item in feedbacks))

    def test_output_arity_defect_is_candidate_local(self) -> None:
        record, packet = self._adapt_record(self.targeted_author_01[0], 0, 0)
        candidate = next(
            candidate
            for candidate in record["realization_candidates"]
            if instrument.candidate_local_feedback(record, candidate, packet["view"])[
                "all_four_obligations_preserved"
            ]
        )
        candidate = copy.deepcopy(candidate)
        extra = next(
            node["node_id"]
            for node in candidate["graph"]["nodes"]
            if node["node_id"] not in candidate["graph"]["output_node_ids"]
        )
        candidate["graph"]["output_node_ids"].append(extra)
        feedback = instrument.candidate_local_feedback(record, candidate, packet["view"])
        self.assertFalse(feedback["output_arity_preserved"])
        self.assertEqual(feedback["operator_output_arity"], 2)

    def test_feedback_record_schema_and_leakage_guard(self) -> None:
        record, packet = self._adapt_record(self.targeted_author_01[0], 0, 0)
        candidates = [
            instrument.candidate_local_feedback(record, candidate, packet["view"])
            for candidate in record["realization_candidates"]
        ]
        feedback = {
            "schema_version": "operator_equivalence_targeted_instrument_feedback_v0_2",
            "run_id": instrument.RUN_ID,
            "author_id": instrument.AUTHOR_IDS[0],
            "question_id": record["question_id"],
            "feedback_round": 1,
            "source_draft_record_sha256": canonical_json_sha256(record),
            "scope": "candidate_local_target_node_required_dependency_target_output_and_output_arity_only",
            "candidates": candidates,
            "record_has_candidate_preserving_all_four_obligations": any(
                item["all_four_obligations_preserved"] for item in candidates
            ),
            "reference_or_preference_content_included": False,
        }
        validator = instrument._validator(self.args.feedback_schema)
        self.assertEqual(list(validator.iter_errors(feedback)), [])
        self.assertEqual(instrument.feedback_leakage_errors(feedback), [])
        contaminated = copy.deepcopy(feedback)
        contaminated["candidates"][0]["signature_sha256"] = "0" * 64
        self.assertTrue(instrument.feedback_leakage_errors(contaminated))

    def test_normalization_keeps_draft_and_final_provenance_distinct(self) -> None:
        record, packet = self._adapt_record(self.targeted_author_01[0], 0, 0)
        candidate = record["realization_candidates"][0]
        draft = instrument._normalize_candidate(
            record, candidate, packet["view"], instrument.AUTHOR_IDS[0], "draft"
        )
        final = instrument._normalize_candidate(
            record, candidate, packet["view"], instrument.AUTHOR_IDS[0], "final"
        )
        self.assertNotEqual(draft["source_candidate_key"], final["source_candidate_key"])
        self.assertEqual(
            draft["candidate_semantic_profile"]["signature_sha256"],
            final["candidate_semantic_profile"]["signature_sha256"],
        )
        validator = instrument._validator(self.args.normalization_schema)
        self.assertEqual(list(validator.iter_errors(draft)), [])
        self.assertEqual(list(validator.iter_errors(final)), [])

    def test_profile_inventory_retains_reference_draft_and_final(self) -> None:
        reference = next(iter_json_records(self.args.targeted_normalized))
        record, packet = self._adapt_record(self.targeted_author_01[0], 0, 0)
        candidate = record["realization_candidates"][0]
        draft = instrument._normalize_candidate(
            record, candidate, packet["view"], instrument.AUTHOR_IDS[0], "draft"
        )
        final = instrument._normalize_candidate(
            record, candidate, packet["view"], instrument.AUTHOR_IDS[0], "final"
        )
        inventory, loss = instrument._profile_inventory(
            [
                ("targeted_v0_1_reference", [reference]),
                ("instrument_draft", [draft]),
                ("instrument_final", [final]),
            ]
        )
        self.assertEqual(loss, 0)
        observations = [
            item for group in inventory for item in group["observations"]
        ]
        self.assertEqual(len(observations), 3)

    def test_frozen_branch_precedence(self) -> None:
        counts = {
            "invalid_draft_records": 0,
            "invalid_final_records": 0,
            "technical_loss": 0,
            "feedback_records": 12,
            "feedback_reference_leakage": 0,
            "feedback_binding_errors": 0,
            "feedback_rounds_per_author_min": 1,
            "feedback_rounds_per_author_max": 1,
            "eligible_set_contamination": 0,
            "unclassified_adapter_candidates": 0,
            "preferred_candidates": 0,
            "fresh_question_ids": 0,
            "profile_inventory_loss": 0,
            "final_candidate_local_author_question_coverage": 12,
            "full_eligible_author_question_coverage": 12,
            "nonempty_final_author_semantic_intersections": 6,
            "final_author_semantic_exact_matches": 5,
            "targeted_v0_1_reference_compatible_author_questions": 12,
        }
        rates = {"mean_final_author_semantic_jaccard": 0.9}
        decision, results = instrument._decision(
            counts, rates, instrument.FROZEN_CRITERIA
        )
        self.assertEqual(decision, instrument.FROZEN_CRITERIA["branch_on_pass"])
        self.assertTrue(results["all_criteria_passed"])

        technical = dict(counts, feedback_reference_leakage=1)
        decision, _ = instrument._decision(
            technical, rates, instrument.FROZEN_CRITERIA
        )
        self.assertEqual(
            decision, instrument.FROZEN_CRITERIA["branch_on_technical_failure"]
        )

        coverage = dict(counts, full_eligible_author_question_coverage=11)
        decision, _ = instrument._decision(
            coverage, rates, instrument.FROZEN_CRITERIA
        )
        self.assertEqual(
            decision,
            instrument.FROZEN_CRITERIA["branch_on_repeated_coverage_failure"],
        )

        semantic = dict(counts, final_author_semantic_exact_matches=4)
        decision, _ = instrument._decision(
            semantic, rates, instrument.FROZEN_CRITERIA
        )
        self.assertEqual(
            decision, instrument.FROZEN_CRITERIA["branch_on_semantic_failure"]
        )

    def test_plan_enumerates_every_output_before_freeze(self) -> None:
        labels = list(instrument._all_planned_outputs(self.args))
        self.assertEqual(len(labels), 17)
        self.assertIn("draft_output_01", labels)
        self.assertIn("feedback_round_01_author_02", labels)
        self.assertIn("final_output_02", labels)
        self.assertIn("run_manifest", labels)


if __name__ == "__main__":
    unittest.main()
