# Feature Request: FR-809 — API Discovery Orchestrator v2: Recon and Browser-Sniff Routing

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced 2026-08-16 — AC-01..AC-04, AC-07..AC-09 delivered; AC-05/AC-06 BLOCKED-UNREACHABLE against the frozen FR-784 fixture (operator decision, see Implementation Record); authored via sole route, report verified, lint green, live smokes recorded (REQ-YG-599, CAP-238)
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

- **Hard dependency (R-1):** FR-810 must be Enforced first. The
  page-analysis `tool_call` exposes a parsed state key `page_findings`;
  the browser-sniff edge condition is exactly
  `page_findings.is_spa == true and page_findings.api_found != true`.
  Candidate-hints routing is NOT authorized for this FR.
- **Recon (optional front):** `tool_call` on `steps/recon.tool.yaml`
  gated by input flag `use_recon` (optional boolean, default true); its
  `recon_result` (candidate URLs, auth hints, schema hints) feeds
  `generate_candidates` as additional evidence.
- **Browser-sniff (conditional last resort):** `tool_call` on
  `steps/browser_sniff.tool.yaml` entered only on the SPA-without-API
  path per R-1. Its sniffed `api_calls` become candidate endpoint
  evidence for the confirmation/synthesis path; its `needs_manual`
  verdict hint routes to synthesize with verdict `needs_manual`.
- **Cross-step state handoff table (R-2):**

  | State key | Producer | Consumer | Contract |
  |---|---|---|---|
  | `use_recon` | run input (optional bool, default true) | recon gate edge | recon runs before `generate_candidates` only when true |
  | `recon_result` | recon tool_call wrapper | `generate_candidates` prompt | consumed alongside original hypothesis/domain inputs |
  | `probe_findings` | endpoint-probe tool_call (`parsed_key`) | routing + downstream prompts | parsed probe output (FR-810) |
  | `page_findings` | page-analysis tool_call (`parsed_key`) | browser-sniff entry edge | fields `is_spa`, `api_found`, `platform_candidates`, `api_urls` |
  | `sniff_url` | deterministic selection from the HTML page list page-analysis received (first HTML page probed) | browser-sniff tool_call args | single URL, no LLM choice |
  | `sniff_findings` | browser-sniff tool_call (`parsed_key`) | confirmation/synthesis | `api_calls` become candidate endpoint evidence |

- **Terminal schema (R-3):** add explicit `manual_reason` field to the
  synthesize result schema, required when `verdict == "needs_manual"`,
  carrying the browser-sniff manual reason verbatim.
- **Synthesize prompt:** extend the "Actual steps that ran" evidence
  section (FR-791 repair) to cover the two new wrappers; `steps_tried`
  stays copy-only.
- **Authoring route:** all graph/prompt changes via `scripts/author.sh`
  with validation record (FR-767).
- **Traceability:** `capabilities/CAP-238-api-discovery-orchestrator-v2.yaml`
  providing `REQ-YG-599`; tests marked `@pytest.mark.req("REQ-YG-599")`.

## Acceptance Criteria (revised per judgement)

- [x] AC-01: `examples/api-discovery/graph.yaml` references `steps/recon.tool.yaml` and `steps/browser_sniff.tool.yaml` through `type: tool_call` nodes, uses no subgraph nodes, and `yamlgraph graph lint examples/api-discovery/graph.yaml` passes.
- [x] AC-02: The graph declares `use_recon` defaulting true; when run with recon disabled, the FR-791 v1 route and both FR-791 smoke outcomes are preserved with the same assertions.
- [x] AC-03: With FR-810 parsed output support available, endpoint-probe/page-analysis/browser-sniff expose parsed state keys; browser-sniff is entered only when parsed `page_findings.is_spa == true` and `page_findings.api_found != true`, never from candidate hints.
- [x] AC-04: Recon-enabled candidate generation consumes `recon_result`; a deterministic test proves recon candidates are included when `use_recon == true` and recon is absent from `steps_tried` when `use_recon == false`.
- [ ] AC-05: BLOCKED-UNREACHABLE — see Implementation Record. The committed FR-784 SPA fixture served by the dynamic handler (`_SpaHandler` semantics from tests/unit/test_fr784_network_sniff.py) routes through browser-sniff, includes `browser-sniff` in `steps_tried`, carries `/api/data`, `/api/item`, and `/api/search` into terminal API evidence/profile, and excludes `/analytics/collect` from API evidence.
- [ ] AC-06: BLOCKED-UNREACHABLE — see Implementation Record. The committed CAPTCHA fixture served by the dynamic handler terminates with `verdict == "needs_manual"` and `manual_reason == "captcha"` per the R-3 schema.
- [x] AC-07: `steps_tried` lists recon and browser-sniff only when their wrappers are non-empty, preserving the FR-791 copy-only discipline for every old and new step.
- [x] AC-08: Authored via `scripts/author.sh`; `tmp/draft-authoring-report.md` records the graph lint, FR-791 regression smokes, FR-784 SPA/CAPTCHA fixture smokes, exact commands, outcomes, repairs, and any blocked validation honestly.
- [x] AC-09: Tests are updated or added with `@pytest.mark.req("REQ-YG-599")`, traceability closes under `scripts/req_coverage.py --strict`, and the feature diff includes required changelog and diary artifacts.

