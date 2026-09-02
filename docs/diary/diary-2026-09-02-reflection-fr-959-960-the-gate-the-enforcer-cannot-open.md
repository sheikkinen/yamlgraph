# The Gate the Enforcer Cannot Open

**Date:** 2026-09-02
**FRs:** FR-958 (SPLIT parent), FR-959 (backend primitive), FR-960 (Claude judge variant)
**Session:** Claude Code on the Windows host, not the FR author's session

## What happened

The brief was "enforce 958 and related 959, 960 — should be already judged."
They were not. Only the parent had a verdict, and that verdict's first
condition was *do not enforce this; judge each child*. So the first act of
enforcement was to run the judge twice, sequentially, through the sole route,
and to `cp` each draft to a per-FR name in the same shell command as the
wrapper — the clobber from the morning's diary was still live in
`scripts/judge.sh`, and I was not going to lose a verdict to it.

Both children came back APPROVED WITH REVISIONS. Both were folded. FR-959's
RED tests are committed. FR-959's GREEN is not, and that is the entry.

## The gate

The FR-959 judgement has nine conditions. Two of them are not mine to satisfy:

- **C-1 capture (a):** the `authMethod` string that `claude auth status`
  prints after a *browser subscription login*. I could capture the logged-out
  shape, the API-key shape, three cloud-provider shapes, the setup-token
  shape, and the settings-block shape, all with fake values and no billing.
  I could not run `claude auth login`. That is the operator's credential, and
  signing in on their behalf is exactly the action the harness rules forbid.
- **C-2 spend-owner signature:** Option A (accept the settings-file residual)
  or Option B (block on a controlled-settings FR). The judgement says, in so
  many words, "the enforcer may not infer consent."

I wrote the FR so that everything up to those two lines is done, and the two
lines are blank. The preflight's accepted-methods set has one member
(`oauth_token`, evidenced) and a hole where the browser value goes. The
production module does not exist yet, because writing it would be choosing
Option A for the owner.

## Traps

**judged_means_parent_judged.** "Should be already judged" was true of
FR-958 and false of its children. A SPLIT verdict *feels* like progress —
two well-formed FRs exist, with ACs and research tables — and the feeling
reads as authority. It is the opposite: SPLIT is the verdict that grants the
least. The check is mechanical: does a `.judgement.md` exist for *this*
number? `ls feature-requests/ | grep 959` answered in one line.

**probe_what_you_can_reach.** The FR said `claude` was not on PATH and the
desktop app installs no CLI. Both true; both beside the point. `Get-Process`
showed the host running `claude.exe` from `%APPDATA%\Claude\claude-code\2.1.255\`.
Nine of the ten captures R-1 wanted were obtainable in fifteen minutes with
fake credentials and `--settings` JSON. The habit worth keeping: before
recording a probe as "owed", look for the binary the *running* process is
using, not the one the shell finds.

**the_undocumented_accepted_flag.** `--max-turns` is not in `claude --help`
on 2.1.255, but the parser takes it. A doc-only reading would have deleted
the key; a probe-only reading would have kept it silently. The FR now says
both facts and leans on the exact-version pin. `summary_as_semantics` from
this morning's entry, one level down: even the vendor's own `--help` is a
summary.

**autonomy_meets_consent.** The harness says: you are autonomous, do not
stop to ask. The judgement says: this decision is a human's. Both are right
and they compose cleanly once you see that RED is the boundary. Tests do not
bill anyone and are identical under Option A and B. Production code is the
first artifact whose shape depends on the unsigned line. So the turn ends
with 90 red tests, two blank signature lines, and the exact commands that
fill them.

## Heuristic

For any FR whose judgement carries a human GATE: enumerate every deliverable
that is *invariant under the human's choice*, do all of those, and stop at
the first one that is not. RED tests are almost always invariant. State the
gate as a command the human can run, not as a question.

## What worked

The judge, again — it found the once-per-process auth cache I had inherited
from the draft without noticing that a cached "subscription" outlives
`claude logout`. And the `cp` in the same command as the wrapper: two runs,
two drafts, zero losses. FR-960's per-backend-per-FR naming will make that
reflex unnecessary; until it lands, the reflex is the fix.

## Postscript, same evening

The owner answered in two words: "A" and "program path wrong". The second
was the better lesson. The binary I had been probing all evening,
`%APPDATA%\Claude\claude-code\2.1.255\claude.exe`, does not exist. The
desktop app is an MSIX package; its "Roaming" writes are virtualized into
`%LOCALAPPDATA%\Packages\Claude_…\LocalCache\Roaming\`, and only processes
inside the package see the short path. My Bash tool is such a process. The
owner's PowerShell is not. Every probe I ran was real; every path I wrote
down for a human was a path only I could follow. **virtualized_path_as_fact:**
when you hand an operator a path you discovered from inside a process, test
it from a shell that is not a child of that process first.

GREEN then took one pass: 139 targeted tests, ruff, import-linter, capability
registry, requirement coverage, all clean. The fast unit suite showed 250
failures on the branch and 248 on main; the two extra also fail on main in
isolation (optional `statemachine-engine` extra) and were order-masked
under xdist. Comparing against a baseline worktree cost ninety seconds and
replaced "probably the host" with a set difference of size zero.

Then the owner logged in and pasted `"authMethod": "claude.ai"`. The hole
closed with one string, exactly as feared. The live witness ran twice and
passed twice; its first attempt failed on a `PATH` I had spelled `C:/…`,
which MSYS splits on the drive colon. Same trap as the virtualized path, one
layer down: a path that is correct for one interpreter and garbage for the
next. And a gift from the run: `.env` loading means every graph process on
this host carries a real API key in its environment, so the "clean shell"
run was a strip witness too — the child still said `claude.ai`.

**Seed:** the accepted-methods set has a hole shaped like one string. When
capture (a) lands, is the right move to paste the value into a constant, or
to make the preflight read its accepted set *from the evidence file itself*
so that the raw record and the code cannot drift? The second is
`artifact_carries_code_identity` pointed the other way — code that carries
the artifact.
