# FR-478: DM v2 — Consistent Button-Press Feedback (Busy Indicator + Lockout)

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Implemented (2026-06-13). Shipped exactly the frozen single-overlay
spec; the original two-mechanism proposal was consolidated to one overlay (see
*Judgement*). See *Implementation Status* at the end.
**Effort:** ~0.5 day (prototype)
**Requested:** 2026-06-13
**Judged:** 2026-06-13

**Continues:** FR-474 / FR-475 / FR-477 (the DM v2 web UI). Same J3 rules apply —
**no CAP/REQ, no CI gate, no demo-log**; the walkthrough tests under
`examples/dungeon_master/tests/` are a visibility harness, not a gate.

## Summary

Give every action button in the DM web UI the same in-flight visual feedback the
**Iterate** button already has, and prevent double-presses while a request is in
flight.

## Value Statement

The Dungeon Master gets immediate, uniform confirmation that a press registered —
no dead-feeling clicks on **Accept** or a breadcrumb during the multi-second LLM
draft, and no accidental double-submits.

## Problem

Every action swaps the whole `#app-body` region, and three of the four actions
trigger a **live LLM call** with multi-second latency:

| Press | Route | Slow LLM work | Feedback today |
|-------|-------|---------------|----------------|
| Iterate (weave) | `/story/synopsis/weave` | yes (weave) | `#gen-spinner` "⏳ Weaving…" ✓ |
| Accept | `/story/synopsis/accept` | yes (`accept` → `_accept_target` roster-expand + `_autodraft` of next stage) | **none** |
| Nav crumb | `/story/nav` | yes (`_autodraft` on entry to an unseeded node) | **none** |
| Edit (autosave) | `/story/synopsis/edit` | no (instant save) | none (acceptable) |

Only **Iterate** carries `hx-indicator="#gen-spinner"`. Pressing **Accept** or a
**breadcrumb** during a draft looks like nothing happened: the card sits still for
several seconds, the cursor gives no busy state, and a second impatient press
fires a second request. The feedback that already exists for one press should
exist for all of them.

### Why the current spinner is not directly reusable

`#gen-spinner` lives *inside* the stage-card form, which is itself inside
`#app-body`. Worse, the **breadcrumb is also rendered inside `#app-body`**
(`app_body.html` → `#app-shell` → `breadcrumb.html`), so every swap destroys and
recreates both. An indicator anchored anywhere inside the swap target cannot
remain stable for the full in-flight window, and cannot cover the breadcrumb
links. Only an element **outside `#app-body`** survives the swap.

## Proposed Solution

**One full-viewport busy overlay, anchored in `base.html` outside `#app-body`,
that provides BOTH the visible wait indicator AND input lockout for every press.**
The overlay is inert when idle and active only while a request is in flight; HTMX
toggles `.htmx-request` on the element named by `hx-indicator` for the request's
duration, and because the element lives outside the swap target it stays put.

### 1. A single overlay in `base.html` (outside `#app-body`)

A fixed, full-viewport container holding a small visible "⏳ Weaving…" badge (the
same wait icon as today). The container is `display: none` when idle (so it never
blocks normal clicks) and `display: block` while in flight (covering the viewport
so it both shows the badge and **shields every control from a second press** —
buttons and breadcrumb anchors alike).

```html
<!-- base.html, directly inside <body>, OUTSIDE #app-body -->
<div id="busy" aria-live="polite">
  <span class="busy-badge">⏳ Weaving…</span>
</div>
```

```css
#busy { display: none; }
.htmx-request#busy {           /* htmx marks the indicator element itself */
  display: block;
  position: fixed; inset: 0; z-index: 50;
  background: rgba(0,0,0,0.15);   /* faint dim; also captures clicks */
  cursor: progress;
}
.busy-badge {
  position: fixed; top: 0.75rem; right: 1rem;
  background: var(--bg-secondary); color: var(--accent);
  border: 1px solid var(--accent); border-radius: 4px;
  padding: 0.35rem 0.7rem; font-size: 0.85rem;
}
```

