# FR-719: SMT-Backed Condition Verification in the Graph Linter (Z3)

**Priority:** MEDIUM
**Type:** Enhancement (linter — static verification)
**Status:** Judged (2026-07-12) — scope frozen with F1/F2 encoding amendments; authority granted
**Effort:** 1.5 days
**Requested:** 2026-07-12
**Spawned by:** Z3 research 2026-07-12 — the condition language is exactly QF_LRA + equality; the runtime hedges condition gaps silently.

## Summary

Add a linter check family that translates expression-edge conditions to
Z3 formulas and proves three properties per source node's guard group:
no gap (exhaustiveness), no overlap (order-independence), no unreachable
edge (shadowing). Each violation reports a **concrete counterexample
state**. Z3 is an optional extra (`yamlgraph[verify]`); checks skip with
a notice when it is not installed.

## Value Statement

Graph authors get lint-time counterexamples for a bug class that today
manifests only as a silent `defaulting to END` WARNING in production —
`spec_kill`: the cheapest bug is the one caught before the graph runs.

## Problem

`routing.py` (expression router, first-match-wins ordered guards):

```python
# No condition matched - this shouldn't happen with well-formed graphs
logger.warning(f"No condition matched for {source_node}, defaulting to END")
return END
```

A condition gap does not crash — it **silently ends the graph**. This is
the silent-fallback class Commandment 6 forbids, and no existing check
(E1xx router, W801 condition syntax) can see it, because gap detection
over numeric thresholds requires interval reasoning:

```yaml
- {from: critique, to: publish, condition: "score >= 0.8"}
- {from: critique, to: retry,   condition: "score < 0.5"}
# score = 0.65 → silent END at runtime. Z3: SAT, model score = 0.65
```

Three aggravating facts:

1. **The reflexion/critique loop is the framework's flagship pattern** —
   numeric threshold guards are exactly where gaps hide.
2. **None-semantics make even "exhaustive" guards leaky**:
   `evaluate_comparison` returns False when the left value is None (or on
   TypeError) — so `score >= 0.5 or score < 0.5` still falls through when
   an upstream `on_error: skip` left `score` unset. A sound encoding must
   model this, or the checker itself becomes a `plausible_wrong_answer`.
3. **Hand-rolling interval analysis in the linter is the
   `regex_fourth_exclusion` trap verbatim** — reimplementing a decision
   procedure badly. The condition grammar (`COMPARISON_PATTERN`,
   `_split_compound`, `_NEGATE_OP` in `utils/conditions.py`) is a solved
   SMT fragment; the proper parser here is a proper solver.

## Proposed Solution

New module `yamlgraph/linter/patterns/conditions_smt.py` (~150 lines),
wired into `graph_linter.py` beside `check_race_patterns`.

### Translation

Reuse the **existing** condition parser — `COMPARISON_PATTERN` and the
quote-aware `_split_compound` — do not write a second grammar. Per
variable (dotted state path), declare a Z3 `Real`/`Bool`/`String` sort
inferred from the literals it is compared against, **plus** a companion
`Bool` `is_none_<var>`. Encoding per operator (F1 — faithful to
`evaluate_comparison`, which EXEMPTS `==`/`!=` from the None→False
rule):

| Runtime form | Z3 encoding |
|---|---|
| `v < / > / <= / >= lit` | `And(Not(is_none_v), v OP lit)` |
| `v == null` | `is_none_v` |
| `v != null` | `Not(is_none_v)` |
| `v == lit` | `And(Not(is_none_v), v == lit)` |
| `v != lit` | `Or(is_none_v, v != lit)` — runtime `None != 0.5` is **True** |

Compound precedence mirrors `evaluate_condition` exactly: or-split
first (Or), then and-split (And); the grammar has no parentheses.
Mixed-sort comparisons on one variable → skip-with-notice for that
group (mirrors runtime TypeError→False; do not guess).

Right-side resolution (F2): `_resolve_right_value` allows UNQUOTED
identifiers as state paths (`a > b`), falling back to literal string
when unresolvable — undecidable at lint time. Rule: an unquoted
identifier right side is encoded as a variable iff it is a known state
key (state_builder's key set for the graph) — with its own
`is_none` companion; otherwise, if it appears nowhere as a state key,
encode as string literal; if the graph's key set is unavailable,
skip-with-notice for that group. Never guess both ways.

### Checks (per source node with ≥ 2 expression edges, or 1 edge whose
target set does not include an unconditional fallback)

| Code | Property | Z3 query | Message payload |
|---|---|---|---|
| W803 | Gap — some state falls through to silent END | `Not(Or(c1..cn))` SAT? | counterexample model, e.g. `score = 0.65` or `score = <missing>` |
| W804 | Overlap — two guards both true, routing is order-dependent | `And(ci, cj)` SAT? (pairwise) | witness model + the two edge indices |
| W805 | Unreachable — guard shadowed by earlier guards | `And(ci, Not(Or(c1..ci-1)))` UNSAT? | shadowing edge list |

W803's `is_none` counterexamples are reported distinctly
(`score = <missing>`) — that variant fires even on syntactically
exhaustive guards and is the highest-value finding.

### Dependency policy

- `z3-solver` under a new optional extra `verify` in `pyproject.toml`
  (~30 MB wheel — never a core dependency; same pattern as `websearch`).
- Import guarded; when absent, the check family emits one informational
  skip notice (not per-node spam) and the linter proceeds. CI installs
  the extra so the gate has substance there.
- Solver calls bounded: `set_param timeout` (e.g. 2000 ms per query) —
  a solver hang must never hang `graph lint`.

