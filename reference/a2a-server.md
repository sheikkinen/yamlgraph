# A2A Server

Expose YAMLGraph graphs as [A2A (Agent-to-Agent)](https://google.github.io/A2A/) protocol agents. Clients can discover graphs via Agent Cards, send tasks, stream responses, and handle interrupts — all over HTTP JSON-RPC.

## Quickstart

### 1. Install A2A dependency

```bash
pip install -e ".[a2a]"
```

### 2. Start the server with the hello graph

```bash
yamlgraph a2a serve examples/demos/hello/ --port 9090
```

### 3. Fetch the Agent Card

```bash
curl http://localhost:9090/.well-known/agent-card.json
```

### 4. Send a task

```bash
curl -X POST http://localhost:9090/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "msg-1",
        "parts": [{"kind": "text", "text": "name=World style=casual"}]
      }
    }
  }'
```

The hello graph requires `name` and `style` variables. The message text uses `key=value` format, which the server parses automatically.

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `yamlgraph a2a serve [path] --host --port` | Start A2A server exposing discovered graphs |
| `yamlgraph a2a card [path] --host --port` | Print Agent Card JSON without starting server |

### a2a serve

Start the A2A HTTP server.

```bash
yamlgraph a2a serve <graph_path> [options]
```

**Arguments:**
- `graph_path` — Path to a graph YAML file or directory. Defaults to discovering graphs from `examples/demos/*/` and `examples/*/`.

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `0.0.0.0` | Server bind address |
| `--port` | `8080` | Server port |

**Examples:**

```bash
# Serve a single graph
yamlgraph a2a serve examples/demos/hello/graph.yaml --port 9090

# Serve all graphs in a directory
yamlgraph a2a serve examples/demos/hello/ --port 9090

# Serve all discovered graphs (default patterns)
yamlgraph a2a serve
```

### a2a card

Print the Agent Card JSON for discovered graphs without starting the server.

```bash
yamlgraph a2a card <graph_path> [options]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `localhost` | Hostname for Agent Card URL |
| `--port` | `8080` | Port for Agent Card URL |

**Example:**

```bash
yamlgraph a2a card examples/demos/hello/ --port 9090
```

---

## Agent Card Generation

`build_agent_card()` maps graph YAML metadata to an A2A `AgentCard`. Each discovered graph becomes a skill:

| Graph YAML field | Agent Card field | Description |
|-----------------|-----------------|-------------|
| `name` | `skills[].id`, `skills[].name` | Graph name becomes skill identifier |
| `description` | `skills[].description` | Graph description becomes skill description |
| presence of `nodes` | included in discovery | Only YAML files with `nodes` key are treated as graphs |
| `state` keys | `required_vars` | Used at message parse time to validate input |

**Example Agent Card** (for the hello graph):

```json
{
  "name": "YAMLGraph A2A Server",
  "description": "YAMLGraph graphs exposed as A2A agents",
  "url": "http://localhost:9090/",
  "version": "0.4.63",
  "skills": [
    {
      "id": "hello-world",
      "name": "hello-world",
      "description": "Simple greeting generator demonstrating basic LLM usage",
      "tags": ["yamlgraph"]
    }
  ],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "capabilities": {
    "streaming": true
  }
}
```

All Agent Cards are generated with `authentication: null`. See [Authentication](#authentication) for production patterns.

---

## Message-to-State Mapping

`parse_a2a_message()` converts A2A message text into graph input variables. It tries four parsing modes in order:

### 1. JSON mode

If the text is valid JSON object, keys map directly to variables.

```json
{"name": "World", "style": "casual"}
```

### 2. key_value mode

If the text contains `=`, it is parsed as space-separated `key=value` pairs (using `shlex.split` for proper quoting).

```
name=World style=casual
```

Quoted values work: `name="Hello World" style=casual`

### 3. single_input mode

If the graph has exactly one required variable, the entire text is assigned to it.

```
Hello World
```

→ `{"input": "Hello World"}` (if the only required var is `input`)

### 4. Fallback

If none of the above match, the entire text is assigned to the `input` key.

```
some free-form text
```

→ `{"input": "some free-form text"}`

**Validation:** After parsing, `_validate_required_vars()` checks that all required variables (from graph `state` keys) are present. Missing variables raise `ValueError` with code `missing_variables`.

---

## Task Lifecycle

The A2A server maps graph execution to the A2A task lifecycle:

| A2A Method | YAMLGraph Behaviour |
|------------|---------------------|
| `message/send` | Stream-execute graph, return final task with artifacts |
| `message/stream` | SSE event stream: `working` → incremental artifact chunks → `completed` |
| `tasks/get` | Retrieve task status and artifacts from in-memory store |
| `task/cancel` | Cancel running asyncio task |

### State Transitions

```
submitted → working → completed
                    → failed
                    → input-required (interrupt) → working (resume) → completed
                    → canceled
```

### message/send

1. Server emits `TaskStatusUpdateEvent` with state `working`
2. Message text is parsed into variables via `parse_a2a_message()`
3. Graph is executed via `run_graph_streaming_native()` with `thread_id` = `task_id`
4. Each token chunk is emitted as `TaskArtifactUpdateEvent`
5. Final `TaskStatusUpdateEvent` with state `completed` is emitted

### message/stream (SSE)

Same execution path as `message/send`, but events are delivered as Server-Sent Events in real-time. Each token chunk produces an individual `TaskArtifactUpdateEvent`, enabling true incremental streaming:

1. `TaskStatusUpdateEvent` — state: `working`
2. `TaskArtifactUpdateEvent` — per-token chunks (one event per streaming chunk)
3. `TaskStatusUpdateEvent` — state: `completed`

### tasks/get

Retrieves task status and artifacts for previously submitted tasks. The SDK's `InMemoryTaskStore` automatically persists task state from events emitted by the executor.

```bash
curl -X POST http://localhost:9090/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 2,
    "method": "tasks/get",
    "params": {"id": "<task-id>"}
  }'
