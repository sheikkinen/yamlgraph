# MCP Sampling Loopback PoC

**Purpose**: Prove that an MCP server tool can call back to the connected
AI assistant (Copilot/Claude) via MCP Sampling (`sampling/createMessage`).

## Architecture

```
Copilot ──tool call──► loopback_pray tool
                              │
  ◄──sampling/createMessage───┘  "Let us pray"
       (Copilot's LLM responds)
  ──response──►
                              │
  ◄──tool result──────────────┘  Returns the prayer
```

## Files

- `mcp_server.py` — Standalone MCP server with `loopback_pray` tool
- `README.md` — This file

## Usage

### 1. Configure in VS Code

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "loopback-poc": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/python3",
      "args": ["${workspaceFolder}/scripts/loopback-poc/mcp_server.py"]
    }
  }
}
```

### 2. Test from Copilot Chat

Ask Copilot: "Use the loopback_pray tool"

### 3. Expected Result

The tool sends "Let us pray" to Copilot's LLM via MCP sampling.
Copilot generates a prayer and returns it as the tool result.
The server **did not use any API key** — the LLM call was free.

## What This Proves

1. MCP servers can request LLM completions from the connected client
2. YAMLGraph graphs could delegate reasoning to the host AI assistant
3. Zero API keys needed for the sampling call
4. The protocol is bidirectional — not just tool-provider
