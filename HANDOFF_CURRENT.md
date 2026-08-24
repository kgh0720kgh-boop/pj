# Current handoff

Date: 2026-08-24

Current research phase: **cumulative question-only AI semantic-backbone exploration; N=100 is complete and the active gate is the precommitted N=300 expansion.**

Active branch: `main`

Expected handoff baseline: `74bf961a10420e0d222b23e0af0c5323985f95fd`

The expected baseline is the committed N=100 partition/normalization sensitivity audit. This metadata handoff is one linear descendant of that baseline.

Last completed task: froze and ran the cumulative N=100 question-only extraction contract, validated 100 records, derived four deterministic signature resolutions, computed recurrence/saturation metrics, recorded all AI exposure, and added a separately versioned post-hoc partition/normalization sensitivity audit without rewriting the primary result.

Next exact task: freeze a separately versioned cumulative N=300 selection, question-only pool, and exposure manifest with the current 100 as an exact prefix and 200 newly selected eligible questions. Then generate positions 101–300 with the N=100 prompt, schema, role set, and normalizer unchanged, distribute committed positions across producer contexts rather than contiguous worker blocks, and recompute cumulative and partition-sensitivity metrics.

Current scientific decision: `UNDECIDED_NEEDS_SCALE_EVIDENCE`.

