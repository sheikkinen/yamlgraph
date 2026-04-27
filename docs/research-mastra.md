# Research: Mastra.ai vs YAMLGraph

*Date: 2026-04-27*

## What is Mastra?

[Mastra](https://mastra.ai/) is a TypeScript-first agent framework for building AI-powered applications. Backed by a VC-funded company with enterprise customers (Docker, SoftBank, Elastic, PayPal, Plaid, Replit). Open source under Apache 2.0.

Core primitives: Agents, Workflows, RAG, Memory, Tools, MCP, Evals, Guardrails.

Tagline: *"Python trains, TypeScript ships."*

## Comparison

| Dimension | Mastra | YAMLGraph |
|---|---|---|
| **Language** | TypeScript | Python |
| **Philosophy** | Code-first — compose in TS | YAML-first — declare in config |
| **Schema validation** | Zod (runtime TS validation) | Pydantic v2 / inline YAML schemas |
| **Orchestration engine** | Custom step engine (built-in) | LangGraph (state machine) |
| **Target audience** | Product teams shipping SaaS | Pipeline builders, prompt engineers |
| **Control flow** | `.then()`, `.parallel()`, `.branch()`, `.doWhile()` | YAML edges, routers, map nodes, race nodes |
| **Visual tooling** | Mastra Studio (built-in web UI) | CLI + graph export |
| **State persistence** | Suspend/resume with server restart survival | LangGraph checkpointers (memory, SQLite, Redis) |
| **Observability** | Built-in traces, logs, Studio inspector | LangSmith tracing |
| **Multi-agent** | Supervisor agents, agent networks | Subgraph composition, shared graph invocation |
| **MCP** | Client support (consume MCP tools) | Server + Client (expose graphs as MCP tools) |
| **Deployment** | Server, Gateway, framework adapters (Next.js, Hono, Express) | CLI, FastAPI wrapper, MCP server |
| **Scale** | Company with 50+ contributors, enterprise deals | Solo-authored, deep doctrine |
| **Testing** | Model-graded evals, rule-based, statistical | pytest + TDD, requirement traceability |

## What Mastra gets right

1. **Developer experience polish.** Studio visualization, type-safe step composition, framework integrations — production-ready surface area for web developers.
2. **Suspend/resume as first-class primitive.** Long-running workflows that survive server restarts, with explicit state persistence and restart APIs.
3. **The TypeScript bet.** Frontend teams building AI features stay in one language from UI to agent. That is a real market — most product engineers write TypeScript, not Python.
4. **Evals built in.** Model-graded, rule-based, and statistical evaluation methods with tracking over time. Ships with the framework rather than requiring external tooling.
5. **Enterprise adoption.** Docker, Elastic, SoftBank, Plaid using it in production validates the approach.

## Where YAMLGraph occupies different ground

1. **The YAML bet is the opposite bet.** Mastra says orchestration logic should be TypeScript. YAMLGraph says orchestration logic should not be code at all. A YAMLGraph graph file is readable by a non-programmer. A Mastra workflow requires TypeScript literacy. These are genuinely different visions of who builds AI pipelines and how fast they iterate.

2. **LangGraph underneath.** YAMLGraph inherits LangGraph's battle-tested state management, checkpointing, and streaming. Mastra built their own engine — more control over the API surface, but more maintenance burden and less ecosystem leverage.

3. **Prompt-as-artifact.** In YAMLGraph, prompts are YAML files with Jinja2 templating, inline schemas, and version-trackable structure. In Mastra, prompts are string literals inside TypeScript agent definitions. YAMLGraph treats the prompt as a first-class configuration artifact; Mastra treats it as code.

4. **The doctrine gap.** Mastra has engineering. YAMLGraph has epistemology. The Scripture, the Chaplain pipeline, the diary system, the traps/cures knowledge graph — this is infrastructure for learning from mistakes. Mastra has evals; YAMLGraph has a Philosopher.

## Different ecological niches

Mastra is not a competitor to YAMLGraph. They occupy different niches:

- **Mastra** is for TypeScript product teams who want agents embedded in their web apps. The workflow engine is a means to production reliability.
- **YAMLGraph** is for anyone who believes the prompt-graph-schema triad should not require a programming language. The framework is a means to declarative LLM orchestration.

## Opportunities

### What YAMLGraph could learn from Mastra

- **Visual Studio.** A web-based graph editor and step inspector would lower the barrier for non-CLI users. Mastra Studio shows this is expected table stakes.
- **Suspend/resume UX.** Explicit APIs for workflow suspension and human-in-the-loop approval flows. YAMLGraph has `interrupt_before` via LangGraph but could surface it more prominently.
- **Framework adapters.** Mastra's integration with Next.js, Hono, Express shows demand for "drop agent into existing app." The MCP server (CAP-19) partially addresses this but HTTP/REST adapters could complement it.

### What Mastra cannot replicate

- **YAML-first declaration.** Moving from code to config requires a philosophical commitment Mastra has explicitly rejected. Their entire type-safety story depends on TypeScript composition.
- **Prompt engineering without code.** Non-engineers can author and iterate on YAMLGraph prompts and graphs. Mastra's audience is always developers.
- **LangGraph ecosystem.** Checkpointers, LangSmith, LangServe — the LangChain ecosystem is a force multiplier that Mastra's custom engine cannot tap.

## Seed

Could YAMLGraph expose a Mastra-compatible API surface (MCP, A2A) such that TypeScript teams use Mastra as their frontend framework but delegate complex LLM pipelines to YAMLGraph graphs running as backend services? The three-layer architecture already separates presentation from logic — the presentation layer could be Mastra.
