# HybridQA 타입 실행 그래프 IR v0.2

상태: **Week 2 첫 planner 실험용 동결 초안**  
IR 버전: `0.2`  
레지스트리 버전: `0.2`

이 문서는 Week 1 실측을 바탕으로 첫 graph-plan 생성 비교에 사용할 최소 IR을
정의한다. HybridQA가 제공하는 gold program 명세가 아니며, 수동으로 재구성한
Week 1 그래프를 gold supervision으로 승격하지 않는다.

기계 판독 시 우선순위는 다음과 같다.

1. `operator_registry_v0_2.json`: 연산자 의미, 서명, 인자 domain, 출력 규칙
2. `type_registry_v0_2.json`: 닫힌 base type 집합과 coercion 정책
3. `execution_graph.schema.json`: 모델이 생성할 plan JSON의 문법적 envelope
4. 이 문서: 위 계약의 해석, 실험 경계, 알려진 한계

JSON Schema와 registry가 충돌하면 의미·타입 검증에는 registry를 우선한다.
JSON Schema는 상태를 갖지 않는 1차 문법 필터다.

## 1. Week 1 근거와 최소화 결정

고정 dev 100문항의 LLM 보조 후보 계획에서 관찰된 연산자는 정확히 다음 11개다.

| 연산자 | 질문 빈도 | v0.2 상태 |
|---|---:|---|
| `PROJECT` | 100 | frozen seed |
| `RETRIEVE` | 99 | frozen seed |
| `EXTRACT` | 99 | frozen seed |
| `FILTER` | 95 | frozen seed |
| `JOIN` | 43 | frozen seed |
| `ARG_EXTREME` | 10 | frozen sample extension |
| `PARSE` | 9 | frozen sample extension |
| `COMPARE` | 5 | frozen seed |
| `AGGREGATE` | 3 | frozen seed |
| `ARITHMETIC` | 3 | frozen sample extension |
| `DISTINCT` | 1 | frozen sample extension |

100개 주석은 모두 `pending_human_review`이므로 빈도는 표본 수준 설계 근거이지
benchmark-wide 추정이 아니다. 상세 그래프 20개에서는 이 중 `PARSE`와
`DISTINCT`를 제외한 9개가 실제 node로 쓰였다. 두 연산자는 상세 20개가 아니라
100개 taxonomy에 직접 관찰됐으므로 유지한다.

v0.1의 `SORT`와 `NTH`는 100개 표본 node에 관찰되지 않았고 표본 밖 공식 예시로만
제안됐으므로 v0.2 첫 평가 registry에서 제거했다. 순위 문제가 평가 subset에
실제로 들어오면 IR `0.3` 후보로 재검토하며, 이번 버전에 미리 넣지 않는다.

v0.1의 `PROJECT`는 `Row | RowSet`만 받아 전체 표 투영 전에 의미 없는 `FILTER`를
요구했다. 반면 100개 후보 계획에는 `PROJECT`-first 경로가 반복되었다. 따라서
v0.2는 `PROJECT(Table | Row | RowSet, ...)`를 허용한다.

## 2. 생성 plan과 평가 metadata의 분리

v0.2 JSON Schema는 `model_generated_plan` profile만 정의한다. 생성 모델이 보는
question/schema/tool context에는 benchmark answer, manual graph, weak answer node,
수동 passage span이 들어가면 안 된다.

이에 따라 generated plan에는 다음을 금지한다.

- `question_ref.answer`
- `nodes[*].provenance`
- `nodes[*].status`
- `nodes[*].execution`
- `EXTRACT.arguments.span`
- `EXTRACT.arguments.pattern`
- `EXTRACT.arguments.oracle_assisted`

