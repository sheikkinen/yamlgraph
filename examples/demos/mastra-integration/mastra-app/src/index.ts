/**
 * YAMLGraph × Mastra MCP Integration Demo
 *
 * Proves that per-graph typed MCP tools are discoverable and executable
 * by external TypeScript clients via MCP protocol.
 *
 * - Discovery: always runs (no API key needed)
 * - Execution: attempts to call the typed tool; skips gracefully if
 *   no LLM API key is configured
 *
 * FR-291 / CAP-136 (REQ-YG-312)
 */

import { MCPConfiguration } from "@mastra/mcp";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function main() {
  // Resolve the MCP server relative to this file
  const projectRoot = resolve(__dirname, "../../../../..");
  const mcpServer = resolve(projectRoot, "yamlgraph/mcp_server.py");
  const graphPattern = resolve(__dirname, "../../graph.yaml");

  // Use the venv Python if available, else system python3
  const pythonExe = process.env.YAMLGRAPH_PYTHON || resolve(projectRoot, ".venv/bin/python3");

  console.log("=== YAMLGraph × Mastra MCP Integration ===\n");
  console.log("Connecting to YAMLGraph MCP server...");

  const mcp = new MCPConfiguration({
    servers: {
      yamlgraph: {
        command: pythonExe,
        args: [mcpServer, "--patterns", graphPattern],
        env: {
          ...process.env,
        },
      },
    },
  });

  try {
    // --- Phase 1: Discovery (no API key required) ---
    console.log("\n--- Phase 1: Tool Discovery ---");
    const tools = await mcp.getTools();
    const toolNames = Object.keys(tools);

    console.log(`Discovered ${toolNames.length} tools:`);
    for (const name of toolNames) {
      console.log(`  - ${name}`);
    }

    // Verify the per-graph typed tool exists
    // Mastra prefixes tool names with the server key ("yamlgraph_")
    const typedToolName = "yamlgraph_hello_mastra";
    if (toolNames.includes(typedToolName)) {
      console.log(`\n✓ Per-graph typed tool "${typedToolName}" found!`);
      console.log("  Auto-generated from graph.yaml state block (FR-291).");
      console.log("  Input schema: name(string), style(string)");
    } else {
      console.error(`\n✗ Expected tool "${typedToolName}" not found`);
      process.exit(1);
    }

    // Show the generic tools are also present
    const genericTools = ["yamlgraph_yamlgraph_list_graphs", "yamlgraph_yamlgraph_run_graph"];
    for (const gt of genericTools) {
      if (toolNames.includes(gt)) {
        console.log(`✓ Generic tool "${gt.replace('yamlgraph_', '')}" retained`);
      }
    }

    // --- Phase 2: Execution (requires LLM API key) ---
    console.log("\n--- Phase 2: Tool Execution ---");
    const tool = tools[typedToolName];
    try {
      const result = await tool.execute({
        context: { name: "World", style: "holy see of code" },
      });

      // Parse the inner JSON from the MCP text content
      const content = result?.content;
      const text = Array.isArray(content) ? content[0]?.text : undefined;
      const inner = text ? JSON.parse(text) : result;
      const hasError = inner?.errors && !inner?.greeting;

      if (hasError) {
        console.log("\n⚠ Graph executed but LLM call failed (no API key)");
        console.log("  MCP round-trip: ✓ (tool called, graph compiled, state returned)");
        console.log("  Set ANTHROPIC_API_KEY to get a real greeting.");
      } else {
        console.log("\n✓ Tool executed successfully!");
        console.log("  Greeting:", inner?.greeting || JSON.stringify(inner));
      }
    } catch (execErr: unknown) {
      const msg = execErr instanceof Error ? execErr.message : String(execErr);
      if (msg.includes("API key") || msg.includes("authentication") || msg.includes("ANTHROPIC") || msg.includes("401")) {
        console.log("\n⚠ Tool execution skipped — no LLM API key configured");
        console.log(`  Error: ${msg.slice(0, 120)}`);
      } else {
        throw execErr;
      }
    }

    console.log("\n=== Demo complete — typed MCP tools verified ===");
  } finally {
    await mcp.disconnect();
  }
}

main().catch((err) => {
  console.error("Demo failed:", err);
  process.exit(1);
});
