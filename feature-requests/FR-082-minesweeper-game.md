# Feature Request: FR-082 Minesweeper Game

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1.5 days
**Requested:** 2026-02-24

## Summary

A fully playable terminal Minesweeper game at `projects/minesweeper/`, built using the `interactive_tool` node pattern. Pure Python game logic (no LLM required for core play); optional LLM hint node for players who want a nudge.

## Problem

YAMLGraph demos demonstrate LLM workflows. But the `interactive_tool` node type — the framework's most powerful multi-turn primitive — has only one demo: a trivial 3-question quiz. A real game with state, board rendering, win/lose conditions, and configurable difficulty would:

1. Prove `interactive_tool` handles non-trivial loops with structured state
2. Serve as a canonical reference for the `start/step/end/loop_until` pattern
3. Show that YAMLGraph is a general game loop framework, not just an LLM pipeline

## Proposed Solution

A `projects/minesweeper/` package mirroring the `interactive_tool` demo structure.

### File Layout

```
projects/minesweeper/
├── graph.yaml           # interactive_tool node wiring
├── run.py               # CLI entry point
├── tools/
│   ├── __init__.py
│   └── minesweeper.py   # game_start / game_step / game_end
├── prompts/
│   └── hint.yaml        # LLM hint (optional, invoked on "h" command)
└── tests/
    └── test_minesweeper.py
```

### graph.yaml

```yaml
version: "1.0"
name: minesweeper
description: |
  Terminal Minesweeper. Commands: r ROW COL (reveal), f ROW COL (flag), h (hint), q (quit).
  Configure difficulty: --var rows=9 --var cols=9 --var mines=10

state:
  # Game configuration (set at start, from --var flags)
  rows: int
  cols: int
  mines: int              # --var mines=10  (consistent CLI name; no vars: block)

  # Board state (JSON-serialised for LangGraph compatibility)
  board_state: str        # JSON: 2D array of cell objects
  mines_placed: bool

  # Display
  board_display: str      # ASCII board for terminal output
  message: str            # feedback line ("💥 Boom!", "⚑ Flagged", etc.)

  # Player interaction
  player_input: str       # raw command from user

  # Session
  move_count: int
  game_over: bool
  game_won: bool
  session_summary: str

tools:
  game_start:
    type: python
    module: projects.minesweeper.tools.minesweeper
    function: game_start
    description: "Initialise board and render welcome screen"
  game_step:
    type: python
    module: projects.minesweeper.tools.minesweeper
    function: game_step
    description: "Apply player move, update board, check win/lose"
  game_end:
    type: python
    module: projects.minesweeper.tools.minesweeper
    function: game_end
    description: "Generate end-game summary"

nodes:
  game:
    type: interactive_tool
    start: game_start
    step: game_step
    end: game_end
    resume_key: player_input
    response_key: board_display
    loop_until: "state.game_over == True"
    max_iterations: 500

edges:
  - from: START
    to: game
  - from: game
    to: END
```

> **Note:** No `vars:` block is used — `vars:` is not a recognised `GraphConfigSchema` field and its values are silently discarded. All three difficulty vars (`rows`, `cols`, `mines`) are **required** via `--var` flags. `run.py` must document this and supply defaults explicitly before invoking the graph.

### Player Commands

| Input | Action |
|-------|--------|
| `r ROW COL` | Reveal cell at ROW, COL (0-indexed) |
| `f ROW COL` | Toggle flag at ROW, COL |
| `h` | Request LLM hint (optional, gracefully skipped if no API key) |
| `q` | Quit (sets `game_over=True`, `game_won=False`) |

### Board Rendering (ASCII)

```
  0 1 2 3 4 5 6 7 8
0 . . . . . . . . .
1 . . . . . . . . .
2 . 1 1 1 . . . . .
3 . 1 ■ 1 . . . . .   ■ = flagged, . = hidden, digit = revealed, space = empty
4 . 1 1 1 . . . . .
5 . . . . . . . . .
```

### Core Game Logic (minesweeper.py)

