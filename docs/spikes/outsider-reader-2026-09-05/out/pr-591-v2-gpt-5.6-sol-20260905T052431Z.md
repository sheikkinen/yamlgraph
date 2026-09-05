<!-- outsider spike | input: inputs/pr-591-v2.md | model: gpt-5.6-sol | 2026-09-05T05:24:57.478990+00:00 -->

## 1. In my own words

This change adds a local AI-assisted pipeline that collects repository evidence for capabilities, classifies each capability by user type and disposition, validates cited evidence, and checks results against six predefined canaries. A three-run, 30-capability pilot produced committed result ledgers, identified two removal candidates and three nonexistent consumer citations, and found that the user-type and business-value classifications are not yet reliable. The instrument supports future capability-retention decisions, but the text does not say exactly who will operate it or approve those decisions.

## 2. Could I decide whether to merge this from the description alone?

YES

The description explains what changed, what the pilot found, where the implementation and results are, how to run it, and which tests, full-scale runs, comparisons, and retirement actions are knowingly absent.

## 3. Words and references I could not understand

- **“FR-990 Proposed Solution 1–5”** · **Question:** What are the exact five proposed changes and their acceptance conditions?
- **“consumer hit-kind check”** · **Question:** What consumer-reference categories exist, and which ones count as valid evidence?
- **“one exclusion bug”** · **Question:** What is being incorrectly included or excluded?
- **“repo's authoring route”** · **Question:** What project-specific process does this route enforce?
- **“Raw Output Read”** · **Question:** What information and interpretation rules does this referenced section contain?

## 4. What a merge decision would still need

- [ ] Determine how the 30 pilot capabilities were selected and whether the sample was intended to be representative.
- [ ] Inspect the six canary expectations and whether any canaries overlap with prompt examples or other model-visible material.
- [ ] Check the exact validation rules and output schema for valid, contested, and failed rows.
- [ ] Determine the required Python, `yamlgraph`, and provider-client versions.
- [ ] Determine how Anthropic credentials and provider errors are configured and handled.
- [ ] Inspect dependency or configuration changes introduced by the pipeline.
- [ ] Establish the merge acceptance criterion for an advisory research instrument whose classification output is acknowledged as unreliable.
