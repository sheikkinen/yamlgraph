<!-- Folded 2026-09-02 from tmp/draft-judgement.md rendered by the sole-route judge (scripts/judge.sh, Copilot CLI, gpt-5.6-sol, session 2e931a2b-851f-4ae8-aa34-55d5dcdb0fba, run 01a06322-9d8e-715f-b168-89a303d4e946, log tmp/judge-fr959.log). Wrapper verified the artifact 2026-09-02 17:24Z; copied to tmp/draft-judgement-fr959.md in the same command to survive the fixed-name clobber (FR-960 §Problem 2). Body below verbatim. Judged in a session other than the author's. -->

# Judgement: FR-959 `backend: claude` — Claude Code CLI as a copilot-node backend (primitive)

**Verdict:** APPROVED WITH REVISIONS — the backend is a sound framework primitive, but authority activates only after the CLI contract is evidenced and frozen, payer claims are made truthful, per-invocation checks replace the unsafe cache, Claude-only flags are typed, and the live witness surface is made explicit.

**Reviewed against:** `feature-requests/FR-959-claude-cli-backend-primitive.md`; `feature-requests/FR-958-claude-code-cli-backend-for-copilot-node.md`; `feature-requests/FR-958-claude-code-cli-backend-for-copilot-node.judgement.md`; `feature-requests/FR-081-copilot-node.md`; `feature-requests/FR-383-copilot-node-backend-api-fallback.md`; `feature-requests/054-copilot-cli-reflection.md`; `feature-requests/FR-329-agent-sdk-planner-spike.md`; `feature-requests/FR-948-lan-copilot-delegation.md`; `feature-requests/105-copilot-session-continuations.md`; `feature-requests/FR-363-per-node-otel-scoping-in-copilot-node.md`; `feature-requests/FR-960-claude-judge-variant.md`; `feature-requests/TEMPLATE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `ARCHITECTURE.md`; `reference/development-operations.md`; `reference/graph-yaml.md`; `docs/plan-research-dependency-negative-space.md`; `.chaplain/graphs/watcher-plan/step-judge-v2.yaml`; `examples/demos/session-continuation/graph.yaml`; `yamlgraph/constants.py`; `yamlgraph/node_factory/copilot_runtime.py`; `yamlgraph/node_factory/copilot_node.py`; `yamlgraph/linter/patterns/copilot.py`; `yamlgraph/models/node_schema.py`; `yamlgraph/models/schemas.py`; `capabilities/CAP-30-copilot-node.yaml`; Claude Code documentation cited by the FR: `https://code.claude.com/docs/en/headless`, `https://code.claude.com/docs/en/cli-reference`, `https://code.claude.com/docs/en/settings`, and `https://code.claude.com/docs/en/env-vars`.

## What is sound

The proposal uses the established backend seam instead of creating a competing node type. FR-383 already separates API and CLI execution, stamps `CopilotResult.backend`, and owns backend-aware lint; the current implementation isolates `_execute_cli` and dispatches in `_execute_backend_once` (`yamlgraph/node_factory/copilot_node.py:129-191`). Adding `_execute_claude` beside that boundary is feasible and architecture-aligned.

The FR correctly folds the parent SPLIT's central corrections: availability and approval are separate controls (`FR-959:101-116`), unknown backends fail closed (`FR-959:64-74`), numeric exit subtypes and the unevidenced usage-limit classifier are excluded (`FR-959:183-199`), and the judge adoption remains in FR-960 (`FR-959:11,341-347`). The result contract rejects malformed or error-shaped output instead of creating a success-shaped fallback (`FR-959:183-196`), consistent with Commandment 6.

The in-body research is substantive. It presents six material solution classes, preserves disagreement, dispositions binding FR-054 and the Agent SDK alternative, and answers `is_this_a_graph` (`FR-959:306-318`). The live subscription and session-resume witness is necessary because mocked subprocess tests cannot establish vendor authentication or a real session ID (`FR-959:293-303`).

Strategically this is a **framework primitive**. The existing `copilot` backend abstraction is the correct extension seam, but none of its implementations supplies a Claude Code tool-bearing, subscription-authenticated agent. The parent identifies twelve agentic graph consumers, while FR-959 names the session-continuation graph and FR-960 as immediate consumers (`FR-959:8,37-50`).

## Required revisions

### R-1: Commit the vendor probes before freezing argv or granting authority

Create and link `feature-requests/evidence/FR-959-claude-auth-probe.md` before this FR receives authority. The record must identify the exact `claude --version` and contain redacted raw command, stdout, stderr, and exit status for: subscription login; logged out; an inherited `ANTHROPIC_API_KEY`; settings-file credential/environment precedence; `claude auth status`; and the target version's tool-availability grammar.

Replace the unresolved branch at `FR-959:120-130` with the one observed contract. The current text simultaneously freezes `--tools`, comma joining, and `tools: [] -> ""` (`FR-959:78-99,252-260`) while permitting a later switch to `--disallowedTools` (`FR-959:124-130`). AC-06 does not currently require the promised `--help` or tool-behavior capture (`FR-959:270-276`). The revised FR must name one argv form, define empty-list behavior from a real probe, and remove the alternative form. If no witnessed availability form can express the contract, activate the kill criterion.

