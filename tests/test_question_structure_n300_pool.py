from __future__ import annotations

import hashlib
import json
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
import analyze_ai_question_structure_cumulative_n300 as analyzer
import build_ai_question_structure_n300_pool as builder
from build_sample import QUESTION_ID_SET_HASH_ALGORITHM


class SyntheticN300Fixture:
    def __init__(self, temporary_root: Path) -> None:
        self.root = temporary_root / "project"
        self.root.mkdir(parents=True)
        self.paths: dict[str, Path] = {}
        all_ids = [f"q{index:04d}" for index in range(builder.EXPECTED_SOURCE_COUNT)]
        historical_ids = set(all_ids[-builder.EXPECTED_HISTORICAL_COUNT :])
        locked_ids = sorted(historical_ids)[: builder.EXPECTED_LOCKED_COUNT]
        eligible = sorted(
            (value for value in all_ids if value not in historical_ids),
            key=lambda value: _common.stable_rank(builder.SEED, value),
        )
        self.all_ids = all_ids
        self.historical_ids = historical_ids
        self.eligible = eligible
        self.selected = eligible[: builder.CUMULATIVE_TARGET]
        self.added = self.selected[builder.PREFIX_RECORD_COUNT :]
        self.reserve = eligible[builder.CUMULATIVE_TARGET :]

        questions = [
            {"question_id": question_id, "question": f"Question for {question_id}?"}
            for question_id in all_ids
        ]
        questions_path = self._json("inputs/dev.json", questions)
        source_sha = self._sha(questions_path)
        source_set_sha = _common.canonical_string_set_sha256(all_ids)
        self.source_reference = {
            "source_id": "synthetic_hybridqa",
            "pinned_commit": "1" * 40,
            "artifact_path": "released_data/dev.json",
            "artifact_sha256": source_sha,
            "record_count": builder.EXPECTED_SOURCE_COUNT,
            "question_id_set_sha256": source_set_sha,
        }
        self._json("inputs/source_manifest.json", {"schema_version": "source_manifest_v0_1"})
        self._json(
            "inputs/source_question_ids.json",
            {
                "schema_version": "hybridqa_source_question_ids_v0_1",
                "artifact_sha256": source_sha,
                "question_id_set_hash_algorithm": QUESTION_ID_SET_HASH_ALGORITHM,
                "question_ids": all_ids,
            },
        )
        self._json(
            "inputs/historical.json",
            {
                "schema_version": "historical_exposed_ids_v0_1",
                "audit_status": "complete",
                "is_complete": True,
                "counts": {
                    "exposed_unique": builder.EXPECTED_HISTORICAL_COUNT,
                    "locked_eval_unique": builder.EXPECTED_LOCKED_COUNT,
                },
                "exposed_question_ids": sorted(historical_ids),
                "locked_eval_question_ids": locked_ids,
            },
        )
        self._json(
            "inputs/locked.json",
            {
                "role": "locked_eval",
                "size": builder.EXPECTED_LOCKED_COUNT,
                "ids": locked_ids,
            },
        )
        self._json(
            "inputs/split.json",
            {
                "schema_version": "split_manifest_v0_1",
                "release_eligible": True,
                "override_used": False,
                "counts": {
                    "annotation_dev": 0,
                    "annotation_schema_pilot": 30,
                    "annotation_train": 0,
                    "locked_eval": 0,
                },
                "roles": {"annotation_schema_pilot": self.selected[:30]},
            },
        )
        self._json(
            "inputs/study_plan.json",
            {
                "schema_version": "question_structure_study_plan_v0_2",
                "sampling_contract": {"cumulative_targets": [30, 100, 300, 1000]},
                "stage_gates": {
                    "n1000": {
                        "status": "conditional_not_yet_allocated",
                        "trigger": (
                            "material_recurring_new_families_OR_high_singleton_mass_"
                            "OR_nonflattening_curve_at_n300"
                        ),
                        "same_extractor_and_normalizer_required": True,
                    }
                },
            },
        )

        n100_views = [
            {
                "schema_version": builder.VIEW_SCHEMA_VERSION,
                "visibility": builder.VIEW_VISIBILITY,
                "question_id": question_id,
                "question": f"Question for {question_id}?",
            }
            for question_id in self.selected[: builder.PREFIX_RECORD_COUNT]
        ]
        n100_views_path = self._jsonl("inputs/question_only_views_n100.jsonl", n100_views)
        self._json(
            "inputs/pool_v0_1.json",
            {
                "schema_version": "ai_question_structure_exploration_pool_manifest_v0_1",
                "selection": {
                    "selected_count": builder.PREFIX_RECORD_COUNT,
                    "selected_question_ids": self.selected[: builder.PREFIX_RECORD_COUNT],
                },
                "artifacts": {"views": {"sha256": self._sha(n100_views_path)}},
            },
        )
        self._json(
            "inputs/exposure_v0_1.json",
            {
                "schema_version": "question_exposure_ledger_v0_1",
                "ai_question_structure_exploration": {
                    "count": builder.PREFIX_RECORD_COUNT,
                    "question_ids": self.selected[: builder.PREFIX_RECORD_COUNT],
                    "future_unseen_evaluation_allowed": False,
                },
            },
        )
        self._jsonl(
            "inputs/records_n100.jsonl",
            [
                {"question_id": question_id}
                for question_id in self.selected[: builder.PREFIX_RECORD_COUNT]
            ],
        )
        self._json(
            "inputs/exploration_plan_n100.json",
            {
                "schema_version": "ai_question_structure_scale_exploration_plan_v0_1",
                "run_id": builder.FROZEN_RECORD_RUN_ID,
                "status": "contract_frozen_before_model_outputs",
            },
        )
        self._json(
            "inputs/run_manifest_n100.json",
            {
                "schema_version": "ai_question_structure_scale_run_manifest_v0_1",
                "run_id": builder.FROZEN_RECORD_RUN_ID,
                "run_status": "complete",
            },
        )
        self._text(
            "inputs/prompt.md",
            "Process only the assigned records from the frozen N=100 question-only view.\n",
        )
        self._json(
            "inputs/record_schema.json",
            {"properties": {"run_id": {"const": builder.FROZEN_RECORD_RUN_ID}}},
        )
        for name in (
            "frozen_analyzer.py",
            "builder.py",
            "builder_test.py",
            "cumulative_analyzer.py",
            "cumulative_analyzer_test.py",
        ):
            self._text(f"inputs/{name}", f"# {name}\n")

        self.partition_inputs = {
            partition: self.root / f"outputs/inputs/{partition}.jsonl"
            for partition in builder.PRODUCER_PARTITIONS
        }
        self.planned_parts = {
            partition: self.root / f"planned/parts/{partition}.jsonl"
            for partition in builder.PRODUCER_PARTITIONS
        }
        cumulative_dir = self.root / "planned/cumulative"
        self.cumulative_outputs = builder._cumulative_output_paths(
            cumulative_dir,
            self.root / "planned/manifests/question_exposure_ledger_v0_3.json",
        )
        self.kwargs = {
            "questions_path": questions_path,
            "project_root": self.root,
            "historical_path": self.paths["inputs/historical.json"],
            "locked_path": self.paths["inputs/locked.json"],
            "source_manifest_path": self.paths["inputs/source_manifest.json"],
            "source_ids_path": self.paths["inputs/source_question_ids.json"],
            "split_path": self.paths["inputs/split.json"],
            "study_plan_path": self.paths["inputs/study_plan.json"],
            "n100_views_path": n100_views_path,
            "n100_pool_path": self.paths["inputs/pool_v0_1.json"],
            "n100_exposure_path": self.paths["inputs/exposure_v0_1.json"],
            "n100_records_path": self.paths["inputs/records_n100.jsonl"],
            "n100_exploration_plan_path": self.paths[
                "inputs/exploration_plan_n100.json"
            ],
            "n100_run_manifest_path": self.paths["inputs/run_manifest_n100.json"],
            "prompt_path": self.paths["inputs/prompt.md"],
            "record_schema_path": self.paths["inputs/record_schema.json"],
            "frozen_analyzer_path": self.paths["inputs/frozen_analyzer.py"],
            "builder_path": self.paths["inputs/builder.py"],
            "builder_test_path": self.paths["inputs/builder_test.py"],
            "cumulative_analyzer_path": self.paths["inputs/cumulative_analyzer.py"],
            "cumulative_analyzer_test_path": self.paths[
                "inputs/cumulative_analyzer_test.py"
            ],
            "output_views_path": self.root / "outputs/question_only_views_n300.jsonl",
            "output_pool_path": self.root / "outputs/pool_v0_2.json",
            "output_exposure_path": self.root / "outputs/exposure_v0_2.json",
            "output_routing_path": self.root / "outputs/routing.json",
            "output_plan_path": self.root / "outputs/plan.json",
            "partition_input_paths": self.partition_inputs,
            "planned_model_output_paths": self.planned_parts,
            "cumulative_output_paths": self.cumulative_outputs,
        }

    def _path(self, relative: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        self.paths[relative] = path
        return path

    def _json(self, relative: str, value: object) -> Path:
        path = self._path(relative)
        path.write_bytes(_common.json_file_bytes(value))
        return path

    def _jsonl(self, relative: str, values: list[dict[str, object]]) -> Path:
        path = self._path(relative)
        path.write_bytes(_common.jsonl_file_bytes(values))
        return path

    def _text(self, relative: str, value: str) -> Path:
        path = self._path(relative)
        path.write_text(value, encoding="utf-8")
        return path

    @staticmethod
    def _sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def build(self, **overrides: object) -> dict[str, tuple[Path, bytes]]:
        kwargs = dict(self.kwargs)
        kwargs.update(overrides)
        with mock.patch.object(builder, "historical_release_errors", return_value=[]), mock.patch.object(
            builder, "verify_source_manifest", return_value=self.source_reference
        ):
            return builder.build_n300_bundle(**kwargs)


class N300PoolBuilderTests(unittest.TestCase):
    def test_live_rank_reconstructs_exact_n300_selection_hashes(self) -> None:
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
        n100_pool = json.loads(
            (
                ROOT
                / "data_construction/manifests/ai_question_structure_exploratory_pool_v0_1.json"
            ).read_text(encoding="utf-8")
        )
        historical_ids = set(historical["exposed_question_ids"])
        locked_ids = set(historical["locked_eval_question_ids"])
        eligible = [value for value in source["question_ids"] if value not in historical_ids]
        eligible.sort(key=lambda value: _common.stable_rank(builder.SEED, value))
        selected = eligible[:300]
        added = selected[100:]
        reserve = eligible[300:]
        self.assertEqual(len(eligible), 3366)
        self.assertEqual(selected[:100], n100_pool["selection"]["selected_question_ids"])
        self.assertEqual(
            _common.canonical_json_sha256(selected),
            "86a7f610ebda71c845651f19e8d1f82006cce7cac134ceafda8123ac2c2c4b78",
        )
        self.assertEqual(
            _common.canonical_string_set_sha256(selected),
            "3e4cafb47cd68e6fc5d0951b9c64bcd52df18c26b07b8734a6908df2786c426e",
        )
        self.assertEqual(
            _common.canonical_json_sha256(added),
            "5f5c785c7937df784e14a5acb5c17aca3a45b34b6119dcd5def9034554ea0838",
        )
        self.assertEqual(
            _common.canonical_string_set_sha256(added),
            "761fd70ca4eaa3a08c092d0e5be064c57d11c026c0d758fc5778b0a8ec058181",
        )
        self.assertEqual(
            _common.canonical_string_set_sha256(reserve),
            "daeac15db023af58e5255cd5d6d065ac6035ea62fa0ed3bee65c426be710e774",
        )
        self.assertEqual((added[0], added[-1]), ("67f5d01fa7df9bed", "e1d41c4b15f3187e"))
        self.assertFalse(set(selected) & historical_ids)
        self.assertFalse(set(selected) & locked_ids)
        self.assertEqual(len(reserve), 3066)
        self.assertEqual(historical_ids | set(selected) | set(reserve), set(source["question_ids"]))

    def test_bundle_preserves_prefix_and_emits_safe_balanced_routing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticN300Fixture(Path(temporary))
            batch = fixture.build()
            self.assertEqual(
                set(batch),
                {
                    "views",
                    "pool_manifest",
                    "exposure_ledger",
                    "routing_manifest",
                    "combined_plan",
                    *(f"input_{partition}" for partition in builder.PRODUCER_PARTITIONS),
                },
            )
            self.assertTrue(all(not path.exists() for path, _ in batch.values()))

            views = [
                json.loads(line)
                for line in batch["views"][1].decode("utf-8").splitlines()
            ]
            prefix_bytes = fixture.kwargs["n100_views_path"].read_bytes()
            self.assertEqual(len(views), 300)
            self.assertTrue(batch["views"][1].startswith(prefix_bytes))
            self.assertEqual([view["question_id"] for view in views], fixture.selected)
            self.assertTrue(
                all(
                    set(view) == {"schema_version", "visibility", "question_id", "question"}
                    for view in views
                )
            )

            routing = json.loads(batch["routing_manifest"][1])
            assignments = routing["assignments"]
            self.assertEqual([item["committed_position"] for item in assignments], list(range(101, 301)))
            self.assertEqual([item["question_id"] for item in assignments], fixture.added)
            self.assertEqual(
                Counter(item["producer_partition"] for item in assignments),
                Counter({partition: 40 for partition in builder.PRODUCER_PARTITIONS}),
            )
            for start in range(101, 301, 10):
                block = [item for item in assignments if start <= item["committed_position"] < start + 10]
                self.assertEqual(
                    Counter(item["producer_partition"] for item in block),
                    Counter({partition: 2 for partition in builder.PRODUCER_PARTITIONS}),
                )
            for item in assignments:
                self.assertEqual(
                    item["question_view_sha256"],
                    _common.canonical_json_sha256(views[item["committed_position"] - 1]),
                )
                self.assertEqual(
                    set(item),
                    {
                        "committed_position",
                        "question_id",
                        "question_view_sha256",
                        "producer_partition",
                    },
                )

            routed_ids: list[str] = []
            for partition in builder.PRODUCER_PARTITIONS:
                records = [
                    json.loads(line)
                    for line in batch[f"input_{partition}"][1].decode("utf-8").splitlines()
                ]
                self.assertEqual(len(records), 40)
                self.assertTrue(
                    all(
                        set(record)
                        == {"schema_version", "visibility", "question_id", "question"}
                        for record in records
                    )
                )
                routed_ids.extend(record["question_id"] for record in records)
            self.assertEqual(set(routed_ids), set(fixture.added))
            self.assertEqual(len(routed_ids), len(set(routed_ids)))

    def test_manifests_preserve_pending_exposure_and_combined_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticN300Fixture(Path(temporary))
            batch = fixture.build()
            pool = json.loads(batch["pool_manifest"][1])
            exposure = json.loads(batch["exposure_ledger"][1])
            plan = json.loads(batch["combined_plan"][1])

            self.assertEqual(pool["schema_version"], builder.POOL_SCHEMA_VERSION)
            self.assertEqual(pool["selection"]["selected_count"], 300)
            self.assertEqual(pool["selection"]["preserved_prefix_count"], 100)
            self.assertEqual(pool["selection"]["added_count"], 200)
            self.assertEqual(pool["selection"]["unexposed_unallocated_reserve_count"], 3066)
            self.assertFalse(pool["selection"]["reserve_question_text_materialized"])
            self.assertEqual(pool["partition_check"]["locked_eval_overlap_count"], 0)
            self.assertFalse(pool["artifacts"]["split_manifest_v0_1"]["modified"])

            self.assertEqual(exposure["schema_version"], builder.EXPOSURE_SCHEMA_VERSION)
            self.assertEqual(exposure["ai_question_structure_exploration"]["processed_prefix_count"], 100)
            self.assertEqual(
                exposure["ai_question_structure_exploration"]["selected_pending_processing_count"],
                200,
            )
            self.assertFalse(
                exposure["ai_question_structure_exploration"][
                    "future_unseen_evaluation_allowed"
                ]
            )
            self.assertEqual(exposure["unexposed_unallocated_reserve"]["count"], 3066)
            self.assertEqual(
                exposure["completion_versioning_policy"][
                    "all_300_processed_requires_new_ledger_version"
                ],
                "question_exposure_ledger_v0_3",
            )
            self.assertFalse(
                exposure["completion_versioning_policy"]["overwrite_v0_2_on_completion"]
            )

            self.assertEqual(plan["schema_version"], builder.PLAN_SCHEMA_VERSION)
            self.assertEqual(plan["analysis_id"], builder.ANALYSIS_ID)
            self.assertEqual(
                plan["status"], "contract_frozen_before_positions_101_300_model_outputs"
            )
            self.assertEqual((plan["cumulative_target"], plan["prefix_record_count"]), (300, 100))
            self.assertEqual(plan["question_ids"], fixture.selected)
            self.assertEqual(plan["assignments"], json.loads(batch["routing_manifest"][1])["assignments"])
            self.assertFalse(plan["legacy_prompt_wording_caveat"]["prompt_bytes_changed_for_n300"])
            self.assertTrue(plan["generation_contract"]["same_deterministic_normalizer_as_n100"])
            self.assertFalse(plan["generation_contract"]["statistical_independence_claimed"])
            self.assertFalse(plan["generation_contract"]["external_lookup_allowed"])
            self.assertEqual(
                plan["generation_contract"], analyzer.EXPECTED_GENERATION_CONTRACT
            )
            self.assertEqual(
                plan["normalization_contract"], analyzer.EXPECTED_NORMALIZATION_CONTRACT
            )
            self.assertEqual(
                plan["normalization_contract"],
                {
                    "transitive_reduction": True,
                    "exact_node_ID_and_array_order_invariant_canonicalization": True,
                    "signature_levels": [
                        "fine_semantic_dag",
                        "contracted_semantic_dag",
                        "topology_shape",
                        "task",
                    ],
                    "same_role_linear_split_merge_contraction": True,
                    "model_output_trusted_for_signature": False,
                    "post_hoc_semantic_cluster_merging_in_primary_metrics": False,
                },
            )
            wrapper = plan["producer_administrative_wrapper"]
            self.assertEqual(
                wrapper["worker_context"],
                "fresh_fork_none_no_inherited_conversation_context",
            )
            self.assertEqual(
                wrapper["required_placeholders"],
                ["{producer_partition}", "{input_path}", "{output_path}"],
            )
            for placeholder in wrapper["required_placeholders"]:
                self.assertIn(placeholder, wrapper["template"])
            self.assertIn("Read only the frozen prompt", wrapper["template"])
            self.assertIn("Do not inspect any other repository artifact", wrapper["template"])
            self.assertIn("Preserve input order", wrapper["template"])
            self.assertIn("Write only the assigned output", wrapper["template"])

            trigger = plan["precommitted_n1000_decision"]
            self.assertEqual(trigger, analyzer.PRECOMMITTED_N1000_DECISION)
            self.assertEqual(trigger["trigger_composition"], "ANY")
            self.assertEqual(len(trigger["trigger_conditions"]), 4)
            self.assertEqual(
                trigger["trigger_conditions"]["cumulative_contracted_singleton_question_mass"],
                {"operator": ">", "threshold": 0.05},
            )
            self.assertEqual(
                trigger["trigger_conditions"]["cumulative_OTHER_question_rate_above_0_05"],
                {"operator": ">", "threshold": 0.05},
            )
            self.assertEqual(
                trigger["trigger_conditions"][
                    "material_cross_partition_new_contracted_families"
                ]["minimum_fixed_ten_question_block_support_per_family"],
                2,
            )
            self.assertEqual(trigger["triggered_decision"], "EXPAND_UNCHANGED_TO_N1000")
            self.assertEqual(
                trigger["no_trigger_decision"],
                "FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_ENVIRONMENT_REALIZATION",
            )
            self.assertEqual(
                trigger["invalid_run_decision"], "NO_DECISION_INVALID_CONTRACT_OR_RECORDS"
            )
            self.assertEqual(
                plan["planned_outputs"]["cumulative_analysis"][
                    "completion_exposure_ledger"
                ]["repository_relative_path"],
                "planned/manifests/question_exposure_ledger_v0_3.json",
            )
            routing = json.loads(batch["routing_manifest"][1])
            self.assertEqual(
                routing["model_visible_input_contract"],
                analyzer.EXPECTED_ROUTING_MODEL_VISIBLE_INPUT_CONTRACT,
            )

            bindings = {
                item["repository_relative_path"]: item["sha256"]
                for item in plan["source_artifacts"] + plan["contract_artifacts"]
            }
            for label in ("views", "pool_manifest", "exposure_ledger", "routing_manifest"):
                path, payload = batch[label]
                self.assertEqual(bindings[path.relative_to(fixture.root).as_posix()], hashlib.sha256(payload).hexdigest())
            self.assertIn("inputs/records_n100.jsonl", bindings)
            self.assertIn("inputs/exploration_plan_n100.json", bindings)
            self.assertIn("inputs/run_manifest_n100.json", bindings)
            self.assertIn("inputs/prompt.md", bindings)
            self.assertIn("inputs/record_schema.json", bindings)
            self.assertIn("inputs/frozen_analyzer.py", bindings)

    def test_atomic_write_once_and_collision_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticN300Fixture(Path(temporary))
            batch = fixture.build()
            statuses = _common.write_output_batch(batch)
            self.assertEqual(set(statuses.values()), {"written"})
            self.assertEqual(set(_common.write_output_batch(batch).values()), {"unchanged"})

            pool_path = batch["pool_manifest"][0]
            views_path = batch["views"][0]
            views_before = views_path.read_bytes()
            pool_path.write_text("different\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists with different bytes"):
                _common.write_output_batch(batch)
            self.assertEqual(views_path.read_bytes(), views_before)

        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticN300Fixture(Path(temporary))
            with self.assertRaisesRegex(builder.N300PoolContractError, "collides with input"):
                fixture.build(output_views_path=fixture.kwargs["questions_path"])
            self.assertFalse(fixture.kwargs["output_pool_path"].exists())

    def test_refuses_stale_planned_outputs_before_freezing_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticN300Fixture(Path(temporary))
            stale_part = fixture.planned_parts["partition_06"]
            stale_part.parent.mkdir(parents=True, exist_ok=True)
            stale_part.write_text("stale\n", encoding="utf-8")
            with self.assertRaisesRegex(
                builder.N300PoolContractError,
                "planned output must not exist at selection-contract freeze",
            ):
                fixture.build()
            self.assertFalse(fixture.kwargs["output_views_path"].exists())
            self.assertFalse(fixture.kwargs["output_plan_path"].exists())

    def test_defaults_preserve_frozen_paths_and_n100_hashes(self) -> None:
        self.assertEqual(
            builder.DEFAULT_ROUTING.relative_to(ROOT).as_posix(),
            "data_construction/exploration/ai_question_structure_scale_v0_1/"
            "n300_extension_v0_1/producer_routing_manifest_v0_1.json",
        )
        self.assertEqual(
            builder.DEFAULT_INPUT_DIR.relative_to(ROOT).as_posix(),
            "data_construction/exploration/ai_question_structure_scale_v0_1/"
            "n300_extension_v0_1/inputs",
        )
        self.assertEqual(
            builder.DEFAULT_MODEL_PARTS_DIR.relative_to(ROOT).as_posix(),
            "data_construction/exploration/ai_question_structure_scale_v0_1/"
            "n300_extension_v0_1/parts",
        )
        expected_hashes = {
            "data_construction/tools/build_ai_question_structure_exploration_pool.py": (
                "7b963165b4240ee35bf3bd66473ab5421c6bdad734198fec0a1a7caf39a74074"
            ),
            "tests/test_question_structure_scale_exploration.py": (
                "0510fd7928cefa833514d12c575ad0d61ef3e97a52813e7e3d50a2c3b0f2bcc1"
            ),
            "data_construction/exploration/ai_question_structure_scale_v0_1/"
            "pool/question_only_views_n100.jsonl": (
                "8cece2fdc33776a077ed32b3dd88d023c9d89273876683b109c6f0f24fc5d14d"
            ),
            "data_construction/manifests/ai_question_structure_exploratory_pool_v0_1.json": (
                "fa89d07a35582936f3824f90cf36476b9035ca01257b119c84d434ca77f7ff96"
            ),
            "data_construction/manifests/question_exposure_ledger_v0_1.json": (
                "681c3e8c8d0fd7490c88e8e8085b6c9421008223f97cc9d5baefd59801ae6b7c"
            ),
            "data_construction/manifests/split_manifest_v0_1.json": (
                "9de7124ab4b3b7a213a0970c0a2c51c0d6353f5eb01d9ce8b60f9250440bcfc8"
            ),
            "data_construction/exploration/ai_question_structure_scale_v0_1/"
            "run_001/records.jsonl": (
                "9e7dc9d48f98a8b9d73dde96f0f61836463578efca6aae67b3bd2d1806c30eef"
            ),
            "data_construction/exploration/ai_question_structure_scale_v0_1/"
            "prompts/primary_extraction_v0_1.md": (
                "081007e4006fd1f41aa53c30a8690bc6f9b388fba43b2a022ed1d5b7022cdc0f"
            ),
            "data_construction/exploration/ai_question_structure_scale_v0_1/"
            "contracts/semantic_backbone_record_schema_v0_1.json": (
                "22663e1d8cd2b56c99cd6ee95493384a8cc4a9ab845209ad3b783e9495ffebb4"
            ),
            "data_construction/tools/run_ai_question_structure_scale_exploration.py": (
                "56eaf5447594ccf2c49cc0f9697a3220b8053aca9da440cb5deda916bb721862"
            ),
            "data_construction/exploration/ai_question_structure_scale_v0_1/"
            "contracts/exploration_plan_v0_1.json": (
                "bce9bd4985105890d56537316eaf2c94615d364fcac0cfa6942122e7377a36ad"
            ),
            "data_construction/exploration/ai_question_structure_scale_v0_1/"
            "run_001/run_manifest.json": (
                "e8af6d6e13df38c0741167ee35f8806d366c796df8fdcf0e1f1f030ed7fa1917"
            ),
        }
        for relative, expected in expected_hashes.items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
