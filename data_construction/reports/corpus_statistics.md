# Corpus statistics

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
