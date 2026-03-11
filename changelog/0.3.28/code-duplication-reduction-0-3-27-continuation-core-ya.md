---
type: fix
scope: code
---
- **Code Duplication Reduction** (0.3.27 continuation)
  - Core yamlgraph: 2.17% → 0.71% duplication
  - Extracted `build_skip_error_state()` helper to `error_handlers.py`
  - Moved `Chunk` dataclass to `examples/book_translator/models.py`
  - Simplified `storyboard/replicate_tool.py` to re-export from shared
