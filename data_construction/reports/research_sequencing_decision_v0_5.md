# Research sequencing decision v0.5

Date: 2026-08-25

## Decision

The representative environment-realization run is complete for the frozen
71-question, 30-family coverage-stress sample. The next stage is
`FREEZE_EQUIVALENCE_AWARE_OPERATOR_NORMALIZATION_BEFORE_GROUNDING`.

Do not expand question-only extraction, begin large duplicate review, select a
preserved coarse/medium/fine vocabulary, or ground the raw open graphs yet.
First test whether producer-specific split/fuse choices reduce to a stable
semantic-backbone plus environment-adapter interface under a separately frozen,
label-free equivalence contract.

## Completed representative run

The evidence was committed in this order:

1. implementation, schemas, prompts, and tests at
   `78fe487327d2fda43cc2ec79203c0a3223d1645b`;
2. the exact plan while every planned output was absent at
   `2e8f6a2c8ee2eb7a3d8a175ea7b8d7f94213175c`;
3. 71 pinned full-table/table-link-closure views and E1 packets at
   `1ff98d3a9cbd7cdd7ae5c7de6676818a57481ec7`;
4. 71 E1 assessments, a hash-only E1 sidecar, and E2 packets at
   `c3ed836c633859d3575bab1f29d7cf0274df6780`; and
5. 71 E2 realizations, 71 five-signal in-progress outcomes, 285 passing checks,
   metrics, report, and exposure ledger at
   `4d4d86885a5294af40653a48cbf12346f699db53`.

Both E1 and E2 were partition-authored in fresh contexts. E2 packets contained
only hashes of the separately committed E1 records, not E1 judgments or
rationales. The four partitions are not independent reviewers. Human evidence
remains zero.

## Scientific result

- E1: 64 `adequate`, five `partially_adequate`, two `indeterminate`, zero
  `inadequate`.
- E2: 71 `available`, zero partial/unavailable/indeterminate; 93 candidates for
  72 primary-or-alternative variants.
- Mappings: 278 one-to-one, four many-to-one, one one-to-many.
- Slot modalities: linked-document text=95, table row/cell=90, question
  literal=72.
- Open candidate multiplicity: 49 questions have one candidate and 22 have
  two.
- The generated all-candidate structural metric finds multiple unlabeled
  profiles in 17/30 families.

The last number is especially sensitive to alternative enumeration: 16 of
those 17 families contain at least one question whose own alternative
candidates contribute different raw profiles, and four contain only one
selected question. On the primary `candidate1` projection, 67/71 questions
have zero node/edge/depth-count delta from the target backbone. These are
sensitivity diagnostics, not a preferred-candidate or equivalence claim.

These counts are diagnostic, not prevalence or accuracy. The sample
overrepresents rare families, the records are AI-authored, and grounding,
execution, and answer recovery remain unmeasured.

## Why exact raw-graph recurrence is not the next criterion

Granularity varies sharply by producer partition. Partition-level candidate
counts are 36, 19, 21, and 17; environment-extension-node counts are 95, 2,
47, and 0. All 18 records in the first E2 partition received two candidates,
while none of the 17 records in the fourth did. This is compatible with the
open prompt, but it means raw node count, candidate multiplicity, and exact
unlabeled profile recurrence conflate question structure with authoring style.

At the same time, 278/283 mappings are one-to-one and 70/93 candidates have
zero node/edge/depth-count delta from the target semantic graph. Together these
observations motivate, but do not prove, a common layered representation:

1. retain the question-derived semantic DAG as the stable obligation layer;
2. represent table/document access through typed unresolved slots and optional
   environment-extension subgraphs; and
3. treat valid split/fuse alternatives as equivalent only under explicit,
   loss-aware rules.

The correct hypothesis is therefore not yet “one exact executable DAG fits
all questions.” It is “a common semantic interface may admit a bounded family
of environment adapters.”

## Exact next task

Before cross-record label induction or any grounding run:

1. Implement and test a new normalization tool and schemas without modifying
   the committed representative-run contracts or outputs.
2. Freeze and commit a versioned normalization plan while every normalized
   output is absent. Bind it to the 93 candidates, 72 target variants, exact
   E2 artifact hash, and producer routing.
3. Give the normalizer a structural-only projection: target semantic topology,
   operator adjacency, semantic-to-operator mappings, operator roles, slot
   modality/cardinality, variation axes, and opaque IDs. Exclude question text,
   raw table/document content, factual answers, E1 status/rationale, operator
   labels/descriptions, and old candidate vocabularies.
4. Define at least two separate signatures:
   - a semantic quotient that verifies coverage/dependency preservation while
     abstracting permitted one-to-one/one-to-many/many-to-one split/fuse
     choices; and
   - an environment-adapter signature that retains source modalities,
     extension placement, and fused-versus-explicit access information.
   The representation must be reversible to the retained raw candidate and
   must never quotient referent identity, cardinality/tie semantics, output
   arity, or table-versus-linked-document modality. Alpha-renaming,
   independent-node ordering, transitive-reduction differences, and
   semantics-preserving access-node split/fuse are the only initial
   equivalence candidates. Any split/fuse whose tool-level equivalence depends
   on grounding remains `provisionally_equivalent`.
5. Compare candidate **sets** within each question, then compare normalized
   sets within each multi-question family. Do not use `candidate1` as a claim
   of preferred truth, because no E2 record selected a preferred candidate.
6. Precommit and report producer-partition stratification. A reduction in raw
   profile count is not sufficient if normalized signatures remain partition
   predictive.
7. Freeze stopping branches before materialization: either proceed to a
   provisional, explicitly non-final operator-adapter contract for grounding,
   or revise the normalization contract in a new version when split/fuse loss,
   family instability, or partition sensitivity remains material.
8. Precommit a minimal crossed-author sensitivity branch before normalized
   results are inspected: if producer sensitivity cannot be separated from the
   fixed question mix, reuse a frozen 16-question subset (four from each
   existing partition, including all seven E1 challenge records) with two new
   fresh-context AI authors covering every selected question. This is a
   confound diagnostic, not duplicate human review or majority voting, and it
   must use no fresh reserve or locked-evaluation IDs.

This task is deterministic structural analysis, not human review and not
operator-label taxonomy induction. It uses the already environment-exposed 71
questions as exploratory development evidence. It must not consume fresh
reserve or locked-evaluation questions. A later held-out environment sample may
be allocated only after the normalization and provisional-adapter contracts are
frozen.

## Evidence boundary

The completed run establishes no semantic gold, human agreement, final
operator vocabulary, exact common graph, grounding success, execution success,
answer accuracy, or modeling readiness. Outcome v0.2 truthfully leaves the
last three signals `not_evaluated`, and later downstream results must not
overwrite E1 or E2.
