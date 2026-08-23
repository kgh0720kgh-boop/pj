# Research sequencing decision v0.1

Decision date: 2026-08-23

Decision status: adopted study plan; human evidence not yet collected

Machine-readable plan: `data_construction/pilot/question_structure_study_plan_v0_1.json`

## Decision

Question-only structure discovery must precede human review of environment-aware operator proposals. The existing 30-record/90-representation granularity artifact, 90 deterministic checks, three HTML packets and manifests, and v0.1 metrics remain unchanged as deferred Phase B evidence. They are model-assisted `llm_proposed` artifacts, not human review, gold, or a selected vocabulary.

The discussion of question `8259c70c392c5b75` that motivated this sequencing decision is protocol analysis only. It creates no human annotation, review, agreement, adjudication, or semantic-confirmation evidence. A prospective reviewer who has seen a granularity packet, candidate graph, model rationale, environment view, answer, trace, or other forbidden later-layer input must declare that exposure and is excluded from the affected exposure-naive Phase A work.

## Phase order

| Phase | Purpose | Evidence required to advance |
|---|---|---|
| A0 — raw open-coding instrument | Build a blank, proposal-free question-only instrument and raw-record validator. | Exact question-only projection, no closed semantic-label ontology/enums, no prefilled content, schema/hash/leakage checks, immutable raw output, exposure/independence attestation contract. |
| A1 — open-coding calibration | Collect two independent free-form representations for one committed-order 10-question batch. | Machine-checkable raw-record conditions plus procedural manual sign-off, followed by a separately versioned and frozen blinded alignment/adjudication contract, artifact, and comparator. Raw validity alone is not semantic agreement. |
| A2 — frozen held-out confirmation/census | Test the frozen instrument on questions untouched by calibration, then complete a same-version census where possible. | Complete held-out records and frozen-comparator outputs; stability claims use only untouched confirmation questions. |
| B — deferred operator granularity | Compare coarse, medium, and fine realization conditional on frozen question-only evidence. | Independent/blinded held-out topology evidence, then a six-stratum taxonomy and exact sequential sample manifest committed before selected proposal judgments, self-assessments, or Phase B human results are opened; 72, 90, or at most 108 substantive decisions. |
| C — representative grounding/execution | Test grounding and execution separately from semantic-plan correctness. | Six result-independent representatives precommitted in the Phase B sample manifest, one per frozen stratum. |

## Phase A visibility and instrument contract

The normal packet interface initially shows only each opaque question ID, exact question text, and unconstrained free-observation field. All ten observations must be nonempty before one batch-wide commit makes all ten readonly; only then does that interface display the answer-request, candidate-structure, required-information-unit, dependency, ambiguity, and alternative-interpretation scaffolds for the whole batch. There is no question-by-question display, and the locked observations cannot be edited through the interface. The exported attestation records `locked_free_observation_before_scaffold=true`.

This is procedural UI staging, not adversarial or server-enforced blinding: stage 2 is embedded in the same self-contained HTML and can be discovered by inspecting or modifying its source/DOM. The reviewer must not do so, and the validator can check only the attestation, not authenticate browser history. Likewise, the raw validator structurally rejects forbidden later-layer key names but cannot detect arbitrary answer, table, document, or proposal content pasted into allowed free-text fields. Therefore neither the stage transition nor raw free-text cleanliness is a machine-proven fact; stronger evidence would require a separately distributed/server-gated stage-2 workflow and an explicit contamination-audit protocol.

The existence and adequacy of the later scaffolds are themselves the structural hypothesis under test; they are not established semantic truth. The instrument must not show a closed semantic-label ontology, answer-type enum, cardinality enum, candidate-kind enum, semantic-function enum, operator vocabulary, example plan, model proposal, or model assessment. Stable local IDs and dependency references may be structural input controls, but their semantic labels remain free text.

Hide table ID/title/section, columns, capability flags, row/cell values, linked-document identity/text, operator vocabulary, candidate graph, model rationale, official answer, weak trace, historical graph/label, grounding, execution graph, evaluator output, and granularity metrics. External lookup and reviewer consultation are prohibited during independent coding.

