# Feature Request: FR-588 LLM-scored prompt abstraction-span — validate before shipping

**Priority:** MEDIUM
**Type:** Feature (linter / research validation)
**Status:** Rejected (2026-06-24) — superseded by FR-589 (rebuilt as a standalone YAMLGraph example); the linter-llm-free enforcement it produced stands
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
spike-gated **calibration study**: run the scorer over a corpus with *known*
complexity labels and test whether abstraction-span **separates** the labelled
monoliths from the clean prompts (anchored by the one prompt with a rigorously
measured L5 failure rate). If it does, the metric earns a standalone report; if it
does not, the metric is noise and is KILLed, with static W026 left standing. We do
not ship a complexity number we have not shown separates complex from simple.

## Value statement

Graph authors get a cheap LLM estimate of a prompt's abstraction-span — the
hand-tagging FR-585 proved informative — **only after** the score is shown to
reproduce the existing complexity labels (anchored by the one measured-failure
point), so the number carries evidence rather than a plausible-looking guess.
## Rejection (2026-06-24)

**Superseded by FR-589.** This FR was judged and granted authority, but its
proposed build (Stage 2: a standalone `spike_*.py` importing `execute_prompt` and
hand-rolling the map loop + structured-output call + verdict) fights the framework's
own thesis — orchestration belongs in `graph.yaml`, not Python. FR-589 rebuilds the
identical validation as a **self-contained YAMLGraph example** (graph + prompt + two
tools, run via `yamlgraph graph run`), carrying forward this FR's hard-won content
unchanged: the ground-truth honesty (reproduce hand labels, not "predict failure"),
the **separation** test (not Spearman), and the KILL discipline.

**What survives this rejection:** the `linter-llm-free` import-linter contract
(`.importlinter`), committed and enforced under this FR, **stands** — the standing
judgement that the linter never makes an LLM call is independent of how the metric
is built. FR-589 retains it.
## Judgement (2026-06-24)

**Verdict: Authority GRANTED on narrowed scope.** The discipline is sound —
validate-before-ship, spike-gated, explicit KILL path, the scorer made to pass its
own metric. Three corrections were required before the path was minimal and
internally consistent:

1. **Ground-truth conflation (resolved).** The draft promised correlation with
   *measured failure rates*, but only `assign_pre_eff` (L5) has a rigorous measured
   rate (FR-584/585: precision ≈0.30). The other six prompts carry complexity
   *labels*, not measured rates — and those labels share lineage with the very
   abstraction reasoning the LLM performs. The honest, deliverable claim: **can a
   cheap LLM pass reproduce the hand abstraction-tagging FR-585 proved informative**,
   anchored where it exists by the one measured point. Gate 1 tests *reproduction of
   the labels*, not *discovery of failure*. The circularity is accepted because the
   value is automating an expensive human judgment, not proving a causal law — a
   claim this 7-prompt corpus is too small to settle.
2. **Spearman ρ at n=7 with tied bins is hollow (cut).** The "ranking" is two bins
   (4 high, 2 low, 1 boundary); a rank-correlation threshold over tied ranks is
   ill-defined and decorative. Gate 1 is now a **clean separation test** with a
   stated margin. No ρ.
3. **In-linter LLM mode is out of scope (deferred *and now enforced*).** A
   networked, API-keyed call inside `yamlgraph graph lint` collides with the
   offline/no-secret nature of pre-commit and CI linters. Stage 3's GO deliverable is
   narrowed to a **standalone reporting command + the validated metric**; wiring an
   advisory W027 into the linter (flag semantics, key sourcing, CI behaviour) is
   deferred to its own follow-up FR. **Standing judgement (2026-06-24): the linter
   stays LLM-free permanently** — mechanically guarded by the `linter-llm-free`
   `import-linter` contract (`.importlinter`), which forbids any `yamlgraph.linter`
   module from importing the executor or LLM-factory layer. Any future FR that
   revisits in-linter scoring must first amend or remove that contract in the open.

**Frozen scope:** Stage 1 (scorer prompt) + Stage 2 (calibration study — the
deliverable) + Stage 3 reduced to a standalone report. KILL on separation failure.
No scorer re-tune beyond one iteration.

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
froze: four prompts labelled monolith (`assign_pre_eff`, `assign_causality`,
`assign_affects`, `extract_agents` — each a documented monolith behind a killed FR or
audit finding) and two clean (`extract_glosses`, `classify_kinds`), with
`extract_goals` as the boundary case. One of these — `assign_pre_eff` — also has a
*rigorously measured* L5 failure rate (FR-585: precision ≈0.30); the rest carry the
complexity *label*, not a measured rate. So Gate 1 honestly tests whether the LLM
score reproduces the existing hand labels (anchored by the one measured point), which
is the cheap-automation question — not the stronger causal claim that complexity
*produces* failure, which this corpus is too small to settle.

