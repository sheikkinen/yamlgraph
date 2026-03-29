# Diary: FR-208 A2A Protocol Server

**Date:** 2026-03-29
**Feature:** FR-208 A2A Protocol Server
**Capability:** CAP-81

## Cognitive Process

The A2A server follows the proven MCP pattern (CAP-19): discover graphs → generate protocol-specific interface → handle invocation. Key insight: the discovery logic was duplicated between MCP and A2A, violating DRY. Extracting `discover_graphs()` into a shared module was prerequisite work that simplified both implementations.

## Traps Encountered

**Message parsing complexity**: A2A messages can be JSON, key-value, or plain text. Rather than hardcoding expectations, the solution uses a cascading parser strategy: try JSON parse → key-value extraction → single input fallback. This normalizes input at the boundary.

**Task state management**: A2A requires persistent task state (pending → working → completed/failed/canceled). Initially considered reusing LangGraph checkpointing, but the granularity mismatch (LangGraph checkpoints graph state, A2A tracks task lifecycle) led to using a separate InMemoryTaskStore. The two concerns are orthogonal.

## Insights

**Protocol pattern**: The MCP → A2A extraction revealed a generalizable pattern: any protocol surface (MCP, A2A, REST, gRPC) needs the same three components:
1. Discovery mechanism (find graphs)
2. Interface generator (convert metadata to protocol schema)
3. Invocation handler (bridge protocol calls to graph execution)

**Streaming as first-class concern**: A2A's SSE streaming requirement (`task/sendSubscribe`) exposed how graph execution streaming differs from HTTP push streaming. The `run_graph_streaming_native()` generator bridges these: it yields LangGraph events, while the A2A handler converts them to SSE format.

## Heuristic

**Protocol adapters share discovery, diverge at serialization.** When exposing resources through multiple protocols, extract the discovery/registry pattern; let each adapter own its wire format.

## Seed

Could a "protocol adapter registry" auto-generate additional protocol surfaces (REST OpenAPI, gRPC protobuf) from the same graph metadata? The YAML metadata already contains the semantic contract — the protocol binding is mechanical translation.
