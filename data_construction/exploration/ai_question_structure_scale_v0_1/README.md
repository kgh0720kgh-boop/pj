# AI question-structure scale exploration v0.1

This namespace implements the scale-first follow-up selected after the separate
30-question AI diagnostic. It asks whether recurrent question-only semantic
backbones and topology shapes appear across cumulative 100- and 300-question
pools.

The prior human Phase A1 contract and diagnostic run remain byte-preserved. This
exploration does not complete them and does not create human evidence or gold
annotations.

The N=300 pool is cumulative under the existing pinned-dev seed. The original
30 views are the first 30 records, the frozen N=100 records are preserved as an
exact byte prefix, and positions 101--300 add 200 newly eligible questions.
After completion, 3,066 official-dev questions remain unexposed and
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

The cumulative N=300 extension is now complete with 300/300 structurally valid
records and a byte-exact N=100 prefix. It yields 39 fine families, 30
same-role-contracted families, 10 topology shapes, and 70 task signatures.
Contracted singleton mass is 0.0467, N100-to-new200 transfer is 0.915, top-10
coverage is 0.9133, and `OTHER` use is zero. The final 50-question contracted
novelty rate is exactly 0.10; one new family meets the material
cross-partition-support rule.

All four precommitted N=1,000 triggers are false. The operational decision is
`FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_ENVIRONMENT_REALIZATION`.
This is not universal saturation or semantic correctness. The next task is to
freeze a versioned library-and-representative-sampling contract, retain all 30
contracted families with their fine/topology/task crosswalks and evidence
strength, and commit frequency/rarity-stratified representative IDs before
inspecting environment or execution outcomes.
