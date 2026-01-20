"""Test FR-006: interrupt_output_mapping with subgraph."""
from pathlib import Path
from langgraph.checkpoint.memory import MemorySaver

from yamlgraph.graph_loader import load_graph_config, compile_graph

print("=== Testing FR-006: interrupt_output_mapping ===")
parent_path = Path("graphs/interrupt-parent.yaml")
config = load_graph_config(parent_path)
state_graph = compile_graph(config)
checkpointer = MemorySaver()
parent_app = state_graph.compile(checkpointer=checkpointer)

thread_config = {"configurable": {"thread_id": "test-fr006"}}

result = parent_app.invoke({"user_input": "hello"}, thread_config)
print("Parent result keys:", result.keys())
print()
print("child_phase:", result.get("child_phase"))
print("child_data:", result.get("child_data"))
print("__interrupt__:", "__interrupt__" in result)
print()
if "child_phase" in result and "child_data" in result:
    print("✅ FR-006 SUCCESS: Child state mapped to parent!")
else:
    print("❌ FR-006 FAILED: Child state not in result")
