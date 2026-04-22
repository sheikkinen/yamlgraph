#!/usr/bin/env bash
# wait_ci.sh — Poll CI status until pass/fail/timeout
#
# Expects: PR_NUMBER set by orchestrator
# Sets: CI_RESULT ("success" | "failure" | "timeout")

CI_POLL_INTERVAL=30
CI_TIMEOUT=600  # 10 minutes

wait_ci() {
    log_info "Waiting for CI on PR #$PR_NUMBER (timeout: ${CI_TIMEOUT}s)..."

    local elapsed=0
    while [[ $elapsed -lt $CI_TIMEOUT ]]; do
        local status
        status=$(gh pr checks "$PR_NUMBER" --json "name,state" --jq '[.[].state] | unique | join(",")' 2>/dev/null) || {
            log_warn "Failed to query CI status — retrying"
            sleep "$CI_POLL_INTERVAL"
            elapsed=$((elapsed + CI_POLL_INTERVAL))
            continue
        }

        # All checks passed
        if [[ "$status" == "SUCCESS" ]]; then
            CI_RESULT="success"
            log_info "CI passed for PR #$PR_NUMBER"
            return 0
        fi

        # Any check failed
        if echo "$status" | grep -q "FAILURE\|ERROR"; then
            CI_RESULT="failure"
            log_error "CI failed for PR #$PR_NUMBER: $status"
            return 1
        fi

        # Still pending
        sleep "$CI_POLL_INTERVAL"
        elapsed=$((elapsed + CI_POLL_INTERVAL))
    done

    CI_RESULT="timeout"
    log_error "CI timed out after ${CI_TIMEOUT}s for PR #$PR_NUMBER"
    return 1
}
