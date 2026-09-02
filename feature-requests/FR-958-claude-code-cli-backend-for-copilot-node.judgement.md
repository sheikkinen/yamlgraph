<!-- Folded 2026-09-02 from tmp/draft-judgement.md rendered by the sole-route judge (scripts/judge.sh, Copilot CLI, gpt-5.6-sol, session 6dade613-37d2-47ff-a1f3-c8f983a791b7, log tmp/judge-fr958.log). The wrapper verified the artifact at 18:57:49 local; a sibling session started its own judge at 18:57:52 and its startup rm -f deleted it. Body below recovered verbatim from the Copilot session file-write event (tmp/draft-judgement-fr958.md). Children: FR-959 (backend primitive), FR-960 (judge variant). -->

# Judgement: FR-958 `backend: claude` — Claude Code CLI as a copilot-node agent backend, with a Claude judge variant

**Verdict:** SPLIT — the reusable Claude CLI backend and the Claude judge variant are independently valuable, independently testable concerns with different risk boundaries; each must re-enter judgement as its own FR, and no implementation authority is granted by this draft.

**Reviewed against:** committed FR blob `b62920bc449e24987a098d29dfdb290755bfce0a:feature-requests/FR-958-claude-code-cli-backend-for-copilot-node.md` (branch `docs/fr-958-claude-backend-fr`); `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/adapters/graph.yaml`; `.github/skills/judge-fr/adapters/README.md`; `.github/skills/graph-authoring/SKILL.md`; `.github/skills/graph-authoring/adapters/README.md`; `scripts/judge.sh`; `feature-requests/054-copilot-cli-reflection.md`; `feature-requests/FR-081-copilot-node.md`; `feature-requests/FR-329-agent-sdk-planner-spike.md`; `feature-requests/FR-383-copilot-node-backend-api-fallback.md`; `docs/diary-2026-02-20.md`; `docs/diary/diary-2026-08-08-the-ancestor-in-the-deployed-folder.md`; `docs/plan-research-dependency-negative-space.md`; `reference/development-operations.md`; `reference/graph-yaml.md`; `yamlgraph/node_factory/copilot_runtime.py`; `yamlgraph/node_factory/copilot_node.py`; `yamlgraph/linter/patterns/copilot.py`; `yamlgraph/models/node_schema.py`; `yamlgraph/models/schemas.py`; `capabilities/CAP-30-copilot-node.yaml`; `ARCHITECTURE.md`; Claude Code documentation cited by the FR: `https://code.claude.com/docs/en/headless`, `https://code.claude.com/docs/en/cli-reference`, `https://code.claude.com/docs/en/env-vars`, and `https://code.claude.com/docs/en/settings-reference`.

## What is sound

The runtime proposal follows the established backend seam rather than inventing a second node type. FR-081 created `type: copilot`; FR-383 established backend-specific execution and linting; the current runtime already isolates `_execute_cli` and dispatches in `_execute_backend_once` (`yamlgraph/node_factory/copilot_node.py:129-191`). A Claude CLI implementation beside that boundary is architecturally feasible.

The FR names real consumers and a first event (`FR-958:8`), distinguishes the binding FR-054 rejection rather than ignoring it (`FR-958:11-16,70-94`), and defines list argv, JSON-envelope normalization, loud failures, tests, documentation, traceability, and a kill criterion. Its alternatives table contains genuine solution classes and answers `is_this_a_graph`; the choice to use a conditional edge inside the existing adapter graph conforms to existing YAMLGraph condition syntax.

The payer distinction is strategically meaningful. Subscription, Anthropic API, and GitHub Copilot are different operator spend decisions, and the FR correctly refuses a silent fallback between them (`FR-958:135-147,406,413-424`). The live witness requirement is appropriate because authentication and billing cannot be established by mocked subprocess tests.

Strategically, the runtime concern qualifies as a **framework primitive**: the FR identifies more than three existing agentic consumers, and neither `backend: api` nor the unimplemented `sampling` backend supplies Claude Code's tool-bearing subscription-authenticated agent contract. The judge concern is a **contrib/internal enforcement adoption** of that primitive, not part of the primitive itself.

## Required revisions

### R-1: Split the primitive from its enforcement adoption

Replace FR-958 with two independently judged FRs:

1. **Claude CLI backend FR:** runtime dispatch, result parsing, session flags, payer boundary, backend-aware lint, schemas, capability requirements, tests, and reference documentation only.
2. **Claude judge variant FR:** depends on the implemented backend and owns the adapter graph, `scripts/judge.sh` selection, narrowed judge permissions, dual-backend witness, disagreement record, and adapter documentation.