gold answer, annotation provenance, 실행 trace, latency, 오류는 평가 결과 envelope에
별도 저장한다. 질문 문자열이나 question-derived predicate literal이 우연히 정답과
같은 것은 “입력 gold 누출”과 다르지만, 실험 시 answer-string overlap을 별도로
감사해야 한다. Schema는 허용된 자유 텍스트에 모델이 추측한 답을 넣는 행위를
의미적으로 판별하지 못한다.

### 2.1 Week 2 pilot binding과 artifact 격리

이 IR을 사용하는 정본 pilot config/run은
`experiments/configs/week2_pilot.json` /
`week2-qwen2.5-0.5b-pilot-v0.6-fp32-sdpa-withinq-lcp-last-token-logits-n11`다. 동결값은 seed
`20260820`, CPU/float32, resolved SDPA attention, `max_nodes=11`, A/B 자유 생성
`max_new_tokens=1536`, B2 최대 regeneration 1회다.

11-node 상한은 IR 의미 계약이 아니라 이 pilot의 공통 실험 예산이다. 고정 50개
질문의 LLM-assisted, human-pending candidate-operation sequence는 최대 11개이며
31/50이 이전 4-node 상한을 넘는다. Task H의 non-gold manual reasoning
obligation은 최대 9개이며 13/20이 4개를 넘는다. 따라서 11은 알고리즘이
필요 연산을 생성하기도 전에 잘라 의미적 불완전성을 강제하던 design ceiling을
완화한다. 이 weak sequence는 gold program이 아니며, 모든 질문이 11 node에
표현된다는 보증도 아니다.

A/B1/B2는 동일 canonical planner input, 동일 최초 prompt 및 greedy decoding을
사용한다. Content-addressed shared cache가 question별 첫 raw output을 고정하므로 B
조건이 별도의 최초 sample을 뽑지 않는다. B2만 최초 parse/validation 실패 뒤
deterministic 오류를 받고 완전한 graph를 한 번 더 생성할 수 있다. C는 graph JSON을
자유 생성하지 않고, 매 단계 허용 후보 전체의 label conditional log-likelihood를
계산해 deterministic argmax를 선택한다. 즉 C의 closed choice는 생성 뒤 reject가
아니며, 1536 completion-token 상한은 A/B 자유 completion에 적용되는 상한이다.

C의 model forward, candidate token log-softmax, 평균 score는 float32이고 resolved
attention은 SDPA다. `token_lcp_dynamic_cache_v4_within_question_float32_sdpa_last_token_logits`는 전체
rendered prompt의 actual token-ID LCP를 **같은 질문 내** 연속 decision에서만
DynamicCache로 재사용하고, question ID가 바뀌면 cache를 초기화한다. 전체 token
sequence는 보존하고 공통 prefix 뒤 suffix를 다시 계산하므로 prompt protocol을
축약하거나 바꾸는 최적화가 아니다.
Prompt와 suffix forward는 후보 첫 token score에 필요한 마지막 위치 logits만
materialize하며 `choice_prompt_logits_projection=last_token_only`를 기록한다.
Multi-token 후보 prefix는 각 위치가 다음 후보 token을 예측하므로 full-sequence
logits를 유지하고 `candidate_prefix_logits_projection=full_sequence`를 기록한다.

SDPA direct/cached score tensor의 bitwise identity는 계약이 아니다. Actual Qwen short 및
canonical-lite probe에서 selected argmax는 같았고 candidate score 최대 절댓값 차이가
`5e-5` 이하였다. Cache metadata는 `within-question` scope, 즉
`choice_cache_scope=within_question`,
`choice_numerical_mode=float32_sdpa`를 명시한다. `5e-5`는 저장 metadata가 아니라
direct-vs-cached 회귀시험의 허용치다.
이 회귀 probe는 관측한 prompt에 대한 guard이지 모든 prompt의 동일 argmax를 증명하지
않는다.
`week2_c_static_first_json_v2`는 canonical question/schema/operator/tool 정보값을
A/B와 동등하게 유지하고 run-static field를 먼저 직렬화한 C 전용 prompt
protocol이다. A/B와 byte serialization이 같다고 주장하지 않으며,
closed-choice/free-decoding 차이도 남는다. Runtime의
`choice_cache_protocol_status=fresh_run_required`는 이 순서·dtype·attention·cache strategy 이전의
결과를 정식 v0.6 result에 섞지 않고 네 조건을 fresh run해야 한다는 계약이다.
V0.4에서 생성된 두 행은 archive에만 남겨 audit 용도로 사용한다.

