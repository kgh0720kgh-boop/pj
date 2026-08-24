# Current Cross-Device Handoff

Project: Hierarchical Data Construction for Semantic Execution Topology Induction

Current research phase: **Phase A0 question-first instrument and artifacts are materialized; Phase A1 question-only calibration is awaiting real human annotations.**

Current branch: `main`

Expected HEAD baseline: `40f8961b5e9ad21fa7e80a11a047754311d5e91c` (`Report AI shadow-pipeline diagnostic results`). The metadata commit containing this handoff is intentionally one linear descendant of that baseline; any later linear descendant is a continuation. A missing or non-ancestor baseline is divergence.

Remote: `origin` → `https://github.com/kgh0720kgh-boop/pj.git`; `main` tracks `origin/main`.

Last completed task: completed a separately namespaced, non-evidentiary end-to-end AI shadow run over all 30 question-only views: two procedurally separated AI reviewers, frozen stage-1 observations, structured records, blinded third-AI alignment, a 20-question shadow hold-out, an independent topology-only pass, a downstream connector preview, and final analysis. This run created no human annotation and changed no scientific gate.

Current scientific decision: `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`. Study status is `question_only_calibration_required_phase_b_deferred`. No semantic instrument, topology, operator vocabulary, corpus, or model is selected, gold, empirically frozen, or modeling-ready.

Synchronization state: `LOCAL_COMMIT_NOT_PUSHED`

Handoff readiness: Not ready. At the expected baseline, local `main` is 26 commits ahead of local `origin/main`; the final metadata commit containing this file is projected to make it 27 commits ahead. No push was performed or authorized. Phase A1 human evidence is also still absent.

## Current artifact snapshot

| Area | Current status |
| --- | --- |
| Official HybridQA sources | Audited at pinned upstream commits; stable identities, hashes, counts, and reacquisition instructions are in `source_manifest_v0_1.json` |
| Historical exposure | Strict-complete: five byte-preserved files, 100 unique exposed IDs, 15 historical locked-eval IDs, zero strict-audit errors |
| Pilot allocation | 30 `annotation_schema_pilot` questions from pinned official dev; deterministic, source-verified, zero historical overlap, no override |
| New train/dev/locked roles | Not allocated; all three counts remain zero |
| Phase A0 study contract | `question_structure_study_plan_v0_1.json` fixes the question-first phase order, three ten-question batches, stopping branches, and deferred Phase B sampling contract; SHA-256 `533aa565f3c08dc533ceaaf9d69b2dfb7fb1d2a0f5abd26840a03de28ee6d7be` |
| Question-only views | 30 ordered records with exactly `schema_version`, `visibility`, `question_id`, and `question`; no environment, answer, proposal, historical label, or other annotator output; JSONL SHA-256 `513d7f3ef28a7d2ad61bc71c02ab7767a61468394e614a783705dd0d9ae5647a` |
| Active Phase A1 packet | Batch `phase_a1_batch_01`, first 10 committed-order questions, reviewers required per question=2, annotations created=0; HTML SHA-256 `ebf13c128b5ea1fbee947050fa52e4f6886244871d01900dbcc6e9cb552cadee` |
| Packet binding | Canonical payload SHA-256 `c86920e63cde36f285312bbbe3da58fe10c4de2e51e33745e22291a7568eb57b`; manifest SHA-256 `6fffe2238df8b6c4178b6ca465d473811ad958d4dce1e84e8f44415bfdbda971` |
| Human evidence | Real reviewer files=0, raw human records=0, agreement observations=0, adjudications=0; calibration/freeze/confirmation are all false |
| AI pipeline diagnostic | Run `ai_question_structure_pipeline_v0_1_run_001` completed as non-human/non-gold engineering evidence: 60 stage-1 records, 60 structured records, 30 blinded alignments, and 20 independent topology-only records; contract freeze commit `fb2ba9e29221c16dd8e1ee71439339d17a92818a` |
| AI diagnostic findings | 10/30 full equivalence and 20/30 compatible variation under the frozen AI crosswalk; reviewer-1/2 instrument issues=19/0; ambiguity flag match=25/30; alternative-plan-presence match=20/30; independent topology exact structural signatures=0.85/0.90. These are not correctness or human-agreement results |
| Schema bundle | 11 Draft 2020-12 schemas and 3 candidate vocabulary instances; exact-pin validation passes with errors=0 and warnings=0 |
| Regression suite | 68 tests pass in the exact-pin project-local environment |
| Historical IR v0.2 | Ten original files remain quarantined read-only; 50 graphs/520 nodes validate with zero parse/schema/IR-validator errors and 455 preserved `DEAD_NODE` warnings |
| Deferred Phase B evidence | Existing operator views, 30 `llm_proposed` records/90 coarse-medium-fine representations, 90 deterministic checks, three legacy packets, and v0.1 metrics are byte-preserved as feasibility evidence only |

