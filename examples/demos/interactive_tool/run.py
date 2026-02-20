#!/usr/bin/env python3
"""Interactive tool demo — runs the trivia quiz graph.

Simulates a full multi-turn conversation using invoke + Command(resume=...).
Run from project root:

    python examples/demos/interactive-tool/run.py

Or interactively (reads from stdin):

    python examples/demos/interactive-tool/run.py --interactive
"""

from __future__ import annotations

import sys
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from yamlgraph.graph_loader import compile_graph, load_graph_config

GRAPH_PATH = Path(__file__).parent / "graph.yaml"

# Canned answers for non-interactive mode
CANNED_ANSWERS = ["Helsinki", "6", "Mercury"]


def main() -> None:
    interactive = "--interactive" in sys.argv

    # Suppress info logs for cleaner demo output
    import logging

    logging.getLogger("yamlgraph").setLevel(logging.WARNING)

    # Load, expand, compile
    config = load_graph_config(GRAPH_PATH)
    sg = compile_graph(config)
    graph = sg.compile(checkpointer=MemorySaver())
    run_cfg = {"configurable": {"thread_id": "demo-quiz-1"}}

    print("═" * 50)
    print("  🎯 Interactive Tool Demo — Trivia Quiz")
    print("═" * 50)
    print()

    # Turn 0: start the quiz
    result = graph.invoke({}, run_cfg)
    print(f"🤖 {result['bot_response']}")
    print()

    turn = 0
    while "__interrupt__" in result:
        if interactive:
            answer = input("You: ").strip()
            if not answer:
                break
        else:
            if turn >= len(CANNED_ANSWERS):
                break
            answer = CANNED_ANSWERS[turn]
            print(f"You: {answer}")

        result = graph.invoke(Command(resume=answer), run_cfg)
        print()
        print(f"🤖 {result.get('bot_response', '')}")
        print()
        turn += 1

    # Show summary if present
    if result.get("session_summary"):
        print("─" * 50)
        print(f"📊 {result['session_summary']}")

    print()
    print("═" * 50)
    print("  Demo complete")
    print("═" * 50)


if __name__ == "__main__":
    main()
