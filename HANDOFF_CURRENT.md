# Current handoff

Date: 2026-08-25

Current research phase: **targeted authoring-instrument revision protocol
freeze before grounding.**

Active branch: `main`

Expected handoff baseline: `f9377db09ef8d34cc846801730980e933e4e8331`

The current metadata commit is a linear descendant of this completed
targeted re-authoring v0.1 result baseline.

Last completed task: froze and ran targeted crossed-author re-authoring v0.1
over exactly the six existing challenge mismatches with two new isolated
authors; its technical contract passed, but full-eligibility coverage failed.

Current scientific decision:
`REVISE_TARGETED_AUTHORING_INSTRUMENT_BEFORE_GROUNDING`.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED` until the current linear
sequence is pushed to `origin/main`.

Handoff readiness: Not ready. The scientific gate is
`TARGETED_REAUTHOR_FULL_ELIGIBILITY_COVERAGE_FAILED`: targeted re-authoring
passed its technical/profile-inventory contract but observed only 8/12
full-eligible author-question coverage, so grounding remains unauthorized. The
separate `LOCAL_COMMIT_NOT_PUSHED` synchronization gate remains until remote
write is authorized and the 24-commit sequence is pushed.

## Completed normalization v0.1

The immutable sequence is:

1. implementation/schema/tests: `c372ef4b43a88b80d85f69359197bdedd3c40e61`;
2. plan frozen while every normalized output was absent: `83428b9698546de054db672e72dbae880ef4c1ac`;
3. materialized normalization: `a9d3272c6cef4f411bf8f124159a634920c0571e`.

| Measure | Result |
| --- | ---: |
| Original records/questions | 71 |
| Target variants | 72 |
| Candidates | 93 |
| Equivalent / provisional / not equivalent | 89 / 4 / 0 |
| Reversible projection loss | 0 |
| Semantic quotient signatures | 39 |
| Environment-adapter signatures | 19 |
| Unstable multi-question semantic sets | 6/16 families |

The structural projection excludes question/environment text, factual answers,
E1 content, operator labels/descriptions, preserved vocabularies, grounding,
and execution. Fixed question/producer assignment prevented attribution, so the
precommitted crossed-author diagnostic ran instead of grounding.

## Completed crossed-author sensitivity

The frozen sequence is:

1. implementation/schema/protocol/tests: `16a864450af38458eeea4d6aced00ecf7b3e593f`;
2. plan frozen before packets and author outputs: `c00bb6f573b11136d84c3cf4216984813a9930dd`;
3. two identical 16-question packet projections: `144de6b3062ad29cc6c2ca43ad9579bca74b94a8`;
4. isolated author histories ending at `8dcf5d5587132e0cc8c3668d67934543e0e5ff16` and `dfc8a8097aac8d2ca24308a1b7889bfaf23eeaf4`;
5. combined result: `95b4b1356a2cbe050d4bf89a259a4c7340930558`.

The 16 records contain all seven E1 challenge cases plus nine adequate controls
and four records from each original producer partition. Both new fresh-context
AI authors covered every question. No fresh reserve or locked-evaluation ID was
used. Isolation is procedural, not machine-authenticated.

| Measure | Result |
| --- | ---: |
| Authors / author records | 2 / 32 |
| Normalized candidates | 34 |
| Semantic-set exact match / mean Jaccard | 16/16 / 1.0 |
| Adapter-set exact match / mean Jaccard | 0/16 / 0.0 |
| Distinct adapter signatures | 25 |
| Equivalent / provisional / not equivalent | 20 / 9 / 5 |
| Challenge / control semantic exact match | 7/7 / 9/9 |

The frozen criteria failed: not-equivalent count had to be zero and provisional
fraction at most 0.10; observed values were 5 and 9/34=0.2647. Five partial
candidates fail target coverage, dependency, and semantic-output preservation.

The 16/16 semantic hash match is insufficient because v0.1 hashes the target
backbone after checking preservation; a partial candidate may retain the same
target hash while being correctly not-equivalent. Adapter exact signatures are
also too producer-sensitive. Grounding was not started.

## Completed normalization v0.2

The immutable sequence is:

1. implementation/two schemas/seven tests:
   `16868477069f4413392c4f968c3e94c510fcb7a8`;
2. exact plan frozen while every v0.2 output was absent:
   `3d636e57b88da4469540a8ed47fa413147857060`;
3. eight materialized outputs:
   `a13fa72c75049e09a966a9ea11e514c4a961841e`.

| Measure | Result |
| --- | ---: |
| Original / crossed / total candidates | 93 / 34 / 127 |
| Full eligible / provisional only / ineligible | 121 / 1 / 5 |
| Technical loss / eligible contamination / unclassified | 0 / 0 / 0 |
| Candidate semantic profiles / overall adapters | 44 / 65 |
| Crossed semantic exact / mean Jaccard | 10/16 / 0.65625 |
| Full-eligible author-question coverage | 27/32 |
| Challenge / control semantic exact | 1/7 / 9/9 |
| Original unstable multi-question families | 6/16 |

The technical and adapter-component contracts pass. The semantic contract
fails its frozen 32/32 coverage, 14/16 exact-match, 0.95 mean-Jaccard, and 5/7
challenge thresholds. All six mismatches are E1 challenge cases. Five are
ineligible partial candidates from author 01; one is a provisional author-02
candidate with an extra non-target dependency. This is author/instrument
sensitivity, not evidence that either author is correct. Grounding was not
started or authorized.

## Completed targeted re-authoring v0.1

The immutable sequence is:

1. implementation/two schemas/protocol/six tests:
   `51b5204d568efc55f6d1fdff3d7d1b2bf1f6f008`;
2. plan frozen while all eleven planned outputs were absent:
   `4fa67b5f908a3b323610451964aeedcaaef06a2f`;
3. two six-question isolated packets:
   `5e45170f86c8f9b540003d2ffeb896407f26594f`;
4. fresh-context author outputs:
   `c83bb1c8583fbd9ce1fa394f92f092889244b156` and
   `a2610732d7b23fb6ad0e88698c19e7d4ebf37af9`;
5. seven materialized comparison outputs:
   `f9377db09ef8d34cc846801730980e933e4e8331`.

| Measure | Result |
| --- | ---: |
| Authors / author records / candidates | 2 / 12 / 14 |
| Full eligible / provisional / ineligible | 9 / 0 / 5 |
| Technical loss / contamination / unclassified | 0 / 0 / 0 |
| Profile inventory loss / preferred candidates | 0 / 0 |
| Full-eligible author-question coverage | 8/12 |
| Nonempty semantic intersections | 2/6 |
| Semantic exact match / mean Jaccard | 1/6 / 0.25 |
| Reference-compatible author-question pairs | 8/12 |

Targeted author 01 supplied full-eligible candidates on all six questions.
Targeted author 02 supplied full-eligible candidates on two and ineligible
partial candidates on five. Every ineligible candidate lacks semantic-node,
required-dependency, and mapped-output coverage. The run therefore selected
the frozen coverage-failure branch before grounding. No fresh question ID was
used, and no old record was replaced or relabeled.

## Exact next task: authoring-instrument revision plan freeze

Before collecting or modifying another author record, freeze a separately
versioned targeted authoring-instrument revision over the same six IDs. Bind
the entire v0.1 targeted run, preserve it byte-for-byte, and prove every new
planned output absent. Keep prior records/results, semantic signatures,
answers, traces, vocabularies, grounding, and execution hidden from new
authors.

The revised instrument should add only label-free candidate-local feedback for
target-node coverage, required dependencies, mapped target outputs, and output
arity. It must not reveal a reference plan or preferred candidate. Precommit
feedback rounds, full-eligibility coverage, semantic-set/alternative-plan
retention, and all branches. Use no fresh or locked-evaluation ID and perform
no grounding. A future pass may authorize only a separately frozen narrowed
grounding plan.

See `data_construction/reports/research_sequencing_decision_v0_8.md`.

## Evidence boundaries

- Human raw records/agreement/adjudication remain zero.
- Grounding, execution, and answer recovery remain zero/not evaluated.
- No semantic gold, final vocabulary, common exact graph, selected corpus,
  modeling readiness, or answer-accuracy claim is authorized.
- Historical artifacts and IR v0.2 remain read-only.
- The 300 AI-exposed IDs remain ineligible for unseen evaluation; this work
  consumed no additional ID.

## Validation commands

```sh
python3 -m json.tool state/project_state.json >/dev/null
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python -B data_construction/tools/analyze_ai_question_structure_cumulative_n300.py --validate-only
.venv/bin/python -B data_construction/tools/build_candidate_backbone_library.py --validate-only
.venv/bin/python -B data_construction/tools/build_representative_environment_realization.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_normalization.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_crossed_author_sensitivity.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_normalization_v0_2.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_targeted_reauthor.py --validate-only
.venv/bin/python -B -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

Expected deterministic results are zero validation failures, 180 unit tests,
120 core JSON/JSONL files parsed, and preflight exit 2 for the declared
targeted full-eligibility-coverage and unpushed-commit synchronization gates.
