# Feature Request: A `clean-dirty-main` skill — classify main's dirt by provenance before touching it

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented 2026-09-10
([judgement](FR-1047-clean-dirty-main-skill.judgement.md), round 1,
APPROVED WITH REVISIONS; R-1–R-6 folded, none refused). C-1 and C-6 satisfied
by operator direction.
**Effort:** 1 day
**Requested:** 2026-09-10
**First consumer / first event:** the next agent handed the operator's
recurring three-word prompt "check dirty main" — witnessed 2026-09-03 and
again 2026-09-10, both times against the same failure class, both times
answered by an ad-hoc investigation instead of a route.
**Research:** in-body dispositioned solution-class table below (FR-889-style
equivalent record). The cause set is closed and enumerated from four
witnessed incidents plus the operator's own taxonomy; a five-persona fan-out
would generate alternatives to a decision procedure whose inputs are already
fixed by git plumbing.
**Prior art:**
[FR-889](FR-889-os-enforced-main-write-lock.md) — creates the OS lock whose
interaction with `git pull` produces the most common dirt class; this FR does
not change the lock, it classifies its debris.
[FR-698](FR-698-executor-neutral-worktree-tooling.md) — owns
`scripts/worktree.sh` including `sync` (unlock → pull → relock); this FR adds
the triage step `sync` lacks and calls `sync`'s own verbs for mutation.
[FR-241](FR-241-complete-worktree-teardown-self-heal.md) / CAP-102 — teardown
self-heal, the source of dirt cause (D) below; this FR classifies that
residue rather than changing teardown.
[FR-312](FR-312-watcher2-post-merge-main-sync.md) — automated post-merge main
sync for watcher2; that is a scheduled writer, this is an operator-invoked
diagnostic on a checkout already found dirty.

## Summary

Add a `clean-dirty-main` skill that answers "is this dirt safe to discard?"
by **provenance of content**, not by `git status` output. It assigns every
dirty path on the main checkout to one of three *evidence* classes and marks
exactly one of them safe — everything else, including every unsupported git
state and every failed probe, preserves and exits non-zero.

## Value Statement

An agent asked to clean main gets a per-path verdict with a named cause and
a safe action, instead of re-deriving the diagnosis from scratch and risking
the deletion of the only copy of somebody's work.

## Problem

The main checkout goes dirty routinely, and `git status` cannot distinguish
debris from work. Both look like ` M` and `??`.

Four causes are known to produce identical-looking status output. **These are
incident explanations, not classifier outputs** (R-1): the tool cannot prove
which one occurred, and A and D share a signature.

| ID | Cause | Evidence it leaves | Repo-committed witness? |
|----|-------|--------------------|-------------------------|
| A | **Partial pull against the FR-889 lock.** `git pull` writes unlocked paths (root docs, `examples/`, `changelog/`, `reference/`), then aborts `Permission denied` on the locked roots. HEAD never moves. | Bytes equal `origin/main:<p>` | **Yes** — [diary 2026-09-03](../docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md) |
| B | **Direct write to main.** A session authored into the shared checkout instead of a worktree (`one_session_one_repo`). | Bytes in no reachable commit — the only copy | No committed witness; the class the design exists to protect |
| C | **Stale buffer from a sibling session.** The editor flushes a buffer held from another branch/older revision into main's tree. | Bytes in some other commit | No committed witness — hypothesis only |
| D | **Worktree teardown residue** (CAP-102 self-heal). The lane's committed changes reappear as working-tree modifications on main's unlocked paths. | Bytes equal `origin/main:<p>` — indistinguishable from A | No committed witness — hypothesis only |

Only cause A is witnessed by a committed artifact in this repository. C and D
rest on operator-memory notes outside the repo's input closure and are recorded
here as hypotheses, not proof (R-1).

The operator's own framing splits the same space by file age — *new file*
versus *old file that has been committed in the past* — which is the useful
intuition, but the decidable question is narrower: **do these exact bytes
appear at this exact path in `origin/main`?** Everything else is unproven.

