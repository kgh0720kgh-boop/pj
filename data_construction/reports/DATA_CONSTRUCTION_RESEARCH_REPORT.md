# Data Construction Research Report

보고일: 2026-08-21  
현재 활성 단계: Phase 0 historical-provenance recovery gate  
보조 scaffold 상태: Phase -1 continuity scaffold는 구현됐지만 Git/remote gate가 미완료이며, Phase 1 schema/operator/tool 계약은 provisional 상태로 선행 구현됨  
과학적 결정: `DATA_SOURCE_BLOCKED`  
동기화 상태: `REMOTE_NOT_CONFIGURED`

## 결과 요약

공식 HybridQA 질문·표·연결 문서 환경은 핀된 upstream commit과 artifact hash로 재획득할 수 있다. 계층형 주석 스키마, coarse/medium/fine 후보 어휘, 결정론적 split/검증/리뷰/통계 도구를 독립 디렉터리에 구축했다. 다만 Week 1–3 원본 산출물은 현재 없어 보존 여부 자체를 검증할 수 없다.

하지만 현재 폴더에는 canonical Git 이력과 다섯 역사 ID 파일이 없다. 공식 dev 3,466문항 중 어느 것이 과거 locked-eval에 노출되었는지 증명할 수 없으므로, 새 파일럿·train/dev/locked split과 실제 주석은 생성하지 않았다. 이 판단은 데이터 부족을 0건으로 바꾸지 않는 보수적 gate다.

## 계층 분리 계약

```text
Question
  -> Semantic Skeleton / Information Obligations
  -> Abstract Semantic Topology
  -> Environment-Aware Operator Topology
  -> Schema / Argument Grounding
  -> Grounded Executable Graph
  -> Execution / Trace
```

초기 층에는 gold answer/span, weak answer node, old graph/label, evaluator modality flag, oracle document ID와 구체 grounding을 노출하지 않는다. 실행 성공은 의미 계획 정답의 필요조건이나 충분조건으로 사용하지 않고, 대안 계획을 표현할 수 있게 한다.

## 연구 질문에 대한 현재 답

1. 안정적인 계층 표현으로 HybridQA를 주석할 수 있는가? **아직 판단 불가.** Schema는 기계 검증 가능한 후보이나 실제 파일럿 사람 검토와 annotation stability 근거가 없다.
2. 어떤 primitive granularity가 가장 좋은가? **아직 판단 불가.** 세 후보는 비교 가능하지만 coverage·길이·불일치·추론 은닉·파편화 측정이 실행되지 않았다.

## 수용 기준 현황

| 기준 | 상태 |
|---|---|
| 역사 Week 1–3 파일 보존 | UNVERIFIABLE/BLOCKED — 원본 5개와 기준 hash 부재 |
| 과거 노출 ID 명시 추적 | BLOCKED — 파일 부재를 명시한 manifest만 존재 |
| 새 역할 zero overlap | BLOCKED — 미배정 |
| 의미 skeleton/grounding 분리 | IMPLEMENTED_IN_SCHEMA_AND_STRUCTURAL_VALIDATOR; annotation instance 없음 |
| 정보 obligation 명시 | IMPLEMENTED_IN_SCHEMA |
| operator topology/grounding 분리 | IMPLEMENTED_IN_SCHEMA_AND_STRUCTURAL_VALIDATOR; annotation instance 없음 |
| grounded graph machine validation | NOT_MET/BLOCKED — IR v0.2 정의·validator 부재, reference envelope만 검증 가능 |
| 대안 계획 표현 | IMPLEMENTED_IN_SCHEMA |
| exact graph match 유일 정답 가정 제거 | PASS(contract) |
| granularity empirical pilot | NOT_RUN |
| 질문별 pseudo-operator 배제 | IMPLEMENTED_AS_VOCABULARY_CRITERION, evidence pending |
| LLM 제안 비-gold 상태 | PASS(contract) |
| 사람 검토 상태 진실성 | CONTRACT_AND_PACKET_READY; human review NOT_RUN |
| 계층 leakage 검사 | PARTIAL_STRUCTURAL_TESTS — 단계별 projection/금지 키/locked manifest 검사는 테스트, 자연어·실제 corpus audit는 NOT_RUN |
| source/document 재현 manifest | PASS |
| raw artifact 기반 corpus 통계 | NOT_RUN/NOT_MET — raw annotation/corpus 없음; 도구만 PARTIAL_TOOL_READY이며 외부 IR graph 길이는 IR v0.2 parser·artifact dereference 복구 전 N/A |
| locked evaluation tuning 차단 | PASS_BY_NON_ALLOCATION; membership/hash validator는 구현, 실제 split 검증은 NOT_RUN |
| negative/ambiguous 사례 보존 | SCHEMA_READY, evidence pending |
| 두 번째 디렉터리/PC 재현 | BLOCKED — Git remote/commit 없음 |

