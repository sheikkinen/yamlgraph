#!/usr/bin/env python3
"""Session Continuation Test Runner - FR-105

Demonstrates:
1. Copilot session continuation (does context persist?)
2. Human-in-the-loop interrupt (with mock input for automation)

Provides mock input for the interrupt node so the demo can run
without real user interaction.

Usage:
    python run_demo.py --genre noir --place "a rain-soaked phone booth"
"""

import argparse
import uuid
from pathlib import Path

from dotenv import load_dotenv

# Load environment from project root
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from langgraph.types import Command  # noqa: E402

from yamlgraph.graph_loader import (  # noqa: E402
    compile_graph,
    get_checkpointer_for_graph,
    load_graph_config,
)

GRAPH_PATH = Path(__file__).parent / "graph.yaml"


def run_session_test(genre: str, place: str):
    """Run the session continuation test with mock interrupt input."""
    print("\n" + "=" * 60)
    print("🎭 FR-105 Session Continuation Test")
    print("=" * 60)

    # Load and compile graph
    config = load_graph_config(str(GRAPH_PATH))
    graph = compile_graph(config)
    checkpointer = get_checkpointer_for_graph(config)
    app = graph.compile(checkpointer=checkpointer)

    # Unique thread for this run
    thread_id = str(uuid.uuid4())
    run_config = {"configurable": {"thread_id": thread_id}}

    # Initial state with genre
    state = {"genre": genre}

    print(f"\n📝 Genre: {genre}")
    print(f"📍 Meeting place (for interrupt): {place}")
    print("\n" + "-" * 60)
    print("Phase 1: Creating characters...")
    print("-" * 60)

    # First invocation - creates characters, then hits interrupt
    result = app.invoke(state, run_config)

    # Check for interrupt (ask_place node)
    interrupt_info = result.get("__interrupt__")

    if interrupt_info:
        # Show the interrupt question
        payload = interrupt_info[0].value if interrupt_info else "Input needed:"
        print(f"\n💬 Interrupt: {payload}")
        print(f"   Mock input: {place}")

        print("\n" + "-" * 60)
        print("Phase 2: Writing meeting scene (with session continuation)...")
        print("-" * 60)

        # Resume with the mock place input
        result = app.invoke(Command(resume=place), run_config)

    # Show results
    print("\n" + "=" * 60)
    print("📖 CHARACTERS CREATED (Node 1)")
    print("=" * 60)
    if "create_result" in result and result["create_result"]:
        cr = result["create_result"]
        print(cr.output if hasattr(cr, "output") else str(cr))

    print("\n" + "=" * 60)
    print("📚 MEETING SCENE (Node 3 - uses session continuation)")
    print("=" * 60)
    if "story_result" in result and result["story_result"]:
        sr = result["story_result"]
        print(sr.output if hasattr(sr, "output") else str(sr))

    # Verification
    print("\n" + "=" * 60)
    print("🔍 VERIFICATION")
    print("=" * 60)
    print("If session continuation works:")
    print("  - Node 3 should use the EXACT character names from Node 1")
    print("  - Node 3 should reference character traits from Node 1")
    print("  - The meeting should happen at:", place)
    print("\nIf session continuation fails:")
    print("  - Node 3 would invent new characters OR be confused")


def main():
    parser = argparse.ArgumentParser(description="FR-105 Session Continuation Test")
    parser.add_argument("--genre", default="noir", help="Story genre (default: noir)")
    parser.add_argument(
        "--place",
        default="a rain-soaked phone booth at midnight",
        help="Meeting place for the characters",
    )
    args = parser.parse_args()

    run_session_test(args.genre, args.place)


if __name__ == "__main__":
    main()