Phase A0 covers only the raw instrument, raw schema, exact projection, validator, hash binding, and attestation capture. It does not define or implement semantic-unit normalization, reviewer-record alignment, agreement scoring, or adjudication. Those remain explicitly unavailable until two independent A1 raw sets exist.

The skeleton, obligations, and topology in each raw record form an **elicited linked representation**: the same reviewer uses one scaffold and explicitly links obligations to upstream structure and topology nodes to obligations. This tests whether the instrument can represent and operate on the reviewer's analysis. It is not independent evidence that question structure predicts graph structure, nor evidence of a motif/structure-to-graph relationship.

## Phase A1 raw-record eligibility and manual sign-off

The active calibration batch is committed positions 1–10. Two distinct, real, exposure-naive humans independently code all ten questions. The deterministically checkable raw-record conditions are:

- 20/20 expected records are substantive, schema-valid, hash-bound, and bound to the exact question-only payload;
- detected forbidden-input and layer-separation violations are zero;
- every record has `representation_assessment.outcome=complete` and `representation_assessment.schema_gap_descriptions=[]`; and
- every record has `instrument_issues=[]`.

Separately, the researcher must manually sign off the real-human identity, mutual independence, and prior-exposure attestations for both reviewers, with zero accepted records affected by disqualifying prior exposure. The current contract has no hash-bound reviewer-identity or approval registry, so this sign-off is procedural and is neither machine-executable nor machine-authenticatable. A declaration of affected prior exposure excludes that reviewer submission from exposure-naive Phase A evidence.

The record conditions and procedural sign-off establish raw-batch eligibility, not semantic agreement. The project must not report an agreement pass or enter Phase A2 until it has created and frozen a separate versioned blinded-alignment contract, alignment/adjudication artifact, and deterministic comparator bound to the raw records. The contract must be frozen before its comparison results are interpreted. The exact task after raw A1 collection is therefore to build and validate that alignment/adjudication layer; it is not part of A0.

Exact-substring source-cue checks provide only minimal localization integrity against the bound question. They do not establish semantic correctness, semantic agreement, or cross-level prediction and cannot make the raw gate an agreement gate.

No current 8/10 categorical rule, semantic-unit F1 threshold, dependency F1 threshold, or recurring-defect count is an executable gate. Such values must not be reported from the raw instrument.

## Calibration and held-out stopping branches

The 30 committed IDs remain split into three disjoint 10-question batches.

1. If batch 1 passes the eventual frozen alignment/adjudication contract, freeze that instrument version. Batches 2 and 3 are 20 untouched confirmatory questions. Phase A2 then has 40 held-out records and a 60-record same-version census including calibration.
2. If batch 1 fails and causes a versioned instrument change, preserve its raw evidence and use batch 2 as calibration. If batch 2 passes and freezes the new version, batch 3 is the only untouched confirmatory set: 10 questions/20 records. Batch 1 may later be re-annotated for a 30-question census, but it never counts as untouched stability evidence.
3. If batches 1 and 2 both fail, batch 3 is the final calibration attempt. Even if it passes, zero untouched confirmatory questions remain. Phase B entry is prohibited until newly authorized fresh questions provide held-out confirmation, or the project chooses `STOP_OR_REFRAME`. Re-annotating an already used batch cannot create held-out evidence.
4. If batch 3 also fails, stop with `REVISE_ANNOTATION_SCHEMA` or `STOP_OR_REFRAME`.

Every failed-version artifact remains preserved. Records from different instrument versions are never pooled into one agreement or stability claim.

## Cross-level claim boundary

No motif/structure-to-graph association or predictive claim may be made from the linked Phase A records. Before Phase B normalization or any such claim, the project must separately version and freeze an independent, blinded topology-elicitation or prediction protocol. Its topology pass must use a different pass or annotator under a predeclared separation rule, expose no upstream skeleton/obligation content, IDs, or mapping references, and be evaluated on held-out questions. Only those held-out results can support a cross-level relationship claim; the current linked records remain representability and instrument-operability evidence.

