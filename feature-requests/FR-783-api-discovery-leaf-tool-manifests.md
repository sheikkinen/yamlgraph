# Feature Request: FR-783 — API Discovery Leaf Tool Manifests

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced 2026-08-13 — AC-01..AC-10 delivered; 17/17 tests green (REQ-YG-585, CAP-224)
**Effort:** 0.5 days
**Requested:** 2026-08-13
**First consumer / first event:** FR-785 endpoint-probe step graph,
the first time it needs `curl_probe` to test a URL — that tool must
exist as a shared manifest before the step graph can declare it.

**Parent plan:** `docs/adaptive-probing-plan.md` §5

## Summary

Create the shared shell/python tool manifests that the API discovery
step graphs consume: `curl_probe`, `fetch_page`, `gh_code_search`, and
`parse_openapi`. Each is an FR-768 `*.tool.yaml` manifest under
`examples/api-discovery/tools/`.

## Value Statement

Step graphs (FR-785..FR-790) get their leaf side effects as shared,
validated, reusable tool declarations — no inline duplication, no
per-graph copy-paste of curl commands.

## Problem

The API discovery pipeline needs deterministic probe actions (HTTP
requests, code search, spec parsing). Without shared manifests, each
step graph would duplicate the same tool declarations inline — the
exact 26-duplicate problem FR-768 was built to solve.

## Ideal Result

Four `*.tool.yaml` files exist under `examples/api-discovery/tools/`,
each loadable by any graph via `manifest:` reference, each validated
at graph load time, each producing the output shape its consumers expect.

## Proposed Solution

### `curl_probe.tool.yaml` (python — R-1, R-2)

Python wrapper manifest — shell `curl -w` format braces conflict with
Python `str.format()` substitution in the shell runtime (R-1). A Python
callable sidesteps the escaping problem and handles body capture + JSON
assembly without temp files.

```yaml
name: curl_probe
description: "Probe a URL: returns {status, redirect, content_type, body_head}"
runtime:
  type: python
  path: curl_probe.py
  function: curl_probe
```

Callable contract: `curl_probe(url: str, user_agent: str, timeout: str) -> dict`
— all parameters required (R-2: no optional/default claims in manifests).
Returns `{"status": int, "redirect": str, "content_type": str, "body_head": str}`
where `body_head` is capped at 2048 characters. Uses `subprocess.run`
with `shlex.quote()` for URL sanitization.

### `fetch_page.tool.yaml` (shell — R-2)

```yaml
name: fetch_page
description: "Fetch full page source with custom User-Agent"
runtime:
  type: shell
  command: "curl -sL -A {user_agent} {url}"
  parse: text
  timeout: 30
```

Both `url` and `user_agent` are required arguments — no optional/default
claims (R-2). No extra quotes around placeholders — `shlex.quote()`
handles sanitization at the runtime level (R-2).

### `gh_code_search.tool.yaml` (shell — R-3)

```yaml
name: gh_code_search
description: "Search GitHub code repositories, returns JSON results"
runtime:
  type: shell
  command: "gh search code {query} --limit 20 --json path,repository,textMatches"
  parse: json
  timeout: 30
```

`query` is the sole required argument. `parse: json` declared (R-3).
Live execution requires authenticated `gh` CLI; tests validate manifest
shape and command format deterministically without GitHub credentials (R-5).

### `parse_openapi.tool.yaml` (python — R-3, R-4)

```yaml
name: parse_openapi
description: "Parse an OpenAPI/Swagger JSON spec into an endpoint inventory"
runtime:
  type: python
  path: parse_openapi.py
  function: parse_openapi
```

Callable contract (R-4): `parse_openapi(spec_json: str | dict) -> dict`
— `tool_call`-compatible kwargs function, not a state-dict node.

Returns:
```json
{
  "endpoints": [{"method": "GET", "path": "/pets", "description": "...", "parameters": [...]}],
  "info": {"title": "Petstore", "version": "1.0.0"}
}
```

Error contract: raises `ValueError` for invalid JSON strings, non-object
specs, and missing/invalid `paths` key — names the defect in the message.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: Four manifest files exist under `examples/api-discovery/tools/`: `curl_probe.tool.yaml`, `fetch_page.tool.yaml`, `gh_code_search.tool.yaml`, `parse_openapi.tool.yaml`
- [ ] AC-02: Each manifest validates as FR-768 `ToolManifest`; each `name` matches its graph-local tool key; no manifest-schema or runtime changes required
- [ ] AC-03: `curl_probe` Python wrapper returns parsed JSON with `status` (int), `redirect` (str), `content_type` (str), and `body_head` (str capped at 2048 chars); no fixed temp path
- [ ] AC-04: `fetch_page` returns full page source as text; accepts required `url` and `user_agent` without extra shell quotes on sanitized placeholders
- [ ] AC-05: `gh_code_search` declares `parse: json`; deterministic tests validate manifest/command shape; live execution documented and gated on `gh` CLI auth
- [ ] AC-06: `parse_openapi(spec_json: str | dict) -> dict` returns endpoint inventory for valid OpenAPI fixture; raises `ValueError` for invalid JSON, non-object specs, missing/invalid `paths`
- [ ] AC-07: Automated tests execute `curl_probe` and `fetch_page` against a local HTTP fixture/server and prove output shape/content without external network dependency (R-5)
- [ ] AC-08: Test fixture graph under `tests/fixtures/` consuming `curl_probe` via `manifest:` loads successfully (R-6: not committed as example artifact, so no graph-authoring route needed)
- [ ] AC-09: Tests marked with `@pytest.mark.req("REQ-YG-585")`; capability `CAP-224` exists (R-7)
- [ ] AC-10: Changelog fragment and diary reflection added (R-7)

## Alternatives Considered

- **Shell manifest for curl_probe:** curl `-w` format braces conflict with Python `str.format()` in the shell runtime; a wrapper script or escaped braces would be fragile (R-1)
- **Optional parameters with defaults:** FR-768 shell manifests don't support parameter schemas or defaults; all placeholders must be required arguments (R-2)

## Related

- FR-768 (tool manifests — the primitive these consume)
- FR-773 (feeder pattern — the architectural precedent)
- `docs/adaptive-probing-plan.md` (parent plan)
- `examples/demos/shared-vision-tool/` (manifest consumption precedent)
- CAP-224 / REQ-YG-585 (traceability)

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
