from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction" / "tools"
sys.path.insert(0, str(TOOLS))

import build_operator_equivalence_normalization_v0_2 as normalizer


def _projection() -> dict[str, object]:
    return {
        "schema_version": "operator_equivalence_structural_projection_v0_1",
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
                {"node_id": "n3", "role": "PROJECT", "depends_on": ["n2"]},
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
                    "depends_on": ["op2"],
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
        "evidence_boundary": {
            "label_free": True,
            "question_text_excluded": True,
            "environment_text_excluded": True,
            "answer_and_trace_excluded": True,
            "e1_content_excluded": True,
            "operator_descriptions_excluded": True,
            "preserved_vocabularies_excluded": True,
            "grounding_evaluated": False,
            "execution_evaluated": False,
            "answer_recovery_evaluated": False,
            "gold_claimed": False,
        },
    }


def _metadata(projection: dict[str, object], key: str = "original:q1:candidate1") -> dict[str, object]:
    return {
        "source_candidate_key": key,
        "source_cohort": "original",
        "source_author_id": None,
        "source_v0_1_normalization_sha256": "a" * 64,
        "source_v0_1_equivalence_status": "equivalent",
        "source_projection_sha256": normalizer.canonical_json_sha256(projection),
    }


class CandidateSemanticProfileTests(unittest.TestCase):
    def test_partial_candidate_has_distinct_profile_and_is_ineligible(self) -> None:
        complete_projection = _projection()
        complete = normalizer.normalize_projection_v0_2(
            complete_projection, _metadata(complete_projection)
        )
        partial_projection = copy.deepcopy(complete_projection)
        partial_projection["coverage_status"] = "partial_for_target_variant"
        partial_projection["unsupported_target_backbone_node_ids"] = ["n3"]
        partial_projection["semantic_to_operator_mappings"].pop()
        partial = normalizer.normalize_projection_v0_2(
            partial_projection,
            _metadata(partial_projection, "original:q1:candidate2"),
        )
        self.assertEqual(
            complete["equivalence_eligibility"]["status"], "full_eligible"
        )
        self.assertEqual(partial["equivalence_eligibility"]["status"], "ineligible")
        self.assertFalse(
            partial["equivalence_eligibility"][
                "included_in_full_eligible_semantic_set"
            ]
        )
        self.assertNotEqual(
            complete["candidate_semantic_profile"]["signature_sha256"],
            partial["candidate_semantic_profile"]["signature_sha256"],
        )
        self.assertTrue(partial["candidate_semantic_profile"]["missing_output_node_ids"])

    def test_alpha_renaming_preserves_candidate_semantic_profile(self) -> None:
        first_projection = _projection()
        first = normalizer.normalize_projection_v0_2(
            first_projection, _metadata(first_projection)
        )
        renamed = copy.deepcopy(first_projection)
        renamed["target_semantic_topology"] = {
            "nodes": [
                {"node_id": "z", "role": "PROJECT", "depends_on": ["y"]},
                {"node_id": "x", "role": "ACQUIRE", "depends_on": []},
                {"node_id": "y", "role": "SELECT", "depends_on": ["x"]},
            ],
            "entry_node_ids": ["x"],
            "output_node_ids": ["z"],
        }
        rename = {"n1": "x", "n2": "y", "n3": "z"}
        for mapping in renamed["semantic_to_operator_mappings"]:
            mapping["backbone_node_ids"] = [
                rename[node] for node in mapping["backbone_node_ids"]
            ]
        second = normalizer.normalize_projection_v0_2(renamed, _metadata(renamed))
        self.assertEqual(
            first["candidate_semantic_profile"]["signature_sha256"],
            second["candidate_semantic_profile"]["signature_sha256"],
        )

    def test_access_split_changes_boundary_component_not_semantic_profile(self) -> None:
        fused_projection = _projection()
        split_projection = copy.deepcopy(fused_projection)
        split_projection["operator_topology"]["nodes"].insert(
            1,
            {
                "node_id": "op4",
                "depends_on": ["op1"],
                "input_slot_ids": [],
                "roles": ["backbone_realization", "environment_extension"],
            },
        )
        split_projection["operator_topology"]["nodes"][2]["depends_on"] = ["op4"]
        split_projection["semantic_to_operator_mappings"][0]["operator_node_ids"] = [
            "op1",
            "op4",
        ]
        split_projection["semantic_to_operator_mappings"][0]["mapping_kind"] = (
            "one_to_many"
        )
        fused = normalizer.normalize_projection_v0_2(
            fused_projection, _metadata(fused_projection)
        )
        split = normalizer.normalize_projection_v0_2(
            split_projection,
            _metadata(split_projection, "original:q1:candidate2"),
        )
        self.assertEqual(split["equivalence_eligibility"]["status"], "full_eligible")
        self.assertEqual(
            fused["candidate_semantic_profile"]["signature_sha256"],
            split["candidate_semantic_profile"]["signature_sha256"],
        )
        self.assertNotEqual(
            fused["factorized_environment_adapter"]["component_signatures"][
                "split_fuse_boundary"
            ],
            split["factorized_environment_adapter"]["component_signatures"][
                "split_fuse_boundary"
            ],
        )


