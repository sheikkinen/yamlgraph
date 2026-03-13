# Feature Request: FSM Pre-commit Quality Gates

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-13

## Summary

Install pre-commit with ruff, file-size-gate, forbid-terms, pytest, and
conventional-commit hooks in the `fsm/` (statemachine-engine) subproject,
adapted from YAMLGraph's `.pre-commit-config.yaml`, and add ruff config plus
`pre-commit` dev dependency to `fsm/pyproject.toml`. Five first-party files
currently exceeding the 450-line threshold are explicitly excluded from the
gate with individual follow-on FRs filed per file.

## Value Statement

FSM contributors get the same quality guardrails as YAMLGraph contributors,
catching lint errors, oversized modules, forbidden terms, and test failures
locally before they reach CI.

## Problem

The `fsm/` subproject is a separate Python package (statemachine-engine
v1.0.75) with 92 source files and a comprehensive test suite, but it has no
pre-commit configuration, no ruff configuration, and no automated quality
gates. Code can be committed with style violations, debug statements, oversized
modules, or failing tests without any local feedback. The root YAMLGraph
project has 14+ custom hooks enforcing quality — the same discipline is absent
from `fsm/`.

Five first-party source files already exceed the 450-line error threshold:

| File | Lines |
|------|-------|
| `database/cli.py` | 1178 |
| `tools/diagrams.py` | 932 |
| `core/engine.py` | 846 |
| `monitoring/websocket_server.py` | 637 |
| `tools/validate.py` | 457 |

Additionally, `src/statemachine_engine/ui/node_modules/` contains vendored
third-party Python files reaching 3978 lines that must be excluded from the
gate.

## Proposed Solution

Create `fsm/.pre-commit-config.yaml` with a focused subset of YAMLGraph's
hooks adapted for `fsm/`'s constraints (Python 3.9+ target, no req-coverage or
capability registry requirements).

**Resolution of Judge Issue 1 — node_modules exclusion:**
The `find` command in the file-size-gate includes `! -path "*/node_modules/*"`
to exclude vendored third-party files from the size check.

**Resolution of Judge Issue 2 — oversized first-party files (Option B):**
The gate is introduced with a temporary `exclude:` pattern for the five known
violators. Each violator is tracked in a dedicated follow-on FR (FR-187 through
FR-191). AC-6 is scoped to pass once ruff violations and the test suite are
clean; the size gate passes for all files *not* in the explicit exclusion list.
This is an intentionally gapped gate — documented here, not hidden — with a
clear follow-on plan. The Scripture's *"detection without enforcement =
advisory"* applies to the gate as a whole; individual file exclusions are
explicit debt, not silent fallback.

```yaml
# fsm/.pre-commit-config.yaml
fail_fast: true

repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-ast
      - id: debug-statements
      - id: detect-private-key

  - repo: local
    hooks:
      - id: file-size-gate
        name: file size gate (>450 error, >400 warn)
        entry: bash -c '
          fail=0; warn=0;
          # Known oversized files deferred to FR-187–FR-191:
          EXCLUDED="database/cli.py|tools/diagrams.py|core/engine.py|monitoring/websocket_server.py|tools/validate.py";
          for f in $(find src/statemachine_engine -type f -name "*.py" \
              ! -path "*/__pycache__/*" \
              ! -path "*/node_modules/*"); do
            base=$(echo "$f" | sed "s|src/statemachine_engine/||");
            echo "$base" | grep -qE "$EXCLUDED" && continue;
            lines=$(wc -l < "$f");
            if [ "$lines" -gt 450 ]; then
              echo "ERROR $f -- $lines lines (max 450)"; fail=1;
            elif [ "$lines" -gt 400 ]; then
              echo "WARN  $f -- $lines lines (target <=400)"; warn=1;
            fi;
          done;
          if [ "$fail" -eq 1 ]; then
            echo "";
            echo "FAIL -- code files exceeding 450 lines detected";
            exit 1;
          fi;
          if [ "$warn" -eq 1 ]; then echo ""; echo "(warnings only -- hook passes)"; fi'
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit]

      - id: forbid-terms
        name: forbid drift terms
        entry: bash -c '! find src/statemachine_engine -type f -name "*.py"
            ! -path "*/__pycache__/*"
            ! -path "*/node_modules/*"
            -print0 | xargs -0 grep -nE "backward.compat|pre.existing.fail"'
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit]

      - id: pytest
        name: pytest (unit tests)
        entry: bash -c 'python -m pytest tests/ -q --no-cov -x'
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit]

  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, chore, docs, refactor, test, ci, perf, style, build, revert]
```

Add ruff configuration and `pre-commit` dev dependency to `fsm/pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "httpx>=0.25.0",
    "ruff>=0.1.0",
    "pre-commit>=3.0.0",
]

[tool.ruff]
line-length = 88
target-version = "py39"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-q"
```

