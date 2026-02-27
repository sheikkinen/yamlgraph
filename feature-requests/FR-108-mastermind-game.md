# Feature Request: FR-108 Mastermind Game

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-02-27

## Summary

A fully playable terminal Mastermind (code-breaking) game at `projects/mastermind/`, built using the `interactive_tool` node pattern. Pure Python game logic (no LLM required for core play); optional LLM hint node for players who want strategic advice.

## Value Statement

Game developers and framework evaluators see that YAMLGraph's `interactive_tool` node handles stateful turn-based games with structured feedback, reinforcing the framework as a general game-loop engine beyond LLM pipelines.

## Problem

The `interactive_tool` node has two showcases: a trivial 3-question quiz demo and the Minesweeper project. Both are grid/spatial games. A Mastermind game would:

1. Prove `interactive_tool` handles combinatorial logic with structured feedback (exact vs. misplaced pegs)
2. Add a non-spatial game archetype to the project portfolio — pattern deduction rather than board scanning
3. Demonstrate rich formatted feedback (colored pegs, guess history table) within the `response_key` pattern

## Proposed Solution

A `projects/mastermind/` package following the `interactive_tool` pattern established by the trivia quiz demo and the Minesweeper project.

### File Layout

```
projects/mastermind/
├── graph.yaml           # interactive_tool node wiring
├── run.py               # CLI entry point with default vars
├── tools/
│   ├── __init__.py
│   └── mastermind.py    # game_start / game_step / game_end
├── prompts/
│   └── hint.yaml        # LLM deduction hint (optional)
└── tests/
    └── test_mastermind.py
```

### graph.yaml

```yaml
version: "1.0"
name: mastermind
description: |
  Terminal Mastermind code-breaking game.
  Guess the secret code of colored pegs within the allowed number of turns.
  Commands: guess (e.g. "R G B Y"), h (hint), q (quit).
  Configure: --var colors=6 --var pegs=4 --var max_guesses=10

state:
  # Game configuration (from --var flags)
  colors: int
  pegs: int
  max_guesses: int

  # Game state (JSON-serialised)
  secret_code: str          # JSON list of color chars
  guess_history: str        # JSON list of {guess, exact, misplaced} dicts

  # Display
  board_display: str        # ASCII guess history + feedback
  message: str              # feedback line ("🎯 2 exact, 1 misplaced")

  # Player interaction
  player_input: str         # raw command from user

  # Session
  guess_count: int
  game_over: bool
  game_won: bool
  session_summary: str

tools:
  game_start:
    type: python
    module: projects.mastermind.tools.mastermind
    function: game_start
    description: "Generate secret code and render welcome screen"
  game_step:
    type: python
    module: projects.mastermind.tools.mastermind
    function: game_step
    description: "Evaluate guess, render feedback, check win/lose"
  game_end:
    type: python
    module: projects.mastermind.tools.mastermind
    function: game_end
    description: "Reveal secret code and generate game summary"

nodes:
  game:
    type: interactive_tool
    start: game_start
    step: game_step
    end: game_end
    resume_key: player_input
    response_key: board_display
    loop_until: "state.game_over == True"
    max_iterations: 50

edges:
  - from: START
    to: game
  - from: game
    to: END
```

> **Note:** No `vars:` block — defaults live in `run.py` only (consistent with FR-082 learnings).

### Game Rules

Classic Mastermind:
- Secret code: a sequence of `pegs` colored pegs drawn from `colors` available colors
- Colors: `R`ed, `G`reen, `B`lue, `Y`ellow, `O`range, `P`urple (first N used based on `colors` setting)
- Duplicates allowed in the secret code
- Each guess receives feedback:
  - **Exact** (🔴): correct color in correct position
  - **Misplaced** (⚪): correct color in wrong position
- Win: all pegs exact within `max_guesses` turns
- Lose: exhausted all guesses without cracking the code

### Player Commands

| Input | Action |
|-------|--------|
| `R G B Y` | Guess: space-separated color letters (must be exactly `pegs` count) |
| `h` | Request LLM deduction hint (optional, gracefully skipped if no API key) |
| `q` | Quit (sets `game_over=True`, `game_won=False`) |

### Board Rendering (ASCII)

```
🔐 Mastermind — Crack the code! (4 pegs, 6 colors: R G B Y O P)

  #  │ Guess       │ 🔴  ⚪
─────┼─────────────┼────────
  1  │ R G B Y     │  1   2
  2  │ R O B P     │  2   1
  3  │ _  _  _  _  │

Guesses remaining: 8
>
```

### Core Game Logic (mastermind.py)

Key functions:

- `game_start(state)` — generates random secret code from available colors, initialises empty guess history, renders welcome screen with color legend
- `game_step(state)` — parses `player_input`, dispatches to `_evaluate_guess` / `_hint` / `_quit`:
  - `_evaluate_guess`: computes exact and misplaced counts using standard Mastermind scoring algorithm (handle duplicates correctly), appends to history, checks win/lose
  - `_hint`: LLM-assisted deduction (guarded by `_HINT_PROVIDERS`)
  - `_quit`: sets `game_over=True`
