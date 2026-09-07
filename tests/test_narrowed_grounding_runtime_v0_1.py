"""Synthetic grounding regressions; never write a research packet or annotation."""
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
import narrowed_grounding_runtime_v0_1 as r


def rehash(packet):
    for candidate in packet["candidates"]:
        candidate["candidate_sha256"] = r.digest({k: v for k, v in candidate.items() if k != "candidate_sha256"})
    packet["environment_sha256"] = r.digest(packet["environment"])
    packet["payload_sha256"] = r.digest({k: v for k, v in packet.items() if k != "payload_sha256"})
    return packet


def packet_fixture(index=1, slot_counts=(2,)):
    environment = {"source_split": "dev", "table_id": "synthetic-table", "title": "Synthetic",
                   "section_title": "", "columns": [{"column_index": 0, "text": "Name", "linked_document_ids": []}],
                   "rows": [{"row_index": 0, "cells": [{"column_index": 0, "text": "Example", "linked_document_ids": ["doc/a~b"]}]}],
                   "linked_documents": [{"document_id": "doc/a~b", "text": "Synthetic source text."}],
                   "scope_contract": {"table_scope": "full_selected_question_table", "document_scope": "table_link_closure",
                                      "question_or_answer_guided_pruning": False, "oracle_document_selection": False,
                                      "truncation": "none", "external_retrieval": False,
                                      "dataset_provided_question_table_binding": True, "table_retrieval_evaluated": False,
                                      "full_table_link_closure_supplied": True}}
    semantic = {"nodes": [{"node_id": "n1", "role": "ACQUIRE_PROPERTY", "other_role_description": None,
                           "description": "Synthetic relation", "source_cues": ["Name"], "implicit_rationale": None,
                           "depends_on": []}], "entry_node_ids": ["n1"], "output_node_ids": ["n1"]}
    candidates = []
    for i, count in enumerate(slot_counts, 1):
        nodes = [{"node_id": f"op{j}", "record_local_label": "Synthetic", "operation_description": "Read a property",
                  "depends_on": [f"op{j-1}"] if j > 1 else [], "input_slot_ids": [f"slot{j}"],
                  "output_description": "Synthetic text", "operator_boundary_rationale": "Synthetic fixture",
                  "label_is_cross_record_taxonomy_key": False} for j in range(1, count+1)]
        candidates.append({"observation_alias": f"observation_{i:02}", "target_backbone_variant_id": "primary",
                           "graph": {"nodes": nodes, "entry_node_ids": ["op1"], "output_node_ids": [f"op{count}"]},
                           "binding_slots": [{"slot_id": f"slot{j}", "required_semantics": "Name column", "environment_modality": "table_header",
                                              "cardinality": "one", "grounding_status": "not_grounded_in_this_stage", "resolved_locator": None}
                                             for j in range(1, count+1)],
                           "backbone_operator_mappings": [{"mapping_id": "mapping1", "mapping_kind": "one_to_many" if count > 1 else "one_to_one",
                                                           "backbone_node_ids": ["n1"], "operator_node_ids": [n["node_id"] for n in nodes]}],
                           "distinguishing_assumptions": ["Synthetic only"]})
    return rehash({"schema_version": "narrowed_grounding_packet_v0_1", "packet_id": f"synthetic_packet_{index}",
                   "question_id": f"synthetic_q{index}", "question": "Name in 2001?", "environment": environment,
                   "backbones": [{"variant_id": "primary", "graph": semantic}], "candidates": candidates,
                   "protocol_sha256": "0"*64, "response_schema_sha256": "0"*64})