## Proposed solution

A spike, then a gate, then (only on pass) a standalone report.

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
7-prompt plot_modeller corpus, emit each prompt's `level_count`, and apply the
**separation test** against the known monolith/clean labels (`min(monolith) >
max(clean)`, gap ≥ one level, boundary case between). Report the raw ranking table
and the pass/fail of the separation. This is a measurement artifact (FR-584 C5),
committed for audit.

### Stage 3 — standalone report (only if Gate 1 passes)

The spike, promoted to a standalone command that prints each prompt's `level_count`,
`levels`, and a flag when the score exceeds the calibration-derived threshold (lowest
monolith score minus a margin). **No linter integration in this FR.** Wiring an
advisory W027 into `yamlgraph graph lint` requires sourcing an API key inside a tool
that runs offline in pre-commit and CI — an architectural question (key handling,
non-determinism in CI, opt-in flag semantics) that belongs in its own follow-up FR.
This FR stops at a validated metric plus a command an author can run on demand.

## Acceptance criteria

- [ ] **Gate 1 — separation (decides the whole FR).** Run the abstraction-span
      scorer over the 7-prompt plot_modeller corpus on a named model (verify the
      `Creating LLM` log line). **Tripwire (separation, not correlation):** PASS
      requires every known monolith (`assign_pre_eff`, `assign_causality`,
      `assign_affects`, `extract_agents`) to score **strictly above both clean
      prompts** (`extract_glosses`, `classify_kinds`) — i.e. `min(monolith_score) >
      max(clean_score)`, the gap at least one level wide — with `extract_goals`
      landing between, and the one measured-failure prompt (`assign_pre_eff`, FR-585)
      in the top band. If any monolith fails to clear both clean prompts, or a clean
      prompt scores into the monolith band → the LLM cannot reproduce the hand
      tagging → **KILL**: do not ship the metric; static W026 stands; record the null
      result. Do not retune the scorer prompt more than once (FR-584
      fourth-iteration-ritual lesson).
- [ ] Scorer prompt is single-judgement (passes its own abstraction-span ≤ 2) and
      uses structured output (no hand-written nested YAML).
- [ ] Calibration study committed as a measurement artifact with the ranking table
      and ρ; reproducible by one command.
- [ ] On GO only: standalone reporting command added (not wired into the default or
      any lint run), threshold derived from calibration data not hand-picked,
      unit/integration tests tagged `@pytest.mark.req`. The command's flag fires on
      the four monoliths, stays silent on the two clean prompts, `extract_goals`
      documented boundary.
- [ ] Diary reflection added.

## Stop rule

If Gate 1's separation fails (any monolith does not clear both clean prompts, or a
clean prompt scores into the monolith band), **the LLM cannot reproduce the hand
abstraction-tagging** — KILL, keep static W026, and record the null result in the
diary (a metric that does not separate is a finding, not a failure). Do not ship a
score that launders an unvalidated guess as a measurement. Do not iterate the scorer
prompt more than once.

## Out of scope (explicit)

- **Not a replacement for W026.** Static field-count stays the default, free check;
  the standalone report is the opt-in semantic complement.
- **No build-gating on an LLM score.** The report is advisory only — an opaque,
  non-deterministic judgement must never block a merge (FR-584 *detection without
  enforcement* caution applies in reverse: do not enforce on a noisy signal).
- **No in-linter integration.** Wiring the validated metric into `yamlgraph graph
  lint` (API-key sourcing, CI/pre-commit offline tension, opt-in flag) is a separate
  follow-up FR, not this one — and is now mechanically forbidden by the
  `linter-llm-free` `import-linter` contract (`.importlinter`). The linter stays a
  pure, offline, deterministic analyzer.
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
  mechanics, not cognitive-operation count; cheap enough to report alongside the
  abstraction-span report as a secondary, non-gating number.

## Related

- `feature-requests/FR-586-prompt-monolith-linter-check.md` (static W026; this FR's complement and calibration-witness source)
- `feature-requests/FR-585-plot-modeller-L5-salience-gate-decode.md` (the abstraction-span hand-decomposition; deconfounded KILL)
- `feature-requests/FR-587-plot-modeller-L5-snapshot-then-diff.md` (the split this metric would have flagged earlier)
- `docs/diary/diary-2026-06-24-the-brief-i-would-never-give-a-subagent.md` (the Seed; abstraction-span as the deepest complexity metric)
- `/memories/prompt-as-subagent-contract.md` (the authoring principle this metric enforces)
