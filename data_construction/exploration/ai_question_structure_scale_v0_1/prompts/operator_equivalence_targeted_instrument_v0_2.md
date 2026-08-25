# Targeted authoring-instrument revision protocol v0.2

You are one of two fresh-context AI authors in a six-question structural
stability diagnostic. The six records were already exposed before this run.
Their selection reason is hidden. This is AI exploratory non-gold evidence,
not human review, voting, adjudication, unseen evaluation, or grounding.

## Isolation

- For the draft, open only your assigned packet, this protocol, and
  `open_operator_realization_schema_v0_1.json` when syntax is needed.
- Do not open earlier E1/E2 records, any earlier author output, any
  normalization/comparison/result artifact, candidate vocabularies, answers,
  traces, grounding, execution, or the other instrument author's files.
- Stay in the same isolated author context for the single feedback round.
- For revision, open only your original allowed inputs, your own immutable
  draft, and your own candidate-local feedback file.
- Attest prior exposure truthfully. Non-naive exposure makes the record
  indeterminate under this protocol.

## Draft task

Return exactly one `open_operator_realization_v0_1` object per packet item.
Copy `fixed_output_fields` exactly and fill only `author_fill_fields`. Use
record-local descriptive operator labels; they are not taxonomy keys.

For every target backbone variant, independently identify valid complete or
partial realizations. When the supplied environment can realize a variant
without grounding a concrete locator, include at least one complete candidate.
For each candidate:

1. map every target node the candidate claims to realize;
2. preserve every required target dependency through the operator DAG;
3. map every target output to an operator output;
4. preserve output arity and emit no unmapped operator output;
5. classify every operator node and use every typed unresolved slot;
6. keep all IDs unique and sequential within the record;
7. keep `preferred_candidate_id` and `preference_reason` null.

Preserve independently identified valid alternatives. Do not manufacture an
alternative and do not imitate an assumed prior author style. Do not emit an
answer, concrete locator, execution/grounding claim, cross-record vocabulary,
or comparison with an unseen reference.

## One feedback round

After the immutable draft is submitted, a deterministic checker returns one
candidate-local feedback record per question. The feedback is limited to:

- target-node coverage;
- preservation of required target dependencies;
- mapped target-output coverage; and
- output arity/unmapped-output preservation.

It contains no reference plan, prior result, semantic signature, eligibility
label, preferred candidate, answer, trace, grounding, or execution evidence.
Use this feedback exactly once. Revise your own record where warranted, while
retaining genuinely valid alternative plans. A passing diagnostic is not a
claim that the candidate is semantically correct; review it independently and
copy it unchanged only if no correction is warranted.

## Output format

For both draft and final submission, write canonical JSONL in packet order:
one compact JSON object per line, with no Markdown, blank lines, or commentary.
