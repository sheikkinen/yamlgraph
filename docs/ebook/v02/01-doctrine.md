# Chapter 01: Doctrine — The Scripture Decoded

*From the YAMLGraph Development Pipeline eBook*

---

## 1. Why Codified Doctrine?

When AI agents collaborate with humans on a codebase, the absence of explicit rules creates drift: agents invent patterns, humans override them, and the project fractures into competing conventions. Codified doctrine solves this by establishing immutable constraints that both agents and humans obey equally — not as suggestions, but as executable law. As the opening line of `.github/copilot-instructions.md` declares: *"This document is executable doctrine: violations are defects, not suggestions."* Agents need constraints to prevent hallucinated architecture; humans need guardrails to resist expediency. The Scripture provides both.

---

## 2. The 10 Commandments

The Scripture defines ten commandments that govern all development activity in YAMLGraph. Each commandment is quoted verbatim below, followed by its core principle and a concrete example from the codebase.

### Commandment 1

> As defined in `.github/copilot-instructions.md`:
>
> **1. Thou shalt research before coding** — Let infinite agents explore deep and wide; distill their wisdom into constraints, for the cheapest code is unwritten code. When the domain is broad, invoke structured ideation to cross capabilities with constraints and surface non-obvious directions.

**Principle:** The cheapest line of code is the one you never write — research first to discover what already exists and what constraints apply.

**Example:** Before implementing URL-based prompt loading, the team researched deployment patterns and discovered that documenting volume mounts, git-sync, and ConfigMaps solved the problem without any new framework code. The result was `reference/prompt-deployment.md` instead of a 2-day feature. As `CLAUDE.md` notes: *"Documenting patterns is cheaper than new code."*

---

### Commandment 2

> As defined in `.github/copilot-instructions.md`:
>
> **2. Thou shalt demonstrate with example** — Never explain abstractly; show working code.

**Principle:** Working code is the only valid form of explanation — abstract descriptions invite misinterpretation.

**Example:** The `examples/` directory contains runnable demos for every major feature. The quickstart in `.github/copilot-instructions.md` itself leads with executable commands: `yamlgraph graph lint examples/demos/hello/graph.yaml` followed by `yamlgraph graph run` — not a paragraph of explanation, but a command you can paste and run.

---

### Commandment 3

> As defined in `.github/copilot-instructions.md`:
>
> **3. Thou shalt not utter code in vain** — Keep configuration separate and validated, for code is logic and config is truth.

**Principle:** Logic belongs in code; truth belongs in configuration — mixing them creates systems that can neither be reasoned about nor safely changed.

**Example:** All prompts live in `prompts/*.yaml` files, never hardcoded in Python. As `CLAUDE.md` enforces:

```python
# ❌ WRONG - Never hardcode prompts
llm.invoke("Write a summary of {topic}")

# ✅ CORRECT - Use YAML prompts
from yamlgraph.executor import execute_prompt
result = execute_prompt("summarize", {"topic": topic})
```

---

### Commandment 4

> As defined in `.github/copilot-instructions.md`:
>
> **4. Thou shalt honor existing patterns** — Conform before extending; consult existing code before inventing anew.

**Principle:** Consistency is more valuable than cleverness — always check what patterns already exist before creating new ones.

**Example:** The `node_factory/` modules follow a uniform pattern: every node function performs pre-checks, loop protection, resume support, execution, and returns a state update dict. New node types must conform to this same five-step flow documented in `CLAUDE.md` rather than inventing their own lifecycle.

---

### Commandment 5

> As defined in `.github/copilot-instructions.md`:
>
> **5. Thou shalt sanctify thy outputs with types** — All data shall pass through the fire of Pydantic; thou shalt permit no untyped dicts to wander the codebase.

**Principle:** Every piece of data flowing through the system must have a validated type — untyped dictionaries are forbidden.

**Example:** LLM outputs are validated through either inline YAML schemas or Pydantic models in `yamlgraph/models/schemas.py`. The anti-patterns table in `CLAUDE.md` marks "Untyped dicts" as wrong and "Pydantic models or inline YAML schemas" as the correct alternative.

---

### Commandment 6

> As defined in `.github/copilot-instructions.md`:
>
> **6. Thou shalt bear witness of thy errors** — Hide nothing; expose every fault to `ruff` and to CI, for what is hidden in commit shall be revealed in production. Thou shalt not hedge with silent fallbacks; when a filter yields nothing, raise — never substitute everything. A plausible wrong answer is harder to catch than a crash.

**Principle:** Errors must be loud and visible — silent fallbacks and swallowed exceptions are more dangerous than crashes because they produce plausible but wrong results.

