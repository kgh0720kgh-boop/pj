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

import build_operator_equivalence_normalization as normalizer


def _projection() -> dict[str, object]:
    return {
        "schema_version": normalizer.PROJECTION_SCHEMA_VERSION,
        "projection_id": "operator_equivalence_projection_v0_1:q1:candidate1",
        "question_id": "q1",
        "family_id": f"cbf_v0_1:{'1' * 64}",
        "producer_partition": "e2_author_partition_01",
        "candidate_id": "candidate1",
        "target_backbone_variant_id": "primary",
        "variation_axes": ["operator_boundary_split_or_merge"],
        "target_semantic_topology": {
            "nodes": [
                {"node_id": "n1", "role": "ACQUIRE", "depends_on": []},
                {"node_id": "n2", "role": "SELECT", "depends_on": ["n1"]},
                {"node_id": "n3", "role": "PROJECT", "depends_on": ["n1", "n2"]},
            ],
            "entry_node_ids": ["n1"],
            "output_node_ids": ["n3"],
        },
        "operator_topology": {
            "nodes": [
                {
                    "node_id": "op1",
                    "depends_on": [],
                    "input_slot_ids": ["slot1"],
                    "roles": ["backbone_realization", "environment_extension"],
                },
                {
                    "node_id": "op2",
                    "depends_on": ["op1"],
                    "input_slot_ids": [],
                    "roles": ["backbone_realization"],
                },
                {
                    "node_id": "op3",
                    "depends_on": ["op1", "op2"],
                    "input_slot_ids": [],
                    "roles": ["backbone_realization"],
                },
            ],
            "entry_node_ids": ["op1"],
            "output_node_ids": ["op3"],
        },
        "semantic_to_operator_mappings": [
            {
                "mapping_id": "mapping1",
                "backbone_node_ids": ["n1"],
                "operator_node_ids": ["op1"],
                "mapping_kind": "one_to_one",
            },
            {
                "mapping_id": "mapping2",
                "backbone_node_ids": ["n2"],
                "operator_node_ids": ["op2"],
                "mapping_kind": "one_to_one",
            },
            {
                "mapping_id": "mapping3",
                "backbone_node_ids": ["n3"],
                "operator_node_ids": ["op3"],
                "mapping_kind": "one_to_one",
            },
        ],
        "typed_unresolved_slots": [
            {
                "slot_id": "slot1",
                "environment_modality": "table_row_or_cell",
                "cardinality": "multiple",
            }
        ],
        "unsupported_target_backbone_node_ids": [],
        "coverage_status": "complete_for_target_variant",
        "evidence_boundary": normalizer.EVIDENCE_BOUNDARY,
    }


class CanonicalGraphTests(unittest.TestCase):
    def test_alpha_order_and_transitive_edge_do_not_change_semantic_signature(self) -> None:
        projection = _projection()
        first = normalizer.normalize_projection(projection)
        renamed = copy.deepcopy(projection)
        renamed["target_semantic_topology"] = {
            "nodes": [
                {"node_id": "z", "role": "PROJECT", "depends_on": ["x", "y"]},
                {"node_id": "x", "role": "ACQUIRE", "depends_on": []},
                {"node_id": "y", "role": "SELECT", "depends_on": ["x"]},
            ],
            "entry_node_ids": ["x"],
            "output_node_ids": ["z"],
        }
        for mapping in renamed["semantic_to_operator_mappings"]:
            mapping["backbone_node_ids"] = [
                {"n1": "x", "n2": "y", "n3": "z"}[mapping["backbone_node_ids"][0]]
            ]
        second = normalizer.normalize_projection(renamed)
        self.assertEqual(
            first["semantic_quotient"]["signature_sha256"],
            second["semantic_quotient"]["signature_sha256"],
        )
        self.assertEqual(first["equivalence_assessment"]["status"], "equivalent")

    def test_missing_semantic_mapping_is_not_equivalent(self) -> None:
        projection = _projection()
        projection["semantic_to_operator_mappings"].pop()
        result = normalizer.normalize_projection(projection)
        self.assertEqual(result["equivalence_assessment"]["status"], "not_equivalent")
        self.assertFalse(result["equivalence_assessment"]["coverage_preserved"])

    def test_explicit_access_changes_adapter_not_semantic_quotient(self) -> None:
        fused = _projection()
        explicit = copy.deepcopy(fused)
        explicit["candidate_id"] = "candidate2"
        explicit["operator_topology"]["nodes"][0]["roles"] = ["backbone_realization"]
        explicit["operator_topology"]["nodes"].insert(
            0,
            {
                "node_id": "op4",
                "depends_on": [],
                "input_slot_ids": ["slot1"],
                "roles": ["environment_extension"],
            },
        )
        explicit["operator_topology"]["nodes"][1]["depends_on"] = ["op4"]
        explicit["operator_topology"]["nodes"][1]["input_slot_ids"] = []
        explicit["operator_topology"]["entry_node_ids"] = ["op4"]
        fused_result = normalizer.normalize_projection(fused)
        explicit_result = normalizer.normalize_projection(explicit)
        self.assertEqual(
            fused_result["semantic_quotient"]["signature_sha256"],
            explicit_result["semantic_quotient"]["signature_sha256"],
        )
        self.assertNotEqual(
            fused_result["environment_adapter_signature"]["signature_sha256"],
            explicit_result["environment_adapter_signature"]["signature_sha256"],
        )
        self.assertEqual(explicit_result["equivalence_assessment"]["status"], "equivalent")


class LiveNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.args = normalizer.parse_args(["--build"])

    def test_live_projection_is_label_free_and_all_candidates_normalize(self) -> None:
        realizations, views = normalizer._load_sources(self.args)
        projections = []
        normalized = []
        for realization in realizations:
            for candidate in realization["realization_candidates"]:
                projection = normalizer.build_structural_projection(
                    realization, candidate, views[realization["question_id"]]
                )
                normalizer._assert_label_free_projection(projection)
                projections.append(projection)
                normalized.append(normalizer.normalize_projection(projection))
        self.assertEqual(len(projections), 93)
        self.assertEqual(
            Counter(record["equivalence_assessment"]["status"] for record in normalized)[
                "not_equivalent"
            ],
            0,
        )
        serialized = "\n".join(json.dumps(record, sort_keys=True) for record in projections)
        for forbidden in (
            "record_local_label",
            "operation_description",
            "output_description",
            "required_semantics",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_reversibility_ledger_hashes_exact_projection(self) -> None:
        realizations, views = normalizer._load_sources(self.args)
        realization = realizations[0]
        projection = normalizer.build_structural_projection(
            realization,
            realization["realization_candidates"][0],
            views[realization["question_id"]],
        )
        result = normalizer.normalize_projection(projection)
        self.assertEqual(
            normalizer.canonical_json_sha256(
                result["reversibility_ledger"]["structural_projection"]
            ),
            result["source_projection_sha256"],
        )
        self.assertTrue(result["reversibility_ledger"]["reconstruction_verified"])

    def test_precommitted_fallback_is_balanced_and_uses_all_challenges(self) -> None:
        realizations, _ = normalizer._load_sources(self.args)
        selection = normalizer._fallback_selection(self.args, realizations)
        self.assertEqual(len(selection), 16)
        self.assertEqual(
            Counter(item["original_e2_producer_partition"] for item in selection),
            Counter({f"e2_author_partition_{index:02d}": 4 for index in range(1, 5)}),
        )
        self.assertEqual(
            Counter(item["selection_role"] for item in selection),
            Counter({"e1_challenge": 7, "adequate_control": 9}),
        )


if __name__ == "__main__":
    unittest.main()
