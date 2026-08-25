# Crossed-author open realization sensitivity protocol v0.1

You are one of two fresh-context AI authors in a producer-confound diagnostic.
Every author receives the same 16 already environment-exposed development
records. This is not human review, majority voting, gold annotation, or unseen
evaluation.

## Isolation

- Open only your assigned authoring packet, this protocol, and the bound
  `open_operator_realization_schema_v0_1.json` when syntax is needed.
- Do not open prior E1 assessments, prior E2 realization records, normalization
  projections/results/metrics, candidate vocabularies, answers, traces, or the
  other author's packet/output.
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
2. preserve every target semantic node through explicit mappings;
3. distinguish backbone-realization nodes from environment-extension nodes;
4. keep unresolved source needs as typed slots whose `resolved_locator` is
   null and whose grounding status remains `not_grounded_in_this_stage`;
5. declare exact DAG roots and sinks, use every slot, and keep candidate,
   mapping, node, and slot IDs unique and sequential within each record;
6. list each variant's candidate IDs in record order;
7. keep `preferred_candidate_id` and `preference_reason` null unless the
   packet supplies evidence that one valid candidate should be preferred.

Do not emit factual answers, row/cell/document/span locators, execution claims,
grounding claims, or reusable vocabulary claims. Multiple valid split/fuse
realizations are allowed, but do not manufacture alternatives merely to match
a perceived prior author style.

## Output

Write canonical JSONL in packet order: one compact JSON object per line, no
Markdown fences, commentary, blank lines, or extra records.
