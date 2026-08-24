# Representative environment realization v0.1

Status: `ai_exploratory_non_human_non_gold_first_two_signals_evaluated`.

## Scope

- Selected questions: 71
- Candidate families covered: 30
- E1 backbone-adequacy records: 71
- E2 open-realization records: 71
- Five-signal outcome records: 71 (`in_progress`)
- Human evidence: 0
- Final operator vocabulary selected: no
- Grounding, execution, answer recovery evaluated: no

## E1 backbone adequacy

| Status | Questions |
| --- | ---: |
| `adequate` | 64 |
| `partially_adequate` | 5 |
| `inadequate` | 0 |
| `indeterminate` | 2 |

Primary-nonadequate records rescued by an adequate preserved alternative: 0.

## E2 open environment-aware realization

| Status | Questions |
| --- | ---: |
| `available` | 71 |
| `partial` | 0 |
| `unavailable` | 0 |
| `indeterminate` | 0 |

Realization candidates per question: 1→49, 2→22

## Backbone-to-operator structural observations

Mapping kinds: `many_to_one`=4, `one_to_many`=1, `one_to_one`=278.

Operator-node roles: `backbone_realization`=284, `environment_extension`=144.

Families with more than one unlabeled operator structural profile: 17/30.

## Precommitted targeted recheck triggers

- `source_backbone_uncertain`: 27
- `rare_singleton_or_doubleton_family`: 28
- `e1_non_adequate_or_indeterminate`: 7
- `e2_partial_unavailable_or_indeterminate`: 0
- `multiple_realization_candidates`: 22
- `unsupported_backbone_nodes`: 0

## Interpretation boundary

E1 was committed before E2. E2 packets used record-local free operator labels
and ungrounded slots, excluded preserved coarse/medium/fine proposals, and
required fresh authors to attest the specified nonexposure conditions.
The resulting structural and adequacy observations are AI-authored diagnostic
evidence, not semantic gold, human agreement, or a final operator ontology.
Environment rows and linked documents can naturally contain answer-bearing facts,
but official answer/reference fields and traces were not projected into the views.
The dataset-provided question-to-table binding and full link closure were supplied;
table retrieval was not evaluated. Record-local label recurrence was not analyzed.
The rarity-overweighted sample is not a probability sample, so counts are not
population prevalence estimates. Structural-profile hashes are label-free
descriptors, not proofs of exact graph isomorphism or a common executable graph.
Exact graph identity is not treated as the only valid realization criterion.

Grounding, execution, and answer recovery remain separate future stages. Their
future results must not overwrite these upstream assessments.
