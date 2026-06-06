# Dungeon Master

An interactive, checkpointed storytelling loop where you play the Dungeon
Master. Characters plan their turns in parallel, a narrator weaves the plans
into a single beat, and you steer the story every turn through an interrupt
window.

Built for **FR-466** (the DM turn loop) and the proving ground for **FR-467**
(conditional edges whose target is a `map` node).

## What it demonstrates

- **Interrupt loop** — `dm_window` pauses the graph each turn so the DM can
  steer; the run resumes with `Command(resume=...)`.
- **Parallel character planning** — `plan_all` is a `map` node: every cast
  member plans its turn concurrently, and the plans are collected for weaving.
- **Conditional-to-map routing (FR-467)** — `parse_dm` routes the `retry`
  action back to the `plan_all` **map** node while routing `end` to `END`. A
  conditional edge whose target is a map node now fans out correctly via
  `Send` instead of registering a second, unconditional router.
- **File-backed state** — beats are committed to chapter files only *after* the
  DM decision; `retry` re-rolls the same turn with no commit.

## Graph shape

```
load_story → prep_turn → plan_all (map) → weave → normalize_beat → dm_window (interrupt) → parse_dm
                ▲                                                                              │
                │  end ──────────────────────────────────────────────────────────────────► END
                │  retry ─────────────────────────────────────────────► plan_all (re-roll)
                └── commit_beat ◄── (accept / edit / nudge / next-chapter)
```

## Running it

First preplan a story skeleton (`story.json`):

```bash
yamlgraph graph run examples/dungeon_master/preplan.yaml \
    --var premise="A clockmaker discovers her city is a machine winding down" \
    --var output_dir=outputs/dungeon-master --full
```

Then drive the turn loop interactively:

```bash
python examples/dungeon_master/run.py --output-dir outputs/dungeon-master
```

Each turn you can steer with:

| Input            | Effect                                  |
|------------------|-----------------------------------------|
| `[Enter]`/`accept` | commit the beat as-is and advance     |
| `edit: <beat>`   | rewrite this beat, then advance         |
| `nudge: <hint>`  | commit, and steer the next turn         |
| `retry`          | re-roll this turn (no commit)           |
| `next-chapter`   | commit and advance the chapter          |
| `end`            | finish the story                        |

For a non-interactive run, pass a script of inputs:

```bash
python examples/dungeon_master/run.py --output-dir outputs/dungeon-master \
    --script "accept" "retry" "accept" "end"
```

## Files

| File | Role |
|------|------|
| `preplan.yaml` | Generates the `story.json` skeleton (synopsis, plot, cast). |
| `turn-loop.yaml` | The interactive turn loop (this example's core graph). |
| `run.py` | Interactive/ scripted driver wiring the interrupt resume cycle. |
| `nodes/story_io.py` | Python tools: load story, prep turn, parse DM input, commit beat. |
| `prompts/` | Character-plan and weave prompt templates. |
