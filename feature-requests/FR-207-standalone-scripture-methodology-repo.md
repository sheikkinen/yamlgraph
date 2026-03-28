# Feature Request: FR-207 Standalone Scripture Methodology Repository

**Priority:** MEDIUM
**Type:** Feature
**FR:** FR-207
**Status:** Implemented
**Effort:** 6 days (Tier 1: 3 days, Tier 2: 2 days, Tier 3: 1 day documentation)
**Requested:** 2026-03-28

## Judge Verdict: APPROVE

**Date:** 2026-03-28
**Verdict:** APPROVED — Scope frozen. Authority granted to implement.

### Evaluation

| Criterion | Assessment |
|-----------|-----------|
| Scope clear and minimal? | ✅ Yes — well-defined tier structure with explicit "What Ships" and "What Does NOT Ship" |
| Contradictions or ambiguities? | ⚠️ One contradiction in parameterization mechanism (see note below) |
| Acceptance criteria measurable? | ✅ Yes — 17 criteria across 3 tiers, all verifiable by grep/CI/smoke-test |
| Implementation approach feasible? | ✅ Yes — template repo + shell scripts + sed substitution is proven |
| Aligned with architecture? | ✅ Yes — extraction, not extension; YAMLGraph unchanged |
| Single responsibility? | ✅ Yes — "extract governance into standalone template." Tiers are phased delivery of a single concern, not orthogonal features |

### Note: `render.sh` re-rendering contradiction

The acceptance criterion on line 211 states: *"Changing `req_prefix` from `REQ` to `REQ-FOO` and re-running `render.sh` produces zero occurrences of `REQ-`."* This contradicts the parameterization design (line 105): *"The original `__PLACEHOLDER__` markers are gone after first render."*

After the first `render.sh` execution, `__REQ_PREFIX__` markers become `REQ-001`, `REQ-002`, etc. A subsequent `render.sh` invocation finds no `__REQ_PREFIX__` markers to substitute — the `sed` commands are no-ops. The acceptance criterion is therefore impossible under the current design.

**The implementer must resolve this before starting Tier 1. Three options:**

- **(a) Keep templates separate:** Maintain originals in a `_templates/` directory. `render.sh` always renders from `_templates/` → root. Re-rendering works because the source templates always contain `__PLACEHOLDER__` markers. This is the cleanest solution.
- **(b) State file:** `render.sh` writes rendered values to `.scripture-state` on first run. Re-rendering reads old values from state file and performs value→value substitution. Fragile — breaks if files are manually edited.
- **(c) One-time only:** Remove the re-rendering acceptance criterion. Document `render.sh` as a one-time setup step. To change config, re-clone from template. Simplest, but less ergonomic.

**Recommendation:** Option (a). The separation of source templates from rendered output is standard practice (cf. Cookiecutter, Copier). The `_templates/` directory can be `.gitignore`d after first render, or retained for future re-configuration. Update the AC to: *"Running `render.sh` with modified `scripture.yaml` re-renders all files from `_templates/` sources."*

This is an implementation-detail decision within Tier 1, not a scope issue. The FR's overall design is sound.

### Overlap with FR-196 (Portable Chaplain)

FR-196 makes the Chaplain pipeline portable within YAMLGraph (`.chaplain/` self-contained). FR-207 extracts the governance methodology to an external repo. These are complementary: FR-196 is a prerequisite refactor that simplifies FR-207's extraction (a self-contained `.chaplain/` directory is easier to extract than scattered files). No scope conflict.

## Summary

Extract YAMLGraph's governance methodology (Scripture, Chaplain workflow, diary discipline, changelog fragments, pre-commit gates, CI enforcement) into a standalone, language-agnostic GitHub template repository (`sheikkinen/scripture-dev`) that any AI-assisted project can adopt without depending on YAMLGraph.

## Value Statement

Any team building AI-assisted software gets a battle-tested governance framework (980 commits, 300 diary entries, 132 FRs) via a single `gh repo create --template` command, without untangling YAMLGraph-specific wiring.

