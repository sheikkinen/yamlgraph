# Feature Request: FR-586 Prompt-monolith linter check (W026)

**Priority:** MEDIUM
**Type:** Feature (linter / developer experience)
**Status:** In Progress (enforced 2026-06-24 — see Implementation status)
**Effort:** 1–1.5 days
**Requested:** 2026-06-24
**Origin:** Graduated Seed from `docs/diary/diary-2026-06-24-the-hard-part-buried-in-bookkeeping.md`
**Evidence:** FR-584 (L5 prompt-only lever KILL), FR-585 (decode escalation), the 7-prompt plot_modeller audit

## Summary

Add a static linter check — **W026, the prompt-monolith warning** — to
`yamlgraph graph lint` that flags a prompt asking one LLM call to make too many
independent judgements at once. The check graduates a hard-won lesson: FR-584
proved that a single L5 prompt carrying ~12 fused jobs starves its one
load-bearing judgement (salience), and no wording fixes a starved judgement —
only decomposition does (FR-585). A subsequent audit found **4 of 7**
plot_modeller prompts share the shape. Today nothing catches this until a
precision wound and two killed FRs. W026 makes the smell visible at *authoring
time*, the way `radon` flags an overloaded function before it ships.

## Value statement

Graph authors get an immediate, free warning when a prompt fuses a discrimination
judgement with bookkeeping or a global cross-unit constraint — catching the
attention-overload anti-pattern in CI instead of after a model silently degrades
in production.

## Problem

A prompt's output schema *looks* like one task because it serialises as one
object, but `enables` + `motivation` + `threatens` (plot_modeller
`assign_causality`) is three cognitive acts wearing one bracket; `assign_pre_eff`
fuses twelve. FR-584's controlled A/B established the consequence empirically:
under that load the model cannot perform the hardest judgement (salience
discrimination), and prompt wording cannot rescue it. The fix is structural
decomposition (FR-585).

The framework already lints prompts for *mechanical* defects — unanchored
variables (W023), mixed template syntax (W024) — but has **no signal for
cognitive overload**, the defect that actually costs accuracy. The lesson
currently lives only in two diaries and three FRs; an author writing the next
monolith has nothing to warn them. The audit shows the pattern is not an L5 quirk:

| prompt | distinct judgements | W026 should |
|---|---|---|
| `extract_glosses` | 1 (decompose → beat) | stay silent |
| `classify_kinds` | 1 (kind + subject) | stay silent |
| `extract_goals` | borderline (salience tension) | (calibration boundary) |
| `extract_agents` | 3 sections | warn |
| `assign_causality` | 3 fused fields | warn |
| `assign_affects` | salience + arc-closure planning | warn |
| `assign_pre_eff` | 12 jobs | warn |

This 7-prompt corpus is the **calibration witness**: W026 must fire on the four
monoliths and stay silent on the two clean prompts, with `extract_goals` as the
documented boundary case.

## Proposed solution

A new check `check_prompt_complexity` in
`yamlgraph/linter/checks_prompts.py`, registered in `graph_linter.py` after
`check_mixed_template_syntax`, graph-driven (reusing the existing
node → prompt-path resolution so it lints exactly the prompts a graph uses).
Severity **warning** (a smell, not a defect — it must never break a build or
change lint exit semantics). Emits code **W026** with two complementary
detectors, because output is declared two different ways in practice:

**W026-1 — inline-schema field count.** When a prompt declares an inline
`schema:` / `output_schema:` with `fields:`, count top-level fields. At or above a
threshold (default **4**, configurable via lint config), warn that the prompt may
fuse independent judgements and suggest decomposition. (Nested fields under one
parent count as one — the signal is *independent top-level outputs*, not depth.)

**W026-2 — prose multi-output and global-constraint phrases.** Many prompts
describe their output in prose rather than an inline schema (all of plot_modeller
does). Two precise, low-false-positive regex families:
  - *enumerated multi-output*: `assign (two|three|four|five|\d+) (fields|slices|sections|outputs)`, `extract (three|\d+) sections` — fires on `assign_causality` ("THREE fields"), `assign_pre_eff` ("FOUR slices"), `extract_agents` ("three sections").
  - *global cross-unit constraint*: phrases that force the model to hold the whole sequence in mind while doing local work — e.g. `every .* (should|must) .* (later|close)`, `forward only`, `must .* later`, `exactly one .* and one`. Fires on `assign_affects` (arc-closure) and `assign_causality` (forward-only).

The message names the suspected fused jobs and links the remedy:

```
W026  Prompt 'assign_pre_eff' may fuse 4+ independent judgements ("assign FOUR
      slices") into one call — the hardest judgement can starve under load.
      Consider splitting discrimination from bookkeeping (see FR-585 decode
      pattern) or push global constraints to a deterministic post-pass.
```

