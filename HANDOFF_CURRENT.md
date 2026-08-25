# Current handoff

Date: 2026-08-25

Current research phase: **normalization v0.2 contract revision before grounding.**

Active branch: `main`

Expected handoff baseline: `95b4b1356a2cbe050d4bf89a259a4c7340930558`

The current metadata commit is a linear descendant of this completed
crossed-author result baseline.

Last completed task: implemented reversible two-layer operator normalization
v0.1, froze its plan before outputs, normalized all 93 original candidates,
and completed the precommitted two-fresh-author fully crossed sensitivity run
on 16 already exposed questions.

Current scientific decision: `REVISE_EQUIVALENCE_NORMALIZATION_CONTRACT`.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED` until the current linear
sequence is pushed to `origin/main`.

Handoff readiness: Not ready. The scientific gate is
`EQUIVALENCE_NORMALIZATION_V0_2_REVISION_REQUIRED`: normalization v0.2 has not
been implemented or frozen, so grounding remains unauthorized. The separate
`LOCAL_COMMIT_NOT_PUSHED` synchronization gate remains until remote write is
authorized and the 13-commit sequence is pushed.

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

## Exact next task: normalization v0.2

Use only the already exposed 93 original and 34 crossed-author candidates.
Consume no fresh question, answer, trace, grounding, or execution evidence.

1. Add a new v0.2 schema/tool/test bundle without modifying v0.1 artifacts.
2. Commit implementation, then freeze a separate plan while all v0.2 outputs
   are absent; bind all 127 candidates, both v0.1 manifests, producers, and
   stopping branches.
3. Make semantic representation candidate-derived: encode supported/missing
   semantic nodes, mapped output coverage, and dependency preservation.
4. Separate equivalence eligibility from quotient identity. Partial and
   not-equivalent candidates must not count as full eligible set members.
5. Factor adapter signatures into modality/cardinality, semantic-relative
   placement, split/fuse boundary, and output-arity components while preserving
   modality, cardinality/tie, referent identity, and output arity.
6. Recompare original question/family sets and crossed author pairs, including
   component agreement, challenge/control strata, and producer predictiveness.
   Never prefer `candidate1`.
7. Grounding may begin only if separately frozen v0.2 criteria pass with zero
   reversible loss and no eligible-set contamination. Otherwise create another
   version or narrow the claim.

See `data_construction/reports/research_sequencing_decision_v0_6.md`.

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
.venv/bin/python -B -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

Expected deterministic results are zero validation failures, 167 unit tests,
97 core JSON/JSONL files parsed, and preflight exit 2 for the declared
normalization-v0.2 revision and unpushed-commit synchronization gates.
