# Research: Safe Mobile/Web Access for Creating and Running YAMLGraphs — Landscape 2026-07

**Date:** 2026-07-28
**Status:** Research note (no FR attached; seeds at the end)
**Method:** Internal inventory of repo surfaces (FRs, `yamlgraph/export/mcp.py`,
`yamlgraph/a2a/server.py`, `examples/openai_proxy/`) + external research agent
sweep of primary sources fetched 2026-07-28 — GitHub docs (workflow_dispatch,
Copilot cloud agent), Claude Code GitHub Actions docs, MCP spec 2025-06-18,
Anthropic Integrations blog, Tailscale/Cloudflare/ngrok docs, Modal/E2B docs.

## Question

How can a developer safely **create** and **run** YAMLGraph pipelines from a
phone or browser, given that running a graph = LLM calls + potentially
shell/python tools = remote code execution?

## Answer in one paragraph

Keep create and run **asymmetric**, and keep **execution local**. *Create*
goes through the existing review boundary (GitHub Issue → chaplain FR → PR),
already mobile-native via the `chaplain` label (FR-243/FR-251). *Run* is
limited to graphs already committed to the repo, triggered from the phone
via GitHub-native channels (issue labels, comments) but **executed by the
local watcher daemon on the trusted machine** — where the `copilot` node
(FR-081) provides LLM execution under the Copilot subscription. GitHub here
is the authenticated message queue, not the execution environment. For
direct remote access to the local MCP/A2A servers, Cloudflare Tunnel +
Access (deny-by-default Zero Trust, outbound-only tunnel) is the correct
upgrade path; no OAuth code needs writing. Collapsing create and run into
one unauthenticated web session is exactly the surface the FR-070 rejection
guards against.

## Constraints (non-negotiable)