## Multi-device 수용 기준 현황 (§31.15)

| 기준 | 상태 |
|---|---|
| Desktop 1 절대경로 없이 두 번째 디렉터리로 clone | BLOCKED — 현재 폴더는 Git repository가 아니며 remote/commit이 없음 |
| `AGENTS.md`의 최신 portable 연구 지침 | PASS_LOCAL_ARTIFACT — 현재 지침은 존재하지만 아직 commit된 상태는 아님 |
| current phase/next task의 committed handoff 기록 | BLOCKED — 로컬 handoff에는 기록됐지만 commit할 Git repository가 없음 |
| Git branch와 expected HEAD 기록 | BLOCKED/UNAVAILABLE — branch는 `NOT_A_GIT_REPOSITORY`, HEAD는 `unknown` |
| machine-local secret의 version-control 제외 | UNVERIFIABLE — root secret scan에는 발견되지 않았지만 version-control 자체가 없어 tracked/staged 상태를 검증할 수 없음 |
| repository 파일로 Python/dependency 재현 | PARTIAL — `.python-version`과 exact-pin `requirements.txt`는 있으나 project-local `.venv` 재현은 미완료 |
| model/cache의 stable ID/revision 식별 | PASS_NOT_APPLICABLE_CURRENT_PHASE — 현재 단계에는 model이 필요하지 않으며 future model identity 정책만 정의됨 |
| 역사 Week 1–3 artifact 보호 | UNVERIFIABLE/BLOCKED — read-only 정책은 있으나 원본 5개가 부재하여 byte 보존을 검증할 수 없음 |
| preflight의 연구 실행 전 missing dependency 탐지 | PASS_LOCAL_CHECK — dependency mismatch와 선언된 readiness gate를 탐지하며 현재 결과는 ready가 아님 |
| 다른 machine 재개에 Git stash 불필요 | BLOCKED/UNVERIFIABLE — Git metadata와 stash 상태가 없고, 현재 산출물을 전달할 commit/remote도 없음 |
| consumer folder sync 비의존 | PASS_POLICY/NO_EVIDENCE_OF_DEPENDENCE — active worktree 조정에 사용하지 않는 정책이며 현재 의존 증거가 없음 |
| local-only commit과 remote sync의 handoff 상태 구분 | PASS_CONTRACT — 명시적 synchronization-state vocabulary가 있고 현재는 `REMOTE_NOT_CONFIGURED` |
| 이전 chat 없이 Desktop 2에서 지침을 읽고 next task 재구성 | PARTIAL_LOCAL_ARTIFACTS/BLOCKED_TRANSFER — 지침은 self-contained이지만 전달할 clone/commit/remote가 없음 |

## 차단 해제 순서

1. canonical 저장소/원격을 복구하거나 preservation-first 신규 Git migration을 연구자가 승인한다.
2. 다섯 역사 파일을 권위 있는 commit/backup에서 복구하고 byte hash를 기록한다. Backup/store 복구본은 연구자 승인 preservation-first Git migration으로 변경 없이 commit한 뒤 full OID를 v0.1 provenance authority로 사용한다.
3. 과거 노출 manifest를 complete로 재생성한다.
4. 권위 있는 역사 IR v0.2 schema와 operator registry를 byte-preserving 방식으로 복구하고, 원래 계약을 사용하는 external parser/validator 및 graph-artifact dereference를 연결한다. 편의상 IR을 재정의하지 않는다.
5. 결정론적으로 30문항 파일럿을 배정하고 세 granularity를 같은 질문에서 비교한다.
6. 결정론 검사와 실제 사람 검토를 수행한 뒤 schema/operator version을 동결 또는 v0.2로 개정한다.
7. 역사 노출 격리와 실제 IR validation이 모두 연결된 이후에만 150–200문항 corpus와 locked evaluation을 고정하거나 modeling-ready 상태를 주장한다.

## 최종 상태

`DATA_SOURCE_BLOCKED`는 공식 HybridQA 원본 부재가 아니라 **과거 노출/locked 역할 증거 부재**를 뜻한다. 프로젝트 동기화 상태는 Git 저장소/remote가 없으므로 `REMOTE_NOT_CONFIGURED`이다.

스키마 번들은 `requirements.txt`의 exact pins를 저장소 밖 임시 경로에 설치한 CPython 3.10 환경에서 Draft 2020-12 meta-validation과 3개 vocabulary instance validation을 오류 0개로 통과했다. 결정론 도구 회귀 테스트는 26/26 통과했다. 이는 실제 annotation/corpus instance, 사람 검토, 또는 의미 정답을 검증했다는 뜻이 아니다. 재현 가능한 프로젝트 `.venv`는 이 머신의 `python3-venv` 부재로 아직 만들지 못했다.
