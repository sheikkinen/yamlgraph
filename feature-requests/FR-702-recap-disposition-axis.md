# Feature Request: Recap Disposition Axis — Outcome, Not Activity

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Completed
**Effort:** 0.5 days
**Requested:** 2026-07-09
**Judged:** 2026-07-09 — scope frozen. 6 findings resolved (see Judgement section).
**Completed:** 2026-07-09 — RED ee792608, GREEN follows; one enforce deviation (IGNORECASE, see Judgement section note).
**Parent:** FR-700 (timeframe recap example)

## Summary

Add a disposition axis to the recap demo: each workstream is tagged with the **verbatim** `Status:` line of its FR, sourced deterministically at HEAD via a new tool node — no normalized vocabulary, no model inference (F1). Secondarily, mechanize orphan detection (commit-reference matching) out of the model via a deterministic python pre-pass node, which produced 2/6 false positives in the first field run.

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
  command: "git -C {repo_path} grep -H -m 1 -e '^\\*\\*Status' HEAD -- 'feature-requests/*.md' || [ $? -eq 1 ]"
  parse: text
```

- Pattern anchored to `^\*\*Status` (F2) — bare `Status` matches prose everywhere; `-m 1` caps at one line per file.
- `git grep` exit 1 = no matches (bare repo / no convention) → normalized to success **at the boundary**; exit 2+ (real error, not a repo) still fails loudly. Verified implementable: `execute_shell_tool` runs `shell=True` for exactly this (tools/shell.py); the exit-code semantics get their own LLM-free unit test (F3). This is boundary normalization, not a silent fallback — distinct from the rejected `|| true` of FR-700/F4.
- Input bound: one status line per FR file at HEAD — bounded by repo convention size; no cap added, revisit via read_raw_output_first if flooding (F5).
- Prompt receives `fr_statuses` and attaches the **verbatim** status to each workstream whose FR id appears in it: `NC-351: … [Status: Rejected]`. Explicit bound: the model must not infer disposition; a workstream without a matching status line is tagged `[no FR status]`. Attaching a given string to a given group is bookkeeping the grouping already requires; no new abstraction level.
- Schema unchanged (disposition rides in the workstream line) — keeps W026 at 3 fields.

### R2 — mechanize orphan detection

Stock Jinja2 has no regex filter (verified: `Environment()` with no custom filters in utils/template.py), so reference detection is a **demo-local `type: python` pre-pass node** (`examples/demos/recap/nodes/partition.py`): partitions the commit list into `referenced` / `unreferenced` state keys using `(FR|NC)-[0-9]+|#[0-9]+` anywhere in the subject (F4). The model's orphan job reduces to copying the `unreferenced` section plus flagging graph/prompt edits without changelog fragments. False-positive class from the field run (mid-subject refs) becomes impossible by construction. File-*path* partitioning stays Jinja2; README teaching points updated to reflect the split (paths = template, reference regex = python pre-pass).

## Acceptance Criteria

- [ ] `fr_statuses` tool node: bare repo without `feature-requests/` succeeds with empty output; non-git repo_path (git grep exit ≥2) still fails loudly — both LLM-free unit tests (F3)
- [ ] grep pattern anchored (`^\*\*Status`): a fixture FR containing the word "Status" in prose contributes no extra lines (unit test)
- [ ] Workstream lines carry verbatim `[Status: …]` tags for FRs with status fields, `[no FR status]` otherwise; rejected FRs surface verbatim — fixture: an FR file with `**Status:** Rejected` whose id appears in a commit subject (integration test, API-key-guarded, tolerant matching)
- [ ] `partition.py` pre-pass: commits with `FR-\d+`/`NC-\d+`/`#\d+` anywhere in the subject land in `referenced`; `d2d2934`-class false positive reproduced in a fixture and proven fixed — RED first, LLM-free unit tests (F4)
- [ ] W026 lint stays clean (3 schema fields)
- [ ] New REQ under CAP-195 — ID verified free against origin/main at enforce time (F6, cap-req-id-allocation-race)
- [ ] `req_coverage.py --strict` green
- [ ] Changelog fragment + diary entry

## Judgement (2026-07-09)

Scope frozen. Findings and resolutions:

| # | Finding | Resolution |
|---|---------|------------|
| F1 | Summary's normalized vocabulary (`shipped\|judged\|…`) contradicts R1's verbatim-only rule | Verbatim wins; normalized taxonomy dropped — mapping is code's job, added only if a consumer ever needs it |
| F2 | `grep -e 'Status'` matches prose everywhere | Anchored to `^\*\*Status`, `-m 1` per file |
| F3 | `\|\| [ $? -eq 1 ]` assumed shell execution | Verified: `execute_shell_tool` uses `shell=True` (documented for pipes/redirects); exit-code semantics get dedicated unit tests |
| F4 | R2 left mechanism open (Jinja2 vs pre-pass) | Pinned: stock Jinja2 has no regex (verified) → `type: python` pre-pass node, demo-local, LLM-free-testable |
| F5 | `fr_statuses` input unbounded | Accepted: one line per FR file; no cap; read_raw_output_first watches for flooding |
| F6 | "REQ extended or new REQ" ambiguous + ID race risk | Pinned: new REQ under CAP-195, ID verified free against origin/main at enforce time |

**Enforce deviation (2026-07-09, raw-output read):** the frozen pattern `(FR|NC)-[0-9]+|#[0-9]+` is case-sensitive; the first GREEN demo run shipped `a9a8bdec docs(fr-691): …` to orphans because conventional-commit scopes lowercase the ref. Pattern amended with `re.IGNORECASE` — same reference class, case-blind — with a condemning unit test added first. Exactly the false-positive family this FR exists to kill, caught by the same read_raw_output_first practice that motivated it.

**Out of scope (purge list):** normalized disposition vocabulary, disposition as schema field, status history (only HEAD), non-FR conventions (GitHub issue states), retroactive FR-700 demo-output regeneration.

## Alternatives Considered

1. **Model infers disposition from commit subjects** — plausible_wrong_answer factory; "GREEN" in a subject does not mean shipped-and-verified. Rejected.
2. **Disposition as a separate schema field (list of `{fr, status}`)** — pushes W026 to 4 fields and duplicates the join the workstream line already expresses. Rejected.
3. **Skip R2, tune the orphan prompt wording** — prompt levers for a mechanizable check; the discrimination-kill lesson (`l5-prompt-lever-discrimination-kill`) says split, don't tune. Rejected.

## Related

- FR-700 (parent) — known-limitation section updated to point here
- Field run: tmp/recap-ninchat-voice.log (2026-07-09), false positives d2d2934 / 27bdeaa
- Scripture: `research_as_inventory`, `plausible_wrong_answer`, `the_one_law`
- User memory: prompt-as-subagent-contract (move mechanizable levels into code)
