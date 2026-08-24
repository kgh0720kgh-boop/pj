# AI question-structure scale exploration v0.1

This namespace implements the scale-first follow-up selected after the separate
30-question AI diagnostic. It asks whether recurrent question-only semantic
backbones and topology shapes appear across a cumulative 100-question pool.

The prior human Phase A1 contract and diagnostic run remain byte-preserved. This
exploration does not complete them and does not create human evidence or gold
annotations.

The N=100 pool is an exact cumulative prefix under the existing pinned-dev seed:
the original 30 question-only views are the exact first 30 records, 70 new
questions are added, and 3,266 official-dev questions remain unexposed and
unallocated. The existing split manifest is unchanged.

Raw model records contain free-text descriptions plus a deliberately small,
frozen provisional semantic-role vocabulary with an `OTHER` escape hatch.
Family IDs and signatures are never supplied by the model. Deterministic code
derives exact labeled-DAG, same-role-contracted, topology-only, and answer-task
signatures after validation.

All findings are descriptive under the frozen extractor and normalizer. They do
not establish semantic correctness, natural-language universality, a common
executable graph, operator-vocabulary adequacy, grounding success, or answer
accuracy.

Run 001 is complete with 100/100 structurally valid records. It yields 23 fine
labeled families, 17 same-role-contracted families, six topology shapes, and 38
task signatures. At the contracted level, singleton mass is 0.09 and
first-30-to-new-70 transfer is 50/70. The precommitted decision is
`EXPAND_UNCHANGED_TO_N300`.

The primary metrics and report remain unchanged. A separately versioned
post-hoc sensitivity audit records that all five recurring-new contracted
families are confined to one producer partition, with zero cross-partition
recurrence. It also separates raw branch/join counts (5/6) from
transitive-reduced counts (0/1), and records dominant-family growth from 46 to
62 questions after same-role contraction. Therefore the N=300 decision is a
conservative next measurement, not confirmation that those families are
semantically novel.

The next run must freeze a cumulative N=300 pool with this N=100 as its exact
prefix, add 200 newly eligible questions to a new exposure-ledger version, keep
the prompt/schema/role set/normalizer unchanged, and distribute committed
positions across producer contexts rather than using contiguous worker blocks.
