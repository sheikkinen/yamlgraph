# Judgement: FR-784 Playwright Network Sniff Utility

**Verdict:** APPROVED WITH REVISIONS - the probe action is real and belongs as an example-level deterministic tool, but authority activates only after the output contract, dependency contract, deterministic fixture, and filtering/redaction rules are folded into the FR.

**Reviewed against:** `feature-requests/FR-784-playwright-network-sniff-utility.md`; `docs/adaptive-probing-plan.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `feature-requests/FR-789-api-discovery-browser-sniff-step.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The FR has a concrete consumer and first event: FR-789 needs the utility when a browser-sniff step must capture XHR/fetch requests from an SPA that hides its API behind client rendering (`feature-requests/FR-784-playwright-network-sniff-utility.md:8-10`). The parent plan confirms the same trigger and bounds browser sniffing as an expensive last resort only when static analysis reports `api_found == false AND is_spa == true` (`docs/adaptive-probing-plan.md:113-119`).

The proposed surface is appropriately narrow: one deterministic side-effect utility plus one shell tool manifest under `examples/api-discovery/tools/` (`feature-requests/FR-784-playwright-network-sniff-utility.md:16-18`, `docs/adaptive-probing-plan.md:173-184`). That matches the plan's layer split where probe actions are shell/python tool manifests and investigation judgment stays in step graphs (`docs/adaptive-probing-plan.md:63-70`).

