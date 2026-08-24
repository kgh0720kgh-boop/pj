# Environment-realization outcome v0.1 to v0.2 migration

Date: 2026-08-25

## Preservation decision

`environment_realization_outcome_schema_v0_1.json` is preserved byte-for-byte.
It was committed as a future five-signal scaffold before any representative
environment-realization outcome records existed. It is not rewritten or
silently reinterpreted.

The representative environment-realization protocol exposed two distinctions
that the v0.1 scaffold could not record without misleading field semantics:

1. the run uses an open, record-local operator notation and does not select an
   operator vocabulary; and
2. a realization candidate targets one particular primary or alternative
   backbone variant, so unsupported nodes and availability must remain
   variant-qualified.

Version v0.2 is therefore a new contract, not an in-place correction to v0.1.
No v0.1 outcome record is migrated because actual v0.1 outcome records remain
zero at this decision point.

New record identifiers use the `environment_outcome_v0_2:{question_id}`
namespace. Because no v0.1 records exist, there is no prior record identity to
preserve or alias.

## Field migration

Within `environment_operator_realization`:

| v0.1 | v0.2 | Reason |
| --- | --- | --- |
| `realization_available` | `complete_realization_available` | Distinguishes a complete ungrounded topology from the existence of a partial proposal. |
| `operator_vocabulary_version` | `operator_notation_id` | An open record-local notation is not a selected cross-record vocabulary. |
| implicit vocabulary selection state | `final_operator_vocabulary_selected: false` | Makes the non-selection claim explicit and schema-enforced. |
| `unsupported_backbone_node_indices` | `variant_realization_results[].blocking_unsupported_node_ids` | Preserves primary/alternative variant identity and stable node IDs. For a partial variant this compact field contains only nodes unsupported by every partial candidate; each candidate retains its complete local unsupported list. |
| no candidate summary | `realization_candidate_count` | Records how many candidate topologies were authored. |
| free-text unresolved summary | `unresolved_issue_count` plus bounded `notes` | Avoids deriving an unbounded joined string while retaining a compact summary. |

For any evaluated operator-realization status (`pass`, `partial`, `fail`, or
`indeterminate`), v0.2 requires `realization_record_id`. Failed or
indeterminate assessment does not erase the record that supports it.

## Independence wording

The v0.1 aggregate statement that all signals are independently scored could
be mistaken for statistical or cognitive author independence. Version v0.2
separates these claims:

- all five signal fields are required;
- evaluated signal values are scored separately and remain logically
  non-deriving;
- no statistical author independence is claimed; and
- cognitive independence is not machine-authenticated.

Execution success or failure, answer recovery, and later downstream failures
still cannot overwrite or imply an upstream semantic judgment.

## Status compatibility

Version v0.2 retains the shared assessment-status vocabulary
(`not_evaluated`, `pass`, `partial`, `fail`, `indeterminate`, and
`not_applicable`) so all five signals remain comparable at the lifecycle
level. For the operator signal, those values mean only:

- `pass`: at least one complete, ungrounded candidate topology was authored;
- `partial`: candidates were authored but none completely covers its target
  variant;
- `fail`: no candidate topology was available and the variant results are
  unavailable; or
- `indeterminate`: the authoring input did not support a defensible result.

They do not mean grounded correctness, executability, answer accuracy, a gold
program, or selection of a final operator ontology.

## Implementation requirement

New representative environment-realization records must bind
`environment_realization_outcome_schema_v0_2.json`. Any tool consuming the
older schema must select v0.1 explicitly; it must not coerce v0.2 notation IDs
into the v0.1 vocabulary field or discard variant-qualified results.

The v0.2 schema rejects duplicate variant identifiers and binds notation
presence to a nonzero candidate count. The producing/validation tool also
checks the cross-item invariant that `realization_candidate_count` equals the
sum of all variant-level `candidate_count` values; JSON Schema cannot express
that arithmetic equality directly.
