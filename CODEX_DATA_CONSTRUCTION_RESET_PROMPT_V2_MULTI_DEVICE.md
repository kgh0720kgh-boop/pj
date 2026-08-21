# Codex Research Reset Prompt — Hierarchical Data Construction for Semantic Execution Topology Induction
## Project: Question → Semantic Skeleton → Operator Topology → Grounding → Executable Graph

You are continuing the existing research project.

The historical Desktop 1 path is:

```text
/home/geonho/pj1/research/hybridqa_execution_graph
```

However, **the absolute path is not the project identity**. This project must be portable across multiple desktops.

At startup, locate the Git repository root from the current working directory or from a user-supplied clone path. Treat the Git remote, repository history, branch, manifests, and committed project instructions as the source of continuity across machines.

Do not hard-code `/home/geonho/...` into new source code, configs, manifests, scripts, or tests unless a machine-local path is explicitly required. Prefer repository-relative paths.

This is **not** a request to delete or rewrite Week 1–3 work.

The purpose of this phase is to reset the *scientific workflow* around a better-defined supervision problem:

> Before further planner optimization, construct a research dataset that separates:
> 1. what can be inferred from the question semantics alone,
> 2. what operator topology is needed given the available environment,
> 3. how that topology is grounded to concrete schema/entities/attributes,
> 4. what executable graph results from that grounding.

The central research object is no longer merely a structurally valid graph.

The new data model should support research on:

```text
Question
  ↓
Semantic Skeleton / Information Obligations
  ↓
Abstract Operator Topology
  ↓
Environment-Aware Operator Realization
  ↓
Schema / Argument Grounding
  ↓
Grounded Executable Graph
  ↓
Execution / Trace
```

Read this entire prompt before modifying code.

---

# 1. Why this reset is necessary

Historical Week 1–3 findings must remain preserved.

## Week 1
- HybridQA data and linked table/document environment were inspected.
- A typed execution-graph IR and operator registry were built.
- 20 detailed graphs were manually/LLM-assisted constructed.
- These graphs are **not gold programs**.
- They used oracle/annotator-assisted extraction evidence.
- They are useful as historical feasibility examples only.

## Week 2
Generation-time constraints produced 50/50 structurally valid graphs in condition C, but:

```text
RETRIEVE = 0
EXTRACT  = 0
JOIN     = 0

dead nodes = 455/520
node-cap hit = 44/50
preliminary semantic-valid = 0/20
EM = 0/50
```

The major lesson is:

```text
STRUCTURALLY VALID GRAPH
!=
SEMANTICALLY CORRECT REASONING PLAN
```

## Week 3
- Human review protocol was prepared, but actual human reviewers were unavailable.
- A gold-free reader contract was implemented.
- Reader results were synthetic regression only, not natural HybridQA performance.
- Historical C failure was diagnosed mainly as planner modality avoidance.
- IR v0.2 was retained.

Therefore:

> Before further planner intervention, the project needs explicit supervision for the semantic structure that lies between the natural-language question and the final grounded execution graph.

---

# 2. Refined research decomposition

Treat the task as several conceptually separate prediction problems.

## Layer 0 — Natural-language question

Example:

```text
For the XXXI and XXX Olympic events, which event had the older flag bearer?
```

## Layer 1 — Semantic Skeleton / Information Obligations

This layer should describe what must be known or compared **without assuming where the information is stored or which physical tool will be used**.

Illustrative representation:

```text
answer_target:
  Event

candidate_set:
  {Event A, Event B}

required_relation:
  Event -> FlagBearer

required_property:
  Age(FlagBearer)

reasoning_requirements:
  compare property values
  select older FlagBearer
  return associated Event
```

This layer answers:

> What information is logically required by the question?

It should NOT yet assume:

```text
RETRIEVE
EXTRACT
SQL
vector search
specific table column
specific document ID
```

unless these are explicitly stated in the question itself.

## Layer 2 — Abstract Operator Topology

Given the semantic obligations and the available environment, represent the required primitive execution operations and dependencies.

Example:

```text
FILTER
-> PROJECT
-> RETRIEVE
-> EXTRACT
-> COMPARE
-> JOIN
-> PROJECT
```

This layer answers:

> What execution operations are required, and how do their outputs depend on each other?

It should not yet contain all concrete schema arguments.

## Layer 3 — Grounding

Fill the operator slots using the actual HybridQA environment:

```text
FILTER.column = edition
FILTER.values = {XXXI, XXX}

PROJECT.column = flag_bearer

EXTRACT.attribute = birth_date
EXTRACT.value_type = Date

JOIN.column = flag_bearer
```

This layer answers:

> What concrete table, column, entity, literal, linked-document capability, attribute, type, and join key realizes each abstract operation?

## Layer 4 — Grounded Executable Graph

Produce the actual typed graph under IR v0.2, or a new version only if data evidence requires it.

## Layer 5 — Execution Reference

Where possible, record:
- whether the graph is executable,
- expected intermediate obligations,
- expected final answer,
- provenance requirements,
- known ambiguity,
- alternative valid plans.

Do NOT use execution success alone to define semantic correctness.

---

# 3. Question semantics vs environment

A major purpose of the dataset is to distinguish:

```text
What the question requires
```

from:

```text
How the current environment can satisfy it
```

For example, the same semantic question may admit different execution topologies depending on the environment.

If birth date is already a table column:

```text
FILTER
-> PROJECT birth_date
-> COMPARE
```

If birth date exists only in linked documents:

```text
FILTER
-> PROJECT flag_bearer
-> RETRIEVE
-> EXTRACT birth_date
-> COMPARE
-> JOIN
```

If a KG provides the property:

```text
FILTER
-> PROJECT entity
-> LOOKUP_PROPERTY
-> COMPARE
-> JOIN
```

Therefore:

> Do not encode storage-specific operations into the semantic skeleton unless the question itself specifies the source.

---

# 4. Primitive operator granularity is an empirical design question

Do not assume the current operator set is already optimal.

Current candidate medium-granularity operators include:

```text
FILTER
PROJECT
RETRIEVE
EXTRACT
JOIN
AGGREGATE
COMPARE
PARSE
ARG_EXTREME
ARITHMETIC
DISTINCT
```

Treat these as provisional.

Compare at least conceptually:

## Coarse
```text
TABLE_LOOKUP
DOCUMENT_QA
COMPARE
CALCULATE
```

Risk:
- reasoning hidden inside large operators,
- weak compositionality.

## Medium
```text
FILTER
PROJECT
RETRIEVE
EXTRACT
JOIN
COMPARE
AGGREGATE
```

Potential advantage:
- clear typed contracts,
- manageable graph length,
- reusable composition.

## Fine
```text
RETRIEVE
SELECT_SENTENCE
EXTRACT_SPAN
PARSE_DATE
NORMALIZE
COMPARE_DATE
ARGMIN
MAP_BACK
```

Risk:
- graph length explosion,
- planning search-space explosion,
- high annotation cost.

The goal is NOT to select final granularity by intuition.

Use annotation evidence.

---

# 5. Operator design criteria

For every candidate primitive operator, assess:

- reusability across questions/schemas,
- typed input/output contract,
- executability/tool binding,
- composability,
- semantic atomicity at the chosen abstraction level,
- annotation stability,
- coverage without question-specific operators.

Reject or flag pseudo-primitives such as:

```text
GET_FLAG_BEARER_AGE
```

unless there is a strong generalizable justification.

---

# 6. Data source policy

Use HybridQA only for this phase.

Do not introduce cross-domain data yet.

## Existing historical IDs

Inspect:

```text
data_analysis/week1_sample_100.jsonl
evaluation/week2_eval_ids.json
evaluation/week3_engineering_dev_ids.json
evaluation/week3_locked_eval_ids.json
evaluation/week3_split_manifest.json
```

Create a complete manifest of previously exposed IDs.

Do not silently reuse prior locked-eval IDs as future training data.

## New annotation corpus

Preferred target:

```text
150–200 fresh HybridQA dev questions
```

disjoint from prior locked-eval/test roles.

If local evidence is insufficient:

1. fetch required official table/document sources,
2. pin source commit/version,
3. store exact question/table/document IDs,
4. hash all source artifacts,
5. create a new source manifest.

If 150–200 fresh questions cannot be obtained without major blocking work, begin with:

```text
30-question annotation pilot
```

then expand after schema stabilization.

Do not fabricate missing sources.

---

# 7. Dataset role split

Before annotation begins, assign each new question to a role.

Recommended:

```text
annotation_schema_pilot
annotation_train
annotation_dev
locked_eval
```

Example for 200 fresh questions:

```text
pilot:        30
train:       100
dev:          30
locked_eval:  40
```

This is a recommendation, not a mandatory count.

Requirements:
- zero overlap,
- deterministic allocation,
- machine-readable manifest,
- locked_eval never used for prompt/rubric/operator-vocabulary tuning,
- operator-vocabulary changes after locked scoring require a new evaluation version.