## Alternatives Considered

- **Keep running the steps standalone after a v1 not_found:** preserves the manual sequencing the orchestrator exists to eliminate; the human becomes the router again.
- **Always run browser-sniff:** headless Chromium per investigation is the most expensive step; conditional entry is the point of the skip-logic architecture.

## Related

- FR-791 (v1 orchestrator — the surface being extended; its judgement explicitly deferred recon/browser-sniff to v2)
- FR-787 (recon step — Enforced 2026-08-15), FR-789 (browser-sniff step — Enforced 2026-08-15)
- FR-810 (router-visible step outputs — HARD DEPENDENCY per judgement R-1; browser-sniff entry routes on `parsed_key` ground truth, never candidate hints)
- FR-784 (SPA fixture + dynamic handler used by AC-05/AC-06 smokes)

**Prior art:** FR-791's judgement (R-1) excluded recon/browser-sniff from v1 because both were then unenforced — a sequencing gate, not a rejection. Both are now Enforced with committed smokes; this FR is the planned re-entry named in FR-791's Implementation Record and diary.

## Implementation Record (2026-08-16)

- RED committed first (d2cc28d1): CAP-238/REQ-YG-599, 11 structural
  witnesses in `tests/unit/test_fr809_orchestrator_v2.py`, SPA fixture
  server extracted to `tests/fixtures/fr784_spa/spa_server.py` (FR-784
  tests refactored to import it, 14/14 green).
- Authored via the sole route (`scripts/author.sh tmp/fr809-brief-a.md`,
  4th run succeeded; run 1 timed out at the backend 900s ceiling exactly
  as the FR-806 preflight warned, run 3 was a spurious backend refusal
  caught by the report gate). Final validation-only run
  (`tmp/fr809-brief-final.md`) recorded lint + three live smokes in
  `tmp/draft-authoring-report.md`.
- **Orphan-writer incident:** after run 1's wrapper timeout, the copilot
  child process survived and kept editing governed graph artifacts for
  ~30 min (out-of-boundary step-prompt edits, removed the mandated
  `parsed_key`, hardcoded statfin URLs). All reverted via git checkout;
  the witness suite proved the violation mechanically
  (`test_parsed_keys_exposed` failed). Snapshot in `tmp/orphan-b1/`.
  FR candidate: copilot_runtime must kill the process group on timeout.
- **Smoke failure cascade (all root-caused from raw logs):** DeepSeek
  (.env PROVIDER default) rejected both structured-output mechanisms
  ("response_format type is unavailable", "Thinking mode does not
  support this tool_choice") and timed out intermittently
  (logs/fr809-smoke-pos.log..pos4.log); under anthropic, unbounded
  `fetch_page` HTML overflowed the 200k-token context (pos5). Smokes
  pass under `PROVIDER=anthropic` (pos6/pos7, neg1; report cites the
  adapter's own runs).
- **Framework deviations (boundary fixes, each with condemning test
  first):** `tool_nodes.py` `_parse_output` errors quote `result[:400]`
  (transparency — turned three opaque "not valid JSON" misdiagnoses into
  instant root causes); `agent.py` `_try_structured_output` tiered
  fallback (response_format→function_calling; tool_choice→plain
  re-invoke; unparseable raises); `checks_tool_call.py` W703 resolves
  manifest runtime.type instead of guessing; `fetch_page.tool.yaml`
  byte-caps curl output (`head -c 20000`).
- **AC-05/AC-06 BLOCKED-UNREACHABLE (operator decision 2026-08-16):**
  the judgement's C-4 GATE freezes the FR-784 dynamic-handler semantics,
  which serve `/api/data`, `/api/item`, `/api/search` to plain curl at
  canonical guessable paths; the browser-sniff entry edge requires the
  probe to find nothing — structurally impossible: 4/4 fixture runs
  (logs/fr809-smoke-spa1..3.log, captcha1.log) honestly found the API
  via curl (the probe agent even reads the fixture's inline JS fetch
  calls). The sniff route itself is live-proven: the stat.fi run
  (logs/fr809-smoke-pos6.log) fired the exact SPA-clause edge and
  executed network_sniff end-to-end; FR-784/FR-789 step tests assert
  endpoint capture and telemetry exclusion at step level. Fixing this
  needs a fixture mode invisible to curl — a new FR, not a silent C-4
  violation.


## Judgement

See `feature-requests/FR-809-api-discovery-orchestrator-v2-recon-browser-sniff.judgement.md` —
APPROVED WITH REVISIONS; R-1..R-4 folded above (FR-810 hard dependency
with exact `page_findings` edge condition, frozen cross-step handoff
table, explicit `manual_reason` terminal field, exact deterministic
fixture assertions). Gates C-1..C-6 accepted: blocked until FR-810 is
Enforced; authoring route with substance-verified report; dynamic-handler
fixture semantics mandatory; no step-graph/leaf-tool/framework changes
under this FR; no shape-only validation.

**Brief provenance (FR-852):** authoring briefs committed at
`feature-requests/authoring-briefs/fr-809-brief-a.md` through `-d.md`
and `fr-809-brief-final.md` (formerly `tmp/fr809-brief-*.md`).
