# Hierarchical HybridQA data construction

이 디렉터리는 질문 의미, 환경 의존 연산자 topology, grounding, 실행 그래프를 서로 다른 감독 층으로 보존한다. 현재 산출물은 데이터 구축용 **v0.1 계약과 도구**이며 gold corpus가 아니다. 현재 연구 순서는 question-only raw open coding → 별도 blinded alignment/freeze → held-out confirmation → 환경 의존 operator granularity → 대표 사례 grounding/execution이다.

## 현재 상태

- 공식 HybridQA 소스의 이식 가능한 식별자와 해시는 `manifests/source_manifest_v0_1.json`에 기록되어 있다.
- 과거 Week 1–3 파일 다섯 개는 연구자 승인 provenance에서 byte-for-byte로 복구되었다. strict manifest는 과거 노출 100개, locked-eval 15개를 기록하며 오류가 없다.
- 역사적 IR v0.2 열 개 파일은 `../historical/ir_v0_2/`에 read-only로 격리되며, 현재 코드의 adapter가 50/50 graph와 520 node를 검증한다. parse/schema/IR-validator error는 0이고 `DEAD_NODE` warning 455개는 과거 planner의 증거이다.
- 현재 bundle은 Draft 2020-12 schema 11개와 후보 vocabulary 3개다. 정확한 최신 exact-pin 및 회귀 테스트 결과는 `../HANDOFF_CURRENT.md`를 기준으로 하며, 이전 9-schema/51-test 관측을 새 Phase A0 artifact의 검증 결과로 소급하지 않는다.
- pinned official dev에서 30개 질문을 `annotation_schema_pilot`에 결정론적으로 할당했다. 역사 노출과 overlap은 0, override는 없고 train/dev/locked-eval은 각각 0이다.
- 기존 30개 model-assisted record/90 coarse-medium-fine 표현, 90개 deterministic check, HTML packet 3개, v0.1 metric은 byte-preserved Phase B 선행 가능성 증거로 남긴다. 기존 packet은 현재 Phase A나 미래 blinded Phase B의 승인된 UI가 아니며 사용하지 않는다.
- 이전의 reviewer×granularity 6파일/180판정 task는 철회됐다. 미래 Phase B는 Phase A2 뒤 동결한 6개 stratum에서 12문항×3 granularity×2 reviewer=72판정으로 시작하고, 사전 선언 trigger에 따라 90, 최대 108판정까지만 확장한다. 정확한 ID는 A2 normalization 전에는 배정하지 않는다.
- 현재 결정은 `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`이다. A0의 30개 question-only view와 첫 10문항 packet이 commit됐고 packet-only 검사가 통과했다. 이제 연구자가 승인한 상호 독립·무노출 실제 사람 2명이 `phase_a1_batch_01`만 question-only로 독립 open-code하여 2개 파일/20개 raw record를 만든다.
- 1번 질문을 둘러싼 기존 대화는 protocol 분석일 뿐 human evidence는 0건이다. Later-layer 자료에 노출된 사람은 영향받은 exposure-naive 작업에서 제외한다. Reviewer 정체성·독립성·승인·노출 여부는 수동 절차이고 기계 인증이 아니다. Raw schema/hash validity는 semantic agreement를 뜻하지 않으며, 별도 blinded alignment/adjudication 계약과 comparator를 version/freeze하기 전에는 Phase A1 agreement나 A2 readiness를 주장하지 않는다.
- `locked_eval`은 prompt, rubric, schema, 연산자 어휘 조정에 사용하지 않는다.
- LLM 생성물의 최초 상태는 `llm_proposed`이며 `gold`가 아니다.

현재 structured proposal은 `model_id=codex_gpt-5`를 기록하지만, 인터페이스가 exact model revision과 raw model output을 노출하지 않았고 seed도 지원하지 않았다. 따라서 각각 `revision_not_exposed`, `not_exposed_by_interface`, `not_supported`로 기록되어 있다. 이는 명시적 재현성 제한이며 값을 추정하거나 exact replay 가능성을 주장하지 않는다.

