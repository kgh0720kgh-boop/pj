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

The project is in the operator-granularity annotation-pilot phase:

- the official HybridQA questions and linked table/document environment remain pinned and audited;
- the strict historical manifest is complete for the five byte-preserved Week 1–3 files: 100 unique exposed IDs, including 15 locked-evaluation IDs, with zero errors;
- the ten-file historical IR v0.2 bundle is quarantined read-only under `historical/ir_v0_2/`, with a recovery manifest and a current-side adapter outside that tree;
- the adapter validates all 50 historical condition-C graphs and 520 nodes with zero parse, Draft 2020-12 schema, or IR-validator errors; its 455 `DEAD_NODE` warnings are historical planner evidence, not successful-pipeline or operator-granularity evidence;
- a project-local exact-pin `.venv` reproduced full validation of all eight schemas and three vocabularies with zero errors/warnings;
- 30 fresh questions were allocated from the pinned official dev source to `annotation_schema_pilot`, with zero historical overlap and no diagnostic override; train/dev/locked-eval remain unallocated at zero;
- the current in-progress scientific state is `DATA_SOURCE_READY_FOR_ANNOTATION_PILOT`, not a final modeling-ready or gold-corpus decision;
- the next exact task is to build leakage-safe coarse, medium, and fine representations for the same 30 questions, then run deterministic checks and human calibration.

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
.venv/bin/python -m unittest discover -s tests -v
```

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
- `historical/ir_v0_2/`: quarantined, byte-preserved historical IR contract/runtime and condition-C evidence; never use condition C as an early-layer input.
- `data_construction/tools/validate_ir_v0_2_reference.py`: current-side adapter that validates references without modifying the preserved IR bundle.
- `data_construction/schemas/`: eight versioned schema files.
- `data_construction/operator_design/`: coarse, medium, and fine v0.1 candidate vocabularies.
- `data_construction/tools/`: deterministic audit, sampling, validation, review, comparison, and statistics tools.
- `tests/test_data_construction_tools.py`: current standard-library test suite.
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
- Record schema/operator versions, source identity and hashes, IDs, model ID and exact revision, seed, code commit, raw-output hashes, and run status for every research run.
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
