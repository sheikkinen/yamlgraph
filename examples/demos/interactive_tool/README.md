# Interactive Tool Demo

Demonstrates `type: interactive_tool` (FR-049) — a single YAML node that
expands into a full multi-turn conversation loop at compile time.

## What It Shows

One node in the YAML:

```yaml
nodes:
  quiz:
    type: interactive_tool
    start: quiz_start
    step: quiz_step
    end: quiz_end
    resume_key: user_answer
    response_key: bot_response
    loop_until: "state.session_done == True"
    max_iterations: 10
```

Expands automatically into four nodes + wiring:

```
quiz__start → quiz__ask → quiz__step ↺ → quiz__end
                  ↑              │
                  └──────────────┘  (loop until session_done)
```

| Expanded Node | Type      | Purpose                         |
|---------------|-----------|---------------------------------|
| `quiz__start` | python    | Initialise session, first question |
| `quiz__ask`   | interrupt | Pause graph, show question to user |
| `quiz__step`  | python    | Score answer, serve next question  |
| `quiz__end`   | python    | Produce final summary              |

## Run

```bash
# Non-interactive (canned answers)
python examples/demos/interactive_tool/run.py

# Interactive (type your answers)
python examples/demos/interactive_tool/run.py --interactive

# Lint
yamlgraph graph lint examples/demos/interactive_tool/graph.yaml
```

## Key Concepts

- **No manual edge wiring** — `interactive_tool` handles the start→ask→step→end
  loop, including conditional routing via `loop_until`.
- **Deterministic tools** — quiz logic is pure Python, no LLM needed.
- **Checkpointer required** — interrupt/resume needs state persistence
  (`MemorySaver` used in `run.py`).
- **`max_iterations`** — safety guard against infinite loops (default 10).
