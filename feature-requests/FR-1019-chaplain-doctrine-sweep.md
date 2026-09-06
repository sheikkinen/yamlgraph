# Feature Request: Doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)

**Priority:** LOW
**Type:** Enhancement (docs only; two-line Scripture edit — human read before merge)
**Status:** Judged — REJECTED round 1 (2026-09-06, [judgement](FR-1019-chaplain-doctrine-sweep.judgement.md)); R-1..R-5 folded below; awaiting round 2.
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
| `reference/onepager-development-process.md`, `reference/audit-index.md` (one archived Chaplain row), `reference/graph-yaml.md`, `reference/command-book.md`, `reference/patterns/fsm-as-conductor.md`, `examples/README.md` | pointer fixes to `proposals/`, `graphs/`, `docs/archive/` |
| `.github/skills/graph-authoring/{SKILL,doctrine}.md`, `.github/skills/judge-fr/doctrine.md` (+ `cp` to its `ramp/` mirror `ramp/assets/tier2/github/skills/judge-fr/doctrine.md`) | "escalate to Chaplain" → file an FR; runtime origin → archive link |

**Archive preservation** (historical content, kept as is — AC-3): `docs/context/chaplain-system.md` is `git mv`'d byte-identical to `docs/archive/chaplain-system.md`; `docs/archive/chaplain.md` gains one link line to it. Both files keep their `.chaplain/` paths; they are history and are linked from the live set only as history.

**Process artifacts:** `changelog/unreleased/fr1019-doctrine-sweep.md` (`type: removal`, `scope: doctrine`); `docs/diary/diary-2026-09-06-reflection-fr-1019-chaplain-doctrine-sweep.md`; this FR's § Implementation record. No other diary, FR, changelog, memento, ebook, research or archive content is touched.

**Post-merge operator action (not in the PR):** after the implementation PR merges, the operator records its merge SHA under FR-1010 § Phase 3, ticks FR-1010 AC-12 (the residual grep, run on merged `main`) and AC-13, and sets FR-1010 `**Status:**` to `Completed`.

The document edits exist on PR #627 (closed, head `cf9b915e`); cherry-pick them file by file, not the census, the baseline, the REQ, or the 421-line test.

## Acceptance Criteria

`BASE=36591389e2fdfedf9ba5ae6362effad1c64cd06e` throughout. No new test file: the permanent witnesses are the existing requirement-owned ones named in AC-4; AC-1..AC-3 and AC-5 are one-time commands run on the PR branch and recorded in § Implementation record.

- [ ] AC-1: Scripture — `grep -c 'Sermon of the Chaplain' .github/copilot-instructions.md` → 0, and the diff against BASE is exactly the two authorized lines:
  ```bash
  git diff --numstat $BASE -- .github/copilot-instructions.md            # → 2 2
  diff <(git show $BASE:.github/copilot-instructions.md | grep -E '^\*\*(Research|Plan|Judge|Enforce|Purge|Submit|Distill)\.\*\*') \
       <(grep -E '^\*\*(Research|Plan|Judge|Enforce|Purge|Submit|Distill)\.\*\*' .github/copilot-instructions.md)   # empty
  diff <(git show $BASE:.github/copilot-instructions.md | sed -n '/^```yaml$/,/^```$/p') \
       <(sed -n '/^```yaml$/,/^```$/p' .github/copilot-instructions.md)   # empty (Knowledge Graph block)
  ```
- [ ] AC-2: Live edit set — zero matches, no exceptions:
  ```bash
  grep -n -E '\.chaplain/inbox|\.chaplain/scripts|start-system\.sh|label: chaplain|chaplain-ops|Chaplain/Watcher' \
    .github/copilot-instructions.md docs/development-process.md reference/onepager-development-process.md \
    reference/audit-index.md reference/graph-yaml.md reference/command-book.md reference/patterns/fsm-as-conductor.md \
    examples/README.md .github/skills/graph-authoring/SKILL.md .github/skills/graph-authoring/doctrine.md \
    .github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md   # exit 1
  grep -c -E 'scripts/author\.sh|scripts/judge\.sh|scripts/review\.sh' docs/development-process.md   # ≥ 3
  git show $BASE:docs/development-process.md | grep -F 'over May–July 2026: **~568 commits on main' && \
    grep -F 'over May–July 2026: **~568 commits on main' docs/development-process.md   # both print the measurement sentence
  ```
- [ ] AC-3: Archive — `docs/context/chaplain-system.md` gone; move detected byte-identical; linked; one `Chaplain` row in the audit index:
  ```bash
  test ! -e docs/context/chaplain-system.md && test -f docs/archive/chaplain-system.md
  git diff --name-status -M100% $BASE -- docs/context/chaplain-system.md docs/archive/chaplain-system.md   # R100
  grep -c 'chaplain-system.md' docs/archive/chaplain.md          # 1
  grep -c 'Chaplain' reference/audit-index.md                     # 1
  grep 'Chaplain' reference/audit-index.md | grep -c 'docs/archive/chaplain.md'   # 1
  ```
- [ ] AC-4: Mirror and existing witnesses (permanent, requirement-owned):
  ```bash
  cmp -s .github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md
  git diff --exit-code $BASE -- ramp/manifest.yaml ramp/curation-diffs.md
  pytest tests/unit/test_ramp_installer.py::test_mirror_exact_entries_match_live_bytes \
         tests/unit/test_knowledge_graph_fr193.py tests/unit/test_fr1012_chaplain_removed.py -q --no-cov
  ```
  (`REQ-YG-613` mirror equality; `REQ-YG-192` Knowledge Graph preserved; `REQ-YG-666` runtime absent. No test is added, tagged with a REQ it does not witness, or left unmarked.)
- [ ] AC-5: Process artifacts — the changelog fragment exists with `type: removal` and `scope: doctrine`; the diary file at the exact path above exists and contains `**Seed:**`; `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` green.
- [ ] AC-6: Human read of the Scripture and judge-doctrine diffs recorded in § Implementation record before merge.
- [ ] AC-7 (post-merge, operator): FR-1010 § Phase 3 records this PR's merge SHA; FR-1010 AC-12 and AC-13 ticked on merged `main`; FR-1010 `**Status:**` → `Completed`. Not satisfiable inside the implementation PR.

## Purge list

No census, no inventory file, no baseline, no new test file, no new REQ or CAP, no per-file hash of the repository, no script, hook or CI change, no rewrite of archive or historical content to satisfy a grep.
