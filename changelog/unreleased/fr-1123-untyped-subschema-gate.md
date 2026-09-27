---
type: fix
scope: schema
req: REQ-YG-712
---
- **FR-1123 Refuse untyped subschemas before Anthropic constrained decoding**: an output schema containing `Any` or `list[Any]` on an Anthropic node now fails at graph compile (and in `bind_structured_output`) with the prompt, node, model and field path, instead of failing at call time and silently nulling the state key. Lint adds E016 (static Anthropic provider) and W028 (`{state.x}` provider). The nine affected example prompts (daily_digest, book_translator, yamlgraph_gen, codegen) now declare concrete types. (REQ-YG-712)
