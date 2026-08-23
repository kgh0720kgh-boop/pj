# 계층형 주석 스키마 v0.1

## 상태와 범위

이 문서는 HybridQA 질문을 다음 여섯 계층으로 분리하는 `annotation_bundle_v0_1` 계약을 설명한다.

```text
질문
  -> 의미 골격(semantic skeleton)
  -> 정보 의무(information obligations)
  -> 환경 독립 추상 토폴로지
  -> 환경 인지 연산자 토폴로지
  -> 구체 grounding
  -> 외부 실행 IR 참조 + 실행 reference
```

모든 스키마 문서는 JSON Schema Draft 2020-12를 선언한다. 파일 간 `$ref`는 같은 디렉터리를 기준으로 한 상대 경로만 사용한다. 저장소나 데스크톱의 절대 경로는 스키마와 후보 어휘에 기록하지 않는다.

이 버전은 **설계 후보**이다. 2026-08-23에 30-question 주석 파일럿 입력은 할당되었지만 coarse/medium/fine 표현, 인간 간 일치도, 실행 통계는 아직 없으므로 gold, 안정성, 최종 연산자 어휘를 주장하지 않는다.

## 파일과 버전

| 파일 | 기계 판독 버전 | 역할 |
|---|---|---|
| `schemas/common_definitions_v0_1.json` | 공통 정의 v0.1 | span, 모호성, provenance, review, leakage, 값 타입 |
| `schemas/semantic_skeleton_v0_1.json` | `semantic_schema_v0_1` | 질문만으로 정하는 저장소 독립 의미 골격 |
| `schemas/information_obligation_v0_1.json` | `obligation_schema_v0_1` | 답에 필요한 사실과 의미 의존성 |
| `schemas/abstract_topology_v0_1.json` | `abstract_topology_schema_v0_1` | 실행 primitive가 아닌 의미 함수 DAG |
| `schemas/operator_topology_v0_1.json` | `operator_topology_schema_v0_1` | 환경 capability와 후보 어휘에 따른 연산자 DAG |
| `schemas/grounding_v0_1.json` | `grounding_schema_v0_1` | 연산자 slot의 실제 표·열·값·문서·추론 결합 |
| `schemas/hierarchical_annotation_v0_1.json` | `annotation_bundle_v0_1` | 모든 계층, 대안 계획, 실행 reference, 감사 상태의 bundle |
| `schemas/operator_vocabulary_schema_v0_1.json` | `operator_vocabulary_schema_v0_1` | 세 후보 어휘 인스턴스의 계약 |
| `operator_design/operator_vocabulary_coarse_v0_1.json` | `operator_vocabulary_coarse_v0_1` | coarse 후보 4개 |
| `operator_design/operator_vocabulary_medium_v0_1.json` | `operator_vocabulary_medium_v0_1` | medium 후보 11개 |
| `operator_design/operator_vocabulary_fine_v0_1.json` | `operator_vocabulary_fine_v0_1` | fine 후보 20개 |

`information_obligations`는 버전과 계층 감사 정보를 함께 보존하기 위해 bare array가 아니라 `obligations` 배열을 가진 객체로 표현한다.

## 핵심 불변식

1. 의미 골격과 정보 의무에는 실제 표, 열, 문서 ID, retriever 결과, 실행 연산자를 넣지 않는다. 질문에 저장소가 명시된 경우에만 해당 source span을 `question_explicit_source_constraints`에 기록한다.
2. 추상 토폴로지의 의미 함수는 최종 primitive 어휘가 아니다.
3. 연산자 토폴로지는 operator와 dependency를 정하지만 인자 slot은 `deferred_to_grounding`, `unresolved`, `not_applicable` 중 하나이다. 실제 binding은 허용하지 않는다.
4. grounding은 `semantic_role_ref`와 `selected_binding`을 별도 필드로 유지한다.
5. 정확한 그래프 일치는 정답 조건이 아니다. `plan_equivalence_contract.exact_graph_match_required`는 항상 `false`이다.
6. 실행 성공은 의미 계획 유효성의 필요조건이 아니다. `execution_success_required_for_semantic_validity`는 항상 `false`이다.
7. LLM 제안, deterministic validation, 인간 검토, adjudication은 서로 다른 상태이다. 이 버전에서 `gold_claimed`는 항상 `false`이다.
8. `locked_eval`은 prompt/rubric/operator-vocabulary tuning을 금지하며 split 및 과거 노출 검사가 모두 `passed`여야 한다.
9. 분석 불가·증거 없음·환경 없음 사례는 가짜 node를 만들지 않는다. 상태별 빈 envelope를 사용한다.
10. 후보 어휘 밖 연산자가 필요하면 v0.1 어휘에 즉시 추가하지 않는다. `required_operator_extensions`에 근거를 남기고 새 버전 결정 대상으로 보낸다.

## 공통 정의의 모든 필드

아래 경로는 `common_definitions_v0_1.json#/$defs` 아래에 있다.