```

### task/cancel

Cancels a running graph execution. The server cancels the asyncio task and emits `TaskStatusUpdateEvent` with state `canceled`.

---

## Error Mapping

`map_pipeline_error()` converts `PipelineError` types to A2A error types:

| PipelineError type | A2A error | Semantics |
|--------------------|-----------|-----------|
| `LLM_ERROR` | `InternalError` | LLM provider failure |
| `STATE_ERROR` | `InternalError` | State management error |
| `UNKNOWN_ERROR` | `InternalError` | Unexpected failure |
| `VALIDATION_ERROR` | `InvalidParamsError` | Input validation failure |
| `PROMPT_ERROR` | `InvalidParamsError` | Prompt template error |
| `VERIFICATION_ERROR` | `InvalidParamsError` | Output verification failure |

When a `PipelineError` occurs, the error is mapped to the appropriate A2A error type. The error data includes:

```json
{
  "node": "node_name",
  "retryable": false,
  "error_type": "LLM_ERROR"
}
```

Non-`PipelineError` exceptions result in a `failed` task state with the exception message.

---

## Interrupt / Human-in-Loop

When a graph hits an `interrupt_before` or `interrupt_after` node, the streaming executor detects the interrupt via `StreamEvent(type="interrupt")` and emits `TaskState.input_required` with the interrupt payload forwarded to the client.

### Detection

During streaming execution, `run_graph_streaming_native()` detects the `__interrupt__` marker in graph state and yields `StreamEvent(type="interrupt", payload=...)` when a graph pauses at an interrupt node. The executor maps this to an A2A `TaskStatusUpdateEvent` with state `input_required`.

### Interrupt Payload

The interrupt payload (the question or prompt from the graph) is forwarded to the client as the message text in the `input_required` event. This tells the client *what* to answer:

```json
{
  "status": {
    "state": "input-required",
    "message": {
      "role": "agent",
      "parts": [{"text": "What is your preferred language?"}]
    }
  }
}
```

### Resume Flow

When the client sends a follow-up `message/send` with the same `task_id`, the executor detects the task is in `input_required` state (via `context.current_task`) and resumes the graph using `Command(resume=user_input)` instead of fresh invocation:

1. Client sends `message/send` with `task_id` of an interrupted task
2. Executor detects `current_task.status.state == input_required`
3. User input is passed as `Command(resume=text)` to `run_graph_streaming_native()`
4. Graph resumes from the interrupt point with the user's answer
5. Streaming continues → `completed`

**Requirements:**
- The graph must have a checkpointer configured for resume to work (thread_id = task_id)
- The `run_graph_streaming_native()` infrastructure handles checkpointer-based resume

```bash
# Step 1: Initial task hits interrupt
curl -X POST http://localhost:9090/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "msg-1",
        "parts": [{"kind": "text", "text": "name=World style=casual"}]
      }
    }
  }'
