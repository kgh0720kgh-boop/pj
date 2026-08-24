# Post-hoc partition-sensitivity addendum v0.1

This addendum is a separately versioned, post-hoc sensitivity audit. It does not modify or replace the frozen contract, extractor, raw records, primary metrics, primary report, or precommitted decision.

## Decision preservation

The precommitted decision remains `EXPAND_UNCHANGED_TO_N300`. It is retained as a **conservative operational decision**. Evidence that the recurring families constitute semantic novelty is **partition-confounded and not cross-partition confirmed**.

## Partition profiles

| Partition | Positions | Records | Uncertain | Uncertain rate | Mean nodes | Uppercase node-description rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| partition_01 | 1–34 | 34 | 5 | 0.147 | 2.294 | 0.000 |
| partition_02 | 35–67 | 33 | 14 | 0.424 | 2.818 | 0.000 |
| partition_03 | 68–100 | 33 | 10 | 0.303 | 2.364 | 1.000 |

The first 30 contract-development questions occur only in `partition_01`; most of the new 70 occur in `partition_02` and `partition_03`. Consequently, new-question transfer and producer-context style are not separated by this run.

## Recurring new contracted families

- First-30-unobserved families recurring at least twice in the new 70: 5
- Those supported by more than one producer partition: 0

| Signature | Questions | Partition support | Question IDs |
| --- | ---: | --- | --- |
| `5e9aa48abfbb14ad807bc3fcc27c3407f2a41dfd6566918dce771f4dab221043` | 2 | `{"partition_03": 2}` | `ad20a4c31ba3dba9`, `27432f264c71480d` |
| `9c3a199eb9e135238922193e4aff4619bfecf99b8ab4994417bd2a10ddf285fc` | 3 | `{"partition_02": 3}` | `f6f09ec02eaa8bb8`, `411562d9ce68b1e8`, `5456c7ee3ac9281a` |
| `ab012c4eaf2773e1f22643f4cca44614e2146efdf0ff0c6fbb6b20fcf7038527` | 4 | `{"partition_03": 4}` | `b99fc5c636ea823c`, `a5cf7ceed7e24ed8`, `6c164eb418d88e42`, `b45751302b0495f9` |
| `b2c5d7fa38b1fd45d360cb479ee059feedcb916901cfa00c06668790c56afc42` | 4 | `{"partition_02": 4}` | `016665beb450ca4e`, `c11b0740b1084da0`, `21148417ac3a50ca`, `846fc6ee43ca7f7d` |
| `cc5563db35f61786e62157f92e0b4043f6b462759175b3a754e25a255a6651cf` | 2 | `{"partition_03": 2}` | `2f8484f7e3324d0e`, `7fdc558f6b822b6a` |

The cross-partition recurrence count is a post-hoc sensitivity diagnostic, not a replacement decision rule. A zero value means the primary trigger is not independently reproduced across producer contexts in this run.

## Raw versus transitive-reduced graph profile

| Dependency view | Mean edges | Branch questions | Join questions |
| --- | ---: | ---: | ---: |
| Raw declared | 1.540 | 5 | 6 |
| Transitive reduced | 1.490 | 0 | 1 |

Transitive reduction removes 5 edges from 5 questions. Raw branch/join counts therefore must not be presented as normalized topology counts.

## Fine-to-contracted dominant-family sensitivity

- Fine dominant family: 46 questions (0.460)
- Contracted dominant family: 62 questions (0.620)
- Increase after same-role linear contraction: 16 questions (0.160 of N)

Same-role contraction is a deterministic split/merge sensitivity view; it does not establish that distinct referential hops are semantically equivalent. Fine and contracted results must be reported together.

## Interpretation boundary

This audit supports a reproducible description of partition sensitivity and graph-normalization sensitivity only. It does not establish semantic correctness, prove that every partition difference is caused by worker style, overturn the frozen primary decision, or create human/gold evidence.
