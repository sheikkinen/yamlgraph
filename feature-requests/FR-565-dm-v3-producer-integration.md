# Feature Request: FR-565 DM v3 — producer integration (ignition key)

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced (2026-06-22)
**Effort:** 1–2 days
**Requested:** 2026-06-22

## Summary

Wire the v3 plot-plan authoring graph (`plot_plan.yaml`) into the DM generation lifecycle so
that the complete M0–M4b infrastructure — validated plan → exclusion seam → focalized beat
instruction — actually fires during book generation. Today every consumer seam (M1 exclusion in
`compile_opening_onepager`, M4b realize in `invoke_turn`) is wired and proven, but gated on
`attached_plot_plan(doc)`, which is always `None` because no production code ever invokes
`plot_plan.yaml` or calls `write_plot_plan`. This FR is the ignition key.

## Value Statement

DM maintainers get a `--plot-plan` flag on `generate.py` (and the HTTP session) that activates
the entire v3 lane end-to-end. A book generated with the flag has:
- authored beats proven spellable before a word is written (M0–M3 validation),
- presumed-dead characters excluded from chapter openings (M1 exclusion seam),
- focalized beat instructions steering the turn prose (M4b realize).

Without the flag, generation is byte-for-byte unchanged (dormancy invariant). The flag is the
sole new surface; every component it activates is already enforced.

## Problem

The design §1 data flow shows:

```
synopsis → author.py → validate.py → project.py → realize.py → turn_engine → prose
```

The first arrow (`synopsis → author.py`) never fires in the generation pipeline. `generate.py`
sequences: `weave(premise)` → `accept()` (derives roster) → `accept()` per character (last one
triggers `expand_chapters`) → `navigate(chapter:1)` → turn loop. There is no step between
chapter derivation and chapter play that invokes `plot_plan.yaml` or calls
`chapter_nav.write_plot_plan(doc, plan)`.

All infrastructure exists:
- `plot_plan.yaml` graph: complete, lints, routes deterministically (FR-563).
- `author_plot_plan.yaml` prompt: takes `premise` (synopsis text), returns JSON plan.
- `parse_plot_plan()`: tolerant boundary parse (FR-563).
- `write_plot_plan(doc, plan)`: gated write seam, raises `InvalidPlotPlan` (FR-563).
- `attached_plot_plan(doc)`: getter, returns `PlotPlan | None` (FR-560).
- `get_app(graph).ainvoke(state)`: graph execution pattern already used by `doc_ops` (FR-494).

The missing piece is one async function + one call site.

## Proposed Solution

### 1. `doc_ops.author_plot_plan()` — the producer function

A new async function in `doc_ops.py` that runs the authoring graph and attaches the result:

```python
async def author_plot_plan(doc: dict, story_dir: Path) -> None:
    """Author a v3 PlotPlan from the synopsis and attach it to the doc (FR-565).

    Runs ``plot_plan.yaml`` (author → validate → bounded repair), parses the output
    through the tolerant boundary, and writes the validated plan through the gated
    ``write_plot_plan`` seam. Persists to ``story_dir`` on success.

    The synopsis is the sole input — the same text the chapter outline derived from.
    When ``write_plot_plan`` raises ``InvalidPlotPlan`` (the repair budget was spent
    and the plan still has flaws), the exception propagates — the caller decides
    whether to abort or continue without a plan.
    """
    synopsis = doc.get("synopsis", {}).get("text", "")
    if not synopsis.strip():
        return
    result = await graph_app.get_app(
        "examples/dungeon_master/plot_plan.yaml"
    ).ainvoke({"premise": synopsis})
    plan_raw = result.get("plan_raw")
    if plan_raw is None:
        return
    from examples.dungeon_master.api.plot.author import parse_plot_plan
    plan = parse_plot_plan(plan_raw)
    chapter_nav.write_plot_plan(doc, plan)
    story_doc.write(story_dir, doc)
```

**Design choices:**
- Lives in `doc_ops.py` beside `expand_roster` / `expand_chapters` — the same layer that
  orchestrates derived artifacts between lifecycle stages. (`doc_ops.py` is at 371 lines;
  +15 brings it to ~386, within the 400-line warning / 450-line error gate — J5.)
- Reuses `graph_app.get_app().ainvoke()`, the existing graph execution pattern.
- The synopsis is the sole input to the authoring prompt (matches `author_plot_plan.yaml`'s
  `{{ premise }}` variable).
- **Triple validation is deliberate, not redundant (J1).** The plan is validated (1) inside
  `plot_plan.yaml`'s repair loop (the LLM's feedback channel), (2) by `write_plot_plan`'s
  gate (`validate_plan` runs before committing — FR-558 doctrine: bind the gate to the write,
  not the writer), and (3) implicitly by `parse_plot_plan` dropping off-alphabet atoms. Layer
  (1) gives the LLM a chance to repair; layer (2) is the un-bypassable contract. Neither is
  an optimization to remove.
