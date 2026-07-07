# Diary: FR-697 watcher2 Sanity Check Reflection

**Date:** 2026-07-07
**FR:** FR-697 — direct-to-main break-glass audit trail gate
**Branch:** feat/watcher2-inquisitor-main-bypass

## Trap

`audit_as_ritual` — three consecutive Inquisitor audits (255, 256, 257, 258) flagged
the same undocumented direct-to-main bypass batch without triggering a blocking gate.
The diary recorded the bypass; the bypass still landed. Documentation ≠ enforcement.

## What Happened

Four commits (`56230029`, `caf14330`, `2b265793`, `b17a8b5e`) were pushed directly to
`main` between 2026-07-04 and 2026-07-07, bypassing commitlint, diary-gate, and
changelog-gate. A diary entry for `56230029` explicitly noted "Bypassed rule
violations" — but that entry itself satisfied no gate, and the pattern recurred in
subsequent commits. The Inquisitor flagged the gap in audits 256, 257, and 258;
each audit named the next action explicitly ("add break-glass entry") and each was
ignored, making the audit cycle a ritual rather than a process.

## Root Cause

`reference/break-glass.md` defined a bypass procedure but contained no structured,
parseable ledger and no CI check enforcing it. Advisory documentation without a
mechanical gate is a post-mortem before the incident. The doctrine phrase
`detection_without_enforcement: "Lint without gate = advisory → add CI block or
remove claim"` directly names this pattern; it was violated here.

## What Worked

1. **Proportionality**: scope is minimal and single-responsibility — one script
   (`scripts/check_direct_push_breakglass.py`), one ledger section, one CI job
   (`breakglass-gate`), eight acceptance tests. No novel abstractions.
2. **Test quality**: all 8 AC tests use temporary git repos and subprocess execution
   to assert actual script exit codes and output content. None check file presence
   alone — they exercise behavior at the boundary.
3. **Traceability spine intact**: CAP-190 registered, REQ-YG-525 added to
   `ARCHITECTURE.md`, all tests carry `@pytest.mark.req("REQ-YG-525")`.
4. **Advisory-first**: `continue-on-error: true` avoids merge disruption while
   building baseline confidence. Promotion to blocking is explicitly deferred to a
   follow-on FR.
5. **Option C detection algorithm** (range = direct by maintainer assertion)
   documented in the FR, removing the need for GitHub API calls and keeping the
   script deterministic.

## Concern (minor)

The `novel_fandom` example event YAML files appear in the diff (26 one-line files,
each adding a trailing newline). These are unrelated to FR-697 and inflate the diff
stat. They do not affect correctness, but they dilute diff signal for reviewers.
Future enforce sessions should stage only FR-relevant files before committing.

**Seed:** If `breakglass-gate` is advisory and `continue-on-error: true`, what is the
escalation trigger that promotes it to blocking? Could the Inquisitor auto-escalate
a gate from advisory to blocking after N consecutive PR cycles where the gate fires
without a corrective commit — making recurrence count the promotion criterion?
