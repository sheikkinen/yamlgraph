# FR-813: The Wrapper Narrowed the Runtime

FR-811 added observability around a public runner while preserving its name and
return behavior, yet narrowed one input shape accidentally. The underlying
LangGraph runtime accepts `None` as an instruction to continue from checkpoint
state. The wrapper classified every non-dict as a dataclass for evidence
hashing, so the instrumentation failed before the runtime could interpret its
own input.

The disabled-path witness mattered as much as the exported span. It proved the
regression belonged to wrapper normalization, not OpenTelemetry setup. The
enabled witness then froze semantic identity: `None` hashes as canonical JSON
`null`; replacing it with `{}` would make the code run while silently changing
checkpoint behavior and evidence.

**Heuristic:** A wrapper around a permissive runtime must test every accepted
control input at the wrapper boundary, including disabled instrumentation. Any
normalization used only for evidence must not alter the value passed onward.

**Seed:** Can runner input types be derived from LangGraph's invocation
protocol so future instrumentation cannot narrow accepted control inputs by
annotation or normalization?