| 정의/필드 | 의미 |
|---|---|
| `identifier` | 계층 내부 ID. 빈 문자열과 공백 기반 ID를 금지한다. |
| `json_pointer` | bundle 내부 경로를 가리키는 RFC 6901 형태의 pointer. 여러 path segment를 허용한다. |
| `repository_relative_path` | 드라이브 문자, UNC, 루트 `/`로 시작하지 않는 이식 가능한 경로. |
| `source_span.text` | 원 질문에서 복사한 표면 문자열. |
| `source_span.start_char`, `end_char` | 반열린 문자 offset `[start, end)`. 텍스트 일치와 `end > start`는 deterministic 검사 대상이다. |
| `source_span.occurrence_note` | 동일 문자열 반복 등 offset 해석 보조 설명. |
| `source_alignment.alignment_status` | `explicit`, `implicit`, `inferred`. |
| `source_alignment.source_spans` | explicit이면 최소 1개인 원문 span 목록. |
| `source_alignment.explanation` | implicit/inferred이면 필수인 추론 이유. |
| `semantic_role.normalized_role` | 열린 정규화 역할명. 보편 ontology 소속을 주장하지 않는다. |
| `semantic_role.description` | 역할의 자연어 설명. |
| `semantic_role.source_alignment` | 역할과 질문 표면의 정렬. |
| `semantic_role.ontology_mapping.status` | `unmapped`, `proposed`, `reviewed`. |
| `semantic_role.ontology_mapping.ontology_id`, `concept_id` | proposed/reviewed일 때만 필요한 외부 mapping. |
| `ambiguity_flag.code`, `custom_code` | 표준 모호성 코드와 `other`일 때의 사용자 코드. |
| `ambiguity_flag.description`, `evidence` | 모호성 설명과 근거. |
| `ambiguity_flag.affected_paths` | 영향을 받는 bundle JSON Pointer들. |
| `ambiguity.has_ambiguity` | 모호성 존재 여부. |
| `ambiguity.flags` | `has_ambiguity=true`이면 비어 있을 수 없는 상세 목록. |
| `ambiguity.resolution_status`, `resolution_note` | 미검토, 미해결, 가정/증거 해결, 복수 해석 보존 상태와 설명. |
| `leakage_violation.affected_path` | 누출 영향을 받은 필드. |
| `leakage_violation.leaked_input_category` | 잘못 노출된 후속 계층 입력 종류. |
| `leakage_violation.description`, `disposition` | 문제 설명과 재작성/제외/명시 제약 인정 등 처리. |
| `leakage_check.status` | `not_run`, `passed`, `failed`. |
| `leakage_check.checked_at`, `checker_id` | 실제 검사를 수행했을 때의 시각과 검사자. |
| `leakage_check.violations` | failed이면 최소 1개, 그 외에는 빈 배열. |
| `layer_input_audit_base.layer` | 주석 계층명. 각 계층 스키마가 `const`로 좁힌다. |
| `layer_input_audit_base.observed_input_categories` | 주석자가 실제 본 입력 종류. 각 계층이 허용 enum을 좁힌다. |
| `layer_input_audit_base.question_explicit_source_constraints` | 질문이 명시한 source/tool 제약의 원문 span. |
| `layer_input_audit_base.leakage_check` | 해당 계층의 누출 검사 결과. |
| `artifact_reference.artifact_id`, `artifact_type` | artifact의 안정적 식별자와 종류. |
| `artifact_reference.repository_relative_path`, `source_uri`, `version_or_revision` | 적어도 하나가 필요한 이식 가능한 위치/버전 식별자. |
| `artifact_reference.sha256` | 있을 경우 64자리 SHA-256 hex. |
| `actor.actor_type`, `actor_id` | human/LLM/system/import 주체와 pseudonymous ID. |
| `model_provenance.provider`, `model_id`, `model_revision` | 모델 공급자, ID, 정확 revision 또는 `not_exposed_by_provider` 같은 정직한 표지. |
| `model_provenance.seed.status`, `seed.value` | seed 지정/미지원/비공개/미기록 상태와 지정 시 정수 값. |
| `model_provenance.generation_parameters` | temperature 등 실행 parameter 객체. |
| `model_provenance.prompt_artifact` | 사용 prompt의 artifact reference. |
| `model_provenance.raw_output_artifact` | SHA-256이 필수인 raw LLM 출력 artifact. |
| `provenance_event.event_type`, `timestamp` | created/edited/validated/reviewed/adjudicated/migrated/excluded 이벤트와 시각. |
| `provenance_event.actor`, `description`, `input_artifact_ids` | 수행 주체, 설명, 입력 artifact ID. |
| `annotation_provenance.creation_method`, `created_at`, `created_by` | 생성 방식, 시각, 생성 주체. |
| `annotation_provenance.source_artifacts` | 질문/표/문서/source manifest 등 입력 artifact. |
| `annotation_provenance.model_provenance` | LLM 관련 생성 방식이면 필수. |
| `annotation_provenance.annotation_tool_version` | 사용한 review/annotation 도구 버전. |
| `annotation_provenance.code_identity.status`, `commit_hash`, `working_tree_dirty` | commit 기록, 미커밋, 비-Git, 미기록 상태와 실제 코드 정체성. |
| `annotation_provenance.history` | 최소 1개의 불변 provenance event 이력. |
| `reviewer_record.reviewer_id`, `completed_at`, `decision` | 완료한 인간 reviewer와 accept/edit/reject/abstain 결정. |
| `reviewer_record.review_artifact`, `notes` | raw review artifact와 메모. |
| `review_status.state` | LLM 제안부터 single/double review, adjudicated, rejected까지의 정직한 상태. |
| `review_status.human_review_count`, `reviewer_records` | 완료된 인간 검토 수와 보존된 raw record. |
| `review_status.gold_claimed` | v0.1에서 항상 `false`. |
| `review_status.semantic_correctness_claim` | unassessed/provisional/human_reviewed/adjudicated. |
| `review_status.adjudication.*` | adjudicator, 시각, accept/preserve/reject 결정, 불일치 요약, artifact. |
| `validation_check.check`, `status` | parse/schema/registry/type/dependency/DAG/reachability/execution/obligation/leakage 검사와 상태. |
| `validation_check.checked_at`, `checker_id`, `details`, `artifact` | 실제 검사 정보, 실패·차단 설명, 결과 artifact. |
| `typed_value.value_type`, `value`, `raw_text`, `unit` | 문자열/entity/date/datetime/number/integer/boolean/null/list/unknown 값의 tagged union. list는 재귀적으로 typed value를 담는다. |

