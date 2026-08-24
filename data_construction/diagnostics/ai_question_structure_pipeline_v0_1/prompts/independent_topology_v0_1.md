# Independent topology-only AI prompt v0.1

Work in a fresh AI context on only the supplied question-only records and this
prompt. Do not inspect reviewer annotations, skeletons, obligations, alignments,
environment data, answers, operator proposals, or repository files. Do not
browse or look up answers.

For each supplied shadow hold-out question, express the minimal storage-neutral
semantic dependency DAG needed to answer it. Nodes use free-text operation
descriptions, not an operator vocabulary. Do not include or refer to upstream
skeleton/obligation content or IDs. All source cues must be exact substrings of
the question, with an implicit rationale when no cue is explicit. Entry IDs are
exactly all roots and output IDs exactly all sinks. This is an AI diagnostic
topology, not an executable graph, gold plan, grounding, or execution evidence.
