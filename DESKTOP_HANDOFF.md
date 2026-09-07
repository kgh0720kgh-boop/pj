# 다른 데스크탑에서 이어받기

작성일: 2026-09-07. 대상 저장소: `https://github.com/kgh0720kgh-boop/pj.git`, 브랜치: `main`.

이 파일은 연구를 관리하는 사용자/주 작업자용이다. 격리 검사 대상 작성자에게
이 문서, AGENTS의 연구 요약, 이전 결과를 입력으로 전달하지 않는다.
현재 상태의 최종 권위는 [HANDOFF_CURRENT.md](HANDOFF_CURRENT.md)와
[state/project_state.json](state/project_state.json)이다. 과거 문서의 “다음 작업”보다 우선한다.

## 1. 기존 저장소 업데이트

다른 데스크탑의 WSL 터미널에서 해당 저장소로 이동한 뒤 실행한다.
절대 경로는 기기마다 달라도 되며 `.venv`나 작업 폴더를 복사하지 않는다.

```sh
git rev-parse --show-toplevel
git status --short --branch
git branch --show-current
git remote -v
```

수정·미추적 파일이 있으면 여기서 멈추고 `STOP_AND_REPORT_LOCAL_CHANGES`로 보고한다.
자동 stash, reset, checkout으로 작업을 버리지 않는다. 원격 URL이 다르면 먼저 확인한다.
깨끗한 저장소에서 아래 명령을 차례로 실행하고, 하나라도 실패하면 다음으로 넘어가지 않는다.

```sh
git fetch origin --prune
git switch main
git rev-list --left-right --count HEAD...origin/main
```

왼쪽 숫자가 0이어야 한다. 왼쪽이 양수면 다른 데스크탑만의 커밋이 있으므로
합치거나 push하지 말고 먼저 보고한다. 왼쪽 0일 때만 다음을 실행한다.

```sh
git merge --ff-only origin/main
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

두 커밋 값이 같고 작업 트리가 깨끗하면 현재 원격을 받아온 것이다.
이 인수인계의 연구 완료 기준 커밋은 `67a70f9c206bfcf23c7c35512d08235d22143338`이며,
동기화용 문서 커밋은 그 뒤에 붙는다. 기준으로 reset하거나 detached checkout하지 않는다.

저장소가 아예 없으면 상위 작업 폴더에서 일반 clone을 사용한다.
동결 시점 검증에 과거 커밋이 필요하므로 shallow clone은 사용하지 않는다.

```sh
git clone https://github.com/kgh0720kgh-boop/pj.git
cd pj
```

## 2. 환경 복원과 점검

루트의 `AGENTS.md`, `HANDOFF_CURRENT.md`, `state/project_state.json`,
`ENVIRONMENT.md`, reset prompt, source audit, versioned manifests를 읽는다.
AGENTS/ENVIRONMENT의 과거 단계 요약이 최신 handoff와 다르면 handoff를 따른다.
Python 기준은 `.python-version`의 3.10.12이고 의존성은 `requirements.txt`의 exact pin이다.
이 기기에 프로젝트 환경이 없을 때만 새로 만든다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --requirement requirements.txt
```

OS의 venv 지원이 없으면 `ENVIRONMENT.md`를 확인한다. 자격 증명과 `.venv`,
공식 원본/모델 캐시는 Git으로 전달하지 않는다. 원본이 필요한 검사가 막히면
`data_construction/manifests/source_manifest_v0_1.json`의 고정 버전 재취득 절차를 따른다.
빈 결과 파일을 만들어 검사를 통과시키거나 과거 연구를 다시 실행하지 않는다.

```sh
sh scripts/cross_device_preflight.sh
.venv/bin/python -B data_construction/tools/freeze_grounding_input_isolation_v0_2.py --validate-only --require-output-absence
```