## 의미 골격 필드

| 경로 | 의미 |
|---|---|
| `schema_version`, `skeleton_id` | 고정 schema 버전과 골격 ID. |
| `answer_target.semantic_role` | 질문이 요구하는 답 역할과 원문 정렬. |
| `answer_target.target_variable_ids` | 답 변수를 가리키는 ID. `not_annotatable`이면 빈 배열. |
| `answer_type.value_type`, `other_value_type` | entity/string/number/date/row/list/set/unknown 등 예상 타입과 `other` 설명. |
| `answer_type.cardinality`, `source_alignment` | 답 개수 기대와 원문 근거. |
| `candidate_structure.kind` | single/set/paired/ordered/grouped/implicit/unknown. |
| `candidate_structure.variables[]` | 후보 변수 배열. `not_annotatable`이면 비어 있다. |
| `variables[].variable_id`, `semantic_role`, `quantification` | 변수 ID, 역할, single/existential/universal/set/group/unknown 수량화. |
| `variables[].explicit_members` | 질문에 명시된 후보 멤버들의 역할/원문 span. |
| `candidate_structure.set_description` | 후보 집합 설명. |
| `candidate_structure.expected_candidate_count.kind/minimum/maximum` | exact/minimum/range/unknown 개수 제약. |
| `relations_required[].requirement_id`, `relation_role` | 열린 관계 요구 ID와 의미 역할. |
| `relations_required[].subject_variable_id`, `object_variable_id` | 관계 양끝 변수. |
| `relations_required[].directionality`, `cardinality_expectation` | 방향성과 관계 cardinality 기대. |
| `attributes_required[].requirement_id`, `attribute_role` | 필요한 속성 ID와 열린 역할. |
| `attributes_required[].subject_variable_id`, `value_variable_id` | 속성 주체와 값 변수. |
| `attributes_required[].expected_value_type`, `other_value_type` | 값 타입 기대. |
| `comparison_requirements[].requirement_id`, `comparison_role`, `comparison_family` | 비교 요구 ID, 원문 역할, equality/ordered/temporal/set/boolean 계열. |
| `comparison_requirements[].operand_variable_ids`, `ordering_direction`, `tie_policy` | 피연산 변수, 방향, 동률 처리. |
| `aggregation_requirements[].requirement_id`, `aggregation_role` | 집계 요구와 질문 정렬. |
| `aggregation_requirements[].input_variable_id`, `result_variable_id`, `grouping_variable_ids` | 입력, 결과, 선택적 group 변수. |
| `arithmetic_requirements[].requirement_id`, `arithmetic_role` | 산술 요구와 질문 정렬. |
| `arithmetic_requirements[].operand_variable_ids`, `result_variable_id`, `unit_semantics` | 순서 있는 피연산자, 결과, 단위 의미. |
| `ordinal_requirements[].requirement_id`, `ordinal_role`, `rank`, `ordered_variable_id`, `direction` | 서수 요구, 순위, 대상, 정렬 방향. |
| `selection_requirements[].requirement_id`, `candidate_variable_id` | 선택 요구와 후보 변수. |
| `selection_requirements[].criterion_requirement_ids`, `selected_variable_id`, `selection_semantics` | 선택 기준 요구, 결과 변수, filter/arg/threshold 등 의미. |
| `back_mapping_requirements[].requirement_id`, `from_variable_id`, `to_answer_variable_id`, `association_role` | 선택된 중간 값에서 답 역할로 돌아가는 의미 관계. |
| `information_dependencies[].dependency_id`, `predecessor_requirement_ids`, `successor_requirement_id` | 의미 요구 간 선후 의존. |
| `information_dependencies[].dependency_kind`, `description` | value/candidate/comparison/selection/back-map/logical 의존 종류와 설명. |
| `ambiguity`, `completeness`, `layer_separation` | 골격 모호성, complete/partial/underspecified/not_annotatable 상태, 질문-only 입력 감사. |

## 정보 의무 필드

| 경로 | 의미 |
|---|---|
| `schema_version`, `obligation_set_id` | 버전과 의무 집합 ID. |
| `obligations` | 의미적 사실 요구 목록. blocked/not-annotatable이면 빈 배열 가능. |
| `terminal_obligation_ids` | 답 반환을 직접 지지하는 terminal 의무. blocked/not-annotatable이면 빈 배열. |
| `graph_status` | complete/partial/cyclic/unresolved/blocked/not_annotatable. |
| `obligations[].obligation_id`, `description`, `normalized_goal` | ID, 자연어 사실 요구, tool 명령이 아닌 정규화 목표. |
| `obligations[].source_alignment` | 질문 표면과 의무의 대응. |
| `obligations[].depends_on`, `dependency_mode` | 선행 의무 ID와 all/any/none 결합. |
| `obligations[].skeleton_requirement_refs` | 의미 골격 requirement ID 참조. |
| `semantic_outputs[].output_role_id`, `semantic_role`, `cardinality` | 의무가 충족되면 알려지는 의미 역할. |
| `satisfaction_criteria[].criterion_id`, `description`, `verifiability` | semantic/environment/human 수준 충족 기준. |
| `obligations[].necessity`, `condition` | required/conditional/optional과 conditional일 때 조건. |
| `obligations[].environment_independent` | 항상 `true`; 물리 도구를 의무에 넣지 않는다. |
| `obligations[].ambiguity`, `layer_separation` | 개별 모호성과 계층 입력 감사. |

