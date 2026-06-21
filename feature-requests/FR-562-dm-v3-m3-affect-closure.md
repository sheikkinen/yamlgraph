# Feature Request: FR-562 DM v3 M3 — affect closure (Lehnert plot-unit debt)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced (2026-06-21)
**Effort:** ~2 days
**Requested:** 2026-06-21

## Summary

Add the fourth and last hand-written narrative check — **affect closure** (design §5 check **4**) — to
`api/plot/validate.py`. Every opened affect unit (`AffectDelta(op="open", char, kind)`) must have a
later `close` of the same `(char, kind)`, unless the author explicitly marks that unit as an
intentional open ending. A plan that opens `loss` for a character and never closes it (the
**dropped-confrontation** class) yields a new `unclosed_affect` flaw localized to the opening beat.
This is milestone **M3** of
[`design-v3-plot-model-implementation.md`](../examples/dungeon_master/docs/design-v3-plot-model-implementation.md)
§7, building on the graduated `api/plot/` from FR-560 and the causal trio from FR-561.

The check is **pure** (no `unified-planning`): affect debt is narrative bookkeeping, not a
precondition, so the planner cannot and should not own it (design §3 note: "every opened affect unit
has a later close — narrative debt, not a precondition"). It slots into `validate_plan` alongside the
M1/M2 pure passes, preserving the no-engine path those passes rely on.

## Value Statement

DM maintainers get **emotional-arc debt** turned into a deterministic pre-prose proof. Today a book
can open a grief or guilt thread (a villainy, a betrayal) and silently never pay it off — the reader
feels the dangling thread, but no gate catches it until late prose review, if ever. M3 makes a
dropped affect unit *impossible to author unremarked*: either the plan closes it, or the author
states the open ending as intent. This completes the four-check narrative half of the validator
(lifecycle, grounding, antecedent, **closure**), leaving only M4 (live wiring) before the v3 lane is
feature-complete.

## Problem

After FR-561, `api/plot/validate.py` runs three pure checks (`_check_monotonic_lifecycle`,
`_check_belief_grounding`, `_check_causal_antecedent`) plus the optional `solve_status` causal proof.
`AffectDelta` is **carried but inert**: `schema.py` models `op`/`char`/`kind`, the floodmark fixture
populates a full open→close ledger (loss opened then closed, guilt opened then closed), but **nothing
reads it**. The schema docstring already flags this: *"Open or close one affect unit (Lehnert Plot
Units). Carried; closure is an M3 check."*

Two gaps:

1. **No closure check.** An `eff_affect=[AffectDelta(op="open", char=HILDE, kind="loss")]` with no
   matching later `close` is spellable. The `unclosed_affect` flaw code from design §2 has no emitter
   yet (it is deliberately absent from the M2 `FlawCode` Literal — FR-560 J4b: no code without an
   emitter).
2. **No intent escape hatch.** A deliberately tragic / unresolved ending (an affect left open on
   purpose) has no typed way to say so, so a naive closure check would force every plot to resolve —
   wrong for the genre.

## Proposed Solution

One pure check + one optional plan field + one fixture + one report column. No change to the M1/M2
checks, the projection, the causal encoding, or the live seam.

### Check 4 — affect closure (`validate._check_affect_closure(plan, order)`, pure)

Walk the **already-computed** `order` (J2: `validate_plan` computes `order = ordered_functions(plan)`
once and threads it to every pure check — `_check_affect_closure` takes `(plan, order)` like its
M1/M2 siblings and does **not** recompute the order). Maintain
`open_units: dict[(CharacterId, AffectKind), str]` mapping an open affect unit to the `id` of the
beat that opened it:

- `AffectDelta(op="open", char, kind)` → record/overwrite `open_units[(char, kind)] = fn.id`.
- `AffectDelta(op="close", char, kind)` → discharge: `open_units.pop((char, kind), None)`.

After the walk, every residual `(char, kind)` still in `open_units` is `unclosed_affect`, **unless**
that `(char, kind)` is listed in the plan's `intentional_open` allowlist. The flaw's `function_id` is
the opening beat's id (localization, mirroring the antecedent check), with a detail naming the
unclosed `(char, kind)`.

Existence/order semantics match the M1 grounding check: a `close` with no prior `open` is **not** a
flaw here (closure is a debt check, not a symmetry check — an unmatched close is harmless narrative
slack; tightening that is out of scope). Re-opening an already-open unit overwrites the opener id;
minimal and sufficient for the dropped-confrontation class.

