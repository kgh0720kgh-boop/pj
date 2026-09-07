"""Grounding selection, provenance and pre-output freeze regressions."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data_construction/tools"))
import freeze_narrowed_grounding_plan_v0_1 as grounding
from _common import iter_json_records, json_file_bytes


class NarrowedGroundingPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = list(iter_json_records(ROOT / grounding.INSTRUMENT / "combined_final_records.jsonl"))
        cls.normalized = list(iter_json_records(ROOT / grounding.INSTRUMENT / "final_normalized_candidates.jsonl"))

    def test_every_observation_and_slot_retained_in_frozen_order(self):
        selected = grounding.select_candidates(self.records, self.normalized)
        self.assertEqual(len(selected), 14)
        self.assertEqual(sum(len(c["slots"]) for c in selected), 52)
        self.assertEqual(list(dict.fromkeys(c["question_id"] for c in selected)), list(grounding.IDS))
        self.assertEqual(len({c["observation_id"] for c in selected}), 14)
        self.assertEqual(grounding.select_candidates(list(reversed(self.records)), self.normalized), selected)

    def test_duplicate_missing_ineligible_and_hash_mismatch_refused(self):
        with self.assertRaises(ValueError):
            grounding.select_candidates(self.records + self.records[:1], self.normalized)
        with self.assertRaises(ValueError):
            grounding.select_candidates(self.records, self.normalized[:-1])
        for field, value in (("status", "ineligible"), ("status", "provisional_only")):
            normalized = copy.deepcopy(self.normalized)
            normalized[0]["equivalence_eligibility"][field] = value
            with self.assertRaises(ValueError):
                grounding.select_candidates(self.records, normalized)
        normalized = copy.deepcopy(self.normalized)
        normalized[0]["source_author_record_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            grounding.select_candidates(self.records, normalized)

    def test_plan_has_no_locator_values_and_enumerates_outputs(self):
        selected = grounding.select_candidates(self.records, self.normalized)
        text = json.dumps(selected)
        for forbidden in ("resolved_locator", "required_semantics", "answer-text", "operation_description"):
            self.assertNotIn(forbidden, text)
        outputs = grounding.planned_outputs()
        self.assertEqual(len(outputs), 20)
        self.assertEqual(len(set(outputs.values())), 20)

    def test_every_branch_and_failure_precedence(self):
        self.assertEqual(grounding.decision(1, 1, 0, 0, 0), "STOP_TECHNICAL_OR_LEAKAGE_FAILURE")
        self.assertEqual(grounding.decision(0, 1, 0, 0, 0), "BLOCKED_PINNED_ENVIRONMENT_UNAVAILABLE")
        self.assertEqual(grounding.decision(0, 0, 13, 13, 0), "INCOMPLETE_GROUNDING_COLLECTION")
        self.assertEqual(grounding.decision(0, 0, 14, 13, 1), "REVIEW_AMBIGUITY_OR_COVERAGE_BEFORE_EXECUTION_PLAN")
        self.assertEqual(grounding.decision(0, 0, 14, 14, 1), "REVIEW_AMBIGUITY_OR_COVERAGE_BEFORE_EXECUTION_PLAN")
        self.assertEqual(grounding.decision(0, 0, 14, 14, 0), "FREEZE_GROUNDING_EVIDENCE_FOR_SEPARATE_EXECUTION_PLAN")
        with self.assertRaises(ValueError):
            grounding.decision(0, 0, 13, 14, 0)

    def test_namespace_guard_rejects_orphans_and_broken_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            grounding.require_absent(root)
            namespace = root / grounding.RUN
            namespace.mkdir(parents=True)
            orphan = namespace / "unplanned.json"
            orphan.write_text("{}")
            with self.assertRaises(ValueError):
                grounding.require_absent(root)
            orphan.unlink()
            orphan.symlink_to("missing-target")
            with self.assertRaises(ValueError):
                grounding.require_absent(root)

    def test_paths_reject_parent_aliases_and_symlink_ancestors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("../outside", "/absolute", "foo/../bar", "foo//bar", "foo:bar"):
                with self.assertRaises(ValueError):
                    grounding.safe_path(root, name)
            (root / "alias").symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                grounding.safe_path(root, "alias/output.json")

    def test_git_freeze_proves_committed_output_absence_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)
                return result.stdout.decode().strip()
            git("init", "-q")
            git("config", "user.email", "test@example.invalid")
            git("config", "user.name", "Synthetic Test")
            (root / "implementation.txt").write_text("v1")
            git("add", "implementation.txt")
            git("commit", "-qm", "implementation")
            implementation = git("rev-parse", "HEAD")
            plan = {"implementation_commit": implementation, "selection_counts": {"candidates": 14}}
            path = root / grounding.PLAN
            path.parent.mkdir(parents=True)
            path.write_bytes(json_file_bytes(plan))
            with patch.object(grounding, "SOURCE_COMMIT", implementation), patch.object(
                grounding, "make_plan", return_value=plan
            ):
                with self.assertRaises(ValueError):
                    grounding.validate_plan(root)
                git("add", grounding.PLAN)
                git("commit", "-qm", "plan")
                self.assertEqual(grounding.validate_plan(root, require_output_absence=True)["status"], "pass")
                path.write_bytes(json_file_bytes(plan) + b"\n")
                with self.assertRaises(ValueError):
                    grounding.validate_plan(root)
                path.write_bytes(json_file_bytes(plan))
                output = root / grounding.RUN / "unplanned.json"
                output.parent.mkdir(parents=True)
                output.write_text("{}")
                git("add", grounding.RUN)
                git("commit", "-qm", "output")
                with self.assertRaises(ValueError):
                    grounding.require_absent(root, git("rev-parse", "HEAD"))
                # Past absence remains true; current absence is a distinct check.
                self.assertEqual(grounding.validate_plan(root)["status"], "pass")
                with self.assertRaises(ValueError):
                    grounding.validate_plan(root, require_output_absence=True)
            (root / "implementation.txt").write_text("tampered")
            with self.assertRaises(ValueError):
                grounding.bindings(root, implementation, ("implementation.txt",))


if __name__ == "__main__":
    unittest.main()