**Calibration over cleverness.** The detector set is deliberately small and
curated. Precision (no false positives on clean prompts) outranks recall — a
linter that cries wolf gets disabled. The phrase list is seeded from the audit
corpus and may grow only with a new fixture proving the addition is warranted.

### Files

- `yamlgraph/linter/checks_prompts.py` — `check_prompt_complexity` + the
  threshold/phrase constants.
- `yamlgraph/linter/graph_linter.py` — register the check.
- `tests/unit/test_linter_prompt_monolith.py` — RED fixtures (the 7-prompt
  corpus or minimal analogues).
- `reference/graph-yaml.md` (or `reference/prompt-yaml.md`) — document W026 +
  the threshold config key.
- `ARCHITECTURE.md` — new REQ-YG-XXX row.
- `capabilities/CAP-XXX-prompt-monolith-lint.yaml` — capability registry entry
  (allocate next free CAP + REQ-YG IDs at enforcement).

## Acceptance criteria

- [ ] `check_prompt_complexity` added; emits W026 at **warning** severity only;
      `graph lint` exit semantics unchanged (clean/warnings-only → exit 0).
- [ ] **Calibration witness:** test asserts W026 fires on `assign_pre_eff`,
      `assign_causality`, `assign_affects`, `extract_agents` and stays silent on
      `extract_glosses`, `classify_kinds` (the 7-prompt corpus is the fixture).
- [ ] W026-1 threshold defaults to 4, exposed as a `field_threshold: int = 4`
      function parameter (no lint-config file); a test exercises a non-default
      value by passing the parameter directly. *(Amended — see Judgement A1.)*
- [ ] W026-2 regex families are unit-tested for both true positives (the audit
      phrases) and true negatives. The negatives MUST include the two
      knife-edge near-miss phrases — `extract_glosses` "Every major plot point
      should be its own beat" and `classify_kinds` "exactly ONE action type" —
      proving the curated regexes do not over-match. *(Amended — see Judgement A2.)*
- [ ] W026 appears in `yamlgraph graph lint --json` output (NDJSON, FR-151) like
      any other issue.
- [ ] Each new test tagged `@pytest.mark.req("REQ-YG-XXX")`; `req_coverage.py`
      passes; CAP file added.
- [ ] W026 documented in the linter reference + ARCHITECTURE.md.

## Out of scope (explicit)

- **No auto-decomposition / refactor.** W026 *detects*; splitting a prompt is the
  author's judgement (and FR-585's job for L5 specifically).
- **No LLM-based prompt critique.** The check stays static, deterministic, and
  CI-fast — an LLM judge would be slow, nondeterministic, and itself a monolith.
  Semantic critique is a separate, optional tool, not this linter rule.
- **No standalone `yamlgraph prompt lint <files>` CLI.** Graph-driven reuse is the
  MVP; a file-scoped command can follow if demand appears.
- **No input-variable counting.** The signal is *output* judgements, not input
  richness; a prompt may legitimately read many variables to make one decision.

## Alternatives considered

- **Error severity** — rejected; a monolith is a smell, not a contract violation,
  and many existing prompts would fail instantly. Warning lets authors adopt it
  incrementally (cf. W017 `on_error: skip`).
- **LLM-scored "judgement count"** — rejected for the linter (cost,
  nondeterminism); the static enumerated-output + global-constraint signals catch
  the documented cases cheaply and reproducibly.
- **Pure line-count threshold** — rejected; the audit's central finding is that
  *length is not the signal — judgement count is* (`classify_kinds` is 65 lines
  and clean). A line gate would mis-flag the clean prompts and miss compact
  monoliths.

## Related

- `feature-requests/FR-584-plot-modeller-L5-salience-and-roles.md` (the empirical KILL that motivates the rule)
- `feature-requests/FR-585-plot-modeller-L5-salience-gate-decode.md` (the decode remedy W026 points authors toward)
- `docs/diary/diary-2026-06-24-the-hard-part-buried-in-bookkeeping.md` (the audit + Seed)
- `yamlgraph/linter/checks_prompts.py`, `yamlgraph/linter/graph_linter.py` (W023/W024 precedent + registration)
- ARCHITECTURE.md REQ-YG-406 / CAP-151 (graph lint JSON output W026 must honour)

## Judgement (2026-06-24)

**Verdict: APPROVED — scope frozen with two binding amendments.** The FR is
clear, minimal, evidence-backed, and internally consistent. Every load-bearing
claim was verified against the codebase before granting authority.

### Verified
- **W026 is free.** Highest existing code is W025 (`checks_contracts.py`); W023/W024
  are the cited prompt-check precedent in `checks_prompts.py`. No collision.
- **Registration site is real.** `check_mixed_template_syntax` is wired in
  `graph_linter.py` `lint_graph()`; appending `check_prompt_complexity` there
  follows the exact `(graph_path, project_root)` signature every other check uses.