**Why the existing pieces do not close it:**

- `scripts/worktree.sh sync` is unlock → pull → relock with no triage. Against
  cause-A residue the pull refuses (local changes / untracked files would be
  overwritten) and `sync` returns non-zero with main relocked and still dirty.
  Verified in the 2026-09-03 incident.
- The recovery recipe exists in two places — `/memories/repo/hook-lessons.md`
  (FR-889 section) and
  [docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md](../docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md)
  — and neither is reachable from the prompt that needs it. Both incidents
  were investigated from zero.
- Cause B is the expensive one and has **no** recorded procedure at all.
  Discarding a cause-B path destroys work with no recovery path (untracked
  content is not in the reflog).

**Witnessed incidents:**

1. **2026-09-03** — 6 modified + 12 untracked, HEAD `b09d1a7f`, 4 behind. All
   cause A. Recovery took a wrong turn: the reappearing dirt was attributed to
   a live parallel session; the writer was the investigation's own failed pull.
   Cost: one operator correction.
2. **2026-09-10** — HEAD `3343b721`, one untracked path
   (`reference/github-batch-hosting.md`). Misclassified as cause B (a
   `one_session_one_repo` leak) and deletion was proposed; it was cause A. The
   subsequent `git pull --ff-only` re-created the full 13-path residue, which
   again presented as an active parallel writer. All 13 byte-matched
   `origin/main`; recovered to `9acb6117`. Cost: a proposed-but-not-executed
   deletion, and a second full re-derivation of a documented diagnosis.
3. **2026-08-30** — CAP-102 teardown left a lane's changes on main. Recorded
   only in operator memory (`/memories/repo/hook-lessons.md`), which is outside
   this repository's committed input closure — cited as a hypothesis for cause
   D, not as proof (R-1).
4. **2026-08-2x** — a sibling session switched branches under a shared
   checkout; commit and push landed on the other session's branch. Same
   uncommitted source, same status: cause-C neighbourhood, unproven.

Note the asymmetry that makes this worth a route: one evidence class is
provably recoverable and every other state — including states the tool cannot
interpret — is not. The probe is cheap (`git show`, `git cat-file`,
`git log --all --find-object`); the failure is unrecoverable. The current
practice runs the expensive judgement in an agent's head, twice, and got the
class wrong the second time.

## Ideal Result

The operator types "check dirty main". One read-only command prints, for every
dirty path, the evidence class, the bytes/OIDs that establish it, and the
sanctioned action. The report is **advisory and snapshot-bound** — a read-only
tool cannot prevent a later independent git command (R-4) — so its force comes
from failing closed: any preserve, unsupported, or error count exits non-zero,
and the skill stops before touching anything. Cleaning is then the mechanical
execution of that table over explicit pathspecs, using verbs that already exist.

## Proposed Solution

Minimal path back from the ideal: **one read-only classifier + one skill that
routes to it.** No new lock mutator, no new git wrapper, no automation.

### 1. `scripts/dirty_main_triage.py` (read-only)

**Preconditions (fail closed, R-2).** Target is the shared main checkout, not a
linked worktree; `HEAD` is on `main`; `origin/main` resolves. Any precondition
failure exits non-zero without classifying.

**Status domain.** `git status --porcelain=v1 -z --untracked-files=all`, so
paths are NUL-delimited and never quoted/ambiguous. Only two entry shapes are
supported in v1: unstaged tracked regular-file modifications, and untracked
regular files.

**Evidence classes (R-1)** — first hit wins:

| Probe | Class | Disposition |
|-------|-------|-------------|
| Working bytes at `p` equal blob at `origin/main:p` | `TARGET_IDENTICAL` | **SAFE** — the only safe class |
| Bytes occur in another reachable commit (`git cat-file` + `git log --all --find-object`) | `KNOWN_BLOB` | PRESERVE/REVIEW; report source revision |
| Bytes in no examined reachable ref | `UNSEEN_BLOB` | PRESERVE |

