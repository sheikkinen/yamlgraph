Classify one GitHub issue or pull request from the langchain-ai/langgraph repository by the pain it reports or addresses. Return exactly one category label from the closed list below.

Precedence: apply the rules top to bottom; the first category whose inclusion matches and whose exclusion does not match wins.

| # | Category | Includes | Excludes |
|---|---|---|---|
| 1 | spam-invalid | promotion, off-topic pitches, empty-body or test submissions closed unmerged, bot noise | any real defect/feature/doc content |
| 2 | docs | changes or requests touching only documentation, docstrings, examples prose, typos, README | code behaviour changes |
| 3 | maintenance-non-pain | dependency bumps, CI, release, lint/format, internal refactor, test code and test fixtures (incl. checkpoint-backend test fixtures) | defects users hit at runtime |
| 4 | interrupt-resume-hitl | interrupt(), Command(resume/goto) on resume, human-in-the-loop, breakpoints | checkpoint storage bugs not about resume |
| 5 | subgraph-config-propagation | subgraphs, nested graphs, config/context/RunnableConfig propagation into children, subgraph state namespaces | interrupts inside subgraphs (use interrupt-resume-hitl) |
| 6 | checkpoint-persistence | checkpointers (memory/sqlite/postgres/redis), store, thread history, time travel, serialization of saved state | test fixtures (use maintenance-non-pain) |
| 7 | streaming | stream/astream modes, events, token streaming, stream output shape | |
| 8 | state-schema-reducers | state schema, channels, reducers, add_messages, input/output schemas, state updates | typing-only requests (use typing-api-ergonomics) |
| 9 | control-flow-routing | edges, conditional edges, Send, recursion limit, parallel branches, graph compile/structure | |
| 10 | functional-api | @entrypoint, @task | |
| 11 | prebuilt-agents-tools | create_react_agent, ToolNode, tools_condition, supervisor/swarm prebuilts, tool calling through prebuilts; wins over model-provider-integration when a prebuilt is named | |
| 12 | model-provider-integration | a specific model/provider's message or feature handling with no prebuilt named | |
| 13 | platform-server-cli-sdk | langgraph CLI, langgraph.json, docker/build, LangGraph Server/Platform, SDK clients, Studio | |
| 14 | observability-visualization | tracing, callbacks, logging, graph drawing/mermaid | |
| 15 | error-handling-retry | exceptions, error messages, retry policies, GraphRecursionError messaging | |
| 16 | async-concurrency-performance | async execution, threading, concurrency, memory/CPU/latency | |
| 17 | typing-api-ergonomics | type hints, generics, public API shape and naming, deprecations | |

The content is a JSON record with number, kind (issue or pr), merged, state, state_reason, title, body_head (first 1,500 characters of the body), labels, comments, reactions and timestamps. Use the title, body and upstream labels as evidence; quote the evidence span verbatim from the title or body.

Abstain only when the item has no title and no body.