Key functions:
- `game_start(state)` — defers mine placement, renders initial board, sets `move_count=0`, `game_over=False`
- `game_step(state)` — parses `player_input`, dispatches to `_reveal` / `_flag` / `_hint` / `_quit`; flood-fill for empty cells; checks win condition; returns updated state dict
- `game_end(state)` — reveals full board with mine positions on loss, formats win/lose summary with move count

Mine placement is deferred until the first `r` command, guaranteeing the first reveal is never a mine (standard Minesweeper UX).

### Hint Guard (amended)

`game_step` must check for provider availability **before** calling `execute_prompt`. Exact guard:

```python
import os
_HINT_PROVIDERS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "MISTRAL_API_KEY")

def _hint(state: dict) -> dict:
    if not any(os.getenv(k) for k in _HINT_PROVIDERS):
        return {**state, "board_display": "💡 Hint unavailable (no LLM API key set)."}
    from yamlgraph.executor import execute_prompt
    result = execute_prompt("hint", {
        "board_display": state["board_display"],
        "flagged_count": _count_flagged(state),
        "hidden_count": _count_hidden(state),
    })
    return {**state, "board_display": f"💡 Hint: {result.suggestion}\n   {result.reasoning}\n\n{state['board_display']}"}
```

### Hint Prompt (prompts/hint.yaml)

```yaml
name: hint
system: |
  You are a Minesweeper assistant. Given the current board state,
  identify the safest move using logical deduction. Be concise: one sentence.
user: |
  Board:
  {{ board_display }}
  Known mines flagged: {{ flagged_count }}
  Remaining hidden cells: {{ hidden_count }}
  Suggest the single safest reveal move and briefly explain why.
schema:
  name: HintResponse
  fields:
    suggestion: {type: str, description: "Recommended move in 'r ROW COL' format"}
    reasoning: {type: str, description: "One-sentence explanation"}
```

## Constraints

1. **No LLM for core gameplay** — `game_start`, `game_step`, `game_end` are pure Python. LLM is optional (hint only).
2. **Serialisable state** — Board stored as JSON string in `board_state` (LangGraph state must be serialisable). Parsed/dumped at tool boundaries.
3. **Standard difficulty presets** — Beginner 9×9/10, Intermediate 16×16/40, Expert 30×16/99. Exposed via `--var` overrides; `run.py` supplies defaults (9/9/10) before invoking graph.
4. **No external dependencies** — Standard library only for game logic (`json`, `random`). No curses/terminal-control libs.
5. **`interactive_tool` pattern only** — No custom node types, no raw LangGraph API. Must work with existing `type: interactive_tool` implementation.
6. **Projects directory** — Lives in `projects/minesweeper/`, not `examples/`. Projects are production-grade standalone applications.
7. **First-move safety** — Mines placed after first reveal; first cell guaranteed safe.
8. **Graceful hint fallback** — `h` command returns `"💡 Hint unavailable (no LLM API key set)."` when no API key env var in `_HINT_PROVIDERS` is set. Must not raise.
9. **No `vars:` block in graph.yaml** — `vars:` is not a recognised schema field; defaults live in `run.py` only.
10. **State field name `mines`** — Not `mine_count`. Consistent with `--var mines=10` CLI flag.

## Acceptance Criteria

