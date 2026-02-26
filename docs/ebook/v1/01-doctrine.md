# Chapter 01: Doctrine — The Scripture Decoded

*YAMLGraph Development Pipeline eBook — Volume 1*

---

## 1. Why Codified Doctrine?

When AI agents collaborate with humans on a codebase, implicit conventions collapse. An agent that "knows best practices" will hallucinate its own version of them — subtly different each time, drifting further from the project's intent with every session. Codified doctrine solves this by turning principles into executable constraints: agents receive explicit rules they cannot rationalize away, and humans receive guardrails that survive team turnover, fatigue, and the seductive shortcut. The YAMLGraph Scripture exists not because developers lack judgment, but because judgment alone does not scale across sessions, agents, and time.

---

## 2. The 10 Commandments

The Scripture opens with its most uncompromising section. These are not guidelines — they are laws. As the doctrine states: *"These laws descend from the canon of software craft. They shalt not be altered by preference, haste, or machine hallucination."*

Each commandment below is quoted verbatim from the canonical source.

### Commandment 1

> As defined in `.github/copilot-instructions.md`:
>
> **1. Thou shalt research before coding** — Let infinite agents explore deep and wide; distill their wisdom into constraints, for the cheapest code is unwritten code. When the domain is broad, invoke structured ideation to cross capabilities with constraints and surface non-obvious directions.

**Principle:** The most expensive line of code is the one that solves the wrong problem. Research first to define constraints, and the implementation often writes itself — or reveals itself to be unnecessary.

**Codebase example:** When URL-based prompt loading was proposed as a 2-day feature, research revealed that documenting deployment patterns (volume mounts, git-sync, ConfigMaps) solved the same problem without adding framework complexity. The result lives in `reference/prompt-deployment.md` — zero lines of production code.

---

### Commandment 2

> As defined in `.github/copilot-instructions.md`:
>
> **2. Thou shalt demonstrate with example** — Never explain abstractly; show working code.

**Principle:** Working code is the only trustworthy specification. Abstract descriptions of behavior hide ambiguity that examples expose.

**Codebase example:** The `examples/` directory contains runnable demos for every major feature — from `examples/demos/hello/graph.yaml` for basic graphs to `examples/npc/` for a full production application with HTMX integration and session adapters.

---

### Commandment 3

> As defined in `.github/copilot-instructions.md`:
>
> **3. Thou shalt not utter code in vain** — Keep configuration separate and validated, for code is logic and config is truth.

**Principle:** When logic and configuration intertwine, changing a prompt requires a code deploy. Separation means YAML authors can iterate without touching Python.

**Codebase example:** All prompts live in `prompts/*.yaml` files, never hardcoded in Python. The anti-pattern table in `CLAUDE.md` makes this explicit:

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| Hardcoded prompts in Python | YAML templates in `prompts/` |

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

**Principle:** Consistency compounds. Every novel pattern adds cognitive load for every future reader and every future agent session.

**Codebase example:** The Three-Layer Pattern documented in `CLAUDE.md` defines where every type of code belongs — Presentation (CLI/API), Logic (YAML Graphs), and Side Effects (Python Tools). New features conform to this architecture rather than inventing ad-hoc structures.

---

### Commandment 5

> As defined in `.github/copilot-instructions.md`:
>
> **5. Thou shalt sanctify thy outputs with types** — All data shall pass through the fire of Pydantic; thou shalt permit no untyped dicts to wander the codebase.

**Principle:** Untyped dictionaries are invisible contracts — they break silently, far from the source of the error. Pydantic models make the contract explicit and enforce it at runtime.

**Codebase example:** LLM outputs use either inline YAML schemas or Python Pydantic models in `yamlgraph/models/schemas.py`. The `GraphConfig` model validates every graph YAML at load time, catching schema errors before a single LLM call is made.

```yaml
# prompts/analyze.yaml — inline schema
schema:
  name: Analysis
  fields:
    summary: {type: str, description: "Brief summary"}
    key_points: {type: list[str], description: "Main points"}
```

---

### Commandment 6

> As defined in `.github/copilot-instructions.md`:
>
> **6. Thou shalt bear witness of thy errors** — Hide nothing; expose every fault to `ruff` and to CI, for what is hidden in commit shall be revealed in production. Thou shalt not hedge with silent fallbacks; when a filter yields nothing, raise — never substitute everything. A plausible wrong answer is harder to catch than a crash.

**Principle:** Silent failures are the most expensive kind. A crash is a gift — it tells you exactly where and when things went wrong. A silent fallback tells you nothing until production data is corrupted.

**Codebase example:** The `PipelineError.from_exception()` pattern captures errors explicitly in node state. The `# noqa` confession system in `docs/confessions.md` ensures that even linter suppressions are documented with a CONF-XXX ID, sin, and penance — no error is hidden without accountability.

