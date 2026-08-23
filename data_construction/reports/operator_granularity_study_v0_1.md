# Operator granularity study v0.1

## 2026-08-23 sequencing revision — Phase B deferred

이 연구의 active gate는 operator proposal 평가가 아니라 question-only structure discovery다. 실행 순서는 raw open coding → 별도 blinded alignment/freeze → held-out confirmation → environment-aware operator granularity → representative grounding/execution이다. 아래 v0.1 실행 결과와 30 record/90 representation/90 deterministic check/3 HTML packet/v0.1 metric은 byte-for-byte 보존된 feasibility evidence이며 삭제·재해석하지 않는다. 그러나 기존 packet은 현재 Phase A 또는 미래 blinded Phase B human UI로 승인되지 않았고, proposal 자기평가를 reviewer에게 미리 보여 주므로 지금 사람 검토에 사용하지 않는다.

이전 six reviewer-by-granularity file/180-decision task는 철회됐다. Phase B 진입에는 Phase A2의 eligible held-out confirmation, frozen semantic evidence normalization, 결과를 보기 전에 commit한 six-stratum taxonomy와 exact sample manifest, 새 blind projection이 필요하다. Base는 12 questions × 3 granularities × 2 substantive reviewers = 72 decisions다. Precommitted disagreement/tie/new-reusable-gap trigger가 발동하면 15 questions/90 decisions, 다시 발동하면 18 questions/108 decisions로 확장하고 거기서 중단한다. Exact ID와 stratum은 A2 normalization 전에는 배정하지 않는다.

새 Phase B UI는 independent assessment를 commit하기 전에 proposal의 coverage, gap, new-operator suggestion, ambiguity, hidden-reasoning, fragmentation, rationale를 숨기고, partial sketch의 진실성과 full-plan completeness를 구분해야 한다. Reviewer identity·independence·approval은 수동 절차이며 machine-authenticated가 아니다. 현재 결정은 `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`; 어떤 vocabulary도 선택·동결하지 않는다.

현재 A0 packet/raw validator는 commit·검증됐다. Immediate human task는 연구자 승인·상호 독립·무노출 실제 사람 2명이 첫 committed-order 10문항을 question text만 보고 open-code하여 2파일/20 raw record를 만드는 것이다. Q1 대화는 zero human evidence이고 later-layer exposure가 있는 사람은 영향받은 작업에서 제외된다. Raw validity 뒤 별도 blinded alignment/adjudication contract와 comparator를 freeze하기 전에는 agreement나 Phase A2 readiness를 주장하지 않는다.

## 2026-08-23 이전 Phase 2 실행 결과 addendum — 보존된 snapshot

당시 granularity artifact 상태는 `structural_integrity_complete_human_calibration_pending`이었고 잠정 결정은 `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`였다. 고정된 30개 `annotation_schema_pilot` 질문에 대해 coarse/medium/fine 표현을 각각 하나씩, 총 90개 만들었다. 이 표현은 model-assisted `llm_proposed` 산출물이며 사람이 확인한 annotation이나 gold가 아니다. 기록된 model ID는 `codex_gpt-5`이고, exact model revision과 raw model output은 실행 인터페이스에서 노출되지 않았다는 한계도 provenance에 명시했다.

`granularity_deterministic_checks.jsonl`의 90개 검사는 모두 통과했고 오류와 경고는 각각 0개다. Comparator도 30개 질문과 세 granularity의 완전한 ID 대응, live artifact hash, vocabulary/schema 결속을 검증해 `integrity_complete=true`로 기록했다. 이는 구조 및 provenance 무결성 결과일 뿐 표현의 의미적 정답성을 입증하지 않는다.

| 지표 | Coarse | Medium | Fine |
|---|---:|---:|---:|
| representation 수 | 30 | 30 | 30 |
| proposal coverage | 14/30 (46.67%) | 13/30 (43.33%) | 13/30 (43.33%) |
| graph 길이 평균 / 중앙값 | 2.57 / 3 | 4.83 / 5 | 6.87 / 7 |
| graph 길이 범위 | 2–3 | 4–8 | 6–9 |
| 질문당 평균 고유 연산자 수 | 2.57 | 4.60 | 6.70 |
| 새 연산자 필요 | 16/30 (53.33%) | 17/30 (56.67%) | 17/30 (56.67%) |
| proposal ambiguity | 19/30 (63.33%) | 19/30 (63.33%) | 19/30 (63.33%) |
| 추론 은닉 | 30/30 (100%) | 0/30 (0%) | 0/30 (0%) |
| 과도한 파편화 | 0/30 (0%) | 0/30 (0%) | 19/30 (63.33%) |
| human review record | 0 | 0 | 0 |
| 사람 간 불일치 | N/A (관측 0) | N/A (관측 0) | N/A (관측 0) |

Coverage·ambiguity·추론 은닉·파편화 값은 proposal에 기록된 자기평가를 집계한 값이므로 human-confirmed 측정값이 아니다. 특히 사람 판정이 0개라서 disagreement를 0%로 해석할 수 없다. 세 leakage-safe review packet은 granularity별 30개 항목으로 생성됐지만 각 manifest는 `packet_created_no_human_reviews`와 `reviews_included=0`을 명시한다. 따라서 `human_calibration_complete=false`, `semantic_confirmation_complete=false`, `evidence_complete=false`, `selection_ready=false`다.

구조적 결과만 보면 coarse는 모든 질문에서 reasoning을 숨기고 fine은 19개 질문에서 과도하게 파편화된다는 trade-off가 나타난다. 그러나 medium의 proposal coverage도 43.33%에 불과하고 실제 사람 검토가 없으므로, 이 비교만으로 medium 또는 다른 어휘를 선택할 수 없다. Coverage alone is not a sufficient selection criterion. 어떤 vocabulary도 선택·동결하지 않았고 resolved annotation, gold corpus, modeling readiness도 주장하지 않는다.

당시 exact task는 각 granularity마다 서로 다른 안정적 pseudonymous reviewer ID 두 개 이상으로 reviewer×granularity 입력 파일 6개와 총 180개 판정을 수집하는 것이었다. 이 task는 위 sequencing revision으로 철회되었다. 당시 comparator 입력 및 hash 계약을 재현하는 역사 설명으로만 보존한다.

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
