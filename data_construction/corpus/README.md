# Corpus artifacts

검토가 끝난 `train.jsonl`, `dev.jsonl`, `locked_eval.jsonl`만 이 디렉터리에 둔다. 현재 빈 placeholder를 corpus로 오해하지 않도록 split 파일은 생성하지 않는다.

생성 전 필수 조건:

- 과거 노출 ID inventory가 complete일 것
- source 및 split manifest가 고정될 것
- 역할 간 ID overlap이 0일 것
- schema/operator version이 고정될 것
- locked-eval이 tuning에 사용되지 않았을 것
- review/provenance 상태가 실제 절차와 일치할 것