단일 첫 qid probe에서 v0.5 float32/SDPA는 18.6초, archived v0.4 eager는
153.8초였다. 동시 부하·warm-up·process 상태가 통제되지 않은 단일 측정이므로
실험 성능 근거로 사용하지 않는다.

Runner는 model load/backend call/output 변경 전에 canonical planner-input hash와
eval ID 순서, 별도 gold sample의 coverage 및 question/table identity, data manifest가
고정한 모든 executor file의 byte 수/SHA-256, 기존 run artifact identity를
fail-closed로 검사한다. 실제 호출 전 preflight `run_manifest.json`에는 config,
eval IDs, planner inputs, gold sample, operator/type registry, graph schema, data
manifest 및 runtime/code identity hash가 기록된다. Gold sample의 사전 hash 검증은
평가 artifact를 고정하기 위한 것이며 answer 값은 planning이 끝난 뒤에만 evaluator가
join한다.

## 3. 정규 JSON 형태

```json
{
  "ir_version": "0.2",
  "graph_id": "week2-dev-036a6e84e2d25443-run-0001",
  "question_ref": {
    "split": "dev",
    "question_id": "036a6e84e2d25443",
    "table_id": "List_of_Pi_Kappa_Alpha_brothers_5",
    "question": "What year was the brother from Beta Omicron born ?"
  },
  "schema_ref": {
    "table_id": "List_of_Pi_Kappa_Alpha_brothers_5",
    "columns": [
      {"index": 0, "label": "Name"},
      {"index": 1, "label": "Original chapter"},
      {"index": 2, "label": "Notability"}
    ]
  },
  "sources": {
    "table": {
      "type": "Table",
      "locator": {
        "kind": "hybridqa_table",
        "table_id": "List_of_Pi_Kappa_Alpha_brothers_5"
      }
    }
  },
  "nodes": [
    {
      "id": "n1",
      "operator": "FILTER",
      "inputs": {
        "table": {"kind": "source", "source_id": "table"}
      },
      "arguments": {
        "predicate": {
          "kind": "eq",
          "column": {"index": 1, "label": "Original chapter"},
          "value": "Beta Omicron"
        }
      },
      "output": {"port": "result", "type": "RowSet"},
      "tool_binding": "table.filter"
    },
    {
      "id": "n2",
      "operator": "PROJECT",
      "inputs": {
        "rows": {"kind": "node", "node_id": "n1", "port": "result"}
      },
      "arguments": {
        "column": {"index": 0, "label": "Name"},
        "mode": "links",
        "cardinality": "one"
      },
      "output": {"port": "result", "type": "Entity"},
      "tool_binding": "table.project"
    },
    {
      "id": "n3",
      "operator": "RETRIEVE",
      "inputs": {
        "entities": {"kind": "node", "node_id": "n2", "port": "result"}
      },
      "arguments": {},
      "output": {"port": "result", "type": "Document"},
      "tool_binding": "document.retrieve"
    },
    {
      "id": "n4",
      "operator": "EXTRACT",
      "inputs": {
        "documents": {"kind": "node", "node_id": "n3", "port": "result"}
      },
      "arguments": {
        "attribute": "birth year of the person",
        "value_type": "Number",
        "cardinality": "one"
      },
      "output": {"port": "result", "type": "Number"},
      "tool_binding": "document.extract"
    }
  ],
  "answer": {"kind": "node", "node_id": "n4", "port": "result"}
}
```

