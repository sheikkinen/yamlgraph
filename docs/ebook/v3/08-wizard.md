---
render_with_liquid: false
---

# Chapter 08: The Wizard Behind the Curtain

> *"The cheapest code is unwritten code."*
> — Commandment I, The Scripture

Throughout this book you have seen what YAMLGraph does: doctrine enforced by linters, pipelines orchestrated from YAML, reflexion loops that improve their own output, traceability woven from requirement to test. Now it is time to open the engine room and show *how* the machine works.

This chapter is for contributors. We will walk the compiler pipeline function by function, tour the node factory that turns YAML stanzas into LangGraph nodes, examine the linter that catches errors before the first LLM call, and map the extension points where new capabilities plug in.

The entire engine lives in 76 Python files totaling roughly 12,700 lines — a codebase you can hold in your head.

---

## 1. The Engine at a Glance

The `yamlgraph/` package is organized into purpose-driven modules, each kept under 400 lines:

```
yamlgraph/
├── graph_loader.py          # Compilation orchestrator
├── node_compiler.py         # Node registration into StateGraph
├── edge_compiler.py         # Edge wiring (simple + conditional)
├── map_compiler.py          # Map node fan-out via Send
├── executor.py              # Unified LLM execution interface
├── executor_base.py         # Shared prompt formatting + message building
├── executor_async.py        # Async wrappers + native streaming
├── routing.py               # Conditional routing functions
├── schema_loader.py         # Pydantic model from YAML schema blocks
├── data_loader.py           # External YAML data files → state
├── error_handlers.py        # on_error strategies (skip/retry/fail/fallback)
├── config.py                # Centralized configuration
├── constants.py             # Type-safe enums (NodeType, ErrorHandler)
├── mcp_server.py            # MCP server for Copilot integration
├── interactive_tool.py      # Interactive tool expansion
│
├── node_factory/            # One module per node category
│   ├── base.py              #   Shared utilities + output model resolution
│   ├── llm_nodes.py         #   LLM and router nodes
│   ├── control_nodes.py     #   Interrupt + passthrough
│   ├── tool_nodes.py        #   Dynamic tool_call
│   ├── copilot_node.py      #   GitHub Copilot CLI delegation
│   ├── subgraph_nodes.py    #   Subgraph composition
│   └── streaming.py         #   Streaming node factory
│
├── models/                  # Pydantic models + state generation
│   ├── graph_schema.py      #   GraphConfigSchema validation
│   ├── state_builder.py     #   Dynamic TypedDict generation
│   └── schemas.py           #   Framework models (PipelineError, etc.)
│
├── linter/                  # Static analysis at YAML-load time
│   ├── graph_linter.py      #   Orchestrator
│   ├── checks.py            #   Core structural checks
│   ├── checks_contracts.py  #   Contract violation detection
│   ├── checks_providers.py  #   Provider-specific checks
│   ├── checks_semantic.py   #   Cross-reference + semantic checks
│   └── patterns/            #   Pattern-specific validators
│       ├── router.py        #     Router pattern
│       ├── map.py           #     Map pattern
│       ├── agent.py         #     Agent pattern
│       ├── subgraph.py      #     Subgraph pattern
│       └── interrupt.py     #     Interrupt pattern
│
├── utils/                   # Shared utilities
│   ├── llm_factory.py       #   Multi-provider LLM abstraction
│   ├── expressions.py       #   State path + arithmetic resolution
│   ├── conditions.py        #   Condition expression evaluator
│   ├── template.py          #   Jinja2 variable extraction + validation
│   ├── prompts.py           #   Prompt file loading + resolution
│   ├── sanitize.py          #   Input sanitization
│   ├── token_tracker.py     #   Token usage accumulation
│   └── validators.py        #   Graph config validation
│
├── cli/                     # Command-line interface
│   ├── graph_commands.py    #   run/info/lint/codegen
│   ├── graph_validate.py    #   validate command
│   └── helpers.py           #   Shared CLI utilities
│
├── tools/                   # External integrations
└── storage/                 # Checkpointer backends
```

The design principle is surgical modularity. When `graph_loader.py` grew past 400 lines, compilation was split into `node_compiler.py`, `edge_compiler.py`, and `map_compiler.py`. When `checks.py` grew, semantic checks moved to `checks_semantic.py` and contract checks to `checks_contracts.py`. The 400-line rule from Commandment VIII is enforced by the linter itself.

---

## 2. The Compiler Pipeline

Every YAMLGraph execution begins with a YAML file becoming a running LangGraph. The pipeline has five stages:

```
YAML file
  │
  ▼
load_graph_config()     ← Parse YAML, detect loops, validate
  │
  ▼
GraphConfig             ← Pydantic-validated configuration object
  │
  ├─► build_state_class()     ← Dynamic TypedDict from config
  ├─► _parse_all_tools()      ← Shell + Python tool registries
  │
  ▼
compile_graph()         ← Nodes → StateGraph → Edges
  │
  ▼
StateGraph.compile()    ← LangGraph compiled graph, ready to invoke
```

### Stage 1: Loading

The entry point is `load_graph_config()` in `graph_loader.py`:

