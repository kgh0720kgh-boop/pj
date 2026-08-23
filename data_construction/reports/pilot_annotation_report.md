# Pilot annotation report

## 2026-08-23 Phase 2 실행 결과 addendum

현재 study 상태: `structural_integrity_complete_human_calibration_pending`

잠정 결정: `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`

역사 노출과 비중복인 고정 30문항에 대해 leakage-safe operator input view와 coarse/medium/fine 후보 표현을 만들었다. 생성 record 30개에는 질문당 세 표현, 총 90개 representation이 들어 있으며 provenance 상태는 `llm_proposed`다. Exact model revision과 raw model output은 인터페이스에서 제공되지 않았다고 명시했으므로, 재현 가능한 구조화 proposal artifact는 보존했지만 이를 human annotation으로 승격하지 않는다.

| 단계 | 현재 상태 | 건수 |
|---|---|---:|
| 질문 역할 배정 및 source/history 비중복 검사 | complete | 30 questions |
| leakage-safe operator input view | complete | 30 views |
| model-assisted coarse/medium/fine proposal | complete, `llm_proposed` | 30 records / 90 representations |
| deterministic representation checks | complete | 90 pass, 0 error, 0 warning |
| granularity별 review packet | packet only | 3 packets / 90 review items |
| 실제 human review | pending | 0 records |
| adjudication | pending | 0 |
| resolved annotation | not_created | 0 |

Comparator가 집계한 proposal-level 결과는 coarse/medium/fine coverage가 각각 14/30(46.67%), 13/30(43.33%), 13/30(43.33%)이고 평균 graph 길이는 2.57, 4.83, 6.87이다. 새 연산자가 필요하다고 표시된 질문은 각각 16, 17, 17개다. 세 granularity 모두 ambiguity 19/30을 기록했다. Coarse는 hidden reasoning 30/30, fine은 excessive fragmentation 19/30이고 medium은 두 항목 모두 0/30이다. 이 값은 아직 사람이 확인하지 않은 proposal 자기평가다.

Human review record는 세 granularity 모두 0개이고 disagreement observation도 0개다. 따라서 사람 간 불일치는 `N/A`이며 0% 합의 또는 0% 불일치로 보고하지 않는다. Review packet manifest 세 개 모두 `packet_created_no_human_reviews`, `reviews_included=0`, `human_reviews_created_by_builder=false`를 기록한다. Comparator 결과도 `human_calibration_complete=false`, `semantic_confirmation_complete=false`, `evidence_complete=false`, `selection_ready=false`다.

프로젝트 로컬 exact-pin 환경에서 현재 9개 schema와 3개 vocabulary 검증이 통과했고 write-once output 보호를 포함한 표준 테스트는 `51/51` 통과했다. 그러나 어떤 vocabulary도 선택하거나 동결하지 않았고 proposal을 gold로 바꾸지 않았으며, resolved corpus나 modeling readiness도 없다.

다음 exact task는 granularity마다 서로 다른 두 reviewer ID로 30개 항목을 독립 검토해 reviewer×granularity 파일 6개와 총 180개 판정을 수집하는 것이다. 다섯 실질 평가 필드를 모두 채우고 대상 representation 및 packet payload hash를 검증한 뒤 reject, `accept_with_edits`, 실질 평가 불일치를 adjudicate해야 한다. Reviewer 인증은 절차적으로 확인해야 하며 기계적으로 검증됐다고 주장하지 않는다.

아래는 gate 해제 전인 2026-08-21의 역사적 상태 기록이다.

## 2026-08-21 역사적 snapshot

상태: `PLANNED_NOT_RUN — FRESHNESS_NOT_VERIFIABLE`

## 요약

공식 HybridQA dev 3,466문항과 각 질문의 table/request 환경은 소스 감사에서 사용 가능함을 확인했다. 그러나 요구된 다섯 Week 1–3 역사 파일이 없어 이전 노출/locked-eval ID와의 비중복을 증명할 수 없다. 이 상태에서 schema tuning용 30문항을 고르면 과거 locked-eval을 재사용할 위험이 있으므로 파일럿을 시작하지 않았다.

| 단계 | 상태 | 건수 |
|---|---|---:|
| 질문 역할 배정 | blocked | N/A |
| LLM 제안 | planned_not_run | N/A |
| 결정론 검사 | planned_not_run | N/A |
| 사람 단일 검토 | unavailable/not_requested | N/A |
| 사람 이중 검토 | unavailable/not_requested | N/A |
| adjudication | planned_not_run | N/A |
| resolved annotation | planned_not_run | N/A |

건수 `N/A`는 실제 0건 corpus라는 뜻이 아니다. LLM 또는 사람 검토를 수행했다고 주장하지 않는다.

## 구현된 안전장치

- 과거 감사가 incomplete이면 `build_sample.py` 기본 실행 거부
- explicit diagnostic override 결과는 `release_eligible=false`
- question-only 샘플에는 answer, weak answer node, document locator, evaluator label 미복사
- 계층 누출, 연산자 registry, DAG cycle/missing dependency, grounding 참조, 허위 gold 상태 결정론 검사
- 질문/연산자/grounding 단계별 가시성 제한 리뷰 패킷과 dependency graph 시각화

## 해제 조건과 다음 실행

1. 권위 있는 Git 이력 또는 원래 연구 PC/백업에서 다섯 역사 파일을 byte-preserving 방식으로 복구한다. 백업/store 출처라면 연구자 승인 preservation-first Git migration으로 bytes를 변경 없이 commit하고 full commit OID를 권위로 기록한다.
2. 연구자 승인 provenance receipt를 지정해 `build_historical_manifest.py --recovery-provenance state/historical_recovery_provenance_v0_1.json --overwrite --strict`로 현재 incomplete audit의 ID 합집합과 locked 역할을 재생성한다. Complete/released manifest는 덮어쓰지 않고 새 versioned path를 쓴다.
3. 해시를 검토한 뒤 `build_sample.py --pilot-count 30`을 override 없이 실행한다.
4. 동일 질문에 coarse/medium/fine 제안을 만들고 결정론 검사를 실행한다.
5. 가능한 경우 calibration subset을 두 사람이 검토하고 원본 판정을 보존한다.

현재 annotation status: `not_created`; 이를 `llm_proposed`나 `gold`로 해석하지 않는다.
