# HybridQA 데이터 소스 감사 v0.1

감사 시각: 2026-08-21T12:50:32+09:00  
범위: 공식 HybridQA 질문 데이터, 공식 연결 테이블/문서 환경, Week 1–3 지정 ID 파일의 정확 경로 확인 및 사용 가능한 홈 영역의 깊이 제한 검색

## 결론

공식 원본 자체는 사용할 수 있다. 저자 공식 저장소의 질문 데이터와 연결 테이블/문서 환경을 각각 변경 불가능한 Git 커밋으로 핀했고, 작업공간 밖 machine-local 캐시에 완전히 체크아웃하여 해시·JSON 파싱·질문-환경 참조를 검증했다. 공식 dev에는 답이 있는 질문 3,466개가 있으므로 요청된 150–200개 규모를 공급할 물리적 용량은 충분하다.

그러나 **새 질문이 Week 1–3 노출 ID와 비중복이라는 사실은 현재 증명할 수 없다.** 지정된 과거 파일 5개가 현재 프로젝트 루트와 리셋 프롬프트가 지칭한 과거 Desktop 1 위치 모두에 없었다. 따라서 현 상태는 다음과 같다.

- `SOURCE_RETRIEVAL = AVAILABLE`
- `HISTORICAL_DISJOINTNESS = BLOCKED`
- `RELEASEABLE_NEW_SPLIT = BLOCKED`

빈 과거-ID 배열은 “과거 노출 0개”가 아니라 “ID 미복구”를 뜻한다. 진단용 30문항 파일은 명시적 override로 만들 수 있어도, 연구용 pilot/train/dev/locked-eval 분할로 동결해서는 안 된다.

기계 판독 결과는 [source_manifest_v0_1.json](../manifests/source_manifest_v0_1.json)과 [historical_exposed_ids.json](../manifests/historical_exposed_ids.json)에 있다.

## 공식 1차 출처와 핀

출처의 공식성은 저자 프로젝트 페이지가 코드와 데이터를 저자 GitHub로 연결하고, 논문이 같은 저장소를 데이터 URL로 제시한다는 점으로 확인했다.

