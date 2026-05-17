# Chapter 7: The Wrong Tool Wearing the Right Name

*On the trap called* `framework_costume`

---

## I. The 389-Line Confession

On the fifth of May, a team built a planning agent. They needed a system that could read a feature-request template, allocate the next sequential identifier, and produce a structured plan. The tool they reached for was the Claude Agent SDK — an autonomous agent framework with subprocess transport, tool-calling hooks, and budget controls. The spike landed at 389 lines of Python: two custom tools, an audit hook, a structured output contract. It worked. It was merged. It was immediately dog-fooded to produce a real feature request.

And then someone said: *"There is an `agent` keyword in YAMLGraph. Check."*

The diary records what followed with the quiet devastation of a post-mortem:

> Found `type: agent` in `yamlgraph/tools/agent.py` — a full LangChain tool-calling loop that already supports python + shell tools, provider-independent, max_iterations, tool_results_key. The spike's 389 lines reimplemented what YAMLGraph already provides.

Three hundred and eighty-nine lines to rebuild something that already existed. The spike's value, the diary concludes, "was not the code — it was the proof that the problem was already solvable with existing infrastructure." A 389-line confession that the team had searched outward before searching inward.

But the failure was not laziness. It was not ignorance of the codebase. It was something more subtle and more dangerous: the name fit. The problem description said *"we need an agent."* The Agent SDK is, by name, *an agent framework.* The syllogism completed itself before anyone thought to question the premises. The costume was convincing.

---

## II. The Seduction of Names

The Knowledge Graph defines `framework_costume` with surgical brevity: *"FSM wearing DAG costume → if <50% of nodes use core features, wrong tool."* But this definition understates the trap's seductive mechanism. The danger is not that someone knowingly selects the wrong tool. The danger is that the right name makes the wrong tool *feel* right — that naming creates false equivalence, and false equivalence short-circuits evaluation.

Every instance in the diary follows the same syllogism:

1. We need capability X.
2. Framework F is called "X Framework."
3. Therefore, use Framework F.

The logic is valid. The conclusion follows from the premises. But the argument is unsound — the word "X" carries different meanings in premises one and two. In premise one, X is a *requirement*: a set of constraints, behaviors, and boundaries that the solution must satisfy. In premise two, X is a *label*: a marketing term, a category, an aspiration encoded in a README. The middle term is equivocal, and the syllogism collapses.

When a voice application needed silence detection, the instinct was to implement it as an FSM action — because "it's part of the state machine":

> An FSM action polling `time.monotonic()` is performing a real-time DSP job. If <50% of the silence-detection logic benefits from FSM context, it belongs in an audio worker, not in a YAML action.

The name of the existing container — the FSM action — attracted the new concern like a magnet. The container's name described the new concern closely enough that the mismatch in *mechanism* went unexamined. The framework wore the costume of the solution, and the team dressed it without noticing.

---

## III. Where the Boundary Breaks

The `framework_costume` trap is a boundary violation — but not in the data plane. It occurs at the *decision boundary*, the moment where a natural-language problem description is translated into a tooling choice.

The problem description enters as prose: "We need an agent." "We need silence detection." "We need a pipeline node." This prose is external data. It arrives from a product requirement, a user complaint, a spike debrief. It carries the vocabulary of the problem domain, not the vocabulary of the solution domain. And like all external data, it must be normalized at entry — translated from what the problem *is called* into what the problem *requires*.

When that normalization is skipped, the name passes through raw. Developers build downstream of the broken boundary, addressing the name of the need rather than its substance. The Agent SDK spike is the canonical example: the need was "a tool-calling loop with two Python functions." The name was "an agent." The name pointed to an external framework. The need pointed to an existing node type.

The pipeline template entry makes the boundary violation explicit:

> Compile-time expansion is the cleanest form of normalizing at the boundary. The pipeline YAML is the external input; `expand_pipelines()` is the boundary function; everything downstream sees only standard nodes and edges.

The fix — expanding pipeline nodes at compile time rather than orchestrating them at runtime — is a boundary normalization. The YAML author writes `type: pipeline` (the name). The compiler translates it into concrete nodes and edges (the mechanism). The runtime never sees the costume; it sees only what LangGraph already knows how to execute.

---

## IV. The Cure: Three Gates Before Code

The Knowledge Graph prescribes `ask_before_generate` as the cure for `framework_costume`. The definition is deceptively simple: *"Before writing code, ask: who solved this before? What don't I understand? Is this the right question?"*

These are three gates, and they must be traversed in order.

**Gate 1: Who solved this before?** This is the inward search. Before evaluating any external framework, audit the existing system's capabilities. The Agent SDK spike failed this gate — the team researched the SDK extensively but "didn't audit our own node type registry." The diary's verdict is unsparing: "The root cause was searching outward before searching inward."

**Gate 2: What don't I understand?** This is the admission of ignorance. The FSM bridge extraction (FR-346) encountered this gate when early drafts tried to unify two action types under a shared class hierarchy:

> These two actions share a name but not a contract: one is synchronous from FSM's perspective (fork + wait), the other is fire-and-forget (asyncio task + guard key). Recognising this as `false_duplicate` kept Phase 1 cleanly scoped.

The name "action" suggested unity. The contracts demanded separation. Gate 2 forced the distinction: *what don't I understand about these two things that share a name?* The answer — different ownership models, different lifecycle guarantees — killed the premature abstraction.

**Gate 3: Is this the right question?** This is the reframing. The Watcher2 sweet-spot reflection demonstrates it:

> The watcher pipeline is a production line — it excels when the shape of the output is known and the work is filling in details. Architectural work is exploration — the output shape is unknown, rewrites are signal not waste.

The original question was "How do we route architectural work through the watcher pipeline?" Gate 3 reframed it: "Should we?" The answer was no — architectural work and enforcement work have different shapes, different failure semantics, different exit conditions. Forcing both through the same pipeline was the `framework_costume` trap applied to process, not just code.

The three gates are mechanical, not intellectual. They require no genius, no intuition, no deep expertise. They require only discipline: the willingness to pause before the name completes the syllogism.

---

## V. The Cargo Cult Variant

The enforce pipeline simplification (FR-183) reveals a variant of the trap: the cargo cult costume. The team had built a seven-node pipeline with a Reflexion loop — a critique node feeding back into a refine node, controlled by loop limits and conditional edges. It looked sophisticated. It was dead code:

> The Reflexion loop between critique→refine nodes was never functional because copilot nodes return strings, not structured objects with `.score` fields. The 7-node design was over-engineered — the loop_limits and loop_exits config were cargo cult patterns copied without understanding the underlying limitation.

The diary names the trap precisely: *"loop config wearing functional-loop costume → if the routing condition can never fire, delete the config."* This is `framework_costume` applied not to tool selection but to tool *configuration*. The framework was correct (LangGraph supports conditional loops). The configuration was copied from an example that used a different node type. The config's name — "loop" — matched the intent — "iterative refinement" — and nobody checked whether the data types were compatible.

The four-node replacement was "honest: no loops, no routing conditions, no dead branches." Honesty, in this context, means the configuration describes what actually happens, not what the designer hoped would happen. The costume was stripped. What remained was a linear pipeline that matched its own execution trace.

---

## VI. The Watcher as Mirror

The most sustained engagement with `framework_costume` concerns Watcher2 — the autonomous development pipeline that grew into a 554-line state machine implemented in the wrong language:

> Watcher2 is a state machine (inbox → processing → worktree → plan → research → test → judge → enforce → merge → cleanup) implemented as a 554-line linear bash script with ad-hoc state variables instead of explicit states and transitions. Bash provides no structured error propagation, no typed state, no testable transitions.

The heuristic is blunt: *"500 lines of shell is a system, not a script."* The deeper observation is about how the costume accumulated incrementally. Nobody decided to implement a state machine in bash. The script started as a loop that processed inbox items. A worktree management phase was added. Then a planning phase. Then CI remediation. Each addition was locally justified. The aggregate shape — a multi-phase orchestrator with error recovery, state persistence, and diagnostic needs — was never evaluated against the medium it inhabited.

The diary's evidence is forensic:

> Bug 1: `cd "$WT_DIR"` mutated cwd, causing relative path resolution failure. Bug 2: Same root cause, different manifestation. Bug 3: ERR trap reports line 554 (`done`), actual failure is upstream — bash gives no stack trace, no variable dump, no structured diagnostics.

Three bugs. Same root cause. The medium cannot express the system's actual constraints. Less than 50% of the system's needs are served by the tool's strengths. The costume has slipped.

---

## VII. What the Trap Reveals

The `framework_costume` trap, traced across the diary, reveals something uncomfortable about how developers select their tools.

The default mode is not evaluation. It is *recognition*. A problem arrives with a name. The name activates a category. The category suggests a tool. The tool is selected before the problem's actual constraints are enumerated. This is not stupidity; it is the ordinary operation of a mind optimized for speed over accuracy. Pattern matching is fast. Constraint analysis is slow. In the absence of a forcing function, speed wins.

The cure is not better names. Names will always be approximate, always carry meanings beyond their referents, always suggest false kinships between unlike things. The cure is the discipline to distrust names — to hold the question open one moment longer than feels natural, to check whether the tool's mechanism matches the problem's constraints rather than whether the tool's label matches the problem's description.

The Agents' Prayer contains the operative line: *"When I feel certain, let that be the sign to Judge."* Certainty is the feeling that the name has been matched, that the category is correct, that the tool is obvious. Certainty is a *signal* — a signal to pause, to examine, to ask the three questions one more time.

Who solved this before? What don't I understand? Is this the right question?

Three hundred and eighty-nine lines could have been zero. The costume was convincing. The cure is three gates and the patience to walk through them.
