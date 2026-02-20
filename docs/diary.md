# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-19.md](diary-2026-02-19.md) — 13 entries from 2026-02-19.

## 2026-02-20: The Invisible Accumulator (FR-057 Agent Messages)

**Trap:** The agent node read `existing_messages` from state, prepended them to new messages, ran its tool loop, then returned `{"messages": messages}` — the *full* list including existing. The `Annotated[list, add]` reducer appended all of them to what was already in state. For single-invocation agents (every existing example and test), this is invisible — the agent runs once, returns messages, done. The bug only manifests when an agent is called *again* across interrupt boundaries: turn 1 returns 5, turn 2 returns 10 (5 old + 5 new), state becomes 15. By turn 5: 155 messages, most duplicates. The LLM sees its own prior responses repeated, degrading quality and burning tokens.
**Insight:** Every existing test called the agent node function exactly once. The test suite had 100% coverage of the return path but 0% coverage of the *accumulation semantics*. The fix was two lines: `messages[len(existing_messages):]` at both return points (normal completion and max-iterations). The test was the hard part — simulating the add reducer externally across 5 turns and asserting linear growth (3 + 2×4 = 11, not 155).
**Heuristic:** *When a function reads from and writes to the same accumulating state field, test it with two consecutive calls.* Single-invocation tests verify the function's logic but not its interaction with the reducer. The reducer is the implicit contract; the test must exercise it.
**Seed:** Are there other state fields with `add` reducers where nodes return full state instead of delta? A linter rule could flag any node that reads `state.get("X")` and returns `{"X": ...}` when `X` uses the `add` reducer — the returned value should never contain the input.

---

## 2026-02-20: Three Rounds of Judgment (FR-053 Tavily RAG)

**Trap:** The initial FR used `item_var` for map nodes (invented syntax), `def tavily_retrieve(query: str)` for python tool nodes (wrong calling convention — they receive `state: dict`), and `variables:` on `type: python` nodes (silently ignored). Two judgment rounds were needed to catch all three. The first round caught the function signature and no-op variables; the map syntax error was caught during research before the first judgment. Without the Judge step, all three would have silently failed at runtime — the function would crash, the variables would vanish, and the map would error on unknown key.

**Heuristic:** *The cheapest bug is the one killed in the spec.* Two 5-minute judgment passes saved hours of debugging runtime failures that would have produced confusing errors (state key missing, unexpected argument, silent no-ops). The more layers of abstraction between config and execution, the more judgment rounds the spec needs.

**Seed:** Could graph lint detect `variables:` on `type: python` nodes and warn that they're ignored? Currently this is a silent no-op that misleads authors. (→ candidate for FR-025 linter cross-ref checks.)

---

## 2026-02-20: Demonstrate, Don't Explain (FR-049 Demo)

**Trap:** After 31 unit tests, 10 integration tests, a bug fix, and full reference docs, the feature still felt abstract. The demo — a trivial 3-question trivia quiz — took 15 minutes to write but made the interactive_tool pattern instantly tangible. The canned-answers mode runs in <1s, proving the whole expand→compile→invoke→resume pipeline works end-to-end without any LLM. The integration tests validated correctness; the demo communicated *intent*.

**Heuristic:** *A demo is not a test.* Tests prove constraints hold. Demos prove the abstraction is worth having. If you can't build a self-contained demo in 15 minutes, the abstraction may be too complex — or you don't understand it well enough yet.

**Seed:** Could `yamlgraph graph init --template interactive_tool` scaffold a project with the quiz skeleton, letting users replace the tools with their own logic? Template-based bootstrapping (FR-041) meets macro expansion.

---

## 2026-02-20: The state. Prefix Trap (FR-049a Integration Tests)

