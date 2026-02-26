# Chapter 01: Doctrine — The Scripture Decoded

*YAMLGraph Development Pipeline eBook*

---

## 1. Why Codified Doctrine?

When AI agents collaborate with human developers on a shared codebase, implicit conventions become a liability — agents cannot infer intent from culture, code review norms, or tribal knowledge. Codified doctrine converts unspoken expectations into executable constraints: agents receive explicit boundaries that prevent drift, hallucination, and speculative code, while humans gain guardrails that make every decision traceable and every deviation visible. Without written law, AI-assisted workflows devolve into a negotiation between what the agent *can* generate and what the project *should* contain.

---

## 2. The 10 Commandments

The Scripture opens with an unambiguous declaration:

> *"These laws descend from the canon of software craft. They shalt not be altered by preference, haste, or machine hallucination."*
>
> — `.github/copilot-instructions.md`

What follows are ten commandments — not guidelines, not suggestions — that govern every line of code, every agent interaction, and every merge in the YAMLGraph project.

---

### Commandment 1

> As defined in `.github/copilot-instructions.md`:
>
> **1. Thou shalt research before coding** — Let infinite agents explore deep and wide; distill their wisdom into constraints, for the cheapest code is unwritten code. When the domain is broad, invoke structured ideation to cross capabilities with constraints and surface non-obvious directions.

**Principle:** The cheapest bug to fix is the feature you never built. Research eliminates unnecessary work before a single line is written.

**Codebase example:** Before implementing URL-based prompt loading, the team researched deployment patterns and discovered that documenting volume mounts, git-sync, and ConfigMaps solved the same problem — no new code required. The result is `reference/prompt-deployment.md`, not a feature branch. As `CLAUDE.md` notes: *"Documenting patterns is cheaper than new code."*

---

### Commandment 2

> As defined in `.github/copilot-instructions.md`:
>
> **2. Thou shalt demonstrate with example** — Never explain abstractly; show working code.

**Principle:** Working examples are the only trustworthy documentation — prose lies, code proves.

**Codebase example:** The `examples/` directory contains runnable demos (e.g., `examples/demos/hello/graph.yaml`) that can be executed with `yamlgraph graph run`. Every pattern documented in `reference/` is backed by a corresponding example graph, not just a description.

---

### Commandment 3

> As defined in `.github/copilot-instructions.md`:
>
> **3. Thou shalt not utter code in vain** — Keep configuration separate and validated, for code is logic and config is truth.

**Principle:** Logic belongs in code; truth belongs in configuration. Mixing the two makes both fragile.

**Codebase example:** All prompts live in `prompts/*.yaml`, never hardcoded in Python. As `CLAUDE.md` enforces:

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

**Principle:** Consistency compounds; novelty fragments. Always check what exists before creating something new.

**Codebase example:** The `node_factory/` modules each follow the same execution pattern: pre-checks → loop protection → resume support → execution → return dict. When adding a new node type, developers conform to this five-step flow rather than inventing a bespoke lifecycle.

---

### Commandment 5

> As defined in `.github/copilot-instructions.md`:
>
> **5. Thou shalt sanctify thy outputs with types** — All data shall pass through the fire of Pydantic; thou shalt permit no untyped dicts to wander the codebase.

**Principle:** Every value that crosses a boundary must have a declared shape. Untyped data is untested data.

**Codebase example:** LLM outputs are validated through either inline YAML schemas or Pydantic models in `yamlgraph/models/schemas.py`. The anti-patterns table in `CLAUDE.md` lists "Untyped dicts" as wrong and "Pydantic models or inline YAML schemas" as correct.

---

### Commandment 6

> As defined in `.github/copilot-instructions.md`:
>
> **6. Thou shalt bear witness of thy errors** — Hide nothing; expose every fault to `ruff` and to CI, for what is hidden in commit shall be revealed in production. Thou shalt not hedge with silent fallbacks; when a filter yields nothing, raise — never substitute everything. A plausible wrong answer is harder to catch than a crash.