- **Local execution required (contractual).** Graph execution must run on
  the trusted local machine via the `copilot` node type (FR-081, Copilot
  CLI under the maintainer's subscription) — not via provider API keys
  stored as CI secrets on GitHub-hosted runners. This excludes
  runner-executed options (`workflow_dispatch` jobs, `claude-code-action`,
  Copilot cloud agent) as *execution* environments; they remain valid as
  *trigger/authoring* channels only. GitHub's role is authenticated
  message transport; the chaplain watcher pattern (poll → execute locally)
  already embodies this split.
- **FR-070 web playground is REJECTED precedent** — "No UI, ever. Text is the
  interface. Agents read YAML, agents write YAML. Visual tools create a human
  dependency that YAML eliminates." Any proposal re-entering this territory
  must distinguish itself or die by the same rationale (FR-737 graveyard rule).
- None of the recommended architectures below introduce a UI: the interfaces
  are GitHub issues/comments (text) and MCP JSON-RPC (text). The doctrine is
  satisfied, not skirted.

## Internal inventory: what exists today

| Surface | Location | Remote-safety state |
|---|---|---|
| GitHub Issues remote inbox | FR-243, hardened FR-251 | ✅ The sanctioned mobile CREATE channel: `chaplain` label → watcher import → Plan → Judge → Enforce. Author allowlist (`.chaplain/allowed-authors.txt`), 10 KB body cap, `<!-- author -->` audit header |
| MCP server | `yamlgraph/export/mcp.py` | stdio-only transport — no HTTP, no remote exposure (by design) |
| A2A server | `yamlgraph/a2a/server.py` | binds `localhost`; **no auth layer** |
| openai_proxy example | `examples/openai_proxy/api/app.py` | Only surface with real web auth: `HTTPBearer` vs `WEB_API_KEY`, deployed on Fly.io — proven pattern for exposing one graph over HTTPS |
| workflow_dispatch | `.github/workflows/daily-digest.yml` | Typed-input manual trigger already in production; renders as a form in GitHub Mobile |
| Voice intake | FR-360 | Phone call → `gh issue create --label chaplain` → chaplain pipeline |
| WebLLM browser demo | FR-731/735/736 | Browser-side prompt *execution* with zero server (static GitHub Pages) — a RUN surface with zero attack surface, limited to single prompts |
| Execution-side constraints | `tools/shell.py`, conditions parser | `shlex.quote()` on all runtime vars; no `eval()`; only YAML config is trusted |

## External landscape (2025–2026)

### GitHub-native mobile channels

- **`workflow_dispatch` from GitHub Mobile** — "Run workflow" form in the
  Actions tab; each typed input becomes a field. Auth: repo write permission.
  Risk: `inputs.*` interpolated into shell is attacker-controlled — use
  `type: choice` enums for graph names and validate vars in the step.
  Effort ~0.5–1 day.
- **Issue label channel** — extend the chaplain watcher with a `run-graph`
  label branch, or trigger a workflow on `issues.labeled`. Same allowlist
  gate as FR-251. Only users with triage permission can add labels.
- **`@claude` mention** (`anthropics/claude-code-action@v1`) — comment
  `@claude run graphs/x.yaml with topic=AI` from GitHub Mobile; Claude runs
  on GitHub runners with `--allowedTools` and `--max-turns` caps. Only
  collaborators can trigger. No local execution surface at all. Best
  CREATE+RUN option: describe the graph in English → agent writes YAML →
  PR review before it ever runs. Effort ~1–2 h.
- **Copilot cloud agent** — assign an issue to `@copilot` from mobile;
  runs on GitHub Actions ephemeral VMs; best at *creating* new graph YAML
  (code generation), indirect at running.
- **`gh` CLI on phone** (Termux/a-Shell) — works; scope the PAT to
  `actions:write` only. Developer-only ergonomics.
- **Codespaces from mobile browser** — functional but awkward; full VS Code
  + terminal + repo secrets in an isolated VM (~$0.18/h).

### Chat-platform bridges

Telegram/Slack bots as command surfaces are viable but add a bot-token
attack surface and require a public HTTPS webhook (→ tunneling). Standard
hardening: numeric user-ID allowlists, HMAC signature verification
(Slack `X-Slack-Signature` with 5-min timestamp window; Telegram secret
token header), server-side command parsing (never raw text to shell).
Known failure mode: leaked bot token = anyone can invoke. GitHub-native
channels dominate on effort and auth inheritance; Slack/Teams already
integrate natively with Copilot cloud agent if a chat surface is wanted.

### Tunneling a local FastAPI/MCP/A2A server

| | Tailscale Serve | Tailscale Funnel | Cloudflare Tunnel + Access | ngrok + OAuth |
|---|---|---|---|---|
| Auth | tailnet identity (WireGuard) | none — app-layer only | Zero Trust IdP, deny-by-default | OAuth Traffic Policy |
| Public? | No (tailnet only) | Yes | Yes | Yes |
| Stable URL | MagicDNS | `{device}.ts.net` | your domain | paid only |
| Setup | 30 min | 30 min (beta) | 1–2 h (free: 50 users) | 30 min |
| Best for | personal dev/MCP in tailnet | avoid (beta, no auth) | production solo-maintainer | quick demos |

Cloudflare Tunnel is outbound-only (no ports opened); an Access policy of
"allow only my email / GitHub login" makes the MCP server auth-free behind
an authenticated edge. This is also the right upgrade path for the
localhost-only A2A server.

### MCP-over-HTTP remote access

- MCP spec 2025-06-18: Streamable HTTP transport; servers MUST validate
  `Origin` (DNS rebinding), SHOULD bind `127.0.0.1` locally, SHOULD
  implement OAuth 2.1 (PKCE mandatory, RFC7591 DCR recommended).
- Implementing OAuth 2.1 in `yamlgraph/export/mcp.py` is a multi-day effort;
  the pragmatic route is Cloudflare Access / Tailscale as the auth layer with
  the MCP server unchanged behind it.
- Claude.ai "Integrations" (remote MCP) is live for Max/Team/Enterprise on
  **web and desktop**; mobile-app support unconfirmed as of 2026-07.

### Sandboxing the execution side

- **Modal sandboxes** (`modal.Sandbox.create()`, 5-min default timeout,
  secrets injected not inherited) and **E2B** (100 ms cold-start micro-VMs,
  gVisor isolation) both fit a "run possibly-untrusted graph" model.
- For the solo-maintainer allowlisted case they are over-engineering. YAML
  graphs are declarative (no eval, no arbitrary Python); residual risks are
  (a) **shell tool abuse** and (b) **LLM API spend**. Proportionate native
  mitigation: run `yamlgraph graph run` inside Docker with
  `--no-new-privileges --cap-drop ALL --read-only --memory 512m
  --pids-limit 50`, and **disable the `shell` tool type entirely** for any
  remotely-submitted graph.

## Ranked recommendations (solo maintainer)

### 🥇 #1 — GitHub-native RUN channel (zero new infrastructure)

`workflow_dispatch` workflow with `type: choice` graph enum + validated vars
string, and/or a `run-graph` label branch in the existing watcher. Auth =
GitHub identity + 2FA + FR-251 allowlist. Smallest possible attack surface:
no servers, no tunnels, no ports; graph YAML already committed and reviewed.
Effort 0.5–1 day. Aligns exactly with "text is the interface".

### 🥈 #2 — `@claude` / `@copilot` mentions (best CREATE+RUN)

Issue comment from GitHub Mobile → agent on GitHub runners generates the
YAML → PR → review → merge → runnable via #1. The review cycle between
create and run is a security feature, not friction. Effort 1–2 h setup.
Cost: API tokens per invocation.

### 🥉 #3 — Cloudflare Tunnel + Access → local MCP/A2A server

For direct remote MCP access as client support matures (Claude.ai web today,
mobile eventually). Outbound-only tunnel, single-identity Access policy, no
auth code written. Also the secure endpoint any future chat bot should call
instead of a bare localhost. Effort 1–2 h.

## The asymmetry principle

```
CREATE (mutation)  : phone → GitHub Issue (chaplain label) → FR → Judge → PR → review → merge
RUN    (execution) : phone → workflow_dispatch / run-graph label / @claude → committed graph only
```

Create passes the review boundary; run touches only already-reviewed
artifacts. Any design that lets a mobile session both author and execute an
arbitrary graph in one step reopens the FR-070 surface and must be rejected
on the same rationale.

## Gaps and uncertainties

1. Claude.ai remote MCP on the mobile app: unconfirmed ("web and desktop"
   per announcement); recheck before investing in #3 for mobile.
2. Tailscale Funnel still beta (2026-01) — not for production reliance.
3. ngrok Traffic Policy availability varies by plan tier.
4. `workflow_dispatch` var-string injection: mitigate with choice enums +
   step-level validation; do not interpolate raw inputs into shell.

## Seeds

- **Seed:** Should the chaplain watcher grow a `run-graph` label branch that
  executes committed graphs (Docker-confined, shell tools disabled) and posts
  output as an issue comment — the RUN twin of the FR-243 CREATE channel?
- **Seed:** Should the A2A server refuse to bind non-localhost without an
  auth layer configured — normalizing at the boundary before anyone tunnels
  it by accident?
- **Seed:** Is a `yamlgraph graph run --confined` flag (Docker wrapper,
  shell tool type disabled, resource caps) worth first-classing, so every
  remote channel shares one hardened execution path instead of each
  reinventing confinement?

## Sources

Full research agent report with per-option citations preserved in session
artifacts (`research-safe-remote-access.md`). Primary sources: GitHub docs
(events-that-trigger-workflows, Copilot cloud agent), code.claude.com
GitHub Actions docs, modelcontextprotocol.io spec 2025-06-18 + 2025-03-26
authorization, claude.com/blog/integrations, tailscale.com (funnel, ssh),
developers.cloudflare.com/cloudflare-one, ngrok.com Traffic Policy docs,
modal.com sandboxes, e2b.dev docs. Internal: FR-070, FR-243, FR-251,
FR-360, FR-731, `examples/openai_proxy/`, `yamlgraph/export/mcp.py`,
`yamlgraph/a2a/server.py`, `.github/workflows/daily-digest.yml`.
