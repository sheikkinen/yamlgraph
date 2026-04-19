# Reflection: FR-250 A2A Server — Complete Protocol Gaps

**Date:** 2026-04-20
**FR:** FR-250
**Branch:** feat/fr-250-a2a-server-complete-gaps

## What Was Done

Implemented the three remaining A2A protocol requirements deferred from FR-208: `task/get` retrieval (REQ-YG-210), `task/sendSubscribe` SSE streaming (REQ-YG-211), and full `input-required` resume flow with `Command(resume=...)` (REQ-YG-213). Added interrupt detection helpers (`_detect_interrupt`, `_extract_interrupt_payload`), streaming artifact events for incremental token delivery, 17 new unit tests, and updated `reference/a2a-server.md` with streaming and resume documentation.

## Cognitive Trap: Partial Implementation as Shipped Feature

FR-208 shipped the A2A server with three requirements formally registered but not implemented — they existed in ARCHITECTURE.md and had REQ-YG IDs, but the code paths were absent. This is a subtle form of **plausible wrong answer**: the capability table says "complete" but the protocol contract is not. The danger is that downstream consumers (FR-248's consumer phase2) build against the spec, not the implementation, and discover the gap in integration.

The cure here was to have FR-250 explicitly target the deferred requirements by ID, making the gap traceable and closeable. The test-first approach (17 new unit tests) proved each protocol path before the PR shipped.

## Heuristic

**Deferred requirements have a half-life**: Every cycle they remain open, they become more expensive to close (new code grows around the gap, more integration tests assume the missing behavior). If a requirement is registered but not implemented, set a maximum deferral count in the FR — if it hasn't shipped by the third subsequent FR touching the same module, escalate to blocking.

## Seed

Could the `req_coverage` tool flag requirements with `implemented: false` in the CAP yaml, and fail CI when such requirements have been open for more than N FRs? That would surface deferred requirements automatically rather than relying on manual FR audits.