---

### Commandment 7

> As defined in `.github/copilot-instructions.md`:
>
> **7. Thou shalt be faithful to TDD** — Red-Green-Refactor; run `pytest` with every change. No bug shall be fixed unless first condemned by a failing test.

**Principle:** A bug fix without a test is a future regression. The Red-Green-Refactor cycle ensures that every behavior change is captured in the test suite before it enters the codebase.

**Codebase example:** Every test function carries a `@pytest.mark.req("REQ-YG-XXX")` marker linking it to a requirement in `ARCHITECTURE.md`. The `scripts/req_coverage.py` script verifies that all requirements have corresponding tests — gaps are CI failures, not warnings.

---

### Commandment 8

> As defined in `.github/copilot-instructions.md`:
>
> **8. Thou shalt kill all entropy and false idols** — Split modules before they bloat; feed the dead to `vulture`; burn duplicates with `jscpd`; sanctify with `radon`. Thou shalt measure structural drift, not only passing checks. Green correctness without entropy context is incomplete truth. No shims, no adapters, no "compat" flags shalt thou tolerate. Delete dead code; record significant removals in commit notes.

**Principle:** Passing tests are necessary but insufficient. A codebase can be "correct" while rotting from within — bloated modules, dead code, duplicated logic. Entropy must be measured and killed continuously.

**Codebase example:** The code quality standards in `CLAUDE.md` enforce a hard module size limit: target < 400 lines, max 450, with mandatory splits into submodules when exceeded. The convention *"Term 'backward compatibility' is a key indicator for a refactoring need"* treats compatibility shims as technical debt, not features.

---

### Commandment 9

> As defined in `.github/copilot-instructions.md`:
>
> **9. Thou shalt define and observe operational truth** — Establish measurable service objectives; instrument and trace execution; treat performance degradation, failure rates, and evaluation drift as production defects. No incident shall be closed without cited traces in LangSmith and recorded rationale in `feature-requests/`.

**Principle:** Code that works in tests but degrades in production is not working code. Operational health is a first-class concern, not an afterthought.

**Codebase example:** LangSmith tracing is integrated via the `LANGCHAIN_TRACING_V2` environment variable. Every incident requires cited traces and a recorded rationale in `feature-requests/`, creating a permanent audit trail from production observation back to the code change that caused it.

---

### Commandment 10

> As defined in `.github/copilot-instructions.md`:
>
> **10. Thou shalt preserve and improve the doctrine** — Every failure shalt refine the law. After correction, amend tests and linters to guard against recurrence; let success be codified, and let the CHANGELOG.md bear witness to the evolution of the Word.

**Principle:** Doctrine is a living document. Every failure that escapes the current rules reveals a gap — and that gap must be closed by amending the tests, linters, and the doctrine itself.

**Codebase example:** The diary system in `docs/diary.md` captures metacognitive entries after every task. When a heuristic proves recurring, it graduates into the Scripture itself — the Knowledge Graph section was born this way, distilled from repeated diary patterns.

---

## 3. The Sermon of the Chaplain

The Commandments define *what*. The Sermon defines *how* — a seven-phase workflow that every feature, fix, and refactoring must follow.

> As defined in `.github/copilot-instructions.md`:
>
> **Research.** Let agents scour competing systems and return with truth. Distill best practices and viable alternatives into explicit constraints.
> **Plan.** Write the feature request in `feature-requests/`. Define objectives, constraints, acceptance criteria, and implementation approach. The feature request is the plan.
> **Judge.** Critically examine the feature request; resolve contradictions; eliminate ambiguity; refine constraints and acceptance criteria until the path is explicit and minimal. If clear, minimal, and internally consistent, freeze scope and grant authority.
> **Enforce.** Obey the Judgement. Write the failing test first; make only the smallest sufficient change; refactor only within scope. Update the feature request with implementation status and decisions.
> **Purge.** Remove invented interfaces, speculative flags, and hypothetical extensibility. If it is not required and not tested, it shall not exist.
> **Submit.** Bump. Commit. Push. Release. Tag. Let CI judge. What survives the fire may merge.
> **Distill.** After completing a task list, add a metacognitive entry to `docs/diary.md`. Name the cognitive trap or insight. Extract a heuristic. Plant a **Seed:** — a forward-looking question to grow new ideas. If the heuristic proves recurring, graduate it to this Scripture.

The seven phases form a funnel: **Research** casts a wide net, **Plan** narrows to specifics, **Judge** applies critical scrutiny, **Enforce** executes with discipline, **Purge** removes excess, **Submit** exposes the work to CI's impartial judgment, and **Distill** captures what was learned so it compounds across sessions.