- `game_end(state)` — reveals secret code, formats win/lose summary with guess count

### Scoring Algorithm

The standard Mastermind scoring with duplicate handling:

```python
def _score_guess(guess: list[str], secret: list[str]) -> tuple[int, int]:
    """Return (exact, misplaced) counts."""
    exact = 0
    secret_remaining = []
    guess_remaining = []

    # Pass 1: exact matches
    for g, s in zip(guess, secret):
        if g == s:
            exact += 1
        else:
            secret_remaining.append(s)
            guess_remaining.append(g)

    # Pass 2: misplaced (correct color, wrong position)
    misplaced = 0
    secret_pool = list(secret_remaining)
    for g in guess_remaining:
        if g in secret_pool:
            misplaced += 1
            secret_pool.remove(g)

    return exact, misplaced
```

### Hint Guard

Same pattern as FR-082 Minesweeper:

```python
import os
_HINT_PROVIDERS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "MISTRAL_API_KEY")

def _hint(state: dict) -> dict:
    if not any(os.getenv(k) for k in _HINT_PROVIDERS):
        return {"board_display": "💡 Hint unavailable (no LLM API key set)."}
    from yamlgraph.executor import execute_prompt
    result = execute_prompt("hint", {
        "guess_history": state["guess_history"],
        "colors": state["colors"],
        "pegs": state["pegs"],
    })
    return {"board_display": f"💡 Hint: {result.suggestion}\n   {result.reasoning}\n\n{state['board_display']}"}
```

### Hint Prompt (prompts/hint.yaml)

```yaml
name: hint
system: |
  You are a Mastermind deduction assistant. Given the history of guesses
  and their exact/misplaced feedback, use logical elimination to suggest
  the most informative next guess. Be concise: one sentence.
user: |
  Game: {{ pegs }} pegs, {{ colors }} colors (R G B Y O P).
  Guess history:
  {% for g in guess_history %}
  {{ g.guess | join(' ') }} → 🔴 {{ g.exact }}, ⚪ {{ g.misplaced }}
  {% endfor %}
  Suggest the best next guess and briefly explain your reasoning.
schema:
  name: HintResponse
  fields:
    suggestion: {type: str, description: "Recommended guess as space-separated colors, e.g. 'R G B Y'"}
    reasoning: {type: str, description: "One-sentence explanation of deduction logic"}
```

## Constraints

1. **No LLM for core gameplay** — `game_start`, `game_step`, `game_end` are pure Python. LLM is optional (hint only).
2. **Serialisable state** — Secret code and guess history stored as JSON strings in state (LangGraph compatibility).
3. **Standard defaults** — 4 pegs, 6 colors, 10 max guesses. Exposed via `--var` overrides; `run.py` supplies defaults.
4. **No external dependencies** — Standard library only for game logic (`json`, `random`).
5. **`interactive_tool` pattern only** — No custom node types. Must work with existing `type: interactive_tool` implementation.
6. **Projects directory** — Lives in `projects/mastermind/`, not `examples/`.
7. **Correct duplicate handling** — Scoring algorithm must handle duplicate colors in both secret and guess correctly (two-pass algorithm).
8. **Graceful hint fallback** — `h` command returns `"💡 Hint unavailable (no LLM API key set)."` when no API key is set. Must not raise.
9. **No `vars:` block in graph.yaml** — Defaults live in `run.py` only.
10. **Case-insensitive input** — Player guesses normalised to uppercase at the boundary.

## Acceptance Criteria

- [ ] `projects/mastermind/graph.yaml` exists, has no `vars:` block, passes `yamlgraph graph lint`
- [ ] State fields named `colors`, `pegs`, `max_guesses` consistent with `--var` CLI flags
- [ ] `projects/mastermind/tools/mastermind.py` implements `game_start`, `game_step`, `game_end`
- [ ] `game_start` generates random secret code, renders welcome with color legend
- [ ] `game_step` handles guess input, `h`, and `q` commands correctly
- [ ] `game_step` scores guesses with correct duplicate handling (two-pass algorithm)
- [ ] `game_step` validates input: rejects wrong peg count, invalid colors, with clear error messages
- [ ] `game_step` detects win condition (all exact) and sets `game_over=True, game_won=True`
- [ ] `game_step` detects loss (guess count >= max_guesses) and sets `game_over=True, game_won=False`
- [ ] `game_end` reveals secret code on loss, formats summary with guess count
- [ ] `h` command: calls `execute_prompt` only when at least one key in `_HINT_PROVIDERS` is set
- [ ] `h` command: returns fallback message when no key is set (no exception raised)
- [ ] `projects/mastermind/prompts/hint.yaml` exists with structured output schema
- [ ] `projects/mastermind/run.py` provides default vars (colors=6, pegs=4, max_guesses=10) and runs game
- [ ] `projects/mastermind/tests/test_mastermind.py` covers: code generation, guess scoring (including duplicates), input validation, win detection, loss detection, hint fallback
- [ ] All test functions carry `@pytest.mark.req("REQ-YG-XXX")` tags
- [ ] New requirements added to `ARCHITECTURE.md` and `ALL_REQS` / `CAPABILITIES` in `scripts/req_coverage.py`
- [ ] `pytest projects/mastermind/tests/ -q` passes
- [ ] `python scripts/req_coverage.py --strict` passes
- [ ] Smoke test: `yamlgraph graph run projects/mastermind/graph.yaml --var colors=6 --var pegs=4 --var max_guesses=10` starts without error

