# Cross-Device Repository Audit

## Successful synchronization retry — 2026-09-07

After the researcher completed browser authentication, the current execution
environment confirmed the GitHub account `kgh0720kgh-boop`. The authenticated
CLI was configured as Git's credential helper for github.com; no credential
contents were copied into the repository or printed unmasked.

The worktree was clean, the handoff baseline was an ancestor, and fetch showed
48 local-only and zero remote-only commits. The exact-pin preflight reproduced
236 passing tests, 161 core JSON/JSONL files and zero validation failures.
A dry-run push succeeded, followed by the normal push of `main` to the existing
origin. Direct `ls-remote` verification returned
`65cc335ee3f0169a5c05ec94667151609a3d1d27`; local/tracking ahead/behind was 0/0.

This supersedes the authentication blocker in the earlier attempt below.
`HANDOFF_CURRENT.md`, `state/project_state.json` and `DESKTOP_HANDOFF.md` now
record `SYNCED_TO_REMOTE`. Their completion-metadata commit follows the verified
baseline and must also be pushed and checked against the live remote before
handoff is declared complete. The baseline intentionally is not the hash of
the commit containing its own metadata. No history, research output, frozen
contract, exposure allocation, credential or cache was replaced or uploaded
outside the authorized portable-history transfer.

The remaining `QUESTION_FREE_ISOLATION_TRANSPORT_NOT_VERIFIED` gate is scientific,
not a Git transfer failure. It remains active; no new research author was run.

## Synchronization authorization — 2026-09-07

The researcher explicitly requested synchronizing this repository and saving
a Markdown handoff for continuation on another desktop. This authorizes fetch
and normal fast-forward push of the current portable `main` history and its
handoff metadata to the existing `origin` at
`https://github.com/kgh0720kgh-boop/pj.git` for this transfer.
It does not authorize force-push, history rewriting, discarding workstation
changes, publishing credentials/caches, or new research/model runs.

At transfer startup, HEAD was `67a70f9c206bfcf23c7c35512d08235d22143338`,
the working tree was clean, and a successful fetch reported 46 local-only
commits and zero remote-only commits. The isolation-design freeze is an ancestor
of HEAD. Transfer instructions are in `DESKTOP_HANDOFF.md`; the authoritative
final synchronization state is recorded in `HANDOFF_CURRENT.md` and
`state/project_state.json` after the push is verified.

This authorization supersedes the older addenda's lack of remote-write
permission for this transfer only; their dated observations remain preserved.

The transfer-document commit is `4ca7aa46460397621db4e3efd632975c843364ef`.
The normal HTTPS push then failed: Git could not obtain a username with
terminal prompts disabled. Read-only checks found no configured Git credential
helper, installed GitHub CLI/credential-manager command, GitHub token environment,
or SSH agent. No credential value was printed or written.
A noninteractive SSH check with strict host-key verification also stopped at
an unknown GitHub host key; no trust entries or SSH settings were changed.
`git ls-remote origin refs/heads/main` still returned
`906df10a0a71ddf677c51c4a7b67ac6b1cc7d560`. The active synchronization state
is `BLOCKED_REMOTE_AUTH`, not a successful remote transfer. The GitHub connector's
new-commit API does not preserve the existing commit metadata/identities and was
not used to reconstruct or replace the frozen history. Authenticate Git in the
execution environment before retrying the authorized normal push.

## Current-state addendum — 2026-08-24

This addendum supersedes the active-status statements in the 2026-08-23 addendum while preserving both older sections as dated evidence.

| Field | Current state |
| --- | --- |
| Git root | resolved repository root |
| Branch | `main` |
| Expected handoff baseline | `5c73da72e93fa534711e222eb53ac02140596946` |
| Remote-write authorization | not granted |
| Synchronization state | `LOCAL_COMMIT_NOT_PUSHED` |
| Scientific decision | `FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_ENVIRONMENT_REALIZATION` |
| Active gate | candidate-backbone library and representative-sampling contract freeze |

The scale-first question-only AI semantic-backbone exploration is complete through cumulative N=300. The preserved v0.1 human lane is deferred rather than deleted or completed; all human evidence counts remain zero. The released split manifest remains unchanged at 30 annotation-pilot questions and zero train/dev/locked-eval allocations.

The frozen cumulative N=100 run produced 100/100 structurally valid, non-human, non-gold records. Its deterministic summaries contain 23 fine labeled families, 17 same-role-contracted families, six topology shapes, and 38 task signatures. Contracted singleton mass is 0.09 and first-30-to-new-70 transfer is 50/70. The precommitted rule returns `EXPAND_UNCHANGED_TO_N300`.

