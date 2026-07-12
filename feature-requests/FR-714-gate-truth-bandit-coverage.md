# Feature Request: FR-714 Gate-Truth Alignment — Bandit Gate + Coverage Claim

**Priority:** HIGH (cheapest, and every day ungated is a day the claim lies)
**Type:** Enhancement (enforcement infrastructure)
**Status:** COMPLETED (2026-07-12) — bandit gated in pre-commit, 6 nosec confessions, coverage gate 70→85 (measured 90.36%)
**Effort:** 0.5 day
**Requested:** 2026-07-12
**Spawned by:** docs/2026-07-12-review-refactoring.md P2.5 (second-pass addendum)
**Related:** run-code-analysis skill (claims "0 medium+ bandit"), `.pre-commit-config.yaml`, `.github/workflows/security.yml` (pip-audit only), Scripture `detection_without_enforcement`

## Summary

Two documented quality claims have no gate behind them. Make each claim
true or delete it — a claim with no gate decays into a lie.

## Problem

1. **Bandit is gated nowhere.** The code-analysis skill targets
   "0 medium+ (bandit)"; actual standing findings: 1 HIGH (B701 jinja2
   `autoescape=False`, `utils/template.py:47`) + 3 MEDIUM (2× B104
   `0.0.0.0` a2a CLI defaults, B108 `/tmp` FSM socket). All four are
   ruff-confessed (S701/S104/CONF-302) and contextually sound — prompt
   templates are not HTML; the socket prefix is deliberate — but bandit
   does not honor ruff `noqa`, and neither pre-commit nor CI runs it
   (CI `security` = pip-audit, dependencies only).
2. **Coverage gate drift.** CLAUDE.md documents "80% coverage threshold"
   for the CI `test` job; `pyproject.toml` enforces `--cov-fail-under=70`.
   One of them lies.

## Proposed Solution

- Add bandit to pre-commit (`-ll -q`, config in `pyproject.toml`), with
  `# nosec BXXX` markers mirroring the four existing ruff confessions —
  each nosec gets a confession entry (noqa-confession discipline applies
  to nosec identically).
- Extend `scripts/noqa_coverage.py` (or its config) to count `# nosec`
  markers so the confession gate covers both suppression dialects.
- Coverage: decide ONE number. Default proposal: raise
  `--cov-fail-under` to the current actual coverage floor rounded down
  (measure first — read the number before choosing it), update CLAUDE.md
  to match. If actual < 80, the doc drops to truth; the gate never drops.

## Acceptance Criteria

- [x] AC-01 `bandit -r yamlgraph/ -ll` exits 0 in pre-commit; findings
      carry `# nosec` + confessions CONF-377..381 (+ CONF-380 for the F1
      pre-existing shell.py B602). Note: bandit parses trailing words on
      nosec as test IDs — markers are bare `# nosec BXXX`, prose lives
      in the confession
- [x] AC-02 Deliberate B602 in a scratch file fails the scan — witnessed
      2026-07-12: `bandit /tmp/fr714_scratch.py -ll -q` exit 1
      (High severity B602 reported); gate bites (F2 recorded run)
- [x] AC-03 nosec markers (specific + blanket) counted by
      `scripts/noqa_coverage.py`; unconfessed nosec fails --strict —
      witnessed by the scanner itself flagging its own example comment
      during development (self-test by accident, fixed by rewording)
- [x] AC-04 Coverage measured **90.36%** (fast unit suite, 2026-07-12);
      gate raised 70 → 85 (margin for suite variance, never
      aspiration); CLAUDE.md updated to the enforced value
- [x] Changelog fragment; CAP-199 / REQ-YG-542; witness tests in
      `tests/unit/test_fr714_bandit_gate.py`

## Judgement (2026-07-12)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | The FR counted 4 suppression sites; source shows a FIFTH pre-existing `# nosec B602` (`tools/shell.py:131`) with NO confession — AC-03's gate would flag it on day one | In scope: shell.py's nosec gets its confession too; total = 5 confessed nosec sites. The gate must be born green |
| F2 | AC-02's scratch-file witness cannot live in CI (a deliberately bad file cannot be committed) | Acceptable as recorded manual verification: command + output pasted into this FR at enforce time |

## Alternatives Considered

- Delete the bandit claim from the skill — honest but wasteful: the scan
  is cheap and the four confessions already exist; gating costs ~30 min
  more than deleting.
- Ratchet coverage to 80 immediately — only if measurement shows we are
  already there; the gate must never encode aspiration
  (`gate_checks_shape_not_substance`).
