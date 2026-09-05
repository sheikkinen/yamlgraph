<!-- outsider spike | input: inputs/pr-591-v4.md | model: gpt-5.6-sol | 2026-09-05T05:51:52.707103+00:00 -->

## 1. In my own words

This change adds a local AI-assisted research pipeline for project maintainers to classify a 30-capability pilot by intended user, code usage, retention recommendation, and stated value, while mechanically checking citations and six predetermined answers. It delivered committed ledgers from three runs, identified CAP-184 and CAP-78 as removal candidates, found that roughly half the sample serves project developers, and showed that the current user-type and business-value classifications are not reliable enough for ranking or removal decisions; it does not retire anything or establish results for all 242 capabilities.

## 2. Could I decide whether to merge this from the description alone?

YES

The description states what changed, what the pilot found, where the implementation and results are, how to run it, its cost and data exposure, and which work remains deliberately incomplete.

## 3. Words and references I could not understand

- **Quote:** `author_graph,run_operate,debug_observe,integrate,serve_embed,census_classify,govern_process,audit_comply,conversational_app,none_internal` · **Question:** What precise criteria distinguish these ten project-defined user types?
- **Quote:** `FR-990 AC-7` · **Question:** What is the complete wording of acceptance criterion 7?
- **Quote:** `plan §12` · **Question:** What procedure and evaluation criteria did the outsider-reader spike use?

## 4. What a merge decision would still need

- [ ] Confirm that the implementation matches the described collection, classification, validation, failure-preservation, and canary behavior.
- [ ] Inspect the six canaries, their expected answers, and the actual outcomes from each committed run.
- [ ] Determine how the 30 pilot capabilities were selected and whether that selection supports the stated extrapolation to 242.
- [ ] Check the exact dependency, environment, API-key, and provider-account requirements for reproducing a run.
- [ ] Review failure modes for unavailable providers, malformed source files, failed `git grep` commands, and partial artifact writes.
- [ ] Confirm that the collected repository text cannot include material that should not be sent to the configured model provider.
- [ ] Compare the implementation and delivered artifacts with the full FR-990 acceptance criteria and repository graph-authoring requirements.
