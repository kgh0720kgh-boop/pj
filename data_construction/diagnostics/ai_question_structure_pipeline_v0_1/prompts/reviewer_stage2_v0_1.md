# AI diagnostic reviewer stage 2 prompt v0.1

Continue only from your own frozen stage-1 records, the exact question-only
views, this prompt, and the frozen annotation schema. Do not inspect any other
reviewer's output, alignment, environment, answer, execution trace, historical
graph, operator proposal, or granularity artifact. Do not browse or look up the
answer.

For every question, preserve the stage-1 observation exactly as
`unconstrained_question_paraphrase`, then encode a storage-neutral linked
representation:

- `semantic_skeleton`: requested answer, answer shape, candidate set, required
  information units, selection requirement, and back-mapping requirement;
- `information_obligations`: the facts or decisions needed, with dependencies;
- `abstract_topology`: free-text semantic operations and their dependencies,
  linked to obligations but not to an executable operator vocabulary;
- visible ambiguity and valid alternative topology plans; and
- a truthful representation assessment and instrument issues.

Use local IDs consistently. All dependency graphs must be acyclic; entry IDs
must be exactly all roots and output IDs exactly all sinks. Every primary
obligation must be fulfilled by at least one primary topology node. `source_cues`
must be exact, case-sensitive substrings from the question; when no explicit cue
exists, use an empty array and a nonempty `implicit_rationale`. Never include a
factual answer. This output is AI-generated, non-human, non-gold, and has no
effect on any scientific phase gate.
