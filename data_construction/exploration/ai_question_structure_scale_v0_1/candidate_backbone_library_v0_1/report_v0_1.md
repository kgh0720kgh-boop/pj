# Candidate backbone library v0.1

Status: `candidate_non_gold_not_established`.

## Materialized scope

- Contracted candidate families: 30
- Exhaustively assigned N=300 members: 300
- Evidence tiers: recurrent=9, doubleton=7, singleton=14
- Pre-environment coverage-stress sample: 71 questions across 30 families
- Human evidence: 0
- Environment, grounding, execution, and answer recovery evaluated: no

## Frozen sampling rule

Each family receives `min(count, 1 + ceil(log2(count)))` seats. Within a family,
questions are greedily selected for equal-axis marginal coverage of fine, topology,
task, N100/new200 source slice, producer partition, record status, and alternative-graph
presence; ties use the frozen seeded SHA-256 rank. Question text and environment data
are not ranking features.

This is a coverage stress sample, not a probability sample and not a prevalence estimate.
Rare families are deliberately overrepresented.

## Frequency strata

| Stratum | Families | Source questions | Selected |
| --- | ---: | ---: | ---: |
| `singleton_1` | 14 | 14 | 14 |
| `doubleton_2` | 7 | 14 | 14 |
| `low_recurrent_3_9` | 5 | 27 | 18 |
| `medium_recurrent_10_19` | 2 | 24 | 10 |
| `high_recurrent_20_99` | 1 | 20 | 6 |
| `dominant_100_plus` | 1 | 201 | 9 |

## Interpretation boundary

The library records deterministic recurrence under one AI question-only extractor
and normalizer. Same-role contraction does not prove semantic equivalence; producer
partitions are not independent reviewers; `complete` is not correctness. The library
does not select an operator vocabulary and is not gold or modeling-ready.

The next stage may inspect environment content only for the committed representative
IDs, and must record backbone adequacy, operator realization, grounding, execution,
and answer recovery as separate outcomes.
