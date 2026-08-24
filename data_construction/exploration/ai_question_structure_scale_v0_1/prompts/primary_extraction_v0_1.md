# Primary question-only semantic-backbone extraction prompt v0.1

Process only the assigned records from the frozen N=100 question-only view.
For each question, emit exactly one JSON object conforming to
`semantic_backbone_record_schema_v0_1.json`, in the assigned input order.

You may use only the opaque question ID and exact question text. Do not inspect,
infer from, browse for, or include a factual answer, table identity/schema/rows,
linked-document identity/text, operator proposal, grounding, execution trace,
historical graph, another worker's record, or downstream metric.

The output describes what information-processing dependencies the question
requires, independent of where information is stored and which physical tool
would execute it.

## Semantic roles

- `RESOLVE_REFERENT`: identify the entity, event, group, or value referred to by
  descriptive constraints.
- `ACQUIRE_PROPERTY`: obtain a requested relation, property, explanation, or
  value of an already available referent.
- `COMPARE`: compare two or more established values.
- `AGGREGATE`: count, sum, average, or otherwise aggregate a set.
- `ORDER_OR_EXTREMUM`: rank, choose an ordinal item, or select a minimum/maximum.
- `DERIVE`: compute or transform a value, such as a difference, date component,
  or arithmetic result.
- `VERIFY`: test whether an established candidate satisfies a condition.
- `COMBINE`: combine separately established results into the requested output.
- `OTHER`: use only when none of the roles above is adequate; explain it in
  `other_role_description` rather than forcing a fit.

Do not create a separate node merely to print or format the answer. Use the
smallest graph that preserves genuine information dependencies. Keep distinct
steps when later work depends on their separate outputs. A node may depend on
multiple prior nodes; branches and joins are allowed. Use no more than eight
nodes.

`source_cues` must be exact, case-sensitive substrings of the question. If a
semantic step is implicit, use an empty cue array and a nonempty
`implicit_rationale`. Never place a cue and an implicit rationale on the same
item.

Use `uncertain` when a plausible primary graph can still be recorded but the
question leaves a material referent, scope, cardinality, time, measurement,
comparison, or grammar choice unresolved. Use `not_representable` only when no
truthful question-only graph can be supplied under this contract.

Alternative graphs are for genuinely different dependency structures that can
change selection, ordering, or answer cardinality. Do not create an alternative
for wording changes, node-ID changes, or a same-role split/merge of the primary
graph.

This is one AI-generated exploratory record per question. It is non-human,
non-gold, and cannot establish semantic correctness, human agreement, a
universal graph, an executable graph, or modeling readiness.
