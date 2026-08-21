# Pilot artifacts

이 디렉터리에는 `questions.jsonl`, `llm_proposals.jsonl`, `deterministic_checks.jsonl`, `human_reviews/`, `resolved_annotations.jsonl`, `granularity_representations.jsonl`이 생성될 예정이다.

현재 과거 노출 ID 감사가 불완전하면 파일럿 선정은 `blocked`이다. diagnostic override로 만든 질문은 release 가능한 파일럿이나 locked-eval 근거로 승격할 수 없다.
