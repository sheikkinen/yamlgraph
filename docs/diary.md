# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-19.md](diary-2026-02-19.md) — 13 entries from 2026-02-19.

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