이 인수인계 기준: 236 tests 통과, core JSON/JSONL 161개, validation failure 0건.
전체 연구 준비 상태는 `NOT_READY`/exit 2가 맞다. 남은 연구 gate는
`QUESTION_FREE_ISOLATION_TRANSPORT_NOT_VERIFIED`이며, Git 동기화 실패를 뜻하지 않는다.
환경·해시·분기·테스트 관련 새로운 실패가 생기면 먼저 해결하거나 명시적으로 보고한다.

## 3. 완료한 것과 아직 하지 않은 것

- 입력 격리 설계 v0.2 구현: `80b74fbc4e727d09265945946e64fc746673e621`.
- 새 probe/grounding 출력이 없는 상태의 동결: `467fc8586321b8e8f3437d59edeec67ab7a26d2e`.
- 입력 경로 9종, host 전달 증거와 작성자 노출 신고의 분리, 합성 control 3종,
  실패/확인 불가/미완료 분기, 회귀검사 10개를 정했다.
- 실제 채널 검사·새 작성자 호출은 0회다. 설계 검증 성공을 실제 격리 성공으로 해석하지 않는다.
- 이전 grounding v0.1은 6/6 context가 이전 연구 정보 노출을 신고하여 실패했다.
  승인 grounding record는 0/14다. 원래 raw와 결과 20개는 수정 없이 보존한다.
- 새 grounding, 실행, 정답 복원, human evidence, gold 지정은 하지 않았다.

## 4. 정확한 다음 작업

판단 근거는 [sequencing decision v0.13](data_construction/reports/research_sequencing_decision_v0_13.md),
계약은 `data_construction/exploration/ai_question_structure_scale_v0_1/contracts/`의
`grounding_input_isolation_design_v0_2.json`과 `grounding_input_isolation_freeze_v0_2.json`이다.

1. 허용된 전달 채널이 실제 초기 입력에 대한 host 측 증거를 제공하는지 읽기 전용으로 확인한다.
2. 충분하면 offline adapter, 닫힌 receipt schema, 검증기, 합성 unit test를 구현한다.
3. 구현을 커밋하고, 문항 없는 정확한 probe plan/runtime/output 계약을 별도 동결한다.
   이 동결 전에는 모델을 호출하지 않는다.
4. 증거가 부족하면 `BLOCKED_UNVERIFIABLE_CONTEXT`와 부족한 증거/권한을 보고한다.
   “새 세션”, `fork_context=false`, 작성자의 깨끗하다는 자기 신고만으로 통과시키지 않는다.

실제 연구 문항, 새 API 연동·유료 호출·자격 증명 설정·플랫폼 설정 변경은 이 인수인계가
허용하지 않는다. 향후 합성 검사가 통과해도 연구 작성에는 별도 grounding 계획이 필요하다.
historical/IR, 노출 ledger, split, 기존 schema/runtime/raw를 수정하지 않는다.
새 질문이나 locked-eval ID를 사용하지 않는다. 이 문서의 전달은 동시 작업 승인이 아니다.

## 5. 다음 작업자에게 전달할 요청

> DESKTOP_HANDOFF.md와 HANDOFF_CURRENT.md, state/project_state.json을 읽고
> 현재 저장소·브랜치·원격·로컬 변경과 preflight를 확인해줘.
> 이전 결과와 동결 계약을 보존하면서, 정확한 다음 작업인 question-free
> input-isolation transport의 host 증거 확인부터 진행해줘.
> 새 연구 작성이나 모델 호출은 하지 말고, 증거가 충분하면 offline 구현과
> 별도 probe 계획 동결을 준비해줘. 부족하면 부족한 증거와 필요한 권한을 보고해줘.

작업을 마치면 handoff/state를 갱신하고 의도한 파일만 커밋한다.
다음 기기로 넘기기 전 push를 명시적으로 요청받아 수행하고 원격과 HEAD 일치를 확인한다.
OneDrive/Dropbox 등의 폴더 동기화로 활성 Git 작업 트리를 공유하지 않는다.
