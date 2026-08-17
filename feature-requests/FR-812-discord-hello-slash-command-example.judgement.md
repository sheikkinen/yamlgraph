# Judgement: FR-812 Discord `/hello` Slash-Command Example

**Prior art:** FR-070 (rejected web playground) dispositioned in the FR — visual
*authoring* ban does not cover a text-command execution adapter in `examples/`.
Gate noun-hits FR-288 (hook preflight), FR-781 (macOS file hook), FR-782
(self-portrait example) share only the tokens "command"/"example" — no overlap
with Discord chat-platform integration. FR-812-*.md is this FR itself.

**Verdict:** APPROVED WITH REVISIONS — the example is strategically sound and example-scoped, but authority activates only after the FR fixes its stale async-run citation, resolves the manual Discord acceptance identity, freezes the dependency pin, and names the exact requirement traceability target.

**Reviewed against:** `feature-requests/FR-812-discord-hello-slash-command-example.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `docs/plan-discord-yamlgraph-poc.md`; `docs/plan-chat-initiated-outbound-calls.md`; `examples/demos/hello/graph.yaml`; `examples/demos/hello/prompts/greet.yaml`; `yamlgraph/executor_async.py`; `yamlgraph/observability/async_run.py`; `feature-requests/070-gui-web-playground.md`; `examples/README.md`; `README.md`; repo doctrine supplied in the execution context.

## What is sound

The proposal has a named first consumer and first event: an internal test-guild member invokes `/hello name:Maija style:playful` and receives the existing hello graph's structured greeting as a Discord embed (`feature-requests/FR-812-discord-hello-slash-command-example.md:8-12`). That satisfies the doctrine's "first consumer" pressure and keeps the change anchored to one observable event.

The strategic classification is **contrib/example**, not a framework primitive. The FR confines implementation to `examples/discord_bot/`, tests, and README linkage (`feature-requests/FR-812-discord-hello-slash-command-example.md:53-55`, `feature-requests/FR-812-discord-hello-slash-command-example.md:61-67`) and explicitly bans `yamlgraph/` core changes and new core/dev dependencies (`feature-requests/FR-812-discord-hello-slash-command-example.md:100-101`). That matches the existing examples catalog pattern, where examples are documented runnable artifacts with clear demonstrated features (`examples/README.md:5-12`).

The architecture is aligned with the three-layer pattern: Discord remains presentation, the hello graph remains YAML logic, and no new side effect is introduced beyond the LLM call already made by the graph (`docs/plan-discord-yamlgraph-poc.md:42-48`). The cited hello graph already accepts `name` and `style` state and writes the result to `greeting` (`examples/demos/hello/graph.yaml:14-27`), and the prompt schema provides the exact fields the FR plans to render (`examples/demos/hello/prompts/greet.yaml:1-12`).

The feasibility claim is mostly supported. `load_and_compile_async` exists and returns a compiled graph ready for async invocation (`yamlgraph/executor_async.py:219-259`), and `run_graph_async` invokes `app.ainvoke` for one compiled-graph call (`yamlgraph/observability/async_run.py:20-63`) while being re-exported from `yamlgraph.executor_async` (`yamlgraph/executor_async.py:351-360`). The Discord-specific 3-second defer requirement is captured as a hard constraint in the cited plan (`docs/plan-discord-yamlgraph-poc.md:63-77`).

The prior-art disposition is credible. FR-070 rejected a reusable visual web playground because "No UI, ever; text is the interface" (`feature-requests/070-gui-web-playground.md:10-20`), while FR-812 proposes a text-command execution adapter for an existing graph, not a visual authoring or exploration surface (`feature-requests/FR-812-discord-hello-slash-command-example.md:14-20`).

## Required revisions

### R-1: Correct the async-run evidence citation

Replace the nonexistent cited file `yamlgraph/executor_async_run.py` in the FR's Related section with the actual committed surface: `yamlgraph/executor_async.py` for the public re-export and `yamlgraph/observability/async_run.py` for the implementation. The current citation names `yamlgraph/executor_async_run.py` (`feature-requests/FR-812-discord-hello-slash-command-example.md:121-122`), but the implementation file present in the repo is `yamlgraph/observability/async_run.py` (`yamlgraph/observability/async_run.py:20-63`) and `run_graph_async` is exported through `yamlgraph.executor_async` (`yamlgraph/executor_async.py:351-360`).

### R-2: Resolve the manual acceptance guild and bot identity

Fold the pending human question into the FR before enforcement: choose either an existing internal test guild/bot or a fresh private Discord application/guild, and state the selected acceptance environment in the FR. Manual acceptance is an acceptance criterion (`feature-requests/FR-812-discord-hello-slash-command-example.md:94-97`), but the FR still leaves the required guild/bot identity as an unresolved human question (`feature-requests/FR-812-discord-hello-slash-command-example.md:129-135`). Authority cannot activate while the required live witness environment is undefined.

### R-3: Freeze the `discord.py` install pin

Replace the placeholder `discord.py==2.x.y` with one exact version in the FR, and require the example README to use that same exact pin. The FR says the dependency is "pinned" (`feature-requests/FR-812-discord-hello-slash-command-example.md:78-79`) but the proposed usage block still contains a placeholder (`feature-requests/FR-812-discord-hello-slash-command-example.md:83-85`). The enforcer must not choose dependency policy ad hoc.

### R-4: Name the exact requirement traceability target

Replace "the appropriate `@pytest.mark.req` requirement ID" with the exact REQ-YG ID(s) the new tests must use, or explicitly authorize adding a new capability registry file with its new requirement ID. The current criterion is not mechanically checkable because it delegates the requirement choice to the enforcer (`feature-requests/FR-812-discord-hello-slash-command-example.md:102-104`) while repo doctrine requires every test function to carry a concrete `@pytest.mark.req("REQ-YG-XXX")` marker.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/discord_bot/README.md` documenting token/guild setup, exact `discord.py` install pin, usage, 3-second defer rationale, and pasted manual run log |
| D-2 | `examples/discord_bot/adapter.py` with pure option-to-state and result-to-embed/error rendering helpers |
| D-3 | `examples/discord_bot/bot.py` implementing the guild-scoped `/hello` command, startup graph compilation, `defer()`, bounded async graph run, and followup/error replies |
| D-4 | `tests/unit/test_discord_hello_adapter.py` covering the pure adapter slice with zero network and exact req markers |
| D-5 | README/example-catalog linkage required for discoverability |
| D-6 | Only if R-4 chooses a new requirement: the minimal capability registry artifact needed for requirement traceability |