Because the overlay is `display: none` when idle, it captures no clicks during
normal use; while in flight it covers the viewport, so a second click on Accept,
Iterate, or any breadcrumb lands on the shield and is swallowed. This is the
lockout — one mechanism, no per-element `disabled` attribute.

### 2. Point every slow press at the overlay

`Accept`, `Iterate`, and every breadcrumb `<a hx-post="/story/nav">` gain
`hx-indicator="#busy"`. Iterate moves from `#gen-spinner` to `#busy`; the inline
`#gen-spinner` span and the now-dead `.htmx-indicator` rules are removed. The fast
`edit` autosave (`hx-trigger="change"`, `hx-swap="none"`) is left untouched.

```html
<button type="button" class="primary"
        hx-post="/story/synopsis/weave" hx-include="closest form"
        hx-indicator="#busy">↻ Iterate</button>
<button type="button"
        hx-post="/story/synopsis/accept" hx-include="closest form"
        hx-indicator="#busy">✓ Accept</button>
```

```html
<!-- breadcrumb.html -->
<a class="crumb…" href="#" hx-post="/story/nav" hx-indicator="#busy" …>…</a>
```

## Judgement (2026-06-13)

Verified against the live templates and HTMX 2.0.4 behaviour. Five binding
rulings, folded into the solution above:

- **J1 — One overlay, not two mechanisms.** The original proposal paired a corner
  indicator with per-button `hx-disabled-elt="this"`. A single full-viewport
  overlay delivers both the visible wait icon *and* lockout for every press,
  including breadcrumb anchors, with one element. Adopted.
- **J2 — `hx-disabled-elt` dropped.** `hx-disabled-elt` adds the HTML `disabled`
  attribute, which is a **no-op on `<a>` anchors** — it would not lock the
  breadcrumb links, re-introducing the very asymmetry the FR exists to remove.
  The overlay shield (J1) covers anchors and buttons uniformly, so
  `hx-disabled-elt` is removed from the spec entirely.
- **J3 — Indicator must live outside `#app-body`.** Confirmed the breadcrumb is
  rendered *inside* `#app-body`, so any in-region indicator is recreated mid-swap.
  `#busy` is anchored directly under `<body>` in `base.html`. Ratified.
- **J4 — Reuse htmx's element-self class toggle.** HTMX adds `.htmx-request` to
  the element referenced by `hx-indicator` for the request duration; the overlay
  uses `#busy { display:none } .htmx-request#busy { display:block }` and does NOT
  carry the `htmx-indicator` class (so the legacy `.htmx-indicator` display rules,
  now dead with `#gen-spinner` gone, are deleted rather than fought).
- **J5 — Acceptance is structural markup + one live check.** Busy *timing* and
  click-swallowing need a browser; the unit harness asserts only the rendered
  attributes/elements. Criteria tightened below.

## Acceptance Criteria (structural, per FR-474 J3)

- [ ] A single `#busy` overlay lives in `base.html` directly under `<body>`,
      outside `#app-body`, and is not re-rendered by any `#app-body` swap.
- [ ] `#busy` is `display: none` when idle and `display: block` (full-viewport)
      under `.htmx-request#busy`; it does NOT carry the `htmx-indicator` class.
- [ ] `Iterate`, `Accept`, and every breadcrumb nav link carry
      `hx-indicator="#busy"`; the inline `#gen-spinner` span and the dead
      `.htmx-indicator` CSS rules are removed.
- [ ] No element uses `hx-disabled-elt` (lockout is via the overlay shield).
- [ ] The `edit` autosave (`hx-trigger="change"`, `hx-swap="none"`) is unchanged.
- [ ] A walkthrough test asserts the rendered stage card and breadcrumb carry
      `hx-indicator="#busy"` on the action controls and that `#busy` exists in the
      page shell (markup assertions — busy *timing* is not unit-testable).
