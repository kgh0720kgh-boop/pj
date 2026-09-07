# Hierarchical HybridQA data construction

이 디렉터리는 질문 의미, 환경 의존 연산자 topology, grounding, 실행 그래프를 서로 다른 감독 층으로 보존한다. 현재 산출물은 versioned 연구 계약과 탐색 artifact이며 gold corpus가 아니다. 동결된 question-only AI extractor/normalizer의 누적 N=300 실험, 30-family candidate-backbone library, 71-question representative environment realization, candidate-derived normalization v0.2, targeted crossed-author re-authoring v0.1, targeted authoring-instrument revision v0.2까지 완료됐다. Instrument v0.2는 같은 기존 challenge 6문항에서 모든 동결 기준을 통과했다. Narrowed-grounding plan v0.1도 결과 부재 상태에서 동결됐으며, 현재 단계는 그 계획의 schema·packet builder·static binding validator·analyzer를 구현하고 runtime receipt를 동결하는 것이다. 인간 검토는 현재 필수 gate가 아니라 향후 주장에 필요한 경우의 선택적 표본 감사로 연기됐다.

## 현재 상태

- 공식 HybridQA 소스의 이식 가능한 식별자와 해시는 `manifests/source_manifest_v0_1.json`에 기록되어 있다.
- 과거 Week 1–3 파일 다섯 개는 연구자 승인 provenance에서 byte-for-byte로 복구되었다. strict manifest는 과거 노출 100개, locked-eval 15개를 기록하며 오류가 없다.
- 역사적 IR v0.2 열 개 파일은 `../historical/ir_v0_2/`에 read-only로 격리되며, 현재 코드의 adapter가 50/50 graph와 520 node를 검증한다. parse/schema/IR-validator error는 0이고 `DEAD_NODE` warning 455개는 과거 planner의 증거이다.
- 현재 bundle은 Draft 2020-12 schema 11개와 후보 vocabulary 3개다. 정확한 최신 exact-pin 및 회귀 테스트 결과는 `../HANDOFF_CURRENT.md`를 기준으로 하며, 이전 9-schema/51-test 관측을 새 Phase A0 artifact의 검증 결과로 소급하지 않는다.
- pinned official dev에서 30개 질문을 `annotation_schema_pilot`에 결정론적으로 할당했다. 역사 노출과 overlap은 0, override는 없고 train/dev/locked-eval은 각각 0이다.
- 기존 30개 model-assisted record/90 coarse-medium-fine 표현, 90개 deterministic check, HTML packet 3개, v0.1 metric은 byte-preserved Phase B 선행 가능성 증거로 남긴다. 기존 packet은 현재 Phase A나 미래 blinded Phase B의 승인된 UI가 아니며 사용하지 않는다.
- 이전의 reviewer×granularity 6파일/180판정 task는 철회됐다. 미래 Phase B는 Phase A2 뒤 동결한 6개 stratum에서 12문항×3 granularity×2 reviewer=72판정으로 시작하고, 사전 선언 trigger에 따라 90, 최대 108판정까지만 확장한다. 정확한 ID는 A2 normalization 전에는 배정하지 않는다.
- 누적 N=300은 300/300 structurally valid record와 byte-exact N=100 prefix를 보존한다. Fine/contracted/topology/task family는 각각 39/30/10/70개이고, contracted singleton mass 0.0467, N100→new200 transfer 0.915, top-10 coverage 0.9133이다. Uncertain은 94/300, provisional `OTHER` 사용은 0/300이다.
- 사전 선언된 N=1,000 trigger 네 개가 모두 false여서 candidate-library branch를 택했고, 그 후 대표 환경 실현, normalization v0.2, targeted re-authoring v0.1, instrument revision v0.2와 grounding 계획 동결까지 완료했다. 현재 운영 판정은 `IMPLEMENT_FROZEN_NARROWED_GROUNDING_PROTOCOL`이다.
- N=100과 N=300의 evidence class는 모두 `ai_exploratory_non_human_non_gold`이다. 하나의 동결된 AI extractor와 결정론적 normalizer 아래의 반복성·곡선 모양만 기술하며, semantic correctness, human agreement, universal saturation, common executable graph, grounding/execution, gold 또는 modeling readiness를 뜻하지 않는다.
- candidate-backbone library v0.1은 300개 전부를 30개 family에 정확히 한 번 배정하고, 9 recurrent/7 doubleton/14 singleton을 보존한다. 대표 표본은 30개 family 전체를 덮는 71개 deterministic coverage-stress sample이며 ordered-ID SHA-256은 `5403debe2cbe9c7f55ded0a01b49d7c42bf03e53a71350efe269bbd3c0bdcb2e`이다. 이는 희귀 family를 의도적으로 과대표집하므로 확률표본이나 prevalence 추정 표본이 아니다.
- 대표 환경 run은 71개 view, 71개 E1 backbone 적합성 판단, 71개 E2 record/93개 open candidate, 71개 five-signal outcome, 285개 통과 check를 materialize했다. E1은 adequate 64, partially adequate 5, indeterminate 2였고 E2는 71개 모두 available이었다. Grounding·execution·answer recovery는 모두 미평가다.
- Raw E2는 producer partition에 매우 민감했다. Partition별 candidate 수는 36/19/21/17, environment-extension node 수는 95/2/47/0이므로 17/30 family의 raw structural heterogeneity를 질문 고유 특성이나 공통 exact graph의 반증으로 해석할 수 없다.
- Normalization v0.2는 기존 93개와 crossed-author 34개, 총 127개 candidate만 사용했다. Full eligible/provisional-only/ineligible은 121/1/5이고 technical loss, eligible-set contamination, unclassified adapter candidate는 모두 0이다. Crossed full-eligible semantic exact match는 10/16, mean Jaccard는 0.65625, coverage는 27/32이며 challenge/control exact match는 1/7과 9/9다. 동결 기준 실패로 grounding은 계속 금지된다.
- Targeted re-authoring v0.1은 같은 기존 challenge ID 6개에 두 새 fresh-context AI author를 배정했다. 12개 record/14개 candidate 중 full/provisional/ineligible은 9/0/5이고 technical loss, contamination, unclassified, profile loss는 모두 0이다. 그러나 full-eligible author-question coverage는 8/12, semantic intersection은 2/6, exact match는 1/6, mean Jaccard는 0.25여서 coverage-failure 분기가 선택됐다.
- Targeted authoring-instrument v0.2는 동일 6개 ID와 두 fresh-context author를 사용했다. Draft/final은 각각 12 record/14 candidate이며 feedback 12건은 target-node, required dependency, mapped output, output arity만 보고했다. Final candidate 14/14가 full eligible이고 coverage 12/12, semantic exact 6/6, mean Jaccard 1.0, v0.1 reference compatibility 12/12, profile loss 0으로 모든 동결 기준을 통과했다. Draft가 이미 모두 local-complete였고 final parsed record가 0/12 변경됐으므로 checker feedback의 인과 효과는 주장하지 않는다.
- Narrowed-grounding plan v0.1은 같은 6문항의 14후보·52슬롯을 모두 보존하며, 예정된 결과 파일 20개가 없는 commit에서 동결됐다. 다음 작업은 계획대로 runtime을 구현·검증하고 결과 생성 전 receipt를 커밋하는 것이다. 현재 grounding·execution·answer recovery 결과는 0이다. 자세한 근거는 `reports/research_sequencing_decision_v0_10.md`에 있다.
- `diagnostics/ai_question_structure_pipeline_v0_1/`의 이전 two-reviewer shadow run은 byte-preserved direction-finding/engineering evidence다. 두 AI reviewer의 60개 구조화 record, 30개 blinded alignment, 20개 독립 topology-only record와 최종 분석은 검증됐지만 모두 `non_human_non_gold`이고 correctness나 human agreement 근거가 아니다.
- v0.1 human question-only view·packet·validator도 byte-preserved됐으나 현재 active gate가 아니다. Human raw file/record, agreement observation, adjudication은 모두 0이며 인간 절차를 나중에 재개하더라도 별도 blinded alignment/adjudication 계약 전에는 agreement나 A2 readiness를 주장하지 않는다.
- `locked_eval`은 prompt, rubric, schema, 연산자 어휘 조정에 사용하지 않는다.
- LLM 생성물의 최초 상태는 `llm_proposed`이며 `gold`가 아니다.