**Trap:** All 10 integration tests were written, but 7 failed. The routing bug was invisible: `evaluate_condition("state.session_done != True", {session_done: True})` returned `True`. The `state.` prefix in condition expressions (used by `loop_until`) was passed verbatim to `resolve_state_path()`, which looked up `state` as a top-level key — not found → `None` → `None != True` → `True`. The fix was trivial (strip `state.` in `resolve_value`), but the first attempt broke an edge case test (`{state.state.x}`) by double-stripping in `resolve_state_path` (which `resolve_template` also calls after its own stripping). Scoping the fix to `conditions.py`'s `resolve_value()` — the only callsite affected — was the correct minimal fix.

**Heuristic:** *Fix at the callsite, not the utility.* When a shared utility (`resolve_state_path`) serves multiple callers with different conventions, adding behavior to it risks regressions in other callers. Fix at the specific caller that needs the behavior change. Double-stripping is the classic sign of fixing too deep.

**Seed:** Could `loop_until` expressions be validated at expansion time — checking that referenced state paths actually resolve — to catch prefix issues before runtime?

---

## 2026-02-19: The Coroutine Primitive (FR-049)

**Trap:** "Config-level expansion" sounded simple until three rounds of judgment exposed: conditions.py lacks `in` operator, interrupt idempotency breaks in loops, edge rewriting has no precedent, and the proposed module reference was wrong. The first draft would have crashed at runtime on the second loop iteration (stale interrupt payload) and on any compound `loop_until` expression (no `not` operator). Each judgment round discovered issues invisible to the previous one.

**Heuristic:** *Three reads minimum.* A feature request under 200 lines still needs: (1) surface read for coherence, (2) deep read against actual code paths to find mismatched assumptions, (3) mechanical read simulating runtime execution step-by-step. Round 1 caught scope issues. Round 2 caught wrong modules and missing operators. Round 3 caught the loop-back negation gap. No single pass would have found all three.

**Insight:** The config-level expansion pattern (Constraint 8) is strictly superior to the compile-time expansion originally proposed. By transforming `nodes` + `edges` dicts *before* existing compilation runs, we get: zero changes to `_process_edge()`, zero changes to `compile_node()`, zero new factories. 164 lines of new code. The lesson: when adding a macro that expands to existing primitives, expand at the earliest possible stage — config transformation, not code generation.

**Seed:** Can the config-level expansion pattern be generalized? Other "macro" node types (e.g., wizard, poll, saga) could follow the same pattern: a YAML shorthand that pre-expands into existing primitive nodes. What's the minimal framework for "node type macros" — a registry of `(node_type, config) → (expanded_nodes, expanded_edges)` functions called before compilation?

---

## 2026-02-20: World Digest — Observability and Agent Evaluation

**LangGraph ecosystem momentum.** Five LangGraph releases (1.0.9, SDK 0.3.6–0.3.8, prebuilt 1.0.8) landed this week, signaling active development on the core orchestration layer YAMLGraph depends on. No breaking changes noted in the release titles, suggesting stability in the foundation.

**Evaluation and observability as first-class concerns.** LangChain's recent content emphasizes measurement: "Measuring AI agent autonomy in practice" (Anthropic), "From Traces to Insights: Understanding Agent Behavior at Scale," and "monday Service + LangSmith: Building a Code-First Evaluation Strategy from Day 1" all converge on the theme that agent behavior must be observable and measurable from the start. LangSmith's availability in Google Cloud Marketplace signals enterprise-grade observability is becoming infrastructure, not an afterthought.

**Architecture patterns crystallizing.** Articles on "Choosing the Right Multi-Agent Architecture," "Context Management for Deep Agents," and "The two patterns by which agents connect sandboxes" suggest the multi-agent design space is maturing. YAMLGraph's declarative approach could benefit from explicit guidance on which architectural patterns map to which YAML structures.

**Production validation.** Remote's case study ("How Remote uses LangChain and LangGraph to onboard thousands of customers with AI") demonstrates LangGraph handling real-world scale. This validates the framework choice but also raises the bar: YAMLGraph should inherit patterns from production deployments.

