from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data_construction" / "tools"
sys.path.insert(0, str(TOOLS))

import validate_ir_v0_2_reference as ir_reference


try:
    import jsonschema

    HAS_DRAFT_2020_12 = hasattr(jsonschema, "Draft202012Validator")
except ImportError:
    HAS_DRAFT_2020_12 = False


ARTIFACT = ROOT / ir_reference.DEFAULT_ARTIFACT
ARTIFACT_SHA256 = ir_reference.DEFAULT_ARTIFACT_SHA256


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_graph_id() -> str:
    with ARTIFACT.open("r", encoding="utf-8") as handle:
        return json.loads(next(handle))["graph"]["graph_id"]


@unittest.skipUnless(
    HAS_DRAFT_2020_12,
    "the preserved IR reference requires the pinned Draft 2020-12 validator",
)
class IrV02ReferenceTests(unittest.TestCase):
    def test_one_graph_passes_every_reference_check(self) -> None:
        graph_id = first_graph_id()
        result = ir_reference.validate_ir_v0_2_reference(
            artifact=ir_reference.DEFAULT_ARTIFACT,
            sha256=ARTIFACT_SHA256,
            graph_id=graph_id,
        )

        self.assertEqual(result["status"], "pass", result["errors"])
        self.assertEqual(result["requested_graph_id"], graph_id)
        self.assertEqual(result["counts"]["records"], 50)
        self.assertEqual(result["counts"]["graphs_selected"], 1)
        self.assertEqual(result["counts"]["graphs_validated"], 1)
        self.assertEqual(result["graphs"][0]["graph_id"], graph_id)
        self.assertIsInstance(result["graphs"][0]["question_id"], str)
        self.assertIsInstance(result["graphs"][0]["table_id"], str)
        self.assertEqual(result["runtime"]["ir_version"], "0.2")
        self.assertEqual(result["runtime"]["registry_version"], "0.2")
        self.assertIn("preserved_raw_output_parser", result["checks"])
        self.assertIn(
            "historical_constrained_planner_envelope_equality",
            result["checks"],
        )
        self.assertIn("all_graphs_draft_2020_12_valid", result["checks"])
        self.assertIn("all_graphs_ir_v0_2_registry_valid", result["checks"])

    def test_all_graphs_reproduce_observed_condition_c_counts(self) -> None:
        self.assertEqual(file_sha256(ARTIFACT), ARTIFACT_SHA256)
        result = ir_reference.validate_ir_v0_2_reference(all_graphs=True)

        self.assertEqual(result["status"], "pass", result["errors"])
        self.assertEqual(
            result["counts"],
            {
                "records": 50,
                "graphs_selected": 50,
                "graphs_validated": 50,
                "preserved_files_verified": 10,
                "nodes": 520,
                "parse_errors": 0,
                "schema_errors": 0,
                "validator_errors": 0,
                "validator_warnings": 455,
                "dead_node_warnings": 455,
            },
        )
        self.assertEqual(result["error_code_counts"], {})
        self.assertEqual(result["warning_code_counts"], {"DEAD_NODE": 455})
        self.assertEqual(len(result["graphs"]), 50)
        self.assertTrue(all(graph["status"] == "pass" for graph in result["graphs"]))
        self.assertIn("preserved_bundle_git_authority", result["checks"])
        self.assertEqual(
            result["runtime"]["authority_identity"],
            ir_reference.APPROVED_AUTHORITY_COMMIT,
        )
        self.assertEqual(
            result["runtime"]["recovery_manifest_sha256"],
            ir_reference.RECOVERY_MANIFEST_SHA256,
        )

    def test_wrong_artifact_hash_is_rejected_before_record_selection(self) -> None:
        result = ir_reference.validate_ir_v0_2_reference(
            artifact=ir_reference.DEFAULT_ARTIFACT,
            sha256="0" * 64,
            graph_id=first_graph_id(),
        )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["counts"]["records"], 0)
        self.assertEqual(result["error_code_counts"], {"ARTIFACT_SHA256_MISMATCH": 1})
        self.assertEqual(result["artifact"]["observed_sha256"], ARTIFACT_SHA256)

    def test_missing_graph_id_is_rejected(self) -> None:
        result = ir_reference.validate_ir_v0_2_reference(
            artifact=ir_reference.DEFAULT_ARTIFACT,
            sha256=ARTIFACT_SHA256,
            graph_id="missing-graph-id",
        )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["error_code_counts"], {"GRAPH_ID_NOT_FOUND": 1})
        self.assertEqual(result["counts"]["records"], 50)
        self.assertEqual(result["counts"]["graphs_selected"], 0)

    def test_duplicate_top_level_graph_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".ir-v0-2-reference-", dir=ROOT) as directory:
            copy = Path(directory) / "duplicate.jsonl"
            contents = ARTIFACT.read_bytes()
            first_line = contents.splitlines(keepends=True)[0]
            copy.write_bytes(contents + first_line)
            relative = copy.relative_to(ROOT).as_posix()

            result = ir_reference.validate_ir_v0_2_reference(
                artifact=relative,
                sha256=file_sha256(copy),
                graph_id=first_graph_id(),
            )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["counts"]["records"], 51)
        self.assertEqual(result["error_code_counts"], {"DUPLICATE_GRAPH_ID": 1})

    def test_modified_preserved_runtime_or_registry_is_rejected_before_loading(self) -> None:
        historical_source = ROOT / "historical" / "ir_v0_2"
        modified_paths = (
            "src/hybridqa_graph/registry.py",
            "ir/operator_registry_v0_2.json",
        )
        for modified_relative in modified_paths:
            with self.subTest(path=modified_relative):
                with tempfile.TemporaryDirectory(
                    prefix=".ir-v0-2-project-copy-",
                    dir=ROOT,
                ) as directory:
                    project_copy = Path(directory)
                    historical_copy = project_copy / "historical" / "ir_v0_2"
                    shutil.copytree(
                        historical_source,
                        historical_copy,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                    )
                    modified = historical_copy / modified_relative
                    modified.write_bytes(modified.read_bytes() + b"\n")

                    with mock.patch.object(
                        ir_reference,
                        "_load_preserved_runtime",
                        side_effect=AssertionError("runtime loading must not occur"),
                    ) as runtime_loader:
                        result = ir_reference.validate_ir_v0_2_reference(
                            artifact=ir_reference.DEFAULT_ARTIFACT,
                            sha256=ARTIFACT_SHA256,
                            graph_id=first_graph_id(),
                            project_root=project_copy,
                        )

                    runtime_loader.assert_not_called()
                    self.assertEqual(result["status"], "fail")
                    self.assertNotIn("preserved_bundle_git_authority", result["checks"])
                    self.assertIn(
                        "PRESERVED_FILE_LIVE_SHA256_MISMATCH",
                        result["error_code_counts"],
                    )

    def test_failed_submodule_execution_removes_sys_modules_entry(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix=".ir-v0-2-bad-module-",
            dir=ROOT,
        ) as directory:
            source = Path(directory) / "broken.py"
            source.write_text("raise RuntimeError('expected failure')\n", encoding="utf-8")
            package_name = "_ir_v0_2_cleanup_test_package"
            qualified_name = f"{package_name}.broken"
            sys.modules.pop(qualified_name, None)

            with self.assertRaisesRegex(RuntimeError, "expected failure"):
                ir_reference._load_submodule(package_name, "broken", source)

            self.assertNotIn(qualified_name, sys.modules)

    def test_unexpected_preserved_validator_exception_is_machine_readable(self) -> None:
        runtime = ir_reference._load_preserved_runtime(str(ROOT.resolve()))
        with mock.patch.object(
            runtime.validator,
            "validate_graph",
            side_effect=RuntimeError("validator fixture failure"),
        ):
            result = ir_reference.validate_ir_v0_2_reference(
                graph_id=first_graph_id(),
            )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["counts"]["validator_errors"], 1)
        self.assertEqual(
            result["error_code_counts"],
            {"PRESERVED_VALIDATOR_EXCEPTION": 1},
        )

    def test_cli_one_and_all_modes_emit_json_summaries(self) -> None:
        one = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "validate_ir_v0_2_reference.py"),
                "--artifact",
                ir_reference.DEFAULT_ARTIFACT,
                "--sha256",
                ARTIFACT_SHA256,
                "--graph-id",
                first_graph_id(),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(one.returncode, 0, one.stderr)
        self.assertEqual(json.loads(one.stdout)["mode"], "one")

        all_graphs = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "validate_ir_v0_2_reference.py"),
                "--all",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(all_graphs.returncode, 0, all_graphs.stderr)
        all_summary = json.loads(all_graphs.stdout)
        self.assertEqual(all_summary["mode"], "all")
        self.assertEqual(all_summary["counts"]["graphs_validated"], 50)


if __name__ == "__main__":
    unittest.main()