### Out of scope (purge list)

- Reachability/dead-node analysis (plain traversal, E006 territory).
- Schema/type compatibility (Pydantic's domain).
- Termination proofs (loop limits already enforce mechanically).
- Router `routes:` label maps (string equality on LLM output — tolerant
  matching territory, not SMT).
- Any runtime use of Z3; lint-time only.
- Autofix suggestions beyond naming the gap interval.

## Acceptance Criteria

- [ ] AC-01 RED: fixture graph with the `score >= 0.8` / `score < 0.5`
      pair → W803 with a numeric counterexample in [0.5, 0.8)
- [ ] AC-02 None-semantics: syntactically exhaustive guards
      (`x >= 0.5 or x < 0.5`) still yield W803 with `x = <missing>`;
      adding an `x != null` guard (supported by the runtime grammar —
      verified: `null`/`none` are literal keywords and `==`/`!=` are
      None-exempt) or an unconditional fallback edge silences it
- [ ] AC-03 W804 overlap witness on `score >= 0.5` / `score >= 0.8`
      (both true at 0.9); W805 on a guard shadowed by earlier guards
- [ ] AC-04 Faithfulness witness: for every counterexample model the
      checker emits, replaying it through `evaluate_condition` confirms
      the fallthrough/overlap actually occurs — the encoding is tested
      against the runtime, not against itself. Parametrized to cover
      every row of the F1 operator table, INCLUDING `!= lit` with a
      missing variable (the case the pre-judgement encoding got wrong)
- [ ] AC-09 Variable-vs-variable and ambiguous-identifier right sides
      (F2): `a > b` with both known state keys → encoded, gap analysis
      runs; unknown identifier → string literal; key set unavailable →
      skip-with-notice — all three witnessed
- [ ] AC-05 Without z3 installed: single skip notice, exit code
      unchanged, all other checks run (unit test manipulates import)
- [ ] AC-06 Mixed-sort comparison group → skip-with-notice, no crash,
      no false verdict
- [ ] AC-07 Existing linter suite green; `examples/` and `graphs/` lint
      clean or with documented findings (run and record — a new check
      that fires on shipped examples must either be right or be fixed)
- [ ] AC-08 Solver timeout produces skip-with-notice for that group,
      never a hang or a false pass
- [ ] Changelog fragment; new REQ-YG-XXX + CAP entry (new lint
      capability); diary entry

## Judgement (2026-07-12)

Claims verified at source: the silent `defaulting to END` fallthrough
(`routing.py`), the regex grammar + quote-aware splitter
(`conditions.py`), `null`/`none` as literal keywords, W803–W805 free in
the code registry (E802 exists — different family, no clash), the
`websearch`/`storyboard` optional-extra precedent, and the absence of
any existing gap/overlap check.

| # | Finding | Resolution |
|---|---------|------------|
| F1 | **The FR's own encoding was unsound.** `evaluate_comparison` exempts `==`/`!=` from None→False (`operator not in ("==", "!=")`): runtime `None != 0.5` is True, `None == None` is True. The proposed uniform `And(Not(is_none), v OP lit)` would mis-encode `!=` and null-comparisons — a `plausible_wrong_answer` in a verification tool, the worst place for one | Encoding table rewritten per operator (see Translation); AC-04's faithfulness witness parametrized over ALL table rows including the corrected `!=` case. The checker is only as trustworthy as its replay witness |
| F2 | Right sides may be UNQUOTED state paths (`a > b`) or fall back to literal strings when unresolvable — the FR encoded literals only; lint-time cannot execute `_resolve_right_value` | Three-way rule (variable iff known state key / literal string / skip-with-notice), witnessed by new AC-09 |
| F3 | Single-conditional-edge nodes: the scope sentence was convoluted and partially overlapping with router-default checks | Simplified: the check family runs per source node over its expression-edge group of ANY size; a group whose targets include an unconditional edge is exempt from W803 (no gap possible) but still eligible for W804/W805 |
| F4 | CI substance: the skip-notice path (AC-05) must not become the ONLY path CI exercises | CI workflow installs `.[dev,verify]`; AC-07 runs with z3 present in CI. AC-05's z3-absent path is a unit test with import manipulation, both paths gated |

**Authority:** granted; scope frozen as amended. The dependency stays
optional forever — promotion of z3 to a core dependency would need its
own FR with field evidence.

## Alternatives Considered

- **Hand-rolled interval analysis** — rejected: `regex_fourth_exclusion`;
  and/or over comparisons with None-semantics IS a decision procedure;
  building a bad one to avoid a 30 MB optional wheel is false economy.
- **sympy / portion (interval libs)** — handle single-variable intervals
  but not compound multi-variable guards or equality over strings/bools;
  half the checks, same dependency argument.
- **Runtime hardening only** (raise instead of silent END) — worth doing
  independently but converts a silent bug into a production crash;
  lint-time counterexamples kill it in the spec. Not a substitute.
- **Do nothing** — the fallthrough WARNING has existed since the
  expression router was written; warnings without gates are advisory
  (`detection_without_enforcement`).

## Related

- `yamlgraph/utils/conditions.py` (`COMPARISON_PATTERN`,
  `_split_compound`, `_NEGATE_OP`, None/TypeError→False semantics)
- `yamlgraph/routing.py` (silent `defaulting to END` fallthrough)
- `yamlgraph/linter/patterns/` (check module pattern, FR-232 race checks)
- W801 (condition syntax) — W803–W805 extend the condition namespace
- Research: chat session 2026-07-12 (Z3 fit assessment)
