---
type: feat
scope: a2a
---
- **FR-253 A2A Consumer to Contrib**: Replace dedicated `type: a2a_call` node type with `yamlgraph.contrib.a2a_client.send_a2a_message()` invoked via `type: python`. Deletes `a2a_nodes.py` (362 lines), `linter/patterns/a2a.py` (140 lines), and `test_a2a_call_node.py` (1235 lines). Net reduction ~1789 lines. FR-252 implemented as prerequisite (`variables:` resolution on python nodes). (REQ-YG-253)
