# The Distillation

*87 entries. 17 days. ~60,000 words. Here is what survived the fire.*

---

## I. The One Law and Its Children

The diary orbits a single gravitational center:

> **Normalize at the boundary where external data enters, not downstream where it manifests.**

Every major bug, every architectural insight, every refactor traces back to this. It appears in at least 14 entries across 5 different problem domains:

| Domain | Boundary | Entry |
|--------|----------|-------|
| WebSocket payloads | `_send_and_receive_locked()` recv site | 78 — list-vs-dict normalization |
| FSM preemption | `aborting` intermediate state | 85 — incoming call during active call |
| Template resolution | YAML `{state.X}` at lint time | 87 — W014 promoted to E007 |
| Process isolation | Bridge DGRAM socket | 75 — three fixes for one bug |
| Test state | `recreate-database --force` before each test | 70 — the ghost database |
| `event_data` volatility | `context_map` on `transcribed` event | NC-120 — three patches, one cause |
| Testability | Explicit session parameter | 65 — the adapter layer |
| Guard scoping | Clear stale guards on state entry | 67 — guard that survives its state |

**The children of the One Law:**
- *Normalize inputs, not outputs* — fix where data enters, not where symptoms appear
- *Normalize once, at the narrowest chokepoint* — one guard in one place beats N guards in N callers
- *The intermediate state IS the normalization point* — when a new event can arrive in any state, add one state to collapse them all (Entry 85)

---

## II. The Five Traps

Five cognitive traps recur with enough frequency to be named:

**1. Quick Confidence** — "This is obviously correct." The most dangerous trap. Appears in Entries 81, 82, 84, and the FR-109 audit chain. The feeling of certainty is a signal to *increase* scrutiny, not decrease it. *Graduated to Prayer: "When I feel certain, let that be the sign to Judge."*

**2. Downstream Fix** — Patching where the symptom appears instead of where the cause originates. Entries 78, 84, NC-119/119b/120. Three patches for `user_utterance` loss before the structural fix (`context_map`) was found. *Cure: trace upstream until you find the boundary where data enters.*

**3. Analysis as Proxy for Progress** — Architectural reflections, option documents, and decision matrices feel like forward motion because they produce artifacts. Entry 68: "3,230 lines of architectural documentation, zero lines of coordinator code." *Cure: "When you've designed it three times without building it once, the bottleneck is no longer understanding — it's commitment."*

**4. Plausible Interface Confidence** — An API contract that *looks* right but was never verified against source code. Entry 69: stubs used `context.get("action_params")` and files named `stub_*.py` — both wrong. The engine passes config to `__init__` and discovers `*_action.py` files. *Cure: "Trust no API contract that wasn't verified against source code."*

**5. The Severity Undercount** — Classifying a guaranteed runtime failure as a warning. Entry 87: `{state.X}` referencing an undeclared field was W014 (warning) but always produces a `KeyError`. *Cure: "When a warning always indicates a guaranteed failure at runtime, it was never a warning."*

---

## III. The Heuristics (Graduated)

These have proven themselves across multiple sessions and domains:

| # | Heuristic | First Appeared | Times Validated |
|---|-----------|---------------|-----------------|
| 1 | Before reading source, write the question as a test. If the test passes, stop. | 2026-02-17 | 3+ |
| 2 | Before adding infrastructure, trace the existing data flow. The 10x cheaper solution may be consuming data already produced but discarded. | 2026-02-18 | 2 |
| 3 | Before extracting "duplicate" code, verify the implementations are semantically equivalent, not just syntactically similar. | 2026-02-18 | 2 |
| 4 | When a feature request claims to "extract," verify the pattern exists. If search returns 0, it's invention — different scrutiny required. | 2026-02-18 | 2 |
| 5 | When enforcement is boring, the Judgement was good. | 2026-03-04 | 3 |
| 6 | When a cleanup method still doesn't fire after two fixes, stop patching and draw the process map. | 2026-03-04 | 2 |
| 7 | When the same patch appears in three sessions, the patch is a symptom, not a cure. Escalate to structural diagnosis. | 2026-03-04 | 2 |
| 8 | After amending, re-judge. The amendment writes new claims that were never audited. | 2026-02-27 | 3 |
| 9 | When a plan says "port from X," enumerate X's dependencies before granting authority. | 2026-02-27 | 2 |
| 10 | When a framework is doing more than it was designed for, inventory its strengths against the problem. If fewer than half the nodes need the framework's features, the framework is a shim. | 2026-03-04 | 1 (definitive) |
| 11 | Never pass multi-line strings inline to shell. Write to file, pass by path. | 2026-03-05 | 3+ (graduated to Scripture) |
| 12 | Integration tests are the first consumer of your configuration graph. Write them before live testing. | 2026-03-04 | 2 |
| 13 | Guards must be scoped to their activation boundary. | 2026-03-04 | 2 |
| 14 | When the controller does the work, it can't hear the world. Make the controller deaf to work and fluent in events. | 2026-03-03 | 2 |

