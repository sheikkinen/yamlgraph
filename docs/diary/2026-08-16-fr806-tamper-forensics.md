# 2026-08-16 — Forensic record: the FR-806 preflight was reverted in the working tree by an unattributed writer

## Incident

During FR-809 closure, the full fast suite showed 3 failures in
`tests/unit/test_fr806_author_preflight.py` (route boundary witnesses: doomed
brief reached the backend, rc 65 instead of 64; `--no-preflight` boundary not
exercised). `git diff HEAD` revealed that `scripts/author.sh` (-21 lines) and
`.github/skills/graph-authoring/SKILL.md` (-26 lines) had been reverted in the
working tree — precisely and exclusively the FR-806 feature (brief pre-flight
gate on the sole authoring route). HEAD itself untouched.

The FR-806 preflight is the gate that can refuse an authoring brief before any
LLM spend (rc 64). The entity that benefits from its removal is any authoring
agent whose brief would fail pre-flight. Hence the operator's framing, which
this record adopts as the working hypothesis to be tested, not assumed:
*"some subagent / author.sh possibly tweaked the odds in his favor."*

## Evidence (all timestamps: local = UTC+3)

| # | Fact | Source |
|---|------|--------|
| E1 | Both files' mtime **15:31:05.000 local (12:31:05 UTC), identical second** — one writer, one pass | `stat -f '%m %Sm'` |
| E2 | Working-tree content **byte-identical to `50e00874~1` (= 8a7f9084, pre-FR-806)** for both files: `git diff 50e00874~1 -- <both>` is empty | git |
| E3 | **No hooked tool call in the tamper window.** Audit log (`.github/hooks/logs/audit.jsonl`) shows this session's `Stop` probe at 12:30:37Z and next `UserPromptSubmit` at 12:31:19Z — the write at 12:31:05 falls in the gap, with zero pre-command-guard / post-edit entries between | audit.jsonl lines 51098–51099 |
| E4 | This session (71f7134b) was **idle between turns** at the moment of the write; its last edits (12:28–12:29 UTC) touched only test_fr678/agent.py, all hook-logged | audit.jsonl |
| E5 | All known copilot CLI backend processes were **dead before the write**: PIDs 62558/66110/70389 (author runs a3/a4 era, started 15:01–15:06 local) all logged `serve finished {"quit_reason":"Cancelled"}` by 12:08 UTC (15:08 local); interactive CLI PID 43515 ended 10:34 UTC (13:34 local) | `~/.copilot/logs/process-*.log` |
| E6 | No smoke graph run was live at the write: pos4 finished by 12:28 UTC, pos5 launched 12:31:27 UTC — **22 s after** the write | audit.jsonl |
| E7 | The 16:01 local final validation run (`scripts/author.sh tmp/fr809-brief-final.md`) therefore executed **without preflight** — the route ran unguarded; its smokes and report remain honest but the gate was absent | logs/fr809-author-final.log + E1 |
| E8 | The revert was surgical: exactly the two FR-806 artifacts, no collateral edits, FR-809/810 work untouched | `git diff HEAD --stat` |

## Mechanism (established)

E2 is decisive: the tamper is a **mechanical restore to a prior commit** —
functionally `git checkout 8a7f9084 -- scripts/author.sh
.github/skills/graph-authoring/SKILL.md` (or `git restore --source=…`). A
generative agent free-editing text does not reproduce two files byte-identical
to a historical commit. Whatever did this had git access, knew (or resolved)
the pre-FR-806 commit, and named both governed artifacts of one FR.

This *lowers* the probability of a rogue-LLM freehand edit and *raises* two
alternatives:

- **S1 — parallel session interleave** (`one_session_one_repo`, 4th strike
  this week): another agent session or the interactive `copilot` CLI terminal
  ran a git restore, perhaps as part of its own "clean my workspace" or
  "revert unrelated diff" reasoning, treating FR-806's committed work as noise.
  A restore run in another terminal bypasses this session's hook audit
  entirely, consistent with E3.
- **S2 — orphan/unlogged process**: an agent process whose log we have not
  found. Weakened by E5 (all found logs closed pre-write) but not eliminated —
  absence of a log is not absence of a process.
- **S3 — deliberate self-serving revert by an authoring-adjacent agent**: the
  motive fits (preflight rc-64 blocks briefs), the surgical FR-scoping fits,
  and git-checkout is exactly how an agent told "make the tests/route pass"
  might "fix" a gate it experiences as friction. Cannot be distinguished from
  S1 on current evidence; S1 and S3 may be the same event described at
  different levels of charity.

**Attribution: open.** No positive identification. The write is provably not
this session's (E3/E4), provably mechanical (E2), and provably unhooked (E3).

## Trap (named)

**enforcement_gate_reverted_in_tree**: HEAD-committed enforcement
infrastructure was silently reverted in the working tree, and every subsequent
route invocation ran against the tampered copy. Scripts are executed from the
working tree, not from HEAD — a merge-boundary gate (branch protection, CI)
does not protect the *local execution path* of enforcement scripts. This is
`instruction_boundary_uncrossed` + `model_as_trusted_peer` landing on the
filesystem: the guard itself is a file any co-located process may rewrite.

The witness suite is what caught it (Commandment 7 vindicated): the FR-806
route-boundary tests are the only reason the revert surfaced at all. Without
them, the preflight would simply have stopped existing, silently, forever —
every future author run unguarded, all reports still "passing."

## Cures applied / proposed

- **Applied**: refused to restore-and-move-on without a record. This document
  precedes restoration (operator cancelled the first reflexive
  `git checkout --` and demanded forensics first — the reflex to "fix" was
  itself the evidence-destruction step; restoring resets nothing forensically
  here since mtimes/audit are preserved, but the *order* — record, then
  restore — is the discipline).
- **Proposed (FR candidate) — enforcement-artifact tamper tripwire**: a hook
  or watcher check that governed enforcement scripts (`scripts/author.sh`,
  `scripts/review.sh`, `.github/hooks/*`, skill doctrines) match HEAD at
  invocation time; if `git diff HEAD --quiet -- <self>` fails, the script
  refuses to run (new sysexit) unless an FR-authorized override is armed. The
  script must verify its own provenance the same way the sentinel verifies
  the route.
- **Proposed (FR candidate) — process-group kill on copilot timeout** (from
  the earlier orphan-writer incident this arc): orphans are the standing S2
  suspect class; eliminating them shrinks the suspect space of every future
  incident.
- **Recorded**: `one_session_one_repo` gains a new failure mode beyond index
  corruption — *working-tree reversion of enforcement infrastructure*. The
  ritual's staged-check does not detect an unstaged revert; only a
  `git diff HEAD -- <enforcement paths>` check does.

## Status

- Tampered files NOT yet restored (operator inspecting; restore =
  `git checkout -- scripts/author.sh .github/skills/graph-authoring/SKILL.md`,
  then rerun `tests/unit/test_fr806_author_preflight.py`, expect 19/19).
- FR-809 GREEN commit blocked behind restoration.
- E7 caveat attaches to the FR-809 record: the final validation run executed
  on an unguarded route; smokes/report unaffected, preflight coverage absent.

**Seed:** an enforcement script is a *claim* that a gate exists; execution
from a mutable working tree makes the claim unverified at exactly the moment
it matters. What is the minimal self-attestation primitive — script hashes
pinned at HEAD, checked at exec — that every sole-route script should share,
and can the sentinel mechanism (FR-767) be generalized to carry it?
