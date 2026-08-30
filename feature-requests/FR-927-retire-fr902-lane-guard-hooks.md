# Feature Request: FR-927 Retire the FR-902 Lane-Guard Hook Machinery

**Priority:** HIGH
**Type:** Removal (R-6 subtraction)
**Status:** Judged APPROVED WITH REVISIONS 2026-08-30 ([judgement](FR-927-retire-fr902-lane-guard-hooks.judgement.md)); R-2..R-6 folded same day; R-1 (research record) WAIVED by operator ("research: skip", 2026-08-30) — operator override recorded in lieu of the artifact
**Effort:** 0.5 days
**Research:** waived by operator 2026-08-30; alternatives dispositioned in-conversation: full hook retirement (chosen), Check-8-only retirement (rejected — SessionStart/Stop hooks have no live lifecycle without the guard), dark-disable via `fr902.live` (rejected — flag only gates lane creation, existing records keep the guard armed; witnessed this session), repair `lane_guard.py` cwd resolution (rejected — third prompt/parser patch on a discredited channel; `two_strike_split`), delivery-fix-only per FR-925 (rejected — delivers a lane to a broken guard). `is_this_a_graph`: no — repo-local enforcement subtraction, no LLM stage.
**Requested:** 2026-08-30 (operator: "check the 902 related bash enum in hooks. fr to remove it all. red test to verify that it is gone never to return")
**First consumer / first event:** every agent session's first write-shaped
tool call — the moment Check 8 currently fires a false denial or forces a
reflexive `FR902_ALLOW_OUTSIDE=1` prefix
**Prior art:** `FR-902-session-worktree-lifecycle.md` [Enforced] — the
subject of this removal, not a competitor; its live-gate clause ("pending
AC-13 operator review") anticipated exactly this verdict path.
`FR-925-lane-delivery-agent-context.md` + judgement + research [Approved,
unenforced] — fixes lane *delivery* for the machinery this FR deletes;
superseded here (AC-05), its witness evidence (session 9acc40e0) is reused
as removal justification. No prior FR proposes retirement — this is the
first disposition of FR-902's rollout review.

## Ideal Result

An agent session writes to its worktree (or anywhere the OS permits)
without any hook-level lane arbitration. The only write barrier on the
main checkout is the FR-889 kernel lock. No bash write-shape grammar
exists anywhere in the hook chain. A structural test pins the absence
forever.

## Value Statement

For every agent session, against the alternative of keeping a guard that
never worked as specified: removes a denial class that fired almost
exclusively on false positives, restores signal to the escape-hatch audit
stream, and completes the grammar deletion FR-889 started — Check 8 is
the last textual write-shape enum in the hooks.

## Problem

FR-902 shipped a session-lane ownership guard (Check 8) live-gated behind
`fr902.live`. Witnessed across four sessions on 2026-08-30, the mechanism
failed its own spec in both directions:

1. **The analyzer denies in-lane writes.** `lane_guard.py` resolves
   relative and `$PWD` targets against the hook payload `cwd`, which is
   always the workspace folder — never the persistent terminal's actual
   cwd (documented by FR-889 §4c itself). Fresh witnesses (session
   ccd5fb52, post-FR-889-merge): in-lane `echo > tmp/...` denied; in-lane
   `echo > "$PWD/tmp/..."` denied. FR-889 §4c deleted the predictive
   heuristics but the retained "explicit-path" check imported the same
   known-bad cwd for every non-absolute path — the false-positive class
   survived through the survivor.
2. **The false positives blind the audit channel.** Agents learn to
   prefix `FR902_ALLOW_OUTSIDE=1` reflexively (witnessed: prefixes on
   read-only commands, on `gh pr create`, on `grep`). The OVERRIDE/
   escape audit stream — the guard's telemetry value — is noise.
3. **The guard defended its own kill switch.** Disarming required
   `sudo rm fr902.live` after both the lane guard and the FR-889 lock
   denied the removal. The live-flag was armed "pending AC-13 operator
   review" (FR-902 status line); the operator's review verdict is this
   FR.
4. **Check 8 carries its own bash write-shape enum** — the tool-name
   `case` list plus the grep alternation
   `>|\btee\b|\bcp\b|\bmv\b|\brsync\b|\binstall\b|\bsed\b|\bdd\b|\btruncate\b|\btouch\b|\bmkdir\b|\brm\b|\bln\b|\bchmod\b`
   — the exact grammar class FR-889 deleted from Check 7 (AC-06:
   "grammar gone"). The hook chain enforces on main via the kernel and
   on lanes via regex; the regex half is the discredited one.
5. **The invariant that matters is already enforced elsewhere.** FR-889's
   OS lock makes main unwritable at the kernel ("agent has no business
   writing to main" — operator, 2026-08-30). What Check 8 added beyond
   that was agent-vs-agent lane arbitration, which in practice only ever
   arbitrated against its own analyzer.

## Proposed Solution

Delete the entire FR-902 hook machinery; keep the substrate tooling.

**Delete:**
- `pre-command-guard.sh` Check 8 block (tool-name case enum, write-verb
  grep alternation, `FR902_*` variables, deny/override plumbing)
- `.github/hooks/scripts/checks/lane_guard.py`
- `.github/hooks/scripts/session-worktree.sh` + its SessionStart
  registration in `session-probe.json`
- `.github/hooks/scripts/session-checkpoint.sh` + its Stop registration
- All `fr902.live` gating references (file already removed by operator
  via sudo, 2026-08-30)
- Hook tests: `test_fr902_lane_guard.py`, `test_fr902_session_worktree.py`,
  `test_fr902_checkpoint.py`, `test_fr902_gc_join.py`, `fr902_fixtures.py`
  (gc/join tests move or die with their scripts — see disposition)
- `FR902_ALLOW_OUTSIDE` escape recognition and every mention of it in
  hook scripts, `copilot-instructions.md`, and `CLAUDE.md`

**Keep (dispositioned):**
- `scripts/worktree.sh session` / `gc` verbs — lane creation stays as
  operator/manual tooling (the substrate was never the defect; the
  automatic hook wiring was). GC still needed to reap existing lanes.
- `scripts/vscode/now.py` lane listing (read-only observability) and
  `scripts/vscode/session_join.py` (reads historical checkpoints).
- Existing `session/*` branches and lanes — untouched; GC reaps them
  under its normal lossless rules.

**Rewrite CAP-254** to cover only the retained tooling (worktree verbs,
GC, now.py listing, join script): REQ-YG-629 loses its guard clause,
REQ-YG-630 loses its Stop-hook clause; module lists shrink accordingly.
`tests/unit/test_session_worktree_lifecycle.py` prunes to match.

**Supersede FR-925** (lane delivery to agent context): moot — there is no
hook-created lane to deliver. Mark SUPERSEDED by FR-927; its historical
judgement and implementation record are preserved untouched (R-4: a
superseded plan is not retroactively rejected).

**Why the SessionStart/Stop hooks die with Check 8 (R-3):** automatic
lane creation and Stop-hook checkpointing exist only to serve the
hook-created lane lifecycle — a lane nobody guards needs no automatic
creation, and a checkpoint hook that commits on a lane branch nobody is
routed to records nothing. Their only live lifecycle is the failed
hook-created lane system; manual `scripts/worktree.sh session`/`gc`,
`now.py`, and `session_join.py` remain as the retained substrate.

**Regression pin:** `.github/hooks/tests/test_fr902_retired.py`
(RED, committed with this FR) asserts structural absence:
no `lane_guard.py`, no session-worktree/session-checkpoint scripts or
registrations, no `FR902`/`fr902` tokens in `pre-command-guard.sh`, no
write-verb grep alternation outside the R-2 mutator fence, no
`FR902_ALLOW_OUTSIDE` anywhere in hook scripts. The test is permanent —
"gone never to return."

## Acceptance Criteria (revised per judgement; judge AC-01 waived with R-1)

- [ ] AC-02: `.github/hooks/tests/test_fr902_retired.py` exists, is
      independent of deleted FR-902 fixtures, fails against the current
      FR-902 hook machinery (RED), and passes only when the retired
      surfaces are absent
- [ ] AC-03: The structural test asserts no `checks/lane_guard.py`, no
      `session-worktree.sh`, no `session-checkpoint.sh`, and no
      `session-probe.json` registrations for the deleted scripts
- [ ] AC-04: `pre-command-guard.sh` contains no FR-902 Check 8 block, no
      `FR902`/`fr902` token, no `FR902_ALLOW_OUTSIDE`, and no write-shape
      grep alternation except the intact FR-889 lock-mutator fence
      (`chmod`/`chflags`/`setfacl`)
- [ ] AC-05: Hook tests green after deleting FR-902 tests/fixtures; no
      orphaned imports of `fr902_fixtures`, `lane_guard.py`,
      `session-worktree.sh`, or `session-checkpoint.sh`
- [ ] AC-06: `session-probe.json` removes only the session-worktree.sh
      SessionStart entry and session-checkpoint.sh Stop entry; all other
      registrations byte-for-byte equivalent
- [ ] AC-07: CAP-254 rewritten to retained tooling only (worktree
      session/gc, now.py, session_join.py); REQ-YG-629 drops the
      PreToolUse guard clause; REQ-YG-630 drops the Stop-hook clause;
      `tests/unit/test_session_worktree_lifecycle.py` matches;
      `python scripts/req_coverage.py --strict` green
- [ ] AC-08: FR-902 records hook machinery RETIRED by FR-927; FR-925
      marked SUPERSEDED by FR-927 — both preserving historical record
- [ ] AC-09: No live FR-902 lane / `FR902_ALLOW_OUTSIDE` guidance in
      `CLAUDE.md` or `.github/copilot-instructions.md`; hooks-section
      bullet replaced by a one-line retirement note
- [ ] AC-10: `pre-command-guard.sh` before/after line count recorded in
      Implementation Record (`wc -l`, baseline 450)
- [ ] AC-11: Changelog fragment (`type: removal`)
- [ ] AC-12: Diary reflection

## Conditions (judgement, C-1..C-6)

C-1 folded (this revision); C-2 human review of the hook-enforcement
deletion diff before retirement is live — NOT yet satisfied: operator
merged the plan+judgement only and explicitly withheld enforcement
authorization (2026-08-30); C-3 RED structural test before enforcement;
C-4 FR-889 OS lock/fence/Check 7 untouched; C-5 retained substrate and
existing lanes/branches untouched; C-6 no replacement lane arbitration.

## Non-Goals

- Deleting `worktree.sh session`/`gc` or existing session lanes/branches
- Touching FR-889's OS lock, mutator fence, or Check 7 replacement
- Building any replacement lane arbitration

## Related

- FR-902 (ships the machinery this retires; status: hook rollout never
  survived operator review — AC-13 verdict is this FR)
- FR-889 §4c / AC-15 (retired the predictive heuristics; this completes
  the subtraction the retained path leaked)
- FR-925 (superseded — lane delivery moot without hook-created lanes)
- FR-888 (worktree-route guidance; unaffected)
- Scripture: `two_strike_split`, `growth_as_default` (subtraction arc),
  `infrastructure_self_exempt` (the guard defended its kill switch)
