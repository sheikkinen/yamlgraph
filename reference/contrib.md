# Contrib Utilities

Shared utility functions extracted from common patterns across YAMLGraph pipelines.

## Installation

Built into YAMLGraph core - no extra install required.

```python
from yamlgraph.contrib import get_map_result, to_serializable
```

## Functions

### `get_map_result(item)`

Extract the result from a map node output item.

Map nodes store results with keys like `_map_<node_name>_sub`. This function finds and returns that result without hardcoding the key name.

```python
from yamlgraph.contrib import get_map_result

# Map node returns list of items like:
# [{"_map_generate_sub": {"title": "Hello"}}, ...]

for item in state["collected_results"]:
    result = get_map_result(item)
    if result:
        print(result["title"])  # "Hello"
```

**Arguments:**
- `item` - A single item from a map node's collected output (dict)

**Returns:**
- The nested result object (Pydantic model or dict), or `None` if not found

### `to_serializable(obj)`

Convert any object to JSON-serializable form.

Recursively converts Pydantic models to dicts. Handles nested structures including lists and dicts containing Pydantic models.

```python
from yamlgraph.contrib import to_serializable
from pydantic import BaseModel

class Character(BaseModel):
    name: str
    level: int

char = Character(name="Hero", level=5)

# Convert for JSON output
data = to_serializable(char)  # {"name": "Hero", "level": 5}

# Works with nested structures
chars = [Character(name="A", level=1), Character(name="B", level=2)]
data = to_serializable(chars)  # [{"name": "A", "level": 1}, ...]
```

**Arguments:**
- `obj` - Any object (Pydantic model, dict, list, or primitive)

**Returns:**
- JSON-serializable version of the object (dict, list, or primitive)

## Use Cases

### Processing Map Node Results

```python
from yamlgraph.contrib import get_map_result, to_serializable

def process_results(state: dict) -> dict:
    """Process collected map results."""
    items = state.get("collected_items", [])

    processed = []
    for item in items:
        result = get_map_result(item)
        if result:
            # Convert Pydantic models to dicts for JSON output
            processed.append(to_serializable(result))

    return {"processed": processed}
```

### Writing Results to File

```python
import json
from yamlgraph.contrib import to_serializable

def save_results(state: dict) -> dict:
    """Save results to JSON file."""
    data = to_serializable(state["results"])

    with open("output.json", "w") as f:
        json.dump(data, f, indent=2)

    return {"saved": True}
```

### `SkipReport`

Report on skipped/failed nodes by reading `state["errors"]`.

When nodes fail with `on_error: skip`, they write a `PipelineError` to `state["errors"]` but produce no visible output. `SkipReport` reads these errors and provides human-readable summaries.

```python
from yamlgraph.contrib import SkipReport

def report_skips(state: dict) -> dict:
    """Report what was skipped during pipeline execution."""
    report = SkipReport.from_state(state)

    if report.count > 0:
        report.log()  # Logs at WARNING level
        return {"skip_summary": report.summary()}

    return {"skip_summary": "All nodes completed successfully."}
```

**With total count:**
```python
# Show X/Y format when you know expected node count
tool_keys = ["scamper", "five_whys", "jtbd", "first_principles"]
report = SkipReport.from_state(state, node_keys=tool_keys)
# Output: "⚠ 2/4 skipped: [scamper: timeout, jtbd: validation error]"
```

**Methods:**
- `count` - Number of errors
- `summary()` - Human-readable string
- `log()` - Log summary at WARNING level
- `to_dict()` - JSON-serializable output

## Why Use These?

**Before (duplicated pattern):**
```python
# This pattern was copied across 10+ pipelines
if hasattr(obj, "model_dump"):
    data = obj.model_dump()
else:
    data = obj
```

**After (single import):**
```python
from yamlgraph.contrib import to_serializable
data = to_serializable(obj)
```

## Related

- [Map Nodes](map-nodes.md) - Parallel processing with fan-out
- [Patterns](patterns.md) - Common pipeline patterns
- [ARCHITECTURE.md](../ARCHITECTURE.md#20-contrib-utilities) - REQ-YG-070, REQ-YG-071 specification
