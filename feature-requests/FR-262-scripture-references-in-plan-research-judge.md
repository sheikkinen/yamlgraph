# Feature Request: FR-262 Scripture References in Plan-Research-Judge Prompts

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-20

## Summary

Add explicit Scripture commandment and trap references to the Chaplain pipeline's plan, research, and judge prompts, mirroring the pattern already established in all four enforce prompts.

## Value Statement

The Chaplain pipeline produces more doctrine-aligned feature requests by forcing the planning and judgment phases to evaluate proposals against the same commandments that the enforce phase already enforces.

## Problem

The Scripture (`.github/copilot-instructions.md`) is referenced in every enforce prompt but absent from every plan-research-judge prompt. This creates a structural asymmetry:

**Active (enforce phase):**
- `enforce-implement.yaml`: Commandments 4, 5, 6, 7
- `enforce-test-demo.yaml`: Commandments 2, 8
- `enforce-critique-and-distill.yaml`: Commandments 7, 10 + trap vocabulary
- `enforce-finalize.yaml`: Commandments 6, 8, 10

**Absent (plan-research-judge phase):**
- `plan.yaml`: no Scripture reference
- `research.yaml`: no Scripture reference
- `judge.yaml`: no Scripture reference

Copilot CLI loads `copilot-instructions.md` automatically into system context, so the agent *sees* the Scripture. But the enforce prompts prove that explicit quoting changes agent behavior — the agent opens the rulebook only when asked to. Without explicit references, planning and judgment operate on general-purpose reasoning rather than project doctrine.

The asymmetry means architectural violations (e.g., inventing new patterns instead of conforming, bundling orthogonal concerns, creating untestable criteria) are caught at enforce time rather than plan/judge time — after the expensive enforce pipeline has already run.

## Proposed Solution

Add a `The Scripture commands:` block to the `system:` section of each prompt, following the exact pattern used in enforce prompts. Select commandments and traps relevant to each phase's responsibility.

### plan.yaml

Add to the `system:` section:

```yaml
system: |
  You are a feature request planner. Your task is to transform a rough topic
  into a well-structured feature request document.

  The Scripture commands:
  - **Commandment 1:** Research before coding — distill wisdom into constraints.
  - **Commandment 3:** Keep configuration separate and validated.
  - **Commandment 4:** Honor existing patterns — conform before extending.
```

**Rationale:** These three commandments constrain what a plan should contain. Commandment 1 sets the research-first mindset. Commandment 3 prevents plans that hardcode configuration. Commandment 4 prevents plans that invent new patterns without checking existing ones.

### research.yaml

Add to the `system:` section:

```yaml
system: |
  You are a strategic research analyst for a YAML-first LLM framework.
  Your task is to gather evidence about a proposed feature request and
  produce a structured research brief.

  The Scripture commands:
  - **Commandment 1:** Let agents explore deep and wide; distill into constraints.
  - **Commandment 8:** Kill entropy — check if the proposal adds or removes complexity.
```

**Rationale:** Commandment 1 defines the research mandate directly. Commandment 8 gives the researcher an entropy lens — every finding should be evaluated for whether it adds or kills complexity.

### judge.yaml

Add to the `system:` section:

```yaml
system: |
  You are a feature request reviewer. Your task is to critically examine
  feature requests and render a verdict: APPROVE, AMEND, REJECT, or SPLIT.

  The Scripture commands:
  - **Commandment 4:** Honor existing patterns — conform before extending.
  - **Commandment 7:** TDD mandate — are acceptance criteria testable?
  - **Commandment 8:** Kill entropy — does this proposal add or remove complexity?

  Guard against these traps (from the Knowledge Graph):
  - **quick_confidence:** "When I feel certain → Judge instead"
  - **intent_drift:** "Plan says X, code does Y → re-read thrice"
  - **framework_costume:** "FSM wearing DAG costume → if <50% nodes use core features, wrong tool"
```

**Rationale:** The Judge gets the heaviest doctrine load because it sits on the 100× cost boundary (Judge ~$0.02 vs Enforce ~$2–10). Commandments 4, 7, and 8 map directly to the Judge's existing evaluation criteria. The three traps are the most relevant cognitive hazards for feature evaluation — quick_confidence prevents rubber-stamping, intent_drift catches scope creep between plan and judgment, and framework_costume catches proposals that don't belong in the framework.

## Acceptance Criteria

- [ ] `plan.yaml` system section includes Commandments 1, 3, 4 in the `The Scripture commands:` format
- [ ] `research.yaml` system section includes Commandments 1, 8 in the `The Scripture commands:` format
- [ ] `judge.yaml` system section includes Commandments 4, 7, 8 and traps `quick_confidence`, `intent_drift`, `framework_costume`
- [ ] All three prompts use the same `The Scripture commands:` / `Guard against these traps:` formatting pattern as enforce prompts
- [ ] Existing prompt functionality (user section, template variables) is unchanged
- [ ] `yamlgraph graph lint .chaplain/graphs/copilot/graph.yaml` passes (prompts are valid YAML)

## Alternatives Considered

1. **Do nothing — rely on system context.** The agent already sees copilot-instructions.md. But enforce prompt history shows explicit quoting changes behavior. Rejected: evidence against.

2. **Include the full Scripture text in each prompt.** Would guarantee full coverage but bloats token usage and dilutes the specific commandments relevant to each phase. Rejected: violates minimality.

