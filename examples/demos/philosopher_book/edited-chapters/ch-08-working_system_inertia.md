# Chapter 8: It Works, Therefore I Cannot See It

---

## I. The Parish of One

On May 11, 2026, someone asked a question that shouldn't have been difficult: can the Chaplain — the autonomous governance system that plans, judges, and enforces changes — process an inbox entry for `ninchat_voice`?

The answer was no. Not "not yet." Not "with a small configuration change." Simply no.

The Chaplain could not create worktrees in that project. It could not run its tests, open pull requests against its repository, or apply its pre-commit hooks. It governed exactly one project — the project inside which it lived — and it governed that project perfectly.

The diary entry that day traced the coupling through five structural layers, each one locally rational:

> *Layer 1: The worktree is a git worktree of the yamlgraph repo.*
> *Layer 2: The `.venv` symlink assumes one Python environment.*
> *Layer 3: The validate gate runs yamlgraph's test suite.*
> *Layer 4: The pipeline invokes `yamlgraph graph run`.*
> *Layer 5: The PRs target the yamlgraph GitHub repository.*

Five assumptions, each invisible, each correct for the one case that existed. And then the observation that makes the story sting:

> *`ninchat_voice` is the highest-fidelity user of the yamlgraph framework. It runs in production. It has healthcare domain logic with IEC 62304-adjacent traceability needs. It generates the most change volume. And it receives zero Chaplain automation.*

The project with the greatest governance need was the one the governance system could not reach. The Chaplain worked — and that was the problem. Its working state was a wall between the builders and their blindness.

This is the trap called `working_system_inertia`: *"'It works' blocks seeing it clearly."*

---

## II. The Evaluation Boundary

The Knowledge Graph codifies a single structural principle from which all boundary violations descend:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

The trap `working_system_inertia` violates this law not at the data boundary but at the *evaluation boundary*. We check "does it produce correct output?" — a downstream manifestation — instead of "is it correct at its architectural boundary?" — an entry-point judgment.

In March 2026, the `extract_answers()` function in `probe_recap.py` called `execute_prompt()` directly from a Python tool node. It worked. The LLM returned structured answers. The pipeline completed. But it violated the three-layer architecture — LLM calls belong in YAML graphs, not Python tools — and that violation was invisible to graph-level observability. The diary noted:

> *The code worked, so the structural defect was tolerated. OC-012 added a `metadata: provider: google` guard as a stopgap. FR-178 was needed to remove the root cause.*

The guard was a downstream fix. The root cause was the LLM call inside a tool. Normalizing at the layer boundary — converting from `type: python` to `type: llm` in the graph YAML — made the call visible and auditable. The code had worked before the fix. The code worked after. The difference was not in the output but in the *legibility of the system to itself*.

The Chaplain's single-parish coupling is the same violation at the system level. Evaluated at the output boundary: "Does it govern yamlgraph correctly?" Yes. Evaluated at the architectural boundary: "Does it govern projects?" No. It governs *one* project, through five layers of hardcoded assumptions that are invisible precisely because the output is correct.

The race node (FR-270) showed the violation in its most quantifiable form. A `with ThreadPoolExecutor` context manager returned correct results. All assertions passed. But:

> *The `with` pattern looks correct and idiomatic Python. It wasn't obviously wrong until measured — `max(candidates)` wall clock vs `min(candidates)`. The race node worked (correct results), but silently degraded performance to the slowest candidate, making it useless as a latency hedge.*

The output boundary said "correct results." The architectural boundary said "this is a race node that never races." Evaluating at the wrong boundary concealed a defect that made the component functionally useless for its stated purpose.

---

## III. Inventory Fit, Not Function

The cure the Knowledge Graph prescribes is deceptively simple: *"inventory fit, not function."* But the word *inventory* is doing enormous work.

To inventory function, you run the tests. Green means working. This is the evaluation that creates the trap — it answers the wrong question with a true answer.

