# Feature Request: Recap Status Join as Deterministic Post-Pass

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** In Progress
**Effort:** 0.5 days
**Requested:** 2026-07-09
**Judged:** 2026-07-09 — scope frozen. 4 findings resolved (see Judgement section).
**Parent:** FR-702 (recap disposition axis)

## Summary

Move the FR-id → status join out of the synthesis model into a deterministic `type: python` post-pass: code parses the FR/NC id from each workstream line and appends the trimmed verbatim status. The model stops attaching statuses entirely. Kills the join-failure class found in the first FR-702 field run, plus the `[Status: **Status:** …]` double-prefix wart.

## Value Statement

Recap readers can trust a `[no FR status]` tag as verified absence rather than model recall failure — the tag currently lies exactly when it matters.

## Problem

Field run against ninchat_voice (2026-07-09, tmp/recap-ninchat-voice-2.log), verified against the repo:

- Workstreams NC-346, NC-347, and NC-341..344 were tagged `[no FR status]` — yet `git -C projects/ninchat_voice grep -c '^\*\*Status' HEAD -- 'feature-requests/NC-346*' 'feature-requests/NC-347*' 'feature-requests/NC-341*'` returns 1 match each. The statuses exist; the model failed the join.
- Root cause: the `fr_statuses` input carried ~50 status lines; the model attached some and silently defaulted the rest. Recall degrades with list size (cf. `l5-encode-recall-bottleneck`), and the `[no FR status]` fallback makes the failure **read as a grounded finding** — a `plausible_wrong_answer` produced by the very feature built to eliminate one (FR-702's orphan false positives).
- Cosmetic: verbatim attachment doubles the prefix — `[Status: **Status:** ENFORCED …]` — because the grep line includes path and markdown bold.

The join is arithmetic: extract first `(FR|NC)-[0-9]+` from a workstream line, look it up in an id→status map. Per `the_one_law` and the FR-702 pattern (R2), arithmetic belongs in code.

## Proposed Solution

New function in the existing [partition module](../examples/demos/recap/nodes/partition.py) (or sibling), wired as a `type: python` post-pass node **after** `synthesize`:

```python
def attach_statuses(state):
    """Append [Status: ...] to each workstream line deterministically."""
    # 0. Normalize recap at the boundary: accept dict OR Pydantic model
    #    (model_dump) — the seam is ambiguous today (F2).
    # 1. Parse fr_statuses lines: 'HEAD:feature-requests/NC-346-x.md:**Status:** ENFORCED ...'
    #    -> {'NC-346': 'ENFORCED ...'}  (strip path, strip '**Status:**', strip
    #    markdown bold). Duplicate id: first line wins (F3).
    # 2. For each recap.workstreams line: finditer ALL (FR|NC)-[0-9]+ ids
    #    (IGNORECASE, F1). All found ids share one trimmed status -> single
    #    '[Status: <s>]'. Distinct statuses -> per-id tags
    #    '[Status: NC-341 ENFORCED; NC-342 Proposed]'. No ids in map ->
    #    '[no FR status]'. No ids in line -> untouched.
    # 3. Return {"recap": updated_dict}  (schema shape unchanged)
```

- **Prompt sheds the join** but gains one *formatting* bound (F1): every workstream line must name each FR id in full (`NC-341 NC-342`), never ranges or shorthand (`NC-341..344`, `NC-280/281/287/339`) — output shape, not judgement; the field run's three shorthand lines are the fixtures proving why. The disposition rule and `[no FR status]` instruction are removed from `recap.yaml`; `fr_statuses` leaves the synthesize inputs entirely.
- Join failure becomes impossible by construction; `[no FR status]` becomes verified absence (id not in map).
- Trim rule fixes the double-prefix wart in the same pass.
- Graph: `synthesize → attach_statuses → END`; `get_fr_statuses` stays (collection unchanged), its output re-routes from prompt input to post-pass input.
- Pattern-freeze evidence (per diary 2026-07-09 heuristic): the parse fixture must be the **verbatim field line** `HEAD:feature-requests/NC-346-offschema-question-stonewall.md:**Status:** ENFORCED (2026-07-08) — R-1..R-4 honoured; see Implementation below`, not an invented example.

## Acceptance Criteria

- [ ] `attach_statuses` unit tests (LLM-free, RED first): verbatim field-line fixture parses to trimmed status; workstream with known id gains `[Status: …]`; unknown id gains `[no FR status]`; line without any id untouched; lowercase `fr-346` joins (IGNORECASE); empty `fr_statuses` map tags all workstreams `[no FR status]`
- [ ] Multi-id workstream (F1): line naming NC-341 and NC-342 with equal statuses gets one tag; with distinct statuses gets per-id tags — fixtures include the verbatim field shorthand lines as condemning evidence for the formatting bound
- [ ] Boundary normalization (F2): post-pass accepts `recap` as dict AND as Pydantic model — both unit-tested
- [ ] Duplicate id in status map: first line wins, deterministic (F3)
- [ ] The NC-346 join failure reproduced as a fixture and proven fixed: given the field run's status lines and a workstream line naming NC-346, the output carries `ENFORCED` — no model involved
- [ ] `recap.yaml` prompt contains no status/disposition instructions and does contain the full-id formatting bound; `fr_statuses` removed from synthesize variables (template-inspection test)
- [ ] No double prefix: output contains `[Status: ENFORCED` not `[Status: **Status:**` (unit test on trim)
- [ ] Existing integration test (Rejected surfaces verbatim) passes unchanged through the post-pass path
- [ ] Still exactly one LLM node; W026 clean
- [ ] README teaching points updated; demo-output.log regenerated from a real run (F4)
- [ ] New REQ under CAP-195 — ID verified free against origin/main at enforce time
- [ ] `req_coverage.py --strict` green; changelog fragment + diary entry

## Judgement (2026-07-09)

Scope frozen. Findings and resolutions:

| # | Finding | Resolution |
|---|---------|------------|
| F1 | Multi-FR workstreams use shorthand (`NC-341..344`, `NC-280/281/287/339` — verbatim field lines); single-id join stamps a 4-FR stream with one FR's status | Prompt formatting bound: full ids only, never shorthand; post-pass joins ALL ids via finditer; per-id tags when statuses differ |
| F2 | `recap` state shape dict-vs-model ambiguous (existing integration test already hedges) | Post-pass normalizes at its boundary; both shapes unit-tested |
| F3 | Duplicate id in status map unspecified | First line wins, deterministic |
| F4 | Demo artifacts not in criteria though behavior changes | README + demo-output.log regeneration added |

**Out of scope (purge list):** status normalization/vocabulary mapping, multi-repo status sources, status history, retry/self-audit loops, changes to the fr_statuses collection command.

## Alternatives Considered

1. **Compact the fr_statuses input (pre-trim, id→status lines) and keep the model join** — reduces but does not eliminate recall failure; the tag still can't be trusted. Rejected.
2. **Retry/verify loop: model self-checks its joins** — asks a stateless worker to audit its own recall; adds a judgement instead of removing one. Rejected.
3. **Drop `[no FR status]` entirely** — hides the axis for unconventioned repos; absence should be stated, just truthfully. Rejected.

## Related

- FR-702 (parent) — this completes its mechanization arc: R2 moved reference detection to code; FR-703 moves the status join
- Field evidence: tmp/recap-ninchat-voice-2.log; verification grep in session log 2026-07-09
- Scripture: `the_one_law`, `plausible_wrong_answer`, `read_raw_output_first`
- Memory: l5-encode-recall-bottleneck (recall degrades with list size); prompt-as-subagent-contract (externalize cross-unit state into code)
- Diary: 2026-07-09 "the regex repeats the model's sin" (pattern-freeze requires field-data fixtures — applied here)
