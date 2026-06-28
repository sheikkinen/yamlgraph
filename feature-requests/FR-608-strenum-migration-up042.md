# Feature Request: Migrate `(str, Enum)` schema enums to `enum.StrEnum` (UP042)

**Priority:** LOW
**Type:** Enhancement
**Status:** Judged — Authority GRANTED with corrections (2026-06-26)
**Effort:** 0.5 days
**Requested:** 2026-06-26

## Summary

Migrate the two production enum classes that inherit from both `str` and
`enum.Enum` to `enum.StrEnum`, clearing the ruff `UP042` rule. The affected
classes are `AffectKind` ([examples/plot_modeller/schema/affects.py](../examples/plot_modeller/schema/affects.py#L11))
and `FunctionKind` ([examples/plot_modeller/schema/kinds.py](../examples/plot_modeller/schema/kinds.py#L8)).

## Value Statement

Maintainers get a lint-clean tree under current ruff, removing latent debt that
will surface the moment the pinned pre-commit ruff is bumped — paid down
deliberately with a serialization audit rather than discovered during an
unrelated version bump.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, with two corrections.** A legitimate, well-scoped debt
paydown that correctly treats a mechanical-looking refactor as behavior-bearing. I verified
every claim: both classes are `(str, Enum)` (affects.py:11, kinds.py:8); UP042 fires on
**exactly** those two repo-wide under local ruff 0.15.18; the pinned pre-commit ruff is
`v0.8.6` (the silent-drift gap is real — red locally, green in CI). The behavior-change
characterization is also correct: on Python 3.11+, `f"{X.loss}"` for `(str, Enum)` yields
`"AffectKind.loss"` while `StrEnum` yields `"loss"` — a genuine `__str__`/`__format__` delta,
not a no-op, so holding it out of the FR-607 commit was the right call.

Most importantly, I confirmed the **frozen L7 gate is structurally immune**:
`evaluate.py` never imports or references `AffectKind`/`FunctionKind` — it operates entirely
on parsed YAML strings (`str(a).lower()`, `_norm()`, `dict.get("kind")`). The enum's
`__str__` cannot reach the gate. And the one site that looked risky, `f"{kind}.yaml"` in
`spike_affect_twopass.py:181`, uses `kind` from `_parse_set` → `_norm(k)` (a string), not
the enum member — so it stays `"loss.yaml"`. yaml/json serialization is likewise safe
because it reads the enum's underlying **string data** (`"loss"`), identical for both forms;
only explicit `str()`/f-string interpolation differs, and none feeds the gate. Two
corrections refine the AC.

1. **(PRIMARY) Be honest that this is behavior-NEUTRAL on the contract being pinned — it is
   a characterization guard, not a TDD RED.** The AC asks for a witness "committed RED
   against the pre-migration form." But the contract that matters (`.value == "loss"`,
   round-trip serialization) is *identical* before and after — there is no failing state to
   condemn, and manufacturing a fake RED is theater. The one place a real RED exists is the
   `__str__` delta itself (`f"{AffectKind.loss}"` is `"AffectKind.loss"` today, `"loss"`
   after) — but the audit proves *nothing depends on that*, so pinning it would pin a
   contract no caller uses. Resolution: (a) pin the serialization/`.value` contract as a
   plain characterization test (neutral, GREEN both sides — it guards future regressions),
   and (b) assert the `__str__` change *explicitly* as the one intentional behavior delta,
   so it is documented rather than discovered. Drop the RED framing; this is a refactor with
   a guard, not a bug fix with a condemnation.

2. **(secondary) Make the grep audit repo-wide, not examples-scoped.** The AC's audit
   targets call sites generally; state it explicitly as a **repo-wide** sweep (`yamlgraph/`,
   `tests/`, `scripts/`, plus `examples/`) for `str(<enum>)` / `f"{<enum>}"` of either
   class. The enums are example-local and the cross-package risk is low (UP042 was clean
   elsewhere), but the audit should prove that, not assume it.

**Endorsed:** correctly rejects the `# noqa` + confession alternative (doctrine removes debt,
doesn't document it); correctly decouples from the ruff bump (separate blast radius);
correctly identifies the frozen gate as the thing to protect — which I verified it cannot
touch. Python floor 3.11+ makes `StrEnum` unconditionally available; pydantic v2 treats
`StrEnum` identically for validation and `.value`.

**Frozen scope:** migrate `AffectKind` and `FunctionKind` to `enum.StrEnum`; a
characterization test pinning `.value` + round-trip serialization (GREEN both sides) and an
explicit assertion of the `__str__` delta; a repo-wide grep audit proving no direct
stringify site; `ruff --select UP042` clean; `pytest examples/plot_modeller` green (gate
untouched); no `# noqa: UP042` introduced.

## Problem

`UP042` (recommend `enum.StrEnum` over `(str, Enum)`) fires on exactly two
classes repo-wide under local ruff `0.15.18`:

```
UP042 Class AffectKind   inherits from both `str` and `enum.Enum`
UP042 Class FunctionKind inherits from both `str` and `enum.Enum`
```

The repo's pinned pre-commit ruff is `v0.8.6`, which predates the stabilized
rule, so the commit gate does **not** currently flag it. This is silent version
drift: the lint is red locally but green in CI. When the pinned ruff is next
bumped (a routine dependency update), `UP042` will block an otherwise-unrelated
PR. The cheapest time to fix lint debt is deliberately, with its own test, not
under the pressure of an unrelated bump.

This was surfaced while enforcing FR-607 (the lint was red on a file touched for
an unrelated reason). It was correctly held out of the FR-607 commit because the
fix carries a real behavior change (below) and belongs in its own scoped,
tested change.

## Behavior-Change Risk (why this is not a mechanical autofix)

`enum.StrEnum` changes `__str__`: for `class X(str, Enum)`, `f"{X.loss}"`
yields `"AffectKind.loss"`; for `StrEnum`, the same yields `"loss"`. Any site
that stringifies the enum **directly** (via `str()` or an f-string `{enum}`)
changes output. Sites that read `.value` are unaffected.

Audit of current call sites:
- `.value` access (SAFE): e.g. [validators/affects.py](../examples/plot_modeller/validators/affects.py#L21)
  `key = (delta.char, delta.kind.value)`.
- f-string of the unpacked value (SAFE): [validators/affects.py](../examples/plot_modeller/validators/affects.py#L28)
  `f"...unclosed affect {kind}({char})"` — `kind` here is the already-extracted
  `.value` string, not the enum.

No direct `str(enum)` / `f"{enum}"` site on `AffectKind`/`FunctionKind` was found
in the initial sweep, so the migration is expected to be behavior-neutral — but
the audit must be completed and pinned by a test before the change is trusted
(ruff `--unsafe-fixes` exists precisely because this is not provably safe in
general).

## Proposed Solution

```python
# examples/plot_modeller/schema/affects.py
from enum import StrEnum  # was: from enum import Enum

class AffectKind(StrEnum):  # was: class AffectKind(str, Enum)
    loss = "loss"
    ...
```

Same change for `FunctionKind` in `schema/kinds.py`. Pydantic v2 treats
`StrEnum` fields identically for validation and `.value` access, so
`AffectDelta.kind` / function-kind fields keep parsing and serializing the same
string values.

Python floor is already 3.11+ (`StrEnum` lands in 3.11), so no version guard is
needed.

## Acceptance Criteria

- [ ] `AffectKind` and `FunctionKind` inherit from `enum.StrEnum`.
- [ ] `ruff check --select UP042 examples/ yamlgraph/` reports zero errors.
- [ ] A witness test asserts the serialized string contract for both enums
      (e.g. `AffectKind.loss.value == "loss"` and that a round-tripped
      `AffectDelta` / function model keeps `kind` equal to the bare value),
      committed RED against the pre-migration `(str, Enum)` form if it would
      have differed, GREEN after.
- [ ] Full grep audit confirms no remaining direct `str(enum)` / `f"{enum}"`
      coercion of either class (only `.value` or already-unpacked strings).
- [ ] `pytest examples/plot_modeller` stays green (frozen L7 gate untouched).
- [ ] No `# noqa: UP042` introduced (the debt is removed, not suppressed).

## Alternatives Considered

1. **Suppress with `# noqa: UP042` + confession** — rejected. Adds a permanent
   confession for a rule the project agrees with; the doctrine prefers removing
   debt over documenting it. The enum *should* be `StrEnum`.
2. **Bump pinned pre-commit ruff and `--unsafe-fixes`** — rejected as the
   trigger. The ruff bump is a separate concern with broader blast radius; this
   FR scopes only the two-class migration so the bump, when it comes, lands on a
   tree already clean of `UP042`.
3. **Leave as-is** — rejected. The lint is genuinely red under current ruff and
   will block a future unrelated PR; paying it down deliberately is cheaper than
   discovering it under a bump.

## Related

- Surfaced during FR-607 enforcement (commit `36c4ef89`), held out deliberately.
- [examples/plot_modeller/schema/affects.py](../examples/plot_modeller/schema/affects.py#L11)
- [examples/plot_modeller/schema/kinds.py](../examples/plot_modeller/schema/kinds.py#L8)
- Pinned ruff: `.pre-commit-config.yaml` (`ruff-pre-commit` rev `v0.8.6`).
