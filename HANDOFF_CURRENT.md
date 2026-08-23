# Current Cross-Device Handoff

Project: Hierarchical Data Construction for Semantic Execution Topology Induction

Current research phase: Phase 2 operator-granularity structural pilot complete; human calibration pending.

Current branch: `main`

Expected HEAD baseline: `7f808d5d1bf75c00c0572b6f3cab6b10d211a94b` (`data: complete structural granularity pilot`). The handoff metadata commit containing this file is intentionally one linear descendant of that baseline; any later linear descendant is a continuation. A missing or non-ancestor baseline is divergence.

Remote: `origin` → `https://github.com/kgh0720kgh-boop/pj.git`; `main` tracks `origin/main`.

Last completed task: built 30 hash-bound leakage-safe operator views and 30 model-assisted records containing 90 coarse/medium/fine candidate representations, produced 90 warning-free deterministic pass records and three exact-rendered review packets, compared structural metrics without fabricating human evidence, and added write-once/explicit-overwrite protection to all five granularity writers.

Current scientific decision: `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`. Study status is `structural_integrity_complete_human_calibration_pending`; this is not a final modeling decision, a selected vocabulary, a gold-corpus claim, or modeling readiness.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED`

Handoff readiness: Not ready. The work tree is clean after the metadata commit, but remote writes were not authorized and real independent human calibration remains open.

## Current artifact snapshot

| Area | Current status |
| --- | --- |
| Official HybridQA sources | Audited at pinned upstream commits; stable identities, hashes, counts, and reacquisition instructions are in `source_manifest_v0_1.json` |
| Historical exposure | Strict-complete: five byte-preserved files, 100 unique exposed IDs, 15 historical locked-eval IDs, zero missing/count/provenance/release-contract errors |
| Pilot allocation | 30 `annotation_schema_pilot` questions from pinned official dev; deterministic, source-verified, zero historical overlap, no override |
| New train/dev/locked roles | Not allocated; all three counts are zero |
| Leakage-safe input views | 30 ordered views; 60 selected upstream table/request files are hash-bound, while row/cell values, linked-document IDs/text, answers, traces, and grounding are excluded |
| Granularity proposals | 30 records / 90 coarse-medium-fine representations; model-assisted status is `llm_proposed`, never gold |
| Deterministic pilot checks | 90/90 pass; Draft 2020-12/schema/DAG/root-sink/vocabulary/leakage/live-artifact checks have errors=0 and warnings=0 |
| Structural comparison | `integrity_complete=true`; coarse/medium/fine coverage is 14/13/13 of 30, but these are unreviewed proposal-level assessments |
| Human evidence | Three 30-item review packets exist; real review records=0, disagreement observation count=0/rate=`null`, calibration/evidence/semantic confirmation/selection are all false |
| Schema bundle | Nine Draft 2020-12 schemas and three candidate vocabularies; full exact-pin project-local validation passes with errors=0 and warnings=0 |
| Historical IR v0.2 | Ten original files quarantined read-only under `historical/ir_v0_2/`, authenticated by recovery manifest and immutable Git authority |
| IR validation | 50/50 condition-C graphs and 520 nodes validated; parse/schema/v0.2-validator errors=0; 455 `DEAD_NODE` warnings retained as historical planner-failure evidence |
| Annotation IR bridge | `referenced_validated` claims now require exact IR/schema declarations, seven passed checks, a live hash-bound graph, and matching graph/question/table identities |
| Output safety | All five granularity writers accept identical-byte regeneration, refuse differing existing outputs by default, and require explicit `--overwrite` for an authorized replacement |
| Regression suite | 51/51 tests pass in the exact-pin project-local environment |
| Git continuity | Local `main` is fourteen commits ahead of local `origin/main` after this metadata commit; no push was performed |

The source manifest is the dated, immutable v0.1 source-audit snapshot and still records the historical gate as it existed on 2026-08-21. The current allocation authority is the strict historical manifest plus `split_manifest_v0_1.json`; do not rewrite the source manifest merely to erase its dated audit context.

## Remaining gates

- `LOCAL_COMMIT_NOT_PUSHED`: fourteen local commits are ahead of `origin/main`, and remote writes were not authorized.
- `HUMAN_REVIEW_NOT_PERFORMED`: no real independent reviewer decisions or researcher-approved reviewer attestation exists; calibration, disagreement adjudication, and resolved annotations are unavailable.

These gates make preflight exit 2 (`RESULT=NOT_READY`) even when every deterministic validation passes.

## Next exact task

For the exact 30 IDs/order and the three committed packet payloads:

1. Obtain two independent substantive review sets for each granularity. This means six reviewer-by-granularity JSON files and 180 decisions total; it does not require six different people, but each granularity must have two distinct stable pseudonymous reviewer IDs.
2. Have the researcher verify and approve the reviewers' real-human identity and independence. The code reports `procedural_not_machine_verifiable`; schema-valid files alone are not sufficient attestation.
3. Require every decision to complete `semantic_validity`, `coverage_status`, `ambiguity_present`, `hides_reasoning`, and `excessive_fragmentation`, while binding the exact packet payload and reviewed representation hashes. Abstentions remain uncertain and are excluded from substantive calibration observations.
4. Rerun `compare_operator_granularity.py` with all six review arrays and the three manifests. Preserve raw arrays and hashes; do not copy human claims into the `llm_proposed` representation artifact.
5. Adjudicate every reject, `accept_with_edits`, and substantive assessment disagreement. Only after attestation and adjudication may the project consider a vocabulary-selection request or a versioned schema/vocabulary revision.

The historical condition-C artifact contains answers, evaluator outputs, and later-stage graph evidence. It is permitted only for late-stage IR compatibility regression and historical failure analysis. Never use it, official answer text, weak traces, oracle document IDs, or later-layer labels in question-only semantic, obligation, abstract-topology, operator-topology, few-shot, prompt, or rubric inputs.

Do not allocate annotation train/dev/locked-eval roles, select a final vocabulary, label proposals gold, or claim modeling readiness from structural pass results alone.

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
| `b65aa94` | Advanced the handoff to the allocated annotation pilot |
| `9499ba5` | Defined the strict granularity schema, plan, builders, validator, comparator, and review contract |
| `4e7a414` | Bound the first leakage-safe 30-view artifact and manifest |
| `3ea0330` | Added atomic write-once and explicit-overwrite protection to all granularity writers |
| `52aa21c` | Refreshed the view manifest at the protected implementation commit |
| `7f808d5` | Committed 90 validated representations, 90 checks, three review packets, metrics, reports, and preflight integration |
| metadata child | Updates this handoff, `state/project_state.json`, and final preflight state bindings; it is one descendant of the expected baseline |

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
13. `data_construction/pilot/granularity_representation_plan_v0_1.json`
14. `data_construction/pilot/granularity_input_views_manifest_v0_1.json`
15. `data_construction/pilot/granularity_representations.jsonl`
16. `data_construction/pilot/granularity_deterministic_checks.jsonl`
17. `data_construction/reports/operator_granularity_metrics_v0_1.json`
18. `historical/README.md`
19. `historical/ir_v0_2/recovery_manifest_v0_1.json`

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

- schema bundle: 9 schemas, 3 vocabularies, errors=0, warnings=0;
- granularity pilot: 30 questions, 90 representations, 90 warning-free pass checks, three exact-rendered packets, human reviews=0, disagreement=`N/A`, selection-ready=false;
- IR adapter: 50 records, 520 nodes, parse/schema/validator errors=0, `DEAD_NODE=455`;
- tests: 51 passed;
- preflight: 25 core JSON files parsed, zero validation failures, `RESULT=NOT_READY`, exit 2 only because real human calibration/attestation and remote synchronization remain open;
- Git work tree: clean after the metadata commit;
- local branch: fourteen commits ahead of the local tracking ref.

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

No model runtime, secret, GPU, database, Docker service, or external account is required to reproduce the deterministic validation of the committed pilot. The proposal plan records `model_id=codex_gpt-5`, but exact model revision and raw output were not exposed and seed was unsupported; exact generation replayability is therefore not claimed. Future model runs must record stable model ID, exact revision, seed, prompt artifact, raw output hash, code commit, and run status when the interface exposes them, or explicit unavailable status otherwise.