To inventory fit, you ask: Does this component sit at the right architectural boundary? Does it accommodate future change without modification? Does it impose coupling that constrains unrelated components? Does it serve the scope it claims to serve, or merely the scope that existed when it was written?

The three-reads cure from the Knowledge Graph maps these questions to escalating modes of perception:

**Surface read:** Does it work? (Function.) The tests pass, the output is correct. This read feels complete — and that is the trap.

**Deep read:** Does it belong here? (Structure.) FR-178's deep read revealed that a working LLM call sat in the wrong architectural layer. The god factory's deep read revealed that a fifteen-branch if/elif dispatch violated the Open-Closed Principle. The Chaplain's deep read revealed that a working governance system was hardcoded to a single project.

**Mechanical simulation:** What happens when you stress it? (Evolution.) When the Chaplain receives a `ninchat_voice` inbox entry. When the PYTHONPATH hack meets a directory layout change. When the race node's slow candidate determines overall latency. Mechanical simulation applies force to the assumptions that the surface read holds constant.

The May diary on prompt caching showed all three reads in action. The surface read: converting prompt files to `system_segments` passes YAML schema validation. The deep read: `type: copilot` nodes silently ignore `system_segments`, so the conversion would remove system instructions while appearing to succeed. The mechanical simulation: the system still "works" — no crash, just degraded prompts with missing context.

> *A broad conversion would have removed system instructions from every Copilot-backed node while appearing to succeed (no crash, just missing context).*

The cure inverted the question: not "which files can I convert?" but "which node types support `system_segments`?" The scope dropped from "all prompts" to one. The surface read's optimism was not wrong — it was *incomplete*.

---

## IV. The Inverted Case

In May 2026, a team frustrated with the copilot CLI's limitations reached for an external framework (Claude Agent SDK) to build a planning agent. The research was thorough. The spike was scoped. The code shipped. And then:

> *Human feedback: "there is agent keyword in yamlgraph. check." Found `type: agent` in `yamlgraph/tools/agent.py` — a full LangChain tool-calling loop that already supports python + shell tools, provider-independent, max_iterations, tool_results_key. The spike's 389 lines reimplemented what YAMLGraph already provides.*

Here the inertia ran in reverse. The team was so focused on what the existing system *lacked* that they failed to see what it already *provided*. The system worked, and that working state was invisible — not because it blocked seeing a defect, but because the assumption of inadequacy was never tested against the actual capability inventory.

This inversion reveals the deeper structure. The trap is not about complacency. It is not about laziness or insufficient testing. It is about the frame of evaluation itself. Function is the default measurement because it is concrete, binary, and falsifiable: does it work or doesn't it? Fit is relational, contextual, and comparative: does it belong here? Could it accommodate that? Should it serve this scope?

Function feels like the end of inquiry. Fit feels like the beginning. And beginnings are expensive. Working systems consume none of that budget, which means they receive none of that scrutiny.

---

## V. Seed

The Chaplain that governs one parish. The pipeline that flattens architecture into features. The race node that never races. The import hack that resolves the wrong module.

In every case, the system worked. In every case, the working state was the obstacle.

The cure — inventory fit, not function — demands something that no test suite can automate: the willingness to evaluate a successful system against criteria it was never built to satisfy. Not "does it produce correct output?" but "is this the right shape for what it has become?"

If every working system generates its own invisibility, what discipline would make that invisibility visible *before* a failure forces the question? The three reads offer a structure. The diary offers evidence that the structure works. But the first read — the surface read, the one that returns "it works" — is always the easiest, always the most satisfying, and always the one that tempts us to stop.

Why would you re-examine something that works?

The answer, perhaps, is that you wouldn't — until you've seen enough systems that worked perfectly right up to the moment they couldn't. And even then, the next working system will whisper the same thing: *it works, don't touch it.* The question is whether you can hear the whisper for what it is — not reassurance, but the sound of a question that was never asked.