역사적 condition-C 파일에는 answer와 evaluator output이 포함되어 있다. 이를 question-only semantic/obligation/abstract/operator 단계의 입력이나 예시로 사용하지 않는다.

## 계층

1. `semantic_skeleton`과 `information_obligations`: 질문만으로 필요한 정보와 의존성
2. `abstract_topology`: 환경 독립 의미 함수와 의존성
3. `operator_topology`: HybridQA 환경이 요구하는 연산자와 의존성, 아직 미grounded
4. `grounding`: 표·열·엔터티·문서 속성·리터럴·타입·join key 바인딩
5. `execution_graph`: 프로젝트 IR로 실현한 grounded graph
6. 실행 참조, 모호성, 대안 계획, provenance, 검토 상태

앞 단계에 뒤 단계의 정답·oracle·grounding을 노출하지 않는다. 리뷰 패킷은 `question_only`, `topology`, `grounding` 단계별로 가시성을 제한한다.

## 디렉터리

- `manifests/`: 과거 노출 ID, 공식 소스 identity/hash, 결정론적 역할 분할
- `schemas/`: Draft 2020-12 계층형 JSON Schema v0.1 11개
- `operator_design/`: coarse/medium/fine 후보 어휘; 파일럿 전에는 어느 것도 gold/final이 아님
- `pilot/`: 질문, question-only view/study plan, raw open-coding packet, 보존된 `llm_proposed` granularity 표현, 결정론 검사, 외부 사람 관측, 해결 주석
- `corpus/`: 검토가 끝난 train/dev/locked-eval 번들만 저장
- `tools/`: 샘플링, 검증, 세분성 비교, 리뷰 패킷, 통계 도구
- `reports/`: 근거·차단점·측정값·최종 연구 결론
- `../historical/ir_v0_2/`: 현재 코드와 분리된 byte-preserved IR v0.2 및 condition-C 역사 증거

## 재현 명령

환경 설치:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --requirement requirements.txt
```

Ubuntu에서 `venv` 생성이 실패하면 해당 Python의 `python3-venv` OS 패키지가 먼저 필요하다. 이 저장소는 관리자 권한으로 시스템 패키지를 자동 설치하지 않는다.

계약 및 테스트:

```sh
python3 data_construction/tools/check_schema_bundle.py
python3 -m unittest discover -s tests -v
sh scripts/cross_device_preflight.sh
```

프로젝트 로컬 exact-pin 환경의 정식 검사:

```sh
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python -m unittest discover -s tests -v
```

과거 ID 감사:

```sh
python3 data_construction/tools/build_historical_manifest.py \
  --recovery-provenance state/historical_recovery_provenance_v0_1.json \
  --overwrite \
  --strict
```

이 명령은 2026-08-23 연구자 승인 preservation commit을 권위로 사용해 통과했다. 결과는 100 unique exposed IDs, 15 locked-eval IDs, missing/count/provenance errors 0이다. `--overwrite`는 명시적 incomplete v0.1 audit만 교체할 수 있으므로 complete manifest를 다시 덮어쓰려 하지 않는다. 다섯 역사 원본은 앞으로도 read-only이며 공개본 개정은 새 versioned path를 써야 한다.

현재 30-question 파일럿을 만든 명령 계약:

```sh
python3 data_construction/tools/build_sample.py \
  --questions /path/to/pinned/HybridQA/released_data/dev.json \
  --pilot-count 30 \
  --role-output-dir data_construction/splits/run-v0_1
