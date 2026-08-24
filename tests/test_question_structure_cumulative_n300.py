from __future__ import annotations

import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction" / "tools"
sys.path.insert(0, str(TOOLS))

import _common
import analyze_ai_question_structure_cumulative_n300 as analyzer


def graph(nodes: list[tuple[str, str, list[str]]]) -> dict[str, object]:
    identifiers = [node_id for node_id, _, _ in nodes]
    depended_on = {dependency for _, _, dependencies in nodes for dependency in dependencies}
    return {
        "nodes": [
            {
                "node_id": node_id,
                "role": role,
                "other_role_description": (
                    "A provisional unmatched information-processing role."
                    if role == "OTHER"
                    else None
                ),
                "description": f"Perform {role}.",
                "source_cues": [],
                "implicit_rationale": "The operation is implicit in the question.",
                "depends_on": dependencies,
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


def question_view(index: int) -> dict[str, str]:
    return {
        "schema_version": "question_only_semantic_view_v0_1",
        "visibility": "question_only_no_environment_answer_or_proposals",
        "question_id": f"q{index:03d}",
        "question": f"Question {index:03d} asks for an entity.",
    }


def record_for(
    view: dict[str, str],
    partition: str,
    *,
    value: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": analyzer.frozen_n100.SCHEMA_VERSION,
        "run_id": analyzer.frozen_n100.RUN_ID,
        "evidence_class": analyzer.frozen_n100.EVIDENCE_CLASS,
        "producer_partition": partition,
        "question_id": view["question_id"],
        "question": view["question"],
        "question_view_sha256": _common.canonical_json_sha256(view),
        "visibility": "question_only_no_environment_answer_or_proposals",
        "status": "complete",
        "answer_spec": {
            "kind": "entity",
            "cardinality": "one",
            "description": "The requested entity.",
            "source_cues": ["entity"],
            "implicit_rationale": None,
        },
        "primary_graph": value or graph([("n1", "RESOLVE_REFERENT", [])]),
        "alternative_graphs": [],
        "uncertainty": {"present": False, "tags": [], "note": None},
        "not_representable_reason": None,
    }


def artifact(path: Path) -> dict[str, object]:
    return {
        "repository_relative_path": path.resolve().relative_to(ROOT).as_posix(),
        "sha256": _common.sha256_file(path),
    }


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.views_path = root / "question_only_views_n300.jsonl"
        self.routing_path = root / "producer_routing_manifest_v0_1.json"
        self.pool_path = root / "pool_manifest_v0_2.json"
        self.prior_exposure_path = root / "question_exposure_ledger_v0_2.json"
        self.prefix_path = root / "records_n100.jsonl"
        self.plan_path = root / "cumulative_n300_analysis_plan_v0_1.json"
        self.records_output = root / "outputs/records.jsonl"
        self.checks_output = root / "outputs/checks.jsonl"
        self.signatures_output = root / "outputs/derived_signatures.jsonl"
        self.metrics_output = root / "outputs/metrics.json"
        self.report_output = root / "outputs/report.md"
        self.manifest_output = root / "outputs/run_manifest.json"
        self.exposure_output = root / "outputs/question_exposure_ledger_v0_3.json"

        self.views = [question_view(index) for index in range(1, 301)]
        _common.write_jsonl(self.views_path, self.views)
        prefix = [record_for(view, "partition_01") for view in self.views[:100]]
        _common.write_jsonl(self.prefix_path, prefix)

        assignments: list[dict[str, object]] = []
        by_partition_views: dict[str, list[dict[str, str]]] = {
            partition: [] for partition in analyzer.EXPECTED_NEW_PARTITIONS
        }
        by_partition_records: dict[str, list[dict[str, object]]] = {
            partition: [] for partition in analyzer.EXPECTED_NEW_PARTITIONS
        }
        positions: dict[str, list[int]] = {
            partition: [] for partition in analyzer.EXPECTED_NEW_PARTITIONS
        }
        for position in range(101, 301):
            partition = analyzer.EXPECTED_NEW_PARTITIONS[(position - 101) % 5]
            view = self.views[position - 1]
            assignments.append(
                {
                    "committed_position": position,
                    "question_id": view["question_id"],
                    "question_view_sha256": _common.canonical_json_sha256(view),
                    "producer_partition": partition,
                }
            )
            by_partition_views[partition].append(view)
            by_partition_records[partition].append(record_for(view, partition))
            positions[partition].append(position)

        self.input_paths: dict[str, Path] = {}
        self.part_paths: list[Path] = []
        partition_artifacts: dict[str, dict[str, object]] = {}
        for partition in analyzer.EXPECTED_NEW_PARTITIONS:
            input_path = root / f"inputs/{partition}.jsonl"
            part_path = root / f"parts/{partition}.jsonl"
            _common.write_jsonl(input_path, by_partition_views[partition])
            _common.write_jsonl(part_path, by_partition_records[partition])
            self.input_paths[partition] = input_path
            self.part_paths.append(part_path)
            partition_artifacts[partition] = {
                "repository_relative_path": input_path.resolve().relative_to(ROOT).as_posix(),
                "record_count": 40,
                "sha256": _common.sha256_file(input_path),
                "bytes": input_path.stat().st_size,
                "committed_positions_ordered_sha256": _common.canonical_json_sha256(
                    positions[partition]
                ),
            }

        routing = {
            "schema_version": "ai_question_structure_n300_producer_routing_manifest_v0_1",
            "routing_id": "ai_question_structure_scale_v0_1_n300_routing_v0_1",
            "status": analyzer.PLAN_STATUS,
            "cumulative_target": 300,
            "prefix_record_count": 100,
            "expansion_record_count": 200,
            "algorithm": "position_round_robin_partition_04_through_08",
            "model_visible_input_contract": {
                "visible_fields": [
                    "schema_version",
                    "visibility",
                    "question_id",
                    "question",
                ],
                "routing_manifest_exposed": False,
                "producer_administrative_wrapper_exposed": True,
                "environment_answer_grounding_or_other_record_exposed": False,
                "shared_workspace_access_is_not_server_enforced": True,
                "worker_compliance_is_procedural": True,
            },
            "source_bindings": {"question_only_views": artifact(self.views_path)},
            "assignments": assignments,
            "partition_artifacts": partition_artifacts,
            "planned_model_outputs": {
                partition: {
                    "repository_relative_path": (
                        root / f"parts/{partition}.jsonl"
                    ).resolve().relative_to(ROOT).as_posix(),
                    "expected_record_count": 40,
                    "write_status": "not_created_selection_stage",
                }
                for partition in analyzer.EXPECTED_NEW_PARTITIONS
            },
            "evidence_boundary": {"human_evidence_count": 0, "gold_claimed": False},
        }
        _common.write_json(self.routing_path, routing)
        pool = {
            "schema_version": "ai_question_structure_exploration_pool_manifest_v0_2",
            "selection": {
                "current_target": 300,
                "selected_count": 300,
                "preserved_prefix_count": 100,
                "contract_development_prefix_count": 30,
                "added_count": 200,
                "selected_question_ids": [view["question_id"] for view in self.views],
                "unexposed_unallocated_reserve_count": 3066,
                "reserve_question_ids_set_sha256": "a" * 64,
            },
            "partition_check": {
                "historical_count": 100,
                "locked_eval_overlap_count": 0,
                "official_dev_count": 3466,
                "pairwise_disjoint": True,
                "selected_ai_exploration_count": 300,
                "unexposed_unallocated_reserve_count": 3066,
                "union_equals_official_dev": True,
            },
        }
        _common.write_json(self.pool_path, pool)
        _common.write_json(
            self.prior_exposure_path,
            {
                "schema_version": "question_exposure_ledger_v0_2",
                "status": "allocated",
                "historical_exposure": {
                    "manifest": "data_construction/manifests/historical_exposed_ids.json",
                    "count": 100,
                    "future_training_allowed": False,
                    "future_unseen_evaluation_allowed": False,
                },
            },
        )
        plan = {
            "schema_version": analyzer.PLAN_SCHEMA_VERSION,
            "analysis_id": analyzer.ANALYSIS_ID,
            "status": analyzer.PLAN_STATUS,
            "cumulative_target": 300,
            "prefix_record_count": 100,
            "expansion_record_count": 200,
            "record_run_id": analyzer.frozen_n100.RUN_ID,
            "question_ids": [view["question_id"] for view in self.views],
            "assignments": assignments,
            "precommitted_n1000_decision": copy.deepcopy(
                analyzer.PRECOMMITTED_N1000_DECISION
            ),
            "source_artifacts": [
                artifact(self.views_path),
                artifact(self.routing_path),
                artifact(self.pool_path),
                artifact(self.prior_exposure_path),
                artifact(self.prefix_path),
            ],
            "contract_artifacts": [
                artifact(Path(analyzer.__file__)),
                artifact(analyzer.FROZEN_ANALYZER),
                artifact(analyzer.DEFAULT_SCHEMA),
                artifact(analyzer.DEFAULT_PROMPT),
            ],
            "generation_contract": copy.deepcopy(analyzer.EXPECTED_GENERATION_CONTRACT),
            "normalization_contract": copy.deepcopy(
                analyzer.EXPECTED_NORMALIZATION_CONTRACT
            ),
            "producer_administrative_wrapper": (
                analyzer.expected_producer_administrative_wrapper(
                    analyzer.DEFAULT_PROMPT, analyzer.DEFAULT_SCHEMA
                )
            ),
            "legacy_prompt_wording_caveat": {
                "prompt_mentions_frozen_n100_view": True,
                "prompt_bytes_changed_for_n300": False,
                "operational_interpretation": (
                    "N=100 is legacy scope wording; for this unchanged-contract extension, "
                    "assigned records are positions 101-300 from the cumulative N=300 view"
                ),
                "semantic_instruction_change_claimed": False,
            },
            "planned_outputs": {
                "new_model_parts": {
                    partition: {
                        "repository_relative_path": (
                            root / f"parts/{partition}.jsonl"
                        ).resolve().relative_to(ROOT).as_posix(),
                        "expected_record_count": 40,
                    }
                    for partition in analyzer.EXPECTED_NEW_PARTITIONS
                },
                "cumulative_analysis": {
                    "records": {
                        "repository_relative_path": self.records_output.resolve().relative_to(ROOT).as_posix()
                    },
                    "checks": {
                        "repository_relative_path": self.checks_output.resolve().relative_to(ROOT).as_posix()
                    },
                    "derived_signatures": {
                        "repository_relative_path": self.signatures_output.resolve().relative_to(ROOT).as_posix()
                    },
                    "metrics": {
                        "repository_relative_path": self.metrics_output.resolve().relative_to(ROOT).as_posix()
                    },
                    "report": {
                        "repository_relative_path": self.report_output.resolve().relative_to(ROOT).as_posix()
                    },
                    "run_manifest": {
                        "repository_relative_path": self.manifest_output.resolve().relative_to(ROOT).as_posix()
                    },
                    "completion_exposure_ledger": {
                        "repository_relative_path": self.exposure_output.resolve().relative_to(ROOT).as_posix()
                    },
                },
            },
        }
        _common.write_json(self.plan_path, plan)

    def cli_args(self) -> list[str]:
        return [
            "--plan",
            str(self.plan_path),
            "--schema",
            str(analyzer.DEFAULT_SCHEMA),
            "--prompt",
            str(analyzer.DEFAULT_PROMPT),
            "--views",
            str(self.views_path),
            "--routing",
            str(self.routing_path),
            "--pool-manifest",
            str(self.pool_path),
            "--prior-exposure",
            str(self.prior_exposure_path),
            "--prefix-records",
            str(self.prefix_path),
            "--parts",
            *(str(path) for path in self.part_paths),
            "--records-output",
            str(self.records_output),
            "--checks-output",
            str(self.checks_output),
            "--signatures-output",
            str(self.signatures_output),
            "--metrics-output",
            str(self.metrics_output),
            "--report-output",
            str(self.report_output),
            "--run-manifest-output",
            str(self.manifest_output),
            "--exposure-output",
            str(self.exposure_output),
        ]


class CumulativeN300AnalysisTests(unittest.TestCase):
    def test_cli_merges_parts_preserves_prefix_and_emits_atomic_bundle(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            fixture = Fixture(Path(temporary))
            with mock.patch.object(
                analyzer, "verify_contract_freeze", return_value="f" * 40
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(analyzer.main(fixture.cli_args()), 0)
            self.assertTrue(fixture.records_output.read_bytes().startswith(fixture.prefix_path.read_bytes()))
            self.assertEqual(len(list(_common.iter_json_records(fixture.records_output))), 300)
            metrics = _common.read_json(fixture.metrics_output)
            self.assertEqual(
                set(metrics["signature_levels"]), set(analyzer.frozen_n100.SIGNATURE_KINDS)
            )
            normalized = metrics["graph_profiles"]["cumulative_n300"][
                "transitive_reduced_normalized_dependencies"
            ]
            self.assertEqual(normalized["branch_question_count"], 0)
            exposure = _common.read_json(fixture.exposure_output)
            self.assertEqual(exposure["contract_freeze_commit"], "f" * 40)
            self.assertEqual(exposure["historical_exposure"]["count"], 100)
            self.assertEqual(exposure["partition_check"]["locked_eval_overlap_count"], 0)
            processed = exposure["ai_question_structure_exploration"]
            self.assertEqual(
                (processed["processed_count"], processed["newly_processed_count"], processed["pending_count"]),
                (300, 200, 0),
            )
            self.assertFalse(processed["future_unseen_evaluation_allowed"])
            self.assertEqual(exposure["unexposed_unallocated_reserve"]["count"], 3066)
            manifest = _common.read_json(fixture.manifest_output)
            self.assertEqual(manifest["contract_freeze_commit"], "f" * 40)
            self.assertIn("records", manifest["outputs"])
            self.assertIn("completion_exposure_ledger", manifest["outputs"])

    def test_atomic_collision_does_not_rewrite_other_outputs(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            fixture = Fixture(Path(temporary))
            failure_stderr = io.StringIO()
            with mock.patch.object(
                analyzer, "verify_contract_freeze", return_value="f" * 40
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(analyzer.main(fixture.cli_args()), 0)
                metrics_before = fixture.metrics_output.read_bytes()
                fixture.report_output.write_text("collision\n", encoding="utf-8")
                with contextlib.redirect_stderr(failure_stderr):
                    self.assertEqual(analyzer.main(fixture.cli_args()), 1)
            self.assertEqual(fixture.metrics_output.read_bytes(), metrics_before)
            self.assertEqual(fixture.report_output.read_text(encoding="utf-8"), "collision\n")
            failure = json.loads(failure_stderr.getvalue())
            self.assertEqual(
                failure["n1000_decision"],
                analyzer.PRECOMMITTED_N1000_DECISION["invalid_run_decision"],
            )

    def test_plan_must_sha_pin_the_frozen_n100_analyzer(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            fixture = Fixture(Path(temporary))
            plan = _common.read_json(fixture.plan_path)
            analyzer_relative = analyzer.FROZEN_ANALYZER.relative_to(ROOT).as_posix()
            for item in plan["contract_artifacts"]:
                if item["repository_relative_path"] == analyzer_relative:
                    item["sha256"] = "0" * 64
            _common.write_json(fixture.plan_path, plan)
            with self.assertRaisesRegex(analyzer.N300AnalysisError, "artifact hash mismatch"):
                analyzer.validate_contract(
                    fixture.plan_path,
                    analyzer.DEFAULT_SCHEMA,
                    analyzer.DEFAULT_PROMPT,
                    fixture.views_path,
                    fixture.routing_path,
                    fixture.pool_path,
                    fixture.prior_exposure_path,
                    fixture.prefix_path,
                )

    def test_uncommitted_plan_cannot_claim_a_precommitted_run(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            fixture = Fixture(Path(temporary))
            plan = _common.read_json(fixture.plan_path)
            with self.assertRaisesRegex(analyzer.N300AnalysisError, "freeze commit"):
                analyzer.verify_contract_freeze(fixture.plan_path, plan)

    def test_producer_wrapper_is_exact_and_hash_clause_cannot_be_removed(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            fixture = Fixture(Path(temporary))
            plan = _common.read_json(fixture.plan_path)
            plan["producer_administrative_wrapper"]["template"] = plan[
                "producer_administrative_wrapper"
            ]["template"].replace("Compute question_view_sha256", "Supply question_view_sha256")
            _common.write_json(fixture.plan_path, plan)
            with self.assertRaisesRegex(
                analyzer.N300AnalysisError, "producer_administrative_wrapper"
            ):
                analyzer.validate_contract(
                    fixture.plan_path,
                    analyzer.DEFAULT_SCHEMA,
                    analyzer.DEFAULT_PROMPT,
                    fixture.views_path,
                    fixture.routing_path,
                    fixture.pool_path,
                    fixture.prior_exposure_path,
                    fixture.prefix_path,
                )

    def test_runtime_output_path_must_equal_frozen_plan(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            fixture = Fixture(Path(temporary))
            plan = _common.read_json(fixture.plan_path)
            with self.assertRaisesRegex(analyzer.N300AnalysisError, "metrics output differs"):
                analyzer._validate_planned_paths(
                    plan,
                    part_paths=fixture.part_paths,
                    cumulative_outputs={
                        "records": fixture.records_output,
                        "checks": fixture.checks_output,
                        "derived_signatures": fixture.signatures_output,
                        "metrics": fixture.root / "unplanned_metrics.json",
                        "report": fixture.report_output,
                        "run_manifest": fixture.manifest_output,
                        "completion_exposure_ledger": fixture.exposure_output,
                    },
                )

    def test_exact_prefix_rejects_semantically_equal_reserialization(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            base = Path(temporary)
            prefix = base / "prefix.jsonl"
            cumulative = base / "cumulative.jsonl"
            prefix.write_bytes(b'{"a":1,"b":2}\n{"a":3,"b":4}\n')
            cumulative.write_bytes(b'{"b":2,"a":1}\n{"a":3,"b":4}\n{"a":5}\n')
            with self.assertRaisesRegex(analyzer.N300AnalysisError, "byte-for-byte"):
                analyzer.assert_exact_prefix_bytes(
                    cumulative, prefix, prefix_count=2, target_count=3
                )

    def test_four_signatures_delegate_to_frozen_normalizer(self) -> None:
        view = question_view(1)
        value = record_for(
            view,
            "partition_01",
            value=graph(
                [
                    ("n1", "RESOLVE_REFERENT", []),
                    ("n2", "ACQUIRE_PROPERTY", ["n1"]),
                ]
            ),
        )
        derived = analyzer.derive_signatures([value])[0]
        self.assertEqual(set(derived["signatures"]), set(analyzer.frozen_n100.SIGNATURE_KINDS))
        self.assertEqual(derived, analyzer.frozen_n100.signature_bundle(value))

    def test_raw_and_normalized_branch_join_are_separate(self) -> None:
        view = question_view(1)
        redundant = graph(
            [
                ("n1", "RESOLVE_REFERENT", []),
                ("n2", "ACQUIRE_PROPERTY", ["n1"]),
                ("n3", "DERIVE", ["n1", "n2"]),
            ]
        )
        profile = analyzer.raw_and_normalized_graph_profile(
            [record_for(view, "partition_01", value=redundant)]
        )
        raw = profile["raw_declared_dependencies_sensitivity"]
        reduced = profile["transitive_reduced_normalized_dependencies"]
        self.assertEqual((raw["branch_question_count"], raw["join_question_count"]), (1, 1))
        self.assertEqual((reduced["branch_question_count"], reduced["join_question_count"]), (0, 0))
        self.assertEqual(profile["removed_transitive_edge_count"], 1)

    def test_transfer_blocks_distinguish_baseline_unseen_from_sequential_novelty(self) -> None:
        signatures = ["a", "a", "b", "b", "b", "c"]
        transfer = analyzer.transfer_from_prefix(signatures, prefix_count=2)
        blocks = analyzer.expansion_block_novelty(signatures, prefix_count=2, block_size=2)
        self.assertEqual(transfer["questions_in_families_unseen_in_prefix"], 4)
        self.assertEqual(blocks[0]["sequential_novel_question_count"], 2)
        self.assertEqual(blocks[1]["sequential_novel_question_count"], 1)
        self.assertEqual(blocks[1]["n100_baseline_unseen_question_count"], 2)

    def test_partition_support_requires_count_partition_and_block_support(self) -> None:
        records = [
            {"question_id": "q1", "producer_partition": "partition_01"},
            {"question_id": "q2", "producer_partition": "partition_01"},
            {"question_id": "q3", "producer_partition": "partition_04"},
            {"question_id": "q4", "producer_partition": "partition_05"},
            {"question_id": "q5", "producer_partition": "partition_04"},
            {"question_id": "q6", "producer_partition": "partition_06"},
            {"question_id": "q7", "producer_partition": "partition_06"},
            {"question_id": "q8", "producer_partition": "partition_06"},
        ]
        signatures = ["known", "known", "x", "x", "x", "y", "y", "y"]
        support = analyzer.new_family_partition_support(
            records, signatures, prefix_count=2, block_size=2
        )
        self.assertEqual(support["recurring_new_family_count"], 2)
        self.assertEqual(support["cross_partition_recurring_new_family_count"], 1)
        self.assertEqual(support["material_cross_partition_recurring_new_family_count"], 1)

    def test_n1000_trigger_strict_boundaries_and_four_any_conditions(self) -> None:
        def blocks(novel_counts: list[int], families: list[list[str]]) -> list[dict[str, object]]:
            return [
                {
                    "positions": [251 + index * 10, 260 + index * 10],
                    "representable_questions": 10,
                    "sequential_novel_question_count": count,
                    "sequential_new_family_signatures": signature_values,
                }
                for index, (count, signature_values) in enumerate(zip(novel_counts, families))
            ]

        cumulative = {"singleton_question_mass": 0.05}
        support = {"material_cross_partition_recurring_new_family_count": 1}
        exact = analyzer.evaluate_n1000_trigger(
            cumulative,
            blocks([1, 1, 1, 1, 1], [["x"], ["y"], [], [], []]),
            support,
            cumulative_other_question_rate=0.05,
        )
        self.assertFalse(any(exact["trigger_values"].values()))
        self.assertEqual(
            exact["decision"], analyzer.PRECOMMITTED_N1000_DECISION["no_trigger_decision"]
        )

        cases = [
            ({"singleton_question_mass": 0.050001}, [0] * 5, [[]] * 5, support, 0.0),
            (cumulative, [0] * 5, [[]] * 5, support, 0.050001),
            (cumulative, [3, 3, 0, 0, 0], [["x"], ["y"], [], [], []], support, 0.0),
            (
                cumulative,
                [0] * 5,
                [[]] * 5,
                {"material_cross_partition_recurring_new_family_count": 2},
                0.0,
            ),
        ]
        for summary, novel, families, support_value, other_rate in cases:
            with self.subTest(case=(summary, novel, other_rate, support_value)):
                result = analyzer.evaluate_n1000_trigger(
                    summary,
                    blocks(novel, families),
                    support_value,
                    cumulative_other_question_rate=other_rate,
                )
                self.assertTrue(any(result["trigger_values"].values()))
                self.assertEqual(
                    result["decision"],
                    analyzer.PRECOMMITTED_N1000_DECISION["triggered_decision"],
                )


if __name__ == "__main__":
    unittest.main()
