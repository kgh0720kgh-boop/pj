# Research sequencing decision v0.9

Date: 2026-08-25

## Decision

The targeted authoring-instrument revision v0.2 is complete. Its frozen
technical, isolation, complete-candidate coverage, semantic-stability,
reference-compatibility, and profile-retention criteria all passed. The
selected frozen branch is:

`FREEZE_INSTRUMENT_REAUTHOR_EVIDENCE_FOR_SEPARATE_NARROWED_GROUNDING_PLAN`

This branch does not authorize grounding itself. The next operation is to
freeze a separately versioned narrowed-grounding plan before creating any
grounding output. Use no fresh or locked-evaluation question ID.

## Frozen sequence

The v0.2 run was committed in this order:

1. checker, three schemas, protocol, and ten tests while the plan and every
   run output were absent: `6703293a3b73539940864d681a034abfd939707b`;
2. exact plan binding the complete targeted v0.1 run while all seventeen new
   outputs were absent: `3caedbe7a84ee2cac15cf24a33c7f0ff26177f21`;
3. two equal-visibility six-question packets:
   `50801e80caa86fc771be0bed85c6ba687e835539`;
4. two fresh-context immutable drafts:
   `2df347a76f381c2d1e6deec02f34e4f38bd4ea4a`;
5. one deterministic, draft-hash-bound feedback round per author:
   `1a92e63d9e7abd12f4ae70c0b250512f42f61601`;
6. final records from the same isolated author contexts:
   `3de0a547770e3c225ce0cb9f8990cf00558af308`;
7. normalized draft/final observations and frozen comparison result:
   `d22a9beca223f49d7af17c8657aafdbf8753de4f`.

Both authors received only their own packet, the v0.2 protocol, and the open
realization schema for the draft. Each then received only their own immutable
draft and own feedback file. Prior outputs, E1/E2 content, normalization,
semantic signatures, metrics, answers, traces, vocabularies, grounding, and
execution were excluded. Isolation was procedural, not globally
machine-authenticated.

The first submissions passed schema and graph checks but used a compact JSON
separator style different from the project serializer. They were mechanically
re-serialized after confirming every parsed-record hash was unchanged. This
was serialization normalization, not semantic feedback. The only semantic
feedback round was the precommitted candidate-local round.

## Result

| Measure | Result |
| --- | ---: |
| Authors / questions | 2 / 6 |
| Draft / final records | 12 / 12 |
| Draft / final candidates | 14 / 14 |
| Candidate-local feedback records | 12 |
| Feedback binding errors / reference leakage | 0 / 0 |
| Final candidate-local complete author-question pairs | 12/12 |
| Final full-eligible candidates | 14/14 |
| Final full-eligible author-question coverage | 12/12 |
| Nonempty final-author semantic intersections | 6/6 |
| Final-author semantic-set exact matches | 6/6 |
| Mean final-author semantic-set Jaccard | 1.0 |
| Targeted-v0.1-reference-compatible author-question pairs | 12/12 |
| Profile-inventory loss / preferred candidates | 0 / 0 |
| Fresh or locked-evaluation IDs | 0 |
| Parsed records changed after feedback | 0/12 |

All fourteen final candidates are full eligible. Every final author-question
set intersects the corresponding union of targeted v0.1 full-eligible
observations. All draft, final, and targeted v0.1 profile observations remain
represented in the profile inventory.

## Interpretation

The complete-coverage failure observed in targeted v0.1 did not recur under
the revised authoring instrument. The two new authors also produced identical
full-eligible semantic sets on all six questions. This supports freezing the
v0.2 instrument evidence and proceeding to a separately planned, narrow
grounding study.

It does not establish semantic gold, a uniquely correct graph, a final
operator vocabulary, human agreement, executable success, or answer accuracy.
It also does not identify a causal effect of checker feedback: every draft
already contained a candidate satisfying all four local obligations, and both
authors retained their parsed drafts unchanged after feedback. The observed
change relative to v0.1 concerns the revised instrument as a whole, including
its protocol and fresh author sample.

The evidence remains AI exploratory, non-human, and non-gold. Exact model
revision and seed were not exposed, and global nonexposure cannot be
machine-authenticated.

## Exact next task: freeze a narrowed-grounding plan

Before producing a locator, grounding record, executable graph, execution
result, or answer, freeze a separately versioned narrowed-grounding plan. It
must:

1. bind the complete targeted v0.1 and instrument v0.2 runs and exactly the
   same six already exposed question IDs;
2. prove every planned grounding packet, record, check, metric, comparison,
   report, and manifest absent at the freeze commit;
3. preserve all prior artifacts byte-for-byte and treat every candidate as an
   observation rather than gold, a vote, or a preferred plan;
4. define whether grounding covers all fourteen final full-eligible candidate
   observations or a deterministic, alternative-preserving deduplicated set;
   the selection rule must be fixed before grounding output exists;
5. expose only the environment information required for grounding and prevent
   answers, official traces, execution outcomes, or later labels from flowing
   back into semantic/operator records;
6. precommit locator completeness, ambiguity, alternative-retention,
   provenance, abstention, technical-failure, and pass/fail branches;
7. perform no execution or answer recovery and consume no fresh reserve or
   locked-evaluation ID.

A grounding-plan pass would still authorize only the activity explicitly
frozen in that plan. It cannot retroactively make the semantic records gold or
authorize a common exact graph claim.
