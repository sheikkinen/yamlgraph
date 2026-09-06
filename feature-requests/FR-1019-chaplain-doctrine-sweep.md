# Feature Request: Doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)

**Priority:** LOW
**Type:** Enhancement (docs only; two-line Scripture edit — human read before merge)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-06
**Plan:** [FR-1010](FR-1010-chaplain-archival-plan.md) Phase 3. Prerequisite FR-1012 merged (`36591389`). Supersedes [FR-1013](FR-1013-chaplain-doctrine-sweep.md) (REJECTED — process outgrew the change; the edits below are the same).
**First consumer / first event:** a new agent session reads `## Sermon of the Chaplain` → `docs/development-process.md` § 3 → `.chaplain/scripts/start-system.sh` (ENOENT).
**Prior art:** FR-1011 (moved the one Scripture *path*), FR-1012 (wrote `docs/archive/chaplain.md`, the single archive pointer), FR-1013 (rejected; see its § Judgement for what not to repeat).

## Problem

The Chaplain runtime is gone (FR-1012); the doctrine and reference documents still describe it as the way work gets done.

## Ideal Result

No live doctrine or reference document presents the Chaplain, its inbox, or the Inquisitor as a running part of the process; every remaining mention is past tense or a link to `docs/archive/`. Scripture changes by two lines. Nothing historical (FRs, diary, changelog, memento, ebook) is touched.

## Change

| File | Edit |
|---|---|
| `.github/copilot-instructions.md` | `## Sermon of the Chaplain` → `## Sermon`; drop "chaplain pipeline, " from the canonical-sources clause. Nothing else. |
| `docs/development-process.md` | intro, topology mermaid, § 2.1 skill row (`chaplain-ops` is deleted), § 3 → "The rite as practised" (author.sh → judge.sh → worktree → outsider.sh/review.sh → human merge), § 3.1 comparison in past tense with the measurement sentence verbatim, § 5 bullet, § 6 mermaid + bullets, § 7 row |
| `reference/onepager-development-process.md`, `reference/audit-index.md` (one archived Chaplain row), `reference/graph-yaml.md`, `reference/command-book.md`, `reference/patterns/fsm-as-conductor.md`, `examples/README.md` | pointer fixes to `proposals/`, `graphs/`, `docs/archive/` |
| `.github/skills/graph-authoring/{SKILL,doctrine}.md`, `.github/skills/judge-fr/doctrine.md` (+ `cp` to its `ramp/` mirror) | "escalate to Chaplain" → file an FR; runtime origin → archive link |
| `docs/context/chaplain-system.md` | `git mv` → `docs/archive/chaplain-system.md`; one link line in `docs/archive/chaplain.md` |

The implementation exists on branch `feat/fr1013-doctrine-sweep` (PR #627, closed); cherry-pick the document edits, not the census, the baseline, the REQ, or the 421-line test.

## Acceptance Criteria

- [ ] AC-1: `grep -c 'Sermon of the Chaplain' .github/copilot-instructions.md` → 0; the seven bold Sermon step names and the Knowledge Graph block are byte-identical to `36591389`.
- [ ] AC-2: None of the edited files contains `.chaplain/`, `start-system.sh`, `label: chaplain`, `chaplain-ops`, or "Chaplain/Watcher"; `docs/development-process.md` names `scripts/author.sh`, `scripts/judge.sh`, `scripts/review.sh`; § 3.1's measurement sentence is byte-identical to BASE.
- [ ] AC-3: `reference/audit-index.md` has exactly one `Chaplain` row and it links `docs/archive/chaplain.md`; `docs/context/chaplain-system.md` is gone, `docs/archive/chaplain-system.md` exists and is linked from `docs/archive/chaplain.md`.
- [ ] AC-4: `cmp -s .github/skills/judge-fr/doctrine.md ramp/assets/tier2/github/skills/judge-fr/doctrine.md`; `ramp/manifest.yaml` and `ramp/curation-diffs.md` unchanged.
- [ ] AC-5: One witness `tests/unit/test_fr1019_doctrine_sweep.py` (≤ 80 lines) asserts AC-1…AC-4 and that no tracked `.md/.py/.sh/.yaml/.yml` file **outside** `feature-requests/ changelog/ docs/diary/ docs/memento/ docs/ebook/ docs/archive/ docs/research-* docs/context/fr-698.md ramp/curation-diffs.md` contains `.chaplain/inbox`, `.chaplain/scripts`, or `start-system.sh`; tagged with an existing REQ the judge names (REQ-YG-666 documents the removal; if the judge holds it does not cover docs consistency, tag REQ-YG-192 for the Scripture assertions only and leave the rest untagged-by-design with a `# noqa`-style confession — do **not** add a requirement).
- [ ] AC-6: changelog fragment `type: removal`, `scope: doctrine`; diary entry; `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` green.
- [ ] AC-7: Human read of the Scripture diff before merge. After merge the operator records the SHA in FR-1010 and closes it.

## Purge list

No census, no inventory file, no baseline, no new REQ or CAP, no per-file hash of the repository, no script, hook or CI change. One judgement round; findings that would add structure to this FR are answered by a sentence, not a table.