The source manifest is a dated immutable v0.1 audit snapshot. Current allocation authority is the complete historical manifest plus `split_manifest_v0_1.json`; do not rewrite the source manifest merely to erase its earlier dated gate description.

## Scientific interpretation boundary

Phase A asks what semantic structure people can elicit from the question alone. Environment capability fields such as linked-document availability belong to later realization and must not appear in the Phase A question-only input.

The raw form deliberately asks one reviewer to connect a question skeleton, semantic obligations, and a topology. Its output is therefore an **elicited linked representation** that can test whether the scaffold is usable and whether humans can express a question through it. It is not independent evidence that natural-language structure predicts a graph: the instrument itself requests the links.

Before any cross-level relationship claim, motif claim, Phase B normalization, or common-graph claim, the project must add a separately versioned and frozen independent/blinded held-out topology elicitation or prediction pass. That pass must not expose the first-pass skeleton, obligation IDs, mapping references, other annotator output, or later-layer evidence, and it must use a different pass or eligible annotator. Agreement on the current linked form cannot substitute for that gate.

Raw schema/hash validation establishes structural record integrity only. It does not establish semantic agreement, correctness, contamination absence, or a researcher's approval of the reviewer.

The completed AI shadow run is deliberately outside the canonical human lane. Its same-family reviewer contexts were procedurally separated but are not statistically independent, and its blinded crosswalk is another AI judgment. The 1.0 compatible-or-full diagnostic rate hides material instrument sensitivity: one reviewer recorded 19 instrument issues while the other recorded none, and two scalar alternative-plan components were marked substantive conflict. The frozen v0.1 disposition rule does not promote those scalar conflicts to a question-level disagreement unless a grouped core layer has a material conflict; the interpretive addendum records this limitation without silently recomputing the result.

## Remaining gates

- `LOCAL_COMMIT_NOT_PUSHED`: the expected baseline is 26 local commits ahead of `origin/main`; the metadata child is projected to make it 27. Remote writes were not authorized.
- `QUESTION_ONLY_CALIBRATION_NOT_PERFORMED`: no two approved independent exposure-naive human files exist for active batch 1.

These are the current preflight/readiness blockers recorded in machine state. Two additional scientific gates become actionable later:

- `ALIGNMENT_CONTRACT_NOT_FROZEN`: no human-evidence alignment/adjudication contract or comparator has been frozen, so future human raw records cannot yet be converted into agreement or Phase A2 readiness claims. The AI diagnostic contract is not a substitute.
- `INDEPENDENT_TOPOLOGY_GATE_NOT_IMPLEMENTED`: no eligible human/scientific independent-topology gate exists. The AI topology-only rehearsal proves only that the mechanics run.

None is a deterministic validation failure. Preflight should remain `RESULT=NOT_READY` with exit 2 while either current blocker remains; later scientific claims remain prohibited until their applicable gates are also truthfully resolved.

## Next exact task

### Human task: Phase A1 batch 1

Use only:

`data_construction/pilot/question_structure_review_packets/question_structure_calibration_batch_1_v0_1.html`

1. The researcher approves two real humans who are mutually independent and exposure-naive for these questions. Anyone who saw later-layer table/document content, answers, grounding, old graphs, proposals, or the earlier worked discussion of question 1 is ineligible for the affected work.
2. Each reviewer works independently on the same 10 committed-order questions and exports one immutable 10-record JSON file. The result is two files and 20 raw records, not 180 granularity decisions.
3. In the normal packet UI, each reviewer completes all ten free observations and locks them before the linked scaffold is revealed. The reviewer then completes or truthfully abstains on each record and supplies the required attestations.
4. The researcher verifies real-human identity, mutual independence, approval, and prior exposure outside the raw packet. Reviewer pseudonyms and self-attestation are not authentication.
5. Validate each file independently, preserving the immutable raw file and its generated check artifact:

```sh
.venv/bin/python data_construction/tools/validate_question_structure_annotations.py \
  data_construction/pilot/human_reviews/<reviewer-file>.json \
  --batch-id phase_a1_batch_01 \
  --checks-output data_construction/pilot/human_reviews/<reviewer-checks>.jsonl
```

The packet stages are enforced only by normal browser UI plus procedural attestation, not by a server or adversarial blinding system. Forbidden-key checks cannot detect arbitrary later-layer content pasted into an allowed free-text field. Those limitations must remain part of the human audit.

### Technical task immediately after two valid raw files

Create and freeze a separately versioned blinded alignment/adjudication contract and comparator before calculating semantic agreement or declaring Phase A1 complete. Preserve raw open coding unchanged; do not silently normalize it in place. The alignment layer must distinguish schema-validity, semantic comparability, unresolved ambiguity, adjudication, and evidence status.

Only after that freeze may the study enter the Phase A2 branch defined in the study plan:

- if batch 1 freezes the contract, batches 2 and 3 provide 20 held-out questions / 40 raw records;
- if batch 1 changes the contract and batch 2 freezes it, only batch 3 provides 10 held-out questions / 20 raw records;
- if batch 2 also changes it, batch 3 is calibration and leaves zero holdout, so Phase B must stop pending fresh authorized questions or a documented reframe.

## Deferred Phase B and later execution

The former task requiring six files and 180 operator-granularity decisions is revoked. Do not use the three legacy packets for current Phase A review or treat them as an approved future Phase B interface.

Phase B may start only after eligible Phase A2 evidence, the independent/blinded topology gate, and a frozen six-stratum taxonomy derived only from eligible frozen Phase A evidence. The exact sample manifest must be committed before selected proposal judgments, self-assessments, or Phase B human outcomes are opened. Base sampling is 12 questions × 3 granularities × 2 reviewers = 72 decisions, with precommitted trigger expansion to 90 and at most 108. Existing proposals already exist and question 1 has been discussed, so no artifact may falsely claim that all proposal content was unopened before this redesign.

Representative grounding/execution belongs only after Phase B; Phase C uses one representative per stratum precommitted in the Phase B sample manifest. Execution success and semantic-plan correctness remain separate signals.

Do not allocate annotation train/dev/locked-eval roles, select a final vocabulary, label proposals gold, or claim modeling readiness from structural checks or packet existence.

## Git continuity

The local continuation after `origin/main` at `c337e9a67c15cd68fbb53eefb79bef90a6f9f242` is linear. The Phase A0 continuation added by the current work is:

| Commit | Purpose |
| --- | --- |
| `73d7849` | Established the question-first study plan, schemas, packet/raw tooling, validators, reports, and tests |
| `1639d67` | Materialized and bound the 30 blind four-field question-only views |
| `b7f1749` | Materialized and bound the active first-ten-question Phase A1 packet |
| `19e3ab8` | Handed off the canonical Phase A1 human-calibration task |
| `fb2ba9e` | Froze the non-evidentiary AI shadow-pipeline contracts, prompts, comparator, and tests before outputs |
| `d5adc9b` | Captured and hash-locked two 30-record AI stage-1 files |
| `c9bd7a1` | Captured the independent 20-question topology-only diagnostic |
| `93486df`, `4c51424` | Captured the two independently generated 30-record structured AI files |
| `2408d68`, `d2bd2dd` | Froze the blinded pair packet and captured the third-AI alignment |
| `40f8961` | Generated metrics, run manifest, compact report, and limitation-focused interpretive addendum |
| metadata child | Updates handoff, machine state, preflight bindings, and current status; one descendant of the expected baseline |

The preceding local commits preserve historical recovery, IR v0.2, the 30-question allocation, and deferred granularity feasibility artifacts. Inspect them with `git log --oneline origin/main..HEAD`; do not force-push, rewrite, reset, or discard this linear continuation. No push is authorized by this handoff.

## Required files to read on continuation

