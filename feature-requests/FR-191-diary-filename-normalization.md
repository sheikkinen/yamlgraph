# Feature Request: Diary Filename Convention Enforcement

**Priority:** MEDIUM  
**Type:** Bug  
**Status:** Proposed  
**Effort:** 1 day  
**Requested:** 2026-04-23

## Summary

Normalize diary filename conventions at creation boundary in watcher2 critique step to prevent CI diary gate failures.

## Value Statement

Pipeline maintainers avoid wasted CI cycles and manual renames by ensuring diary files follow the required filename pattern at creation, not just at enforcement.

## Problem

The CI diary gate (`.github/workflows/commitlint.yml`) enforces filename pattern `docs/diary/.*reflection.*fr-${FR_NUM}[^0-9]` but the critique prompt that generates diary entries never communicates the filename convention. This boundary violation causes:

1. **Naming mismatches**: FR-276 produced `2026-04-23-script-retirement-fr276.md` instead of the required `2026-04-23-reflection-fr-276-script-retirement.md`
2. **Wasted cycles**: Pipeline pushes to PR, CI fails on diary gate, requires manual rename and re-push
3. **Silent continuation**: Critique failure logs warning but continues to finalize, creating inconsistent state

**Root cause**: The naming convention is enforced downstream (CI gate) but not communicated at the point of creation (critique prompt).

## Proposed Solution

### 1. Extract FR number in watcher2 shell script

Extract FR number from feature request path and pass as variable to critique step:

```bash
# Extract FR number from the FR_PATH before calling critique
FR_NUM=$(basename "$FR_PATH" | grep -oE 'FR-[0-9]+' | sed 's/FR-//')

# Pass FR number to critique graph
yamlgraph graph run "$ENFORCE_DIR/step-critique.yaml" \
    --var fr_path="$FR_PATH" \
    --var fr_num="$FR_NUM" \
    --import-state "$ENFORCE_STATE" \
    --export-state "$ENFORCE_STATE" \
    --full 2>&1 | tee tmp/watcher2-critique.log
```

### 2. Update critique prompt with explicit filename instruction

Modify `.chaplain/graphs/enforce/prompts/enforce-critique-and-distill.yaml`:

```yaml
user: |
  ## Part 2: Diary Reflection

  Based on what happened during implementation, generate a diary reflection:

  **IMPORTANT**: Save the diary reflection to: `docs/diary/YYYY-MM-DD-reflection-fr-{fr_num}-<topic>.md`
  
  Where:
  - YYYY-MM-DD is today's date (2026-04-23)
  - fr_num is {{ fr_num }} (the FR number without 'FR-' prefix)
  - topic is a short kebab-case description of the feature

  ### Template:
  [existing template content...]
```

### 3. Add local pre-commit hook for filename validation

Add hook to `.pre-commit-config.yaml` that mirrors CI regex pattern:

```yaml
- repo: local
  hooks:
    - id: diary-filename-check
      name: diary filename pattern validation
      entry: bash -c 'BAD_FILES=$(git ls-files "docs/diary/*reflection*.md" | grep -vE "docs/diary/.*reflection.*fr-[0-9]+[^0-9]"); if [ -n "$BAD_FILES" ]; then echo "❌ Diary files with invalid filename pattern:"; echo "$BAD_FILES"; echo "Required: docs/diary/YYYY-MM-DD-reflection-fr-NNN-topic.md"; exit 1; fi'
      language: system
      pass_filenames: false
      always_run: true
      stages: [pre-commit]
```

### 4. Make critique failure blocking

Change watcher2 script to fail fast on critique failure instead of logging warning:

```bash
# Current: logs warning and continues
if ! yamlgraph graph run "$ENFORCE_DIR/step-critique.yaml" ...; then
    log_warn "Critique step failed — continuing to finalize"
fi

# Proposed: fail fast
if ! yamlgraph graph run "$ENFORCE_DIR/step-critique.yaml" ...; then
    handle_failure "critique step failed"
    continue
fi
```

## Acceptance Criteria

- [ ] **FR number extraction**: Watcher2 extracts FR number from feature request path and passes as `--var fr_num=X` to critique step
- [ ] **Prompt filename instruction**: Critique prompt explicitly instructs to save as `docs/diary/YYYY-MM-DD-reflection-fr-{fr_num}-topic.md` pattern
- [ ] **Local validation hook**: Pre-commit hook validates diary filename pattern matches CI regex before commit
- [ ] **Blocking critique**: Critique step failure terminates pipeline instead of logging warning
- [ ] **Existing files normalized**: All existing diary files follow consistent naming convention
- [ ] **Tests added**: Unit tests verify FR number extraction logic
- [ ] **Documentation updated**: README explains diary filename requirements

## Alternatives Considered

### A. Regex-based filename enforcement only
Just add local pre-commit hook without fixing creation boundary. **Rejected**: Still requires manual intervention and doesn't prevent the problem.

### B. Post-processing rename in shell
Let critique create any filename, then rename in shell script. **Rejected**: Fragile file matching logic and doesn't address root cause.

### C. Template-based filename generation
Use file templates with FR number substitution. **Rejected**: Overcomplicates the critique prompt which already generates content.

## Related

- `.github/workflows/commitlint.yml` - CI diary gate implementation
- `.chaplain/graphs/enforce/prompts/enforce-critique-and-distill.yaml` - Critique prompt
- `.chaplain/watcher2.sh` - Main pipeline orchestrator  
- `.pre-commit-config.yaml` - Local validation hooks
- `docs/diary/` - Existing diary entries requiring normalization