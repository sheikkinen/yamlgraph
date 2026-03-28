# scripture-dev

> Battle-tested governance framework for AI-assisted software development.

Methodology extracted from [yamlgraph](https://github.com/sheikkinen/yamlgraph) — 980+ commits, 300 diary entries, 130+ feature requests of accumulated engineering discipline.

## Quick Start

### 1. Create from template

```bash
gh repo create my-project --template sheikkinen/scripture-dev --clone
cd my-project
```

### 2. Configure

Edit `scripture.yaml` with your project values:

```yaml
project_name: my-project
req_prefix: REQ              # Requirement marker prefix
fr_prefix: FR                # Feature request prefix
max_file_lines: 450          # File size gate
max_complexity: 21           # Cyclomatic complexity threshold
coverage_threshold: 80       # Minimum test coverage %
```

### 3. Render

```bash
./render.sh
```

This reads `scripture.yaml` and applies values to all template files. The `_templates/` directory contains the source templates with `__PLACEHOLDER__` markers; `render.sh` substitutes them and writes rendered files to their target locations.

### 4. Install hooks

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

### 5. First commit

```bash
# Create a diary entry
cp templates/diary-entry.md docs/diary/$(date +%Y-%m-%d)-reflection-initial-setup.md
# Edit the diary entry...

# Create a changelog fragment
cat > changelog/unreleased/initial-setup.md << 'EOF'
---
type: feat
scope: setup
---
- **Initial Setup**: Configured scripture-dev governance framework.
EOF

# Commit
git add -A
git commit -m "feat(setup): initial scripture-dev configuration"
```

## What's Included

### The Scripture (`.github/copilot-instructions.md`)

The 10 Commandments of software craft — a framework-agnostic governance doctrine:

1. Research before coding
2. Demonstrate with example
3. Don't utter code in vain
4. Honor existing patterns
5. Sanctify outputs with types
6. Bear witness of errors
7. Be faithful to TDD
8. Kill all entropy
9. Define operational truth
10. Preserve and improve the doctrine

Plus: Sermon of the Chaplain (Plan → Judge → Enforce workflow), Knowledge Graph (traps/cures/seeds), Rite of Correction, and Agents' Prayer.

### Pre-commit Hooks

| Hook | Purpose |
|------|---------|
| `conventional-pre-commit` | Enforce Conventional Commits format |
| `feat-requires-fr` | `feat:` commits must reference FR-XXX |
| `changelog-required` | `feat/fix` commits need changelog fragment |
| `diary-reflection-check` | Block unfilled diary template stubs |
| `radon-complexity` | Block functions exceeding complexity threshold |
| `file-size-gate` | Warn/fail on oversized files |
| `forbid-terms` | Block TODO/FIXME markers |
| `jscpd-dup` | Detect code duplication |
| `vulture-dead-code` | Detect dead code |

### CI Workflows

| Workflow | Gates |
|----------|-------|
| `commitlint.yml` | PR title validation, changelog-gate, diary-gate, conflict-check |
| `security.yml` | Dependency vulnerability scanning (pip-audit) |

### Diary Discipline (`docs/diary/`)

Metacognitive reflection after every task:
- **Trap**: Name the cognitive hazard encountered
- **Heuristic**: Extract a reusable principle
- **Seed**: Plant a forward-looking question

### Changelog Fragments (`changelog/`)

Append-only fragments eliminate merge conflicts:
```
changelog/unreleased/FR-001-feature.md
changelog/1.0.0/FR-001-feature.md
```

Generate CHANGELOG.md: `./scripts/aggregate_changelog.sh > CHANGELOG.md`

### Requirement Traceability (`scripts/req_coverage.py`)

Tag tests with requirement markers, track coverage:
```python
@pytest.mark.req("REQ-001")
def test_feature():
    ...
```

```bash
python scripts/req_coverage.py --prefix REQ
```

## Re-rendering

To change configuration after initial setup:

1. Edit `scripture.yaml`
2. Run `./render.sh`
3. Review changes with `git diff`
4. Commit

The `_templates/` directory is the source of truth — `render.sh` always renders from templates, so re-rendering is safe and idempotent.

## Chaplain Workflow (Optional Pattern)

The Plan → Judge → Enforce workflow can be automated with shell scripts or AI pipelines:

1. **Plan**: Write a feature request describing the problem and proposed solution
2. **Judge**: Critically review — resolve contradictions, eliminate ambiguity, freeze scope
3. **Enforce**: Implement with TDD discipline — failing test first, minimal change, refactor

This pattern works with any AI coding assistant (Copilot, Cursor, Claude) or human reviewers. The `.github/copilot-instructions.md` file provides the governance context automatically.

## License

Code: MIT License
Doctrine text: CC-BY-4.0

Methodology extracted from [yamlgraph](https://github.com/sheikkinen/yamlgraph).
