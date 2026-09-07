# Narrowed-grounding collection v0.1: input-isolation failure

Date: 2026-09-07

Frozen decision: `STOP_TECHNICAL_OR_LEAKAGE_FAILURE`.

## Outcome

Six complete question packets were committed before authoring. Six distinct
new author tasks were then dispatched in frozen question order with
`fork_context=false` and no model override. Each was allowed only its own
packet, the protocol, author guide and raw schema, and one write to its own
raw response path. No coordinator manifest or other author's output was sent.

Nevertheless, all six authors reported that excluded prior-research summaries
had been supplied in their initial context. They recorded `known_exposed`,
describing AGENTS/project instructions containing previous study results or
decisions. Therefore the fresh-context option did not establish the required
research-input isolation. The author reports establish the observed failure;
the entire hidden platform prompt is not available for independent auditing.

All six sole structured responses were preserved without repair and matched
the file hashes reported by their authors. No semantic feedback, post-output
retry, relabeling or rerun took place. Every raw file parses and passes the
closed response schema, but the frozen validator rejects prior exposure before
evaluating candidate bindings.

| Signal | Result |
| --- | ---: |
| Packets / received raw files | 6 / 6 |
| Raw parse / schema passes | 6 / 6 |
| Author contexts reporting prior exposure | 6 / 6 |
| Fixed source candidates / slots / operator nodes | 14 / 52 / 43 |
| Accepted canonical grounding records | 0 / 14 |
| Prior-exposure gate errors | 6 |
| Execution / answer recovery / human evidence | 0 / 0 / 0 |

The scientific branch is a leakage failure, not semantic impossibility,
grounding inaccuracy, missing pinned source, or successful static grounding.
All source candidate/slot/node units receive `technical_invalid` because no
submission passes the prior-exposure gate. The empty canonical records file
is a legitimate derived result, not an invented missing response. Original
raw bytes and parsed payloads remain in the raw files and audit checks.
Zero accepted-alternative counts refer only to the empty accepted set; they
must not be interpreted as zero authored alternatives or proof of retention
across every possible semantic alternative.

## Immutable provenance

1. Runtime implementation: `2983168f48689e8e7129a9bdecde4787a4ecb8cf`.
2. Output-absent runtime receipt: `6c7487beddb03625b9fd23ef7514eebe307d397b`.
3. Six packets and coordinator manifest: `861b3cfd69fd622cfc67faaa7856f7e60f8ac872`.
4. Dispatch receipt: `0a44cbcc6825e9ef781999c911533163b24a9860`.
5. Six original raw responses: `af8d2a2723137a94ee44706f17a7b96fb50fe2a8`.
6. Seven analysis outputs: `3035317c9930b03b5c1b6be3e09b9c343e7ac439`.

The dispatch receipt is `state/narrowed_grounding_author_dispatch_v0_1.json`.
It records exact task/context identities and input hashes; it does not claim
the dispatch mechanism suppressed every automatic context source. All twenty
planned outputs now exist under the original run namespace. No old source,
normalization, instrument, schema, runtime or historical artifact was changed.

Authors reported GPT-6/Codex model identities in their original strings.
Those are self-reported runtime identities, not authenticated backend model
revisions. Exact revision and seed remain unavailable. The saved JSON is the
primary structured capture; neither hidden reasoning nor a backend raw stream
is represented as captured.

## Interface observation, separate from the failure gate

Two authors also noted that packet `protocol_sha256` differs from the hash of
the separately named protocol file. The frozen builder assigns that field the
author-guide hash. The protocol itself is transitively bound through the plan
and runtime receipt, and both source files retain their pinned bytes. This is
a field-naming ambiguity, not source/hash corruption. No v0.1 field or output
was repaired in response to the observation. The actual six frozen errors are
all `grounding context prior exposure not cleared`.

## Validation boundary and next exact task

`narrowed_grounding_runtime_v0_1.py --validate-results` reconstructs the seven
result files exactly, including the failure branch. Three post-collection
integrity regressions cover non-promotion of exposed raw, dispatch/first-capture
hashes and historical-versus-current output absence. These are later audit
tests, not retroactively added evidence for the frozen pre-run instrument.
Latest full-suite/preflight counts are in the current handoff and project state.

Before any new research authoring, design and freeze a separately versioned
input-delivery/isolation contract. It must verify the actual initial context
before question packets are delivered, account for automatic project/AGENTS
injection, and stop if excluded research information is present. Probe the
transport without fresh/locked research questions. Clarify protocol/guide
identity fields in a new version. Do not use exposed binding content to tune
semantic rules, quietly clear prior-exposure flags, or reuse these responses
as clean grounding observations. Preserve this v0.1 run byte-for-byte.

No execution plan, graph execution, answer recovery, corpus allocation, final
vocabulary, semantic gold, population estimate or modeling readiness follows
from this run. The next work is isolation-contract design, not another attempt
through the same unverified authoring channel. No fetch or push was performed.