Not authorized: changes under `yamlgraph/` core; modifications to `examples/demos/hello/graph.yaml` or its prompt files; generic `/run <graph>` execution; arbitrary graph authorization; streaming Discord updates; multi-turn threads; HTTP interactions endpoint; Discord global command rollout; production outbound-call behavior; Twilio/STT/TTS/call-hub work; new project dependencies outside the example README install line; graph authoring or prompt authoring.

## Revised acceptance criteria

- [ ] AC-01: `feature-requests/FR-812-discord-hello-slash-command-example.md` is revised to satisfy R-1 through R-4 before implementation authority activates.
- [ ] AC-02: `examples/discord_bot/adapter.py` unit tests pass with zero network for option-to-state mapping, embed rendering from a canned `greeting` dict, and error rendering with a correlation ID.
- [ ] AC-03: `examples/discord_bot/bot.py` compiles `examples/demos/hello/graph.yaml` once at startup with `load_and_compile_async`, defers each `/hello` interaction before running the graph, invokes `run_graph_async` independently per interaction, and sends the result through `followup.send()`.
- [ ] AC-04: Manual acceptance in the selected test guild is pasted into `examples/discord_bot/README.md` and records all three styles, two overlapping invocations without crossed replies, unset provider key producing the ephemeral error, and restart re-sync without duplicate commands.
- [ ] AC-05: `examples/demos/hello/` is byte-identical before and after enforcement.
- [ ] AC-06: No files under `yamlgraph/` are changed, and no dependency manifest gains `discord.py` or any Discord dependency.
- [ ] AC-07: The repo README and examples catalog link the new example; the example README documents token setup, guild scoping, exact dependency pin, usage, and the 3-second defer rationale.
- [ ] AC-08: Every new or changed test function has the exact `@pytest.mark.req("REQ-YG-XXX")` marker authorized by the revised FR, and requirement coverage tooling accepts it.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not begin implementation until R-1 through R-4 are folded into the FR. | GATE |
| C-2 | Do not run graph-authoring routes or modify the hello graph/prompt artifacts; this FR is an execution-adapter example only. | GATE |
| C-3 | Do not add `discord.py` or any Discord package to core, dev, or optional dependency manifests; the exact install pin belongs only in the example README. | GATE |
| C-4 | Do not substitute a fallback greeting on errors; errors must be visible and correlated as specified. | GATE |
| C-5 | Do not perform billable telephony, outbound-call, Twilio, STT, TTS, or call-hub work under this FR. | GATE |

Authority granted: after the required revisions are folded into the FR, enforcement may build only the minimal Discord `/hello` example adapter and its documentation/tests as frozen above.
