# Open operator realization prompt v0.1

## Role, isolation, and evidence boundary

You are producing an instance-level environment-aware operator realization for
one frozen non-gold question-only candidate backbone. Operator granularity is
an empirical research question. This task does not select a final operator
vocabulary and does not create a gold, grounded, or executable graph.

Use only the records from the assigned E2 authoring packet and their supplied
hashes. Treat each packet record independently: do not carry a label,
decomposition, preference, or status from one record into another. Apart from
this prompt and its output schema, do not open another partition or repository
data artifact. The hashes bind separately frozen E1 backbone-adequacy
assessments, but their content, status, rationale, changes, and variant
judgments are not in the E2 authoring input and must not be reconstructed.

E2 must run in a fresh context that does not inherit the E1 conversation. This
is a procedural requirement, not machine-authenticated global nonexposure.
Set `author_prior_exposure_to_backbone_adequacy` truthfully:

- `procedurally_attested_none` only if this fresh authoring context has not
  read or received E1 content;
- `known_exposed` if it has; or
- `unknown` if that cannot be established.

Always set `global_nonexposure_machine_authenticated` to `false`. The
authoring input proves only that E1 content was not included in that packet.
Also set `author_prior_exposure_to_record_before_packet` to
`procedurally_attested_none` only if this fresh context had no
question-specific information before receiving the assigned packet. If it was
previously exposed or cannot establish that fact, use `known_exposed` or
`unknown` and return an indeterminate result.

The dataset supplies the question-to-table association and the full table-link
closure. Table retrieval is not evaluated.

## Forbidden inputs and actions

Do not consult:

- the official factual answer, answer span, answer node, `dev_reference`, or
  any weak or gold trace;
- E1 assessment content;
- historical condition-C or other historical graphs;
- the preserved coarse, medium, or fine operator vocabularies;
- any previous granularity representation, operator proposal, review packet,
  grounding record, execution result, or answer-recovery result; or
- any external source or retrieval tool.

Do not write the factual answer. Do not record an exact row, cell, column,
linked-document identifier, or text span. Do not resolve a binding slot,
produce a formal grounding record, run an external execution, or record an
answer-recovery comparison. The protocol does not claim to machine-authenticate
whether visible environment facts caused an internal locator or answer
inference.

## Open operator notation

Use record-local descriptive labels. A repeated label in two records does not
assert a shared taxonomy entry. Do not translate labels into an existing
coarse, medium, or fine vocabulary.

Choose understandable operator boundaries without assuming they are final. If
two decompositions are reasonable—for example, one fuses an access step with
property acquisition and one splits them—preserve both as separate candidates
and mark `operator_boundary_split_or_merge` in `variation_axes`. Alternatives
may also differ in environment access path, semantic interpretation, or valid
dependency order. Exact graph match is not the sole correctness target.

## Candidate target and coverage

Every realization candidate targets exactly one supplied backbone variant via
`target_backbone_variant_id`. Do not cover multiple variants by taking a union
of mappings across candidates. A candidate is evaluated only against its own
target variant.

For each candidate:

1. Create a directed acyclic graph with unique `opN` node identifiers.
2. Give every node a record-local label, operation description, direct
   dependencies, input slots, output description, and operator-boundary
   rationale.
3. Create at least one `slotN` source binding slot. Slots describe required
   semantics, environment modality, and cardinality. Set every slot's
   `grounding_status` to `not_grounded_in_this_stage` and `resolved_locator` to
   `null`.
4. Every graph root must directly consume at least one source slot. A candidate
   marked `complete_for_target_variant` must contain at least one slot whose
   modality is an environment modality rather than only `question_literal` or
   `unknown`.
5. Map target-backbone nodes to operator nodes using `mappingN` records. Use
   only `one_to_one`, `one_to_many`, `many_to_one`, or `many_to_many` according
   to the actual cardinality. The mappings within one candidate must form a
   unique coverage partition of the target backbone and their referenced
   operator nodes.
