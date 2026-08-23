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
- Do not release a pilot/train/dev/locked-eval split until historical exposure is authoritatively recovered and disjointness is verified.

Before changing research artifacts, read:

1. `CODEX_DATA_CONSTRUCTION_RESET_PROMPT_V2_MULTI_DEVICE.md`
2. `HANDOFF_CURRENT.md`
3. `state/project_state.json`
4. `ENVIRONMENT.md`
5. `data_construction/reports/data_source_audit.md`
6. the three files under `data_construction/manifests/`

## Historical preservation rule

Historical Week 1-3 artifacts are evidence and feasibility examples, not gold programs. Preserve them byte-for-byte when recovered. Do not delete, rewrite, relabel, or silently move them. Paths under `historical_read_only_paths` in `state/project_state.json` are read-only inputs.

The current empty historical-ID arrays mean “not recovered,” never “zero prior exposure.” Never use recovered locked-evaluation IDs for training, prompt/rubric/schema tuning, or operator-vocabulary tuning.

## Current phase

The project is at the Phase 0 historical-provenance gate:

- the official HybridQA questions and linked table/document environment were audited at pinned upstream commits;
- the source manifest records stable commits, hashes, counts, and reacquisition instructions;
- eight Draft 2020-12 schemas, three candidate operator vocabularies, data-construction tools, and tests are present;
- the five historical Week 1-3 files and authoritative project provenance are absent;
- no research split is allocated or release-eligible;
- full Draft 2020-12 validation passed for all eight schemas and three vocabularies in an ephemeral exact-pin environment with zero errors/warnings, but a project-local `.venv` has not reproduced it.

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

The unqualified schema-bundle command checks JSON, expected files, portable `$id`/local `$ref` resolution, and vocabulary instances. With the currently observed system `jsonschema==3.2.0`, it emits legacy-validator warnings and is not full Draft 2020-12 validation.

Full schema validation was observed to pass in an ephemeral environment matching every requirements pin. Cross-device reconstruction still requires the same check in the project-local pinned environment:

```sh
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python -m unittest discover -s tests -v
```

The preflight selects `.venv/bin/python` when present, otherwise `python3`. It parses the core JSON set, validates state/manifest meaning, compares installed packages with every exact requirements pin, runs the schema checker and current test suite, and verifies Git/historical gates. Exit `0` means ready, exit `1` means a validation failure, and exit `2` means checks ran without validation failure but a declared readiness blocker remains. Recorded ephemeral validation evidence does not make the current machine reproducible until the project-local environment passes the same command.

## Data-construction commands

Recover historical exposure only from researcher-authorized provenance, then run the strict builder:

```sh
python3 data_construction/tools/build_historical_manifest.py \
  --recovery-provenance state/historical_recovery_provenance_v0_1.json \
  --overwrite \
  --strict
```

Do not create `state/historical_recovery_provenance_v0_1.json` by inference. The v0.1 release gate requires a researcher-approved full 40-hex canonical Git commit OID and per-file hashes/counts; bytes recovered from a backup/store must first be preserved unchanged in an approved migration commit. `--overwrite` may replace only the current explicitly incomplete v0.1 audit; the builder refuses to replace a complete, released, unknown, or unversioned manifest and never writes to the five historical source paths.

After the strict historical audit passes, use the pinned official source and deterministic sampler. Diagnostic overrides never produce a releaseable corpus.

Annotation/tool entry points are documented in `data_construction/README.md`. Do not run corpus or review commands against nonexistent inputs merely to create placeholder outputs.

## Important artifact paths

- `data_construction/manifests/historical_exposed_ids.json`: truthful incomplete historical audit until authoritative recovery.
- `data_construction/manifests/source_manifest_v0_1.json`: audited official source identities, hashes, counts, and reacquisition contract.
- `data_construction/manifests/split_manifest_v0_1.json`: blocked, unallocated split contract.
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
