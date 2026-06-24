# Feature Request: FR-588 LLM-scored prompt abstraction-span — validate before shipping

**Priority:** MEDIUM
**Type:** Feature (linter / research validation)
**Status:** Proposed
**Effort:** 1–1.5 days (spike-gated; the validation study is ~0.5 day and may KILL the metric)
**Requested:** 2026-06-24
**Origin:** Graduated Seed from `docs/diary/diary-2026-06-24-the-brief-i-would-never-give-a-subagent.md`
**Complements:** FR-586 (static W026 prompt-monolith linter — field-count heuristic)
**Evidence:** FR-584/585 (four killed L5 prompt-lever FRs), the 7-prompt plot_modeller audit

## Summary

FR-586 ships **W026**, a *static* prompt-monolith warning that counts declared
output fields and matches a few structural near-miss phrases. It catches monoliths
whose overload is visible in the **schema shape**. It is blind to the monolith whose
overload lives in **prose**: a prompt can declare one output field and still fuse
ten cognitive operations in its instructions — `assign_pre_eff` declares four slices
but spans ten *abstraction levels* (comprehension → causal → temporal-delta →
salience → ontology → theory-of-mind → token-fidelity → arg-syntax → serialization →
self-correction), and field-count alone cannot see that.

This FR proposes **abstraction-span**: a metric counting the distinct *cognitive
operations* a prompt asks for in one output, scored by a small LLM pass (a prompt
cannot reliably count its own cognitive levels with regex). **But the deliverable is
not a scorer — it is the validation that the score means anything.** The work is a
spike-gated **calibration study**: run the scorer over a corpus with *known* failure
behavior and test whether abstraction-span ranks the prompts in the same order as
their measured failure. If it does, the metric earns an advisory **W027**; if it does
not, the metric is noise and is KILLed, with static W026 left standing. We do not
ship a complexity number we have not shown predicts complexity.

## Value statement

Graph authors catch the *prose monolith* — a prompt that fuses many cognitive
operations without a wide output schema — that the static W026 cannot see, **only
after** the abstraction-span score is proven to rank-correlate with real failure, so
the warning carries evidence rather than a plausible-looking number.

## Problem

Two gaps motivate this.

1. **Static W026 is shape-blind.** It keys on declared output fields and phrase
   heuristics. A prompt with one output field but five fused judgements in its
   instruction body scores clean and ships. The diary's abstraction-level tagging of
   `assign_pre_eff` was done **by hand**; nothing automates it, so the deepest
   complexity signal (FR-585 diary: abstraction-span predicted *where* the model
   broke, not just *that* it was big) is unavailable at authoring time.

2. **An LLM-scored metric is itself a prompt — and untrusted by default.** Asking a
   model "how many distinct cognitive operations does this prompt ask for?" is
   plausible-output territory (Scripture: *a plausible wrong answer is harder to
   catch than a crash*). A number that looks reasonable but does not correlate with
   real failure is worse than no number — it launders a guess as a measurement. The
   only honest way to add it is to **validate it against ground truth first**.

The plot_modeller corpus is the ready-made calibration witness, the same one FR-586
froze: four prompts with *measured* failure (`assign_pre_eff`, `assign_causality`,
`assign_affects`, `extract_agents` — each a documented monolith behind a killed FR or
audit finding) and two clean (`extract_glosses`, `classify_kinds`), with
`extract_goals` as the boundary case. The failure ordering is already known; the
question is whether the LLM abstraction-span score reproduces it.

## Proposed solution

A spike, then a gate, then (only on pass) a thin advisory check.

### Stage 1 — the scorer (a prompt obeying its own contract)

`prompts/lint/abstraction_span.yaml` — a single-judgement prompt (it must not break
the very contract it measures): given one prompt's text, return a typed score —
`{level_count: int, levels: list[str], rationale: str}` — where each `level` names a
distinct cognitive operation the prompt requires in one output (comprehension,
classification, salience judgment, state-delta, serialization, self-correction, …).
One judgement, closed input, structured output, no cross-prompt state. Scored by a
small/cheap model; the score is advisory, never a build gate.

### Stage 2 — the calibration study (the actual deliverable)

`examples/.../spike_abstraction_span.py` (or `scripts/`): run the scorer over the
7-prompt plot_modeller corpus, emit each prompt's `level_count`, and compute the
**rank correlation** against the known failure ordering (the four monoliths ranked
above the two clean prompts, boundary case between). Report Spearman ρ and the raw
ranking table. This is a measurement artifact (FR-584 C5), committed for audit.

### Stage 3 — advisory W027 (only if Gate 1 passes)