1. `CODEX_DATA_CONSTRUCTION_RESET_PROMPT_V2_MULTI_DEVICE.md`
2. `AGENTS.md`
3. `HANDOFF_CURRENT.md`
4. `state/project_state.json`
5. `ENVIRONMENT.md`
6. `reports/cross_device_repo_audit.md`
7. `data_construction/reports/data_source_audit.md`
8. all versioned files under `data_construction/manifests/`
9. `data_construction/pilot/question_structure_study_plan_v0_1.json`
10. `data_construction/reports/research_sequencing_decision_v0_1.md`
11. `data_construction/pilot/question_only_semantic_views_manifest_v0_1.json`
12. `data_construction/pilot/question_structure_review_packets/question_structure_calibration_batch_1_v0_1_manifest.json`
13. `data_construction/schemas/question_only_semantic_view_v0_1.json`
14. `data_construction/schemas/question_structure_annotation_v0_1.json`
15. `data_construction/pilot/granularity_representation_plan_v0_1.json`
16. `data_construction/reports/operator_granularity_metrics_v0_1.json`
17. `historical/README.md`
18. `historical/ir_v0_2/recovery_manifest_v0_1.json`
19. `data_construction/diagnostics/ai_question_structure_pipeline_v0_1/contracts/diagnostic_plan_v0_1.json`
20. `data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/run_manifest.json`
21. `data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/analysis/metrics_v0_1.json`
22. `data_construction/diagnostics/ai_question_structure_pipeline_v0_1/run_001/analysis/interpretive_addendum_v0_1.md`

## Commands to reproduce current checks

Run from the repository root:

```sh
git rev-parse --show-toplevel
git status --short --branch
git log -1 --oneline
git remote -v
python3 -m json.tool state/project_state.json >/dev/null
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python data_construction/tools/validate_question_structure_annotations.py \
  --batch-id phase_a1_batch_01 \
  --packet-only
.venv/bin/python -m unittest discover -s tests -v
sh -n scripts/cross_device_preflight.sh
sh scripts/cross_device_preflight.sh
```

Expected deterministic results for the current committed baseline:

- schema bundle: 11 schemas, 3 vocabularies, errors=0, warnings=0;
- question-only views: 30 exact four-field records in committed allocation order;
- active packet: batch 1, 10 questions, exact-render/hash validation pass, human annotations=0;
- IR adapter: 50 records, 520 nodes, parse/schema/validator errors=0, `DEAD_NODE=455`;
- AI diagnostic: contract and all raw/alignment/topology bindings pass; 60 structured reviewer records, 30 alignments, and 20 independent topologies; final status `NOT_EVALUATED_AI_SUBSTITUTE`;
- tests: 68 passed;
- preflight: zero deterministic validation failures, `RESULT=NOT_READY`, exit 2 for declared human/synchronization gates;
- Git work tree: clean after the metadata commit;
- local branch: projected 27 commits ahead of the local tracking ref after that commit.

The preflight comparison uses local remote-tracking refs. Fetch only when remote reads are authorized; do not pull over or reset the local continuation.

## Historical and machine-local boundaries

Every path listed under `historical_read_only_paths` in `state/project_state.json`, including the five Week 1–3 source files and ten files under `historical/ir_v0_2/`, is immutable evidence. A correction or additional recovery requires a new versioned manifest and preservation commit. Never use recovered exposed IDs for training, or recovered locked-evaluation IDs for prompt, rubric, schema, or operator-vocabulary tuning.

Recreate `.venv` from `requirements.txt`; never copy it between machines. Official HybridQA checkouts are untracked caches and must be reacquired or verified from the source manifest. Conversation state, caches, credentials, local stashes, editor state, and consumer-synchronized folders are non-portable.

No model runtime, secret, GPU, database, Docker service, or external account is required for committed deterministic validation. The deferred proposal plan and AI diagnostic record `model_id=codex_gpt-5`; exact revision was not exposed, seed was unsupported, and the structured artifacts are the primary capture because a separate raw response was not exposed. Exact generation replayability and statistical reviewer independence are not claimed. Future model runs must record stable model ID, exact revision, seed, prompt artifact, raw-output hash, code commit, and run status when exposed, or an explicit unavailable status otherwise.
