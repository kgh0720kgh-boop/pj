# Data Construction Research Report

## 2026-08-24 scale-first N=100 result

활성 연구 순서는 question-only AI semantic-backbone의 누적 규모 탐색으로 바뀌었다. 보존된 v0.1 human-first lane은 삭제·완료된 것이 아니라 deferred 상태이고 human evidence는 계속 0건이다. 현재 결정은 `UNDECIDED_NEEDS_SCALE_EVIDENCE`이며, N=100→300→조건부 1,000에서 반복 구조와 희귀화 곡선을 확인한 뒤 후보 backbone/조합 규칙과 대표 환경 실현으로 이동한다.

동결된 N=100 run은 100/100 structurally valid, `ai_exploratory_non_human_non_gold` record를 만들었다. Deterministic signature 기준 fine labeled family 23개, same-role-contracted family 17개, topology shape 6개, task signature 38개다. Contracted singleton mass는 0.09, top-10 coverage는 0.93, first-30→new-70 transfer는 50/70이며 uncertainty는 29/100, `OTHER` 사용은 0/100이다. 사전 선언 rule의 판정은 `EXPAND_UNCHANGED_TO_N300`이다.

별도 post-hoc sensitivity audit는 이 판정의 해석 한계를 보존한다. Trigger를 만든 반복 신규 contracted family 5개는 모두 single producer partition 안에서만 반복되어 cross-partition support가 0이다. Raw dependency branch/join 5/6도 transitive reduction 뒤 0/1이 되고, same-role contraction은 dominant family를 46개에서 62개로 키운다. 따라서 N=300은 보수적 다음 측정이지만, N=100이 새 의미 family 5개를 확정했다는 결론은 내리지 않는다. Fine/contracted/partition sensitivity를 항상 함께 보고한다.

정확한 다음 작업은 기존 100개를 exact prefix로 유지한 cumulative N=300 selection, question-only pool, exposure manifest, producer-routing plan을 새 version으로 먼저 동결하고 신규 200개를 같은 prompt/schema/role/normalizer로 처리하는 것이다. 신규 committed position은 producer context에 분산해 질문 순서와 한 작업자 context가 공선이 되지 않게 한다. 이 단계는 answer, environment realization, grounding, execution, semantic correctness, human agreement, gold 또는 modeling readiness를 평가하지 않는다.

## 2026-08-23 question-first sequencing decision

핵심 연구 대상을 다시 분리했다. 먼저 질문 문장만으로 semantic obligation과 environment-independent topology를 open-code하고, 별도 blinded alignment/freeze와 held-out confirmation으로 구조 안정성을 확인한다. 그 다음에만 환경 capability를 반영한 operator topology granularity를 비교하고, 마지막에 대표 사례 grounding과 execution을 별도 signal로 평가한다.

기존 30 model-assisted record/90 coarse-medium-fine representation/90 deterministic check/3 HTML packet/v0.1 metric은 byte-preserved Phase B feasibility evidence다. 삭제하거나 결과를 무효화하지 않지만, proposal/self-assessment anchoring 때문에 기존 packet은 현재 Phase A 또는 미래 blinded Phase B human UI로 승인되지 않았다. 이전 six reviewer-by-granularity file/180-decision task는 철회됐다.

현재 A0 raw instrument, 30개 question-only view, 첫 10문항 packet은 commit·packet-only 검증됐다. Instrument는 opaque question ID와 question text만 보여 주고 answer request, candidate structure, required information unit, dependency를 free text로 받는다. Closed semantic/operator enum은 없지만 scaffold 자체가 시험할 structural hypothesis다. 이제 연구자 승인·상호 독립·무노출 실제 사람 2명이 첫 committed-order 10문항을 각각 open-code해 2파일/20 raw record를 만든다. Q1 대화는 protocol analysis이고 human evidence는 0이다. Later-layer exposure가 있는 사람은 영향받은 exposure-naive work에서 제외한다. Identity, independence, approval, exposure attestation은 procedural/manual이고 machine-authenticated가 아니다.