---

# 8. Hierarchical annotation schema

Create a versioned schema.

Suggested top level:

```json
{
  "question_id": "...",
  "question": "...",
  "table_id": "...",

  "semantic_skeleton": {},
  "information_obligations": [],
  "abstract_topology": {},
  "operator_topology": {},
  "grounding": {},
  "execution_graph": {},
  "alternative_plans": [],
  "ambiguity": {},
  "annotation_provenance": {},
  "review_status": {}
}
```

Document every field.

---

# 9. Semantic Skeleton

Candidate fields:

```text
answer_target
answer_type

candidate_structure
candidate_entities_or_variables

relations_required

attributes_required

comparison_requirement
aggregation_requirement
arithmetic_requirement
ordinal_requirement

selection_requirement
back_mapping_requirement

information_dependencies
ambiguity_flags
```

Preserve both:
- source-language span,
- normalized semantic role.

Do not force domain-specific surface relation names into a universal ontology prematurely.

---

# 10. Information Obligations

Represent facts needed to answer the question.

Example:

```json
[
  {
    "obligation_id": "o1",
    "description": "identify the flag bearer associated with event XXXI",
    "depends_on": []
  },
  {
    "obligation_id": "o2",
    "description": "obtain the age or birth date of that flag bearer",
    "depends_on": ["o1"]
  },
  {
    "obligation_id": "o3",
    "description": "compare the two flag bearers",
    "depends_on": ["o2", "o4"]
  }
]
```

These obligations are semantic, not tool-specific.

---

# 11. Abstract semantic topology

Create an environment-independent semantic topology where possible.

Candidate semantic functions:

```text
SELECT_CANDIDATES
RESOLVE_RELATION
ACQUIRE_ATTRIBUTE
COMPARE_VALUES
ARG_SELECT
MAP_BACK_TO_ANSWER
```

Important:

This is NOT automatically the final primitive operator vocabulary.

Its purpose is to support:

```text
Question
-> Semantic Skeleton
-> Semantic Topology
```

as a separate modeling problem.

---

# 12. Environment-aware operator topology

Given:
- question,
- semantic skeleton,
- HybridQA schema,
- linked-document capability,
- candidate operator registry,

annotate the operator topology.

Example:

```json
{
  "nodes": [
    {"id": "t1", "operator": "FILTER", "depends_on": []},
    {"id": "t2", "operator": "PROJECT", "depends_on": ["t1"]},
    {"id": "t3", "operator": "RETRIEVE", "depends_on": ["t2"]},
    {"id": "t4", "operator": "EXTRACT", "depends_on": ["t3"]},
    {"id": "t5", "operator": "COMPARE", "depends_on": ["t4"]},
    {"id": "t6", "operator": "JOIN", "depends_on": ["t1", "t5"]},
    {"id": "t7", "operator": "PROJECT", "depends_on": ["t6"]}
  ]
}
```

At this layer:
- operator is known,
- dependency is known,
- concrete arguments may remain partially ungrounded.

---

# 13. Grounding

For each operator node, record environment-specific bindings.

Structured data:
- table ID,
- column index,
- column label,
- row predicate,
- literal/value,
- join key.

Linked documents:
- entity role,
- link/document locator rule,
- requested attribute,
- declared value type,
- cardinality.

Reasoning:
- comparison relation,
- aggregate function,
- arithmetic function,
- ordering semantics.

Distinguish:

```text
semantic role
```

from:

```text
concrete surface binding
```

---

# 14. Grounded execution graph

Convert resolved annotations into the project's typed execution IR.

Rules:
- preserve historical IR v0.2 files unchanged,
- use v0.2 if sufficient,
- create a new version only when repeated annotation evidence requires it,
- do not alter IR merely for convenience.

Run:
- parse validation,
- operator validation,
- type validation,
- schema validation,
- dependency validation,
- source reachability.

Execution is desirable but not required for every annotation if reader/tool capability is missing.

Execution failure does not automatically mean semantic-plan failure.

---

# 15. Alternative valid plans

Do NOT assume one unique gold graph.

Store:
- representative plan,
- required obligations,
- required dependencies,
- allowed alternatives.

Support:

```text
VALID_ALTERNATIVE_PLAN
```

Do not make exact graph match the primary scientific target.

---

# 16. Annotation workflow

## Stage A — LLM proposal
LLM may propose:
- semantic skeleton,
- obligations,
- topology,
- grounding,
- graph.

