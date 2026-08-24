from __future__ import annotations

import copy
import json
import hashlib
import io
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
import build_granularity_views
import build_question_only_semantic_views as question_only_semantic_views
import build_question_structure_annotation_packet as question_structure_packet
import compare_operator_granularity
import _common
import validate_annotation
import validate_ir_v0_2_reference as ir_v0_2_reference_adapter
import validate_question_structure_annotations as question_structure_validator
import run_ai_question_structure_diagnostic as ai_question_structure_diagnostic


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


def question_structure_annotation(
    *,
    question_id: str = "q1",
    question: str = "Which city opened first?",
    annotator_id: str = "reviewer-001",
    batch_id: str = "phase_a1_batch_01",
    question_view_sha256: str = "a" * 64,
    packet_payload_sha256: str = "b" * 64,
    status: str = "complete",
) -> dict[str, object]:
    annotation: dict[str, object] = {
        "schema_version": "question_structure_annotation_v0_1",
        "annotator_id": annotator_id,
        "batch_id": batch_id,
        "question_id": question_id,
        "question": question,
        "question_view_sha256": question_view_sha256,
        "annotation_packet_payload_sha256": packet_payload_sha256,
        "completed_at": "2026-08-23T12:34:56Z",
        "prior_exposure_declared": False,
        "researcher_approval_self_claimed": False,
        "submission_status": "annotated",
        "abstention_reason": None,
        "attestation": {
            "human_authored": True,
            "worked_independently": True,
            "used_only_packet_question_view": True,
            "did_not_use_answers_grounding_environment_or_proposals": True,
            "locked_free_observation_before_scaffold": True,
        },
        "unconstrained_question_paraphrase": "Find the city selected by opening order.",
        "representation_assessment": {
            "outcome": "complete",
            "rationale": "The scaffold expresses the observation.",
            "schema_gap_descriptions": [],
        },
        "instrument_issues": [],
        "semantic_skeleton": {
            "answer_target": {
                "description": "the requested city",
                "source_cues": [question],
                "implicit_rationale": None,
            },
            "answer_shape_description": "one city name",
            "answer_shape_source_cues": [question],
            "answer_shape_implicit_rationale": None,
            "candidate_structure": {
                "description": "cities with an opening relation",
                "source_cues": [question],
                "implicit_rationale": None,
            },
            "required_information_units": [
                {
                    "unit_id": "u1",
                    "description": "opening order for each candidate",
                    "source_cues": [question],
                    "implicit_rationale": None,
                }
            ],
            "selection_requirement": {
                "description": "select the earliest opening",
                "source_cues": [question],
                "implicit_rationale": None,
            },
            "back_mapping_requirement": None,
        },
        "information_obligations": [
            {
                "obligation_id": "o1",
                "description": "obtain opening order",
                "depends_on": [],
                "source_cues": [question],
                "implicit_rationale": None,
            },
            {
                "obligation_id": "o2",
                "description": "identify the earliest candidate",
                "depends_on": ["o1"],
                "source_cues": [question],
                "implicit_rationale": None,
            },
        ],
        "abstract_topology": {
            "nodes": [
                {
                    "node_id": "n1",
                    "operation_description": "obtain opening order for the candidates",
                    "depends_on": [],
                    "fulfills_obligation_ids": ["o1"],
                    "source_cues": [question],
                    "implicit_rationale": None,
                },
                {
                    "node_id": "n2",
                    "operation_description": "select the earliest candidate",
                    "depends_on": ["n1"],
                    "fulfills_obligation_ids": ["o2"],
                    "source_cues": [question],
                    "implicit_rationale": None,
                },
            ],
            "entry_node_ids": ["n1"],
            "output_node_ids": ["n2"],
        },
        "ambiguity": {
            "present": False,
            "description": None,
            "alternative_interpretations": [],
        },
        "alternative_topology_plans": [],
        "notes": None,
        "gold_claimed": False,
    }
    if status == "abstained":
        annotation.update(
            {
                "submission_status": "abstained",
                "abstention_reason": "The wording is not interpretable without guessing.",
                "representation_assessment": None,
                "instrument_issues": [],
                "semantic_skeleton": None,
                "information_obligations": [],
                "abstract_topology": None,
                "ambiguity": None,
                "alternative_topology_plans": [],
            }
        )
    elif status == "incomplete_schema_gap":
        annotation.update(
            {
                "representation_assessment": {
                    "outcome": "incomplete_schema_gap",
                    "rationale": "The scaffold cannot express a necessary distinction.",
                    "schema_gap_descriptions": ["A necessary distinction has no field."],
                },
                "instrument_issues": [
                    {
                        "type": "cannot_express",
                        "severity": "major",
                        "rationale": "Forcing a topology would erase the observation.",
                    }
                ],
                "semantic_skeleton": None,
                "information_obligations": [],
                "abstract_topology": None,
                "ambiguity": None,
                "alternative_topology_plans": [],
            }
        )
    return {
        "annotation": annotation,
        "annotation_sha256": canonical_sha256(annotation),
    }


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