## Phase B taxonomy, sampling, and stopping rule

Phase B begins only after an eligible Phase A2 held-out confirmation and the independent/blinded held-out topology gate above. Its sampling taxonomy must be discovered from a separate normalization of frozen Phase A evidence—not from the current model graphs, proposal gaps, granularity metrics, or Phase B human results.

The model proposals already exist, and the protocol discussion exposed question `8259c70c392c5b75`; the project therefore does not claim that proposals have never been opened. A taxonomy author must use only the frozen Phase A allowlist, declare prior proposal exposure, and be excluded or have the affected question excluded as predeclared and applicable. After the independent topology gate and before the selected proposal judgments, proposal self-assessments, or any Phase B human results are opened, commit a versioned motif taxonomy and exact sample manifest. The taxonomy must define six mutually exclusive primary strata and assign eligible questions deterministically. Each stratum must contain at least three eligible questions. The manifest selects the first two eligible questions per frozen stratum under its declared deterministic order, giving `6 × 2 = 12` questions. It also precommits two disjoint three-question expansion blocks: block 1 adds one unused question from the first three frozen strata, and block 2 adds one unused question from the remaining three strata. Exact IDs and stratum labels remain `not_allocated_until_phase_a2_normalization` in this plan.

Every sampled question receives coarse, medium, and fine review from two substantive reviewers:

- base: `12 × 3 × 2 = 72` decisions;
- after expansion block 1: `15 × 3 × 2 = 90` decisions;
- after expansion block 2: `18 × 3 × 2 = 108` decisions.

Add the next precommitted block if any trigger fires:

1. **Disagreement:** within any granularity, at least 25% of sampled question cells have different substantive assessment vectors between the reviewer pair—at least 3 cells at 12 questions or 4 at 15.
2. **Tie:** the two best granularities differ by at most one question in paired-usable count, where paired-usable means both reviewers independently mark the full plan semantically valid and covered.
3. **New reusable gap:** a reusable semantic-operation or typed-contract gap absent from the committed candidate's gap set is independently identified in at least two different sampled questions.

Stop at 18 regardless of remaining uncertainty. There is no automatic 30-question/180-decision requirement. Remaining uncertainty yields vocabulary/schema revision, `NEED_MORE_HUMAN_REVIEW`, or stop/reframe—not silent expansion. Abstentions are preserved but not substantive; replacement/third reviews may be obtained until each sampled cell has two substantive judgments.

The Phase B interface must be a new versioned projection bound to the preserved representation hashes. Before an independent assessment is committed, hide the proposal's coverage, gaps, new-operator suggestions, ambiguity, hidden-reasoning, fragmentation, and rationales. Distinguish full-plan validity from the truthfulness of a partial sketch or gap diagnosis.

## Phase C result-independent representatives

The exact Phase C representatives are not selected from Phase B outcomes. The Phase B sample manifest must precommit one base-sample question per frozen stratum for Phase C before any operator review result is opened. These six IDs remain fixed after Phase B selection or revision; an unsupported or ambiguous representative is retained as a negative case rather than replaced post hoc.

## Immediate next human and technical tasks

No human should use the existing granularity HTML packets now. The A0 raw open-coding instrument, 30 views, active packet, and validator are committed and pass their deterministic packet checks. The researcher must now procedurally sign off two mutually independent, exposure-naive real-human reviewers. This manual sign-off is not machine-authenticatable under the current no-registry contract. Each reviewer independently codes the first committed-order 10-question batch using only the question-only payload, without consultation or external lookup, and submits one immutable raw 10-record artifact.

That collection creates raw human observations only. The next exact technical task is then to define, version, freeze, and validate the blinded alignment/adjudication artifact and comparator. Until that task is complete, Phase A1 semantic agreement, Phase A2 readiness, and all downstream human-evidence claims remain pending.
