# Current handoff

Date: 2026-08-25

Current research phase: **equivalence-aware operator normalization contract
freeze before grounding.**

Active branch: `main`

Expected handoff baseline: `4d4d86885a5294af40653a48cbf12346f699db53`

The expected baseline contains the completed representative environment run.
This metadata handoff is one linear descendant of that baseline.

Last completed task: froze and executed the 71-question representative
environment study, keeping backbone adequacy (E1), open operator realization
(E2), grounding, execution, and answer recovery as separate signals.

Next exact task: implement and test a reversible, label-free two-layer
equivalence normalizer for all 93 open realization candidates, then commit a
separate plan while normalized outputs are absent. Do not begin grounding or
consume fresh reserve questions first.

Current scientific decision:
`FREEZE_EQUIVALENCE_AWARE_OPERATOR_NORMALIZATION_BEFORE_GROUNDING`.

Study status:
`representative_environment_e1_e2_complete_equivalence_normalization_required_before_grounding_or_common_graph_claim`.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED`.

Handoff readiness: Not ready. At the expected baseline, local `main` is 46
commits ahead of local `origin/main`; the metadata commit containing this
handoff is projected to make it 47 commits ahead. No push was performed or
authorized.

## Authoritative status

| Area | Current evidence |
| --- | --- |
| Official source | HybridQA table corpus and released train/dev remain pinned and hash-audited at manifest-recorded upstream commits |
| Historical exposure | Five Week 1--3 files remain byte-preserved; 100 unique exposed IDs and 15 locked-evaluation IDs; strict errors=0 |
| Historical IR v0.2 | Ten files remain quarantined read-only; 50 graphs/520 nodes validate with zero parse/schema/validator errors and 455 preserved `DEAD_NODE` warnings |
| Released role allocation | Annotation-pilot=30; train=0, dev=0, locked-eval=0 |
| N=300 question-only extraction | 300/300 records pass; fine/contracted/topology/task families=39/30/10/70; the 300 IDs are AI-exposed and 3,066 official-dev questions remain unexposed/unallocated |
| Candidate library/sample | 30/30 contracted families, 300/300 exhaustive membership, and a deterministic 71-question rarity/variation coverage-stress sample |
| Environment views | 71/71 full-table plus table-link-closure views; official answer and trace fields are absent |
| E1 backbone adequacy | adequate=64, partially adequate=5, indeterminate=2, inadequate=0 |
| E2 open realization | available=71; 72 target variants; 93 ungrounded candidate DAGs |
| E2 mappings | one-to-one=278, many-to-one=4, one-to-many=1 |
| Deterministic integrity | 285/285 run checks pass and `--validate-only` reconstructs the committed outputs exactly |
| Later signals | grounding=0, execution=0, answer recovery=0; all 71 outcomes remain truthfully `in_progress` after only the first two signals |
| Human evidence | human raw files/records/agreement/adjudication all remain zero; human review is not the active gate |
| Gold/model status | no semantic gold, final vocabulary, common exact graph, selected corpus, or modeling readiness is claimed |

## Scientific interpretation

The run establishes a narrow feasibility result: under an intentionally open
notation, an ungrounded operator candidate could be authored for every sampled
target semantic variant. It does not establish that any candidate is grounded,
executable, answer-producing, or uniquely correct.

Most mappings preserve the semantic backbone, so a common layered interface is
plausible: a semantic obligation kernel plus a bounded environment adapter. The
evidence does not support one common exact executable DAG.

Raw graph variation is strongly confounded with producer style:

| E2 partition | Records | Candidates | Multi-candidate records | Environment-extension nodes |
| --- | ---: | ---: | ---: | ---: |
| 01 | 18 | 36 | 18 | 95 |
| 02 | 18 | 19 | 1 | 2 |
| 03 | 18 | 21 | 3 | 47 |
| 04 | 17 | 17 | 0 | 0 |

The generated all-candidate metric reports multiple raw structural profiles in
17/30 families, but 16 of those 17 include within-question alternatives that
themselves contribute different profiles, and four contain only one selected
question. On the primary `candidate1` projection, 67/71 questions have zero
node/edge/depth-count delta from their target backbone. Consequently, raw node
counts, candidate multiplicity, and `17/30` cannot be attributed to question or
environment structure alone.

The 64/71 E1 headline is also not a calibrated accuracy estimate. The sample
overrepresents rare families and each question was assigned to only one AI
producer. Six of the seven non-adequate-or-indeterminate cases involve
multiplicity, tie, or referent ambiguity. Any common representation must retain
referent identity, cardinality/tie semantics, and set-valued or ambiguous
outcomes rather than reducing everything to a simple chain.

## Freeze/provenance sequence

1. `78fe487327d2fda43cc2ec79203c0a3223d1645b` committed implementation, v0.1/v0.2 schemas, prompts, and tests.
2. `2e8f6a2c8ee2eb7a3d8a175ea7b8d7f94213175c` committed the exact plan while planned outputs were absent and before selected raw environment access.
3. `1ff98d3a9cbd7cdd7ae5c7de6676818a57481ec7` materialized 71 pinned views, routing, and E1 packets.
4. `c3ed836c633859d3575bab1f29d7cf0274df6780` froze 71 E1 assessments and E2 packets containing hash-only E1 bindings.
5. `4d4d86885a5294af40653a48cbf12346f699db53` committed 71 E2 records/93 candidates, outcomes, 285 checks, metrics, report, exposure ledger, and run manifest.

E1 and E2 were partition-authored in fresh contexts, and E2 authors did not
receive E1 judgments or rationales. This limits direct stage leakage; it does
not make the four partitions independent reviewers or statistically identify a
producer effect.

## Exact next task: reversible two-layer normalization

1. Add a new versioned normalization schema, deterministic implementation, and regression tests without changing any committed representative-run artifact.
2. Before normalized outputs exist, commit a plan bound to the exact 93 candidates, 72 variants, E2 hash, producer routing, and stopping branches.
3. Supply only a structural projection: target semantic topology, operator adjacency, semantic-to-operator mappings, roles, typed unresolved slots, variation axes, opaque IDs, and producer route. Exclude question/environment text, factual answers, E1 content, operator labels/descriptions, and preserved vocabularies.
4. Produce a reversible semantic quotient that checks coverage/dependency preservation and a separate environment-adapter signature retaining modality, cardinality/tie, output arity, access placement, and fused-versus-explicit access.
5. Initially allow only alpha-renaming, independent-node ordering, transitive-reduction differences, and meaning/input-output-preserving access split/fuse. Leave grounding-dependent cases `provisionally_equivalent`.
6. Compare alternative candidates as sets within each question, then normalized sets within multi-question families. Report producer partition sensitivity; do not treat `candidate1` as preferred truth.
7. Precommit the fallback before inspecting normalized results. If the fixed question/producer assignment still prevents attribution, reuse 16 already exposed questions (four per existing partition, all seven E1 challenge cases plus nine adequate controls) in a two-new-author fully crossed AI sensitivity run. This is a confound diagnostic, not human majority review, and uses no fresh reserve IDs.
8. Proceed to a provisional non-final grounding adapter only if loss, family instability, and producer sensitivity meet the frozen branch criteria. Otherwise revise the normalization contract in a new version.

## Evidence and exposure boundaries

- The 300 question-only records and all representative E1/E2 records are `ai_exploratory_non_human_non_gold`.
- The 71 selected IDs were already part of the 300-ID AI-exposed set. The run consumed no fresh reserve or locked-evaluation ID.
- Sanitized views omit official answers/traces, but include table and linked-document content; their 71 IDs are environment-exposed development evidence.
- `71/71 available` is expressive representability under an open validator, not execution success.
- Record-local E2 labels are not vocabulary entries and their recurrence has not been established.
- Exact model revision, seed, and raw interface response were unavailable; structured partition files are the primary capture and exact generation replayability is not claimed.
- Human review remains deferred and is not a blocker for deterministic normalization. Later targeted review may be warranted for ambiguous or execution-suspicious cases.

## Declared blockers

- `LOCAL_COMMIT_NOT_PUSHED`: portable work exists only in local commits; remote writes were not authorized.
- `OPERATOR_EQUIVALENCE_NORMALIZATION_NOT_STARTED`: the reversible quotient and its precommitted branch criteria do not yet exist.

The prior representative-environment-realization blocker is resolved.

## Validation commands

Run from the repository root:

```sh
python3 -m json.tool state/project_state.json >/dev/null
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python data_construction/tools/analyze_ai_question_structure_cumulative_n300.py --validate-only
.venv/bin/python -B data_construction/tools/build_candidate_backbone_library.py --validate-only
.venv/bin/python -B data_construction/tools/build_representative_environment_realization.py --validate-only
.venv/bin/python -B -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

Expected result after this metadata update:

- central bundle: 11 schemas and three vocabulary instances, zero errors/warnings under the exact pin;
- historical adapter: 50 records/520 nodes, zero errors and 455 preserved warnings;
- N=300, candidate-library, and representative-run validate-only checks reconstruct committed artifacts exactly;
- core JSON/JSONL parse set: 76 files;
- unit tests: 157 passed, zero failed;
- preflight: zero deterministic validation failures, `RESULT=NOT_READY`, exit 2 only for synchronization and operator-equivalence-normalization gates.

The preflight compares local remote-tracking refs. Fetch only when remote reads
are authorized; never pull over, reset, or rewrite this continuation.