이 예시에 `1944`나 수동 exact span은 없다. semantic reader가 실제 passage에서
값을 찾아야 하며, reader가 없거나 실패하면 실행 실패로 기록한다.

## 4. Graph 구조 계약

HybridQA 원시 표에는 빈 헤더 문자열이 실제로 존재한다. 따라서 column
reference의 `label`은 누락되어서는 안 되고 문자열이어야 하지만, 빈 문자열은
허용한다. `index`와 원시 `label`의 쌍을 그대로 비교하며 임의 이름으로
canonicalize하지 않는다.

### 4.1 최상위 필드

| 필드 | 요구 | 의미 |
|---|---:|---|
| `ir_version` | yes | 정확히 `0.2` |
| `graph_id` | yes | run 안에서 고유한 비어 있지 않은 ID |
| `question_ref` | yes | split/question/table ID와 질문; answer 금지 |
| `schema_ref` | yes | 실제 planner input의 table ID와 순서 있는 column 목록 |
| `sources` | yes | v0.2에서는 한 개 이상의 `Table` locator만 허용 |
| `nodes` | yes | 하나 이상의 operator node |
| `answer` | yes | 기존 node의 `result` port reference |

`question_ref.table_id`, `schema_ref.table_id`, 모든 table source locator의
`table_id`는 같아야 한다. JSON Schema는 서로 떨어진 문자열의 동일성을 비교할 수
없으므로 deterministic validator가 `TABLE_ID_MISMATCH`를 검사한다.

### 4.2 Node와 edge

generated node 필드는 다음 6개뿐이다.

```text
id, operator, inputs, arguments, output, tool_binding
```

별도 edge 배열은 없다. data edge는 `inputs`의 node reference에서 유도한다.
출력 port는 모든 node에서 `result` 하나다.

```json
{"kind": "source", "source_id": "table"}
{"kind": "node", "node_id": "n2", "port": "result"}
```

Stepwise constrained builder는 source 또는 이미 commit한 node만 후보로 노출한다.
따라서 그 builder가 정확히 구현되면 self/forward/dangling reference와 cycle은
생성 중 차단된다. 자유 생성 baseline은 같은 조건을 사후 validator로 검사한다.

### 4.3 Schema-grounded column

모든 실행 column 인자는 다음 완전한 쌍이다.

```json
{"index": 2, "label": "Points"}
```

Constrained condition은 planner input의 실제 column 쌍만 후보로 노출한다. index는
존재해야 하고 label은 그 index의 실제 label과 정확히 같아야 한다. fuzzy match나
모델이 만든 새 label은 허용하지 않는다.

## 5. 타입 시스템

닫힌 base type 집합은 v0.1과 같다.

```text
structured:       Table, Row, RowSet
linked evidence:  Entity, EntitySet, Document, DocumentSet
scalar:           String, Number, Date, Boolean
collection:       ValueSet
```

`Entity`도 scalar 비교/answer 관점에서는 scalar family에 포함된다. 등록된
coercion은 없다. 특히 다음 변환은 암묵적으로 일어나지 않는다.

- `String -> Number | Date`: `PARSE` 필요
- `Entity -> Document`: `RETRIEVE` 필요
- `Document -> scalar`: `EXTRACT` 필요
- `RowSet -> scalar`: `PROJECT` 또는 `AGGREGATE` 필요

`ValueSet`은 v0.2에서도 parameterized type 문자열이 아니다. 생성 builder는
`PROJECT`, `EXTRACT`, `PARSE`의 `output_rules`에서 얻은 원소 타입을 typed-state
metadata로 추적할 수 있지만 직렬화와 기존 executor는 base type `ValueSet`만
본다. 이 최소 호환 결정은 첫 실험의 구현 범위를 줄이지만 정적 보장이 약해지는
남은 모호성이다. `ValueSet<Number>` 같은 직렬화 변경은 이번 실험 결과가 필요성을
보일 때 다음 IR 버전에서 검토한다.

