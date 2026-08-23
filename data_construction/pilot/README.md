# Pilot artifacts

이 디렉터리는 30-question `annotation_schema_pilot`의 question-only Phase A artifact와 byte-preserved operator-granularity Phase B 선행 증거를 함께 보존한다. 현재 순서는 raw open coding → 별도 blinded alignment/freeze → held-out confirmation → operator granularity → grounding/execution이다. Packet이나 schema의 존재는 human evidence, semantic confirmation, gold를 뜻하지 않는다.

## 현재 artifact

- `questions.jsonl`: pinned official dev에서 결정론적으로 할당된 30개 질문. 역사 노출 overlap과 diagnostic override는 0이다.
- `question_structure_study_plan_v0_1.json`: 세 개의 committed-order 10문항 batch, Phase A stopping branch, Phase B 72→90→108 sampling rule을 고정한 machine-readable plan.
- `question_only_semantic_views_v0_1.jsonl`과 manifest: opaque question ID와 exact question text만 담는 committed 30개 projection. 환경·answer·trace·proposal을 포함하지 않는다.
- `question_structure_review_packets/`: active batch의 committed 10-question blank open-coding packet과 manifest. Scaffold는 answer request, candidate structure, required information unit, dependency를 묻지만, 그 scaffold 자체가 검증할 구조 가설이며 closed semantic/operator enum을 제공하지 않는다. Packet-only 검사는 통과했고 human annotation은 0이다.
- `granularity_input_views.jsonl`과 `granularity_input_views_manifest_v0_1.json`: 질문별 question view와 leakage-reduced operator view. 표의 identity/title/section, column label·index·link capability, 환경 capability만 보이며 row/cell 값, linked-document ID/text, answer, trace, grounding은 보이지 않는다.
- `granularity_representation_plan_v0_1.json`: 30개 질문과 coarse/medium/fine 후보를 담은 structured proposal plan.
- `granularity_representations.jsonl`: plan을 live view와 세 vocabulary에 결속한 30개 record, 90개 candidate representation.
- `granularity_deterministic_checks.jsonl`: 90개 representation의 Draft 2020-12, structural DAG, vocabulary, leakage, live-artifact 및 validator-provenance 검사. 현재 90/90 pass, errors=0, warnings=0이다.
- `review_packets/`: coarse/medium/fine self-contained HTML과 hash-bound manifest. 세 manifest 모두 `packet_created_no_human_reviews`, `reviews_included=0`이다. 이들은 deferred evidence이고 현재 Phase A 또는 미래 blinded Phase B human UI로 승인되지 않았다.

현재 proposal provenance는 `model_id=codex_gpt-5`를 기록한다. Exact model revision과 raw model output은 인터페이스에서 노출되지 않았고 seed도 지원되지 않아 각각 `revision_not_exposed`, `not_exposed_by_interface`, `not_supported`로 기록했다. 따라서 structured artifact는 hash-bound이지만 original generation의 exact replay는 주장할 수 없다.

## 현재 Phase A raw observation 계약

Question-only packet과 raw validator는 commit·검증됐다. 이제 연구자가 수동으로 승인한 서로 다른 실제 사람 2명은 상호 상담이나 외부 lookup 없이 committed order의 첫 10문항을 독립 작성한다. 각 reviewer가 immutable 10-record 파일 하나를 제출하므로 총 2파일/20 raw record다. Reviewer identity, independence, approval, prior-exposure attestation은 procedural/manual이며 machine-authenticated가 아니다. 한 HTML 안의 batch-wide lock은 정상 UI staging일 뿐 source/DOM inspection에 맞선 server-enforced blinding이 아니며, key 기반 금지 검사는 허용 free-text의 의미 contamination까지 탐지하지 못한다.

질문 1에 관한 앞선 대화는 protocol 분석이고 human evidence는 0이다. Environment view, candidate graph, model rationale, answer, trace 등 later-layer material을 본 사람은 영향받은 exposure-naive 작업에서 제외한다. Raw record가 schema-valid·hash-bound·substantive여도 이는 observation integrity만 뜻한다. Semantic unit normalization, reviewer alignment, agreement score, adjudication은 아직 구현되지 않았으며, 두 raw set 뒤 별도 versioned blind contract와 comparator를 결과 해석 전에 동결해야 한다.

## 보존된 legacy granularity 검토 계약

각 HTML packet은 candidate representation과 허용된 operator view만 포함하고, 그 canonical payload의 SHA-256을 manifest에 기록한다. Packet에서 내보낸 raw review JSON은 representation과 분리된 외부 입력이다. 한 파일은 stable pseudonymous reviewer ID 한 개와 granularity 한 개에 대한 정확히 30개의 ordered record를 담는다.

각 review annotation은 다음에 결속된다.

- `question_id`와 `granularity`
- original candidate의 `reviewed_representation_sha256`
- packet의 `review_packet_payload_sha256`
- UTC `completed_at`
- envelope의 canonical `annotation_sha256`

판정은 `accept`, `accept_with_edits`, `reject`, `abstain` 중 하나다. 모든 record는 `semantic_validity`, `coverage_status`, `ambiguity_present`, `hides_reasoning`, `excessive_fragmentation`의 다섯 assessment 차원을 갖는다. `accept`는 원 표현과 assessment를 그대로 확인하고, `accept_with_edits`는 schema-valid corrected representation과 그 hash를 포함해야 하며, `reject`는 `semantic_validity=invalid`여야 한다. `abstain`은 모든 assessment를 `uncertain`으로 기록하고 substantive calibration 및 disagreement 관측에서 제외된다.

위 legacy comparator는 granularity마다 서로 다른 reviewer ID 두 개, 즉 reviewer×granularity 파일 6개와 decision 180개를 요구하도록 구현됐다. 이 수치는 현재 next task가 아니며 기존 HTML로 사람 수집을 시작하면 안 된다. 미래 Phase B는 A2-derived six-stratum taxonomy를 먼저 동결하고 12문항×3×2=72판정에서 시작해 사전 선언 trigger로 90, 최대 108판정까지 확장하는 새 blind interface를 사용한다. 정확한 ID는 A2 normalization 뒤에만 배정한다.

## 현재 상태와 다음 작업

`../reports/operator_granularity_metrics_v0_1.json`의 `structural_integrity_complete_human_calibration_pending`은 보존된 v0.1 Phase B artifact 상태다. 사람 review record와 disagreement 관측은 모두 0이고 rate는 `null`이다. 현재 전체 결정은 계속 `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`이며 vocabulary는 선택·동결되지 않았고 corpus는 gold 또는 modeling-ready가 아니다.

다음 human task는 materialized Phase A0 packet의 첫 10문항에 대한 exposure-naive 독립 open coding 2파일/20 raw record다. 그 다음 technical task는 blinded alignment/adjudication 계약과 comparator의 versioning·freeze다. 정확한 명령은 `../README.md` 및 최신 handoff에 있다.

기존 allocation, view, representation, packet을 단지 새로 만들기 위해 덮어쓰지 않는다. 변경이 과학 계약을 바꾸면 새 versioned artifact와 migration note를 만든다. Diagnostic override 산출물은 release 가능한 pilot이나 locked-eval 근거로 승격할 수 없다.
