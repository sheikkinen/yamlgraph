# FR-939 research record — map overflow disposition

**Prior art:** governed by `FR-939-map-overflow-policy.md` (the FR this
record backs — full disposition there). FR-936 and its judgement are
the SPLIT parent (this is deliverable D-2). FR-851 audited requirement
witnesses repo-wide, no overflow-contract overlap; FR-733 is a CWE
classifier application, shares only generic tokens.

- promoted from: tmp/draft-alternatives.md (FR-890 sole route, scripts/research.sh)
- brief: feature-requests/research-briefs/fr939-map-overflow-brief.md

## Solution classes (R-1 fold, per FR-939 judgement)

The raw route table below converged three personas on one class with
different enum spellings; per judgement R-1 the genuine solution
classes are compared here. Correction carried through: load-time
validation can reject an invalid policy VALUE, but the overflow
COMPARISON is necessarily runtime — `over` resolves from state
(`map_compiler.py:338-354`); the raw table's "reject overflow at
graph-load time" claim was wrong.

| class | mechanism | precedent | cost/risk | disposition |
|---|---|---|---|---|
| 1. Unconditional fail-on-overflow | Remove disposition choice; overflow always raises pre-`Send` | Airflow `max_map_length`: source task fails at expansion, never partial-executes | Low cost; kills the deliberate sampling use FR-027-era graphs may rely on | REJECTED — sampling must remain expressible (brief constraint) |
| 2. Optional typed policy, default `error` | `on_overflow: Literal["error","truncate"] \| None` on node + `defaults.on_overflow`; load-time value validation; runtime pre-dispatch enforcement | Airflow fail-fast for the default; FR-027 truncation preserved as opt-in | Medium cost; graphs silently over cap today start failing loudly — that failure is the defect surfacing | CHOSEN |
| 3. Mandatory explicit policy, no default | Every map node must declare disposition; load fails otherwise | Subtractionist persona; "config is truth" maximalism | Forces an edit on every existing map graph while adding no safety beyond class 2's default | REJECTED |
| 4. In-band partial-success metadata | Truncate but record `{dropped: N}` in returned state; run still succeeds | Batch systems reporting partial completions | Keeps the plausible wrong answer; consumer must remember to check the marker — the trap this FR exists to kill | REJECTED |
| 5. Remove/relocate cap to bounded scheduling | Replace cap with chunked/windowed dispatch so no item is ever dropped | Durable-map gap analysis in `docs/plan-web-toolkit.md` | Correct long-term but is FR-936's deferred durability scope, not overflow disposition | REJECTED here — out of FR-939 fence (judgement C-6) |

Preserved disagreement: default `error` (chosen; FR-936 judgement AC-05,
Commandment 6) vs default `truncate` (two personas, continuity of
existing capped graphs) vs mandatory declaration (class 3).

`is_this_a_graph`: no — a compile-time schema contract plus a runtime
guard inside the framework's fan-out boundary; no graph-shaped
alternative can act before the fan-out cost is paid. All five personas
concur.

## Raw route output (provenance appendix)

# Draft alternatives

- brief: fr939-map-overflow-brief.md
- run date: 2026-08-31T03:15:01Z
- personas executed: os-infra-primitivist, data-process-planner, yamlgraph-native-planner, subtractionist, librarian

| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk | rationale |
|---|---|---|---|---|---|---|---|
| Reject overflow at graph-load validation time using Pydantic schema constraints on `max_items` and `max_map_items` fields. Enforce non-negative integers; fail fast before compilation, surfacing node name and cap value in the validation error message. | os-infra-primitivist | os-permissions | pursue | CAP-01 Config Loading & Validation; CAP-02 Graph Compilation; Commandment 3 (config is truth, validated); Commandment 5 (Typed schema surface, Pydantic) | No. This is a compile-time contract enforcement inside the framework's config loader, not a graph-shaped alternative. The mechanism sits in the platform's validation boundary before any node executes. | Low effort, low risk. Pydantic validators already guard config fields; adding range and type constraints is a standard schema hardening pattern with no runtime overhead or behavioral change to in-cap runs. | The platform's config loader (CAP-01) already owns validation. Pushing the overflow decision into Pydantic schema constraints moves the guard from runtime (map_compiler.py:350-365) to load time, eliminating silent truncation. This satisfies Commandment 3 (config validated) and Commandment 5 (typed schema) without inventing new machinery. |
| Add typed `overflow_mode` enum (error/warn/truncate) to node and graph schema; validate at load time; surface decision before first sub-node executes with node name, item count, cap. | data-process-planner | schema-data (convergent x3) | pursue | CAP-17 Execution Safety Guards; CAP-01 Config Loading & Validation; FR-936 judgement AC-05/AC-06; brief-echo: overflow disposition must be configurable, observable, decidable pre-execution, and surfaced with actionable context. | No. This is a compile-time schema and validation contract inside the framework. The map node's fan-out logic is deterministic and does not require graph-shaped alternatives; the decision point is structural, not behavioral routing. | Medium effort, low risk. Adds Pydantic enum field to MapNode and GraphDefaults, validation in config loader, and pre-execution check in map_compiler. Existing graphs default to current behavior (truncate); no breaking change if default is preserved. | Dissolves the problem at the input shape and schema layer before any guard must catch it. Moves overflow disposition from silent fallback to explicit, typed, validated contract. Satisfies Commandment 3 (config is truth, validated), Commandment 5 (typed schema), Commandment 6 (no silent hedges), and FR-936 constraints (C-1, C-6, pre-execution decidability, actionable error context). |
| Add a typed `overflow_policy` field to map node schema (enum: error/warn/truncate) and graph defaults, validated at compile time. Raise an error before any sub-node executes if items exceed cap and policy is error. Include node name, item count, and cap in the error message. Preserve truncate-and-warn as opt-in for sampling use cases. | yamlgraph-native-planner | schema-data (convergent x3) | pursue | FR-936, CAP-02, CAP-17, plausible_wrong_answer, Commandment 6 | none: this is a compile-time schema and validation contract change inside the framework, not a graph-shaped orchestration problem. The research confirms no graph-shaped alternative (e.g., a separate validation subgraph) is mechanically enforceable before fan-out cost is paid. | medium: Pydantic schema extension is low-friction; compile-time validation hook is proven (CAP-02). Risk is regression in existing graphs relying on silent truncate—mitigated by defaulting to current behavior and requiring explicit opt-in for error policy. | This surfaces overflow as a decidable, observable contract before execution, satisfies Commandment 6 (no silent fallbacks), preserves sampling use cases, and makes the disposition actionable without log archaeology. Typed schema (Commandment 5) and validation at load time (Commandment 3) are both met. |
| Delete the `max_items` and `max_map_items` configuration knobs entirely. Require explicit overflow disposition (fail-fast, sample-N, or stream-chunked) as a mandatory node-level schema field with no fallback default. Graphs relying on silent truncation must be rewritten to declare their intent. | subtractionist | schema-data (convergent x3) | pursue | FR-936 judgement; CAP-17 Execution Safety Guards; brief-echo: current truncate-and-warn behavior is silent data loss at production scale and violates Commandment 6. | No. This is a compile-time schema contract change inside the framework. The overflow disposition is decided before any sub-node executes, not a graph-shaped alternative. | Medium. Requires Pydantic schema update, map_compiler.py refactor to reject missing disposition, and test suite rewrite. Risk: existing graphs break loudly at load time, forcing explicit migration—this is intentional and correct. | Silent fallbacks are the root cause. Forcing explicit disposition at schema time (before execution) eliminates the plausible_wrong_answer trap, satisfies Commandment 6, and makes the contract observable in YAML. Graphs that need sampling remain expressible; they simply declare it. |
| Apache Airflow's dynamic task mapping uses `max_map_length` configuration (default 1024) to limit task expansion. When exceeded, the source task fails immediately at parse time, not at runtime after partial execution. This fail-fast pattern prevents silent data loss and makes the overflow contract observable in the DAG execution state. | librarian | external-method | pursue | https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html | Yes. Airflow DAGs are directed acyclic graphs; dynamic task mapping is a compile-time graph expansion mechanism that fails before execution begins, making overflow detection part of the graph shape contract. | Medium. Airflow's approach requires validation before sub-node dispatch (matching constraint C-4), but differs from yamlgraph's current truncate-and-warn. Adoption requires schema-level disposition enum, pre-execution validation gate, and test RED before fix. | Airflow's fail-fast on overflow is the inverse of yamlgraph's truncate-and-warn. It surfaces the contract in task state (not log-only), prevents silent data loss, and validates at parse time before any work executes. This directly addresses the plausible_wrong_answer trap and Commandment 6 (no silent fallbacks). |