`RowSet`은 순서 보장을 갖지 않는다. `SORT`/`NTH`를 제외했으므로 v0.2 graph는
임의 row order를 순위 의미로 사용하면 안 된다. 관찰된 min/max row 선택은
`ARG_EXTREME`으로 표현한다.

## 6. 연산자 계약

아래 표는 사람이 읽는 요약이다. 정확한 input role, overload, argument domain,
output rule, failure code는 operator registry가 정본이다.

| 연산자 | 입력 → 출력 | 필수 인자 | schema | tool | 결정성·대표 실패 |
|---|---|---|---|---|---|
| `FILTER` | `Table→RowSet` 또는 `RowSet→RowSet` | `predicate` | `predicate.column` | `table.filter` | 입력 고정 시 결정론적; invalid predicate/column, empty |
| `PROJECT` | `Table\|Row\|RowSet→scalar/set` | `column`, `mode`, `cardinality` | `column` | `table.project` | 결정론적; column/cardinality mismatch, empty |
| `RETRIEVE` | `Entity→Document`, `EntitySet→DocumentSet` | 없음 | 없음 | `document.retrieve` | 고정 snapshot에서 결정론적; missing link/document |
| `EXTRACT` | `Document\|DocumentSet→typed value/set` | `attribute`, `value_type`, `cardinality` | 없음 | `document.extract` | reader 설정에 의존; unsupported/not found/type/cardinality |
| `JOIN` | `RowSet × key→RowSet` | `right_column`, `match` | `right_column` | `table.join` | 결정론적; no/ambiguous match, stale column |
| `AGGREGATE` | collection→`Number` | `function` | 없음 | `calculator.aggregate` | 결정론적; empty/non-numeric/unsupported function |
| `COMPARE` | keyed set 또는 same-type pair→selection/Boolean | `relation`, `return`, `tie_policy`; set은 `parse`도 필수 | 없음 | `calculator.compare` | 결정론적; type/parse/tie/relation failure |
| `PARSE` | `String→Number\|Date`, `ValueSet→ValueSet` | `target_type` | 없음 | `calculator.parse` | 결정론적; parse/ambiguous date failure |
| `ARG_EXTREME` | `Table\|RowSet→Row` | `column`, `mode`, `parse`, `tie_policy=error` | `column` | `table.arg_extreme` | 결정론적; empty/parse/tie failure |
| `ARITHMETIC` | `Number²→Number` 또는 `Date²→Number` | `function`; date는 `unit` | 없음 | `calculator.arithmetic` | 결정론적; zero division/type/unit failure |
| `DISTINCT` | `ValueSet\|EntitySet→동일 base type` | `normalization` | 없음 | `calculator.distinct` | 결정론적; normalization failure |

### 6.1 `FILTER`

v0.2는 executor와 Week 1 사례가 요구한 닫힌 predicate kind만 노출한다.

```text
eq, contains, in, numeric_eq, numeric_gt, numeric_lt
```

`in`은 `values`만 요구하며 다른 variant는 `value`만 요구한다. 값 자체는 schema
후보가 아니라 질문에서 모델이 생성하는 literal이다. 따라서 column identity와
predicate grammar는 generation-time constraint지만 predicate의 의미적 적합성은
그렇지 않다.

### 6.2 `PROJECT`와 명시적 cardinality

`cardinality`는 출력 타입을 생성 중 하나로 정하기 위한 planner 선언이다.

| mode | cardinality | 출력 |
|---|---|---|
| `text` | `one` | `String` |
| `text` | `many` | `ValueSet` (state metadata: String) |
| `links` | `one` | `Entity` |
| `links` | `many` | `EntitySet` |

