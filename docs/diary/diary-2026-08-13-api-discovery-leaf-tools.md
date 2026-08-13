# Diary: 2026-08-13 — API Discovery Leaf Tools (FR-783)

## Context

Built the foundation layer for the API discovery pipeline: four shared
tool manifests that step graphs (FR-785..FR-790) will consume.

## Trap: Shell Format Brace Collision (R-1)

The original plan had `curl_probe` as a shell manifest with curl's `-w`
format string: `%{http_code}`, `%{redirect_url}`, etc. These literal
braces collide with Python's `str.format(**safe_vars)` substitution in
`yamlgraph/tools/shell.py:109-115`. The shell runtime would try to
interpret `{http_code}` as a variable, fail, and crash before curl runs.

**Cure:** Python wrapper manifest. The callable handles curl invocation
via `subprocess.run` with `shlex.quote()`, assembles the JSON result
internally, and returns a clean dict. The format braces never hit the
shell runtime's substitution layer. This is `normalize_at_boundary`
applied: the brace semantics conflict exists at the manifest-to-runtime
translation boundary, so fix it there — don't try to escape braces
through multiple layers.

## Trap: Optional Parameter Illusion (R-2)

FR-768 `ShellRuntime` has `command`, `parse`, `timeout` — no parameter
schema, no defaults for tool arguments. Writing `{timeout}` in a shell
command means the caller *must* pass it. The original FR claimed
"optional, default 10" — that's the shell runtime pretending to have
features it doesn't. The fix: all parameters required in the callable
contract. If a step graph wants a default timeout, it passes `"10"`
explicitly in its `tool_call` args.

## Insight: Two Runtimes, One Manifest Primitive

`curl_probe` as Python and `fetch_page` as shell — same FR-768 manifest
primitive, different runtimes. The manifest is a declaration layer that
translates to existing runtimes; choosing the runtime is a per-tool
decision based on what the command's syntax demands. The judge caught
this correctly: the manifest schema doesn't change, only the runtime
binding does.

## Seed

The `curl_probe` two-pass approach (metadata pass + body pass) doubles
the HTTP requests. For the API discovery use case this is acceptable
(probing is cheap, insight is expensive), but a production probe tool
might want a single-pass Python implementation using `urllib` or
`httpx` directly instead of shelling out to curl. When does the
"shell tool wrapping a CLI" pattern become worse than a native Python
implementation? The answer probably lives at the error-handling
boundary: curl gives you status codes and redirects for free; Python
gives you exception handling and streaming for free.
