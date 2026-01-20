#!/usr/bin/env python3
"""Run a multi-turn encounter with multiple NPCs.

This script demonstrates the map node feature for parallel NPC processing.
Each turn, ALL NPCs perceive, decide, and act in response to DM input.

Usage:
    python examples/npc/run_encounter.py

    # With pre-created NPCs
    python examples/npc/run_encounter.py --npc-dir npcs/
"""

import argparse
import uuid
from pathlib import Path

import yaml
from langgraph.types import Command

from yamlgraph.graph_loader import (
    compile_graph,
    get_checkpointer_for_graph,
    load_graph_config,
)


# ANSI colors
class C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"
    RESET = "\033[0m"


def load_npcs(npc_dir: str | None) -> list[dict]:
    """Load NPC data from directory or use defaults."""
    if npc_dir:
        npc_path = Path(npc_dir)
        if npc_path.exists():
            npcs = []
            for f in npc_path.glob("*.yaml"):
                with open(f) as fp:
                    data = yaml.safe_load(fp)
                    identity = data.get("identity", {})
                    personality = data.get("personality", {})
                    behavior = data.get("behavior", {})
                    # Build structured NPC dict
                    npc = {
                        "name": identity.get("name", f.stem),
                        "appearance": identity.get("appearance", ""),
                        "voice": identity.get("voice", ""),
                        "race": identity.get("race", ""),
                        "character_class": identity.get("character_class", ""),
                        "personality": personality,  # Keep as dict
                        "behavior": behavior,  # Keep as dict
                        "goals": behavior.get("goals", []),  # Keep as list
                    }
                    npcs.append(npc)
            if npcs:
                print(f"{C.GREEN}✓ Loaded {len(npcs)} NPCs from {npc_dir}{C.RESET}")
                return npcs

    # Default NPCs for demo
    return [
        {
            "name": "Thorin Ironfoot",
            "appearance": "A stocky dwarf with burn scars and a copper beard",
            "voice": "Gruff, low rumble",
            "personality": {
                "traits": ["Stoic", "Hardworking", "Practical"],
                "ideals": ["Quality craftsmanship", "Honest trade"],
                "flaws": ["Distrustful of magic", "Stubborn"],
                "disposition": "neutral",
            },
            "behavior": {
                "combat_style": "defensive",
                "goals": ["Run a successful smithy", "Find an apprentice"],
            },
            "goals": ["Run a successful smithy", "Find an apprentice"],
            "race": "Dwarf",
            "character_class": "Blacksmith",
        },
        {
            "name": "Lyra Whisperwind",
            "appearance": "A lithe elf with silver hair and piercing blue eyes",
            "voice": "Melodic, speaks in riddles",
            "personality": {
                "traits": ["Curious", "Mischievous", "Observant"],
                "ideals": ["Truth", "Knowledge"],
                "flaws": ["Overly secretive", "Distrustful"],
                "disposition": "curious",
            },
            "behavior": {
                "combat_style": "ranged",
                "goals": ["Uncover hidden truths", "Protect the ancient grove"],
            },
            "goals": ["Uncover hidden truths", "Protect the ancient grove"],
            "race": "Elf",
            "character_class": "Ranger",
        },
        {
            "name": "Marcus the Bold",
            "appearance": "A burly human with a thick black beard and battle scars",
            "voice": "Booming laugh, speaks loudly",
            "personality": {
                "traits": ["Jovial", "Brave", "Loyal"],
                "ideals": ["Glory", "Protecting the weak"],
                "flaws": ["Reckless", "Overconfident"],
                "disposition": "friendly",
            },
            "behavior": {
                "combat_style": "aggressive",
                "goals": ["Find glory in battle", "Earn gold for his family"],
            },
            "goals": ["Find glory in battle", "Earn gold for his family"],
            "race": "Human",
            "character_class": "Fighter",
        },
    ]


def run_encounter():
    """Run the interactive multi-NPC encounter."""
    parser = argparse.ArgumentParser(description="Multi-NPC Encounter")
    parser.add_argument("--npc-dir", "-n", help="Directory with NPC YAML files")
    parser.add_argument(
        "--location", "-l", default="The Rusty Anchor tavern", help="Location name"
    )
    args = parser.parse_args()

    print(f"\n{C.BOLD}{'=' * 60}{C.RESET}")
    print(f"{C.BOLD}⚔️  YAMLGraph Multi-NPC Encounter{C.RESET}")
    print(f"{C.BOLD}{'=' * 60}{C.RESET}\n")

    # Load graph
    config = load_graph_config("examples/npc/encounter-multi.yaml")
    graph = compile_graph(config)
    checkpointer = get_checkpointer_for_graph(config)
    app = graph.compile(checkpointer=checkpointer)

    # Session setup
    thread_id = str(uuid.uuid4())
    run_config = {"configurable": {"thread_id": thread_id}}

    # Initial state
    npcs = load_npcs(args.npc_dir)
    initial_state = {
        "npcs": npcs,
        "location": args.location,
        "location_description": "A dimly lit tavern with rough wooden tables and the smell of ale",
        "turn_number": 1,
        "encounter_history": [],
        "perceptions": [],
        "decisions": [],
        "narrations": [],
    }

    print(f"{C.CYAN}📍 Location: {args.location}{C.RESET}")
    print(f"{C.CYAN}🎭 NPCs present:{C.RESET}")
    for npc in npcs:
        print(
            f"   - {C.BOLD}{npc['name']}{C.RESET} ({npc['race']} {npc['character_class']})"
        )
    print(f"\n{C.DIM}Type 'end' to finish the encounter, 'quit' to exit.{C.RESET}\n")

    # Start the graph
    result = app.invoke(initial_state, run_config)
    turn = 1

    while True:
        # Get interrupt message
        state = app.get_state(run_config)
        next_nodes = state.next if hasattr(state, "next") else []

        if not next_nodes:
            print(f"\n{C.GREEN}✓ Encounter complete!{C.RESET}")
            break

        # Show prompt
        print(f"\n{C.MAGENTA}{'─' * 50}{C.RESET}")
        print(f"{C.YELLOW}🎲 Turn {turn} - What happens?{C.RESET}")

        # Get user input
        try:
            dm_input = input(f"{C.CYAN}DM> {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{C.YELLOW}Encounter ended by user.{C.RESET}")
            break

        if dm_input.lower() == "quit":
            print(f"\n{C.YELLOW}Farewell, Dungeon Master!{C.RESET}")
            break

        if not dm_input:
            print(f"{C.DIM}(Describe what happens in the scene){C.RESET}")
            continue

        # Resume with DM input
        print(f"\n{C.DIM}Processing all NPCs...{C.RESET}")
        result = app.invoke(Command(resume=dm_input), run_config)

        # Show results
        if result.get("turn_summary"):
            print(f"\n{C.GREEN}📜 Turn Summary:{C.RESET}")
            print(result["turn_summary"])

        if result.get("scene_image"):
            print(f"\n{C.CYAN}🖼️  Image saved: {result['scene_image']}{C.RESET}")

        if dm_input.lower() == "end":
            print(f"\n{C.GREEN}✓ Encounter ended!{C.RESET}")
            # Show history
            history = result.get("encounter_history", [])
            if history:
                print(f"\n{C.CYAN}📚 Encounter History:{C.RESET}")
                for i, summary in enumerate(history, 1):
                    print(f"\n{C.DIM}Turn {i}:{C.RESET}")
                    print(summary[:300] + "..." if len(summary) > 300 else summary)
            break

        turn += 1


if __name__ == "__main__":
    run_encounter()
