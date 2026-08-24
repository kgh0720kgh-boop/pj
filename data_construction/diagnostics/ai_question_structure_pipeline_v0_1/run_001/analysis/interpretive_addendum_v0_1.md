# Interpretive addendum for AI shadow-pipeline run 001

Evidence class: non-evidentiary AI diagnostic; non-human; non-gold

Primary metrics artifact: `metrics_v0_1.json`, SHA-256
`ce354643f2e2e6ebb56ecd793d13b4cfdeac2fb4da3aacc41dc1655c2ee2bd67`

This addendum makes distinctions that the compact generated report intentionally
does not collapse into a phase gate.

## What worked mechanically

- Both reviewer lanes completed 30 frozen stage-1 observations and 30 structured
  records. All 120 stage records passed their applicable schema, view-hash,
  stage binding, source-cue, reference, root/sink, obligation-coverage, and DAG
  checks.
- The identity-blinded alignment covered every required-information-unit,
  obligation, and primary topology-node ID exactly once. There were no unmatched
  items and no conflict or partial-overlap groups in those three core layers.
- Ten questions were classified `FULL_EQUIVALENCE`; twenty were classified
  `COMPATIBLE_VARIATION`. The calibration and shadow-hold-out primary topology
  crosswalks both had mean direct-edge and reachability Dice of 1.0.
- For question `8259c70c392c5b75`, both reviewers independently produced the
  same two-stage semantic dependency: identify the museum satisfying the Harvest
  Vision ownership condition, then obtain the selected museum's summary. It was
  classified `FULL_EQUIVALENCE`.

These observations show that the mechanics can preserve and compare linked
question-only representations. They do not establish that the representations
are correct or that a common executable graph exists.

## Variation that the headline compatibility rate hides

- The ambiguity-present flags matched on 25/30 questions (0.8333).
- The presence of alternative plans matched on 20/30 questions (0.6667).
- The blinded aligner marked 13 ambiguity components as partial overlap, 11
  alternative-plan components as partial overlap, and two alternative-plan
  components as substantive conflict. It also marked three answer-shape
  components as partial overlap.
- The two alternative-plan conflicts were questions `d8b4bad4f5a73509` and
  `fc9605cb355ae05c`.

The frozen v0.1 disposition rule treats scalar-component conflict as compatible
variation unless a material conflict or unmatched item occurs in a grouped core
layer. Therefore the reported 1.0 `compatible_or_full_question_rate` must not be
read as “zero conflict.” A later alignment contract should add explicit impact
to scalar component decisions or define their materiality before human results
are interpreted. The v0.1 result is preserved rather than silently recomputed.

## Strong reviewer sensitivity in instrument-issue reporting

- Reviewer 1 recorded 19 instrument issues: 17 `rubric_unclear` and two
  `multiple_equally_valid_encodings`; severity was ten major, eight minor, and
  one critical. Four occurred in the ten-question calibration slice and fifteen
  in the twenty-question shadow hold-out.
- Reviewer 2 recorded zero instrument issues.
- Both reviewers nevertheless marked all 30 representations `complete`, with no
  schema-gap or not-annotatable outcomes.

Under the canonical human Phase A1 raw eligibility rule, accepted records must
have `instrument_issues=[]`. If these had been human submissions, reviewer 1's
batch would not have satisfied that raw condition. The diagnostic continued only
because its precommitted purpose was to exercise the full pipeline regardless of
such findings. This asymmetry is a concrete reason not to replace human
calibration with same-family AI agreement.

## Independent topology and downstream connection

- The topology-only pass, generated without upstream skeletons or obligations,
  had exact graph-invariant signatures on 17/20 questions versus reviewer 1
  (0.85) and 18/20 versus reviewer 2 (0.90). Branch and join presence matched on
  all 20 for both reviewers; mean node-count differences were 0.15 and 0.10.
- Against the preserved environment-aware proposals, exact structural signatures
  were 0.45 for coarse and 0.0 for medium and fine. Mean node-count differences
  were 0.60, 2.45, and 4.45 respectively.

Those granularity differences are expected from differently sized operator
vocabularies. They cannot select coarse as “best”: graph-size resemblance is not
semantic adequacy, and the preserved proposal evidence already records hidden
reasoning and typed-contract gaps. No Phase B human judgment, grounding, or
execution was performed.

## Bottom line

The end-to-end rehearsal succeeded as an engineering pipeline and exposed a
scientifically useful weakness: same-family AI reviewers can agree on the core
two-stage dependency pattern while differing sharply on ambiguity, alternative
plans, and whether the instrument itself is adequate. Human Phase A1 remains
pending, every scientific gate remains closed, and the alignment materiality
rule should be frozen explicitly before any future human agreement claim.
