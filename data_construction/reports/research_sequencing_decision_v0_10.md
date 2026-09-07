# Research sequencing decision v0.10

Date: 2026-09-07

## Decision

`IMPLEMENT_FROZEN_NARROWED_GROUNDING_PROTOCOL`

Narrowed-grounding plan v0.1 is frozen at
`b2ca1fbc413336fa330b11a14649735acc25f0df`, after implementation/design/protocol
commit `6bd9c36ddc6207552b778cf5b20b16946975ef05`. The validator verifies the
introducing commit, its parent ancestry, exact plan reconstruction, source and
contract hashes, and the entire output namespace's absence at that commit.
Current output absence also passes. There are no grounding results.

## Bound observations and choice

The source baseline is `aa380e69b534e475f09d496955ebcbac69531309`. Bind the
complete targeted-v0.1 and instrument-v0.2 runs, their plans, the existing
sanitized environment contract and views, source/history/exposure/split
manifests, and decision v0.9. All remain unchanged.

Use exactly these question IDs in order:

1. `0d48bffa70ef4acf`
2. `cc681cfdba9badd5`
3. `1e2e4e4f72a64bbf`
4. `1e674ae4b655c1a1`
5. `1ca8ffcd3e20e498`
6. `ba563b015b09bf21`

Retain all fourteen final full-eligible candidate observations, twelve
original author-question pairs, and 52 binding slots. At this small scale,
deduplication would save little and could conceal differences in physical
source binding despite shared semantic profiles. Each source candidate and
record has its own hash and all identities remain in the coordinator ledger.
No candidate is preferred or promoted to gold.

## Frozen operational design

Twenty output files are predeclared: six question packets, six raw response
files, a packet manifest, canonical records, checks, question comparisons,
metrics, report, run manifest, and grounding exposure ledger. Each question
gets one fresh context and one immutable response covering all its candidates.
This design does not provide independent cross-author grounding agreement.
Missing responses remain missing with an incomplete run status. Invalid raw
responses remain preserved without semantic repair or hidden retry.

Use complete already committed table/link-closure views, with question-local
candidate inputs and opaque aliases. No official answer, trace, prior result,
E1 assessment, producer identity, signature, or unselected question is sent to
grounding authors. Source text can contain relevant facts; global cognitive
noninference cannot be authenticated. The freezer hashes environment bytes
but does not extract locators or values.

Specify static pointers or symbolic dynamic locator rules. Dynamic rules
refer to strict upstream outputs and pinned source scopes without evaluating
filters, retrieval, extraction, arithmetic, comparison, or answer projection.
Bindings include provenance, types/cardinality, entity association and
reasoning parameters. Resolved means explicitly bound under the contract;
it does not mean successfully executed or semantically correct.

Every candidate alternative accounts for every source slot and operator.
Preserve compatible alternatives and flag incompatible unresolved choices.
Pass requires all fourteen candidates resolved, zero unresolved dispositions,
zero technical/leakage errors, and zero lost observations or identified
alternatives. Apply technical failure, missing source, incomplete collection,
ambiguity/coverage review, then pass, in that order. Even pass only freezes
evidence for a separate execution plan.

## Implementation gate and interpretation

The plan is concretely committed and machine-checkable. Packet/output schemas,
the grounding validator, and the analyzer are not yet implemented. Implement
them from the unchanged design and commit a runtime receipt binding code,
schemas, dependencies, tests, plan hash and plan-freeze commit while the twenty
outputs remain absent. This is the next task before any grounding generation.
Any necessary protocol change requires a new version before outputs.

Seven new regressions cover exhaustive selection, provenance mismatch and
ineligibility rejection, branch ordering, output namespace contamination,
path/symlink guards, and actual temporary-Git freeze/ancestry/tampering checks.
They are engineering tests, not grounding observations. The broader suite and
preflight results are recorded in the handoff/state after integration checking.

Earlier results, eleven released schemas, three provisional vocabularies,
historical evidence, split allocations and the 300-question exposure ledger
remain unchanged. Grounding, execution, answer recovery and human evidence
remain zero; no fresh or locked-evaluation question was consumed. Remote push
is outside the user's requested TODO-2 work and remains pending.