Status:

```text
llm_proposed
```

Never `gold`.

## Stage B — deterministic validation
Check:
- schema fields,
- operator names,
- type contracts,
- dependencies,
- graph structure,
- leakage.

## Stage C — human review
Humans correct:
- semantic skeleton,
- obligations,
- operator topology,
- grounding,
- ambiguity,
- alternative valid plans.

Recommended:
- two humans for at least the calibration subset.

If unavailable:
- do not claim gold,
- use truthful statuses such as `human_single_review` or `llm_assisted_pending_human`.

## Stage D — adjudication
For disagreement:
- consensus or third reviewer.

Preserve raw ratings.

---

# 17. Annotation review interface

Do not force raw JSON editing if a simple review UI or packet can reduce errors.

Show:
- question,
- table title/schema,
- relevant environment information,
- linked-document capability,
- LLM-proposed semantic skeleton,
- obligations,
- topology,
- grounding,
- graph visualization.

Reviewer actions:
- accept,
- edit,
- reject,
- ambiguity reason,
- alternative plan.

Where feasible, do not expose:
- final gold answer during semantic/topology annotation,
- old model performance,
- EM/F1,
- old condition identity.

---

# 18. Operator granularity pilot

Before full annotation, use 20–30 pilot questions to compare coarse/medium/fine representations.

Produce:

```text
data_construction/reports/operator_granularity_study_v0_1.md
```

Measure:
- coverage,
- graph length,
- distinct operators/question,
- percentage requiring a new operator,
- annotation disagreement if available,
- examples where coarse hides reasoning,
- examples where fine fragments reasoning excessively.

Do not select granularity solely by coverage.

---

# 19. Operator vocabulary statistics

For each operator report:
- question frequency,
- node frequency,
- input/output types,
- number of semantic contexts,
- number of schemas,
- ambiguity count,
- exceptions,
- evidence that it is reusable rather than question-specific.

---

# 20. Experiments this dataset must enable

## Experiment 1 — Question-only abstraction
```text
Question
-> Semantic Skeleton / Obligations
```

Question:
> How much of the reasoning requirement can language alone determine?

## Experiment 2 — Environment-aware realization
```text
Semantic Skeleton
+ Environment
-> Operator Topology
```

Question:
> How do schema/modality/tool affordances affect execution topology?

## Experiment 3 — Grounding
```text
Operator Topology
+ Schema
-> Grounded Arguments
```

Question:
> Can the correct column/entity/attribute/literal be selected?

## Experiment 4 — End-to-end induction
```text
Question + Environment
-> Grounded Execution Graph
```

## Experiment 5 — Operator granularity
Compare coarse / medium / fine representations.

---

# 21. Direct vs factorized modeling

The dataset must support:

## Direct
```text
Question + Environment
-> Grounded Execution Graph
```

## Factorized
```text
Question
-> Semantic Skeleton
-> Operator Topology
-> Grounding
-> Grounded Execution Graph
```

Key future hypothesis:

> Factorizing semantic topology induction from environment-specific grounding may reduce structurally-valid-but-semantically-wrong plans.

Do not assume this is true before experiments.

---

# 22. Leakage rules

Do not leak later-stage labels into earlier-stage annotation/prediction.

Forbidden examples:
- gold answer,
- gold span,
- old manual graph,
- old semantic label,
- weak answer node,
- evaluator-only document-required flag,
- oracle document ID,
- future-stage grounding while annotating question-only skeleton.

Especially enforce:

```text
Layer 1 annotation/prediction must not see Layer 3/4 gold grounding.
```

---

# 23. Versioning

Use explicit versions:

```text
semantic_schema_v0_1
obligation_schema_v0_1
operator_vocabulary_v0_1
grounding_schema_v0_1
annotation_bundle_v0_1
```

Never overwrite historical Week 1–3 artifacts.

If schema changes after pilot:
- create v0_2,
- write migration notes.

---

# 24. Recommended repository structure

Create a new research area:

```text
data_construction/
  README.md

  manifests/
    historical_exposed_ids.json
    source_manifest_v0_1.json
    split_manifest_v0_1.json

  schemas/
    semantic_skeleton_v0_1.json
    information_obligation_v0_1.json
    abstract_topology_v0_1.json
    operator_topology_v0_1.json
    grounding_v0_1.json
    hierarchical_annotation_v0_1.json

  operator_design/
    operator_vocabulary_coarse_v0_1.json
    operator_vocabulary_medium_v0_1.json
    operator_vocabulary_fine_v0_1.json

  pilot/
    questions.jsonl
    llm_proposals.jsonl
    deterministic_checks.jsonl
    human_reviews/
    resolved_annotations.jsonl

  corpus/
    train.jsonl
    dev.jsonl
    locked_eval.jsonl

  tools/
    build_sample.py
    validate_annotation.py
    compare_operator_granularity.py
    build_review_packet.py
    compute_annotation_stats.py

  reports/
    data_source_audit.md
    annotation_schema_v0_1.md
    operator_granularity_study_v0_1.md
    pilot_annotation_report.md
    corpus_statistics.md
    DATA_CONSTRUCTION_RESEARCH_REPORT.md
```

---

# 25. Immediate execution order

## Phase 0 — Audit
1. inspect Week 1–3 ID manifests,
2. build `historical_exposed_ids.json`,
3. identify forbidden future locked-eval IDs,
4. verify source availability.

## Phase 1 — Schema design
5. define semantic skeleton schema,
6. define information-obligation schema,
7. define abstract-topology schema,
8. define operator-topology schema,
9. define grounding schema,
10. define hierarchical annotation schema.

## Phase 2 — Granularity pilot
11. select 20–30 pilot questions,
12. build coarse/medium/fine candidate representations,
13. quantify trade-offs,
14. choose provisional operator vocabulary,
15. version/freeze it for first corpus pass.

## Phase 3 — Annotation pilot
16. create LLM proposals,
17. run deterministic checks,
18. generate human-review packets,
19. obtain human review if available,
20. resolve disagreements,
21. revise schema only through a new version.

## Phase 4 — Corpus expansion
22. select/fetch 150–200 fresh questions if feasible,
23. freeze split/source manifests,
24. generate proposals,
25. review according to available human resources,
26. build train/dev/locked_eval artifacts.

## Phase 5 — Quality audit
27. compute coverage,
28. compute ambiguity,
29. compute operator statistics,
30. compute graph-length statistics,
31. audit alternative valid plans,
32. audit leakage,
33. write final data-construction report.

---

# 26. Required reports

Produce at minimum:

```text
data_construction/reports/data_source_audit.md
data_construction/reports/annotation_schema_v0_1.md
data_construction/reports/operator_granularity_study_v0_1.md
data_construction/reports/pilot_annotation_report.md
data_construction/reports/corpus_statistics.md
data_construction/reports/DATA_CONSTRUCTION_RESEARCH_REPORT.md
```

---

# 27. Acceptance criteria

The phase is ready for modeling only if:

- [ ] Historical Week 1–3 data are preserved.
- [ ] Previously exposed IDs are explicitly tracked.
- [ ] New corpus roles are disjoint.
- [ ] Semantic skeleton is separated from environment-specific grounding.
- [ ] Information obligations are explicit.
- [ ] Operator topology is separated from concrete grounding.
- [ ] Grounded execution graph is machine-validatable.
- [ ] Alternative valid plans can be represented.
- [ ] Exact graph match is not assumed to be the only correct target.
- [ ] Operator granularity has been empirically piloted.
- [ ] Question-specific pseudo-operators are rejected or justified.
- [ ] LLM proposals are not labeled gold.
- [ ] Human-review status is machine-readable and truthful.
- [ ] Leakage between layers is tested.
- [ ] Source/document manifests are reproducible.
- [ ] Corpus statistics are generated from raw artifacts.
- [ ] Locked evaluation is untouched during tuning.
- [ ] Negative and ambiguous cases are preserved.

---

# 28. Scientific cautions

## Do not overclaim the operator vocabulary
The final operator set is an empirical design choice, not a universal algebra.

## Do not assume syntax determines reasoning
Surface patterns such as:

```text
"A와 B 중 더 X한 Y를 가진 Z는?"
```

may be useful signals, but annotation targets should be semantic structures, not Korean syntactic templates alone.

## Do not conflate semantic topology with physical execution
The same semantic skeleton may compile differently under different environments.

## Do not treat execution failure as semantic-plan failure
A semantically correct graph can fail because of reader/retriever/tool limitations.

## Do not force a unique graph
Multiple execution plans may be valid.

## Do not let the current IR dictate the data
If repeated annotation evidence exposes an IR limitation, document it separately.

---

# 29. Final research questions for this reset phase

At the end of data construction, answer:

> Can HybridQA questions be annotated with a stable hierarchical representation that separates question-level semantic obligations, environment-aware operator topology, and schema-specific grounding well enough to support controlled experiments on semantic execution-graph induction?