class FactorizedAdapterTests(unittest.TestCase):
    def test_every_synthetic_source_element_is_classified(self) -> None:
        projection = _projection()
        record = normalizer.normalize_projection_v0_2(projection, _metadata(projection))
        coverage = record["factorized_environment_adapter"]["classification_coverage"]
        self.assertTrue(coverage["all_source_elements_classified"])
        self.assertEqual(coverage["typed_slot_source_count"], 1)
        self.assertEqual(coverage["access_operator_source_count"], 1)
        self.assertEqual(coverage["mapping_source_count"], 3)
        self.assertEqual(coverage["operator_output_source_count"], 1)

    def test_record_sets_never_include_ineligible_candidate(self) -> None:
        complete_projection = _projection()
        complete = normalizer.normalize_projection_v0_2(
            complete_projection, _metadata(complete_projection)
        )
        partial_projection = copy.deepcopy(complete_projection)
        partial_projection["coverage_status"] = "partial_for_target_variant"
        partial_projection["unsupported_target_backbone_node_ids"] = ["n3"]
        partial_projection["semantic_to_operator_mappings"].pop()
        partial = normalizer.normalize_projection_v0_2(
            partial_projection,
            _metadata(partial_projection, "original:q1:candidate2"),
        )
        sets = normalizer._record_sets([complete, partial])
        self.assertEqual(sets["full_eligible_candidate_count"], 1)
        self.assertEqual(sets["ineligible_candidate_count"], 1)
        self.assertEqual(sets["eligible_set_contamination_count"], 0)
        self.assertEqual(sets["full_eligible_member_keys"], ["original:q1:candidate1"])


class LiveSourceContractTests(unittest.TestCase):
    def test_live_sources_bind_exactly_127_existing_candidates(self) -> None:
        args = normalizer.parse_args(["--build"])
        sources = normalizer._load_source_candidates(args)
        self.assertEqual(len(sources), 127)
        self.assertEqual(
            len({source["source_candidate_key"] for source in sources}), 127
        )
        self.assertEqual(
            sum(source["source_cohort"] == "original" for source in sources), 93
        )
        self.assertEqual(
            sum(source["source_cohort"] == "crossed_author" for source in sources),
            34,
        )
        self.assertEqual(
            {source["source_author_id"] for source in sources if source["source_author_id"]},
            {"crossed_author_01", "crossed_author_02"},
        )

    def test_synthetic_normalization_is_valid_against_v0_2_schema(self) -> None:
        projection = _projection()
        record = normalizer.normalize_projection_v0_2(projection, _metadata(projection))
        validator = normalizer._validator(normalizer.DEFAULT_SCHEMA)
        self.assertEqual(list(validator.iter_errors(record)), [])


if __name__ == "__main__":
    unittest.main()