Raw schema/hash/leakage validity는 observation integrity일 뿐 semantic agreement가 아니다. 두 raw set 뒤 blinded alignment/adjudication artifact와 deterministic comparator를 별도 version으로 만들고 결과를 보기 전에 freeze해야 한다. Held-out confirmation을 통과한 뒤 Phase B는 A2-derived six-stratum taxonomy와 exact manifest를 먼저 commit하고 12×3×2=72 decisions로 시작한다. Precommitted disagreement/tie/new-reusable-gap trigger에 따라 90, 최대 108까지 확장한다. Exact IDs는 A2 normalization 전에 배정하지 않는다. Phase C representatives도 Phase B 결과와 무관하게 stratum별 한 개씩 사전 고정한다.

같은 reviewer와 scaffold가 skeleton→obligation→topology 연결을 직접 작성하므로 이 raw triple은 `elicited_linked_representation`, 즉 representability·instrument-operability evidence일 뿐 질문 구조가 graph 구조를 예측한다는 독립 증거가 아니다. 그런 cross-level claim이나 Phase B normalization 전에 upstream mapping을 보지 않는 별도 versioned/frozen topology pass와 held-out 평가가 필요하다. 또한 현재 한-file stage transition은 정상 UI/attestation 기반이지 source·DOM inspection에 맞선 server-enforced blinding이 아니고, forbidden-key validator는 허용 free-text의 의미 contamination을 탐지하지 못한다.

결정은 계속 `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`다. 어떤 semantic instrument나 operator vocabulary도 empirically frozen, gold, modeling-ready로 선언하지 않는다. 현재 bundle은 11 schemas와 3 candidate vocabularies이고, 최신 exact-pin 및 regression 결과는 handoff를 따른다.

## 2026-08-23 이전 Phase 2 실행 결과 addendum — 보존된 snapshot

당시 활성 단계는 operator-granularity annotation pilot이었고 보존된 artifact의 study 상태는 `structural_integrity_complete_human_calibration_pending`이다. 잠정 결정은 `UNDECIDED_NEEDS_ANNOTATION_EVIDENCE`이며, 최종 modeling decision이나 modeling-ready 선언이 아니다.

### 이번 단계에서 완료한 항목

- 연구자 승인 provenance의 Week 1–3 파일 5개와 100개 역사 노출 ID/15개 역사 locked-eval ID에 대한 strict audit는 계속 complete이고 오류는 0개다.
- 핀된 공식 HybridQA dev source에서 역사 노출과 겹치지 않는 30개 `annotation_schema_pilot` 질문을 유지했다. 새 train/dev/locked 역할은 모두 0개다.
- 질문과 table/document 환경의 허용된 schema/capability만 담고 answer, row/cell value, document text/ID, trace, grounding을 배제한 operator input view 30개를 생성했다.
- 같은 30문항에 coarse/medium/fine 표현을 각각 하나씩 생성해 30 records/90 representations를 보존했다. 상태는 model-assisted `llm_proposed`이며 exact model revision과 raw model output이 인터페이스에서 노출되지 않았다는 provenance 한계를 명시했다.
- 90개 representation의 Draft 2020-12, DAG, operator-vocabulary, source/view/artifact hash 결속 검사가 모두 통과했다. Deterministic check 결과는 90 pass, 0 error, 0 warning이다.
- 세 granularity review packet을 각각 30항목으로 만들었다. Packet은 review UI와 hash contract일 뿐 사람 검토를 생성하지 않았으며 manifest의 review count는 모두 0이다.
- 프로젝트 로컬 exact-pin 환경에서 현재 9개 schema와 3개 vocabulary 검증이 통과했고 write-once output 보호를 포함한 표준 테스트는 `51/51` 통과했다.
- 역사 IR v0.2 10-file quarantine과 adapter baseline은 계속 50 records/520 nodes, parse/schema/v0.2 validator errors 0, 역사적 `DEAD_NODE` warnings 455로 보존된다. 이는 현재 granularity 우수성 증거가 아니다.

### Proposal-level 비교 결과