`check_prompt_abstraction_span` in `yamlgraph/linter/checks_prompts.py`, **opt-in**
(behind a `--llm` flag or a separate `yamlgraph graph lint --semantic` mode, because
it costs an LLM call and is non-deterministic). Severity **warning**, code **W027**,
emitted only when `level_count` exceeds a threshold *set from the calibration data*
(the lowest score among the known monoliths, minus a margin). W027 complements, does
not replace, W026: static catches schema monoliths cheaply in every run; W027 catches
prose monoliths when the author opts into the LLM pass.

## Acceptance criteria

- [ ] **Gate 1 — calibration (decides the whole FR).** Run the abstraction-span
      scorer over the 7-prompt plot_modeller corpus on a named model (verify the
      `Creating LLM` log line). **Tripwire:** PASS requires the score to rank the
      **four known monoliths above the two known clean prompts** (a clean ordinal
      separation), with Spearman ρ ≥ 0.7 against the documented failure ordering, and
      `extract_goals` landing in the boundary band. If the score does not separate
      monoliths from clean prompts — or it inverts a pair — the metric does not
      predict failure → **KILL**: do not ship W027; static W026 stands; record the
      null result. Do not retune the scorer prompt more than once (FR-584
      fourth-iteration-ritual lesson).
- [ ] Scorer prompt is single-judgement (passes its own abstraction-span ≤ 2) and
      uses structured output (no hand-written nested YAML).
- [ ] Calibration study committed as a measurement artifact with the ranking table
      and ρ; reproducible by one command.
- [ ] On GO only: W027 added, opt-in (LLM pass not in the default lint run),
      warning-severity (never breaks a build or changes lint exit semantics),
      threshold derived from calibration data not hand-picked, unit/integration tests
      tagged `@pytest.mark.req`.
- [ ] W027 calibration witness mirrors FR-586: fires on the four monoliths, silent on
      the two clean prompts, `extract_goals` documented boundary.
- [ ] Diary reflection added.

## Stop rule

If Gate 1's score does not reproduce the known failure ordering, **abstraction-span
as an LLM-judged metric is falsified** — KILL, keep static W026, and record the null
result in the diary (a metric that does not predict is a finding, not a failure). Do
not ship an advisory that launders an unvalidated guess as a measurement. Do not
iterate the scorer prompt more than once.

## Out of scope (explicit)

- **Not a replacement for W026.** Static field-count stays the default, free check;
  W027 is the opt-in semantic complement.
- **No build-gating on an LLM score.** W027 is advisory only — an opaque,
  non-deterministic judgement must never block a merge (FR-584 *detection without
  enforcement* caution applies in reverse: do not enforce on a noisy signal).
- **No auto-fix / auto-split.** The metric flags; the author decides. Splitting a
  monolith into a pipeline is a human architectural call (cf. FR-587).
- **No generalization to graph nodes yet.** The wider asymmetry (does the
  meta-work/unit-of-work split show up in graph *node* granularity too, not just
  prompts?) is noted as a future direction, not built here.

## Alternatives considered

- **Pure static heuristic (extend W026 with instruction-body keyword counting)** —
  rejected as the *primary* signal: prose cognitive-operation counting by regex is
  the fourth-special-case trap (Scripture: *switch to a proper parser* — here, a
  model). Keyword counts miss paraphrase and fuse unrelated verbs; the hand-tagging
  that produced the ten-level decomposition was semantic, not lexical.
- **Ship the LLM scorer without calibration** — rejected: violates the FR's own
  thesis. An unvalidated complexity score is a plausible wrong answer; the
  calibration study *is* the value, the scorer is incidental.
- **Readability metric (Flesch–Kincaid) as the proxy** — rejected as primary: a real
  correlate of the "complicated to a human" signal, but it measures sentence
  mechanics, not cognitive-operation count; cheap enough to report alongside W027 as
  a secondary, non-gating number.

## Related

- `feature-requests/FR-586-prompt-monolith-linter-check.md` (static W026; this FR's complement and calibration-witness source)
- `feature-requests/FR-585-plot-modeller-L5-salience-gate-decode.md` (the abstraction-span hand-decomposition; deconfounded KILL)
- `feature-requests/FR-587-plot-modeller-L5-snapshot-then-diff.md` (the split this metric would have flagged earlier)
- `docs/diary/diary-2026-06-24-the-brief-i-would-never-give-a-subagent.md` (the Seed; abstraction-span as the deepest complexity metric)
- `/memories/prompt-as-subagent-contract.md` (the authoring principle this metric enforces)
