#!/usr/bin/env python3
"""Automated demo of the D&D NPC Encounter System using YAMLGraph.

This script demonstrates:
1. Creating NPCs using the npc-creation.yaml graph
2. Running automated encounters with pre-scripted scenarios
3. Optionally generating images for each turn

Usage:
    python examples/npc/demo.py                    # 3 NPCs, 5 rounds
    python examples/npc/demo.py --npcs 2           # 2 NPCs
    python examples/npc/demo.py --rounds 3         # 3 rounds
    python examples/npc/demo.py --images           # Generate images
    python examples/npc/demo.py -n 4 -r 3 -i       # 4 NPCs, 3 rounds, images
"""

import argparse
import random
import uuid

from langgraph.types import Command

from yamlgraph.graph_loader import (
    compile_graph,
    get_checkpointer_for_graph,
    load_graph_config,
)

# =============================================================================
# Colors for output
# =============================================================================


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    RED = "\033[31m"


def header(text: str):
    print(f"\n{C.BOLD}{C.CYAN}{'═' * 60}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {text}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═' * 60}{C.RESET}\n")


def section(text: str):
    print(f"\n{C.YELLOW}▶ {text}{C.RESET}")
    print(f"{C.DIM}{'─' * 50}{C.RESET}")


# =============================================================================
# NPC Concepts for Demo
# =============================================================================

NPC_CONCEPTS = [
    {
        "concept": "a gruff dwarven bartender who secretly waters down the ale",
        "race": "Dwarf",
        "character_class": "Commoner",
        "location": "The Red Dragon Inn",
        "role_in_story": "Bartender who knows everyone's secrets",
    },
    {
        "concept": "a mysterious elven bard who trades in information and secrets",
        "race": "Elf",
        "character_class": "Bard",
        "location": "The Red Dragon Inn",
        "role_in_story": "Information broker",
    },
    {
        "concept": "a retired human soldier turned bouncer, haunted by the past",
        "race": "Human",
        "character_class": "Fighter",
        "location": "The Red Dragon Inn",
        "role_in_story": "Tavern bouncer and protector",
    },
    {
        "concept": "a young tiefling server saving money for wizard academy",
        "race": "Tiefling",
        "character_class": "Commoner",
        "location": "The Red Dragon Inn",
        "role_in_story": "Aspiring wizard working as server",
    },
    {
        "concept": "a paranoid gnome inventor convinced everyone wants his secrets",
        "race": "Gnome",
        "character_class": "Artificer",
        "location": "The Red Dragon Inn",
        "role_in_story": "Eccentric patron with gadgets",
    },
    {
        "concept": "a boisterous half-orc celebrating their first dungeon delve",
        "race": "Half-Orc",
        "character_class": "Barbarian",
        "location": "The Red Dragon Inn",
        "role_in_story": "Novice adventurer patron",
    },
]

# Pre-scripted DM scenarios
DM_SCENARIOS = [
    "A group of adventurers bursts through the door, looking exhausted. One shouts 'We need help! There's something in the mines!'",
    "The adventurers explain they barely escaped strange creatures in the old silver mine. They need supplies and information.",
    "One adventurer slams a glowing crystal on the bar and asks if anyone knows what it is.",
    "A hooded figure in the corner stands and offers to buy the crystal for 500 gold.",
    "The city watch enters, looking for someone matching one adventurer's description.",
    "A loud explosion rocks the building. Through the windows, smoke rises from the market.",
    "One adventurer collapses, muttering about 'the shadow beneath' in delirium.",
    "A young child runs in crying - their parents didn't come home from the mines.",
    "The hooded figure reveals themselves as a noble's agent and demands cooperation.",
    "Strange scratching sounds begin coming from the cellar below.",
]


# =============================================================================
# Demo Functions
# =============================================================================


