# N=100 question-only semantic-backbone exploration

Evidence class: AI-generated exploratory, non-human, non-gold.

## Mechanical result

- Valid records: 100/100
- Status counts: `{"complete": 71, "uncertain": 29}`
- Provisional `OTHER` role: 0/100 questions
- Uncertainty marked: 29/100 questions
- Alternative graph present: 1/100 questions

## Recurrence at four resolutions

| Signature | Families | Singleton mass | Top-10 coverage | New-70 transfer from first 30 |
| --- | ---: | ---: | ---: | ---: |
| fine_semantic_dag | 23 | 0.130 | 0.870 | 0.671 |
| contracted_semantic_dag | 17 | 0.090 | 0.930 | 0.714 |
| topology_shape | 6 | 0.020 | 1.000 | 0.971 |
| task | 38 | 0.250 | 0.690 | 0.629 |

The four resolutions must be interpreted together. Fine labeled recurrence is strict; contracted recurrence tolerates same-role linear split/merge; topology recurrence ignores semantic labels; task recurrence additionally includes answer kind and cardinality.

## Graph profile

- Mean nodes: 2.490
- Mean edges: 1.540
- Mean depth: 2.480
- Branch questions: 5/100
- Join questions: 6/100

## Scientific boundary

This run measures recurrence and curve shape under one frozen AI extractor and deterministic normalizer. N=100 may show that a curve is flattening or not flattening; it cannot establish universal saturation. It evaluates no factual answer, environment realization, grounding, execution, human agreement, or semantic correctness.

The next decision is based on the new-70 novelty curves, singleton mass, `OTHER` rate, and split/merge sensitivity: expand unchanged to N=300 if material recurring families are still appearing; otherwise freeze a candidate backbone library and begin representative environment realization while preserving an untouched reserve.
Precommitted N=100 decision: `EXPAND_UNCHANGED_TO_N300`.