현재 structured proposal은 `model_id=codex_gpt-5`를 기록하지만, 인터페이스가 exact model revision과 raw model output을 노출하지 않았고 seed도 지원하지 않았다. 따라서 각각 `revision_not_exposed`, `not_exposed_by_interface`, `not_supported`로 기록되어 있다. 이는 명시적 재현성 제한이며 값을 추정하거나 exact replay 가능성을 주장하지 않는다.

역사적 condition-C 파일에는 answer와 evaluator output이 포함되어 있다. 이를 question-only semantic/obligation/abstract/operator 단계의 입력이나 예시로 사용하지 않는다.

## Narrowed-grounding 계획 검증

저장소 루트에서 실행한다. 이 명령은 계획·원본 해시·Git 동결 순서와
출력 부재를 확인하며 grounding 결과를 생성하거나 검증하지 않는다.

```sh
.venv/bin/python -B data_construction/tools/freeze_narrowed_grounding_plan_v0_1.py --validate-only --require-output-absence
```

계획과 설계는 `exploration/ai_question_structure_scale_v0_1/contracts/narrowed_grounding_{plan,design}_v0_1.json`,
프로토콜은 같은 영역의 `prompts/narrowed_grounding_v0_1.md`다.
후속 runtime 구현은 이 동결 계약을 따라야 하며, 변경이 필요하면 새 버전을 만든다.

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
- `diagnostics/`: canonical human evidence와 격리한 non-evidentiary pipeline rehearsal, 계약, AI 산출물, 검증, 분석
- `exploration/`: 활성 scale-first question-only AI extraction, deterministic signature, exposure ledger, 포화도 metric/report; 모두 non-human/non-gold
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
.venv/bin/python -B data_construction/tools/build_representative_environment_realization.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_normalization.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_crossed_author_sensitivity.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_normalization_v0_2.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_targeted_reauthor.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_targeted_instrument_v0_2.py --validate-only
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

