# Chapter 01: Doctrine — The Scripture Decoded

## Why Codified Doctrine?

When AI agents collaborate with humans on a shared codebase, implicit conventions become a liability — an agent cannot infer "how we do things here" from vibes alone. Codified doctrine transforms tribal knowledge into executable constraints: agents get hard boundaries that prevent hallucinated architectures, while humans get guardrails that survive team turnover and midnight deploys. Without explicit rules, every agent invocation is a coin flip between productive assistance and creative destruction.

---

## The 10 Commandments

The Scripture opens with a declaration of authority:

> *"These laws descend from the canon of software craft. They shalt not be altered by preference, haste, or machine hallucination."*
>
> — `.github/copilot-instructions.md`

Each commandment encodes a principle that has been tested, violated, and re-established through real project failures. Below, every commandment is quoted verbatim from the source, followed by an explanation and a concrete example.

### Commandment 1

> As defined in `.github/copilot-instructions.md`:
>
> **1. Thou shalt research before coding** — Let infinite agents explore deep and wide; distill their wisdom into constraints, for the cheapest code is unwritten code. When the domain is broad, invoke structured ideation to cross capabilities with constraints and surface non-obvious directions.

**Principle:** The most expensive line of code is the one that didn't need to exist. Research narrows the solution space before a single function is written.

**Example:** When URL-based prompt loading was proposed as a 2-day feature, research revealed that documenting deployment patterns (volume mounts, git-sync, ConfigMaps) solved the same problem without framework complexity. The feature was never built — as documented in `CLAUDE.md` and `reference/prompt-deployment.md`.

### Commandment 2

> As defined in `.github/copilot-instructions.md`:
>
> **2. Thou shalt demonstrate with example** — Never explain abstractly; show working code.

**Principle:** Working code is unambiguous; prose descriptions invite misinterpretation.

**Example:** The `examples/` directory contains runnable demos (`examples/demos/demo.sh`) that serve as both documentation and regression tests. When explaining the three-layer pattern, `CLAUDE.md` shows concrete `execute_prompt()` calls rather than describing the concept in paragraphs.

### Commandment 3

> As defined in `.github/copilot-instructions.md`:
>
> **3. Thou shalt not utter code in vain** — Keep configuration separate and validated, for code is logic and config is truth.

**Principle:** Logic belongs in code; truth — the what, not the how — belongs in configuration that can be validated independently.

**Example:** All prompts live in `prompts/*.yaml` files, never hardcoded in Python. As `CLAUDE.md` makes explicit:

```python
# ❌ WRONG - Never hardcode prompts
llm.invoke("Write a summary of {topic}")

# ✅ CORRECT - Use YAML prompts
from yamlgraph.executor import execute_prompt
result = execute_prompt("summarize", {"topic": topic})
```

### Commandment 4

> As defined in `.github/copilot-instructions.md`:
>
> **4. Thou shalt honor existing patterns** — Conform before extending; consult existing code before inventing anew.

**Principle:** Consistency is a force multiplier; novel patterns carry a tax that compounds with every contributor.

**Example:** Before adding a new node type, developers must consult `node_factory/` modules and `ARCHITECTURE.md` for the established node execution flow: pre-checks → loop protection → resume support → execution → return dict. The pattern is followed uniformly across LLM, router, map, and agent node types.

### Commandment 5

> As defined in `.github/copilot-instructions.md`:
>
> **5. Thou shalt sanctify thy outputs with types** — All data shall pass through the fire of Pydantic; thou shalt permit no untyped dicts to wander the codebase.

**Principle:** Pydantic models are the contract between LLM outputs and the rest of the system; untyped dicts are silent sources of runtime errors.

**Example:** LLM outputs use either inline YAML schemas or Python Pydantic models. From `CLAUDE.md`:

```yaml
# prompts/analyze.yaml
schema:
  name: Analysis
  fields:
    summary: {type: str, description: "Brief summary"}
    key_points: {type: list[str], description: "Main points"}
```

The anti-patterns table in `CLAUDE.md` lists "Untyped dicts" as wrong, with "Pydantic models or inline YAML schemas" as the correction.