def create_npc(concept_data: dict, index: int) -> dict:
    """Create an NPC using the npc-creation graph."""
    section(f"Creating NPC {index + 1}: {concept_data.get('role_in_story', 'NPC')}")

    print(f"  📝 Concept: {C.DIM}{concept_data['concept'][:60]}...{C.RESET}")
    print("  ⏳ Generating NPC...")

    # Build and run the NPC creation graph
    config = load_graph_config("examples/npc/npc-creation.yaml")
    graph = compile_graph(config)
    app = graph.compile()

    result = app.invoke(concept_data)

    # Extract NPC data from result
    identity = result.get("identity", {})
    if hasattr(identity, "model_dump"):
        identity = identity.model_dump()

    npc_name = identity.get("name", f"NPC_{index}")
    npc_race = identity.get("race", concept_data.get("race", "Unknown"))
    npc_class = identity.get("character_class", concept_data.get("character_class", ""))

    print(f"  ✓ Created: {C.GREEN}{C.BOLD}{npc_name}{C.RESET}")
    print(f"    {npc_race} {npc_class}")

    # Build flat NPC dict for encounter
    personality = result.get("personality", {})
    if hasattr(personality, "model_dump"):
        personality = personality.model_dump()

    behavior = result.get("behavior", {})
    if hasattr(behavior, "model_dump"):
        behavior = behavior.model_dump()

    return {
        "name": npc_name,
        "race": str(npc_race),
        "character_class": str(npc_class),
        "appearance": identity.get("appearance", ""),
        "voice": identity.get("voice", ""),
        "personality": str(personality),
        "behavior": str(behavior),
        "goals": str(behavior.get("goals", [])),
    }


def create_multiple_npcs(count: int) -> list[dict]:
    """Create multiple NPCs for the demo."""
    header(f"Creating {count} NPCs")

    concepts = random.sample(NPC_CONCEPTS, min(count, len(NPC_CONCEPTS)))
    npcs = []

    for i, concept in enumerate(concepts):
        try:
            npc = create_npc(concept, i)
            npcs.append(npc)
        except Exception as e:
            print(f"  {C.RED}✗ Error: {e}{C.RESET}")

    return npcs


def show_npc_roster(npcs: list[dict]):
    """Display the NPC roster."""
    section(f"NPC Roster ({len(npcs)} characters)")

    for i, npc in enumerate(npcs, 1):
        print(f"  {C.CYAN}{i}. {C.BOLD}{npc['name']}{C.RESET}")
        print(f"     {npc['race']} {npc['character_class']}")
        print()


