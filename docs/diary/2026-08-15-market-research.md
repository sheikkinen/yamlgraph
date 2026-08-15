# Market Research — Is There a Need for YAMLGraph?

**Date**: 2026-08-15
**Context**: Critical competition review, `forced_opposite` applied — strongest case against first, then what survives.

---

## Competitive Landscape (verified 2026-08-15)

| Competitor | Stars | Positioning | Overlap with YAMLGraph |
|------------|-------|-------------|------------------------|
| **LangGraph** (LangChain Inc.) | 39.7k | Low-level stateful agent orchestration; Python-only API | The substrate itself; ships LangSmith Studio visual prototyping + Deep Agents |
| **CrewAI** | 49k | Config-first multi-agent (JSONC/YAML); enterprise visual builder (AMP) | Declarative agent/task config without Python |
| **gh-aw** (GitHub) | 4.9k, 428 releases | Markdown + YAML frontmatter agentic workflows compiled to GitHub Actions | Overlaps the *chaplain* automation, not just the runtime; GitHub distribution |
| **Dify / Langflow / Flowise** | large | Visual LLM pipeline builders with hosting | The "author pipelines without Python" market, with UIs |
| **Haystack** (deepset) | large | Component pipelines with YAML serialization + hardened deserialization allowlist | YAML pipeline representation |

## The Case Against

1. **Moat is one dependency deep.** YAMLGraph is a declarative skin over LangGraph. A first-party YAML/JSON DSL from LangChain would erase the core value prop in one release. We absorb their breaking changes with none of their leverage (FR-797: langgraph 1.x subgraph-interrupt regression is live proof).
2. **Crowded, better-funded category.** Five credible answers to "declarative LLM pipelines" exist, each with more distribution.
3. **Consumer list is one operator's portfolio.** ninchat_voice, outcaller, incaller, statemachine-engine — all internal. Zero verified external adopters. By our own canon (`would_you_use_this`) the external trigger list is empty.
4. **The original thesis is eroding.** "60–80% of workflows without Python" targeted humans avoiding code. Agents write Python trivially; the audience that couldn't write Python no longer exists.
5. **Gravity has shifted to governance.** Recent FR energy goes to chaplain, judge/review adapters, hooks, gates, fr-board — the runtime is increasingly substrate for process machinery, not the product.

## What Survives

1. **Constrained surface for agent authors.** `graph.yaml` has a schema, a linter, and deterministic parsing — a hallucinating agent is caught by `graph lint`; hallucinated LangGraph Python is caught in production. The honest version of the agent-first thesis: *lintable, diffable, mechanically judgeable artifacts*. No competitor sells this framing; gh-aw is closest but is prompt-body-first, not typed-pipeline-first.
2. **Traceability spine.** CAP registry, REQ marks, judged FRs, diary graduation, enforcement gates. For IEC 62304 / EU AI Act / SaMD territory, none of CrewAI/Dify/Langflow offer requirement-to-test traceability. Real moat, narrow vertical — and mostly separable from the graph runtime.
3. **Paid-for boundary knowledge.** The incident record (diary, Scripture) is the asset; the runtime is regenerable (`constraint_over_code`).
4. **Open source with no commercial execution-platform commitment.** Every credible competitor funnels toward a paid control plane: LangGraph → LangSmith Deployment, CrewAI → AMP/Studio, Dify/Langflow/Flowise → hosted clouds, gh-aw → GitHub Actions billing (a live billing-bug retirement notice on releases 0.68.4–0.71.3 at time of survey). YAMLGraph runs entirely locally — MIT-style stack, any provider via the LLM factory, checkpoints in SQLite/Redis you own, observability optional (LangSmith/OTel opt-in, not load-bearing). For regulated deployments (healthcare data residency, procurement constraints) and for agent-operated infrastructure, *no forced vendor runtime* is a differentiator the funded competitors structurally cannot match — their business model **is** the execution platform.

## Verdict

- **As a general-purpose framework competing for adoption: no need.** Do not invest in framework positioning or feature parity with CrewAI.
- **As the substrate for a regulated, agent-first, self-hosted development system: yes, conditionally.** The unique object is the *governed pipeline* — doctrine + traceability + enforcement over a declarative runtime, with zero commercial-platform lock-in. That combination does not exist elsewhere.
- **Direction: subtraction.** Make the runtime smaller and boring (LangGraph orchestrates; we do schema, lint, trace, gate). Treat the governance layer as the product.

## Cross-Check: ninchat_voice (most complex consumer)

Audit of the largest production consumer (~24K LOC, 11 graphs, 40+ prompts, 367 NC-* FRs, live PSTN calls) to test whether real usage validates the runtime or the governance layer.

**Feature usage (what actually carries load):**