- [ ] Live manual check: pressing Accept and a breadcrumb both show the busy
      badge for the full draft, dim the viewport, and swallow a second press until
      the swap resolves.

## Out of Scope

- Per-button `hx-disabled-elt` (removed by J2 — the overlay shield is the lockout).
- Optimistic UI / skeleton cards (the swap is whole-region; a skeleton would need a
  separate pre-render path).
- A progress percentage or token-stream preview (turns are a single `ainvoke`, not
  streamed in this prototype).
- Any change to the `edit` autosave latency or a "Saved ✓" toast.
- Server-side debounce / idempotency keys (the overlay shield is sufficient for a
  single-user prototype).

## Alternatives Considered

- **Corner indicator + per-button `hx-disabled-elt` (the original proposal).**
  Rejected by J1/J2: two mechanisms, and `disabled` is a no-op on the breadcrumb
  `<a>` links, so the double-press asymmetry survives. The overlay covers both
  presses and anchors with one element.
- **Keep the per-button inline spinner, add one to the breadcrumb too.** Rejected:
  duplicates the indicator across fragments and re-renders it on every swap.
- **Server-side guard against concurrent drafts.** Deferred: unnecessary for a
  single-user prototype; the client-side overlay covers the real failure (an
  impatient double-press).

## Files (anticipated)

| File | Change |
|------|--------|
| `examples/dungeon_master/api/templates/base.html` | add `#busy` overlay element under `<body>`; add `#busy` / `.busy-badge` CSS; remove the dead `.htmx-indicator` rules |
| `examples/dungeon_master/api/templates/components/stage_card.html` | Iterate/Accept → `hx-indicator="#busy"`; drop `#gen-spinner` span |
| `examples/dungeon_master/api/templates/components/breadcrumb.html` | nav links → `hx-indicator="#busy"` |
| `examples/dungeon_master/tests/test_turn_prototype.py` (or a new UI test) | assert the `hx-indicator="#busy"` attributes on action controls + `#busy` present in the shell |

## Implementation Status (2026-06-13)

Shipped the frozen single-overlay spec; no deviation from J1–J5.

| File | What shipped |
|------|--------------|
| `api/templates/base.html` | `#busy` overlay (`<div id="busy"><span class="busy-badge">⏳ Weaving…</span></div>`) placed under `<body>`, outside and before `#app-body`; `#busy` / `.htmx-request#busy` / `.busy-badge` CSS added; the 3 dead `.htmx-indicator` rules removed |
| `api/templates/components/stage_card.html` | Iterate moved `#gen-spinner` → `#busy`; Accept gained `hx-indicator="#busy"`; `#gen-spinner` span removed |
| `api/templates/components/breadcrumb.html` | every `<a hx-post="/story/nav">` nav link gained `hx-indicator="#busy"` (non-clickable `<span>` crumbs untouched) |
| `tests/test_turn_prototype.py` | `test_busy_overlay_wires_every_slow_press`: asserts `#busy` exists before `#app-body`, no `gen-spinner`, ≥2 `hx-indicator="#busy"` on the synopsis card, and that on a turn page the overlay count equals nav-link count + 2 (the two card buttons) |

**Verification.** Full DM suite **18 passed** (17 prior + 1 new); `ruff check
examples/dungeon_master/` clean; live `TestClient` render confirms the overlay,
badge, `#busy`-before-`#app-body` ordering, Iterate→`#busy` wiring, and removal of
`gen-spinner` / legacy `.htmx-indicator` CSS. `hx-disabled-elt` appears nowhere
(J2). The live busy-timing/click-swallow check remains a manual browser step per
J5 (not unit-testable).

**Test-correctness note.** The first GREEN attempt failed because the breadcrumb
anchor renders across multiple lines, so a per-line `all(... in line)` check could
not see `hx-post` and `hx-indicator` together. Replaced with a formatting-robust
occurrence-count assertion (`busy_count == nav_count + 2`) — a fix to the test
harness, not a spec change.
