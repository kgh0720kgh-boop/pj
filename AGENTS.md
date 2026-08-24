# Portable Project Instructions

## Project purpose

This project constructs a hierarchical HybridQA research dataset for studying the path from natural-language questions to semantic obligations, abstract semantic topology, environment-aware operator topology, grounding, grounded executable graphs, and execution references.

Repository files and Git history are the continuity mechanism. A Codex conversation, local stash, virtual environment, source/model cache, or workstation directory is never canonical project state.

## Current scientific scope

- Use HybridQA only during this reset phase.
- Keep question-only semantics separate from storage- and tool-specific realization.
- Treat operator granularity as an empirical design question.
- Represent valid alternative plans; exact graph match is not the sole correctness target.
- Treat execution success and semantic-plan correctness as separate signals.
- Do not allocate train/dev/locked-eval roles until the pilot evidence justifies a versioned decision; every role must remain disjoint from the authoritatively recovered historical exposure set.

Before changing research artifacts, read:

1. `CODEX_DATA_CONSTRUCTION_RESET_PROMPT_V2_MULTI_DEVICE.md`
2. `HANDOFF_CURRENT.md`
3. `state/project_state.json`
4. `ENVIRONMENT.md`
5. `data_construction/reports/data_source_audit.md`
6. the versioned files under `data_construction/manifests/`

## Historical preservation rule

Historical Week 1-3 artifacts are evidence and feasibility examples, not gold programs. Preserve them byte-for-byte when recovered. Do not delete, rewrite, relabel, or silently move them. Paths under `historical_read_only_paths` in `state/project_state.json` are read-only inputs.

The historical exposure audit is now complete: the five Week 1–3 files were recovered byte-for-byte from researcher-approved provenance, yielding 100 unique exposed IDs and 15 locked-evaluation IDs with zero strict-audit errors. Never use any recovered exposed ID for training, and never use recovered locked-evaluation IDs for prompt/rubric/schema tuning or operator-vocabulary tuning.

## Current phase

The cumulative scale-first question-only AI exploration, candidate-backbone library, 71-question representative environment views, and first two environment-aware signals are complete and committed. The preserved v0.1 human-first lane is deferred and is not the active gate. The active step is a separately frozen equivalence-aware, label-free normalization of the open operator realizations before any provisional vocabulary, grounding, execution, or answer recovery:

