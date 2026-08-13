# Judgement: FR-783 API Discovery Leaf Tool Manifests

**Verdict:** APPROVED WITH REVISIONS — the example-scoped leaf-tool library is a valid prerequisite for the API discovery step graphs, but authority activates only after the FR fixes the shell command contracts, removes unsupported optional/default parameter claims, and makes tests/smoke evidence deterministic.

**Reviewed against:** `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `docs/adaptive-probing-plan.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.md`; `feature-requests/FR-768-tool-manifest-declaration-reuse.judgement.md`; `feature-requests/FR-773-shared-document-splitter-manifest.md`; `feature-requests/FR-773-shared-document-splitter-manifest.judgement.md`; `feature-requests/FR-785-api-discovery-endpoint-probe-step.md`; `feature-requests/FR-786-api-discovery-page-analysis-step.md`; `feature-requests/FR-787-api-discovery-recon-step.md`; `feature-requests/FR-788-api-discovery-platform-confirm-step.md`; `feature-requests/FR-790-api-discovery-schema-extract-step.md`; `examples/demos/shared-vision-tool/graph.yaml`; `examples/demos/shared-vision-tool/README.md`; `examples/demos/shared-vision-tool/demo-output.log`; `examples/shared/describe_image.tool.yaml`; `yamlgraph/tools/manifest.py`; `yamlgraph/tools/shell.py`; `yamlgraph/node_factory/tool_nodes.py`; `yamlgraph/tools/python_tool.py`; `reference/graph-yaml.md`.

## What is sound

The FR names a concrete first consumer and event: FR-785 endpoint-probe needs `curl_probe` before it can declare the step graph (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:8-10`). The parent plan independently confirms the same leaf library shape under `examples/api-discovery/tools/` and assigns the four proposed manifests to FR-783 (`docs/adaptive-probing-plan.md:173-185`). The dependent step FRs consume those exact tools: endpoint-probe and platform-confirm use `curl_probe` (`feature-requests/FR-785-api-discovery-endpoint-probe-step.md:46-50`; `feature-requests/FR-788-api-discovery-platform-confirm-step.md:42-53`), page-analysis uses `fetch_page` (`feature-requests/FR-786-api-discovery-page-analysis-step.md:41-47`), recon uses `gh_code_search` (`feature-requests/FR-787-api-discovery-recon-step.md:41-46`), and schema-extract uses `parse_openapi` (`feature-requests/FR-790-api-discovery-schema-extract-step.md:42-51`).

The direction aligns with FR-768: manifests are declaration reuse over existing shell/python runtimes, not a new execution engine (`feature-requests/FR-768-tool-manifest-declaration-reuse.md:16-20`; `yamlgraph/tools/manifest.py:1-10`). The shared-vision demo proves the intended consumption precedent: a graph references `manifest: ../../shared/describe_image.tool.yaml` and invokes it through `type: tool_call` inline args (`examples/demos/shared-vision-tool/graph.yaml:9-22`), with recorded successful execution (`examples/demos/shared-vision-tool/demo-output.log:14-18`).

Strategic classification: **Contrib/example**. FR-768 already supplied the framework primitive, including typed manifest validation and translation (`yamlgraph/tools/manifest.py:63-80`, `yamlgraph/tools/manifest.py:114-180`; `reference/graph-yaml.md:1424-1474`). FR-783 is a reusable example library for one API discovery family with multiple immediate consumers, not a core framework extension.

## Required revisions

### R-1: Replace the `curl_probe` sketch with a format-safe command contract

Fold an exact, tested `curl_probe.tool.yaml` contract into the FR. The current command contains curl write-out braces and JSON braces (`%{http_code}`, `%{redirect_url}`, `%{content_type}`, and `{...}`) inside a runtime that performs Python `str.format(**safe_vars)` substitution (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:42-46`; `yamlgraph/tools/shell.py:109-115`). Literal braces must be escaped for Python format, or the command must be moved behind a Python wrapper; leaving the sketch as-is will fail before curl runs.

The revised contract must also actually emit the claimed body head. The current sketch writes the response body to `/tmp/curl_body` but never reads it back into stdout, while the FR promises structured JSON plus the first 2KB of body (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:44-46`). Do not use a fixed `/tmp/curl_body` path; use a per-invocation temporary file with cleanup or a Python wrapper. The accepted output shape is `{"status": int, "redirect": str, "content_type": str, "body_head": str}`.

### R-2: Remove unsupported optional/default parameter claims from shell manifests