### R-2: Make the payer boundary and human spend decision truthful

Remove the once-per-process auth cache. Run the fail-closed auth-status check immediately before every `claude -p` invocation with the same child environment and effective settings boundary. A cached success can outlive logout, settings edits, an `apiKeyHelper` change, or a provider-routing change, contradicting the claim that the backend refuses whenever it cannot prove subscription auth (`FR-959:53-60,162-177,281-285`).

Derive the stripped credential/routing set from the pinned evidence rather than freezing only four names (`FR-959:159-160`). The cited environment reference includes additional credential and routing surfaces, and settings `env` values override inherited values. Tests must prove every supported-version payer-switch variable identified by the evidence is absent from both preflight and execution environments.

Fold one explicit human decision into the FR:

1. **Option A — recommended for this minimal FR:** accept the enumerated settings race/residual, record `Residual payer boundary accepted by <name>, <date>`, and narrow Summary, Value Statement, Ideal Result, requirements, and docs from “can only ever bill” to “strips observed ambient payer switches and verifies subscription auth immediately before each invocation; enumerated settings changes can still reroute.”
2. **Option B:** preserve the absolute subscription-only claim by adding a separately proved controlled-settings boundary; if that requires settings mutation or managed-policy work, split it into its own FR and block FR-959 on it.

Do not treat the default repository owner named in prose as consent (`FR-959:169-176,278-280`). A spend owner must choose and sign one option.

### R-3: Enforce the supported Claude CLI version

Add a fail-closed supported-version check before execution and derive the accepted exact version or closed version range from R-1. Recording a version only in the witness (`FR-959:293-294,352-356`) does not pin runtime behavior.

This is a hard compatibility boundary: the cited headless documentation says `--bare` is recommended for scripted calls and will become the default for `-p`; bare mode skips `CLAUDE.md` and subscription OAuth. Those are both defining properties of this FR (`FR-959:31-35,53-60,130-136`). An unrecognized version must fail before the agent prompt, with the observed and accepted versions in the error. The version check and auth check may share a helper but must execute for every backend invocation.

### R-4: Validate Claude-only flag shapes before subprocess execution

Define and test compile-time validation for the new flag values. `NodeConfig.cli_flags` is currently `dict[str, Any]` (`yamlgraph/models/node_schema.py:110-112`), while the proposed implementation assumes iterable strings and truthy positive integers (`FR-959:88-98`). Require:

- `tools` and `allowed_tools`: `list[str]`, including an explicitly evidenced meaning for `[]`;
- `max_turns`: positive integer, rejecting booleans and zero;
- `allow_all_tools`, `allow_all_paths`, and `continue_session`: booleans;
- `resume` and `model`: strings when present.

Invalid shapes must fail at schema/compile and lint before any auth, version, or agent subprocess. Add mechanically named lint errors or schema diagnostics and direct tests for strings passed where lists are expected, non-string list members, `max_turns` zero/negative/bool/string, and non-boolean switches. Do not allow Python truthiness to silently omit malformed values.

### R-5: Type and validate the Claude JSON envelope

Add a private Pydantic model for the Claude JSON envelope and require a JSON object with `result: str`, `session_id: str`, and `is_error: bool` when present before constructing `CopilotResult`. “Parses as one JSON object” is not enough if field types remain unchecked (`FR-959:183-196`); repo doctrine requires external LLM output to cross a typed boundary.

Tests must cover a JSON array, missing `result`, non-string `result`, missing or non-string `session_id`, and non-boolean `is_error`, with each case failing before state update. Keep `CopilotResult`'s public field set unchanged.

### R-6: Replace the ambiguous demo witness with an exact disposable integration witness

Do not modify or directly run the committed `examples/demos/session-continuation/graph.yaml` under this FR. That graph has no backend variable, invokes broad write-capable enforcement/demo prompts, and defaults to unrestricted Copilot flags (`examples/demos/session-continuation/graph.yaml:20-50`). Changing it would add a graph-authoring deliverable absent from this primitive's scope; running it would permit unrelated repository edits.

Rewrite AC-12 and AC-13 to name an integration test or witness harness that creates a disposable temporary graph/config with two minimal copilot nodes, no file-writing task, and the second node's `resume` bound to the first result's real `session_id`. The witness record must include the exact command, temporary graph/config digest, CLI version, auth result, timestamps, both redacted argv lists, first session ID, second resume ID, result heads, and limitations. It must run in a disposable worktree or temporary directory and leave the committed session-continuation demo unchanged.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Closed backend input and typed Claude flag validation in `yamlgraph/models/node_schema.py` and the copilot node compile boundary |
| D-2 | Claude CLI execution, version/auth preflight, environment boundary, typed envelope parsing, and explicit dispatch in `yamlgraph/node_factory/` |
| D-3 | Backend and flag lint rules in `yamlgraph/linter/patterns/copilot.py` |
| D-4 | Requirement-tagged unit and disposable live-integration tests under `tests/` |
| D-5 | Redacted probe and live witness records under `feature-requests/evidence/` |
| D-6 | CAP-30, generated architecture requirements, `reference/graph-yaml.md`, `reference/getting-started.md`, and one FR-959 changelog fragment |