The present FR explicitly introduces both a generic backend and a "second brain" for the judge (`FR-958:17,24-30,224-283`), but its ADR requirements cover only backend runtime and lint (`FR-958:297-321`). The judge selector and comparison therefore have no requirement identity of their own. Dependency does not make these one responsibility: the backend can be accepted and tested without changing enforcement infrastructure, while the judge variant can be rejected or revised without invalidating the backend.

### R-2: Correct the Claude tool-permission contract

In both child FRs, distinguish **tool availability** from **permission auto-approval**. Claude's CLI reference says `--allowedTools` / `--allowed-tools` auto-approves tools and explicitly says to use `--tools` to restrict which tools are available. The current proposal maps `allowed_tools` only to `--allowedTools` (`FR-958:125-127,151-161`) while claiming the judge is granted "exactly four tools instead of all" (`FR-958:252,276`). That claim is false.

Freeze and test one explicit contract: either rename the field to reflect auto-approval only, or define a separate closed tool-availability field that emits `--tools`; the judge child FR must emit both a restriction and the necessary approvals and must assert the exact argv. Do not authorize `--dangerously-skip-permissions` for the judge variant.

### R-3: Prove payer isolation across Claude settings, not only the parent environment

The backend child FR must replace the environment-only proof with a boundary that accounts for Claude settings. Claude's environment-variable reference states that `env` values from settings files are applied by Claude after process launch and can replace inherited shell values; the CLI reference also exposes `--settings`, `--setting-sources`, and restricted mode. Removing four keys from `subprocess.run(env=...)` (`FR-958:135-147`) therefore does not prove that the child uses subscription authentication, and AC-14 proves only that one parent-shell key was removed (`FR-958:375-378`).

Before freezing argv, commit a redacted raw `claude auth status` record and a settings-precedence probe from the target CLI version. Fold the observed fields into a fail-closed preflight and define which user, project, local, managed, `apiKeyHelper`, and cloud-provider settings remain capable of changing the payer. The human operator must explicitly accept that residual boundary in the child FR because this is a spend decision. If subscription-only execution cannot be proved under the supported settings boundary, apply the existing kill criterion rather than weaken the billing claim.

### R-4: Remove the unevidenced usage-limit classifier from v1

Move `ClaudeUsageLimitError`, `resets_at`, its detection pattern, and AC-15 to the follow-on FR. The cited diary records only that an external `loop.sh` performed five-hour-limit detection; it does not contain the raw refusal or regex (`docs/diary/diary-2026-08-08-the-ancestor-in-the-deployed-folder.md:8-15`). AC-15 permits enforcement to copy an uncommitted external regex if no real refusal exists (`FR-958:379-388`), which does not satisfy the raw-record-first boundary. V1 should surface every nonzero or `is_error` result as a generic typed backend execution failure until a committed real refusal supports a narrower classifier.

### R-5: Close backend dispatch before adding a fourth value

The backend child FR must reject unknown and non-string backend values at schema/lint/runtime boundaries. Today `NodeConfig.backend` is an unrestricted `str`, non-string values normalize to `cli`, and every unknown string falls through to `_execute_cli` (`yamlgraph/models/node_schema.py:107-109`; `yamlgraph/node_factory/copilot_node.py:183-191,227-228`). Adding only `if backend == "claude"` would preserve a success-shaped typo path such as `backend: cluade`. Add direct tests proving the accepted set and proving all other values fail before any subprocess starts.

### R-6: Replace unsupported exit-code semantics with observed contracts

The backend child FR must state only the vendor-documented contract, exit 0 versus nonzero, unless committed raw probes establish stable meanings for particular codes. The cited headless documentation says success is 0, failures are nonzero, invalid flags report to stderr, and in-run failures such as missing authentication are returned on stdout. It does not support the FR's fixed "1 failure / 2 partial" taxonomy (`FR-958:169-179`). Keep deterministic parsing and diagnostic-head tests, but do not assign semantic meaning to exit 2 without evidence from the pinned CLI version.

### R-7: Make route evidence persistent and research substantive

In the judge child FR, change AC-09 so `tmp/draft-authoring-report.md` remains the local, advisory route proof; it is not itself committed. The graph-authoring skill calls that report uncommitted (`.github/skills/graph-authoring/SKILL.md:35`), while FR-958 says it is committed as evidence (`FR-958:353-356`). Commit a separate witness record containing the authoring command, report digest or quoted required sections, lint command/result, smoke command/result, graph commit SHA, and limitations.