class HandoffHeadClassifierTests(unittest.TestCase):
    def make_repository(self, directory: str) -> tuple[Path, str, str, str]:
        repository = Path(directory)

        def git(*arguments: str) -> str:
            return subprocess.run(
                ["git", *arguments],
                cwd=repository,
                text=True,
                check=True,
                capture_output=True,
            ).stdout.strip()

        git("init")
        git("config", "user.name", "Fixture")
        git("config", "user.email", "fixture@example.invalid")
        fixture = repository / "fixture.txt"
        fixture.write_text("base\n", encoding="utf-8")
        git("add", "fixture.txt")
        git("commit", "-m", "base")
        base = git("rev-parse", "HEAD")

        fixture.write_text("child\n", encoding="utf-8")
        git("commit", "-am", "child")
        child = git("rev-parse", "HEAD")

        git("checkout", "-b", "sibling", base)
        fixture.write_text("sibling\n", encoding="utf-8")
        git("commit", "-am", "sibling")
        sibling = git("rev-parse", "HEAD")
        return repository, base, child, sibling

    def classify(self, repository: Path, expected: str, current: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", str(ROOT / "scripts/classify_handoff_head.sh"), str(repository), expected, current],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_exact_handoff_head_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, base, _, _ = self.make_repository(directory)
            result = self.classify(repository, base, base)
            self.assertEqual((result.returncode, result.stdout.strip()), (0, "exact"))

    def test_descendant_handoff_head_passes_with_distance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, base, child, _ = self.make_repository(directory)
            result = self.classify(repository, base, child)
            self.assertEqual((result.returncode, result.stdout.strip()), (0, "descendant:1"))

    def test_nonancestor_handoff_head_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, _, child, sibling = self.make_repository(directory)
            result = self.classify(repository, child, sibling)
            self.assertEqual((result.returncode, result.stdout.strip()), (2, "diverged"))

    def test_missing_handoff_head_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, _, child, _ = self.make_repository(directory)
            result = self.classify(repository, "f" * 40, child)
            self.assertEqual((result.returncode, result.stdout.strip()), (2, "missing-baseline"))


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

    def ir_v0_2_reference_envelope(self) -> dict[str, object]:
        return {
            "declared_target_ir_version": "IR_v0.2",
            "local_ir_definition_status": "available",
            "graph_status": "referenced_validated",
            "ir_schema_artifact": {
                "artifact_id": "preserved-ir-v0.2-schema",
                "artifact_type": "json_schema",
                "repository_relative_path": validate_annotation.IR_V0_2_SCHEMA_REPOSITORY_PATH,
                "sha256": validate_annotation.IR_V0_2_SCHEMA_SHA256,
            },
            "graph_artifact": {
                "artifact_id": "preserved-condition-c",
                "artifact_type": "jsonl",
                "repository_relative_path": "historical/ir_v0_2/condition-c.jsonl",
                "sha256": "a" * 64,
            },
            "graph_id": "graph-q1",
            "executable_status": "not_tested",
            "semantic_plan_assessment": "unassessed",
            "validation_checks": [
                {"check": check, "status": "passed"}
                for check in validate_annotation.IR_V0_2_REQUIRED_VALIDATION_CHECKS
            ],
        }

    def test_ir_v0_2_reference_bridge_accepts_a_hash_bound_matching_graph(self) -> None:
        adapter_result = {
            "status": "pass",
            "errors": [],
            "warnings": [{"code": "DEAD_NODE", "message": "unused node"}],
            "graphs": [
                {
                    "graph_id": "graph-q1",
                    "question_id": "q1",
                    "table_id": "t1",
                    "status": "pass",
                    "errors": [],
                }
            ],
        }
        with mock.patch.object(
            validate_annotation,
            "validate_ir_v0_2_reference",
            return_value=adapter_result,
        ) as adapter:
            errors, warnings, checks = (
                validate_annotation.validate_ir_v0_2_execution_graph_reference(
                    self.ir_v0_2_reference_envelope(),
                    "q1",
                    "t1",
                    ROOT,
                )
            )

        self.assertEqual(errors, [])
        self.assertTrue(any("DEAD_NODE=1" in warning for warning in warnings))
        self.assertIn("execution_graph_ir_v0_2_reference_declarations", checks)
        self.assertIn("execution_graph_ir_v0_2_live_reference", checks)
        adapter.assert_called_once_with(
            artifact="historical/ir_v0_2/condition-c.jsonl",
            sha256="a" * 64,
            graph_id="graph-q1",
            all_graphs=False,
            project_root=ROOT,
        )

    def test_ir_v0_2_reference_bridge_validates_the_live_preserved_first_graph(self) -> None:
        artifact_path = ROOT / ir_v0_2_reference_adapter.DEFAULT_ARTIFACT
        first_row = json.loads(
            artifact_path.read_text(encoding="utf-8").splitlines()[0]
        )
        graph = first_row["graph"]
        question_ref = graph["question_ref"]
        envelope = self.ir_v0_2_reference_envelope()
        envelope["graph_artifact"] = {
            "artifact_id": "preserved-condition-c",
            "artifact_type": "jsonl",
            "repository_relative_path": ir_v0_2_reference_adapter.DEFAULT_ARTIFACT,
            "sha256": ir_v0_2_reference_adapter.DEFAULT_ARTIFACT_SHA256,
        }
        envelope["graph_id"] = graph["graph_id"]

        errors, _, checks = (
            validate_annotation.validate_ir_v0_2_execution_graph_reference(
                envelope,
                question_ref["question_id"],
                question_ref["table_id"],
                ROOT,
            )
        )

        self.assertEqual(errors, [])
        self.assertIn("execution_graph_ir_v0_2_live_reference", checks)

    def test_ir_v0_2_reference_bridge_rejects_question_and_table_mismatches(self) -> None:
        adapter_result = {
            "status": "pass",
            "errors": [],
            "warnings": [],
            "graphs": [
                {
                    "graph_id": "graph-q1",
                    "question_id": "other-question",
                    "table_id": "other-table",
                    "status": "pass",
                    "errors": [],
                }
            ],
        }
        with mock.patch.object(
            validate_annotation,
            "validate_ir_v0_2_reference",
            return_value=adapter_result,
        ):
            errors, _, checks = (
                validate_annotation.validate_ir_v0_2_execution_graph_reference(
                    self.ir_v0_2_reference_envelope(),
                    "q1",
                    "t1",
                    ROOT,
                )
            )

        self.assertTrue(any("adapter question_id" in error for error in errors))
        self.assertTrue(any("adapter table_id" in error for error in errors))
        self.assertNotIn("execution_graph_ir_v0_2_live_reference", checks)

    def test_ir_v0_2_reference_bridge_rejects_invalid_declarations_before_adapter(self) -> None:
        envelope = self.ir_v0_2_reference_envelope()
        envelope["declared_target_ir_version"] = "unresolved"
        envelope["local_ir_definition_status"] = "not_checked"
        envelope["ir_schema_artifact"] = {
            "repository_relative_path": "wrong/schema.json",
            "sha256": "b" * 64,
        }
        envelope["graph_artifact"] = {
            "repository_relative_path": "../outside/graph.jsonl",
            "sha256": "UPPERCASE",
        }
        envelope["graph_id"] = ""
        checks = envelope["validation_checks"]
        assert isinstance(checks, list)
        checks.pop()
        checks.append({"check": "parse", "status": "failed"})

        with mock.patch.object(
            validate_annotation,
            "validate_ir_v0_2_reference",
        ) as adapter:
            errors, _, passed_checks = (
                validate_annotation.validate_ir_v0_2_execution_graph_reference(
                    envelope,
                    "q1",
                    "t1",
                    ROOT,
                )
            )

        adapter.assert_not_called()
        self.assertTrue(any("declared_target_ir_version" in error for error in errors))
        self.assertTrue(any("local_ir_definition_status" in error for error in errors))
        self.assertTrue(any("ir_schema_artifact.repository_relative_path" in error for error in errors))
        self.assertTrue(
            any("graph_artifact.repository_relative_path escapes" in error for error in errors)
        )
        self.assertTrue(any("graph_artifact.sha256" in error for error in errors))
        self.assertTrue(any("graph_id" in error for error in errors))
        self.assertTrue(any("'parse' exactly once; found 2" in error for error in errors))
        self.assertTrue(any("'source_reachability' exactly once; found 0" in error for error in errors))
        self.assertEqual(passed_checks, [])

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
            self.assertTrue(
                any("declared_target_ir_version must be exactly" in error for error in errors)
            )
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


class GranularityViewTests(unittest.TestCase):
    def test_exact_projection_preserves_empty_header_without_concrete_values(self) -> None:
        table = {
            "uid": "t1",
            "title": "Visible title",
            "section_title": "Visible section",
            "url": "SECRET_URL",
            "intro": "SECRET_INTRO",
            "section_text": "SECRET_SECTION_TEXT",
            "header": [["", ["SECRET_HEADER_LINK"]], ["Visible column", []]],
            "data": [
                [["SECRET_ROW_VALUE", ["SECRET_DOCUMENT_ID"]], ["SECRET_CELL", []]],
            ],
        }
        projected = build_granularity_views.table_schema_view(table, "t1")
        rendered = json.dumps(projected, ensure_ascii=False)
        self.assertEqual(projected["columns"][0]["label"], "")
        self.assertTrue(projected["columns"][0]["entity_link_capability"])
        self.assertFalse(projected["columns"][1]["entity_link_capability"])
        for secret in (
            "SECRET_URL",
            "SECRET_INTRO",
            "SECRET_SECTION_TEXT",
            "SECRET_HEADER_LINK",
            "SECRET_ROW_VALUE",
            "SECRET_DOCUMENT_ID",
            "SECRET_CELL",
        ):
            self.assertNotIn(secret, rendered)
        self.assertNotIn("row_count", rendered)

    def test_committed_view_manifest_binds_the_verified_sixty_file_subset(self) -> None:
        manifest = json.loads(
            (ROOT / "data_construction/pilot/granularity_input_views_manifest_v0_1.json").read_text(
                encoding="utf-8"
            )
        )
        selected = manifest["selected_environment_artifacts"]
        self.assertEqual(selected["file_count"], 60)
        self.assertEqual(
            selected["tables_canonical_sha256"],
            "0f33966dccd1ee627bdfdddc667bc9a27e278984a226b37b2f2b4e9c565069fc",
        )
        self.assertEqual(
            selected["requests_canonical_sha256"],
            "bed0f41af2cc4497335a82ca06c9c6d00548ca056a8c422774ad6a5a721ed1e8",
        )
        self.assertEqual(
            selected["canonical_sha256"],
            "9e7055ad0e9e351f597237d9bff9edb77b2b58acf8ae8bbd653aeb88dafe69c3",
        )
        self.assertNotIn("/home/", json.dumps(manifest))

        questions_path = ROOT / "data_construction/pilot/questions.jsonl"
        views_path = ROOT / "data_construction/pilot/granularity_input_views.jsonl"
        questions = [json.loads(line) for line in questions_path.read_text().splitlines()]
        views = [json.loads(line) for line in views_path.read_text().splitlines()]
        forged = json.loads(json.dumps(manifest))
        forged["linked_environment"] = {}
        forged["selected_environment_artifacts"]["canonical_sha256"] = "0" * 64
        errors, _ = compare_operator_granularity.validate_view_manifest(
            forged,
            questions_path,
            questions,
            views_path,
            views,
            ROOT,
        )
        self.assertTrue(any("linked_environment" in error for error in errors))
        self.assertTrue(any("internally inconsistent" in error for error in errors))


class GranularityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temporary_directory.name)
        cls.representations = cls.base / "representations.jsonl"
        cls.checks = cls.base / "checks.jsonl"
        built = run_tool(
            "build_granularity_representations.py",
            "--output",
            cls.representations,
        )
        if built.returncode != 0:
            raise AssertionError(built.stderr)
        validated = run_tool(
            "validate_operator_granularity.py",
            cls.representations,
            "--checks-output",
            cls.checks,
        )
        if validated.returncode != 0:
            raise AssertionError(validated.stderr)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def comparator_arguments(self, metrics: Path) -> tuple[object, ...]:
        return (
            self.representations,
            "--questions",
            ROOT / "data_construction/pilot/questions.jsonl",
            "--input-views",
            ROOT / "data_construction/pilot/granularity_input_views.jsonl",
            "--input-views-manifest",
            ROOT / "data_construction/pilot/granularity_input_views_manifest_v0_1.json",
            "--validation-checks",
            self.checks,
            "--json-output",
            metrics,
        )

    def build_packet_fixture(self) -> tuple[list[Path], dict[str, Path]]:
        manifests: list[Path] = []
        packets: dict[str, Path] = {}
        for granularity in ("coarse", "medium", "fine"):
            packet = self.base / f"{granularity}-calibration-fixture.html"
            manifest = self.base / f"{granularity}-calibration-fixture-manifest.json"
            result = run_tool(
                "build_granularity_review_packet.py",
                "--questions",
                ROOT / "data_construction/pilot/questions.jsonl",
                "--input-views",
                ROOT / "data_construction/pilot/granularity_input_views.jsonl",
                "--input-views-manifest",
                ROOT / "data_construction/pilot/granularity_input_views_manifest_v0_1.json",
                "--representations",
                self.representations,
                "--validation-checks",
                self.checks,
                "--granularity",
                granularity,
                "--output",
                packet,
                "--manifest-output",
                manifest,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifests.append(manifest)
            packets[granularity] = packet
        return manifests, packets

    def write_synthetic_review_fixture(
        self,
        path: Path,
        reviewer_id: str,
        granularity: str,
        packet_manifest: Path,
        disagree_on_first: bool,
    ) -> None:
        packet_sha256 = json.loads(packet_manifest.read_text(encoding="utf-8"))[
            "packet_payload"
        ]["sha256"]
        records = [
            json.loads(line)
            for line in self.representations.read_text(encoding="utf-8").splitlines()
        ]
        reviews: list[dict[str, object]] = []
        for index, record in enumerate(records):
            representation = record["representations"][granularity]
            annotation = {
                "schema_version": "operator_representation_review_v0_1",
                "question_id": record["question_id"],
                "granularity": granularity,
                "reviewed_view": "operator_granularity_representation",
                "reviewed_representation_sha256": canonical_sha256(representation),
                "review_packet_payload_sha256": packet_sha256,
                "completed_at": "2026-08-23T12:00:00.000Z",
                "decision": "reject" if disagree_on_first and index == 0 else "accept",
                "assessment": {
                    "semantic_validity": (
                        "invalid" if disagree_on_first and index == 0 else "valid"
                    ),
                    "coverage_status": representation["coverage_status"],
                    "ambiguity_present": representation["ambiguity_present"],
                    "hides_reasoning": representation["hides_reasoning"],
                    "excessive_fragmentation": representation["excessive_fragmentation"],
                },
                "edit": None,
                "notes": "synthetic unit-test contract fixture; not research evidence",
            }
            reviews.append(
                {
                    "reviewer_id": reviewer_id,
                    "annotation": annotation,
                    "annotation_sha256": canonical_sha256(annotation),
                }
            )
        write_json(path, reviews)

    def test_structurally_validated_pilot_remains_pending_real_humans(self) -> None:
        metrics = self.base / "metrics.json"
        result = run_tool("compare_operator_granularity.py", *self.comparator_arguments(metrics))
        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(metrics.read_text(encoding="utf-8"))
        self.assertTrue(payload["integrity_complete"])
        self.assertFalse(payload["human_calibration_complete"])
        self.assertFalse(payload["evidence_complete"])
        self.assertEqual(
            payload["study_status"],
            "structural_integrity_complete_human_calibration_pending",
        )
        self.assertEqual(payload["metrics"]["coarse"]["coverage_count"], 14)
        self.assertEqual(payload["metrics"]["medium"]["coverage_count"], 13)
        self.assertEqual(payload["metrics"]["fine"]["coverage_count"], 13)
        self.assertIsNone(payload["metrics"]["medium"]["annotation_disagreement_rate"])
        self.assertGreater(
            payload["metrics"]["fine"]["mean_graph_length"],
            payload["metrics"]["medium"]["mean_graph_length"],
        )

    def test_validator_rejects_leakage_and_view_hash_tampering(self) -> None:
        tampered = self.base / "tampered.jsonl"
        tampered_checks = self.base / "tampered-checks.jsonl"
        records = [json.loads(line) for line in self.representations.read_text().splitlines()]
        records[0]["representations"]["coarse"]["answer_text"] = "forbidden"
        records[1]["input_views"]["operator_view_sha256"] = "0" * 64
        records[2]["representations"]["medium"]["topology"]["nodes"][0][
            "semantic_role"
        ] = "gold answer: SECRET_LATER_LAYER_VALUE"
        medium_topology = records[3]["representations"]["medium"]["topology"]
        if len(medium_topology["nodes"]) > 1:
            medium_topology["output_node_ids"] = [medium_topology["nodes"][0]["id"]]
        write_jsonl(tampered, records)
        result = run_tool(
            "validate_operator_granularity.py",
            tampered,
            "--checks-output",
            tampered_checks,
        )
        self.assertEqual(result.returncode, 1)
        checks = [json.loads(line) for line in tampered_checks.read_text().splitlines()]
        self.assertEqual(len(checks), 90)
        self.assertTrue(all(check["status"] == "fail" for check in checks))
        errors = "\n".join(checks[0]["errors"])
        self.assertIn("forbidden early-layer keys", errors)
        self.assertIn("view binding mismatch", errors)
        self.assertIn("deterministic structured-plan materialization", errors)
        self.assertIn("every and only DAG sink", errors)

    def test_comparator_rejects_a_check_not_bound_to_live_representation(self) -> None:
        invalid_checks = self.base / "invalid-checks.jsonl"
        metrics = self.base / "invalid-check-metrics.json"
        checks = [json.loads(line) for line in self.checks.read_text().splitlines()]
        checks[0]["representation_canonical_sha256"] = "0" * 64
        write_jsonl(invalid_checks, checks)
        arguments = list(self.comparator_arguments(metrics))
        arguments[arguments.index(self.checks)] = invalid_checks
        result = run_tool("compare_operator_granularity.py", *arguments)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(metrics.exists())
        self.assertIn("canonical hash mismatch", result.stderr)

    def test_review_packet_contains_only_operator_view_and_candidate(self) -> None:
        output = self.base / "coarse-review.html"
        manifest = self.base / "coarse-review-manifest.json"
        result = run_tool(
            "build_granularity_review_packet.py",
            "--questions",
            ROOT / "data_construction/pilot/questions.jsonl",
            "--input-views",
            ROOT / "data_construction/pilot/granularity_input_views.jsonl",
            "--input-views-manifest",
            ROOT / "data_construction/pilot/granularity_input_views_manifest_v0_1.json",
            "--representations",
            self.representations,
            "--validation-checks",
            self.checks,
            "--granularity",
            "coarse",
            "--output",
            output,
            "--manifest-output",
            manifest,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        rendered = output.read_text(encoding="utf-8")
        self.assertIn("8259c70c392c5b75", rendered)
        self.assertIn("Harvest Vision", rendered)
        self.assertNotIn("source_manifest_artifact", rendered)
        self.assertNotIn("selected_environment_artifacts", rendered)
        self.assertNotIn(str(ROOT), rendered)
        packet_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(packet_manifest["review_status"], "packet_created_no_human_reviews")
        self.assertEqual(packet_manifest["review_record_contract"]["reviews_included"], 0)

    def test_external_review_contract_and_exact_packet_rendering_are_enforced(self) -> None:
        manifests, packets = self.build_packet_fixture()
        reviews: list[Path] = []
        for granularity_index, granularity in enumerate(("coarse", "medium", "fine")):
            for reviewer_index, reviewer_id in enumerate(
                ("synthetic-fixture-a", "synthetic-fixture-b")
            ):
                path = self.base / f"{granularity}-{reviewer_id}.json"
                self.write_synthetic_review_fixture(
                    path,
                    reviewer_id,
                    granularity,
                    manifests[granularity_index],
                    disagree_on_first=False,
                )
                reviews.append(path)

        metrics = self.base / "synthetic-reviewed-metrics.json"
        arguments = list(self.comparator_arguments(metrics))
        for manifest in manifests:
            arguments.extend(("--review-packet-manifest", manifest))
        for review in reviews:
            arguments.extend(("--human-review", review))
        result = run_tool("compare_operator_granularity.py", *arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(metrics.read_text(encoding="utf-8"))
        self.assertTrue(payload["integrity_complete"])
        self.assertTrue(payload["human_calibration_complete"])
        self.assertTrue(payload["evidence_complete"])
        self.assertTrue(payload["semantic_confirmation_complete"])
        self.assertEqual(payload["metrics"]["coarse"]["annotation_disagreement_count"], 0)
        self.assertEqual(
            payload["reviewer_authentication_status"],
            "procedural_not_machine_verifiable",
        )

        disputed_reviews = json.loads(reviews[1].read_text(encoding="utf-8"))
        disputed_reviews[0]["annotation"]["decision"] = "reject"
        disputed_reviews[0]["annotation"]["assessment"]["semantic_validity"] = "invalid"
        disputed_reviews[0]["annotation_sha256"] = canonical_sha256(
            disputed_reviews[0]["annotation"]
        )
        write_json(reviews[1], disputed_reviews)
        disputed_metrics = self.base / "synthetic-disputed-metrics.json"
        disputed_arguments = list(self.comparator_arguments(disputed_metrics))
        for manifest in manifests:
            disputed_arguments.extend(("--review-packet-manifest", manifest))
        for review in reviews:
            disputed_arguments.extend(("--human-review", review))
        disputed = run_tool("compare_operator_granularity.py", *disputed_arguments)
        self.assertEqual(disputed.returncode, 2, disputed.stderr)
        disputed_payload = json.loads(disputed_metrics.read_text(encoding="utf-8"))
        self.assertTrue(disputed_payload["human_calibration_complete"])
        self.assertTrue(disputed_payload["evidence_complete"])
        self.assertFalse(disputed_payload["semantic_confirmation_complete"])
        self.assertEqual(
            disputed_payload["study_status"],
            "human_calibration_complete_adjudication_pending",
        )
        self.assertEqual(
            disputed_payload["metrics"]["coarse"]["annotation_disagreement_count"], 1
        )

        abstention_reviews: list[Path] = []
        for source in reviews:
            target = self.base / f"abstain-{source.name}"
            raw = json.loads(source.read_text(encoding="utf-8"))
            for envelope in raw:
                annotation = envelope["annotation"]
                annotation["decision"] = "abstain"
                annotation["assessment"] = {
                    "semantic_validity": "uncertain",
                    "coverage_status": "uncertain",
                    "ambiguity_present": "uncertain",
                    "hides_reasoning": "uncertain",
                    "excessive_fragmentation": "uncertain",
                }
                envelope["annotation_sha256"] = canonical_sha256(annotation)
            write_json(target, raw)
            abstention_reviews.append(target)
        abstention_metrics = self.base / "synthetic-abstention-metrics.json"
        abstention_arguments = list(self.comparator_arguments(abstention_metrics))
        for manifest in manifests:
            abstention_arguments.extend(("--review-packet-manifest", manifest))
        for review in abstention_reviews:
            abstention_arguments.extend(("--human-review", review))
        abstained = run_tool("compare_operator_granularity.py", *abstention_arguments)
        self.assertEqual(abstained.returncode, 2, abstained.stderr)
        abstention_payload = json.loads(abstention_metrics.read_text(encoding="utf-8"))
        self.assertFalse(abstention_payload["human_calibration_complete"])
        self.assertFalse(abstention_payload["evidence_complete"])
        self.assertEqual(
            abstention_payload["metrics"]["coarse"]["human_abstention_count"], 60
        )

        coarse_packet = packets["coarse"]
        coarse_packet.write_text(
            coarse_packet.read_text(encoding="utf-8").replace(
                "<h1>HybridQA", "<h1>ALTERED HybridQA", 1
            ),
            encoding="utf-8",
        )
        coarse_manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
        coarse_manifest["packet_artifact"]["sha256"] = hashlib.sha256(
            coarse_packet.read_bytes()
        ).hexdigest()
        write_json(manifests[0], coarse_manifest)
        tampered_metrics = self.base / "tampered-packet-metrics.json"
        tampered_arguments = list(self.comparator_arguments(tampered_metrics))
        for manifest in manifests:
            tampered_arguments.extend(("--review-packet-manifest", manifest))
        for review in reviews:
            tampered_arguments.extend(("--human-review", review))
        tampered = run_tool("compare_operator_granularity.py", *tampered_arguments)
        self.assertEqual(tampered.returncode, 2)
        self.assertFalse(tampered_metrics.exists())
        self.assertIn("deterministic approved rendering", tampered.stderr)


class QuestionOnlyStructurePhaseATests(unittest.TestCase):
    def setUp(self) -> None:
        self.questions_path = ROOT / "data_construction/pilot/questions.jsonl"
        self.split_path = ROOT / "data_construction/manifests/split_manifest_v0_1.json"
        self.schema_path = (
            ROOT / "data_construction/schemas/question_structure_annotation_v0_1.json"
        )
        self.questions = list(_common.iter_json_records(self.questions_path))
        self.views = question_only_semantic_views.build_records(self.questions)
        self.plan = json.loads(
            (
                ROOT
                / "data_construction/pilot/question_structure_study_plan_v0_1.json"
            ).read_text(encoding="utf-8")
        )
        self.batch_id = self.plan["phase_a1"]["active_batch_id"]
        self.selected_ids = question_structure_packet.validate_study_plan(
            self.plan,
            self.batch_id,
            [view["question_id"] for view in self.views],
            {
                "repository_relative_path": self.plan["source_questions"][
                    "repository_relative_path"
                ],
                "record_count": 30,
                "sha256": self.plan["source_questions"]["sha256"],
            },
        )
        self.payload = question_structure_packet.build_payload(
            self.views,
            self.selected_ids,
            self.batch_id,
            hashlib.sha256(self.schema_path.read_bytes()).hexdigest(),
        )

    def packet_context(self) -> dict[str, object]:
        return {
            "selected_ids": self.selected_ids,
            "selected_views": self.views[:10],
            "payload": self.payload,
            "payload_sha256": canonical_sha256(self.payload),
        }

    def raw_records(self) -> list[dict[str, object]]:
        payload_sha256 = canonical_sha256(self.payload)
        return [
            question_structure_annotation(
                question_id=item["question_view"]["question_id"],
                question=item["question_view"]["question"],
                batch_id=self.batch_id,
                question_view_sha256=item["question_view_sha256"],
                packet_payload_sha256=payload_sha256,
            )
            for item in self.payload["items"]
        ]

    def view_manifest_fixture(
        self,
        views_path: Path,
        views: list[dict[str, object]],
    ) -> dict[str, object]:
        implementation_paths = [
            ROOT
            / "data_construction/schemas/question_only_semantic_view_v0_1.json",
            ROOT / "data_construction/tools/_common.py",
            ROOT
            / "data_construction/tools/build_question_only_semantic_views.py",
        ]
        implementation_artifacts = sorted(
            [
                {
                    "repository_relative_path": path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                for path in implementation_paths
            ],
            key=lambda item: item["repository_relative_path"].encode("utf-8"),
        )
        record_hashes = [
            {
                "question_id": view["question_id"],
                "canonical_sha256": canonical_sha256(view),
            }
            for view in views
        ]
        return {
            "schema_version": "question_only_semantic_view_manifest_v0_1",
            "builder_version": "question_only_semantic_view_builder_v0_1",
            "provenance": {
                "code_commit": "a" * 40,
                "implementation_artifacts": implementation_artifacts,
                "implementation_artifact_set_sha256": canonical_sha256(
                    implementation_artifacts
                ),
            },
            "views_artifact": {
                "repository_relative_path": views_path.relative_to(ROOT).as_posix(),
                "record_count": 30,
                "sha256": hashlib.sha256(views_path.read_bytes()).hexdigest(),
            },
            "questions_artifact": {
                "repository_relative_path": self.questions_path.relative_to(ROOT).as_posix(),
                "record_count": 30,
                "sha256": hashlib.sha256(self.questions_path.read_bytes()).hexdigest(),
            },
            "split_manifest_artifact": {
                "repository_relative_path": self.split_path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(self.split_path.read_bytes()).hexdigest(),
            },
            "allocation_contract": {
                "dataset_role": "annotation_schema_pilot",
                "source_split": "dev",
                "question_count": 30,
                "release_eligible": True,
                "zero_overlap_verified": True,
                "override_used": False,
                "question_order_matches_split_manifest": True,
            },
            "record_hash_contract": {
                "canonicalization": "sorted_compact_json_utf8_sha256_v0_1",
                "ordered_question_ids_sha256": canonical_sha256(
                    [view["question_id"] for view in views]
                ),
                "ordered_record_hashes_sha256": canonical_sha256(record_hashes),
                "records": record_hashes,
            },
            "view_contract": {
                "allowed_fields": [
                    "schema_version",
                    "visibility",
                    "question_id",
                    "question",
                ],
                "visible_input_categories": ["question_id", "question_text"],
                "excluded_categories": question_only_semantic_views.EXCLUDED_CATEGORIES,
                "environment_exposed": False,
                "answer_or_execution_evidence_exposed": False,
                "proposal_or_historical_label_exposed": False,
                "other_annotator_output_exposed": False,
                "leakage_audit_status": "pass_by_exact_projection",
            },
        }

    def schema_errors(self, record: dict[str, object]) -> list[object]:
        from jsonschema import Draft202012Validator, FormatChecker

        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return list(
            Draft202012Validator(
                schema,
                format_checker=FormatChecker(),
            ).iter_errors(record)
        )

    def test_question_only_views_are_the_exact_canonical_four_field_projection(self) -> None:
        split_manifest = json.loads(self.split_path.read_text(encoding="utf-8"))
        question_only_semantic_views.validate_split_provenance(split_manifest, ROOT)
        allocated_ids = question_only_semantic_views.validate_questions(
            self.questions,
            self.questions_path,
            split_manifest,
        )
        self.assertEqual(len(self.views), 30)
        self.assertEqual(allocated_ids, [view["question_id"] for view in self.views])
        for source, view in zip(self.questions, self.views, strict=True):
            self.assertEqual(
                set(view),
                {"schema_version", "visibility", "question_id", "question"},
            )
            self.assertEqual(view["question_id"], source["question_id"])
            self.assertEqual(view["question"], source["question"])
            self.assertNotIn("table_id", view)
            self.assertNotIn("dataset_role", view)
            self.assertNotIn("source_split", view)

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            alternate_questions = base / "questions.jsonl"
            shutil.copyfile(self.questions_path, alternate_questions)
            output = base / "views.jsonl"
            manifest = base / "manifest.json"
            refused = run_tool(
                "build_question_only_semantic_views.py",
                "--questions",
                alternate_questions,
                "--output",
                output,
                "--manifest-output",
                manifest,
            )
            self.assertEqual(refused.returncode, 2)
            self.assertIn("canonical release inputs are required", refused.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            refused_external_output = run_tool(
                "build_question_only_semantic_views.py",
                "--output",
                base / "views.jsonl",
                "--manifest-output",
                base / "manifest.json",
            )
            self.assertEqual(refused_external_output.returncode, 2)
            self.assertIn(
                "canonical outputs must remain inside the repository",
                refused_external_output.stderr,
            )

    def test_view_manifest_reconstructs_exact_source_projection(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=ROOT / "data_construction/pilot"
        ) as directory:
            views_path = Path(directory) / "views.jsonl"
            write_jsonl(views_path, self.views)
            manifest = self.view_manifest_fixture(views_path, self.views)

            def committed_blob_sha256(
                project_root: Path,
                commit: str,
                relative_path: str,
            ) -> str:
                self.assertEqual(commit, "a" * 40)
                return hashlib.sha256((project_root / relative_path).read_bytes()).hexdigest()

            with mock.patch.object(
                question_structure_packet,
                "_git_commit_exists",
                return_value=True,
            ), mock.patch.object(
                question_structure_packet,
                "_git_blob_sha256",
                side_effect=committed_blob_sha256,
            ):
                bindings = question_structure_packet.validate_views_manifest(
                    manifest,
                    views_path,
                    self.views,
                    [view["question_id"] for view in self.views],
                    ROOT,
                )
                self.assertEqual(bindings["questions_path"], self.questions_path)

                tampered_views = copy.deepcopy(self.views)
                tampered_views[0]["question"] += " TAMPERED"
                write_jsonl(views_path, tampered_views)
                tampered_manifest = self.view_manifest_fixture(
                    views_path,
                    tampered_views,
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "exact ordered four-field projection",
                ):
                    question_structure_packet.validate_views_manifest(
                        tampered_manifest,
                        views_path,
                        tampered_views,
                        [view["question_id"] for view in tampered_views],
                        ROOT,
                    )

    def test_phase_a_question_view_bytes_obey_atomic_write_once(self) -> None:
        payload = _common.jsonl_file_bytes(self.views)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "views.jsonl"
            self.assertEqual(
                _common.write_output_batch({"views": (output, payload)}),
                {"views": "written"},
            )
            self.assertEqual(
                _common.write_output_batch({"views": (output, payload)}),
                {"views": "unchanged"},
            )
            output.write_bytes(b"preserve prior phase-a views\n")
            with self.assertRaisesRegex(ValueError, "pass --overwrite"):
                _common.write_output_batch({"views": (output, payload)})
            self.assertEqual(output.read_bytes(), b"preserve prior phase-a views\n")
            self.assertEqual(
                _common.write_output_batch(
                    {"views": (output, payload)},
                    overwrite=True,
                ),
                {"views": "overwritten"},
            )
            self.assertEqual(output.read_bytes(), payload)

    def test_raw_schema_accepts_complete_abstained_and_partial_gap_records(self) -> None:
        for status in ("complete", "abstained", "incomplete_schema_gap"):
            with self.subTest(status=status):
                record = question_structure_annotation(status=status)
                self.assertEqual(self.schema_errors(record), [])

        multiline = question_structure_annotation()
        multiline["annotation"]["unconstrained_question_paraphrase"] = (
            "First line of the free observation.\nSecond line remains valid."
        )
        multiline["annotation_sha256"] = canonical_sha256(multiline["annotation"])
        self.assertEqual(self.schema_errors(multiline), [])

    def test_raw_schema_rejects_closed_ontology_fields_and_inconsistent_completion(self) -> None:
        closed_ontology = question_structure_annotation()
        closed_ontology["annotation"]["abstract_topology"]["nodes"][0][
            "semantic_function"
        ] = "SELECT_CANDIDATES"
        closed_ontology["annotation_sha256"] = canonical_sha256(
            closed_ontology["annotation"]
        )

        forbidden_extra = question_structure_annotation()
        forbidden_extra["annotation"]["table_id"] = "later-layer-identity"
        forbidden_extra["annotation_sha256"] = canonical_sha256(
            forbidden_extra["annotation"]
        )

        complete_with_issue = question_structure_annotation()
        complete_with_issue["annotation"]["instrument_issues"] = [
            {
                "type": "rubric_unclear",
                "severity": "minor",
                "rationale": "This contradicts a complete assessment.",
            }
        ]
        complete_with_issue["annotation_sha256"] = canonical_sha256(
            complete_with_issue["annotation"]
        )

        empty_obligation_mapping = question_structure_annotation()
        empty_obligation_mapping["annotation"]["abstract_topology"]["nodes"][0][
            "fulfills_obligation_ids"
        ] = []
        empty_obligation_mapping["annotation_sha256"] = canonical_sha256(
            empty_obligation_mapping["annotation"]
        )

        for label, record in (
            ("closed_ontology", closed_ontology),
            ("forbidden_extra", forbidden_extra),
            ("complete_with_issue", complete_with_issue),
            ("empty_obligation_mapping", empty_obligation_mapping),
        ):
            with self.subTest(label=label):
                self.assertTrue(self.schema_errors(record))

    def test_packet_payload_is_exactly_ordered_blank_and_rubric_bound(self) -> None:
        self.assertEqual(self.payload["batch_id"], self.batch_id)
        self.assertEqual(
            [item["question_view"]["question_id"] for item in self.payload["items"]],
            self.selected_ids,
        )
        self.assertEqual(len(self.payload["items"]), 10)
        for item in self.payload["items"]:
            self.assertEqual(
                set(item["question_view"]),
                {"schema_version", "visibility", "question_id", "question"},
            )
            self.assertEqual(
                item["question_view_sha256"],
                canonical_sha256(item["question_view"]),
            )
        instrument = self.payload["instrument_contract"]
        self.assertEqual(
            instrument["annotation_schema_sha256"],
            hashlib.sha256(self.schema_path.read_bytes()).hexdigest(),
        )
        self.assertTrue(instrument["stage1_visible_instructions"])
        self.assertTrue(instrument["stage2_visible_instructions"])
        self.assertEqual(
            instrument["stage_transition_contract"],
            "all_ten_nonempty_then_normal_ui_readonly_lock_before_scaffold_display_"
            "procedural_attestation_not_adversarial_blinding",
        )
        self.assertEqual(
            instrument["rubric_version"],
            "question_structure_open_coding_rubric_v0_1",
        )
        self.assertFalse(instrument["closed_semantic_label_ontology_exposed"])
        self.assertFalse(instrument["prefilled_semantic_decomposition_exposed"])

        blank = self.payload["blank_annotation_form"]
        self.assertEqual(blank["information_obligations"], [])
        self.assertEqual(blank["abstract_topology"]["nodes"], [])
        self.assertEqual(blank["semantic_skeleton"]["required_information_units"], [])
        self.assertEqual(blank["semantic_skeleton"]["answer_target"]["description"], "")

        payload_text = json.dumps(self.payload, ensure_ascii=False, sort_keys=True)
        html_text = question_structure_packet.render_html(
            self.payload,
            canonical_sha256(self.payload),
        )
        self.assertIn('<section id="stage-2" hidden>', html_text)
        self.assertIn('id="lock-observations"', html_text)
        self.assertLess(
            html_text.index('id="prior-exposure"'),
            html_text.index('id="stage1-items"'),
        )
        self.assertIn("paraphrase.disabled = true", html_text)
        self.assertIn("priorExposureControl.addEventListener('change'", html_text)
        self.assertIn("priorExposureControl.disabled = true", html_text)
        self.assertIn("locked_free_observation_before_scaffold", html_text)
        for question in self.questions:
            self.assertNotIn(question["table_id"], payload_text)
            self.assertNotIn(question["table_id"], html_text)
        for forbidden in (
            "TABLE_LOOKUP",
            "DOCUMENT_QA",
            "COMPARE_VALUES",
            "ARG_SELECT",
            "operator_topology",
            "granularity_representation",
            "llm_proposed",
        ):
            self.assertNotIn(forbidden, payload_text)
            self.assertNotIn(forbidden, html_text)
        self.assertEqual(
            question_structure_packet.render_html(
                self.payload,
                canonical_sha256(self.payload),
            ),
            html_text,
        )

    def test_packet_only_contract_reconstructs_exact_render_hash_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            views_path = base / "views.jsonl"
            views_manifest_path = base / "views-manifest.json"
            study_plan_path = base / "study-plan.json"
            packet_path = base / "packet.html"
            packet_manifest_path = base / "packet-manifest.json"
            write_jsonl(views_path, self.views)
            write_json(views_manifest_path, {"fixture": True})
            write_json(study_plan_path, self.plan)

            payload_sha256 = canonical_sha256(self.payload)
            packet_bytes = question_structure_packet.render_html(
                self.payload,
                payload_sha256,
            ).encode("utf-8")
            packet_path.write_bytes(packet_bytes)
            inputs = {
                "views": views_path,
                "views_manifest": views_manifest_path,
                "study_plan": study_plan_path,
                "annotation_schema": self.schema_path,
                "view_schema": (
                    ROOT
                    / "data_construction/schemas/question_only_semantic_view_v0_1.json"
                ),
            }
            live_hashes = {
                label: hashlib.sha256(path.read_bytes()).hexdigest()
                for label, path in inputs.items()
            }
            builder_commit = "c" * 40
            manifest = question_structure_packet.build_manifest(
                payload=self.payload,
                payload_sha256=payload_sha256,
                packet_bytes=packet_bytes,
                batch_id=self.batch_id,
                selected_ids=self.selected_ids,
                inputs=inputs,
                live_hashes=live_hashes,
                output_path=packet_path,
                project_root=ROOT,
                code_commit=builder_commit,
                paths=question_structure_packet.implementation_paths(ROOT),
            )
            write_json(packet_manifest_path, manifest)
            questions_artifact = {
                "repository_relative_path": self.plan["source_questions"][
                    "repository_relative_path"
                ],
                "record_count": 30,
                "sha256": self.plan["source_questions"]["sha256"],
            }
            with mock.patch.object(
                question_structure_packet,
                "validate_views_manifest",
                return_value={"questions_artifact": questions_artifact},
            ), mock.patch.object(
                question_structure_validator,
                "_validate_builder_commit_bindings",
                return_value=builder_commit,
            ):
                context = question_structure_validator.validate_packet_contract(
                    views_path=views_path,
                    views_manifest_path=views_manifest_path,
                    study_plan_path=study_plan_path,
                    schema_path=self.schema_path,
                    packet_path=packet_path,
                    packet_manifest_path=packet_manifest_path,
                    batch_id=self.batch_id,
                    project_root=ROOT,
                )
                self.assertEqual(context["selected_ids"], self.selected_ids)
                self.assertEqual(context["payload_sha256"], payload_sha256)
                self.assertEqual(
                    context["packet_sha256"],
                    hashlib.sha256(packet_bytes).hexdigest(),
                )

                packet_path.write_bytes(packet_bytes + b"\n")
                with self.assertRaisesRegex(
                    ValueError,
                    "exact deterministic rendering",
                ):
                    question_structure_validator.validate_packet_contract(
                        views_path=views_path,
                        views_manifest_path=views_manifest_path,
                        study_plan_path=study_plan_path,
                        schema_path=self.schema_path,
                        packet_path=packet_path,
                        packet_manifest_path=packet_manifest_path,
                        batch_id=self.batch_id,
                        project_root=ROOT,
                    )

    def test_raw_validator_accepts_one_complete_ordered_ten_record_array(self) -> None:
        records = self.raw_records()
        validator = question_structure_validator.load_schema_validator(self.schema_path)
        results, global_errors = question_structure_validator.validate_raw_records(
            records,
            self.packet_context(),
            validator,
        )
        self.assertEqual(global_errors, [])
        self.assertEqual(len(results), 10)
        self.assertTrue(all(result["errors"] == [] for result in results))
        self.assertTrue(
            all(
                question_structure_validator.raw_gate_eligible(result["annotation"])
                for result in results
            )
        )

    def test_raw_validator_rejects_hash_cue_reference_cycle_exposure_and_batch_defects(
        self,
    ) -> None:
        validator = question_structure_validator.load_schema_validator(self.schema_path)

        wrong_hash = self.raw_records()
        wrong_hash[0]["annotation_sha256"] = "0" * 64

        wrong_cue = self.raw_records()
        wrong_cue[0]["annotation"]["semantic_skeleton"]["answer_target"][
            "source_cues"
        ] = ["NOT AN EXACT QUESTION SUBSTRING"]
        wrong_cue[0]["annotation_sha256"] = canonical_sha256(wrong_cue[0]["annotation"])

        missing_reference = self.raw_records()
        missing_reference[0]["annotation"]["information_obligations"][1][
            "depends_on"
        ] = ["missing-obligation"]
        missing_reference[0]["annotation_sha256"] = canonical_sha256(
            missing_reference[0]["annotation"]
        )

        cycle = self.raw_records()
        cycle[0]["annotation"]["abstract_topology"]["nodes"][0]["depends_on"] = [
            "n2"
        ]
        cycle[0]["annotation_sha256"] = canonical_sha256(cycle[0]["annotation"])

        exposed = self.raw_records()
        exposed[0]["annotation"]["prior_exposure_declared"] = True
        exposed[0]["annotation_sha256"] = canonical_sha256(exposed[0]["annotation"])

        uncovered_obligation = self.raw_records()
        uncovered_obligation[0]["annotation"]["abstract_topology"]["nodes"][1][
            "fulfills_obligation_ids"
        ] = ["o1"]
        uncovered_obligation[0]["annotation_sha256"] = canonical_sha256(
            uncovered_obligation[0]["annotation"]
        )

        mixed_annotators = self.raw_records()
        mixed_annotators[-1]["annotation"]["annotator_id"] = "reviewer-002"
        mixed_annotators[-1]["annotation_sha256"] = canonical_sha256(
            mixed_annotators[-1]["annotation"]
        )

        short_batch = self.raw_records()[:-1]
        empty_batch: list[dict[str, object]] = []

        cases = (
            ("wrong_hash", wrong_hash, "annotation_sha256"),
            ("wrong_cue", wrong_cue, "exact case-sensitive question substring"),
            ("missing_reference", missing_reference, "missing dependency"),
            ("cycle", cycle, "cycle"),
            ("exposure", exposed, "prior exposure"),
            ("uncovered_obligation", uncovered_obligation, "does not cover every"),
            ("mixed_annotators", mixed_annotators, "one stable annotator"),
            ("short_batch", short_batch, "exactly 10 records"),
            ("empty_batch", empty_batch, "exactly 10 records"),
        )
        for label, records, expected_error in cases:
            with self.subTest(label=label):
                results, global_errors = (
                    question_structure_validator.validate_raw_records(
                        records,
                        self.packet_context(),
                        validator,
                    )
                )
                all_errors = [
                    *global_errors,
                    *[
                        error
                        for result in results
                        for error in result["errors"]
                    ],
                ]
                self.assertTrue(all_errors)
                self.assertTrue(
                    any(expected_error in error for error in all_errors),
                    all_errors,
                )

    def test_empty_raw_cli_writes_one_batch_scope_failure_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            annotations = base / "empty.json"
            checks = base / "checks.jsonl"
            write_json(annotations, [])
            packet_context = {
                **self.packet_context(),
                "packet_sha256": "c" * 64,
                "packet_manifest_sha256": "d" * 64,
                "live_hashes": {
                    "views": "e" * 64,
                    "views_manifest": "f" * 64,
                    "study_plan": "0" * 64,
                    "annotation_schema": "1" * 64,
                },
            }
            stdout = io.StringIO()
            with mock.patch.object(
                sys,
                "argv",
                [
                    "validate_question_structure_annotations.py",
                    str(annotations),
                    "--batch-id",
                    self.batch_id,
                    "--checks-output",
                    str(checks),
                ],
            ), mock.patch.object(
                question_structure_validator,
                "git_tracked_commit_identity",
                return_value="a" * 40,
            ), mock.patch.object(
                question_structure_validator,
                "validate_packet_contract",
                return_value=packet_context,
            ), mock.patch.object(sys, "stdout", stdout):
                result = question_structure_validator.main()

            self.assertEqual(result, 1)
            output = json.loads(stdout.getvalue())
            self.assertEqual(output["raw_records"], 0)
            self.assertEqual(output["batch_fail_checks"], 1)
            self.assertGreater(output["global_error_count"], 0)
            self.assertEqual(output["record_error_count"], 0)
            check_records = list(_common.iter_json_records(checks))
            self.assertEqual(len(check_records), 1)
            self.assertEqual(check_records[0]["validation_scope"], "batch")
            self.assertEqual(check_records[0]["status"], "fail")
            self.assertTrue(check_records[0]["errors"])

    def test_phase_a_clis_refuse_overwrite_of_provenance_and_implementation_inputs(
        self,
    ) -> None:
        targets = {
            "historical_manifest": (
                ROOT / "data_construction/manifests/historical_exposed_ids.json"
            ),
            "historical_tree_artifact": (
                ROOT / "historical/ir_v0_2/recovery_manifest_v0_1.json"
            ),
            "view_builder": (
                ROOT / "data_construction/tools/build_question_only_semantic_views.py"
            ),
            "packet_builder": (
                ROOT / "data_construction/tools/build_question_structure_annotation_packet.py"
            ),
            "validator": (
                ROOT / "data_construction/tools/validate_question_structure_annotations.py"
            ),
        }
        before = {label: path.read_bytes() for label, path in targets.items()}
        with tempfile.TemporaryDirectory(
            dir=ROOT / "data_construction/pilot"
        ) as directory:
            base = Path(directory)
            empty_annotations = base / "empty.json"
            write_json(empty_annotations, [])
            cases = (
                (
                    "view_historical_manifest",
                    "build_question_only_semantic_views.py",
                    (
                        "--output",
                        targets["historical_manifest"],
                        "--manifest-output",
                        base / "view-manifest.json",
                        "--overwrite",
                    ),
                    "collides with input",
                ),
                (
                    "view_historical_tree",
                    "build_question_only_semantic_views.py",
                    (
                        "--output",
                        targets["historical_tree_artifact"],
                        "--manifest-output",
                        base / "historical-tree-view-manifest.json",
                        "--overwrite",
                    ),
                    "read-only historical tree",
                ),
                (
                    "view_builder_self",
                    "build_question_only_semantic_views.py",
                    (
                        "--output",
                        base / "views.jsonl",
                        "--manifest-output",
                        targets["view_builder"],
                        "--overwrite",
                    ),
                    "collides with input",
                ),
                (
                    "packet_builder_self",
                    "build_question_structure_annotation_packet.py",
                    (
                        "--batch-id",
                        self.batch_id,
                        "--output",
                        targets["packet_builder"],
                        "--manifest-output",
                        base / "packet-manifest.json",
                        "--overwrite",
                    ),
                    "collides with input",
                ),
                (
                    "validator_self",
                    "validate_question_structure_annotations.py",
                    (
                        empty_annotations,
                        "--batch-id",
                        self.batch_id,
                        "--checks-output",
                        targets["validator"],
                        "--overwrite",
                    ),
                    "collides with input",
                ),
            )
            for label, tool, arguments, expected_error in cases:
                with self.subTest(label=label):
                    refused = run_tool(tool, *arguments)
                    self.assertEqual(refused.returncode, 2, refused.stderr)
                    self.assertIn(expected_error, refused.stderr)
        for label, path in targets.items():
            self.assertEqual(path.read_bytes(), before[label])


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
    def test_atomic_write_once_batch_preflights_before_any_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            first = base / "first.json"
            second = base / "second.jsonl"
            first.write_bytes(b"original bytes\n")

            with self.assertRaisesRegex(ValueError, "pass --overwrite"):
                _common.write_output_batch(
                    {
                        "first": (first, b"replacement bytes\n"),
                        "second": (second, b'{"value":1}\n'),
                    }
                )
            self.assertEqual(first.read_bytes(), b"original bytes\n")
            self.assertFalse(second.exists())

            statuses = _common.write_output_batch(
                {
                    "first": (first, b"original bytes\n"),
                    "second": (second, b'{"value":1}\n'),
                }
            )
            self.assertEqual(statuses, {"first": "unchanged", "second": "written"})
            self.assertEqual(first.read_bytes(), b"original bytes\n")
            self.assertEqual(second.read_bytes(), b'{"value":1}\n')

            statuses = _common.write_output_batch(
                {
                    "first": (first, b"replacement bytes\n"),
                    "second": (second, b'{"value":2}\n'),
                },
                overwrite=True,
            )
            self.assertEqual(statuses, {"first": "overwritten", "second": "overwritten"})
            self.assertEqual(first.read_bytes(), b"replacement bytes\n")
            self.assertEqual(second.read_bytes(), b'{"value":2}\n')
            self.assertEqual(list(base.glob(".*.tmp")), [])

    def test_granularity_writers_require_explicit_overwrite_for_changed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            representations = base / "representations.jsonl"
            checks = base / "checks.jsonl"
            metrics = base / "metrics.json"
            packet = base / "coarse.html"
            packet_manifest = base / "coarse-manifest.json"

            built = run_tool(
                "build_granularity_representations.py",
                "--output",
                representations,
            )
            self.assertEqual(built.returncode, 0, built.stderr)
            representation_bytes = representations.read_bytes()
            identical = run_tool(
                "build_granularity_representations.py",
                "--output",
                representations,
            )
            self.assertEqual(identical.returncode, 0, identical.stderr)
            self.assertEqual(representations.read_bytes(), representation_bytes)

            representations.write_bytes(b"do not silently truncate\n")
            refused = run_tool(
                "build_granularity_representations.py",
                "--output",
                representations,
            )
            self.assertEqual(refused.returncode, 2)
            self.assertIn("pass --overwrite", refused.stderr)
            self.assertEqual(representations.read_bytes(), b"do not silently truncate\n")
            replaced = run_tool(
                "build_granularity_representations.py",
                "--output",
                representations,
                "--overwrite",
            )
            self.assertEqual(replaced.returncode, 0, replaced.stderr)
            self.assertEqual(representations.read_bytes(), representation_bytes)

            validated = run_tool(
                "validate_operator_granularity.py",
                representations,
                "--checks-output",
                checks,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            check_bytes = checks.read_bytes()
            checks.write_bytes(b"preserve prior checks\n")
            refused_checks = run_tool(
                "validate_operator_granularity.py",
                representations,
                "--checks-output",
                checks,
            )
            self.assertEqual(refused_checks.returncode, 2)
            self.assertIn("pass --overwrite", refused_checks.stderr)
            self.assertEqual(checks.read_bytes(), b"preserve prior checks\n")
            replaced_checks = run_tool(
                "validate_operator_granularity.py",
                representations,
                "--checks-output",
                checks,
                "--overwrite",
            )
            self.assertEqual(replaced_checks.returncode, 0, replaced_checks.stderr)
            self.assertEqual(checks.read_bytes(), check_bytes)

            comparator_arguments = (
                representations,
                "--questions",
                ROOT / "data_construction/pilot/questions.jsonl",
                "--input-views",
                ROOT / "data_construction/pilot/granularity_input_views.jsonl",
                "--input-views-manifest",
                ROOT / "data_construction/pilot/granularity_input_views_manifest_v0_1.json",
                "--validation-checks",
                checks,
                "--json-output",
                metrics,
            )
            compared = run_tool("compare_operator_granularity.py", *comparator_arguments)
            self.assertEqual(compared.returncode, 2, compared.stderr)
            metric_bytes = metrics.read_bytes()
            metrics.write_bytes(b"preserve prior metrics\n")
            refused_metrics = run_tool(
                "compare_operator_granularity.py", *comparator_arguments
            )
            self.assertEqual(refused_metrics.returncode, 2)
            self.assertIn("pass --overwrite", refused_metrics.stderr)
            self.assertEqual(metrics.read_bytes(), b"preserve prior metrics\n")
            replaced_metrics = run_tool(
                "compare_operator_granularity.py",
                *comparator_arguments,
                "--overwrite",
            )
            self.assertEqual(replaced_metrics.returncode, 2, replaced_metrics.stderr)
            self.assertEqual(metrics.read_bytes(), metric_bytes)

            packet_arguments = (
                "--questions",
                ROOT / "data_construction/pilot/questions.jsonl",
                "--input-views",
                ROOT / "data_construction/pilot/granularity_input_views.jsonl",
                "--input-views-manifest",
                ROOT / "data_construction/pilot/granularity_input_views_manifest_v0_1.json",
                "--representations",
                representations,
                "--validation-checks",
                checks,
                "--granularity",
                "coarse",
                "--output",
                packet,
                "--manifest-output",
                packet_manifest,
            )
            packet_result = run_tool(
                "build_granularity_review_packet.py", *packet_arguments
            )
            self.assertEqual(packet_result.returncode, 0, packet_result.stderr)
            packet_bytes = packet.read_bytes()
            packet_manifest.write_bytes(b"preserve prior packet manifest\n")
            refused_packet = run_tool(
                "build_granularity_review_packet.py", *packet_arguments
            )
            self.assertEqual(refused_packet.returncode, 2)
            self.assertIn("pass --overwrite", refused_packet.stderr)
            self.assertEqual(packet.read_bytes(), packet_bytes)
            self.assertEqual(
                packet_manifest.read_bytes(), b"preserve prior packet manifest\n"
            )
            replaced_packet = run_tool(
                "build_granularity_review_packet.py",
                *packet_arguments,
                "--overwrite",
            )
            self.assertEqual(replaced_packet.returncode, 0, replaced_packet.stderr)
            self.assertEqual(packet.read_bytes(), packet_bytes)
            self.assertTrue(packet_manifest.read_bytes().startswith(b"{\n"))

    def test_granularity_view_builder_exposes_explicit_overwrite(self) -> None:
        with mock.patch.object(
            sys,
            "argv",
            [
                "build_granularity_views.py",
                "--wikitables-checkout",
                "source-checkout",
                "--overwrite",
            ],
        ):
            args = build_granularity_views.parse_args()
        self.assertTrue(args.overwrite)

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
                "--questions",
                ROOT / "data_construction/pilot/questions.jsonl",
                "--input-views",
                ROOT / "data_construction/pilot/granularity_input_views.jsonl",
                "--input-views-manifest",
                ROOT / "data_construction/pilot/granularity_input_views_manifest_v0_1.json",
                "--validation-checks",
                validation_checks,
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

            ir_target = ROOT / "historical/ir_v0_2/ir/spec_v0_2.md"
            ir_before = ir_target.read_bytes()
            protected_ir = run_tool(
                "validate_operator_granularity.py",
                annotations,
                "--checks-output",
                ir_target,
            )
            self.assertEqual(protected_ir.returncode, 2)
            self.assertEqual(ir_target.read_bytes(), ir_before)

            fake_checkout = base / "official-source"
            (fake_checkout / "tables_tok").mkdir(parents=True)
            checkout_target = fake_checkout / "tables_tok" / "do-not-overwrite.json"
            checkout_target.write_text("source bytes\n", encoding="utf-8")
            protected_checkout = run_tool(
                "build_granularity_views.py",
                "--wikitables-checkout",
                fake_checkout,
                "--output",
                checkout_target,
                "--manifest-output",
                base / "view-manifest.json",
            )
            self.assertEqual(protected_checkout.returncode, 2)
            self.assertEqual(checkout_target.read_text(encoding="utf-8"), "source bytes\n")

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


class AIQuestionStructureDiagnosticTests(unittest.TestCase):
    @staticmethod
    def _stage1_records(
        views: list[dict[str, object]], reviewer_slot: str
    ) -> list[dict[str, object]]:
        return [
            {
                "schema_version": "ai_question_structure_stage1_observation_v0_1",
                "run_id": ai_question_structure_diagnostic.RUN_ID,
                "reviewer_slot": reviewer_slot,
                "evidence_class": "ai_pipeline_diagnostic_non_human_non_gold",
                "question_id": view["question_id"],
                "question": view["question"],
                "question_view_sha256": canonical_sha256(view),
                "visibility": "question_only_no_environment_answer_or_proposals",
                "free_observation": "Identify the qualifying subject and return the requested property.",
                "generation_boundary": {
                    "producer_kind": "ai_model",
                    "human_authored": False,
                    "counts_as_human_evidence": False,
                    "counts_toward_phase_gate": False,
                    "scaffold_visible_during_generation": False,
                    "other_reviewer_output_consulted": False,
                    "runtime_input_isolation": "procedural_prompt_only_not_machine_authenticated",
                    "statistical_independence_claimed": False,
                },
            }
            for view in views
        ]

    @staticmethod
    def _annotation_records(
        views: list[dict[str, object]],
        stage1: list[dict[str, object]],
        reviewer_slot: str,
    ) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for view, observation in zip(views, stage1):
            source = question_structure_annotation(
                question_id=str(view["question_id"]),
                question=str(view["question"]),
                question_view_sha256=canonical_sha256(view),
            )["annotation"]
            payload = {
                key: copy.deepcopy(source[key])
                for key in (
                    "unconstrained_question_paraphrase",
                    "representation_assessment",
                    "instrument_issues",
                    "semantic_skeleton",
                    "information_obligations",
                    "abstract_topology",
                    "ambiguity",
                    "alternative_topology_plans",
                    "notes",
                    "gold_claimed",
                )
            }
            payload["unconstrained_question_paraphrase"] = observation["free_observation"]
            records.append(
                {
                    "schema_version": "ai_question_structure_diagnostic_annotation_v0_1",
                    "run_id": ai_question_structure_diagnostic.RUN_ID,
                    "reviewer_slot": reviewer_slot,
                    "evidence_class": "ai_pipeline_diagnostic_non_human_non_gold",
                    "question_id": view["question_id"],
                    "question": view["question"],
                    "question_view_sha256": canonical_sha256(view),
                    "stage1_observation_sha256": canonical_sha256(observation),
                    "generation_provenance": {
                        "producer_kind": "ai_model",
                        "model_id": "codex_gpt-5",
                        "model_revision_status": "revision_not_exposed",
                        "seed_status": "not_supported",
                        "generation_interface": "codex_subagent",
                        "separate_agent_context": True,
                        "other_reviewer_output_consulted": False,
                        "runtime_input_isolation": "procedural_prompt_only_not_machine_authenticated",
                        "statistical_independence_claimed": False,
                        "raw_response_status": "structured_artifact_is_primary_capture_no_separate_raw_response",
                    },
                    "evidence_boundary": {
                        "human_authored": False,
                        "counts_as_human_evidence": False,
                        "counts_toward_phase_gate": False,
                        "gold_claimed": False,
                        "semantic_agreement_claimed": False,
                        "phase_a1_pass_claimed": False,
                        "phase_a2_entry_claimed": False,
                        "phase_b_entry_claimed": False,
                        "common_executable_graph_claimed": False,
                    },
                    "semantic_payload": payload,
                }
            )
        return records

    def test_frozen_contract_is_live_and_non_evidentiary(self) -> None:
        plan, views, bindings = ai_question_structure_diagnostic.validate_contract()
        self.assertEqual(len(views), 30)
        self.assertGreaterEqual(len(bindings), 12)
        self.assertEqual(
            plan["continuation_policy"]["policy"],
            "always_emit_analysis_regardless_of_semantic_concordance",
        )
        self.assertEqual(
            plan["canonical_effects"],
            {
                "human_annotation_count_delta": 0,
                "human_review_count_delta": 0,
                "human_agreement_observation_count_delta": 0,
                "phase_a1_gate_satisfied": False,
                "phase_a2_entry_authorized": False,
                "phase_b_entry_authorized": False,
                "gold_claimed": False,
                "modeling_ready_claimed": False,
                "common_executable_graph_claimed": False,
                "grounding_or_execution_evaluated": False,
            },
        )

    def test_valid_stage1_bundle_and_false_human_boundary(self) -> None:
        _, views, _ = ai_question_structure_diagnostic.validate_contract()
        records = self._stage1_records(views, "ai_reviewer_01")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stage1.jsonl"
            write_jsonl(path, records)
            _, checks, errors = ai_question_structure_diagnostic.validate_stage1_records(
                path, "ai_reviewer_01"
            )
            self.assertEqual(errors, [])
            self.assertEqual(len(checks), 30)
            self.assertTrue(all(check["status"] == "pass" for check in checks))

            records[0]["generation_boundary"]["human_authored"] = True
            write_jsonl(path, records)
            _, _, errors = ai_question_structure_diagnostic.validate_stage1_records(
                path, "ai_reviewer_01"
            )
            self.assertTrue(any("False was expected" in error for error in errors))

    def test_alignment_coverage_is_id_rename_invariant_and_exhaustive(self) -> None:
        def payload(prefix: str) -> dict[str, object]:
            return {
                "semantic_skeleton": {
                    "required_information_units": [
                        {"unit_id": f"{prefix}_u1"},
                        {"unit_id": f"{prefix}_u2"},
                    ]
                },
                "information_obligations": [
                    {"obligation_id": f"{prefix}_o1"},
                    {"obligation_id": f"{prefix}_o2"},
                ],
                "abstract_topology": {
                    "nodes": [
                        {"node_id": f"{prefix}_n1"},
                        {"node_id": f"{prefix}_n2"},
                    ]
                },
            }

        packet = {"left": {"semantic_payload": payload("l")}, "right": {"semantic_payload": payload("r")}}
        alignment: dict[str, object] = {}
        for layer, stem in (
            ("required_information_unit", "u"),
            ("obligation", "o"),
            ("topology_node", "n"),
        ):
            alignment[f"{layer}_groups"] = [
                {
                    "group_id": f"g_{stem}1",
                    "left_ids": [f"l_{stem}1"],
                    "right_ids": [f"r_{stem}1"],
                },
                {
                    "group_id": f"g_{stem}2",
                    "left_ids": [f"l_{stem}2"],
                    "right_ids": [f"r_{stem}2"],
                },
            ]
            alignment[f"{layer}_unmatched_items"] = []
            self.assertEqual(
                ai_question_structure_diagnostic._coverage_errors(alignment, packet, layer),
                [],
            )
        alignment["topology_node_groups"][1]["left_ids"] = ["l_n1"]
        errors = ai_question_structure_diagnostic._coverage_errors(
            alignment, packet, "topology_node"
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("exactly-once", errors[0])

    def test_graph_invariants_and_joint_empty_edge_semantics(self) -> None:
        topology = {
            "nodes": [
                {"node_id": "n1", "depends_on": []},
                {"node_id": "n2", "depends_on": ["n1"]},
                {"node_id": "n3", "depends_on": ["n1"]},
                {"node_id": "n4", "depends_on": ["n2", "n3"]},
            ]
        }
        self.assertEqual(
            ai_question_structure_diagnostic.graph_invariants(topology),
            {
                "node_count": 4,
                "edge_count": 4,
                "root_count": 1,
                "sink_count": 1,
                "longest_path_node_count": 3,
                "branch_present": True,
                "join_present": True,
            },
        )

    def test_disposition_keeps_unresolved_and_conflict_visible(self) -> None:
        base = {
            "component_decisions": {
                key: {"status": "equivalent"}
                for key in ("answer_target", "answer_shape", "candidate_structure", "ambiguity", "alternative_plans")
            },
            "required_information_unit_groups": [
                {"left_ids": ["l1"], "right_ids": ["r1"], "status": "equivalent", "impact": "material"}
            ],
            "obligation_groups": [
                {"left_ids": ["l2"], "right_ids": ["r2"], "status": "equivalent", "impact": "material"}
            ],
            "topology_node_groups": [
                {"left_ids": ["l3"], "right_ids": ["r3"], "status": "equivalent", "impact": "material"}
            ],
            "required_information_unit_unmatched_items": [],
            "obligation_unmatched_items": [],
            "topology_node_unmatched_items": [],
        }
        graph = {
            "projected_reachability_dice": 1.0,
            "mapped_root_jaccard": 1.0,
            "mapped_sink_jaccard": 1.0,
        }
        self.assertEqual(
            ai_question_structure_diagnostic._question_disposition(base, graph),
            "FULL_EQUIVALENCE",
        )
        unresolved = copy.deepcopy(base)
        unresolved["component_decisions"]["ambiguity"]["status"] = "unresolved"
        self.assertEqual(
            ai_question_structure_diagnostic._question_disposition(unresolved, graph),
            "INDETERMINATE",
        )
        conflict = copy.deepcopy(base)
        conflict["obligation_groups"][0]["status"] = "substantive_conflict"
        self.assertEqual(
            ai_question_structure_diagnostic._question_disposition(conflict, graph),
            "SUBSTANTIVE_DISAGREEMENT",
        )

    def test_synthetic_full_pipeline_reaches_truthful_final_metrics(self) -> None:
        plan, views, _ = ai_question_structure_diagnostic.validate_contract()
        stage1_01 = self._stage1_records(views, "ai_reviewer_01")
        stage1_02 = self._stage1_records(views, "ai_reviewer_02")
        annotations_01 = self._annotation_records(views, stage1_01, "ai_reviewer_01")
        annotations_02 = self._annotation_records(views, stage1_02, "ai_reviewer_02")
        packet, _ = ai_question_structure_diagnostic.build_alignment_packet(
            annotations_01, annotations_02
        )
        alignments: list[dict[str, object]] = []
        for item in packet:
            alignments.append(
                {
                    "schema_version": "ai_question_structure_alignment_v0_1",
                    "run_id": ai_question_structure_diagnostic.RUN_ID,
                    "question_id": item["question_id"],
                    "alignment_packet_record_sha256": canonical_sha256(item),
                    "evidence_class": "ai_alignment_diagnostic_non_human_non_gold",
                    "component_decisions": {
                        key: {"status": "equivalent", "rationale": "The two descriptions express the same diagnostic commitment."}
                        for key in ("answer_target", "answer_shape", "candidate_structure", "ambiguity", "alternative_plans")
                    },
                    "required_information_unit_groups": [
                        {
                            "group_id": "gu1",
                            "left_ids": ["u1"],
                            "right_ids": ["u1"],
                            "status": "equivalent",
                            "impact": "material",
                            "rationale": "The required information is the same.",
                        }
                    ],
                    "required_information_unit_unmatched_items": [],
                    "obligation_groups": [
                        {
                            "group_id": f"go{number}",
                            "left_ids": [f"o{number}"],
                            "right_ids": [f"o{number}"],
                            "status": "equivalent",
                            "impact": "material",
                            "rationale": "The obligations are equivalent.",
                        }
                        for number in (1, 2)
                    ],
                    "obligation_unmatched_items": [],
                    "topology_node_groups": [
                        {
                            "group_id": f"gn{number}",
                            "left_ids": [f"n{number}"],
                            "right_ids": [f"n{number}"],
                            "status": "equivalent",
                            "impact": "material",
                            "rationale": "The semantic operations are equivalent.",
                        }
                        for number in (1, 2)
                    ],
                    "topology_node_unmatched_items": [],
                    "aligner_summary": "The two synthetic representations are equivalent.",
                    "evidence_boundary": {
                        "producer_kind": "ai_alignment_assistant",
                        "human_adjudication_performed": False,
                        "counts_as_semantic_agreement": False,
                        "gold_claimed": False,
                        "correctness_claimed": False,
                    },
                }
            )
        holdout_ids = [
            qid
            for batch in plan["batches"]
            if batch["diagnostic_role"] == "shadow_holdout"
            for qid in batch["question_ids"]
        ]
        view_by_id = {view["question_id"]: view for view in views}
        topology_records: list[dict[str, object]] = []
        for qid in holdout_ids:
            view = view_by_id[qid]
            topology_records.append(
                {
                    "schema_version": "independent_question_topology_ai_v0_1",
                    "run_id": ai_question_structure_diagnostic.RUN_ID,
                    "evidence_class": "ai_independent_topology_diagnostic_non_human_non_gold",
                    "question_id": qid,
                    "question": view["question"],
                    "question_view_sha256": canonical_sha256(view),
                    "visibility": "question_only_no_upstream_structure_environment_answer_or_proposals",
                    "nodes": [
                        {
                            "node_id": "t1",
                            "operation_description": "identify the qualifying subject",
                            "depends_on": [],
                            "source_cues": [view["question"]],
                            "implicit_rationale": None,
                        },
                        {
                            "node_id": "t2",
                            "operation_description": "return the requested property",
                            "depends_on": ["t1"],
                            "source_cues": [view["question"]],
                            "implicit_rationale": None,
                        },
                    ],
                    "entry_node_ids": ["t1"],
                    "output_node_ids": ["t2"],
                    "alternative_topologies": [],
                    "generation_provenance": {
                        "producer_kind": "ai_model",
                        "model_id": "codex_gpt-5",
                        "model_revision_status": "revision_not_exposed",
                        "seed_status": "not_supported",
                        "generation_interface": "codex_subagent",
                        "fresh_context": True,
                        "runtime_input_isolation": "procedural_prompt_only_not_machine_authenticated",
                    },
                    "evidence_boundary": {
                        "upstream_structure_exposed": False,
                        "environment_exposed": False,
                        "answer_exposed": False,
                        "operator_vocabulary_exposed": False,
                        "human_authored": False,
                        "gold_claimed": False,
                        "executable_graph_claimed": False,
                    },
                }
            )
        metrics = ai_question_structure_diagnostic.build_metrics(
            annotations_01,
            annotations_02,
            packet,
            alignments,
            topology_records,
        )
        self.assertEqual(metrics["pipeline_execution_status"], "complete")
        self.assertEqual(metrics["scientific_gate_status"], "NOT_EVALUATED_AI_SUBSTITUTE")
        self.assertEqual(metrics["alignment"]["all_questions"]["disposition_counts"], {"FULL_EQUIVALENCE": 30})
        self.assertEqual(metrics["canonical_research_status"]["human_evidence_count"], 0)
        self.assertFalse(metrics["canonical_research_status"]["phase_a2_entry_claimed"])
        report = ai_question_structure_diagnostic.render_report(metrics)
        self.assertIn("Human evidence: 0", report)
        self.assertIn("not authorized", report)


if __name__ == "__main__":
    unittest.main()
