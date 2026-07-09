# Feature Request: Recap Status Join as Deterministic Post-Pass

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-07-09
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
    # 1. Parse fr_statuses lines: 'HEAD:feature-requests/NC-346-x.md:**Status:** ENFORCED ...'
    #    -> {'NC-346': 'ENFORCED ...'}  (strip path, strip '**Status:**', strip markdown bold)
    # 2. For each recap.workstreams line: first (FR|NC)-[0-9]+ (IGNORECASE) -> lookup.
    #    Append '[Status: <trimmed>]' or '[no FR status]'.
    # 3. Return {"recap": updated}  (schema shape unchanged)
```

- **Prompt sheds the join**: the disposition rule and `[no FR status]` instruction are removed from `recap.yaml`; `fr_statuses` leaves the synthesize inputs entirely. The model's abstraction span shrinks (grouping only) — the FR-702 W026 posture improves further.
- Join failure becomes impossible by construction; `[no FR status]` becomes verified absence (id not in map).
- Trim rule fixes the double-prefix wart in the same pass.
- Graph: `synthesize → attach_statuses → END`; `get_fr_statuses` stays (collection unchanged), its output re-routes from prompt input to post-pass input.
- Pattern-freeze evidence (per diary 2026-07-09 heuristic): the parse fixture must be the **verbatim field line** `HEAD:feature-requests/NC-346-offschema-question-stonewall.md:**Status:** ENFORCED (2026-07-08) — R-1..R-4 honoured; see Implementation below`, not an invented example.

## Acceptance Criteria

- [ ] `attach_statuses` unit tests (LLM-free, RED first): verbatim field-line fixture parses to trimmed status; workstream with known id gains `[Status: …]`; unknown id gains `[no FR status]`; line without any id untouched; lowercase `fr-346` joins (IGNORECASE); empty `fr_statuses` map tags all workstreams `[no FR status]`
- [ ] The NC-346 join failure reproduced as a fixture and proven fixed: given the field run's status lines and a workstream line naming NC-346, the output carries `ENFORCED` — no model involved
- [ ] `recap.yaml` prompt contains no status/disposition instructions; `fr_statuses` removed from synthesize variables (template-inspection test)
- [ ] No double prefix: output contains `[Status: ENFORCED` not `[Status: **Status:**` (unit test on trim)
- [ ] Existing integration test (Rejected surfaces verbatim) passes unchanged through the post-pass path
- [ ] Still exactly one LLM node; W026 clean
- [ ] New REQ under CAP-195 — ID verified free against origin/main at enforce time
- [ ] `req_coverage.py --strict` green; changelog fragment + diary entry

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
