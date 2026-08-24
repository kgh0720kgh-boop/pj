from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction" / "tools"
sys.path.insert(0, str(TOOLS))

import _common
import build_ai_question_structure_exploration_pool as pool_builder
import run_ai_question_structure_diagnostic as old_diagnostic
import run_ai_question_structure_scale_exploration as exploration


try:
    import jsonschema

    HAS_DRAFT_2020_12 = hasattr(jsonschema, "Draft202012Validator")
except ImportError:
    HAS_DRAFT_2020_12 = False


def graph(nodes: list[tuple[str, str, list[str]]]) -> dict[str, object]:
    identifiers = [node_id for node_id, _, _ in nodes]
    depended_on = {dependency for _, _, dependencies in nodes for dependency in dependencies}
    return {
        "nodes": [
            {
                "node_id": node_id,
                "role": role,
                "other_role_description": None,
                "description": f"Perform {role}",
                "depends_on": dependencies,
                "source_cues": [],
                "implicit_rationale": "The dependency is implicit in the question.",
            }
            for node_id, role, dependencies in nodes
        ],
        "entry_node_ids": [
            node_id for node_id, _, dependencies in nodes if not dependencies
        ],
        "output_node_ids": [
            node_id for node_id in identifiers if node_id not in depended_on
        ],
    }


@unittest.skipUnless(HAS_DRAFT_2020_12, "Draft 2020-12 validator required")
class ScaleExplorationSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema = json.loads(exploration.SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        cls.validator = jsonschema.Draft202012Validator(schema)

    def valid_record(self) -> dict[str, object]:
        question = "Which city has the older station?"
        view = {
            "schema_version": "question_only_semantic_view_v0_1",
            "visibility": "question_only_no_environment_answer_or_proposals",
            "question_id": "q1",
            "question": question,
        }
        return {
            "schema_version": exploration.SCHEMA_VERSION,
            "run_id": exploration.RUN_ID,
            "evidence_class": exploration.EVIDENCE_CLASS,
            "producer_partition": "partition_01",
            "question_id": "q1",
            "question": question,
            "question_view_sha256": _common.canonical_json_sha256(view),
            "visibility": "question_only_no_environment_answer_or_proposals",
            "status": "complete",
            "answer_spec": {
                "kind": "entity",
                "cardinality": "one",
                "description": "The requested city.",
                "source_cues": ["Which city"],
                "implicit_rationale": None,
            },
            "primary_graph": graph(
                [
                    ("n1", "RESOLVE_REFERENT", []),
                    ("n2", "COMPARE", ["n1"]),
                ]
            ),
            "alternative_graphs": [],
            "uncertainty": {"present": False, "tags": [], "note": None},
            "not_representable_reason": None,
        }

    def test_minimal_record_schema_accepts_valid_question_only_graph(self) -> None:
        errors = list(self.validator.iter_errors(self.valid_record()))
        self.assertEqual(errors, [])

    def test_model_supplied_family_or_signature_is_rejected(self) -> None:
        for forbidden in ("family_id", "cluster_id", "topology_signature"):
            with self.subTest(forbidden=forbidden):
                value = self.valid_record()
                value[forbidden] = "model-supplied"
                self.assertTrue(list(self.validator.iter_errors(value)))

    def test_other_role_requires_explanation(self) -> None:
        value = self.valid_record()
        value["primary_graph"]["nodes"][0]["role"] = "OTHER"  # type: ignore[index]
        self.assertTrue(list(self.validator.iter_errors(value)))
        value["primary_graph"]["nodes"][0]["other_role_description"] = "Resolve a novel relation."  # type: ignore[index]
        self.assertEqual(list(self.validator.iter_errors(value)), [])


class ExactGraphCanonicalizationTests(unittest.TestCase):
    def test_signature_ignores_node_ids_node_order_and_dependency_order(self) -> None:
        left = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "ACQUIRE_PROPERTY", ["n1"]),
                ("n3", "ACQUIRE_PROPERTY", ["n1"]),
                ("n4", "COMPARE", ["n2", "n3"]),
            ]
        )
        right = graph(
            [
                ("n8", "COMPARE", ["n6", "n7"]),
                ("n7", "ACQUIRE_PROPERTY", ["n5"]),
                ("n5", "RESOLVE_REFERENT", []),
                ("n6", "ACQUIRE_PROPERTY", ["n5"]),
            ]
        )
        self.assertEqual(
            exploration.canonical_graph(left, "fine"),
            exploration.canonical_graph(right, "fine"),
        )

    def test_transitive_redundant_edge_does_not_change_signature(self) -> None:
        reduced = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "ACQUIRE_PROPERTY", ["n1"]),
                ("n3", "DERIVE", ["n2"]),
            ]
        )
        redundant = copy.deepcopy(reduced)
        redundant["nodes"][2]["depends_on"] = ["n1", "n2"]  # type: ignore[index]
        self.assertEqual(
            exploration.canonical_graph(reduced, "fine"),
            exploration.canonical_graph(redundant, "fine"),
        )

    def test_role_change_changes_fine_but_not_topology(self) -> None:
        left = graph([("n1", "RESOLVE_REFERENT", []), ("n2", "COMPARE", ["n1"])])
        right = graph([("n1", "RESOLVE_REFERENT", []), ("n2", "DERIVE", ["n1"])])
        self.assertNotEqual(
            exploration.canonical_graph(left, "fine"),
            exploration.canonical_graph(right, "fine"),
        )
        self.assertEqual(
            exploration.canonical_graph(left, "topology"),
            exploration.canonical_graph(right, "topology"),
        )

    def test_same_role_linear_split_changes_fine_but_not_contracted(self) -> None:
        one = graph([("n1", "ACQUIRE_PROPERTY", [])])
        split = graph(
            [
                ("n1", "ACQUIRE_PROPERTY", []),
                ("n2", "ACQUIRE_PROPERTY", ["n1"]),
            ]
        )
        self.assertNotEqual(
            exploration.canonical_graph(one, "fine"),
            exploration.canonical_graph(split, "fine"),
        )
        self.assertEqual(
            exploration.canonical_graph(one, "contracted"),
            exploration.canonical_graph(split, "contracted"),
        )

    def test_old_invariant_collision_is_separated_by_exact_signature(self) -> None:
        left = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "RESOLVE_REFERENT", ["n1"]),
                ("n3", "RESOLVE_REFERENT", ["n1"]),
                ("n4", "RESOLVE_REFERENT", ["n2"]),
                ("n5", "RESOLVE_REFERENT", ["n1"]),
            ]
        )
        right = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "RESOLVE_REFERENT", ["n1"]),
                ("n3", "RESOLVE_REFERENT", ["n2"]),
                ("n4", "RESOLVE_REFERENT", ["n2"]),
                ("n5", "RESOLVE_REFERENT", ["n1"]),
            ]
        )
        self.assertEqual(
            old_diagnostic.graph_invariants(left), old_diagnostic.graph_invariants(right)
        )
        self.assertNotEqual(
            exploration.canonical_graph(left, "topology"),
            exploration.canonical_graph(right, "topology"),
        )


