# Problem brief: the agent runtime seam is bound to two vendor CLIs that share no contract

**Prior art:** FR-383 (`feature-requests/FR-383-copilot-node-backend-api-fallback.md`)
introduced the `backend` selector on the copilot node; FR-959
(`feature-requests/FR-959-claude-cli-backend-primitive.md`) added the
`claude` backend and recorded, as unresolved dissent, that a node called
`copilot` running another vendor's CLI is a naming lie and that an
in-process SDK would be the better long-term boundary. FR-960
(`feature-requests/FR-960-claude-judge-variant.md`) proved the value of a
second harness for the judge by finding a safety hole the first judge
missed. FR-961 (`feature-requests/FR-961-claude-code-hooks-registration.md`)
proposes registering the shell hook layer for a second agent runtime.
FR-910 (`feature-requests/FR-910-retire-mcp-surface.md`) and FR-912
(`feature-requests/FR-912-retire-skill-export-surface.md`) retired
agent-facing surfaces that had no consumer. FR-362 and FR-364
(`docs/copilot-instrumentation-poc.md`) built process-mining
instrumentation over Copilot CLI stdout and OTel files. No prior FR
evaluates a third agent runtime or a vendor-neutral harness for the
governance adapters.

## Problem statement

Every governance adapter in this repo (author, judge, review, outsider)
executes through `type: copilot` nodes whose `backend` value names a
specific vendor CLI. Each backend is a separate subprocess contract:
the Copilot CLI backend recovers the session id by regex from a
`--share` markdown file and treats exit 0 with empty stdout as a
silent failure; the Claude Code backend pins one exact CLI version
banner, runs two auth probes per node call, and strips six payer
environment variables. The two backends accept different `cli_flags`
keys, and the linter carries a per-backend flag matrix. Adding the
second backend cost a 1.5-day FR, a judgement, an evidence file, and a
witness, and produced 578 lines of tests for 298 lines of runtime. The
shell hook enforcement layer under `.github/hooks/` is likewise keyed
on one vendor's tool vocabulary, so a second runtime needs a
registration port (FR-961) before any rule fires. Process-mining
instrumentation (`scripts/copilot_instrument.sh`,
`scripts/extract_copilot_events_lib.py`) parses one vendor's stdout
JSONL and OTel export. The repo therefore builds, per vendor, what it needs exactly once:
a headless run contract, a tool-call gate, a readable transcript, and a
session id that resumes. Each vendor CLI
changes these on its own schedule, and the pinned-version banner in the
Claude backend means every vendor release is a repo change.

## Classification

enforcement/latency-critical

## Constraints

- The adapters' output contract is unchanged: uncommitted files plus a
  draft artifact verified by shape, never by exit code
  (`.github/skills/graph-authoring/adapters/README.md`).
- A backend must expose a real session id that a second node resumes
  byte-for-byte (`examples/demos/session-continuation`, FR-959 AC-14), and must fail closed when the
  binary, the auth, or the version is not what the graph declared.
- Payer honesty (FR-959): the graph author must be able to say which
  subscription or key a node bills, and a missing login must not fall
  back to an API key silently.
- Enforcement infrastructure changes require human review before merge
  (FR-883 judgement R-4); a tool-call gate inside a third-party runtime
  is enforcement infrastructure and inherits that gate.
- The Windows host has no POSIX runtime and no WSL; Node 24 and the
  Copilot CLI are installed, Claude Code is installed but logged out.
  Anything that only runs under bash is owed by the mac, not verified
  here.
- Retirement follows the FR-466 CAP lifecycle: a surface is retired by
  an FR that names its zero consumers, and its spec survives in the FR
  record (`constraint_over_code`).
- `is_this_a_graph`: must be answered. The adapters already are graphs;
  the question is whether the runtime seam beneath them belongs in
  yamlgraph code, in a vendor-neutral harness's extension layer, or in
  neither.

## Witnessed incidents

- 2026-09-02, FR-959 evidence file
  (`feature-requests/evidence/FR-959-claude-auth-probe.md`): the Claude
  Code print-mode envelope reports `subtype: "success"` on a failed run;
  `is_error` is the only failure signal. The backend pins banner
  `2.1.255 (Claude Code)` and rejects every other version.
- 2026-09-04, `docs/diary/diary-2026-09-04-reflection-fr-960-two-brains-one-route.md`:
  two judges on different harnesses read the same FR; one found that the
  guard's allow path prints a deprecated approve key that would remove a
  permission prompt if honoured. The comparison was the deliverable; the
  second harness cost a working day.
- 2026-09-02, `feature-requests/research-briefs/fr961-claude-code-hooks-port-brief.md`:
  `.github/hooks/logs/audit.jsonl` did not exist on this host; no hook
  had fired for any agent here. Tool-name allowlists in
  `pre-command-guard.sh` cover one vendor's vocabulary only.
- 2026-08-29, `docs/research-agentic-sdlc-providers-2026-08-29.md` §4.4:
  the MCP surface served ~130 tools from editor cache for six weeks after
  its launcher was deleted, and nobody noticed; the CLI-in-adapter
  transport was the one agents consumed daily.
- `docs/node-type-census-2026-08.md`: `type: copilot` has 70 occurrences,
  11 of them in the governance pipeline, and a 0.043 incident-per-use
  ratio; `type: agent` was dispositioned RETIRE for having no committed
  consumer outside demos.
- 2026-09-05, this host: `copilot` 1.0.82 on PATH; `claude` and `pi`
  not on PATH; the `--share` regex seam in
  `yamlgraph/node_factory/copilot_runtime.py` is the only way the
  Copilot backend learns its own session id.
