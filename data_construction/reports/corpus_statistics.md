# Corpus statistics

## 2026-08-23 question-first sequencing addendum

Resolved annotation corpus는 여전히 0건이다. 현재 순서는 question-only raw open coding → 별도 blinded alignment/freeze → held-out confirmation → deferred operator granularity → representative grounding/execution이다. 기존 30 model-assisted record, 90 coarse-medium-fine representation, 90 deterministic check, 세 packet, v0.1 metric은 byte-preserved Phase B feasibility statistics이고 corpus record가 아니다. 기존 packet은 승인된 Phase A/Phase B human UI가 아니며 이전 180-decision task는 철회됐다.

A0 packet/raw validator는 commit·검증됐다. Immediate human task는 서로 독립적이고 exposure-naive인 researcher-approved real human 2명이 첫 committed-order 10문항을 question-only open-code해 2파일/20 raw record를 만드는 것이다. Q1 논의는 zero evidence다. Identity/independence/approval/exposure는 manual procedural sign-off이고 machine authentication이 아니다. Raw record validity는 semantic agreement나 corpus confirmation이 아니며, 별도 blinded alignment/adjudication contract와 comparator가 frozen되기 전에는 agreement statistics를 만들지 않는다.

Future Phase B 통계는 A2-derived frozen six-stratum sample에 대해 base 72 decisions, trigger-based 90, maximum 108을 분리 보고한다. Exact sample IDs는 A2 normalization 뒤 precommit한다. 현재 bundle은 11 schemas/3 vocabularies이며 최신 exact-pin/test 결과는 handoff 기준이다.

## 2026-08-23 이전 Phase 2 실행 결과 addendum — 보존된 snapshot

당시 granularity artifact 상태는 `structural_integrity_complete_human_calibration_pending`이고 잠정 결정은 `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`였다. Pilot proposal과 결정론 검사는 생성됐지만, resolved annotation corpus는 여전히 구축하지 않았다. 아래에서 pilot 구조 통계와 corpus 건수를 분리한다.

| 항목 | 현재 값 |
|---|---:|
| 역사 노출 고유 question ID | 100 |
| 역사 locked-eval question ID | 15 |
| release-eligible `annotation_schema_pilot` 질문 | 30 |
| 새 `annotation_train` 질문 | 0 |
| 새 `annotation_dev` 질문 | 0 |
| 새 `locked_eval` 질문 | 0 |
| model-assisted proposal record | 30 — `llm_proposed` |
| coarse/medium/fine representation | 30 / 30 / 30 — 총 90 |
| deterministic check | 90 pass, 0 error, 0 warning |
| review packet | 3 — 사람 판정 미포함 |
| human review record | 0 — pending |
| adjudication / resolved annotation | 0 / 0 — pending/not_created |
| corpus record | 0 — NOT_BUILT |

### Pilot proposal 진단 통계

| 지표 | Coarse | Medium | Fine |
|---|---:|---:|---:|
| coverage | 14/30 (46.67%) | 13/30 (43.33%) | 13/30 (43.33%) |
| graph 길이 평균 / 중앙값 / 범위 | 2.57 / 3 / 2–3 | 4.83 / 5 / 4–8 | 6.87 / 7 / 6–9 |
| 평균 고유 연산자 수 | 2.57 | 4.60 | 6.70 |
| 새 연산자 필요 | 16/30 (53.33%) | 17/30 (56.67%) | 17/30 (56.67%) |
| ambiguity | 19/30 (63.33%) | 19/30 (63.33%) | 19/30 (63.33%) |
| hidden reasoning | 30/30 (100%) | 0/30 (0%) | 0/30 (0%) |
| excessive fragmentation | 0/30 (0%) | 0/30 (0%) | 19/30 (63.33%) |
| human disagreement | N/A (관측 0) | N/A (관측 0) | N/A (관측 0) |

이 표는 `operator_granularity_metrics_v0_1.json`의 model-assisted proposal 집계다. Coverage, ambiguity, hidden reasoning, fragmentation은 human-confirmed corpus statistics가 아니며, 90개 표현을 90개 resolved annotation 또는 corpus record로 합산해서는 안 된다. 사람 검토가 없으므로 disagreement는 N/A이고 암묵적 100% 합의가 아니다.

30문항 배정은 핀된 source와 역사 노출 100개의 비중복을 검증했고, input view는 answer/trace/grounding을 노출하지 않는다. 90개 deterministic pass는 schema, DAG, vocabulary, source/view/artifact hash 결속의 구조적 무결성을 뜻할 뿐 semantic correctness를 뜻하지 않는다. 현재 `human_calibration_complete=false`, `semantic_confirmation_complete=false`, `evidence_complete=false`, `selection_ready=false`이며 어떤 vocabulary도 선택·동결하지 않았다. Gold corpus와 modeling-ready 상태도 없다.

당시 exact task는 각 granularity에 두 독립 reviewer ID를 배정해 총 180개 판정을 수집하는 것이었다. 이 task는 위 sequencing 결정으로 철회됐다. Pilot proposal 수치를 corpus-level 확정 통계로 승격하지 않는 제한은 계속 유효하다.

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