### Commandment 6

> As defined in `.github/copilot-instructions.md`:
>
> **6. Thou shalt bear witness of thy errors** — Hide nothing; expose every fault to `ruff` and to CI, for what is hidden in commit shall be revealed in production. Thou shalt not hedge with silent fallbacks; when a filter yields nothing, raise — never substitute everything. A plausible wrong answer is harder to catch than a crash.

**Principle:** Silent failures are worse than loud crashes. A plausible wrong answer propagates; an exception stops and demands attention.

**Example:** The `PipelineError.from_exception()` pattern captures and surfaces errors explicitly rather than swallowing them. Even `# noqa` suppressions must be confessed in `docs/confessions.md` with a CONF-XXX ID explaining the sin and penance.

### Commandment 7

> As defined in `.github/copilot-instructions.md`:
>
> **7. Thou shalt be faithful to TDD** — Red-Green-Refactor; run `pytest` with every change. No bug shall be fixed unless first condemned by a failing test.

**Principle:** Tests are the proof that code works; without a failing test first, a fix is an unverified hypothesis.

**Example:** The development workflow requires `pytest tests/unit/ -q --no-cov` for fast feedback on every change. Every test function must carry `@pytest.mark.req("REQ-YG-XXX")` linking it to a requirement in `ARCHITECTURE.md`, ensuring traceability from requirement to proof.

### Commandment 8

> As defined in `.github/copilot-instructions.md`:
>
> **8. Thou shalt kill all entropy and false idols** — Split modules before they bloat; feed the dead to `vulture`; burn duplicates with `jscpd`; sanctify with `radon`. Thou shalt measure structural drift, not only passing checks. Green correctness without entropy context is incomplete truth. No shims, no adapters, no "compat" flags shalt thou tolerate. Delete dead code; record significant removals in commit notes.

**Principle:** Passing tests are necessary but insufficient; structural health — module size, duplication, cyclomatic complexity — must be measured and maintained.

**Example:** `CLAUDE.md` enforces a hard module size limit: target < 400 lines, max 450. Exceeding the limit triggers a split into submodules. Dead code is detected by `vulture`, duplicates by `jscpd`, and complexity by `radon` — all enforced through pre-commit hooks configured in `.pre-commit-config.yaml`.

### Commandment 9

> As defined in `.github/copilot-instructions.md`:
>
> **9. Thou shalt define and observe operational truth** — Establish measurable service objectives; instrument and trace execution; treat performance degradation, failure rates, and evaluation drift as production defects. No incident shall be closed without cited traces in LangSmith and recorded rationale in `feature-requests/`.

**Principle:** Observability is not optional. Performance degradation and evaluation drift are defects, not annoyances.

