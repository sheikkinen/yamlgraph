#!/usr/bin/env bash
# wait_ci.sh — Poll CI status until pass/fail/timeout
#
# Usage: bash wait_ci.sh --pr <pr_number>
# Sets: CI_RESULT ("success" | "failure" | "timeout")

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Parse args and call function only when executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --pr) PR_NUMBER="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    if [[ -z "$PR_NUMBER" ]]; then
        log_error "Usage: wait_ci.sh --pr <pr_number>"
        exit 1
    fi
fi

CI_POLL_INTERVAL=30
CI_TIMEOUT=600  # 10 minutes

wait_ci() {
    log_info "Waiting for CI on PR #$PR_NUMBER (timeout: ${CI_TIMEOUT}s)..."

    local elapsed=0
    while [[ $elapsed -lt $CI_TIMEOUT ]]; do
        local status
        status=$(gh pr checks "$PR_NUMBER" --json "name,state" --jq '[.[].state] | unique | join(",")' 2>&1) || {
            log_warn "Failed to query CI status: $status — retrying in ${CI_POLL_INTERVAL}s"
            sleep "$CI_POLL_INTERVAL"
            elapsed=$((elapsed + CI_POLL_INTERVAL))
            continue
        }

        log_info "CI status ($((elapsed))s): $status"

        # Check IN_PROGRESS first — wait for all checks to finish
        if echo "$status" | grep -qiE "PENDING|IN_PROGRESS|QUEUED|REQUESTED|WAITING"; then
            sleep "$CI_POLL_INTERVAL"
            elapsed=$((elapsed + CI_POLL_INTERVAL))
            continue
        fi

        # Only evaluate failure after all checks are complete
        if echo "$status" | grep -qiE "FAILURE|ERROR"; then
            CI_RESULT="failure"
            log_error "CI failed for PR #$PR_NUMBER: $status"
            echo "{\"ci_result\": \"failure\"}"
            return 1
        fi

        # All done (SUCCESS, SKIPPED, or mix of both)
        CI_RESULT="success"
        log_info "CI passed for PR #$PR_NUMBER"
        echo "{\"ci_result\": \"success\"}"
        return 0
    done

    CI_RESULT="timeout"
    log_error "CI timed out after ${CI_TIMEOUT}s for PR #$PR_NUMBER"
    echo "{\"ci_result\": \"timeout\"}"
    return 1
}

# Call function only when executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    wait_ci
fi
