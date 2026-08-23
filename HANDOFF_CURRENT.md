# Current Cross-Device Handoff

Project: Hierarchical Data Construction for Semantic Execution Topology Induction

Current research phase: Phase 2 operator-granularity annotation pilot preparation.

Current branch: `main`

Expected HEAD baseline: `bedfd1f4feeb48f78cea86a9b0deef88e5d34ddc` (`Integrate recovered IR validation and pilot readiness`). The handoff metadata commit containing this file is intentionally one linear descendant of that baseline; any later linear descendant is a continuation. A missing or non-ancestor baseline is divergence.

Remote: `origin` → `https://github.com/kgh0720kgh-boop/pj.git`; `main` tracks `origin/main`.

Last completed task: recovered and strictly audited the five Week 1–3 exposure artifacts, preserved and authenticated the historical IR v0.2 bundle, reconstructed the exact-pin project environment, allocated the verified 30-question annotation pilot, and integrated live IR-reference validation.

Current scientific decision: `DATA_SOURCE_READY_FOR_ANNOTATION_PILOT`. This is an in-progress source/history/environment gate result, not a final modeling decision, a final operator vocabulary, a gold-corpus claim, or modeling readiness.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED`

Handoff readiness: Not ready. The work tree is intended to be clean after the metadata commit, but remote writes were not authorized and empirical annotation/review gates remain open.

## Current artifact snapshot

| Area | Current status |
| --- | --- |
| Official HybridQA sources | Audited at pinned upstream commits; stable identities, hashes, counts, and reacquisition instructions are in `source_manifest_v0_1.json` |
| Historical exposure | Strict-complete: five byte-preserved files, 100 unique exposed IDs, 15 historical locked-eval IDs, zero missing/count/provenance/release-contract errors |
| Pilot allocation | 30 `annotation_schema_pilot` questions from pinned official dev; deterministic, source-verified, zero historical overlap, no override |
| New train/dev/locked roles | Not allocated; all three counts are zero |
| Pilot annotations | Not created; coarse/medium/fine representations, LLM proposals, deterministic annotation results, human reviews, adjudication, and resolved annotations are all `NOT_RUN` |
| Schema bundle | Eight Draft 2020-12 schemas and three candidate vocabularies; full exact-pin project-local validation passes with errors=0 and warnings=0 |
| Historical IR v0.2 | Ten original files quarantined read-only under `historical/ir_v0_2/`, authenticated by recovery manifest and immutable Git authority |
| IR validation | 50/50 condition-C graphs and 520 nodes validated; parse/schema/v0.2-validator errors=0; 455 `DEAD_NODE` warnings retained as historical planner-failure evidence |
| Annotation IR bridge | `referenced_validated` claims now require exact IR/schema declarations, seven passed checks, a live hash-bound graph, and matching graph/question/table identities |
| Regression suite | 43/43 tests pass in the exact-pin project-local environment |
| Git continuity | Local `main` is eight commits ahead of local `origin/main` after this metadata commit; no push was performed |

The source manifest is the dated, immutable v0.1 source-audit snapshot and still records the historical gate as it existed on 2026-08-21. The current allocation authority is the strict historical manifest plus `split_manifest_v0_1.json`; do not rewrite the source manifest merely to erase its dated audit context.

## Remaining gates

- `LOCAL_COMMIT_NOT_PUSHED`: eight local commits are ahead of `origin/main`, and remote writes were not authorized.
- `OPERATOR_GRANULARITY_PILOT_NOT_RUN`: the same 30 questions have not yet been represented and compared under coarse, medium, and fine vocabularies.
- `ANNOTATION_PROPOSALS_NOT_CREATED`: no LLM or human annotation proposals exist for the 30 questions.
- `HUMAN_REVIEW_NOT_PERFORMED`: calibration, adjudication, and resolved annotations do not exist.

These gates make preflight exit 2 (`RESULT=NOT_READY`) even when every deterministic validation passes.

## Next exact task

For the exact 30 IDs and order already fixed in `data_construction/pilot/questions.jsonl` and `split_manifest_v0_1.json`:

1. Materialize hash-bound leakage-safe input views according to the committed layer contracts.
2. Build one coarse, one medium, and one fine representation for every question while preserving ambiguity and valid alternatives.
3. Store the versioned representations at `data_construction/pilot/granularity_representations.jsonl`; do not call any proposal gold.
4. Run the deterministic representation/schema/DAG/reference checks and `compare_operator_granularity.py`, preserving raw outputs and hashes.
5. Create calibration packets tied to the exact views and representation hashes, then obtain real independent human decisions. Do not fabricate reviewer identity, agreement, or adjudication.

The historical condition-C artifact contains answers, evaluator outputs, and later-stage graph evidence. It is permitted only for late-stage IR compatibility regression and historical failure analysis. Never use it, official answer text, weak traces, oracle document IDs, or later-layer labels in question-only semantic, obligation, abstract-topology, operator-topology, few-shot, prompt, or rubric inputs.

Do not allocate annotation train/dev/locked-eval roles, select a final vocabulary, or claim modeling readiness from the 30-question source allocation alone.

## Git continuity

The local continuation after `origin/main` at `c337e9a67c15cd68fbb53eefb79bef90a6f9f242` is linear:

| Commit | Purpose |
| --- | --- |
| `dc44e7a` | Fixed descendant-aware handoff baseline checks and refreshed the repository baseline |
| `1995c0c` | Preserved the five recovered Week 1–3 files byte-for-byte |
| `5680d02` | Verified researcher-approved provenance and generated the complete strict historical manifest |
| `dcc5ac5` | Preserved the ten-file historical IR v0.2 contract/runtime/evidence bundle |
| `4cf0f9c` | Allocated the verified 30-question pilot |
| `94fe6cf` | Recorded the exact IR recovery inventory and leakage policy |
| `bedfd1f` | Integrated hardened IR validation, annotation bridging, preflight checks, tests, and current reports |
| metadata child | Updates this handoff and `state/project_state.json`; it is one descendant of the expected baseline |

Do not force-push, rewrite these commits, discard them, or push without explicit remote-write authorization. Because they are not on `origin/main`, this is not yet a portable cross-device handoff.

## Required files to read

1. `CODEX_DATA_CONSTRUCTION_RESET_PROMPT_V2_MULTI_DEVICE.md`
2. `AGENTS.md`
3. `HANDOFF_CURRENT.md`
4. `state/project_state.json`
5. `ENVIRONMENT.md`
6. `reports/cross_device_repo_audit.md`
7. `data_construction/reports/data_source_audit.md`
8. `state/historical_recovery_provenance_v0_1.json`
9. `data_construction/manifests/historical_exposed_ids.json`
10. `data_construction/manifests/source_manifest_v0_1.json`
11. `data_construction/manifests/source_question_ids.json`
12. `data_construction/manifests/split_manifest_v0_1.json`
13. `historical/README.md`
14. `historical/ir_v0_2/recovery_manifest_v0_1.json`

## Commands to reproduce current checks

Run from the repository root:

```sh
git rev-parse --show-toplevel
git status --short --branch
git log -1 --oneline
git remote -v
python3 -m json.tool state/project_state.json >/dev/null
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