| 자료 | 공식 출처 | 핀한 커밋 | 관찰한 브랜치 | 태그 |
|---|---|---|---|---|
| 질문, 정답, weak trace, 평가 코드 | [wenhuchen/HybridQA](https://github.com/wenhuchen/HybridQA) | [`db22fda8c5951438fade3c69d75b350335ba93b3`](https://github.com/wenhuchen/HybridQA/commit/db22fda8c5951438fade3c69d75b350335ba93b3) | `master` | 없음 |
| 토큰화 테이블, 하이퍼링크 passage | [wenhuchen/WikiTables-WithLinks](https://github.com/wenhuchen/WikiTables-WithLinks) | [`dc066e1a6d5281511d8b73a6107d5ad2824cc2b2`](https://github.com/wenhuchen/WikiTables-WithLinks/commit/dc066e1a6d5281511d8b73a6107d5ad2824cc2b2) | `master` | 없음 |

논문 식별자는 [ACL Anthology 2020.findings-emnlp.91](https://aclanthology.org/2020.findings-emnlp.91/), DOI는 `10.18653/v1/2020.findings-emnlp.91`이다. [공식 프로젝트 페이지](https://hybridqa.github.io/)는 질문이 Wikipedia 표와 연결 passage를 함께 사용한다고 설명하고 데이터 라이선스를 CC BY 4.0으로 표시한다.

공식 README가 제공하는 S3 `preprocessed_data.zip`과 모델 압축 파일은 이번 감사에서 받지 않았다. 계층 주석의 원본은 Git으로 정확히 핀할 수 있는 `released_data`, `tables_tok`, `request_tok`이며, 파생 전처리/모델 파일은 필요하지 않다.

## 확보 및 무결성 결과

원본은 저장소 안에 복사하지 않았다. 두 체크아웃의 관찰 크기는 약 99 MB와 764 MB이며, 위치는 다음 portable locator로만 기록한다.

```text
<machine-local-cache>/pj1-hybridqa-source-audit/
  HybridQA-db22fda/
  WikiTables-WithLinks-dc066e1/
```

재획득 및 검증은 [fetch_official_hybridqa_sources.sh](../tools/fetch_official_hybridqa_sources.sh)가 수행한다. 이 스크립트는 기존 비-Git 디렉터리나 변경된 체크아웃을 덮어쓰지 않으며, 커밋·Git tree·핵심 파일 SHA-256·연결 환경 전체의 canonical content-list SHA-256을 확인한다.

### 질문 파일

| split | 레코드 | 고유 question ID | 고유 table ID | `answer-text` | SHA-256 |
|---|---:|---:|---:|---|---|
| train | 62,682 | 62,682 | 12,374 | 있음 | `b33aa73638959a2383e1e1638fd6abe87818b7379c7a42eac1621475d2d959e2` |
| dev | 3,466 | 3,466 | 3,053 | 있음 | `424272b233735a70ed8ef5af4a615373d114f472168c686c4370d54c92d58ac1` |
| test | 3,463 | 3,463 | 3,061 | 없음 | `41845fec9cba21979e663a96626c2880adbf2d26b5667ea7d0bf61fab0cdc356` |

세 split의 question ID 교집합은 모두 0이고, 합계 69,611개가 모두 고유하다. 반면 table ID는 split 사이에 겹친다: train–dev 3,050개, train–test 3,059개, dev–test 718개다. 이후 실험이 question-disjoint뿐 아니라 table-disjoint 일반화를 주장하려면 별도 분할 정책과 통계를 사용해야 한다.

### 연결 환경

| 검사 | 결과 |
|---|---:|
| `tables_tok/*.json` | 15,316개, 전부 JSON 파싱 성공 |
| `request_tok/*.json` | 15,316개, 전부 JSON 파싱 성공 |
| 두 디렉터리의 파일 stem 집합 차이 | 0 |
| 질문 전체가 참조하는 고유 table ID | 12,378 |
| 질문 table ID 중 table 파일 누락 | 0 |
| 질문 table ID 중 request 파일 누락 | 0 |
| 표 데이터 행 | 241,435 |
| header 포함 cell | 1,150,426 |
| cell 내 하이퍼링크 출현 | 679,119 |
| request passage 엔트리 | 512,737 |
| 대응 request 파일에 없는 하이퍼링크 출현 | 0 |

`tables_tok`과 `request_tok`의 canonical content-list SHA-256은 각각 다음과 같다.

```text
tables_tok   3969fcf6c0192d6085ad999e3abd41f0039a73c878ffd30d7cd8b7786ea62c92
request_tok  bc289b9aa6d397369b44cbf9b54250539a5a0cf01287f94c9a5572e79e8cd916
```

해시 직렬화 정의와 개별 핵심 파일 해시는 source manifest에 기록했다.

소스 안의 ID도 별도로 canonical set hash로 고정했다. 핀된 원본에는 question ID 69,611개, 질문이 참조하는 table ID 12,378개, 사용 가능한 table 파일 ID 15,316개, `request_tok`의 고유 linked-document ID 286,270개가 있다. 정확한 값은 각각 원본 JSON의 필드·파일 stem·object key이며, manifest에는 집합별 개수, 재생성 정의, SHA-256을 기록했다. 아직 fresh 비중복을 증명하지 못했으므로 `selected_new_corpus_question_ids`는 의도적으로 비어 있고 selection status는 blocked다. 과거 ID 복구 후 실제 선택 ID와 역할을 `split_manifest_v0_1.json`에 명시해야 한다.

## Week 1–3 ID 감사

다음 경로를 현재 프로젝트 루트와 리셋 프롬프트가 명시한 과거 Desktop 1 루트에서 각각 정확히 확인했다. 또한 사용 가능한 WSL 홈 영역에서 Git metadata와 다섯 정확한 파일명만 깊이를 제한해 검색했으나 추가 저장소나 역사 파일을 찾지 못했다. 다른 디스크 전체 탐색은 하지 않았다.

| 지정 파일 | 현재 루트 | 과거 루트 |
|---|---|---|
| `data_analysis/week1_sample_100.jsonl` | 없음 | 없음 |
| `evaluation/week2_eval_ids.json` | 없음 | 없음 |
| `evaluation/week3_engineering_dev_ids.json` | 없음 | 없음 |
| `evaluation/week3_locked_eval_ids.json` | 없음 | 없음 |
| `evaluation/week3_split_manifest.json` | 없음 | 없음 |

현재 작업공간에는 감사 시작 시 리셋 프롬프트만 있었고, 과거 Git 이력도 없었다. 이 조건에서는 ID를 복원하거나 추정할 증거가 없다. `historical_exposed_ids.json`은 호환용 명시 배열을 제공하지만 `audit_status = incomplete_missing_historical_artifacts`이며, 모든 빈 배열에 미복구 의미를 부여한다.

필수 해제 조건은 다음 중 하나에서 원본 5개 파일을 복구한 뒤 ID를 다시 추출하는 것이다.

1. 기존 연구 저장소의 권위 있는 커밋/원격 브랜치
2. 원래 연구 장비의 작업 디렉터리 또는 검증된 백업
3. 해시 또는 커밋 출처가 있는 연구 아티팩트 보관소

파일이 계속 없으면 과거 ID를 임의 생성하거나, 공식 dev 전체가 fresh라고 가정해서는 안 된다.

복구 출처 후보와 v0.1 release authority는 구분한다. 현재 verifier는 이동 가능한 backup/store 문자열을 신뢰하지 않으며, 복구 bytes가 researcher-approved canonical Git commit에 그대로 보존되고 full 40-hex OID 및 commit 내 파일 hash가 일치할 때만 gate를 연다.

## 데이터 역할 및 누출 주의

- 공식 dev 3,466개는 **후보 풀**이다. 과거 ID 복구와 제외가 끝나기 전에는 새 역할을 배정하지 않는다.
- 공식 test 3,463개는 답이 없고 기존 test 역할이다. 튜닝·주석 스키마 개발·operator vocabulary 개발에 재사용하지 않는다.
- `train.traced.json`과 `dev.traced.json`의 `answer-node`는 공식 `released_data/README.md`가 “approximated, not guaranteed to be correct”인 weak label이라고 명시한다. 이것은 gold graph가 아니며, question-only semantic skeleton 주석이나 다른 초기 레이어 입력에 노출하면 안 된다.
- 원본 `answer-text`와 `dev_reference.json`도 semantic/topology 주석 단계에는 숨기고 실행 검증 또는 허용된 후속 레이어에서만 사용해야 한다.
- question ID는 split-disjoint지만 table ID가 크게 겹친다. 환경 일반화 평가에서 이를 별도로 관리해야 한다.

## 라이선스 증거

- 공식 프로젝트 페이지: 데이터셋을 Creative Commons Attribution 4.0 International로 표시한다.
- `HybridQA` 핀 커밋: 저장소 루트에 MIT `LICENSE`가 있다.
- `WikiTables-WithLinks` 핀 커밋: 루트 `LICENSE` 파일이 없다.

따라서 연구 내부 재현에는 공식 사이트와 저장소 고지를 보존하고 출처를 인용한다. 연결 환경을 별도로 재배포하거나 외부 공개 번들에 포함하기 전에는 CC BY 4.0 문구가 해당 저장소 내용 전체에 적용되는지 연구자가 확인해야 한다. 이는 법률 판단이 아니라 감사상 범위 불명확성 기록이다.

## 재현 명령

네트워크를 사용해 새 machine-local 캐시를 만들고 검증한다.

```bash
source_root="${XDG_CACHE_HOME:-$HOME/.cache}/pj1-hybridqa-source-audit"
bash data_construction/tools/fetch_official_hybridqa_sources.sh --dest "$source_root"
```

이미 받은 원본을 네트워크 없이 다시 검증한다.

```bash
source_root="${XDG_CACHE_HOME:-$HOME/.cache}/pj1-hybridqa-source-audit"
bash data_construction/tools/fetch_official_hybridqa_sources.sh \
  --dest "$source_root" \
  --verify-only
```

커밋 대상 JSON과 스크립트 구문을 확인한다.

```bash
python3 -m json.tool data_construction/manifests/historical_exposed_ids.json >/dev/null
python3 -m json.tool data_construction/manifests/source_manifest_v0_1.json >/dev/null
bash -n data_construction/tools/fetch_official_hybridqa_sources.sh
```

## 감사 한계와 다음 게이트

이번 감사는 공식 원격의 2026-08-21 관찰 상태를 커밋으로 고정한 것이며, Wikipedia의 현재 웹 내용과 동일하다는 주장을 하지 않는다. 사용해야 할 환경은 핀된 snapshot이다. 또한 사람 검토, 주석 안정성, operator granularity는 이 감사 범위가 아니다.

다음 안전한 작업은 과거 5개 파일의 복구다. 복구 전에는 `build_sample.py`의 불완전-history 차단을 유지하고, 꼭 필요한 형식 시험만 명시적 diagnostic override로 수행해야 한다.