## 추상 토폴로지 필드

| 경로 | 의미 |
|---|---|
| `schema_version`, `topology_id` | 버전과 추상 토폴로지 ID. |
| `nodes`, `entry_node_ids`, `output_node_ids` | 의미 함수 node와 입출구. blocked/not-applicable이면 모두 빈 배열. |
| `nodes[].node_id`, `semantic_function`, `other_function_label` | node ID와 SELECT/RESOLVE/ACQUIRE/COMPARE/ARG/MAP 등의 의미 함수. `OTHER`는 label 필수. |
| `nodes[].description`, `source_alignment` | 의미 기능 설명과 질문 정렬. |
| `nodes[].depends_on`, `dependency_mode` | node 의존성과 all/any/none 결합. |
| `nodes[].fulfills_obligation_ids` | 충족하는 의무 ID. |
| `nodes[].realizes_skeleton_requirement_ids` | 구현하는 골격 요구 ID. |
| `nodes[].input_semantic_variable_ids`, `output_semantic_variable_ids` | 의미 변수 흐름. |
| `nodes[].required_for_all_valid_plans` | 모든 유효 대안에서 필요한지 여부. |
| `required_dependency_constraints[].constraint_id` | exact node match 대신 검사할 계획 불변 의존 ID. |
| `predecessor_obligation_ids`, `successor_obligation_id`, `dependency_kind`, `required`, `description` | 의무 수준 선행/후행 관계와 설명. `required`는 항상 true. |
| `graph_status`, `ambiguity`, `layer_separation` | DAG/partial/invalid/blocked 상태, 모호성, question-semantic 입력 감사. |

## 연산자 토폴로지 필드

| 경로 | 의미 |
|---|---|
| `schema_version`, `topology_id` | 버전과 환경 인지 토폴로지 ID. |
| `operator_vocabulary.vocabulary_version`, `granularity` | coarse/medium/fine 후보 버전. 두 값의 조합은 조건식으로 고정한다. |
| `operator_vocabulary.artifact` | 사용한 어휘 파일 reference. |
| `environment_context.environment_id`, `capability_profile_id` | 환경 snapshot과 capability profile ID. |
| `environment_context.available_capabilities` | table/filter/project/link/retrieve/extract/parse/compare/join/KG 등 가능한 기능. |
| `environment_context.source_manifest` | pinned source manifest artifact. |
| `nodes`, `entry_node_ids`, `output_node_ids` | 선택된 연산자 node와 입출구. blocked/not-applicable이면 빈 배열. |
| `required_operator_extensions` | frozen 어휘가 부족할 때만 채우는 새 연산자 요구. 다른 상태에서는 빈 배열. |
| `required_operator_extensions[].extension_id`, `proposed_name` | extension 제안 ID와 후보 이름. 기존 v0.1에는 추가하지 않는다. |
| `semantic_functions_supported`, `typed_contract_summary`, `reusability_rationale` | 필요한 의미 기능, 타입 계약, 여러 질문/스키마 재사용 근거. |
| `pseudo_primitive_review`, `evidence_status`, `example_obligation_ids` | pseudo-primitive 검사, LLM/annotator/repeated-pilot 근거 수준, 예시 의무. |
| `nodes[].node_id`, `operator`, `depends_on`, `dependency_mode` | operator node와 DAG 의존성. granularity별 enum으로 이름을 제한한다. |
| `nodes[].realizes_abstract_node_ids`, `fulfills_obligation_ids` | 추상 node 및 의무 연결. |
| `nodes[].environment_capabilities_used`, `selection_rationale` | 사용 capability와 해당 실현을 선택한 이유. |
| `input_slots[].slot_name`, `expected_type`, `cardinality` | 입력 port 계약. |
| `input_slots[].source.source_kind` | upstream/environment/semantic/unbound 출처. |
| `source_node_id`, `source_port`, `capability`, `semantic_variable_id` | source kind에 따라 필요한 출처 상세. |
| `output_slots[].slot_name`, `declared_type`, `cardinality`, `semantic_variable_ids` | 출력 port와 의미 변수 연결. |
| `argument_slots[].slot_name`, `semantic_role_ref`, `expected_binding_kind`, `required` | 아직 구체화하지 않은 인자 역할. |
| `argument_slots[].grounding_status` | `deferred_to_grounding`, `unresolved`, `not_applicable`만 허용. |
| `graph_status` | complete/partial/cyclic/unresolved/unsupported/blocked/not_applicable. |
| `validation_checks`, `ambiguity`, `layer_separation` | 구조 검사, 모호성, 환경까지의 입력 감사. |

## Grounding 필드

