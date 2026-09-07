# Narrowed grounding v0.1 protocol

This protocol fixes a six-question grounding study before any new grounding
packet or annotation exists. It implements the next branch in sequencing
decision v0.9. The authoritative machine design is
`contracts/narrowed_grounding_design_v0_1.json`; the plan embeds it verbatim.

## Scope and selection

Use every one of the fourteen final full-eligible instrument-v0.2 candidate
observations. Retain their original twelve author-question identities, target
variants, graph hashes, and 52 source slots. No deduplication, preference,
majority vote, or new question selection is performed. All targeted-v0.1 and
instrument-v0.2 artifacts are bound as historical observations. The older run
is comparison provenance, not a grounding-author input or gold reference.

The six questions were selected for prior challenge behavior. Results are
conditional feasibility observations, not population prevalence or independent
replications. No human evidence, semantic gold, final vocabulary, executable
success, or answer accuracy is created by this study.

## Before any author receives a packet

First commit the design, this protocol, the metadata-only freezer, and its
tests. Run the freezer and commit the exact plan while the entire
`narrowed_grounding_v0_1/` output namespace is empty. The validator must check
the introducing Git commit, source and implementation ancestry, live file
hashes, exact reconstructed selection, and namespace absence at that commit.
An uncommitted JSON plan is insufficient.

Next implement the packet and output schemas, packet builder, static binding
validator, and analyzer from this unchanged contract. Commit a runtime receipt
at the path named in the plan, binding that plan's hash and freeze commit plus
all runtime dependencies, schemas, tests, and implementation commit. All twenty
planned outputs must still be absent. Runtime tests must cover valid static
and dynamic bindings, missing/duplicate slots, changed graphs, incompatible
alternatives, nonexistent pointers, wrong link membership, downstream/cyclic
references, literal span mismatch, answer fields, and every stopping branch.
If this design cannot be implemented faithfully, create a new design/plan
version before outputs; do not reinterpret the pass rule after seeing results.

## Packet content and routing

Create six self-contained packets in frozen question order. One new context
receives each packet, containing only that question, its referenced semantic
variants, all its selected candidates, and its complete existing sanitized
table/link-closure environment view. Assign opaque aliases in the plan's
candidate order (`observation_01`, etc. within each packet). A coordinator-only
manifest maps aliases back to source observations and hashes. Remove author
identity, E1 assessments and assessment hashes, family/signature fields,
eligibility labels, earlier metrics, and unrelated records from author input.
Retain candidate operation descriptions, graph dependencies, assumptions,
binding-slot requirements, and declared modality/cardinality.

Use the previously committed complete environment view by exact question ID.
Do not rank/crop passages using answers, obtain current Wikipedia pages, or
consult official answers/traces. Natural facts in allowed source text remain
visible; their presence is not an answer label. Cognitive noninference is not
machine-authenticated. If packet delivery is truncated, stop that submission
with an explicit incomplete-delivery disposition; do not claim full coverage.

Each context handles every candidate in its one question, preserving each
observation separately. This is one proposal pass, not two independent
grounding reviewers and not a cross-author grounding-agreement experiment.
There is no semantic feedback or repair round. Preserve even invalid output.
Exact same-packet transport resumption is allowed only before any output has
been delivered; log every attempt. Missing responses remain missing rather
than fabricated placeholders. A separate run manifest may report incomplete
collection without manufacturing a raw record for a failed context.

## Author task: bind arguments without evaluating the graph

For each candidate, submit one or more coherent grounding alternatives. Each
alternative accounts for exactly every original binding slot and operator node.
Every slot has one of `resolved`, `ambiguous`, `unavailable`, or `abstained`;
every operator has one of `specified`, `ambiguous`, `unavailable`, or `abstained`
argument dispositions. Identify the source slot/node, required role, locator
or symbolic parameter, expected type/cardinality, supporting provenance,
assumptions, and unresolved reason. Explicitly record `no_additional_arguments`
with a reason for an operator needing no extra parameter.

Grounding alternatives must be internally coherent. Two incompatible choices
require explicit ambiguity and separate alternatives; they cannot be silently
combined, preferred, or dropped. Preserve every identified alternative and its
assumptions. Retention checks measure captured alternatives; they do not prove
that an author discovered every semantically valid plan.

Static bindings use exact RFC 6901 pointers into the hash-bound environment
view. Column identity includes index and exact label. A linked document must
be in the allowed table-link closure and carry its link origin or a dynamic
link-following rule. A generic "use a document" placeholder is insufficient.

When a locator depends on an upstream operation, specify an unevaluated rule
over the pinned source scope and strict upstream node output. State the entity
association, requested attribute, declared type/cardinality, and selector.
Do not replace such a rule with a manually computed entity, filtered row set,
retrieved value, extracted span, or final answer. A resolved rule means its
arguments are explicit, not that runtime retrieval succeeded.

Question literals use exact zero-based half-open Unicode codepoint spans.
Source literals, when necessary as parameters, require source pointers and
must not encode a computed/extracted answer. Reasoning parameters specify
relation/function, ordered operand references, units, and tie/null rules.
Do not evaluate filters, comparisons, aggregates, arithmetic, extraction,
or answer projection. Local schema, hash, pointer, membership, and dependency
checks are static verification, not graph execution.

Keep original graphs, mappings, slots, and earlier semantic records immutable.
A newly discovered semantic defect becomes a separate limitation or unresolved
disposition here, never a silent upstream edit.

## Derivation and decision

Retain raw bytes, capture their hash, and write parsed canonical records
separately. Bind the source plan, candidate, view, packet, raw response, runtime
receipt and code commit. Record actual model identity at run time; revision,
seed, or raw-response details unavailable from the interface must be explicit.
Do not reuse an older run's model ID to imply the same current model.

Static checks derive candidate status. `resolved` requires every slot resolved
and every operator specified in every retained alternative, with no unresolved
choice. All-unavailable or all-abstained candidates keep those statuses;
incompatible complete choices are ambiguous; mixed resolved/unresolved cases
are partial (with ambiguity details retained). A raw omission is a technical
failure rather than abstention. Complementary partial candidates cannot be
unioned into a complete candidate.

Report fourteen candidate observations and 52 source slots as fixed primary
denominators. A source slot is resolved in the primary summary only if it is
resolved in every retained alternative with no incompatible unresolved choice;
report alternative-qualified counts separately. Report node coverage, target
variant coverage, six question and twelve author-question summaries separately.
After raw collection, compare locator/rule coverage by existing semantic
profiles and original authors without promoting exact pointer equality to
correctness. Different sources can legitimately implement the same requirement.

Apply branches in this order: technical/leakage failure; pinned source
unavailable; incomplete collection; ambiguity/coverage review; pass. Missing
source delivery is not evidence of semantic impossibility. Pass requires all
fourteen candidates resolved, zero unresolved slot/operator dispositions, zero
lost alternatives, and zero technical/leakage errors. Negative observations
are preserved and do not trigger automated re-authoring or fresh sampling.

The pass branch freezes grounding evidence for a separate execution plan.
Every branch ends without graph execution, answer recovery, corpus allocation,
vocabulary selection, or automatic expansion. Any later execution study needs
its own versioned contract.