## 활성 scale-first question-only 구조 탐색

`pilot/question_structure_study_plan_v0_2.json`이 scale-first 단계 순서를, `reports/research_sequencing_decision_v0_3.md`가 완료된 N=300 판정을, `reports/research_sequencing_decision_v0_4.md`가 candidate library와 대표 환경 run 진입을, `reports/research_sequencing_decision_v0_5.md`가 완료된 대표 run의 해석과 다음 exact task를 기록한다. 질문마다 opaque ID와 exact question text만 입력하고, 하나의 primary AI semantic-backbone record를 만든 뒤 model output과 독립된 deterministic normalizer로 fine semantic DAG, same-role split/merge contracted DAG, topology shape, task signature를 계산했다.

완료된 `exploration/ai_question_structure_scale_v0_1/run_001/`의 기계적 결과는 다음과 같다.

- valid records: 100/100
- contracted semantic-DAG families: 17
- contracted singleton question mass: 0.09
- first-30에서 new-70으로의 contracted-family transfer: 0.7143
- uncertain records: 29/100
- provisional `OTHER` questions: 0/100
- precommitted decision: `EXPAND_UNCHANGED_TO_N300`

Primary metric의 마지막 판정은 원래 동결한 규칙을 정확히 실행한 값이다. 별도 `partition_sensitivity_metrics_v0_1.json`과 `interpretive_addendum_v0_1.md`는 그 판정을 소급 변경하지 않으면서, 반복 신규 family 5개 중 cross-partition 지지를 받은 것은 0개이고 raw 5/6 branch/join이 normalized 0/1이라는 해석 제한을 추가한다. Contracted dominant family 62개는 fine dominant family 46개보다 넓으므로 contracted recurrence는 same-role split/merge 민감도의 상한으로 취급한다.