**Everything else preserves.** Staged entries, deletions, renames/copies,
unmerged entries, type changes, symlinks, submodules, non-regular files and
malformed status records are `UNSUPPORTED/PRESERVE`. Every git, filesystem,
decode or lookup failure is `ERROR/PRESERVE` — a failed probe must never
degrade into "no match" (R-2).

**Output.** Per path: repository root, `HEAD` OID, `origin/main` OID, status
code, unambiguously escaped path, working-content hash, class, disposition.
Summary line `safe=<n> preserve=<n> unsupported=<n> errors=<n>`. Exit 0 only
when the tree is clean or every path is `TARGET_IDENTICAL`; any other result
exits non-zero (R-4).

The script **never mutates** — no `chmod` (which the FR-889 lock-mutator fence
denies anyway), no `checkout`, no `clean`. Mutation stays with
`scripts/worktree.sh unlock-main | lock-main` and plain git, invoked by the
agent after reading the verdict.

### 2. `.github/skills/clean-dirty-main/SKILL.md`

Description keyed to the phrases that actually occur: "check dirty main",
"clean dirty main", "main is dirty", "regression on main?". Contents:

- Run the triage first. **Its output is the input to every later step**; no
  discard without it.
- **Stop on anything non-safe (R-3).** A non-zero exit, or any
  preserve/unsupported/error count, halts the procedure *before* unlocking or
  mutating anything — including the paths marked safe.
- **All-safe recipe only:** `unlock-main` → `git checkout -- <explicit paths>`
  → `rm` the explicit untracked residue paths → `scripts/worktree.sh sync`
  (which owns pull and relock). No repository-wide `checkout`, `restore`,
  `clean`, or `git clean -fd` — the FR's first draft carried exactly that
  hazard. The FR-889 lock is restored on every exit path, success or failure.
- **Re-run triage immediately before cleanup**, and after any tree/ref change.
  A changed snapshot aborts the procedure (R-4).
- **PRESERVE handling:** stop, report path + content hash, hand control to the
  operator. The skill does **not** claim to transport the content —
  `worktree.sh new` creates a lane but does not move dirty files (R-3).
- The named trap `partial_pull_against_lock`, and its counter-diagnostic:
  dirty + byte-identical to `origin/main` is an interrupted sync, not a
  regression, and not a parallel writer.

### 3. Route the prompt

One line in `.github/copilot-instructions.md` pointing "check dirty main" at
the skill, so the knowledge is reachable from the phrase that needs it —
the gap that made incident 2 a full re-derivation.

## Acceptance Criteria

<!-- Superseded by the judgement's revised list (R-1..R-6). -->