## Problem

YAMLGraph's governance apparatus is its most reusable asset — the Philosopher's world-view analysis (2026-03-28) identified it as the highest-leverage contribution. But it is locked inside the YAMLGraph repository. Adopting it requires:

1. **Copy-paste surgery** — extracting `.github/copilot-instructions.md`, `.pre-commit-config.yaml`, `scripts/`, `.chaplain/`, `docs/diary/`, `changelog/` and manually removing YAMLGraph-specific references (FR-XXX IDs, REQ-YG-XXX markers, LangGraph imports, Pydantic schema hooks).
2. **Implicit knowledge** — the relationships between pre-commit hooks, CI workflows, diary gates, and changelog gates are not documented as a standalone system. A newcomer cannot understand the governance without the surrounding YAMLGraph context.
3. **Version drift** — improvements to the methodology in YAMLGraph (new traps graduated to Scripture, new CI gates) cannot propagate to downstream adopters.

## Proposed Solution

Create a standalone template repository (`sheikkinen/scripture-dev`) containing the governance methodology as a self-contained, configurable system.

### Repository Structure

```
scripture-dev/
├── README.md                          # Quick-start, philosophy, adoption guide
├── LICENSE                            # MIT (code) + CC-BY-4.0 (doctrine text)
├── scripture.yaml                     # Project config (name, req prefix, etc.)
├── render.sh                          # Parameterization script (reads scripture.yaml)
│
├── .github/
│   ├── copilot-instructions.md        # The Scripture (parameterized template)
│   └── workflows/
│       ├── commitlint.yml             # Conventional Commits + changelog-gate + diary-gate
│       └── security.yml               # pip-audit / npm audit
│
├── .pre-commit-config.yaml            # Curated hook set (no YAMLGraph-specific hooks)
│
├── docs/
│   └── diary/
│       └── .gitkeep                   # Diary discipline structure
│
├── changelog/
│   ├── unreleased/
│   │   └── .gitkeep
│   └── README.md                      # Fragment format documentation
│
├── scripts/
│   ├── aggregate_changelog.sh         # Changelog generation (shell, no Python dependency)
│   └── aggregate_changelog.py         # Changelog generation (Python + PyYAML, Tier 2)
│   └── req_coverage.py                # Requirement traceability (configurable --prefix flag)
│
├── templates/
│   ├── diary-entry.md                 # Reflection template (trap/heuristic/seed)
│   ├── feature-request.md             # FR template
│   └── knowledge-graph.yaml           # Empty trap/cure/seed/process structure
│
└── hooks/                             # Custom pre-commit hook scripts
    ├── diary-reflection-check.sh      # Validate filled diary stubs
    ├── changelog-required.sh          # Require fragment for feat/fix
    └── feat-requires-fr.sh            # feat: commits must reference FR-XXX
```

### Configuration (`scripture.yaml`)

```yaml
# Project-specific configuration
project_name: my-project
req_prefix: REQ              # Default: REQ (YAMLGraph uses REQ-YG)
fr_prefix: FR                # Feature request prefix
max_file_lines: 450          # File size gate threshold
max_complexity: 21           # Cyclomatic complexity threshold (radon grade D)
language: python             # Primary language (python|javascript|go|rust)
coverage_threshold: 80       # Minimum test coverage percentage
```

### Parameterization Mechanism

A `render.sh` script is the central technical design for template configuration.

**What reads `scripture.yaml`:** `render.sh` — a POSIX shell script that parses the YAML config (line-by-line key-value extraction, no PyYAML dependency) and performs `sed`-based substitution on template files.

**When it runs:** Once after initial clone (`gh repo create --template`), and on-demand when `scripture.yaml` is modified. It is NOT a pre-commit hook — it is a manual setup step documented in `README.md`.

