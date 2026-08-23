# Operator granularity study v0.1

## 2026-08-23 현재 상태 addendum

현재 in-progress 상태: `DATA_SOURCE_READY_FOR_ANNOTATION_PILOT`

Week 1–3 파일 5개는 researcher-approved workspace에서 byte-for-byte 복구되어 commit `1995c0cf79ab8e987773041d456d4a1b8df19793`에 보존됐고 provenance receipt가 검증됐다. 과거 노출 audit는 exposed 100/locked 15, 오류 0으로 strict-complete가 되었다. 핀된 공식 source에서 이 역사 노출 100개를 제외한 `annotation_schema_pilot` 30문항도 결정론적으로 배정됐다. 배정은 `release_eligible=true`, override 없음, 역할 간 overlap 없음이며 질문 view에는 answer/weak trace 등 금지 필드가 없다. 따라서 이전의 표본 확정 차단은 해제됐다.

다만 coarse/medium/fine representation 자체는 아직 작성하지 않았다. Coverage, graph 길이, 연산자 수, 새 연산자 필요율, 추론 은닉, 과도한 파편화, 사람 간 불일치는 모두 계속 `N/A/NOT_RUN`이며, 어떤 vocabulary도 경험적으로 선택하거나 동결하지 않았다. LLM proposal, human review, resolved annotation, corpus도 `NOT_RUN`이다.

역사 IR v0.2 계약과 condition C graph 50개는 10-file read-only quarantine 및 recovery manifest와 함께 commit `dcc5ac5c14e9acb5c689b400a4046708b6837ac3`에 보존됐다. Current-side adapter baseline은 50 records/520 nodes에 대해 parse/schema/v0.2 validator 오류 0개와 `DEAD_NODE` 경고 455개를 재현했다. 이는 역사 artifact 무결성/validator 연결 증거이지 현재 어휘의 granularity 우수성 증거가 아니다.

프로젝트 로컬 exact-pin `.venv`는 8개 schema/3개 vocabulary 검증을 통과했고, IR adapter hardening과 live annotation-reference bridge를 포함한 최종 pinned suite는 `43/43` 통과했다.

다음 exact task는 배정된 같은 30문항 각각에 대해 leakage-safe coarse/medium/fine 표현을 만들고 결정론 검사를 실행하는 것이다. 그 다음 raw 판정과 대상 hash를 보존하는 human calibration을 수행한다. 현재 결정 `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`는 유지되며, `DATA_SOURCE_READY_FOR_ANNOTATION_PILOT`는 최종 modeling decision이나 modeling-ready 선언이 아니다.

아래는 표본 배정 전인 2026-08-21의 역사적 상태 기록이다.

## 2026-08-21 역사적 snapshot

상태: `PLANNED_NOT_RUN — HISTORICAL_EXPOSURE_GATE_BLOCKED`

## 결론

coarse/medium/fine 후보 어휘는 비교 가능한 버전 계약으로 만들었지만, 어떤 어휘도 아직 동결하거나 gold로 채택하지 않았다. 공식 HybridQA dev 질문은 충분히 확보 가능하나 과거 Week 1–3 노출 ID가 복구되지 않아 안전한 20–30문항 파일럿을 확정할 수 없다. 따라서 coverage만 계산하거나 임의 질문으로 어휘를 선택하지 않았다.

## 계획된 측정값

| 지표 | Coarse | Medium | Fine |
|---|---:|---:|---:|
| 검토 질문 수 | N/A | N/A | N/A |
| coverage | N/A | N/A | N/A |
| 평균/중앙 graph 길이 | N/A | N/A | N/A |
| 질문당 고유 연산자 수 | N/A | N/A | N/A |
| 새 연산자 필요율 | N/A | N/A | N/A |
| 사람 간 annotation 불일치 | N/A | N/A | N/A |
| 추론을 숨기는 사례 | N/A | N/A | N/A |
| 과도하게 파편화하는 사례 | N/A | N/A | N/A |

`N/A`는 0이 아니라 아직 관측하지 않았다는 뜻이다.

## 재현 절차

과거 노출 감사가 complete가 된 후 동일한 질문별로 세 표현을 작성하고 다음을 실행한다.

```sh
python3 data_construction/tools/compare_operator_granularity.py \
  data_construction/pilot/granularity_representations.jsonl
```

각 표현에는 `coverage_status`, topology nodes, `requires_new_operator`, `hides_reasoning`, `excessive_fragmentation`과 근거를 기록한다. 사람 간 불일치는 임의 boolean을 신뢰하지 않는다. `human_review_evidence.canonicalization=sorted_compact_json_utf8_sha256_v0_1` 아래 서로 다른 익명 `reviewer_id`를 가진 독립 검토 2개 이상이 필요하다. 각 versioned review record는 question ID, granularity, reviewed view, packet SHA-256, 실제 representation SHA-256과 판정을 담고 raw record hash가 재계산되어야 한다. 빈 annotation, 다른 질문/세분성, 다른 packet, 또는 검토 대상 hash 불일치가 있으면 disagreement는 반드시 N/A다. 도구의 연구 최소 질문 수는 20개이며 CLI로 낮출 수 없다.

## 선택 기준

- schema 간 재사용성
- 명시적 typed contract와 실행/tool binding 가능성
- 조합 가능성과 선택한 층에서의 semantic atomicity
- 주석 안정성 및 사람 검토 비용
- coverage와 예외 수
- graph 길이 및 planner 탐색 복잡도
- coarse 표현이 숨기는 추론과 fine 표현이 만드는 불필요한 분절

현재 잠정 결정: `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`.