```python
def load_graph_config(path: str | Path) -> GraphConfig:
    """Load and parse a YAML graph definition.

    Args:
        path: Path to the YAML file

    Returns:
        GraphConfig instance

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the YAML is invalid or missing required fields
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Graph config not found: {path}")

    with open(path) as f:
        config = yaml.safe_load(f)

    # Guard against empty/null YAML files
    if config is None:
        raise ValueError(f"Empty or invalid YAML file: {path}")
    if not isinstance(config, dict):
        raise ValueError(
            f"Graph config must be a dict, got {type(config).__name__}: {path}"
        )

    # FR-010: Auto-apply skip_if_exists=false to loop nodes
    config = apply_loop_node_defaults(config)

    # FR-049: Expand interactive_tool nodes before compilation
    from yamlgraph.interactive_tool import expand_interactive_tools

    config = expand_interactive_tools(config)

    return GraphConfig(config, source_path=path.resolve())
```

Before the config reaches `GraphConfig`, two transformations happen automatically. First, `apply_loop_node_defaults()` uses DFS cycle detection to find nodes that participate in loops and disables `skip_if_exists` for them — eliminating the common footgun where loop nodes wouldn't re-execute on iteration:

```python
def detect_loop_nodes(edges: list[dict]) -> set[str]:
    """Detect nodes that participate in cycles (loops).

    Uses DFS with path tracking to find back edges indicating cycles.
    """
```

Second, `expand_interactive_tools()` desugars `type: interactive_tool` nodes into their multi-node expansion before compilation even begins.

The `GraphConfig` constructor validates the configuration via `validate_config()`:

```python
class GraphConfig:
    """Parsed graph configuration from YAML."""

    def __init__(self, config: dict, source_path: Path | None = None):
        # Validate before storing
        validate_config(config)

        self.version = config.get("version", "1.0")
        self.name = config.get("name", "unnamed")
        self.description = config.get("description", "")
        self.defaults = config.get("defaults", {})
        self.nodes = config.get("nodes", {})
        self.edges = config.get("edges", [])
        self.tools = config.get("tools", {})
        # ...
        self.raw_config = config
        self.source_path = source_path
```

### Stage 2: State Generation

`build_state_class()` in `models/state_builder.py` generates a TypedDict at runtime from the graph configuration. No manual state class is ever needed:

```python
def build_state_class(config: dict) -> type:
    """Build TypedDict state class from graph configuration.

    Dynamically generates a TypedDict with:
    - Base infrastructure fields (errors, messages, thread_id, etc.)
    - Common input fields (topic, style, input, message, etc.)
    - Custom fields from YAML 'state' section
    - Fields extracted from node state_key
    - Special fields for agent/router node types
    - FR-021: Fields from data_files directive
    """
    fields: dict[str, type] = {}
    fields.update(BASE_FIELDS)
    fields.update(COMMON_INPUT_FIELDS)

    # Add custom state fields from YAML 'state' section
    state_config = config.get("state", {})
    custom_fields = parse_state_config(state_config)
    fields.update(custom_fields)

    # Extract fields from nodes
    nodes = config.get("nodes", {})
    node_fields = extract_node_fields(nodes)
    fields.update(node_fields)

    # Build TypedDict programmatically
    return TypedDict("GraphState", fields, total=False)
```

The base fields include carefully chosen reducers for concurrent safety:

```python
BASE_FIELDS: dict[str, type] = {
    "current_step": Annotated[str, last_value],
    "error": Annotated[Any, last_value],
    "errors": Annotated[list, add],
    "messages": Annotated[list, add],
    "_loop_counts": Annotated[dict, last_value],
    # ...
}
```

The `last_value` reducer ensures that parallel fan-in from map nodes doesn't raise `INVALID_CONCURRENT_GRAPH_UPDATE`. The `add` reducer on `errors` and `messages` accumulates across all nodes. Map node collect fields get a special `sorted_add` reducer that guarantees ordering:

```python
def sorted_add(existing: list, new: list) -> list:
    """Reducer that adds items and sorts by _map_index if present."""
    combined = (existing or []) + (new or [])
    if combined and isinstance(combined[0], dict) and "_map_index" in combined[0]:
        combined = sorted(combined, key=lambda x: x.get("_map_index", 0))
    return combined
```

### Stage 3: Tool Parsing

`_parse_all_tools()` builds three registries — shell tools, Python tools, and a callable registry for `tool_call` nodes:

```python
def _parse_all_tools(
    config: GraphConfig,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Callable]]:
    """Parse shell and Python tools from config.

    Returns:
        Tuple of (shell_tools, python_tools, callable_registry)
    """
    tools = parse_tools(config.tools)
    python_tools = parse_python_tools(config.tools)

    callable_registry: dict[str, Callable] = {}
    for name, tool_config in python_tools.items():
        try:
            callable_registry[name] = load_python_function(tool_config)
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to load tool '{name}': {e}")

    return tools, python_tools, callable_registry
```

### Stage 4: Node Compilation

`compile_nodes()` in `node_compiler.py` iterates all nodes and dispatches by type:

```python
def compile_nodes(
    config: "GraphConfig",
    graph: StateGraph,
    tools: dict[str, Any],
    python_tools: dict[str, Any],
    callable_registry: dict[str, Callable],
) -> tuple[dict[str, tuple], set[str]]:
    """Compile all nodes and add to graph.

    Returns:
        Tuple of:
        - map_nodes: name -> (map_edge_fn, sub_node_name)
        - interrupt_nodes: set of node names with prepare split
    """
```

