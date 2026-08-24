# Backbone adequacy assessment prompt v0.1

## Role and evidence boundary

You are performing the first environment-aware assessment of one frozen
question-only candidate semantic backbone. The candidate was AI-produced, is
non-human and non-gold, and may be incomplete or wrong. A candidate family is
not evidence of semantic correctness.

Use only the records supplied in the assigned E1 authoring packet. Treat every
packet record independently: do not use another record to infer its semantics,
status, or rationale. Apart from this prompt and its output schema, do not open
another partition, repository data artifact, external source, prior response,
or unrelated tool output.

E1 must run in a fresh context that does not inherit any earlier conversation
about a selected question. This is a procedural requirement, not a
machine-authenticated global nonexposure guarantee. Set
`author_prior_exposure_to_record_before_packet` to
`procedurally_attested_none` only when this context had no question-specific
information before receiving the assigned packet; otherwise use
`known_exposed` or `unknown` and return an indeterminate result. Always set
`global_nonexposure_machine_authenticated` to `false`.

The dataset supplies the question-to-table binding and the complete linked
document closure for that table. This task does not evaluate table retrieval.
The visible environment can naturally contain answer-bearing facts; this does
not mean that an official answer annotation is in the authoring input.

## Inputs you may use

The supplied record contains:

- the question;
- the frozen question-only answer specification, primary semantic graph, and
  explicitly preserved alternative semantic graphs;
- the full selected table, including every row and cell; and
- the exact closure of documents linked from that full table.

The answer specification describes the requested answer type and cardinality.
It is not a factual answer label.

## Inputs and actions that are forbidden

Do not consult or reconstruct:

- the official factual answer, answer span, answer node, `dev_reference`, or
  any weak or gold trace;
- historical condition-C or other historical graphs;
- any existing coarse, medium, or fine operator vocabulary;
- any previous operator proposal, granularity representation, review packet,
  grounding record, execution result, or answer-recovery result; or
- an operator realization produced for this question or another question.

Do not write the factual answer. Do not quote or identify a particular
answer-bearing row, cell, column, linked-document identifier, or text span. Do
not produce a formal grounding record, run an external execution, or record an
answer-recovery comparison. Because the environment is visible, the protocol
does not claim to machine-authenticate whether you internally inferred a
locator or answer.

## Semantic-versus-operational boundary

Judge only whether each frozen graph variant expresses the semantic
obligations of the question. Environment storage and access operations belong
to E2 and must not be used as a reason to change a semantic backbone.

For example:

- needing to scan table rows is an E2 access operation, not a missing E1
  semantic obligation;
- following a cell link and reading a linked document are E2 operations, not
  reasons by themselves to mark an E1 variant inadequate; and
- a missing row, missing link, or unavailable passage is an environment-support
  issue, not by itself evidence that the question-only semantics are wrong.

The environment may affect E1 only when it disambiguates the meaning of the
question or reveals a semantic mismatch, such as the intended referent,
cardinality, scope, comparison direction, or requested property. Every
`required_change.change_basis` must therefore be `question_semantics` or
`environment_disambiguation`. A `semantic_clarification` must not describe a
storage/access operation and must not contain a grounded locator.

## Variant-by-variant task

1. Assess the primary graph first, followed by every alternative graph in the
   exact order in which it appears in the input.
2. Emit exactly one `variant_assessments` item for each input variant, in that
   same order. Use `primary`, then the supplied `altN` identifier.
3. For each variant, check answer type and cardinality, referent resolution,
   property acquisition, transformations, and semantic dependencies.
4. Preserve a newly noticed interpretation in
   `additional_semantic_interpretations`; do not force one interpretation just
   to make the record complete.
5. Record required changes without modifying or overwriting the frozen input.

Use each variant `status` as follows:

- `adequate`: no semantic change is required;
- `partially_adequate`: some semantic obligations or dependencies are usable,
  but at least one explicit change is required;
- `inadequate`: the variant substantially fails to express the needed
  semantics and at least one explicit change is required; or
- `indeterminate`: the question and visible environment do not support a
  defensible judgment.

Set `candidate_variant_adequate` to `true`, `false`, `false`, or `null`,
respectively.

Derive the top-level result from all variant statuses using this exact order:

1. if any variant is `adequate`, top-level `overall_status` is `adequate` and
   `candidate_backbone_adequate` is `true`;
2. otherwise, if any variant is `partially_adequate`, the top level is
   `partially_adequate` and `false`;
3. otherwise, if any variant is `indeterminate`, the top level is
   `indeterminate` and `null`;
4. otherwise, all variants are `inadequate`, so the top level is `inadequate`
   and `false`.

This aggregate assesses the preserved candidate set. It does not silently
convert an adequate alternative into evidence that the primary graph is
adequate.

## Input-delivery status

Set `input_delivery.view_fully_consumed` to `true` and
`input_delivery.completeness_status` to `complete` only if the entire supplied
view was available and consumed without truncation. If it may have been
truncated or completeness is unknown, record that truthfully and use an
indeterminate/unable-to-assess result rather than guessing.

## Output contract

Return exactly one JSON object conforming to
`backbone_adequacy_assessment_schema_v0_1.json`. Return no Markdown and no text
outside the JSON object.

Copy every key and value in the packet record's `fixed_output_fields` object
verbatim into the output object. This supplies the exact schema version,
derived assessment ID, run/selection/question/family/view bindings, producer
partition, visibility, `operator_realization_seen`, and downstream statuses;
do not recompute or alter them.

Set `author_prior_exposure_to_record_before_packet` truthfully as described
above; this attestation is intentionally not prefilled by the packet.

In `evidence_boundary`, record that no official answer annotation, official
trace, historical graph, or prior operator proposal was in the authoring
input; no formal grounding record was produced; no external execution was run;
no answer value was output; and grounding, execution, and answer recovery were
not evaluated. Keep the latent-inference machine-authentication claim false,
and keep all gold, human-evidence, family-correctness, and modeling-ready
claims false.