- the official HybridQA questions and linked table/document environment remain pinned and audited;
- the strict historical manifest is complete for the five byte-preserved Week 1–3 files: 100 unique exposed IDs, including 15 locked-evaluation IDs, with zero errors;
- the ten-file historical IR v0.2 bundle is quarantined read-only under `historical/ir_v0_2/`, with a recovery manifest and a current-side adapter outside that tree;
- the adapter validates all 50 historical condition-C graphs and 520 nodes with zero parse, Draft 2020-12 schema, or IR-validator errors; its 455 `DEAD_NODE` warnings are historical planner evidence, not successful-pipeline or operator-granularity evidence;
- the schema bundle now contains eleven versioned schemas and three candidate vocabularies; the authoritative result for the current bundle is the latest project-local exact-pin check recorded in the handoff;
- 30 fresh questions were allocated from the pinned official dev source to `annotation_schema_pilot`, with zero historical overlap and no diagnostic override; train/dev/locked-eval remain unallocated at zero;
- the existing leakage-safe operator views, 30 model-assisted records/90 coarse-medium-fine representations, 90 deterministic checks, three hash-bound HTML packets, and v0.1 metrics are byte-preserved as deferred Phase B feasibility evidence; the existing packets are not an approved Phase B human interface and must not be used for current Phase A review;
- the old six-file/180-decision next task is revoked. Future Phase B starts only after Phase A2 and a frozen six-stratum taxonomy: 12 questions × 3 granularities × 2 reviewers = 72 decisions, with precommitted trigger-based expansion to 90 and at most 108 decisions;
- the active study plan remains `question_structure_study_plan_v0_2.json`, and the current operational decision is `FREEZE_EQUIVALENCE_AWARE_OPERATOR_NORMALIZATION_BEFORE_GROUNDING`; no semantic instrument, operator vocabulary, executable graph, or corpus is selected, gold, universally supported, or modeling-ready merely because a schema or run exists;
- the preserved v0.1 Phase A0 artifacts include 30 exact four-field question-only views and one exact-rendered, hash-bound 10-question `phase_a1_batch_01` packet. Packet-only validation passes, while human raw artifacts, records, agreement observations, and adjudications remain zero. Their workflow disposition is `preserved_deferred_not_active_gate`;
- a separately namespaced `ai_question_structure_pipeline_v0_1_run_001` engineering rehearsal has completed across all 30 questions with two AI reviewer passes, blinded third-AI alignment, a 20-question topology-only shadow hold-out, downstream structural comparison, and final analysis. It is explicitly non-human, non-gold, and non-evidentiary: all human counts remain zero and it satisfies no Phase A1, A2, B, grounding, execution, or common-graph gate. Its high core-DAG concordance coexists with a 19-versus-0 reviewer instrument-issue split and scalar alternative-plan conflicts, so do not cite its headline compatibility rate as correctness or human agreement;
- the cumulative N=100 scale run is complete with 100/100 structurally valid question-only AI records. Under the frozen deterministic signatures it has 23 fine labeled families, 17 same-role-contracted families, six topology shapes, and 38 task signatures. Contracted singleton mass is 0.09, first-30-to-new-70 transfer is 50/70, uncertainty is 29/100, and `OTHER` use is 0/100;
- the precommitted N=100 rule returns `EXPAND_UNCHANGED_TO_N300`, because five contracted families absent from the first 30 recur at least twice in the new 70. This remains a conservative operational decision, not semantic-novelty proof: a separately versioned post-hoc audit found all five recurrences confined to a single producer partition and zero cross-partition recurrence;
- primary graph-profile branch/join counts are raw-dependency counts (5/6). After the same transitive reduction used for signatures they are 0/1, and the dominant family grows from 46 to 62 questions under same-role contraction. Always report fine and contracted results together and do not present raw branch/join counts as normalized topology;
- the cumulative N=300 extension is complete with 300/300 structurally valid records and a byte-exact N=100 prefix. Fine/contracted/topology/task family counts are 39/30/10/70; contracted singleton mass is 0.0467, N100-to-new200 transfer is 0.915, final-50 novelty is exactly 0.10, uncertainty is 94/300, and `OTHER` use is 0/300;
- all four precommitted N=1,000 triggers are false: contracted singleton mass and `OTHER` rate do not exceed 0.05, tail novelty equals rather than exceeds 0.10, and only one family meets the material cross-partition rule where two were required. This selects the candidate-library branch but does not establish universal saturation or semantic correctness;
- candidate-backbone library v0.1 is frozen and materialized: all 300 questions are exhaustively and uniquely assigned to 30 unmerged contracted-signature families, with 9 recurrent families, 7 doubletons, and 14 singletons. The deterministic coverage-stress sample contains 71 questions and all 30 families; its ordered-ID SHA-256 is `5403debe2cbe9c7f55ded0a01b49d7c42bf03e53a71350efe269bbd3c0bdcb2e`. This is deliberately rarity-overrepresenting, not a probability sample or prevalence estimate;
- the implementation/source contract was committed at `66bd21948d5269f75d5f816e3f7cfba3941229d5`, the plan was committed while all planned outputs were absent at `f3ac5c47527b46234543d89bc1d7d8034f2723f1`, and the materialized library/sample was committed at `80ce8c2e992e56b1175cf144ff52b0765755dcd2`. The tool input allowlist and question-only record schema exclude environment, answers, traces, grounding, and execution outcomes from selection; broader noninspection remains procedural rather than globally machine-authenticated;
- all 300 AI-processed IDs are recorded in `question_exposure_ledger_v0_3.json` and are ineligible for future unseen-evaluation claims. The separate exploratory allocation leaves 3,066 official-dev questions unexposed and unallocated, while `split_manifest_v0_1.json` remains unchanged at 30 annotation-pilot and zero train/dev/locked-eval allocations;
- representative environment realization v0.1 was committed in five ordered stages: implementation `78fe487327d2fda43cc2ec79203c0a3223d1645b`, pre-raw plan freeze `2e8f6a2c8ee2eb7a3d8a175ea7b8d7f94213175c`, 71 full-table/table-link-closure views `1ff98d3a9cbd7cdd7ae5c7de6676818a57481ec7`, 71 E1 records plus hash-only E2 packets `c3ed836c633859d3575bab1f29d7cf0274df6780`, and final E2/outcomes/checks/metrics `4d4d86885a5294af40653a48cbf12346f699db53`;
- E1 has 64 `adequate`, five `partially_adequate`, and two `indeterminate` records. E2 has 71 `available` records, 93 ungrounded candidates for 72 target variants, and 285 passing deterministic checks. Grounding, execution, and answer recovery remain zero/not evaluated, human evidence remains zero, and the open notation is not a selected vocabulary;
- raw E2 granularity is producer-sensitive: partition candidate counts are 36/19/21/17 and environment-extension-node counts are 95/2/47/0. The reported 17/30 all-candidate family heterogeneity therefore mixes question/environment variation with author split/fuse style and cannot establish or refute one common exact graph;
- the next exact task is to implement and test a reversible, equivalence-aware structural normalizer, then separately freeze its plan while normalized outputs are absent. Its input must omit question/environment text, factual answers, E1 content, operator labels/descriptions, and preserved vocabularies; retain only topology, mappings, roles, typed unresolved slots, variation axes, opaque IDs, and producer routing. Keep the semantic quotient separate from an environment-adapter signature, never erase referent identity, cardinality/tie semantics, output arity, or table-versus-document modality, compare candidates as sets, and stratify by producer before selecting any provisional adapter or beginning grounding;
- because producer and question assignment were not crossed, the normalization plan must precommit a no-fresh-reserve fallback before results are inspected: if partition sensitivity remains unattributable, reuse a frozen 16-question subset containing all seven E1 challenge cases plus nine adequate controls and have two new fresh-context AI authors cover every selected question. This is a confound diagnostic, not human majority review or new unseen evaluation;
- outcome schema v0.2 records five separate signals—backbone adequacy, environment-operator realization, grounding, execution, and answer recovery—and rejects internally contradictory lifecycle/outcome combinations. The 71 actual outcome records are `in_progress`: only the first two signals are evaluated. The schema does not machine-authenticate latent inference or cognitive independence;
- full duplicate review is not the active scaling strategy. Targeted AI rechecks or later human audits are reserved for novel, rare, uncertain, retried, high-frequency, or execution-suspicious cases. If the v0.1 human lane is resumed, reviewer identity, independence, approval, and prior-exposure sign-off remain procedural/manual rather than machine-authenticated, and a separately frozen blinded alignment/adjudication contract is still required before human agreement can be claimed.