| Feature | Used | Load |
|---------|------|------|
| `interrupt` nodes | ✓ every questionnaire graph | HIGH — pause/resume on user input; raw LangGraph needs hand-rolled handler |
| `race` nodes | ✓ extract/probe/recap, 2–3 providers | MEDIUM — auto-winner + timeout (NC-241, NC-339) |
| Checkpointer + Jinja2 inline schemas | ✓ | MEDIUM — schema reuse across 6+ callback graphs |
| `router`, `map`, `subgraph` | ✗ | Routing lives in the FSM and Python functions; graphs are atomic units |

**Hard findings:**

1. **The runtime is a thin, replaceable veneer.** Graphs are mostly linear prompt chains; the FSM (statemachine-engine) is the decision engine. ~15% of hard logic is in yamlgraph; dropping it costs ~200–300 LOC of LangGraph boilerplate per pattern and breaks nothing. Net LOC savings from YAML: near zero.
2. **Zero yamlgraph pain complaints in 5 months of production.** All complaints (NC-138, NC-243) are FSM-integration hygiene. But also: all major incidents (NC-287→NC-304 concurrent clobber arc, greeting replay, echo) were resolved in the FSM layer — the framework was never where the fight was.
3. **FR-797 confirmed irrelevant to the consumer**: no subgraphs, no nested interrupts — the framework's most complex machinery is unexercised by its most complex consumer.
4. **Governance is measurably load-bearing.** 367 FRs, 120+ judgements, `@pytest.mark.req("NC-XXX")` on every test, incident arcs resolvable only via the judgement trail. Resilience split estimated ~80% governance discipline / ~20% framework.

**Cross-check verdict:** ninchat_voice does **not** validate the runtime as a needed framework — it validates three narrow primitives (`interrupt`, `race`, schema-templated prompts) and the governance spine. This *strengthens* the main verdict: the defensible product is the governed pipeline; the runtime should shrink toward those proven primitives plus lint/schema/trace, and stop growing topology features its best consumer routes around via the FSM.

## Alternative Implementations of the Core Pair

The cross-check shows the actual production architecture is a **two-plane split**: a deterministic control plane (statemachine-engine FSM — 50 states, 100+ transitions, millisecond dispatch, no LLM) driving a stochastic reasoning plane (yamlgraph — atomic, bounded, lintable LLM tasks). Alternatives must be judged against the *pair*, not against yamlgraph alone.

**Merged alternatives (one framework owns both planes):**

| Alternative | Assessment |
|-------------|------------|
| **Single LangGraph graph** (durable execution + interrupts for the whole call) | What LangChain markets. DAG wearing FSM costume, inverted: 50 states × 100 transitions as graph edges is illegible; sub-second media events (barge-in, VAD, marks) don't fit checkpoint-resume cadence. The incident record (NC-287→304) lives at exactly the timing boundary a turn-based graph cannot see. |
| **Pipecat + Pipecat Flows** | The strongest genuine challenger. The April 2026 assessment ([pipecat-assessment-2026-04.md](docs/diary/pipecat-assessment-2026-04.md)) ruled "no competition — different planes", but that compared *frameworks*; at *architecture* level Pipecat Flows is a conversation FSM and would replace statemachine-engine + the ~2.8K LOC audio/telephony services in one move (`evaluation` boundary trap: the method determined the conclusion). Cost: control flow moves into Pipecat's runtime model, auditability of transitions weakens, and the ecosystem funnels toward Pipecat Cloud — violating the no-commercial-platform argument. |
| **Agent loop as controller** (ReAct / deepagents) | LLM owns control flow. Dead on arrival for regulated voice: non-deterministic control plane, unauditable transitions. The pair exists precisely to forbid this. |

**Control-plane alternatives (replace statemachine-engine, keep yamlgraph):**

- **Statecharts (XState/SCXML)**: hierarchical states would compress the 50 flat states meaningfully; mature formalism with model-checking literature. Weak Python implementations; would still need the action-script layer. The one alternative with a *theoretical* edge.
- **Temporal-class durable workflows**: battle-tested durability and signals, but workflow-as-code (loses the declarative, judgeable transition artifact) plus heavyweight infra and a commercial-cloud gravity of its own.
- **Raw asyncio dispatch**: the null hypothesis. Works; loses exactly the property both YAML layers share — transitions as diffable, lintable, mechanically judgeable artifacts.

**Reasoning-plane alternatives (replace yamlgraph, keep the FSM):**

- **Raw LangGraph Python**: ~200–300 LOC boilerplate per pattern (audit figure); loses the lintable artifact and the authoring guard.
- **Typed prompt functions** (bare `execute_prompt` + Pydantic; BAML/DSPy-class): the sharpest challenge, because it attacks the decomposition itself. The `interrupt` primitive — yamlgraph's highest-load feature — exists only because graphs *span turns*. Decompose one level finer (one atomic graph/prompt invocation per turn, FSM owns all conversation state) and `interrupt` disappears; `race` and schema-templated prompts reduce to a ~300-LOC library. The framework's flagship primitive is an artifact of where the plane boundary was drawn, not an intrinsic necessity.

