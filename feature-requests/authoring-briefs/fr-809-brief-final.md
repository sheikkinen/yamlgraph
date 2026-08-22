# Task: FR-809 resumed validation — live smokes + honest blocked-validation record

Validation-only continuation of the FR-809 authoring run. The v2
orchestrator is authored in the working tree and structurally green; do
NOT modify graph.yaml, prompts, nodes, or tests. Your job: run the live
smokes below, then EXTEND tmp/draft-authoring-report.md (preserve its
existing Artifacts / Precedent / Validation / Repairs sections) with a
"Live smokes" section and an updated "Blocked validation" section.

Every graph run MUST be prefixed with `PROVIDER=anthropic` — the .env
default (deepseek) currently rejects structured output (400s on both
response_format and tool_choice; verified today, logs/fr809-smoke-pos*.log).

The FR-784 fixture server is ALREADY RUNNING at http://127.0.0.1:8799/
(started outside this run) — do not start or stop it.

## Validation

1. Positive regression smoke (FR-791 AC-07 / FR-809 AC-02):

```bash
PROVIDER=anthropic yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="Statistics Finland publishes official statistics through a PxWeb API" --var purpose="programmatic access to Finnish population statistics" --var country="FI" --var domain_hint="statfin.stat.fi PxWeb StatFin database" --var use_recon=false --full
```

Assert: `verdict == "found"`, platform_family PxWeb, a statfin.stat.fi
PxWeb API URL with non-empty endpoints and sample data.

2. Negative regression smoke (FR-791 AC-08 / FR-809 AC-02):

```bash
PROVIDER=anthropic yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="The domain example.invalid hosts an open data API" --var purpose="test negative discovery" --var country="FI" --var domain_hint="example.invalid" --var use_recon=false --full
```

Assert: `verdict` is `not_found` or `needs_manual`, non-empty
`steps_tried`, a permitted reason, and alternatives or manual guidance.

3. SPA fixture smoke — run ONCE, record the outcome verbatim:

```bash
PROVIDER=anthropic yamlgraph graph run examples/api-discovery/graph.yaml --var hypothesis="A local test portal exposes a JSON data API used by its single-page frontend" --var purpose="capture the SPA's backing data API" --var country="FI" --var domain_hint="http://127.0.0.1:8799/" --var use_recon=false --full
```

Expected honest outcome (verified 3x today, logs/fr809-smoke-spa*.log):
the run terminates `found` via endpoint-probe WITHOUT routing through
browser-sniff, because the frozen FR-784 fixture is curl-transparent —
it serves /api/data, /api/item, /api/search to plain curl at canonical
guessable paths, and the probe agent also reads the inline JS fetch
calls from the page source. Record whatever actually happens.

## Blocked validation to record

Record AC-05 and AC-06 as BLOCKED-UNREACHABLE against the frozen
fixture, with this rationale (operator decision 2026-08-16):

- The judgement's C-4 GATE freezes the FR-784 dynamic-handler semantics,
  which serve the API endpoints to any HTTP client at guessable paths.
- The browser-sniff entry edge requires parsed
  `page_findings.is_spa == true and page_findings.api_found != true`,
  i.e. the probe must find nothing — structurally impossible here: the
  probe honestly finds the API by curl every run (4/4 runs:
  logs/fr809-smoke-spa1.log, spa2, spa3, captcha1).
- The browser-sniff route itself IS live-proven: the stat.fi run
  (logs/fr809-smoke-pos6.log) fired the exact SPA-clause edge and
  executed network_sniff end-to-end; FR-784/FR-789 step tests assert the
  exact endpoint capture and /analytics/collect telemetry exclusion at
  step level.

Write the exact commands you ran, quoted raw evidence (actual verdicts,
endpoints, reasons from the output), outcomes, and any repairs. Honesty
over completeness: if a smoke fails, record the failure — do not retry
more than once.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
