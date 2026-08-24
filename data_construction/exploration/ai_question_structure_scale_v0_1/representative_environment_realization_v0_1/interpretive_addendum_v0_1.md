# Representative environment realization interpretive addendum v0.1

Date: 2026-08-25

## Why this addendum exists

The generated `report_v0_1.md` records the precommitted descriptive metrics.
This addendum records the interpretation needed before those metrics are used
to choose an operator vocabulary or a grounding experiment. It does not alter
the committed E1/E2 records, outcomes, checks, metrics, or run manifest.

## Result in one sentence

The experiment supports a reusable **semantic-backbone plus environment-adapter
layering hypothesis**, but it does not establish one common exact operator DAG,
a final operator vocabulary, grounding success, or executability.

## What was observed

- All 71 selected questions and all 30 frozen candidate families received full
  pinned table and table-link-closure views. The views excluded official answer
  and trace fields.
- E1 classified 64 records as `adequate`, five as `partially_adequate`, and two
  as `indeterminate`; none was `inadequate`. These are AI-authored instance
  judgments in a rarity-overweighted diagnostic sample, not accuracy or
  prevalence estimates.
- The five partial records contain ten required-change instances:
  `revise_referent`=4, `revise_answer_spec`=4, `add_obligation`=1, and
  `split_obligation`=1. The two indeterminate records retain unresolved
  referent ambiguity.
- E2 produced 93 ungrounded realization candidates for 72 target variants
  across 71 questions. Every question was `available`, every target variant was
  `fully_realized`, and no candidate reported an unsupported backbone node.
- Of 283 semantic-to-operator mappings, 278 are one-to-one, four are
  many-to-one, and one is one-to-many. Across 321 unique operator nodes, 284
  have a backbone-realization role and 144 have an environment-extension role;
  107 nodes have both roles.
- Seventy of 93 candidates have the same node, edge, and depth counts as their
  target semantic graph. The remaining deltas include fused as well as split
  realizations, so zero delta does not mean storage access disappeared: access
  may instead be represented by an unresolved slot or fused into a mapped
  node.
- The generated all-candidate metric reports more than one unlabeled structural
  profile in 17 of 30 families. Restricting the diagnostic to `candidate1` for
  the primary variant and to the 16 families represented by at least two
  selected questions leaves eight families with more than one profile. Neither
  number is exact graph-isomorphism evidence or a population estimate.
- Sixteen of the 17 all-candidate heterogeneous families contain at least one
  question whose own alternatives contribute multiple raw profiles, and four
  of the 17 contain only one selected question. On the primary `candidate1`
  projection, 67/71 questions have zero node/edge/depth-count delta from the
  target graph. This further limits any interpretation of `17/30` as
  cross-question environment heterogeneity.

## The decisive confound

Raw granularity is strongly associated with the producer partition:

| E2 producer partition | Records | Candidates | Records with multiple candidates | Environment-extension nodes | Mean operator-node delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `e2_author_partition_01` | 18 | 36 | 18 | 95 | +0.972 |
| `e2_author_partition_02` | 18 | 19 | 1 | 2 | +0.105 |
| `e2_author_partition_03` | 18 | 21 | 3 | 47 | -0.143 |
| `e2_author_partition_04` | 17 | 17 | 0 | 0 | 0.000 |

The single additional variant in the source occurs in partition 02; most other
multiple-candidate records express optional split/merge choices. The prompt
intentionally allowed those choices, and the four producers are work
partitions rather than independent reviewers. Therefore candidate multiplicity,
extension-node counts, raw node expansion, and the 17/30 family-profile metric
cannot be read as intrinsic properties of the questions alone.

E1 also varies by producer partition: partition 01 marked all 18 adequate,
while partitions 02, 03, and 04 produced respectively one, three, and three
non-adequate-or-indeterminate records. The samples differ, so this is not proof
of a producer effect, but it prevents treating the 64/71 headline as calibrated
semantic accuracy.

## What the experiment establishes

1. The frozen workflow can preserve question-only semantics, actual environment
   context, open operator realization, grounding, execution, and answer
   recovery as separate signals.
2. Under an intentionally expressive open notation, every sampled target
   semantic variant could be covered by at least one ungrounded operator DAG.
3. The dominant mapping pattern preserves the semantic backbone and attaches or
   fuses environment access around it. This makes a two-layer common
   representation plausible enough to test.
4. Partial or indeterminate E1 judgments coexist with available E2 topologies,
   demonstrating that realizability does not repair or overwrite semantic
   adequacy.

## What it does not establish

- `71/71 available` is an expressivity result conditioned on a permissive
  notation and validator; it is not execution success or proof that the data
  contains an answer.
- The one-to-one mapping majority is partly induced by the mapping contract and
  cannot alone prove a natural universal decomposition.
- Raw operator labels are record-local. Their recurrence has not been analyzed
  and no label is a vocabulary item.
- No operator candidate is grounded, compiled to IR v0.2, executed, or compared
  with a reference answer.
- No human evidence, gold program, common exact DAG, final ontology, or
  modeling-ready corpus is produced.

## Consequence for sequencing

Grounding the raw candidates now would silently privilege producer-specific
split/fuse styles. The next stage should first freeze an equivalence-aware,
label-free normalization contract. It should be a reversible two-layer
quotient rather than destructive canonicalization: preserve a semantic
obligation/mapping kernel separately from modality, cardinality/tie, output
arity, filter/join/aggregate/order, and access effects. It should retain slot
modalities and extension placement, compare alternative candidates as sets
rather than as exact graph matches, and report every result by producer
partition. Equivalences that cannot be justified without grounding stay
provisional.

Because the current question assignment and producer assignment are not
crossed, normalized partition differences alone still cannot identify a causal
author effect. The normalization plan should therefore precommit a small
crossed-author branch before results are inspected: if sensitivity remains
unresolved, freeze 16 already exposed questions (four from each partition,
including all seven E1 challenge cases) and have two new fresh-context AI
authors realize all 16. This is a confound diagnostic, not majority review, and
does not consume fresh reserve questions. Only after normalized question-level
candidate-set overlap is stable should a provisional operator adapter be
frozen for representative grounding and execution.

Large duplicate human review is not the active gate. Later human or AI rechecks
may target the seven non-adequate-or-indeterminate E1 records or suspicious
normalization/execution cases, but they must not be counted as completed by
this run.