And:

> What primitive-operator granularity provides the best trade-off among coverage, compositionality, annotation stability, execution transparency, and planning complexity?

Do not assume either answer is positive.

---

# 30. Final Codex decision

Choose one:

```text
READY_FOR_FACTORIZED_MODELING
REVISE_ANNOTATION_SCHEMA
REVISE_OPERATOR_VOCABULARY
NEED_MORE_HUMAN_REVIEW
DATA_SOURCE_BLOCKED
STOP_OR_REFRAME
```

The priority of this phase is dataset validity and conceptual separation, not model performance.

---

# 31. Multi-device Codex continuity and environment-sharing contract

The user intends to continue this same Codex research project across multiple computers.

The project must therefore be designed so that **Desktop 1 and Desktop 2 can reconstruct the same research state from the repository**, without relying on a specific Codex chat session, local stash, or local-only working directory.

The continuity model is:

```text
Desktop 1 Codex
    ↓
repository files + commits
    ↓
Git remote
    ↓
repository files + commits
    ↓
Desktop 2 Codex
```

Do not assume that local Codex conversation state, uncommitted files, stashes, caches, virtual environments, model downloads, or machine-local secrets are automatically synchronized.

## 31.1 Source of truth

Use the following priority for cross-device continuity:

```text
1. Git commit history and remote branch
2. committed research manifests / configs / schemas / reports
3. committed AGENTS.md and portable project instructions
4. environment lockfiles and reproducible bootstrap scripts
5. machine-local secrets and caches
6. Codex conversational memory
```

Conversational memory is never the canonical project state.

## 31.2 Git repository requirements

Audit whether the project root is currently a Git repository.

If it is not, do **not** silently destroy or rewrite files. Prepare a Git initialization/migration plan and record:

```text
REQUIRES_RESEARCHER_DECISION
```

for remote-provider/repository-visibility choices.

If a Git repository already exists, record:

```text
git root
current branch
HEAD commit
remote(s)
working-tree status
untracked files
unpushed commits if determinable
```

Create:

```text
reports/cross_device_repo_audit.md
```

Never assume a local Git stash can be accessed from another computer.

For work that must move to another machine, prefer a WIP commit over a stash:

```text
git add <intended files>
git commit -m "wip: <concise handoff state>"
```

Do not automatically push to a remote unless remote writes are already authorized for this project/session. If push authorization is unavailable, prepare the local commit and report:

```text
BLOCKED_REMOTE_AUTH
```

with the exact branch and commit hash that need to be pushed.

## 31.3 Branch policy

For sequential work across Desktop 1 and Desktop 2, use the same named research branch only when the previous machine has committed and pushed all intended changes.

Suggested branch for this reset phase:

```text
research/semantic-topology-data-v1
```

If both desktops may work concurrently, do not make simultaneous uncoordinated commits on the same branch.

Use per-task branches such as:

```text
research/data-schema-v1
research/operator-granularity-v1
research/annotation-pilot-v1
```

and merge through an explicit integration branch or reviewed merge.

Record the active branch in the handoff artifact.

## 31.4 Portable project instructions

Create or update a repository-root:

```text
AGENTS.md
```

It should be committed to Git and contain only portable project-level instructions.

Minimum content:

```text
Project purpose
Current scientific scope
Historical Week 1–3 preservation rule
Current phase
Canonical commands
Test commands
Important artifact paths
Leakage rules
Versioning rules
Locked-eval rules
Cross-device startup procedure
Cross-device shutdown/handoff procedure
```

Do not put secrets, passwords, tokens, personally identifying values, or machine-specific absolute paths in `AGENTS.md`.

If the repository already has `AGENTS.md`, preserve unrelated valid instructions and update it carefully rather than replacing it wholesale.

If a portable project-level Codex config is already used, inspect:

```text
.codex/config.toml
```

Keep only settings that are:
- safe to commit,
- non-secret,
- project-specific,
- portable across machines.

Do not commit user-level credentials or machine-specific authentication material.

User/global Codex settings remain machine-local unless the user separately manages them through private dotfiles.

## 31.5 Cross-device handoff artifact

Create a concise machine-readable and human-readable current-state handoff.

Recommended:

```text
HANDOFF_CURRENT.md
state/project_state.json
```

`HANDOFF_CURRENT.md` should contain:

```text
Project:
Current research phase:
Current branch:
Expected HEAD commit:
Last completed task:
Current scientific decision:
Blocked gates:
Next exact task:
Required files to read:
Commands to reproduce current checks:
Known machine-local dependencies:
Known non-portable resources:
Do-not-modify historical paths:
```

`state/project_state.json` should contain at minimum:

```json
{
  "schema_version": "project_state_v0_1",
  "active_phase": "...",
  "active_branch": "...",
  "expected_head": "...",
  "last_completed_task": "...",
  "next_task": "...",
  "blocked_gates": [],
  "canonical_artifacts": [],
  "historical_read_only_paths": [],
  "environment_contract": {}
}
```

Do not make the JSON depend on a Desktop 1 absolute path.

## 31.6 Environment reproducibility

The second desktop must be able to reconstruct the development environment without copying the entire local virtual environment.

Audit and standardize the Python environment.

Prefer project-controlled files such as:

```text
pyproject.toml
requirements.txt
requirements-lock.txt
uv.lock
.python-version
```

Use whichever dependency-management approach the repository already uses; do not introduce multiple competing package managers without need.

Record the exact Python version expected.

If the project depends on:
- Java,
- Neo4j,
- Docker,
- system libraries,
- model runtimes,
- GPU drivers,
- external binaries,

document versions and bootstrap commands in:

```text
ENVIRONMENT.md
```

If a Dev Container or Docker environment already exists, preserve and improve it.

Do not require Docker merely for cross-device portability if the existing Python environment can be reproduced cleanly with a lockfile.

## 31.7 Machine-local resources

The following should normally NOT be committed:

```text
.venv/
venv/
__pycache__/
model caches
Hugging Face caches
temporary experiment caches
large generated checkpoints unless explicitly versioned elsewhere
.env
.env.local
API tokens
SSH keys
Codex authentication state
OS keychain contents
```

Ensure `.gitignore` reflects the actual project.

For each non-portable dependency, document how Desktop 2 recreates or reacquires it.

Example:

```text
Resource:
Qwen2.5-0.5B-Instruct snapshot

Portable identity:
model ID + exact revision

Machine-local object:
local model cache

Desktop 2 action:
download/cache the same model revision before reproducing the run
```

## 31.8 Secrets

Never commit secrets.

Provide safe templates such as:

```text
.env.example
```

with names only:

```text
OPENAI_API_KEY=
HF_TOKEN=
...
```

Do not place real values in the repository.

If a secret is required on both desktops, mark:

```text
MACHINE_LOCAL_SECRET_REQUIRED
```

and document only the variable name and purpose.

## 31.9 Research artifact portability

Every important research result should be reconstructable from committed or explicitly externalized artifacts.

For each experiment or annotation run, save:

```text
config
question IDs
source manifest
schema/operator version
model ID/revision
seed
raw outputs
result summary
code commit hash
artifact hashes
status: complete / incomplete / blocked / planned_not_run
```

Avoid storing only prose summaries.

If artifacts are too large for normal Git:
- do not put them into an ad-hoc cloud-synced folder,
- define a deliberate external artifact strategy,
- store content hashes and retrieval instructions in the repository.

Possible external storage choices require researcher approval.

## 31.10 Do not use consumer folder sync as repository coordination

Do not make OneDrive, Dropbox, iCloud Drive, or similar filesystem synchronization the primary synchronization mechanism for the active Git working tree.

Reason:
- Git metadata can race with sync,
- generated files can conflict,
- virtual environments and caches are non-portable,
- two machines may edit the same working tree state indirectly.

Use:

```text
Git for source/research state
secret manager or machine-local env for secrets
lockfiles/bootstrap scripts for environment
explicit artifact storage for large outputs
```

## 31.11 Desktop startup protocol

Whenever Codex starts on a different desktop, do not immediately modify files.

First run the equivalent of:

```text
1. locate repository root
2. read AGENTS.md
3. read HANDOFF_CURRENT.md
4. read state/project_state.json
5. inspect git status
6. inspect current branch and HEAD
7. inspect remote configuration
8. fetch remote if network/auth is available and authorized
9. compare local HEAD to expected handoff HEAD
10. run a lightweight integrity/smoke check
```

Before pulling/merging, protect local uncommitted work.

If the working tree is dirty and changes are not clearly disposable:

```text
STOP_AND_REPORT_LOCAL_CHANGES
```

Do not overwrite them automatically.

If local and remote branches diverged:

```text
STOP_AND_REPORT_BRANCH_DIVERGENCE
```

Do not silently force-push, hard-reset, or discard commits.