Not authorized: any edit to `.github/skills/judge-fr/**`, `scripts/judge.sh`, FR-960 surfaces, prompts or committed graph YAML, `examples/demos/session-continuation/**`, `backend: sampling`, a usage-limit classifier or wait/reroute policy, streaming, remote delegation, settings-file mutation, managed-policy installation, new dependencies, a `CopilotResult` field addition, renaming `type: copilot`, or changing default/Copilot/API backend behavior.

## Revised acceptance criteria

- [ ] AC-01: R-1's committed redacted probe names the supported CLI version and contains all auth, settings-precedence, environment-key, tool-grammar, and empty-tool-list observations; the FR freezes one observed argv contract with no conditional fallback.
- [ ] AC-02: `backend: cluade`, `backend: 3`, and `backend: ""` fail schema/compile and lint with the four accepted values before any subprocess; `None` alone defaults to `cli`.
- [ ] AC-03: Exact argv tests cover prompt/output format, model, resolved resume, continue, evidenced tool availability, tool approval, broad approval, cwd access, and positive max turns in the frozen order.
- [ ] AC-04: Tool availability and auto-approval remain distinct; `--allowedTools` is never represented as restricting availability, and conflicting broad/narrow approval emits the specified warning.
- [ ] AC-05: Every invalid Claude-only flag shape listed in R-4 fails before version, auth, or agent subprocess execution and has a direct schema/lint test.
- [ ] AC-06: Every Claude invocation performs the supported-version check and fail-closed subscription auth-status check immediately before `claude -p`; two node executions produce two version checks, two auth checks, and two agent calls.
- [ ] AC-07: The preflight and agent receive the same sanitized environment; every observed payer-switch variable is absent, `PATH` remains, and FR-363 OTel scoping remains present when configured.
- [ ] AC-08: The FR records the named spend owner's dated Option A or Option B decision from R-2; all billing claims and residual documentation match that decision.
- [ ] AC-09: A supported version with subscription auth proceeds; logged-out, API/console, cloud-provider, malformed-auth JSON, nonzero auth, missing binary, and unsupported-version cases fail before `-p`.
- [ ] AC-10: A typed Claude envelope maps valid `result` and `session_id` into `CopilotResult(backend="claude")`; every malformed shape in R-5, `is_error: true`, nonzero exit, timeout, and non-JSON stdout raises without state update.
- [ ] AC-11: Exit 1 and exit 7 remain generic nonzero failures; no numeric subtype, usage-limit exception, reset-time parser, or refusal regex exists in the package.
- [ ] AC-12: Every linter condition in the revised table has one direct test, including unknown backend, backend-incompatible flags, provider-on-Claude, approval/availability warnings, model warning, and invalid flag shapes.
- [ ] AC-13: Existing Copilot CLI/API/sampling and copilot-linter tests retain their assertions; no default dispatch, argv, result, session, provider, OTel, or lint behavior changes.
- [ ] AC-14: The disposable two-node live integration witness proves a real first `session_id` is passed byte-for-byte as the second node's `--resume` value without modifying committed graph artifacts or permitting file-writing work.
- [ ] AC-15: The live witness succeeds with an invalid inherited API key removed, and a logged-out run fails during auth preflight before `-p`; command, version, auth mode, timestamps, redacted argv, IDs, output heads, and limitations are committed.
- [ ] AC-16: CAP-30 carries the final requirement IDs, `ARCHITECTURE.md` is regenerated, references document the exact supported-version and residual payer contract, the changelog fragment cites the backend requirement, and `python scripts/req_coverage.py --strict` passes.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 into FR-959 and commit the R-1 probe before production implementation begins. | GATE |
| C-2 | The named human spend owner must choose and sign R-2 Option A or Option B; the enforcer may not infer consent. | GATE |
| C-3 | Unknown backend values and malformed Claude flags must fail before every subprocess, including version and auth probes. | GATE |
| C-4 | Version and auth checks run for every Claude invocation; no once-per-process payer cache is authorized. | GATE |
| C-5 | The implementation must use only the one tool grammar witnessed on the enforced supported version and must fail closed on version drift. | GATE |
| C-6 | Claude JSON crosses the private typed envelope boundary before `CopilotResult` construction or state update. | GATE |
| C-7 | The live witness uses a disposable, non-file-writing two-node integration fixture; no committed graph or prompt artifact is changed under this FR. | GATE |
| C-8 | Failure of the subscription, tool-grammar, version, or real-resume witness activates the kill criterion; no API key, provider, Copilot backend, or weakened claim rescues that witness. | GATE |
| C-9 | FR-960 and all enforcement-infrastructure adoption remain blocked until FR-959 is implemented and independently human-reviewed. | GATE |

Authority granted: after R-1 through R-6 are folded and C-1 through C-9 are satisfied, implement only the reusable `backend: claude` primitive and the frozen D-1 through D-6 surfaces above.