The authoritative phase/next task is always the current handoff, not this summary.

## Environment setup

Use the single project-controlled pip contract:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --requirement requirements.txt
```

Do not copy a virtual environment between machines or introduce another dependency manager without an explicit migration decision. See `ENVIRONMENT.md` if the workstation lacks the OS support needed to create a pip-enabled virtual environment.

## Canonical validation commands

Run from the project root:

```sh
python3 -m json.tool state/project_state.json >/dev/null
python3 data_construction/tools/check_schema_bundle.py
python3 -m unittest discover -s tests -v
sh scripts/cross_device_preflight.sh
```

The unqualified schema-bundle command checks JSON, expected files, portable `$id`/local `$ref` resolution, and vocabulary instances with whatever `jsonschema` the system Python provides. The earlier 2026-08-21 system observation was `jsonschema==3.2.0`; the 2026-08-23 system observation is `4.26.0`. Neither substitutes for the exact project pin.

Full schema validation has also passed in the reconstructed project-local pinned environment. Use it for the authoritative schema, IR-reference, and test checks:

```sh
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python -B data_construction/tools/build_representative_environment_realization.py --validate-only
.venv/bin/python -m unittest discover -s tests -v
```

The current bundle contains eleven schemas and three vocabulary instances. Use the latest exact-pin schema-check and test counts recorded in `HANDOFF_CURRENT.md`; historical nine-schema/51-test observations cover an earlier committed bundle and must not be presented as validation of current artifacts. The granularity comparator may still exit `2`, but that preserved Phase B evidence is not the active scale-first gate.

The preflight selects `.venv/bin/python` when present, otherwise `python3`. It parses the core JSON set, validates state/manifest meaning, compares installed packages with every exact requirements pin, runs the schema and IR-reference checks plus the current test suite, and verifies Git/historical gates. Exit `0` means ready, exit `1` means a validation failure, and exit `2` means checks ran without validation failure but a declared readiness blocker remains.

## Data-construction commands

Recover historical exposure only from researcher-authorized provenance, then run the strict builder:

```sh
python3 data_construction/tools/build_historical_manifest.py \
  --recovery-provenance state/historical_recovery_provenance_v0_1.json \
  --overwrite \
  --strict