Each child FR must carry its own research record or substantive in-body equivalent. Preserve actual disagreement about the abstraction and risk boundary, not only the selected author's dispositions, and keep 4-6 material solution classes. The current table is useful precedent work, but the doctrine also requires disagreement to be preserved (`.github/skills/judge-fr/doctrine.md:118-128`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Child FR for the reusable `backend: claude` runtime primitive, incorporating R-2 through R-6 |
| D-2 | Dependent child FR for the opt-in Claude judge variant, incorporating R-2, R-3, and R-7 |
| D-3 | Independent judgement artifact for each child FR before enforcement |

No production Python, graph, prompt, script, capability, requirement, test, documentation, changelog, diary, or evidence implementation is authorized by this SPLIT verdict. In particular, this draft does not authorize edits to `.github/skills/judge-fr/adapters/graph.yaml`, `scripts/judge.sh`, the copilot runtime, or the linter. It does not authorize `backend: sampling`, usage-limit waiting/rerouting, streaming, remote delegation, review/author adapter migration, a default-backend change, or any silent payer fallback.

## Revised acceptance criteria

- [ ] AC-01: Two child FRs exist with non-overlapping implementation surfaces: backend primitive and judge adoption; the judge FR explicitly depends on the backend FR.
- [ ] AC-02: The backend FR has committed research evidence satisfying precedent, 4-6 material solution classes, preserved disagreement, and an explicit `is_this_a_graph` answer.
- [ ] AC-03: The backend FR freezes list argv and tests exact order for prompt, output format, model, session continuation, tool availability, tool approval, path access, and turn limit.
- [ ] AC-04: Tests prove `--allowedTools` is not represented as restricting tool availability; any restriction contract emits and asserts `--tools`.
- [ ] AC-05: Tests prove every unsupported or non-string backend value fails before `subprocess.run`, while `cli`, `api`, `sampling`, and `claude` retain their explicitly specified behavior.
- [ ] AC-06: A committed, redacted target-version probe records `claude auth status` shape and settings precedence; the FR derives a fail-closed subscription-auth preflight from that evidence.
- [ ] AC-07: Mocked environment/settings tests and a live witness jointly prove the supported payer-isolation boundary; residual managed/operator settings are enumerated and human-approved.
- [ ] AC-08: Exit handling relies on 0 versus nonzero plus envelope contents; no numeric failure subtype is asserted without a committed target-version raw record.
- [ ] AC-09: V1 contains no usage-limit text classifier, reset-time parser, or `ClaudeUsageLimitError`; those remain in a separately researched follow-on.
- [ ] AC-10: Claude JSON success, `is_error`, malformed stdout, missing binary, timeout, nonzero stdout/stderr diagnostics, and non-update of state on failure have direct requirement-tagged tests.
- [ ] AC-11: Existing Copilot CLI and API behavior is covered by unchanged regression expectations, and the backend child FR updates CAP-30, architecture requirements, docs, and changelog.
- [ ] AC-12: The judge FR defines a requirement for backend selection and dual-judge comparison rather than hiding those behaviors under runtime requirements.
- [ ] AC-13: The judge graph is authored only through `scripts/author.sh`; a persistent witness record cites the local report, graph SHA, lint, smoke, and limitations without claiming `tmp/draft-authoring-report.md` is committed.
- [ ] AC-14: Exact judge argv restricts available tools to the reviewed set and separately auto-approves that set; no Bash, MCP, broad bypass, or unreviewed tool is available.
- [ ] AC-15: A human reviews the enforcement-infrastructure graph/script diff and the payer boundary before the judge child FR receives implementation authority.
- [ ] AC-16: Live witnesses run both backends against the same committed FR and record backend, CLI version, auth mode, settings boundary, timestamps, artifact hashes, verdict headers, and a complete disagreement table.
- [ ] AC-17: Failure of the subscription-auth witness activates the kill criterion; no API key, cloud provider, Copilot backend, or other payer rescues the Claude witness.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not enforce this combined FR; each child FR must be committed, researched, and judged independently. | GATE |
| C-2 | The backend primitive must land before the judge variant can execute a Claude live witness. | GATE |
| C-3 | Tool restriction must use the vendor's availability control, not `--allowedTools` alone. | GATE |
| C-4 | Subscription-only billing must be proven across the declared settings boundary and approved by the human spend owner. | GATE |
| C-5 | No usage-limit classifier may ship without a committed real raw refusal and independently judged scope. | GATE |
| C-6 | Unknown backend values must fail closed before subprocess execution. | GATE |
| C-7 | The graph-authoring route and artifact proof are mandatory for the judge graph; the ignored local report must not be represented as committed evidence. | GATE |
| C-8 | The judge adapter and launcher are enforcement infrastructure; their diff and live witness require explicit human review before authority. | GATE |

Authority granted: none; this draft authorizes only the preparation and independent judgement of the two child FRs described in D-1 and D-2.
