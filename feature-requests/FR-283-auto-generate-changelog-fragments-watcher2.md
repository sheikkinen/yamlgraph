# Feature Request: Auto-Generate Changelog Fragments in Watcher2 Pipeline

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-04-25

## Summary

Auto-generate changelog fragments in the watcher2 pipeline to eliminate the #1 cause of manual intervention: missing or incorrectly numbered changelog fragments in feature PRs.

## Value Statement

<!-- One sentence: Who benefits and how. -->
Watcher2 automation eliminates manual changelog intervention, reducing PR processing failures from 100% (5/5 recent PRs) to 0% and speeding up deployment cycles.

## Problem

Every watcher2 PR requires manual changelog fragment addition. The pipeline has no changelog generation step — it is the #1 cause of manual intervention (5/5 PRs on 2026-04-25 required manual fix).

### Evidence

- PR #214 (FR-278): missing changelog → manual add
- PR #218 (FR-280): missing changelog → manual add  
- PR #220 (FR-219): wrong FR number in fragment (fr-276 vs fr-219) → manual rename
- PR #222 (FR-281): missing changelog → manual add

### Root Cause

No prompt or shell step creates the changelog fragment:
- `enforce-implement.yaml`: no changelog instruction
- `enforce-critique-and-distill.yaml`: creates diary but not changelog
- `enforce-finalize.yaml`: only handles pre-commit
- `enforce-ci-remediate.yaml`: mentions changelog but only after CI fails (too late), lacks FR context

## Proposed Solution

Add changelog fragment generation at multiple pipeline layers for defense-in-depth:

### Layer 1: Shell Step (Primary) — Between Step 3 and 4

Add deterministic shell-based changelog generation after critique/diary commit, before finalize:

```bash
# Extract FR number from feature request path
FR_NUM=$(basename "$FR_PATH" | grep -oE 'FR-[0-9]+' | sed 's/FR-//')
FR_ID="FR-${FR_NUM}"

# Generate changelog fragment filename
CHANGELOG_FRAG="changelog/unreleased/fr-${FR_NUM}-$(basename "$FR_PATH" .md | sed "s/FR-${FR_NUM}-//" | head -c 40).md"

if [[ ! -f "$CHANGELOG_FRAG" ]]; then
    # Derive change type and scope from FR path
    CHANGE_TYPE="feat"
    SCOPE=$(basename "$FR_PATH" .md | sed "s/FR-${FR_NUM}-//" | cut -d- -f1)
    
    # Find requirement ID from capability registry
    REQ_ID=$(grep -l "fr: $FR_ID" capabilities/CAP-*.yaml 2>/dev/null | head -1 | \
        xargs -I{} grep -oE 'REQ-YG-[0-9]+' {} 2>/dev/null | head -1)
    
    # Generate fragment content
    mkdir -p "$(dirname "$CHANGELOG_FRAG")"
    {
        echo "---"
        echo "type: $CHANGE_TYPE"
        echo "scope: $SCOPE"
        [[ -n "$REQ_ID" ]] && echo "req: $REQ_ID"
        echo "---"
        echo "- **$FR_ID**: Generated changelog fragment. ($REQ_ID)"
    } > "$CHANGELOG_FRAG"
    
    log_info "Generated changelog fragment: $CHANGELOG_FRAG"
fi
```

### Layer 2: Critique Prompt Enhancement

Add Part 3 to `enforce-critique-and-distill.yaml` using `{{ fr_num }}` template variable:

```yaml
template: |
  ...existing critique content...
  
  ## Part 3: Changelog Fragment
  
  Create a changelog fragment in `changelog/unreleased/fr-{{ fr_num }}-<descriptive-name>.md`:
  
  ```markdown
  ---
  type: feat
  scope: <primary-scope>
  req: <REQ-YG-XXX-if-available>
  ---
  - **FR-{{ fr_num }}**: Brief description of the change. ({{ req_id }})
  ```
  
  Use the FR path to derive scope and filename.
```

### Layer 3: Finalize Verification

Add Part 0 to `enforce-finalize.yaml` to verify changelog fragment exists before running pre-commit:

```yaml
template: |
  ## Part 0: Verify Changelog Fragment
  
  Before proceeding with pre-commit fixes, verify the changelog fragment exists:
  - File: `changelog/unreleased/fr-{{ fr_num }}-*.md`
  - Must contain correct FR number: `FR-{{ fr_num }}`
  
  If missing, create it now with appropriate type/scope/req fields.
  
  ## Part 1: Pre-commit Fixes
  ...existing content...
```

### Layer 4: CI Remediation Context

Pass `fr_path` variable to `step-ci-remediate.yaml` and update `enforce-ci-remediate.yaml` to use FR context when creating missing fragments.

## Acceptance Criteria

- [ ] Changelog fragment auto-generated with correct FR number from `FR_PATH` variable
- [ ] Fragment type/scope/req derived from capability registry when available  
- [ ] Fragment FR number matches branch FR (no cross-wiring like fr-276 vs fr-219)
- [ ] Shell step generates fragment between critique and finalize steps
- [ ] Finalize step verifies changelog exists before pre-commit
- [ ] CI remediation receives FR context for correct fragment naming
- [ ] Existing ruff fix flow unchanged (lines 314-316 are already correct)
- [ ] All CI gates pass without manual changelog intervention
- [ ] Generated fragments follow existing naming convention: `fr-{num}-{descriptive}.md`
- [ ] Fragment content includes proper YAML frontmatter and FR reference

## Alternatives Considered

1. **Only CI remediation approach**: Too late in pipeline, lacks FR context for correct numbering
2. **Only prompt-based approach**: Unreliable, prompt adherence varies
3. **Pre-commit hook approach**: Runs too frequently, lacks pipeline context
4. **Manual approach (current)**: 100% failure rate, blocks automation

The defense-in-depth approach (shell + prompt + finalize + CI) provides multiple layers of protection.

## Related

- FR-179: Append-Only Changelog system
- CAP-66: Append-Only Changelog capability
- `.github/workflows/commitlint.yml`: changelog-gate enforcement
- `scripts/aggregate_changelog.py`: Fragment aggregation
- Evidence from recent watcher2 PR failures requiring manual intervention