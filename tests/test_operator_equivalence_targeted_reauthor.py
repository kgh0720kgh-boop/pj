from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction" / "tools"
sys.path.insert(0, str(TOOLS))

import build_operator_equivalence_targeted_reauthor as targeted


def _recursive_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(
            *(_recursive_keys(item) for item in value.values())
        )
    if isinstance(value, list):
        return set().union(*(_recursive_keys(item) for item in value))
    return set()


class TargetedSelectionAndPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.args = targeted.parse_args(["--materialize-packets"])

    def test_selection_is_exactly_the_six_v02_challenge_mismatches(self) -> None:
        selection = targeted._selection(self.args)
        self.assertEqual(
            tuple(item["question_id"] for item in selection),
            targeted.EXPECTED_QUESTION_IDS,
        )
        self.assertEqual(len(selection), 6)
        self.assertEqual({item["selection_role"] for item in selection}, {"e1_challenge"})
        targeted._validate_source_contract(self.args)

    def test_two_fresh_packets_share_sanitized_views_and_hide_prior_results(self) -> None:
        packets = targeted.build_packets(self.args)
        self.assertEqual([len(packet) for packet in packets], [6, 6])
        self.assertEqual(
            [item["view"]["question_id"] for item in packets[0]],
            [item["view"]["question_id"] for item in packets[1]],
        )
        self.assertEqual(
            [item["author_id"] for item in (packets[0][0], packets[1][0])],
            list(targeted.AUTHOR_IDS),
        )
        self.assertEqual(
            [
                item["fixed_output_fields"]["producer_partition"]
                for item in (packets[0][0], packets[1][0])
            ],
            list(targeted.AUTHOR_PRODUCERS),
        )
        keys = _recursive_keys(packets)
        for forbidden in (
            "realization_candidates",
            "normalization_id",
            "candidate_semantic_profile",
            "equivalence_eligibility",
            "full_eligible_semantic_set",
        ):
            self.assertNotIn(forbidden, keys)
        for packet in packets:
            for item in packet:
                isolation = item["isolation_contract"]
                self.assertTrue(isolation["prior_author_outputs_excluded"])
                self.assertTrue(isolation["normalization_artifacts_excluded"])
                self.assertTrue(item["selection_reason_hidden_from_author"])

    def test_existing_valid_shape_adapted_to_packet_passes_author_validator(self) -> None:
        packet = targeted.build_packets(self.args)[0][0]
        question_id = packet["view"]["question_id"]
        source_path = targeted.SOURCE_BASE / "stage_e2/open_operator_realizations.jsonl"
        source = next(
            record
            for record in map(
                json.loads, source_path.read_text(encoding="utf-8").splitlines()
            )
            if record["question_id"] == question_id
        )
        adapted = copy.deepcopy(source)
        adapted.update(copy.deepcopy(packet["fixed_output_fields"]))
        adapted["preferred_candidate_id"] = None
        adapted["preference_reason"] = None
        validator = targeted._validator(self.args.realization_schema)
        self.assertEqual(
            targeted._targeted_author_record_errors(adapted, packet, validator), []
        )


class TargetedNormalizationAndDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.args = targeted.parse_args(["--materialize-packets"])

    def _adapted_source(self) -> tuple[dict[str, object], dict[str, object]]:
        packet = targeted.build_packets(self.args)[0][0]
        question_id = packet["view"]["question_id"]
        source_path = targeted.SOURCE_BASE / "stage_e2/open_operator_realizations.jsonl"
        source = next(
            record
            for record in map(
                json.loads, source_path.read_text(encoding="utf-8").splitlines()
            )
            if record["question_id"] == question_id
        )
        adapted = copy.deepcopy(source)
        adapted.update(copy.deepcopy(packet["fixed_output_fields"]))
        adapted["preferred_candidate_id"] = None
        adapted["preference_reason"] = None
        return adapted, packet

    def test_targeted_normalization_uses_distinct_provenance_and_v02_semantics(self) -> None:
        record, packet = self._adapted_source()
        normalized = targeted._normalize_candidate(
            record,
            record["realization_candidates"][0],
            packet["view"],
            targeted.AUTHOR_IDS[0],
        )
        self.assertEqual(normalized["source_cohort"], "targeted_reauthor")
        self.assertEqual(normalized["source_author_id"], "targeted_author_01")
        self.assertTrue(normalized["source_candidate_key"].startswith("targeted:"))
        self.assertEqual(
            normalized["normalization_algorithm_version"],
            "operator_equivalence_normalization_v0_2",
        )
        validator = targeted._validator(self.args.targeted_normalization_schema)
        self.assertEqual(list(validator.iter_errors(normalized)), [])

    def test_profile_inventory_retains_every_candidate_observation(self) -> None:
        record, packet = self._adapted_source()
        normalized = targeted._normalize_candidate(
            record,
            record["realization_candidates"][0],
            packet["view"],
            targeted.AUTHOR_IDS[0],
        )
        reference = copy.deepcopy(normalized)
        reference["source_cohort"] = "crossed_author"
        reference["source_author_id"] = "crossed_author_01"
        reference["source_candidate_key"] = "crossed:crossed_author_01:q:candidate1"
        inventory, loss = targeted._profile_inventory([reference], [normalized])
        self.assertEqual(loss, 0)
        self.assertEqual(len(inventory), 1)
        self.assertEqual(len(inventory[0]["observations"]), 2)

    def test_frozen_branch_precedence_separates_technical_coverage_and_semantics(self) -> None:
        counts = {
            "invalid_author_records": 0,
            "technical_loss": 0,
            "eligible_set_contamination": 0,
            "unclassified_adapter_candidates": 0,
            "preferred_candidates": 0,
            "fresh_question_ids": 0,
            "profile_inventory_loss": 0,
            "full_eligible_author_question_coverage": 12,
            "nonempty_new_author_semantic_intersections": 6,
            "new_author_semantic_exact_matches": 5,
            "reference_compatible_author_questions": 12,
        }
        rates = {"mean_new_author_semantic_jaccard": 0.9}
        decision, results = targeted._decision(
            counts, rates, targeted.FROZEN_CRITERIA
        )
        self.assertEqual(decision, targeted.FROZEN_CRITERIA["branch_on_pass"])
        self.assertTrue(results["all_criteria_passed"])

        technical_failure = dict(counts, technical_loss=1)
        decision, _ = targeted._decision(
            technical_failure, rates, targeted.FROZEN_CRITERIA
        )
        self.assertEqual(
            decision, targeted.FROZEN_CRITERIA["branch_on_technical_failure"]
        )

        coverage_failure = dict(counts, full_eligible_author_question_coverage=11)
        decision, _ = targeted._decision(
            coverage_failure, rates, targeted.FROZEN_CRITERIA
        )
        self.assertEqual(
            decision, targeted.FROZEN_CRITERIA["branch_on_coverage_failure"]
        )

        semantic_failure = dict(counts, new_author_semantic_exact_matches=4)
        decision, _ = targeted._decision(
            semantic_failure, rates, targeted.FROZEN_CRITERIA
        )
        self.assertEqual(
            decision, targeted.FROZEN_CRITERIA["branch_on_semantic_failure"]
        )


if __name__ == "__main__":
    unittest.main()