The individual `compile_node()` function is a dispatch table driven by `NodeType`:

```python
node_type = node_config.get("type", NodeType.LLM)

if node_type == NodeType.TOOL:
    node_fn = create_tool_node(node_name, enriched_config, tools)
    graph.add_node(node_name, node_fn)
elif node_type == NodeType.PYTHON:
    node_fn = create_python_node(node_name, enriched_config, python_tools)
    graph.add_node(node_name, node_fn)
elif node_type == NodeType.AGENT:
    node_fn = create_agent_node(...)
    graph.add_node(node_name, node_fn)
elif node_type == NodeType.MAP:
    map_edge_fn, sub_node_name = compile_map_node(...)
    return (node_name, (map_edge_fn, sub_node_name))
# ... 8 more types
```

The twelve node types, defined as a `StrEnum` in `constants.py`, cover every pattern:

```python
class NodeType(StrEnum):
    LLM = "llm"
    ROUTER = "router"
    TOOL = "tool"
    AGENT = "agent"
    PYTHON = "python"
    MAP = "map"
    TOOL_CALL = "tool_call"
    INTERRUPT = "interrupt"
    SUBGRAPH = "subgraph"
    PASSTHROUGH = "passthrough"
    INTERACTIVE_TOOL = "interactive_tool"
    COPILOT = "copilot"
```

### Stage 5: Edge Wiring

`edge_compiler.py` processes each edge declaration and adds it to the StateGraph. The `_process_edge()` function handles six edge patterns:

```python
def _process_edge(
    edge: dict[str, Any],
    graph: StateGraph,
    map_nodes: dict[str, tuple],
    router_edges: dict[str, list],
    expression_edges: dict[str, list[tuple[str, str]]],
    interrupt_nodes: set[str] | None = None,
) -> None:
```

1. **START edges** — `_handle_start_edge()` sets the entry point (or conditional entry for map nodes)
2. **Map-to-map edges** — `_handle_map_to_map_edge()` chains fan-out functions
3. **To-map edges** — `_handle_to_map_edge()` wires regular nodes into fan-out
4. **From-map edges** — `_handle_from_map_edge()` handles fan-in to regular nodes or END
5. **Conditional edges** — collected into `router_edges` for batch processing
6. **Expression edges** — collected into `expression_edges` for condition routing

After all edges are processed, `_add_conditional_edges()` installs the router functions:

```python
def _add_conditional_edges(
    graph: StateGraph,
    router_edges: dict[str, list],
    expression_edges: dict[str, list[tuple[str, str]]],
) -> None:
    # Add router conditional edges
    for source_node, target_nodes in router_edges.items():
        route_mapping = {target: target for target in target_nodes}
        graph.add_conditional_edges(
            source_node,
            make_router_fn(target_nodes),
            route_mapping,
        )

    # Add expression-based conditional edges
    for source_node, expr_edges in expression_edges.items():
        targets = {target for _, target in expr_edges}
        targets.add(END)  # Always include END as fallback
        route_mapping = {t: (END if t == END else t) for t in targets}
        graph.add_conditional_edges(
            source_node,
            make_expr_router_fn(expr_edges, source_node),
            route_mapping,
        )
```

The whole pipeline comes together in `compile_graph()`:

```python
def compile_graph(config: GraphConfig) -> StateGraph:
    """Compile a GraphConfig to a LangGraph StateGraph."""
    state_class = _resolve_state_class(config)
    graph = StateGraph(state_class)

    tools, python_tools, callable_registry = _parse_all_tools(config)

    map_nodes, interrupt_nodes = compile_nodes(
        config, graph, tools, python_tools, callable_registry
    )

    router_edges: dict[str, list] = {}
    expression_edges: dict[str, list[tuple[str, str]]] = {}

    for edge in config.edges:
        _process_edge(
            edge, graph, map_nodes, router_edges, expression_edges, interrupt_nodes
        )

    _add_conditional_edges(graph, router_edges, expression_edges)

    return graph
```

---

## 3. The Node Factory

The `node_factory/` package uses the factory pattern: one module per node category, each exporting a `create_*` function that returns a closure compatible with `graph.add_node()`.

### The LLM Node: Where Prompts Meet Models

`llm_nodes.py` is the workhorse. `create_node_function()` constructs a closure that encapsulates all node configuration — prompt name, provider, temperature, output model, error handling, loop limits:

```python
def create_node_function(
    node_name: str,
    node_config: dict,
    defaults: dict,
    graph_path: Path | None = None,
) -> Callable[[GraphState], dict]:
    """Create a node function from YAML config."""
```

The generated `node_fn` follows a strict execution protocol:

1. **Loop limit check** — `check_loop_limit()` prevents infinite cycles
2. **Skip-if-exists** — truthy check on `state_key` for checkpoint resume (FR-050)
3. **Requirements check** — `check_requirements()` verifies prerequisite state keys
4. **Variable resolution** — `resolve_node_variables()` maps templates to state values
5. **LLM execution** — `execute_prompt()` with all configuration baked in
6. **Router routing** — if `type: router`, maps output to `_route` state key
7. **Error handling** — dispatches to `handle_skip`, `handle_retry`, `handle_fail`, or `handle_fallback`

