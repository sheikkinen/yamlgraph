<!-- outsider spike | input: inputs/fr-995.md | model: gpt-5.6-sol | 2026-09-05T05:41:13.426107+00:00 -->

## 1. In my own words

This proposes an advisory “outsider” reader for authors and reviewers of `feat` and `fix` pull requests. It gives a context-free model only the PR title and body, then produces a restatement, up to eight unclear phrases, and a checklist of information still needed for a merge decision; code derives a separate YES/NO verdict, while a wrapper can optionally post the report and records each run in a ledger. The spike found that uncapped item counts were not useful, a model-generated verdict produced a false YES, the model exposed a title/body count mismatch, and its missing-information list mixed unlinked material with genuinely absent material. FR-body reading and any blocking gate are knowingly left out.

## 2. Could I decide whether to merge this from the description alone?

YES

The description identifies the proposed files and behavior, reports the spike findings and their locations, gives commands and acceptance criteria, and states what is deferred or out of scope.

## 3. Words and references I could not understand

- **“CAP journey census”** · What does “CAP” mean here, and what is being counted by this census?
- **“Submit step”** · What project workflow contains this named step?
- **“authoring route”** · What process does this project call the authoring route?
- **“lock and lineage sentinel”** · What does the lineage sentinel verify?
- **“judge-class model”** · What project-specific model category does “judge-class” denote?
- **“pointer reasons”** · What conditions count as pointer reasons for the plain-account fixture?
- **“new CAP”** · What is a CAP, and how are tests assigned to one?
- **“guard-by-content”** · What behavior does this term describe?

## 4. What a merge decision would still need

- [ ] Whether the proposed implementation is complete or this PR contains only the feature request.
- [ ] The actual self-test and unit-test results for the implementation in this PR.
- [ ] The current PR #591 regression result required by AC-4.
- [ ] The dogfood report, its PR-comment location, and the disposition of each section-3 item required by AC-5.
- [ ] How the wrapper is invoked automatically when a `feat` or `fix` PR opens, since the described command is manual and commenting is off by default.
- [ ] Whether `--fr <path>` is being implemented now, given that reading FR bodies is also stated to be out of scope.
- [ ] Expected per-run model cost and any practical rate or usage limits.
- [ ] How concurrent runs safely append to the shared JSONL ledger.
- [ ] How temporary PR text and generated reports are cleaned up or retained.
- [ ] What command or runtime executes the graph YAML and which version is required.
