# Diary: Three Boundary Fixes in One Pass

**Date:** 2026-07-03
**FRs:** FR-669, FR-670, FR-671

## Observation

Three bugs, all the same pattern: silent fallback at a system boundary.

- **FR-669**: JSON extraction fails → re-raises the *original* provider
  error instead of the extraction failure. The user sees "response_format
  not supported" when the real problem is "model returned prose."
- **FR-670**: A2A response has no text parts → returns `""`. Downstream
  prompts render nothing, LLM fills the gap with plausible invention.
- **FR-671**: Graph execution fails inside MCP handler → returns error JSON
  without logging. The outer handler logs but never fires because the inner
  handler catches first.

All three are `the_one_law` violations: error information is lost or
transformed at the boundary where external data enters.

## Trap

**downstream_fix** dressed as **hedging check**: the original authors
weren't being careless — they were being "graceful." Return empty string
instead of crashing. Return the original error instead of a new one.
Suppress logs to avoid noise. Each decision seemed reasonable in isolation.
The trap is that "graceful degradation" at a boundary is indistinguishable
from information loss.

## Cure

**Commandment 6** applied mechanically: when a filter yields nothing,
raise. When an error occurs, log it. When a fallback fails, name the
failure, not the original trigger. The three fixes are 5 lines of
production code total.

## Seed

Cross-thread logging (FR-671) revealed that `caplog` doesn't capture
logs from `run_in_executor` threads. This means any async MCP test using
caplog is testing the wrong thing. Should we add a
`thread_safe_log_capture` fixture, or is `patch("module.logger")` the
correct pattern for cross-thread assertion?