- [ ] AC-01: On a clean shared `main` checkout with resolvable `origin/main`, `scripts/dirty_main_triage.py` exits 0 and prints `safe=0 preserve=0 unsupported=0 errors=0`.
- [ ] AC-02: A tracked regular file whose working bytes equal `origin/main` at the same path is `TARGET_IDENTICAL`; an all-safe fixture exits 0 with `safe=1`.
- [ ] AC-03: An untracked regular file whose bytes equal `origin/main` at the same path is `TARGET_IDENTICAL`, covering the committed 2026-09-03 incident shape.
- [ ] AC-04: Bytes found only in another reachable commit are `KNOWN_BLOB`, name a source revision, count as `preserve=1`, and produce a non-zero exit.
- [ ] AC-05: Bytes absent from examined reachable refs are `UNSEEN_BLOB`, count as `preserve=1`, and produce a non-zero exit.
- [ ] AC-06: `git status --porcelain=v1 -z --untracked-files=all` is parsed without path ambiguity; fixtures cover spaces, a leading dash, a newline/control character, and binary content.
- [ ] AC-07: A non-main branch, linked worktree, missing `origin/main`, staged entry, deletion, rename/copy, conflict, type change, symlink, submodule, non-regular file, or failed git/filesystem probe is never safe and produces a non-zero exit with an `unsupported` or `errors` count.
- [ ] AC-08: A mixed fixture containing one `TARGET_IDENTICAL` path and one preserve/unsupported/error path exits non-zero; the skill performs no cleanup for that result.
- [ ] AC-09: Before and after every classifier run, `HEAD`, refs, index, working-tree bytes, untracked-path set, and lock state are identical; output records root, `HEAD`, `origin/main`, status, escaped path, and content hash.
- [ ] AC-10: The skill has valid YAML frontmatter, contains the literal trigger `dirty main`, invokes triage first, reruns it after tree/ref changes, and stops before mutation on any non-zero or non-safe result.
- [ ] AC-11: The skill contains no `git clean -fd`, repository-wide discard, or automatic cause-B transport; the all-safe recipe uses explicit `-- <path>` pathspecs and restores the FR-889 lock on every documented exit.
- [ ] AC-12: `.github/copilot-instructions.md` routes the literal phrase `check dirty main` to `.github/skills/clean-dirty-main/SKILL.md`, with no unrelated doctrine edits.
- [ ] AC-13: `tests/unit/test_dirty_main_triage.py` is committed RED before production changes and every test is marked `REQ-YG-678`; `capabilities/CAP-272-clean-dirty-main-triage.yaml` registers that requirement and `python scripts/req_coverage.py --strict` passes after capability aggregation.
- [ ] AC-14: `changelog/unreleased/fr1047-clean-dirty-main-skill.md` records the operator-facing route and cites `REQ-YG-678`.
- [ ] AC-15: `pre-commit run --files` over the exact D-1–D-8 changed paths exits zero.
- [ ] AC-16: The FR records implementation status, RED/GREEN evidence, decisions, and deviations, and a Distill entry under `docs/diary/` contains a concrete heuristic and `Seed:`.

**Number availability verified 2026-09-10:** `CAP-272` is free (max is CAP-271)
and `REQ-YG-678` is free (max is REQ-YG-677) — the judge's pinned identifiers
are usable as written.

## Judgement fold (round 1, 2026-09-10)

[Judgement](FR-1047-clean-dirty-main-skill.judgement.md): APPROVED WITH
REVISIONS. All six revisions folded; none refused.

| # | Revision | Fold |
|---|----------|------|
| R-1 | Classify evidence, not historical cause | Folded. Cause table relabelled as incident explanations with a "repo-committed witness?" column; only A is witnessed. Classifier now emits `TARGET_IDENTICAL` / `KNOWN_BLOB` / `UNSEEN_BLOB`. Incidents 3–4 marked as uncommitted-memory hypotheses. |
| R-2 | Define the status domain and fail closed | Folded. `--porcelain=v1 -z`, preconditions, v1 supported shapes, `UNSUPPORTED`/`ERROR` classes, four-count summary. |
| R-3 | Remove repository-wide cleanup | Folded. `git clean -fd` deleted from the recipe; explicit pathspecs only; stop-before-unlock on any non-safe path; the "move to a worktree" claim removed as undefined. |
| R-4 | Honest, snapshot-bound safety claim | Folded. "structurally impossible" replaced with advisory + fail-closed; re-run triage before cleanup; exit-code contract. |
| R-5 | Pin RED tests and traceability | Folded. `REQ-YG-678`, `CAP-272`, `tests/unit/test_dirty_main_triage.py`, changelog fragment, diary entry pinned in D-1–D-8. Both identifiers verified free. |
| R-6 | Test the safety contract, not keywords | Folded. Presence-only ACs replaced with behavioral assertions (AC-10, AC-11). |

### Deliverables (scope frozen)