누적 N=300 산출물은 `exploration/ai_question_structure_scale_v0_1/cumulative_n300_v0_1/`에 있다. 300/300 record가 통과했고 N=100 bytes는 exact prefix다. Contracted family는 30개, singleton mass는 0.0467, N100→new200 transfer는 0.915, final-50 sequential novelty는 0.10이다. N=100에 없던 contracted family 13개 중 3개가 반복되고 2개가 cross-partition에서 반복되지만 material rule을 만족한 것은 1개다. 네 N=1,000 trigger가 모두 false이므로 같은 extractor로 N=1,000까지 확장하지 않는다.

Candidate-backbone library와 representative-sampling contract는 `exploration/ai_question_structure_scale_v0_1/contracts/candidate_backbone_library_plan_v0_1.json` 및 `candidate_backbone_library_v0_1/`에 동결·materialize됐다. 30개 contracted family를 사후 의미 병합 없이 유지하며 frequency, segment/partition/block support, fine/topology/task crosswalk, member ID, canonical graph를 기록한다. Recurrent/doubleton/singleton family는 각각 9/7/14개이고, 71개 대표 ID는 environment/outcome field를 selection input으로 사용하지 않은 계약에서 commit됐다. 이것은 별도의 이전 작업에서 중첩 ID의 schema/capability metadata를 본 적이 없다는 사실까지 machine-authenticate하지는 않는다. Fine/contracted/partition 차이는 항상 함께 보고하며, same-role contraction을 semantic equivalence로 취급하지 않는다.

대표 환경 run은 implementation→pre-raw plan→environment views→E1 commit→fresh-context E2 순서로 동결됐다. 71/71 question에 full table과 table-link closure를 제공하되 official answer/trace는 투영하지 않았고, E2에는 E1 내용 대신 commit된 hash binding만 제공했다. 결과는 open notation에서 71/71 target의 ungrounded realization이 가능하다는 expressivity evidence다. 이는 실행 가능성이나 정답 회수 성공을 뜻하지 않는다.

Equivalence-aware normalization v0.1은 implementation `c372ef4b43a88b80d85f69359197bdedd3c40e61`, output 부재 상태의 plan `83428b9698546de054db672e72dbae880ef4c1ac`, materialized result `a9d3272c6cef4f411bf8f124159a634920c0571e` 순서로 동결됐다. 93개 candidate 모두 reversible label-free projection으로 재구성되며 equivalent=89, provisionally-equivalent=4, not-equivalent=0, projection loss=0이다. Semantic quotient 39개와 environment-adapter signature 19개를 분리했고 candidate는 question별 set으로 비교했다. Multi-question family 16개 중 semantic-set instability가 6개이며 고정 question/producer 배정으로 효과를 분리할 수 없어 동결된 분기는 `RUN_PRECOMMITTED_CROSSED_AUTHOR_SENSITIVITY`다. Grounding은 아직 허용되지 않는다.

Crossed-author sensitivity v0.1은 이미 environment-exposed인 16개만 재사용했다. 네 기존 partition에서 각 4개, E1 challenge 7개 전부와 adequate control 9개를 포함하며 두 fresh-context AI author가 모든 16개를 독립적으로 처리했다. Semantic-set exact match는 16/16이지만 target-anchored v0.1 quotient의 한계 때문에 partial candidate도 같은 target hash를 가질 수 있다. Adapter-set exact match는 0/16이고, 34개 후보 중 equivalent/provisional/not-equivalent는 20/9/5다. 동결 기준에 따라 `REVISE_EQUIVALENCE_NORMALIZATION_CONTRACT`가 선택됐으며 grounding은 계속 금지된다. 이 분기가 요구한 작업은 같은 127개 기존 후보만 사용해 candidate-derived eligibility와 factorized adapter components를 분리하는 normalization v0.2를 output 부재 상태의 새 plan과 함께 동결하는 것이었고, 아래와 같이 완료됐다. 이는 producer confound 진단이지 human review, majority vote, gold annotation 또는 unseen evaluation이 아니며 새 reserve/locked-eval ID를 사용하지 않는다.

