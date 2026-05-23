# Diary: 2026-05-22 — FR-447/448: Demo-First Discovery and Self-Referential Judgement

## What happened

Built the FR-447 judge agent demo (standalone `type: agent` node with 4 shell tools). Demo ran successfully — 4 iterations, read the FR, checked architecture, searched for overlap, read referenced files, produced a thorough APPROVE verdict.

Then discovered the structured output gap: the agent returned markdown text, not the `JudgeVerdict` dict defined in the prompt schema. Traced root cause to `agent.py` line 292 — agent loop bypasses `execute_prompt()` entirely, so `with_structured_output` is never applied.

Drafted FR-448 to fix the gap. Judged FR-448 manually (5 issues → AMEND). Then ran the judge demo *against* FR-448 — the agent independently confirmed all 5 issues and found a 6th (no skeleton test code). The structured output gap was self-demonstrating: the verdict about missing structured output was itself unstructured text.

## Traps encountered

### 1. Downstream fix temptation
When the demo returned text instead of a dict, the first instinct was "add a shell helper to parse the markdown". This is the `downstream_fix` trap — guarding where the symptom manifests instead of normalizing at the entry boundary. The boundary is `agent.py` line 292 (the agent's return value), not the CLI output or a post-processing script.

### 2. Demo-before-integrate (validated)
The human override to scope FR-447 as a standalone demo (not wired into the chaplain pipeline) was exactly right. If the agent had been integrated directly into the chaplain FSM, the text-vs-dict mismatch would have broken event routing at runtime. The demo surfaced the gap safely. This confirms: `demo_vs_test` — demos prove abstraction worth having; tests prove constraints.

### 3. Model name format boundary
`claude-sonnet-4.6` → 404. Anthropic uses hyphens: `claude-sonnet-4-6`. This is the `provider` boundary — external API format conventions must be normalized at the boundary where external data enters. The fix was trivial once identified.

## Insight: Self-referential validation

Running the judge against its own follow-up FR is a powerful validation pattern. The tool dogfoods itself — the judge agent's inability to return structured output *is the evidence* for FR-448. This is more convincing than any test assertion because the failure mode is directly observable in the output.

The automated judge found the same 5 issues as the manual judgement plus one more (no skeleton test). This validates the agent's tool selection and reasoning — it read the right files (`agent.py`, `executor.py`, `base.py`) and correctly identified the signature mismatch in the pseudocode by comparing it against actual source.

## Heuristic

**Try the tool on itself before declaring it ready.** Self-referential use exposes gaps that external testing misses because the tool's output format becomes the test input. If it can't judge its own follow-up, it can't judge anything.

## Seed:

When FR-448 delivers structured output, the judge's verdict dict could feed directly into an FSM transition: `APPROVE → enforce`, `AMEND → re-plan`, `REJECT → close`. The manual `sed` extraction step disappears entirely. But the CLI presentation layer still needs `--output json` to make the structured state accessible to shell pipelines. Is that FR-449, or should `graph run` always support JSON output as a core capability?
