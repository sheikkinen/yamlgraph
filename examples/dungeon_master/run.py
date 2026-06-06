#!/usr/bin/env python3
"""Run the dungeon-master turn loop over a preplanned story (FR-466, Phase 3).

Preplan a story first, then drive the turn loop:

    yamlgraph graph run examples/dungeon_master/preplan.yaml \\
        --var premise="A clockmaker discovers her city is a machine winding down" \\
        --var output_dir=outputs/dungeon-master --full

    python examples/dungeon_master/run.py --output-dir outputs/dungeon-master

Each turn the characters plan in parallel, the narrator weaves a beat, and you
(the DM) steer:

    [Enter]/accept     commit the beat as-is and advance
    edit: <new beat>   rewrite this beat, then advance
    nudge: <hint>      commit, and steer the next turn
    retry              re-roll this turn (no commit)
    next-chapter       commit and advance the chapter
    end                finish the story
"""

import argparse
import uuid

from langgraph.types import Command

from yamlgraph.graph_loader import (
    compile_graph,
    get_checkpointer_for_graph,
    load_graph_config,
)

GRAPH = "examples/dungeon_master/turn-loop.yaml"


class C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"


def _is_done(app, run_config) -> bool:
    state = app.get_state(run_config)
    return not (getattr(state, "next", None) or [])


def run() -> None:
    parser = argparse.ArgumentParser(description="Dungeon Master turn loop")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="outputs/dungeon-master",
        help="Directory containing the preplanned story.json",
    )
    parser.add_argument(
        "--script",
        nargs="*",
        default=None,
        help="Non-interactive DM inputs to replay (for demos/tests)",
    )
    args = parser.parse_args()

    config = load_graph_config(GRAPH)
    graph = compile_graph(config)
    checkpointer = get_checkpointer_for_graph(config)
    app = graph.compile(checkpointer=checkpointer)

    run_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    scripted = list(args.script) if args.script is not None else None

    print(f"\n{C.BOLD}{'=' * 60}{C.RESET}")
    print(f"{C.BOLD}📖 Dungeon Master — Turn Loop{C.RESET}")
    print(f"{C.BOLD}{'=' * 60}{C.RESET}\n")

    app.invoke({"output_dir": args.output_dir}, run_config)

    while not _is_done(app, run_config):
        state = app.get_state(run_config).values
        beat = state.get("beat", "")
        turn = state.get("turn_number", 0)

        print(f"\n{C.MAGENTA}{'─' * 50}{C.RESET}")
        print(f"{C.YELLOW}🎲 Turn {turn}{C.RESET}")
        print(f"{C.GREEN}{beat}{C.RESET}\n")

        if scripted is not None:
            dm_input = "end" if not scripted else scripted.pop(0)
            print(f"{C.CYAN}DM> {C.RESET}{dm_input}")
        else:
            try:
                dm_input = input(f"{C.CYAN}DM> {C.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                dm_input = "end"

        app.invoke(Command(resume=dm_input), run_config)

    print(f"\n{C.GREEN}✓ The story is complete.{C.RESET}")
    final = app.get_state(run_config).values
    history = final.get("history", [])
    if history:
        print(f"\n{C.CYAN}📚 {len(history)} committed beat(s).{C.RESET}")


if __name__ == "__main__":
    run()
