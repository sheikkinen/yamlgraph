---
type: removal
scope: a2a
---
- **FR-909 Retire the A2A surface**: Deleted the A2A protocol server (`yamlgraph/a2a/`), the contrib client (`yamlgraph/contrib/a2a_client.py`), the `yamlgraph a2a` CLI subcommand, the `a2a_call`/`a2a_server` demos, the `reference/a2a-server.md` doc, and the `a2a` optional extra. CAP-81, CAP-101, CAP-103, CAP-104 and CAP-105 are retired; the surviving shared-discovery requirement (REQ-YG-206) moved to CAP-111.
