# Research sequencing decision v0.4

Date: 2026-08-25

## Decision

The cumulative N=300 candidate-backbone library and its pre-environment
representative sample are frozen and materialized. The active next stage is a
representative environment-realization contract and run, not additional
question-only scaling and not full duplicate human review.

This advances the operational branch
`FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_ENVIRONMENT_REALIZATION`
without claiming that the candidate families are semantically correct, gold,
universally saturated, executable, or modeling-ready.

## Materialized result

- All 300 cumulative question-only records belong to exactly one of 30 full
  contracted-signature families; no post-hoc semantic family merge was made.
- The evidence tiers are 9 recurrent families, 7 doubletons, and 14
  singletons.
- Each family preserves its canonical contracted graph, N100/new200 frequency,
  producer-partition and ten-question-block support, complete member list,
  fine/topology/task crosswalks, and uncontracted role/transition composition.
- A deterministic coverage-stress sample contains 71 unique questions and all
  30 families. Its ordered-ID SHA-256 is
  `5403debe2cbe9c7f55ded0a01b49d7c42bf03e53a71350efe269bbd3c0bdcb2e`.
- The library has 102 deterministic passing checks: one bundle check, 30
  family checks, and 71 representative-selection checks.
- Human evidence remains 0. Environment realization, grounding, execution,
  and answer recovery remain not started.

The implementation was committed before the plan. The plan was then committed
while every planned output was absent, and only afterward were the library and
sample generated. The implementation/source commit is
`66bd21948d5269f75d5f816e3f7cfba3941229d5`, the freeze-plan commit is
`f3ac5c47527b46234543d89bc1d7d8034f2723f1`, and the materialization commit is
`80ce8c2e992e56b1175cf144ff52b0765755dcd2`.

## Sampling interpretation

For a family with `n` questions, the quota is
`min(n, 1 + ceil(log2(n)))`. Within each family, greedy equal-axis marginal
coverage uses fine signature, topology signature, task signature, N100/new200
slice, producer partition, record status, and alternative-graph presence.
Ties use the frozen seeded SHA-256 rank.

This is a deterministic `coverage_stress_sample`, not a probability sample.
It deliberately overrepresents rare families and cannot estimate their
population prevalence. The axes are correlated, N100/new200 slice and producer
partition are partly confounded, producer partitions are not independent
reviewers, and status/alternative presence are AI-generated diagnostics.

Question text is present in the hash-bound source records but is not a ranking
feature. Table identity/schema/rows/cells, linked-document identity/text,
factual answers, traces, grounding, operator proposals, and downstream outcomes
are forbidden selection inputs. The builder enforces the frozen question-only
record schema and input allowlist. The broader claim that nobody inspected
environment material remains procedural and is not machine-authenticated.

## Separate future outcomes

The v0.1 environment-outcome schema freezes five independently scored signals:

1. candidate-backbone adequacy;
2. environment-aware operator realization;
3. grounding;
4. execution;
5. answer recovery.

Execution success does not prove backbone adequacy, execution failure does not
prove backbone inadequacy, and answer recovery does not overwrite upstream
assessments. The schema also prevents internally contradictory lifecycle,
execution, and answer-comparison records. A per-question outcome cannot
establish family-level semantic correctness.

## Exact next task

Before inspecting row/cell values or linked-document contents for this 71-ID
realization stage, freeze a versioned input-view and realization protocol that:

1. is bound to the committed representative ID order and pinned official
   HybridQA source identities;
2. exposes only the environment content needed for realization and keeps
   factual answers, official traces, historical graphs, execution outcomes,
   and old candidate operator proposals out of the authoring view;
3. does not silently adopt the preserved coarse/medium/fine vocabulary as the
   final operator ontology;
4. records open environment-aware operator realizations and candidate-backbone
   adequacy at the selected-question instance level;
5. keeps grounding, execution, and answer recovery unscored until their own
   versioned inputs and procedures are invoked; and
6. preserves alternative realizations rather than treating exact graph match as
   the only correctness target.

After that contract is committed, materialize sanitized pinned environment
views for exactly the 71 selected IDs and begin representative realization.
The current blocker is therefore
`REPRESENTATIVE_ENVIRONMENT_REALIZATION_NOT_STARTED`, not missing human review.