```

현재 committed allocation은 `pilot/questions.jsonl` 30건이며 zero overlap, verified source, `override_used=false`, `release_eligible=true`이다. 이 release eligibility는 해당 파일럿 할당의 source/history 계약만 뜻하며 주석이나 modeling readiness를 뜻하지 않는다. 기존 출력을 교체하려고 sampler를 재실행하지 않는다. 일반적으로 실제 입력 경로는 machine-local CLI 값일 수 있지만 manifest에는 로컬 절대경로 대신 placeholder와 source URL/commit/artifact hash를 남긴다. Diagnostic override 결과는 corpus release에 사용할 수 없다.

일반 계층 주석 검증 및 리뷰의 향후 entry-point 계약은 다음과 같다. 아래 `llm_proposals.jsonl`과 `deterministic_checks.jsonl`은 현재 granularity pilot의 파일이 아니며 아직 생성되지 않았다. Placeholder를 만들거나 존재하지 않는 입력으로 이 명령을 실행하지 않는다.

```sh
python3 data_construction/tools/validate_annotation.py data_construction/pilot/llm_proposals.jsonl
python3 data_construction/tools/build_review_packet.py \
  --questions data_construction/pilot/questions.jsonl \
  --proposals data_construction/pilot/llm_proposals.jsonl \
  --validation-checks data_construction/pilot/deterministic_checks.jsonl \
  --stage question_only
```

리뷰 패킷은 질문/제안 ID 집합이 정확히 같고, 제안 bytes에 1:1로 결속된 full-schema+structural validator pass가 있어야 한다. 허용된 review view 안에서 금지 키가 발견되면 삭제 후 계속하지 않고 실패한다. topology 단계에는 환경 schema·capability metadata만 투영하고 row/cell/passage 값은 숨긴다. 다운로드 시 익명 reviewer ID, 완료 시각, schema-compatible decision, 검토 view와 packet payload SHA-256을 기록한다. 이것은 리뷰를 수행할 수 있는 형식일 뿐 실제 사람 검토가 수행됐다는 주장이 아니다.

## Phase A question-only 구조 발견

`pilot/question_structure_study_plan_v0_1.json`과 `reports/research_sequencing_decision_v0_1.md`가 현재 phase order, 세 개의 committed-order 10문항 batch, 중단 분기, Phase B 72→90→108 규칙을 고정한다. A0 instrument의 첫 화면에는 opaque question ID, question text, unconstrained free-observation field만 보인다. 열 질문의 자유 관찰이 모두 nonempty가 된 뒤 한 번의 batch-wide action으로 열 개를 모두 read-only로 잠그고 나서야 정상 UI가 stage-2 scaffold 전체를 표시한다. Answer request, candidate structure, required information unit, dependency scaffold는 정답 ontology가 아니라 검증할 구조 가설이다. Closed semantic label, answer/cardinality/candidate kind enum, semantic-function enum, operator vocabulary, 표·열·capability·연결 문서·answer·trace·proposal·metric은 정상 view에 보이지 않는다.

이 전환은 하나의 self-contained HTML 안에서 구현한 procedural UI staging이다. Stage 2 bytes는 같은 파일에 있으므로 source/devtools/DOM 조작에 맞선 server-enforced blinding이 아니며, validator도 browser history를 인증하지 못한다. Reviewer는 이를 우회하지 않았다고 attestation한다. 또한 later-layer 금지 검사는 key 구조를 탐지할 뿐 허용된 notes/description/free-text에 붙여 넣은 의미 내용을 판별하지 못한다. 따라서 packet-only/raw pass를 stage-transition 또는 free-text contamination의 기계적 무결성 증명으로 해석하지 않는다.

아래 CLI로 committed question-only 30개 view와 active batch packet을 결정론적으로 재검증할 수 있다. Builder는 tracked implementation identity에 결속되므로 uncommitted implementation으로 canonical output을 만들지 않는다. 현재 versioned output은 이미 생성·commit됐으므로 bytes를 교체하려고 재실행하지 않는다.

```sh
python3 data_construction/tools/build_question_only_semantic_views.py
python3 data_construction/tools/build_question_structure_annotation_packet.py \
  --batch-id phase_a1_batch_01
