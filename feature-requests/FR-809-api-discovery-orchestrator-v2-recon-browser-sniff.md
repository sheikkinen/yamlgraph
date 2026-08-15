# Feature Request: FR-809 — API Discovery Orchestrator v2: Recon and Browser-Sniff Routing

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-15
**First consumer / first event:** the first control-plane investigation
where the v1 orchestrator returns `not_found` on a source that a human
later finds by hand — either because GitHub prior art would have named
the API base URL (recon) or because the portal is a SPA whose API only
appears in browser network traffic (browser-sniff).

**Parent plan:** `docs/adaptive-probing-plan.md` §4.7 (full route)

## Summary

Extend the API discovery orchestrator (`examples/api-discovery/graph.yaml`,
FR-791) with the two steps its judgement deliberately excluded from v1:
recon (FR-787, Enforced) as an optional front-of-pipe evidence source, and
browser-sniff (FR-789, Enforced) as the expensive last resort when
page-analysis identifies a SPA with no visible API. Both steps exist,
are Enforced, and already ship graph-runtime tool manifests
(`steps/recon.tool.yaml`, `steps/browser_sniff.tool.yaml`) built for
exactly this consumer.

## Value Statement

For control-plane source investigations, versus manually re-running recon
or browser-sniff as standalone graphs after a v1 `not_found`: the
orchestrator exhausts its own step inventory before rendering a verdict,
so a `not_found` becomes trustworthy — the pain is verdicts that are
wrong only because the router never consulted evidence the pipeline
already knows how to gather.

## Problem

v1 (frozen by the FR-791 judgement, R-1) routes endpoint-probe →
page-analysis → platform-confirm → schema-extract → synthesize. Two
failure classes are structural:

1. **SPA-without-API**: page-analysis detects a client-rendered portal
   with no embedded API references; v1 routes straight to a terminal
   not-found/manual result. FR-789's browser-sniff exists precisely for
   this case (headless Chromium network capture) but is never invoked.
2. **Thin candidate generation**: candidate URLs come from one llm node
   over the hypothesis and domain hint. FR-787's recon mines GitHub for
   prior-art base URLs, auth patterns, and schema hints — evidence that
   would improve or rescue candidate generation — but is never invoked.

The v1 exclusion was correct sequencing (the steps were unenforced when
FR-791 was judged), not architecture. Both dependencies are now Enforced
with committed smokes.

## Ideal Result

A statfin-class investigation behaves as v1. A SPA-only portal produces:
recon-informed candidates → probe finds no API → page-analysis says SPA →
browser-sniff captures the XHR traffic → platform-confirm/schema-extract
run against the sniffed endpoints → `found` profile. A truly absent
source still terminates `not_found`, now with `steps_tried` proving
recon and browser-sniff were consulted.

## Proposed Solution

- **Recon (optional front):** `tool_call` on `steps/recon.tool.yaml`
  gated by an input flag (`use_recon`, default true) or a cheap
  hypothesis-shape condition; its `recon_result` (candidate URLs, auth
  hints, schema hints) feeds `generate_candidates` as additional
  evidence.
- **Browser-sniff (conditional last resort):** `tool_call` on
  `steps/browser_sniff.tool.yaml` entered only on the SPA-without-API
  path (routing-visible signal per the FR-791 deviation pattern —
  candidate hints or a dedicated router-visible flag; see FR-810 for the
  general cure). Its `sniff_result.api_calls` re-enter the
  platform-confirm path as live endpoint evidence; its `needs_manual`
  verdict hint routes to synthesize with verdict `needs_manual`.
- **Synthesize prompt:** extend the "Actual steps that ran" evidence
  section (FR-791 repair) to cover the two new wrappers; `steps_tried`
  stays copy-only.
- **Authoring route:** all graph/prompt changes via `scripts/author.sh`
  with validation record (FR-767).

## Acceptance Criteria

- [ ] AC-01: Orchestrator references `steps/recon.tool.yaml` and `steps/browser_sniff.tool.yaml` via `type: tool_call`; no subgraph nodes; graph lint passes.
- [ ] AC-02: Recon can be disabled per run; with it disabled, the v1 route and both FR-791 smoke outcomes are preserved (regression smokes re-run with identical assertions).
- [ ] AC-03: Browser-sniff is entered only on the SPA-without-API path; a deterministic smoke against the committed FR-784 SPA fixture (served with its dynamic handler) reaches browser-sniff and carries sniffed `/api/*` calls into the terminal result.
- [ ] AC-04: A CAPTCHA/auth fixture smoke terminates `needs_manual` with `manual_reason` propagated into the result.
- [ ] AC-05: `steps_tried` lists recon/browser-sniff only when their wrappers are non-empty (copy-only discipline preserved).
- [ ] AC-06: Authored via `scripts/author.sh`; report records lint, smoke commands, and honest outcomes; tests updated (FR-791 test module extended or sibling module added) with req markers.

## Alternatives Considered

- **Keep running the steps standalone after a v1 not_found:** preserves the manual sequencing the orchestrator exists to eliminate; the human becomes the router again.
- **Always run browser-sniff:** headless Chromium per investigation is the most expensive step; conditional entry is the point of the skip-logic architecture.

## Related

- FR-791 (v1 orchestrator — the surface being extended; its judgement explicitly deferred recon/browser-sniff to v2)
- FR-787 (recon step — Enforced 2026-08-15), FR-789 (browser-sniff step — Enforced 2026-08-15)
- FR-810 (router-visible step outputs — the clean mechanism for AC-03's entry condition; this FR can ship with the candidate-hints workaround if FR-810 is not yet enforced)
- FR-784 (SPA fixture + dynamic handler used by AC-03/AC-04 smokes)

**Prior art:** FR-791's judgement (R-1) excluded recon/browser-sniff from v1 because both were then unenforced — a sequencing gate, not a rejection. Both are now Enforced with committed smokes; this FR is the planned re-entry named in FR-791's Implementation Record and diary.
