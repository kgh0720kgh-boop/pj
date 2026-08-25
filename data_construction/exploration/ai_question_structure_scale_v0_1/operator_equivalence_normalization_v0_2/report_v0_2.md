# Operator equivalence normalization v0.2

This deterministic revision uses only the already exposed 93 original and
34 crossed-author candidates. It separates full semantic-set eligibility
from candidate-sensitive semantic identity and factors adapters without
using question/environment text, answers, traces, grounding, or execution.

## Eligibility and integrity

- candidates: 127
- full eligible: 121
- provisional only: 1
- ineligible: 5
- reversible projection loss: 0
- eligible-set contamination: 0
- unclassified adapter candidates: 0

## Crossed-author semantic comparison

- full-eligible semantic-set exact match: 10/16
- mean full-eligible semantic-set Jaccard: 0.656250
- author-question pairs with a full-eligible candidate: 27/32

## Crossed-author adapter components

- modality_cardinality: exact 0/16, mean Jaccard 0.000000
- semantic_relative_placement: exact 7/16, mean Jaccard 0.437500
- split_fuse_boundary: exact 9/16, mean Jaccard 0.562500
- output_arity: exact 10/16, mean Jaccard 0.656250

## Frozen branch result

`NARROW_OR_REAUTHOR_BEFORE_GROUNDING`

Grounding was not performed. Producer concentration is descriptive and
does not establish causal producer effects or semantic correctness.