| 경로 | 의미 |
|---|---|
| `schema_version`, `grounding_id`, `operator_topology_id` | 버전, grounding ID, 대상 topology ID. |
| `environment_snapshot.environment_id`, `capability_profile_id` | 실제 환경 identity. |
| `environment_snapshot.table_ids`, `document_collection_ids`, `source_manifest` | 표, 문서 collection, pinned source manifest. |
| `node_bindings` | topology node별 slot 결합. blocked/not-applicable이면 빈 배열. |
| `grounding_status` | full/partial/ambiguous/blocked/not_applicable/invalid. |
| `oracle_assistance_summary.used`, `affected_node_ids`, `acceptable_for_training_role`, `note` | oracle 사용을 숨기지 않는 전체 요약. |
| `node_bindings[].binding_id`, `topology_node_id`, `operator` | node grounding identity와 operator 교차검사용 사본. |
| `node_bindings[].argument_groundings`, `coverage_status`, `ambiguity` | slot grounding 목록, coverage, 모호성. |
| `argument_groundings[].slot_name`, `semantic_role_ref`, `expected_binding_kind` | topology slot과 semantic 역할. |
| `argument_groundings[].status`, `selected_binding`, `candidate_bindings` | grounded/partial/ambiguous/unresolved/not-applicable 상태와 선택/후보. |
| `candidate_bindings[].candidate_id`, `binding`, `selection_status`, `confidence`, `rationale` | 복수 surface 후보와 선택 판단. |
| `argument_groundings[].evidence_artifacts`, `selection_provenance`, `oracle_assistance_used`, `unresolved_reason` | 근거, schema/retriever/reader/oracle 출처, oracle flag, 미해결 사유. |
| `column_reference.table_id`, `column_index`, `column_label`, `match_status` | 열의 ID·위치·표면명과 exact/normalized/semantic/ambiguous match. |
| `table_binding.table_id`, `table_title` | 실제 표 결합. |
| `column_binding.column` | 실제 열 결합. |
| `row_predicate_binding.column`, `comparator`, `values`, `case_sensitive` | row predicate의 열, 비교자, typed literal, 대소문자 정책. |
| `literal_binding.literal`, `question_span` | 질문에서 온 typed literal과 선택적 span. |
| `entity_binding.entity_role`, `surface_form`, `entity_id`, `resolution_status`, `source_column` | entity 역할, 표면형, 해소 ID/상태와 출처 열. |
| `document_locator_binding.locator_rule`, `entity_role`, `document_collection_id`, `document_id` | link/search/question/direct-ID 문서 locator. |
| `document_locator_binding.selection_basis`, `oracle_assistance_used` | 환경 link/retriever/질문/annotator/oracle 선택 근거. |
| `requested_attribute_binding.semantic_attribute_role`, `surface_attribute_label`, `aliases` | 의미 속성과 환경 표면명. |
| `declared_value_type_binding.value_type`, `format_hint` | extraction/parsing 값 타입과 형식. |
| `cardinality_binding.cardinality` | 결과 개수 기대. |
| `key_reference.key_kind`과 `column`/`semantic_variable_id`/`table_id`/`entity_role`/`field_name` | column, 의미 변수, row identity, entity identity, document field 중 하나인 key 출처. |
| `join_key_binding.left_key`, `right_key`, `match_semantics`, `other_match_semantics` | 두 key reference와 equality 의미. |
| `reasoning_binding.binding_type`, `function`, `parameters` | comparison/aggregate/arithmetic/ordering/normalization/selection 함수. |
| `retrieval_query_binding.query_template`, `entity_role_refs` | entity 역할을 parameter로 쓰는 query template. |
| `other_binding.custom_binding_type`, `value`, `justification` | 아직 정식화되지 않은 binding과 필수 정당화. |
| `validation_checks`, `ambiguity`, `layer_separation` | grounding 구조 검사, 모호성, 실제 환경 입력 감사. |

## 계층 bundle 필드