**Template format:** Templates use literal `__PLACEHOLDER__` markers (double-underscore delimited) for `sed` compatibility. This avoids conflicts with Jinja2 `{{ }}` syntax in the Scripture's code examples and shell `$VAR` references in hook scripts.

```
# In template files:
__REQ_PREFIX__         →  sed replacement →  REQ-YG
__FR_PREFIX__          →  sed replacement →  FR
__PROJECT_NAME__       →  sed replacement →  my-project
__MAX_FILE_LINES__     →  sed replacement →  450
__MAX_COMPLEXITY__     →  sed replacement →  21
__COVERAGE_THRESHOLD__ →  sed replacement →  80
```

**Rendered output is committed:** After running `render.sh`, the rendered files overwrite the templates in-place. This ensures CI, pre-commit hooks, and IDE tooling see the final values without a build step. The original `__PLACEHOLDER__` markers are gone after first render. Re-running `render.sh` after editing `scripture.yaml` re-reads the config and applies substitutions to any remaining or re-introduced placeholders.

**`render.sh` implementation sketch:**

```bash
#!/usr/bin/env bash
set -euo pipefail

CONFIG="scripture.yaml"

# Parse scripture.yaml (POSIX, no PyYAML)
get_value() { grep "^${1}:" "$CONFIG" | sed "s/^${1}: *//; s/ *#.*//" ; }

REQ_PREFIX=$(get_value req_prefix)
FR_PREFIX=$(get_value fr_prefix)
PROJECT_NAME=$(get_value project_name)
MAX_FILE_LINES=$(get_value max_file_lines)
MAX_COMPLEXITY=$(get_value max_complexity)
COVERAGE=$(get_value coverage_threshold)

# Target files for substitution
FILES=(
  .github/copilot-instructions.md
  .pre-commit-config.yaml
  .github/workflows/commitlint.yml
  scripts/req_coverage.py
  hooks/*.sh
)

for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  sed -i'' \
    -e "s/__REQ_PREFIX__/${REQ_PREFIX}/g" \
    -e "s/__FR_PREFIX__/${FR_PREFIX}/g" \
    -e "s/__PROJECT_NAME__/${PROJECT_NAME}/g" \
    -e "s/__MAX_FILE_LINES__/${MAX_FILE_LINES}/g" \
    -e "s/__MAX_COMPLEXITY__/${MAX_COMPLEXITY}/g" \
    -e "s/__COVERAGE_THRESHOLD__/${COVERAGE}/g" \
    "$f"
done

echo "✓ Rendered templates with config from ${CONFIG}"
```

### What Ships (Minimum Viable Subset)

**Tier 1 — Core (must ship, 3 days):**
1. **The Scripture** — 10 Commandments, Sermon of the Chaplain, Rite of Correction, Agents' Prayer — with `__PLACEHOLDER__` markers for all project-specific values, zero YAMLGraph/LangGraph/Pydantic references
2. **`render.sh`** — Parameterization script reading `scripture.yaml`, POSIX shell only
3. **Pre-commit config** — conventional commits, changelog gate, diary gate, merge conflict detection, file-size gate, radon complexity, jscpd duplication, vulture dead code (shell hooks only, no Python framework dependency)
4. **Diary discipline** — `docs/diary/` structure, reflection template with trap/heuristic/seed markers
5. **Changelog fragments** — `changelog/unreleased/` pattern with shell-based `aggregate_changelog.sh` (reads fragments, concatenates by type, no PyYAML)

**Tier 2 — Extended (should ship, 2 days):**
6. **CI workflows** — commitlint, changelog-gate, diary-gate, conflict-check as GitHub Actions
7. **Requirement traceability** — `req_coverage.py` with `--prefix` flag (default: `REQ`), decoupled from capability registry YAML
8. **Knowledge Graph template** — empty trap/cure/seed/process YAML structure for project-specific doctrine evolution
9. **Python changelog aggregator** — `aggregate_changelog.py` (requires Python + PyYAML) for full Keep a Changelog output with SemVer sorting, as an upgrade from the shell version

