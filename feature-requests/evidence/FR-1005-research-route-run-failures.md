# FR-1005 evidence: three research-route runs killed by one cell each

Host: Windows 11, `YAMLGRAPH_BIN=.venv/Scripts/yamlgraph.exe`, code SHA
`ec7b607a`, graph `examples/demos/research-route/graph.yaml`, all LLM
nodes `claude-haiku-4-5` at temperature 0. Brief:
`feature-requests/research-briefs/pi-agent-runtime-brief.md`. Logs were
written to git-ignored `tmp/research-pi*.log`; the excerpts below are
verbatim except for line wrapping. No `research-runs.jsonl` line was
stamped for any run (the wrapper stamps only a verified artifact).

## Run 1, 2026-09-05 20:36Z: reducer kills the run on one enum cell

All five persona nodes completed. `gather_findings` completed.
`reduce_findings` raised:

```
Python node reduce_findings failed: empty or invalid required cell in finding 2:
1 validation error for PersonaFinding
solution_class
  Value error, solution_class must be one of ['boundary-enforcement',
  'external-method', 'graph-pipeline', 'os-permissions', 'process-boundary',
  'schema-data', 'subtraction'], got 'process-boundary. The four per-vendor
  concerns (headless contract, tool-call gate, transcript, session id) belong
  in a single abstraction boundary, not scattered across adapters and hooks.'
research.sh: contract violated (graph rc=1): tmp/draft-alternatives.md missing
or empty — tmp/draft-alternatives.md is the proof of research
rc=65
```

Finding 2 is `data_process_finding` (`PERSONA_KEYS` order). The cell's
head, up to the first full stop, is the exact enum value
`process-boundary`; the tail is the persona's rationale leaking into the
enum field. Four valid findings and this one were all discarded.

The brief sentence the persona echoed ("The repo therefore pays
per-vendor for four things it needs once: …") was reworded before run 2.

## Run 2, 2026-09-05 20:39Z: persona node kills the run on one over-length cell

Four persona nodes completed (`os_infra_primitivist`,
`data_process_planner`, `subtractionist`, `librarian_structure`). The
fifth failed inside the LLM node's structured-output parse, was retried
once by `on_error: retry` with the identical input, and failed identically:

```
[ERROR] yamlgraph.error_handlers: Node yamlgraph_native_planner failed after 2 attempts
[ERROR] yamlgraph.tools.python_tool: Python node gather_findings failed:
missing persona findings: yamlgraph_native_finding
recorded node errors:
  yamlgraph_native_planner: unknown_error (OutputParserException): Failed to
  parse YamlgraphNativeFinding from completion {...}. Got: 1 validation error
  for YamlgraphNativeFinding
candidate
  String should have at most 400 characters [type=string_too_long,
  input_value='Introduce a vendor-neutr... in copilot_runtime.py.', input_type=str]
```

The FR-926 cause-citation worked exactly as specified: the operator saw
the node, the category, the exception type and the message in one read.
The run still died, and the four completed findings were lost with it.

## Run 3, 2026-09-05 20:41Z: brief unchanged, byte-identical failure

```
[ERROR] yamlgraph.error_handlers: Node yamlgraph_native_planner failed after 2 attempts
[ERROR] yamlgraph.tools.python_tool: Python node gather_findings failed:
missing persona findings: yamlgraph_native_finding
...
  String should have at most 400 characters [type=string_too_long,
  input_value='Introduce a vendor-neutr... in copilot_runtime.py.', input_type=str]
```

Same truncated prefix as run 2. At temperature 0 the overshoot is a
property of (brief, prompt, model), not of the run; the in-node retry
re-executes the identical call (`yamlgraph/error_handlers.py`,
`handle_retry`) and re-fails.

## The raw completion the parser rejected (run 3)

Read end-to-end before any fix was designed (`read_raw_output_first`).
The `candidate` field is 471 characters; every other field validates.

```json
{"persona": "yamlgraph-native-planner",
 "candidate": "Introduce a vendor-neutral backend abstraction layer as a YAMLGraph
   extension point. Each backend (Copilot CLI, Claude Code) registers its contract
   (session recovery, auth probes, flag matrix, stdout parsing) through a common
   interface. The graph author declares `backend: copilot` or `backend: claude-code`
   in the node; the runtime dispatches to the registered handler without embedding
   vendor logic in copilot_runtime.py.",
 "solution_class": "boundary-enforcement",
 "verdict": "pursue",
 "precedent": "FR-767-graph-authoring-sole-route.md, CAP-249 Invocation-time
   tool-slot binding, constraint_over_code",
 "is_this_a_graph": "none: the runtime seam is infrastructure, not a graph shape.
   The adapters themselves (author, judge, review, outsider) are already graphs;
   this candidate moves vendor dispatch logic into YAMLGraph's extension-point
   layer, not into a new graph.",
 "effort_risk": "medium/high: requires refactoring copilot_runtime.py into a
   registry pattern and moving per-backend logic (banner pinning, auth probes,
   flag matrices, stdout parsing) into separate handler modules. Existing 578
   test lines must migrate to handler-scoped tests. Enforcement gate (FR-883 R-4)
   applies because tool-call gates inside third-party runtimes inherit that gate.",
 "rationale": "This isolates vendor-specific contracts from graph execution,
   making each backend testable independently and allowing new backends (e.g.,
   pi, future providers) to register without modifying core runtime. It honors
   payer honesty (FR-959) by making the backend choice explicit in the graph,
   not implicit in environment state or fallback logic."}
```

Surprising details a fabricated dump would not carry: the persona cites
`CAP-249` (invocation-time tool-slot binding), a real capability with no
obvious vocabulary link to the brief; `effort_risk` is 341 characters,
itself near the cap; the persona independently proposes a registry
pattern the FR-959 dissent column had declined to resolve.

## Prior witness of the same class

`feature-requests/FR-926-research-failure-cites-recorded-cause.md`,
2026-08-30: "three consecutive runs of the FR-925 brief … `ValidationError:
rationale … string_too_long`, retried and re-failed identically". FR-926
surfaced the cause and deferred the larger fix "until recurrence". This
file is the recurrence.