def run_automated_encounter(
    npcs: list[dict],
    num_rounds: int = 5,
    generate_images: bool = False,
):
    """Run an automated encounter with pre-scripted DM inputs."""
    header(f"Running Automated Encounter ({num_rounds} rounds)")

    print("  📍 Location: The Red Dragon Inn")
    print(f"  🎭 NPCs: {', '.join(npc['name'] for npc in npcs)}")
    print(f"  🔄 Rounds: {num_rounds}")
    if generate_images:
        print("  🖼️  Images: Enabled")

    # Load encounter graph
    config = load_graph_config("examples/npc/encounter-multi.yaml")
    graph = compile_graph(config)
    checkpointer = get_checkpointer_for_graph(config)
    app = graph.compile(checkpointer=checkpointer)

    # Session setup
    thread_id = str(uuid.uuid4())
    run_config = {"configurable": {"thread_id": thread_id}}

    # Initial state
    initial_state = {
        "npcs": npcs,
        "location": "The Red Dragon Inn",
        "location_description": "A warm, crowded tavern with a crackling fireplace and the smell of ale",
        "turn_number": 1,
        "encounter_history": [],
        "perceptions": [],
        "decisions": [],
        "narrations": [],
    }

    # Start the graph (will hit interrupt)
    app.invoke(initial_state, run_config)

    # Run through scenarios
    scenarios = DM_SCENARIOS[:num_rounds]

    for turn_num, dm_input in enumerate(scenarios, 1):
        print(f"\n{C.BOLD}{'═' * 60}{C.RESET}")
        print(f"{C.BOLD}  Turn {turn_num} of {num_rounds}{C.RESET}")
        print(f"{C.BOLD}{'═' * 60}{C.RESET}")

        print(f'\n{C.CYAN}DM:{C.RESET} "{dm_input}"\n')
        print(f"{C.DIM}Processing all NPCs...{C.RESET}")

        # Resume with DM input
        result = app.invoke(Command(resume=dm_input), run_config)

        # Show turn summary
        if result.get("turn_summary"):
            print(f"\n{C.GREEN}📜 Turn Summary:{C.RESET}")
            summary = result["turn_summary"]
            if hasattr(summary, "model_dump"):
                summary = str(summary)
            # Wrap long text
            for line in str(summary).split("\n"):
                print(f"   {line}")

        # Show image if generated
        if result.get("scene_image"):
            print(f"\n{C.CYAN}🖼️  Image: {result['scene_image']}{C.RESET}")

    # Final summary
    header("Encounter Complete!")

    history = result.get("encounter_history", [])
    if history:
        print(f"{C.CYAN}📚 {len(history)} turns recorded in history{C.RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Automated D&D NPC Encounter Demo using YAMLGraph"
    )
    parser.add_argument(
        "--npcs",
        "-n",
        type=int,
        default=3,
        help="Number of NPCs to create (default: 3)",
    )
    parser.add_argument(
        "--rounds",
        "-r",
        type=int,
        default=5,
        help="Number of encounter rounds (default: 5)",
    )
    parser.add_argument(
        "--images",
        "-i",
        action="store_true",
        help="Generate images for each turn (requires REPLICATE_API_TOKEN)",
    )
    parser.add_argument(
        "--skip-creation",
        action="store_true",
        help="Skip NPC creation, use default NPCs",
    )

    args = parser.parse_args()

    header("D&D NPC ENCOUNTER SYSTEM - Automated Demo")

    print("This demo shows AI-powered NPCs responding to pre-scripted scenarios.")
    print("The AI perceives each scene, decides actions, and narrates in character.")
    print()

    # Get NPCs
    if args.skip_creation:
        print(f"{C.YELLOW}Using default NPCs...{C.RESET}")
        npcs = [
            {
                "name": "Thorin Ironfoot",
                "race": "Dwarf",
                "character_class": "Blacksmith",
                "appearance": "Stocky with burn scars and a copper beard",
                "voice": "Gruff, low rumble",
                "personality": {
                    "traits": ["Stoic", "Hardworking", "Practical"],
                    "ideals": ["Quality craftsmanship", "Honest trade"],
                    "flaws": ["Distrustful of magic", "Stubborn"],
                    "disposition": "neutral",
                },
                "behavior": {
                    "combat_style": "defensive",
                    "goals": ["Run a successful smithy", "Protect the tavern"],
                },
                "goals": ["Run a successful smithy", "Protect the tavern"],
            },
            {
                "name": "Lyra Whisperwind",
                "race": "Elf",
                "character_class": "Ranger",
                "appearance": "Lithe with silver hair and piercing blue eyes",
                "voice": "Melodic, speaks in riddles",
                "personality": {
                    "traits": ["Curious", "Mischievous", "Observant"],
                    "ideals": ["Truth", "Knowledge"],
                    "flaws": ["Overly secretive", "Distrustful"],
                    "disposition": "curious",
                },
                "behavior": {
                    "combat_style": "ranged",
                    "goals": ["Uncover hidden truths", "Gather information"],
                },
                "goals": ["Uncover hidden truths", "Gather information"],
            },
            {
                "name": "Marcus the Bold",
                "race": "Human",
                "character_class": "Fighter",
                "appearance": "Burly with thick beard and battle scars",
                "voice": "Booming laugh",
                "personality": {
                    "traits": ["Jovial", "Brave", "Loyal"],
                    "ideals": ["Glory", "Protecting the weak"],
                    "flaws": ["Reckless", "Overconfident"],
                    "disposition": "friendly",
                },
                "behavior": {
                    "combat_style": "aggressive",
                    "goals": ["Find glory in battle", "Protect friends"],
                },
                "goals": ["Find glory in battle", "Protect friends"],
            },
        ][: args.npcs]
    else:
        npcs = create_multiple_npcs(args.npcs)

    if not npcs:
        print(f"{C.RED}No NPCs available. Exiting.{C.RESET}")
        return

    # Show roster
    show_npc_roster(npcs)

    # Run encounter
    run_automated_encounter(npcs, args.rounds, args.images)


if __name__ == "__main__":
    main()