Revise `curl_probe` and `fetch_page` so every placeholder in each shell command is a required tool-call argument, or implement defaults inside an authorized Python wrapper. FR-768 manifests do not define parameter schemas or defaults: shell runtimes expose only `command`, `parse`, and `timeout` (`yamlgraph/tools/manifest.py:22-31`; `reference/graph-yaml.md:1456-1464`). If `{user_agent}` or `{timeout}` appears in a shell command, omitting it produces a missing-variable failure at command formatting time (`yamlgraph/tools/shell.py:109-116`), not a default.

Also remove extra shell quotes around placeholders. Runtime variables are already sanitized with `shlex.quote()` (`yamlgraph/tools/shell.py:68-88`; `reference/graph-yaml.md:1333-1335`), so command templates must use forms like `-A {user_agent}` rather than `-A '{user_agent}'` (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:49-52`).

### R-3: Specify manifest YAML shape, parse modes, and implementation files

Add concrete manifest snippets or a per-tool field table that states `name`, `description`, `runtime.type`, runtime binding, `parse`, and `timeout` for all four tools. `curl_probe` and `gh_code_search` claim JSON returns and therefore must declare `runtime.parse: json`; `fetch_page` returns text and must declare text parsing (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:42-60`; `yamlgraph/tools/shell.py:157-170`). `parse_openapi` must name its Python implementation surface, e.g. `examples/api-discovery/tools/parse_openapi.py` plus `function: parse_openapi`, because `runtime.type: python` requires exactly one of `path` or `module` and a function (`yamlgraph/tools/manifest.py:33-49`; `reference/graph-yaml.md:1460-1461`).

### R-4: Freeze the `parse_openapi` callable and error contract

Define the Python callable as a `tool_call`-compatible kwargs function, not a state-dict node. `type: tool_call` invokes registered tools with `tool_func(**args)` and wraps success/error in the result envelope (`yamlgraph/node_factory/tool_nodes.py:89-114`), while state-dict functions are the Python node contract (`reference/graph-yaml.md:1395-1407`). Fold this exact contract into the FR: `parse_openapi(spec_json: str | dict) -> dict` returns `{"endpoints": [{"method": str, "path": str, "description": str, "parameters": list}], "info": {"title": str | None, "version": str | None}}`; invalid JSON, non-object specs, and missing/invalid `paths` raise `ValueError` naming the defect.

### R-5: Make automated validation independent of external network and auth

Replace acceptance criteria that require live unauthenticated internet or `gh` auth as mandatory proof with deterministic local tests plus explicitly gated optional live smoke. `gh_code_search` may document that live execution requires an authenticated `gh` CLI (`feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:56-60`, `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md:77-78`), but CI-grade acceptance must be mechanically checkable without GitHub credentials: manifest validation, command shape, parse mode, and an integration smoke that skips only when the documented auth precondition is absent. `curl_probe` and `fetch_page` runtime behavior must be tested against a local HTTP fixture/server, not an external public endpoint.

### R-6: Route any committed smoke graph through graph authoring

If the smoke-test graph in AC-07 is committed under `examples/api-discovery/`, it is a governed `graph.yaml` artifact and must be authored through `scripts/author.sh` with `tmp/draft-authoring-report.md` evidence. Repo doctrine makes the graph-authoring route mandatory for new or materially modified `graph.yaml` and prompt artifacts (`.github/copilot-instructions.md:15`), and the parent plan repeats that every graph goes through that route (`docs/adaptive-probing-plan.md:217`). If enforcement instead uses a temporary test fixture graph under `tests/fixtures/`, the FR must say so explicitly and must not claim it as an example/demo artifact.

### R-7: Add traceability and demo-gate artifacts to the scope