3. **Add a shared Scripture preamble prompt included by all phases.** Possible via Jinja2 include or a shared YAML fragment. Premature abstraction — only three files, each needs different commandments. If a fourth phase is added, reconsider.

## Related

- `.chaplain/graphs/copilot/prompts/plan.yaml` — target file
- `.chaplain/graphs/copilot/prompts/research.yaml` — target file
- `.chaplain/graphs/copilot/prompts/judge.yaml` — target file
- `.chaplain/graphs/enforce/prompts/enforce-implement.yaml` — reference pattern
- `.chaplain/graphs/enforce/prompts/enforce-critique-and-distill.yaml` — reference pattern (traps)
- GitHub Issue #142 — source proposal

## Research Brief

### Competitive Landscape

No competing framework embeds phase-specific governance rule references in multi-stage LLM pipeline prompts. Each framework handles agent instructions as flat system prompts:

- **CrewAI** ([planning docs](https://docs.crewai.com/concepts/planning)): `planning=True` flag delegates task decomposition to an `AgentPlanner`. The planner receives all crew info but no governance ruleset — it focuses on step-by-step task ordering, not doctrinal alignment.
- **Google ADK** ([LLM agents docs](https://google.github.io/adk-docs/agents/llm-agents/)): Uses a single `instruction` string per agent. No mechanism for selective rule injection by pipeline phase.
- **OpenAI Agents SDK** ([agents docs](https://openai.github.io/openai-agents-python/agents/)): `instructions` is the system prompt. Supports `input_guardrails` and `output_guardrails` as separate validation layers, but these are runtime checks, not doctrinal references embedded in the prompt.
- **LangGraph**: System messages are static strings. No structured pattern for phase-specific rule selection.
- **AutoGen**: Custom agents with system messages. No governance reference architecture.

**Conclusion**: The explicit "Scripture commands" pattern — selecting specific commandments per phase — is unique to YAMLGraph's Chaplain infrastructure. No external solution exists to document instead of build.

### Existing Abstractions

The "Scripture commands" prompt pattern is already established in 4/4 enforce prompts:

| Prompt | Commandments | Traps |
|--------|-------------|-------|
| `enforce-implement.yaml` | 4, 5, 6, 7 | — |
| `enforce-test-demo.yaml` | 2, 8 | — |
| `enforce-critique-and-distill.yaml` | 7, 10 | 7 trap names |
| `enforce-finalize.yaml` | 6, 8, 10 | — |

Target files (0/3 have the pattern):
- `.chaplain/graphs/copilot/prompts/plan.yaml` — 27 lines, no Scripture reference
- `.chaplain/graphs/copilot/prompts/research.yaml` — 45 lines, no Scripture reference
- `.chaplain/graphs/copilot/prompts/judge.yaml` — 48 lines, no Scripture reference

The `enforce-critique-and-distill.yaml` is the only prompt that uses both commandments AND trap vocabulary — making it the direct template for the judge.yaml enhancement.

### Diary Precedents

Three diary entries provide direct evidence:

1. **`2026-04-20-chaplain-as-compiler.md`** — Maps Plan/Research/Judge to compiler passes (Parser/Semantic Analysis/Type Checking). Identifies "structured output gradient": quality increases with structure moving downstream. FR-262 adds structure (explicit rule references) to the upstream passes, which the compiler metaphor predicts will improve downstream output quality.

2. **`2026-03-13-fr-199-fsm-scripture-claude-md.md`** — The `framework_costume` trap: agents operating under `fsm/CLAUDE.md` had a 4-line YAGNI/TDD/DRY/KISS summary instead of full doctrine. The fix was embedding the full scaffold, not a summary. Directly analogous: plan/research/judge prompts operate with implicit (system context) doctrine instead of explicit (prompt-embedded) references.

3. **`2026-04-20-reflection-fr-257-chaplain-research-step.md`** — The `unchallenged_premise` trap: "Judge validates execution, not intent." The research step was added to challenge intent. FR-262 extends this by giving both the research step and the judge explicit doctrinal lenses, not just general-purpose reasoning.

4. **`2026-03-11-reflection-fr-184.md`** — The `plausible_wrong_answer` trap: LLM-based exact matching against structured vocabulary is non-deterministic. Relevant caution: explicit commandment references work because they prime the LLM's attention, not because they guarantee compliance. The enforcement boundary remains CI gates, not prompt text.

### Usage Evidence

- **Graphs using the Chaplain pipeline**: 1 (`.chaplain/graphs/copilot/graph.yaml`)
- **Graphs using the Enforce pipeline**: 1 (`.chaplain/graphs/enforce/graph.yaml`)
- **Total prompt files affected**: 3 (plan, research, judge)
- **Total prompt files with existing pattern**: 4 (all enforce prompts)
- **Real-world use cases beyond the proposal**: The Chaplain pipeline processes every FR in the project. As of 2026-04-20, the diary records 260+ FRs processed through this pipeline. Every FR benefits from improved doctrinal alignment in early phases.

### Classification Signal

- **Abstraction level**: pattern — this is a prompt content change, not a new node type, tool, or framework feature
- **Recommended approach**: build — 3 YAML files need ~5-10 lines added each; the pattern is proven in 4 enforce prompts; no code changes required; effort is correctly estimated at 0.5 days
- **Key risk**: Over-constraining the Plan phase with too many commandments could reduce creative exploration, but the proposed selection (Commandments 1, 3, 4) explicitly includes Commandment 1 ("explore deep and wide"), which mitigates this
