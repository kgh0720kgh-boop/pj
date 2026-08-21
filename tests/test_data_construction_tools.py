from __future__ import annotations

import json
import hashlib
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

import build_sample
import compare_operator_granularity
import validate_annotation


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def write_pass_validation_checks(
    path: Path,
    annotations_path: Path,
    records: list[dict[str, object]],
) -> None:
    artifact_sha256 = hashlib.sha256(annotations_path.read_bytes()).hexdigest()
    write_jsonl(
        path,
        [
            {
                "question_id": record["question_id"],
                "validator_version": "annotation_validator_v0_1",
                "annotation_canonical_sha256": canonical_sha256(record),
                "validation_context": {
                    "annotations_artifact_sha256": artifact_sha256,
                    "schema_artifact_sha256": "a" * 64,
                    "operator_vocabulary_artifact_sha256": "b" * 64,
                    "validation_mode": "draft_2020_12_plus_structural",
                },
                "status": "pass",
                "errors": [],
                "warnings": [],
            }
            for record in records
        ],
    )


def run_tool(name: str, *arguments: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOLS / name), *(str(argument) for argument in arguments)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def complete_history_manifest() -> dict[str, object]:
    source_ids = {
        "data_analysis/week1_sample_100.jsonl": [f"w1_{index}" for index in range(100)],
        "evaluation/week2_eval_ids.json": [f"w2_{index}" for index in range(50)],
        "evaluation/week3_engineering_dev_ids.json": ["w3_engineering"],
        "evaluation/week3_locked_eval_ids.json": ["w3_locked"],
        "evaluation/week3_split_manifest.json": ["w3_pilot", "w3_train", "w3_dev", "w3_split_locked"],
    }
    exposed = sorted({identifier for identifiers in source_ids.values() for identifier in identifiers})
    return {
        "schema_version": "historical_exposed_ids_v0_1",
        "audit_status": "complete",
        "is_complete": True,
        "recovery_provenance_status": "verified",
        "recovery_provenance_errors": [],
        "recovery_provenance": {
            "schema_version": "historical_recovery_provenance_v0_1",
            "status": "researcher_approved_authoritative",
            "authority_kind": "git_commit",
            "authority_identity": "a" * 40,
            "verification": "verified",
        },
        "missing_required_files": [],
        "required_files_with_no_question_ids": [],
        "known_expected_count_mismatches": [],
        "source_files": [
            {
                "path": path,
                "status": "present",
                "question_id_count": len(identifiers),
                "sha256": "0" * 64,
            }
            for path, identifiers in source_ids.items()
        ],
        "source_question_ids": source_ids,
        "exposed_question_ids": exposed,
        "locked_eval_question_ids": ["w3_locked", "w3_split_locked"],
        "forbidden_future_training_ids": exposed,
    }


