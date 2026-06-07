# The Cursor That Forgot to Weave — 2026-06-07

## What happened

Continuing the Dungeon Master v2 prototype, I extended the proven synopsis loop into
a chain of stages: collapse two generation modes into one `weave`, build a `STAGES`
registry so one `weave/edit/accept` path serves every stage, and add a Phase 2 plot
stage that reads the accepted synopsis as context. It all worked — tests green, live
eyeball confirmed the plot wove from the synopsis, the breadcrumb advanced.

Then the user accepted the synopsis and showed me a screenshot of the plot stage:
**a blank card.** The breadcrumb said `Story · Synopsis · Plot`, the prompt box sat
empty, and nothing told the DM what to do next. The architecture was correct and the
experience was a dead end.

## The root cause

`accept` did exactly what I wrote it to do: freeze the current stage and **advance a
cursor** (`doc["stage"] = next`). But advancing the cursor is not the same as
*producing the next artifact*. The plot card rendered blank because no one had run
the plot graph yet — and unlike the synopsis card, which seeds its prompt box with
the tagline, the plot card seeded nothing. So the stage that already held everything
it needed (the accepted synopsis, wired in as context) sat idle, waiting for a prompt
the DM might not even have.

The tell I walked past: I tested `accept` by asserting the *cursor moved* and the
*card rendered*, not that the DM *had something to react to*. A passing test for a
dead screen.

## The inversion that dropped a step

The detached v1 (`purgatory/preplan.yaml`) was a **batch pipeline**:
`synopsis → plot → chapters → cast` ran in one uninterrupted sweep. Each stage
consumed its predecessor's output *the instant it existed*. A blank stage was
impossible — by the time anything rendered, every stage was already populated. The
cost was the opposite: no human could steer between stages.

v2 **inverted** that into a per-stage human loop — and in doing so silently dropped
the "produce on entry" behavior that batch got for free. I added the gate (accept →
advance) but forgot to re-add the generation that the gate had interrupted. The
inversion preserved *steering* and lost *continuity*. The empty screen was exactly
the seam where the dropped step manifested.

## The fix

Auto-draft on entry. `accept` became async: it persists the acceptance and the cursor
advance **first** (so the acceptance survives even if drafting throws), then runs the
next stage's graph if that stage declares a `seed` and has no draft yet. The DM now
lands on a *populated* plot card — a real three-act arc woven from the synopsis they
just accepted — and iterates from there. This restores purgatory's "never empty"
continuity while keeping v2's per-stage gate. One new field on the `Stage`
dataclass (`seed`), one shared `_invoke_stage` helper, and the dead screen is gone.

## Heuristic

> **`cursor_is_not_artifact`** — When inverting a batch pipeline into an interactive
> per-step loop, the gate you add (advance / commit / approve) silently drops the
> *production* the batch did automatically between steps. Advancing a cursor is not
> producing the artifact. Tell: a step renders empty, or its input is present but its
> output is absent. Cure: at every gate that advances to a step with upstream
> context, decide explicitly whether entry should *produce* (auto-draft) or *wait*
> (seed the action) — never leave it blank. Test the step's *content on entry*, not
> just that the cursor moved and a card rendered.

## What good would have looked like

When I inverted batch→interactive, I should have enumerated what batch did *for free*
between stages — `B reads A's output the moment A finishes` — and asked, for each
adjacency, "in the interactive version, who triggers that now?" The answer ("nobody,
until a manual click") would have surfaced the empty screen at design time, in the
`STAGES` table, instead of in a screenshot after the fact. The cheapest place to catch
a dropped step is the adjacency list, not the running UI.

## Seed

When a stage can *produce on entry* (it has all its inputs as upstream context),
should "wait for a human prompt" ever be the default — or should auto-draft be the
default and `wait` the explicit opt-in? If every well-fed stage should draft on
entry, the `seed` field is really answering the wrong question; the right primitive
might be `on_entry: draft | wait`, making the batch-continuity behavior the norm and
the empty card an explicit, justified choice rather than an accident of omission.