**Principle:** Crashes are honest; silent failures are liars. Make errors loud and visible.

**Codebase example:** The error handling pattern uses `PipelineError.from_exception()` to capture and surface every fault — never swallowing exceptions. Every `# noqa` suppression must be documented in `docs/confessions.md` with a CONF-XXX ID explaining the sin and the penance.

---

### Commandment 7

> As defined in `.github/copilot-instructions.md`:
>
> **7. Thou shalt be faithful to TDD** — Red-Green-Refactor; run `pytest` with every change. No bug shall be fixed unless first condemned by a failing test.

**Principle:** Tests are not verification — they are specification. The failing test comes first, always.

**Codebase example:** Every test function carries `@pytest.mark.req("REQ-YG-XXX")` linking it to a requirement in `ARCHITECTURE.md`. The script `python scripts/req_coverage.py --strict` enforces that no requirement exists without a corresponding test. The development loop is: `pytest tests/unit/ -q --no-cov` after every change.

---

### Commandment 8

> As defined in `.github/copilot-instructions.md`:
>
> **8. Thou shalt kill all entropy and false idols** — Split modules before they bloat; feed the dead to `vulture`; burn duplicates with `jscpd`; sanctify with `radon`. Thou shalt measure structural drift, not only passing checks. Green correctness without entropy context is incomplete truth. No shims, no adapters, no "compat" flags shalt thou tolerate. Delete dead code; record significant removals in commit notes.

**Principle:** Passing tests are necessary but insufficient — a codebase can be correct and still rotting. Measure complexity, kill dead code, and refuse backward-compatibility shims.

**Codebase example:** Module size is capped at 400 lines (max 450) per `CLAUDE.md` quality standards. The convention that *"Term 'backward compatibility' is a key indicator for a refactoring need"* means that any request for a compatibility layer is treated as a signal to refactor, not to add an adapter.

---

### Commandment 9

> As defined in `.github/copilot-instructions.md`:
>
> **9. Thou shalt define and observe operational truth** — Establish measurable service objectives; instrument and trace execution; treat performance degradation, failure rates, and evaluation drift as production defects. No incident shall be closed without cited traces in LangSmith and recorded rationale in `feature-requests/`.

**Principle:** If you can't measure it, you can't defend it. Observability is not optional — it is an operational requirement.

**Codebase example:** LangSmith tracing is configured via `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY`. Every incident requires cited traces and a recorded rationale in `feature-requests/` before it can be closed.

---

### Commandment 10

> As defined in `.github/copilot-instructions.md`:
>
> **10. Thou shalt preserve and improve the doctrine** — Every failure shalt refine the law. After correction, amend tests and linters to guard against recurrence; let success be codified, and let the CHANGELOG.md bear witness to the evolution of the Word.

**Principle:** Doctrine is living law — every failure teaches and every lesson is encoded as a new guard.

**Codebase example:** The Knowledge Graph of the Diary (see Section 4) was graduated from recurring diary patterns into the doctrine itself. Insights that appear repeatedly in `docs/diary.md` are promoted to `.github/copilot-instructions.md`, ensuring the law evolves with experience.

---

## 3. The Sermon of the Chaplain

The Sermon defines the seven-phase workflow that governs every feature from inception to reflection. It is not a suggestion — it is the liturgical order of development.

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

The Sermon encodes a critical insight: **the feature request is the plan**. There is no separate planning document, no Jira ticket, no design doc — the feature request in `feature-requests/` *is* the specification, the acceptance criteria, and the implementation record. This collapses the planning-to-execution gap and ensures that the artifact of planning is the same artifact that tracks enforcement.

The **Distill** phase is uniquely powerful. By requiring metacognitive reflection after every task, the Sermon creates a feedback loop that feeds `docs/diary.md` — and when patterns recur, they graduate into the doctrine itself. The Scripture is not static; it grows from the lived experience of its practitioners.