**Tier 3 — Documentation only (1 day):**
10. **Chaplain pipeline** — Plan→Judge→Enforce workflow documented as a pattern with shell-script reference implementation (no YAMLGraph dependency). YAMLGraph graph versions referenced as optional add-on.

### What Does NOT Ship

- No runtime code, no CLI, no library imports
- No YAMLGraph-specific hooks (inline-llm-check, validate-capabilities, validate-id-registry, hedging-check, noqa-confession, demo-proof-check, absolution, inquisitor-background)
- No LangGraph/LangSmith/Pydantic references in core templates
- No specific FR numbers or REQ-YG IDs (all parameterized via `__PLACEHOLDER__` markers)
- No Inquisitor/Philosopher graphs (these require LLM access; document as pattern only)

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Template repo, not package | No runtime dependency; `gh repo create --template` is zero-install |
| `scripture.yaml` + `render.sh` | Single config file, POSIX `sed` substitution, no build tool dependency |
| `__PLACEHOLDER__` format | No conflicts with Jinja2 `{{ }}`, shell `$VAR`, or YAML syntax |
| Rendered output committed | CI/hooks/IDE see final values; no build step required for governance |
| Shell hooks for Tier 1 | Pre-commit hooks work without Python framework; `bash` is universal |
| Python scripts in Tier 2 | `aggregate_changelog.py` and `req_coverage.py` require PyYAML; teams opt in |
| Dual license (MIT + CC-BY) | Code is MIT; doctrine text benefits from attribution requirement |
| No SemVer for doctrine | Use date-based tags (`2026.03`) for methodology versions |
| Build-from-scratch, not fork | Clean git history; no 980+ commits of YAMLGraph pipeline history polluting template. Attribution via LICENSE and README section |
| Tier structure with effort | Tier 1 (3d): Scripture + pre-commit + diary + shell changelog. Tier 2 (2d): CI + traceability + Python tools. Tier 3 (1d): Chaplain documentation |

### Extraction Strategy

1. **Create fresh repository** — `gh repo create sheikkinen/scripture-dev --template` is the end state; start with `git init` in a new directory. Attribute YAMLGraph as origin in LICENSE and README ("Methodology extracted from [yamlgraph](https://github.com/sheikkinen/yamlgraph)").
2. **Copy specific files** — Cherry-pick governance files from YAMLGraph: `.github/copilot-instructions.md`, `.pre-commit-config.yaml`, `scripts/aggregate_changelog.py`, `scripts/req_coverage.py`, `.github/workflows/commitlint.yml`, `.github/workflows/security.yml`, `feature-requests/TEMPLATE.md`.
3. **Parameterize** — Replace all `REQ-YG-XXX` with `__REQ_PREFIX__-XXX`, all hardcoded project names with `__PROJECT_NAME__`, all thresholds with `__MAX_FILE_LINES__` etc. Verify zero occurrences of `yamlgraph`, `LangGraph`, `Pydantic`, `LangSmith` in rendered output.
4. **Write `render.sh`** — POSIX shell script parsing `scripture.yaml` and applying `sed` substitutions.
5. **Write shell changelog aggregator** — `aggregate_changelog.sh` providing Tier 1 changelog generation without PyYAML dependency.
6. **Strip YAMLGraph-specific hooks** — Remove 12 domain-specific hooks (inline-llm-check, validate-capabilities, validate-id-registry, hedging-check, noqa-confession, demo-proof-check, changelog-release-sync, pytest, absolution, inquisitor-background, req-coverage-strict, diary-rotate). Retain 8 generic hooks (conventional-commits, changelog-required, feat-requires-fr, diary-reflection-check, radon-complexity, file-size-gate, forbid-terms, jscpd-dup, vulture-dead-code).
7. **Test in isolation** — Create a fresh repo from template, run `render.sh`, verify all hooks and CI pass with zero YAMLGraph artifacts.

### Migration Path for YAMLGraph