class BuildSampleTests(unittest.TestCase):
    def test_release_refuses_outputs_outside_project_root_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            project.mkdir()
            questions = base / "official-dev.json"
            history = project / "history.json"
            source_manifest = project / "source.json"
            write_json(questions, [{"question_id": "fresh", "question": "Question?", "table_id": "t1"}])
            write_json(history, complete_history_manifest())
            write_json(source_manifest, {})
            verified_source = {
                "source_id": "hybridqa_questions_and_code",
                "pinned_commit": build_sample.OFFICIAL_HYBRIDQA_COMMIT,
                "artifact_path": "released_data/dev.json",
                "artifact_sha256": hashlib.sha256(questions.read_bytes()).hexdigest(),
                "record_count": 1,
                "question_id_set_sha256": hashlib.sha256(b"fresh\n").hexdigest(),
            }

            cases = (
                (base / "outside-role.jsonl", project / "split-role-case.json"),
                (project / "inside-role.jsonl", base / "outside-split.json"),
            )
            for output, split in cases:
                with self.subTest(output=output, split=split):
                    argv = [
                        "build_sample.py",
                        "--questions",
                        str(questions),
                        "--project-root",
                        str(project),
                        "--historical-manifest",
                        str(history),
                        "--source-manifest",
                        str(source_manifest),
                        "--output",
                        str(output),
                        "--split-manifest",
                        str(split),
                        "--pilot-count",
                        "1",
                    ]
                    with (
                        mock.patch.object(sys, "argv", argv),
                        mock.patch.object(build_sample, "verify_source_manifest", return_value=verified_source),
                        mock.patch.object(build_sample, "historical_release_errors", return_value=[]),
                    ):
                        result = build_sample.main()
                    self.assertEqual(result, 2)
                    self.assertFalse(output.exists())
                    self.assertFalse(split.exists())

            output = project / "release" / "pilot.questions.jsonl"
            split = project / "release" / "split.json"
            argv = [
                "build_sample.py",
                "--questions",
                str(questions),
                "--project-root",
                str(project),
                "--historical-manifest",
                str(history),
                "--source-manifest",
                str(source_manifest),
                "--output",
                str(output),
                "--split-manifest",
                str(split),
                "--pilot-count",
                "1",
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(build_sample, "verify_source_manifest", return_value=verified_source),
                mock.patch.object(build_sample, "historical_release_errors", return_value=[]),
            ):
                result = build_sample.main()
            self.assertEqual(result, 0)
            release_manifest = json.loads(split.read_text(encoding="utf-8"))
            self.assertTrue(release_manifest["release_eligible"])
            self.assertEqual(
                release_manifest["role_artifacts"]["annotation_schema_pilot"]["path"],
                "release/pilot.questions.jsonl",
            )

    def test_incomplete_history_requires_explicit_diagnostic_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            questions = base / "dev.json"
            history = base / "history.json"
            output = base / "questions.jsonl"
            split = base / "split.json"
            write_json(
                questions,
                [
                    {"question_id": "q1", "question": "First?", "table_id": "t1", "answer": "SECRET"},
                    {"question_id": "q2", "question": "Second?", "table_id": "t2", "answer": "SECRET2"},
                ],
            )
            write_json(
                history,
                {
                    "audit_status": "incomplete_missing_historical_artifacts",
                    "exposed_question_ids": ["q1"],
                },
            )
            refused = run_tool(
                "build_sample.py",
                "--questions",
                questions,
                "--historical-manifest",
                history,
                "--output",
                output,
                "--split-manifest",
                split,
                "--pilot-count",
                1,
                "--allow-unverified-source",
            )
            self.assertEqual(refused.returncode, 2, refused.stderr)
            self.assertFalse(output.exists())

            allowed = run_tool(
                "build_sample.py",
                "--questions",
                questions,
                "--historical-manifest",
                history,
                "--output",
                output,
                "--split-manifest",
                split,
                "--pilot-count",
                1,
                "--allow-incomplete-history",
                "--allow-unverified-source",
            )
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            selected = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(selected["question_id"], "q2")
            self.assertNotIn("answer", selected)
            self.assertFalse(json.loads(split.read_text(encoding="utf-8"))["release_eligible"])

    def test_verified_official_source_hash_is_required_for_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            questions = base / "dev.json"
            history = base / "history.json"
            source_manifest = base / "source.json"
            output = base / "questions.jsonl"
            split = base / "split.json"
            write_json(questions, [{"question_id": "q1", "question": "Question?", "table_id": "t1"}])
            source_sha = hashlib.sha256(questions.read_bytes()).hexdigest()
            write_json(history, complete_history_manifest())
            write_json(
                source_manifest,
                {
                    "dataset": "HybridQA",
                    "source_policy": "official_primary_sources_only",
                    "upstreams": [
                        {
                            "source_id": "fixture_pinned_source",
                            "pinned_commit": "abc123",
                            "artifacts": [{"path": "released_data/dev.json", "sha256": source_sha}],
                        }
                    ],
                },
            )
            refused = run_tool(
                "build_sample.py",
                "--questions",
                questions,
                "--historical-manifest",
                history,
                "--source-manifest",
                source_manifest,
                "--output",
                output,
                "--split-manifest",
                split,
                "--pilot-count",
                1,
            )
            self.assertEqual(refused.returncode, 2)

            diagnostic = run_tool(
                "build_sample.py",
                "--questions",
                questions,
                "--historical-manifest",
                history,
                "--source-manifest",
                source_manifest,
                "--output",
                output,
                "--split-manifest",
                split,
                "--pilot-count",
                1,
                "--allow-incomplete-history",
                "--allow-unverified-source",
            )
            self.assertEqual(diagnostic.returncode, 0, diagnostic.stderr)
            written = json.loads(split.read_text(encoding="utf-8"))
            self.assertFalse(written["release_eligible"])
            self.assertIsNone(written["source"]["portable_reference"])

            write_json(questions, [{"question_id": "q2", "question": "Changed?", "table_id": "t2"}])
            refused = run_tool(
                "build_sample.py",
                "--questions",
                questions,
                "--historical-manifest",
                history,
                "--source-manifest",
                source_manifest,
                "--output",
                output,
                "--split-manifest",
                split,
                "--pilot-count",
                1,
            )
            self.assertEqual(refused.returncode, 2)

    def test_roles_are_written_to_isolated_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            questions = base / "questions.json"
            history = base / "history.json"
            pilot_output = base / "pilot.jsonl"
            role_dir = base / "roles"
            split = base / "split.json"
            write_json(
                questions,
                [
                    {"question_id": f"fresh_{index}", "question": f"Question {index}?", "table_id": f"t{index}"}
                    for index in range(4)
                ],
            )
            write_json(history, complete_history_manifest())
            forged_release = run_tool(
                "build_sample.py",
                "--questions",
                questions,
                "--historical-manifest",
                history,
                "--output",
                pilot_output,
                "--role-output-dir",
                role_dir,
                "--split-manifest",
                split,
                "--pilot-count",
                1,
                "--allow-unverified-source",
            )
            self.assertEqual(forged_release.returncode, 2)
            self.assertFalse(pilot_output.exists())
            result = run_tool(
                "build_sample.py",
                "--questions",
                questions,
                "--historical-manifest",
                history,
                "--output",
                pilot_output,
                "--role-output-dir",
                role_dir,
                "--split-manifest",
                split,
                "--pilot-count",
                1,
                "--train-count",
                1,
                "--dev-count",
                1,
                "--locked-eval-count",
                1,
                "--allow-incomplete-history",
                "--allow-unverified-source",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            pilot = json.loads(pilot_output.read_text(encoding="utf-8"))
            locked = json.loads((role_dir / "locked_eval.questions.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(pilot["dataset_role"], "annotation_schema_pilot")
            self.assertEqual(locked["dataset_role"], "locked_eval")
            self.assertNotEqual(pilot["question_id"], locked["question_id"])
            manifest = json.loads(split.read_text(encoding="utf-8"))
            self.assertFalse(manifest["combined_role_output_written"])
            self.assertFalse(manifest["role_artifacts"]["locked_eval"]["tuning_allowed"])

            stale_retry = run_tool(
                "build_sample.py",
                "--questions",
                questions,
                "--historical-manifest",
                history,
                "--output",
                pilot_output,
                "--role-output-dir",
                role_dir,
                "--split-manifest",
                split,
                "--pilot-count",
                4,
                "--train-count",
                0,
                "--dev-count",
                0,
                "--locked-eval-count",
                0,
                "--allow-incomplete-history",
                "--allow-unverified-source",
            )
            self.assertEqual(stale_retry.returncode, 2)


class HistoricalManifestTests(unittest.TestCase):
    def test_split_role_ids_are_all_historically_exposed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            paths = {
                "data_analysis/week1_sample_100.jsonl": base / "data_analysis/week1_sample_100.jsonl",
                "evaluation/week2_eval_ids.json": base / "evaluation/week2_eval_ids.json",
                "evaluation/week3_engineering_dev_ids.json": base / "evaluation/week3_engineering_dev_ids.json",
                "evaluation/week3_locked_eval_ids.json": base / "evaluation/week3_locked_eval_ids.json",
                "evaluation/week3_split_manifest.json": base / "evaluation/week3_split_manifest.json",
            }
            write_jsonl(
                paths["data_analysis/week1_sample_100.jsonl"],
                [{"question_id": f"w1_{index}"} for index in range(100)],
            )
            write_json(paths["evaluation/week2_eval_ids.json"], [f"w2_{index}" for index in range(50)])
            write_json(paths["evaluation/week3_engineering_dev_ids.json"], ["engineering_only"])
            write_json(paths["evaluation/week3_locked_eval_ids.json"], ["locked_only"])
            write_json(
                paths["evaluation/week3_split_manifest.json"],
                {
                    "roles": {
                        "annotation_schema_pilot": ["pilot_only"],
                        "annotation_train": ["train_only"],
                        "annotation_dev": ["dev_only"],
                        "locked_eval": ["split_locked_only"],
                    }
                },
            )
            subprocess.run(["git", "init"], cwd=base, check=True, capture_output=True)
            subprocess.run(
                ["git", "add", "data_analysis", "evaluation"],
                cwd=base,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Fixture",
                    "-c",
                    "user.email=fixture@example.invalid",
                    "commit",
                    "-m",
                    "historical fixture",
                ],
                cwd=base,
                check=True,
                capture_output=True,
            )
            authority_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=base,
                text=True,
                check=True,
                capture_output=True,
            ).stdout.strip()
            provenance = base / "provenance.json"
            write_json(
                provenance,
                {
                    "schema_version": "historical_recovery_provenance_v0_1",
                    "status": "researcher_approved_authoritative",
                    "authority_kind": "git_commit",
                    "authority_identity": authority_commit,
                    "files": [
                        {
                            "path": relative,
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "question_id_count": (
                                100 if "week1" in relative else 50 if "week2" in relative else
                                1 if "engineering" in relative or "locked_eval_ids" in relative else 4
                            ),
                        }
                        for relative, path in paths.items()
                    ],
                },
            )
            output = base / "historical.json"
            protected_sha = hashlib.sha256(paths["data_analysis/week1_sample_100.jsonl"].read_bytes()).hexdigest()
            collision = run_tool(
                "build_historical_manifest.py",
                "--project-root",
                base,
                "--output",
                paths["data_analysis/week1_sample_100.jsonl"],
                "--recovery-provenance",
                provenance,
            )
            self.assertEqual(collision.returncode, 2)
            self.assertEqual(
                hashlib.sha256(paths["data_analysis/week1_sample_100.jsonl"].read_bytes()).hexdigest(),
                protected_sha,
            )
            result = run_tool(
                "build_historical_manifest.py",
                "--project-root",
                base,
                "--output",
                output,
                "--recovery-provenance",
                provenance,
                "--strict",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(manifest["is_complete"])
            self.assertTrue(
                {"pilot_only", "train_only", "dev_only", "split_locked_only"}.issubset(
                    set(manifest["forbidden_future_training_ids"])
                )
            )
            self.assertIn("split_locked_only", manifest["locked_eval_question_ids"])

            backup_provenance = base / "backup-provenance.json"
            backup_payload = json.loads(provenance.read_text(encoding="utf-8"))
            backup_payload["authority_kind"] = "verified_backup"
            backup_payload["authority_identity"] = "self-asserted-backup"
            write_json(backup_provenance, backup_payload)
            backup_output = base / "backup-history.json"
            backup_result = run_tool(
                "build_historical_manifest.py",
                "--project-root",
                base,
                "--output",
                backup_output,
                "--recovery-provenance",
                backup_provenance,
                "--strict",
            )
            self.assertEqual(backup_result.returncode, 2)
            self.assertFalse(json.loads(backup_output.read_text(encoding="utf-8"))["is_complete"])

    def test_overwrite_only_replaces_an_incomplete_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            output = base / "historical.json"
            write_json(
                output,
                {
                    "schema_version": "historical_exposed_ids_v0_1",
                    "audit_status": "incomplete_missing_historical_artifacts",
                    "is_complete": False,
                },
            )
            replace_incomplete = run_tool(
                "build_historical_manifest.py",
                "--project-root",
                base,
                "--output",
                output,
                "--overwrite",
            )
            self.assertEqual(replace_incomplete.returncode, 0, replace_incomplete.stderr)

            write_json(
                output,
                {
                    "schema_version": "historical_exposed_ids_v0_1",
                    "audit_status": "complete",
                    "is_complete": True,
                },
            )
            complete_bytes = output.read_bytes()
            refuse_complete = run_tool(
                "build_historical_manifest.py",
                "--project-root",
                base,
                "--output",
                output,
                "--overwrite",
            )
            self.assertEqual(refuse_complete.returncode, 2)
            self.assertEqual(output.read_bytes(), complete_bytes)


class AnnotationValidatorTests(unittest.TestCase):
    def test_required_formats_use_dependency_free_assertions(self) -> None:
        self.assertTrue(validate_annotation.is_rfc3339_datetime("2026-08-21T12:34:56+09:00"))
        self.assertTrue(validate_annotation.is_rfc3339_datetime("2026-08-21T03:34:56Z"))
        self.assertFalse(validate_annotation.is_rfc3339_datetime("2026-08-21 12:34:56"))
        self.assertFalse(validate_annotation.is_rfc3339_datetime("not-a-date"))
        self.assertTrue(validate_annotation.is_absolute_uri("https://example.org/artifact"))
        self.assertFalse(validate_annotation.is_absolute_uri("https:///missing-host"))
        self.assertFalse(validate_annotation.is_absolute_uri("relative/path"))

    def base_annotation(self) -> dict[str, object]:
        return {
            "question_id": "q1",
            "question": "Which row is older?",
            "table_id": "t1",
            "semantic_skeleton": {"answer_target": "row", "answer_type": "Entity"},
            "information_obligations": [
                {"obligation_id": "o1", "description": "compare ages", "depends_on": []}
            ],
            "abstract_topology": {
                "nodes": [{"id": "a1", "function": "COMPARE_VALUES", "depends_on": []}]
            },
            "operator_topology": {
                "nodes": [
                    {"id": "n1", "operator": "FILTER", "depends_on": []},
                    {"id": "n2", "operator": "PROJECT", "depends_on": ["n1"]},
                ]
            },
            "grounding": {"node_bindings": [{"topology_node_id": "n1"}]},
            "execution_graph": None,
            "alternative_plans": [],
            "review_status": {
                "state": "llm_proposed",
                "human_review_count": 0,
                "reviewer_records": [],
                "gold_claimed": False,
                "semantic_correctness_claim": "unassessed",
            },
        }

    def test_passed_leakage_audit_is_bound_to_live_input_and_result_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            input_path = base / "views" / "question-to-semantics.json"
            result_path = base / "audits" / "question-to-semantics.json"
            write_json(input_path, {"question_id": "q1", "question": "Question?"})
            input_sha = hashlib.sha256(input_path.read_bytes()).hexdigest()
            audit_result = {
                "schema_version": "leakage_boundary_audit_v0_1",
                "boundary": "question_to_semantics",
                "status": "passed",
                "checked_at": "2026-08-21T00:00:00Z",
                "checker_id": "fixture-checker-v1",
                "input_view_sha256": input_sha,
                "violations": [],
            }
            write_json(result_path, audit_result)
            audit = {
                "boundary": "question_to_semantics",
                "status": "passed",
                "checked_at": audit_result["checked_at"],
                "checker_id": audit_result["checker_id"],
                "violations": [],
                "input_view_artifact": {
                    "artifact_id": "view-q1",
                    "artifact_type": "prediction_view",
                    "repository_relative_path": input_path.relative_to(base).as_posix(),
                    "sha256": input_sha,
                },
                "audit_result_artifact": {
                    "artifact_id": "audit-q1",
                    "artifact_type": "leakage_boundary_audit",
                    "repository_relative_path": result_path.relative_to(base).as_posix(),
                    "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
                },
            }
            self.assertEqual(
                validate_annotation.leakage_audit_artifact_errors(
                    "question_to_semantics",
                    audit,
                    base,
                    {"question_id": "q1", "question": "Question?"},
                ),
                [],
            )

            write_json(input_path, {"question": "Wrong question", "grounding": {"secret": "x"}})
            leaked_sha = hashlib.sha256(input_path.read_bytes()).hexdigest()
            audit["input_view_artifact"]["sha256"] = leaked_sha
            audit_result["input_view_sha256"] = leaked_sha
            write_json(result_path, audit_result)
            audit["audit_result_artifact"]["sha256"] = hashlib.sha256(
                result_path.read_bytes()
            ).hexdigest()
            leak_errors = validate_annotation.leakage_audit_artifact_errors(
                "question_to_semantics",
                audit,
                base,
                {"question_id": "q1", "question": "Question?"},
            )
            self.assertTrue(any("forbidden key" in error for error in leak_errors))
            self.assertTrue(any("does not match the annotation" in error for error in leak_errors))

            split_path = base / "split.json"
            tuning_path = base / "views" / "tuning-inventory.json"
            locked_result_path = base / "audits" / "locked-isolation.json"
            write_json(split_path, {"roles": {"locked_eval": ["locked-q1"]}})
            write_json(
                tuning_path,
                {
                    "schema_version": "locked_eval_tuning_input_inventory_v0_1",
                    "question_ids": ["locked-q1"],
                },
            )
            split_sha = hashlib.sha256(split_path.read_bytes()).hexdigest()
            tuning_sha = hashlib.sha256(tuning_path.read_bytes()).hexdigest()
            locked_result = {
                "schema_version": "leakage_boundary_audit_v0_1",
                "boundary": "locked_eval_isolation",
                "status": "passed",
                "checked_at": "2026-08-21T00:00:00Z",
                "checker_id": "fixture-checker-v1",
                "input_view_sha256": tuning_sha,
                "split_manifest_sha256": split_sha,
                "tuning_question_id_set_sha256": hashlib.sha256(b"locked-q1\n").hexdigest(),
                "locked_eval_overlap_count": 0,
                "violations": [],
            }
            write_json(locked_result_path, locked_result)
            locked_audit = {
                "boundary": "locked_eval_isolation",
                "status": "passed",
                "checked_at": locked_result["checked_at"],
                "checker_id": locked_result["checker_id"],
                "violations": [],
                "input_view_artifact": {
                    "artifact_id": "locked-tuning-inventory",
                    "artifact_type": "prediction_view",
                    "repository_relative_path": tuning_path.relative_to(base).as_posix(),
                    "sha256": tuning_sha,
                },
                "audit_result_artifact": {
                    "artifact_id": "locked-isolation-audit",
                    "artifact_type": "leakage_boundary_audit",
                    "repository_relative_path": locked_result_path.relative_to(base).as_posix(),
                    "sha256": hashlib.sha256(locked_result_path.read_bytes()).hexdigest(),
                },
            }
            locked_record = {
                "locked_eval_controls": {
                    "split_manifest_artifact": {
                        "artifact_id": "split",
                        "artifact_type": "split_manifest",
                        "repository_relative_path": split_path.relative_to(base).as_posix(),
                        "sha256": split_sha,
                    }
                }
            }
            locked_errors = validate_annotation.leakage_audit_artifact_errors(
                "locked_eval_isolation", locked_audit, base, locked_record
            )
            self.assertTrue(any("tuning input contains locked-eval" in error for error in locked_errors))
            self.assertTrue(any("only a locked_eval annotation" in error for error in locked_errors))

    def test_cross_field_and_leakage_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            checks = base / "checks.jsonl"
            write_json(vocabulary, {"operators": ["FILTER", "PROJECT"]})
            write_jsonl(annotations, [self.base_annotation()])
            good = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                checks,
                "--structural-only",
            )
            self.assertEqual(good.returncode, 0, good.stderr)
            good_check = json.loads(checks.read_text(encoding="utf-8"))
            self.assertEqual(good_check["status"], "pass")
            self.assertEqual(
                good_check["annotation_canonical_sha256"],
                canonical_sha256(self.base_annotation()),
            )
            self.assertEqual(
                good_check["validation_context"]["annotations_artifact_sha256"],
                hashlib.sha256(annotations.read_bytes()).hexdigest(),
            )

            bad_record = self.base_annotation()
            bad_record["semantic_skeleton"] = {
                "column_index": 3,
                "Gold_Answer": "leaked",
                "GOLD_ANSWERS": ["plural leak"],
                "oracle_document_ids": ["doc"],
                "weak_answer_nodes": ["node"],
            }
            bad_record["information_obligations"] = [
                {"obligation_id": "o1", "depends_on": ["o2"]},
                {"obligation_id": "o2", "depends_on": ["o1"]},
            ]
            bad_record["abstract_topology"] = {
                "nodes": [{"id": "a1", "function": "GET_FLAG_BEARER_AGE", "depends_on": []}]
            }
            bad_record["operator_topology"] = {
                "nodes": [
                    {"id": "n1", "operator": "MADE_UP", "depends_on": ["n2"]},
                    {"id": "n2", "operator": "PROJECT", "depends_on": ["n1"]},
                ]
            }
            bad_record["grounding"] = {"node_bindings": [{}]}
            bad_record["execution_graph"] = {
                "graph_status": "referenced_validated",
                "executable_status": "executable",
            }
            bad_record["alternative_plans"] = [
                {
                    "alternative_plan_id": "alt1",
                    "satisfies_obligation_ids": ["missing"],
                    "operator_topology": {
                        "nodes": [
                            {"id": "x1", "operator": "MADE_UP", "depends_on": ["x2"]},
                            {"id": "x2", "operator": "PROJECT", "depends_on": ["x1"]},
                        ]
                    },
                }
            ]
            bad_record["review_status"] = {"status": "gold"}
            bad_record["bundle_status"] = "structurally_validated"
            bad_record["leakage_controls"] = {
                "early_layer_answer_exposure": False,
                "prediction_view_contracts": [
                    {
                        "task": task,
                        "input_paths": ["/grounding"],
                        "target_paths": ["/grounding"],
                        "prohibited_input_paths": ["/grounding"],
                    }
                    for task in (
                        "question_to_semantics",
                        "semantics_to_operator_topology",
                        "operator_topology_to_grounding",
                        "question_environment_to_execution_graph",
                        "execution_evaluation",
                    )
                ],
                "boundary_audits": [
                    {
                        "boundary": boundary,
                        "status": "failed",
                        "checked_at": "2026-08-21T00:00:00Z",
                        "checker_id": "fixture-checker",
                        "violations": [{"kind": "fixture-leak"}],
                    }
                    for boundary in (
                        "question_to_semantics",
                        "semantics_to_abstract_topology",
                        "abstract_to_operator_topology",
                        "operator_topology_to_grounding",
                        "grounding_to_execution_graph",
                        "locked_eval_isolation",
                    )
                ],
            }
            bad_record["leakage_controls"]["boundary_audits"][0].update(
                {"status": "passed", "violations": []}
            )
            write_jsonl(annotations, [bad_record])
            bad = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                checks,
                "--structural-only",
            )
            self.assertEqual(bad.returncode, 1)
            errors = json.loads(checks.read_text(encoding="utf-8"))["errors"]
            self.assertTrue(any("leakage" in error for error in errors))
            self.assertTrue(any("cycle" in error for error in errors))
            self.assertTrue(any("unknown operator" in error for error in errors))
            self.assertTrue(any("gold label" in error for error in errors))
            self.assertTrue(any("information_obligations" in error and "cycle" in error for error in errors))
            self.assertTrue(any("unknown semantic function" in error for error in errors))
            self.assertTrue(any("missing topology_node_id" in error for error in errors))
            self.assertTrue(any("alternative_plans" in error and "unknown reference" in error for error in errors))
            self.assertTrue(any("input_paths" in error and "not allowed" in error for error in errors))
            self.assertTrue(any("failed audit requires bundle_status" in error for error in errors))
            self.assertTrue(any("input_view_artifact" in error for error in errors))
            self.assertTrue(any("referenced_validated is unsupported" in error for error in errors))
            self.assertTrue(any("executable is unsupported" in error for error in errors))

    def test_grounding_binding_and_plan_references_are_cross_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            checks = base / "checks.jsonl"
            write_json(
                vocabulary,
                {
                    "vocabulary_version": "fixture_medium_v1",
                    "granularity": "medium",
                    "operators": [
                        {
                            "name": "PROJECT",
                            "input_ports": [],
                            "output_ports": [],
                            "argument_slots": [
                                {"name": "column", "binding_kind": "column", "required": True}
                            ],
                        }
                    ],
                },
            )
            record = self.base_annotation()
            record["abstract_topology"]["nodes"][0].update(
                {
                    "realizes_skeleton_requirement_ids": ["ghost_requirement"],
                    "input_semantic_variable_ids": ["ghost_input"],
                    "output_semantic_variable_ids": ["ghost_output"],
                }
            )
            record["operator_topology"] = {
                "topology_id": "top1",
                "operator_vocabulary": {
                    "vocabulary_version": "fixture_medium_v1",
                    "granularity": "medium",
                },
                "nodes": [
                    {
                        "node_id": "n1",
                        "operator": "PROJECT",
                        "depends_on": [],
                        "input_slots": [],
                        "output_slots": [],
                        "argument_slots": [
                            {
                                "slot_name": "column",
                                "semantic_role_ref": "role_column",
                                "expected_binding_kind": "column",
                                "required": True,
                            }
                        ],
                    }
                ],
            }
            record["grounding"] = {
                "operator_topology_id": "top1",
                "grounding_status": "fully_grounded",
                "node_bindings": [
                    {
                        "topology_node_id": "n1",
                        "operator": "PROJECT",
                        "coverage_status": "all_required_slots_grounded",
                        "argument_groundings": [
                            {
                                "slot_name": "column",
                                "semantic_role_ref": "role_column",
                                "expected_binding_kind": "column",
                                "status": "grounded",
                                "selected_binding": {"binding_type": "literal", "literal": {"value": "x"}},
                                "candidate_bindings": [],
                            }
                        ],
                    }
                ],
            }
            record["plan_equivalence_contract"] = {
                "required_obligation_ids": ["missing_obligation"],
                "required_dependencies": [
                    {
                        "constraint_id": "c1",
                        "predecessor_obligation_ids": ["missing_predecessor"],
                        "successor_obligation_id": "missing_successor",
                    }
                ],
            }
            record["alternative_plans"] = [
                {
                    "alternative_plan_id": "alt1",
                    "satisfies_obligation_ids": ["o1"],
                    "satisfies_dependency_constraint_ids": ["missing_constraint"],
                    "assessment": {"semantic_validity": "proposed_valid"},
                    "abstract_topology": {
                        "nodes": [
                            {
                                "node_id": "ax1",
                                "semantic_function": "COMPARE_VALUES",
                                "depends_on": [],
                                "fulfills_obligation_ids": ["o1"],
                                "GOLD_ANSWERS": ["SECRET_ALTERNATIVE_LEAK"],
                            }
                        ],
                        "required_dependency_constraints": [],
                    },
                    "operator_topology": {
                        "topology_id": "alt-top",
                        "operator_vocabulary": {
                            "vocabulary_version": "wrong-vocabulary",
                            "granularity": "medium",
                        },
                        "nodes": [
                            {
                                "node_id": "alt-n1",
                                "operator": "PROJECT",
                                "depends_on": [],
                                "fulfills_obligation_ids": ["o1"],
                                "realizes_abstract_node_ids": ["ax1"],
                                "input_slots": [],
                                "output_slots": [
                                    {
                                        "slot_name": "ghost-output",
                                        "declared_type": "String",
                                        "cardinality": "one",
                                        "semantic_variable_ids": ["ghost_semantic"],
                                    }
                                ],
                                "argument_slots": [
                                    {
                                        "slot_name": "column",
                                        "semantic_role_ref": "ghost_role",
                                        "expected_binding_kind": "column",
                                        "required": True,
                                    }
                                ],
                            }
                        ],
                    },
                    "grounding": {
                        "operator_topology_id": "alt-top",
                        "grounding_status": "fully_grounded",
                        "node_bindings": [
                            {
                                "topology_node_id": "alt-n1",
                                "operator": "PROJECT",
                                "coverage_status": "all_required_slots_grounded",
                                "argument_groundings": [
                                    {
                                        "slot_name": "column",
                                        "semantic_role_ref": "ghost_role",
                                        "expected_binding_kind": "column",
                                        "status": "grounded",
                                        "selected_binding": {
                                            "binding_type": "column",
                                            "column_name": "A",
                                        },
                                        "candidate_bindings": [
                                            {
                                                "selection_status": "selected",
                                                "binding": {
                                                    "binding_type": "column",
                                                    "column_name": "B",
                                                },
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                }
            ]
            write_jsonl(annotations, [record])
            result = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                checks,
                "--structural-only",
            )
            self.assertEqual(result.returncode, 1)
            errors = json.loads(checks.read_text(encoding="utf-8"))["errors"]
            self.assertTrue(any("selected binding type" in error for error in errors))
            self.assertTrue(any("plan_equivalence_contract" in error and "unknown reference" in error for error in errors))
            self.assertTrue(any("missing_constraint" in error for error in errors))
            self.assertTrue(any("ghost_requirement" in error for error in errors))
            self.assertTrue(any("ghost_input" in error for error in errors))
            self.assertTrue(any("SECRET_ALTERNATIVE_LEAK" not in error and "leakage" in error for error in errors))
            self.assertTrue(any("ghost_semantic" in error for error in errors))
            self.assertTrue(any("vocabulary_version" in error and "alternative_plans" in error for error in errors))
            self.assertTrue(any("selected candidate and selected_binding differ" in error for error in errors))
            self.assertTrue(any("valid semantic claim omits" in error for error in errors))

    def test_execution_reference_identifiers_and_obligations_are_cross_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            checks = base / "checks.jsonl"
            write_json(vocabulary, {"operators": ["FILTER", "PROJECT"]})
            record = self.base_annotation()
            record["execution_reference"] = {
                "availability": "unavailable",
                "answer_visibility": "execution_layer_only",
                "expected_intermediates": [
                    {
                        "expectation_id": "expectation_1",
                        "obligation_ids": ["o1"],
                        "description": "known obligation",
                        "evidence_requirements": ["operator_trace"],
                    },
                    {
                        "expectation_id": "expectation_1",
                        "obligation_ids": ["missing_obligation"],
                        "description": "unknown obligation",
                        "evidence_requirements": ["operator_trace"],
                    },
                ],
                "execution_trials": [
                    {
                        "trial_id": "trial_1",
                        "status": "not_run",
                        "runtime_id": "fixture",
                        "timestamp": "2026-08-21T00:00:00Z",
                    },
                    {
                        "trial_id": "trial_1",
                        "status": "not_run",
                        "runtime_id": "fixture",
                        "timestamp": "2026-08-21T00:00:01Z",
                    },
                ],
                "unavailability_reason": "fixture",
            }
            write_jsonl(annotations, [record])
            result = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                checks,
                "--structural-only",
            )
            self.assertEqual(result.returncode, 1)
            errors = json.loads(checks.read_text(encoding="utf-8"))["errors"]
            self.assertTrue(any("duplicate expectation_id 'expectation_1'" in error for error in errors))
            self.assertTrue(any("unknown reference 'missing_obligation'" in error for error in errors))
            self.assertTrue(any("duplicate trial_id 'trial_1'" in error for error in errors))

    def test_empty_annotation_input_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "empty.jsonl"
            vocabulary = base / "vocabulary.json"
            annotations.write_text("", encoding="utf-8")
            write_json(vocabulary, {"operators": ["FILTER"]})
            result = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--structural-only",
            )
            self.assertEqual(result.returncode, 2)

    def test_malformed_topology_types_become_record_failures_not_tracebacks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            checks = base / "checks.jsonl"
            write_json(vocabulary, {"operators": ["FILTER", "PROJECT"]})
            records: list[dict[str, object]] = []
            for index in range(8):
                record = json.loads(json.dumps(self.base_annotation()))
                record["question_id"] = f"malformed-{index}"
                records.append(record)
            records[0]["operator_topology"] = ["bad"]
            records[1]["operator_topology"] = {"nodes": 3}
            records[2]["abstract_topology"] = {"nodes": 3}
            records[3]["alternative_plans"] = [
                {"alternative_plan_id": "alt-bad", "abstract_topology": {"nodes": 3}}
            ]
            records[4]["operator_topology"]["nodes"][0]["depends_on"] = [{}]
            records[5]["grounding"] = {
                "node_bindings": [],
                "oracle_assistance_summary": {"used": False, "affected_node_ids": [{}]},
            }
            records[6]["leakage_controls"] = {
                "early_layer_answer_exposure": False,
                "prediction_view_contracts": [{"task": {"not": "a string"}}],
                "boundary_audits": [{"boundary": {"not": "a string"}}],
            }
            records[7]["alternative_plans"] = [
                {
                    "alternative_plan_id": "alt-deps",
                    "operator_topology": {
                        "nodes": [
                            {"node_id": "alt-n1", "operator": "FILTER", "depends_on": [{}]}
                        ]
                    },
                }
            ]
            write_jsonl(annotations, records)
            result = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                checks,
                "--structural-only",
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            check_rows = [json.loads(line) for line in checks.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(check_rows), 8)
            self.assertTrue(all(row["status"] == "fail" for row in check_rows))
            self.assertFalse(
                any(
                    "validator_internal_error" in error
                    for row in check_rows
                    for error in row["errors"]
                )
            )

    def test_locked_eval_requires_real_membership_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            checks = base / "checks.jsonl"
            write_json(vocabulary, {"operators": ["FILTER", "PROJECT"]})
            fake_artifact = {
                "artifact_id": "fake",
                "artifact_type": "not_a_manifest",
                "repository_relative_path": "AGENTS.md",
                "sha256": hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest(),
            }
            record = self.base_annotation()
            record["dataset_role"] = "locked_eval"
            record["locked_eval_controls"] = {
                "prompt_tuning_allowed": False,
                "rubric_tuning_allowed": False,
                "operator_vocabulary_tuning_allowed": False,
                "split_membership_verified": "passed",
                "historical_exposure_checked": "passed",
                "split_manifest_artifact": fake_artifact,
                "historical_exposure_manifest_artifact": fake_artifact,
            }
            write_jsonl(annotations, [record])
            result = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                checks,
                "--structural-only",
            )
            self.assertEqual(result.returncode, 1)
            errors = json.loads(checks.read_text(encoding="utf-8"))["errors"]
            self.assertTrue(any("artifact is not readable JSON" in error for error in errors))

            split_path = base / "malformed-split.json"
            history_path = base / "malformed-history.json"
            malformed_history = complete_history_manifest()
            malformed_history["exposed_question_ids"] = [{}]
            malformed_history["forbidden_future_training_ids"] = [{}]
            malformed_history["locked_eval_question_ids"] = [{}]
            write_json(history_path, malformed_history)
            write_json(
                split_path,
                {
                    "schema_version": "split_manifest_v0_1",
                    "release_eligible": True,
                    "combined_role_output_written": False,
                    "roles": {
                        "annotation_schema_pilot": [],
                        "annotation_train": [{}],
                        "annotation_dev": [],
                        "locked_eval": ["q1"],
                    },
                },
            )
            malformed_controls = {
                "split_manifest_artifact": {
                    "repository_relative_path": split_path.name,
                    "sha256": hashlib.sha256(split_path.read_bytes()).hexdigest(),
                },
                "historical_exposure_manifest_artifact": {
                    "repository_relative_path": history_path.name,
                    "sha256": hashlib.sha256(history_path.read_bytes()).hexdigest(),
                },
            }
            malformed_errors = validate_annotation.locked_eval_membership_errors(
                {"question_id": "q1", "dataset_role": "locked_eval"},
                malformed_controls,
                base,
            )
            self.assertTrue(any("unique string-ID array" in error for error in malformed_errors))
            self.assertTrue(any("historical exposed_question_ids" in error for error in malformed_errors))


class ReviewPacketTests(unittest.TestCase):
    def test_question_only_packet_hides_later_layers_and_answers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            questions = base / "questions.jsonl"
            proposals = base / "proposals.jsonl"
            checks = base / "checks.jsonl"
            output = base / "packet.html"
            write_jsonl(questions, [{"question_id": "q1", "question": "Question?", "table_id": "t1"}])
            proposal_records = [
                {
                    "question_id": "q1",
                    "semantic_skeleton": {"answer_target": "row"},
                    "annotation_provenance": {
                        "model_provenance": {
                            "generation_parameters": {
                                "payload": "SECRET_PROVENANCE"
                            }
                        }
                    },
                    "ambiguity": {"reasons": ["SECRET_LATER_LAYER_AMBIGUITY"]},
                    "grounding": {"document_id": "SECRET_DOCUMENT"},
                    "gold_answer": "SECRET_ANSWER",
                }
            ]
            write_jsonl(proposals, proposal_records)
            write_pass_validation_checks(checks, proposals, proposal_records)
            result = run_tool(
                "build_review_packet.py",
                "--questions",
                questions,
                "--proposals",
                proposals,
                "--validation-checks",
                checks,
                "--stage",
                "question_only",
                "--output",
                output,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = output.read_text(encoding="utf-8")
            self.assertNotIn("SECRET_DOCUMENT", rendered)
            self.assertNotIn("SECRET_ANSWER", rendered)
            self.assertNotIn("SECRET_LATER_LAYER_AMBIGUITY", rendered)
            self.assertNotIn("SECRET_PROVENANCE", rendered)
            self.assertNotIn('"t1"', rendered)
            self.assertIn("answer_target", rendered)

            contaminated_records = [
                {
                    "question_id": "q1",
                    "semantic_skeleton": {
                        "answer_target": "row",
                        "nested": {
                            "final_answer": "SECRET_FINAL",
                            "correct_response": "SECRET_CORRECT",
                        },
                    },
                }
            ]
            write_jsonl(proposals, contaminated_records)
            write_pass_validation_checks(checks, proposals, contaminated_records)
            contaminated = run_tool(
                "build_review_packet.py",
                "--questions",
                questions,
                "--proposals",
                proposals,
                "--validation-checks",
                checks,
                "--stage",
                "question_only",
                "--output",
                output,
            )
            self.assertEqual(contaminated.returncode, 2)
            self.assertIn("contaminates", contaminated.stderr)

    def test_topology_environment_is_sanitized_and_id_sets_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            questions = base / "questions.jsonl"
            proposals = base / "proposals.jsonl"
            checks = base / "checks.jsonl"
            environment = base / "environment.jsonl"
            output = base / "packet.html"
            write_jsonl(questions, [{"question_id": "q1", "question": "Question?", "table_id": "t1"}])
            proposal_records = [{"question_id": "q1", "operator_topology": {"nodes": []}}]
            write_jsonl(proposals, proposal_records)
            write_pass_validation_checks(checks, proposals, proposal_records)
            write_jsonl(
                environment,
                [
                    {
                        "table_id": "t1",
                        "title": "Visible title",
                        "schema": {"rows": [["SECRET_SCHEMA_ROW"]], "linked_passages": ["SECRET_SCHEMA_DOC"]},
                        "columns": [{"name": "visible_column", "sample_values": ["SECRET_SAMPLE_VALUE"]}],
                        "data": [["SECRET_CONCRETE_ROW"]],
                        "execution_graph": {"literal": "SECRET_EXECUTION"},
                        "grounding": {"document_id": "SECRET_GROUNDING"},
                    }
                ],
            )
            result = run_tool(
                "build_review_packet.py",
                "--questions",
                questions,
                "--proposals",
                proposals,
                "--validation-checks",
                checks,
                "--environment",
                environment,
                "--stage",
                "topology",
                "--output",
                output,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("Visible title", rendered)
            self.assertNotIn("SECRET_EXECUTION", rendered)
            self.assertNotIn("SECRET_GROUNDING", rendered)
            self.assertNotIn("SECRET_CONCRETE_ROW", rendered)
            self.assertNotIn("SECRET_SCHEMA_ROW", rendered)
            self.assertNotIn("SECRET_SCHEMA_DOC", rendered)
            self.assertNotIn("SECRET_SAMPLE_VALUE", rendered)
            self.assertIn("visible_column", rendered)

            write_jsonl(proposals, [{"question_id": "extra", "operator_topology": {"nodes": []}}])
            write_pass_validation_checks(
                checks,
                proposals,
                [{"question_id": "extra", "operator_topology": {"nodes": []}}],
            )
            mismatch = run_tool(
                "build_review_packet.py",
                "--questions",
                questions,
                "--proposals",
                proposals,
                "--validation-checks",
                checks,
                "--environment",
                environment,
                "--stage",
                "topology",
                "--output",
                output,
            )
            self.assertEqual(mismatch.returncode, 2)


class GranularityTests(unittest.TestCase):
    def test_complete_three_way_pilot_writes_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "representations.jsonl"
            metrics = base / "metrics.json"
            report = base / "report.md"
            def representation(operator: str, question_id: str, granularity: str) -> dict[str, object]:
                value: dict[str, object] = {
                    "coverage_status": "covered",
                    "requires_new_operator": False,
                    "hides_reasoning": False,
                    "ambiguity_present": False,
                    "excessive_fragmentation": False,
                    "topology": {
                        "nodes": [{"id": "n1", "operator": operator, "depends_on": []}]
                    },
                }
                review_annotation = {
                    "schema_version": "operator_representation_review_v0_1",
                    "question_id": question_id,
                    "granularity": granularity,
                    "reviewed_view": "operator_granularity_representation",
                    "reviewed_representation_sha256": canonical_sha256(value),
                    "review_packet_sha256": "a" * 64,
                    "decision": "accept",
                }
                value["human_review_evidence"] = {
                    "canonicalization": "sorted_compact_json_utf8_sha256_v0_1",
                    "independent_reviews": [
                        {
                            "reviewer_id": reviewer_id,
                            "annotation": review_annotation,
                            "annotation_sha256": canonical_sha256(review_annotation),
                        }
                        for reviewer_id in ("reviewer_a", "reviewer_b")
                    ],
                }
                return value
            write_jsonl(
                source,
                [
                    {
                        "question_id": f"q{index}",
                        "representations": {
                            "coarse": representation("TABLE_LOOKUP", f"q{index}", "coarse"),
                            "medium": representation("FILTER", f"q{index}", "medium"),
                            "fine": representation("SELECT_ROWS", f"q{index}", "fine"),
                        },
                    }
                    for index in range(20)
                ],
            )
            result = run_tool(
                "compare_operator_granularity.py",
                source,
                "--json-output",
                metrics,
                "--report-output",
                report,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(metrics.read_text(encoding="utf-8"))
            self.assertTrue(payload["evidence_complete"])
            self.assertEqual(payload["metrics"]["medium"]["annotation_disagreement_rate"], 0.0)
            self.assertIn("Coverage alone", payload["scientific_caution"])
            self.assertEqual(
                payload["provenance"]["representations_artifact_sha256"],
                hashlib.sha256(source.read_bytes()).hexdigest(),
            )
            self.assertEqual(set(payload["provenance"]["vocabularies"]), {"coarse", "medium", "fine"})

    def test_llm_only_disagreement_flag_is_not_human_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "representations.jsonl"
            metrics = base / "metrics.json"
            report = base / "report.md"
            representation = lambda operator: {  # noqa: E731
                "coverage_status": "covered",
                "requires_new_operator": False,
                "annotation_disagreement": False,
                "hides_reasoning": False,
                "ambiguity_present": False,
                "excessive_fragmentation": False,
                "topology": {"nodes": [{"id": "n1", "operator": operator, "depends_on": []}]},
            }
            write_jsonl(
                source,
                [
                    {
                        "question_id": f"q{index}",
                        "representations": {
                            "coarse": representation("TABLE_LOOKUP"),
                            "medium": representation("FILTER"),
                            "fine": representation("SELECT_ROWS"),
                        },
                    }
                    for index in range(20)
                ],
            )
            result = run_tool(
                "compare_operator_granularity.py",
                source,
                "--json-output",
                metrics,
                "--report-output",
                report,
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(metrics.read_text(encoding="utf-8"))
            self.assertFalse(payload["evidence_complete"])
            self.assertIsNone(payload["metrics"]["medium"]["annotation_disagreement_rate"])
            empty_hash = canonical_sha256({})
            self.assertEqual(
                compare_operator_granularity.observed_human_disagreement(
                    {
                        "human_review_evidence": {
                            "canonicalization": "sorted_compact_json_utf8_sha256_v0_1",
                            "independent_reviews": [
                                {
                                    "reviewer_id": reviewer_id,
                                    "annotation": {},
                                    "annotation_sha256": empty_hash,
                                }
                                for reviewer_id in ("reviewer_a", "reviewer_b")
                            ],
                        }
                    },
                    "q1",
                    "medium",
                ),
                (False, False),
            )


class CorpusStatisticsTests(unittest.TestCase):
    def test_duplicate_ids_and_unknown_operators_fail_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            checks = base / "checks.jsonl"
            output = base / "stats.json"
            report = base / "stats.md"
            write_json(vocabulary, {"operators": [{"name": "FILTER"}]})
            write_jsonl(
                annotations,
                [
                    {
                        "question_id": "same",
                        "table_id": f"t{index}",
                        "semantic_skeleton": {"answer_type": f"type{index}"},
                        "operator_topology": {
                            "nodes": [{"node_id": "n1", "operator": "UNKNOWN_OPERATOR", "depends_on": []}]
                        },
                    }
                    for index in range(2)
                ],
            )
            result = run_tool(
                "compute_annotation_stats.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--json-output",
                output,
                "--report-output",
                report,
            )
            self.assertEqual(result.returncode, 1)
            stats = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(stats["integrity_status"], "fail")
            self.assertEqual(stats["duplicate_question_ids"], ["same"])
            self.assertEqual(stats["unknown_operators"], ["UNKNOWN_OPERATOR"])
            self.assertEqual(
                stats["operator_statistics"]["UNKNOWN_OPERATOR"]["observed_reusability_evidence"],
                "insufficient_observations_for_reusability_claim",
            )

    def test_missing_review_ambiguity_and_alternatives_are_unobserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            checks = base / "checks.jsonl"
            output = base / "stats.json"
            report = base / "stats.md"
            write_json(vocabulary, {"operators": [{"name": "FILTER"}]})
            records = [
                {
                    "question_id": "q1",
                    "operator_topology": {
                        "nodes": [{"node_id": "n1", "operator": "FILTER", "depends_on": []}]
                    },
                }
            ]
            write_jsonl(annotations, records)
            result = run_tool(
                "compute_annotation_stats.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--json-output",
                output,
                "--report-output",
                report,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            stats = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(stats["evidence_complete"])
            self.assertIn(
                "hash-bound full annotation validation checks are not attached",
                stats["integrity_errors"],
            )
            self.assertEqual(stats["ambiguity_observation_count"], 0)
            self.assertIsNone(stats["ambiguity_rate"])
            self.assertEqual(stats["alternative_plan_observation_count"], 0)
            self.assertEqual(stats["review_status_observation_count"], 0)
            self.assertEqual(
                stats["provenance"]["annotations_artifact_sha256"],
                hashlib.sha256(annotations.read_bytes()).hexdigest(),
            )

            write_pass_validation_checks(checks, annotations, records)
            check_record = json.loads(checks.read_text(encoding="utf-8"))
            check_record["validation_context"]["operator_vocabulary_artifact_sha256"] = (
                hashlib.sha256(vocabulary.read_bytes()).hexdigest()
            )
            write_jsonl(checks, [check_record])
            verified = run_tool(
                "compute_annotation_stats.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--validation-checks",
                checks,
                "--json-output",
                output,
                "--report-output",
                report,
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)
            verified_stats = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(verified_stats["provenance"]["validation_checks_verified"])
            self.assertFalse(verified_stats["evidence_complete"])

    def test_invalid_review_state_and_topology_cycle_fail_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            output = base / "stats.json"
            report = base / "stats.md"
            write_json(vocabulary, {"operators": [{"name": "FILTER"}]})
            write_jsonl(
                annotations,
                [
                    {
                        "question_id": "q1",
                        "review_status": "not_observed",
                        "ambiguity": {"has_ambiguity": False},
                        "alternative_plans": [],
                        "operator_topology": {
                            "nodes": [
                                {
                                    "node_id": "n1",
                                    "operator": "FILTER",
                                    "depends_on": ["n1", "n1"],
                                }
                            ]
                        },
                    }
                ],
            )
            result = run_tool(
                "compute_annotation_stats.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--json-output",
                output,
                "--report-output",
                report,
            )
            self.assertEqual(result.returncode, 1)
            stats = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(stats["integrity_status"], "fail")
            self.assertFalse(stats["evidence_complete"])
            self.assertEqual(stats["invalid_review_status_record_indices"], [0])
            self.assertTrue(any("cycle" in error for error in stats["topology_integrity_errors"]))
            self.assertTrue(any("duplicate dependency" in error for error in stats["topology_integrity_errors"]))


class SchemaBundleTests(unittest.TestCase):
    def test_malformed_vocabulary_is_rejected_even_with_old_jsonschema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "data_construction"
            shutil.copytree(ROOT / "data_construction" / "schemas", target / "schemas")
            shutil.copytree(ROOT / "data_construction" / "operator_design", target / "operator_design")
            vocabulary_path = target / "operator_design" / "operator_vocabulary_coarse_v0_1.json"
            vocabulary = json.loads(vocabulary_path.read_text(encoding="utf-8"))
            vocabulary["operators"][0].pop("purpose")
            write_json(vocabulary_path, vocabulary)
            result = run_tool("check_schema_bundle.py", "--root", base)
            self.assertEqual(result.returncode, 1)
            self.assertIn("vocabulary schema validation failed", result.stdout)

    def test_remote_schema_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "data_construction"
            shutil.copytree(ROOT / "data_construction" / "schemas", target / "schemas")
            shutil.copytree(ROOT / "data_construction" / "operator_design", target / "operator_design")
            schema_path = target / "schemas" / "semantic_skeleton_v0_1.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["properties"]["skeleton_id"]["$ref"] = "https://example.invalid/unportable.json"
            write_json(schema_path, schema)
            result = run_tool("check_schema_bundle.py", "--root", base)
            self.assertEqual(result.returncode, 1)
            self.assertIn("remote or URN", result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "data_construction"
            shutil.copytree(ROOT / "data_construction" / "schemas", target / "schemas")
            shutil.copytree(ROOT / "data_construction" / "operator_design", target / "operator_design")
            grounding_path = target / "schemas" / "grounding_v0_1.json"
            grounding = json.loads(grounding_path.read_text(encoding="utf-8"))
            grounding["$defs"]["argument_grounding"]["properties"]["expected_binding_kind"][
                "enum"
            ].append("DRIFT_ONLY_IN_GROUNDING")
            write_json(grounding_path, grounding)
            drift = run_tool("check_schema_bundle.py", "--root", base)
            self.assertEqual(drift.returncode, 1)
            self.assertIn("binding-kind enum drift", drift.stdout)

    def test_duplicate_schema_keys_return_machine_readable_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "data_construction"
            shutil.copytree(ROOT / "data_construction" / "schemas", target / "schemas")
            shutil.copytree(ROOT / "data_construction" / "operator_design", target / "operator_design")
            schema_path = target / "schemas" / "operator_vocabulary_schema_v0_1.json"
            schema_text = schema_path.read_text(encoding="utf-8")
            schema_path.write_text(
                schema_text.replace(
                    '"$id": "operator_vocabulary_schema_v0_1.json",',
                    '"$id": "operator_vocabulary_schema_v0_1.json",\n'
                    '  "$id": "duplicate.json",',
                    1,
                ),
                encoding="utf-8",
            )
            result = run_tool("check_schema_bundle.py", "--root", base)
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertTrue(any("duplicate JSON object key" in error for error in payload["errors"]))


class ToolOutputCollisionTests(unittest.TestCase):
    def test_tools_refuse_to_overwrite_inputs_or_alias_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            proposals = base / "proposals.jsonl"
            validation_checks = base / "validation-checks.jsonl"
            second_output = base / "report.md"
            write_jsonl(annotations, [{"question_id": "q1", "question": "Question?"}])
            write_json(vocabulary, {"operators": ["FILTER"]})
            write_jsonl(proposals, [{"question_id": "q1"}])
            write_pass_validation_checks(
                validation_checks,
                proposals,
                [{"question_id": "q1"}],
            )
            original_annotations = annotations.read_bytes()

            validator = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                annotations,
                "--structural-only",
            )
            self.assertEqual(validator.returncode, 2)
            self.assertEqual(annotations.read_bytes(), original_annotations)

            review = run_tool(
                "build_review_packet.py",
                "--questions",
                annotations,
                "--proposals",
                proposals,
                "--validation-checks",
                validation_checks,
                "--stage",
                "question_only",
                "--output",
                annotations,
            )
            self.assertEqual(review.returncode, 2)
            self.assertEqual(annotations.read_bytes(), original_annotations)

            stats = run_tool(
                "compute_annotation_stats.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--json-output",
                annotations,
                "--report-output",
                second_output,
            )
            self.assertEqual(stats.returncode, 2)
            self.assertEqual(annotations.read_bytes(), original_annotations)

            comparison = run_tool(
                "compare_operator_granularity.py",
                annotations,
                "--json-output",
                annotations,
                "--report-output",
                second_output,
            )
            self.assertEqual(comparison.returncode, 2)
            self.assertEqual(annotations.read_bytes(), original_annotations)

            output_alias = run_tool(
                "compute_annotation_stats.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--json-output",
                second_output,
                "--report-output",
                second_output,
            )
            self.assertEqual(output_alias.returncode, 2)

            historical_target = ROOT / "data_analysis" / "week1_sample_100.jsonl"
            historical_before = historical_target.read_bytes() if historical_target.exists() else None
            protected = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                historical_target,
                "--structural-only",
            )
            self.assertEqual(protected.returncode, 2)
            if historical_before is None:
                self.assertFalse(historical_target.exists())
            else:
                self.assertEqual(historical_target.read_bytes(), historical_before)

    def test_nonstandard_or_duplicate_key_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "annotations.jsonl"
            vocabulary = base / "vocabulary.json"
            checks = base / "checks.jsonl"
            write_json(vocabulary, {"operators": ["FILTER"]})

            annotations.write_text(
                '{"question_id":"first","question_id":"second"}\n',
                encoding="utf-8",
            )
            duplicate = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                checks,
                "--structural-only",
            )
            self.assertEqual(duplicate.returncode, 2)
            self.assertIn("duplicate JSON object key", duplicate.stderr)
            self.assertFalse(checks.exists())

            annotations.write_text(
                '{"question_id":"q1","score":NaN}\n',
                encoding="utf-8",
            )
            nonfinite = run_tool(
                "validate_annotation.py",
                annotations,
                "--operator-vocabulary",
                vocabulary,
                "--checks-output",
                checks,
                "--structural-only",
            )
            self.assertEqual(nonfinite.returncode, 2)
            self.assertIn("non-standard non-finite JSON number", nonfinite.stderr)
            self.assertFalse(checks.exists())


if __name__ == "__main__":
    unittest.main()