A separately versioned post-hoc audit records that all five triggering recurring-new contracted families are confined to one producer partition and have zero cross-partition recurrence. Raw branch/join counts of 5/6 reduce to normalized counts of 0/1, and same-role contraction grows the dominant family from 46 to 62 questions. These facts restrict interpretation without rewriting the frozen primary decision: N=300 is a conservative next measurement, not proof that the five families are semantically novel.

The cumulative N=300 run preserves N=100 as a byte-exact prefix and validates 300/300 records. Fine/contracted/topology/task family counts are 39/30/10/70, contracted singleton mass is 0.0467, and N100-to-new200 transfer is 0.915. All four precommitted N=1,000 triggers are false, so the selected branch is candidate-library freeze and representative environment realization. All 300 processed IDs are excluded from future unseen-evaluation claims, and 3,066 official-dev questions remain unexposed and unallocated.

The exact next task is to freeze a versioned 30-family candidate library and frequency/rarity-stratified representative-selection contract before environment inspection. Fine/topology/task crosswalks, evidence strength, and support information must remain explicit; same-role contraction is not semantic equivalence. Only after representative IDs are committed may environment-aware operator realization begin.

## Current-state addendum — 2026-08-23

This addendum records the state after the dated 2026-08-21 audit below. The older absence/blocking observations remain intact as historical evidence; they no longer describe the current repository.

| Field | Current state |
| --- | --- |
| Git root | resolved repository root |
| Branch | `main` |
| Upstream baseline | `origin/main` at `c337e9a67c15cd68fbb53eefb79bef90a6f9f242` |
| Local history | multiple linear local commits ahead of `origin/main` |
| Remote-write authorization | not granted |
| Synchronization state | `LOCAL_COMMIT_NOT_PUSHED` |

The five required Week 1–3 files were recovered byte-for-byte from the researcher-approved historical workspace and preserved in commit `1995c0cf79ab8e987773041d456d4a1b8df19793`. The verified researcher-approved receipt is `state/historical_recovery_provenance_v0_1.json`. The strict manifest is complete with 100 unique exposed IDs, 15 historical locked-evaluation IDs, no missing files, no expected-count mismatches, and no provenance/release-contract errors.

Ten authoritative IR v0.2 files were separately preserved as read-only evidence in commit `dcc5ac5c14e9acb5c689b400a4046708b6837ac3`, together with a recovery manifest. A current-side adapter baseline validated all 50 condition C records and 520 nodes with zero JSONL parse, Draft 2020-12 graph-schema, or explicitly injected v0.2-registry validator errors. It reproduced 455 `DEAD_NODE` warnings; those warnings are retained as known historical planner-failure evidence.

The bundle now contains 11 schemas and 3 vocabulary instances. The earlier exact-pin 9-schema/51-test result is retained as historical evidence for its committed bundle; the authoritative current-bundle schema and test results must be taken from the latest handoff rather than extrapolated from that observation.

A deterministic, source-verified 30-question `annotation_schema_pilot` is allocated with `release_eligible=true`, no diagnostic override, zero overlap with the recovered 100-ID historical exclusion set, and no forbidden answer/trace fields in the question source artifact. New annotation train, dev, and locked-evaluation roles each remain at zero. The active sequence is now question-only raw open coding, separately frozen blinded alignment, held-out confirmation, deferred environment-aware operator granularity, then representative grounding/execution.

The prior 30 model-assisted records/90 coarse-medium-fine representations, 90 warning-free checks, three hash-bound packets, and v0.1 metrics remain byte-preserved as deferred Phase B feasibility evidence. They are not an approved Phase A or future blinded Phase B review UI, and the old 180-decision task is revoked. Future Phase B freezes six strata after Phase A2, begins at `12 × 3 × 2 = 72` decisions, and expands through precommitted triggers to 90 and at most 108.

The decision remains `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`. Phase A0 is now materialized as 30 exact question-only views plus a hash-bound first-batch packet, and packet-only validation passes. Two researcher-approved, mutually independent, exposure-naive real humans must now independently annotate the first committed-order ten questions, yielding two files and 20 raw records. The question-1 discussion is protocol analysis and zero human evidence; affected exposed reviewers are excluded. Identity, independence, approval, exposure sign-off, and the single-file UI transition are procedural rather than machine-authenticated. Raw record validity alone cannot establish free-text contamination absence or semantic agreement; a separate blinded alignment/adjudication contract and comparator must be frozen before agreement, and an independent blinded held-out topology pass is required before cross-level claims or Phase B normalization.

## Historical audit snapshot — 2026-08-21

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
