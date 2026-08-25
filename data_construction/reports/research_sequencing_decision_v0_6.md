# Research sequencing decision v0.6

Date: 2026-08-25

## Decision

The reversible operator-equivalence normalization v0.1 and its precommitted
crossed-author producer diagnostic are complete. The frozen sensitivity
criteria failed, so the selected branch is:

`REVISE_EQUIVALENCE_NORMALIZATION_CONTRACT`

Do not begin grounding, execution, answer recovery, cross-record operator-label
induction, or provisional vocabulary selection. Create normalization v0.2 as a
new version; do not overwrite any v0.1 plan, author record, projection,
normalization, metric, report, or manifest.

## Frozen sequence

Normalization v0.1 was committed in this order:

1. implementation/schema/tests: `c372ef4b43a88b80d85f69359197bdedd3c40e61`;
2. exact plan while all normalized outputs were absent:
   `83428b9698546de054db672e72dbae880ef4c1ac`;
3. 93 materialized normalizations: `a9d3272c6cef4f411bf8f124159a634920c0571e`.

The frozen fallback was then committed in this order:

1. sensitivity implementation/schema/protocol/tests:
   `16a864450af38458eeea4d6aced00ecf7b3e593f`;
2. plan while author packets and outputs were absent:
   `c00bb6f573b11136d84c3cf4216984813a9930dd`;
3. two 16-record packets: `144de6b3062ad29cc6c2ca43ad9579bca74b94a8`;
4. isolated author histories ending at
   `8dcf5d5587132e0cc8c3668d67934543e0e5ff16` and
   `dfc8a8097aac8d2ca24308a1b7889bfaf23eeaf4`;
5. combined checks/normalizations/comparisons/metrics:
   `95b4b1356a2cbe050d4bf89a259a4c7340930558`.

Both authors received all 16 identical selected views in separate fresh
contexts and were instructed not to inspect prior E2 records, normalization
outputs, E1 content, preserved vocabularies, or each other's packet/output.
Isolation is procedural rather than machine-authenticated. No fresh reserve or
locked-evaluation ID was used.

## Normalization v0.1 result

- original candidates: 93 across 71 questions and 72 target variants;
- equivalent: 89;
- provisionally equivalent: 4;
- not equivalent: 0;
- reversible projection loss: 0;
- semantic quotient signatures: 39;
- environment-adapter signatures: 19;
- multi-question families with unstable semantic sets: 6/16.

The fixed original question/producer assignment made producer attribution
impossible, activating the precommitted crossed-author fallback before
grounding.

## Crossed-author result

- selected questions: 16, four per original E2 partition;
- selection composition: all seven E1 challenge cases plus nine adequate
  controls;
- AI authors: 2, every author covering every question;
- author records: 32;
- candidates: 34;
- semantic-set exact matches: 16/16;
- mean semantic-set Jaccard: 1.0;
- adapter-set exact matches: 0/16;
- mean adapter-set Jaccard: 0.0;
- distinct adapter signatures: 25;
- normalized status: 20 equivalent, 9 provisionally equivalent, 5 not
  equivalent;
- challenge/control semantic-set exact matches: 7/7 and 9/9.

The five not-equivalent candidates are partial realizations from one author;
they fail target coverage, dependency, and semantic-output preservation. The
nine provisional cases expose one-to-many split, extra-dependency, or
many-to-one fusion sensitivity. The frozen requirements of zero
not-equivalent candidates and at most 10% provisional candidates therefore
fail. Adapter signatures are completely author-separated under v0.1's exact
signature even though the target-anchored semantic quotient matches.

## Interpretation

The 16/16 semantic-set match is not sufficient evidence for a stable common
operator interface. In v0.1 the semantic quotient is anchored to the target
backbone after checking candidate coverage/dependencies. Consequently a partial
candidate can retain the same target quotient hash while its equivalence status
correctly says `not_equivalent`. Future comparisons must not count that hash as
a full semantic-set match.

Conversely, adapter exact mismatch of 0/16 shows that the current adapter hash
is too producer-sensitive to serve directly as a reusable adapter type. It
conflates typed modality/cardinality requirements with exact split/fuse node
counts and placement choices. This does not show that no common adapter
interface exists; it shows that v0.1 has not identified one.

The evidence remains AI exploratory, non-human, and non-gold. It establishes no
grounding success, execution success, answer accuracy, final vocabulary,
semantic correctness, or modeling readiness.

## Exact next task: normalization v0.2

Use only the already exposed 93 original candidates and 34 crossed-author
candidates. Consume no fresh question, answer, trace, grounding, or execution
evidence.

1. Add a separately versioned v0.2 schema/tool/test bundle; keep all v0.1 files
   immutable.
2. Before producing v0.2 outputs, freeze a plan bound to all 127 candidate
   records, both v0.1 run manifests, producer identities, and stopping rules.
3. Make the semantic representation candidate-derived: encode supported
   semantic nodes, missing nodes, mapped output coverage, and dependency
   preservation. A partial/not-equivalent candidate must not contribute the
   same eligible semantic-set member as a complete equivalent candidate.
4. Separate `equivalence_eligibility` from the canonical quotient hash. Compare
   eligible semantic sets and partial/failure profiles independently.
5. Factor the environment adapter into at least modality/cardinality profile,
   semantic-relative access placement, split/fuse boundary profile, and output
   arity. Report exact and component-wise agreement; do not silently collapse
   table versus linked-document modality, cardinality/tie semantics, referent
   identity, or output arity.
6. Re-evaluate the original within-question/family sets and the fully crossed
   16-question author pairs. Report author predictiveness and challenge/control
   strata. Do not prefer `candidate1`.
7. Freeze pass/fail criteria before materialization. Grounding may begin only
   if v0.2 has zero reversible loss, zero eligible-set contamination from
   partial/not-equivalent candidates, stable semantic eligible sets under the
   crossed design, and a bounded adapter component contract. Otherwise create
   another versioned revision or narrow the scientific claim.

Human review remains deferred and is not introduced by this branch.