**The ordered pop-walk is load-bearing (J3).** The debt is *not* a symmetric `+1/-1` count: a plan
that `close`s `(char, kind)` at an early beat and then `open`s the same unit at a later beat must flag
the later open as `unclosed_affect`. The `dict`-keyed `pop`-then-record walk over `order` produces
this correctly (the early close is a harmless unmatched-close; the late open is residual debt) — a
`collections.Counter` net-zero balance would wrongly pass it. This is **not** a free implementation
choice; acceptance criterion 6 witnesses it so a future "simplification" to a multiset count cannot
pass review (the FR-561-J5 lesson: witness the subtle behavior, don't let it be an accident).

### Schema — `PlotPlan.intentional_open` (optional, empty default)

Add a plan-level allowlist, following the `turn_budget` precedent (FR-561: optional field, default
leaves the canonical floodmark untouched):

```python
# Affect units the author deliberately leaves open (tragic / unresolved endings). Default empty,
# so a fully-resolved plan like floodmark is unaffected; list (char, kind) to exempt from closure.
intentional_open: list[tuple[CharacterId, AffectKind]] = Field(default_factory=list)
```

Per-unit, not a global boolean: a single flag would exempt *all* open affects and gut the check. The
allowlist localizes intent to the exact unit, so an author who means to drop one thread still gets
caught if they accidentally drop a second.

**Reconcile the design stub (J1).** The design §5 check-4 docstring describes the escape hatch as a
plan-level flag ("unless the plan is flagged intentional-open-ending"). This FR deliberately upgrades
it to the per-unit allowlist above; the enforce diff must update that design-doc docstring (or add a
one-line note beside it) to the per-unit form, so code and spec do not silently fork and a future
reader does not trust the stub and reintroduce the global flag (mirrors how FR-561 reconciled its J5
correction back into the design).

### `FlawCode` grows by one

`FlawCode = Literal["open_condition", "lifecycle_violation", "ungrounded_reveal", "unclosed_affect"]`
— the fourth and (for the narrative half) final code. The design §2 six-code set then lacks only
`unreachable`/`causal_threat`, which remain planner-owned (no pure emitter) per design §3.

### `report.py` — affect-ledger column

Extend the human-inspectable report with a per-unit affect ledger (opened-at / closed-at / **debt**),
consistent with the M1 exclusion/grounding columns, so a maintainer can eyeball which threads a plan
leaves open before running the gate.

## Acceptance Criteria (RED first)

A RED commit (`SKIP=pytest`) lands the failing tests; the GREEN commit makes them pass. Example tests
are requirement-exempt (FR-474 J3): **no** `@pytest.mark.req`, **no** capability YAML.

1. **Regression — canonical floodmark closes cleanly.** `validate_plan(floodmark).ok is True` and no
   flaw has `code == "unclosed_affect"` (the fixture opens loss+guilt and closes both).
2. **Dropped confrontation flagged.** A new `dropped_confrontation_variant` (floodmark with the final
   guilt-`close` removed) yields **exactly one** `unclosed_affect` flaw, whose `function_id` is the
   beat that opened the guilt unit, naming `(HILDE, "guilt")`.
3. **Intent escape hatch suppresses.** The same variant with `intentional_open=[(HILDE, "guilt")]`
   validates clean — `ok is True`, no `unclosed_affect`.
4. **Unmatched close is harmless.** A plan with a `close` and no prior `open` for some `(char, kind)`
   produces no `unclosed_affect` flaw (debt check, not symmetry check).
5. **Report renders the ledger.** `python -m examples.dungeon_master.api.plot.report floodmark` shows
   an affect column with zero debt; the dropped variant shows the open guilt unit as debt.
6. **Close-then-reopen is debt, not net-zero (J3).** A plan that closes `(char, kind)` at an early
   beat and reopens the same unit at a later beat yields **one** `unclosed_affect` flaw whose
   `function_id` is the *reopening* beat — proving the ordered pop-walk, not a `Counter` balance,
   backs the check.

## Fixtures

Add to `examples/dungeon_master/api/plot/floodmark.py`, alongside `early_reveal_variant` /
`world_revival_variant` (FR-560) and the FR-561 causal variants:

- `dropped_confrontation_variant`: the canonical floodmark with the reconciliation beat's
  `eff_affect=[AffectDelta(op="close", char=HILDE, kind="guilt")]` removed, so the guilt opened at
  the reveal beat is never discharged.
- `reopened_affect_variant` (J3 witness): a plan that closes a `(char, kind)` unit at an early beat
  and reopens the same unit at a later beat, so the residual debt sits on the *reopening* beat \u2014 the
  fixture criterion 6 asserts against to pin the ordered pop-walk.

## Out of Scope

- **Unmatched-close symmetry** (a `close` with no `open`): harmless slack, not a defect this milestone
  models.
- **Cross-character affect transfer / Lehnert composite plot units** (mutual, hidden-blessing, etc.):
  the `AffectKind` alphabet stays the M1 `loss`/`guilt` subset; widening it is a future milestone with
  its own fixtures (`regex_fourth_exclusion` discipline — grow the alphabet only when a check needs
  it).
- **Live wiring / generation impact:** M3 is still a dormant verification lane. Like M1/M2, it only
  fires on an explicit `PlotPlan`; the generator attaches none until **M4** (`author.py` +
  `doc["plot_plan"]`). Floodmark book generation is byte-for-byte unchanged.

## Dependencies

- FR-560 (Enforced): graduated `api/plot/` package, `ordered_functions`, `report.py`, floodmark
  fixtures.
- FR-561 (Enforced): `turn_budget` optional-field precedent, the `FlawCode`/pure-check pattern this
  extends.

## Risks

- **Genre over-fitting:** forcing closure could mis-flag legitimately open endings. Mitigated by the
  `intentional_open` allowlist (criterion 3) — the author states intent, the gate respects it.
- **Inert until M4:** like every v3 increment so far, M3 proves and reports but does not yet steer a
  generated chapter. This is the intended strangler-fig sequencing (design §0), not a gap.

## Judgement (2026-06-21)

**Verdict: APPROVE WITH CONDITIONS.** This is the cleanest milestone of the v3 arc so far. The check
is genuinely pure, the scope is tight, and it faithfully follows the M1/M2 precedent (one pure check,
one optional plan field defaulting to leave floodmark untouched, one `FlawCode` growth with an
emitter, one fixture, one report column). I verified every load-bearing claim against the code:

- **Floodmark ledger is fully closed** (`F1` opens `loss(Hilde)`; `Fr` closes `loss`, opens
  `guilt(Hilde)`; `Ff` closes `guilt`) — so criterion 1 (`ok is True`, no `unclosed_affect`) holds
  under the new check, and the dropped variant (delete `Ff.eff_affect`) leaves exactly the
  `guilt(Hilde)` opened at **`Fr`** residual ⇒ one flaw, `function_id == "Fr"` (criterion 2 correct:
  the opener is the reveal beat, not the deleted reconciliation beat).
- **No collateral flaws in the dropped variant**: a `Ff` stripped of `eff_affect` still fires; its
  `pre_belief believes(Clan, alive(Arnulf))=True` is produced by the earlier `Fr`, so the antecedent
  check stays silent — exactly one flaw, as claimed.
- **Design fidelity**: §5 row 4 ("hand-written, narrative debt, not a precondition"), §2 six-code
  literal, §7 M3 row, and the defect table ("Dropped confrontation → `unclosed_affect`") all match.
  `FlawCode` grows by exactly `unclosed_affect`; `unreachable`/`causal_threat` stay planner-owned
  (no pure emitter — FR-560 J4b honored).
- **Headroom**: `validate.py` is 209 lines, `report.py` 86, `floodmark.py` 211 — all comfortably
  under the 450 gate after the additions.

Three conditions, all **non-blocking folds** (no blocking defects — the spec is internally
consistent and the path is explicit).

**J1 — fold. The per-unit `intentional_open` allowlist deviates from the design's single flag;
witness the deviation, don't let the spec drift.** The design §5 check-4 stub docstring says "unless
the plan is flagged intentional-open-ending" — a *plan-level boolean*. The FR upgrades this to a
per-`(char, kind)` allowlist, and its reasoning is correct: a global flag would exempt *every* open
affect and gut the check, while the allowlist localizes intent so a second accidentally-dropped thread
still trips. Keep the allowlist — it is the better design. But record the divergence so code and spec
don't silently fork: update the design doc's check-4 docstring (or add a one-line note there) to the
per-unit form as part of the enforce diff, the way FR-561 reconciled J5 into the design. Without this,
a future reader trusts the stub and reintroduces the global flag.

**J2 — fold. Match the sibling signature; don't recompute the order.** The FR header writes
`_check_affect_closure(plan)` (echoing the design stub) but the body "walk[s] `ordered_functions(plan)`."
The M1/M2 siblings take `(plan, order)` and `validate_plan` computes `order = ordered_functions(plan)`
**once** and threads it to all of them. Enforce should give check 4 the same `(plan, order)` signature
and reuse the already-computed order — not call `ordered_functions` a second time inside the check.
Purely a consistency + single-traversal fold; no behavior change.

**J3 — fold (witness the order-sensitivity). The ordered pop-walk is load-bearing; pin it so a future
"simplification" to a multiset balance can't pass review.** The debt is *not* a symmetric +1/−1
count: a plan that `close`s `(char, kind)` at an early beat and then `open`s the same unit at a later
beat must flag the later open as `unclosed_affect` (a `Counter`-style net-zero would wrongly pass it).
The FR's `dict`-keyed `pop`-then-record walk over `ordered_functions` already produces the correct
result (the early close is the harmless unmatched-close of "Out of Scope"; the late open is residual
debt). Add **one** acceptance criterion that witnesses this exact close-then-reopen case yields a
`unclosed_affect` at the reopening beat — the FR-561-J5 lesson: witness the subtle behavior, don't let
it be an accident. This also forecloses the tempting but wrong `collections.Counter` implementation.

**Authority granted to enforce once J1–J3 are folded into the FR text.** Freeze scope to: the pure
`validate._check_affect_closure(plan, order)` emitting the one new `unclosed_affect` code; the optional
per-unit `PlotPlan.intentional_open` field (default empty); one `dropped_confrontation_variant`
fixture; the close-then-reopen witnessing AC (J3); a `report.py` affect-ledger column; and the
design-doc check-4 docstring reconciliation (J1). **No** unmatched-close symmetry check, **no**
`AffectKind` alphabet growth beyond `loss`/`guilt`, **no** engine call inside `validate_plan`, **no**
M4 live wiring. Example-exempt (no `@pytest.mark.req`, no capability YAML); `unified-planning` stays
optional (this check and the report run pure). RED commit first (`SKIP=pytest`): the acceptance tests
(five in the FR, six with the J3 witness) committed failing before `_check_affect_closure` exists.
Changelog fragment + diary required. Also tidy the stale dependency line — FR-561 is now **Enforced**,
not "enforcing."

## Enforcement (2026-06-21)

**Status: Enforced.** RED `8883b3f5` → GREEN `109d369d`. 450 DM tests green (was 444; +6 affect).

What landed, against the frozen scope:

- **Check 4 (pure).** `validate._check_affect_closure(plan, order)` — an ordered pop-walk over the
  order `validate_plan` already computes (J2: same `(plan, order)` signature as the M1/M2 siblings, no
  recompute). Residual opens → `unclosed_affect` localized to the opening beat. `dropped_confrontation_variant`
  (floodmark with `Ff`'s guilt-close removed) yields exactly one flaw, `function_id == "Fr"`, as judged.
- **J1 (per-unit allowlist + design reconciliation).** Added `PlotPlan.intentional_open:
  list[tuple[CharacterId, AffectKind]]` (default empty). Listing `(Hilde, guilt)` suppresses the
  dropped-variant flaw. The design-doc check-4 docstring was updated from the plan-level flag to the
  per-unit allowlist (+ the ordered-walk note), so spec and code no longer fork.
- **J3 (ordered pop-walk witnessed).** `reopened_affect_variant` (early close, later reopen of the
  same unit) yields one `unclosed_affect` on the **reopening** beat — acceptance criterion 6 pins it,
  foreclosing a `collections.Counter` net-zero implementation. The lone-close case stays harmless.
- **`FlawCode`** grew by exactly `unclosed_affect`. `unreachable`/`causal_threat` remain planner-owned
  (no pure emitter — FR-560 J4b honored). The four-check narrative half is now complete.
- **Report** gained an affect-ledger block (per-unit opened-at / closed-at / DEBT + an affect-closure
  verdict line). Verified: floodmark renders both units `closed`; the dropped variant shows
  `guilt(Hilde): opened@Fr closed@- -- DEBT` and `affect-closure: FLAW`.

No engine call inside `validate_plan` (stays pure); `unified-planning` untouched; no `AffectKind`
growth; no M4 wiring. Floodmark book generation is byte-for-byte unchanged.

Files: `api/plot/schema.py` (FlawCode + `intentional_open`), `api/plot/validate.py`
(`_check_affect_closure`), `api/plot/report.py` (affect ledger), `api/plot/floodmark.py`
(`dropped_confrontation_variant` + `reopened_affect_variant`), `tests/test_plot_affect_closure.py`
(6 tests), `docs/design-v3-plot-model-implementation.md` (check-4 docstring, J1).
