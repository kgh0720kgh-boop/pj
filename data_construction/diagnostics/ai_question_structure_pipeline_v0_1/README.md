# AI question-structure pipeline diagnostic v0.1

This directory contains a non-evidentiary shadow run of the question-first
pipeline.  It exists to exercise artifact binding, two-reviewer collection,
blinded alignment, shadow hold-out comparison, independent topology elicitation,
and final reporting from end to end.

Nothing in this directory is human annotation, human review, gold data, a
Phase A1 pass, Phase A2 entry evidence, Phase B authorization, or evidence that
a common executable graph exists.  The canonical human lane remains unchanged
with zero raw human records.

The contract and prompts under `contracts/` and `prompts/` are frozen before
reviewer output is collected.  `run_001/` is write-once evidence for the first
diagnostic execution.  The two reviewer contexts receive the same question-only
views and never receive each other's output.  This is procedural context
separation, not machine-authenticated or statistical independence.

Pipeline order:

1. reviewer-specific question-only free observations;
2. reviewer-specific structured, storage-neutral semantic representations;
3. deterministic schema, hash-binding, cue, reference, and DAG checks;
4. identity-blinded A/B semantic alignment by a separate AI role;
5. calibration-versus-shadow-hold-out descriptive comparison;
6. a separate topology-only AI pass on the 20 shadow hold-out questions;
7. structural comparison with reviewer topologies and the preserved Phase B
   proposal artifacts; and
8. a final diagnostic report, emitted regardless of semantic concordance.

Invalid or tampered inputs block derived analysis.  Low agreement, unresolved
alignment, abstention, or schema gaps do not block the diagnostic report; they
are findings in it.
