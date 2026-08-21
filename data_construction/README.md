# Hierarchical HybridQA data construction

이 디렉터리는 질문 의미, 환경 의존 연산자 topology, grounding, 실행 그래프를 서로 다른 감독 층으로 보존한다. 현재 산출물은 데이터 구축용 **v0.1 계약과 도구**이며 gold corpus가 아니다.

## 현재 상태

- 공식 HybridQA 소스의 이식 가능한 식별자와 해시는 `manifests/source_manifest_v0_1.json`에 기록한다.
- 과거 Week 1–3 파일이 없으면 `historical_exposed_ids.json`의 빈 ID 목록을 “과거 노출 없음”으로 해석하지 않는다.
- 과거 노출 ID 감사가 완전하지 않으면 `build_sample.py`는 기본적으로 새 역할 분할을 거부한다.
- 질문 파일 SHA-256이 핀된 공식 source manifest에 없으면 샘플러는 기본적으로 분할을 거부한다.
- `locked_eval`은 prompt, rubric, schema, 연산자 어휘 조정에 사용하지 않는다.
- LLM 생성물의 최초 상태는 `llm_proposed`이며 `gold`가 아니다.

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

과거 ID 감사:

```sh
python3 data_construction/tools/build_historical_manifest.py \
  --recovery-provenance state/historical_recovery_provenance_v0_1.json \
  --overwrite \
  --strict
```

`--overwrite`는 현재의 명시적 incomplete v0.1 audit만 교체할 수 있다. complete/released/unknown manifest나 다섯 역사 원본은 덮어쓰지 않으며, 이후 공개본 개정은 새 versioned path를 써야 한다. v0.1 release verifier는 full 40-hex Git commit OID와 그 commit의 실제 5개 파일 byte hash만 권위로 인정한다. 백업/아티팩트 보관소에서 복구했다면 연구자 승인 preservation-first Git migration으로 원본 bytes를 그대로 commit한 뒤 그 commit을 provenance authority로 사용한다. `--strict`의 exit 2는 다섯 역사 파일의 부재/빈 ID, 알려진 Week 1·2 규모 불일치, 또는 이 provenance 부재를 뜻한다. 파일이 단순히 존재한다는 이유만으로 gate를 열지 않는다. 이를 해결하기 전에는 release 가능한 split을 만들지 않는다.

파일럿 split 예시:

```sh
python3 data_construction/tools/build_sample.py \
  --questions /path/to/pinned/HybridQA/released_data/dev.json \
  --pilot-count 30 \
  --role-output-dir data_construction/splits/run-v0_1
```

실제 경로는 machine-local CLI 입력일 수 있지만, 출력 manifest에는 로컬 절대경로 대신 placeholder와 소스의 URL/commit/artifact hash를 남긴다. 역할은 한 파일에 합치지 않고 pilot/train/dev/locked-eval별 파일로 분리한다. 기존 출력이 하나라도 있거나 입력·출력 경로가 충돌하면 stale locked artifact와 덮어쓰기를 피하기 위해 실패한다. 불완전한 역사 감사에서 `--allow-incomplete-history`를 쓰거나 미검증 소스에 `--allow-unverified-source`를 쓰면 결과는 diagnostic-only이고 corpus release에 사용할 수 없다. Release gate는 매니페스트의 문자열만 믿지 않고 역사 원본 5개와 provenance receipt를 다시 읽어 hash·ID 합집합을 검증한다.

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

Granularity 비교의 `annotation_disagreement` boolean은 사람 근거로 인정하지 않는다. 각 표현에는 서로 다른 reviewer ID 2개 이상의 versioned review record가 필요하며, review record의 question ID·granularity·packet SHA와 검토 대상 representation SHA가 실제 입력에 결속돼야 불일치가 관측된다. 최소 20개의 서로 다른 질문과 세 어휘에 유효한 DAG가 없으면 study는 incomplete다. 통계는 동일 annotation bytes와 vocabulary에 결속된 full-schema+structural validator pass JSONL 없이는 integrity pass/evidence complete를 주장하지 않는다. 통계 도구의 graph 길이는 operator topology와 호환용 legacy inline graph까지만 계산한다. v0.1 외부 IR execution graph 길이는 IR v0.2 parser/artifact dereference가 복구되기 전에는 N/A다.

## 상태 의미

- `complete`: 요구 입력과 검사가 모두 존재
- `incomplete`: 일부 근거/검토가 없음
- `blocked`: 외부 입력 또는 연구자 결정 없이는 과학적으로 안전하게 진행 불가
- `planned_not_run`: 실행하지 않았으며 결과가 없는 상태

빈 파일이나 0건 통계를 성공한 corpus로 취급하지 않는다. 사람 검토를 실제로 받지 않았다면 `human_*` 상태를 기록하지 않는다.