def response_fixture(packet):
    candidates = []
    for source in packet["candidates"]:
        slots = [{"slot_id": slot["slot_id"], "status": "resolved", "role": "Synthetic name",
                  "expected_type": "Text", "cardinality": slot["cardinality"], "reason": None, "searched_scope": [],
                  "bindings": [{"kind": "table_column", "view_sha256": packet["environment_sha256"], "value_type": "Text",
                                "pointer": "/columns/0", "table_id": "synthetic-table", "column_index": 0, "column_label": "Name"}]}
                 for slot in source["binding_slots"]]
        operators = [{"node_id": n["node_id"], "status": "specified", "role": "Synthetic identity",
                      "expected_output_type": "Text", "no_additional_arguments": True,
                      "parameters": [], "reason": "Identity needs no additional parameters"} for n in source["graph"]["nodes"]]
        candidates.append({"observation_alias": source["observation_alias"], "candidate_sha256": source["candidate_sha256"],
                           "identified_alternative_ids": ["a1"], "alternative_relationship": "single",
                           "alternatives": [{"alternative_id": "a1", "assumptions": [], "slots": slots, "operators": operators}], "limitations": []})
    return {"schema_version": "narrowed_grounding_raw_v0_1", "packet_id": packet["packet_id"],
            "packet_sha256": packet["payload_sha256"], "question_id": packet["question_id"], "environment_sha256": packet["environment_sha256"],
            "input_delivery": {"status": "complete", "reason": None},
            "provenance": {"model_id": "synthetic_fixture_not_a_model_run", "model_revision": None,
                           "revision_status": "revision_not_exposed", "seed": None, "seed_status": "not_supported",
                           "context_id": packet["packet_id"], "prior_exposure": "procedurally_attested_none",
                           "raw_capture_status": "full_response_bytes", "attempts": [{"packet_sha256": packet["payload_sha256"], "delivery": "response_delivered"}]},
            "candidates": candidates}


class GroundingRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.packet = packet_fixture()
        self.raw = response_fixture(self.packet)

    def check(self, raw=None, packet=None):
        return r.validate_response(json.dumps(raw or self.raw).encode(), packet or self.packet)

    def alternative(self):
        return self.raw["candidates"][0]["alternatives"][0]

    def add_alternative(self, relationship):
        candidate = self.raw["candidates"][0]
        candidate["alternative_relationship"] = relationship
        candidate["identified_alternative_ids"].append("a2")
        candidate["alternatives"][0]["assumptions"] = ["Synthetic assumption A"]
        alternative = copy.deepcopy(candidate["alternatives"][0])
        alternative["alternative_id"] = "a2"
        alternative["assumptions"] = ["Synthetic assumption B"]
        candidate["alternatives"].append(alternative)

    def document_binding(self):
        return {"kind": "linked_document", "view_sha256": self.packet["environment_sha256"], "value_type": "Text",
                "pointer": "/linked_documents/0", "document_id": "doc/a~b", "link_origin": "/rows/0/cells/0/linked_document_ids",
                "requested_attribute": "name", "entity_association": "follow the entity link"}

    def set_modality(self, index, modality):
        self.packet["candidates"][0]["binding_slots"][index]["environment_modality"] = modality
        rehash(self.packet)
        self.raw = response_fixture(self.packet)

    def test_synthetic_static_bindings_pass(self):
        result = self.check()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["candidates"][0]["summary"]["status"], "resolved")

    def test_synthetic_document_locator_and_link_membership(self):
        self.set_modality(0, "linked_document_text")
        binding = self.document_binding()
        self.alternative()["slots"][0]["bindings"] = [binding]
        self.assertEqual(self.check()["errors"], [])
        binding["link_origin"] = "/columns/0/linked_document_ids"
        self.assertIn("wrong document link membership", str(self.check()["errors"]))

    def test_dynamic_rule_preserves_upstream_reference_without_evaluation(self):
        self.set_modality(1, "linked_document_text")
        binding = {"kind": "dynamic", "view_sha256": self.packet["environment_sha256"], "value_type": "Text",
                   "scope": "/linked_documents", "link_scope": "/rows", "upstream_node_ids": ["op1"],
                   "question_spans": [], "selector": "follow matching row entity links", "requested_attribute": "name",
                   "entity_association": "entity produced by op1"}
        self.alternative()["slots"][1]["bindings"] = [binding]
        self.assertEqual(self.check()["errors"], [])
        binding["upstream_node_ids"] = ["op2"]
        self.assertIn("non-upstream", str(self.check()["errors"]))

    def test_dynamic_document_placeholder_and_missing_scope_rejected(self):
        self.set_modality(1, "linked_document_text")
        binding = {"kind": "dynamic", "view_sha256": self.packet["environment_sha256"], "value_type": "Text",
                   "scope": "/linked_documents", "link_scope": None, "upstream_node_ids": ["op1"],
                   "question_spans": [], "selector": "follow row links", "requested_attribute": None,
                   "entity_association": "entity"}
        self.alternative()["slots"][1]["bindings"] = [binding]
        self.assertTrue(self.check()["errors"])
        binding["link_scope"] = "/rows"
        self.assertIn("requested attribute", str(self.check()["errors"]))

    def test_question_literal_codepoint_spans(self):
        self.set_modality(0, "question_literal")
        binding = {"kind": "question_literal", "view_sha256": self.packet["environment_sha256"], "value_type": "Text",
                   "start": 8, "end": 12, "literal": "2001"}
        self.alternative()["slots"][0]["bindings"] = [binding]
        self.assertEqual(self.check()["errors"], [])
        binding["literal"] = "2002"
        self.assertIn("literal span mismatch", str(self.check()["errors"]))
        self.assertEqual(r.pointer({"a/b": {"~": 1}}, "/a~1b/~0"), 1)

    def test_missing_duplicate_and_extra_slots_fail(self):
        for mutation in (lambda a: a["slots"].pop(), lambda a: a["slots"].append(copy.deepcopy(a["slots"][0])),
                         lambda a: a["slots"][0].update(slot_id="slot99")):
            raw = copy.deepcopy(self.raw)
            mutation(raw["candidates"][0]["alternatives"][0])
            self.assertTrue(self.check(raw)["errors"])

    def test_missing_candidate_and_operator_fail(self):
        raw = copy.deepcopy(self.raw)
        raw["candidates"] = []
        self.assertTrue(self.check(raw)["errors"])
        self.alternative()["operators"].pop()
        self.assertTrue(self.check()["errors"])

    def test_graph_hash_and_cycles_rejected(self):
        self.packet["candidates"][0]["graph"]["nodes"][0]["operation_description"] = "changed"
        with self.assertRaisesRegex(ValueError, "payload hash"):
            self.check()
        self.packet = packet_fixture()
        self.packet["candidates"][0]["graph"]["nodes"][0]["depends_on"] = ["op2"]
        rehash(self.packet)
        with self.assertRaisesRegex(ValueError, "cyclic"):
            self.check()

    def test_invalid_pointer_column_label_and_view_hash_fail(self):
        for key, value in (("pointer", "/columns/99"), ("column_label", "Wrong"), ("view_sha256", "f"*64)):
            raw = copy.deepcopy(self.raw)
            raw["candidates"][0]["alternatives"][0]["slots"][0]["bindings"][0][key] = value
            self.assertTrue(self.check(raw)["errors"])
        for path in ("/rows/01", "/rows/-1", "/rows/~2", "/absent", "/rows/99"):
            with self.assertRaises(ValueError):
                r.pointer(self.packet["environment"], path)

    def test_incompatible_alternatives_never_pass(self):
        self.add_alternative("incompatible")
        result = self.check()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["candidates"][0]["summary"]["status"], "ambiguous")
        self.assertEqual(set(result["candidates"][0]["summary"]["slot_statuses"].values()), {"ambiguous"})

    def test_compatible_alternatives_retained_and_missing_inventory_fails(self):
        self.add_alternative("compatible")
        result = self.check()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["candidates"][0]["summary"]["retained_alternatives"], 2)
        self.raw["candidates"][0]["alternatives"].pop()
        self.assertTrue(self.check()["errors"])

    def test_explicit_abstention_and_partial_coverage(self):
        slot = self.alternative()["slots"][0]
        slot.update(status="abstained", bindings=[], reason="Cannot justify this binding")
        result = self.check()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["candidates"][0]["summary"]["status"], "partial")

    def test_unavailable_requires_search_scope(self):
        slot = self.alternative()["slots"][0]
        slot.update(status="unavailable", bindings=[], reason="Absent in allowed source")
        self.assertTrue(self.check()["errors"])
        slot["searched_scope"] = ["/columns"]
        self.assertEqual(self.check()["errors"], [])

    def test_incomplete_delivery_cannot_claim_resolution(self):
        self.raw["input_delivery"] = {"status": "incomplete", "reason": "Packet truncated"}
        self.assertTrue(self.check()["errors"])
        for slot in self.alternative()["slots"]:
            slot.update(status="abstained", reason="Packet truncated", bindings=[])
        for operator in self.alternative()["operators"]:
            operator.update(status="abstained", reason="Packet truncated", no_additional_arguments=False, parameters=[])
        self.assertEqual(self.check()["errors"], [])

    def test_answer_and_arbitrary_fields_rejected(self):
        for value in ("answer", "execution_result", "gold_span"):
            raw = copy.deepcopy(self.raw)
            raw[value] = "forbidden"
            self.assertEqual(self.check(raw)["schema"], "fail")

    def test_missing_malformed_and_duplicate_key_responses_distinct(self):
        self.assertEqual(r.validate_response(None, self.packet)["delivery"], "missing")
        for data in (b"{", b'{"x":1,"x":2}', b'{"x":NaN}'):
            result = r.validate_response(data, self.packet)
            self.assertEqual(result["parse"], "fail")
            self.assertEqual(result["raw_sha256"], r.sha(data))

    def test_cardinality_modality_and_type_mismatches_rejected(self):
        for key, value in (("cardinality", "multiple"), ("expected_type", "Number")):
            raw = copy.deepcopy(self.raw)
            raw["candidates"][0]["alternatives"][0]["slots"][0][key] = value
            self.assertTrue(self.check(raw)["errors"])

    def test_symbolic_derived_parameters_reject_downstream_or_unrelated_slot(self):
        operator = self.alternative()["operators"][1]
        binding = {"kind": "derived", "view_sha256": self.packet["environment_sha256"], "value_type": "Text",
                   "function": "identity", "operands": [{"kind": "node", "id": "op1"}], "units": "not_applicable",
                   "tie_policy": "preserve_all", "null_policy": "abstain"}
        operator.update(no_additional_arguments=False, reason=None, parameters=[{"name": "input", "binding": binding}])
        self.assertEqual(self.check()["errors"], [])
        binding["operands"] *= 2
        self.assertEqual(self.check()["errors"], [])
        for operand in ({"kind": "node", "id": "op2"}, {"kind": "slot", "id": "slot1"}):
            binding["operands"] = [operand]
            self.assertTrue(self.check()["errors"])

    def test_provenance_missing_revision_and_post_output_retry_rejected(self):
        self.raw["provenance"]["revision_status"] = "exposed"
        self.assertTrue(self.check()["errors"])
        self.raw["provenance"]["revision_status"] = "revision_not_exposed"
        self.raw["provenance"]["attempts"] *= 2
        self.assertTrue(self.check()["errors"])

    def test_live_packet_projection_only_in_memory_preserves_all_sources(self):
        packets, routes = r.build_packets()
        self.assertEqual(len(packets), 6)
        self.assertEqual(sum(len(p["candidates"]) for p in packets), 14)
        self.assertEqual(sum(len(c["binding_slots"]) for p in packets for c in p["candidates"]), 52)
        def keys(value):
            if isinstance(value, dict):
                return set(value) | set().union(*(keys(v) for v in value.values()))
            if isinstance(value, list):
                return set().union(*(keys(v) for v in value))
            return set()
        forbidden = {"producer_partition", "family_id", "contracted_signature_sha256", "source_record_sha256",
                     "backbone_assessment_binding", "equivalence_eligibility", "answer-text", "answer-node"}
        for packet in packets:
            self.assertFalse(keys(packet) & forbidden)
            r.verify_packet(packet)
        self.assertEqual(len(routes[0]), 4)

    def test_synthetic_full_analysis_fixed_denominators_and_branches(self):
        counts = ((4,4,4,4), (4,4), (4,4), (4,4), (3,3), (3,3))
        packets = [packet_fixture(i, c) for i, c in enumerate(counts, 1)]
        routes = [[{"observation_alias": c["observation_alias"], "selection": {
            "observation_id": f'{p["question_id"]}:{j}', "question_id": p["question_id"],
            "producer_partition": f"synthetic_producer_{j%2}", "target_backbone_variant_id": "primary"}}
            for j, c in enumerate(p["candidates"])] for p in packets]
        raw = {i: json.dumps(response_fixture(p)).encode() for i, p in enumerate(packets, 1)}
        records, _, _, metrics = r.analyze(packets, routes, raw, {})
        self.assertEqual(len(records), 14)
        self.assertEqual(metrics["source_slot_status_counts"], {"resolved": 52})
        self.assertEqual(metrics["decision"], "FREEZE_GROUNDING_EVIDENCE_FOR_SEPARATE_EXECUTION_PLAN")
        for bad_packets, bad_routes in ((packets[:-1], routes), (packets, routes[:-1]),
                                       (packets, [routes[0][:-1]] + routes[1:])):
            with self.assertRaises(ValueError):
                r.analyze(bad_packets, bad_routes, raw, {})
        with self.assertRaises(ValueError):
            r.analyze(packets, routes, {**raw, 7: b"{}"}, {})
        partial = response_fixture(packets[0])
        partial["candidates"][0]["alternatives"][0]["slots"][0].update(
            status="abstained", bindings=[], reason="Cannot justify this binding")
        raw[1] = json.dumps(partial).encode()
        self.assertEqual(r.analyze(packets, routes, raw, {})[3]["decision"], "REVIEW_AMBIGUITY_OR_COVERAGE_BEFORE_EXECUTION_PLAN")
        incomplete = response_fixture(packets[0])
        incomplete["input_delivery"] = {"status": "incomplete", "reason": "Packet truncated"}
        for candidate in incomplete["candidates"]:
            for alternative in candidate["alternatives"]:
                for slot in alternative["slots"]:
                    slot.update(status="abstained", reason="Packet truncated", bindings=[])
                for operator in alternative["operators"]:
                    operator.update(status="abstained", reason="Packet truncated", no_additional_arguments=False, parameters=[])
        raw[1] = json.dumps(incomplete).encode()
        metrics = r.analyze(packets, routes, raw, {})[3]
        self.assertEqual(metrics["decision"], "BLOCKED_PINNED_ENVIRONMENT_UNAVAILABLE")
        self.assertEqual(metrics["source_unavailable"], 1)
        raw.pop(1)
        self.assertEqual(r.analyze(packets, routes, raw, {})[3]["decision"], "INCOMPLETE_GROUNDING_COLLECTION")
        raw[1] = b"invalid"
        self.assertEqual(r.analyze(packets, routes, raw, {})[3]["decision"], "STOP_TECHNICAL_OR_LEAKAGE_FAILURE")

    def test_write_once_refuses_collision_before_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = r.freeze.planned_outputs()
            existing = root / paths["checks"]
            existing.parent.mkdir(parents=True)
            existing.write_text("original")
            with self.assertRaises(ValueError):
                r.write_once(root, {"records": b"new", "checks": b"changed"})
            self.assertFalse((root / paths["records"]).exists())
            self.assertEqual(existing.read_text(), "original")

    def test_runtime_receipt_commit_ancestry_absence_and_immutability(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True).stdout.decode().strip()
            git("init", "-q")
            git("config", "user.email", "synthetic@example.invalid")
            git("config", "user.name", "Synthetic")
            plan_path = root / r.freeze.PLAN
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text("{}")
            (root / "runtime.txt").write_text("runtime")
            git("add", ".")
            git("commit", "-qm", "plan and implementation fixture")
            baseline = git("rev-parse", "HEAD")
            evidence = {"tests_run": 1, "failures": 0, "errors": 0, "skipped": 0,
                        "command": ".venv/bin/python -B -m unittest discover -s tests -p " + Path(r.TEST).name + " -v",
                        "output_sha256": "0"*64}
            with patch.object(r.freeze, "validate_plan", return_value={"freeze_commit": baseline}), \
                 patch.object(r, "exact_pins"), patch.object(r, "RUNTIME_INPUTS", ("runtime.txt",)):
                receipt = r.implementation_receipt(root, baseline, evidence)
                receipt_path = root / r.RECEIPT
                receipt_path.write_bytes(r.json_file_bytes(receipt))
                with self.assertRaises(ValueError):
                    r.validate_runtime(root)
                git("add", r.RECEIPT)
                git("commit", "-qm", "runtime receipt fixture")
                self.assertEqual(r.validate_runtime(root, True)["status"], "pass")
                (root / "runtime.txt").write_text("changed")
                with self.assertRaises(ValueError):
                    r.validate_runtime(root)
                (root / "runtime.txt").write_text("runtime")
                output = root / r.freeze.planned_outputs()["raw_01"]
                output.parent.mkdir(parents=True)
                output.write_text("{}")
                with self.assertRaises(ValueError):
                    r.validate_runtime(root, True)
                self.assertEqual(r.validate_runtime(root)["status"], "pass")

    def test_missing_pinned_source_has_separate_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(r.SourceUnavailable):
                r.pinned_views(Path(directory))

    def test_packet_then_raw_commit_order_and_immutable_first_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True).stdout.decode().strip()
            git("init", "-q")
            git("config", "user.email", "synthetic@example.invalid")
            git("config", "user.name", "Synthetic")
            receipt = root / r.RECEIPT
            receipt.parent.mkdir(parents=True)
            receipt.write_text("synthetic runtime fixture")
            git("add", ".")
            git("commit", "-qm", "runtime fixture")
            payloads = {label: b"synthetic packet fixture" for label in r.PACKET_LABELS}
            r.write_once(root, payloads)
            with self.assertRaises(ValueError):
                r.verify_packets_committed(root, payloads)
            git("add", ".")
            git("commit", "-qm", "packets fixture")
            packet_commit = r.verify_packets_committed(root, payloads)
            raw_path = r.freeze.planned_outputs()["raw_01"]
            raw = root / raw_path
            raw.parent.mkdir()
            raw.write_bytes(b"first capture")
            with self.assertRaises(ValueError):
                r.verify_raw_committed(root, raw_path, raw.read_bytes(), packet_commit)
            git("add", ".")
            git("commit", "-qm", "raw fixture")
            raw_commit = r.verify_raw_committed(root, raw_path, raw.read_bytes(), packet_commit)
            self.assertEqual(raw_commit, git("rev-parse", "HEAD"))
            with self.assertRaises(ValueError):
                r.verify_raw_committed(root, raw_path, raw.read_bytes(), raw_commit)
            raw.write_bytes(b"semantic repair must not replace raw")
            git("add", ".")
            git("commit", "-qm", "invalid repair fixture")
            with self.assertRaisesRegex(ValueError, "first capture"):
                r.verify_raw_committed(root, raw_path, raw.read_bytes(), packet_commit)

    def test_unplanned_namespace_files_and_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            namespace = root / r.freeze.BASE / "narrowed_grounding_v0_1"
            namespace.mkdir(parents=True)
            extra = namespace / "extra.json"
            extra.write_text("{}")
            with self.assertRaisesRegex(ValueError, "unplanned"):
                r.validate_namespace(root)
            extra.unlink()
            link = root / r.freeze.planned_outputs()["raw_01"]
            link.parent.mkdir()
            link.symlink_to(root / "absent")
            with self.assertRaisesRegex(ValueError, "symlink"):
                r.validate_namespace(root)


if __name__ == "__main__":
    unittest.main()