## Implementation Approach

### Phase 1 — Game Logic (TDD)

1. Write `test_mastermind.py` with cases for: scoring (exact, misplaced, duplicates), input validation, win/lose detection, code generation
2. Implement `mastermind.py` — `game_start`, `game_step`, `game_end`
3. Refactor: clean up JSON serialisation boundaries

### Phase 2 — YAML Wiring

4. Write `graph.yaml` (no `vars:` block; interactive_tool pattern)
5. Run `yamlgraph graph lint projects/mastermind/graph.yaml`
6. Write `run.py` with defaults (colors=6, pegs=4, max_guesses=10)
7. Smoke test: play one full game manually

### Phase 3 — Hint

8. Write `prompts/hint.yaml` with Jinja2 template and structured schema
9. Wire `h` command to `_hint()` with `_HINT_PROVIDERS` guard
10. Write hint-fallback test (no API key env var)

### Phase 4 — Traceability

11. Add requirements to `ARCHITECTURE.md`
12. Update `scripts/req_coverage.py` ranges and `CAPABILITIES` dict
13. Tag all tests with `@pytest.mark.req`
14. Run `python scripts/req_coverage.py --strict`

## Alternatives Considered

1. **LLM as code-maker** — Rejected. Secret code generation must be uniformly random; LLM-generated codes introduce bias and non-reproducibility.
2. **Knuth's minimax algorithm as built-in solver** — Rejected. Overengineered for a demo. LLM hint is sufficient and showcases the framework's LLM integration.
3. **Color emoji instead of letters** — Rejected. Terminal compatibility varies. Single uppercase letters are universal, accessible, and unambiguous.
4. **`examples/demos/` instead of `projects/`** — Rejected. A game with tests, tools, and prompts is a project, consistent with Minesweeper placement.
5. **`vars:` block for defaults** — Rejected. Not a recognised `GraphConfigSchema` field (FR-082 lesson).

## Related

- `projects/minesweeper/` — Sister game project (FR-082, not yet implemented) using identical `interactive_tool` pattern
- `examples/demos/interactive_tool/` — Canonical pattern this follows
- `feature-requests/FR-082-minesweeper-game.md` — Prior art for game feature requests
- `feature-requests/FR-049-interactive-tool.md` — The node type being exercised
- `ARCHITECTURE.md` — Requirements traceability target
- `scripts/req_coverage.py` — Coverage verification

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Date:** 2026-02-27

### Evaluation

| Criterion | Result | Notes |
|-----------|--------|-------|
| Scope clear & minimal | ✅ | Single `interactive_tool` game project. No framework changes. |
| No contradictions | ✅ | graph.yaml structure verified against `GraphConfigSchema` and `interactive_tool` validator. |
| Acceptance criteria measurable | ✅ | 18 checkable criteria: file existence, lint, specific behaviours, test coverage, traceability. |
| Implementation feasible | ✅ | All patterns exist in `examples/demos/interactive_tool/`. 1-day effort realistic. |
| Architecture alignment | ✅ | Follows 3-layer pattern (run.py / graph.yaml / tools/). Consistent with FR-082. |

### Findings

1. **Schema compliance verified.** All `interactive_tool` node fields (`start`, `step`, `end`, `resume_key`, `response_key`, `loop_until`, `max_iterations`) are valid per `validators.py:163-181`. The `state:` and `tools:` top-level blocks are handled by `state_builder.py` and `parse_python_tools()` respectively.

2. **Pattern consistency confirmed.** The proposed `graph.yaml` mirrors the canonical trivia quiz demo (`examples/demos/interactive_tool/graph.yaml`) exactly: same node type, same field names, same edge structure.

3. **No `vars:` block — correct.** Consistent with FR-082 lesson and `GraphConfigSchema` (which silently ignores unknown fields).

4. **`max_iterations: 50` is appropriate.** With `max_guesses=10` default, each guess + possible `h` command = ~2 iterations, so 50 provides safe headroom without being wasteful.

5. **Scoring algorithm is correct.** The two-pass algorithm (exact matches first, then misplaced from remaining) correctly handles duplicate colors — this is the standard Mastermind scoring method.

6. **Minor correction applied:** Updated Related section to note `projects/minesweeper/` is not yet implemented (FR-082 exists as spec only).

### Implementation Notes

- `guess_history` is stored as a JSON string in state. The `_hint()` function must deserialise it before passing to `execute_prompt()` so the Jinja2 template can iterate over it. This is an implementation detail, not an FR defect.
- Next available requirement IDs: REQ-YG-093 through REQ-YG-104, then REQ-YG-106+. Allocate from REQ-YG-093.