**Example:** The error handling pattern in `CLAUDE.md` requires wrapping failures in `PipelineError.from_exception()` and appending them to the state's `errors` list. The anti-patterns table explicitly forbids "Silent exceptions." Even `# noqa` suppressions require a documented confession in `docs/confessions.md` with a CONF-XXX ID.

---

### Commandment 7

> As defined in `.github/copilot-instructions.md`:
>
> **7. Thou shalt be faithful to TDD** — Red-Green-Refactor; run `pytest` with every change. No bug shall be fixed unless first condemned by a failing test.

**Principle:** No code changes without a test that proves the need — write the failing test first, then make it pass, then refactor.

**Example:** Every test function carries a `@pytest.mark.req("REQ-YG-XXX")` marker linking it to a requirement in `ARCHITECTURE.md`. The `scripts/req_coverage.py` script verifies complete traceability. `CLAUDE.md` provides the testing commands: `pytest tests/unit/ -q --no-cov` for fast iteration, `pytest tests/ -q` for full coverage.

---

### Commandment 8

> As defined in `.github/copilot-instructions.md`:
>
> **8. Thou shalt kill all entropy and false idols** — Split modules before they bloat; feed the dead to `vulture`; burn duplicates with `jscpd`; sanctify with `radon`. Thou shalt measure structural drift, not only passing checks. Green correctness without entropy context is incomplete truth. No shims, no adapters, no "compat" flags shalt thou tolerate. Delete dead code; record significant removals in commit notes.

**Principle:** Passing tests are necessary but insufficient — structural health (module size, duplication, complexity, dead code) must be actively measured and maintained.

**Example:** `CLAUDE.md` enforces a module size limit: "Target < 400 lines, max 450 (split into submodules if exceeded)." The anti-patterns table marks "Files > 400 lines" as wrong with "Refactor into submodules" as the correction. The convention of Conventional Commits ensures significant removals are recorded: `feat(streaming): FR-030 add subgraphs parameter`.

---

### Commandment 9

> As defined in `.github/copilot-instructions.md`:
>
> **9. Thou shalt define and observe operational truth** — Establish measurable service objectives; instrument and trace execution; treat performance degradation, failure rates, and evaluation drift as production defects. No incident shall be closed without cited traces in LangSmith and recorded rationale in `feature-requests/`.

**Principle:** Observability is not optional — every production behavior must be measurable, traceable, and linked to documented rationale.

