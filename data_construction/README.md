# Hierarchical HybridQA data construction

이 디렉터리는 질문 의미, 환경 의존 연산자 topology, grounding, 실행 그래프를 서로 다른 감독 층으로 보존한다. 현재 산출물은 데이터 구축용 **v0.1 계약과 도구**이며 gold corpus가 아니다.

## 현재 상태

- 공식 HybridQA 소스의 이식 가능한 식별자와 해시는 `manifests/source_manifest_v0_1.json`에 기록되어 있다.
- 과거 Week 1–3 파일 다섯 개는 연구자 승인 provenance에서 byte-for-byte로 복구되었다. strict manifest는 과거 노출 100개, locked-eval 15개를 기록하며 오류가 없다.
- 역사적 IR v0.2 열 개 파일은 `../historical/ir_v0_2/`에 read-only로 격리되며, 현재 코드의 adapter가 50/50 graph와 520 node를 검증한다. parse/schema/IR-validator error는 0이고 `DEAD_NODE` warning 455개는 과거 planner의 증거이다.
- exact-pin `.venv`에서 Draft 2020-12 schema 8개와 후보 vocabulary 3개가 errors=0, warnings=0으로 통과했다.
- pinned official dev에서 30개 질문을 `annotation_schema_pilot`에 결정론적으로 할당했다. 역사 노출과 overlap은 0, override는 없고 train/dev/locked-eval은 각각 0이다.
- 현재 진행 중인 과학 상태는 `DATA_SOURCE_READY_FOR_ANNOTATION_PILOT`이다. 이는 gold, 최종 어휘 선택, modeling-ready corpus를 뜻하지 않는다.
- 다음 exact task는 같은 30개 질문에 leakage-safe coarse/medium/fine 표현을 만들고, 결정론 검사와 사람 calibration을 수행하는 것이다.
- `locked_eval`은 prompt, rubric, schema, 연산자 어휘 조정에 사용하지 않는다.
- LLM 생성물의 최초 상태는 `llm_proposed`이며 `gold`가 아니다.

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
- `schemas/`: Draft 2020-12 계층형 JSON Schema v0.1
- `operator_design/`: coarse/medium/fine 후보 어휘; 파일럿 전에는 어느 것도 gold/final이 아님
- `pilot/`: 질문, LLM 제안, 결정론 검사, 사람 검토, 해결 주석
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

주석 검증 및 리뷰:

```sh
python3 data_construction/tools/validate_annotation.py data_construction/pilot/llm_proposals.jsonl
python3 data_construction/tools/build_review_packet.py \
  --questions data_construction/pilot/questions.jsonl \
  --proposals data_construction/pilot/llm_proposals.jsonl \
  --validation-checks data_construction/pilot/deterministic_checks.jsonl \
  --stage question_only
```

리뷰 패킷은 질문/제안 ID 집합이 정확히 같고, 제안 bytes에 1:1로 결속된 full-schema+structural validator pass가 있어야 한다. 허용된 review view 안에서 금지 키가 발견되면 삭제 후 계속하지 않고 실패한다. topology 단계에는 환경 schema·capability metadata만 투영하고 row/cell/passage 값은 숨긴다. 다운로드 시 익명 reviewer ID, 완료 시각, schema-compatible decision, 검토 view와 packet payload SHA-256을 기록한다. 이것은 리뷰를 수행할 수 있는 형식일 뿐 실제 사람 검토가 수행됐다는 주장이 아니다.

세분성·통계:

```sh
python3 data_construction/tools/compare_operator_granularity.py \
  data_construction/pilot/granularity_representations.jsonl
python3 data_construction/tools/compute_annotation_stats.py \
  data_construction/pilot/resolved_annotations.jsonl \
  --validation-checks data_construction/pilot/deterministic_checks.jsonl
```

Granularity 비교의 `annotation_disagreement` boolean은 사람 근거로 인정하지 않는다. 각 표현에는 서로 다른 reviewer ID 2개 이상의 versioned review record가 필요하며, review record의 question ID·granularity·packet SHA와 검토 대상 representation SHA가 실제 입력에 결속돼야 불일치가 관측된다. 최소 20개의 서로 다른 질문과 세 어휘에 유효한 DAG가 없으면 study는 incomplete다. 통계는 동일 annotation bytes와 vocabulary에 결속된 full-schema+structural validator pass JSONL 없이는 integrity pass/evidence complete를 주장하지 않는다. 복구된 condition-C의 520 node와 455 `DEAD_NODE` warning은 과거 planner artifact의 진단값이지 현재 30-question granularity pilot의 graph-length, coverage, 또는 quality 측정값이 아니다.

## 상태 의미

- `complete`: 요구 입력과 검사가 모두 존재
- `incomplete`: 일부 근거/검토가 없음
- `blocked`: 외부 입력 또는 연구자 결정 없이는 과학적으로 안전하게 진행 불가
- `planned_not_run`: 실행하지 않았으며 결과가 없는 상태

빈 파일이나 0건 통계를 성공한 corpus로 취급하지 않는다. 사람 검토를 실제로 받지 않았다면 `human_*` 상태를 기록하지 않는다.
