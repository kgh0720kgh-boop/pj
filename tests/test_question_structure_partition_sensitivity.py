from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction" / "tools"
sys.path.insert(0, str(TOOLS))

import audit_ai_question_structure_partition_sensitivity as audit


def graph(nodes: list[tuple[str, str, list[str]]]) -> dict[str, object]:
    identifiers = [node_id for node_id, _, _ in nodes]
    depended_on = {dependency for _, _, dependencies in nodes for dependency in dependencies}
    return {
        "nodes": [
            {
                "node_id": node_id,
                "role": role,
                "depends_on": dependencies,
                "description": role,
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


def record(
    question_id: str,
    partition: str,
    value: dict[str, object],
    *,
    uncertain: bool = False,
) -> dict[str, object]:
    return {
        "run_id": audit.EXPECTED_RUN_ID,
        "producer_partition": partition,
        "question_id": question_id,
        "status": "uncertain" if uncertain else "complete",
        "primary_graph": value,
        "answer_spec": {"kind": "entity", "cardinality": "one"},
    }


class PartitionSensitivityAuditTests(unittest.TestCase):
    def test_partition_profiles_are_deterministic(self) -> None:
        rows = [
            record("q1", "partition_01", graph([("n1", "RESOLVE_REFERENT", [])])),
            record(
                "q2",
                "partition_01",
                graph(
                    [
                        ("n1", "RESOLVE_REFERENT", []),
                        ("n2", "ACQUIRE_PROPERTY", ["n1"]),
                    ]
                ),
                uncertain=True,
            ),
            record("q3", "partition_02", graph([("n1", "RESOLVE_REFERENT", [])])),
        ]
        profiles = audit.partition_profiles(rows)
        self.assertEqual([item["producer_partition"] for item in profiles], ["partition_01", "partition_02"])
        self.assertEqual(profiles[0]["record_count"], 2)
        self.assertEqual(profiles[0]["uncertain_rate"], 0.5)
        self.assertEqual(profiles[0]["mean_primary_node_count"], 1.5)

    def test_recurring_new_families_report_partition_support(self) -> None:
        known = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "ACQUIRE_PROPERTY", ["n1"]),
            ]
        )
        local_new = graph(
            [
                ("n1", "ORDER_OR_EXTREMUM", []),
                ("n2", "ACQUIRE_PROPERTY", ["n1"]),
            ]
        )
        cross_new = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "AGGREGATE", ["n1"]),
            ]
        )
        rows = [
            record("q1", "partition_01", known),
            record("q2", "partition_01", known),
            record("q3", "partition_02", local_new),
            record("q4", "partition_02", local_new),
            record("q5", "partition_02", cross_new),
            record("q6", "partition_03", cross_new),
        ]
        value = audit.recurring_new_contracted_families(rows, 2)
        self.assertEqual(value["recurring_new_contracted_family_count"], 2)
        self.assertEqual(value["cross_partition_recurring_new_contracted_family_count"], 1)
        support = sorted(family["partition_support_count"] for family in value["families"])
        self.assertEqual(support, [1, 2])
        self.assertFalse(value["all_recurring_new_contracted_families_are_partition_local"])

    def test_raw_and_reduced_branch_join_profiles_differ_on_redundant_edges(self) -> None:
        redundant = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "ACQUIRE_PROPERTY", ["n1"]),
                ("n3", "ORDER_OR_EXTREMUM", ["n1", "n2"]),
            ]
        )
        genuine_join = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "RESOLVE_REFERENT", []),
                ("n3", "VERIFY", ["n1", "n2"]),
            ]
        )
        rows = [
            record("redundant", "partition_01", redundant),
            record("join", "partition_02", genuine_join),
        ]
        value = audit.raw_vs_reduced_graph_profile(rows)
        raw = value["raw_declared_dependencies"]
        reduced = value["transitive_reduced_dependencies"]
        self.assertEqual((raw["branch_question_count"], raw["join_question_count"]), (1, 2))
        self.assertEqual((reduced["branch_question_count"], reduced["join_question_count"]), (0, 1))
        self.assertEqual(value["removed_transitive_edge_count"], 1)
        self.assertEqual(value["questions_with_removed_transitive_edges"], ["redundant"])

    def test_same_role_contraction_inflates_dominant_family(self) -> None:
        simple = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "ACQUIRE_PROPERTY", ["n1"]),
            ]
        )
        split = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "RESOLVE_REFERENT", ["n1"]),
                ("n3", "ACQUIRE_PROPERTY", ["n2"]),
            ]
        )
        other = graph(
            [
                ("n1", "ORDER_OR_EXTREMUM", []),
                ("n2", "ACQUIRE_PROPERTY", ["n1"]),
            ]
        )
        rows = [
            record("q1", "partition_01", simple),
            record("q2", "partition_01", simple),
            record("q3", "partition_02", split),
            record("q4", "partition_03", other),
        ]
        value = audit.dominant_family_inflation(rows)
        self.assertEqual(value["fine_dominant_family_count"], 2)
        self.assertEqual(value["contracted_dominant_family_count"], 3)
        self.assertEqual(value["dominant_family_count_increase"], 1)
        self.assertEqual(
            value["question_ids_added_to_contracted_dominant_beyond_fine_dominant"],
            ["q3"],
        )
        self.assertFalse(value["same_role_contraction_establishes_semantic_equivalence"])

    def test_build_and_render_preserve_primary_decision(self) -> None:
        known = graph([("n1", "RESOLVE_REFERENT", [])])
        new = graph([("n1", "ORDER_OR_EXTREMUM", [])])
        rows = [
            record("q1", "partition_01", known),
            record("q2", "partition_01", known),
            record("q3", "partition_02", new),
            record("q4", "partition_02", new),
        ]
        primary_metrics = {
            "n100_precommitted_decision": {"decision": audit.EXPECTED_PRIMARY_DECISION}
        }
        metrics = audit.build_metrics(rows, primary_metrics, prefix_count=2)
        decision = metrics["primary_decision_preservation"]
        self.assertEqual(decision["precommitted_decision"], audit.EXPECTED_PRIMARY_DECISION)
        self.assertFalse(decision["changed_by_post_hoc_audit"])
        first = audit.render_addendum(metrics)
        second = audit.render_addendum(metrics)
        self.assertEqual(first, second)
        self.assertIn("conservative operational decision", first)
        self.assertIn("partition-confounded", first)
        json.dumps(metrics, sort_keys=True, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