The skip-if-exists check is subtle — it uses truthiness, not existence:

```python
def _should_skip_if_exists(skip_if_exists: bool, state_key: str, state: dict) -> bool:
    """FR-050: Uses truthiness check, not existence check.
    Empty collections ([], {}), empty strings (""), None, 0, and False
    do NOT trigger skip — only truthy values do."""
    if not skip_if_exists:
        return False
    return bool(state.get(state_key))
```

### Output Model Resolution

`base.py` provides `get_output_model_for_node()` with a three-tier priority:

```python
def get_output_model_for_node(node_config, prompts_dir, graph_path, prompts_relative):
    """Get output model for a node.

    Priority:
    1. Explicit output_model in node config (class path)
    2. Inline schema in prompt YAML file
    3. None (raw string output)
    """
```

This is how a prompt's `schema:` block becomes a runtime Pydantic model. The `schema_loader.py` module handles the actual model generation:

```python
def build_pydantic_model(schema: dict) -> type:
    """Build a Pydantic model dynamically from a schema dict."""
    model_name = schema["name"]
    field_definitions = {}

    for field_name, field_def in schema["fields"].items():
        field_type = resolve_type(field_def["type"], field_name)
        # Handle optional, constraints, defaults...
        field_definitions[field_name] = (field_type, Field(**field_kwargs))

    return create_model(model_name, **field_definitions)
```

### Control Nodes

`control_nodes.py` provides two node types. The interrupt node uses a two-function split (FR-060) — `prepare_fn` commits the payload to state *before* `interrupt()` fires, ensuring the state key is populated even when `GraphInterrupt` is raised:

```python
def create_interrupt_node(node_name, config, ...):
    """FR-060: The prepare function commits payload to state BEFORE
    interrupt() fires, so state_key holds the payload even when
    GraphInterrupt is raised.

    Returns:
        Tuple of (prepare_fn, interrupt_fn)
    """
```

The passthrough node handles pure state transformations — loop counters, list accumulation, data reshaping — without any LLM calls:

```python
def create_passthrough_node(node_name, config):
    """Create a passthrough node that transforms state without external calls.

    Useful for:
    - Loop counters (increment values)
    - State accumulation (append to lists)
    - Simple data transformations
    """
```

### Tool Call Nodes

`tool_nodes.py` enables dynamic tool dispatch from state. The tool name and arguments are resolved at runtime from state expressions:

```python
def create_tool_call_node(node_name, node_config, tools_registry):
    """Create a node that dynamically calls a tool from state.

    This enables YAML-driven tool execution where tool name and args
    are resolved from state at runtime.
    """
    tool_expr = node_config["tool"]   # e.g., "{state.task.tool}"
    args_expr = node_config["args"]   # e.g., "{state.task.args}"
```

### Map Node Compilation

`map_compiler.py` is where fan-out happens. It creates a sub-node wrapped with `wrap_for_reducer()` and a `map_edge` function that returns `Send` objects:

```python
def compile_map_node(name, config, builder, defaults, ...):
    """Compile type: map node using LangGraph Send.

    Creates a sub-node and returns a map edge function that fans out
    to the sub-node for each item in the list.
    """
    # ...
    def map_edge(state: dict) -> list[Send]:
        items = resolve_state_expression(over_expr, state)

        # FR-027: Cap fan-out to prevent unbounded Send() calls
        max_items = config.get("max_items", defaults.get("max_map_items", DEFAULT_MAX_MAP_ITEMS))
        if len(items) > max_items:
            items = items[:max_items]

        return [
            Send(sub_node_name, {**state, item_var: item, "_map_index": i})
            for i, item in enumerate(items)
        ]
```

The `wrap_for_reducer()` function ensures each sub-node's output includes `_map_index` for ordered fan-in via the `sorted_add` reducer.

### Subgraph Nodes

`subgraph_nodes.py` provides graph composition with circular reference detection using `ContextVar`:

```python
# Thread-safe loading stack to detect circular subgraph references
_loading_stack: ContextVar[list[Path]] = ContextVar("loading_stack")

def create_subgraph_node(node_name, node_config, parent_graph_path, ...):
    """Create a node that invokes a compiled subgraph.

    Raises:
        ValueError: If circular reference detected
    """
    # Circular reference detection (thread-safe)
    stack = _loading_stack.get([])
    if graph_path in stack:
        cycle = " -> ".join(str(p) for p in [*stack, graph_path])
        raise ValueError(f"Circular subgraph reference: {cycle}")
```

Two modes are supported: `invoke` (explicit state mapping between parent and child) and `direct` (shared schema, LangGraph handles natively).

### Copilot Nodes

`copilot_node.py` delegates to the GitHub Copilot CLI via subprocess, with injection safety enforced by list-based command construction (never `shell=True`):

```python
def _execute_cli(node_name, prompt, state_key, cli_flags, timeout):
    # Build command as list (not shell=True) for injection safety
    cmd = ["copilot", "--silent"]
    if cli_flags.get("allow_all_paths"):
        cmd.append("--allow-all-paths")
    # ...
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
```

---

## 4. The Linter

The linter is YAMLGraph's first line of defense. It catches at YAML-load time what would otherwise fail at runtime — missing prompts, dangling edges, invalid expressions, contract violations. When you run `yamlgraph graph lint`, every graph YAML file passes through this gauntlet before a single token is generated.