- **`plan_raw` is the last authored attempt (J2).** When the graph's repair budget is spent
  (`loop_exits: {validate_plan: END}`), `plan_raw` holds the last repair attempt — which may
  still have flaws. The `write_plot_plan` gate is the contract that catches a flawed
  best-effort before it reaches the doc: `InvalidPlotPlan` fires and the caller's catch block
  skips the attach. AC5 covers this.
- Persist to `story_dir` so the plan survives session reloads.

### 2. Call site in `generate_story()` — the lifecycle hook (J3 option (b))

Insert in `generate.py`'s `generate_story()` between the last character accept (line 65) and
`navigate(chapter:1)` (line 75), exactly where the function already reads the doc (line 67):

```python
doc = story_doc.read(story_dir)
order = doc.get("chapters", {}).get("order", [])
if not order:
    raise RuntimeError("no chapters were derived from the synopsis")

# FR-565: author and attach a v3 plot plan (opt-in).
if enable_plot_plan:
    try:
        await doc_ops.author_plot_plan(doc, story_dir)
    except chapter_nav.InvalidPlotPlan:
        pass  # repair budget spent; continue without a plan

await session.navigate(f"chapter:{order[0]}")
```

**Why `generate_story()`, not `session.accept()` (J3):** `DMSession.__init__` takes only
`session_id: str` and is stateless — all state in the doc. Adding an `_enable_plot_plan`
attribute would widen the constructor for one caller's concern. Instead, `generate_story()`
already holds `doc` and `story_dir` at this point, so the call is direct. The web UI can add
its own call site independently — same function, different caller. No session class change.

**The `InvalidPlotPlan` catch is deliberate silence, not hedging.** The v3 lane is opt-in and
additive. A premise that defeats the authoring LLM (too ambiguous, too many characters, no
natural belief arc) should not block v2 generation — the book proceeds exactly as before. The
failure is visible in the story.json (no `plot_plan` key) and can be surfaced in the generation
log.

### 3. CLI flag on `generate.py`

```python
parser.add_argument(
    "--plot-plan", action="store_true",
    help="Author a v3 plot plan after cast derivation (activates belief exclusion + beat steering).",
)
```

Passed through to `generate_story(... enable_plot_plan=args.plot_plan)` as a parameter.
Default is `False` — existing generation is unchanged. No session class change (J3).

### 4. `generate_and_review.sh` — opt-in flag

```bash
"$PY" examples/dungeon_master/scripts/generate.py \
  --premise "$PREMISE" \
  --out "$OUT" \
  --turn-cap "$TURN_CAP" \
  ${PLOT_PLAN:+--plot-plan}
```

When `PLOT_PLAN=1 ./generate_and_review.sh ...` is set, the flag passes through. Without it,
no change. The demo-gate witness (`demo-output.log`) for this FR is a run **with** the flag.

## Acceptance Criteria (RED first)

RED commit (`SKIP=pytest`) lands failing tests; GREEN makes them pass. Example tests are
requirement-exempt (FR-474 J3): **no** `@pytest.mark.req`, **no** capability YAML.

1. **Producer→parse→gate→attach pipeline (J4).** `doc_ops.author_plot_plan(doc, story_dir)`
   with a mocked `get_app().ainvoke()` returning `fm.floodmark_json` attaches the plan to the
   doc: `attached_plot_plan(doc)` is not `None` and `validate_plan(plan).ok` is `True`.
   (Deterministic test, no LLM — the graph is mocked, the parse + gate are real.)
2. **Dormancy invariant.** A doc that never had `author_plot_plan` called has
   `attached_plot_plan(doc) is None`. (Deterministic test.)
3. **Graceful degradation.** When the mocked graph returns a `plan_raw` that fails validation
   (e.g., a world-revival variant), `author_plot_plan` raises `InvalidPlotPlan` and the doc has
   no `plot_plan` key. (Deterministic test.)
4. **CLI flag.** `generate.py --help` shows `--plot-plan`; the flag reaches `generate_story` as
   `enable_plot_plan=True`. (Deterministic test or inspection.)
5. **Existing seam tests pass (regression).** `test_plot_exclusion_seam.py` and
   `test_plot_realize.py` continue to pass unchanged — the consumer seams are not broken by the
   producer integration.
6. **End-to-end demo (AC5b).** `generate_and_review.sh` with `PLOT_PLAN=1` produces a
   `demo-output.log` showing the plan was authored and attached (grep for `plot_plan` in the
   story.json or log output). (Integration test, requires LLM — demo witness, not gated suite.)

## Fixtures