`one`인데 실제 결과가 0개 또는 여러 개이면 plan이 문법적으로 valid했더라도
executor는 `CARDINALITY_MISMATCH` 계열 실패를 내야 한다. v0.1의 raw `cells`
mode는 첫 planner 실험에 필수적이지 않아 제거했다.

### 6.3 `RETRIEVE`

v0.1처럼 `String`이나 `ValueSet`을 entity처럼 묵시적으로 받아들이지 않는다.
entity link는 `PROJECT(mode=links)` 또는 typed `EXTRACT(value_type=Entity)`가
만들어야 한다. `link_policy=all`은 HybridQA local snapshot 도구의 고정 동작으로
내려가며 모델 생성 인자에서 제거했다.

### 6.4 `EXTRACT`와 answer leakage 경계

v0.1 수동 그래프 20개는 모두 annotator/oracle-assisted extraction을 사용했고,
성공 16개 중 12개는 gold answer literal이 node argument에 있었다. 그 contract를
모델 생성 실험에 그대로 쓰면 answer accuracy를 측정할 수 없다.

따라서 v0.2 `EXTRACT`는 다음만 생성한다.

```json
{
  "attribute": "birth date of each person",
  "value_type": "Date",
  "cardinality": "many"
}
```

`attribute`는 IR 수준에서는 **자유 텍스트**이며 Week 1은 닫힌 ontology를
확립하지 않았다. 다만 이번 resource-limited pilot 구현은 질문 cue에서 만든
결정론적 finite proposal과 generic fallback만 열거하고 모델이 그중 하나를
고른다. 따라서 한 실행 안의 선택은 closed choice이지만, 전역 attribute
ontology나 의미적 coverage 보장은 아니다. 올바른 attribute가 후보에 없을 수
있으므로 이 휴리스틱 자체가 over-constraint 오류 원인이 될 수 있다. output
type과 cardinality만 registry가 의미와 무관하게 제한한다.

`cardinality=one`은 `value_type`과 같은 scalar를 출력한다. `many + Entity`는
`EntitySet`, 그 밖의 many scalar는 `ValueSet`을 출력한다. span/pattern/oracle
인자는 post-hoc validator와 JSON Schema 모두 거부해야 한다.

현재 Week 2 executor에는 이 generated semantic-attribute contract를 수행할 reader가
없다. 따라서 generated plan의 실행이 `EXTRACT(attribute=...)` node에 도달하는 모든
경로는 의도적으로 `UNSUPPORTED_EXTRACTION`으로 끝난다. Week 1 oracle
`exact_span`/`regex`로 조용히 fallback하지 않는다. 이 상태에서 graph validity는
구조·schema·type·reference diagnostic일 뿐 document entailment나 end-to-end
executability를 증명하지 않으며, hybrid end-to-end 핵심 가설은 `INCONCLUSIVE`다.

### 6.5 Reduction과 selection

- `AGGREGATE`는 base type이 분명하도록 `ValueSet`에는 `values`, `EntitySet`에는
  `entities`, `RowSet`에는 `rows` input role을 사용한다. Row/Entity set은
  `count`만 허용한다.
- `AGGREGATE(ValueSet, ...)`는 count/sum/min/max/average를 허용한다. 수치
  reduction의 원소 타입 정밀성은 typed-state metadata와 executor parse에 의존한다.
- `COMPARE`는 Boolean pair 비교와 keyed-set 선택을 한 연산자로 유지하되 `return`
  인자로 의미를 명시한다. 이는 여전히 다소 넓은 연산자라는 모호성이 남는다.
- `ARG_EXTREME`은 table row의 min/max 선택에만 사용하며 `tie_policy=error`로
  singleton 출력을 정직하게 보장한다.
- `DISTINCT`는 input base type을 보존한다.

## 7. Generation-time constraint에 사용하는 방법

Registry는 prompt 설명문이 아니라 후보 열거의 source of truth다. 권장 stepwise
builder state는 다음과 같다.

