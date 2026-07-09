# Feature Request: Recap Orphans Bypass the Model

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** In Progress
**Effort:** 0.5 days
**Requested:** 2026-07-09
**Judged:** 2026-07-09 — scope frozen (compact judgement; core facts pre-verified during FR-703).
**Parent:** FR-703 (status join post-pass); grandparent FR-702, FR-700

## Summary

Remove the last transport field from the recap model's schema: orphans are assembled entirely in code. The `unreferenced` commit lines (already computed by the FR-702 partition pre-pass) are copied by the post-pass — never transiting the model — and the "graph/prompt change without changelog fragment" rule becomes a deterministic window-level check. Schema drops to two judgement fields (`workstreams`, `hotspots`).

## Value Statement

Orphan hashes in the recap become bit-exact copies of git output — a reader can paste them into `git show` and always hit a commit.

## Problem

Field evidence from two independent runs against ninchat_voice (2026-07-09, tmp/recap-ninchat-voice-3.log and -4.log):

1. **Reproducible hash corruption in a copy-verbatim step.** Both runs emitted orphan `703b72e|2026-07-08|docs(diary): held against the Letter…`; the real hash is `703b72d` (verified: `git log --oneline --all | grep 'held against the Letter'`). A single-character corruption, stable across runs — the model cannot copy 7-char hex strings reliably, and the current schema *requires* it to ("Copy of the UNREFERENCED commit lines… Quote hashes verbatim"). A corrupted hash fails `git show` — the recap's most actionable output (e.g. `63fcc67 fix(export)` with no NC ref) is exactly the part that must be paste-safe.
2. **Prompt-level transport bounds are advisory.** The same run shows the FR-703 full-id formatting bound violated once (`NC-353..356` shorthand emitted alongside the compliant full-id line, creating a duplicate workstream). Instructions constrain transport only probabilistically; code constrains it absolutely. The orphans copy rule is the same class of instruction.

Diary 2026-07-09 ("the model is squeezed out one field at a time") named the law: schema fields are either **judgement** or **transport**; transport fields are pipeline bugs by construction. `orphans` is transport: code already holds `unreferenced` in state, and the convention sub-rule is a set operation on data code also holds (`churn` paths × `fragments`).

## Proposed Solution

Extend the FR-703 post-pass (`attach_statuses` → rename or sibling `assemble_recap`) in [partition.py](../examples/demos/recap/nodes/partition.py):

1. **Orphan commits**: `state["unreferenced"]` lines copied bit-exact into `recap["orphans"]` — zero model transit.
2. **Convention orphans (deterministic window rule)**: if the window changed files matching the graph/prompt path heuristics (from `churn`) and added **no** changelog fragment (`fragments` empty), append those file paths with a `no changelog fragment in window` marker. Per-FR fragment↔file matching is fuzzy and stays out of scope — the window-level rule is honest and arithmetic; the Judge may sharpen or confirm.
3. **Schema shrinks to `workstreams` + `hotspots`** (judgement only). Prompt loses the orphans field, the UNREFERENCED section, and the copy instructions; `unreferenced` leaves the synthesize inputs. W026 posture: 2 fields.
4. Existing integration assertion (orphan hash flagged) flips from tolerant matching to **exact equality** — the copy is code now; `tolerant_matching` applies to LLM output, and this no longer is.

## Acceptance Criteria

- [ ] RED first: unit fixture reproducing the field corruption class — given `unreferenced` containing the verbatim `703b72d|…` line, `recap["orphans"]` contains the hash **bit-exact** (would fail under model transport, passes under copy)
- [ ] Orphans are exactly the unreferenced lines (order preserved) plus deterministic convention entries; unit tests LLM-free
- [ ] Convention rule: graph/prompt-path churn + empty `fragments` → paths flagged; non-empty `fragments` → no convention entries; both unit-tested
- [ ] Prompt/template inspection: no `orphans` in schema, no UNREFERENCED section, no copy instructions; `unreferenced` absent from synthesize variables/requires
- [ ] Integration test asserts orphan hash by exact equality (no tolerant matching for code-owned fields); Rejected-status test still passes
- [ ] Still exactly one LLM node; lint clean (W026 at 2 fields)
- [ ] FR-700/702/703 suites evolved where topology assertions change
- [ ] New REQ under CAP-195 — ID verified free against origin/main at enforce time
- [ ] **Field rerun against projects/ninchat_voice (`--var since="1 week ago"`): every orphan hash resolves via `git -C projects/ninchat_voice show <hash>` — mechanically verified in a loop, zero failures; the `703b72d` line appears bit-exact. Result recorded in this FR's Implementation section.**
- [ ] README teaching points + demo-output.log regenerated; `req_coverage.py --strict` green; changelog fragment + diary entry

## Judgement (2026-07-09, compact)

Scope frozen with these pins (facts verified during FR-703 enforce — python-node dict merge, state declarations, post-pass seam):

| # | Pin |
|---|-----|
| J1 | `attach_statuses` stays as the statuses-only unit (FR-703 tests keep their target); new `finalize_recap` composes it + orphan assembly and becomes the graph's post-pass node/tool (node renamed `finalize_recap`; FR-700/702/703 topology assertions evolve) |
| J2 | Orphan order = unreferenced order, blanks skipped; convention entries appended after commit orphans, paths deduped preserving first occurrence |
| J3 | Convention path heuristic identical to the template's (`.yaml` ∧ (`graphs/` ∨ `prompts/`)); path = last tab field of a numstat line |
| J4 | Integration exactness = hash field equality (`entry.split('\|')[0] == hash`), full-line equality not required (date format is git's) |
| J5 | `referenced` stays a synthesize input (grouping); `unreferenced`, with orphans code-owned, leaves synthesize and joins finalize_recap requires |

**Out of scope:** per-FR fragment↔file matching (window rule only), duplicate-workstream dedup (judgement territory, separate FR if it recurs), any change to collection tools.

## Alternatives Considered

1. **Harden the copy instruction / lower temperature** — prompt levers for transport; two runs prove the corruption is stable at current settings; instructions are advisory (shorthand escape proves it same-day). Rejected.
2. **Post-pass validates model-copied hashes against `unreferenced` and repairs** — doubles the machinery to keep the model doing work code does natively; repair-after-corruption where bypass is cheaper. Rejected.
3. **Per-FR fragment↔file matching for convention orphans** — requires joining fragments to FRs to files; fuzzy, and the window-level rule already catches the real case (prompt/graph tweak slipped through with no fragment at all). Deferred, noted for the Judge.

## Related

- Field evidence: tmp/recap-ninchat-voice-3.log, tmp/recap-ninchat-voice-4.log (`703b72e` twice; real `703b72d`); shorthand escape in -4
- Diary: 2026-07-09 "the model is squeezed out one field at a time" (judgement/transport field taxonomy; this FR is its seed executed)
- Scripture: `the_one_law`, `plausible_wrong_answer`; user memory prompt-as-subagent-contract (clause 3: validator-uncovered jobs are the flood surface)
- Completes the arc: FR-702 (detection → code), FR-703 (join → code), FR-704 (copy → code)