```

기본 output은 각각 `pilot/question_only_semantic_views_v0_1.jsonl`, 그 manifest, 그리고 `pilot/question_structure_review_packets/question_structure_calibration_batch_1_v0_1.html`, 그 manifest다. 현재 30 views/10 packet items가 materialized됐고 packet payload SHA-256은 `c86920e63cde36f285312bbbe3da58fe10c4de2e51e33745e22291a7568eb57b`이다. Packet 생성은 human annotation 생성이 아니며 현재 human raw record는 0이다. Exact rendering·hash·batch/order 계약을 검사하는 packet-only 명령은 다음과 같다.

```sh
python3 data_construction/tools/validate_question_structure_annotations.py \
  --batch-id phase_a1_batch_01 \
  --packet-only
```

한 reviewer가 packet에서 export한 정확히 10-record JSON array는 다음처럼 검증한다. `--checks-output`은 write-once이며 다른 bytes를 명시적으로 교체할 때만 `--overwrite`를 추가한다.

```sh
python3 data_construction/tools/validate_question_structure_annotations.py \
  /path/to/question_structure_annotations_phase_a1_batch_01_reviewer-pseudonym.json \
  --batch-id phase_a1_batch_01 \
  --checks-output /path/to/question_structure_checks_phase_a1_batch_01_reviewer-pseudonym.jsonl
```

Validator는 exact packet reconstruction, schema/canonical hash, UTC·pseudonym·attestation, batch/order/single-reviewer, exposure=false, 최소·국소 source-cue substring의 localization integrity, ID/reference/DAG/root/sink, complete topology의 obligation coverage, later-layer 금지 key를 검사한다. 이 검사는 자유문장의 의미 contamination, cue의 semantic alignment, reviewer identity/approval, browser 조작 이력, 사람 간 agreement를 인증하지 않는다. 연구자 승인은 아직 별도 machine-authenticatable registry가 없는 procedural manual gate다.

Packet과 validator가 준비됐으므로, 다음에는 연구자 수동 승인을 받은 서로 다른 실제 사람 2명이 상담·외부 lookup 없이 첫 10문항을 독립 작성한다. 각자 한 개의 immutable 10-record 파일을 제출해 총 20 raw record가 된다. Q1 대화는 evidence가 아니며, proposal/환경/answer 등 금지 입력을 본 사람은 영향받은 무노출 작업에서 제외한다. Raw validity는 observation integrity일 뿐 semantic confirmation이 아니다. 같은 scaffold 안에서 semantic skeleton, obligations, topology를 연결해 유도한 raw triple은 `elicited_linked_representation`이며 질문 구조에서 common executable graph로 가는 독립 evidence가 아니다. 두 raw set을 얻은 다음 exact technical task는 두 파일에 결속되는 별도 blinded alignment/adjudication schema·artifact·comparator를 만들고 결과를 보기 전에 version을 동결하는 것이다. Phase B normalization이나 cross-level claim 전에 upstream mapping reference를 보지 않는 별도 pass·다른 annotator의 versioned frozen independent/blinded topology elicitation 또는 prediction과 held-out evaluation gate가 추가로 필요하다.

## 보존된 Operator-granularity 파일럿 — Phase B로 연기

아래 명령과 artifact 설명은 기존 v0.1 evidence를 재현·감사하기 위한 기록이다. 현재 사람 작업으로 실행하지 않으며 기존 HTML은 미래 Phase B blind UI로 승인되지 않았다. Phase B sample ID와 6-stratum taxonomy는 A2 question-only evidence normalization 뒤 별도 versioned manifest에서만 정한다.

현재 committed input view를 원래 pinned WikiTables-WithLinks checkout에서 재구성하는 CLI 계약은 다음과 같다. checkout은 source manifest의 exact commit에 있어야 하며 machine-local cache이지 canonical project state가 아니다. builder는 질문 30개와 선택된 `tables_tok`/`request_tok` 60개 파일을 hash-bound manifest에 결속한다. review view에는 질문, table identity/title/section, column label·index·link capability, 환경 capability만 있으며 row/cell 값, linked-document ID/text, answer, trace, grounding은 없다.

```sh
python3 data_construction/tools/build_granularity_views.py \
  --wikitables-checkout /path/to/pinned/WikiTables-WithLinks
