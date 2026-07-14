# Feature Request: FR-728 Session-Safe Release and Commit Hygiene — Kill the Shared-Scratch Race

**Priority:** HIGH
**Type:** Bug / Process hardening
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-07-14
**Spawned by:** v0.5.13 release commit (889ef54b) carrying a parallel session's
FR-727 judgement text as its message — `scripts/release.sh` L29–31 writes
`tmp/msg.txt` then commits it, and the parallel session overwrote the file in
the gap. Third strike of the shared-workspace race in one day.
**Related:** reference/release-checklist.md, .github/skills/release-version,
Scripture conventions (multi-line commits via `tmp/msg.txt`), NC-359
second-strike rule (ninchat), diary-2026-07-14-the-seam-debt-collector.md

## Summary

Two parallel agent sessions in one working tree communicate through three
unreserved shared channels: the git index, the `tmp/msg.txt` scratch file,
and the working tree itself. All three raced today, and one race reached a
**pushed release commit**. Make the release script atomic against all three,
and change the doctrine's commit-message convention from a fixed shared path
to session-unique paths.

## Condemning evidence (all 2026-07-14, plus one prior)

1. **v0.5.13 (this FR's trigger):** `release.sh` wrote
   `chore(release): v0.5.13 changelog freeze` to `tmp/msg.txt`; the parallel
   FR-727 session overwrote it before `git commit -F` ran. The release commit
   subject is FR-727 judgement text; the parallel session's staged FR-727
   files also rode into the release commit. Pushed before detection; repaired
   via annotated tag + release notes as the record.
2. **7c2ee15e:** parallel session's doc-sweep commit swept this session's
   staged files (index race, second strike per repo memory).
3. **icpc WIP destruction:** `git add -u` + `git checkout --` in one session
   destroyed the other's tracked-modified files; recovered only because
   pre-commit's stash patches happened to hold the diff.
4. **2026-07-10 (ninchat 8d339e7):** first recorded strike; NC-359 diary set
   the "third strike graduates to doctrine" rule. This is the third strike.

## Proposed Solution

### 1. `scripts/release.sh` becomes session-atomic

- **Message file:** `MSG=$(mktemp)` — never `tmp/msg.txt`. Clean up on exit.
- **Pre-flight staging guard:** abort with a named error if
  `git diff --cached --quiet` fails (someone else's staged files would ride
  into the release commit — evidence #1 rode exactly this way).
- **Post-commit self-check:** after committing, verify
  `git log -1 --format=%s` matches `^chore\(release\): v` **before** tagging;
  on mismatch, abort loudly without tagging (the tag is the release record —
  it must never point at a commit whose message lost a race).

### 2. Doctrine amendment (Scripture convention)

- The convention "write to `./tmp/msg.txt` and `git commit -F ./tmp/msg.txt`"
  becomes "write to a **session-unique** file (`tmp/msg-<topic>.txt` or
  `mktemp`)". The fixed shared path is the defect: it is a mailbox with two
  writers and no lock.
- Add the shared-workspace rules from repo memory as a conventions bullet:
  explicit file lists only (no `git add -u`/`add .` in a shared tree); no
  `checkout --`/`restore` on files the session did not modify.

### 3. Out of scope (recorded as seeds, not built)

- Worktree-per-interactive-session ("one session, one repo") — the
  structural cure; belongs to a chaplain proposal with its own design
  (`.chaplain/worktrees/` precedent exists for the FSM runtime).
- Any locking daemon or index arbitration — over-engineering for a
  two-session workspace; the guards above make the blast radius zero for
  the release path, which is the only path that tags.

## Acceptance Criteria

- [ ] AC-01 RED — test asserting `scripts/release.sh` contains no literal
      shared scratch path (`tmp/msg.txt`) and does use `mktemp`; plus a
      harness test: with a file pre-staged, `release.sh` aborts before
      freezing/bumping anything (guard fires first, tree untouched).
- [ ] AC-02 — harness test: when the commit subject does not match
      `^chore\(release\): v` after commit (simulated by a hook or injected
      message), the script exits non-zero and **no tag exists**.
- [ ] AC-03 — happy path: on a scratch repo fixture, `release.sh X.Y.Z`
      produces exactly one commit (`chore(release): vX.Y.Z ...`), the frozen
      fragment dir, both version bumps, and a tag pointing at that commit.
- [ ] AC-04 — copilot-instructions.md convention updated to session-unique
      message files + the two shared-tree rules; the release skill and
      reference/release-checklist.md updated to match.
- [ ] AC-05 — changelog fragment; diary reflection naming the trap
      (shared scratch = unlocked mailbox) and pointing the worktree seed at
      the chaplain inbox.

## Alternatives Considered

- **Fix nothing, rely on care:** three strikes in one day under active care
  falsifies this.
- **Global lockfile around git operations:** cross-session coordination
  primitive nobody owns; the release path is the only one that tags, so
  hardening it plus unique message files removes the observed blast radius.
- **Force-rewriting the mislabeled release commit:** rejected — it was
  already on origin/main; history rewrite on main is a bigger hazard than a
  mislabeled subject with an annotated-tag record.
