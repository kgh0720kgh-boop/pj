# Grounding author interface v0.1

Read only your assigned packet, this guide, the frozen grounding protocol and
the raw response schema. Use a new context for this question. Do not inspect
other questions, coordinator manifests, prior results, official answers,
traces, historical artifacts, or other authors' outputs. Ground every opaque
observation in your packet separately. These are AI proposals, not gold.

Return one JSON object conforming to `narrowed_grounding_raw_schema_v0_1.json`.
Copy packet ID, question ID, packet `payload_sha256` into `packet_sha256`,
environment hash, and each candidate hash exactly. The raw response is kept
unchanged. There is one submission and no semantic repair round.

If input delivery is incomplete, say so and mark all slots and operators
`abstained`, giving a reason; do not infer missing source contents. Record your
actual model/context provenance, explicit unavailable revision/seed fields,
raw capture limitations, and all transport attempts. Only a no-output transport
failure may precede the sole delivered response. Prior-exposure clearance is
a procedural attestation, not proof of cognitive independence.

For each observation enumerate all identified coherent alternatives, with
unique IDs. `identified_alternative_ids` must exactly equal the emitted set.
Use relationship `single` for one, `compatible` for interchangeable alternatives,
or `incompatible` for unresolved competing interpretations. Explain each
multiple-alternative assumption. Incompatible choices remain ambiguous even
if every locator can be found. Do not drop alternatives to improve coverage.

Each alternative must account for all original slot IDs and operator node IDs
exactly once. Do not return a rewritten graph. Slots use `resolved`,
`ambiguous`, `unavailable`, or `abstained`. Operators use `specified`,
`ambiguous`, `unavailable`, or `abstained`. Unresolved entries require reasons.
Unavailable slots require `searched_scope` pointers. A resolved slot has a
nonempty `bindings` list and null reason. An operator with no extra parameters
must explicitly set `no_additional_arguments=true` and explain why.

Each binding has `view_sha256` equal to the packet environment hash and a
declared `value_type`. Keep the source slot cardinality; it describes eventual
runtime values, not how many candidate source locations exist. State role,
type and assumptions honestly; deterministic validation does not certify their
semantic truth.

Pointer coordinates are relative to the packet's `environment` object, whose
entire contents are copied from the pinned sanitized view. Use RFC 6901 escapes
(`~0` for tilde, `~1` for slash); array indexes are zero-based. These coordinates
and hashes bind back to the original view in the coordinator manifest.

Supported bindings:

- `table_column`: `/columns/N`, table ID, index, exact label.
- `table_scope`: whole table (`""`), `/rows`, `/columns`, `/title`, or
  `/section_title`. Do not enumerate filtered rows or compute their values.
- `cell_link`: an exact `/columns/N/linked_document_ids` or
  `/rows/R/cells/C/linked_document_ids` collection, with a follow rule and
  entity association.
- `linked_document`: a whole `/linked_documents/D` object, exact document ID,
  its originating cell/header link collection, requested attribute, and entity
  association. Do not extract or quote an answer span.
- `dynamic`: a whole source collection or column `scope`, a symbolic selector,
  strict upstream node IDs and/or exact question spans, entity association,
  and a link scope/requested attribute for document requests. `link_scope`
  denotes a table row/column collection whose links will be followed later.
  These are unevaluated rules, not retrieved values.
- `question_literal`: exact half-open Unicode codepoint `start`, `end`,
  `literal` from the question. The codepoint count is not a UTF-8 byte offset.
- `source_literal`: a scalar pointer used only as an operator parameter,
  `purpose=operator_parameter`, and a rationale. Do not copy the value into
  the response or use it to encode an extracted answer.
- `derived`: symbolic function, ordered node/slot operands, units and tie/null
  policy. Node operands must be strict upstream outputs, and slot operands
  must belong to the consuming operator. No computed result is returned.

For a locator depending on an earlier result, give the dynamic rule rather
than manually computing its entity, row set, attribute value, or answer. A
dynamic document request needs a source link scope, requested attribute, and
entity association; a generic document placeholder is insufficient.

Do not run any graph operation: retrieval, extraction, filtering, comparison,
aggregation, arithmetic, or answer projection. Existing candidate operation
descriptions and their physical boundaries remain unchanged. Any suspected
semantic defect is recorded as an unresolved disposition/limitation, not an
upstream correction. No final answer or execution result is requested.