Normalization v0.2는 implementation `16868477069f4413392c4f968c3e94c510fcb7a8`, output 부재 상태의 127-candidate plan `3d636e57b88da4469540a8ed47fa413147857060`, materialized result `a13fa72c75049e09a966a9ea11e514c4a961841e` 순서로 동결됐다. Candidate-derived semantic profile과 full/provisional/ineligible eligibility를 분리하고 adapter를 modality/cardinality, semantic-relative placement, split/fuse boundary, output arity로 factorize했다. 기술·adapter 계약은 통과했지만 crossed 의미 exact 10/16, mean Jaccard 0.65625, full-eligible coverage 27/32, challenge exact 1/7로 사전 기준에 미달했다. Control은 9/9 exact다. 따라서 `NARROW_OR_REAUTHOR_BEFORE_GROUNDING` 분기가 선택됐고, 새 ID 없이 실패한 challenge 6개에 대한 targeted re-authoring v0.1을 수행했다.

Targeted re-authoring v0.1은 implementation `51b5204d568efc55f6d1fdff3d7d1b2bf1f6f008`, output 부재 plan `4fa67b5f908a3b323610451964aeedcaaef06a2f`, isolated packets `5e45170f86c8f9b540003d2ffeb896407f26594f`, 두 author output `c83bb1c8583fbd9ce1fa394f92f092889244b156`/`a2610732d7b23fb6ad0e88698c19e7d4ebf37af9`, result `f9377db09ef8d34cc846801730980e933e4e8331` 순서로 보존됐다. 기술 계약은 통과했지만 8/12 coverage 때문에 `REVISE_TARGETED_AUTHORING_INSTRUMENT_BEFORE_GROUNDING`이 선택됐다. 다음 plan은 prior-result/semantic-signature 노출 없이 candidate-local completeness feedback만 추가해야 하며, v0.1 record를 수정하거나 grounding을 시작할 수 없다.

Targeted authoring-instrument revision v0.2는 implementation `6703293a3b73539940864d681a034abfd939707b`, 17개 output 부재 plan `3caedbe7a84ee2cac15cf24a33c7f0ff26177f21`, equal-visibility packets `50801e80caa86fc771be0bed85c6ba687e835539`, immutable drafts `2df347a76f381c2d1e6deec02f34e4f38bd4ea4a`, candidate-local feedback `1a92e63d9e7abd12f4ae70c0b250512f42f61601`, finals `3de0a547770e3c225ce0cb9f8990cf00558af308`, result `d22a9beca223f49d7af17c8657aafdbf8753de4f` 순서로 보존됐다. Final 14/14 candidate가 full eligible이고 두 author의 semantic set은 6/6 exact다. Draft와 final parsed records가 동일하므로 전체 개정 instrument의 안정성만 지지하며 checker 단독 효과는 식별하지 않는다. 동결 분기는 별도 narrowed-grounding plan의 freeze만 허용한다.

누적 산출물은 다음 명령으로 재검증할 수 있다.

```sh
.venv/bin/python data_construction/tools/analyze_ai_question_structure_cumulative_n300.py --validate-only
.venv/bin/python data_construction/tools/build_candidate_backbone_library.py --validate-only
.venv/bin/python -B data_construction/tools/build_representative_environment_realization.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_normalization.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_crossed_author_sensitivity.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_normalization_v0_2.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_targeted_reauthor.py --validate-only
.venv/bin/python -B data_construction/tools/build_operator_equivalence_targeted_instrument_v0_2.py --validate-only
```

## 보존된 v0.1 Phase A human question-only 계약