| # | Surface |
|---|---------|
| D-1 | `feature-requests/FR-1047-clean-dirty-main-skill.md` |
| D-2 | `scripts/dirty_main_triage.py` (read-only classifier) |
| D-3 | `.github/skills/clean-dirty-main/SKILL.md` |
| D-4 | One literal route entry in `.github/copilot-instructions.md` |
| D-5 | `tests/unit/test_dirty_main_triage.py` (RED before production) |
| D-6 | `capabilities/CAP-272-clean-dirty-main-triage.yaml` + regenerated `ARCHITECTURE.md` |
| D-7 | `changelog/unreleased/fr1047-clean-dirty-main-skill.md` |
| D-8 | One FR-1047 Distill entry under `docs/diary/` with a `Seed:` |
| D-9 | `docs/confessions.md` — added by scope amendment (review P5); the `# noqa: S603` ledger entries the confession gate requires for the two git helpers. Not foreseen at judgement time. |

**Not authorized:** changes to `scripts/worktree.sh`; FR-889 lock roots,
permissions, marker, audit or relock behaviour;
`.github/hooks/scripts/checks/main_write.py`; hook/CI/branch-protection policy;
watcher teardown or post-merge flows; automatic cleanup in `sync`; a new git
wrapper or mutating classifier mode; YAMLGraph runtime changes; classifying any
unsupported git state as safe.

**Blocking conditions:** C-1 (human review of the advisory judgement) and C-6
(human review of the `.github/copilot-instructions.md` diff) were both
satisfied by the operator on 2026-09-10 ("enforce. pr. outsider. merge").

## Implementation record

**Status:** Implemented 2026-09-10.

| Phase | Commit | Evidence |
|-------|--------|----------|
| RED | `9393f0fc` | 29 failing tests, `REQ-YG-678`. No vacuous passes: the three precondition tests assert a specific `REFUSED:` reason and the read-only test asserts a summary line was produced, so an absent script cannot satisfy them. |
| GREEN | this commit | 29 passing. `ruff` clean; `radon` below the reporting threshold after `unreadable_reason` was split out of `classify` (C(12) → under C). |

**Dogfood evidence — the real incident replayed.** A scratch clone was reset to
`3343b721` (the incident HEAD) and the exact 13 paths restored from
`origin/main` (`9acb6117`), reproducing the 2026-09-10 state byte for byte:

```
safe=13 preserve=0 unsupported=0 errors=0   rc=0
```

`reference/github-batch-hosting.md` — the path this session first misread as
unique work and proposed deleting — classifies `TARGET_IDENTICAL  SAFE`. Adding
one novel file to the same snapshot flips the run closed:

```
safe=13 preserve=1 unsupported=0 errors=0   rc=1
NOT SAFE TO CLEAN: every path above must be dispositioned by a human ...
```

That is the asymmetry the FR was filed for, demonstrated on the incident that
prompted it.

**Deviations from the frozen scope:** one. `docs/confessions.md` was not in the
judgement's deliverable list but is required by the noqa-confession gate for the
two `subprocess.run` git helpers (CONF-487, CONF-488). Recorded as D-9 above.
The earlier claim of "no deviations" in this record was wrong and was corrected
after review finding P5.

## Review round 1 (PR #655, 2026-09-11)

`scripts/review.sh 655` — **not approved**, five blocking findings. Three were
real defects that the 29-test suite did not catch; all three were in the one
class this FR exists to prevent — a path licensed SAFE that must not be.