Study status: `n100_complete_n300_expansion_required_human_validation_deferred`.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED`.

Handoff readiness: Not ready. At the expected baseline, local `main` is 31 commits ahead of local `origin/main`; the metadata commit containing this handoff is projected to make it 32 commits ahead. No push was performed or authorized.

## Authoritative status

| Area | Current evidence |
| --- | --- |
| Official source | HybridQA table corpus and released train/dev remain pinned and hash-audited at the manifest-recorded upstream commits |
| Historical exposure | Five recovered Week 1–3 files are byte-preserved; 100 unique exposed IDs and 15 locked-evaluation IDs; strict errors=0 |
| Historical IR v0.2 | Ten files are quarantined read-only; 50 graphs/520 nodes validate with 0 parse/schema/validator errors and 455 preserved `DEAD_NODE` warnings |
| Released role allocation | `split_manifest_v0_1.json` remains unchanged: annotation-pilot=30, train=0, dev=0, locked-eval=0 |
| N=100 exploratory allocation | Prior 30 are the exact prefix; 70 fresh eligible questions were added; historical overlap=0; 3,266 official-dev questions remain unexposed and unallocated |
| N=100 extraction integrity | 100/100 records pass Draft 2020-12 schema, exact question/order/hash/cue, forbidden-key, reference, root/sink, and DAG checks |
| N=100 recurrence | Fine labeled families=23; same-role-contracted families=17; topology shapes=6; task signatures=38 |
| Contracted-family diagnostics | Singleton mass=0.09; top-10 coverage=0.93; first-30→new-70 transfer=50/70=0.7142857; final block novelty=0.30 and 0.00 |
| Record diagnostics | Complete=71, uncertain=29; provisional `OTHER` questions=0; alternative graph questions=1 |
| Precommitted N=100 outcome | `EXPAND_UNCHANGED_TO_N300`; the active trigger is five first-30-unseen contracted families recurring at least twice in the new 70 |
| Post-hoc partition sensitivity | All five triggering families recur only within one producer partition; cross-partition recurrence=0. This limits semantic-novelty interpretation but does not replace the precommitted operational decision |
| Graph normalization sensitivity | Raw dependency branch/join counts=5/6; after transitive reduction=0/1. Fine dominant family=46 questions; contracted dominant family=62 |
| Human evidence | Human raw files=0, human records=0, agreement observations=0, adjudications=0; the v0.1 human-first lane is preserved but deferred and is not the active gate |
| Prior AI diagnostic | The two-reviewer/alignment/topology rehearsal remains non-human/non-gold direction-finding evidence and is not pooled with the N=100 primary records |
| Operator granularity | The 30-record/90-representation/90-check/three-packet feasibility bundle remains deferred; no vocabulary is selected and human reviews remain 0 |

## What the N=100 result means

The result supports one narrow claim: under one frozen question-only AI extraction contract and deterministic normalizer, many HybridQA questions map to recurrent small semantic-DAG shapes. A small number of families cover much of this sample, but the curve is not yet a universal saturation result.

The operational N=300 expansion remains appropriate because more scale is the conservative response to unresolved novelty. However, the sole active trigger is not clean evidence of new semantic families: the first 30 occur in partition 01, most new questions occur in partitions 02 and 03, and all five recurring-new families are partition-local. Producer-context style and question novelty are therefore confounded in N=100.

The same-role-contracted view must also be treated as a sensitivity bound, not semantic equivalence. It increases the dominant family from 46 to 62 questions by merging linear hops with the same role, including cases where those hops can correspond to distinct referents. Always report fine and contracted results together.

None of these measurements evaluates factual answers, table/document realization, grounding, execution, human agreement, semantic correctness, universal topology, or a common executable graph.

## Declared blockers

- `LOCAL_COMMIT_NOT_PUSHED`: the portable work exists only in local commits; remote writes were not authorized.
- `N300_SCALE_EXPANSION_NOT_PERFORMED`: the precommitted N=100 result requires a versioned N=300 extension before candidate-backbone freeze or environment realization.

The absence of human review is no longer a current blocker. It remains a truthful zero-count evidence boundary and may become relevant later for targeted validation claims.

## Exact next task: cumulative N=300

1. Reacquire the pinned official dev source only through `source_manifest_v0_1.json` if the machine-local cache is absent.
2. Create a new versioned exploratory selection and question-only pool of 300 questions using the same seed/ranking rule, with all current N=100 IDs and bytes as the exact prefix.
3. Exclude every historical exposure and retain the released split allocation unchanged; add 200 AI-processed IDs to a new exposure-ledger version and mark all 300 ineligible for future unseen-evaluation claims.
4. Commit the N=300 selection, pool, producer-routing plan, and hashes before generating positions 101–300.
5. Keep `primary_extraction_v0_1`, the semantic-backbone record schema, provisional roles, and deterministic normalizer unchanged. Any extractor/normalizer change starts a different experiment version.
6. Route new committed positions across producer contexts deterministically, rather than assigning a contiguous question range to one context. Preserve producer identity on every record.
7. Validate all 300 records and recompute fine, contracted, topology, and task families, rarity/coverage curves, block novelty, transfer, `OTHER`, uncertainty, alternatives, normalized graph profile, and cross-partition support.
8. Only after the cumulative N=300 evidence is frozen, apply the separately precommitted N=1,000 trigger or freeze a candidate backbone library and precommit representative environment-realization sampling.

This is a scale task, not a request to resume full duplicate human review.

## Evidence and exposure boundaries

- N=100 records are `ai_exploratory_non_human_non_gold`.
- The post-hoc sensitivity audit is separately versioned and does not rewrite the frozen primary contract, records, metrics, report, or decision.
- All 100 processed questions are excluded from future unseen-evaluation claims; this is exposure accounting, not a correctness label.
- Table identity/schema/rows/cells, linked-document identity/text, answers, traces, operator proposals, grounding, and historical graphs were forbidden inputs to the question-only extractor.
- The interface exposed no exact model revision and supported no seed. Structured partition JSONL is the primary capture; exact generation replayability and statistical independence are not claimed.
- The v0.1 human packet and AI diagnostic remain preserved. Neither contributes human evidence to this run.
- No operator vocabulary, candidate-backbone library, corpus, or model is selected, gold, or modeling-ready.

## Portable commits

| Commit | Role |
| --- | --- |
| `14b3cb0` | Added the scale-first v0.2 study machinery, N=100 builder/analyzer, frozen prompt/schema, and tests |
| `5adb852` | Froze the exact cumulative N=100 selection, contract bindings, and N=300 trigger before model records |
| `0bed27e` | Committed 100 primary records, checks, deterministic signatures, metrics/report, run manifest, and exposure ledger |
| `74bf961` | Added the separately versioned post-hoc partition and normalization sensitivity audit |
| metadata child | Updates AGENTS, handoff/state, documentation, and preflight bindings; one descendant of the expected baseline |

No push was performed.

## Validation commands

Run from the repository root:

```sh
python3 -m json.tool state/project_state.json >/dev/null
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python data_construction/tools/run_ai_question_structure_scale_exploration.py \
  --validate-only \
  data_construction/exploration/ai_question_structure_scale_v0_1/run_001/parts/partition_01.jsonl \
  data_construction/exploration/ai_question_structure_scale_v0_1/run_001/parts/partition_02.jsonl \
  data_construction/exploration/ai_question_structure_scale_v0_1/run_001/parts/partition_03.jsonl
.venv/bin/python data_construction/tools/audit_ai_question_structure_partition_sensitivity.py
.venv/bin/python -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

Expected current result after this metadata update:

- schema bundle: 11 schemas and 3 vocabulary instances, zero errors/warnings under the exact pin;
- IR adapter: 50 records, 520 nodes, zero parse/schema/validator errors, 455 `DEAD_NODE` warnings;
- N=100 primary validation: 100 records, zero errors;
- sensitivity audit: recurring-new=5, cross-partition=0;
- unit tests: 87 passed, 0 failed;
- preflight: zero deterministic validation failures, `RESULT=NOT_READY`, exit 2 only for the declared synchronization and N=300 gates.

The preflight compares local remote-tracking refs. Fetch only when remote reads are authorized; never pull over, reset, or rewrite this continuation.