**Reflection:** every alternative either collapses the two planes (Pipecat, single-LangGraph, agent-loop) or redraws the boundary between them (per-turn decomposition). The pair's real claim is not "YAML runtime" but the **split itself**: stochastic reasoning confined to atomic, typed, lintable tasks under a deterministic, auditable controller. That claim survives every alternative for the regulated domain — but it is an *architecture pattern*, portable to other runtimes, which again points at governance-and-contract as the product rather than the engine. The April Pipecat verdict needs a scheduled re-read at architecture level, not framework level.

## Kill-Risks (review quarterly)

1. LangChain ships a first-party declarative DSL.
2. gh-aw grows repo-local (non-Actions) pipeline execution.
3. **Pipecat Flows: THREAT-DORMANT** (FR-803, assessed at Pipecat commit `a5bb7867e1a08595dac1a778948bbdb49e0549b2`). Flows is self-hosted and action-capable, but v1.0 removed static flows; live transitions are Python handlers advertised as LLM tools and returning the next `NodeConfig`. It therefore fails static diffable transitions and deterministic non-LLM dispatch for the ninchat_voice control plane. Recheck when Pipecat ships either a first-class static transition/event schema or an export API for the complete dynamic transition relation, including guards, wildcard events, timeouts, and actions, without executing LLM-selected handlers. See [the architecture assessment](2026-08-15-pipecat-flows-architecture-assessment.md).

Any fires → the runtime half of this repo becomes commodity within a release cycle; the governance spine and platform-independence remain.

**Seed:** If the product is the governed pipeline and platform-independence, can the traceability spine (CAP/REQ/judge/gates) be packaged to govern *foreign* runtimes — LangGraph-native code, gh-aw workflows — so the moat survives even if the YAML runtime dies?

## Addendum 2026-08-15: "Why not just Python + LangGraph?" — the self-hosting null hypothesis

Probe: if the argument is "open source, self-hosted, no commercial execution platform," what stops a buyer from taking raw LangGraph (MIT, fully self-hostable) and their own conventions?

**Finding: OSS + self-hosted is table stakes, not a moat.** Nearly every competitor's runtime is OSS and runs anywhere. What differs is (a) vendor incentive and (b) artifact class:

| Alternative | Self-hosted | Commercial gravity | Artifact class |
|---|---|---|---|
| Raw Python + LangGraph | fully | LangSmith/Platform is the funnel; OSS runtime is its top | Python code — not lintable as config |
| Haystack 3.0 (Apache-2, 26.2k stars) | fully | Haystack Enterprise Starter/Platform (managed **or self-hosted**); deepset Studio; telemetry on by default | **YAML is serialization, not authoring** — see below |
| Dify / Langflow / Flowise | yes | cloud editions are the business | visual-editor JSON blobs |
| CrewAI | yes (MIT core) | AMP/Enterprise push | Python code |
| gh-aw | no — structurally GitHub Actions | GitHub billing *is* the platform | md+frontmatter, lintable but platform-bound |
| Pipecat Flows | fully (BSD-2) | Daily transport funnel | Python dicts/handler code |

**Haystack cross-check (verified against docs.haystack.deepset.ai/docs/serialization and repo, 2026-08-15):** the earlier "closest artifact-class competitor" assessment was too generous. Haystack's YAML is a **round-trip serialization format** (`Pipeline.dumps()`/`loads()`), not an authoring surface: pipelines are authored in Python; the YAML embeds fully-qualified Python class paths (`type: haystack.components...DocumentCleaner`) plus `init_parameters` mirrors of constructor signatures. Loading YAML instantiates classes — hence their trusted-module allowlist, blocked builtins, and `unsafe=True` escape hatch. Their own docs warn of "stale snapshots from older Haystack versions" breaking deserialization. It is a pickle wearing YAML clothes: machine-diffable, but coupled to Python class internals, version-brittle, and not schema-lintable independent of the installed package. No judge, no gates, no traceability. Closer to Dify's JSON blobs than to a declarative DSL. Notable counterpoint: deepset's Enterprise Platform *is offered self-hosted* — so even the "no self-hosted governance offering" line must be argued on lock-in and artifact class, not deployment topology alone.

**Surviving one-liner:** not "open source, self-hosted" — everyone claims that. It is: *self-hosted governed pipelines where the vendor's business model does not require execution to leave the building, and the pipeline artifact is declarative-first — authored as YAML, lintable without executing Python, constrained enough for an agent to author and a machine to judge.* Raw Python + LangGraph fails the artifact clause; Haystack fails it too (serialization ≠ authoring) plus the governance clause; the visual builders fail human-judgeability; gh-aw fails self-hosting. For a competent *human* team the null hypothesis (raw LangGraph + house conventions) genuinely wins — the differentiator only binds when the authors are agents and the reviewers are machines (`constraint_over_code`).
