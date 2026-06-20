# Feature Request: Promote `as_dict()` Boundary Coercion to Core Utility

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Closed (Rejected) — folded into `reference/patterns.md` Pattern 14
**Effort:** 1 day
**Requested:** 2026-06-20
**Closed:** 2026-06-20

## Resolution

Closed without core code changes. The Judgement (below) rejected the speculative
`as_dict()` core utility because the cited callsites are not semantic duplicates.
The single reusable artifact — a note naming the *distinct* coercion variants —
was folded into [reference/patterns.md](../reference/patterns.md) as **Pattern 14:
Boundary Coercion (Trust No Provider's Type)**. No CAP/REQ, no callsite refactor,
no `to_serializable` change. Docs-only outcome, per the prescribed minimal scope.

## Judgement (2026-06-20)

**Verdict: REJECT as written. Send back to Plan with a narrowed scope.**

The FR's load-bearing claim — "the same coercion is reinvented 7+ times; refactor
all callsites to `as_dict()` with no behavior change" — was verified against source
and is **false**. It is the `false_duplicate` trap: `hasattr(x, "model_dump")` is a
syntactic token match, not semantic equivalence. Each cited site differs downstream:

| Callsite | Actual semantics | `as_dict()` drop-in? |
|---|---|---|
| `map_compiler.py` L72 | model→dump, scalar **keeps original wrapper** (`result.append(item)`) | No — `as_dict` returns `{}`, loses wrapper |
| `map_compiler.py` L180/L207 | scalar preserved as `{"value": extracted}` | No — opposite of junk→`{}`; data loss |
| `utils/fsm/helpers.py` L40 | junk → **`None`** (guarded by `if d is not None`) | No — changes None contract |
| `utils/fsm/helpers.py` L65 (`json_safe`) | **recursive, primitive-preserving** | No — a `to_serializable` sibling; `str`→`{}` corrupts |
| `node_factory/guard_runtime.py` L26/L39 | `model_dump(exclude_none=True)` + `dict(rule)` fallback | No — drops `exclude_none` |
| `utils/guard_evaluator.py` L64 | extracts `.keys()` for the `keys` filter | No — not a coercion |

**Self-contradiction:** the Problem section cites this divergence as motivation
("some return `{}`, some return `None`, some recurse") yet the acceptance criteria
demand collapsing all sites into one function *with no behavior change*. Divergent
behaviors cannot be unified into one function while preserving every behavior.
Forcing the refactor would **introduce** bugs (scalar→`{}` data loss in
`map_compiler`; `exclude_none` loss in `guard_runtime`; recursion loss in
`json_safe`).

**Graduation signal collapses.** Exact-semantic duplicates of the proposed
`as_dict` reduce to ~1 (`book_reviewer::_as_dict`); `dungeon_master` uses a
tolerant-*parse* variant (parse → validate-into-typed-model), not coerce-to-dict.
By this FR's own rule (two = pattern doc, three = feature), the honest outcome is a
**documentation pattern**, not a core primitive + CAP + refactor sweep. Per
"the cheapest bug is the one killed in the spec," the speculative core utility with
a single real consumer is rejected.

### Prescribed minimal scope (for re-Plan)

1. **Document** the boundary-coercion family in `reference/patterns.md`, naming
   the *distinct* variants explicitly (dict-or-`{}`; dict-or-`None`; scalar-as
   -`{"value": x}`; recursive `to_serializable`/`json_safe`; `exclude_none` rule
   dicts). The lesson is "name the seam," not "unify the seams."
2. **Optionally** extract `as_dict()` into the `book_reviewer` example's local
   utils only if a *third independent* example reinvents the exact dict-or-`{}`
   form. Until then it stays example-local.
3. **Do not** touch `map_compiler`, `fsm/helpers`, `guard_runtime`,
   `guard_evaluator`, or `to_serializable`. Their coercions are correct and
   intentionally different.
4. No new CAP/REQ required for a docs-only change.

The original specification below is retained for the record but is **not** authorized.

---

## Summary

Promote the FR-059 "trust no provider's type" boundary-coercion idiom —
`value.model_dump() if hasattr(value, "model_dump") else value` — into a single
canonical core utility (`yamlgraph/utils/coercion.py::as_dict()`), and refactor
the duplicated callsites in core to use it.

## Value Statement

Graph and node authors get one audited, tested boundary-coercion primitive
instead of re-deriving the `hasattr(x, "model_dump")` dance at every seam where
an LLM-node's dynamically built schema instance meets a hand-written model —
eliminating a reinvented idiom that already appears 7+ times in core and in
example code.

## Problem

FR-059 established the boundary law: an `llm` node stores the executor's
*dynamically built* schema instance — a class distinct from our own models
despite sharing a name — so `OurModel.model_validate(that_instance)` rejects it.
The cure is to collapse the instance to a plain `dict` at the boundary where it
enters our code.

That cure is correct but **uncodified**. The same coercion is hand-rolled
independently across the codebase:

- [yamlgraph/map_compiler.py](../yamlgraph/map_compiler.py#L72) (3 sites: L72, L180, L207)
- [yamlgraph/utils/fsm/helpers.py](../yamlgraph/utils/fsm/helpers.py#L40) (L40, L65)
- [yamlgraph/utils/guard_evaluator.py](../yamlgraph/utils/guard_evaluator.py#L64)
- [yamlgraph/node_factory/guard_runtime.py](../yamlgraph/node_factory/guard_runtime.py#L26) (L26, L39)
- [yamlgraph/contrib/utils.py](../yamlgraph/contrib/utils.py#L31) (recursive `to_serializable` variant)
- [examples/book_reviewer/nodes/tools.py](../examples/book_reviewer/nodes/tools.py#L417) (`_as_dict`)

The `dungeon_master` example reinvents the *tolerant-parse* sibling of this idiom
in `parse_world_state` and `parse_seam_packet` (dict-or-junk → typed-or-empty).

Convergent reinvention across two independent examples **and** five core modules
is the Scripture's cross-project graduation signal: this is a missing primitive,
not application logic. The risk of leaving it uncodified is drift — each callsite
handles the `None`/junk/list edge cases slightly differently (some return `{}`,
some return `None`, some recurse), so a fix at one seam does not protect the
others.

## Proposed Solution

Add a small, pure, dependency-free module `yamlgraph/utils/coercion.py`:

```python
# yamlgraph/utils/coercion.py
from typing import Any


def as_dict(value: Any) -> dict:
    """Collapse a value to a plain dict at a provider boundary (FR-059).

    Accepts Pydantic model instances (incl. the executor's dynamically built
    schema classes), plain dicts, and junk. Never raises.

    - dict            -> returned as-is
    - has model_dump  -> value.model_dump()
    - anything else   -> {} (empty default; the boundary swallows junk)
    """
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}
```

Refactor the in-core duplicated callsites (map_compiler, fsm/helpers,
guard_evaluator, guard_runtime) to call `as_dict()`. The recursive
`contrib/utils.py::to_serializable` keeps its recursion but delegates its
leaf-level model coercion to `as_dict` semantics. Update the `book_reviewer`
example to import `as_dict` instead of its local `_as_dict`.

Document the pattern in `reference/patterns.md` under a new
"Boundary Coercion (Trust No Provider's Type)" section, cross-referencing FR-059.

## Decisions (resolved during investigation)

### D1 — Module home: `yamlgraph/utils/coercion.py` (not `contrib`)

The primary consumers are **core internals** — `map_compiler.py` (Layer 2),
`utils/fsm/helpers.py`, `utils/guard_evaluator.py`, `node_factory/guard_runtime.py`.
Under the three-layer import contract, core must **not** depend on `contrib`
(a Layer 3 user-facing convenience module). Therefore `as_dict()` lives in
`yamlgraph/utils/coercion.py`, which every layer may import. The `book_reviewer`
example imports from there too.

### D2 — REQ/CAP ownership: new `REQ-YG` under a new `CAP`

Investigation ruled out reusing existing IDs:

- **FR-059's REQ** belongs to *content-string* normalization
  (`normalize_content()` in `yamlgraph/utils/content.py`, owned by **CAP-117**
  and **CAP-171**). That coerces `response.content` (str-or-list-of-blocks) to a
  `str` — a **different boundary** than model-instance → dict. Do not reuse.
- **CAP-20 / REQ-YG-070** owns `to_serializable()` in `contrib/utils.py` — the
  recursive sibling — but is **contrib-scoped**, and core must not depend on
  contrib (see D1). Do not fold a core-utils primitive into a contrib CAP.

Decision: add a new `capabilities/CAP-XXX-boundary-coercion.yaml` with a fresh
`REQ-YG-XXX` covering `as_dict()` in `utils/coercion`. Tag the new tests with it.

### D3 — `to_serializable()` does **not** delegate to `as_dict()`

They are **siblings with distinct semantics**, not a delegation chain:

| Input | `to_serializable` | `as_dict` |
|-------|-------------------|-----------|
| `42` | `42` (primitives pass through) | `{}` (junk → empty) |
| nested model in a list | recurses, converts deeply | n/a (shallow) |
| `None` | `None` | `{}` |

`to_serializable` answers "make this whole tree JSON-safe (preserving primitives)";
`as_dict` answers "give me a dict-or-empty at *this* boundary." Routing one
through the other would break `to_serializable`'s primitive pass-through and its
recursion. `contrib/utils.py::to_serializable` stays **unchanged**; it is removed
from this FR's refactor scope. The patterns doc notes the two as a sibling pair.

## Acceptance Criteria

- [ ] `yamlgraph/utils/coercion.py::as_dict()` exists, pure, never raises (D1)
- [ ] Unit tests cover: dict pass-through, Pydantic instance, dynamically built
      schema instance, `None`, list, scalar junk → `{}`
- [ ] New `capabilities/CAP-XXX-boundary-coercion.yaml` with `REQ-YG-XXX`; tests
      tagged `@pytest.mark.req("REQ-YG-XXX")` (D2 — not FR-059's REQ, not REQ-YG-070)
- [ ] In-core callsites in `map_compiler.py` (×3), `utils/fsm/helpers.py` (×2),
      `utils/guard_evaluator.py`, `node_factory/guard_runtime.py` (×2) refactored
      to `as_dict()` with no behavior change (existing tests stay green)
- [ ] `contrib/utils.py::to_serializable` left unchanged (D3 — sibling, not a chain)
- [ ] `examples/book_reviewer/nodes/tools.py` imports `as_dict` (local `_as_dict`
      removed)
- [ ] `reference/patterns.md` documents the boundary-coercion pattern and notes
      `as_dict` / `to_serializable` as a sibling pair
- [ ] `lint-imports` passes (no new core→contrib dependency)
- [ ] Changelog fragment added in `changelog/unreleased/`

## Alternatives Considered

- **Leave it duplicated.** Rejected: drift across callsites already exists
  (different junk-handling), and the idiom is reinvented in new examples,
  guaranteeing recurrence.
- **Build a larger `yamlgraph/memory/` + `yamlgraph/seam/` + `yamlgraph/validators/`
  suite** (from the dungeon_master reflection). Rejected for now: those modules
  are domain-shaped (their value is the frozen antonym sets and lifecycle vocab,
  which do not generalize). Promoting their skeletons risks shipping empty
  abstractions (the `growth_as_default` / phantom-capability trap). They remain a
  *reference architecture*, not core code. This FR promotes only the one piece
  that is genuinely generic and already duplicated inside core.
- **A `CoercingModel` base class** that auto-coerces in a `model_validator`.
  Deferred: useful but broader; `as_dict()` is the minimal sufficient change and
  unblocks the duplicated callsites immediately.
- **Place `as_dict` in `contrib/utils` next to `to_serializable`.** Rejected
  (D1): core internals are the primary consumers and core must not depend on the
  Layer 3 `contrib` convenience module.
- **Make `to_serializable` delegate to `as_dict`.** Rejected (D3): distinct
  semantics (recursive + primitive-preserving vs shallow + junk-to-empty).

## Related

- FR-059 (Trust No Provider's Type) — the boundary law this codifies
- `the_one_law` / `downstream_fix` cure in `.github/copilot-instructions.md`
- Reflection on `dungeon_master` + `book_reviewer` convergent patterns
- Callsites: `map_compiler.py`, `utils/fsm/helpers.py`, `utils/guard_evaluator.py`,
  `node_factory/guard_runtime.py`, `contrib/utils.py`,
  `examples/book_reviewer/nodes/tools.py`
