# YAMLGraph Development Process — One-Pager

---

## The Scripture

Ten commandments that govern every agent and every human working on this codebase. Not guidelines — executable constraints enforced by tooling.

| # | Law | Enforcement |
|---|-----|-------------|
| 1 | Research before coding — cheapest code is unwritten code | FR `**Research:**` field; judge research gate |
| 2 | Demonstrate with working examples, never abstract prose | `demo-gate` CI check |
| 3 | Config is truth; code is logic — all prompts in YAML | `inline-llm-check` hook |
| 4 | Conform before extending — read existing patterns first | Code review |
| 5 | All LLM outputs through Pydantic | `ruff` + type checks |
| 6 | Expose faults; no silent fallbacks — raise, never substitute | `hedging-check` hook |
| 7 | TDD — Red → Green → Refactor; no fix without a failing test first | `pytest` hook + CI |
| 8 | Kill entropy: no dead code, no duplication, no bloat | `vulture`, `jscpd`, `radon` |
| 9 | Instrument execution; treat perf/failure drift as defects | LangSmith tracing |
| 10 | Every failure refines the law — update tests, update doctrine | `diary-gate` CI check |

**Source:** `.github/copilot-instructions.md` — never alter by preference, haste, or hallucination.

---

## The Rite

Operator-driven loop that turns a spark into a judged plan, an enforced change, and a diary entry.

```
proposals/<topic>.md              (untracked spark)
         │
         ▼
  feature-requests/FR-XXX.md      ── scripts/judge.sh ──► FR-XXX.judgement.md
         │
         ▼  worktree: RED, then GREEN
  PR ── scripts/outsider.sh ── scripts/review.sh ──► human merge
         │
         ▼
  docs/diary/YYYY-MM-DD-reflection-fr-XXX-*.md
```

**To submit a proposal:** write a markdown spark into `proposals/` (`mkdir -p proposals && cat > proposals/<topic>.md`). The rite runs Research → Plan → Judge → Enforce → Distill; each word is defined in `command-book.md`.

---

## Pre-commit Gates

`fail_fast: true` — first failure stops the commit. Two hooks must also be installed:

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

### Pre-commit stage (runs on `git commit`)

| Gate | What it catches |
|------|-----------------|
| `ruff` + `ruff-format` | Lint and style |
| `check-yaml`, `check-toml`, `check-ast` | Syntax errors |
| `detect-private-key` | Accidental secrets |
| `check-merge-conflict` | Unresolved conflict markers |
| `inline-llm-check` | LLM calls bypassing graph execution |
| `hedging-check` | Silent fallbacks (Commandment 6) |
| `forbid-terms` | `TODO`, `FIXME`, `backward compatibility` |
| `radon-complexity` | Cyclomatic complexity ≥ 21 (grade D) |
| `file-size-gate` | Files > 450 lines (error), > 400 (warn) |
| `jscpd-dup` | Code duplication > 10% threshold |
| `vulture-dead-code` | Unused code (≥ 80% confidence) |
| `req-coverage-strict` | Every requirement has tagged tests |
| `noqa-confession` | Every `# noqa` has a `docs/confessions.md` entry |
| `pytest` | Full unit test suite |
| `diary-rotate` | Rotates `docs/diary.md` on day change |

### Commit-msg stage

| Gate | What it catches |
|------|-----------------|
| `conventional-pre-commit` | Commit message must follow Conventional Commits |
| `feat-requires-fr` | `feat:` commits must reference `FR-XXX` |
| `changelog-required` | `feat:`/`fix:` commits must include a changelog fragment |

### Post-commit stage (async, non-blocking)

| Gate | What it does |
|------|--------------|

---

## CI Gates (GitHub Actions — blocks PR merge)

Branch protection on `main` enforces squash-merge-only. All checks must pass before merge.

| Check | Workflow | Blocks |
|-------|----------|--------|
| `commitlint` | `commitlint.yml` | PR title not in Conventional Commits format; `feat` without `FR-XXX` |
| `test` | `workflow.yml` | `pytest` below 80% coverage; `ruff` violations |
| `conflict-check` | `commitlint.yml` | Unresolved merge conflict markers in any tracked file |
| `changelog-gate` | `commitlint.yml` | `feat`/`fix` PR with no fragment in `changelog/unreleased/` |
| `changelog-req-gate` | `commitlint.yml` | Fragment `req:` field references invalid REQ-YG-XXX |
| `diary-gate` | `commitlint.yml` | `feat`/`fix` + `FR-XXX` PR with no diary entry in diff |
| `demo-gate` | `commitlint.yml` | Changes to `examples/demos/<name>/` without `demo-output.log` proving demo ran |
| `security` | `security.yml` | Known CVEs in installed dependencies (`pip-audit`) |

---

## Requirement Traceability Loop

```
Scripture (.github/copilot-instructions.md)
    │  defines doctrine
    ▼
ARCHITECTURE.md  (CAP-XX → REQ-YG-XXX)
    │  translates doctrine → numbered requirements
    ▼
Test files  (@pytest.mark.req("REQ-YG-XXX"))
    │  prove requirements are met
    ▼
Pre-commit: req_coverage.py --strict  +  CI: req_coverage.py
    │  enforce: every REQ has ≥ 1 test; every test has a REQ tag
    ▼
Diary → Philosopher
    │  recurring heuristics graduate to doctrine
    └──────────────────────────────► back to Scripture
```

Every link is mechanically enforced. You cannot commit a test without `@pytest.mark.req`. You cannot commit code when a requirement has zero tests. You cannot merge a `feat:` PR without a diary entry.

---

## The Developer Flow

```
1. Write spark → proposals/                (then draft the FR)
2. Review FR in feature-requests/FR-XXX.md
3. Write failing test (RED) — commit with SKIP=pytest
4. Implement fix (GREEN) — pre-commit gates run
5. Commit: feat(scope): FR-XXX description
   └─ conventional-pre-commit, feat-requires-fr, changelog-required all check
6. Push PR → CI gates run (commitlint, test, changelog-gate, diary-gate …)
7. Squash merge → PR title becomes the commit on main
8. scripts/outsider.sh + scripts/review.sh on the PR (advisory)
9. Add diary entry to docs/diary/ (diary-gate blocks merge if missing)
```

**Emergency bypass:** admin override only — every bypass must be documented in `reference/break-glass.md`.

---

*Sources: `CLAUDE.md`, `.pre-commit-config.yaml`, `docs/ebook/v3/`, `docs/archive/chaplain-system.md`*
