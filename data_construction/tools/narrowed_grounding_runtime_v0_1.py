#!/usr/bin/env python3
"""Static grounding contracts and deterministic artifacts; no graph execution."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import subprocess
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from _common import (canonical_json_sha256 as digest, iter_json_records, json_file_bytes,
                     jsonl_file_bytes, read_json, strict_json_loads, write_output_batch)
import freeze_narrowed_grounding_plan_v0_1 as freeze

ROOT = freeze.ROOT
CONTRACTS = freeze.BASE + "/contracts/"
PACKET_SCHEMA = CONTRACTS + "narrowed_grounding_packet_schema_v0_1.json"
RAW_SCHEMA = CONTRACTS + "narrowed_grounding_raw_schema_v0_1.json"
RECEIPT = CONTRACTS + "narrowed_grounding_runtime_freeze_v0_1.json"
GUIDE = freeze.BASE + "/prompts/narrowed_grounding_author_guide_v0_1.md"
TOOL = "data_construction/tools/narrowed_grounding_runtime_v0_1.py"
TEST = "tests/test_narrowed_grounding_runtime_v0_1.py"
ENV_SCHEMA = CONTRACTS + "representative_environment_view_schema_v0_1.json"
OP_SCHEMA = CONTRACTS + "open_operator_realization_schema_v0_1.json"
VIEWS = freeze.BASE + "/representative_environment_realization_v0_1/inputs/environment_views.jsonl"
RUNTIME_INPUTS = (TOOL, TEST, GUIDE, PACKET_SCHEMA, RAW_SCHEMA, ENV_SCHEMA, OP_SCHEMA,
                  freeze.TOOL, "data_construction/tools/_common.py", "requirements.txt", ".python-version")
PACKET_LABELS = tuple(f"packet_{i:02}" for i in range(1, 7)) + ("packet_manifest",)
RAW_LABELS = tuple(f"raw_{i:02}" for i in range(1, 7))
RESULT_LABELS = ("records", "checks", "comparisons", "metrics", "report", "exposure", "run_manifest")
EVIDENCE = {"evidence_class": "ai_exploratory_non_human_non_gold", "human_evidence_count": 0,
            "gold_claimed": False, "execution_evaluated": False, "answer_recovery_evaluated": False,
            "static_validity_is_semantic_correctness": False, "cognitive_independence_authenticated": False}


class SourceUnavailable(ValueError):
    """Missing pinned source is not evidence of semantic grounding failure."""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact_pins(root=ROOT):
    for line in (root / "requirements.txt").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            package, pin = line.split("==")
            require(version(package) == pin, "dependency pin mismatch: " + package)


@lru_cache(maxsize=8)
def validator(schema_path: str):
    schemas = [read_json(ROOT / p) for p in (PACKET_SCHEMA, RAW_SCHEMA, ENV_SCHEMA, OP_SCHEMA)]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
    return Draft202012Validator(read_json(ROOT / schema_path), registry=registry)


def schema_errors(schema_path, value):
    return ["schema/" + "/".join(map(str, e.absolute_path)) + ": " + e.message
            for e in validator(schema_path).iter_errors(value)]


def pointer(value, path):
    """RFC 6901 resolution only. Reject noncanonical indexes and malformed escapes."""
    require(isinstance(path, str) and (path == "" or path.startswith("/")), "invalid JSON pointer")
    for encoded in path.split("/")[1:] if path else []:
        require(not re.search(r"~(?![01])", encoded), "invalid pointer escape")
        key = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            require(re.fullmatch(r"0|[1-9][0-9]*", key) is not None, "invalid array index")
            require(int(key) < len(value), "pointer array index absent")
            value = value[int(key)]
        else:
            require(isinstance(value, dict) and key in value, "pointer member absent")
            value = value[key]
    return value


def ancestors(graph):
    nodes = {n["node_id"]: n for n in graph["nodes"]}
    require(len(nodes) == len(graph["nodes"]), "duplicate operator node")
    cache, visiting = {}, set()
    def visit(node):
        require(node in nodes and node not in visiting, "unknown or cyclic operator dependency")
        if node not in cache:
            visiting.add(node)
            found = set()
            for upstream in nodes[node]["depends_on"]:
                found.add(upstream)
                found.update(visit(upstream))
            cache[node] = found
            visiting.remove(node)
        return cache[node]
    for node in nodes:
        visit(node)
    return cache


def packet_projection(view, selected, source_records, index, guide_hash, schema_hash):
    """Explicit allowlist; no assessment, author, signature or normalization fields."""
    require(view["question_id"] == selected[0]["question_id"], "view/question mismatch")
    payload = view["payload"]
    require(digest(payload) == view["payload_sha256"], "source environment payload changed")
    env = payload["environment"]
    require(env["scope_contract"]["truncation"] == "none" and
            env["scope_contract"]["full_table_link_closure_supplied"] is True, "source view incomplete")
    context = payload["candidate_backbone_context"]
    graphs = {"primary": context["primary_graph"]}
    graphs.update({a["alternative_id"]: a["graph"] for a in context["alternative_graphs"]})
    candidates, routing = [], []
    for position, entry in enumerate(selected, 1):
        require(entry["environment_payload_sha256"] == view["payload_sha256"], "candidate/view binding mismatch")
        record = source_records[entry["question_id"], entry["producer_partition"]]
        require(digest(record) == entry["source_record_sha256"], "source record changed")
        matches = [c for c in record["realization_candidates"] if c["candidate_id"] == entry["candidate_id"]]
        require(len(matches) == 1 and digest(matches[0]) == entry["source_candidate_sha256"], "source candidate changed")
        candidate = matches[0]
        alias = f"observation_{position:02}"
        projection = {key: candidate[key] for key in ("target_backbone_variant_id", "graph",
                      "binding_slots", "backbone_operator_mappings", "distinguishing_assumptions")}
        projection["observation_alias"] = alias
        projection["candidate_sha256"] = digest(projection)
        candidates.append(projection)
        routing.append({"observation_alias": alias, "selection": entry,
                        "packet_candidate_sha256": projection["candidate_sha256"]})
    variants = list(dict.fromkeys(c["target_backbone_variant_id"] for c in candidates))
    require(set(variants) <= set(graphs), "candidate target variant absent")
    packet = {"schema_version": "narrowed_grounding_packet_v0_1", "packet_id": f"ng_v0_1_question_{index:02}",
              "question_id": view["question_id"], "question": payload["question_context"]["question"],
              "environment": env, "environment_sha256": digest(env),
              "backbones": [{"variant_id": v, "graph": graphs[v]} for v in variants],
              "candidates": candidates, "protocol_sha256": guide_hash, "response_schema_sha256": schema_hash}
    packet["payload_sha256"] = digest(packet)
    require(not schema_errors(PACKET_SCHEMA, packet), "packet schema failed")
    return packet, routing


def verify_packet(packet):
    require(not schema_errors(PACKET_SCHEMA, packet), "packet schema failed")
    require(packet["payload_sha256"] == digest({k: v for k, v in packet.items() if k != "payload_sha256"}),
            "packet payload hash mismatch")
    require(packet["environment_sha256"] == digest(packet["environment"]), "packet environment changed")
    require(len({c["observation_alias"] for c in packet["candidates"]}) == len(packet["candidates"]),
            "duplicate packet observation")
    env = packet["environment"]
    require(env["scope_contract"]["full_table_link_closure_supplied"] and
            env["scope_contract"]["truncation"] == "none", "incomplete environment")
    links = {d for c in env["columns"] for d in c["linked_document_ids"]}
    links.update(d for row in env["rows"] for cell in row["cells"] for d in cell["linked_document_ids"])
    docs = [d["document_id"] for d in env["linked_documents"]]
    require(len(docs) == len(set(docs)) and set(docs) == links, "document closure mismatch")
    for candidate in packet["candidates"]:
        require(candidate["candidate_sha256"] == digest({k: v for k, v in candidate.items() if k != "candidate_sha256"}),
                "packet candidate graph or slots changed")
        ancestors(candidate["graph"])


def span(question, binding):
    require(0 <= binding["start"] < binding["end"] <= len(question), "literal span out of bounds")
    require(question[binding["start"]:binding["end"]] == binding["literal"], "question literal span mismatch")


def link_collection(env, path):
    require(re.fullmatch(r"/(?:columns/[0-9]+|rows/[0-9]+/cells/[0-9]+)/linked_document_ids", path),
            "not a header/cell link collection")
    links = pointer(env, path)
    require(isinstance(links, list) and all(isinstance(x, str) for x in links), "link collection type mismatch")
    return links


def check_binding(binding, packet, candidate, consumer_ids, expected_type=None, modality=None):
    env = packet["environment"]
    require(binding["view_sha256"] == packet["environment_sha256"], "locator view hash mismatch")
    if expected_type is not None:
        require(binding["value_type"] == expected_type, "declared binding type mismatch")
    upstream = ancestors(candidate["graph"])
    nodes = {n["node_id"]: n for n in candidate["graph"]["nodes"]}
    def check_upstream(ids):
        require(len(ids) == len(set(ids)), "duplicate upstream reference")
        require(all(ref in upstream[consumer] for ref in ids for consumer in consumer_ids),
                "locator references non-upstream node")
    kind = binding["kind"]
    allowed = {
        "question_literal": {"question_literal"}, "table_metadata": {"table_scope"},
        "table_header": {"table_column", "table_scope"},
        "table_row_or_cell": {"table_column", "table_scope", "dynamic"},
        "cell_link": {"cell_link", "dynamic"}, "linked_document_text": {"linked_document", "dynamic"},
        "unknown": set(),
    }
    if modality:
        require(kind in allowed[modality], "binding kind incompatible with source modality")
    if kind == "table_column":
        require(binding["table_id"] == env["table_id"], "table identity mismatch")
        require(binding["pointer"] == f'/columns/{binding["column_index"]}', "column index/pointer mismatch")
        column = pointer(env, binding["pointer"])
        require(column["column_index"] == binding["column_index"] and column["text"] == binding["column_label"],
                "column label/index mismatch")
    elif kind == "table_scope":
        require(binding["table_id"] == env["table_id"], "table identity mismatch")
        require(binding["pointer"] in ("", "/columns", "/rows", "/title", "/section_title"),
                "table scope must not materialize filtered rows")
        pointer(env, binding["pointer"])
    elif kind == "cell_link":
        require(bool(link_collection(env, binding["pointer"])), "empty source link collection")
    elif kind == "linked_document":
        require(re.fullmatch(r"/linked_documents/[0-9]+", binding["pointer"]), "not a whole-document locator")
        document = pointer(env, binding["pointer"])
        require(document["document_id"] == binding["document_id"], "document identity mismatch")
        require(binding["document_id"] in link_collection(env, binding["link_origin"]), "wrong document link membership")
    elif kind == "dynamic":
        require(binding["scope"] in ("", "/rows", "/columns", "/linked_documents") or
                re.fullmatch(r"/columns/[0-9]+", binding["scope"]), "dynamic source scope is not a collection/column")
        pointer(env, binding["scope"])
        check_upstream(binding["upstream_node_ids"])
        for literal in binding["question_spans"]:
            span(packet["question"], literal)
        require(binding["upstream_node_ids"] or binding["question_spans"], "dynamic rule lacks an input")
        if modality in ("cell_link", "linked_document_text") or binding["scope"] == "/linked_documents":
            require(binding["link_scope"] is not None, "dynamic document rule lacks link scope")
            require(binding["link_scope"] in ("/rows", "/columns") or
                    re.fullmatch(r"/columns/[0-9]+", binding["link_scope"]), "dynamic link scope is invalid")
            pointer(env, binding["link_scope"])
        if modality == "linked_document_text" or binding["scope"] == "/linked_documents":
            require(binding["requested_attribute"] is not None, "dynamic document rule lacks requested attribute")
    elif kind == "question_literal":
        span(packet["question"], binding)
    elif kind == "source_literal":
        require(modality is None, "source literal is an operator parameter only")
        value = pointer(env, binding["pointer"])
        require(isinstance(value, (str, int, float, bool)), "source literal is not scalar")
    elif kind == "derived":
        require(modality is None, "derived argument is not a source locator")
        # Repeated ordered operands (e.g. x - x) are legitimate symbolic arguments.
        check_upstream(list(dict.fromkeys(v["id"] for v in binding["operands"] if v["kind"] == "node")))
        for operand in binding["operands"]:
            if operand["kind"] == "slot":
                require(all(operand["id"] in nodes[c]["input_slot_ids"] for c in consumer_ids),
                        "derived argument references unrelated slot")
    else:
        raise ValueError("unknown binding kind")


def exact_ids(items, key, expected, label):
    ids = [x[key] for x in items]
    require(len(ids) == len(set(ids)) and set(ids) == set(expected), label + " missing/duplicate/extra identity")


def disposition(statuses, incompatible=False):
    if incompatible:
        return "ambiguous" if set(statuses) <= {"resolved", "specified", "ambiguous"} else "partial"
    if set(statuses) <= {"resolved", "specified"}:
        return "resolved"
    if len(set(statuses)) == 1 and statuses[0] in ("unavailable", "abstained", "ambiguous"):
        return statuses[0]
    return "partial"


def validate_candidate(raw, source, packet, incomplete=False):
    require(raw["candidate_sha256"] == source["candidate_sha256"], "source candidate hash changed")
    alternatives = raw["alternatives"]
    exact_ids(alternatives, "alternative_id", raw["identified_alternative_ids"], "identified alternatives")
    relation = raw["alternative_relationship"]
    require((relation == "single") == (len(alternatives) == 1), "alternative relationship/count contradiction")
    expected_slots = {s["slot_id"]: s for s in source["binding_slots"]}
    expected_nodes = {n["node_id"]: n for n in source["graph"]["nodes"]}
    slot_statuses, operator_statuses = defaultdict(list), defaultdict(list)
    counts = Counter()
    reasons = []
    for alternative in alternatives:
        require(relation == "single" or alternative["assumptions"], "multiple alternatives need assumptions")
        exact_ids(alternative["slots"], "slot_id", expected_slots, "slots")
        exact_ids(alternative["operators"], "node_id", expected_nodes, "operators")
        for slot in alternative["slots"]:
            source_slot = expected_slots[slot["slot_id"]]
            require(slot["cardinality"] == source_slot["cardinality"], "source cardinality changed")
            status = slot["status"]
            require(not incomplete or status == "abstained", "incomplete delivery cannot claim binding coverage")
            require((status == "resolved") == (slot["reason"] is None), "slot reason/status contradiction")
            require(status not in ("resolved", "ambiguous") or slot["bindings"], "slot lacks locator")
            require(status != "ambiguous" or relation == "incompatible", "ambiguous binding needs incompatible alternatives")
            require(status != "unavailable" or slot["searched_scope"], "unavailable slot needs searched scope")
            require(status not in ("abstained", "unavailable") or not slot["bindings"], "unresolved slot claims a binding")
            consumers = [n["node_id"] for n in expected_nodes.values() if slot["slot_id"] in n["input_slot_ids"]]
            require(consumers, "source slot has no consumer")
            for binding in slot["bindings"]:
                check_binding(binding, packet, source, consumers, slot["expected_type"], source_slot["environment_modality"])
                counts[binding["kind"]] += 1
            for scope in slot["searched_scope"]:
                pointer(packet["environment"], scope)
            slot_statuses[slot["slot_id"]].append(status)
            if slot["reason"]:
                reasons.append({"kind": "slot", "id": slot["slot_id"], "status": status,
                                "alternative_id": alternative["alternative_id"], "reason": slot["reason"]})
        for operator in alternative["operators"]:
            status = operator["status"]
            require(not incomplete or status == "abstained", "incomplete delivery cannot specify operators")
            require(status != "specified" or operator["parameters"] or operator["no_additional_arguments"],
                    "specified operator lacks arguments")
            require(not operator["no_additional_arguments"] or
                    (status == "specified" and not operator["parameters"] and operator["reason"] is not None),
                    "no-additional-arguments declaration inconsistent")
            require(status == "specified" or (operator["reason"] is not None and not operator["no_additional_arguments"]),
                    "unresolved operator lacks reason")
            require(status not in ("abstained", "unavailable") or not operator["parameters"], "unresolved operator claims arguments")
            require(status != "ambiguous" or relation == "incompatible", "ambiguous operator needs incompatible alternatives")
            names = [p["name"] for p in operator["parameters"]]
            require(len(names) == len(set(names)), "duplicate operator parameter")
            for parameter in operator["parameters"]:
                check_binding(parameter["binding"], packet, source, [operator["node_id"]])
                counts[parameter["binding"]["kind"]] += 1
            operator_statuses[operator["node_id"]].append(status)
            if status != "specified":
                reasons.append({"kind": "operator", "id": operator["node_id"], "status": status,
                                "alternative_id": alternative["alternative_id"], "reason": operator["reason"]})
    incompatible = relation == "incompatible"
    all_statuses = [s for values in (*slot_statuses.values(), *operator_statuses.values()) for s in values]
    return {"status": disposition(all_statuses, incompatible),
            "slot_statuses": {key: disposition(value, incompatible) for key, value in slot_statuses.items()},
            "operator_statuses": {key: disposition(value, incompatible) for key, value in operator_statuses.items()},
            "alternative_qualified_slot_counts": dict(Counter(s for values in slot_statuses.values() for s in values)),
            "alternative_qualified_operator_counts": dict(Counter(s for values in operator_statuses.values() for s in values)),
            "binding_kind_counts": dict(counts), "identified_alternatives": len(alternatives),
            "retained_alternatives": len(alternatives), "lost_alternatives": 0, "reasons": reasons}


def validate_response(data: bytes | None, packet):
    """Return parse/schema/check signals separately; never repair invalid raw bytes."""
    verify_packet(packet)
    if data is None:
        return {"delivery": "missing", "parse": "not_run", "schema": "not_run", "errors": [], "candidates": []}
    result = {"delivery": "received", "raw_sha256": sha(data), "raw_bytes": len(data),
              "parse": "fail", "schema": "not_run", "errors": [], "candidates": []}
    try:
        raw = strict_json_loads(data.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        result["errors"] = ["raw_parse: " + str(exc)]
        return result
    result["parse"] = "pass"
    errors = schema_errors(RAW_SCHEMA, raw)
    result["schema"] = "fail" if errors else "pass"
    result["parsed_sha256"] = digest(raw)
    result["raw_parsed"] = raw
    if errors:
        result["errors"] = errors
        return result
    try:
        for key, expected in (("packet_id", packet["packet_id"]), ("packet_sha256", packet["payload_sha256"]),
                              ("question_id", packet["question_id"]), ("environment_sha256", packet["environment_sha256"])):
            require(raw[key] == expected, "response binding mismatch: " + key)
        p = raw["provenance"]
        require((p["revision_status"] == "revision_not_exposed") == (p["model_revision"] is None), "revision provenance contradiction")
        require((p["seed_status"] == "not_supported") == (p["seed"] is None), "seed provenance contradiction")
        require(p["prior_exposure"] == "procedurally_attested_none", "grounding context prior exposure not cleared")
        attempts = p["attempts"]
        require(all(a["packet_sha256"] == packet["payload_sha256"] for a in attempts), "transport changed packet")
        require([a["delivery"] for a in attempts] == ["no_output_transport_failure"] * (len(attempts)-1) + ["response_delivered"],
                "multiple submissions or post-output retry")
        incomplete = raw["input_delivery"]["status"] == "incomplete"
        require(incomplete == (raw["input_delivery"]["reason"] is not None), "input delivery reason contradiction")
        sources = {c["observation_alias"]: c for c in packet["candidates"]}
        exact_ids(raw["candidates"], "observation_alias", sources, "candidate observations")
        for candidate in raw["candidates"]:
            summary = validate_candidate(candidate, sources[candidate["observation_alias"]], packet, incomplete)
            result["candidates"].append({"observation_alias": candidate["observation_alias"],
                                         "annotation": candidate, "summary": summary})
        result["provenance"] = p
        result["input_delivery"] = raw["input_delivery"]
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        result["errors"] = [str(exc)]
        result["candidates"] = []  # no partial promotion from a technically invalid submission
    return result


def implementation_receipt(root, implementation_commit, tests):
    plan_check = freeze.validate_plan(root)
    return {"schema_version": "narrowed_grounding_runtime_freeze_v0_1", "status": "frozen_before_all_outputs",
            "plan_sha256": sha((root / freeze.PLAN).read_bytes()), "plan_freeze_commit": plan_check["freeze_commit"],
            "implementation_commit": implementation_commit,
            "runtime_artifacts": freeze.bindings(root, implementation_commit, RUNTIME_INPUTS),
            "test_evidence": tests, "planned_outputs": freeze.planned_outputs(),
            "output_absence_proof": "entire_namespace_empty_at_receipt_introduction_commit",
            "execution_authorized": False, "answer_recovery_authorized": False}


def runtime_tests(root=ROOT):
    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", Path(TEST).name, "-v"]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    output = result.stdout + result.stderr
    match = re.search(r"Ran (\d+) tests?", output)
    require(result.returncode == 0 and match and "skipped=" not in output, "runtime tests failed: " + output[-3000:])
    return {"command": ".venv/bin/python -B -m unittest discover -s tests -p " + Path(TEST).name + " -v",
            "tests_run": int(match.group(1)), "failures": 0, "errors": 0, "skipped": 0,
            "output_sha256": sha(output.encode())}


def validate_runtime(root=ROOT, require_absence=False):
    exact_pins(root)
    receipt = read_json(freeze.safe_path(root, RECEIPT))
    expected = implementation_receipt(root, receipt["implementation_commit"], receipt["test_evidence"])
    require(receipt == expected and (root / RECEIPT).read_bytes() == json_file_bytes(expected), "runtime receipt changed")
    evidence = receipt["test_evidence"]
    require(evidence["tests_run"] > 0 and all(evidence[k] == 0 for k in ("failures", "errors", "skipped")), "runtime tests did not pass")
    require(evidence["command"] == ".venv/bin/python -B -m unittest discover -s tests -p " + Path(TEST).name + " -v"
            and re.fullmatch(r"[0-9a-f]{64}", evidence["output_sha256"]), "invalid runtime test evidence")
    commits = freeze.git(root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--", RECEIPT).decode().splitlines()
    require(len(commits) == 1, "runtime receipt must have one committed introduction")
    commit = commits[0]
    require(freeze.git(root, "show", commit + ":" + RECEIPT) == (root / RECEIPT).read_bytes(), "receipt changed since freeze")
    freeze.git(root, "merge-base", "--is-ancestor", receipt["implementation_commit"], commit + "^")
    freeze.git(root, "merge-base", "--is-ancestor", receipt["plan_freeze_commit"], commit + "^")
    freeze.require_absent(root, commit)
    if require_absence:
        freeze.require_absent(root)
    validator(PACKET_SCHEMA)
    validator(RAW_SCHEMA)
    return {"status": "pass", "runtime_freeze_commit": commit, "implementation_commit": receipt["implementation_commit"],
            "plan_freeze_commit": receipt["plan_freeze_commit"], "runtime_tests": evidence["tests_run"],
            "current_output_absence_checked": require_absence, "grounding_results_validated": False}


def build_packets(root=ROOT):
    """Pure reconstruction; callers gate writes and authoring with committed receipt."""
    plan = read_json(root / freeze.PLAN)
    records = {(r["question_id"], r["producer_partition"]): r
               for r in iter_json_records(root / freeze.INSTRUMENT / "combined_final_records.jsonl")}
    views = pinned_views(root)
    packets, routes = [], []
    for index, qid in enumerate(freeze.IDS, 1):
        selected = [e for e in plan["selection"] if e["question_id"] == qid]
        packet, routing = packet_projection(views[qid], selected, records, index,
                                           sha((root / GUIDE).read_bytes()), sha((root / RAW_SCHEMA).read_bytes()))
        verify_packet(packet)
        packets.append(packet)
        routes.append(routing)
    return packets, routes


def pinned_views(root=ROOT):
    if not (root / VIEWS).is_file():
        raise SourceUnavailable("pinned environment file unavailable; reacquire only the pinned bytes")
    views = {}
    for view in iter_json_records(root / VIEWS):
        qid = view["question_id"]
        if qid in freeze.IDS:
            require(qid not in views, "duplicate pinned selected view")
            views[qid] = view
    if set(views) != set(freeze.IDS):
        raise SourceUnavailable("pinned selected environment unavailable")
    return views


def validate_namespace(root=ROOT):
    paths = set(freeze.planned_outputs().values())
    namespace = freeze.safe_path(root, freeze.RUN)
    if namespace.exists():
        for path in namespace.rglob("*"):
            relative = path.relative_to(root).as_posix()
            require(not path.is_symlink(), "symlink in grounding output namespace")
            require(path.is_dir() or relative in paths, "unplanned grounding output: " + relative)


def packet_artifacts(root=ROOT):
    runtime = validate_runtime(root)
    packets, routes = build_packets(root)
    outputs = freeze.planned_outputs()
    payloads = {f"packet_{i:02}": json_file_bytes(packet) for i, packet in enumerate(packets, 1)}
    manifest = {"schema_version": "narrowed_grounding_packet_manifest_v0_1", "runtime": runtime,
                "runtime_receipt_sha256": sha((root / RECEIPT).read_bytes()),
                "plan_sha256": sha((root / freeze.PLAN).read_bytes()),
                "packets": [{"path": outputs[f"packet_{i:02}"], "sha256": sha(payloads[f"packet_{i:02}"]),
                             "payload_sha256": p["payload_sha256"], "routing": routes[i-1]}
                            for i, p in enumerate(packets, 1)]}
    payloads["packet_manifest"] = json_file_bytes(manifest)
    return payloads, packets, routes


def verify_packets_committed(root, expected):
    paths = freeze.planned_outputs()
    for label, data in expected.items():
        require(freeze.safe_path(root, paths[label]).read_bytes() == data, "packet bytes differ: " + label)
    commits = freeze.git(root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--", paths["packet_manifest"]).decode().splitlines()
    require(len(commits) == 1, "packet manifest not committed exactly once")
    commit = commits[0]
    receipt_commits = freeze.git(root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--", RECEIPT).decode().splitlines()
    freeze.git(root, "merge-base", "--is-ancestor", receipt_commits[0], commit + "^")
    for label, data in expected.items():
        require(freeze.git(root, "show", commit + ":" + paths[label]) == data, "packet not frozen with manifest")
    for label in RAW_LABELS + RESULT_LABELS:
        require(not freeze.git(root, "ls-tree", "-r", "--name-only", commit, "--", paths[label]).strip(),
                "raw or result existed before packet freeze")
    return commit


def verify_raw_committed(root, path, data, packet_commit):
    commits = freeze.git(root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--", path).decode().splitlines()
    require(len(commits) == 1, "raw response must have one committed introduction")
    commit = commits[0]
    freeze.git(root, "merge-base", "--is-ancestor", packet_commit, commit + "^")
    require(freeze.git(root, "show", commit + ":" + path) == data and
            freeze.git(root, "show", "HEAD:" + path) == data, "raw response changed since first capture commit")
    return commit


def analyze(packets, routes, raw_by_index, source_profiles):
    """Pure deterministic analysis; retains invalid parsed payloads in audit checks."""
    require(len(packets) == len(routes) == 6, "analysis requires exactly six question packets and routes")
    require(len({p["question_id"] for p in packets}) == 6, "duplicate analysis question")
    require(sum(len(p["candidates"]) for p in packets) == 14 and
            sum(len(c["binding_slots"]) for p in packets for c in p["candidates"]) == 52,
            "analysis candidate/slot denominator mismatch")
    require(set(raw_by_index) <= set(range(1, 7)), "unexpected raw response index")
    observations, pairs = set(), set()
    for packet, routing in zip(packets, routes):
        exact_ids(routing, "observation_alias", [c["observation_alias"] for c in packet["candidates"]], "routing")
        for route in routing:
            selection = route["selection"]
            require(selection["question_id"] == packet["question_id"], "route question mismatch")
            require(selection["observation_id"] not in observations, "duplicate routed observation")
            observations.add(selection["observation_id"])
            pairs.add((selection["question_id"], selection["producer_partition"]))
    require(len(pairs) == 12, "analysis author-question denominator mismatch")
    records, checks, comparisons = [], [], []
    statuses, slot_counts, node_counts, binding_counts = Counter(), Counter(), Counter(), Counter()
    alt_slot_counts, alt_node_counts = Counter(), Counter()
    contexts = []
    technical = 0
    for index, (packet, routing) in enumerate(zip(packets, routes), 1):
        result = validate_response(raw_by_index.get(index), packet)
        checks.append({"question_id": packet["question_id"], **result})
        technical += len(result["errors"])
        route_map = {r["observation_alias"]: r for r in routing}
        observed = {r["observation_alias"]: r for r in result["candidates"]}
        question_records = []
        if "provenance" in result:
            contexts.append(result["provenance"]["context_id"])
        for source in packet["candidates"]:
            alias = source["observation_alias"]
            route = route_map[alias]["selection"]
            if alias not in observed:
                status = "technical_invalid" if result["errors"] else "not_delivered"
                statuses[status] += 1
                slot_counts[status] += len(source["binding_slots"])
                node_counts[status] += len(source["graph"]["nodes"])
                question_records.append({"observation_id": route["observation_id"], "status": status})
                continue
            observation = observed[alias]
            summary = observation["summary"]
            statuses[summary["status"]] += 1
            slot_counts.update(summary["slot_statuses"].values())
            node_counts.update(summary["operator_statuses"].values())
            binding_counts.update(summary["binding_kind_counts"])
            alt_slot_counts.update(summary["alternative_qualified_slot_counts"])
            alt_node_counts.update(summary["alternative_qualified_operator_counts"])
            record = {"schema_version": "narrowed_grounding_record_v0_1", "question_id": packet["question_id"],
                      "source": route, "packet_sha256": packet["payload_sha256"],
                      "environment_sha256": packet["environment_sha256"], "raw_sha256": result["raw_sha256"],
                      "parsed_response_sha256": result["parsed_sha256"], "provenance": result["provenance"],
                      "annotation": observation["annotation"], "summary": summary, "evidence_boundary": EVIDENCE}
            records.append(record)
            question_records.append({"observation_id": route["observation_id"], "status": summary["status"],
                                     "producer_partition": route["producer_partition"],
                                     "target_variant": route["target_backbone_variant_id"],
                                     "semantic_profile": source_profiles.get(route["observation_id"]),
                                     "binding_inventory": [s["bindings"] for a in observation["annotation"]["alternatives"] for s in a["slots"]]})
        comparisons.append({"question_id": packet["question_id"], "observations": question_records,
                            "all_candidates_resolved": all(r["status"] == "resolved" for r in question_records),
                            "exact_locator_identity_is_correctness": False})
    if len(contexts) != len(set(contexts)):
        technical += 1
        checks.append({"error": "question contexts not distinct", "errors": ["question contexts not distinct"]})
    delivered = sum(len(c["candidates"]) for c in checks if "candidates" in c)
    unresolved = sum(value for key, value in slot_counts.items() if key != "resolved")
    unresolved += sum(value for key, value in node_counts.items() if key != "resolved")
    unavailable = sum(c.get("input_delivery", {}).get("status") == "incomplete" for c in checks)
    branch = freeze.decision(technical, unavailable, delivered, statuses["resolved"], unresolved)
    author_pairs, variants = defaultdict(list), defaultdict(list)
    for packet, route in zip(packets, routes):
        by_id = {r["source"]["observation_id"]: r for r in records}
        for entry in route:
            selection = entry["selection"]
            status = by_id.get(selection["observation_id"], {}).get("summary", {}).get("status", "not_validated")
            author_pairs[selection["question_id"], selection["producer_partition"]].append(status)
            variants[selection["question_id"], selection["target_backbone_variant_id"]].append(status)
    metrics = {"schema_version": "narrowed_grounding_metrics_v0_1", "decision": branch,
               "denominators": {"questions": 6, "author_question_pairs": 12, "candidates": 14, "source_slots": 52},
               "candidate_status_counts": dict(statuses), "source_slot_status_counts": dict(slot_counts),
               "operator_status_counts": dict(node_counts), "binding_kind_counts": dict(binding_counts),
               "alternative_qualified_slot_counts": dict(alt_slot_counts),
               "alternative_qualified_operator_counts": dict(alt_node_counts),
               "technical_errors": technical, "delivered_valid_candidate_records": delivered,
               "question_all_candidate_coverage": sum(c["all_candidates_resolved"] for c in comparisons),
               "author_question_any_complete_candidate_coverage": sum("resolved" in s for s in author_pairs.values()),
               "target_variant_any_complete_candidate_coverage": sum("resolved" in s for s in variants.values()),
               "identified_alternatives": sum(r["summary"]["identified_alternatives"] for r in records),
               "retained_alternatives": sum(r["summary"]["retained_alternatives"] for r in records),
               "alternative_retention_scope": "validated_records_only_invalid_raw_preserved_in_checks",
               "lost_alternatives_in_validated_records": 0, "unresolved_dispositions": unresolved,
               "source_unavailable": unavailable, "evidence_boundary": EVIDENCE}
    return records, checks, comparisons, metrics


def result_artifacts(root=ROOT):
    validate_namespace(root)
    expected, packets, routes = packet_artifacts(root)
    packet_commit = verify_packets_committed(root, expected)
    paths = freeze.planned_outputs()
    raw_bytes = {}
    for index, label in enumerate(RAW_LABELS, 1):
        path = freeze.safe_path(root, paths[label])
        raw_bytes[index] = path.read_bytes() if path.exists() else None
        if path.exists():
            verify_raw_committed(root, paths[label], raw_bytes[index], packet_commit)
    # Profiles are coordinator-only and are joined after raw collection, never sent to authors.
    profiles = {}
    for n in iter_json_records(root / freeze.INSTRUMENT / "final_normalized_candidates.jsonl"):
        key = ":".join((n["question_id"], n["producer_partition"], n["candidate_id"]))
        profiles[key] = n["candidate_semantic_profile"]
    records, checks, comparisons, metrics = analyze(packets, routes, raw_bytes, profiles)
    provenance = {"plan_sha256": sha((root / freeze.PLAN).read_bytes()),
                  "plan_freeze_commit": freeze.validate_plan(root)["freeze_commit"],
                  "runtime_receipt_sha256": sha((root / RECEIPT).read_bytes()),
                  "runtime_freeze_commit": validate_runtime(root)["runtime_freeze_commit"],
                  "implementation_commit": read_json(root / RECEIPT)["implementation_commit"],
                  "packet_freeze_commit": packet_commit}
    for record in records:
        record["run_provenance"] = provenance
    metrics["run_provenance"] = provenance
    exposure = {"schema_version": "narrowed_grounding_exposure_v0_1", "question_ids": list(freeze.IDS),
                "new_question_ids": [], "delivered_question_ids": [p["question_id"] for i, p in enumerate(packets, 1) if raw_bytes[i] is not None],
                "unseen_evaluation_allowed": False, "evidence_boundary": EVIDENCE}
    report = ("# Narrowed grounding v0.1 result\n\nDecision: `" + metrics["decision"] + "`.\n\n"
              "These are static AI grounding observations, not semantic gold, execution, or answer accuracy.\n\n"
              "```json\n" + json.dumps(metrics, indent=2, sort_keys=True) + "\n```\n")
    payloads = {"records": jsonl_file_bytes(records), "checks": jsonl_file_bytes(checks),
                "comparisons": jsonl_file_bytes(comparisons), "metrics": json_file_bytes(metrics),
                "report": report.encode(), "exposure": json_file_bytes(exposure)}
    manifest = {"schema_version": "narrowed_grounding_run_manifest_v0_1",
                "status": "complete" if metrics["delivered_valid_candidate_records"] == 14 and
                not metrics["technical_errors"] and not metrics["source_unavailable"] else "incomplete_or_failed",
                "decision": metrics["decision"], "run_provenance": provenance, "evidence_boundary": EVIDENCE,
                "raw_outputs": [{"path": paths[label], "status": "received" if raw_bytes[i] is not None else "missing",
                                 "sha256": sha(raw_bytes[i]) if raw_bytes[i] is not None else None}
                                for i, label in enumerate(RAW_LABELS, 1)],
                "outputs": {label: {"path": paths[label], "sha256": sha(data)} for label, data in payloads.items()}}
    payloads["run_manifest"] = json_file_bytes(manifest)
    return payloads, metrics


def write_once(root, payloads):
    paths = freeze.planned_outputs()
    for label in payloads:
        path = freeze.safe_path(root, paths[label])
        require(not path.exists(), "output already exists: " + label)
    return write_output_batch({label: (root / paths[label], data) for label, data in payloads.items()}, overwrite=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ("freeze-runtime", "validate-only", "build-packets", "analyze", "validate-results"):
        mode.add_argument("--" + name, action="store_true")
    parser.add_argument("--require-output-absence", action="store_true")
    args = parser.parse_args()
    try:
        exact_pins()
        pinned_views()
        if args.freeze_runtime:
            freeze.validate_plan(require_output_absence=True)
            require(not freeze.safe_path(ROOT, RECEIPT).exists(), "runtime receipt already exists")
            head = freeze.git(ROOT, "rev-parse", "HEAD").decode().strip()
            freeze.bindings(ROOT, head, RUNTIME_INPUTS)
            tests = runtime_tests()
            freeze.require_absent(ROOT)
            receipt = implementation_receipt(ROOT, head, tests)
            write_output_batch({"receipt": (ROOT / RECEIPT, json_file_bytes(receipt))}, overwrite=False)
            result = {"status": "receipt_written_commit_required", "tests": tests}
        elif args.validate_only:
            result = validate_runtime(require_absence=args.require_output_absence)
        elif args.build_packets:
            validate_runtime(require_absence=True)
            payloads, _, _ = packet_artifacts()
            result = {"status": "packets_written_commit_before_authoring", "outputs": write_once(ROOT, payloads)}
        else:
            payloads, metrics = result_artifacts()
            if args.validate_results:
                for label, data in payloads.items():
                    require(freeze.safe_path(ROOT, freeze.planned_outputs()[label]).read_bytes() == data,
                            "result does not reconstruct: " + label)
            else:
                # Do not create placeholder results when no author input exists.
                require(any((ROOT / freeze.planned_outputs()[label]).exists() for label in RAW_LABELS),
                        "no raw input exists; refusing placeholder results")
                write_once(ROOT, payloads)
            result = {"status": "artifacts_reconstructed" if args.validate_results else "artifacts_written",
                      "decision": metrics["decision"], "technical_errors": metrics["technical_errors"]}
        print(json.dumps(result, sort_keys=True))
        return 0
    except SourceUnavailable as exc:
        print(json.dumps({"status": "blocked", "decision": "BLOCKED_PINNED_ENVIRONMENT_UNAVAILABLE",
                          "error": str(exc), "outputs_written": False}, sort_keys=True))
        return 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
