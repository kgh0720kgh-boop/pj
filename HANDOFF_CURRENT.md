# Current handoff

Date: 2026-08-25

Current research phase: **representative environment-realization contract
freeze after the candidate-backbone library and pre-environment sample were
frozen and materialized.**

Active branch: `main`

Expected handoff baseline: `80ce8c2e992e56b1175cf144ff52b0765755dcd2`

The expected baseline contains the implementation contract, a separately
committed freeze plan, and the deterministic candidate-library/sample outputs.
This metadata handoff is one linear descendant of that baseline.

Last completed task: retained all 30 cumulative N=300 contracted-signature
families without post-hoc semantic merging, materialized their complete
membership/support/crosswalk records, and committed a deterministic
71-question coverage-stress sample without environment or outcome fields as
selection features.

Next exact task: before inspecting row/cell values or linked-document contents
for this 71-ID realization stage, freeze a versioned environment input-view and
realization protocol bound to the committed ID order and pinned official
sources. Then materialize sanitized environment views and begin instance-level
environment-aware operator realization, while keeping backbone adequacy,
grounding, execution, and answer recovery separate.

Current scientific decision:
`FREEZE_CANDIDATE_BACKBONE_LIBRARY_AND_BEGIN_REPRESENTATIVE_ENVIRONMENT_REALIZATION`.

