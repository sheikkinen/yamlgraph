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