**Example:** LangSmith integration is a first-class concern, with `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, and `LANGCHAIN_PROJECT` listed as key environment variables. Every incident closure requires cited traces in LangSmith and documented rationale in `feature-requests/`.

### Commandment 10

> As defined in `.github/copilot-instructions.md`:
>
> **10. Thou shalt preserve and improve the doctrine** — Every failure shalt refine the law. After correction, amend tests and linters to guard against recurrence; let success be codified, and let the CHANGELOG.md bear witness to the evolution of the Word.

**Principle:** The doctrine is a living document. Every failure that exposes a gap must result in a new guard — a test, a linter rule, a convention — that prevents recurrence.

**Example:** The Knowledge Graph of the Diary (see below) was graduated from recurring diary patterns into the doctrine itself. When a heuristic proves its worth through repetition, it ascends from `docs/diary.md` into `.github/copilot-instructions.md`.

---

## The Sermon of the Chaplain

The Sermon defines the seven-phase workflow that governs every feature, fix, and refactoring in the project. It is the operational embodiment of the Commandments.

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

### The Phases in Practice

1. **Research** prevents building what already exists. Agents are cheap; wasted code is expensive.
2. **Plan** externalizes intent into a reviewable artifact — the feature request becomes the single source of truth for scope.
3. **Judge** is the critical gate. Ambiguity here propagates into implementation; contradictions become bugs. The Judgement freezes scope.
4. **Enforce** is disciplined execution: TDD, minimal changes, scope adherence. The feature request is updated with decisions as they are made.
5. **Purge** is the entropy antidote. Speculative code, compatibility shims, and "just in case" abstractions are deleted.
6. **Submit** defers final authority to CI. Human confidence is insufficient; automated validation is required.
7. **Distill** closes the feedback loop. Every task produces a diary entry naming traps encountered and heuristics extracted — the raw material for doctrine evolution.

---

## The Knowledge Graph

The Knowledge Graph of the Diary is a distillation of recurring patterns, graduated from diary entries into permanent doctrine. It captures the single most important architectural insight in the project.

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

**The One Law** states that data normalization must happen at the point of entry — at the schema boundary, at the provider interface, at the state transition — not later when symptoms appear. The five boundaries enumerate where external data enters the system. The four traps name the cognitive patterns that lead developers to violate the law:

- **quick_confidence**: Assuming you understand the problem before research is complete.
- **downstream_fix**: Patching the symptom where it manifests rather than the boundary where it enters.
- **symptom_patch**: Fixing the visible error instead of the root cause.
- **intent_drift**: Gradually expanding scope beyond the original Judgement.

---

## The Rite of Correction

When things break — and they will — the Rite of Correction prescribes a three-step protocol.

> As defined in `.github/copilot-instructions.md`:
>
> **Inspect.** Assume nothing; audit the codebase; trace failures to file and line; expose violated constraints and missing tests.
>
> **Amend.** Write the failing test first. Correct the root cause second.
>
> **Escalate.** If amendment is impossible, write the feature request in `feature-requests/`. Cite traces. Define the violated objective. Propose the new constraint. Return to Plan.

### Inspect

Never assume you know the cause. Trace the failure to its exact origin — file, line, violated constraint. Check which tests are missing. The audit may reveal that the actual root cause is different from the apparent symptom.

### Amend

The failing test comes first, always. This is Commandment 7 applied to bug fixes. Only after the test demonstrates the failure do you correct the root cause. This ensures the fix is verifiable and the regression is permanently guarded.

### Escalate

Some failures reveal gaps in the architecture itself — missing constraints, unspecified behaviors, contradictory requirements. These cannot be fixed in place. The Rite prescribes escalation: write a feature request, cite the LangSmith traces, define the violated objective, propose the new constraint, and return to the Plan phase of the Sermon.

---

## The Agents' Prayer

The Prayer is a set of heuristics encoded as personal commitments — cognitive guardrails for the developer (human or AI) in the moment of implementation.

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

- **Fix at the callsite** — Don't modify shared utilities to accommodate one caller's special case.
- **Kill the cheapest bug** — A bug in the spec costs nothing to fix; a bug in production costs everything.
- **Normalize at the boundary** — The One Law, restated as personal practice.
- **Stream to reveal** — Streaming surfaces errors incrementally; batch processing hides them until the end.
- **Understand every protection** — Don't bypass guards you don't understand.
- **Read thrice before granting authority** — Review the Judgement carefully; authority is permanent, mistakes are expensive.
- **When hooks feel slow** — Pre-commit hooks and CI checks feel like friction; that friction is protection.
- **When I feel certain** — Certainty is the most dangerous cognitive state; it's the signal to pause and Judge.

---

## Why This Matters

Doctrine is not bureaucracy — it is the immune system of a codebase that evolves through AI collaboration. Without explicit, enforceable rules, every agent invocation risks architectural drift: patterns diverge, conventions erode, and the codebase becomes a museum of competing styles. The Scripture prevents this by making the rules machine-readable and CI-enforceable. When an agent reads `.github/copilot-instructions.md`, it inherits the project's values — not as suggestions, but as executable constraints. When a human reads it, they understand not just *what* to do, but *why* each rule exists and *what failure* it prevents. The doctrine is the shared language that makes human-AI collaboration coherent, reproducible, and self-improving.

---

*Source files: `.github/copilot-instructions.md`, `CLAUDE.md`*