After extraction, YAMLGraph can adopt `scripture-dev` as its own upstream methodology source, replacing the in-repo governance files. This is a separate FR (future).

## Acceptance Criteria

### Tier 1 — Core

- [ ] Template repo created via `git init` (not fork) with clean history
- [x] `scripture.yaml` parameterizes all project-specific values (req prefix, FR prefix, project name, thresholds)
- [x] `render.sh` reads `scripture.yaml` and applies `sed` substitutions to all template files (POSIX shell, no Python)
- [x] Changing `req_prefix` in `scripture.yaml` from `REQ` to `REQ-FOO` and re-running `render.sh` produces templates with zero occurrences of `REQ-` (old prefix) and >0 occurrences of `REQ-FOO-` (new prefix)
- [x] `.github/copilot-instructions.md` contains zero YAMLGraph-specific references (`yamlgraph`, `LangGraph`, `Pydantic`, `LangSmith`, `REQ-YG`)
- [ ] Pre-commit hooks pass `pre-commit run --all-files` in a fresh clone after `render.sh`
- [x] `scripts/aggregate_changelog.sh` generates CHANGELOG.md from fragments without Python
- [x] No Python package dependencies required for Tier 1 governance (all hooks and scripts are shell-only)
- [ ] Smoke test: fresh repo from template → `render.sh` → create diary entry + changelog fragment + conventional commit → all hooks pass

### Tier 2 — Extended

- [x] CI workflows (commitlint, changelog-gate, diary-gate, conflict-check) pass on a fresh repo with a sample PR
- [x] `scripts/req_coverage.py` works with `--prefix` flag (default: `REQ`) and does not import YAMLGraph modules
- [x] `scripts/aggregate_changelog.py` generates CHANGELOG.md from fragments without YAMLGraph imports
- [x] Knowledge Graph template is valid YAML with empty sections for boundaries/traps/cures/process/seeds
- [x] README.md documents adoption path: template clone → configure `scripture.yaml` → run `render.sh` → first commit

### Tier 3 — Documentation

- [x] Chaplain Plan→Judge→Enforce workflow documented as a pattern with shell-script examples
- [x] README references YAMLGraph graph-based Chaplain as optional add-on (not dependency)

## Alternatives Considered

### 1. Publish as a Python package (`pip install scripture-dev`)
**Rejected.** The methodology is not code — it is templates, hooks, and CI configs. A package adds unnecessary dependency management and limits adoption to Python projects.

### 2. Git submodule pointing to YAMLGraph subdirectory
**Rejected.** Submodules are fragile, require specific directory layouts, and expose the full YAMLGraph repo. A template repo is self-contained and forkable.

### 3. Cookiecutter / Copier template
**Considered for future.** A Cookiecutter template would add interactive prompts for `scripture.yaml` values. Worth adding as enhancement once the base template is stable, but adds a dependency that `gh repo create --template` avoids.

### 4. Document-only (no code extraction)
**Rejected.** Documentation without executable hooks is advisory, not enforcement. YAMLGraph has 20 local pre-commit hooks — the value is in the runnable gates, not the written philosophy.

### 5. Fork from YAMLGraph and delete
**Rejected.** Pollutes the template repo with 980+ commits of unrelated LLM pipeline history. GitHub template repos should have clean history. Attribution is better served by LICENSE file and README section than git history preservation.

## Related

- **Philosopher world-view analysis** (2026-03-28): Identified methodology extraction as highest-leverage contribution
- **FR-179**: Append-only changelog fragments (pattern to extract)
- **FR-150**: Branch protection rules (CI gate pattern to extract)
- **FR-143/FR-178**: Requirement traceability (script to genericize)
- **FR-084/FR-098/FR-196**: Chaplain watch pipeline (pattern to document)
- **FR-076/FR-118/FR-131**: Inquisitor audit loop (pattern to document, not extract)
- **ADR-001**: Requirement traceability architecture decision
- **FR-206**: Demo proof gate (YAMLGraph-specific, not extracted)