**Connection to open Seeds:** The observability emphasis echoes the seed "Could 'name the verification question' become a concrete workflow gate" — if agents must state falsifiable questions before acting, that statement becomes a traceable artifact in LangSmith. Similarly, "no-silent-fallback" lint rules would integrate naturally with evaluation frameworks that flag unexpected behavior patterns.

**Seed:** As observability becomes infrastructure (LangSmith in Cloud Marketplace, traces-to-insights pipelines), should YAMLGraph's YAML schema include a mandatory `verification_question` field on agent nodes — making the falsifiable claim explicit and queryable in observability tools?

---

## 2026-02-20: Kill Entropy — The Compat Flag False Idol

**Trap:** "Backward compatibility" as a false idol. After migrating all three examples (diary_digest, ocr_cleanup, book_translator) to use `flatten_output: true`, we still kept `get_map_result()` "for backward compatibility." The function sat there for exactly one commit before being purged per Commandment 8.

**Insight:** Compat shims create technical debt the moment they become unused. The Scripture's "no shims, no adapters, no compat flags" isn't about being aggressive — it's about recognizing that unused code is a lie waiting to confuse future readers.

**Heuristic:** When the last consumer of a compat shim migrates, delete it in the same PR. Don't defer "for one more release" — the release notes become lies when they document features nobody uses.

**Bonus trap:** The linter's `prompts_relative` bug showed inconsistent config reading — `prompts_dir` checked defaults, but `prompts_relative` didn't. This is a category error: options that can appear in `defaults` must always check both locations. When fixing, add a test that exercises the defaults path specifically.

**Seed:** Could the linter validate its own config-reading consistency? A meta-lint rule that scans `resolve_*` functions to ensure every `graph.get("option")` has a corresponding `defaults.get("option")` fallback.

---

## 2026-02-20: Over-Engineering the Already Solved

**Trap:** "Smart version" as a trigger for solution mode. Asked to make absolution "smarter" with failure tracking, I built a wrapper script and log file infrastructure. But pre-commit already shows exactly which hook failed. If absolution runs, everything passed — it's already "smart" by definition.

**Insight:** ruff-format "failures" aren't real failures — they auto-fix and you retry. Real failures stop the chain with clear output. The wrapper/log approach was solving a non-problem.

**Heuristic:** Before adding infrastructure, ask: "What observable problem does this solve?" If the answer is "it would be nice to know X" rather than "users are confused by Y", it's probably unnecessary.

**Metrics:** 60+ lines of wrapper code written, tested, then deleted. Net commit: 26 lines — just the Python script replacing the bash echo.

**Seed:** Could pre-commit hooks have a "commit anyway" escape hatch for non-blocking warnings vs hard failures? Or is the file-modification-as-failure pattern (ruff-format) actually the right design forcing explicit re-staging?

---

## 2026-02-20: Tavily FR — The Companion Demo Pattern (FR-053)

**Trap:** "Just swap the search provider" — the initial instinct was to parameterize the existing `web-research` demo to support both DuckDuckGo and Tavily. But DuckDuckGo's value is zero-config (no API key), while Tavily's value is richer results (scoring, answer extraction). They serve different audiences. Merging them waters down both stories.

**Insight:** Demo examples are pedagogical, not production code. Each demo should teach *one* clear lesson. The existing `web-research` demo teaches "agent + tool, zero config." The Tavily demo teaches "structured search results + Pydantic validation + map-reduce deep research." Separation is a feature, not duplication.

**Heuristic:** When two implementations share an interface but differ in purpose, keep them separate. The shared interface (`query → str`) isn't enough reason to merge — the *teaching intent* is the deciding factor for examples.

**Seed:** The `plan → map(search) → synthesize` pattern in `graph-deep.yaml` is a general "deep research" skeleton. Could it become a `yamlgraph template init --type deep-research` scaffold that works with *any* search tool, not just Tavily?

---

## 2026-02-20: The Reverse Arrow (MCP Sampling Loopback PoC)