### The Orchestrator

`graph_linter.py` is clean delegation — it calls every check module and aggregates results:

```python
def lint_graph(graph_path: Path | str, project_root: Path | str | None = None) -> LintResult:
    """Lint a YAML graph file for issues."""
    all_issues: list[LintIssue] = []

    # Core structural checks
    all_issues.extend(check_state_declarations(graph_path, project_root))
    all_issues.extend(check_tool_references(graph_path))
    all_issues.extend(check_prompt_files(graph_path, project_root))
    all_issues.extend(check_edge_coverage(graph_path))
    all_issues.extend(check_node_types(graph_path))

    # Semantic checks
    all_issues.extend(check_cross_references(graph_path))
    all_issues.extend(check_passthrough_nodes(graph_path))
    all_issues.extend(check_tool_call_nodes(graph_path))
    all_issues.extend(check_expression_syntax(graph_path))
    all_issues.extend(check_error_handling(graph_path))
    all_issues.extend(check_edge_types(graph_path))
    all_issues.extend(check_unguarded_cycles(graph_path))

    # Pattern-specific checks
    all_issues.extend(check_router_patterns(graph_path, project_root))
    all_issues.extend(check_map_patterns(graph_path, project_root))
    all_issues.extend(check_interrupt_patterns(graph_path, project_root))
    all_issues.extend(check_agent_patterns(graph_path, project_root))
    all_issues.extend(check_subgraph_patterns(graph_path, project_root))

    # Contract violation checks
    all_issues.extend(check_python_node_variables(graph_path))
    all_issues.extend(check_identifier_keys(graph_path))
    all_issues.extend(check_skip_if_exists_add_reducer(graph_path))

    # Provider-specific checks
    all_issues.extend(check_thinking_budget(graph_path))

    has_errors = any(issue.severity == "error" for issue in all_issues)
    return LintResult(file=str(graph_path), issues=all_issues, valid=not has_errors)
```

Every issue is a structured `LintIssue` with severity, code, message, and fix suggestion:

```python
class LintIssue(BaseModel):
    """A single lint issue found in the graph."""
    severity: str   # "error", "warning", "info"
    code: str       # e.g., "E001", "W002"
    message: str
    line: int | None = None
    fix: str | None = None
```

### Core Structural Checks (`checks.py`)

These catch the basics — the things that would crash immediately at runtime:

| Code | Check | What It Catches |
|------|-------|-----------------|
| **E001** | `check_state_declarations` | Variable used in tool command but not declared in state |
| **E002** | `check_state_declarations` | Variable used in prompt but not declared in state |
| **E003** | `check_tool_references` | Tool referenced in node but not defined in tools section |
| **E004** | `check_prompt_files` | Prompt YAML file not found on disk |
| **E005** | `check_node_types` | Invalid node type (not in the 12-type enum) |
| **W001** | `check_tool_references` | Tool defined but never used |
| **W002** | `check_edge_coverage` | Node not reachable from START |
| **W003** | `check_edge_coverage` | Node has no path to END |
| **W005** | `check_node_types` | Node name contains `__` (reserved for expansion) |

The edge coverage check uses bidirectional graph traversal — forward from START to find reachable nodes, backward from END to find nodes that can complete:

```python
def check_edge_coverage(graph_path: Path) -> list[LintIssue]:
    """Check that all nodes are reachable and have paths to END."""
    # Forward traversal from START
    frontier = {"START"}
    while frontier:
        current = frontier.pop()
        for edge in edges:
            if edge.get("from") == current:
                # ...

    # Backward traversal from END
    frontier = {"END"}
    while frontier:
        current = frontier.pop()
        for edge in edges:
            targets = normalize_targets(edge.get("to"))
            if current in targets:
                # ...
```

### Semantic Checks (`checks_semantic.py`)

These catch logical errors that are structurally valid but semantically wrong:

| Code | Check | What It Catches |
|------|-------|-----------------|
| **E006** | `check_cross_references` | Edge references non-existent node |
| **E008** | `check_cross_references` | `loop_limits` key references non-existent node |
| **E010** | `check_error_handling` | `on_error: fallback` without fallback configuration |
| **E011** | `check_error_handling` | `on_error: retry` on non-LLM node (tool, python, passthrough) |
| **E601** | `check_passthrough_nodes` | Passthrough node without `output` (silent no-op) |
| **E701** | `check_tool_call_nodes` | `tool_call` node missing `tool` field |
| **E702** | `check_tool_call_nodes` | `tool_call` node missing `args` field |
| **E802** | `check_edge_types` | Conditional edge with string `to` (needs list) |
| **W007** | `check_expression_syntax` | `{name}` without `state.` prefix for known state field |
| **W012** | `check_unguarded_cycles` | Node in cycle without `loop_limits` entry |
| **W013** | `check_dynamic_map_without_max_items` | Dynamic map `over:` without `max_items` cap |
| **W014** | `check_expression_syntax` | `{state.X}` references undeclared state field |
| **W801** | `check_expression_syntax` | Condition uses `{braces}` (should be bare names) |

### Contract Checks (`checks_contracts.py`)

These detect the gap between "valid YAML" and "correct graph" — configurations that parse successfully but fail or behave incorrectly at runtime:

```python
"""FR-061: Contract violation lint checks.

E012: Hyphen in identifier position (state key, node name, tool name, state_key)
W020: variables: on type: python (silent no-op)
W021: skip_if_exists on list field with add reducer
"""
```

The `check_identifier_keys` check (E012) is a boundary normalization guard. YAML permits hyphens in keys, but Python identifiers don't allow them. The linter catches this at load time:

```python
def check_identifier_keys(graph_path: Path) -> list[LintIssue]:
    """E012: Keys used as Python identifiers must not contain hyphens."""
    # Check state keys, node names, node state_key values, tool names
    for key in graph.get("state", {}):
        if "-" in key:
            issues.append(LintIssue(
                severity="error", code="E012",
                message=f"State key '{key}' contains hyphen — invalid as Python identifier",
                fix=f"Rename to '{key.replace('-', '_')}'",
            ))
```

The W021 check catches a subtle footgun: `skip_if_exists` on list fields. Since LLM nodes default to `skip_if_exists: True`, and lists are truthy after the first element, a loop that writes to a list would skip after the first iteration:

```python
def check_skip_if_exists_add_reducer(graph_path: Path) -> list[LintIssue]:
    """W021: skip_if_exists on list fields with add reducer is likely wrong.

    Lists are truthy after the first element, so skip_if_exists triggers
    after turn 1 even when you want to keep generating.
    """
```

### Provider-Specific Checks (`checks_providers.py`)

The `check_thinking_budget` function validates Anthropic extended thinking configuration with four sub-checks:

| Code | What It Catches |
|------|-----------------|
| **W071-1** | Explicit `temperature != 1` with `thinking_budget` (Anthropic requires temperature=1) |
| **W071-2** | `thinking_budget` with non-Anthropic provider |
| **W071-3** | `thinking_budget` with model that doesn't support it (pre-3.7) |
| **W071-4** | `thinking_budget` between 1 and 1023 (below Anthropic minimum of 1024) |

### Pattern-Specific Checks (`linter/patterns/`)

Each major node pattern has its own validation module:

- **`router.py`** — validates routes are dicts (not lists), checks for `default_route`, verifies conditional edges have list targets
- **`map.py`** — validates required fields (`over`, `as`, `node`, `collect`), warns on dynamic fan-out without `max_items`
- **`agent.py`** — checks agent tool references, validates `max_iterations`
- **`subgraph.py`** — verifies subgraph file exists, checks input/output mappings
- **`interrupt.py`** — validates interrupt node configuration, checks resume_key patterns

The pattern-specific checks are imported through a clean `__init__.py`:

```python
from yamlgraph.linter.patterns.agent import check_agent_patterns
from yamlgraph.linter.patterns.interrupt import check_interrupt_patterns
from yamlgraph.linter.patterns.map import check_map_patterns
from yamlgraph.linter.patterns.router import check_router_patterns
from yamlgraph.linter.patterns.subgraph import check_subgraph_patterns
```

---

## 5. The Utilities

### The LLM Factory (`utils/llm_factory.py`)

The factory abstracts away seven LLM providers behind a single function with thread-safe caching:

```python
def create_llm(
    provider: ProviderType | None = None,
    model: str | None = None,
    temperature: float | None = 0.7,
    max_tokens: int | None = None,
    thinking_budget: int | None = None,
) -> BaseChatModel:
    """Create an LLM instance with multi-provider support.

    LLM instances are cached by (provider, model, temperature, max_tokens, thinking_budget)
    to improve performance.
    """
```

The provider resolution priority chain is:

```
Function parameter  →  PROVIDER env var  →  "anthropic" (default)
```

Model resolution:

```
Function parameter  →  {PROVIDER}_MODEL env var  →  DEFAULT_MODELS[provider]
```

Provider dispatch is handled by `_dispatch_provider()`, which routes to seven helper functions:

```python
def _dispatch_provider(provider, model, temperature, thinking_budget, **kwargs):
    if provider == "google":
        return _create_google_llm(model, temperature, **kwargs)
    if provider == "mistral":
        return _create_mistral_llm(model, temperature, **kwargs)
    if provider == "openai":
        return _create_openai_llm(model, temperature, **kwargs)
    if provider == "replicate":
        return _create_replicate_llm(model, temperature, **kwargs)
    if provider == "xai":
        return _create_xai_llm(model, temperature, **kwargs)
    if provider == "lmstudio":
        return _create_lmstudio_llm(model, temperature, **kwargs)
    # Default: anthropic
    return _create_anthropic_llm(model, temperature, thinking_budget, **kwargs)
```

Each provider is a lazy import — `from langchain_anthropic import ChatAnthropic` only runs when that provider is actually used.

### The Expression Engine (`utils/expressions.py`)

State expressions like `{state.critique.score}` and arithmetic like `{state.counter + 1}` are resolved by a focused parser — no `eval()` anywhere:

```python
def resolve_state_expression(expr: str | Any, state: dict[str, Any]) -> Any:
    """Resolve {state.path.to.value} expressions.

    Supports:
        - "{name}" -> state["name"]
        - "{state.story.panels}" -> state["story"]["panels"]
        - "{story.title}" -> state["story"]["title"]
    """
```

Arithmetic is handled by regex pattern matching:

```python
# Pattern for arithmetic expressions: {state.field + 1} or {state.a + state.b}
ARITHMETIC_PATTERN = re.compile(r"^\{(state\.[a-zA-Z_][\w.]*)\s*([+\-*/])\s*(.+)\}$")
```

Chained arithmetic (`{state.a + state.b + state.c}`) is explicitly rejected with a clear error — the parser supports one operation per expression to keep the semantics unambiguous.

### The Condition Evaluator (`utils/conditions.py`)

Routing conditions like `score < 0.8` and `a > 1 and b < 2` are evaluated safely without `eval()`:

```python
def evaluate_condition(expr: str, state: dict) -> bool:
    """Safely evaluate a condition expression against state.

    Uses pattern matching - no eval() for security.
    """
    # Handle compound OR (lower precedence) — quote-aware split
    or_parts = _split_compound(expr, "or")
    if or_parts is not None:
        return any(evaluate_condition(part, state) for part in or_parts)

    # Handle compound AND — quote-aware split
    and_parts = _split_compound(expr, "and")
    if and_parts is not None:
        return all(evaluate_condition(part, state) for part in and_parts)

    # Parse single comparison
    match = COMPARISON_PATTERN.match(expr)
    if not match:
        raise ValueError(f"Invalid condition expression: {expr}")
```

The module also provides `negate_condition()` for De Morgan's law transformations, used by the linter to reason about guard conditions.

### The Prompt Loader (`utils/prompts.py`)

Prompt resolution follows a five-strategy cascade:

```python
def resolve_prompt_path(prompt_name, prompts_dir, graph_path, prompts_relative):
    """Resolution order:
    1. If prompts_relative + prompts_dir + graph_path: graph_path.parent/prompts_dir/{prompt_name}.yaml
    2. If prompts_dir specified: prompts_dir/{prompt_name}.yaml
    3. If prompts_relative + graph_path: graph_path.parent/{prompt_name}.yaml
    4. Default: PROMPTS_DIR/{prompt_name}.yaml
    5. Fallback: {parent}/prompts/{basename}.yaml (external examples)
    """
```

This cascade enables self-contained examples (prompts next to the graph YAML), monorepo layouts (shared prompts directory), and external examples that carry their own prompt folders.

### Template Handling (`utils/template.py`)

Variable extraction works for both simple `{var}` syntax and full Jinja2:

```python
def extract_variables(template: str) -> set[str]:
    """Extract all variable names required by a template.

    Handles both simple {var} and Jinja2 {% raw %}{{ var }}, {% for x in var %}{% endraw %} syntax.
    Uses Jinja2's AST parser for Jinja2 templates to correctly handle edge cases.
    """
    if is_jinja:
        env = Environment()
        ast = env.parse(template)
        variables = meta.find_undeclared_variables(ast)
```

The companion `validate_variables()` function provides fail-fast validation before execution — missing variables are reported with the prompt name and a list of what's missing.

### Token Tracking (`utils/token_tracker.py`)

Cost awareness is built into the framework via a LangChain callback handler:

```python
class TokenUsageCallbackHandler(BaseCallbackHandler):
    """Accumulates token usage across all LLM calls in a graph run.

    Works transparently with graph.invoke() via LangGraph's
    contextvars-based callback propagation — no modification to
    node functions required.
    """

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        self.total_calls += 1
        for gen_list in response.generations:
            for gen in gen_list:
                message = getattr(gen, "message", None)
                usage = getattr(message, "usage_metadata", None)
                if usage:
                    self.total_input_tokens += usage.get("input_tokens", 0)
                    self.total_output_tokens += usage.get("output_tokens", 0)
```

### Security (`utils/sanitize.py`)

Input sanitization checks for prompt injection patterns and control characters:

```python
def sanitize_topic(topic: str) -> SanitizationResult:
    """Checks for: length limits, prompt injection patterns, control characters."""
    topic_lower = cleaned.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in topic_lower:
            return SanitizationResult(value=cleaned, is_safe=False, warnings=[...])
```

The dangerous patterns are defined in `config.py`:

```python
DANGEROUS_PATTERNS = [
    "ignore previous", "ignore above", "disregard",
    "forget everything", "new instructions",
    "system:", "<|", "|>",
]
```

Shell commands use `shlex.quote()` for variable escaping — never `eval()`, never `shell=True`.

---

## 6. How to Extend YAMLGraph

### Adding an LLM Provider

The factory pattern in `utils/llm_factory.py` makes this straightforward:

1. Add a default model in `config.py`:
   ```python
   DEFAULT_MODELS = {
       # ...existing providers...
       "newprovider": os.getenv("NEWPROVIDER_MODEL", "default-model-name"),
   }
   ```

2. Add a creation function in `llm_factory.py`:
   ```python
   def _create_newprovider_llm(model, temperature, **kwargs):
       from langchain_newprovider import ChatNewProvider
       return ChatNewProvider(model=model, temperature=temperature, **kwargs)
   ```

3. Add dispatch in `_dispatch_provider()`:
   ```python
   if provider == "newprovider":
       return _create_newprovider_llm(model, temperature, **kwargs)
   ```

4. Update the `ProviderType` type alias and add provider-specific linter checks if needed.

