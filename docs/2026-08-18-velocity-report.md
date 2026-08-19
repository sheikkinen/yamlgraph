# Velocity Report — 2026-08-18

Commit velocity and topic distribution for the trailing six months
(2026-02-18 → 2026-08-18). Source: `git log --since="2026-02-18" --no-merges`
on `main`. 1,791 non-merge commits total.

## Velocity (commits/month)

| Month | Commits | Note |
|-------|---------|------|
| 2026-02 (partial) | 234 | |
| 2026-03 | 267 | |
| 2026-04 | 209 | trough |
| 2026-05 | 247 | |
| 2026-06 | 245 | |
| 2026-07 | 428 | spike — 1.7× baseline |
| 2026-08 (18 days) | 161 | ~268/mo pace — normal |

Steady ~240/month baseline (~8/day). The July outlier is docs-driven
(193 docs commits that month — the introspection/doctrine arc).

## Type distribution

| Type | Count | Share |
|------|-------|-------|
| docs | 690 | 39% |
| feat | 439 | 25% |
| chore | 248 | 14% |
| fix | 214 | 12% |
| test | 145 | 8% |
| refactor | 46 | 3% |
| ci / style / perf / other | 9 | <1% |

## Type mix by month

| Month | feat | docs | fix | chore | test | refactor |
|-------|------|------|-----|-------|------|----------|
| 2026-02 | 43 | 79 | 39 | 38 | 17 | 14 |
| 2026-03 | 77 | 116 | 20 | 48 | 1 | 3 |
| 2026-04 | 78 | 59 | 34 | 33 | 5 | 0 |
| 2026-05 | 79 | 70 | 45 | 50 | 0 | 3 |
| 2026-06 | 48 | 91 | 22 | 22 | 42 | 20 |
| 2026-07 | 81 | 193 | 42 | 49 | 54 | 6 |
| 2026-08 | 33 | 82 | 12 | 8 | 26 | 0 |

## Scope clusters (aliases merged)

| Cluster | Scopes | Commits |
|---------|--------|---------|
| Governance/reflection | fr, FR, feature-requests, diary, docs | ~454 |
| Examples/demos | examples, demos, demo | 230 |
| Dungeon master arc | dm, dungeon_master, dungeon-master | 110 |
| Enforcement infra | hooks, scripts, linter, ci | 99 |
| Automation | watcher, chaplain, enforce | 96 |
| Core framework | graph, fsm, llm, race, a2a, tools | ~85 |
| Release | release | 37 |

## Observations

1. **docs is the plurality type at 39%** — before counting FR/diary scopes
   hiding under other types. The doctrine writes more than the framework
   builds. Write-side gates (diary-gate, changelog-gate) mechanically
   generate this share.
2. **Core framework work is a small minority** (~5% by scope). The repo's
   center of gravity has moved from building YAMLGraph to operating its
   governance system — supporting the "doctrine is the product" read
   (see `docs/diary/diary-2026-08-18-unaddressed-opportunities.md`).
3. **fix:feat ratio is healthy** (~1:2) and stable across months — no
   quality-debt drift.
4. **test commits are bursty**: 0–17/month through spring, then 42/54/26 in
   Jun–Aug. Tests arrive in enforcement waves (e.g. the FR-714 coverage-gate
   push), not continuously with features — notable given the TDD commandment
   implies RED commits should track feat commits month by month.
5. **refactor at 3%, zero in two of seven months** — either entropy-kill
   (Commandment 8) happens inside feat commits, or pruning is
   under-practiced relative to doctrine.

## Reproduction

```bash
# Velocity per month
git log --since="2026-02-18" --no-merges --date=format:'%Y-%m' \
  --pretty='%ad' | sort | uniq -c

# Type distribution
git log --since="2026-02-18" --no-merges --pretty='%s' \
  | sed -E 's/^([a-z]+)(\([^)]*\))?!?:.*/\1/' | sort | uniq -c | sort -rn

# Scope distribution
git log --since="2026-02-18" --no-merges --pretty='%s' \
  | grep -oE '^[a-z]+\(([^)]*)\)' | sed -E 's/^[a-z]+\(([^)]*)\)/\1/' \
  | sort | uniq -c | sort -rn
```