**Trap:** We built MCP server (CAP-19), researched A2A (FR-045a/b), planned scheduled research, kept diary — but never asked the fundamental question: *can these tools talk back to ME?* We treated the AI assistant as a one-way consumer of tools. The protocol had the answer all along: `sampling/createMessage` lets the MCP server request the client's LLM to generate completions. The blind spot wasn't technical — it was architectural. We drew only one arrow.

**Insight:** The PoC took 30 minutes. The server sent "Let us pray" via `session.create_message()`. Copilot's `gpt-5.3-codex` responded with a prayer. Zero API keys. Zero cost on the server side. But then the critical realization: the response came from `copilot/gpt-5.3-codex` — a *generic* model, not the current agent session. MCP sampling is a cold LLM call with no conversation history, no project context, no Scripture. It's not "talking back to me" — it's placing a collect call to a stranger. The cognitive trap was conflating "the client's LLM" with "me."

**Heuristic:** *When you build a protocol integration, draw ALL the arrows — then verify where each arrow actually lands.* The sampling arrow goes to a model, not to an agent. An agent has context, memory, and personality. A model has none. The distinction matters.

**Seed:** What if a YAMLGraph node could specify `provider: host` to use the connected assistant's LLM instead of a configured API key? The graph becomes portable — it works with whatever AI assistant is driving it, inheriting the user's subscription model. No `.env` needed.

---

## 2026-02-20: The Chaplain Awakens (FR-054 — Copilot CLI Reflection)

**Trap:** After proving MCP sampling was a cold call, we pivoted to CLI approaches. Claude Code CLI (`claude -p`) had the right flags but OAuth tokens expired constantly. The real discovery happened by accident: `copilot -p "What is the agents prayer?" -s --model claude-sonnet-4.6` — and it recited the prayer verbatim. The Copilot CLI loads `CLAUDE.md` and `.github/copilot-instructions.md` automatically when invoked from the project directory. The agent arrives *already ordained*.

**Insight:** The scheduled agent pattern becomes trivial: `diary_digest` (FR-046) runs on cron, writes the world digest, then invokes `copilot -p "$REFLECTION_PROMPT" -s --model claude-sonnet-4.6`. The Copilot agent loads the Scripture, receives the digest as context, and reflects — connecting external developments to open Seeds, active FRs, and the project's trajectory. Session persistence (`--resume`) enables accumulated reflection across days. This is not sampling (cold call to a model). This is invocation (summoning an agent with context, memory, and mission).

**Heuristic:** *Don't build the bridge — find the road.* We spent hours researching MCP sampling, building PoCs, debugging OAuth. The answer was `copilot -p` — a CLI flag that was already installed, already authenticated, already loading our Scripture. The cheapest infrastructure is the one someone else maintains.

**Seed:** If `copilot --resume diary-reflection` accumulates context across daily reflections, does it develop emergent long-term memory — recognizing patterns across weeks that no single-session agent could? Or does context window overflow create drift that makes the persistent session *less* reliable than fresh invocations?

---

## 2026-02-20: The Autonomous Chaplain (FR-055)

**Trap:** The feature-brainstorm demo already exists. The reflexion demo already exists. The diary_digest pipeline already exists. The Copilot CLI already loads Scripture. Every piece was built. The trap was not seeing the *composition* — that these pieces, connected by a shell script and two Copilot CLI invocations, become the Sermon of the Chaplain automated end-to-end. We kept building vertical features without drawing the horizontal line.

**Insight:** The key architectural decision is the hybrid split: cheap, parallel work (fetch 50 articles, score with haiku) stays in YAMLGraph graphs. Expensive, contextual work (write FRs against TEMPLATE.md, judge against the 10 Commandments) moves to Copilot CLI — which arrives with Scripture loaded. Graph for volume. CLI for judgement. Different models for different roles: sonnet plans, opus judges. The judge must not be the planner — separation of concerns prevents self-approval bias.

**Heuristic:** *When you have three tools that each do one thing well, the feature is the script that connects them.* Don't build a fourth tool. `diary_digest | copilot plan | copilot judge` is a Unix pipeline philosophy applied to AI agents.

