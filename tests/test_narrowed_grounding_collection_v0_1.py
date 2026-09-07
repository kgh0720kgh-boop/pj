"""Post-collection integrity regressions, not part of the pre-run instrument."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data_construction/tools"))
import narrowed_grounding_runtime_v0_1 as runtime


class GroundingCollectionIntegrityTests(unittest.TestCase):
    def test_frozen_failure_reconstructs_without_promoting_exposed_raw(self):
        payloads, metrics = runtime.result_artifacts(ROOT)
        paths = runtime.freeze.planned_outputs()
        for label, data in payloads.items():
            self.assertEqual((ROOT / paths[label]).read_bytes(), data)
        self.assertEqual(metrics["decision"], "STOP_TECHNICAL_OR_LEAKAGE_FAILURE")
        self.assertEqual(metrics["technical_errors"], 6)
        self.assertEqual(metrics["candidate_status_counts"], {"technical_invalid": 14})
        self.assertEqual(metrics["source_slot_status_counts"], {"technical_invalid": 52})
        self.assertEqual(metrics["operator_status_counts"], {"technical_invalid": 43})
        self.assertEqual(payloads["records"], b"")
        checks = [json.loads(line) for line in payloads["checks"].splitlines()]
        self.assertEqual(len(checks), 6)
        for check in checks:
            self.assertEqual((check["parse"], check["schema"]), ("pass", "pass"))
            self.assertEqual(check["raw_parsed"]["provenance"]["prior_exposure"], "known_exposed")
            self.assertEqual(check["errors"], ["grounding context prior exposure not cleared"])
            self.assertEqual(check["candidates"], [])

    def test_dispatch_and_first_capture_bind_all_six_raw_files(self):
        receipt = json.loads((ROOT / "state/narrowed_grounding_author_dispatch_v0_1.json").read_text())
        self.assertFalse(receipt["fork_context"])
        self.assertFalse(receipt["model_override_requested"])
        self.assertEqual([a["question_index"] for a in receipt["authors"]], list(range(1, 7)))
        self.assertEqual(len({a["agent_id"] for a in receipt["authors"]}), 6)
        for author in receipt["authors"]:
            packet = author["packet"]
            self.assertEqual(hashlib.sha256((ROOT / packet["path"]).read_bytes()).hexdigest(), packet["sha256"])
            raw_path = author["raw_output"]
            data = (ROOT / raw_path).read_bytes()
            raw = json.loads(data)
            self.assertEqual(raw["packet_sha256"], packet["payload_sha256"])
            self.assertEqual(raw["provenance"]["context_id"], author["procedural_context_id"])
            self.assertEqual(runtime.verify_raw_committed(ROOT, raw_path, data, receipt["packet_freeze_commit"]),
                             "af8d2a2723137a94ee44706f17a7b96fb50fe2a8")

    def test_historical_freeze_absence_does_not_mean_outputs_still_absent(self):
        check = runtime.validate_runtime(ROOT)
        self.assertEqual(check["status"], "pass")
        self.assertFalse(check["current_output_absence_checked"])
        self.assertFalse(check["grounding_results_validated"])
        with self.assertRaises(ValueError):
            runtime.validate_runtime(ROOT, require_absence=True)
        for path in runtime.freeze.planned_outputs().values():
            self.assertTrue((ROOT / path).is_file())


if __name__ == "__main__":
    unittest.main()