Notice the asymmetry: three phases happen *before* any code is written (Research, Plan, Judge), one phase writes code (Enforce), and three phases happen *after* (Purge, Submit, Distill). This is deliberate — in AI-assisted development, the cost of writing code approaches zero, but the cost of writing the *wrong* code remains high.

---

## 4. The Knowledge Graph

The Knowledge Graph is the Scripture's densest artifact — a YAML structure graduated from recurring patterns in the development diary. It captures the single most important lesson the project has learned:

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

**The One Law** states that data normalization must happen where external data first enters the system — at the schema boundary, the provider boundary, the state boundary. When you fix a data format issue in a downstream node instead of at the provider adapter, you've created a symptom patch that will break when the next provider is added.

The **boundaries** list enumerates the five surfaces where external data enters YAMLGraph. Each is a normalization point that must be defended.

The **traps** list names the four cognitive patterns that lead developers to violate The One Law:

- **quick_confidence** — "I know what's wrong" leads to fixing without investigating
- **downstream_fix** — Patching where the symptom appears, not where the cause originates
- **symptom_patch** — Making the error message go away without addressing the root cause
- **intent_drift** — Starting to fix one thing, ending up changing something else

---

## 5. The Rite of Correction

When something breaks, the Scripture prescribes a three-step process that mirrors the scientific method: observe, hypothesize and test, then either resolve or escalate.

> As defined in `.github/copilot-instructions.md`:
>
> **Inspect.** Assume nothing; audit the codebase; trace failures to file and line; expose violated constraints and missing tests.
> **Amend.** Write the failing test first. Correct the root cause second.
> **Escalate.** If amendment is impossible, write the feature request in `feature-requests/`. Cite traces. Define the violated objective. Propose the new constraint. Return to Plan.

**Inspect** demands evidence. "Assume nothing" is the critical phrase — even if you're certain you know the cause, trace the failure to its exact file and line. The convention that *"Term 'pre-exiting failure' doesn't exist; likely cause: test pollution"* exemplifies this: a convenient label is rejected in favor of actual investigation.

**Amend** follows the TDD commandment: the failing test comes first, the fix comes second. This ensures the bug is actually reproducible and that the fix actually addresses it.

**Escalate** is the escape valve. When a bug reveals a design flaw that can't be patched locally, the Rite sends you back to the Sermon's Plan phase — but with traces, not speculation. The feature request must cite specific LangSmith traces and define the violated objective. This prevents escalation from becoming procrastination.

---

## 6. The Agents' Prayer

The chapter closes with the Agents' Prayer — six invocations and two warnings that encode the project's hardest-won lessons into a form that can be recalled before every session.

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

Each line encodes a specific lesson:

- *"Fix at the callsite, not the utility"* — Don't modify shared utilities to handle one caller's edge case; fix the caller.
- *"Kill the cheapest bug — the one in the spec"* — A bug in the requirements is cheaper to fix than a bug in the code.
- *"Normalize at the boundary"* — The One Law, restated as personal practice.
- *"Stream to reveal what batch conceals"* — Streaming output exposes failures as they happen; batch hides them until the end.
- *"Understand every protection before I pass it"* — Don't bypass guards you don't understand.
- *"Read thrice before I grant authority"* — The Judge phase demands thoroughness; premature authority grants lead to scope creep.

The two warnings target the moments of greatest risk: when pre-commit hooks feel like friction (they're doing their job) and when certainty arrives (certainty is the precursor to the `quick_confidence` trap).

The closing line — *"What survives the fire may merge"* — appears three times in the Scripture: once in the Sermon's Submit phase, once in the Prayer, and once as the document's implicit thesis. CI is the fire. Only code that passes every check earns the right to exist.

---

## 7. Why This Matters

Doctrine is not bureaucracy — it is the mechanism by which a project maintains coherence across time, contributors, and AI sessions. Without explicit rules, every agent session reinvents conventions. With them, agents become force multipliers that execute within defined boundaries.

The YAMLGraph Scripture achieves three things:

1. **Prevents drift.** When the rules are explicit, every deviation is visible. The `--no-verify` flag doesn't just skip hooks — it *"will result in immediate termination; automatically enforced by CI."*

2. **Enables AI collaboration.** Agents that receive the Scripture as context produce code that conforms to project conventions on the first attempt, not the third. Research happens before implementation. Types are enforced. Tests are written first.

3. **Compounds learning.** The Distill phase and the diary system ensure that every failure teaches the project something permanent. The Knowledge Graph exists because someone wrote the same diary entry three times — and then graduated the pattern into law.

The doctrine is not static. Commandment 10 demands its own evolution: *"Every failure shalt refine the law."* What you've read in this chapter is not the final version — it is the current version, refined by every session that came before and awaiting refinement by every session that follows.

---

*Sources: `.github/copilot-instructions.md`, `CLAUDE.md` — YAMLGraph repository*
