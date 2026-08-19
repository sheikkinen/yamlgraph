# Research: Channels That Reach Agents

**Date:** 2026-08-18
**Origin:** Continuation of
`docs/research-publication-channels-2026-08-18.md`, focused on the
agent-facing half. Framing constraint from the operator: consider the
plan-judge-enforce-review process itself, and the existing GitHub
integration planning.

## The central observation: the pipeline already has an agent-facing door

FR-243 (implemented, April 2026) made GitHub Issues labeled `chaplain` a
remote inbox for Plan→Judge→Enforce. Its own problem statement named the
consumer: *"External CI, bots, or collaborators cannot trigger the
pipeline"*. That FR was written for humans-on-phones, but it accidentally
built the first **agent channel**: any GitHub-capable agent can file an
issue and receive back a judged, enforced, reviewed, merged PR.

This inverts the publication question. The other channels publish
*artifacts* to agents. GitHub publishes the **process**: plan-judge-
enforce-review as a service any agent can invoke with one API call it
already knows how to make. No new protocol, no registry, no SDK — issue
in, governed PR out. Agents live on GitHub today; it is the only channel
where the audience is already inside the building.

## Channel inventory, mapped to pipeline stages

### 1. GitHub — the process channel (strongest, mostly built)

| Pipeline stage | Existing surface | Agent-facing extension | Signal |
|---|---|---|---|
| Plan (inbox) | `chaplain`-labeled issues (FR-243) | document the label as a public API in README/AGENTS.md; accept issues from bot accounts explicitly | issues filed by agent accounts (`gh api` — account type Bot) |
| Judge | judgement artifacts, repo-local | post verdict as issue/PR comment — the judgement becomes visible, citable doctrine | agent reactions/replies to verdicts |
| Enforce | watcher2 PR flow | PRs are already public | external agents reviewing/citing our PRs |
| Review | `scripts/review.sh` verdicts | render as PR review comments (planned in review-pr doctrine) | consumption by GitHub's own agent surfaces |
| Whole pipeline | repo-local scripts | **GitHub App / Action packaging**: run chaplain on *someone else's* repo | installs — the doctrine-as-product signal |

The last row is the growth step the prior planning points at: FR-243 lets
the world into our pipeline; a packaged Action/App puts our pipeline into
the world's repos. GitHub Actions Marketplace is a real distribution
channel with install counts — and its consumers are CI systems, i.e.
agents by construction. The judge alone (FR text in → verdict out) is the
most extractable single stage: stateless, doctrine-driven, no worktree
needed.

### 2. MCP registries — the tool channel (server built, unlisted)

`mcp_server.py` (CAP-19) already exposes graphs as tools; it is registered
nowhere. Registries agents' hosts actually pull from:

- **GitHub MCP Registry** — the official one; highest agent traffic
- Smithery, PulseMCP, mcp.so — aggregators feeding Claude/Cursor configs
- VS Code MCP gallery — Copilot-native discovery
- awesome-mcp-servers lists — crawled by both humans and agents

Caveat from the MCP-pruning observation: list a *curated* server (5–10
fit-for-purpose tools: run_graph, list_graphs, judge, five_whys), not the
100-tool firehose. A registry listing of 100 undifferentiated demo tools
reads as noise to a tool-selecting agent — tool descriptions are the ad
copy; an agent chooses tools by description match.

### 3. A2A directories — the peer channel (server built, uncarded)

The a2a_server (CAP-101/104/105) speaks the protocol agents use to call
agents. Publishing an agent card at a well-known URL and listing in
emerging A2A directories makes yamlgraph agents *callable peers*. Signal:
inbound A2A calls from foreign agents — the single purest thesis witness.
Latency to first signal is unknown (young ecosystem); cost is one hosted
endpoint plus a card.

### 4. Repo-level agent conventions — the drive-by channel (zero infra)

Agents that *land on the repo* (via search, dependents, or a human's
prompt) read specific files:

- **AGENTS.md** at repo root — the emerging cross-vendor convention;
  yamlgraph has rich agent instructions but in `.github/`, invisible to
  non-Copilot agents. One file, pointing into existing docs.
- **llms.txt** — curated entry map for LLM consumers of the docs.
- **README structured for extraction** — agents quote READMEs into
  answers; the first 50 lines are what gets retrieved.

Signal: GitHub traffic API user-agent mix, clone spikes without star
movement (a known agent-crawl signature).

### 5. Package registries — the dependency channel (live, unharvested)

PyPI reaches agents directly: coding agents resolve "build an LLM pipeline
from YAML" to `pip install yamlgraph` only if the package description and
keywords match agent queries. pypistats harvest (first-slice item from the
parent doc) tells us whether that resolution ever happens.

### 6. The training corpus — the slowest, largest channel

Whatever is published permissively and widely *becomes part of the next
model generation*. Documentation on the public web, answered questions,
essays with code samples — this is SEO for model weights. It cannot be
measured directly; its proxy is whether future agents suggest yamlgraph
unprompted. Every human-channel publication (parent doc) doubles as a
deposit here — a reason content channels serve the agent thesis even when
their immediate audience is human.

## Ranked recommendation (extends the parent doc's first slice)

1. **Document the chaplain label as a public agent API** — README section
   plus AGENTS.md. Zero code; FR-243 built the mechanism 4 months ago and
   never proclaimed it. The fastest possible agent bell: it rings the
   first time any bot account files a chaplain issue.
2. **Curated MCP server listing** in the GitHub MCP Registry (5–10 tools,
   descriptions written as ad copy) with invocation logging landed first.
3. **AGENTS.md + llms.txt** — one session of writing, permanent drive-by
   surface.
4. **Judge-as-Action** on the Actions Marketplace — the doctrine's most
   extractable stage as an installable product; this is the cheap test of
   "the doctrine is the product" (unaddressed-opportunities §5) with
   install counts as the verdict.
5. **A2A agent card** — cheap to publish, uncertain ecosystem latency;
   worth doing for the witness value of one inbound call.

## The reflexive point

The chaplain pipeline consumes external proposals and emits merged
capability. If the proposals start arriving *from agents*, the system
closes its own loop: agents proposing features to an agent-governed
pipeline that builds features for agents. Every stage boundary
(inbox, verdict, PR, review) then emits an externally visible artifact —
and the harvest ledger reads the whole funnel. The plan-judge-enforce-
review process is not adjacent to the agent channel question; properly
packaged, it *is* the channel.