Add a capability/requirement entry for the API discovery leaf tool library, or name an existing requirement that governs these exact artifacts, before tests are written. Repo doctrine requires every test to carry a concrete `@pytest.mark.req("REQ-YG-XXX")` and new capabilities to add a capability YAML file (`.github/copilot-instructions.md:173-176`). Because this is a feature/example change under `examples/`, the FR must also include a changelog fragment and diary reflection, and if a demo graph under `examples/demos/` is introduced, a committed `demo-output.log` is required by repo gates (`CLAUDE.md:408-411`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md` revised to fold R-1 through R-7 before enforcement authority activates |
| D-2 | `examples/api-discovery/tools/curl_probe.tool.yaml` as a shell manifest or an explicitly authorized Python-wrapper manifest, producing status/redirect/content_type/body_head JSON |
| D-3 | `examples/api-discovery/tools/fetch_page.tool.yaml` as a shell manifest returning page source with required `url` and `user_agent` args |
| D-4 | `examples/api-discovery/tools/gh_code_search.tool.yaml` as a shell manifest returning parsed JSON search results when `gh` auth is available |
| D-5 | `examples/api-discovery/tools/parse_openapi.tool.yaml` plus the minimal Python implementation file for deterministic OpenAPI JSON parsing |
| D-6 | Tests/artifact checks for manifest validation, shell command formatting, local `curl_probe`/`fetch_page` execution, `parse_openapi` success/failure behavior, and gated `gh_code_search` behavior |
| D-7 | One smoke graph only if routed through graph authoring, or a clearly test-only fixture graph if not committed as an example artifact |
| D-8 | Capability/requirement traceability, changelog fragment, and diary reflection |

Not authorized: changes to `yamlgraph/` manifest schema, shell executor, `tool_call` dispatch, graph loader, linter, CI/hooks, judge/review doctrine, graph-runtime step graphs FR-785 through FR-790, the FR-784 network-sniff tool, the FR-791 orchestrator, browser automation, platform catalogs, remote registries, dependency installation, or a generic parameter/default schema for tool manifests. The four leaf tools must remain deterministic side-effect declarations/implementations over existing FR-768 runtimes.

## Revised acceptance criteria

- [ ] AC-01: Four manifest files exist under `examples/api-discovery/tools/`: `curl_probe.tool.yaml`, `fetch_page.tool.yaml`, `gh_code_search.tool.yaml`, and `parse_openapi.tool.yaml`.
- [ ] AC-02: Each manifest validates as an FR-768 `ToolManifest`; each `name` matches its graph-local tool key; no manifest entry requires a manifest-schema or runtime change.
- [ ] AC-03: `curl_probe` has a format-safe command or Python wrapper, uses no fixed temp path, and returns parsed JSON with `status`, `redirect`, `content_type`, and `body_head` capped at 2048 characters.
- [ ] AC-04: `fetch_page` returns full page source as text and accepts required `url` and `user_agent` arguments without wrapping sanitized placeholders in extra shell quotes.
- [ ] AC-05: `gh_code_search` declares JSON parsing and has deterministic tests for manifest/command shape; live execution is documented and gated on authenticated `gh` CLI availability.
- [ ] AC-06: `parse_openapi(spec_json: str | dict) -> dict` returns endpoint inventory and info for a valid OpenAPI JSON fixture, and raises `ValueError` for invalid JSON, non-object specs, and missing/invalid `paths`.
- [ ] AC-07: Automated tests execute `curl_probe` and `fetch_page` against a local HTTP fixture/server and prove output shape/content without external network dependency.
- [ ] AC-08: A graph or fixture consuming at least `curl_probe` via `manifest:` loads successfully; if committed as an example `graph.yaml`, it is authored through `scripts/author.sh` and its validation evidence is recorded.
- [ ] AC-09: Every new or changed test is marked with the governing `REQ-YG-XXX`; the capability/requirement entry for the API discovery leaf tools exists or the FR names the exact existing governing requirement.
- [ ] AC-10: A changelog fragment and diary reflection are added; any committed demo under `examples/demos/` includes `demo-output.log`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-7 are folded into `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`. | GATE |
| C-2 | Shell commands must survive `str.format(**safe_vars)` before execution; literal JSON/curl braces must be escaped or hidden behind a Python wrapper. | GATE |
| C-3 | Runtime argument defaults must not be claimed for shell manifests unless implemented without changing FR-768 manifest schema. | GATE |
| C-4 | Required automated validation must not depend on external public endpoints or authenticated GitHub access; live `gh_code_search` smoke may be optional/gated only. | GATE |
| C-5 | Any committed graph/prompt artifact must use the graph-authoring route; unsentineled manual graph authoring is not permitted. | GATE |
| C-6 | No core runtime, manifest schema, graph loader, tool-call dispatch, CI/hook, or doctrine changes may be made under this FR. | GATE |
| C-7 | Downstream step graphs FR-785..FR-790 and orchestrator FR-791 remain out of scope; they may consume these manifests only in their own judged FRs. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may add the four API discovery leaf tool manifests, the minimal `parse_openapi` implementation, deterministic tests/fixtures, and directly required traceability/changelog/diary artifacts, and nothing else.

**Prior art:** FR-783..FR-792 are sibling sub-FRs of the same API discovery pipeline (docs/adaptive-probing-plan.md §6). Each addresses a distinct step; no overlap in scope.