| 경로 | 의미 |
|---|---|
| `schema_version`, `annotation_id` | `annotation_bundle_v0_1`과 주석 ID. |
| `question_id`, `question`, `question_language`, `table_id`, `dataset_role` | 원 질문 identity, BCP-47 언어, HybridQA 표, pilot/train/dev/locked 역할. |
| `semantic_skeleton`, `information_obligations`, `abstract_topology`, `operator_topology`, `grounding` | 각 독립 schema를 상대 `$ref`로 포함한 대표 계층. |
| `execution_graph.declared_target_ir_version` | historical target인 `IR_v0.2` 또는 unresolved. |
| `execution_graph.local_ir_definition_status` | available/missing/not_checked. |
| `execution_graph.graph_status` | not constructed, missing-IR blocked, external reference pending/validated/incompatible. |
| `execution_graph.ir_schema_artifact`, `graph_artifact`, `graph_id` | 외부 IR schema와 graph artifact reference. graph 구조를 이 schema에서 재정의하지 않는다. |
| `execution_graph.executable_status` | 미실행/실행 가능/불가/reader-tool 차단/IR 부재 차단. |
| `execution_graph.semantic_plan_assessment` | 실행 결과와 독립인 의미 계획 판단. review 상태와 교차 제약된다. |
| `execution_graph.validation_checks`, `limitation_note` | 외부 IR 검사 결과와 한계. |
| `execution_reference.availability`, `answer_visibility` | late execution 계층 reference의 available/withheld/unavailable 상태; 답은 execution-only. |
| `expected_final_answer`, `answer_provenance_artifacts` | available일 때만 허용되는 typed answer와 provenance. |
| `expected_intermediates[].expectation_id`, `obligation_ids`, `description`, `expected_value`, `evidence_requirements` | 의무별 예상 중간 사실과 필요한 row/cell/doc/span/trace provenance. |
| `execution_trials[].trial_id`, `status`, `runtime_id`, `timestamp` | 개별 실행 시도. |
| `observed_answer`, `trace_artifact`, `failure_category`, `details` | 실제 답, trace, semantic/grounding/tool/runtime/source 실패 분류. |
| `plan_equivalence_contract.applicability` | 의미 계획 비교 가능 여부. not-annotatable이면 `not_applicable`. |
| `exact_graph_match_required` | 항상 false. |
| `primary_correctness_criterion` | applicable이면 obligation/dependency/answer equivalence. |
| `required_obligation_ids`, `required_dependencies` | 모든 유효 계획이 만족해야 하는 사실과 선후 의존. |
| `answer_equivalence_required` | applicable이면 true, not-applicable이면 false. |
| `execution_success_required_for_semantic_validity` | 항상 false. |
| `allowed_variation` | fusion/fission/order/retrieval/join/normalization/environment realization 등 허용 차이. |
| `alternative_plans[].alternative_plan_id`, `representation_kind`, `description` | description-only/abstract/operator/grounded/external-graph 대안. |
| `alternative_plans[].abstract_topology`, `operator_topology`, `grounding`, `execution_graph` | representation kind에 따라 필요한 실제 대안 artifact. |
| `satisfies_obligation_ids`, `satisfies_dependency_constraint_ids` | 대안이 충족한다고 주장하는 invariant. |
| `differences_from_representative`, `valid_when` | 대표 계획과 차이, 환경 조건. |
| `assessment.semantic_validity`, `environment_compatibility`, `grounding_validity`, `execution_status`, `assessment_basis`, `notes` | 대안의 계층별 검토. top-level review보다 강한 인간/adjudication 상태를 주장할 수 없다. |
| `alternative_plans[].ambiguity` | 대안 자체의 모호성. |
| `ambiguity` | bundle 전체 모호성. |
| `annotation_provenance`, `review_status` | 공통 provenance와 truthful review 상태. |
| `leakage_controls.policy_version`, `early_layer_answer_exposure` | 정책 버전과 early-layer answer 비노출 const false. |
| `prediction_view_contracts[].task`, `input_paths`, `target_paths`, `prohibited_input_paths` | factorized/direct/execution task별 view. 다섯 task가 정확히 한 번씩 필요하다. |
| `boundary_audits[].boundary`, `status`, `checked_at`, `checker_id`, `violations` | 여섯 계층 경계 누출 감사. 각 경계가 정확히 한 번씩 필요하다. |
| `locked_eval_controls.prompt_tuning_allowed`, `rubric_tuning_allowed`, `operator_vocabulary_tuning_allowed` | locked_eval에서 모두 false. |
| `split_membership_verified`, `historical_exposure_checked` | locked_eval에서 모두 passed. |
| `split_manifest_artifact`, `historical_exposure_manifest_artifact` | locked_eval에서 필수인 두 manifest reference. |
| `bundle_validation` | 아홉 필수 check(parse/schema/registry/type/dependency/DAG/reachability/obligation/leakage)를 각각 정확히 한 번 기록하고 execution check는 최대 한 번 선택한다. |
| `bundle_status` | proposal/validated/pending/human/adjudicated/ambiguous/blocked/rejected. `review_status`와 교차 제약된다. |

`semantic_skeleton.completeness=not_annotatable`이면 obligations=`not_annotatable`, 이후 세 토폴로지/grounding=`not_applicable`, equivalence=`not_applicable`, 대안 계획=[]을 강제한다. missing source처럼 질문 의미는 해석 가능하지만 실행 환경이 없는 경우에는 의미 계층을 보존하고 더 뒤 계층만 blocked로 둘 수 있다.

## 후보 연산자 어휘 필드와 목록

세 JSON 인스턴스는 모두 `operator_vocabulary_schema_v0_1.json`을 `schema_ref`로 가리킨다.

| 경로 | 의미 |
|---|---|
| `schema_ref`, `schema_version`, `vocabulary_version`, `granularity` | validation schema의 상대 경로와 어휘 identity. |
| `status`, `domain_scope`, `selection_claim`, `empirical_evidence_status` | provisional, HybridQA-only, 미선정, 미파일럿 상태. |
| `type_system.status`, `note`, `types[].name`, `description` | IR v0.2가 아닌 분석용 후보 타입임을 밝히는 타입 표. |
| `operators[].name`, `category`, `purpose`, `semantics` | 연산자 identity와 실행 의미. |
| `semantic_functions_supported` | 어떤 추상 의미 함수를 실현할 수 있는지. |
| `input_ports/output_ports[].name`, `type`, `cardinality`, `description` | typed port 계약. |
| `argument_slots[].name`, `binding_kind`, `required`, `description` | grounding할 인자 slot. |
| `tool_binding_class` | table/retriever/reader/parser/function/graph/composite/unbound 후보. |
| `design_assessment.reusability`, `typed_contract_clarity`, `executability`, `composability`, `semantic_atomicity` | `provisional_rating`과 근거. |
| `design_assessment.annotation_stability.status`, `rationale` | 반드시 `unknown_pending_pilot`; 관측하지 않은 일치도를 만들지 않는다. |
| `known_risks`, `empirical_frequency_status` | 개별 위험과 `not_measured` 상태. |
| `pseudo_primitive_policy.default_disposition`, `rejected_patterns`, `exception_requirements` | 질문 특화 operator의 기본 거부/flag 정책과 예외 입증 조건. |
| `known_global_risks` | granularity 전체 위험. |

후보 목록은 다음과 같다.