class SaturationMetricTests(unittest.TestCase):
    def test_known_family_metrics_and_rarefaction(self) -> None:
        signatures = ["a", "a", "a", "b", "b", "c", "d", "e", "f", "g"]
        metrics = exploration._family_metrics(signatures, block_size=5)
        self.assertEqual(metrics["observed_family_count"], 7)
        self.assertEqual(metrics["singleton_family_count"], 5)
        self.assertEqual(metrics["doubleton_family_count"], 1)
        self.assertAlmostEqual(metrics["top_k_question_coverage"]["top_1"], 0.3)
        self.assertEqual(metrics["block_novelty_committed_order"][0]["new_family_count"], 2)
        self.assertEqual(metrics["block_novelty_committed_order"][1]["new_family_count"], 5)
        self.assertAlmostEqual(
            metrics["exact_rarefaction_order_independent"][-1]["expected_observed_families"],
            7.0,
        )

    def test_rarefaction_is_order_independent(self) -> None:
        left = exploration._family_metrics(["a", "a", "b", "c", "d", "d"])
        right = exploration._family_metrics(["d", "c", "a", "d", "b", "a"])
        self.assertEqual(
            left["exact_rarefaction_order_independent"],
            right["exact_rarefaction_order_independent"],
        )


class PortablePoolSelectionTests(unittest.TestCase):
    def test_tracked_id_rank_has_exact_existing_30_prefix_and_n100_partition(self) -> None:
        source = json.loads(
            (ROOT / "data_construction/manifests/source_question_ids.json").read_text(
                encoding="utf-8"
            )
        )
        historical = json.loads(
            (ROOT / "data_construction/manifests/historical_exposed_ids.json").read_text(
                encoding="utf-8"
            )
        )
        split = json.loads(
            (ROOT / "data_construction/manifests/split_manifest_v0_1.json").read_text(
                encoding="utf-8"
            )
        )
        historical_ids = set(historical["exposed_question_ids"])
        eligible = [value for value in source["question_ids"] if value not in historical_ids]
        eligible.sort(key=lambda value: _common.stable_rank(pool_builder.SEED, value))
        selected = eligible[:100]
        reserve = eligible[100:]
        self.assertEqual(len(eligible), 3366)
        self.assertEqual(selected[:30], split["roles"]["annotation_schema_pilot"])
        self.assertEqual(len(set(selected)), 100)
        self.assertFalse(set(selected) & historical_ids)
        self.assertEqual(len(reserve), 3266)
        self.assertEqual(historical_ids | set(selected) | set(reserve), set(source["question_ids"]))

    def test_study_plan_freezes_scale_and_truthfulness_contract(self) -> None:
        plan = json.loads(
            (ROOT / "data_construction/pilot/question_structure_study_plan_v0_2.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(plan["sampling_contract"]["cumulative_targets"], [30, 100, 300, 1000])
        self.assertEqual(plan["truthfulness_contract"]["current_decision"], "UNDECIDED_NEEDS_SCALE_EVIDENCE")
        self.assertFalse(plan["truthfulness_contract"]["gold_claimed"])
        self.assertFalse(plan["truthfulness_contract"]["common_executable_graph_claimed"])
        self.assertFalse(plan["targeted_robustness_audit"]["full_second_reviewer_lane_required"])


if __name__ == "__main__":
    unittest.main()