6. Preserve dependency direction. For every target-backbone dependency A→B,
   the mapped operator sets must either share a fused operator or contain a
   forward operator path from A's realization to B's realization. A
   reversed-only path is invalid.
7. Align semantic outputs with graph sinks: every realized target-backbone
   output must lead to an operator sink, and every declared graph sink must be
   justified by a target output or an explicit downstream environment
   extension.
8. Classify every operator node exactly once in
   `operator_node_classifications`. Its nonempty `roles` is a subset of
   `backbone_realization` and `environment_extension`. If it has the
   environment-extension role, provide non-null `extension_type` and
   `extension_description`; otherwise both are null.
9. Every operator node must be covered by a backbone mapping, classified as an
   environment extension, or explicitly have both roles. Do not force a table
   scan, row/cell access, cell-link traversal, or linked-document access step
   into a false semantic-backbone mapping merely to pass coverage.
10. For `complete_for_target_variant`, map every target node and leave
    `unsupported_target_backbone_nodes` empty. For
    `partial_for_target_variant`, list every uncovered target node with a
    reason. Do not silently drop it.

Every operator node must contribute to an output path. All node dependencies,
slot references, roots, sinks, mappings, classifications, candidate references,
and variant references must resolve locally.

## Variant and record aggregation

Emit exactly one `variant_realization_results` item for every input variant in
input order (`primary`, then each `altN`). Candidate IDs in each result must
list exactly the candidates targeting that variant, in their record order.
For `blocking_unsupported_node_ids`, use an empty array for `fully_realized`;
for `partially_realized`, list only nodes unsupported by every partial
candidate for that variant (the intersection, which may be empty); for
`unavailable`, list at least one known blocking node. Candidate-local
unsupported lists remain the authority for each particular decomposition.
Use:

- `fully_realized` when at least one candidate for that variant has complete
  coverage;
- `partially_realized` when at least one partial candidate exists but none has
  complete coverage;
- `unavailable` when no candidate can be authored and the blockers are known;
  or
- `indeterminate` when the visible inputs do not support a defensible result
  (including when all candidates for that variant are themselves
  `indeterminate`).

Derive top-level `realization_status` using this exact order:

1. any `fully_realized` variant → `available`;
2. otherwise any `partially_realized` variant → `partial`;
3. otherwise any `indeterminate` variant → `indeterminate`;
4. otherwise all variants are `unavailable` → `unavailable`.

Zero realization candidates are valid only when no variant is fully or
partially realized. Do not invent a graph to avoid an empty array. Do not
designate `preferred_candidate_id` unless the visible question and environment
provide a defensible non-answer-based reason. If one is designated, it must be
complete when the top level is `available`, partial when it is `partial`, and
indeterminate when it is `indeterminate`.

## Input-delivery status

Set `input_delivery.view_fully_consumed` to `true` and
`input_delivery.completeness_status` to `complete` only if the entire supplied
view was available and consumed without truncation. A record may be
`available`, `partial`, or `unavailable` only with that complete delivery status.
Otherwise return an indeterminate/unable-to-realize record.

## Output contract

Return exactly one JSON object conforming to
`open_operator_realization_schema_v0_1.json`. Return no Markdown and no text
outside the JSON object.

Copy every key and value in the packet record's `fixed_output_fields` object
verbatim into the output object. This supplies the exact schema version,
derived realization ID, run/selection/question/family/view bindings, producer
partition, hash-only backbone-assessment binding, visibility, open authoring
contract, global-nonexposure flag, and downstream statuses; do not recompute or
alter them.

Set both author-exposure attestations truthfully as described above; neither is
prefilled by the packet.

In
`evidence_boundary`, truthfully record the input exclusions and that no formal
grounding record, external execution, or answer-value output was produced;
keep all evaluation, gold, human-evidence, global-nonexposure, and
modeling-ready claims false.

Do not derive or revise E1 adequacy from realization availability, and do not
infer any downstream signal from this record.