| # | Finding | Disposition |
|---|---------|-------------|
| P1 | A symlink in `origin/main` is stored as a blob, so a local *regular* file whose bytes equal the symlink target was classified `TARGET_IDENTICAL SAFE`. | **Fixed.** `origin_blob` now checks the tree mode against `REGULAR_MODES`; symlink (`120000`) and gitlink targets return None and fall through to preserve. Regression test `test_origin_symlink_target_is_never_safe`. |
| P2 | `parse_status` mapped every malformed record to `??`, so a malformed entry could reach the safe class. | **Fixed.** Malformed records get the `MALFORMED` code, which is outside `SUPPORTED_CODES` by construction. Regression test `test_malformed_status_record_is_never_untracked`. |
| P3 | `git log --find-object` also reports commits that DELETED the object; the classifier could name a deletion commit as a blob's source — a false provenance claim. | **Fixed.** Candidates are now verified with `tree_contains` before being reported. Regression test `test_known_blob_names_a_revision_that_contains_it` (add-then-delete fixture). |
| P4 | Gate C-2 requires the RED tests to be committed before the capability surface; commit `9393f0fc` contains both. | **Refused, with witness.** C-2's ordering is unsatisfiable for a *new* requirement ID. With `capabilities/CAP-272-*.yaml` absent, `python scripts/req_coverage.py --strict` exits 1 ("REQ-YG-678 referenced by 29 test(s)" with no owning capability), so a tests-only commit is blocked by the pre-commit gate. Satisfying C-2 would require `SKIP=req-coverage-strict`, i.e. bypassing an enforced gate to satisfy an advisory condition. The capability and tests are committed together, before any production code — which is what C-2 protects. |
| P5 | `docs/confessions.md` is outside the frozen deliverables, and the record claimed no deviations. | **Fixed.** D-9 added above; the deviation is recorded accurately. |

Non-blocking note (AC-09 index guarantee) also folded: `test_classifier_mutates_nothing`
now compares `.git/index` bytes, not just `git diff --cached`.

**What this round shows.** The first suite was written by the same agent that
wrote the implementation, and it tested the contract as that agent understood
it. All three real defects came from git semantics the author did not think to
question — blobs carry a mode, `--find-object` spans deletions, a malformed
record is not an untracked file. Independent probing found them in one pass.

**Decisions taken during enforcement:**

- Three tests initially passed in RED purely because the script did not exist.
  They were strengthened to require a named refusal reason rather than any
  non-zero exit — a negative assertion that a missing binary can satisfy is not
  a witness.
- Four unnecessary `# noqa: S603` comments in the test module tripped the
  confession gate; `tests/**` already carries that per-file ignore. Removed
  rather than confessed.
- `classify` was split (`unreadable_reason`) to keep the symlink and
  regular-file checks legible; behaviour unchanged, suite green before and
  after.

## Alternatives Considered

| # | Solution class | Disposition |
|---|----------------|-------------|
| S1 | **Do nothing; rely on the diary + memory entries.** | Rejected: both artifacts existed before incident 2 and neither was consulted. Knowledge not reachable from the triggering phrase is not knowledge in force. |
| S2 | **Teach `worktree.sh sync` to auto-clean residue.** | Rejected: makes an automatic discard decision on a class (B) where discard is unrecoverable, inside a verb agents run reflexively. The triage must be a separate, read-only, human-read step. |
| S3 | **Remove the FR-889 lock so pulls stop half-applying.** | Rejected: the lock is the only write barrier on main and prevents cause B, the expensive class. Trading an unrecoverable failure for a recoverable one is backwards. |
| S4 | **Make the pull atomic (pull in a temp clone, then swap).** | Rejected: large blast radius on the shared checkout, and it addresses only causes A and D. B and C are unaffected. |
| S5 | **Read-only classifier + skill, mutation via existing verbs.** | **Chosen.** Smallest surface that separates the safe classes from the unsafe one, adds no new lock mutator (clearing the FR-889 fence), and makes the recorded recipe reachable from the operator's actual prompt. |
| S6 | **Pre-commit / CI gate that fails when main is dirty.** | Rejected: main's dirt is a local working-tree condition; CI never sees it, and a pre-commit gate fires only when someone is already committing — after the risky moment, not before. |

## Related

- [docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md](../docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md) — cause A, first recorded recurrence and the recovery recipe.
- `scripts/worktree.sh` — `lock-main` / `unlock-main` / `sync` (FR-889, FR-698).
- `.github/hooks/scripts/checks/main_write.py` — the lock-mutator fence the classifier must not trip.
- `/memories/repo/hook-lessons.md` — FR-889 section (causes A and D).