- Coarse(4): `TABLE_LOOKUP`, `DOCUMENT_QA`, `COMPARE`, `CALCULATE`
- Medium(11): `FILTER`, `PROJECT`, `RETRIEVE`, `EXTRACT`, `JOIN`, `AGGREGATE`, `COMPARE`, `PARSE`, `ARG_EXTREME`, `ARITHMETIC`, `DISTINCT`
- Fine(20): `SELECT_ROWS`, `READ_CELL`, `FOLLOW_LINK`, `RETRIEVE`, `SELECT_SENTENCE`, `EXTRACT_SPAN`, `PARSE_DATE`, `PARSE_NUMBER`, `NORMALIZE`, `COMPARE_DATE`, `COMPARE_NUMBER`, `COMPARE_STRING`, `ARGMIN`, `ARGMAX`, `COUNT_ITEMS`, `SUM_VALUES`, `APPLY_ARITHMETIC`, `DEDUPLICATE_ITEMS`, `MATCH_KEYS`, `MAP_BACK`

이 개수와 목록은 coverage 결과가 아니다. 파일럿에서 새 연산자 필요 비율, graph 길이, schema 수, 의미 context 수, 모호성, reviewer disagreement를 측정해야 한다.

## IR v0.2 처리 (2026-08-21 설계 시점 기록)

현재 로컬 workspace에는 역사적 IR v0.2 schema와 operator registry가 없다. 따라서 이 작업은 IR node/edge/type를 추측해 새로 정의하지 않았다.

`execution_graph`는 다음 두 경우만 지원하는 reference-only envelope이다.

1. IR 정의가 없으면 `local_ir_definition_status=missing_local_definition`과 `graph_status=blocked_missing_ir_definition` 또는 `not_constructed`를 기록한다.
2. 이후 실제 IR v0.2 정의가 복구되면 `ir_schema_artifact`와 `graph_artifact`를 함께 참조하고 별도 IR validator의 결과를 기록한다.

실제 IR이 복구되기 전에는 grounded executable graph가 schema-validated되었다고 주장하면 안 된다. 반복 주석 증거가 IR 한계를 보이더라도 v0.1에서 편의상 새 IR을 만들지 말고 별도 변경 제안과 migration을 작성해야 한다.

### 2026-08-23 복구 업데이트

위 문단은 IR이 없던 설계 시점의 판단을 보존한 것이다. 이후 연구자 승인 provenance로 IR v0.2의 schema, operator/type registries, 네 Python module, condition-C JSONL, run manifest 등 열 개 파일을 byte-for-byte 복구해 `historical/ir_v0_2/`에 read-only로 격리했다. `historical/ir_v0_2/recovery_manifest_v0_1.json`이 파일별 hash와 Git authority를 고정하며, current-side adapter `data_construction/tools/validate_ir_v0_2_reference.py`는 역사 파일을 수정하지 않고 참조를 검증한다.

Exact-pin `.venv`에서 adapter의 `--all` 검사는 condition-C graph 50/50, node 520개에 대해 parse error 0, Draft 2020-12 schema error 0, IR v0.2 validator error 0을 확인했다. `DEAD_NODE` warning 455개는 숨기거나 성공으로 재분류하지 않는다. 이는 과거 planner의 reachability/dead-output 동작을 보여 주는 진단 증거이며, 현재 후보 granularity의 coverage나 품질을 입증하지 않는다.

Condition-C artifact에는 answer와 evaluator output이 포함된다. 따라서 execution-reference 검증 외에는 late-stage historical evidence로만 취급하고, question-only semantic skeleton, information obligations, abstract topology, operator topology의 입력·few-shot 예시·rubric tuning에 절대 노출하지 않는다.

## Schema가 강제하는 누출·검토·locked-eval 조건

- 각 계층의 `observed_input_categories`는 그 계층에서 볼 수 있는 enum으로 제한된다.
- semantic/obligation/abstract 계층에는 gold answer, gold span, 구체 grounding, old graph, oracle document ID를 나타내는 입력 category가 없다.
- grounding에서 oracle annotation을 쓸 수는 있지만 `selection_provenance=oracle_annotation`, slot의 `oracle_assistance_used=true`, 전체 summary를 모두 기록해야 한다.
- bundle의 다섯 prediction view와 여섯 boundary audit은 Draft 2020-12 `contains`, `minContains`, `maxContains`로 각각 정확히 한 번 나타나야 한다.
- `locked_eval`은 tuning 세 종류가 false이고, 두 격리 검사가 passed이며, 두 manifest가 있고, `locked_eval_isolation` boundary가 passed여야 한다.
- non-human review 상태는 `bundle_status=adjudicated`, `semantic_plan_assessment=human_accepted/adjudicated_accepted`, 인간 기반 alternative assessment를 허용하지 않는다.
- human single/double review는 adjudicated claim을 허용하지 않는다. adjudicated 상태만 adjudicated bundle/semantic claim을 허용한다.

## JSON Schema만으로 완전히 검사할 수 없는 항목

아래 항목은 deterministic validator의 **필수** 책임이다. `bundle_validation`에 상태를 기록하되 실행하지 않았으면 반드시 `not_run` 또는 `blocked`로 남긴다.

- 배열 안 ID의 유일성 및 모든 cross-reference 존재 여부
- `depends_on`의 자기 참조, cycle, entry/output 일관성
- obligation/requirement/abstract/operator/grounding 간 coverage와 ID 대응
- upstream `source_port` 존재, producer/consumer 타입과 cardinality compatibility
- 선택 vocabulary artifact의 실제 operator 목록과 topology enum 일치
- topology slot과 grounding slot 이름, operator, `expected_binding_kind` 일치
- source span의 offset 범위, 원 질문 substring과 `text` 일치
- row predicate의 comparator별 literal cardinality와 타입
- candidate `selected` 상태, `selected_binding`, oracle summary의 상호 일관성
- source reachability 및 dead node 검사
- repository-relative artifact path의 실제 존재와 hash 일치
- split의 zero overlap, 과거 노출 ID 및 locked-eval 격리
- `human_review_count`와 실제 reviewer identity/record 수의 정합성
- execution graph의 parse/operator/type/dependency/reachability 검사(IR v0.2 복구 후)
- 자연어 description 안에 later-stage 정보가 숨어 있는지에 대한 leakage 검사

