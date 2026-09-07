# Narrowed-grounding runtime freeze v0.1

Date: 2026-09-07

Decision: `MATERIALIZE_FROZEN_NARROWED_GROUNDING_PACKETS`.

## Completed prerequisite, not a grounding result

The frozen design/plan from decision v0.10 is unchanged. Implementation,
packet/raw schemas, author guide and 26 regression tests were committed at
`2983168f48689e8e7129a9bdecde4787a4ecb8cf`. The runtime receipt was committed
separately at `6c7487beddb03625b9fd23ef7514eebe307d397b`, after the plan commit
`b2ca1fbc413336fa330b11a14649735acc25f0df`, with the entire output namespace
empty. Its SHA-256 is
`723ba3447ac618ec049d4b875cf1341c0a053a2a50870211d90c3773fda230b7`.

The same six existing questions, twelve author-question pairs, fourteen
candidate observations and 52 source slots remain fixed. No fresh ID, raw
grounding proposal, executed graph, extracted answer, human evidence, or gold
record was introduced. Live packet projections were reconstructed only in
memory to verify allowlisted visibility and exact retention; this was an
engineering check, not an authoring run.

## Frozen runtime contract

The two closed Draft 2020-12 schemas and static validator cover packet/candidate
hashes, source slot cardinality, complete slot/operator identities, identified
alternative retention, scoped table/column/link/document locators, exact
question-literal spans, unevaluated upstream-dependent locators and ordered
symbolic derived operands. Document locators require link membership, entity
association and requested attribute. No graph operation is executed.

The analyzer preserves all alternatives, counts the fixed 6/12/14/52
denominators, separates alternative-qualified counts, and retains malformed
or invalid raw evidence without promoting partial records. It implements the
five original stopping branches, in order:

1. Technical or leakage failure.
2. Missing pinned source or explicitly incomplete source delivery.
3. Incomplete raw collection.
4. Unresolved ambiguity or coverage requiring review.
5. Full static coverage permitting a separately frozen execution plan only.

Every branch stops before execution and answer recovery. A file-generation or
reconstruction success is distinct from the scientific decision. Missing source
diagnostics do not write placeholder results. Existing outputs are never
overwritten; packet commits must follow the receipt and precede raw capture.
Raw responses must match their first committed capture, even after later Git
commits. Post-output semantic retries are rejected.

## Validation and limitations

All 26 runtime-specific tests passed before receipt creation. They include
synthetic positive/adversarial bindings, ambiguous/incompatible alternatives,
abstention and source delivery, all five branches, invalid JSON/provenance,
missing or duplicated identities, fixed denominator checks, local pointer
validation, namespace collisions/symlinks, Git ordering, raw immutability and
live in-memory projection retention. Latest complete-suite and preflight
observations are recorded in `HANDOFF_CURRENT.md` and `state/project_state.json`.

Declared types, roles, semantic compatibility, explanation truthfulness,
complete disclosure of all mentally considered alternatives, non-execution
inside an author's reasoning and cognitive independence are not authenticated
by these checks. Closed fields and visibility allowlists do not prove absence
of latent inference. Static structural validity is not semantic correctness,
successful execution, gold grounding or answer accuracy. Actual model IDs,
revision/seed limitations, context IDs and raw capture status must be recorded
truthfully in the future author responses, not invented now.

## Exact next task

Validate the committed runtime with current output absence. Generate exactly
six question packets plus the coordinator manifest using `--build-packets`,
inspect their allowed inputs and commit them together before authoring. Use
one new context per question; each sees only its own complete packet, frozen
protocol, guide and response schema. Do not distribute routing metadata or
prior result/author information. Preserve and commit the single raw response
per question unchanged, then analyze without semantic repair. Runtime contract
changes require a separately versioned decision before any affected output.

This turn performed no fetch or push. Local-only commit continuity is recorded
separately from scientific readiness; remote synchronization remains pending.
