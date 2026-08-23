# Environment Contract

## Current reproducibility status

The continuity scaffold, canonical project Git history, official HybridQA source identities, Python version, exact pip requirements, schema/vocabulary bundle, tools, tests, historical-exposure audit, and recovered IR v0.2 evidence are portable. On 2026-08-23 the project-local pinned virtual environment was reconstructed. The current bundle contains eleven schemas and three vocabularies; the latest authoritative exact-pin result and test count are recorded in `HANDOFF_CURRENT.md` after each bundle change.

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

On 2026-08-23 the unqualified system Python instead exposed `jsonschema==4.26.0`. It can perform Draft 2020-12 checks, but it is not the exact project contract; authoritative reproduction uses `.venv` and the `4.23.0` pin.

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
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python -m unittest discover -s tests -v
sh scripts/cross_device_preflight.sh
```

The earlier workstation observation lacked `ensurepip`/the matching `python3-venv` OS package. On 2026-08-23 this workstation was rechecked: CPython 3.10.12, `ensurepip`, `python3-venv`, and `python3.10-venv` were available, and a fresh project-local `.venv` was created from the exact pins. Recreate it independently on every workstation; never copy a virtual environment between workstations.

The earlier exact-pin ephemeral validation of the then-current eight-schema/three-vocabulary bundle and the later nine-schema/three-vocabulary project-local result remain historical evidence. Neither may be rewritten as if it covered the current eleven-schema Phase A0 bundle; rerun the exact-pin command after changing the bundle and record that result separately.

## Validation levels

The checks intentionally have different meanings:

1. `python3 -m json.tool` and the preflight core-JSON loop prove UTF-8 JSON parseability.
2. `python3 data_construction/tools/check_schema_bundle.py` checks all eleven schemas, all three vocabularies, expected identities, portable `$id`/local `$ref` resolution, and available validator behavior. Under the 2026-08-21 system `jsonschema==3.2.0` it used a warned Draft 7 fallback; the 2026-08-23 system has `4.26.0`, but an unpinned system result is still not the project reproduction result.
3. `.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema` is the required project-local reproduction check. It now passes with every installed version matching `requirements.txt` and `pip check` passing.
4. `.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all` authenticates the ten preserved files against their recovery manifest and immutable Git authority, loads the recovered runtime in isolation, and validates all 50 condition-C graphs. The current result is 50/50 graphs, 520 nodes, zero parse/schema/IR-validator errors, and 455 `DEAD_NODE` warnings.
5. `.venv/bin/python -m unittest discover -s tests -v` runs the deterministic regression suite covering history/source gates, sampling, leakage checks, exact review-packet rendering, write-once output protection, schema hardening, IR references, question-only Phase A0 contracts, and deferred operator-granularity/statistics behavior. Use the latest count recorded in the handoff; the earlier 51-test result predates the Phase A0 additions.

A lower validation level must never be reported as the full Draft 2020-12 result.

## Data and external-runtime contract

The three source/history/split manifests are present. Official HybridQA questions and the linked table/document environment were audited at pinned commits, with stable hashes/counts and a portable reacquisition command recorded in `data_construction/manifests/source_manifest_v0_1.json`. Local source materialization remains an untracked machine-local cache.

The five historical Week 1–3 artifacts were preserved byte-for-byte with researcher-approved immutable Git provenance. The strict manifest records 100 unique exposed IDs, including 15 locked-evaluation IDs, with no missing files, count mismatches, or provenance errors. The deterministic sampler then allocated 30 pinned-official-dev questions to `annotation_schema_pilot` with zero historical overlap and no override; train/dev/locked-eval remain unallocated at zero.

The ten-file IR v0.2 evidence bundle is quarantined read-only under `historical/ir_v0_2/` and bound to its recovery manifest. Its condition-C JSONL contains answers and evaluator outputs, so it is late-stage historical evidence only and must never enter question-only semantic, obligation, abstract-topology, or operator-topology views. The current-side adapter lives outside the historical tree.

The active sequence now begins with question-only raw open coding. Its view contract permits exactly opaque question ID and question text; its raw scaffold is a structural hypothesis under test and supplies no closed semantic-label or operator enum. The single self-contained HTML enforces its batch lock only through the normal UI and attestation, not against source/DOM inspection, and the forbidden-key audit does not semantically inspect allowed free text. Raw schema, hash, and structural leakage checks therefore establish limited record integrity only. Cross-reviewer semantic alignment, adjudication, and agreement remain a separately versioned contract to be built and frozen after two independent raw sets exist.

The 30-question granularity pilot remains materialized as a committed, hash-bound input-view contract plus 30 model-assisted records containing 90 coarse/medium/fine candidates, 90 deterministic checks, three self-contained HTML packets, and v0.1 metrics. These bytes are preserved as deferred Phase B feasibility evidence. The packets contain zero human reviews and are not approved for current Phase A or future blinded Phase B assessment. The old 180-decision task is revoked; future Phase B uses a six-stratum, Phase-A-derived sample of 72 decisions with precommitted trigger-based expansion to 90 and at most 108.

The question-only implementation, 30 exact four-field views, and first 10-question packet are committed, and exact packet-only validation passes. The immediate human task is now for two researcher-approved, mutually independent, exposure-naive real humans to independently annotate that first committed-order batch, producing two files and 20 raw records. Reviewer identity, independence, approval, and prior-exposure status are manual procedural sign-offs, not machine-authenticated facts. The earlier question-1 discussion contributes zero human evidence, and exposed reviewers are excluded from affected exposure-naive work.

The current proposal provenance truthfully records `model_id=codex_gpt-5`, but the interface exposed neither an exact model revision nor raw model output, and did not support a seed. The plan and representations record `revision_not_exposed`, `not_exposed_by_interface`, and `not_supported` rather than fabricating those values. This is a reproducibility limitation: the structured proposal artifact and its hashes are portable, but the original model generation cannot be claimed as exactly replayable.

If official sources must be reacquired, use the manifest-recorded command and pinned commits. Do not commit the source cache. If future artifacts are too large for normal Git, obtain researcher approval for an external artifact store and commit content identities, hashes, and retrieval instructions.

No model runtime, Java, Neo4j, Docker, GPU driver, or additional system library is currently evidenced as required. The recovered Python IR runtime is historical validation evidence loaded in isolation by the adapter, not a model runtime or authorization to execute condition-C data in early layers. Future experiments must identify every model by stable model ID plus exact revision, never a cache directory; when an interface does not expose a required identity or raw-output artifact, record that fact explicitly and do not claim complete replayability.

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

From an approved canonical branch:

1. Clone the approved repository to any local directory.
2. Check out the branch and HEAD recorded in `state/project_state.json`.
3. Read `AGENTS.md` and `HANDOFF_CURRENT.md`.
4. Install CPython 3.10.12.
5. Create a new local virtual environment and install `requirements.txt`.
6. Reacquire official data with committed IDs, commits, hashes, and manifests.
7. Verify the committed historical inputs and both recovery manifests; never replace them with machine-local copies.
8. Provision any future secrets locally.
9. Run `sh scripts/cross_device_preflight.sh` and the pinned full-validation commands.

Do not use consumer folder synchronization for the active work tree, caches, or virtual environment.
