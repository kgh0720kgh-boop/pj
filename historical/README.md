# Historical read-only evidence

This directory quarantines recovered Week 1–3 research evidence. It is not a source of gold programs or an input to question-only annotation.

## IR v0.2 bundle

`ir_v0_2/` preserves the original contract, parser/registry/validator modules, and one complete Week 2 condition-C artifact bundle without modifying their bytes. The recovered files are listed and hashed in `ir_v0_2/recovery_manifest_v0_1.json`; the unchanged files were first fixed in Git commit `dcc5ac5c14e9acb5c689b400a4046708b6837ac3`.

The condition-C JSONL contains expected answers, planner outputs, validation reports, and execution/evaluation fields. It may be used only for late-stage IR compatibility regression and historical failure analysis. Never expose it to semantic-skeleton, information-obligation, abstract-topology, operator-vocabulary, or other early-layer annotation/prediction work.

Current adapters and reports live outside the recovered tree. Do not edit the ten paths listed in the recovery manifest; a correction or additional recovery requires a new versioned manifest and preservation commit.
