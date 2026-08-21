# Cross-Device Repository Audit

Audit date: 2026-08-21

Scope: current project directory, continuity metadata, integrated research scaffold, and a bounded read-only search for relevant Git metadata/source material. This audit was superseded by the initial repository snapshot at `1616684f8505c1b0ee90b956adb292193c172338`, pushed to `origin/main`.

## Repository state

| Field | Observed value |
| --- | --- |
| Git root | repository root |
| Current branch | `main` |
| HEAD | `1616684f8505c1b0ee90b956adb292193c172338` |
| Remotes | `origin` → `https://github.com/kgh0720kgh-boop/pj.git` |
| Working-tree status | clean |
| Git-untracked files | none |
| Unpushed commits | none known; tracks `origin/main` |
| Stash state | empty |
| Synchronization state | `SYNCED_TO_REMOTE` |

The earlier non-repository observation is historical. The current project is a clean Git work tree on `main`, synchronized with `origin/main`.

A separate upstream HybridQA source-audit checkout exists in a machine-local cache outside the project. It supports source verification but contains neither approved project history nor the five historical Week 1-3 artifacts. It is not the canonical project repository and is deliberately excluded from Git continuity.

## Integrated portable artifact inventory

The initial one-file snapshot has been expanded without fabricating missing research history:

- official-source, historical-exposure, and split manifests are present;
- official HybridQA questions and linked table/document sources are pinned by commit, artifact/tree hashes, counts, and portable reacquisition instructions;
- the historical manifest remains explicitly incomplete, and the split manifest remains blocked/unallocated;
- eight Draft 2020-12 schema files and three coarse/medium/fine candidate vocabulary files are present;
- deterministic history/source audit, sampling, schema, annotation, review, granularity, and statistics tools are present;
- a standard-library unit-test suite is present;
- CPython `3.10.12` is pinned through `.python-version`;
- all Python packages are exactly pinned in `requirements.txt`.

These files improve reproducibility but do not replace canonical Git provenance or the missing historical evidence.

## Source and historical evidence

Official HybridQA source retrieval is `available_and_locally_verified` at the commits recorded in `data_construction/manifests/source_manifest_v0_1.json`. The audited official dev pool has sufficient physical capacity for the requested pilot/corpus size.

Research release remains blocked because:

- all five historical project inputs are absent;
- authoritative project recovery provenance is unavailable;
- empty recovered-ID arrays mean “not recovered,” not “zero prior exposure”;
- fresh-question disjointness cannot be verified;
- `split_manifest_v0_1.json` is `blocked_not_allocated` and `release_eligible=false`.

Current scientific status is therefore `DATA_SOURCE_BLOCKED`, even though official upstream source capacity is available.

## Environment observations

- CPython: `3.10.12`
- Git: `2.34.1`
- system jsonschema: `3.2.0`
- required jsonschema: `4.23.0`

The system package set does not match the five exact requirements pins. In particular, the observed system jsonschema cannot perform Draft 2020-12 meta-validation. The structural bundle checker succeeds with explicit legacy-validator warnings and a Draft 7 vocabulary-instance fallback.

Separately, an ephemeral environment outside the work tree was installed from the exact requirements pins. It ran the required Draft 2020-12 meta-validation and vocabulary-instance validation for 8 schemas/3 vocabularies with errors=0 and warnings=0. This is valid full-schema evidence, but the project-local `.venv` remains unreconstructed and is still a portability blocker.

## Verification performed

- `sh -n scripts/cross_device_preflight.sh`: exit `0`.
- `python3 -m json.tool state/project_state.json`: exit `0`.
- Core JSON parse set: 15 files parsed.
- State/manifest semantic contract: passed for the current incomplete `strict_builder` historical shape and `blocked_placeholder` split shape.
- Schema bundle structural/local-reference check: 8 schemas and 3 vocabularies passed, with legacy-validator warnings.
- Standard-library unit tests: 26/26 passed.
- Full Draft 2020-12 validation in an ephemeral exact-pin environment: 8 schemas/3 vocabularies, errors=0, warnings=0.
- Project-local exact-pin reproduction: pending; no project `.venv` exists.
- `sh scripts/cross_device_preflight.sh`: `RESULT=NOT_READY`, exit `2`, zero check failures. Declared blockers include repository/remote absence, historical/provenance gates, and project-local pinned-environment reconstruction.
- The same script resolves its project root from its own location and does not rely on a hostname or project absolute path.

The preflight also understands the future complete strict historical state and allocated split-manifest shape. A future allocated split is accepted only if official source verification, authoritative historical completeness, historical-ID exclusion, question-only leakage controls, role isolation/disjointness, per-role file hashes/counts, and locked-eval tuning exclusion all pass.

## Decision gates

- The repository/remote decision is resolved for the current handoff: `main` tracks `origin/main`.
- `AUTHORITATIVE_PROJECT_PROVENANCE_NOT_AVAILABLE`.
- `HISTORICAL_ARTIFACTS_NOT_AVAILABLE`.
- `PROJECT_LOCAL_PINNED_ENVIRONMENT_NOT_RECONSTRUCTED`.

No local stash can resolve these gates and no conversation state is an acceptable substitute.

## Preservation-first repository plan

Do not execute this plan until the researcher resolves the repository/remote decisions.

1. Search researcher-provided locations and accounts for canonical project history; compare commits/manifests, not directory names.
2. If a canonical remote exists, clone it into a clean directory and reconcile current portable artifacts through an explicit reviewed import. Never overwrite either copy.
3. If no repository exists and initialization is authorized, inventory/hash current files before initializing Git.
4. Audit `.gitignore`, staged paths, secrets, credentials, caches, virtual environments, official-source materialization, and large artifacts before the first commit.
5. Create the approved branch; the reset specification suggests `research/semantic-topology-data-v1` for sequential work.
6. Configure a remote only after provider, identity, and visibility are approved.
7. Push only with explicit remote-write authorization and record the exact branch/commit in both handoff artifacts.
8. Report exactly one synchronization state: `SYNCED_TO_REMOTE`, `LOCAL_COMMIT_NOT_PUSHED`, `BLOCKED_REMOTE_AUTH`, `DIRTY_WORKTREE_NOT_HANDOFF_READY`, or `REMOTE_NOT_CONFIGURED`.

Concurrent workstations must use separate task branches and an explicit integration step. Consumer folder synchronization must not coordinate an active Git work tree.

## Remaining acceptance gaps

- Clone-equivalent reconstruction is possible from `origin/main`.
- The canonical current handoff commit is `1616684f8505c1b0ee90b956adb292193c172338`.
- The five historical inputs and approved recovery provenance are absent.
- No fresh split can be proven disjoint or release-eligible.
- The pinned project-local dependency environment has not been created on this machine, although equivalent ephemeral exact-pin full validation passed.

Rerun `sh scripts/cross_device_preflight.sh` after each gate changes. A transfer-ready state requires committed portable artifacts and an explicit synchronization result.