- Deterministic tests (AC1–AC3): mock `get_app().ainvoke()` to return `{"plan_raw": fm.floodmark_json}`
  or a world-revival-variant JSON. Use a `tmp_path` for `story_dir`.
- Integration/demo (AC6): a floodmark-class premise via `generate_and_review.sh`.

## Out of Scope

- **Web UI integration.** The HTTP routes (`graph_app.py`, `routes/`) can enable the flag
  independently; wiring the UI toggle is a separate FR.
- **Plan repair UX.** When `InvalidPlotPlan` fires, the session silently continues. A richer
  experience (show the flaws, let the user retry) is a UI concern, not a producer concern.
- **Plan editing / re-authoring.** Once attached, the plan is immutable for the book's lifetime.
  Re-planning mid-book is a future milestone.
- **Outline-aware planning.** The current prompt takes the synopsis only. Feeding the derived
  chapter outline (so the plan's `chapter` ordinals align with the actual chapter count) is a
  refinement — the plan's chapters are authored from the premise and may not match the outline's
  chapter count 1:1. Alignment is a successor FR.

## Dependencies

- **FR-563 (Enforced):** `plot_plan.yaml`, `parse_plot_plan`, `write_plot_plan`.
- **FR-564 (Enforced):** `beat_instruction`, `belief_at`, additive wiring in `invoke_turn`.
- **FR-560 (Enforced):** `exclusion_set`, `attached_plot_plan`, the exclusion seam.

## Risks

- **Plan/outline chapter mismatch (J6).** The plan and the chapter outline are authored
  **independently from the same synopsis**; chapter ordinal alignment is coincidental, not
  guaranteed. The plan's `chapter` ordinals are the LLM's guess; `expand_chapters` /
  `outline_chapters` independently decides the actual chapter count. If the plan says "reveal
  at ch6" but the outline only has 4 chapters, ch6 beats never fire (no chapter maps to ordinal
  6). The inverse is harmless: an 8-chapter outline with beats only at ch1 and ch6 means
  chapters 2–5 and 7–8 get empty `beat_instruction` — dormancy passthrough, byte-for-byte
  unchanged. Mitigated by the dormancy invariant and the plan's internal coherence (validation
  ensures the beat sequence is self-consistent). A future FR (Out of Scope: outline-aware
  planning) can feed the chapter count as a constraint to the authoring prompt.
- **LLM authoring cost.** The `plot_plan.yaml` graph adds 1–3 LLM calls (author + up to 2
  repair rounds) to the generation pipeline. Mitigated by the opt-in flag — default is off.
- **Flaky repair loop.** The bounded retry (3 rounds) may not converge for complex premises.
  Mitigated by graceful degradation (AC5) — the book proceeds without a plan.

---

## Judgement (2026-06-22)

**Verdict: APPROVE WITH CONDITIONS.** The FR is correctly framed and small in scope — one
function, one call site, one flag. The infrastructure it activates (M0–M4b) is proven by 474
tests; the remaining work is pure plumbing. The code sketch checks out against the as-built
contracts. Six conditions (J1–J6) must be folded before enforce; authority is granted once they
are.

**J1 — fold (blocking). Double validation is redundant but harmless — document the intention.**
The proposed `author_plot_plan` function calls `parse_plot_plan(plan_raw)` and then
`write_plot_plan(doc, plan)`. But `write_plot_plan` already calls `validate_plan(plan)` inside
the gate (chapter_nav.py:150–154). Meanwhile `plot_plan.yaml`'s validate node already ran the
same four checks during the author→validate→repair loop. So the plan is validated **three
times**: (1) inside the graph repair loop, (2) inside `write_plot_plan`'s gate, (3) implicitly
by the tolerant parse dropping off-alphabet atoms. Layer (1) is the LLM's feedback loop; layer
(2) is the write-seam contract (FR-558 doctrine: bind the gate to the write, not the writer).
Both are correct. But the FR text says the function "parses the output through the tolerant
boundary, and writes the validated plan through the gated write_plan seam" without noting that
the graph already validated it. Add a brief note so a future reader doesn't try to "optimize
away" the gate's re-validation (the gate is the contract, not an optimization).

**J2 — fold (blocking). The `plan_raw` output from the graph may be stale if repair ran.**
`plot_plan.yaml` has `state_key: plan_raw` on both `author_plan` and `repair_plan`. If the
repair loop fires, `plan_raw` is overwritten by the repair node. But the graph also has
`loop_exits: {validate_plan: END}` — when the loop budget is spent, the graph exits at
`validate_plan`, NOT at `repair_plan`. At that point `plan_raw` holds the **last repair
attempt** (the one that still had flaws), not the original. This is correct behavior (the last
attempt is the best-effort), but the FR must explicitly state: the `plan_raw` returned by the
graph is the **last authored attempt**, which may or may not validate. The `write_plot_plan`
gate is the contract that catches a stale/flawed best-effort before it reaches the doc. If
the best-effort has flaws, `InvalidPlotPlan` fires and the caller's catch block activates —
AC5 covers this. State it.

