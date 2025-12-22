"""Graph builders for the showcase pipeline.

Provides functions to build various pipeline configurations.

Pipeline Architecture
=====================

The main showcase pipeline follows this flow:

```mermaid
graph LR
    A[generate] -->|content| B{should_continue}
    B -->|continue| C[analyze]
    B -->|end| E[END]
    C -->|analysis| D[summarize]
    D --> E[END]
```

State Flow:
- generate: Creates GeneratedContent from topic
- analyze: Produces Analysis from generated content  
- summarize: Combines all outputs into final_summary

Resume Support:
- Pipeline can resume from any node if state is persisted
- Use build_resume_graph(start_from="analyze") to skip completed steps
"""

from langgraph.graph import END, StateGraph

from showcase.models import ShowcaseState, create_initial_state
from showcase.nodes import analyze_node, generate_node, should_continue, summarize_node


def build_showcase_graph() -> StateGraph:
    """Build the main showcase pipeline graph.
    
    Pipeline flow:
        generate → analyze → summarize → END
        
    With conditional check after generate:
        - If error or no content: END
        - Otherwise: continue to analyze
    
    Returns:
        StateGraph ready for compilation
    """
    graph = StateGraph(ShowcaseState)
    
    # Add nodes
    graph.add_node("generate", generate_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("summarize", summarize_node)
    
    # Set entry point
    graph.set_entry_point("generate")
    
    # Add conditional edge after generate
    graph.add_conditional_edges(
        "generate",
        should_continue,
        {
            "continue": "analyze",
            "end": END,
        }
    )
    
    # Linear edges for the rest
    graph.add_edge("analyze", "summarize")
    graph.add_edge("summarize", END)
    
    return graph


def build_resume_graph(start_from: str = "analyze") -> StateGraph:
    """Build a graph for resuming from a specific step.
    
    This demonstrates how to create alternate entry points
    for resuming interrupted pipelines.
    
    Resume Graph Flow:
    
    ```mermaid
    graph LR
        subgraph "start_from='analyze'"
            A1[analyze] --> B1[summarize] --> C1[END]
        end
        subgraph "start_from='summarize'"
            A2[summarize] --> C2[END]
        end
    ```
    
    Args:
        start_from: Node to start from ('analyze' or 'summarize')
        
    Returns:
        StateGraph for resume
        
    Raises:
        ValueError: If start_from is not a valid node name
        
    Example:
        >>> # Resume a pipeline that failed during analysis
        >>> from showcase.storage import ShowcaseDB
        >>> db = ShowcaseDB()
        >>> state = db.load_state("thread-123")
        >>> if state and state.get("generated") and not state.get("analysis"):
        ...     graph = build_resume_graph(start_from="analyze").compile()
        ...     result = graph.invoke(state)
    """
    valid_nodes = {"analyze", "summarize"}
    if start_from not in valid_nodes:
        raise ValueError(f"start_from must be one of {valid_nodes}, got '{start_from}'")
    
    graph = StateGraph(ShowcaseState)
    
    # Add only the nodes needed from start_from onwards
    if start_from == "analyze":
        graph.add_node("analyze", analyze_node)
        graph.add_node("summarize", summarize_node)
        graph.set_entry_point("analyze")
        graph.add_edge("analyze", "summarize")
        graph.add_edge("summarize", END)
    else:  # summarize
        graph.add_node("summarize", summarize_node)
        graph.set_entry_point("summarize")
        graph.add_edge("summarize", END)
    
    return graph


def run_pipeline(topic: str, style: str = "informative", word_count: int = 300) -> ShowcaseState:
    """Run the complete pipeline with given inputs.
    
    Args:
        topic: Topic to generate content about
        style: Writing style
        word_count: Target word count
        
    Returns:
        Final state with all outputs
    """
    graph = build_showcase_graph().compile()
    initial_state = create_initial_state(
        topic=topic,
        style=style,
        word_count=word_count,
    )
    
    return graph.invoke(initial_state)