Install hooks by running inside `fsm/`:
```bash
pip install -e ".[dev]"
pre-commit install
pre-commit install --hook-type commit-msg
```

Any ruff violations surfaced in existing `src/statemachine_engine/` files must
be fixed as part of this FR before the hook can pass.

## Acceptance Criteria

- [ ] `fsm/.pre-commit-config.yaml` exists with ruff, standard
      pre-commit-hooks, file-size-gate (`language: system` inline bash),
      forbid-terms, pytest, and conventional-pre-commit hooks
- [ ] file-size-gate `find` command excludes both `*/__pycache__/*` and
      `*/node_modules/*`
- [ ] file-size-gate explicitly excludes the five known oversized files
      (`database/cli.py`, `tools/diagrams.py`, `core/engine.py`,
      `monitoring/websocket_server.py`, `tools/validate.py`) via an inline
      `EXCLUDED` pattern; exclusion is documented in a comment referencing
      FR-187–FR-191
- [ ] `fsm/pyproject.toml` includes `ruff>=0.1.0` and `pre-commit>=3.0.0`
      under `[project.optional-dependencies] dev`
- [ ] `fsm/pyproject.toml` includes `[tool.ruff]` with
      `target-version = "py39"`
- [ ] `fsm/pyproject.toml` includes `[tool.pytest.ini_options]` with
      `testpaths = ["tests"]`
- [ ] Running `pre-commit run --all-files` inside `fsm/` exits 0 (ruff clean,
      tests pass, no drift terms, no new files exceed 450 lines); the five
      excluded oversized files do not cause failure
- [ ] Running `pre-commit run --hook-stage commit-msg
      --commit-msg-filename <(echo "feat: add thing")` validates conventional
      commits
- [ ] forbid-terms hook blocks commits containing `backward compat` or
      `pre-existing fail` in Python source files under
      `src/statemachine_engine/` (excluding `node_modules/`)
- [ ] No ruff violations remain in existing `src/statemachine_engine/` source
      files (violations introduced by enabling ruff are fixed within this FR)
- [ ] Follow-on FRs FR-187 through FR-191 are filed in `feature-requests/`,
      one per oversized file, each with a split plan and acceptance criteria
- [ ] `fsm/README.md` updated with a "Development Setup" section documenting
      hook installation (`pre-commit install &&
      pre-commit install --hook-type commit-msg`)

## Alternatives Considered

**Extend root `.pre-commit-config.yaml` to cover `fsm/`:** Rejected — `fsm/`
is an independent package with its own git context and Python 3.9 target.
Coupling it to the root config would make `fsm/` un-publishable as a
standalone project.

**GitHub Actions only (no local hooks):** Rejected — CI-only gates give no
local feedback. The Knowledge Graph explicitly states: *"detection without
enforcement = advisory → add CI block or remove claim."* Local hooks are the
enforcement layer.

**Minimal config (ruff only):** Rejected — single-hook configs invite gradual
erosion. A coherent gate set (lint + size + tests + commit message) is harder
to selectively disable.

**`language: script` with external shell file for file-size-gate:** Rejected —
`scripts/file_size_gate.sh` does not exist in the root project; the root uses
an inline `language: system` bash command. The `fsm/` version follows the same
pattern to stay consistent and avoid creating a phantom script dependency.

**Raise threshold (Judge Option C):** Rejected — a threshold that passes all
existing files is not a gate; it is advisory. The Scripture is unambiguous:
*"detection without enforcement = advisory."* Option B (explicit exclusions
with follow-on FRs) enforces discipline on all new code immediately while
creating a concrete, tracked path to full compliance.

**Split five oversized files within this FR (Judge Option A):** Rejected —
splitting five modules with full test coverage is a 3–5 day effort and would
obscure the gate installation in a large structural refactor. Each file split
deserves its own FR, design discussion, and commit trail.

## Related

- Root `.pre-commit-config.yaml` — source of hook patterns adapted here
- `FR-038` — conventional-commit enforcement pattern
- `FR-047` — custom pygrep hook pattern (inline-llm-check)
- `FR-073` — fast unit tests in pre-commit
- `FR-077` — commit-msg stage enforcement
- `FR-187` — split `database/cli.py` (1178 lines) *(to be filed)*
- `FR-188` — split `tools/diagrams.py` (932 lines) *(to be filed)*
- `FR-189` — split `core/engine.py` (846 lines) *(to be filed)*
- `FR-190` — split `monitoring/websocket_server.py` (637 lines) *(to be filed)*
- `FR-191` — split `tools/validate.py` (457 lines) *(to be filed)*
- `fsm/pyproject.toml` — target file for ruff and pytest config additions
- Scripture: *"automation_inherits_doctrine: Scripts follow same rules as
  humans"*
- Scripture: *"infrastructure_self_exempt: Meta-tooling exempted from gates it
  enforces → apply same rules to the guardrail as to what it guards"*
- Scripture: *"detection_without_enforcement: Lint without gate = advisory →
  add CI block or remove claim"*