`pilot/question_structure_study_plan_v0_1.json`과 `reports/research_sequencing_decision_v0_1.md`는 이전 human-first phase order, 세 개의 committed-order 10문항 batch, 중단 분기, Phase B 72→90→108 규칙을 보존한다. 이 계약과 산출물은 덮어쓰거나 N=100 결과로 소급 변경하지 않는다. A0 instrument의 첫 화면에는 opaque question ID, question text, unconstrained free-observation field만 보인다. 열 질문의 자유 관찰이 모두 nonempty가 된 뒤 한 번의 batch-wide action으로 열 개를 모두 read-only로 잠그고 나서야 정상 UI가 stage-2 scaffold 전체를 표시한다. Answer request, candidate structure, required information unit, dependency scaffold는 정답 ontology가 아니라 검증할 구조 가설이다. Closed semantic label, answer/cardinality/candidate kind enum, semantic-function enum, operator vocabulary, 표·열·capability·연결 문서·answer·trace·proposal·metric은 정상 view에 보이지 않는다.

이 전환은 하나의 self-contained HTML 안에서 구현한 procedural UI staging이다. Stage 2 bytes는 같은 파일에 있으므로 source/devtools/DOM 조작에 맞선 server-enforced blinding이 아니며, validator도 browser history를 인증하지 못한다. Reviewer는 이를 우회하지 않았다고 attestation한다. 또한 later-layer 금지 검사는 key 구조를 탐지할 뿐 허용된 notes/description/free-text에 붙여 넣은 의미 내용을 판별하지 못한다. 따라서 packet-only/raw pass를 stage-transition 또는 free-text contamination의 기계적 무결성 증명으로 해석하지 않는다.

아래 CLI로 committed question-only 30개 view와 보존된 batch packet을 결정론적으로 재검증할 수 있다. Builder는 tracked implementation identity에 결속되므로 uncommitted implementation으로 canonical output을 만들지 않는다. 현재 versioned output은 이미 생성·commit됐으므로 bytes를 교체하려고 재실행하지 않는다.

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

이 human lane은 현재 deferred이며 N=300보다 앞선 next task가 아니다. 나중에 재개한다면 연구자 수동 승인을 받은 서로 다른 실제 사람 2명이 상담·외부 lookup 없이 첫 10문항을 독립 작성하고, 각자 immutable 10-record 파일 하나를 제출해 총 20 raw record를 만든다는 v0.1 계약을 그대로 따른다. Q1 대화는 evidence가 아니며, proposal/환경/answer 등 금지 입력을 본 사람은 영향받은 무노출 작업에서 제외한다. Raw validity는 observation integrity일 뿐 semantic confirmation이 아니다. 두 raw set 뒤에도 결과를 해석하기 전 별도 blinded alignment/adjudication schema·artifact·comparator를 version/freeze해야 한다.

## Non-evidentiary AI shadow pipeline

`diagnostics/ai_question_structure_pipeline_v0_1/`은 보존된 human 계약의 mechanics를 끝까지 rehearsal한 별도 namespace다. 현재 scale-first run과 합치거나 그 산출물을 새 correctness 근거로 재분류하지 않는다. 계약·prompt·comparator는 commit `fb2ba9e29221c16dd8e1ee71439339d17a92818a`에서 model output 전에 동결됐다. Run 001은 stage-1 60건, structured representation 60건, identity-blinded alignment 30건, upstream structure를 보지 않은 held-out topology 20건을 포함하며 deterministic live reconstruction이 통과한다.

Compact result는 10 full-equivalence/20 compatible-variation, independent topology structural-signature match 0.85/0.90이다. 그러나 ambiguity flag는 25/30, alternative-plan presence는 20/30만 일치했고 reviewer 1은 instrument issue 19개를, reviewer 2는 0개를 보고했다. 또한 v0.1 question disposition은 scalar alternative-plan conflict 2건을 grouped core conflict가 없다는 이유로 compatible variation에 남긴다. 따라서 headline compatibility rate를 correctness, zero conflict, human agreement, Phase A1 pass, Phase A2 held-out evidence, common graph로 읽지 않는다. `run_001/analysis/interpretive_addendum_v0_1.md`가 이 제한을 보존한다.

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

빈 파일이나 0건 통계를 성공한 corpus로 취급하지 않는다. 보존된 human lane처럼 packet만 있고 사람 검토가 0건이면 `human_calibration_complete=false`, disagreement 관측 수 0, rate `null`로 기록한다. N=100의 100 structurally valid AI records도 human count나 gold/corpus status를 변경하지 않는다.
