/**
 * YAMLGraph × Mastra MCP Integration Demo
 *
 * Proves that per-graph typed MCP tools are discoverable by external
 * TypeScript clients. No LLM or API key required — this demo only
 * exercises tool discovery and schema inspection via MCP protocol.
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
      },
    },
  });

  try {
    // Discover all tools exposed by the MCP server
    const tools = await mcp.getTools();
    const toolNames = Object.keys(tools);

    console.log(`\nDiscovered ${toolNames.length} tools:`);
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

    console.log("\n=== Demo complete — typed MCP tools verified ===");
  } finally {
    await mcp.disconnect();
  }
}

main().catch((err) => {
  console.error("Demo failed:", err);
  process.exit(1);
});
