# Pilot annotation report

## 2026-08-23 현재 상태 addendum

현재 in-progress 상태: `DATA_SOURCE_READY_FOR_ANNOTATION_PILOT`

역사 노출 gate가 해제되어 핀된 공식 HybridQA dev 원본에서 30개 질문을 `annotation_schema_pilot` 역할로 결정론적으로 배정했다. `split_manifest_v0_1.json`은 source hash/ID inventory를 검증했고, `release_eligible=true`, `override_used=false`, `zero_overlap_verified=true`다. Pilot 질문 view에는 answer, answer-node/trace, oracle document ID 등 question-only 단계의 금지 필드가 없다. 새 `annotation_train`, `annotation_dev`, `locked_eval` 역할은 각각 0개다.

| 단계 | 현재 상태 | 건수 |
|---|---|---:|
| 질문 역할 배정 및 source/history 비중복 검사 | complete | 30 |
| coarse/medium/fine representation | not_run | 0 |
| LLM 제안 | not_run | 0 |
| annotation deterministic checks | not_run | 0 |
| 사람 단일/이중 검토 | not_run | 0 |
| adjudication | not_run | 0 |
| resolved annotation | not_run | 0 |

역사 파일 5개는 researcher-approved workspace에서 byte-for-byte 복구되어 commit `1995c0cf79ab8e987773041d456d4a1b8df19793`에 보존됐다. Verified provenance를 사용한 strict manifest 결과는 노출 고유 ID 100개, 역사 locked-eval 15개, 오류 0개다. IR v0.2 원본 10개와 condition C graph 50개도 commit `dcc5ac5c14e9acb5c689b400a4046708b6837ac3`의 read-only quarantine에 보존했다. Current-side adapter baseline은 50 records/520 nodes를 parse/schema/v0.2 validator 오류 0개로 검증했고, 알려진 역사 실패 신호인 `DEAD_NODE` 경고 455개를 재현했다.

프로젝트 로컬 exact-pin `.venv`는 8개 schema/3개 vocabulary 검증을 통과했고, IR adapter hardening과 live annotation-reference bridge를 포함한 최종 pinned suite는 `43/43` 통과했다. 이 결과와 질문 배정은 annotation 완료나 modeling readiness를 뜻하지 않는다.

다음 exact task는 동일한 30문항에 leakage-safe coarse/medium/fine 표현을 작성하고 각 표현에 결정론 검사를 실행한 뒤, 결과를 보존해 human calibration을 수행하는 것이다.

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
