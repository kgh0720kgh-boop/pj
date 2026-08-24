# Cumulative N=300 question-only semantic-backbone exploration

Evidence class: AI-generated exploratory, non-human, non-gold.

## Mechanical integrity

- Valid records: 300/300
- Frozen N=100 prefix preserved byte-for-byte: `true`
- New records: positions 101–300 under the frozen schema, prompt, roles, and normalizer.

## Four frozen signature resolutions

| Signature | N300 families | Singleton mass | Top-10 coverage | N100→new200 transfer | New families |
| --- | ---: | ---: | ---: | ---: | ---: |
| fine_semantic_dag | 39 | 0.067 | 0.863 | 0.900 | 16 |
| contracted_semantic_dag | 30 | 0.047 | 0.913 | 0.915 | 13 |
| topology_shape | 10 | 0.010 | 1.000 | 0.970 | 4 |
| task | 70 | 0.130 | 0.700 | 0.805 | 32 |

Fine, contracted, topology, and task results are reported separately. Contracted recurrence is a split/merge sensitivity view and is not semantic equivalence.

## Normalized graph profile

- Transitive-reduced mean edges: 1.393
- Transitive-reduced branches: 1/300
- Transitive-reduced joins: 6/300
- Raw declared branches/joins (sensitivity only): 6/11

## New-family producer support

- N100-unseen contracted families: 13
- Recurring across at least two new producer partitions: 2
- Material trigger-qualified families: 1

Producer partitions are generation contexts, not independent human reviewers. Cross-partition support is a robustness diagnostic, not proof of semantic novelty.

## Precommitted N=1,000 decision

Decision: `FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_ENVIRONMENT_REALIZATION`.
Trigger values: `{"at_least_2_material_cross_partition_new_contracted_families": false, "cumulative_OTHER_question_rate_above_0_05": false, "cumulative_contracted_singleton_question_mass_above_0_05": false, "tail_50_sequential_contracted_novelty_above_0_10_with_at_least_2_new_families": false}`

The trigger is an operational scale decision frozen before positions 101–300 were generated. Post-hoc style audits, semantic cluster merges, alternate normalizers, or threshold changes cannot replace it.

## Interpretation boundary

These metrics describe recurrence, transfer, partition support, and normalized graph shape under one frozen AI extractor. They do not establish semantic correctness, human agreement, gold labels, universal saturation, an executable graph, grounding, or answer accuracy.