```

현재 versioned view를 단지 교체하기 위해 이 명령을 재실행하지 않는다. 검증 목적의 재구성은 별도 출력 경로에 만들고 committed manifest/hash와 비교한다.

구조화된 proposal plan을 live view와 세 vocabulary에 결속해 30×3 표현을 만들고 90개 검사를 실행하는 명령은 다음과 같다. 기본값은 현재 versioned 경로를 가리킨다.

```sh
python3 data_construction/tools/build_granularity_representations.py
python3 data_construction/tools/validate_operator_granularity.py \
  data_construction/pilot/granularity_representations.jsonl
```

representation provenance는 `llm_proposed`이고 `gold`가 아니다. Validator는 plan의 결정론적 materialization, 정확한 question/view 순서, schema, vocabulary membership, DAG root/sink, leakage 금지 키, live artifact hash, validator code/implementation 결속을 검사한다. 현재 결과는 30 records, 90 checks, errors=0, warnings=0이다.

각 granularity의 self-contained HTML packet과 manifest를 만드는 정확한 명령은 다음과 같다. Builder는 사람 검토를 생성하지 않으며 manifest의 `human_reviews_created_by_builder`는 `false`, `reviews_included`는 `0`이다.

```sh
python3 data_construction/tools/build_granularity_review_packet.py \
  --questions data_construction/pilot/questions.jsonl \
  --input-views data_construction/pilot/granularity_input_views.jsonl \
  --input-views-manifest data_construction/pilot/granularity_input_views_manifest_v0_1.json \
  --representations data_construction/pilot/granularity_representations.jsonl \
  --validation-checks data_construction/pilot/granularity_deterministic_checks.jsonl \
  --granularity coarse \
  --output data_construction/pilot/review_packets/operator_granularity_coarse_v0_1.html \
  --manifest-output data_construction/pilot/review_packets/operator_granularity_coarse_v0_1_manifest.json

python3 data_construction/tools/build_granularity_review_packet.py \
  --questions data_construction/pilot/questions.jsonl \
  --input-views data_construction/pilot/granularity_input_views.jsonl \
  --input-views-manifest data_construction/pilot/granularity_input_views_manifest_v0_1.json \
  --representations data_construction/pilot/granularity_representations.jsonl \
  --validation-checks data_construction/pilot/granularity_deterministic_checks.jsonl \
  --granularity medium \
  --output data_construction/pilot/review_packets/operator_granularity_medium_v0_1.html \
  --manifest-output data_construction/pilot/review_packets/operator_granularity_medium_v0_1_manifest.json

python3 data_construction/tools/build_granularity_review_packet.py \
  --questions data_construction/pilot/questions.jsonl \
  --input-views data_construction/pilot/granularity_input_views.jsonl \
  --input-views-manifest data_construction/pilot/granularity_input_views_manifest_v0_1.json \
  --representations data_construction/pilot/granularity_representations.jsonl \
  --validation-checks data_construction/pilot/granularity_deterministic_checks.jsonl \
  --granularity fine \
  --output data_construction/pilot/review_packets/operator_granularity_fine_v0_1.html \
  --manifest-output data_construction/pilot/review_packets/operator_granularity_fine_v0_1_manifest.json
```

Packet에서 내려받은 raw review는 representation에 내장하지 않는 외부 JSON array이다. 한 파일은 한 reviewer와 한 granularity의 30개 질문을 정확한 순서로 포함한다. 각 annotation은 `review_packet_payload_sha256`와 `reviewed_representation_sha256`에 결속되고, envelope는 canonical `annotation_sha256`을 가진다. 판정은 `accept`, `accept_with_edits`, `reject`, `abstain` 중 하나이고, 모든 판정은 `semantic_validity`, `coverage_status`, `ambiguity_present`, `hides_reasoning`, `excessive_fragmentation` 평가 차원을 채워야 한다. `abstain`은 다섯 차원을 모두 `uncertain`으로 기록하며 calibration 관측에서 제외된다.

사람 입력 없이 현재 structural metric을 재계산하는 명령은 다음과 같다. Integrity는 통과하지만 실제 사람 calibration이 없으므로 metric을 쓰고 종료 코드 `2`를 내는 것이 예상 결과다.

```sh
python3 data_construction/tools/compare_operator_granularity.py \
  data_construction/pilot/granularity_representations.jsonl \
  --questions data_construction/pilot/questions.jsonl \
  --input-views data_construction/pilot/granularity_input_views.jsonl \
  --input-views-manifest data_construction/pilot/granularity_input_views_manifest_v0_1.json \
  --validation-checks data_construction/pilot/granularity_deterministic_checks.jsonl