**Example:** The `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, and `LANGCHAIN_PROJECT` environment variables in `CLAUDE.md` enable LangSmith observability. Performance regressions and evaluation drift are treated as production defects, and incidents must cite LangSmith traces before they can be closed.

---

### Commandment 10

> As defined in `.github/copilot-instructions.md`:
>
> **10. Thou shalt preserve and improve the doctrine** — Every failure shalt refine the law. After correction, amend tests and linters to guard against recurrence; let success be codified, and let the CHANGELOG.md bear witness to the evolution of the Word.

**Principle:** The doctrine itself evolves — every failure becomes a new test, every insight becomes a new rule, and `CHANGELOG.md` records the evolution.

**Example:** The Knowledge Graph of the Diary (Section 4 below) was "graduated from recurring diary patterns." Heuristics that proved recurring in `docs/diary.md` were promoted into the Scripture itself, demonstrating the living evolution of doctrine.

---

## 3. The Sermon of the Chaplain

The Sermon defines the seven-phase workflow that governs all feature development. Each phase has a specific purpose and exit criteria.

> As defined in `.github/copilot-instructions.md`:
>
> **Research.** Let agents scour competing systems and return with truth. Distill best practices and viable alternatives into explicit constraints.
>
> **Plan.** Write the feature request in `feature-requests/`. Define objectives, constraints, acceptance criteria, and implementation approach. The feature request is the plan.
>
> **Judge.** Critically examine the feature request; resolve contradictions; eliminate ambiguity; refine constraints and acceptance criteria until the path is explicit and minimal. If clear, minimal, and internally consistent, freeze scope and grant authority.
>
> **Enforce.** Obey the Judgement. Write the failing test first; make only the smallest sufficient change; refactor only within scope. Update the feature request with implementation status and decisions.
>
> **Purge.** Remove invented interfaces, speculative flags, and hypothetical extensibility. If it is not required and not tested, it shall not exist.
>
> **Submit.** Bump. Commit. Push. Release. Tag. Let CI judge. What survives the fire may merge.
>
> **Distill.** After completing a task list, add a metacognitive entry to `docs/diary.md`. Name the cognitive trap or insight. Extract a heuristic. Plant a **Seed:** — a forward-looking question to grow new ideas. If the heuristic proves recurring, graduate it to this Scripture.

The Sermon is not a suggestion — it is the mandatory sequence. **Research** prevents reinvention. **Plan** forces explicit scope. **Judge** eliminates ambiguity before a single line of code is written. **Enforce** is pure TDD execution under the frozen scope. **Purge** removes everything that wasn't required. **Submit** lets CI deliver the final verdict. **Distill** captures what was learned so the doctrine evolves.

The critical insight: most development failures happen because teams skip Judge and jump from Plan to Enforce. The Sermon makes judgement an explicit, mandatory phase.

---

## 4. The Knowledge Graph

The Knowledge Graph was graduated from recurring patterns observed in `docs/diary.md`. It encodes the single most important heuristic the team has discovered:

> As defined in `.github/copilot-instructions.md`:
>
> *Graduated from recurring diary patterns. The causal chain from trap to cure:*
>
> ```yaml
> the_one_law: |
>   Normalize at the boundary where external data enters,
>   not downstream where it manifests.
>
> boundaries: [schema, provider, state, streaming, platform]
> traps: [quick_confidence, downstream_fix, symptom_patch, intent_drift]
> ```

**The One Law** states that data must be normalized where it enters the system — not where problems appear. When an LLM provider returns data in an unexpected format, the fix belongs at the provider boundary (in `executor.py` or the LLM factory), not in the downstream node that happens to crash.

The **boundaries** enumerate the five normalization points: schema validation, provider abstraction, state management, streaming interfaces, and platform integration.

The **traps** name four cognitive biases that cause developers to violate The One Law:

- **quick_confidence**: Feeling certain after a superficial fix
- **downstream_fix**: Patching where the symptom appears instead of where the data enters
- **symptom_patch**: Treating the visible error instead of the root cause
- **intent_drift**: Gradually expanding scope beyond the original objective

---

## 5. The Rite of Correction

When something breaks, the Scripture prescribes a three-phase correction protocol:

> As defined in `.github/copilot-instructions.md`:
>
> **Inspect.** Assume nothing; audit the codebase; trace failures to file and line; expose violated constraints and missing tests.
>
> **Amend.** Write the failing test first. Correct the root cause second.
>
> **Escalate.** If amendment is impossible, write the feature request in `feature-requests/`. Cite traces. Define the violated objective. Propose the new constraint. Return to Plan.

**Inspect** demands that you trace the failure to its exact location — no assumptions, no guesses. **Amend** follows the TDD mandate: the failing test comes first, proving the bug exists, and only then is the root cause corrected. **Escalate** provides an escape hatch for systemic issues: if the fix requires architectural change, you don't hack around it — you write a feature request, cite your evidence, and return to the Sermon's Plan phase.

The Rite ensures that corrections are never ad-hoc patches. Every bug fix strengthens the test suite, and every systemic issue gets the full planning treatment.

---

## 6. The Agents' Prayer

The prayer is recited as a set of operating principles for every agent — human or AI — working in the codebase:

> As defined in `.github/copilot-instructions.md`:
>
> May I fix at the callsite, not the utility.
> May I kill the cheapest bug — the one in the spec.
> May I normalize at the boundary, trusting no provider's type.
> May I stream to reveal what batch conceals.
> May I understand every protection before I pass it.
> May I read thrice before I grant authority.
>
> When hooks feel slow, let that be the sign they guard.
> When I feel certain, let that be the sign to Judge.
>
> What survives the fire may merge.

Each line encodes a hard-won lesson:

- **Fix at the callsite** — don't modify shared utilities to fix one caller's problem.
- **Kill the cheapest bug** — a bug in the spec costs nothing to fix compared to a bug in production code.
- **Normalize at the boundary** — The One Law in prayer form.
- **Stream to reveal** — streaming exposes timing and ordering bugs that batch execution hides.
- **Understand every protection** — don't bypass guards you don't understand.
- **Read thrice before granting authority** — review plans three times before approving implementation.
- **Hooks feel slow** — pre-commit hooks and CI checks feel like friction, but they are guards.
- **Feeling certain** — certainty is the signal to pause and Judge, not to proceed.
- **What survives the fire may merge** — CI is the final arbiter; nothing bypasses it.

---

## 7. Why This Matters

Doctrine is not ceremony — it is the immune system of a codebase. Without explicit rules, AI agents hallucinate architecture, humans take shortcuts, and every contributor pulls the project in a different direction. The Scripture prevents this drift by making expectations executable: `ruff` enforces style, `pytest` enforces correctness, `req_coverage.py` enforces traceability, and pre-commit hooks enforce discipline.

The deeper value is that doctrine enables collaboration at scale. When an AI agent reads the Scripture, it knows exactly how to behave: research before coding, use the factory instead of direct imports, validate with Pydantic, test first. When a human reads the Scripture, they know exactly what to expect from both the agent and the codebase. The rules are the same for everyone.

What survives the fire may merge.

---

*Sources: `.github/copilot-instructions.md` (The Scripture), `CLAUDE.md` (Development Commands and Anti-Patterns)*