Study status:
`candidate_backbone_library_and_pre_environment_representative_selection_complete_environment_realization_not_started_human_validation_deferred`.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED`.

Handoff readiness: Not ready. At the expected baseline, local `main` is 40
commits ahead of local `origin/main`; the metadata commit containing this
handoff is projected to make it 41 commits ahead. No push was performed or
authorized.

## Authoritative status

| Area | Current evidence |
| --- | --- |
| Official source | HybridQA table corpus and released train/dev remain pinned and hash-audited at manifest-recorded upstream commits |
| Historical exposure | Five recovered Week 1--3 files are byte-preserved; 100 unique exposed IDs and 15 locked-evaluation IDs; strict errors=0 |
| Historical IR v0.2 | Ten files are quarantined read-only; 50 graphs/520 nodes validate with 0 parse/schema/validator errors and 455 preserved `DEAD_NODE` warnings |
| Released role allocation | `split_manifest_v0_1.json` remains unchanged: annotation-pilot=30, train=0, dev=0, locked-eval=0 |
| N=300 extraction integrity | 300/300 question-only records pass; N=100 bytes are an exact prefix; all 300 IDs are AI-exposed and 3,066 official-dev questions remain unexposed/unallocated |
| N=300 recurrence | Fine/contracted/topology/task families=39/30/10/70; contracted singleton mass=0.0467; N100-to-new200 transfer=0.915; final-50 novelty=0.10 |
| N=1,000 branch | All four precommitted triggers are false, selecting candidate-library freeze and representative environment realization |
| Candidate library | 30/30 contracted-signature families materialized; 300/300 IDs occur exactly once; no post-hoc semantic merge |
| Family evidence tiers | Recurrent=9, doubleton=7, singleton=14; these labels record recurrence only, not correctness |
| Representative sample | 71 unique questions cover all 30 families; ordered-ID SHA-256=`5403debe2cbe9c7f55ded0a01b49d7c42bf03e53a71350efe269bbd3c0bdcb2e` |
| Sample interpretation | Deterministic rarity/variation coverage stress test, not a probability sample and not a prevalence estimate |
| Candidate checks | 102/102 pass: one bundle, 30 family, and 71 selection checks |
| Outcome separation | Future schema requires backbone adequacy, environment realization, grounding, execution, and answer recovery as independent signals |
| Environment realization | Input/visibility/run protocol not frozen; new 71-ID representative environment views=0; realization records=0; actual status=`not_started` |
| Human evidence | Human raw files=0, records=0, agreement observations=0, adjudications=0; the preserved human-first lane remains deferred |
| Operator granularity | The old 30-record/90-representation feasibility bundle remains deferred; no vocabulary is selected |

## What the library result means

The 30 families are exact equivalence classes under one frozen AI
question-only extractor and one deterministic same-role-contracted signature.
The library preserves all observed families rather than merging similar-looking
ones after seeing frequency. It also keeps fine, topology, and task crosswalks
so contraction sensitivity remains visible.

The frequency distribution is highly uneven: one dominant family contains 201
questions, while 14 families are singletons and seven are doubletons. A simple
uniform or prevalence-oriented sample does not guarantee coverage of rare
shapes, so the frozen quota `min(n, 1 + ceil(log2(n)))` deliberately selects at
least one member of every family and more members from internally varied
high-frequency families. The result is 71 questions:

| Frequency stratum | Families | Source questions | Selected |
| --- | ---: | ---: | ---: |
| singleton 1 | 14 | 14 | 14 |
| doubleton 2 | 7 | 14 | 14 |
| recurrent 3--9 | 5 | 27 | 18 |
| recurrent 10--19 | 2 | 24 | 10 |
| recurrent 20--99 | 1 | 20 | 6 |
| dominant 100+ | 1 | 201 | 9 |

Within each family, the rule greedily covers fine signature, topology
signature, task signature, N100/new200 slice, producer partition, record
status, and alternative-graph presence; ties use a frozen seeded SHA-256 rank.
Question text is not a ranking feature.

This design is useful for finding realization failures across structural and
diagnostic variation. It cannot estimate population prevalence because rare
families are intentionally overrepresented, the axes are correlated,
N100/new200 and producer context are partly confounded, producer partitions are
not independent reviewers, and status/alternative presence are AI-generated.

Nothing here establishes semantic correctness, universal saturation, a common
executable graph, operator-vocabulary adequacy, grounding success, execution
success, or answer accuracy. Same-role contraction can still hide distinct
referent hops, and a `complete` source record is not a correctness label.

## Freeze and provenance sequence

The ordering is part of the evidence:

1. `66bd21948d5269f75d5f816e3f7cfba3941229d5` committed the builder, three schemas, and regression tests. It also binds the common runtime, frozen N=300 analyzer/normalizer, question-only source schema, and exact committed source bytes.
2. `f3ac5c47527b46234543d89bc1d7d8034f2723f1` committed the plan while all five planned outputs were absent. The plan freezes the 30-family result, 71 selected IDs, strata, hashes, and five independent future outcomes.
3. `80ce8c2e992e56b1175cf144ff52b0765755dcd2` materialized the 30-family JSONL, 71-question selection, 102 checks, report, and run manifest.

The builder rejects dirty or untracked source/implementation bytes, external
input paths, environment-like keys in source records, changed trigger or
exposure contracts, unsafe output paths, uncommitted plans, incorrect Git
ancestry, outputs that existed at freeze time, and any byte mismatch during
`--validate-only` reconstruction.

## Declared blockers

- `LOCAL_COMMIT_NOT_PUSHED`: portable work exists only in local commits; remote writes were not authorized.
- `REPRESENTATIVE_ENVIRONMENT_REALIZATION_NOT_STARTED`: the 71-ID environment input/visibility/run protocol and sanitized views have not been frozen or materialized.

`CANDIDATE_BACKBONE_LIBRARY_NOT_FROZEN` is resolved. The absence of human review
is not a current blocker; it remains a truthful zero-count evidence boundary
and may become relevant for later targeted claims.

## Exact next task: representative environment realization

1. Freeze a versioned environment-view schema, visibility allowlist, source-binding contract, realization record schema, prompt/procedure, and planned output paths before inspecting row/cell values or linked-document contents for this 71-ID realization stage.
2. Bind the contract to the exact 71-ID selection order and pinned official HybridQA table/document source hashes.
3. Permit only question/backbone context and environment content needed to author a realization. Exclude factual answers, official traces, historical condition-C graphs, execution outcomes, and prior coarse/medium/fine operator proposals.
4. Do not silently choose one preserved candidate operator vocabulary. Treat operator granularity as an empirical question and allow unsupported or alternative realizations.
5. After the contract is committed, materialize sanitized environment views for exactly the selected 71 IDs and validate their ID/order/hash/source bindings.
6. Produce instance-level environment-aware operator realizations and separately assess whether each frozen candidate backbone remains adequate in its actual environment.
7. Leave grounding, execution, and answer recovery unscored until their own versioned inputs and procedures are invoked; later downstream results must not overwrite upstream semantic assessments.

This is not authorization to use historical answer-bearing condition-C files or
official answers/traces as realization-authoring inputs.

## Evidence and exposure boundaries

- All 300 source records and all 30 families are `ai_exploratory_non_human_non_gold`.
- All 300 processed IDs are excluded from future unseen-evaluation claims; selection of 71 changes no corpus role.
- The library builder enforces a bound question-only source schema. Table/document identity or content, factual answers, traces, operator proposals, grounding, execution, and answer-recovery outcomes are forbidden selection inputs.
- The artifacts establish that environment and outcome fields were not supplied to the selection ranker. Any claim about what researchers may have seen in separate earlier work is procedural, not globally machine-authenticated.
- The stable model identity contract is `codex_gpt-5`; no immutable exact revision or seed was exposed, and exact generation replayability or statistical reviewer independence is not claimed.
- The v0.1 human packet and non-evidentiary AI diagnostic remain preserved and contribute zero human evidence.
- The candidate library exists, but no family is established as semantic gold; no operator vocabulary, corpus, or model is selected or modeling-ready.

## Portable commits

| Commit | Role |
| --- | --- |
| `dc64c89` | Added the N=300 pool builder, cumulative analyzer, frozen trigger implementation, and tests |
| `98a1627` | Committed exact N=300 selection/routing/exposure plan before model outputs |
| `1f9c118` | Committed five positions-101--300 AI JSONL parts |
| `5c73da7` | Committed cumulative N=300 records/checks/signatures/metrics/report/manifest/exposure |
| `66bd219` | Added candidate-library schemas, builder, source/provenance guards, and tests |
| `f3ac5c4` | Froze the exact candidate-library and 71-ID sampling plan before outputs |
| `80ce8c2` | Materialized and validated the 30-family library and 71-question sample |
| metadata child | Updates AGENTS, handoff/state, docs, preflight, and sequencing decision v0.4; one descendant of the expected baseline |

No push was performed.

## Validation commands

Run from the repository root:

```sh
python3 -m json.tool state/project_state.json >/dev/null
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python data_construction/tools/analyze_ai_question_structure_cumulative_n300.py --validate-only
.venv/bin/python -B data_construction/tools/build_candidate_backbone_library.py --validate-only
.venv/bin/python -B -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

Expected current result after this metadata update:

- central schema bundle: 11 schemas and 3 vocabulary instances, zero errors/warnings under the exact pin;
- exploration-local candidate schemas: Draft 2020-12 valid and exercised by the builder/tests;
- IR adapter: 50 records, 520 nodes, zero parse/schema/validator errors, 455 `DEAD_NODE` warnings;
- cumulative N=300 validation: 300 records, 300 passing checks, byte-exact N=100 prefix;
- candidate library validation: 30 families, 300 exhaustive members, 71 representatives, 102 passing checks, exact byte reconstruction;
- unit tests: 117 passed, 0 failed;
- core JSON/JSONL parse set: 60 files;
- preflight: zero deterministic validation failures, `RESULT=NOT_READY`, exit 2 only for synchronization and representative-environment-realization gates.

The preflight compares local remote-tracking refs. Fetch only when remote reads
are authorized; never pull over, reset, or rewrite this continuation.
