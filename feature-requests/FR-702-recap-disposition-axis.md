# Feature Request: Recap Disposition Axis — Outcome, Not Activity

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-09
**Parent:** FR-700 (timeframe recap example)

## Summary

Add a disposition axis to the recap demo: each workstream is tagged with its outcome (`shipped | in-progress | judged | rejected | blocked | no-FR`) sourced deterministically from FR `Status:` fields at HEAD via a new tool node. Secondarily, mechanize orphan detection (commit-reference matching) out of the model, which produced 2/6 false positives in the first field run.

## Value Statement

A reader of the recap learns what the week *meant* — what shipped, what was rejected, what is blocked — instead of assuming all listed activity shipped.

## Problem

Field feedback from the first real run against `sheikkinen/ninchat-voice` (2026-07-09):

> **No disposition axis — the biggest gap.** Workstreams list activity, not outcome. NC-351 (**rejected**), NC-353..356 (judged, unbuilt, Phase-0-blocked), and NC-345 (shipped and verified) read identically. A reader would assume all fifteen shipped. This is the `research_as_inventory` trap: a description of what happened is inventory; what it *means* (shipped / judged / rejected / blocked) is the analysis, and it's absent. It also misses the period's defining fact — roughly half the work product was judgements and reflections, including two rejections that were deliverables.

Two distinct defects:

1. **Missing disposition (R1).** The data exists and is mechanical: FR files carry `Status:` fields, and the recap already collects which FR files changed in the window. Nothing joins them. The synthesis prompt cannot supply the axis honestly — asking the model to infer disposition from commit subjects would be a `plausible_wrong_answer` factory.
2. **Orphan detection is a model judgement that should be arithmetic (R2).** The same field run flagged `d2d2934` and `27bdeaa` as orphans although their subjects carry NC-refs mid-string. "Does this subject contain `(FR|NC)-\d+` or `#\d+`?" is a regex, not a judgement. Per the one law: mechanize at the boundary, leave the model only the grouping.

Note the taxonomy requirement embedded in the feedback: **a rejection is a deliverable**, not noise. The disposition vocabulary must make judged-and-rejected a first-class outcome so weeks dominated by judgement work read as productive, not empty.

## Proposed Solution

### R1 — disposition tool node (deterministic)

New shell tool + `type: tool` node collecting FR statuses at HEAD:

```yaml
fr_statuses:
  type: shell
  command: "git -C {repo_path} grep -H -m1 -e 'Status' HEAD -- 'feature-requests/*.md' || [ $? -eq 1 ]"
  parse: text
```

- `git grep` exit 1 = no matches (bare repo / no convention) → normalized to success **at the boundary**; exit 2+ (real error, not a repo) still fails loudly. This is boundary normalization, not a silent fallback — the Judge should distinguish it from the rejected `|| true` of FR-700/F4.
- Prompt receives `fr_statuses` and attaches the **verbatim** status to each workstream whose FR id appears in it: `NC-351: … [Status: Rejected]`. Explicit bound: the model must not infer disposition; a workstream without a matching status line is tagged `[no FR status]`. Attaching a given string to a given group is bookkeeping the grouping already requires; no new abstraction level.
- Schema unchanged (disposition rides in the workstream line) — keeps W026 at 3 fields.

### R2 — mechanize orphan detection

Move reference-detection out of the model: the Jinja2 template (or a small deterministic pre-pass if Jinja2 proves insufficient — no regex filter in stock Jinja2) partitions commits into `referenced` / `unreferenced` sections using the pattern `(FR|NC)-[0-9]+|#[0-9]+` anywhere in the subject. The model's orphan job reduces to copying the `unreferenced` section plus flagging graph/prompt edits without changelog fragments. False-positive class from the field run (mid-subject refs) becomes impossible by construction.

## Acceptance Criteria

- [ ] `fr_statuses` tool node: bare repo without `feature-requests/` succeeds with empty output; non-git repo_path still fails loudly (unit tests, LLM-free)
- [ ] Workstream lines carry verbatim `[Status: …]` tags for FRs with status fields; rejected FRs surface as rejected — fixture: an FR file with `**Status:** Rejected` whose id appears in a commit subject (integration test, API-key-guarded, tolerant matching)
- [ ] Commits with `FR-\d+`/`NC-\d+`/`#\d+` anywhere in the subject can no longer appear as orphans (unit-testable if partition is a pre-pass; template-inspection test if Jinja2)
- [ ] `d2d2934`-class false positive reproduced in a fixture repo and proven fixed (RED first)
- [ ] W026 lint stays clean (3 schema fields)
- [ ] REQ under CAP-195 extended or new REQ added; `req_coverage.py --strict` green
- [ ] Changelog fragment + diary entry

## Alternatives Considered

1. **Model infers disposition from commit subjects** — plausible_wrong_answer factory; "GREEN" in a subject does not mean shipped-and-verified. Rejected.
2. **Disposition as a separate schema field (list of `{fr, status}`)** — pushes W026 to 4 fields and duplicates the join the workstream line already expresses. Rejected.
3. **Skip R2, tune the orphan prompt wording** — prompt levers for a mechanizable check; the discrimination-kill lesson (`l5-prompt-lever-discrimination-kill`) says split, don't tune. Rejected.

## Related

- FR-700 (parent) — known-limitation section updated to point here
- Field run: tmp/recap-ninchat-voice.log (2026-07-09), false positives d2d2934 / 27bdeaa
- Scripture: `research_as_inventory`, `plausible_wrong_answer`, `the_one_law`
- User memory: prompt-as-subagent-contract (move mechanizable levels into code)
