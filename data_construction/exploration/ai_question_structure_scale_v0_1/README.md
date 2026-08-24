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
