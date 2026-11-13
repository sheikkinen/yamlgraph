---
type: fix
scope: deps
req: REQ-YG-712
---
- **FR-1156 Anthropic SDK 2.8 floor**: `anthropic>=2.8.0` and `langchain-anthropic>=1.7.7` are now the declared floors, and `constraints/dev-py312.txt` pins anthropic 2.8.0 with its ten-pin cascade (reproduced on a clean Linux/Python 3.12 install). The untyped-subschema walker follows the 2.8 rule: a subschema with a primitive `const` or a non-empty all-primitive `enum` is constrainable even without `type`, and nothing below it is descended or reported as an open object; compositions and `$defs` are still checked. A Pydantic model with `Literal["a", 1]` now binds with `json_schema` instead of being refused. The SDK parity test asserts the 2.8 error text and covers the literal shapes against the real transform. (REQ-YG-712)
