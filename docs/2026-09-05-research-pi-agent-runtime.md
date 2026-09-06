# pi as an agent runtime for YAMLGraph: how to use it, what it retires

**Date:** 2026-09-05
**Type:** Research (no FR authorized; no implementation proposed here)
**Subject:** [pi](https://pi.dev/), the minimal terminal coding-agent harness by
Mario Zechner / Earendil (`badlogic/pi-mono`, MIT, TypeScript, v0.85.1
released 2026-09-05), evaluated against the agent-runtime seam this repo
already pays for twice.
**Brief:** `feature-requests/research-briefs/pi-agent-runtime-brief.md`
(FR-890 sole route; run record in §9).
**Relation to prior work:** FR-383 (backend selector), FR-959 (`backend: claude`),
FR-960 (second judge harness), FR-961 (hook port, Proposed),
FR-910/FR-912 (retired agent-facing surfaces),
`docs/research-agentic-sdlc-providers-2026-08-29.md` §4.4 (keep-or-retire
method), `docs/node-type-census-2026-08.md` (`copilot` KEEP, `agent` RETIRE).

---

## 0. Verdict in one paragraph

pi is a fit for exactly one recurring task class in this repo: the headless
agent execution beneath the four governance adapters (author, judge, review,
outsider). Today that seam is two vendor CLIs with two hand-built subprocess
contracts. pi offers one documented headless contract (`--mode json` /
`--mode rpc`), a first-line session id, a tool allowlist, a `tool_call`
gate, and one login surface for every provider the repo uses, including the
GitHub Copilot and Claude subscriptions. The recommended use is a third
`backend` value on the copilot node, first consumed by the judge adapter as
the third judge witness FR-960 asked for. pi is **not** recommended as an
in-process SDK, as a wrapper that exposes yamlgraph graphs to agents (that is
the MCP surface FR-910 retired), or, yet, as the operator's editor runtime.
Retirements follow from the witness, not from this document: `backend:
sampling` and the Copilot process-mining instrumentation can retire now on
their own zero-consumer evidence; the Claude and Copilot backends, the
session GC script, and half of the copilot linter matrix retire only after a
pi backend reproduces FR-959's session-resume witness and the FR-960 judge
comparison.

---

## 1. Method

Read: every file under `yamlgraph/node_factory/copilot_*.py`,
`yamlgraph/linter/patterns/copilot.py`, `yamlgraph/models/schemas.py`,
`.github/skills/*/adapters/graph.yaml`, `.github/hooks/`, the FR-959/960/961
records and diaries, the retirement FRs 910/912, the two census documents,
and the business brainstorm. Read from pi: the coding-agent README, the
RPC, JSON, SDK, extensions, skills and settings docs, and the changelog.

Probed on this host (Windows 11, no POSIX runtime): which binaries are on
PATH, consumer counts for each retirement candidate, last-touch dates.

**Not probed:** pi itself. It is not installed here, and installing it is a
download the operator has not approved. Every claim about pi below is a
documentation claim (`does_the_platform_already_do_this` says one source
grep beats a week of prediction; the grep is owed, §7).

---

## 2. What pi is, in the terms this repo cares about

The repo builds four things per agent vendor. The table maps each to pi's
documented surface.

| Need (from FR-959/960/961) | Copilot CLI backend today | Claude Code backend today | pi |
|---|---|---|---|
| Headless run | `copilot --silent -p`; exit 0 with empty stdout is a silent failure | `claude -p --output-format json`; `subtype: "success"` on failed runs, `is_error` is the only signal | `pi -p` (text), `pi --mode json` (LF-delimited events), `pi --mode rpc` (commands + events over stdin/stdout, `{"type":"response","success":…}` envelope) |
| Session id that resumes | regex over a `--share` markdown file | `session_id` in the envelope | first JSON line `{"type":"session","version":3,"id":…}`; resume with `--session <path\|id>`, `-c`, `--fork` |
| Tool availability vs approval | `--allow-all-tools`, `--allow-all-paths` (NC-414 trap: without them, writes are denied and exit is still 0) | `--tools` (availability) vs `--allowedTools` (approval) | `--tools`, `--exclude-tools`, `--no-builtin-tools`; **no approval layer exists** (no permission popups by design); project trust via `--approve`/`--no-approve`, `defaultProjectTrust` |
| Tool-call gate | shell PreToolUse hook in the operator's editor | shell hook, not yet registered (FR-961) | extension event `tool_call` can `block` with `reason`, `terminate`, or mutate `event.input`; runs in every mode (`ctx.mode` ∈ tui/rpc/json/print) |
| Readable transcript | OTel file + `stdout.jsonl` parsed by 404 lines of extractor | `~/.claude/projects/<slug>/*.jsonl`, thinking mostly redacted | session JSONL tree (`id`/`parentId`), `get_entries` with cursor, `get_tree`, `export_html`; JSON mode streams `tool_execution_start/end`, `message_end`, `usage` |
| Model and payer | `--model` (Copilot seat) | `--model` alias, banner pinned to one version, two auth probes per call | `--provider <name> --model <pattern>[:thinking]`; providers include Anthropic, OpenAI, **GitHub Copilot**, Google, DeepSeek, Mistral, OpenRouter, 15+ more; subscription logins for Claude Pro/Max, ChatGPT, Copilot via `/login`; `get_state` reports the resolved model; `get_session_stats` reports tokens and cost |
| Windows | Copilot CLI runs | Claude Code runs, logged out | npm install, native `powershell` tool since v0.84.3, Git Bash path handling fixed v0.82.0 |
| Skills | `.github/skills/*/SKILL.md` (Copilot discovers) | `.claude/skills` | Agent Skills standard; discovery `.pi/skills/`, `.agents/skills/`, plus any paths listed in `settings.skills[]`; the repo's SKILL.md files already carry the required `name`/`description` frontmatter |

What pi deliberately omits, with the repo's own position beside each:

| pi omits | Repo position | Consequence |
|---|---|---|
| MCP | retired by FR-910 | aligned |
| sub-agents | fan-out is a graph (`docs/2026-07-29-research-subagent-promotion.md` C1 → PROMOTE to graph) | aligned; the adapters are the fan-out |
| permission popups | adapters run non-interactively; the NC-414 `allow_all_tools` trap exists only because Copilot has popups | aligned for adapters; **not** aligned for the operator runtime, where FR-767's PreToolUse deny is load-bearing (see §4 option B) |
| plan mode, todos, background bash | not used by any adapter | neutral |

Release cadence matters: 0.80.8 (ModelRuntime, breaking SDK options) →
0.84.0 (JSON/RPC `message_update` now delta-only, session API v4, breaking)
→ 0.85.1, all inside roughly two months. Any backend must pin what it
parses to the header line, `message_end.message`, `tool_execution_end` and
the response envelope, and must pin a version range the way FR-959 pins a
banner.

---

## 3. The seam in yamlgraph today

| Surface | Size | Consumers (outside its own tests) | Last functional touch |
|---|---|---|---|
| `type: copilot` node, `backend ∈ {cli, api, sampling, claude}` | `copilot_node.py` 417 + `copilot_runtime.py` 229 + `copilot_runtime_claude.py` 298 | 4 adapters (author, judge×2 backends, review, outsider-view), `.chaplain/graphs/philosopher` (4 nodes), `.chaplain/graphs/watcher-plan`, `examples/ebook` (48 nodes across 12 graphs), `examples/bugfix` (4), `examples/demos/session-continuation` (2), `examples/demos/philosopher_book` (2), one spike | 2026-09-02 (FR-959) |
| `backend: sampling` | 3 lines, raises `NotImplementedError` | **zero** graphs | never implemented; its transport (MCP sampling) retired with FR-910 |
| copilot linter pattern (`E-COPILOT-BACKEND-UNKNOWN`, per-backend flag matrix, `gpt-*`/`-sol` model regex) | 279 | lint route | 2026-09-02 |
| Copilot/Claude tests | ≈ 3,300 lines across 13 files | CI | 2026-09-02 |
| `.github/hooks/` shell layer (guard 417, reasoning check 157, checks ≈ 500) | ≈ 1,100 | VS Code Copilot sessions only; Claude Code registration is FR-961 (Proposed); **no hook has ever fired on this host** | 2026-09-02 |
| Copilot process-mining instrumentation (CAP-145, CAP-191): `copilot_instrument.sh` 231, `extract_copilot_events_lib.py` 404, `docs/copilot-instrumentation-poc.md` | ≈ 680 + 2 RED test files | one recorded run, `minesweeper-001`, 2026-05-10; `outputs/copilot-instrumentation/` is empty | 2026-07-07 (worktree delegation refactor), then encoding-only |
| `copilot_session_gc.sh` (CAP-43, FR-138) | 92 | none; referenced by ARCHITECTURE.md and its CAP | 2026-03-08 |
| `type: agent` (in-process LangChain tool loop) | 418 | demos only; census disposition RETIRE | 2026-09-05 (FR-998 structured output) |

Two facts from the record shape everything below. First, the census gave
`copilot` KEEP because of eleven governance-pipeline consumers, and gave
`agent` RETIRE for having none; pi touches the former and not the latter,
because `type: agent` is an LLM tool loop *inside* a graph with typed
output, and pi is a coding agent *outside* it. Second, FR-959's own
dissent column recorded two things it declined to resolve: a node called
`copilot` that runs another vendor is a naming lie, and an in-process SDK
would be the better long-term boundary. pi resolves the first (one backend
for every vendor makes the name `agent_cli` honest) and refuses the second
(pi's SDK is Node, and the repo is Python).

---

## 4. How to utilize pi: four options, dispositioned

| # | Option | Disposition | Reasoning |
|---|---|---|---|
| A | **`backend: pi` on the copilot node.** Spawn `pi --mode json --no-session --provider P --model M --tools read,write,grep,find,ls -p <prompt>` (or `--session <id>` to resume); parse the header line for `session_id`, `message_end` for `output`, `tool_execution_end` for the tool ledger, exit code for `exit_code`. Fits the existing `_execute_backend_once` dispatch and the `CopilotResult` envelope unchanged. | **PURSUE**, first consumer the judge adapter | Same shape as FR-959 (1.5 days + judgement + evidence + witness) but cheaper in kind: the envelope is documented, the session id is line one, there is no `--share` regex, no version banner to pin per release (pin a `--version` range instead), and the Windows host can witness it, which no bash-wrapper test can. Every later vendor is a `--provider` value, not a backend. FR-960's seed named a third judge witness as the trigger for the comparison graph; this is that witness. |
| B | **pi as the operator runtime** (replacing VS Code Copilot / Claude Code sessions in the repo), with the `.github/hooks/` rules ported to one TypeScript extension: `tool_call` → the pre-command guard (trailer block, `--no-verify`, governed-write sentinel), `message_end`/`tool_result` → reasoning-pattern check, `session_start` → briefing, `pi.appendEntry` → audit trail. | **DEFER**; decide inside FR-961, not here | It dissolves FR-961's "one rule set, two registrations" problem by collapsing to one runtime, but it moves enforcement code from shell (pytest-testable, `.github/hooks/tests/`) into TypeScript (a new language surface in a Python repo), and it changes the operator's daily tool. FR-883 R-4 makes it a human-review gate regardless. The adapter question (A) is independent of this one and should not wait for it. One constraint FR-961 should absorb now: its tool-vocabulary normaliser must be written for N vendors, not two, because pi's eight tool names are a third vocabulary. |
| C | **pi SDK in-process** (`createAgentSession` from Python via a Node bridge). | **REJECT** | Same disposition FR-959 gave `claude-agent-sdk`: a second runtime and a second permission model inside core. Worse here: a Node process boundary in a Python framework. The subprocess seam is the boundary the repo already trusts. |
| D | **A `yamlgraph` pi package** (skills + prompts + an extension tool wrapping `yamlgraph graph run`). | **REJECT until a named consumer exists** | This is FR-910's MCP surface reborn under a different transport. FR-910's resurrection condition stands: a named external host actually wired to it. The zero-copy part is different and free: `.pi/settings.json` with `"skills": [".github/skills"]` makes the existing SKILL.md files discoverable to a pi session with no export step, which is what FR-912 retired an exporter for. |

**is_this_a_graph:** No, for A. A backend is a node primitive; the adapters
are already the graphs. Yes, for the thing A enables: the three-judge
comparison FR-960's diary described (`ID, section, claim, evidence,
disposition` is already a schema) is a map over judgements with an LLM-free
reduce, and it becomes affordable only when the third witness costs one
`--provider` flag.

---

## 5. What to retire

Each row is a separate FR under the FR-466 lifecycle. "Now" means the
evidence is complete without pi; "after witness" means after option A's
AC-14-class witness (a real session id resumed byte-for-byte by a second
node) exists on main; "after comparison" means after the judge adapter has
produced the FR-960-style inventory on pi.

| Candidate | Evidence | Disposition | Blocking witness |
|---|---|---|---|
| `backend: sampling` | zero graphs; `NotImplementedError`; transport retired by FR-910 | **RETIRE now** | none; shrink `COPILOT_BACKENDS`, the schema `Literal`, the linter enum and their tests in one FR |
| Copilot process-mining instrumentation (CAP-145, CAP-191, FR-362/364) | one run in May; output dir empty; pi's JSON mode *is* a normalised event stream (`tool_execution_start/end`, `message_end`, `usage`), so the extractor's job disappears | **RETIRE now** | none; the process-mining *question* survives in FR-362; if it is asked again the answer is a python node over `--mode json` output |
| `copilot_session_gc.sh` (CAP-43) | zero consumers since 2026-03; adapters on pi run `--no-session`, leaving nothing to prune | **RETIRE with the Copilot backend** | the Copilot backend's own retirement below |
| `backend: claude` (FR-959, 298 + 578 lines, banner pin `2.1.255`) | every Claude Code release is a repo change; FR-960 could not pin the resolved model (`alias_is_not_a_pin`), which pi's `get_state` reports; the payer claim moves from two probes per call to pi's provider login state | **RETIRE after witness**, only if the pi witness also carries the payer claim (P5 in §7) | A's witness plus a probe that an unauthenticated provider fails closed |
| `backend: cli` (Copilot CLI) | the `--share` regex is the weakest contract in the seam; **but** the judge, review and outsider adapters are pinned to `gpt-5.6-sol`, a Copilot-CLI-only model variant, and whether pi's Copilot login lists it is unknown (P3) | **RETIRE after comparison**, conditional on P3 | the FR-960 inventory reproduced on pi with a Copilot-billed GPT model |
| copilot linter matrix (`CLAUDE_ONLY_CLI_FLAGS`, `_COPILOT_ONLY_MODEL`, `E-COPILOT-*`) | exists only because backends disagree on flags | **SHRINK** with each backend retired; the closed-backend check itself stays | follows the rows above |
| `.github/hooks/` shell layer | load-bearing for FR-767 on the operator runtime | **KEEP**; FR-961 decides the registration target | not a pi question until option B is chosen |
| `type: agent` | census RETIRE, demos only | **unchanged by pi**; listed to prevent conflation | its own FR |
| `examples/ebook` (48 copilot nodes, last touched 2026-02-26) and `.chaplain` graphs | example and governance consumers of `backend: cli` | **MIGRATE or RETIRE** as part of the Copilot-backend FR; ebook has had no functional commit in six months and is a candidate for the FR-466 queue on its own evidence | the Copilot backend's retirement |

Net effect if every conditional row lands: one backend (`pi`) plus `api`,
about 1,600 lines of vendor-specific runtime, scripts and tests gone,
and the FR-959 naming dissent resolved by renaming `type: copilot` to
`type: agent_cli` in the same FR that removes the last vendor name from the
enum.

---

## 6. What pi does not give, and the risks

- **No approval layer.** pi runs any allowed tool without asking. For
  adapters this removes the NC-414 trap; the gate is `--tools` plus, if
  needed, a `tool_call` extension. For the FR-767 governed-write guard the
  mechanism is unchanged: it lives in the operator's session, not in the
  adapter subprocess.
- **Payer preflight.** FR-959 spends two subprocesses per call to prove the
  subscription is the payer. pi centralises auth per provider and has an
  `auth.json`, but the documentation read here does not say what `-p` does
  when the chosen provider has no credential. Until P5 is captured, the
  Claude backend keeps its preflight and stays.
- **`gpt-5.6-sol` reachability.** The judge, review and outsider adapters
  bill a Copilot seat for a model variant the Copilot CLI exposes. If pi's
  Copilot provider does not list it, the Copilot backend stays for those
  three adapters and pi serves the Anthropic-billed judge only.
- **Churn.** Two breaking releases in two months. Parse only the stable
  fields, pin a version range, and keep the FR-959 discipline: widening the
  range requires a new capture.
- **TypeScript.** Option A needs zero extension code. Options B and D need
  TypeScript in a Python repo; that cost is why B is deferred and D rejected.
- **Headless `block`.** `tool_call` handlers run in print/json mode
  (`ctx.hasUI === false`), but a block's `reason` reaches the model, not a
  UI. Whether a blocked write in `-p` mode produces a non-zero exit or a
  quiet success is the same exit-0 question FR-959 and NC-414 both hit;
  the adapters already verify by artifact, never by exit code, so the
  contract holds either way. P6 captures it.

---

## 7. Owed probes (before any FR asks for authority)

Each probe writes a redacted raw capture to
`feature-requests/evidence/FR-XXX-pi-probe.md`, FR-959 style. Expected
answers are written first so a miss is visible.

| # | Probe | Expected | If it misses |
|---|---|---|---|
| P1 | `npm install -g @earendil-works/pi-coding-agent`; `pi --version` | 0.85.x on Windows, `powershell` tool present | pi is not Windows-viable; A is owed by the mac like every bash test |
| P2 | `pi --mode json --no-session --tools read -p "read README.md and name its first heading"` | line 1 `{"type":"session",…,"id":…}`, a `tool_execution_end` for `read`, a `message_end` carrying the answer, exit 0 | the envelope contract differs from the docs; pin to what is observed |
| P3 | `/login` GitHub Copilot, then RPC `get_available_models` | the list includes the GPT variants the adapters pin (`gpt-5.6-sol`, `gpt-5.5`) | Copilot backend stays for judge/review/outsider; pi serves Anthropic-billed nodes only |
| P4 | Two `--mode json` runs, the second with `--session <id from the first>` | the second header repeats the id and the model sees the first turn | no resume; A fails its AC-14-class criterion |
| P5 | P2 with a provider that has no credential, `PI_OFFLINE=1` | non-zero exit and an error event, no fallback to another provider or key | payer honesty cannot be claimed; Claude backend stays |
| P6 | A three-line `.pi/extensions/deny-write.ts` blocking `write`, then P2 with `--tools read,write -p "write x.txt"` | `tool_execution_end` with `isError`, no file, the block `reason` in the transcript | headless gating is not real; adapters rely on `--tools` alone |

P1 and P3 need the operator (a download and two logins). P2, P4, P5, P6
can run in this session once P1 is done.

---

## 8. Recommended sequence

1. Operator: P1 and P3 (twenty minutes). Everything below is conditional on
   their answers.
2. This session or the next: P2, P4, P5, P6; commit the evidence file.
3. FR: `backend: pi` on the copilot node, first consumer the judge adapter
   as `JUDGE_BACKEND=pi`, acceptance criteria copied from FR-959 (typed
   flags, closed enum, lint, resume witness, payer claim, version range) plus
   the FR-960 inventory against the two existing judges. Research field:
   the promoted record from §9.
4. FRs, now, independent of pi: retire `backend: sampling`; retire the
   Copilot process-mining instrumentation (CAP-145, CAP-191).
5. FRs, after the witness: retire `backend: claude`; after the comparison
   and P3: retire `backend: cli`, `copilot_session_gc.sh` (CAP-43), migrate
   or retire `examples/ebook` and the `.chaplain` copilot graphs, shrink the
   linter, rename the node type.
6. FR-961: add pi as a third tool vocabulary to its normaliser design and
   decide the registration target there. Do not block A on it.

---

## 9. Research route record (FR-890 sole route)

**Run 1, 2026-09-05 20:36Z, code SHA ec7b607a:** discarded by the reducer.
Persona 2 wrote its rationale into the `solution_class` cell
(`'process-boundary. The four per-vendor concerns (…) belong in a single
abstraction boundary…'`), and `PersonaFinding._closed_class` failed the
whole run on one cell. The brief sentence it echoed was reworded and the
run repeated. Route defect worth its own FR: the reducer's own docstring
says findings are demoted, never dropped, but a contaminated enum cell
drops the run; FR-990 met the same class (`enum-leak demotion`) and fixed
it in code. Two strikes across two instruments is the `two_strike_split`
signal: split the cell at the first delimiter, validate the head, keep the
tail as rationale.

**Run 2, 2026-09-05 20:39Z, same SHA:** discarded again, one layer
earlier. The `yamlgraph_native_planner` node's structured output failed
`YamlgraphNativeFinding` validation after two attempts because its
`candidate` cell ran past the 400-character cap (`string_too_long`); the
other four personas completed, and `gather_findings` then failed the run
on the missing fifth finding. Two consecutive runs killed by schema shape
on one cell each, with the personas' content never reaching the reducer.
The brief was left unchanged for run 3 (`two_strike_split`: stop rewording
the input; the cap and the enum split belong in the route's code).

**Run 3, 2026-09-05 20:41Z, same SHA, brief unchanged:** identical failure
to run 2, byte-for-byte the same truncated `candidate` prefix
(`'Introduce a vendor-neutr… in copilot_runtime.py.'`). At temperature 0
the overshoot is deterministic for this brief, so a fourth run would be
ritual. Stopped after three.

**Consequence for this record.** No promoted five-persona table exists;
no `research-runs.jsonl` line was stamped (the wrapper stamps only on a
verified artifact). The dispositioned table in §4 is the FR-889-style
in-body equivalent the FR template accepts. The one persona output that
did surface, three times, is itself a finding: the yamlgraph-native
planner's candidate was a vendor-neutral backend abstraction at the
`copilot_runtime.py` seam, which is option A.

**Run 4, 2026-09-06 (FR-1005 GREEN `d53cae3f`):** the fixed gather died on
a loader defect the unit tests could not see: the graph's Python tool
loader execs the module without a `sys.modules` entry, so pydantic could
not resolve a deferred `Literal` on the new `FailedPersona` record. Fixed
in `4bc34a82` with a witness that loads the module as the runtime does.

**Run 5, 2026-09-05T21:19:01Z (code `4bc34a82`), verified and stamped:**
four rows; the fifth persona is accounted for in the header with its
recorded cause. Stamp: `research-runs.jsonl` line at 2026-09-05T21:19:01Z,
`brief_sha256 = 03ea8495…`, `artifact_sha256 = 4a3b0a79…`.
Same Windows CRLF verifier caveat as every record on this host: verify the
appendix below with `--verify-artifact`, not `--verify-promotion`. Two
things the record shows that the earlier failed runs hid: two personas
wrote a paragraph into their `persona` cell (the human-names header line
is model text; the canonical key line is what to trust, which is exactly
why FR-1005's judge demanded key-based identity), and the four surviving
findings converge on the vendor-neutral backend seam this document calls
option A, with the librarian citing OpenClaw's CLI-backend plugin contract
as external precedent.

**Route defects to file (one FR, `two_strike_split`):** (1) a persona's
enum cell carrying its rationale drops the run instead of being split at
the first delimiter and demoted; (2) a persona's over-length cell drops
the run instead of being truncated with a `row_failed` mark, although the
reducer's docstring promises demote-never-drop; (3) the route offers no
partial artifact, so four completed personas' findings are lost with the
fifth. All three are the FR-990 enum-leak class at a different instrument.

---

## 10. Sources

- pi site and docs: [pi.dev](https://pi.dev/),
  [coding-agent README](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md),
  [RPC mode](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/rpc.md),
  [JSON mode](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/json.md),
  [SDK](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/sdk.md),
  [extensions](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/extensions.md),
  [skills](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md),
  [settings](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/settings.md),
  [changelog](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/CHANGELOG.md),
  [npm package](https://www.npmjs.com/package/@mariozechner/pi-coding-agent).
- Secondary: [explainx.ai overview](https://www.explainx.ai/blog/pi-minimal-agent-harness-mario-zechner-guide-2026),
  [MakerOnSite 2026 guide](https://makeronsite.com/blog/2026/08/065-pi-coding-agent-2026-guide-en/),
  [Petronella review](https://petronellatech.com/blog/pi-dev-platform-review/),
  [DeepWiki](https://deepwiki.com/badlogic/pi-mono).
- Repo: files named inline; FR-959/960/961 records; `docs/node-type-census-2026-08.md`;
  `docs/research-agentic-sdlc-providers-2026-08-29.md` §4.4.

---

## 11. Promoted research record (run 5, byte-faithful, LF-normalised)

# Draft alternatives

- brief: pi-agent-runtime-brief.md
- run date: 2026-09-05T21:18:59Z
- personas executed: os-infra-primitivist, Data-process-planner analyzing vendor-specific backend coupling in governance adapters. The problem is architectural: each backend rediscovery (session id, auth, version, flags, instrumentation) is bespoke, creating 1.5-day FRs and 578-line test suites per vendor., Subtractionist: I reduce scope by retiring vendor-specific runtime seams and moving backend contracts into a vendor-neutral harness layer, eliminating per-CLI pinning, regex fragility, and dual instrumentation., librarian
- persona keys executed: ["os_infra_finding", "data_process_finding", "subtractionist_finding", "librarian_finding"]
- personas failed: {"yamlgraph_native_finding": "yamlgraph_native_planner: unknown_error (OutputParserException): Failed to parse YamlgraphNativeFinding from completion {\"persona\": \"yamlgraph-native-planner\", \"candidate\": \"Introduce a vendor-neutral backend abstraction layer as a YAMLGraph extension point. Each backend (Copilot CLI, Claude Code) registers its contract (session recovery, auth probes, flag matrix, stdout parsing) through a common interface. The graph author declares `backend: copilot` or `backend: claude-code` in the node; the runtime dispatches to the registered handler without embedding vendor logic in copilot_runtime.py.\", \"solution_class\": \"boundary-enforcement\", \"verdict\": \"pursue\", \"precedent\": \"FR-767-graph-authoring-sole-route.md, CAP-249 Invocation-time tool-slot binding, constraint_over_code\", \"is_this_a_graph\": \"none: the runtime seam is infrastructure, not a graph shape. The adapters themselves (author, judge, review, outsider) are already graphs; this candidate moves vendor dispatch logic into YAMLGraph's extension-point layer, not into a new graph.\", \"effort_risk\": \"medium/high: requires refactoring copilot_runtime.py into a registry pattern and moving per-backend logic (banner pinning, auth probes, flag matrices, stdout parsing) into separate handler modules. Existing 578 test lines must migrate to handler-scoped tests. Enforcement gate (FR-883 R-4) applies because tool-call gates inside third-party runtimes inherit that gate.\", \"rationale\": \"This isolates vendor-specific contracts from graph execution, making each backend testable independently and allowing new backends (e.g., pi, future providers) to register without modifying core runtime. It honors payer honesty (FR-959) by making the backend choice explicit in the graph, not implicit in environment state or fallback logic.\"}. Got: 1 validation error for YamlgraphNativeFinding candidate String should have at most 400 characters [type=string_too_long, input_value='Introduce a vendor-neutr... in copilot_runtime.py.', input_type=str] For further information visit https://errors.pydantic.dev/2.13/v/string_too_long For troubleshooting, visit: https://docs.langchain.com/oss/python/langchain/errors/OUTPUT_PARSING_FAILURE"}

### Prior art retrieved for this brief (filename-noun, IDF-ranked)
  FR-767-graph-authoring-sole-route.md  [Implemented]  matches: agent, runtime, brief
  FR-777-shared-shell-toolbelt-manifests.md  [Enforced]  matches: agent, runtime, brief
  FR-786-api-discovery-page-analysis-step.md  [Enforced]  matches: agent, runtime, brief
  FR-787-api-discovery-recon-step.md  [Enforced]  matches: agent, runtime, brief
  FR-788-api-discovery-platform-confirm-step.md  [Enforced]  matches: agent, runtime, brief

| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk | rationale |
|---|---|---|---|---|---|---|---|
| Vendor-neutral subprocess contract: define a stable interface (session-id recovery, exit semantics, stdout/stderr parsing, auth-probe count, env-var scrubbing) that each backend implements once, decoupling adapter logic from CLI-specific regex, banner-pinning, and flag matrices. | os-infra-primitivist | boundary-enforcement (convergent x2) | pursue | FR-959, CAP-03, constraint_over_code, name_the_seam | no | medium; requires one interface spec and per-backend adapter refactor, but eliminates 578-line test debt and vendor-release churn. | The platform already enforces process boundaries; codifying the subprocess contract once (not per-vendor) moves enforcement from linter matrices and regex seams into the OS process model itself. This eliminates the 1.5-day FR cost per new backend and the banner-pinning brittleness. |
| Unify backend contracts into a vendor-neutral adapter interface that each backend implements, moving session recovery, auth probes, version pinning, and instrumentation into a common harness layer. | Data-process-planner analyzing vendor-specific backend coupling in governance adapters. The problem is architectural: each backend rediscovery (session id, auth, version, flags, instrumentation) is bespoke, creating 1.5-day FRs and 578-line test suites per vendor. | process-boundary | pursue | FR-767-graph-authoring-sole-route.md, CAP-05 Tool & Agent Integration, constraint_over_code, name_the_seam | No. The runtime seam belongs in a vendor-neutral harness extension layer, not in yamlgraph code. Each backend becomes a pluggable implementation of a shared interface. | Medium effort, low risk. Refactoring existing backends into a common contract is mechanical; the output shape is unchanged. Risk is low because the adapters' uncommitted-file contract and session-resume requirement are already enforced. | The problem dissolves by dissolving the seam, not guarding it. A vendor-neutral harness eliminates per-backend linter matrices, hook registration ports, and instrumentation parsers. Each vendor CLI change then affects only its backend implementation, not the governance pipeline. |
| Delete the per-backend flag matrix, banner pinning, and vendor-specific stdout parsing. Move session-id recovery, auth probes, and transcript normalization into a single vendor-neutral adapter interface that each CLI backend implements once, not scattered across copilot_runtime.py, hooks, and instrumentation scripts. | Subtractionist: I reduce scope by retiring vendor-specific runtime seams and moving backend contracts into a vendor-neutral harness layer, eliminating per-CLI pinning, regex fragility, and dual instrumentation. | boundary-enforcement (convergent x2) | pursue | FR-767-graph-authoring-sole-route.md, CAP-05 Tool & Agent Integration, constraint_over_code, name_the_seam | Yes. The adapters are already graphs; the runtime seam belongs in a vendor-neutral harness extension layer, not duplicated in yamlgraph code per vendor. | Medium effort, low risk. Consolidates 578 test lines and 298 runtime lines into one contract; eliminates banner pinning and regex brittleness. Requires one FR naming zero consumers of old per-backend paths (FR-466 CAP lifecycle). | Each vendor release currently forces a repo change; dual instrumentation and per-backend linter matrices are maintenance debt. A single adapter interface with pluggable backends reduces incident density (0.043 per use) and aligns with FR-959 payer honesty by centralizing auth and session-id recovery. |
| OpenClaw's CLI backend plugin architecture provides vendor-neutral session resumption, version pinning, and per-backend fresh/resume profiles with transcript verification before resume. | librarian | external-method | pursue | https://docs.openclaw.ai/gateway/cli-backends | Yes. OpenClaw's CLI backends are graph-shaped: each backend plugin owns separate fresh/resume profiles, the watchdog remains active across state transitions, and session binding is verified against a readable project transcript before resume. | Medium. OpenClaw's plugin contract is proven but requires mapping your adapter interface (session id, exit code, JSONL parsing) to their CliBackendConfig schema and transcript verification model. | OpenClaw solves the exact problem: multiple vendor CLIs with different contracts, version pinning per backend, session resumption with transcript verification, and enforcement infrastructure that fails closed on missing auth or version mismatch. Their plugin architecture avoids the 1.5-day FR cost you paid per backend. |