The solution aligns with existing manifest infrastructure rather than inventing a new runtime. FR-768 already defines `runtime.type: shell` manifests with `command`, optional `parse`, and optional `timeout` (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:94-95`), and the enforced judgement froze manifest support as translation over existing runtimes, not a new execution engine (`feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md:43-46`, `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md:73-78`).

Strategic classification: **Contrib/example**. The utility has one named direct consumer today, FR-789, and lives inside the API-discovery example family. It is not a framework primitive; the framework primitive is already FR-768's manifest layer.

## Required revisions

### R-1: Replace the ambiguous JSON array with an explicit output schema

Revise the FR so `network-sniff.js` emits one stable JSON object, not a bare array: `{ "requests": CapturedRequest[], "auth_required": bool, "needs_manual_reason": "auth_token" | "captcha" | null, "warnings": string[] }`. Define `CapturedRequest` fields as `url`, `method`, `status`, `content_type`, `body_preview`, and optional `classification: "data" | "telemetry" | "other"`. This reconciles the FR's current "JSON array" contract (`feature-requests/FR-784-playwright-network-sniff-utility.md:35-38`, `feature-requests/FR-784-playwright-network-sniff-utility.md:72-78`) with FR-789's consumer schema requiring `auth_required` and `needs_manual` behavior (`feature-requests/FR-789-api-discovery-browser-sniff-step.md:41-45`).

### R-2: Make the test witness deterministic and local

Replace "known SPA URL" with a committed local fixture or test harness that serves an HTML page performing one data fetch and one telemetry fetch. The acceptance test must run against that local fixture, assert at least one XHR/fetch capture, assert telemetry exclusion, and assert timeout behavior. The current AC-02 depends on an unnamed external SPA (`feature-requests/FR-784-playwright-network-sniff-utility.md:72-73`), which is not mechanically checkable and violates the doctrine that code demonstrated only against unstated conditions is not trusted (`.github/copilot-instructions.md:208-220`).

### R-3: Pin and document the Playwright runtime contract

Add an explicit dependency/setup deliverable for the example tool: a pinned Node package manifest and lockfile under `examples/api-discovery/tools/` or another named committed package boundary, plus the exact browser-install command needed for Chromium. `node network-sniff.js` cannot rely on ambient global Playwright installation while the FR only says Node is "assumed available" and Playwright is a one-time setup (`feature-requests/FR-784-playwright-network-sniff-utility.md:64-68`). If Chromium or the Playwright package is missing, the utility must fail with a clear non-zero diagnostic rather than silently returning an empty successful result.

### R-4: Specify filter and redaction policy

Define the exact data-carrying filter and analytics exclusion policy: eligible resource types, accepted content types, hostname/path denylist for telemetry, and preview length. Also require redaction of token-like query parameters, headers, and body-preview fragments before output. The FR currently says "exclude known analytics domains" and "auth tokens / CAPTCHA detected -> flagged" (`feature-requests/FR-784-playwright-network-sniff-utility.md:47-49`, `feature-requests/FR-784-playwright-network-sniff-utility.md:77-78`) but does not say which domains, what counts as data, or whether token values may be emitted. Since external page data enters at this boundary, normalization and redaction belong here (`.github/copilot-instructions.md:49-52`, `.github/copilot-instructions.md:216-218`).

### R-5: Make the shell manifest mechanically compliant with FR-768

Revise the manifest example and acceptance criteria to require `runtime.type: shell`, `runtime.command` pointing at `examples/api-discovery/tools/network-sniff.js`, `runtime.parse: json`, and a runtime timeout at least as strict as the script timeout. The current sketch omits `parse: json` and leaves validation as "passes lint when referenced" without naming the referencing fixture (`feature-requests/FR-784-playwright-network-sniff-utility.md:54-62`, `feature-requests/FR-784-playwright-network-sniff-utility.md:77-78`). FR-768 requires manifest validation at graph load and fail-closed behavior (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:103-106`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/api-discovery/tools/network-sniff.js` |
| D-2 | `examples/api-discovery/tools/network_sniff.tool.yaml` |
| D-3 | Pinned Node/Playwright package boundary and lockfile for the example tool, if Playwright is not already pinned in a committed package boundary |
| D-4 | Local deterministic SPA fixture or test harness proving capture, filtering, timeout, and redaction |
| D-5 | Tests for the utility and manifest contract, tagged per requirement doctrine if Python/pytest tests are added |
| D-6 | Minimal usage/setup note only if needed to run the example tool reproducibly |

Not authorized: FR-789 browser-sniff graph, `steps/browser-sniff/graph.yaml`, prompt files, the FR-791 orchestrator, other API-discovery step graphs, core YAMLGraph runtime changes, new manifest schema changes beyond consuming FR-768, Python dependencies, CAPTCHA solving, credentialed browsing, proxy infrastructure, persistent request-body capture beyond bounded previews, or any attempt to bypass authentication. Any material `graph.yaml` or `prompts/*.yaml` work belongs to the graph-authoring route and is outside this FR (`.github/copilot-instructions.md:15-16`).

## Revised acceptance criteria

- [ ] AC-01: `examples/api-discovery/tools/network-sniff.js` exists and accepts `URL` plus `--timeout <ms>`.
- [ ] AC-02: The Playwright/Chromium dependency setup is pinned in a committed package boundary or explicitly documented with an exact reproducible install command; missing package/browser produces a clear non-zero error.
- [ ] AC-03: Running the utility against the committed local SPA fixture captures at least one XHR/fetch data request.
- [ ] AC-04: Output is valid JSON object with `requests`, `auth_required`, `needs_manual_reason`, and `warnings`; each request includes `url`, `method`, `status`, `content_type`, and `body_preview`.
- [ ] AC-05: Request capture is limited to the declared resource types and content types, including JSON and XML data responses.
- [ ] AC-06: The committed fixture proves analytics/telemetry requests are excluded or classified behind data requests according to the declared denylist/ranking policy.
- [ ] AC-07: The hard timeout bounds browser launch, page navigation, and response-body reads; the timeout path exits cleanly with valid JSON and a warning.
- [ ] AC-08: Auth-token and CAPTCHA indicators set `auth_required`/`needs_manual_reason` without treating the run as a tool failure.
- [ ] AC-09: Token-like values in URLs, headers, and body previews are redacted in output while preserving enough evidence to diagnose the auth requirement.
- [ ] AC-10: `examples/api-discovery/tools/network_sniff.tool.yaml` uses the FR-768 shell manifest schema with `parse: json` and a runtime timeout, and validates when referenced by a minimal graph or manifest fixture.
- [ ] AC-11: The change does not create or materially modify graph or prompt artifacts; FR-789 owns the browser-sniff graph.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1 through R-5 are folded into the FR. | GATE |
| C-2 | Tests must not depend on a public website, live government portal, CAPTCHA service, or ambient network timing. | GATE |
| C-3 | The implementation must not rely on globally installed Playwright packages or browser binaries without a committed setup contract. | GATE |
| C-4 | Captured auth material must be detected and redacted; emitting raw tokens, cookies, authorization headers, or credential-bearing query values is forbidden. | GATE |
| C-5 | The utility may observe network traffic from the supplied page only; CAPTCHA solving, login automation, credential storage, and auth bypass are out of scope. | GATE |
| C-6 | The manifest must consume FR-768's existing shell runtime semantics; no core YAMLGraph manifest/runtime changes are authorized. | GATE |
| C-7 | No graph or prompt artifact may be authored under this FR. If enforcement touches governed graph artifacts, it must stop and re-enter through the graph-authoring route. | GATE |

Authority granted: after the required revisions are folded into the FR, the enforcer may build the example-level Playwright network sniff utility and its FR-768 shell manifest under `examples/api-discovery/tools/` with deterministic local tests, timeout enforcement, telemetry filtering, and auth redaction.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