```

Do not create `state/historical_recovery_provenance_v0_1.json` by inference. The v0.1 release gate requires a researcher-approved full 40-hex canonical Git commit OID and per-file hashes/counts; bytes recovered from a backup/store must first be preserved unchanged in an approved migration commit. `--overwrite` may replace only the current explicitly incomplete v0.1 audit; the builder refuses to replace a complete, released, unknown, or unversioned manifest and never writes to the five historical source paths.

The strict historical audit has passed and the pinned official-source sampler allocated the 30-question pilot without overrides. Do not rerun it merely to replace the committed allocation. Diagnostic overrides never produce a releaseable corpus.

Annotation/tool entry points are documented in `data_construction/README.md`. Do not run corpus or review commands against nonexistent inputs merely to create placeholder outputs.

## Important artifact paths

- `data_construction/manifests/historical_exposed_ids.json`: complete strict audit of 100 unique historical exposures and 15 locked-evaluation IDs.
- `data_construction/manifests/source_manifest_v0_1.json`: audited official source identities, hashes, counts, and reacquisition contract.
- `data_construction/manifests/split_manifest_v0_1.json`: release-eligible 30-question annotation-pilot allocation; train/dev/locked-eval counts remain zero.
- `data_construction/pilot/questions.jsonl`: leakage-safe source records for the 30-question pilot.
- `data_construction/pilot/question_structure_study_plan_v0_1.json`: preserved human-first phase order, three committed-order ten-question batches, stopping branches, and deferred Phase B sampling contract.
- `data_construction/pilot/question_structure_study_plan_v0_2.json`: active scale-first cumulative sampling, extraction, signature, metric, trigger, and later-realization contract.
- `data_construction/pilot/question_only_semantic_views_v0_1.jsonl` and its manifest: 30 exact four-field question-only projections, hash-bound to canonical source/allocation and builder provenance.
- `data_construction/pilot/question_structure_review_packets/`: the preserved 10-question Phase A1 open-coding packet and manifest; it contains zero human annotations and is not the active gate.
- `data_construction/diagnostics/ai_question_structure_pipeline_v0_1/`: frozen-contract AI-only shadow pipeline, immutable run-001 reviewer/alignment/topology artifacts, deterministic metrics, compact report, and an interpretive addendum preserving the non-evidentiary boundary and observed reviewer sensitivity.
- `data_construction/exploration/ai_question_structure_scale_v0_1/`: frozen N=100 and cumulative N=300 contracts, exact question-only pools, primary records, deterministic signatures, recurrence metrics, partition/normalization sensitivity evidence, and the candidate-backbone library/sample v0.1.
- `data_construction/exploration/ai_question_structure_scale_v0_1/contracts/candidate_backbone_library_plan_v0_1.json`: pre-environment library/sampling freeze plan bound to implementation, source, schemas, expected family signatures, and exact selected-ID hashes.
- `data_construction/exploration/ai_question_structure_scale_v0_1/contracts/representative_environment_realization_plan_v0_1.json`: pre-raw exact 71-ID/source/visibility/stage/output freeze plan.
- `data_construction/exploration/ai_question_structure_scale_v0_1/contracts/environment_realization_outcome_schema_v0_1.json`: preserved pre-run five-signal scaffold; actual records use separately versioned v0.2.
- `data_construction/exploration/ai_question_structure_scale_v0_1/contracts/environment_realization_outcome_schema_v0_2.json`: actual five-signal outcome contract with open-notation and variant-qualified realization results.
- `data_construction/exploration/ai_question_structure_scale_v0_1/candidate_backbone_library_v0_1/`: 30-family library, 71-question selection, 102 checks, report, and run manifest; all remain candidate/non-gold.
- `data_construction/exploration/ai_question_structure_scale_v0_1/representative_environment_realization_v0_1/`: 71 views, 71 E1 assessments, 71 E2 realizations/93 candidates, 71 in-progress outcomes, 285 checks, metrics, report, exposure ledger, run manifest, and interpretive addendum.
- `data_construction/manifests/ai_question_structure_exploratory_pool_v0_1.json`: separate non-corpus N=100 allocation with the prior 30 as exact prefix.
- `data_construction/manifests/ai_question_structure_exploratory_pool_v0_2.json`: cumulative N=300 allocation with the frozen N=100 as exact prefix.
- `data_construction/manifests/question_exposure_ledger_v0_1.json`: historical/AI exposure accounting and the 3,266-question untouched reserve identity.
- `data_construction/manifests/question_exposure_ledger_v0_3.json`: completed cumulative N=300 exposure accounting and the 3,066-question untouched reserve identity.
- `data_construction/reports/research_sequencing_decision_v0_1.md`: preserved human-first sequencing rationale and evidence boundary.
- `data_construction/reports/research_sequencing_decision_v0_2.md`: active scale-first sequencing rationale and evidence boundary.
- `data_construction/reports/research_sequencing_decision_v0_3.md`: preserved cumulative N=300 result and precommitted no-N1000 decision.
- `data_construction/reports/research_sequencing_decision_v0_4.md`: materialized candidate-library result, sampling interpretation, five-signal outcome boundary, and representative environment-realization exact next task.
- `data_construction/reports/research_sequencing_decision_v0_5.md`: completed representative-run interpretation and equivalence-aware normalization exact next task.
- `data_construction/schemas/question_only_semantic_view_v0_1.json` and `question_structure_annotation_v0_1.json`: isolated question projection and raw open-coding record contracts. Their scaffold is a tested structural hypothesis, not established semantic truth.
- `data_construction/pilot/granularity_input_views.jsonl` and `granularity_input_views_manifest_v0_1.json`: hash-bound question/operator views that expose table schema and capabilities but no row/cell or linked-document content.
- `data_construction/pilot/granularity_representation_plan_v0_1.json`: structured model-assisted proposal plan; its exact model revision and raw model output were not exposed by the interface, and those limitations are recorded explicitly.
- `data_construction/pilot/granularity_representations.jsonl`: 30 `llm_proposed` records with coarse, medium, and fine candidate DAGs.
- `data_construction/pilot/granularity_deterministic_checks.jsonl`: 90 passing checks bound to live artifacts and validator implementation provenance.
- `data_construction/pilot/review_packets/`: three deterministic legacy Phase B candidate packets and manifests; packet creation does not constitute human review, downloaded review arrays remain external, and these packets are not approved for current Phase A or future blinded Phase B assessment.
- `data_construction/reports/operator_granularity_metrics_v0_1.json`: current structural metrics with human-calibration observations at zero.
- `historical/ir_v0_2/`: quarantined, byte-preserved historical IR contract/runtime and condition-C evidence; never use condition C as an early-layer input.
- `data_construction/tools/validate_ir_v0_2_reference.py`: current-side adapter that validates references without modifying the preserved IR bundle.
- `data_construction/schemas/`: eleven versioned schema files.
- `data_construction/operator_design/`: coarse, medium, and fine v0.1 candidate vocabularies.
- `data_construction/tools/`: deterministic audit, sampling, validation, review, comparison, and statistics tools.
- `tests/test_candidate_backbone_library.py`: candidate-library, representative selection, provenance, leakage, schema, and outcome-separation regression tests.
- `tests/test_representative_environment_realization.py`: representative source projection, staged Git freeze, E1/E2 schema and semantic graph, outcome v0.2, and contamination regression tests.
- `tests/test_data_construction_tools.py`: core standard-library test suite.
- `data_construction/reports/`: source/schema/granularity/pilot/corpus/final research reports.
- `requirements.txt` and `.python-version`: portable runtime contract.
- `HANDOFF_CURRENT.md` and `state/project_state.json`: human- and machine-readable current state.
- `scripts/cross_device_preflight.sh`: non-destructive cross-device readiness check.

## Leakage rules

- Layer 1 question-only annotation or prediction must not see Layer 3/4 gold grounding.
- Do not expose gold answers/spans, old manual graphs, old semantic labels, weak answer nodes, evaluator-only modality flags, oracle document IDs, or later-stage labels to earlier-stage work.
- Official traced files are weak supervision, not human gold, and are forbidden question-only inputs.
- Split roles must be deterministic and disjoint.
- Audit leakage with machine-readable checks before any training or locked scoring.

## Versioning rules

- Use `semantic_schema_v0_1`, `obligation_schema_v0_1`, `operator_vocabulary_v0_1`, `grounding_schema_v0_1`, and `annotation_bundle_v0_1` as the initial version family.
- Never overwrite a released schema, manifest, vocabulary, annotation bundle, or historical artifact.
- If pilot evidence requires a change, create a new version and migration notes.
- Record schema/operator versions, source identity and hashes, IDs, model ID and exact revision, seed, code commit, raw-output hashes, and run status for every research run. If an interface does not expose an exact model revision, seed, or raw output, record the explicit unavailable/not-supported status and treat that as a reproducibility limitation; never invent a value or claim complete model provenance.
- Do not change IR v0.2 for convenience; require repeated annotation evidence and a separately documented version decision.

## Locked-evaluation rules

- Track every historically exposed ID before allocating a new corpus.
- Never use `locked_eval` examples for prompt, rubric, schema, or operator-vocabulary tuning.
- A vocabulary or evaluation-contract change after locked scoring requires a new evaluation version.
- Preserve ambiguous and negative examples, and keep review status truthful. `llm_proposed` is never `gold`.

## Cross-device startup procedure

Before editing on any workstation:

1. Locate the repository root with `git rev-parse --show-toplevel`; never infer project identity from an absolute directory.
2. Read this file, the handoff/state/environment files, and the manifests.
3. Inspect `git status --short --branch`, the current branch, `git rev-parse HEAD`, and `git remote -v`.
4. If local changes are not clearly disposable, stop with `STOP_AND_REPORT_LOCAL_CHANGES`.
5. Fetch only when network/authentication is available and remote reads are authorized.
6. Compare local branch/HEAD with the handoff baseline. An equal HEAD is an exact match and a descendant HEAD is a later linear continuation; if the recorded baseline is unavailable or is not an ancestor of HEAD, stop with `STOP_AND_REPORT_BRANCH_DIVERGENCE`. Never force-push, hard-reset, or discard work silently.
7. Run `sh scripts/cross_device_preflight.sh` and resolve or explicitly preserve every blocker before research runs.

The current directory is a Git repository on `main` with `origin/main` as its upstream. Do not reinitialize it, replace its remote, rewrite history, or push without the researcher decisions recorded in the repository audit and handoff.

## Cross-device shutdown and handoff procedure

Before work is expected to continue on another workstation:

1. Run the preflight and relevant deterministic checks/tests.
2. Update `HANDOFF_CURRENT.md`, `state/project_state.json`, and scientific decision/status artifacts.
3. Verify that no secret, credential, source/model cache, virtual environment, or machine-local path is staged.
4. Inspect `git diff`, `git diff --cached`, and `git status --short --branch`.
5. Commit only intended portable changes; prefer a labeled WIP commit to a stash for handoff.
6. Record the exact branch and commit in both handoff artifacts.
7. Push only when remote writes are explicitly authorized.
8. Record exactly one synchronization state: `SYNCED_TO_REMOTE`, `LOCAL_COMMIT_NOT_PUSHED`, `BLOCKED_REMOTE_AUTH`, `DIRTY_WORKTREE_NOT_HANDOFF_READY`, or `REMOTE_NOT_CONFIGURED`.

Do not coordinate an active Git work tree through consumer folder synchronization. Sequential work may use `research/semantic-topology-data-v1` only after the prior workstation has committed and pushed. Concurrent work must use separate task branches and an explicit reviewed integration step.
