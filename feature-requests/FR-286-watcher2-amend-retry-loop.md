# Feature Request: Watcher2 AMEND Retry Loop

**Priority:** MEDIUM
**Type:** Enhancement  
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-04-25

## Summary

Implement retry loop for AMEND verdict in watcher2 pipeline to iteratively improve feature requests instead of treating AMEND as terminal failure.

## Value Statement

<!-- One sentence: Who benefits and how. -->
Chaplain users get auto-improving feature requests via judge feedback, reducing manual intervention from immediate failure to eventual convergence.

## Problem

Currently, watcher2 treats AMEND verdict from the judge as a terminal failure (handle_failure at line 269), moving the topic to `.chaplain/failed/` and abandoning the cycle. However, AMEND means "the FR needs refinement then re-judge" — the pipeline should revise the FR using the judge's feedback and loop back to the judge step, not give up.

The judge prompt explicitly instructs to "write issues back into the FR file" when issuing AMEND, providing actionable feedback that could be used for automatic revision.

## Proposed Solution

When judge renders AMEND verdict:

1. **Capture judge feedback** from the copilot session or judge_result state
2. **Invoke revision step** using the plan copilot with:
   - Original topic as context
   - Current FR content 
   - Judge's specific feedback as additional constraints
3. **Re-run judge step** on the revised FR
4. **Limit retries** to 2 AMEND cycles to prevent infinite loops
5. **Preserve audit trail** by committing each revision attempt

```bash
# Pseudo-code for retry loop
AMEND_RETRIES=0
MAX_AMEND_RETRIES=2

while [[ "$VERDICT" == "AMEND" && $AMEND_RETRIES -lt $MAX_AMEND_RETRIES ]]; do
    log_info "AMEND retry $((AMEND_RETRIES + 1))/$MAX_AMEND_RETRIES"
    
    # Extract judge feedback from state or session
    JUDGE_FEEDBACK=$(extract_judge_feedback)
    
    # Revise FR using plan copilot with judge feedback as constraints
    yamlgraph graph run "$GRAPH_DIR/step-revise.yaml" \
        --var judge_feedback="$JUDGE_FEEDBACK" \
        --import-state "$PIPELINE_STATE" \
        --export-state "$PIPELINE_STATE"
    
    # Commit revision
    git add feature-requests/
    git commit -m "chore: watcher2 — FR revision (AMEND retry $((AMEND_RETRIES + 1)))" --no-verify
    
    # Re-run judge
    yamlgraph graph run "$GRAPH_DIR/step-judge.yaml" \
        --import-state "$PIPELINE_STATE" \
        --export-state "$PIPELINE_STATE"
    
    # Re-extract verdict
    VERDICT=$(extract_verdict)
    AMEND_RETRIES=$((AMEND_RETRIES + 1))
done

# If still AMEND after max retries, then handle_failure
if [[ "$VERDICT" == "AMEND" ]]; then
    handle_failure "judge AMEND (exhausted retries)"
fi
```

## Acceptance Criteria

- [ ] AMEND verdict triggers revision step instead of immediate failure
- [ ] Judge feedback is extracted and passed to revision step  
- [ ] Revision step reuses plan copilot with additional judge constraints
- [ ] Revised FR is re-judged automatically
- [ ] Maximum 2 AMEND retries to prevent infinite loops
- [ ] Each revision attempt is committed with descriptive message
- [ ] SPLIT verdict remains terminal (unchanged behavior)
- [ ] After max retries, AMEND still results in handle_failure
- [ ] Tests added for retry loop logic
- [ ] Integration test with actual AMEND scenario

## Alternatives Considered

1. **Manual intervention**: Keep AMEND as terminal failure, require human review
   - Rejected: Defeats purpose of autonomous chaplain
   
2. **Unlimited retries**: No retry limit
   - Rejected: Risk of infinite loops with pathological cases
   
3. **Different retry limits**: 1, 3, or 5 retries instead of 2
   - Rationale for 2: Balance between improvement opportunity and loop prevention

4. **Separate revision graph**: Create new `step-revise.yaml` instead of reusing plan step
   - Preferred approach: Allows specialized prompting for revision vs initial planning

## Related

- `.chaplain/watcher2.sh` line 268-274 (current AMEND handling)
- `.chaplain/graphs/copilot/prompts/judge.yaml` (judge feedback format)
- `.chaplain/graphs/watcher-plan/step-judge.yaml` (judge step implementation)
- `.chaplain/graphs/watcher-plan/step-plan.yaml` (plan step to reuse for revision)
- FR-257: Chaplain research step (related pipeline enhancement)