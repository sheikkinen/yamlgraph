# 2026-07-14 — FR-722: the gate that fired three times in five runs

**Context.** Enforcing the ICPC-2 RFE classifier. The Judgement's
read_raw_output_first gate demanded ≥5 field transcripts read end-to-end
before the reducer policy froze. It felt ceremonial — the policy was
already coded from the frozen spec. It was not ceremonial.

**What the five reads caught that no unit test would have:**
1. **Case-fold spans** (runs 3, 6): the model returns evidence spans with
   lowercased first letters ("He also" → "he also"). Exact substring
   matching — the obvious spec reading of F3 — rejected honest evidence.
   The cure kept the guard but case-folded the containment.
2. **Duplicate codes** (run 3): one cluster emitted L03 twice → duplicate
   secondary entries. The judged ranking policy said nothing about
   dedup because nobody imagined a cluster voting twice.
3. **Merged-return contract** (run 1): python tools returning dicts merge
   into state rather than storing at state_key — `classification` simply
   vanished from output until declared as a state key. A framework fact
   I "knew" and still tripped on.

**Trap: spec_faithful_but_field_false.** Each defect was a place where
the frozen spec was *silent*, not wrong — and code written faithfully to
a silent spec is confidently incomplete. The unit fixtures I authored
all had clean capitalization, unique codes, declared keys — fixtures
inherit the author's imagination; field outputs don't.

**Heuristic.** For any LLM-boundary contract, the witness suite is not
done when the spec's clauses are covered — it is done when N raw field
outputs have been read and each surprise is either tolerated explicitly
(case-fold) or rejected explicitly (dedup, off-catalog codes), with a
witness naming the field run that motivated it. The gate's cost was ~10
minutes; each finding would have been a consumer bug report.

**Also banked:** `from __future__ import annotations` breaks Pydantic
models under file-path module loading (spec_from_file_location can't
resolve the postponed `Literal` string) — hyphenated example dirs force
file-path loading, so their node modules must not use postponed
annotations.

**Addendum (field runs 7–8): the two-strike rule for prompt fixes.**
The span-fidelity arc ran: exact match failed (case-folds) → tolerance
added → editing-by-omission caught → prompt hardened + temp 0.1 →
one-character inflection drift ("äitini" → "äitiini") STILL failed. Two
prompt-level fixes for the same defect class both failing is the signal
that the defect is not in the instructions — it is in the delegation.
Token-fidelity copying sits at the lowest, fully mechanizable
abstraction level of the prompt contract; the model was never the right
worker for it. The cure moved copying into code: the boundary now
treats the model's span as a *claim* and aligns it to the transcript
(repair ≥ 0.85 similarity, reject below — fabrications still die). This
is `prompt-as-subagent-contract` clause 3 in action: if the validator
can't trust a job to the model, the job belongs to code, and the
validator becomes a normalizer with a floor. Corollary heuristic: when
the SAME guard fires twice for the same failure class after a prompt
fix, stop rewording — split the level out of the prompt.

**Second seed:** two consecutive HP-36 runs gave different 0.98 primaries
(K86 vs A13) — both defensible matches. Per-cluster verdict variance is
now the dominant noise source. Would a race/self-consistency vote per
cluster (N=3, majority verdict, median confidence) be worth 3× the cost
for classification workloads — and could the map node express it
natively?

**Seed:** The raw-read gate is currently doctrine enforced by Judge
diligence. Could `graph lint` or the FR template mechanically require a
`field-runs:` section (N run logs + one surprise each) for any FR whose
graph contains an LLM node feeding a python validator — making the gate
structural, like RED-before-GREEN?
