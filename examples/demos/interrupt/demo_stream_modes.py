#!/usr/bin/env python
"""Demo: Stream mode effects on interrupt_output_mapping visibility.

This demonstrates the FR-039 finding: when using astream() with subgraphs
that have interrupt_output_mapping, you must use stream_mode="values" to
see the mapped state.

Run:
    python examples/demos/interrupt/demo_stream_modes.py
"""

import asyncio
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver

from yamlgraph.compile.graph_loader import compile_graph, load_graph_config


async def demo_updates_mode():
    """Default stream_mode='updates' - mapped state NOT visible in chunks."""
    print("=" * 60)
    print("DEMO 1: stream_mode='updates' (default)")
    print("=" * 60)
    print()

    graph_path = Path(__file__).parent / "interrupt-parent.yaml"
    config = load_graph_config(graph_path)
    state_graph = compile_graph(config)
    checkpointer = MemorySaver()
    compiled = state_graph.compile(checkpointer=checkpointer)

    thread_config = {"configurable": {"thread_id": "demo-updates"}}

    print("Streaming with default mode (updates)...")
    print()

    chunks = []
    async for chunk in compiled.astream({"user_input": "hello"}, thread_config):
        chunks.append(chunk)
        print(f"  Chunk: {chunk}")

    print()
    print(f"Total chunks received: {len(chunks)}")

    # Check for mapped fields
    all_keys = set()
    for c in chunks:
        all_keys.update(c.keys())

    print(f"All keys seen in chunks: {sorted(all_keys)}")
    print()
    print("❌ Notice: 'child_phase' and 'child_data' are NOT in chunks!")
    print("   The interrupt_output_mapping fired, but updates mode")
    print("   only yields node outputs, not accumulated state.")
    print()


async def demo_values_mode():
    """stream_mode='values' - mapped state IS visible."""
    print("=" * 60)
    print("DEMO 2: stream_mode='values'")
    print("=" * 60)
    print()

    graph_path = Path(__file__).parent / "interrupt-parent.yaml"
    config = load_graph_config(graph_path)
    state_graph = compile_graph(config)
    checkpointer = MemorySaver()
    compiled = state_graph.compile(checkpointer=checkpointer)

    thread_config = {"configurable": {"thread_id": "demo-values"}}

    print("Streaming with stream_mode='values'...")
    print()

    chunks = []
    async for chunk in compiled.astream(
        {"user_input": "hello"},
        thread_config,
        stream_mode="values",
    ):
        chunks.append(chunk)
        # Show abbreviated output (state can be large)
        keys = list(chunk.keys()) if isinstance(chunk, dict) else []
        has_phase = "child_phase" in keys
        has_data = "child_data" in keys
        has_interrupt = "__interrupt__" in keys
        print(
            f"  Chunk {len(chunks)}: keys={len(keys)}, "
            f"child_phase={has_phase}, child_data={has_data}, "
            f"interrupt={has_interrupt}"
        )

    print()
    print(f"Total chunks received: {len(chunks)}")

    # Show the final chunk details
    if chunks:
        final = chunks[-1]
        if isinstance(final, dict):
            print()
            print("Final chunk details:")
            print(f"  child_phase = {final.get('child_phase', '<missing>')!r}")
            print(f"  child_data  = {final.get('child_data', '<missing>')!r}")

    print()
    print("✅ Notice: 'child_phase' and 'child_data' ARE in the final chunk!")
    print("   Using stream_mode='values' yields full accumulated state.")
    print()


async def demo_ainvoke():
    """ainvoke() - combines both modes, mapped state visible."""
    print("=" * 60)
    print("DEMO 3: ainvoke() (recommended for interrupt workflows)")
    print("=" * 60)
    print()

    graph_path = Path(__file__).parent / "interrupt-parent.yaml"
    config = load_graph_config(graph_path)
    state_graph = compile_graph(config)
    checkpointer = MemorySaver()
    compiled = state_graph.compile(checkpointer=checkpointer)

    thread_config = {"configurable": {"thread_id": "demo-ainvoke"}}

    print("Running with ainvoke()...")
    print()

    result = await compiled.ainvoke({"user_input": "hello"}, thread_config)

    print(f"Result keys: {list(result.keys())}")
    print()
    print("Result details:")
    print(f"  child_phase = {result.get('child_phase', '<missing>')!r}")
    print(f"  child_data  = {result.get('child_data', '<missing>')!r}")
    print(f"  __interrupt__ present = {'__interrupt__' in result}")

    print()
    print("✅ ainvoke() returns full state including mapped fields.")
    print("   Internally it combines updates + values modes.")
    print()


async def main():
    print()
    print("=" * 60)
    print("  FR-039 Demo: Stream Modes & interrupt_output_mapping")
    print("=" * 60)
    print()
    print("This demo shows how stream_mode affects visibility of")
    print("state mapped via interrupt_output_mapping in subgraphs.")
    print()

    await demo_updates_mode()
    await demo_values_mode()
    await demo_ainvoke()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    print("When consuming graphs with interrupt_output_mapping:")
    print()
    print("  1. stream_mode='updates' (default):")
    print("     ❌ Mapped state NOT in chunks")
    print()
    print("  2. stream_mode='values':")
    print("     ✅ Mapped state in final chunk")
    print()
    print("  3. ainvoke():")
    print("     ✅ Mapped state in return value (recommended)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