# Response: task with state "input-required", message: "What language?"

# Step 2: Resume with user input
curl -X POST http://localhost:9090/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 2,
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "msg-2",
        "taskId": "<task-id-from-step-1>",
        "parts": [{"kind": "text", "text": "English"}]
      }
    }
  }'
# Response: task with state "completed"
```

---

## Authentication

**Status:** Not implemented in the A2A server itself.

Agent Cards are generated with `authentication: null`. For production deployments, use a reverse proxy to add authentication:

- **nginx**: Basic auth, JWT validation, or OAuth2 proxy
- **Caddy**: Automatic TLS + built-in auth middleware
- **Traefik**: Forward auth middleware

The recommended deployment pattern is:

```
Client → Reverse Proxy (TLS + Auth) → yamlgraph a2a serve (localhost)
```

See [Deployment Patterns](#deployment-patterns) for full examples.

---

## Deployment Patterns

### Standalone (development)

Run the server directly for local development and testing:

```bash
yamlgraph a2a serve examples/demos/hello/ --port 9090
```

### Behind Reverse Proxy (production)

For production, place the A2A server behind a reverse proxy that handles TLS termination and authentication:

```nginx
# nginx example
server {
    listen 443 ssl;
    server_name a2a.example.com;

    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Container

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[a2a]"
EXPOSE 8080
CMD ["yamlgraph", "a2a", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

---

## Relationship to MCP Server

YAMLGraph exposes graphs through two protocol servers that share the same discovery layer:

| Aspect | MCP (`yamlgraph mcp serve`) | A2A (`yamlgraph a2a serve`) |
|--------|-----|-----|
| Transport | stdio | HTTP (JSON-RPC) |
| Discovery | Shared `discovery.py` | Shared `discovery.py` |
| Model | Tools | Agent Skills |
| Streaming | No | SSE |
| Auth | None (IDE-controlled) | None (use reverse proxy) |
| Use case | IDE integration (Copilot, Claude) | Agent-to-agent communication |

Both servers use `discover_graphs()` from `discovery.py` to scan the same glob patterns:

- `examples/demos/*/*.yaml`
- `examples/*/*.yaml`

The MCP server exposes graphs as tools (`yamlgraph_list_graphs`, `yamlgraph_run_graph`). The A2A server exposes graphs as agent skills with the A2A JSON-RPC protocol.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ImportError: A2A SDK not installed` | `pip install -e ".[a2a]"` |
| `uvicorn not installed` | `pip install uvicorn` |
| No graphs found | Verify path matches a graph YAML with `nodes` key |
| `missing_variables` error | Message text must include all required state variables |
| Server not responding | Check host/port; default binds to `0.0.0.0:8080` |

## Related

- [`reference/mcp-server.md`](mcp-server.md) — MCP server reference
- [`examples/demos/a2a_server/`](../examples/demos/a2a_server/) — A2A server demo
- [`examples/demos/a2a_call/`](../examples/demos/a2a_call/) — A2A call consumer demo

Last reviewed: 2026-05-03
