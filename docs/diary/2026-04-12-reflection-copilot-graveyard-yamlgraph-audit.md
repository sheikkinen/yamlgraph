# Reflection: Copilot Graveyard → YAMLGraph Self-Audit

**Date:** 2026-04-12
**Trigger:** After discovering Copilot's 1,490-session graveyard with near-zero knowledge retention, asked: does YAMLGraph exhibit the same patterns?

## The Audit

Applied the five failure patterns from the Copilot infrastructure analysis to YAMLGraph itself.

### Pattern 1: Accumulation Without Cleanup

**Found.** Three hotspots:

| Accumulator | Size | Problem |
|---|---|---|
| `.mypy_cache/` | **156 MB** | Grows with every type-check run, never cleaned |
| `tmp/` | **28 MB** | 47 enforcement logs, stale LangSmith JSONs, philosopher logs — never rotated |
| `__pycache__` | **1,272 dirs, 8,820 .pyc files** | Gitignored but locally heavy |

The `.mypy_cache` is the YAMLGraph analog of Copilot's 1,490 dead sessions: a cache that only grows, never shrinks, invisible because gitignored.

The `tmp/` enforcement logs are the analog of the 101 orphaned plan.md files: artifacts from completed workflows that persist after their purpose expires.

### Pattern 2: Structural Ghosts

**Found, but minor.** 333 zero-byte files — mostly intentional `__init__.py` markers. The `build/bdist.macosx-*/` empty directory mirrors Copilot's 1,328 empty `research/` dirs — created by tooling, never used.

### Pattern 3: Dual Registries

**Found, but managed.** Requirements live in 5 places:
1. `capabilities/*.yaml` (primary, FR-178)
2. `ARCHITECTURE.md` (prose summary)
3. `scripts/req_coverage.py` (loader)
4. `@pytest.mark.req()` markers (test-level)
5. Feature request files (origin)

Unlike Copilot's mismatched 734-vs-1,490 session registries, YAMLGraph has CI gates: FR-154 catches ARCHITECTURE.md drift, FR-145 detects phantom req references, FR-178 settled on YAML as the canonical source. The dual-registry problem exists but is *enforced*, not ignored.

### Pattern 4: Knowledge Retention

**Strong.** 359 diary entries, 215 feature requests, append-only changelog — the direct opposite of Copilot's 2-fact memory from 1,490 sessions. The diary system works because it's git-tracked and reflective, not because it's automated. The Copilot memory system failed because it's automated and unreflective.

### Pattern 5: Stale Indexes

**Found.** LangSmith session JSONs in `tmp/` (2.4 MB, dates unknown). Small, but the pattern is identical to Copilot's 52-day-stale workspace-chunks.db.

## The Takeaway

YAMLGraph has the same accumulation pattern as Copilot but at smaller scale and with better enforcement. The difference:

| Aspect | Copilot | YAMLGraph |
|---|---|---|
| Accumulation | Grows forever, no cleanup | Grows in `.mypy_cache` and `tmp/`, no cleanup |
| Knowledge | 2 facts from 1,490 sessions | 359 diary entries, well-retained |
| Dual registries | Mismatched, no enforcement | Multiple but CI-gated |
| Structural ghosts | 1,328 empty dirs | ~30 empty dirs (minor) |

The scale is different but the failure mode is the same: **things that grow without bounds eventually become invisible debt.**

## Actions

1. **Clean `.mypy_cache/`** — add to `make clean` or equivalent cleanup target
2. **Rotate `tmp/` logs** — enforcement logs older than 30 days should be pruned; LangSmith JSONs deleted
3. **No new actions needed** for registries (FR-154, FR-145, FR-178 already guard)
4. **No action needed** for knowledge retention (diary system works)

## Trap: `infrastructure_self_exempt`

This is the second instance today. Copilot's infrastructure exempts itself from cleanup rules. YAMLGraph's `.mypy_cache` is exempted from entropy monitoring because it's "just a cache." But 156 MB of unchecked growth is entropy by definition — the same entropy that Commandment 8 says to kill. The `.gitignore` file doesn't make something clean; it makes it invisible.

**Heuristic:** Gitignored ≠ managed. If a gitignored artifact grows without bounds, it needs a cleanup policy just like tracked code needs a test.

## Seed

The `tmp/` enforcement logs are actually a trace record — they prove that the enforcement pipeline ran and what it found. Deleting them loses auditability. But keeping them forever loses disk. Is there a pattern for "compressed audit trail"? The changelog system solves this for features (fragments → aggregated CHANGELOG.md). Could enforcement logs follow the same pattern: individual logs → aggregated enforcement report on release, then prune the individuals?