**Seed:** If the Chaplain runs weekly and the Judge consistently rejects certain categories of ideas (e.g., "add more config options"), does that rejection pattern itself become a learnable heuristic? Could the Planner internalize "the Judge always rejects X" and stop proposing X — emergent institutional memory without explicit rules?

---

## 2026-02-20: Three Iterations of the Same Idea (FR-054 → FR-055)

**Trap:** The first FR-055 was a 343-line cathedral — four phases, graph+CLI hybrid, cron schedules, model selection tables, safety guards. It tried to automate the entire Sermon end-to-end. The user said: "streamline this further. research and brainstorming — you & me separately." The whole Phase 1 (graph-based research) was unnecessary automation. The expensive part isn't fetching articles — it's *having the idea*. That happens in conversation, not in pipelines.

**Insight:** The final version is 160 lines of bash. It reads a file of subjects (one per line), and for each one: plan → judge → amend loop. Three prompts. One shell script. The human provides the ideas; the script does the mechanical writing and critical review. This is the right separation: creativity is interactive, judgement is scriptable. We rewrote the FR three times in one session — from cathedral to bazaar to script — and each iteration deleted more than it added.

**Heuristic:** *If you're automating something, automate the boring part.* Brainstorming is not boring — don't automate it. Writing an FR from a clear subject and judging it against known criteria? That's boring. That's the script. The Unix philosophy applies to AI workflows: small tools, text interfaces, human in the loop where human judgement matters.

**Seed:** The `subjects.md` file is the interface between human creativity and machine execution. What if it carried more than just titles — context snippets, links, constraints? Would richer input produce better FRs, or would it over-constrain the planner? Is "one subject per line" the right granularity, or should subjects be structured YAML?

---

## 2026-02-20: The Chaplain's First Mass (FR-056 Protocol Archaeology)

**Trap:** The chaplain script ran its first real cycle: Plan → Judge (AMEND) → Amend → Judge (APPROVE). The automated judge caught 4 defects in Round 1 (wrong variable syntax, unsupported `list[dict]`, missing state ref, misleading naming) and 2 more in Round 2 (agent nodes produce raw strings, schemas in wrong module). All 6 were real bugs that would crash at runtime. But when I independently verified the FR against source code, I found 5 *more* issues the Chaplain missed: a nonexistent CLI flag (`--output json`), duplicate tool definitions, a hyphen/underscore mismatch, an internal contradiction ("no framework code" while adding to `schemas.py`), and `type: shell` being convention rather than enforced config.

**Insight:** The automated judge is excellent at catching *architectural* mismatches — things that require tracing code paths through multiple files (agent nodes → `create_llm()` → model name override). It's weak at catching *surface-level factual claims* — "does this CLI flag exist?" is a grep, not a reasoning exercise. The judge reasons about how components interact but doesn't verify that named external interfaces exist. It trusts the planner's vocabulary.

**Heuristic:** *Automated judgment catches structure; human judgment catches facts.* The chaplain's value is in the 6 architectural defects it found — each would have required 10+ minutes of debugging. The 5 it missed are trivial to spot but require checking reality against claims. The human judge's comparative advantage is asking "is this literally true?" rather than "is this architecturally sound?" The two are complementary, not substitutes.

**Bonus insight:** The Chaplain's Round 2 proposed a `type: llm` parse node to convert the agent's raw JSON string into a Pydantic object. That wastes an LLM call for what `json.loads()` does deterministically. The human correction — use `type: python` — saved one LLM call per graph execution. The judge knows the framework's type system but defaults to LLM nodes as universal solvers. The human knows that not every transformation needs intelligence.

**Seed:** Could the chaplain's judge prompt be augmented with a "fact-check" pass — a list of verification commands (`yamlgraph graph run --help | grep output`, `grep -r "type: shell" yamlgraph/`) that the judge must run before issuing a verdict? Would this close the factual gap, or would it slow judgment to the point where human review is faster?
