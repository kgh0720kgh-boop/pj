# Pilot artifacts

이 디렉터리는 30-question `annotation_schema_pilot`의 입력, model-assisted operator-granularity 제안, 결정론 검사, 사람 검토용 packet을 보존한다. 현재 structural integrity는 완료됐지만 human calibration은 0건이며, 모든 제안은 `llm_proposed`이고 `gold`가 아니다.

## 현재 artifact

- `questions.jsonl`: pinned official dev에서 결정론적으로 할당된 30개 질문. 역사 노출 overlap과 diagnostic override는 0이다.
- `granularity_input_views.jsonl`과 `granularity_input_views_manifest_v0_1.json`: 질문별 question view와 leakage-reduced operator view. 표의 identity/title/section, column label·index·link capability, 환경 capability만 보이며 row/cell 값, linked-document ID/text, answer, trace, grounding은 보이지 않는다.
- `granularity_representation_plan_v0_1.json`: 30개 질문과 coarse/medium/fine 후보를 담은 structured proposal plan.
- `granularity_representations.jsonl`: plan을 live view와 세 vocabulary에 결속한 30개 record, 90개 candidate representation.
- `granularity_deterministic_checks.jsonl`: 90개 representation의 Draft 2020-12, structural DAG, vocabulary, leakage, live-artifact 및 validator-provenance 검사. 현재 90/90 pass, errors=0, warnings=0이다.
- `review_packets/`: coarse/medium/fine self-contained HTML과 hash-bound manifest. 세 manifest 모두 `packet_created_no_human_reviews`, `reviews_included=0`이며 packet 생성은 사람 검토가 아니다.

현재 proposal provenance는 `model_id=codex_gpt-5`를 기록한다. Exact model revision과 raw model output은 인터페이스에서 노출되지 않았고 seed도 지원되지 않아 각각 `revision_not_exposed`, `not_exposed_by_interface`, `not_supported`로 기록했다. 따라서 structured artifact는 hash-bound이지만 original generation의 exact replay는 주장할 수 없다.

## 검토 계약

각 HTML packet은 candidate representation과 허용된 operator view만 포함하고, 그 canonical payload의 SHA-256을 manifest에 기록한다. Packet에서 내보낸 raw review JSON은 representation과 분리된 외부 입력이다. 한 파일은 stable pseudonymous reviewer ID 한 개와 granularity 한 개에 대한 정확히 30개의 ordered record를 담는다.

각 review annotation은 다음에 결속된다.

- `question_id`와 `granularity`
- original candidate의 `reviewed_representation_sha256`
- packet의 `review_packet_payload_sha256`
- UTC `completed_at`
- envelope의 canonical `annotation_sha256`

판정은 `accept`, `accept_with_edits`, `reject`, `abstain` 중 하나다. 모든 record는 `semantic_validity`, `coverage_status`, `ambiguity_present`, `hides_reasoning`, `excessive_fragmentation`의 다섯 assessment 차원을 갖는다. `accept`는 원 표현과 assessment를 그대로 확인하고, `accept_with_edits`는 schema-valid corrected representation과 그 hash를 포함해야 하며, `reject`는 `semantic_validity=invalid`여야 한다. `abstain`은 모든 assessment를 `uncertain`으로 기록하고 substantive calibration 및 disagreement 관측에서 제외된다.

Human calibration 최소 입력은 granularity마다 서로 다른 reviewer ID 두 개, 즉 reviewer×granularity 파일 6개와 decision 180개다. 같은 두 사람이 세 granularity를 모두 검토할 수 있으므로 여섯 명을 뜻하지 않는다. Reviewer 정체성과 독립성은 `procedural_not_machine_verifiable`이다. Reject, edit, substantive assessment disagreement는 adjudication 전까지 vocabulary selection을 막는다.

## 현재 상태와 다음 작업

`../reports/operator_granularity_metrics_v0_1.json`의 현재 상태는 `structural_integrity_complete_human_calibration_pending`이고 결정은 `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`이다. 사람 review record와 disagreement 관측은 모두 0이며 rate는 `null`이다. 따라서 vocabulary는 선택·동결되지 않았고 corpus는 gold 또는 modeling-ready가 아니다.

다음 exact task는 세 packet에 대해 독립적인 substantive human review 6개 파일을 수집해 live packet/representation hash를 검증하고 comparator를 다시 실행한 뒤, 모든 reject/edit/disagreement를 adjudicate하는 것이다. 정확한 생성·검증·비교 명령은 `../README.md`에 있다.

기존 allocation, view, representation, packet을 단지 새로 만들기 위해 덮어쓰지 않는다. 변경이 과학 계약을 바꾸면 새 versioned artifact와 migration note를 만든다. Diagnostic override 산출물은 release 가능한 pilot이나 locked-eval 근거로 승격할 수 없다.