## 31.12 Desktop shutdown/handoff protocol

Before ending a work session intended to continue elsewhere:

```text
1. run relevant tests/checks
2. update HANDOFF_CURRENT.md
3. update state/project_state.json
4. update research decision/status artifacts
5. verify no secret files are staged
6. inspect git diff
7. commit intended portable changes
8. record commit hash
9. push only when authorized
10. report whether remote is synchronized
```

Use explicit end states:

```text
SYNCED_TO_REMOTE
LOCAL_COMMIT_NOT_PUSHED
BLOCKED_REMOTE_AUTH
DIRTY_WORKTREE_NOT_HANDOFF_READY
```

The next computer must not assume synchronization unless the state is `SYNCED_TO_REMOTE`.

## 31.13 Cross-device reproducibility check

Create a script or documented procedure such as:

```text
scripts/bootstrap_check.py
```

or:

```text
scripts/cross_device_preflight.sh
```

that checks, where practical:

```text
Python version
required dependency files
required dataset/source manifests
expected historical artifact paths
model IDs/revisions
operator/schema versions
test entry points
Git commit identity
```

Do not make the check depend on the original machine hostname.

## 31.14 Add these deliverables to the current reset phase

In addition to the data-construction artifacts, create:

```text
AGENTS.md
HANDOFF_CURRENT.md
ENVIRONMENT.md
state/project_state.json
reports/cross_device_repo_audit.md
scripts/cross_device_preflight.sh
```

or equivalent repository-native names if existing conventions differ.

If `.codex/config.toml` already exists, audit it for portability and secrets.

If it does not exist, do not create one merely for appearance; create it only if project-level Codex configuration is actually needed.

## 31.15 Multi-device acceptance criteria

Add these acceptance criteria:

- [ ] The project can be cloned to a second directory without relying on the Desktop 1 absolute path.
- [ ] `AGENTS.md` contains the current portable research instructions.
- [ ] Current phase/next task is recorded in a committed handoff artifact.
- [ ] Git branch and expected HEAD commit are recorded.
- [ ] Machine-local secrets are excluded from version control.
- [ ] Python/dependency versions are reproducible from repository files.
- [ ] Model/cache dependencies are identified by stable IDs/revisions rather than local cache paths.
- [ ] Historical Week 1–3 artifacts remain protected.
- [ ] Cross-device preflight identifies missing dependencies before research runs.
- [ ] No Git stash is required to resume the project on another machine.
- [ ] No active repository coordination depends on OneDrive/Dropbox/iCloud filesystem sync.
- [ ] The handoff state distinguishes local-only commit from remotely synchronized commit.
- [ ] Codex on Desktop 2 can read repository instructions and reconstruct the next task without relying on the previous chat session.

---

# 32. Updated immediate execution order

The earlier data-construction execution order remains valid, but prepend the following portability phase.

## Phase -1 — Cross-device project continuity

1. locate and audit the current Git/project root,
2. inspect Git status/branch/remotes,
3. create `reports/cross_device_repo_audit.md`,
4. create/update portable `AGENTS.md`,
5. create `HANDOFF_CURRENT.md`,
6. create `state/project_state.json`,
7. audit `.gitignore`,
8. audit dependency/lock files,
9. write `ENVIRONMENT.md`,
10. create a cross-device preflight command/script,
11. verify no secrets or machine-local absolute paths are being newly committed,
12. record the active research branch and current commit.

Then proceed with the existing:

```text
Phase 0 — historical ID/source audit
Phase 1 — annotation schema design
Phase 2 — operator granularity pilot
Phase 3 — annotation pilot
Phase 4 — corpus expansion
Phase 5 — quality audit
```

At the end of every major phase, update the cross-device handoff artifacts.

---

# 33. Updated final Codex decision

In addition to the scientific decision:

```text
READY_FOR_FACTORIZED_MODELING
REVISE_ANNOTATION_SCHEMA
REVISE_OPERATOR_VOCABULARY
NEED_MORE_HUMAN_REVIEW
DATA_SOURCE_BLOCKED
STOP_OR_REFRAME
```

report one synchronization state:

```text
SYNCED_TO_REMOTE
LOCAL_COMMIT_NOT_PUSHED
BLOCKED_REMOTE_AUTH
DIRTY_WORKTREE_NOT_HANDOFF_READY
REMOTE_NOT_CONFIGURED
```

A phase is not considered ready for transfer to Desktop 2 unless the repository state needed for continuation is committed and the synchronization state is explicitly reported.

