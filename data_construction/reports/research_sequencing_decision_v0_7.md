# Research sequencing decision v0.7

Date: 2026-08-25

## Decision

Operator-equivalence normalization v0.2 is complete. Its technical and
factorized-adapter contracts passed, but its frozen crossed-author semantic
stability criteria failed. The selected frozen branch is:

`NARROW_OR_REAUTHOR_BEFORE_GROUNDING`

Do not begin grounding, execution, answer recovery, provisional-vocabulary
selection, or a common-interface claim. The next operation is to freeze a
separate targeted re-authoring protocol over exactly the six already exposed
challenge questions that failed the v0.2 crossed-author comparison. No fresh
question ID may be consumed.

## Frozen sequence

Normalization v0.2 was committed in this order:

1. implementation, two schemas, and seven regression tests:
   `16868477069f4413392c4f968c3e94c510fcb7a8`;
2. exact 127-candidate plan while every v0.2 output was absent:
   `3d636e57b88da4469540a8ed47fa413147857060`;
3. eight materialized outputs:
   `a13fa72c75049e09a966a9ea11e514c4a961841e`.

The run consumed only the 93 original and 34 crossed-author v0.1 normalized
candidates. The plan binds both source run manifests, every source candidate
key, source-record and structural-projection hashes, producer/author identity,
the implementation commit, and all pass/fail branches. No v0.1 artifact was
modified.

## Result

| Measure | Result |
| --- | ---: |
| Candidates | 127 |
| Original / crossed-author candidates | 93 / 34 |
| Full eligible / provisional only / ineligible | 121 / 1 / 5 |
| Reversible technical loss | 0 |
| Eligible-set contamination | 0 |
| Unclassified adapter candidates | 0 |
| Maximum component records per candidate | 7 |
| Distinct candidate-derived semantic profiles | 44 |
| Distinct overall factorized adapters | 65 |
| Crossed semantic-set exact match | 10/16 |
| Crossed mean semantic-set Jaccard | 0.65625 |
| Full-eligible author-question coverage | 27/32 |
| Challenge / control semantic exact match | 1/7 / 9/9 |
| Unstable multi-question original families | 6/16 |

The factorized adapter component counts are 32 modality/cardinality, 38
semantic-relative-placement, 24 split/fuse-boundary, and 9 output-arity
signatures. Their crossed exact matches are respectively 0/16, 7/16, 9/16,
and 10/16. These component identities preserve distinctions rather than
asserting that all producer variation has been removed.

The frozen technical contract passed because loss, contamination, and
unclassified counts are all zero and component bounds hold. The frozen
semantic contract failed because it required at least 32/32 full-eligible
author-question coverage, 14/16 exact matches, mean Jaccard at least 0.95, and
5/7 challenge matches. The observed values were 27/32, 10/16, 0.65625, and
1/7. The 9/9 control requirement passed.

## Discrepancy set

Exactly six questions fail full-eligible semantic-set equality, and all six
are in the predeclared E1-challenge stratum:

| Question ID | Jaccard | Structural discrepancy |
| --- | ---: | --- |
| `0d48bffa70ef4acf` | 0.5 | author 01 has one full and one ineligible candidate; author 02 has two full candidates |
| `cc681cfdba9badd5` | 0.0 | author 01 candidate is ineligible; author 02 has one full candidate |
| `1e2e4e4f72a64bbf` | 0.0 | author 01 has one full candidate; author 02 is provisional-only because of an extra non-target dependency |
| `1e674ae4b655c1a1` | 0.0 | author 01 candidate is ineligible; author 02 has one full candidate |
| `1ca8ffcd3e20e498` | 0.0 | author 01 candidate is ineligible; author 02 has one full candidate |
| `ba563b015b09bf21` | 0.0 | author 01 candidate is ineligible; author 02 has one full candidate |

Each of the five ineligible candidates is missing semantic-node coverage,
mapped semantic-output coverage, output-arity/mapping preservation, and a
required semantic dependency. The one provisional candidate adds a non-target
semantic dependency. This is evidence of author/instrument sensitivity in the
observed design, not proof that either author is semantically correct.

## Interpretation

The v0.1 result of 16/16 semantic matches was an overestimate for the intended
claim because its quotient identity was target-anchored even when a candidate
was partial. V0.2 makes identity candidate-derived and keeps eligibility
separate, so partial and provisional records cannot enter the full-eligible
set. The resulting 10/16 result is therefore the authoritative crossed-author
comparison for these records.

Producer-signature concentration remains descriptive. Weighted partition
purity is high for the overall adapter and modality/cardinality component, but
the design does not support causal producer attribution or semantic-correctness
claims. Exact component disagreement can also reflect legitimate alternative
plans, so it is not itself an error count.

The evidence remains AI exploratory, non-human, and non-gold. It establishes
no grounding success, execution success, answer accuracy, final vocabulary,
universal semantic topology, or modeling readiness.

## Exact next task: targeted re-authoring plan freeze

Create a separately versioned targeted crossed-author re-authoring plan before
collecting any new author output. The plan must:

1. bind exactly the six discrepancy IDs above in that order, the v0.2 run
   manifest and comparison hashes, both existing author records, and the
   immutable sanitized source views;
2. prove that all planned outputs are absent at the freeze commit;
3. use no fresh reserve or locked-evaluation question ID;
4. assign two new fresh-context AI authors to all six questions with identical
   visibility, while withholding E1 labels, prior author outputs, v0.1/v0.2
   normalization results, metrics, preserved vocabularies, answers, traces,
   grounding, and execution results;
5. preserve all existing records and treat new records as additional
   observations rather than replacements, votes, adjudications, or gold;
6. precommit candidate-derived full-eligibility, semantic-set, alternative-plan
   coverage, author-pair, and challenge-level stopping criteria and all
   branches before materialization;
7. forbid grounding in the re-authoring run itself. A successful branch may
   only authorize a separately frozen narrowed grounding protocol; a failed
   branch must narrow the claim or revise the authoring instrument.

Human review remains deferred. A later human audit would require its own
approved visibility, independence, and adjudication contract.
