# Scale-first research sequencing decision v0.2

Decision date: 2026-08-24
Current decision: `UNDECIDED_NEEDS_SCALE_EVIDENCE`

## Decision

The completed 30-question AI shadow run is reinterpreted as a direction-finding
experiment. It showed that an end-to-end question-only structure pipeline is
mechanically viable and that a recurrent abstract semantic backbone is a
plausible hypothesis. It did not establish correctness, human agreement, a
universal topology, or an executable graph.

The active research sequence therefore changes from full human double review of
the first ten questions to scale-first AI exploration over cumulative question
pools. The preserved v0.1 human calibration contract remains valid historical
work, but it is deferred and is no longer the active gate.

The immediate experiment is cumulative N=100: the existing 30 question-only
views remain the exact prefix and 70 pinned-official-dev questions are added
under the same deterministic seed. The extractor, provisional semantic roles,
normalizer, signature definitions, and metrics are frozen before any of the new
70 records are generated.

## Why scale is the higher-value next measurement

The present research question is not whether two people can use the annotation
form identically. It is whether HybridQA questions exhibit a compact reusable
semantic structure and whether that structure can later be realized as
environment-specific executable graphs.

Increasing question coverage directly measures:

- recurrence of labeled semantic DAGs and unlabeled topology shapes;
- the fraction of new questions covered by structures seen in the first 30;
- the rate at which genuinely new families continue to appear;
- how much novelty is only a same-role split/merge encoding difference;
- whether a small provisional role set needs repeated `OTHER` escape cases; and
- which frequent and rare structures should be grounded and executed later.

Full duplicate review of every question is not on the critical path. A second AI
pass or human audit is reserved for a small, stratified set of novel, rare,
uncertain, retried, high-frequency, or execution-suspicious cases.

## Separation of research objects

The hierarchy remains:

```text
question
  -> question-only semantic backbone
  -> environment-aware operator realization
  -> concrete grounding
  -> executable graph
  -> execution and answer recovery
```

The N=100 experiment covers only the first arrow. It does not expose table or
linked-document evidence, answer text, operator proposals, grounding, execution
traces, or historical graphs to the extractor.

## Exposure and reserve policy

The released `split_manifest_v0_1.json` remains unchanged at 30
`annotation_schema_pilot` questions and zero train/dev/locked-eval allocations.
The scale experiment uses a separate exploratory manifest and assigns no corpus
role.

Every question processed by AI is permanently ineligible for a future claim of
unseen evaluation. The N=100 selection leaves 3,266 official-dev questions
unexposed and unallocated. Their question text is not materialized in the pool.
Any later N=300 or N=1,000 expansion requires a new versioned selection and
exposure update.

## Measurement contract

The model emits no cluster or family ID. Deterministic code derives four
ID-invariant signatures:

1. exact transitively reduced labeled semantic DAG;
2. the same graph after deterministic same-role linear contraction;
3. exact unlabeled topology shape; and
4. semantic DAG plus answer kind and cardinality.

Each level reports observed families, cumulative and block novelty, top-k
coverage, singleton/doubleton counts, singleton mass, exact rarefaction,
first-30-to-new-70 transfer, and representative examples. Role escape, uncertainty,
alternatives, branch/join, depth, and role-transition frequencies are reported
separately.

N=100 can support only a statement that a curve is flattening or is not
flattening under this frozen extractor. It cannot establish universal
saturation.

## Decision after N=100

Expand unchanged to N=300 when the N=100 results still contain material
recurring new families, high singleton mass, a material `OTHER` rate, or a
clearly non-flattening curve. Otherwise freeze a candidate semantic-backbone
library and composition rules, select frequency- and rarity-stratified
representatives before seeing execution outcomes, and begin environment-aware
realization.

At every later stage, semantic-plan correctness, grounding correctness,
execution success, and final-answer recovery remain separate signals.
