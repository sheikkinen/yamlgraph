# The Lock That Skipped the Anchor

**Date:** 2026-06-13
**FR:** FR-478 (DM v2 — consistent button-press feedback)

## What happened

The DM web UI gave only the **Iterate** button an in-flight spinner. Accept and
the breadcrumb nav links fired multi-second LLM drafts with no feedback and no
double-press guard. The first plan was the obvious one: copy the spinner pattern
to every control and add `hx-disabled-elt="this"` for lockout.

The Judgement killed that plan before a line of code was written. Two findings:

1. `hx-disabled-elt` sets the HTML `disabled` attribute — **a no-op on `<a>`
   anchors**. The breadcrumb links are anchors. So the per-element lockout would
   have silently excluded exactly the controls the FR exists to fix. The asymmetry
   would have survived, invisibly.
2. The indicator and the breadcrumb both live *inside* `#app-body`, the swap
   target. Any in-region indicator is destroyed and recreated mid-request.

The cure was to stop thinking per-control and normalize at one boundary: a single
full-viewport `#busy` overlay anchored in `base.html` *outside* the swap target.
One element provides both the visible wait badge and the click shield, and it
covers buttons and anchors uniformly because it sits on top of all of them.

## The trap

**`vendor_default_as_help` / `plausible_wrong_answer`.** `hx-disabled-elt` is the
documented, idiomatic HTMX lockout — it *looks* correct, and it passes a shape
check (the attribute renders, the buttons disable). But on the one control type
that mattered it does nothing. The wrong answer was more plausible than the right
one because it came pre-blessed by the framework's own docs.

A second, smaller trap surfaced in the test itself: a per-line
`all('hx-indicator' in line)` assertion assumed each anchor renders on one line.
Jinja spread the anchor across five lines, so the check failed even though the
markup was correct. The test was reading the symptom (line layout) instead of the
invariant (every slow control points at `#busy`). Fixed by counting occurrences
(`busy == nav + 2`) — formatting-robust, intent-faithful.

## The heuristic

> When a lockout/feedback mechanism is per-control, enumerate the control *types*
> it must cover (button, anchor, form) and verify the mechanism is not a no-op on
> any of them. If it is, lift the mechanism to a single boundary above all
> controls rather than patching each type.

This is the boundary law again: don't guard at N downstream controls where one of
the guards silently fails on one control type — guard once, above, where the
shield covers everything.

## Seed

**Seed:** The overlay locks the client, but the server still accepts a concurrent
draft if a press slips through (e.g. keyboard activation before the overlay
paints). At what point does a single-user prototype's "the UI prevents it" become
a lie worth a server-side idempotency key — and is there a cheap structural test
that would catch the gap before a user does?
