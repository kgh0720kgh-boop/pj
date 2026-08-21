# Pilot annotation report

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
