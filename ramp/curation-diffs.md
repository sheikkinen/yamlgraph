# Ramp Curation Diffs — FR-865 AC-17

Drift-evidence records for curated assets. Every `curation_diff` entry
in `ramp/manifest.yaml` points at a section here; each names the live
source, the curated asset, the removed/changed material, and why each
removal is domain-specific. `mirror_exact` entries need no record —
byte equality is asserted by test.

## pre-commit-config

- live source: `.pre-commit-config.yaml`
- curated asset: `ramp/assets/tier1/pre-commit-config.yaml`
- removed/changed: all `repo: local` gates except forbidden-phrases —
  authoring proof (FR-767), diary import/reflection, req-coverage,
  capability/ID-registry validation, architecture sync, noqa
  confessions, dependency rationale, direct-import scan, inline-LLM
  check, radon/bandit/file-size/jscpd/import-linter/vulture/hedging
  gates, gitignore boundary, demo proof, changelog cross-checks, FR
  board, prior-art/triage gates, pytest hook, final summary; entries
  hardcode `.venv/bin/python` and this repo's scripts. The forbidden
  phrases hook is rebuilt as a generic pygrep. Standard `repos:` blocks
  (ruff v0.8.6, pre-commit-hooks v5.0.0) are kept at identical revs so
  hook environments stay cache-compatible with this repo's own runs.
- reason: every removed gate depends on this repo's scripts/, registry
  layout, doctrine files or venv path — installing them cold would break
  the target's first commit. A `--no-verify` block is not expressible in
  pre-commit (bypassed hooks never run); that protection ships in the
  curated Copilot guard instead.

## pre-command-guard

- live source: `.github/hooks/scripts/pre-command-guard.sh`
- curated asset: `ramp/assets/tier1/github/hooks/scripts/pre-command-guard.sh`
- removed/changed: lockdown channel and command handler, reasoning
  pattern sentinel (FR-438/439), graph-authoring sole-route guard
  (FR-767), branch-creation block (FR-662), spike-end detector (FR-869),
  doctrine citations in deny messages. Kept byte-similar: JSON
  parse/fail-closed, audit logging, Co-authored-by, --no-verify,
  multiline `-m`, pytest pipe-buffer checks.
- reason: the removed checks enforce this repo's graph-authoring
  doctrine, worktree policy, session tooling and foreign-repo detection
  — all reference paths (`examples/`, `graphs/`, `.chaplain/`) or
  workflows a Tier-1 target does not have.

## judge-sh

- live source: `scripts/judge.sh`
- curated asset: `ramp/assets/tier2/scripts/judge.sh`
- removed/changed: added an explicit adapter-graph existence check with
  a pointer to the skill doctrine; internal incident citations
  (NC-414/NC-415, PR #58) trimmed; `.venv` hint generalized.
- reason: the installer never ships graph artifacts (FR-865 GATE C-4) —
  the adapter graph must be authored in the target per its own doctrine,
  so the wrapper must fail loudly and instructively when it is absent.

## review-sh

- live source: `scripts/review.sh`
- curated asset: `ramp/assets/tier2/scripts/review.sh`
- removed/changed: same as judge-sh — adapter-graph existence check
  added; incident citations trimmed.
- reason: same as judge-sh.

## req-coverage

- live source: `scripts/req_coverage.py`
- curated asset: `ramp/assets/tier3/scripts/req_coverage.py`
- removed/changed: dropped the `coverage_contexts` import and
  `--implementation` mode (FR-850 coverage-DB tooling), the
  framework/hook scope split (FR-436), and the ARCHITECTURE.md coupling;
  requirement-ID prefix is taken from the registry instead of assuming
  this repo's prefix; test scope widened to `tests/`.
- reason: the removed features depend on this repo's coverage database,
  module map and hook-test layout; a target needs only the
  registry-vs-marks gate.