- **Calibration corpus is real.** All 7 prompts exist. Cited phrases confirmed:
  `assign_pre_eff` "assign FOUR slices"; `assign_causality` "assign THREE fields"
  + "FORWARD ONLY"; `assign_affects` "every arc you OPEN should CLOSE later";
  `extract_agents` "Extract three sections". `assign_pre_eff` carries no inline
  `schema:`, so it is caught by W026-2 (prose) not W026-1 — consistent with the
  FR's "two complementary detectors" rationale. No calibration claim is fictional.

### A1 — Purge the invented "lint config" interface *(binding)*
The linter has **no config mechanism**: every check is a pure
`(graph_path, project_root)` function with hardcoded constants (cf. W021/W022).
"Configurable via lint config" + "a test exercises a custom threshold" would
require inventing a config-file loader — a speculative interface the Purge
commandment forbids. **Resolution:** the threshold is a module constant surfaced
as a `field_threshold: int = 4` parameter on `check_prompt_complexity`. The test
exercises a non-default value by passing the argument directly. No config file,
no new surface. Acceptance criterion amended accordingly.

### A2 — Pin the knife-edge negatives *(binding)*
The two "stay silent" prompts both contain near-miss phrases: `extract_glosses`
"**Every** major plot point **should** be its own beat" and `classify_kinds`
"**exactly ONE** action type". The curated regexes stay silent only because they
demand a trailing `(later|close)` / `.* and one` the clean prompts lack — a
deliberate but fragile margin. **Resolution:** these two exact phrases are now
required members of the true-negative fixture set, so any future loosening of the
regexes is caught as a calibration regression. Acceptance criterion amended.

### Within scope as written (no change required)
- Warning severity (not error) — correct; matches W017/W022 incremental-adoption
  precedent.
- `extract_goals` left as documented boundary, asserted in neither fire nor
  silent list — internally consistent, no contradiction.
- CAP/REQ-YG ID allocation deferred to enforcement — matches repo convention.

**Authority granted to enforce** under the Sermon: RED fixture commit (7-prompt
corpus, `SKIP=pytest`) then GREEN (`check_prompt_complexity` + registration),
separately. Scope is frozen to the two detectors and the two amendments above —
no third detector, no LLM critique, no standalone CLI without a new FR.

## Implementation status (2026-06-24)

**Enforced.** RED → GREEN landed on `docs/dm-v3-paper-tests-and-v4-plan`:
- RED `62f9c4ce` — `tests/unit/test_linter_prompt_monolith.py` (ImportError) +
  CAP-172 / REQ-YG-473 registration + ARCHITECTURE.md sync.
- GREEN `c3769b4f` — `check_prompt_complexity` in `linter/checks_prompts.py`,
  registered in `linter/graph_linter.py` after `check_mixed_template_syntax`;
  changelog fragment.

### Decisions
- **IDs:** CAP-172, REQ-YG-473 (next free at enforcement). ARCHITECTURE.md is
  generated — synced via `scripts/aggregate_capabilities.py`, not hand-edited.
- **A1 honoured:** threshold is the `field_threshold: int = 4` parameter; the
  custom-threshold test calls `check_prompt_complexity(..., field_threshold=3)`
  directly. No lint-config file invented.
- **A2 honoured:** the two knife-edge negatives ("Every … should …",
  "exactly ONE …") are explicit fixture members; the corpus test asserts
  `FIRE <= fired` and `not (SILENT & fired)`.
- **Single W026 per prompt:** schema signal (W026-1) preferred; prose (W026-2)
  only if schema does not already fire — avoids double-warning one prompt.
- **Line-scoped regexes:** default `.` does not cross newlines, so `.*` stays
  within a line — no cross-sentence false positives (the A2 risk).

### Verification
- 7/7 FR-586 tests pass; 296 linter tests pass; `ruff` clean.
- **Real-prompt calibration** (production `examples/plot_modeller/graphs/*`):
  fires on `assign_pre_eff`, `assign_causality`, `assign_affects`,
  `extract_agents`; silent on `extract_glosses`, `classify_kinds`, and the
  boundary `extract_goals` — exactly the frozen calibration, on the real prompts
  not just analogues.

### Acceptance criteria
- [x] `check_prompt_complexity` added; W026 warning-only; exit semantics unchanged.
- [x] Calibration witness test (fire set / silent set).
- [x] `field_threshold` parameter; custom-threshold test.
- [x] W026-2 regex families unit-tested (true positives + knife-edge negatives).
- [x] W026 surfaced through `lint_graph` (and thus `graph lint --json`).
- [x] Tests tagged `REQ-YG-473`; `req_coverage --strict` passes; CAP-172 added.
- [x] W026 documented in `reference/graph-yaml.md` + ARCHITECTURE.md.
