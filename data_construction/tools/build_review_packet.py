#!/usr/bin/env python3
"""Build a self-contained, stage-gated HTML annotation review packet."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

from _common import (
    first_string,
    historical_output_collision_errors,
    iter_json_records,
    output_path_collision_errors,
    sha256_file,
)


ALWAYS_HIDDEN_KEYS = {
    "answer",
    "answer_node",
    "answer_text",
    "correct_response",
    "em",
    "f1",
    "gold_answer",
    "gold_span",
    "final_answer",
    "model_performance",
    "old_condition",
    "old_manual_graph",
    "oracle_document_id",
    "reference_answer",
    "target_answer",
    "weak_answer_node",
}
STAGE_ALLOWED_PROPOSAL_KEYS = {
    "question_only": {
        "question_id",
        "semantic_skeleton",
        "information_obligations",
        "abstract_topology",
    },
    "topology": {
        "question_id",
        "semantic_skeleton",
        "information_obligations",
        "abstract_topology",
        "operator_topology",
    },
    "grounding": {
        "question_id",
        "semantic_skeleton",
        "information_obligations",
        "abstract_topology",
        "operator_topology",
        "grounding",
        "execution_graph",
        "alternative_plans",
        "ambiguity",
    },
}
QUESTION_ONLY_HIDDEN_KEYS = ALWAYS_HIDDEN_KEYS | {
    "arguments",
    "column_index",
    "column_label",
    "document_id",
    "document_ids",
    "execution_graph",
    "grounding",
    "join_key",
    "literal",
    "operator",
    "operator_topology",
    "oracle_document_id",
    "row_predicate",
    "schema_id",
    "table_id",
    "tool",
}
TOPOLOGY_HIDDEN_KEYS = ALWAYS_HIDDEN_KEYS | {
    "column_index",
    "column_label",
    "document_id",
    "document_ids",
    "execution_graph",
    "grounding",
    "join_key",
    "literal",
    "oracle_document_id",
    "row_predicate",
    "schema_id",
    "table_id",
}
STAGE_HIDDEN_KEYS = {
    "question_only": QUESTION_ONLY_HIDDEN_KEYS,
    "topology": TOPOLOGY_HIDDEN_KEYS,
    "grounding": ALWAYS_HIDDEN_KEYS,
}
ENVIRONMENT_DERIVED_LAYER_KEYS = ALWAYS_HIDDEN_KEYS | {
    "abstract_topology",
    "alternative_plans",
    "bundle_status",
    "execution_graph",
    "grounding",
    "information_obligations",
    "operator_topology",
    "review_status",
    "semantic_skeleton",
}
TOPOLOGY_ENVIRONMENT_KEYS = {
    "capabilities",
    "capability_profile",
    "columns",
    "environment_capabilities",
    "header",
    "headers",
    "id",
    "schema",
    "section_title",
    "table_id",
    "title",
    "uid",
}
TOPOLOGY_CONCRETE_VALUE_KEYS = {
    "answer",
    "answers",
    "cell",
    "cells",
    "content",
    "data",
    "document",
    "documents",
    "linked_passage",
    "linked_passages",
    "passage",
    "passages",
    "request",
    "requests",
    "row",
    "rows",
    "sample_value",
    "sample_values",
    "text",
    "value",
    "values",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--proposals", required=True, type=Path)
    parser.add_argument(
        "--validation-checks",
        required=True,
        type=Path,
        help="Full-schema+structural validator JSONL bound to the exact proposal bytes",
    )
    parser.add_argument("--environment", type=Path, help="Optional JSON/JSONL table/schema context keyed by table_id")
    parser.add_argument("--stage", choices=tuple(STAGE_ALLOWED_PROPOSAL_KEYS), default="question_only")
    parser.add_argument("--output", type=Path, default=Path("data_construction/pilot/review_packet.html"))
    return parser.parse_args()


def canonical_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.casefold())


def canonical_key_variants(key: str) -> set[str]:
    canonical = canonical_key(key)
    variants = {canonical}
    if canonical.endswith("s") and len(canonical) > 1:
        variants.add(canonical[:-1])
    if canonical.endswith("ies") and len(canonical) > 3:
        variants.add(canonical[:-3] + "y")
    return variants


def sanitize(
    value: Any,
    hidden_keys: set[str] = ALWAYS_HIDDEN_KEYS,
    canonical_hidden: set[str] | None = None,
) -> Any:
    canonical_hidden = canonical_hidden or {
        variant for key in hidden_keys for variant in canonical_key_variants(key)
    }
    if isinstance(value, dict):
        return {
            key: sanitize(child, hidden_keys, canonical_hidden)
            for key, child in value.items()
            if not (canonical_key_variants(key) & canonical_hidden)
        }
    if isinstance(value, list):
        return [sanitize(child, hidden_keys, canonical_hidden) for child in value]
    return value


def forbidden_key_paths(
    value: Any,
    forbidden: set[str],
    prefix: str = "$",
) -> list[str]:
    canonical_forbidden = {
        variant for key in forbidden for variant in canonical_key_variants(key)
    }
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}"
            if canonical_key_variants(key) & canonical_forbidden:
                paths.append(path)
            paths.extend(forbidden_key_paths(child, forbidden, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(forbidden_key_paths(child, forbidden, f"{prefix}[{index}]"))
    return paths


def validation_check_errors(proposals_path: Path, checks_path: Path) -> list[str]:
    proposals = list(iter_json_records(proposals_path))
    checks = list(iter_json_records(checks_path))
    errors: list[str] = []
    if len(proposals) != len(checks):
        return ["validation checks do not have a 1:1 proposal record count"]
    proposals_sha256 = sha256_file(proposals_path)
    seen_ids: set[str] = set()
    for index, (proposal, check) in enumerate(zip(proposals, checks)):
        label = f"validation checks record {index}"
        question_id = first_string(proposal, ("question_id", "qid", "id"))
        context = check.get("validation_context") if isinstance(check, dict) else None
        if not isinstance(check, dict):
            errors.append(f"{label} is not an object")
            continue
        if question_id is None or question_id in seen_ids:
            errors.append(f"{label} proposal question_id is missing or duplicated")
        elif check.get("question_id") != question_id:
            errors.append(f"{label} question_id does not match the proposal")
        else:
            seen_ids.add(question_id)
        if check.get("validator_version") != "annotation_validator_v0_1":
            errors.append(f"{label} validator_version is unsupported")
        if check.get("status") != "pass" or check.get("errors") not in ([], None):
            errors.append(f"{label} is not a clean pass")
        if check.get("annotation_canonical_sha256") != canonical_json_sha256(proposal):
            errors.append(f"{label} proposal canonical SHA-256 does not match")
        if not isinstance(context, dict):
            errors.append(f"{label} has no validation_context")
            continue
        if context.get("annotations_artifact_sha256") != proposals_sha256:
            errors.append(f"{label} proposals artifact SHA-256 does not match")
        if context.get("validation_mode") != "draft_2020_12_plus_structural":
            errors.append(f"{label} was not produced by full-schema plus structural validation")
        for field in ("schema_artifact_sha256", "operator_vocabulary_artifact_sha256"):
            value = context.get(field)
            if not isinstance(value, str) or len(value) != 64:
                errors.append(f"{label} has no {field}")
    return errors


def topology_environment_view(value: dict[str, Any]) -> dict[str, Any]:
    """Expose schema/capability metadata, never concrete rows or linked passages."""
    projected = {
        key: child
        for key, child in value.items()
        if canonical_key(key) in {canonical_key(allowed) for allowed in TOPOLOGY_ENVIRONMENT_KEYS}
    }
    return sanitize(
        projected,
        ENVIRONMENT_DERIVED_LAYER_KEYS | TOPOLOGY_HIDDEN_KEYS | TOPOLOGY_CONCRETE_VALUE_KEYS,
    )


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def index_records(path: Path, keys: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(iter_json_records(path)):
        identifier = first_string(record, keys)
        if not identifier:
            raise ValueError(f"{path}: record {index} has no identifier from {keys!r}")
        if identifier in result:
            raise ValueError(f"{path}: duplicate identifier {identifier!r}")
        result[identifier] = record
    return result


def build_items(args: argparse.Namespace) -> list[dict[str, Any]]:
    questions = index_records(args.questions, ("question_id", "qid", "id"))
    proposals = index_records(args.proposals, ("question_id", "qid", "id"))
    environment = (
        index_records(args.environment, ("table_id", "id")) if args.environment else {}
    )
    missing_proposals = sorted(set(questions) - set(proposals))
    extra_proposals = sorted(set(proposals) - set(questions))
    if missing_proposals or extra_proposals:
        raise ValueError(
            "question/proposal identifiers differ: "
            f"missing proposals={missing_proposals[:20]!r}; extra proposals={extra_proposals[:20]!r}"
        )
    if not questions:
        raise ValueError("review packet input contains no questions")
    items: list[dict[str, Any]] = []
    allowed = STAGE_ALLOWED_PROPOSAL_KEYS[args.stage]
    for question_id, question in questions.items():
        proposal = proposals[question_id]
        table_id = first_string(question, ("table_id", "table", "tableId"))
        visible_proposal = {key: value for key, value in proposal.items() if key in allowed}
        contaminated_paths = forbidden_key_paths(
            visible_proposal,
            STAGE_HIDDEN_KEYS[args.stage],
        )
        if contaminated_paths:
            raise ValueError(
                f"proposal {question_id!r} contaminates the {args.stage!r} review view at "
                f"{contaminated_paths[:20]!r}"
            )
        item: dict[str, Any] = {
            "question_id": question_id,
            "question": first_string(question, ("question", "query", "text")),
            "proposal": sanitize(visible_proposal, STAGE_HIDDEN_KEYS[args.stage]),
        }
        if args.stage != "question_only":
            if not table_id:
                raise ValueError(f"question {question_id!r} has no table_id for stage {args.stage!r}")
            if table_id not in environment:
                raise ValueError(f"environment has no record for table_id {table_id!r}")
            item["table_id"] = table_id
            if args.stage == "topology":
                item["environment"] = topology_environment_view(environment[table_id])
            else:
                item["environment"] = sanitize(environment[table_id], ENVIRONMENT_DERIVED_LAYER_KEYS)
        item["reviewed_view_sha256"] = canonical_json_sha256(item)
        items.append(item)
    return items


def render_html(items: list[dict[str, Any]], stage: str) -> str:
    packet_payload_sha256 = canonical_json_sha256(items)
    # JSON is embedded in a classic script-data block.  Escaping every '<'
    # removes all HTML parser state transitions (including comment/script edge
    # cases), while U+2028/U+2029 remain safe across older JS parsers.
    payload = (
        json.dumps(items, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    stage_explanation = {
        "question_only": "질문 의미만 검토합니다. 표 환경, 정답, grounding, 실행 그래프는 숨겨져 있습니다.",
        "topology": "환경과 연산자 의존성을 검토합니다. 정답과 구체 grounding은 숨겨져 있습니다.",
        "grounding": "grounding과 실행 그래프를 검토합니다. 정답·기존 모델 점수·oracle 정보는 숨겨져 있습니다.",
    }[stage]
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HybridQA review packet — {html.escape(stage)}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 1100px; margin: 2rem auto; padding: 0 1rem; line-height: 1.45; }}
.notice {{ border-left: .3rem solid #805ad5; padding: .75rem 1rem; background: #faf5ff; }}
.card {{ border: 1px solid #cbd5e0; border-radius: .5rem; padding: 1rem; margin: 1rem 0; }}
pre, textarea {{ width: 100%; box-sizing: border-box; white-space: pre-wrap; overflow-wrap: anywhere; }}
pre {{ background: #f7fafc; padding: .75rem; }} textarea {{ min-height: 12rem; }}
.graph {{ overflow-x: auto; margin: .75rem 0; }} .graph svg {{ background: #fff; border: 1px solid #e2e8f0; }}
label {{ display: block; margin-top: .75rem; font-weight: 600; }}
button {{ padding: .65rem 1rem; }}
</style>
</head>
<body>
<h1>HybridQA 계층 주석 검토 패킷</h1>
<p class="notice"><strong>단계:</strong> {html.escape(stage)} — {html.escape(stage_explanation)}</p>
<label for="reviewer-id">검토자 익명 ID</label>
<input id="reviewer-id" type="text" autocomplete="off" required placeholder="stable-pseudonymous-id">
<div id="items"></div>
<button id="download" type="button">검토 결과 JSON 다운로드</button>
<script>
const items = {payload};
const packetPayloadSha256 = {json.dumps(packet_payload_sha256)};
const root = document.getElementById('items');
function renderGraph(topology) {{
  const holder = document.createElement('div'); holder.className = 'graph';
  const nodes = topology && Array.isArray(topology.nodes) ? topology.nodes : [];
  if (!nodes.length) return holder;
  const byId = new Map(nodes.map((node, index) => [String(node.id || node.node_id || `node_${{index}}`), node]));
  const levels = new Map([...byId.keys()].map(id => [id, 0]));
  for (let pass = 0; pass < nodes.length; pass += 1) {{
    for (const [id, node] of byId) {{
      const dependencies = Array.isArray(node.depends_on) ? node.depends_on.map(String) : [];
      const next = dependencies.length ? 1 + Math.max(...dependencies.map(dep => levels.get(dep) || 0)) : 0;
      if (next > (levels.get(id) || 0) && next < nodes.length) levels.set(id, next);
    }}
  }}
  const groups = new Map();
  for (const id of byId.keys()) {{ const level = levels.get(id) || 0; if (!groups.has(level)) groups.set(level, []); groups.get(level).push(id); }}
  const position = new Map();
  for (const [level, ids] of [...groups.entries()].sort((a, b) => a[0] - b[0])) {{
    ids.sort().forEach((id, index) => position.set(id, {{x: 35 + level * 220, y: 30 + index * 90}}));
  }}
  const width = Math.max(320, 90 + (Math.max(...levels.values()) + 1) * 220);
  const height = Math.max(120, 70 + Math.max(...[...groups.values()].map(ids => ids.length)) * 90);
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('width', width); svg.setAttribute('height', height);
  const defs = document.createElementNS(ns, 'defs'); const marker = document.createElementNS(ns, 'marker');
  marker.setAttribute('id', 'arrow-' + Math.random().toString(36).slice(2)); marker.setAttribute('markerWidth', '8'); marker.setAttribute('markerHeight', '8'); marker.setAttribute('refX', '7'); marker.setAttribute('refY', '4'); marker.setAttribute('orient', 'auto');
  const arrow = document.createElementNS(ns, 'path'); arrow.setAttribute('d', 'M0,0 L8,4 L0,8 z'); arrow.setAttribute('fill', '#718096'); marker.appendChild(arrow); defs.appendChild(marker); svg.appendChild(defs);
  for (const [id, node] of byId) {{
    const target = position.get(id); const dependencies = Array.isArray(node.depends_on) ? node.depends_on.map(String) : [];
    for (const dependency of dependencies) {{ const source = position.get(dependency); if (!source) continue; const line = document.createElementNS(ns, 'line'); line.setAttribute('x1', source.x + 150); line.setAttribute('y1', source.y + 24); line.setAttribute('x2', target.x); line.setAttribute('y2', target.y + 24); line.setAttribute('stroke', '#718096'); line.setAttribute('marker-end', `url(#${{marker.id}})`); svg.appendChild(line); }}
  }}
  for (const [id, node] of byId) {{
    const point = position.get(id); const rect = document.createElementNS(ns, 'rect'); rect.setAttribute('x', point.x); rect.setAttribute('y', point.y); rect.setAttribute('width', '150'); rect.setAttribute('height', '48'); rect.setAttribute('rx', '7'); rect.setAttribute('fill', '#edf2f7'); rect.setAttribute('stroke', '#4a5568'); svg.appendChild(rect);
    const label = document.createElementNS(ns, 'text'); label.setAttribute('x', point.x + 75); label.setAttribute('y', point.y + 20); label.setAttribute('text-anchor', 'middle'); label.setAttribute('font-size', '12'); label.textContent = String(node.operator || node.function || node.operation || 'NODE'); svg.appendChild(label);
    const idLabel = document.createElementNS(ns, 'text'); idLabel.setAttribute('x', point.x + 75); idLabel.setAttribute('y', point.y + 37); idLabel.setAttribute('text-anchor', 'middle'); idLabel.setAttribute('font-size', '10'); idLabel.textContent = id; svg.appendChild(idLabel);
  }}
  holder.appendChild(svg); return holder;
}}
for (const item of items) {{
  const card = document.createElement('section');
  card.className = 'card';
  const title = document.createElement('h2');
  title.textContent = item.question_id;
  card.appendChild(title);
  const question = document.createElement('p');
  question.textContent = item.question || '(질문 텍스트 없음)';
  card.appendChild(question);
  const context = document.createElement('pre');
  context.textContent = JSON.stringify({{table_id: item.table_id, environment: item.environment}}, null, 2);
  card.appendChild(context);
  const proposal = document.createElement('pre');
  proposal.textContent = JSON.stringify(item.proposal, null, 2);
  card.appendChild(proposal);
  const graph = item.proposal.execution_graph || item.proposal.operator_topology || item.proposal.abstract_topology;
  card.appendChild(renderGraph(graph));
  const statusLabel = document.createElement('label');
  statusLabel.textContent = '판정';
  const status = document.createElement('select');
  status.dataset.qid = item.question_id;
  status.className = 'status';
  for (const value of ['unreviewed', 'accept', 'accept_with_edits', 'reject', 'abstain']) {{
    const option = document.createElement('option'); option.value = value; option.textContent = value; status.appendChild(option);
  }}
  statusLabel.appendChild(status); card.appendChild(statusLabel);
  const editLabel = document.createElement('label');
  editLabel.textContent = '수정 주석 / 의견 / 대안 계획';
  const edit = document.createElement('textarea'); edit.dataset.qid = item.question_id; edit.className = 'edit';
  editLabel.appendChild(edit); card.appendChild(editLabel);
  root.appendChild(card);
}}
document.getElementById('download').addEventListener('click', () => {{
  const reviewerId = document.getElementById('reviewer-id').value.trim();
  if (!reviewerId) {{ window.alert('검토자 익명 ID를 입력하세요.'); return; }}
  const decisions = items.map(item => document.querySelector(`select[data-qid="${{CSS.escape(item.question_id)}}"]`).value);
  if (decisions.some(value => value === 'unreviewed')) {{ window.alert('모든 항목의 판정을 완료하세요.'); return; }}
  const completedAt = new Date().toISOString();
  const reviews = items.map((item, index) => ({{
    schema_version: 'human_review_record_v0_1',
    question_id: item.question_id,
    review_stage: {json.dumps(stage)},
    reviewer_record: {{
      reviewer_id: reviewerId,
      completed_at: completedAt,
      decision: decisions[index],
      notes: document.querySelector(`textarea[data-qid="${{CSS.escape(item.question_id)}}"]`).value || undefined
    }},
    reviewed_view_sha256: item.reviewed_view_sha256,
    provenance: {{
      method: 'offline_review_packet_v0_1',
      human_review_claimed: true,
      packet_payload_sha256: packetPayloadSha256,
      reviewed_view_canonicalization: 'sorted_compact_json_utf8_sha256_v0_1'
    }}
  }}));
  const blob = new Blob([JSON.stringify(reviews, null, 2) + '\\n'], {{type: 'application/json'}});
  const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'human_reviews.json'; link.click();
  URL.revokeObjectURL(link.href);
}});
</script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    outputs = {"output": args.output}
    collisions = output_path_collision_errors(
        {
            "questions": args.questions,
            "proposals": args.proposals,
            "validation_checks": args.validation_checks,
            "environment": args.environment,
        },
        outputs,
    )
    collisions.extend(
        historical_output_collision_errors(outputs, Path(__file__).resolve().parents[2])
    )
    if collisions:
        print("; ".join(collisions), file=sys.stderr)
        return 2
    if args.stage != "question_only" and args.environment is None:
        print(f"--environment is required for the {args.stage!r} review stage", file=sys.stderr)
        return 2
    try:
        validation_errors = validation_check_errors(args.proposals, args.validation_checks)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        items = build_items(args)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(items, args.stage), encoding="utf-8", newline="\n")
    print(json.dumps({"stage": args.stage, "items": len(items), "output": args.output.as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
