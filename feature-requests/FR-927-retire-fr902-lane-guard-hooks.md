# Feature Request: FR-927 Retire the FR-902 Lane-Guard Hook Machinery

**Priority:** HIGH
**Type:** Removal (R-6 subtraction)
**Status:** Proposed 2026-08-30 (operator-directed; RED committed same day, judgement pending)
**Effort:** 0.5 days
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
hook-created lane to deliver. Mark REJECTED/SUPERSEDED by this FR.

**Regression pin:** `.github/hooks/tests/test_fr902_retired.py`
(RED, committed with this FR) asserts structural absence:
no `lane_guard.py`, no session-worktree/session-checkpoint scripts or
registrations, no `FR902`/`fr902` tokens in `pre-command-guard.sh`, no
write-verb grep alternation outside the R-2 mutator fence, no
`FR902_ALLOW_OUTSIDE` anywhere in hook scripts. The test is permanent —
"gone never to return."

## Acceptance Criteria

- [ ] AC-01: `test_fr902_retired.py` passes — every structural-absence
      assertion green; the test itself carries no dependency on deleted
      fixtures
- [ ] AC-02: Hook suite green after deletion; no orphaned imports or
      fixtures; `pre-command-guard.sh` shrinks (line count recorded)
- [ ] AC-03: `session-probe.json` SessionStart/Stop entries for
      session-worktree.sh and session-checkpoint.sh removed; remaining
      hook registrations untouched
- [ ] AC-04: CAP-254 rewritten to retained scope; REQ descriptions match
      reality; `req_coverage.py --strict` green;
      `tests/unit/test_session_worktree_lifecycle.py` pruned to match
- [ ] AC-05: FR-925 marked SUPERSEDED with pointer here; FR-902 status
      updated to RETIRED (hook machinery) with pointer here
- [ ] AC-06: No `FR902_ALLOW_OUTSIDE` or lane-denial guidance survives in
      `CLAUDE.md` / `.github/copilot-instructions.md`; the FR-902 bullet
      in the Copilot Hooks section is replaced by a one-line retirement
      note
- [ ] AC-07: Changelog fragment (`type: removal`); diary reflection

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
