# Research sequencing decision v0.8

Date: 2026-08-25

## Decision

The targeted crossed-author re-authoring v0.1 run is complete. Its frozen
technical and profile-inventory contracts passed, but its full-eligibility
coverage gate failed before the semantic-stability gate could pass. The
selected frozen branch is:

`REVISE_TARGETED_AUTHORING_INSTRUMENT_BEFORE_GROUNDING`

Do not begin grounding, execution, answer recovery, vocabulary selection, or
a common-interface claim. The next operation is to freeze a separately
versioned targeted authoring-instrument revision before collecting any new
author output. No fresh question ID may be consumed.

## Frozen sequence

The targeted re-authoring run was committed in this order:

1. implementation, two schemas, protocol, and six tests while the plan and
   every targeted output were absent:
   `51b5204d568efc55f6d1fdff3d7d1b2bf1f6f008`;
2. exact plan frozen while all eleven planned outputs were absent:
   `4fa67b5f908a3b323610451964aeedcaaef06a2f`;
3. two reconstructed six-question isolated authoring packets:
   `5e45170f86c8f9b540003d2ffeb896407f26594f`;
4. fresh-context author outputs:
   `c83bb1c8583fbd9ce1fa394f92f092889244b156` and
   `a2610732d7b23fb6ad0e88698c19e7d4ebf37af9`;
5. seven derived comparison outputs:
   `f9377db09ef8d34cc846801730980e933e4e8331`.

Both authors received only their assigned packet, the frozen protocol, and the
open-realization schema. Isolation was procedural, not globally
machine-authenticated. Mechanical validation errors were returned only to the
author that produced them. Final JSONL serialization was normalized with the
project serializer after verifying that parsed-value hashes were unchanged.

## Result

| Measure | Result |
| --- | ---: |
| New authors / author records | 2 / 12 |
| Targeted questions / fresh question IDs | 6 / 0 |
| New normalized candidates | 14 |
| Full eligible / provisional only / ineligible | 9 / 0 / 5 |
| Technical loss / eligible contamination / unclassified | 0 / 0 / 0 |
| Profile-inventory loss / preferred candidates | 0 / 0 |
| Full-eligible author-question coverage | 8/12 |
| Nonempty new-author semantic intersections | 2/6 |
| New-author semantic exact match | 1/6 |
| Mean new-author semantic Jaccard | 0.25 |
| Reference-compatible author-question pairs | 8/12 |
| Distinct observed semantic profiles | 11 |

Targeted author 01 supplied a full-eligible semantic set on all six questions.
Targeted author 02 supplied a full-eligible candidate on two questions and an
ineligible partial candidate on the other five. The pair shared one semantic
profile on `0d48bffa70ef4acf` and exactly matched on `1e2e4e4f72a64bbf`.

Each of the five ineligible candidates has incomplete semantic-node coverage,
missing mapped semantic-output coverage, and missing required semantic
dependencies. The affected questions are:

1. `0d48bffa70ef4acf`
2. `cc681cfdba9badd5`
3. `1e674ae4b655c1a1`
4. `1ca8ffcd3e20e498`
5. `ba563b015b09bf21`

The technical contract passed because all source candidates were normalized,
all adapter source elements were classified, no ineligible candidate entered a
full-eligible set, and every observed alternative profile remained in the
inventory. The frozen 12/12 coverage requirement failed at 8/12, so the
coverage branch takes precedence. The semantic thresholds also did not pass,
but empty sets created by coverage failure make them secondary evidence.

## Interpretation

This run reproduces author/instrument sensitivity rather than resolving it.
The identity of the author producing partial plans changed relative to the
earlier crossed-author run, while the full-eligible profiles observed on the
same questions remained compatible with prior full-eligible reference
profiles. This does not identify a correct author, establish a causal producer
effect, or make any record gold.

The current authoring schema and graph validator permit a structurally valid
partial record. The prose protocol asks for a complete candidate when the
environment supports one, but it does not provide a narrow machine-readable
pre-submission diagnostic for semantic-node, dependency, and output coverage.
The next revision should address that instrument gap without exposing prior
author results or reference semantic signatures.

The evidence remains AI exploratory, non-human, and non-gold. The two author
sessions inherited the Codex GPT-5 model family; an exact model revision and
seed were not exposed by the interface, so exact generation replayability is
not claimed.

## Exact next task: freeze an authoring-instrument revision

Before collecting or revising another author record, create a separately
versioned targeted authoring-instrument plan. It must:

1. bind the complete v0.1 targeted run, all twelve immutable author records,
   and exactly the same six already exposed question IDs;
2. prove that every newly planned packet, author output, diagnostic, and
   comparison output is absent at the freeze commit;
3. preserve v0.1 artifacts byte-for-byte and treat them as observations, not
   correction targets, votes, adjudication, or gold;
4. retain fresh-context, equal-visibility authoring while hiding prior E1/E2
   content, prior author outputs, normalization results, semantic signatures,
   metrics, answers, traces, vocabularies, grounding, and execution;
5. add a label-free, candidate-local pre-submission checker that reports only
   whether every target semantic node, required dependency, target output, and
   output-arity obligation is preserved; it must not reveal a reference plan
   or preferred candidate;
6. precommit how checker feedback may be used, how many correction rounds are
   allowed, complete-candidate coverage, semantic-set and alternative-plan
   retention criteria, and all pass/fail branches;
7. use no fresh reserve or locked-evaluation ID and perform no grounding.

A successful future branch may only authorize freezing a separate narrowed
grounding protocol. A repeated coverage failure must narrow the claim or move
to a separately approved human review design rather than iteratively tuning on
locked or fresh evaluation records.