| 지표 | Coarse | Medium | Fine |
|---|---:|---:|---:|
| representation | 30 | 30 | 30 |
| coverage | 14/30 (46.67%) | 13/30 (43.33%) | 13/30 (43.33%) |
| graph 길이 평균 / 중앙값 / 범위 | 2.57 / 3 / 2–3 | 4.83 / 5 / 4–8 | 6.87 / 7 / 6–9 |
| 평균 고유 연산자 수 | 2.57 | 4.60 | 6.70 |
| 새 연산자 필요 | 16/30 (53.33%) | 17/30 (56.67%) | 17/30 (56.67%) |
| ambiguity | 19/30 (63.33%) | 19/30 (63.33%) | 19/30 (63.33%) |
| hidden reasoning | 30/30 (100%) | 0/30 (0%) | 0/30 (0%) |
| excessive fragmentation | 0/30 (0%) | 0/30 (0%) | 19/30 (63.33%) |
| human review record | 0 | 0 | 0 |
| human disagreement | N/A (관측 0) | N/A (관측 0) | N/A (관측 0) |

위 coverage·ambiguity·hidden reasoning·fragmentation은 proposal 자기평가의 집계이며 사람 확인값이 아니다. 구조적 결과는 coarse의 reasoning 은닉과 fine의 파편화 trade-off를 보여 주지만, medium의 coverage도 43.33%이고 새 연산자 필요율도 56.67%다. Coverage alone is not a sufficient selection criterion. 사람 검토 없이 이 표만으로 어휘를 선택할 수 없다.

### 현재 수용 기준과 연구 해석

| 기준 | 2026-08-23 상태 |
|---|---|
| 역사 Week 1–3 파일 보존 | PASS — 5 files, byte-for-byte preservation commit |
| 과거 노출 ID 명시 추적 | PASS — exposed 100, historical locked 15, strict errors 0 |
| Pilot 역할 source/history 비중복 | PASS — 30 questions, deterministic, no override |
| 새 train/dev/locked 분할 | NOT_ALLOCATED — 모두 0 |
| 프로젝트 로컬 schema/vocabulary 재현 | PASS — 9 schemas/3 vocabularies |
| IR v0.2 원본 보존/validator 연결 | PASS — 10-file quarantine; 50 records/520 nodes, errors 0, `DEAD_NODE` warnings 455 |
| coarse/medium/fine proposal 생성 | COMPLETE — 30 records/90 representations, `llm_proposed` |
| deterministic representation validation | PASS — 90/90, errors 0, warnings 0 |
| human calibration | PENDING — 0 review records, disagreement N/A |
| semantic confirmation / evidence complete | FALSE / FALSE |
| vocabulary selection | NOT_SELECTED |
| resolved annotation/corpus | NOT_CREATED/NOT_BUILT |
| factorized modeling readiness | NOT_CLAIMED |

두 핵심 연구 질문은 아직 최종 답을 낼 수 없다. Leakage-safe 계층 표현 후보를 30문항에서 구조적으로 생성하고 검증할 수 있음은 확인했지만, 의미 정답성과 주석 안정성은 확인하지 못했다. 어떤 primitive granularity가 가장 좋은지도 human calibration 전에는 판단하지 않는다. 따라서 어떤 vocabulary도 선택·동결하지 않고, `llm_proposed`를 gold로 승격하지 않으며, corpus/modeling readiness를 주장하지 않는다. Comparator의 상태는 `human_calibration_complete=false`, `semantic_confirmation_complete=false`, `evidence_complete=false`, `selection_ready=false`다.

당시 exact task는 granularity마다 서로 다른 안정적 pseudonymous reviewer ID 두 개 이상으로 reviewer×granularity 파일 6개와 총 180개 판정을 수집하는 것이었다. 이 task는 위 question-first sequencing 결정으로 철회됐으며, 아래 수치와 해석은 당시 v0.1 snapshot으로만 보존한다.

아래는 2026-08-21 당시의 감사·설계 snapshot이다. 당시의 부재/차단 주장은 그 시점의 증거를 보존하기 위해 유지하며, 현재 상태 판단에는 위 addendum을 우선한다.

## 2026-08-21 역사적 snapshot

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