```text
available_values = {
  value_id: {
    base_type,
    optional_element_type,
    source_or_committed_node,
    output_port
  }
}
committed_nodes
table_schema_columns
```

각 step은 다음 순서를 따른다.

1. `generation.enabled=true`인 operator만 열거한다.
2. `signatures[*].inputs`의 role/type을 현재 `available_values`와 exact match한다.
3. 선택한 signature의 role별로 source 또는 과거 node reference만 열거한다.
4. `schema_requirements` 인자는 planner input의 완전한 column pair만 열거한다.
5. enum은 `argument_schemas`와 signature `argument_domains`의 교집합만 열거한다.
6. `state_constraints`가 있으면 planner가 추적한 `ValueSet` element metadata에도
   적용한다. 예를 들어 numeric reduction은 `Number` 원소만, collection
   `PARSE`는 `String` 원소만 후보가 된다.
7. 이번 pilot의 `question_derived_literal/text`는 질문에서 결정론적으로 제안한
   finite 후보 중 closed choice로 고른다. 후보 내용의 의미 정확성·완전성은
   보장하지 않는다.
8. `output_rules`로 base output type과 선택적 element metadata를 결정한다.
9. node를 commit하고 새 typed value를 state에 추가한다.
10. answer-eligible type을 가진 기존 node만 termination 후보로 노출한다.

이 절차가 적용하는 것은 “generation-time operator/type/schema constraints”다.
다음은 여전히 deterministic post-hoc validator가 확인한다.

- 전체 graph field와 ID uniqueness
- 외부에서 주어진 graph의 dangling reference/cycle
- table ID 일치
- answer source reachability와 dead node
- registry signature/argument/output/tool binding 일치
- schema index/label의 실제 일치

실제 row cardinality, document 존재, semantic extraction, parse 가능성, join match,
동률, 답의 의미적 정확성은 executor-time 또는 평가-time 속성이다. 따라서 v0.2
prototype을 모든 의미에서 “valid by construction”이라고 부르면 안 된다.

## 8. JSON Schema가 보장하는 것과 못 하는 것

Draft 2020-12 schema는 다음을 문법적으로 차단한다.

- 잘못된 IR version, 필수 top-level/node field, 알 수 없는 field
- gold/runtime/annotation field
- 미등록 operator 이름과 operator별 input role shape
- column reference의 `{index,label}` 모양
- 닫힌 argument enum, tool binding, output port/base type의 일부 조건
- answer가 node-reference 모양이 아닌 경우

일반 JSON Schema만으로는 다음을 검사할 수 없다.

- `nodes[*].id`나 column index의 property 기준 uniqueness
- reference resolution, self/forward reference, cycle, source reachability
- referenced node의 실제 type과 operator signature의 결합
- column pair가 현재 planner input schema에 실제 존재하는지
- 멀리 떨어진 `table_id` 필드들의 동일성
- resolved input type에 따라 달라지는 signature별 argument domain 전부
- semantic correctness, document entailment, guessed-answer 자유 텍스트

`uniqueItems`는 object 전체 동일성만 비교하므로 node ID uniqueness 해결책이
아니다. `$data` 같은 비표준 확장은 사용하지 않는다. 이 한계 때문에 JSON Schema
통과율을 graph structural/type/schema validity와 동일시하지 않는다.

## 9. v0.1 호환성과 adapter

직렬화의 source/ref/node/output 골격과 base type 문자열은 의도적으로 유지했다.
현재 코드에서는 다음처럼 v0.2 registry를 명시적으로 주입해야 한다.

```python
from hybridqa_graph.registry import load_registries
from hybridqa_graph.validator import validate_graph

registry_v02 = load_registries(
    "ir/operator_registry_v0_2.json",
    "ir/type_registry_v0_2.json",
)
report = validate_graph(
    graph,
    schema=graph["schema_ref"],
    registry=registry_v02,
    generated_plan=True,
)
```

