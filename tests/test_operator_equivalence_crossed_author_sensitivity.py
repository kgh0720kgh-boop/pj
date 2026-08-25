from __future__ import annotations

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction" / "tools"
sys.path.insert(0, str(TOOLS))

import build_operator_equivalence_crossed_author_sensitivity as sensitivity


def _recursive_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_recursive_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_recursive_keys(item) for item in value))
    return set()


class CrossedAuthorContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.args = sensitivity.parse_args(["--materialize-packets"])

    def test_fallback_selection_is_exact_balanced_and_precommitted(self) -> None:
        selection = sensitivity._selection(self.args)
        self.assertEqual(len(selection), 16)
        self.assertEqual(
            Counter(item["selection_role"] for item in selection),
            Counter({"e1_challenge": 7, "adequate_control": 9}),
        )
        self.assertEqual(
            Counter(item["original_e2_producer_partition"] for item in selection),
            Counter({f"e2_author_partition_{index:02d}": 4 for index in range(1, 5)}),
        )

    def test_two_packets_are_crossed_and_hide_prior_results(self) -> None:
        packets = sensitivity.build_packets(self.args)
        self.assertEqual([len(packet) for packet in packets], [16, 16])
        self.assertEqual(
            [item["view"]["question_id"] for item in packets[0]],
            [item["view"]["question_id"] for item in packets[1]],
        )
        self.assertNotEqual(packets[0][0]["author_id"], packets[1][0]["author_id"])
        for forbidden in (
            "realization_candidates",
            "preferred_candidate_id",
            "backbone_adequacy_status",
            "normalization_id",
            "semantic_quotient",
        ):
            self.assertNotIn(forbidden, _recursive_keys(packets))
        for packet in packets:
            for item in packet:
                self.assertTrue(item["isolation_contract"]["prior_e2_records_excluded"])
                self.assertTrue(item["isolation_contract"]["normalization_artifacts_excluded"])

    def test_existing_valid_shape_adapted_to_packet_passes_validator(self) -> None:
        packets = sensitivity.build_packets(self.args)
        packet = packets[0][0]
        question_id = packet["view"]["question_id"]
        source_path = (
            sensitivity.SOURCE_BASE / "stage_e2/open_operator_realizations.jsonl"
        )
        source = next(
            record
            for record in map(json.loads, source_path.read_text(encoding="utf-8").splitlines())
            if record["question_id"] == question_id
        )
        adapted = copy.deepcopy(source)
        adapted.update(copy.deepcopy(packet["fixed_output_fields"]))
        validator = sensitivity._validator(self.args.realization_schema)
        self.assertEqual(sensitivity._author_record_errors(adapted, packet, validator), [])

    def test_jaccard_handles_empty_and_partial_sets(self) -> None:
        self.assertEqual(sensitivity._jaccard(set(), set()), 1.0)
        self.assertEqual(sensitivity._jaccard({"a"}, {"a", "b"}), 0.5)
        self.assertEqual(sensitivity._jaccard({"a"}, {"b"}), 0.0)


if __name__ == "__main__":
    unittest.main()
