# Research sequencing decision v0.3: cumulative N=300 result

Date: 2026-08-24

Current operational decision:
`FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_ENVIRONMENT_REALIZATION`

Evidence class: `ai_exploratory_non_human_non_gold`. Human evidence remains
zero.

## What was completed

The cumulative question-only exploration now contains 300 structurally valid
records under one frozen prompt, record schema, provisional role set, and
deterministic normalizer. The committed N=100 record file is the exact byte
prefix of the cumulative N=300 file. Positions 101--300 were assigned
round-robin across five producer contexts, 40 questions per context, so
committed order is not a contiguous worker block. All 300 records pass schema,
question/order/hash/cue, forbidden-key, reference, root/sink, and DAG checks.

The cumulative signature results are:

| Resolution | Families | Singleton question mass | Top-10 coverage | N100-to-new200 transfer |
| --- | ---: | ---: | ---: | ---: |
| Fine labeled semantic DAG | 39 | 0.0667 | 0.8633 | 0.9000 |
| Same-role-contracted semantic DAG | 30 | 0.0467 | 0.9133 | 0.9150 |
| Unlabeled topology shape | 10 | 0.0100 | 1.0000 | 0.9700 |
| Task signature | 70 | 0.1300 | 0.7000 | 0.8050 |

The contracted view has 13 families absent from N=100. Three recur in the new
200, two recur across at least two new producer partitions, and one satisfies
the precommitted material-support rule. The final 50 questions contain five
sequentially new contracted-family questions, a novelty rate of exactly 0.10.
The cumulative records contain 94 `uncertain` questions, zero questions using
`OTHER`, and one question with an alternative graph.

## Precommitted N=1,000 decision

The N=300 plan was committed before any positions 101--300 model output. It
required expansion to N=1,000 when **any** of four conditions was true. All four
were false:

| Trigger | Required | Observed | Result |
| --- | ---: | ---: | --- |
| Contracted singleton question mass | greater than 0.05 | 0.0467 | false |
| `OTHER` question rate | greater than 0.05 | 0.0000 | false |
| Final-50 contracted novelty with at least two new families | greater than 0.10 | 0.10 with five | false |
| Material cross-partition new contracted families | at least two | one | false |

The strict inequalities matter: equality at 0.10 does not trigger the tail
condition. These thresholds are frozen design choices, not universal
statistical laws. Post-hoc threshold changes, semantic cluster merging, or a
different normalizer cannot replace this primary operational decision.

## Interpretation

The result supports moving from repeated question-only extraction to testing
how a compact candidate backbone system is realized in the actual HybridQA
environment. Most new questions reuse an N=100 family, and the contracted
singleton mass falls below the precommitted continuation threshold. Spending
the next unit on 700 more records with the same extractor is therefore not the
selected branch.

This does **not** establish universal semantic saturation. Fine signatures
still have 6.67% singleton mass, task signatures have 13%, and same-role
contraction can merge semantically distinct referent hops. Producer-context
profiles also vary: mean primary node count ranges from 2.0 to 2.825 and
uncertainty rate from 0.15 to 0.525 in the five new partitions. These are
sensitivity warnings, not independent-reviewer disagreement measurements.

The normalized graph evidence is similarly narrow. After transitive reduction,
one of 300 questions branches and six join; raw declared dependencies contain
six branches and eleven joins. This describes the frozen extractor's output,
not the true frequency of branching reasoning and not an executable graph
claim.

## Exact next task

Before reading environment contents or execution outcomes, create and commit a
versioned candidate-backbone/library-and-sampling contract. Then build the
library deterministically from the frozen N=300 records and signatures.

The contract must:

1. retain all 30 observed contracted families without post-hoc semantic merging;
2. preserve each family's canonical contracted graph, frequency, N=100/new200
   counts, producer-partition and ten-question-block support, member question
   IDs, and fine/topology/task signature crosswalks;
3. distinguish recurrent, doubleton, and singleton evidence rather than calling
   every family established;
4. record observed composition evidence separately from family identity, and
   explicitly deny that same-role contraction proves semantic equivalence;
5. precommit a deterministic frequency-and-rarity-stratified representative
   selection before table/document content, grounding, execution, or answers
   are inspected; and
6. define separate outcome fields for backbone adequacy, environment/operator
   realization, grounding, execution, and final-answer recovery.

Only after that contract and representative IDs are committed should the
selected questions receive environment-aware operator graphs. Human duplicate
review remains deferred; it is not a prerequisite for this engineering and
coverage test, and its evidence count remains zero.

## Claims that remain forbidden

The N=300 result does not establish semantic correctness, human agreement,
gold labels, a universal topology, a common executable graph, grounding
correctness, execution success, answer accuracy, a selected operator
vocabulary, or modeling readiness. The 300 AI-processed question IDs are
excluded from future unseen-evaluation claims, while 3,066 official-dev
questions remain unexposed and unallocated.
