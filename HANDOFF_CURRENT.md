# Current handoff

Date: 2026-09-07

Current research phase: **materialize and commit the six frozen grounding
packets before isolated raw collection.**

Active branch: `main`

Expected handoff baseline: `6c7487beddb03625b9fd23ef7514eebe307d397b`

The current metadata commit is a linear descendant of this output-absent
narrowed-grounding runtime freeze baseline.

Last completed task: implemented two grounding schemas, the packet builder,
static binding validator and analyzer, then froze their runtime receipt.
All 26 new regression tests passed. Exact pins, source/contract hashes, Git
ancestry, and absence of all twenty planned outputs passed validation.

Current scientific decision:
`MATERIALIZE_FROZEN_NARROWED_GROUNDING_PACKETS`.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED` until the current linear
sequence is pushed to `origin/main`.

Handoff readiness: Not ready. The plan and runtime gates are complete; the
active research gate is `NARROWED_GROUNDING_PACKETS_NOT_MATERIALIZED`. Create
and commit the six complete question packets and coordinator manifest before
any authoring. The separate
`LOCAL_COMMIT_NOT_PUSHED` gate remains: 38 commits including this metadata
handoff are ahead of `origin/main`. The user requested work from research
TODO 2; remote synchronization was not performed.

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

## Completed targeted authoring-instrument revision v0.2

The immutable sequence is:

1. checker/three schemas/protocol/ten tests:
   `6703293a3b73539940864d681a034abfd939707b`;
2. plan frozen while all seventeen outputs were absent:
   `3caedbe7a84ee2cac15cf24a33c7f0ff26177f21`;
3. two equal-visibility six-question packets:
   `50801e80caa86fc771be0bed85c6ba687e835539`;
4. two fresh-context immutable drafts:
   `2df347a76f381c2d1e6deec02f34e4f38bd4ea4a`;
5. one draft-hash-bound candidate-local feedback round:
   `1a92e63d9e7abd12f4ae70c0b250512f42f61601`;
6. final author records from the same isolated contexts:
   `3de0a547770e3c225ce0cb9f8990cf00558af308`;
7. nine comparison/result outputs:
   `d22a9beca223f49d7af17c8657aafdbf8753de4f`.

| Measure | Result |
| --- | ---: |
| Draft / final records | 12 / 12 |
| Draft / final candidates | 14 / 14 |
| Feedback records / binding errors / leakage | 12 / 0 / 0 |
| Final full eligible / provisional / ineligible | 14 / 0 / 0 |
| Candidate-local / full-eligible author-question coverage | 12/12 / 12/12 |
| Nonempty intersections / semantic exact | 6/6 / 6/6 |
| Mean semantic Jaccard | 1.0 |
| Targeted-v0.1-compatible author-question pairs | 12/12 |
| Profile loss / preferred candidates / fresh IDs | 0 / 0 / 0 |
| Parsed records changed after feedback | 0/12 |

Both authors received only their own packet/protocol/schema, then only their
own immutable draft and feedback. The feedback contained target-node,
required-dependency, mapped-output, and output-arity facts only. Every draft
already passed these local obligations, so finals were parsed-value identical.
The result supports the revised instrument as a whole; it does not identify a
causal checker-feedback effect. Isolation remains procedural rather than
globally machine-authenticated.

## Completed narrowed-grounding plan v0.1

Implementation/design/protocol/seven tests were committed at
`6bd9c36ddc6207552b778cf5b20b16946975ef05`. The metadata-only plan was committed
at `b2ca1fbc413336fa330b11a14649735acc25f0df` while its entire output namespace
was empty. The source baseline is `aa380e69b534e475f09d496955ebcbac69531309`.

The plan keeps all fourteen final candidate observations and 52 source slots,
without deduplication or preference. Six new contexts will each receive one
complete question packet containing all that question's candidates. This is
one proposal per question, not independent duplicate grounding review.
No authoring has run. Static source pointers and unevaluated dynamic locator
rules are distinct from runtime values; actual graph execution and answer
recovery remain outside this study.

The design fixes provenance, visibility, exact observation/slot retention,
ambiguity/abstention, raw preservation without semantic repair, and five
ordered branches. Pass requires fourteen resolved candidates and zero
unresolved dispositions, technical/leakage errors, or lost alternatives.
Every branch stops before execution or answer recovery.

## Completed narrowed-grounding runtime v0.1

Implementation, two schemas, author guide and 26 regression tests were
committed at `2983168f48689e8e7129a9bdecde4787a4ecb8cf`. The runtime receipt
was committed separately at `6c7487beddb03625b9fd23ef7514eebe307d397b`, while
the entire output namespace and all twenty planned files were absent.

Static checks bind locators to exact environment hashes, preserve every
candidate/slot/operator and identified alternative, distinguish literal spans
from unevaluated dynamic rules, and reject invalid links, non-upstream
references, contradictory dispositions and post-output retries. The analyzer
keeps technical errors, missing responses, incomplete source delivery,
unresolved coverage and full static coverage separate under the five frozen
branches. Original raw bytes must remain equal to their first capture commit.

Synthetic tests do not constitute grounding evidence. In-memory reconstruction
of the six actual packet projections verified 14 candidates and 52 slots
without writing or distributing a packet. No raw author response exists.

## Exact next task: narrowed-grounding packet materialization

Read `contracts/narrowed_grounding_plan_v0_1.json`,
`contracts/narrowed_grounding_design_v0_1.json`, and
`prompts/narrowed_grounding_v0_1.md` under the scale-exploration directory.
Also read the runtime receipt, packet/raw schemas and
`prompts/narrowed_grounding_author_guide_v0_1.md`. First validate the receipt
with `--validate-only --require-output-absence`, then use the runtime tool's
`--build-packets` mode. Commit all six question packets and the coordinator
manifest together before authoring. The manifest's routing metadata must not
be sent to authors.

Then use one fresh context per question, with only its complete packet,
protocol, guide and response schema. Preserve the sole raw response unchanged
and commit it before `--analyze`. No semantic repair, cross-question history,
prior records or later-layer evidence is allowed. Packet/receipt Git order and
raw immutability are checked by the analyzer. `--validate-results` reconstructs
existing results; it does not certify semantic correctness.

The exact six-ID order and all 14 observations/52 slots remain frozen.
The plan does not authorize execution, answer recovery, fresh questions,
upstream annotation edits, or selection of a final operator vocabulary.
If the contract needs changing, use a new plan version before outputs.

See `data_construction/reports/research_sequencing_decision_v0_11.md`.

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
.venv/bin/python -B data_construction/tools/build_operator_equivalence_targeted_instrument_v0_2.py --validate-only
.venv/bin/python -B data_construction/tools/freeze_narrowed_grounding_plan_v0_1.py --validate-only --require-output-absence
.venv/bin/python -B data_construction/tools/narrowed_grounding_runtime_v0_1.py --validate-only --require-output-absence
.venv/bin/python -B -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

Expected deterministic results are zero validation failures, 223 unit tests,
145 core JSON/JSONL files parsed, and preflight exit 2 for the declared
grounding-packet and unpushed-commit synchronization gates.
The 2026-09-07 exact-pin integration check reproduced 223 passing tests and
145 parsed JSON/JSONL files, with zero validation failures. All 26 runtime
tests and output-absent runtime validation passed. The pre-commit preflight
also noted this turn's metadata edits; committing them clears that worktree
blocker without changing the scientific or remote synchronization gates.
The original eleven-schema/three-vocabulary bundle is unchanged. Two new
grounding packet/raw schemas live separately in the exploration contracts and
are validated by the pinned runtime and its local-only reference registry.
