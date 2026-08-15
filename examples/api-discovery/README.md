# API Discovery

Automated API discovery pipeline — from hypothesis to structured API profile.

Given a domain and purpose, this example family probes for APIs using a
multi-step investigation pattern: an orchestrator routes between reusable
agent step graphs (each exposed as a graph-runtime tool manifest), which
consume shared leaf tools declared as FR-768 manifests.

## Architecture

```
examples/api-discovery/
├── tools/                          shared leaf tool manifests
│   ├── curl_probe.tool.yaml        HTTP probe (Python wrapper)
│   ├── curl_probe.py               implementation
│   ├── fetch_page.tool.yaml        full page fetch (shell)
│   ├── gh_code_search.tool.yaml    GitHub code search (shell)
│   ├── parse_openapi.tool.yaml     OpenAPI spec parser (Python)
│   ├── parse_openapi.py            implementation
│   ├── network_sniff.tool.yaml     browser XHR/fetch capture (shell)
│   ├── network-sniff.js            implementation (Playwright)
│   ├── package.json                pinned Node deps for network-sniff.js
│   └── package-lock.json           lockfile (FR-784 dependency contract)
└── steps/                          (future: step graphs FR-785..FR-790)
```

## Tools

| Tool | Runtime | Description |
|------|---------|-------------|
| `curl_probe` | python | Probe URL → `{status, redirect, content_type, body_head}` |
| `fetch_page` | shell | Full page source with custom User-Agent |
| `gh_code_search` | shell | GitHub code search (requires `gh` auth) |
| `parse_openapi` | python | OpenAPI JSON → endpoint inventory |
| `network_sniff` | shell | Headless Chromium XHR/fetch capture → JSON inventory (FR-784) |

### network_sniff setup (one-time)

```bash
cd examples/api-discovery/tools
npm ci
npx playwright install chromium
```

Output contract: `{requests, auth_required, needs_manual_reason, warnings}`
with telemetry demoted behind data requests and token values redacted.
Missing package or browser fails loudly with the install command.

## Usage

Reference any tool from a graph via FR-768 manifest:

```yaml
tools:
  curl_probe:
    manifest: ../../api-discovery/tools/curl_probe.tool.yaml
```

## Plan

See `docs/adaptive-probing-plan.md` for the full pipeline design
(FR-783..FR-792).

## Related

- FR-783: Leaf tool manifests (this layer)
- FR-785..FR-790: Step graphs (orchestrated investigation steps)
- FR-791: Orchestrator graph
- FR-768: Tool manifest primitive
