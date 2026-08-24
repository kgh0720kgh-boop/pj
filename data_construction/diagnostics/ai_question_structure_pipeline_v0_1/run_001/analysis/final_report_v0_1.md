# AI question-structure shadow-pipeline analysis v0.1

## Outcome

The non-evidentiary diagnostic pipeline completed end to end. This is an engineering rehearsal, not a scientific phase pass. The canonical human lane still has zero records and the project decision remains `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`.

## Raw collection and integrity

- Two AI reviewer files contain 60 structured records in total, plus 60 frozen stage-1 observations.
- Schema, source-view hash, stage-1 binding, cue, reference, root/sink, obligation-coverage, and DAG checks passed.
- The reviewer contexts were procedurally separated; neither human nor statistical independence is claimed.

## Blinded alignment diagnostic

- Question dispositions across all 30: `{"COMPATIBLE_VARIATION": 20, "FULL_EQUIVALENCE": 10}`.
- Calibration compatible-or-full rate: `1.0` over 10 questions.
- Shadow hold-out compatible-or-full rate: `1.0` over 20 questions.
- Calibration mean reachability Dice: `1.0`; shadow hold-out: `1.0`.
- These values are deterministic only conditional on the frozen third-AI semantic crosswalk. They do not measure correctness.

## Independent topology-only diagnostic

- A fresh topology-only pass produced 20 held-out DAGs without upstream structure, environment, answers, or operator proposals.
- Exact full structural-signature rate versus reviewer 1: `0.85`; versus reviewer 2: `0.9`.
- This checks structural stability only; it is not evidence that question structure predicts an executable graph.

## Downstream connector preview

- The preserved Phase B proposal artifact remains unchanged with 30 records.
- Its deterministic check artifact contains 90 passing checks.
- Coarse/medium/fine comparisons here use only graph-size/depth/branch/join invariants. No Phase B human judgment was performed.
- Phase C grounding and execution were not run because this diagnostic intentionally exposes no answers or executable grounding references.

## Scientific status after the rehearsal

- Human evidence: 0
- Human agreement observations: 0
- Phase A1 pass: not claimed
- Phase A2 entry: not authorized
- Phase B entry: not authorized
- Gold/modeling-ready/common executable graph: not claimed
- Grounding/execution success: not evaluated

The next canonical task therefore remains two approved, mutually independent, exposure-naive real humans annotating the first ten-question batch. The diagnostic artifacts can be used to inspect and debug pipeline mechanics only.