---

## 4. The Knowledge Graph

Graduated from recurring diary patterns, the Knowledge Graph distills the deepest recurring insight into a single law and its associated context:

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

**The One Law** — *normalize at the boundary* — is the distilled wisdom of repeated failures. When data enters the system from an external provider, a user input, or a streaming chunk, that is where validation, type coercion, and normalization must happen. Attempting to fix malformed data downstream — after it has already propagated through the state graph — is the **downstream_fix** trap: it creates patches that mask the root cause.

The **boundaries** list (`schema, provider, state, streaming, platform`) enumerates the five surfaces where external data enters YAMLGraph. The **traps** list names the four cognitive failure modes that lead developers to violate the One Law:

- **quick_confidence** — assuming the fix is obvious without tracing the root cause
- **downstream_fix** — patching symptoms instead of normalizing at entry
- **symptom_patch** — addressing the visible error rather than the structural flaw
- **intent_drift** — losing sight of the original objective during implementation

This Knowledge Graph is a living artifact: as new traps are identified in `docs/diary.md`, they are added here to guard future development.

---

## 5. The Rite of Correction

When something breaks — and it will — the Rite of Correction prescribes a three-phase response:

> As defined in `.github/copilot-instructions.md`:
>
> **Inspect.** Assume nothing; audit the codebase; trace failures to file and line; expose violated constraints and missing tests.
>
> **Amend.** Write the failing test first. Correct the root cause second.
>
> **Escalate.** If amendment is impossible, write the feature request in `feature-requests/`. Cite traces. Define the violated objective. Propose the new constraint. Return to Plan.

**Inspect** demands rigor: no guessing, no "I think the problem is..." — trace the failure to a specific file and line number. Identify which constraint was violated and which test was missing.

**Amend** enforces TDD even in bugfixes: the failing test comes *before* the fix. This ensures the bug is captured as a regression test that will prevent recurrence.

**Escalate** is the escape valve. When a bug reveals a deeper architectural problem that cannot be fixed in place, the Rite redirects to the Sermon's planning phase. The feature request must cite traces (from LangSmith or test output), define the violated objective, and propose a new constraint. This ensures that systemic problems are addressed systemically, not with local patches.

---

## 6. The Agents' Prayer

The prayer is recited not by humans, but by agents — a set of principles that guide autonomous decision-making in every interaction with the codebase:

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

Each line encodes a heuristic:

- **Fix at the callsite** — don't modify shared utilities to accommodate one caller's needs.
- **Kill the cheapest bug** — a bug in the spec costs nothing to fix compared to a bug in production code.
- **Normalize at the boundary** — the One Law, restated as personal practice.
- **Stream to reveal** — streaming execution exposes timing, ordering, and intermediate state that batch execution conceals.
- **Understand every protection** — never bypass a guard (pre-commit hook, type check, lint rule) without understanding why it exists.
- **Read thrice before granting authority** — review plans, judgements, and scope three times before authorizing implementation.

The closing lines are warnings against two cognitive traps: when safeguards feel like friction, that's evidence they're working; when you feel certain, that's the moment to invoke the Judge phase and challenge your assumptions.

---

## 7. Why This Matters

Doctrine is not bureaucracy — it is the immune system of a codebase that evolves under AI assistance. Without explicit, codified rules, agent-generated code drifts toward plausible-but-wrong patterns: silent fallbacks, untyped data, hardcoded prompts, and speculative abstractions. The Scripture prevents this drift by making every expectation executable and every violation detectable.

The feedback loop is the key: the Sermon's **Distill** phase feeds `docs/diary.md`, recurring insights graduate to the Knowledge Graph, and the Knowledge Graph amends the Commandments. The doctrine is not imposed from above — it is grown from below, refined by failure, and hardened by CI. What survives the fire may merge.

---

*Sources: `.github/copilot-instructions.md`, `CLAUDE.md` — YAMLGraph repository*