기본 `get_registry()`는 Week 1 재현을 위해 v0.1을 계속 가리킨다. v0.1
`ExecutionGraph` dataclass도 기본 version과 annotation provenance contract가
다르므로 generated v0.2 plan에는 ordinary mapping 또는 별도 planner builder를
사용해야 한다.

v0.1 수동 graph를 단순히 `ir_version`만 바꿔 v0.2로 사용할 수 없다.

| v0.1 요소 | v0.2 migration |
|---|---|
| `question_ref.answer` | 제거하고 evaluator metadata로 이동 |
| node `provenance/status/execution` | plan에서 제거하고 결과 envelope로 이동 |
| `PROJECT` | `cardinality` 추가; `cells`는 의미에 따라 `text`로 재표현 |
| `RETRIEVE.link_policy` | 제거; local tool fixed behavior로 compile |
| exact-span/regex `EXTRACT` | 자동 변환 금지; 비-gold `attribute` plan을 새로 생성 |
| `ARG_EXTREME` | `tie_policy=error` 추가 |
| bespoke `COMPARE` relation | 닫힌 relation/return/parse로 재표현 |
| `SORT`, `NTH` | unsupported; v0.2 평가 subset에서 제외하거나 명시 실패 |

현재 최소 executor의 table projection/retrieval/filter/join/calculator 경로는 같은
base node shape를 받아들인다. `PROJECT.cardinality`, `ARG_EXTREME.tie_policy`, v0.2
`COMPARE` relation/return/tie와 `ARITHMETIC` left/right role도 runtime에서 명시적으로
처리한다. 다만 가장 중요한 tool gap은 자유형 `attribute`를 수행할 semantic document
reader가 없다는 점이다. 현재 executor가 모든 reached generated attribute path에
`UNSUPPORTED_EXTRACTION`을 내는 것은 올바른 동작이며 exact-span oracle로 조용히
대체하면 안 된다. 실행기는
`execute_graph(..., registry=registry_v02, generated_plan=True)`처럼 동일 registry와
generated profile로 validation한 뒤 실행해야 한다.

## 10. 알려진 모호성과 동결 범위

첫 실험 동안 동결하는 항목은 다음이다.

- 11개 operator 이름과 input role
- v0.2 base type 집합과 암묵 coercion 금지
- data-dependency DAG와 단일 `result` port
- 실제 `{index,label}` schema 후보만 사용하는 정책
- generated plan과 gold/provenance/runtime metadata의 분리
- `EXTRACT`의 answer-span 금지, open-string IR과 finite pilot proposer의 경계
- registry를 이용한 동일 조건 간 constraint enumeration

남은 모호성은 결과 보고서에서 숨기지 않는다.

- `ValueSet` member type은 직렬화되지 않고 planner state metadata에만 있다.
- keyed document value와 원 table row association은 base type이 아니라 runtime
  key/provenance에 의존한다.
- `COMPARE`는 Boolean 판정과 selected-value 반환을 함께 가진다.
- semantic `EXTRACT`의 reader 모델, entailment, confidence contract가 미정이다.
- missing/null, unit, locale, tie, multiple-answer rendering이 완전하지 않다.
- 서로 다른 graph가 같은 정답과 동등한 의미를 가질 수 있다.

또한 평가 subset의 `answer_source=table_cell`은 table-only 의미가 아니다. 15문항 중
14문항은 Week 1 annotation에서 `requires_text=true`이고, 전체 50문항 중 49문항이
linked text를 요구한다. 전자는 최종 답 표면 위치, 후자는 추론 modality need에 대한
서로 다른 LLM-assisted, `pending_human_review` metadata다.

이 동결은 첫 controlled comparison을 위한 것이다. 실측 failure가 표현 부족에서
나오면 operator를 즉석에서 늘리지 말고 `UNSUPPORTED_REASONING`으로 기록한 뒤 다음
version 결정 근거로 사용한다.
