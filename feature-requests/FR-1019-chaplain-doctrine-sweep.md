# Feature Request: Doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)

**Priority:** LOW
**Type:** Enhancement (docs only; two-line Scripture edit — human read before merge)
**Status:** Judged — APPROVED WITH REVISIONS round 2 (2026-09-06, [judgement](FR-1019-chaplain-doctrine-sweep.judgement.md); round 1 REJECTED, its R-1..R-5 folded). Round-2 R-1..R-4 folded below. Authority activates after human review of the round-2 draft (C-1, C-2); nothing implemented yet.
**Effort:** 0.5 day
**Requested:** 2026-09-06
**Plan:** [FR-1010](FR-1010-chaplain-archival-plan.md) Phase 3. Prerequisite FR-1012 merged (`BASE = 36591389e2fdfedf9ba5ae6362effad1c64cd06e`). Supersedes [FR-1013](FR-1013-chaplain-doctrine-sweep.md) (REJECTED — process outgrew the change; the edits below are the same).
**First consumer / first event:** a new agent session reads `## Sermon of the Chaplain` → `docs/development-process.md` § 3 → `.chaplain/scripts/start-system.sh` (ENOENT).
**Research:** [FR-1010 § Alternatives Considered](FR-1010-chaplain-archival-plan.md#alternatives-considered-r-1-six-solution-classes) — the umbrella plan's six-class comparison (delete-only, banner-and-keep, archive-repo, …) is the research for every phase, and Phase 3 is its "active docs point at the archive; historical docs are not rewritten" leg; no alternative is specific to this phase because the edit set is fixed by what FR-1012 deleted. `is_this_a_graph`: **no** — a fixed, deterministic set of document edits with no per-item model call.
**Prior art:** FR-1011 (moved the one Scripture *path*), FR-1012 (wrote `docs/archive/chaplain.md`, the single archive pointer), FR-1013 (rejected; see its § Judgement for what not to repeat: census, baseline, new REQ, 421-line test).

## Problem

The Chaplain runtime is gone (FR-1012); the doctrine and reference documents still describe it as the way work gets done.

## Ideal Result

No live doctrine or reference document presents the Chaplain, its inbox, or the Inquisitor as a running part of the process; every remaining mention is past tense or a link to `docs/archive/`. Scripture changes by two lines. Nothing historical (FRs, diary, changelog, memento, ebook) is touched.

## Change

**Live edit set** (the files in which the retired route must be absent — AC-2):

| File | Edit |
|---|---|
| `.github/copilot-instructions.md` | `## Sermon of the Chaplain` → `## Sermon`; drop "chaplain pipeline, " from the canonical-sources clause. Nothing else. |
| `docs/development-process.md` | intro, topology mermaid, § 2.1 skill row (`chaplain-ops` is deleted), § 3 → "The rite as practised" (author.sh → judge.sh → worktree → outsider.sh/review.sh → human merge), § 3.1 comparison in past tense with the measurement sentence verbatim, § 5 bullet, § 6 mermaid + bullets, § 7 row |
| `reference/onepager-development-process.md` | "The Chaplain Pipeline" section → "The Rite" (proposals/ → FR → judge.sh → worktree → outsider.sh/review.sh → human merge); Commandment-1 enforcement cell, `inquisitor-background` gate row, Inquisitor/Chaplain loop in the traceability chain, developer-flow steps 1/6–9 and the sources footer replaced by the operator-driven rite and `docs/archive/chaplain-system.md` |
| `reference/audit-index.md` | the six retired runtime component rows (Chaplain Pipeline, Dispatcher FSM, Pipeline FSM, Inquisitor, Author allowlist, ID registry) deleted; one `Chaplain (archived)` row linking `docs/archive/chaplain.md`; Philosopher row → `graphs/philosopher/graph.yaml` (dormant) |
| `reference/graph-yaml.md` | `# Based on .chaplain/watcher2.sh pattern` comment dropped; the `path:` vs `module:` note names `graphs/fr_triage` instead of "chaplain graphs" |
| `reference/command-book.md` | § Related link text "Sermon of the Chaplain" → "Sermon" |
| `reference/patterns/fsm-as-conductor.md` | Chaplain case kept as an explicitly archived historical instance: Location → `docs/archive/chaplain.md` (retired 2026-09), Context and See-Also → `docs/archive/chaplain-system.md` |
| `examples/README.md` | `philosopher/` stub row and the `.chaplain/demos/` witness line deleted; relocation note → "The philosopher graph lives in `graphs/philosopher/` (FR-196 → FR-1011)" |
| `.github/skills/graph-authoring/{SKILL,doctrine}.md`, `.github/skills/judge-fr/doctrine.md` (+ `cp` to its `ramp/` mirror `ramp/assets/tier2/github/skills/judge-fr/doctrine.md`) | "escalate to Chaplain" → file an FR; runtime origin → archive link |

**Archive preservation** (historical content, kept as is — AC-3): `docs/context/chaplain-system.md` is `git mv`'d byte-identical to `docs/archive/chaplain-system.md`; `docs/archive/chaplain.md` gains one link line to it. Both files keep their `.chaplain/` paths; they are history and are linked from the live set only as history.

**Process artifacts:** `changelog/unreleased/fr1019-doctrine-sweep.md` (`type: removal`, `scope: doctrine`); `docs/diary/diary-2026-09-06-reflection-fr-1019-chaplain-doctrine-sweep.md`; this FR's § Implementation record. No other diary, FR, changelog, memento, ebook, research or archive content is touched.

**Post-merge operator action (not in the PR; AC-7):** after the implementation PR merges, the operator edits FR-1010 only: § Phase 3 heading and the phase-order sentence / AC-04 list name "FR-1019, superseding rejected FR-1013" instead of FR-1013; § Phase 3 records this PR's immutable merge SHA; AC-12 is run on merged `main` and its residual list recorded; AC-12 and AC-13 ticked; `**Status:**` → `Completed`.

**Source of the edits:** closed PR #627 (head `cf9b915e`) is evidence and a hunk source only. Port only the hunks the Change table describes, one file at a time, each reviewed as a patch against current HEAD (`git diff BASE cf9b915e -- <file>` read, then applied by hand or `git apply` of that file's hunks). Never `git cherry-pick` a commit, never `git checkout cf9b915e -- <path>`, and import nothing from its `ARCHITECTURE.md`, `capabilities/`, `docs/census/`, `tests/`, `docs/confessions.md`, diary, FR or post-merge-record changes.

## Acceptance Criteria

No new test file: the permanent witnesses are the existing requirement-owned ones named in AC-5; AC-1..AC-4 and AC-6 are one-time assertions run on the PR branch, their output pasted into § Implementation record.

Every command below is an assertion: the block is run with `set -e` and must exit 0.

```bash
set -e
BASE=36591389e2fdfedf9ba5ae6362effad1c64cd06e
git merge-base --is-ancestor "$BASE" HEAD
S='.github/copilot-instructions.md'
LIVE='.github/copilot-instructions.md docs/development-process.md reference/onepager-development-process.md
reference/audit-index.md reference/graph-yaml.md reference/command-book.md reference/patterns/fsm-as-conductor.md
examples/README.md .github/skills/graph-authoring/SKILL.md .github/skills/graph-authoring/doctrine.md
.github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md'
STEPS='^\*\*(Research|Plan|Judge|Enforce|Purge|Submit|Distill)\.\*\*'
```

- [ ] AC-1: Scripture — heading gone; exactly two lines differ from BASE; Sermon steps and Knowledge Graph block byte-identical:
  ```bash
  test "$(grep -c 'Sermon of the Chaplain' $S)" = 0
  test "$(git diff --numstat $BASE -- $S | cut -f1,2)" = "$(printf '2\t2')"
  diff <(git show $BASE:$S | grep -E "$STEPS") <(grep -E "$STEPS" $S)
  diff <(git show $BASE:$S | sed -n '/^```yaml$/,/^```$/p') <(sed -n '/^```yaml$/,/^```$/p' $S)
  ```
- [ ] AC-2: Live edit set — zero forbidden operational strings; each of the three scripts named; measurement sentence byte-equal to BASE:
  ```bash
  ! grep -n -E '\.chaplain/inbox|\.chaplain/scripts|start-system\.sh|label: chaplain|chaplain-ops|Chaplain/Watcher' $LIVE
  for s in scripts/author.sh scripts/judge.sh scripts/review.sh; do grep -q -F "$s" docs/development-process.md; done
  M='over May–July 2026: \*\*~568 commits on main, of which ~94 (17%) arrived via PR (chaplain path)'
  test "$(git show $BASE:docs/development-process.md | grep -E "$M")" = "$(grep -E "$M" docs/development-process.md)"
  ```
- [ ] AC-3: Residual disposition — the case-insensitive census of the live set is pasted into § Implementation record and every surviving line is dispositioned by a human as (a) explicit history / past tense, (b) an archive link, or (c) one of the two untouched Knowledge Graph entries (`audit # Inquisitor findings → enforcement gates`, `inquisitor_auto_escalation`). No surviving line presents the runtime as an active route:
  ```bash
  grep -n -i -E 'chaplain|inquisitor' $LIVE   # output = the census to disposition
  ```
- [ ] AC-4: Archive — byte-identical move, one link, one audit-index row:
  ```bash
  test ! -e docs/context/chaplain-system.md && test -f docs/archive/chaplain-system.md
  test "$(git diff --name-status -M100% $BASE -- docs/context/chaplain-system.md docs/archive/chaplain-system.md | cut -f1)" = R100
  test "$(grep -c 'chaplain-system.md' docs/archive/chaplain.md)" = 1
  test "$(grep -c 'Chaplain' reference/audit-index.md)" = 1
  grep 'Chaplain' reference/audit-index.md | grep -q -F 'docs/archive/chaplain.md'
  ```
- [ ] AC-5: Mirror and the existing requirement-owned witnesses (`REQ-YG-613` mirror equality; `REQ-YG-192` Knowledge Graph preserved; `REQ-YG-666` runtime absent). No test is added, tagged with a REQ it does not witness, or left unmarked:
  ```bash
  cmp -s .github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md
  git diff --exit-code $BASE -- ramp/manifest.yaml ramp/curation-diffs.md
  pytest tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes \
         tests/unit/test_knowledge_graph_fr193.py tests/unit/test_fr1012_chaplain_removed.py -q --no-cov
  ```
- [ ] AC-6: Process artifacts:
  ```bash
  F=changelog/unreleased/fr1019-doctrine-sweep.md
  grep -q -x 'type: removal' $F && grep -q -x 'scope: doctrine' $F
  grep -q -F '**Seed:**' docs/diary/diary-2026-09-06-reflection-fr-1019-chaplain-doctrine-sweep.md
  pytest tests/unit/ -q --no-cov -m "not slow" -n auto
  ```
- [ ] AC-7 (pre-merge, human): § Implementation record lists every changed path (all within D-1…D-6 of the round-2 judgement), states that no commit or whole file was taken from `cf9b915e`, and records the human read of the Scripture diff and both judge-doctrine copies.
- [ ] AC-8 (post-merge, operator): FR-1010 names FR-1019 as the Phase 3 successor superseding rejected FR-1013 (§ Phase 3, phase-order sentence, AC-04 list), records this PR's immutable merge SHA, records the merged-`main` AC-12 residual, ticks AC-12/AC-13, and moves to `Completed`. Not satisfiable inside the implementation PR.

## Purge list

No census, no inventory file, no baseline, no new test file, no new REQ or CAP, no per-file hash of the repository, no script, hook or CI change, no rewrite of archive or historical content to satisfy a grep.
