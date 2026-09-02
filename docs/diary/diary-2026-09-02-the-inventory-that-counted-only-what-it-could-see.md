# The Inventory That Counted Only What It Could See

**Date:** 2026-09-02
**FR:** FR-951 — Declare UTF-8 at every first-party text boundary

## What happened

The FR opened with a number: 496. Ruff's `PLW1514` had enumerated every
first-party text boundary that inherits the host codec, six roots, counts
summing exactly to the total. The judge required the sum to reconcile, and it
did. That reconciliation felt like completeness.

Enforcement applied all 496 declarations. Then the very next required step —
regenerating `ARCHITECTURE.md` for the new capability — crashed:

```
File "scripts/aggregate_capabilities.py", line 135, in update_architecture
    text = ARCHITECTURE_MD.read_text()
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 800
```

A first-party read of a first-party file, undeclared, inside the tool the
deliverable depended on — and absent from an inventory whose arithmetic was
perfect. Ruff only fires where it can infer the receiver's type. A module-level
`Path` constant defeats it. So does a fixture argument. Grepping the six roots
for `read_text`/`write_text` without an encoding returned **1840** more sites:
the audit had seen 21% of its own subject.

AC-11 was what refused to let this pass. It scanned the Windows suite log for
raised Unicode exceptions and demanded zero. After the frozen diff it still
counted 255 decode and 45 encode failures — and *encode had gone up*, from 11
to 45, because fixing the reads let execution reach writes that had never run
before. The aggregate looked like a regression; it was progress moving the
failure downstream.

## Trap

**inventory_by_detector.** The tool's finding count was read as the size of the
class. But a detector's output measures *the detector's reach*, not the
phenomenon — and the reconciliation ritual (do the per-root counts sum to the
total?) validates internal consistency while saying nothing about coverage. A
perfectly reconciled inventory of 27% of a defect class is a more convincing
artifact than a rough estimate of 100%, and that is exactly what makes it
dangerous. This is `gate_checks_shape_not_substance` one level up: the FR
checked that the inventory's *arithmetic* was sound, never that its *census*
was.

The tell was available at planning time and was misread: the FR itself noted
that seven prior FRs already passed `encoding="utf-8"` "ad hoc". Those were
evidence that the idiom is used in code ruff never flagged.

## Heuristic

**Ask a second, dumber question of every detector-derived inventory.** Before
freezing scope from a tool's finding count, ask the crudest independent
question — a grep for the bare API name — and compare the magnitudes. If the
naive count exceeds the precise count by an order of magnitude, the precise
tool is a floor and the scope is a forecast, not a census. The naive query took
one command and would have changed the effort estimate, the deliverable table,
and the judge's freeze.

Corollary for gates: this one held only because AC-11 counted the *phenomenon*
(raised exceptions in a real run) rather than the *detector's* verdict (`ruff
exits zero`). A class-scoped outcome gate outranks a tool-scoped one, and when
the two disagree the tool is wrong. The shipped rule now has this weakness
written into the FR rather than papered over: PLW1514 cannot statically defend
the 1703 pathlib sites it never saw.

Second-order note: the mechanical fix regressed 46 tests because
`Path.read_text(encoding, ...)` takes encoding *positionally first*, so
`read_text("utf-8")` became `read_text("utf-8", encoding="utf-8")`. The AST
pass checked for a keyword and never asked about arity — the same blindness as
the inventory, at one-hundredth the scale. Detectors inherit the questions
their authors thought to ask.

## Seed

We reconcile inventories against themselves — do the parts sum to the whole? —
but never against a cheaper, independent estimator of the same population. What
would it cost to require every scope-freezing inventory in an FR to carry a
**second count from a deliberately dumber method**, with the ratio stated? And
if the two counts must agree before authority is granted, which of our currently
frozen scopes would fail that test today?
