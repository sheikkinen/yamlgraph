# 2026-07-24 — The artifact contract caught the observability probe lying about its innocence

**Context:** first live run of the ported sole-route judge
(`scripts/judge.sh` on FR-758). The wrapper's artifact contract fired:
graph rc=0, but `tmp/draft-judgement.md` missing. The operator saved
the child transcript as `tmp/judge-fr.log` for forensics.

**What the forensics showed:** the child session *rendered a complete
judgement* — verdict, findings, frozen scope — then spent its final
turns trying every write route (`apply_patch` to repo, to session
state, `bash` heredoc) and losing each to `PermissionRequest hook
failed`. The full judgement text survived only inside the failed
heredoc in the transcript. The wrapper's design principle — *verify by
artifact, never exit code* — was vindicated on its first real
execution: the CLI exited 0 through all of that.

**Root cause (composition_bug, textbook form):** FR-743 A2 widened the
session-observability probe to all 16 hook events "for completeness."
Fifteen of those are fail-open notifications. The sixteenth,
`PermissionRequest`, is a fail-closed *decision* hook: the platform
parses handler output as a verdict, and the probe prints a plain-text
marker. Every component was correct — the probe fail-opens internally
(`|| true`, `exit 0`), the platform correctly fail-closes on a
malformed decision, the wrapper correctly refused the missing
artifact. The defect lived entirely in the registration policy that
connected them. And it was invisible in interactive sessions, where
the editor UI answers permissions — only a non-interactive child (the
judge adapter) ever consults the hook. The proof was an absence:
audit.jsonl holds probe entries for Stop/SessionEnd/PostToolUseFailure
from the same child session and **zero PermissionRequest entries in
all history**. The hook that never logs is the hook that never ran as
intended.

**The trap named:** call it *completeness_as_correctness* — a
subscription widened to "all events" treats a heterogeneous event
family as uniform. Events differ in failure polarity: observing a
notification costs nothing; observing a decision *is deciding*, badly.
The FR-743 probe was even labeled "fail-open everywhere" — true of its
exit code, false of its effect, because the receiving contract
inverted the polarity.

**Heuristic:** before registering any handler on a hook event, ask the
polarity question: is this event fail-open (notification) or
fail-closed (decision)? A handler whose output is not a valid decision
must never sit on a decision hook. Graduation candidate for the
Scripture boundaries list: `hook_polarity` — the hook registration is
itself a boundary where handler semantics meet platform contract.

**Also recorded:** `git commit --amend` takes the whole index — the
pathspec discipline that protects against foreign staged files does
not survive an amend. The two parallel-session diary files were swept
in silently; the mandatory post-commit `git show --stat` audit caught
it (second catch today). If foreign files are staged, amend is
forbidden; soft-reset and recommit with pathspec instead.

**Rite followed:** RED (`test_permission_request_decision_hook.py`,
witnessed failing) → GREEN (probe unregistered from PermissionRequest
only, empty registration left as documentation) → re-run judge →
artifact written, FR-758 judged APPROVED WITH REVISIONS end-to-end.
Both judge runs, before and after the fix, converged on the same
verdict — the pipeline's first real execution also became its first
regression test.

**Seed:** the platform's hook events should be classified once,
mechanically — a small registry (event → polarity) that the hook tests
assert against every `*.json` registration in `.github/hooks/`. Then
`completeness_as_correctness` can never recur here: widening a probe
to a decision hook fails a test, not a judge run. And: should the
probe's stdout contract be witnessed per event family, the way FR-743
set out to witness stdin?