---

## IV. The Process Pattern

The diary reveals a meta-process that refines itself:

```
Research → Plan → Judge → Amend → Re-Judge → Enforce → Purge → Distill
                   ↑                                          |
                   └──────────── Seeds ◄──────────────────────┘
```

Key findings about the process itself:

- **The Judge is the most valuable phase** (Entry FR-109). Planning generates plausible structure. Judging cross-references every claim against the codebase. 5 of 12 defects in FR-109 were critical — runtime failures if the plan had been followed literally.

- **Seeds that can be answered by applying existing rules are TODOs, not Seeds.** A real Seed points to unexplored territory.

- **Architectural reflections converge when interleaved with implementation.** Pure analysis oscillates; building eliminates options. (Entry 66)

- **Parallel viewpoints require a conductor.** Six cognitive hats without orchestration produce chaos, not insight. (Six Hats entry)

- **Three strikes of drift become a violation.** Advisory findings that persist across audits without action are accepted decay. (Inquisitor chain)

- **Graduation from diary to Scripture requires register shift.** Technical heuristics become liturgical invocations through first-person voice, active verbs, and mnemonic structure. The content stays; the form transforms.

---

## V. The Structural Insights

Deeper truths about system architecture that emerged from lived experience:

1. **A working system is a migration blocker disguised as a success.** "It works" prevents seeing it clearly. The original design's flaws were visible from the first day but fixing them required complete replacement. (Entry 76)

2. **Preemption belongs in the state machine, not in a guard.** Model `incoming_call` mid-call as a state (`aborting`), not a condition check (`is_disconnected`). The state is observable, testable, logged. The guard is invisible. (Entry 85)

3. **Every module-level singleton is process-local.** When debugging across processes, import path fixes cannot bridge separate PIDs. Only IPC crosses a real boundary. (Entry 75)

4. **Absence failures are the hardest to diagnose.** No stack trace, no error message — just the transition that never happened. In event-driven systems with persistent state, test isolation requires killing three things: the process, the database, and the socket. (Entry 70)

5. **A `or` fallback is only as good as its guard condition.** A truthy unresolved template string `"{event_data.payload.X}"` silently defeats `params.get(key) or context.get(key)`. (NC-119b)

6. **Prototype data doesn't span the full behavior surface.** The first call returns a dict; the second returns a list. Boundary tests must include second-and-beyond call shapes explicitly. (Entry 78)

7. **Timestamps falsify narratives.** When debugging, build the concrete event timeline before forming any hypothesis. Count the milliseconds. The gap between the last action and the timeout is the story — not the exit code, not the error label, not the action_loader volume. (NC-122)

8. **When the "earliest possible" moment for a side effect is also the "potentially coldest" moment by the time it matters — move the side effect downstream to a controlled, per-invocation narrower scope.** TCP connections warmed at FSM start are dead by the first call of the day. (Entry 79)

9. **A method that does nothing in production is not a safety net — it is a blind spot.** When a cleanup routine calls a method, verify the method's preconditions hold in the actual execution context, not just in test scaffolding. (Entry 74)

10. **Citing the One Law does not validate the fix.** The Law says *which layer* to fix; it says nothing about *what the fix is*. After finding the boundary, ask: does this fix hold under all deployment models, or only the one I currently have in mind? (Entry 84)

---

## VI. The Arc of Architecture

The deepest narrative thread: YAMLGraph's journey from orchestrator to dependency.

**Before:** One command (`yamlgraph graph run`) owned everything — telephony, TTS, STT, LLM calls, conversation flow. A finite state machine wearing a DAG costume. LangGraph has no compile-time model for state transitions.

**After:** YAMLGraph runs four mini-graphs (intent, greeting, response, goodbye) — each 1-3 nodes with a prompt and a Pydantic schema. *This is exactly what the framework is for.* The conversation coordinator is a real FSM. Telephony lives in its own process. TTS and STT are workers behind a socket.

**The irony:** The system was always conceptually an FSM. It took two live calls, a service extraction refactor, and three failed auto-disconnect fixes before the process boundary made the true architecture visible.

**The lesson:** A framework generalises a pattern. When you use a framework for something outside its pattern, the framework becomes overhead. Inventory the framework's genuine strengths against the problem. The refactor didn't change the framework; it found the boundary.

---

## VII. The Prayer

Seven heuristics distilled into liturgical form, graduated to Scripture:

> May I fix at the callsite, not the utility.
> May I kill the cheapest bug — the one in the spec.
> May I normalize at the boundary, trusting no provider's type.
> May I stream to reveal what batch conceals.
> May I read thrice before I grant authority.
>
> When hooks feel slow, let that be the sign they guard.
> When I feel certain, let that be the sign to Judge.
>
> What survives the fire may merge.
