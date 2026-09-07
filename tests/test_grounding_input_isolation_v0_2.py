"""Question-free design invariants and Git freeze integrity, not host qualification."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data_construction/tools"))
import freeze_grounding_input_isolation_v0_2 as isolation
from _common import json_file_bytes, read_json


class GroundingInputIsolationTests(unittest.TestCase):
    def setUp(self):
        self.design = read_json(ROOT / isolation.DESIGN)

    def test_design_is_question_free_and_not_transport_evidence(self):
        isolation.validate_design(self.design)
        for key in self.design["scope"]:
            changed = copy.deepcopy(self.design)
            changed["scope"][key] = ["synthetic-not-a-research-id"] if key == "research_question_ids" else True
            with self.subTest(key=key), self.assertRaises(ValueError):
                isolation.validate_design(changed)
        changed = copy.deepcopy(self.design)
        changed["evidence_boundary"]["transport_qualified"] = True
        with self.assertRaises(ValueError):
            isolation.validate_design(changed)

    def test_every_context_source_is_required(self):
        for category in isolation.CATEGORIES:
            changed = copy.deepcopy(self.design)
            changed["inventory_categories"].remove(category)
            with self.subTest(category=category), self.assertRaises(ValueError):
                isolation.validate_design(changed)
        changed = copy.deepcopy(self.design)
        changed["inventory_categories"].append(isolation.CATEGORIES[0])
        with self.assertRaises(ValueError):
            isolation.validate_design(changed)

    def test_stop_unknown_incomplete_and_qualification_order_is_frozen(self):
        changed = copy.deepcopy(self.design)
        changed["branch_order"].reverse()
        with self.assertRaises(ValueError):
            isolation.validate_design(changed)
        self.assertIn("Expected control results never qualify", self.design["aggregate_probe_rule"])

    def test_controls_cannot_be_dropped_relabelled_or_retried(self):
        for replacement in ([], self.design["probe_contract"]["cases"][:1]):
            changed = copy.deepcopy(self.design)
            changed["probe_contract"]["cases"] = replacement
            with self.assertRaises(ValueError):
                isolation.validate_design(changed)
        for value in (True, 0, 2):
            changed = copy.deepcopy(self.design)
            changed["probe_contract"]["max_launches_per_case"] = value
            with self.assertRaises(ValueError):
                isolation.validate_design(changed)
        changed = copy.deepcopy(self.design)
        changed["probe_contract"]["cases"][1]["expected"] = isolation.BRANCHES[3]
        with self.assertRaises(ValueError):
            isolation.validate_design(changed)

    def test_protocol_and_guide_identities_cannot_alias_or_rewrite_old_bytes(self):
        for field, value in (("new_version_required_fields", ["protocol_sha256"]), ("old_bytes_changed", True)):
            changed = copy.deepcopy(self.design)
            changed["identity_migration"][field] = value
            with self.assertRaises(ValueError):
                isolation.validate_design(changed)

    def test_full_commit_identity_required(self):
        for oid in ("HEAD", "bd841ea", "g" * 40, None):
            with self.subTest(oid=oid), self.assertRaises(ValueError):
                isolation.make_plan(ROOT, oid)

    def test_absence_guards_both_namespaces_and_symlinks(self):
        for namespace in isolation.NAMESPACES:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                isolation.require_absent(root)
                path = root / namespace
                path.mkdir(parents=True)
                orphan = path / "unplanned"
                orphan.symlink_to("missing")
                with self.assertRaises(ValueError):
                    isolation.require_absent(root)
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / namespace
                path.parent.mkdir(parents=True)
                path.symlink_to("missing")
                with self.assertRaises(ValueError):
                    isolation.require_absent(root)

    def test_preserved_failure_sources_match_original_commit(self):
        entries = isolation.bindings(ROOT, isolation.SOURCE_COMMIT, isolation.SOURCE_PATHS)
        old_outputs = [e for e in entries if "/narrowed_grounding_v0_1/" in e["path"]]
        self.assertEqual(len(old_outputs), 20)
        self.assertEqual(sum("/raw/" in e["path"] for e in old_outputs), 6)

    def test_freeze_requires_commit_and_rejects_rewrite(self):
        self.exercise_git_freeze(outputs_at_freeze=False)

    def test_freeze_rejects_preexisting_output_even_after_removal(self):
        self.exercise_git_freeze(outputs_at_freeze=True)

    def exercise_git_freeze(self, outputs_at_freeze):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], check=True,
                                      capture_output=True).stdout.decode().strip()
            git("init", "-q")
            git("config", "user.email", "test@example.invalid")
            git("config", "user.name", "Synthetic Test")
            (root / "implementation.txt").write_text("synthetic")
            git("add", "implementation.txt")
            git("commit", "-qm", "implementation")
            implementation = git("rev-parse", "HEAD")
            plan = {"implementation_commit": implementation, "preserved_artifacts": []}
            path = root / isolation.PLAN
            path.parent.mkdir(parents=True)
            path.write_bytes(json_file_bytes(plan))
            with patch.object(isolation, "SOURCE_COMMIT", implementation), patch.object(
                isolation, "make_plan", return_value=plan
            ):
                with self.assertRaises(ValueError):
                    isolation.validate_plan(root)
                if outputs_at_freeze:
                    output = root / isolation.NAMESPACES[0] / "early.json"
                    output.parent.mkdir(parents=True)
                    output.write_text("{}")
                    git("add", isolation.NAMESPACES[0])
                git("add", isolation.PLAN)
                git("commit", "-qm", "freeze")
                if outputs_at_freeze:
                    output.unlink()
                    git("add", "-u")
                    git("commit", "-qm", "remove early synthetic output")
                    with self.assertRaises(ValueError):
                        isolation.validate_plan(root)
                    return
                result = isolation.validate_plan(root, require_output_absence=True)
                self.assertFalse(result["transport_qualified"])
                self.assertFalse(result["grounding_authorized"])
                path.write_bytes(json_file_bytes(plan) + b"\n")
                with self.assertRaises(ValueError):
                    isolation.validate_plan(root)
                path.write_bytes(json_file_bytes(plan))
                output = root / isolation.NAMESPACES[0] / "later.json"
                output.parent.mkdir(parents=True)
                output.write_text("{}")
                self.assertEqual(isolation.validate_plan(root)["status"], "pass")
                with self.assertRaises(ValueError):
                    isolation.validate_plan(root, require_output_absence=True)


if __name__ == "__main__":
    unittest.main()