- [x] `projects/minesweeper/graph.yaml` exists, has no `vars:` block, passes `yamlgraph graph lint`
- [x] State field is named `mines` (not `mine_count`) throughout graph.yaml, tools, and tests
- [x] `projects/minesweeper/tools/minesweeper.py` implements `game_start`, `game_step`, `game_end`
- [x] `game_start` initialises board, defers mine placement, renders ASCII board
- [x] `game_step` handles `r ROW COL`, `f ROW COL`, `q` commands correctly
- [x] `game_step` performs flood-fill reveal for empty cells (adjacent mine count = 0)
- [x] `game_step` detects win condition (all non-mine cells revealed) and sets `game_over=True, game_won=True`
- [x] `game_step` detects loss (mine revealed) and sets `game_over=True, game_won=False`
- [x] First reveal is never a mine (deferred placement)
- [x] `game_end` reveals full board with mine positions on loss
- [x] `h` command: calls `execute_prompt` only when at least one key in `_HINT_PROVIDERS` is set
- [x] `h` command: returns `"💡 Hint unavailable (no LLM API key set)."` when no key is set (no exception raised)
- [x] `projects/minesweeper/prompts/hint.yaml` exists with structured output schema
- [x] `projects/minesweeper/run.py` provides default vars (9/9/10) and runs game via Python API
- [x] `projects/minesweeper/tests/test_minesweeper.py` covers: board init, reveal, flag, flood-fill, win detection, loss detection, first-move safety, hint fallback (no API key)
- [x] All test functions carry `@pytest.mark.req("REQ-YG-XXX")` tags (REQ-YG-090–095)
- [x] New requirements added to `ARCHITECTURE.md` and `ALL_REQS` / `CAPABILITIES` in `scripts/req_coverage.py`
- [x] `pytest projects/minesweeper/tests/ -q` passes (24/24)
- [x] `python scripts/req_coverage.py --strict` passes (CAP-31: 6/6 reqs, 24 tests)
- [ ] Smoke test: `yamlgraph graph run projects/minesweeper/graph.yaml --var rows=9 --var cols=9 --var mines=10` starts without error

## Implementation Approach

### Phase 1 — Game Logic (TDD)

1. Write `test_minesweeper.py` — red
2. Implement `minesweeper.py` — green
3. Refactor: clean up board serialisation

### Phase 2 — YAML Wiring

4. Write `graph.yaml` (no `vars:` block; state field `mines`)
5. Run `yamlgraph graph lint projects/minesweeper/graph.yaml`
6. Write `run.py` with default vars (9/9/10) injected before graph invocation
7. Smoke test: play one full game manually

### Phase 3 — Hint

8. Write `prompts/hint.yaml`
9. Wire `h` command to `_hint()` with `_HINT_PROVIDERS` guard
10. Write hint-fallback test (no API key env var)

### Phase 4 — Traceability

11. Add requirements to `ARCHITECTURE.md`
12. Update `scripts/req_coverage.py` ranges and `CAPABILITIES` dict
13. Tag all tests with `@pytest.mark.req`
14. Run `python scripts/req_coverage.py --strict`

## Alternatives Considered

1. **Full curses TUI** — Rejected. `curses` requires terminal control that conflicts with YAMLGraph's streaming output. ASCII rendering is sufficient and avoids the dependency.
2. **LLM as game engine** — Rejected. Minesweeper requires deterministic rules. LLM as hint oracle is appropriate; LLM as arbiter is not.
3. **`examples/demos/` instead of `projects/`** — Rejected. Demos are lightweight single-file showcases. A game with tests, tools, and prompts is a project.
4. **Custom node type for game loop** — Rejected. `interactive_tool` already provides start/step/end/loop_until semantics. No new primitives needed.
5. **`vars:` block for defaults** — Rejected. `vars:` is not a recognised `GraphConfigSchema` field; defaults live in `run.py` only.

## Related

- `examples/demos/interactive_tool/` — Canonical pattern this follows
- `projects/ninchat/`, `projects/incaller/` — Existing project structure reference
- `feature-requests/FR-049-interactive-tool.md` — The node type being exercised
- `ARCHITECTURE.md` — Requirements traceability target
- `scripts/req_coverage.py` — Coverage verification

## Amendment Log

| Date | Issue | Resolution |
|------|-------|------------|
| 2026-02-24 | `vars:` block silently discarded by `GraphConfigSchema` | Removed `vars:` block; defaults moved to `run.py` |
| 2026-02-24 | Name mismatch `mine_count` (state) vs `mines` (CLI var) | Renamed state field to `mines` throughout |
| 2026-02-24 | Hint invocation mechanism underspecified; `execute_prompt` raises without API key | Added `_HINT_PROVIDERS` guard with explicit fallback message |