Expected deterministic results:

- schema bundle: 8 schemas, 3 vocabularies, errors=0, warnings=0;
- IR adapter: 50 records, 520 nodes, parse/schema/validator errors=0, `DEAD_NODE=455`;
- tests: 43 passed;
- preflight: zero validation failures, `RESULT=NOT_READY`, exit 2 because of the declared gates and local unpushed commits;
- Git work tree: clean after the metadata commit;
- local branch: eight commits ahead of the local tracking ref.

The preflight comparison uses local remote-tracking refs. Fetch separately only when remote reads are authorized. Do not pull over or reset the local continuation.

## Do-not-modify historical paths

The following are read-only evidence:

- `data_analysis/week1_sample_100.jsonl`
- `evaluation/week2_eval_ids.json`
- `evaluation/week3_engineering_dev_ids.json`
- `evaluation/week3_locked_eval_ids.json`
- `evaluation/week3_split_manifest.json`
- `historical/ir_v0_2/ir/spec_v0_2.md`
- `historical/ir_v0_2/ir/execution_graph.schema.json`
- `historical/ir_v0_2/ir/operator_registry_v0_2.json`
- `historical/ir_v0_2/ir/type_registry_v0_2.json`
- `historical/ir_v0_2/src/hybridqa_graph/ir.py`
- `historical/ir_v0_2/src/hybridqa_graph/planning.py`
- `historical/ir_v0_2/src/hybridqa_graph/registry.py`
- `historical/ir_v0_2/src/hybridqa_graph/validator.py`
- `historical/ir_v0_2/experiments/results/week2_pilot/condition_C.jsonl`
- `historical/ir_v0_2/experiments/results/week2_pilot/run_manifest.json`

A correction or additional recovery requires a new versioned manifest and preservation commit. Never use recovered exposed IDs for training, and never use the recovered locked-evaluation IDs for prompt/rubric/schema/operator-vocabulary tuning.

## Machine-local resources

- CPython 3.10.12 and Git are workstation dependencies.
- Recreate `.venv` from `requirements.txt`; never copy it across machines.
- Official HybridQA source checkouts are untracked caches and must be reacquired or verified from the source manifest.
- Codex conversation state, caches, credentials, local stashes, editor state, and consumer-synchronized folders are non-portable.

No model runtime, secret, GPU, database, Docker service, or external account is required for the completed recovery/validation work. Future model runs must record stable model ID, exact revision, seed, prompt artifact, raw output hash, code commit, and run status.
