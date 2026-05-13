import { execFile } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function main() {
  const here = dirname(fileURLToPath(import.meta.url));
  const projectRoot = resolve(here, "../../../../");
  const graphPath = resolve(projectRoot, "examples/demos/typescript-node/graph.yaml");
  const yamlgraphBin = process.env.YAMLGRAPH_BIN ?? "yamlgraph";

  const args = [
    "graph",
    "run",
    graphPath,
    "--json",
    "--var",
    "name=World",
    "--var",
    "style=holy see of code",
  ];

  const { stdout } = await execFileAsync(yamlgraphBin, args, {
    cwd: projectRoot,
    env: process.env,
    maxBuffer: 5 * 1024 * 1024,
  });

  const state = JSON.parse(stdout.trim()) as {
    result?: { message?: string; style?: string };
  };

  console.log("Parsed JSON state from yamlgraph graph run --json");
  console.log(`message=${state.result?.message ?? "n/a"}`);
  console.log(`style=${state.result?.style ?? "n/a"}`);
}

main().catch((err: unknown) => {
  const message = err instanceof Error ? err.message : String(err);
  console.error(`TypeScript subprocess demo failed: ${message}`);
  process.exit(1);
});
