# Current handoff

Date: 2026-08-25

Current research phase: **candidate-backbone library and representative-sampling contract freeze after the completed cumulative N=300 question-only exploration.**

Active branch: `main`

Expected handoff baseline: `5c73da72e93fa534711e222eb53ac02140596946`

The expected baseline is the committed cumulative N=300 records, deterministic
analysis, and completion exposure ledger. This metadata handoff is one linear
descendant of that baseline.

Last completed task: froze the cumulative N=300 selection and routing before
model output, generated positions 101--300 under the unchanged N=100 contract,
validated the cumulative 300 records with a byte-exact N=100 prefix, computed
all precommitted metrics, and applied the frozen N=1,000 decision rule.

Next exact task: before inspecting table/document contents or execution
outcomes, create and commit a versioned candidate-backbone/library-and-
representative-sampling contract. Retain all 30 contracted families without
post-hoc semantic merging, preserve their fine/topology/task crosswalks and
evidence strength, and deterministically commit frequency/rarity-stratified
representative IDs. Then begin environment-aware operator realization while
keeping backbone adequacy, grounding, execution, and answer recovery separate.

Current scientific decision:
`FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_ENVIRONMENT_REALIZATION`.

Study status:
`n300_complete_candidate_backbone_library_freeze_required_human_validation_deferred`.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED`.

Handoff readiness: Not ready. At the expected baseline, local `main` is 36
commits ahead of local `origin/main`; the metadata commit containing this
handoff is projected to make it 37 commits ahead. No push was performed or
authorized.

## Authoritative status

| Area | Current evidence |
| --- | --- |
| Official source | HybridQA table corpus and released train/dev remain pinned and hash-audited at manifest-recorded upstream commits |
| Historical exposure | Five recovered Week 1--3 files are byte-preserved; 100 unique exposed IDs and 15 locked-evaluation IDs; strict errors=0 |
| Historical IR v0.2 | Ten files are quarantined read-only; 50 graphs/520 nodes validate with 0 parse/schema/validator errors and 455 preserved `DEAD_NODE` warnings |
| Released role allocation | `split_manifest_v0_1.json` remains unchanged: annotation-pilot=30, train=0, dev=0, locked-eval=0 |
| N=300 exploratory allocation | Frozen N=100 is the exact prefix; 200 fresh eligible questions were added; historical overlap=0; 3,066 official-dev questions remain unexposed/unallocated |
| N=300 extraction integrity | 300/300 records pass Draft 2020-12 schema, exact question/order/hash/cue, forbidden-key, reference, root/sink, and DAG checks; N=100 bytes are an exact prefix |
| N=300 recurrence | Fine labeled families=39; same-role-contracted families=30; topology shapes=10; task signatures=70 |
| Contracted diagnostics | Singleton mass=0.0467; top-10 coverage=0.9133; N100-to-new200 transfer=183/200=0.915; final-50 sequential novelty=5/50=0.10 |
| New-family support | 13 contracted families are absent from N=100; 3 recur in new200, 2 recur across new producer partitions, and 1 meets the material cross-partition rule |
| Record diagnostics | Complete=206, uncertain=94; provisional `OTHER` questions=0; alternative-graph questions=1 |
| Graph profile | Raw branch/join=6/11; transitive-reduced branch/join=1/6; reduced mean edges=1.3933 |
| Precommitted N=1,000 outcome | All four triggers are false; selected branch is candidate-library freeze and representative environment realization |
| Human evidence | Human raw files=0, human records=0, agreement observations=0, adjudications=0; the v0.1 human-first lane is preserved but deferred |
| Prior AI diagnostic | The two-reviewer/alignment/topology rehearsal remains non-human/non-gold direction-finding evidence and is not pooled with the N=300 primary records |
| Operator granularity | The 30-record/90-representation/90-check/three-packet feasibility bundle remains deferred; no vocabulary is selected and human reviews remain 0 |

## What the N=300 result means

Under one frozen question-only AI extractor and deterministic normalizer, most
new HybridQA questions reuse families already seen in N=100. The contracted
view transfers 91.5% of the new 200 questions into N=100 families, and its
singleton question mass falls from 0.09 at N=100 to 0.0467 at N=300.

The frozen N=1,000 rule used four `ANY` triggers. None fired:

- contracted singleton mass 0.0467 is not greater than 0.05;
- `OTHER` rate 0 is not greater than 0.05;
- final-50 novelty is exactly 0.10, not greater than 0.10, although it contains five new families;
- one material cross-partition family is below the required two.

This makes environment realization the selected next measurement. It does not
mean that the 30 contracted families are semantic gold or that all HybridQA
structure is saturated. Fine singleton mass remains 0.0667, task singleton
mass remains 0.13, and same-role contraction can hide distinct referent hops.
Producer-context profiles also vary, so partition support is a robustness
diagnostic rather than reviewer agreement.

No result here evaluates factual answers, table/document realization,
grounding, execution, human agreement, semantic correctness, a universal
topology, or a common executable graph.

## Declared blockers

- `LOCAL_COMMIT_NOT_PUSHED`: portable work exists only in local commits; remote writes were not authorized.
- `CANDIDATE_BACKBONE_LIBRARY_NOT_FROZEN`: the precommitted N=300 branch requires a versioned candidate library and representative-sampling contract before environment realization.

The absence of human review is not a current blocker. It remains a truthful
zero-count evidence boundary and may become relevant later for targeted claims.

## Exact next task: library and sampling freeze

1. Define and commit the library/sampling schema, builder contract, and deterministic representative-selection rule before reading any environment content or outcomes.
2. Materialize all 30 contracted signatures as candidate families; do not perform post-hoc semantic family merging.
3. Bind each family to its canonical contracted graph, cumulative/N100/new200 frequency, producer-partition and ten-question-block support, member IDs, and fine/topology/task crosswalks.
4. Label evidence strength separately for recurrent, doubleton, and singleton families; `candidate` must not be relabeled `gold` or `established`.
5. Preserve observed role/transition composition evidence separately from family identity and state that same-role contraction does not prove semantic equivalence.
6. Select and commit frequency/rarity-stratified representative IDs before table/document text, answers, grounding, execution traces, or outcome metrics are inspected.
7. Only then produce environment-aware operator realizations, recording semantic-backbone adequacy, environment realization, grounding, execution, and final-answer recovery as separate signals.

This is not a request to resume full duplicate human review and is not an
authorization to use the historical condition-C answer-bearing files as an
early-layer input.

## Evidence and exposure boundaries

- All 300 primary records are `ai_exploratory_non_human_non_gold`.
- All 300 processed IDs are excluded from future unseen-evaluation claims; this is exposure accounting, not a correctness label.
- Table identity/schema/rows/cells, linked-document identity/text, answers, traces, operator proposals, grounding, and historical graphs were forbidden inputs to the question-only extractor.
- The stable model identity contract is `codex_gpt-5`; no immutable exact revision or seed was available. Structured partition JSONL is the primary capture, and exact generation replayability or statistical independence is not claimed.
- The v0.1 human packet and AI diagnostic remain preserved and contribute zero human evidence.
- No operator vocabulary, candidate-backbone library, corpus, or model is selected, gold, universally supported, or modeling-ready.

## Portable commits

| Commit | Role |
| --- | --- |
| `dc64c89` | Added the N=300 pool builder, cumulative analyzer, frozen trigger implementation, and tests |
| `98a1627` | Committed exact N=300 selection, five-way routing, exposure v0.2, and analysis plan before model outputs |
| `1f9c118` | Committed five positions-101--300 AI JSONL parts, 40 records each |
| `5c73da7` | Committed cumulative 300 records/checks/signatures/metrics/report, run manifest, and exposure v0.3 |
| metadata child | Updates AGENTS, handoff/state, documentation, preflight, and N=300 sequencing report; one descendant of the expected baseline |

No push was performed.

## Validation commands

Run from the repository root:

```sh
python3 -m json.tool state/project_state.json >/dev/null
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python data_construction/tools/analyze_ai_question_structure_cumulative_n300.py --validate-only
.venv/bin/python -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

Expected current result after this metadata update:

- schema bundle: 11 schemas and 3 vocabulary instances, zero errors/warnings under the exact pin;
- IR adapter: 50 records, 520 nodes, zero parse/schema/validator errors, 455 `DEAD_NODE` warnings;
- cumulative N=300 validation: 300 records, 300 passing checks, byte-exact N=100 prefix;
- N=1,000 trigger: four false conditions and the candidate-library decision;
- unit tests: 105 passed, 0 failed;
- preflight: zero deterministic validation failures, `RESULT=NOT_READY`, exit 2 only for synchronization and candidate-library gates.

The preflight compares local remote-tracking refs. Fetch only when remote reads
are authorized; never pull over, reset, or rewrite this continuation.
