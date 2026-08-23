# Corpus statistics

## 2026-08-23 현재 상태 addendum

현재 in-progress 상태는 `DATA_SOURCE_READY_FOR_ANNOTATION_PILOT`이며, corpus는 아직 구축하지 않았다. 아래 수치는 질문 역할 배정과 역사 audit의 현재 사실을 annotation/corpus 산출물과 구분한다.

| 항목 | 현재 값 |
|---|---:|
| 역사 노출 고유 question ID | 100 |
| 역사 locked-eval question ID | 15 |
| release-eligible `annotation_schema_pilot` 질문 | 30 |
| 새 `annotation_train` 질문 | 0 |
| 새 `annotation_dev` 질문 | 0 |
| 새 `locked_eval` 질문 | 0 |
| coarse/medium/fine representation | 0 — NOT_RUN |
| LLM proposal | 0 — NOT_RUN |
| human review/adjudication | 0 — NOT_RUN |
| resolved annotation | 0 — NOT_RUN |
| corpus record | 0 — NOT_BUILT |

30문항 배정은 핀된 source와 source-ID inventory를 검증하고 역사 노출 100개를 제외해 결정론적으로 수행했다. Manifest는 `release_eligible=true`, `override_used=false`, `zero_overlap_verified=true`이고 질문 view에 금지된 answer/trace 필드가 없다. 이 30은 “release 가능한 annotation 30개”가 아니라 주석을 시작할 수 있는 질문 30개다.

역사 파일 5개는 commit `1995c0cf79ab8e987773041d456d4a1b8df19793`에 byte-for-byte 보존됐고 verified strict manifest는 오류 없이 complete다. IR v0.2 10-file quarantine과 condition C graph 50개는 commit `dcc5ac5c14e9acb5c689b400a4046708b6837ac3`에 보존됐다. Current-side adapter baseline은 50 records/520 nodes를 parse/schema/v0.2 validator 오류 0개로 검증하고 `DEAD_NODE` 경고 455개를 재현했다. 이는 역사 validation 통계이므로 50개 graph를 새 corpus record나 현재 annotation 통계에 합산하지 않는다.

프로젝트 로컬 exact-pin `.venv`는 8개 schema/3개 vocabulary 검증을 통과했고, IR adapter hardening과 live annotation-reference bridge를 포함한 최종 pinned suite는 `43/43` 통과했다. Granularity 표현과 결정론 검사, human calibration이 완료되기 전에는 모호성·대안 계획·topology 길이·합의율을 계산하지 않는다.

다음 exact task는 같은 30문항의 leakage-safe coarse/medium/fine representation을 만들고 결정론 검사 후 human calibration을 수행하는 것이다.

아래는 역사 gate 해제 및 pilot 배정 전인 2026-08-21의 snapshot이다.

## 2026-08-21 역사적 snapshot

상태: `CORPUS_NOT_BUILT`

## 현재 관측값

| 항목 | 값 |
|---|---:|
| release 가능한 annotation 수 | N/A |
| annotation_schema_pilot | N/A |
| annotation_train | N/A |
| annotation_dev | N/A |
| locked_eval | N/A |
| 모호성 비율 | N/A |
| 대안 계획 수 | N/A |
| 평균 operator topology 길이 | N/A |
| 외부 IR execution graph 길이 | N/A — IR v0.2 parser/artifact dereference 미복구 |
| 사람 검토 합의 | N/A |

Split은 아직 배정되지 않았다. 따라서 위 값을 0으로 보고하거나 빈 corpus 통계로 해석하면 안 된다.

## 차단 이유

- `historical_exposed_ids.json`가 `incomplete_missing_historical_artifacts`
- 새 질문과 과거 locked-eval/test 역할의 비중복을 검증할 수 없음
- operator granularity 파일럿과 사람 검토가 실행되지 않음
- 실행 IR v0.2 파일이 이 작업공간에 없어 grounded graph 검증을 연결할 수 없음

## 생성 명령

검토 완료 annotation이 생긴 뒤 다음 명령이 원시 JSONL에서 역할, 검토 상태, 모호성, 대안 계획, operator topology 길이와 연산자별 빈도·타입·문맥·schema·예외를 계산한다. v0.1 `execution_graph`는 inline node가 아니라 외부 IR reference envelope이므로, 외부 graph 길이는 IR v0.2 parser와 artifact dereference를 복구한 뒤에만 관측한다. 도구의 현재 execution-graph 길이 필드는 호환용 legacy inline graph에만 적용된다.

```sh
python3 data_construction/tools/compute_annotation_stats.py \
  data_construction/pilot/resolved_annotations.jsonl \
  --validation-checks data_construction/pilot/deterministic_checks.jsonl
```

`deterministic_checks.jsonl`의 각 pass는 annotation canonical hash, 전체 annotation 파일 hash, schema hash, operator-vocabulary hash와 full-schema+structural validation mode에 1:1로 결속되어야 한다. 없거나 불일치하면 통계는 diagnostic output만 남기고 integrity/evidence complete를 거부한다. 사람 검토가 없으면 agreement를 계산하거나 암묵적으로 100%로 간주하지 않는다.
