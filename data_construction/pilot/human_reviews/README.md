# Human review records

실제 사람이 독립적으로 작성한 원본 응답만 저장한다. 리뷰 패킷을 생성했다는 사실만으로 `human_single_review`, `human_double_review`, 합의 또는 gold 상태를 주장하지 않는다. Raw observation, blinded alignment, adjudication 산출물은 서로 다른 versioned artifact로 분리한다.

현재 Phase A1 수집 단위는 연구자 승인·상호 독립·무노출 실제 reviewer 한 명당 첫 committed-order 10문항의 immutable raw 파일 한 개다. 두 reviewer가 총 2파일/20 record를 만든다. Q1 대화는 human evidence가 아니며, 금지된 later-layer 자료에 노출된 사람은 영향받은 exposure-naive 작업에서 제외한다. Stable pseudonymous ID와 timestamp를 보존하되 실제 identity, 독립성, 연구자 승인, prior-exposure 확인은 수동 절차이며 기계 인증으로 표현하지 않는다.

Raw schema/hash/leakage pass는 record integrity일 뿐 semantic agreement가 아니다. 두 raw 파일 뒤 별도 blinded alignment/adjudication schema와 comparator를 결과 해석 전에 version/freeze하기 전에는 agreement, calibration pass, Phase A2 readiness를 주장하지 않는다. 기존 granularity packet용 accept/edit/reject review는 deferred Phase B evidence와 구분하며 지금 수집하지 않는다.
