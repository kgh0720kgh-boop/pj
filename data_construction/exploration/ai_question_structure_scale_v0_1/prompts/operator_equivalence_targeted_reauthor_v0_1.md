# Targeted crossed-author re-authoring protocol v0.1

You are one of two fresh-context AI authors in a narrowly targeted structural
stability diagnostic. Every author receives the same six already exposed
development records. These records were selected before this authoring run;
the reason for selecting any individual record is hidden from you. This is not
human review, majority voting, adjudication, gold annotation, or unseen
evaluation.

## Isolation

- Open only your assigned authoring packet, this protocol, and the bound
  `open_operator_realization_schema_v0_1.json` when syntax is needed.
- Do not open prior E1 assessments, prior E2 realization records, any earlier
  author outputs, normalization projections/results/metrics, candidate
  vocabularies, answers, traces, or the other targeted author's packet/output.
- Do not inherit or consult another authoring conversation.
- If you had prior exposure to a packet record before this packet, set the
  exposure field truthfully; non-naive exposure requires an indeterminate
  result under the schema contract.

## Task

For each packet item, return exactly one JSON object conforming to
`open_operator_realization_v0_1`. Copy every field in `fixed_output_fields`
exactly and fill only the fields listed in `author_fill_fields`.

Use record-local descriptive operator labels. They are not cross-record
taxonomy keys. For every target backbone variant:

1. create at least one complete candidate when the supplied environment can
   realize it without grounding a concrete locator;
2. preserve every target semantic node and required semantic dependency
   through explicit mappings;
3. preserve every target output and do not add an unmapped operator output;
4. distinguish backbone-realization nodes from environment-extension nodes;
5. keep unresolved source needs as typed slots whose `resolved_locator` is
   null and whose grounding status remains `not_grounded_in_this_stage`;
6. declare exact DAG roots and sinks, use every slot, and keep candidate,
   mapping, node, and slot IDs unique and sequential within each record;
7. list each variant's candidate IDs in record order;
8. keep `preferred_candidate_id` and `preference_reason` null because the
   packet supplies no evidence for preferring one valid alternative.

Exact graph identity is not the sole correctness target. Preserve genuinely
valid alternative split/fuse plans when you independently identify them, but
do not manufacture alternatives or imitate a perceived prior author style.

Do not emit factual answers, row/cell/document/span locators, execution claims,
grounding claims, prior-result comparisons, or reusable vocabulary claims.

## Output

Write canonical JSONL in packet order: one compact JSON object per line, no
Markdown fences, commentary, blank lines, or extra records.