따라서 schema 통과는 의미 정답이나 executable graph 정답을 뜻하지 않는다.

## 검증 결과 (2026-08-21 설계 시점 기록)

작성 시점 검증은 다음과 같다.

1. 작업 범위의 JSON 11개(스키마 8개, 어휘 3개)가 표준 JSON parser로 모두 파싱되었다.
2. 스키마 안 모든 로컬 상대 `$ref`의 대상 파일과 JSON Pointer fragment가 존재함을 확인했다.
3. system `jsonschema==3.2.0` 실행에서는 8개 Draft 2020-12 meta-validation을 건너뛰고 경고하며, 세 어휘에만 Draft 7 구조 호환 fallback을 적용했다. 이 결과를 정식 Draft 2020-12 통과로 해석하지 않는다.
4. 이어서 `requirements.txt`의 exact pins(`jsonschema==4.23.0` 포함)를 저장소 밖 임시 경로에 설치하고 아래 `--require-jsonschema` 명령을 실행했다. 8개 schema meta-validation과 3개 vocabulary instance validation이 `errors=0`, `warnings=0`으로 통과했다. operator 수는 4/11/20이고 topology enum과 vocabulary 이름 집합도 일치했다.
5. 결정론 도구 회귀 테스트는 26/26 통과했다. 실제 annotation/corpus instance는 freshness gate 때문에 생성되지 않아 instance validation 대상이 없다.

현재 system Python은 3.10.12이고 `jsonschema==3.2.0`이다. 이 system package만으로는 정식 검증을 재현할 수 없다. 완전한 검증에는 `requirements.txt`의 `jsonschema==4.23.0` 환경이 필요하며, 이번에는 저장소 밖 임시 exact-pin 환경에서 다음 검사를 실제로 통과시켰다.

```bash
python3 data_construction/tools/check_schema_bundle.py --root . --require-jsonschema
```

임시 환경은 schema bundle 검증 근거이지만 기기 간 복사할 project `.venv`가 아니다. 이 머신은 `python3-venv`가 없어 저장소 로컬 `.venv`를 만들지 못했으므로, 다른 기기에서는 새 `.venv`를 만들고 같은 명령을 다시 실행해야 한다.

## 파일럿 전 결정 (2026-08-21 설계 시점 기록)

**Schema-design candidate와 정식 bundle validation은 준비되었지만 실제 pilot 투입은 여전히 차단되어 있다.** historical exposure ID를 복구해 fresh question 분리를 입증해야 한다. 따라서 전체 phase의 현재 결정 `DATA_SOURCE_BLOCKED`는 바뀌지 않는다. 이 gate가 해소된 뒤 20–30개의 fresh HybridQA pilot에서 세 granularity를 실제로 주석하고 schema 부담, coverage, graph 길이, 대안 계획, 모호성, reviewer agreement를 측정한다. 인간 검토 전에는 이 bundle을 gold 또는 모델링-ready corpus로 부르지 않는다.

## 2026-08-23 현재 상태 addendum

위 `DATA_SOURCE_BLOCKED` 결정은 당시 스냅샷이며 현재 상태를 덮어쓰지 않는다. 이후 다음 gate가 실제로 해소되었다.

- 다섯 Week 1–3 역사 파일을 byte-for-byte 복구하고 strict manifest를 완성했다: 100 unique exposed IDs, 15 locked-eval IDs, errors 0.
- pinned official dev source에서 역사 ID와 겹치지 않는 30개 질문을 `annotation_schema_pilot`에 할당했다. override는 없고 train/dev/locked-eval은 모두 0이다.
- project-local exact-pin `.venv`에서 schema 8개와 vocabulary 3개가 full Draft 2020-12 validation을 errors=0, warnings=0으로 통과했다.
- 복구 IR adapter는 50/50 graph와 520 node를 error 없이 검증했으며 455 `DEAD_NODE` warning을 역사 planner evidence로 보존했다.

따라서 현재 진행 중인 과학 상태는 `DATA_SOURCE_READY_FOR_ANNOTATION_PILOT`이다. 이는 source/history/환경 gate가 파일럿 입력에 대해 열렸다는 뜻일 뿐, final modeling decision, gold annotation, final vocabulary, modeling-ready corpus를 뜻하지 않는다.

다음 exact task는 `data_construction/pilot/questions.jsonl`의 동일한 30개 질문 각각에 대해 answer/evaluator/grounding을 보이지 않는 leakage-safe coarse, medium, fine 표현을 만들고, 그 결과에 deterministic validation을 실행한 뒤 사람 calibration을 수행하는 것이다. 이 단계 전후에도 condition-C answer와 evaluator output은 early-layer view에 들어가면 안 된다.

현재 정식 재현 명령은 다음과 같다.

```sh
.venv/bin/python data_construction/tools/check_schema_bundle.py --require-jsonschema
.venv/bin/python data_construction/tools/validate_ir_v0_2_reference.py --all
.venv/bin/python -m unittest discover -s tests -v
sh scripts/cross_device_preflight.sh
```
