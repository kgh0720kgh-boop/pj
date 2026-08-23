# Environment Contract

## Current reproducibility status

The continuity scaffold, canonical project Git history, official HybridQA source identities, Python version, exact pip requirements, schema/vocabulary bundle, tools, and tests are portable. Full research-state reconstruction is still blocked by absent authoritative historical recovery provenance, the five historical Week 1-3 artifacts not yet migrated into the repository, and the missing project-local pinned virtual environment. This is a declared blocker, not evidence that there was no historical exposure.

The canonical project repository decision is resolved. The researcher authorized a preservation-first migration from the recovered historical workspace on 2026-08-23. This reset scaffold uses one dependency mechanism: pip requirements pinned in `requirements.txt`.

## Observed baseline

The following versions were observed on 2026-08-21:

| Component | Observed version | Current treatment |
| --- | --- | --- |
| CPython | 3.10.12 | Exact version in `.python-version` |
| Git | 2.34.1 | Compatibility observation; another version is reported for review |
| POSIX shell | available | Required for `scripts/cross_device_preflight.sh` |
| Bash + GNU coreutils/findutils | Ubuntu 22.04/WSL baseline | Required by `fetch_official_hybridqa_sources.sh`; macOS/BSD needs equivalent GNU tooling |
| jsonschema (system) | 3.2.0 | Too old for full Draft 2020-12 validation |
| jsonschema (project pin) | 4.23.0 | Required through `requirements.txt` |

The observations are not tied to a hostname or project absolute path. Operating-system integration is not project identity.

## Dependency policy

The project uses `.python-version` plus fully pinned `requirements.txt`:

- `attrs==24.2.0`
- `jsonschema==4.23.0`
- `jsonschema-specifications==2024.10.1`
- `referencing==0.35.1`
- `rpds-py==0.20.1`

Do not add a competing package manager unless recovered canonical history proves one was already in use and the researcher approves a migration.

Canonical local setup:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --requirement requirements.txt
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python -m unittest discover -s tests -v
sh scripts/cross_device_preflight.sh
```

The earlier workstation observation lacked `ensurepip`/the matching `python3-venv` OS package. On 2026-08-23 this workstation was rechecked: CPython 3.10.12, `ensurepip`, `python3-venv`, and `python3.10-venv` are available, but a project-local `.venv` has not yet been created. Recreate it with the canonical commands above; never copy a virtual environment between workstations.

An ephemeral environment outside the work tree was installed from the exact `requirements.txt` pins. In that environment, `check_schema_bundle.py --require-jsonschema` validated all eight schemas and all three vocabulary instances with errors=0 and warnings=0. This establishes that the pinned dependency set can perform the full Draft 2020-12 check; it does not establish that the current project-local environment is reconstructed.

## Validation levels

The checks intentionally have different meanings:

1. `python3 -m json.tool` and the preflight core-JSON loop prove UTF-8 JSON parseability.
2. `python3 data_construction/tools/check_schema_bundle.py` checks all eight schemas, all three vocabularies, expected identities, portable `$id`/local `$ref` resolution, and available validator behavior. Under system `jsonschema==3.2.0` it warns that Draft 2020-12 meta-validation was not performed and uses a Draft 7 vocabulary-instance fallback.
3. `.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema` is the required project-local reproduction check. The equivalent exact-pin ephemeral check has passed, but the preflight accepts the local environment only after every installed version matches `requirements.txt` and `pip check` passes.
4. `python3 -m unittest discover -s tests -v` currently passes 26/26 tests covering deterministic history/source gates, sampling, leakage checks, review-packet redaction, schema hardening, execution references, and operator-granularity/statistics behavior.

A lower validation level must never be reported as the full Draft 2020-12 result.

## Data and external-runtime contract

The three source/history/split manifests are present. Official HybridQA questions and the linked table/document environment were audited at pinned commits, with stable hashes/counts and a portable reacquisition command recorded in `data_construction/manifests/source_manifest_v0_1.json`. Local source materialization remains an untracked machine-local cache.

The five historical project artifacts themselves are absent. `historical_exposed_ids.json` is explicitly incomplete, and `split_manifest_v0_1.json` is blocked and unallocated. Do not fabricate historical IDs or interpret empty arrays as proof of zero exposure.

When historical artifacts are recovered:

- preserve all five files byte-for-byte;
- record researcher-approved authoritative provenance;
- if the bytes came from a backup/artifact store, preserve them unchanged in a researcher-approved canonical Git commit; the v0.1 release verifier accepts only a full immutable Git commit OID;
- verify per-file SHA-256 and extracted ID counts;
- regenerate the historical manifest with the strict builder;
- treat historical and locked-evaluation inputs as read-only;
- allocate a split only after strict historical completeness and official-source verification both pass.

If official sources must be reacquired, use the manifest-recorded command and pinned commits. Do not commit the source cache. If future artifacts are too large for normal Git, obtain researcher approval for an external artifact store and commit content identities, hashes, and retrieval instructions.

No model runtime, Java, Neo4j, Docker, GPU driver, or additional system library is currently evidenced as required. Future experiments must identify every model by stable model ID plus exact revision, never a cache directory.

## Machine-local resources

These are intentionally not synchronized through Git:

- `.venv/` or `venv/`;
- Python bytecode and test/tool caches;
- official dataset and model download caches;
- generated checkpoints unless an approved artifact policy versions them;
- `.env`, `.env.local`, credentials, SSH keys, and authentication state;
- local Git stashes;
- editor, OS, and Codex session state.

The `.gitignore` excludes common forms of these resources. A source checkout outside the project is a cache, not canonical project history.

## Secrets

No required secret variable names are established, so an `.env.example` is intentionally not fabricated. If an integration later requires a secret:

1. add only its variable name and purpose to `.env.example`;
2. mark it `MACHINE_LOCAL_SECRET_REQUIRED` in the handoff;
3. provision the value independently on each workstation;
4. never commit the value.

## Reconstruction procedure

After a canonical remote exists:

1. Clone the approved repository to any local directory.
2. Check out the branch and HEAD recorded in `state/project_state.json`.
3. Read `AGENTS.md` and `HANDOFF_CURRENT.md`.
4. Install CPython 3.10.12.
5. Create a new local virtual environment and install `requirements.txt`.
6. Reacquire official data with committed IDs, commits, hashes, and manifests.
7. Restore historical inputs only from approved authoritative provenance.
8. Provision any future secrets locally.
9. Run `sh scripts/cross_device_preflight.sh` and the pinned full-validation commands.

Do not use consumer folder synchronization for the active work tree, caches, or virtual environment.