```

아래는 보존된 comparator가 요구했던 legacy full-30 calibration 입력 예시다. 이는 현재 next task가 아니며 180개 판정을 수집하라는 지시로 사용하지 않는다. 미래 Phase B는 새 blind projection과 72→90→108 stopping rule을 구현해야 한다.

```sh
python3 data_construction/tools/compare_operator_granularity.py \
  data_construction/pilot/granularity_representations.jsonl \
  --questions data_construction/pilot/questions.jsonl \
  --input-views data_construction/pilot/granularity_input_views.jsonl \
  --input-views-manifest data_construction/pilot/granularity_input_views_manifest_v0_1.json \
  --validation-checks data_construction/pilot/granularity_deterministic_checks.jsonl \
  --human-review /path/to/reviewer_a_coarse.json \
  --human-review /path/to/reviewer_b_coarse.json \
  --human-review /path/to/reviewer_a_medium.json \
  --human-review /path/to/reviewer_b_medium.json \
  --human-review /path/to/reviewer_a_fine.json \
  --human-review /path/to/reviewer_b_fine.json \
  --review-packet-manifest data_construction/pilot/review_packets/operator_granularity_coarse_v0_1_manifest.json \
  --review-packet-manifest data_construction/pilot/review_packets/operator_granularity_medium_v0_1_manifest.json \
  --review-packet-manifest data_construction/pilot/review_packets/operator_granularity_fine_v0_1_manifest.json
```

사람 reviewer ID 두 개는 granularity 사이에 재사용할 수 있으므로 “여섯 명”을 뜻하지 않는다. 다만 각 granularity 안에서는 서로 다른 두 ID가 필요하고, 정체성과 독립성은 `procedural_not_machine_verifiable`이다. 두 substantive assessment hash가 다를 때 불일치가 관측된다. packet HTML bytes와 manifest, live payload hash도 다시 계산해 검증한다. reject, edit, 불일치가 있거나 모든 review가 abstain이면 원 표현의 의미 확인 및 selection은 완료되지 않는다. Coverage만으로 vocabulary를 선택하지 않는다.

일반 corpus 통계:

```sh
python3 data_construction/tools/compute_annotation_stats.py \
  data_construction/pilot/resolved_annotations.jsonl \
  --validation-checks data_construction/pilot/deterministic_checks.jsonl
```

Granularity representation에 자체 기입한 불일치 표시는 사람 근거로 인정하지 않는다. 통계는 동일 annotation bytes와 vocabulary에 결속된 full-schema+structural validator pass JSONL 없이는 integrity pass/evidence complete를 주장하지 않는다. 복구된 condition-C의 520 node와 455 `DEAD_NODE` warning은 과거 planner artifact의 진단값이지 현재 30-question granularity pilot의 graph-length, coverage, 또는 quality 측정값이 아니다.

## 상태 의미

- `complete`: 요구 입력과 검사가 모두 존재
- `incomplete`: 일부 근거/검토가 없음
- `blocked`: 외부 입력 또는 연구자 결정 없이는 과학적으로 안전하게 진행 불가
- `planned_not_run`: 실행하지 않았으며 결과가 없는 상태

빈 파일이나 0건 통계를 성공한 corpus로 취급하지 않는다. 현재처럼 packet만 있고 사람 검토가 0건이면 `human_calibration_complete=false`, disagreement 관측 수 0, rate `null`로 기록한다.