**J3 — fold (blocking). `generate.py` does not own the session; it cannot set
`session._enable_plot_plan`.** The FR says the CLI flag "sets `session._enable_plot_plan`."
But `DMSession.__init__` takes only `session_id: str` (session.py:139). The proposed
`_enable_plot_plan` attribute does not exist. Two options: **(a)** add an
`enable_plot_plan: bool = False` parameter to `DMSession.__init__` (the constructor plumbs
it), or **(b)** do not touch the session class — call `doc_ops.author_plot_plan` directly
from `generate_story()` between `expand_chapters` (the last `session.accept()` for a
character) and `session.navigate(chapter:1)`, exactly where `generate.py` already reads the
doc (line 67). Option **(b)** is cleaner: `generate.py` already holds the `doc` and
`story_dir` at that point, and the session is stateless (all state in the doc). The web UI
can add its own call site independently. Pick one; do not leave the plumbing undefined.
Recommended: **(b)** — it matches the stated "caller-controlled" principle without widening
`DMSession`'s constructor.

**J4 — fold (blocking). AC2 and AC3 already pass.** The FR says "a new test proves the wired
path fires, not just the seam in isolation" for both the exclusion seam (AC2) and the realize
seam (AC3). But `test_plot_exclusion_seam.py` already proves the wired path: it attaches
`fm.floodmark` to a doc and calls `compile_opening_onepager` — the real function, not a mock.
And `test_plot_realize.py` (FR-564) already proves `beat_instruction` and
`merge_beat_instruction` with the floodmark fixture. The **only new behavior** this FR adds
is: (a) `doc_ops.author_plot_plan` exists and calls the graph + write_plot_plan, (b) the
flag plumbing, (c) graceful degradation on `InvalidPlotPlan`. Rewrite the ACs to test **what
this FR actually builds**, not what prior FRs already proved. Specifically:
- AC2/AC3: delete or restate as "existing seam tests continue to pass" (regression, not new).
- Add an AC for the producer function itself: `doc_ops.author_plot_plan(doc, story_dir)` with
  a mocked `get_app().ainvoke()` returning `fm.floodmark_json` attaches the plan to the doc.
  This is the new deterministic test — it proves the producer→parse→gate→attach pipeline
  without an LLM.

**J5 — fold (minor). `doc_ops.py` is at 371 lines; adding `author_plot_plan` is safe but note
it.** The 400-line warning / 450-line error gate applies. The function is ~15 lines. At 386
lines post-change, it's within bounds but approaching the warning. Note it so the enforce does
not discover the gate mid-commit.

**J6 — fold (minor). The chapter/plan mismatch risk is under-specified.** The Risk section
says "if the plan says reveal at ch6 but the outline only has 4 chapters, ch6 beats never
fire." This is correct but incomplete. The inverse is also true: if the outline has 8 chapters
and the plan only has beats at ch1 and ch6, chapters 2–5 and 7–8 get empty `beat_instruction`
— which is fine (dormancy passthrough). But the plan's `chapter` ordinals are authored from
the premise (the LLM guesses how many chapters there will be), while
`expand_chapters`/`outline_chapters` independently decides the chapter count. The plan has no
knowledge of the outline's actual chapter count. State explicitly: the plan and outline are
authored independently from the same synopsis; chapter ordinal alignment is coincidental, not
guaranteed; a future FR (Out of Scope) can feed the chapter count as a constraint. This is
already implied but should be explicit so a reader doesn't assume the plan's `chapter` fields
are coordinated with the outline.

**Authority granted to enforce once J1–J6 are folded into the FR text.** Freeze scope to:
`doc_ops.author_plot_plan(doc, story_dir)` (async, runs `plot_plan.yaml` via
`get_app().ainvoke()`, parses through `parse_plot_plan`, attaches through `write_plot_plan`,
persists); one call site in `generate_story()` between the last character accept and
`navigate(chapter:1)` (J3 option (b)), gated on `enable_plot_plan` parameter, catching
`InvalidPlotPlan` silently; `--plot-plan` CLI flag on `generate.py`; `${PLOT_PLAN:+--plot-plan}`
passthrough in `generate_and_review.sh`. ACs: producer attaches a plan (mocked graph, deterministic),
dormancy invariant (no flag = no plan), graceful degradation (mocked graph returning a flawed plan),
CLI flag, end-to-end demo witness (live LLM, `demo-output.log`). Example-exempt (FR-474 J3): no
`@pytest.mark.req`, no capability YAML. RED commit first (`SKIP=pytest`). Changelog fragment + diary
required.