The environment variable table from the project:

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic authentication |
| `GOOGLE_API_KEY` | Google Gemini authentication |
| `MISTRAL_API_KEY` | Mistral authentication |
| `OPENAI_API_KEY` | OpenAI authentication |
| `REPLICATE_API_TOKEN` | Replicate authentication |
| `XAI_API_KEY` | xAI Grok authentication |
| `LMSTUDIO_BASE_URL` | LM Studio local server URL |
| `PROVIDER` | Default LLM provider |

### Adding Custom Tools

Tools are defined in graph YAML and loaded at compile time. Python tools point to importable functions:

```yaml
tools:
  my_tool:
    type: python
    module: my_package.tools
    function: do_something
```

Shell tools run commands with `shlex.quote()` sanitization on all variables — the security boundary is at the tool definition, never at runtime input.

### Adding a New Node Type

1. Add the type to `NodeType` in `constants.py`
2. Create a factory function in the appropriate `node_factory/` module
3. Add the dispatch case in `node_compiler.py`'s `compile_node()`
4. Add the type to `VALID_NODE_TYPES` in `linter/checks.py`
5. Add pattern-specific lint checks in `linter/patterns/`
6. Tag tests with `@pytest.mark.req("REQ-YG-XXX")`

### Checkpointers

Three backends are supported via the `storage/checkpointer_factory.py`:

- **Memory** — `checkpointer: memory` for development and testing
- **SQLite** — `checkpointer: sqlite` for single-process persistence
- **Redis** — `checkpointer: redis` for distributed deployments

Async-compatible checkpointers are created via `get_checkpointer_async()` for use with `ainvoke()`.

### Streaming

Two streaming modes are available:

1. **Node-level streaming** — set `stream: true` on a node to get async token generation via `create_streaming_node()` in `node_factory/streaming.py`
2. **Native LangGraph streaming** — `run_graph_streaming_native()` in `executor_async.py` uses `astream(stream_mode="messages")` for true token-by-token streaming from all LLM nodes, with error propagation (FR-062) and interrupt detection

### The MCP Server

`mcp_server.py` exposes YAMLGraph graphs as MCP tools for Copilot integration:

```python
def create_server(graph_patterns: list[str] | None = None) -> Server:
    """Create and configure the MCP server."""
    graphs = discover_graphs(graph_patterns)
    server = Server("yamlgraph")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(name="yamlgraph_list_graphs", ...),
            types.Tool(name="yamlgraph_run_graph", ...),
        ]
```

The `discover_graphs()` function scans glob patterns for YAML files containing a `nodes` key — this heuristic distinguishes graph definitions from prompt templates without requiring a special file extension or marker.

### The Executor Stack

The executor is layered for progressive capability:

```
execute_prompt()            ← Sync, singleton-based, most common
  └── PromptExecutor.execute()
        ├── prepare_messages()    ← Shared: load prompt, validate, format
        ├── _get_llm()            ← Cached via create_llm()
        └── _invoke_with_retry()  ← Exponential backoff

execute_prompt_async()      ← Async wrapper via run_in_executor
execute_prompt_streaming()  ← Async generator yielding tokens
run_graph_streaming_native()  ← Full graph streaming with error/interrupt events
```

The retry logic in `_invoke_with_retry()` uses exponential backoff with a configurable ceiling:

```python
def _invoke_with_retry(self, llm, messages, output_model=None):
    for attempt in range(self._max_retries):
        try:
            if output_model:
                structured_llm = llm.with_structured_output(output_model)
                return structured_llm.invoke(messages)
            else:
                response = llm.invoke(messages)
                return response.content
        except Exception as e:
            if not is_retryable(e) or attempt == self._max_retries - 1:
                raise
            delay = min(RETRY_BASE_DELAY * (2**attempt), RETRY_MAX_DELAY)
            time.sleep(delay)
```

Only specific exceptions trigger retry — rate limits, connection errors, timeouts, and server errors. Authentication failures and validation errors fail immediately.

---

## Closing

We have traced the path from YAML to running graph: loading and validation, dynamic state generation, node factory dispatch, edge wiring, and finally `graph.compile()`. We have seen how the linter catches errors across four layers of checks — structural, semantic, contractual, and provider-specific — before a single token is generated. And we have mapped every extension point where new providers, tools, node types, and integrations plug in.

The engine is 76 files and 12,700 lines. Every module has a single purpose. Every node follows the same protocol. Every error is typed and traceable. The linter enforces at compile time what would otherwise fail at runtime.

This is the machinery behind YAMLGraph: a compiler that turns declarative YAML into executable LangGraph pipelines, with enough static analysis to catch most mistakes before they cost you tokens.

Throughout this book — from doctrine to linters, from chaplain pipelines to reflexion loops, from diary systems to requirement traceability, from the YAML-first development philosophy to the engine that makes it all run — we have walked the full lifecycle of a development pipeline built on the belief that 60-80% of AI workflows should never require writing Python.

What survives the fire may merge.

---

*Agents' Prayer*

> May I fix at the callsite, not the utility.
> May I kill the cheapest bug — the one in the spec.
> May I normalize at the boundary, trusting no provider's type.
> May I stream to reveal what batch conceals.
> May I understand every protection before I pass it.
> May I read thrice before I grant authority.
>
> When hooks feel slow, let that be the sign they guard.
> When I feel certain, let that be the sign to Judge.
>
> What survives the fire may merge.

---
