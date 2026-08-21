# Current Cross-Device Handoff

Project: Hierarchical Data Construction for Semantic Execution Topology Induction

Current research phase: Phase 0 historical-provenance recovery gate, with a provisional Phase 1 schema/operator/tool scaffold already implemented.

Current branch: `main`

Current HEAD commit: `6fd427c97b8a3f656e98604f4895031dbd5705f7` (`Update cross-device handoff after repository setup`)
Remote: `origin` → `https://github.com/kgh0720kgh-boop/pj.git`; `main` tracks `origin/main`.

Last completed task: Audited the official HybridQA question and linked table/document sources at pinned commits; created truthful blocked historical/split manifests; integrated eight v0.1 schemas, three candidate operator vocabularies, deterministic tools/tests, the pinned Python contract, and a fail-closed cross-device preflight.

Current scientific decision: `DATA_SOURCE_BLOCKED`. Official HybridQA source capacity is available, but freshness/disjointness cannot be established without the five historical artifacts and researcher-approved authoritative project provenance.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED` (one intended handoff commit is ahead of `origin/main`)

Handoff readiness: Repository transfer ready; scientific gates remain blocked below.

## Startup instructions for the next desktop

```bash
git pull --ff-only
git status --short --branch
git log -1 --oneline
sh scripts/cross_device_preflight.sh
```

Then read `AGENTS.md`, this handoff, `state/project_state.json`, `ENVIRONMENT.md`, `reports/cross_device_repo_audit.md`, the source audit, and all three manifests. Continue from committed files and Git history; Codex conversation state, `.venv`, caches, and local secrets are not portable.

## Artifact snapshot

| Area | Current status |
| --- | --- |
| Official HybridQA sources | Audited and locally verified at pinned upstream commits; portable identities/hashes are in `source_manifest_v0_1.json` |
| Historical exposure | Incomplete; all five required historical files are absent, and empty ID arrays mean not recovered |
| New split | `blocked_not_allocated`; no release-eligible pilot/train/dev/locked-eval roles |
| Schema bundle | 8 Draft 2020-12 schema files present; portable JSON/local-ref check passes with legacy-validator warnings |
| Operator vocabularies | 3 v0.1 candidate vocabularies present: coarse, medium, fine |
| Tools and tests | Implemented; 26/26 tests pass with system CPython 3.10.12 |
| Full Draft 2020-12 validation | Passed for 8 schemas/3 vocabularies with errors=0 and warnings=0 in an ephemeral exact-pin environment; project-local `.venv` reproduction remains pending |
| Git continuity | `main` at `1616684f8505c1b0ee90b956adb292193c172338`, tracking `origin/main`; clean |

## Blocked gates

- `AUTHORITATIVE_PROJECT_PROVENANCE_NOT_AVAILABLE`.
- `HISTORICAL_ARTIFACTS_NOT_AVAILABLE`: the five paths listed below are absent.
- `HISTORICAL_EXPOSED_ID_AUDIT_INCOMPLETE`.
- `FRESH_QUESTION_DISJOINTNESS_NOT_VERIFIABLE`.
- `IR_V0_2_DEFINITION_AND_VALIDATOR_NOT_RECOVERED`: the historical IR schema/operator registry and the external graph parser/validator/artifact dereference path are absent.
- `PROJECT_LOCAL_PINNED_ENVIRONMENT_NOT_RECONSTRUCTED`: the exact-pin full validation passed externally to the work tree, but no reproducible project-local `.venv` exists yet.

## Next exact task

Recover all five historical artifacts byte-for-byte from an authoritative repository commit, verified backup, or approved artifact store. The v0.1 executable release gate can verify only an immutable full Git commit OID: if recovery begins from a backup/store, first obtain researcher approval for a preservation-first Git migration, commit the unchanged five files, and use that canonical commit as authority. Then create researcher-approved `state/historical_recovery_provenance_v0_1.json` with the full 40-hex commit OID and per-file SHA-256/ID counts, and run:

```sh
python3 data_construction/tools/build_historical_manifest.py \
  --recovery-provenance state/historical_recovery_provenance_v0_1.json \
  --overwrite \
  --strict
```

The explicit overwrite is limited to the current incomplete v0.1 audit. The builder refuses to overwrite any complete/released/unknown manifest or the five recovered sources; use a new versioned path for a later released revision. Do not allocate a new split unless that strict command succeeds and the historical manifest is complete. Do not infer or fabricate provenance.

Before corpus/locked-evaluation construction or any modeling-ready claim, also recover the authoritative historical IR v0.2 schema and operator registry byte-for-byte. Connect the original contract to an external parser/validator and graph-artifact dereference path, then record actual parse/operator/type/dependency/reachability validation. Do not recreate or change IR v0.2 for convenience.

Independently, create the project virtual environment when OS support is available, install `requirements.txt`, and run full Draft 2020-12 validation:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --requirement requirements.txt
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python -m unittest discover -s tests -v
```

The repository/remote decision is resolved for this handoff. Use `main` and `origin/main`; do not force-push, rewrite history, or change repository visibility without an explicit decision.

## Required files to read

1. `CODEX_DATA_CONSTRUCTION_RESET_PROMPT_V2_MULTI_DEVICE.md`
2. `AGENTS.md`
3. `HANDOFF_CURRENT.md`
4. `state/project_state.json`
5. `ENVIRONMENT.md`
6. `reports/cross_device_repo_audit.md`
7. `data_construction/reports/data_source_audit.md`
8. `data_construction/manifests/historical_exposed_ids.json`
9. `data_construction/manifests/source_manifest_v0_1.json`
10. `data_construction/manifests/split_manifest_v0_1.json`

## Commands to reproduce current checks

```sh
git rev-parse --show-toplevel
git status --short --branch
git remote -v
python3 --version
git --version
python3 data_construction/tools/check_schema_bundle.py
python3 -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

The first three Git commands are expected to report that this directory is not a Git repository. The preflight must not return `READY` while any declared gate, manifest block, dependency mismatch, test failure, or project-local reproduction requirement remains.

## Known machine-local dependencies

- CPython 3.10.12
- Git 2.34.1
- POSIX-compatible shell
- Bash plus GNU coreutils/findutils (`realpath -m`, `sha256sum`, NUL-safe `find`/`sort`/`xargs`) for official-source reacquisition; the verified baseline is Ubuntu 22.04/WSL, while macOS/BSD requires equivalent tooling
- A newly created local `.venv` using the exact pins in `requirements.txt`
- Official HybridQA source materialization reacquired through the manifest command, not copied from an undocumented cache path

## Known non-portable resources

Codex conversation state, local stashes, virtual environments, official-source/model caches, secrets, credentials, editor/OS metadata, and consumer-synchronized folders are non-portable. A machine-local upstream checkout is not the project repository.

## Do-not-modify historical paths

When recovered, preserve these repository-relative inputs byte-for-byte:

- `data_analysis/week1_sample_100.jsonl`
- `evaluation/week2_eval_ids.json`
- `evaluation/week3_engineering_dev_ids.json`
- `evaluation/week3_locked_eval_ids.json`
- `evaluation/week3_split_manifest.json`

Do not silently reuse any recovered locked-evaluation or historically exposed ID as training/tuning data.
