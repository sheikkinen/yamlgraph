# Research: Published Agentic-SDLC Definitions vs the YAMLGraph Process

**Date:** 2026-08-29
**Question:** The yamlgraph repo contains an elaborate development process
(Scripture, plan-judge-enforce, enforcement rings, diary graduation). Assumption:
similar SDLC definitions have been invented and published by multiple providers.
Investigate and report.

**Verdict: confirmed — the core skeleton (spec-before-code, frozen scope, gated
phases, independent review, agent-readable doctrine) has been published by at
least five providers since ~2025, largely convergently. Three specific layers of
the YAMLGraph process have no published provider equivalent.**

Companion docs: [development-process.md](development-process.md) (internal
self-reflection), [feature-request-methodology.md](feature-request-methodology.md)
(waterfall-era lineage). This document covers the *modern provider* landscape
those two do not.

---

## 1. Provider survey

| Provider / spec | Published process | Governing artifact |
|---|---|---|
| **GitHub Spec Kit** (132k stars, v1.0.0, 2026-08) | Spec-Driven Development: `/constitution → /specify → /plan → /tasks → /implement → /converge`; optional `/clarify`, `/analyze`, `/checklist`; bug extension `assess → fix → test`; idea extension `intake → research → define → shape → decide` ending in **go / clarify / kill** | Constitution (project principles) + spec/plan/tasks per feature |
| **AWS Kiro** | Three-phase specs with **approval gates**: `requirements.md` (user stories + acceptance criteria) → `design.md` → `tasks.md`; separate **Bugfix Specs** (current/expected/unchanged behavior); dependency-graph "waves" for parallel task execution; Quick Spec skips gates for well-understood work | Spec triple + steering files |
| **Anthropic Claude Code** | Explore → Plan → Implement → Commit; "give Claude a check it can run"; **deterministic hooks vs advisory instructions** (their exact framing); fresh-context **adversarial review subagent**; Writer/Reviewer split sessions; worktree-isolated parallel sessions; `/goal` + Stop hooks as verification gates | CLAUDE.md + hooks + skills |
| **AGENTS.md** (OpenAI, Google, Cursor, Factory → Linux Foundation AAIF) | Open standard for repo-level agent doctrine; nearest-file precedence in monorepos; 60k+ adopting repos | AGENTS.md |
| **BMAD Method** (52k stars, v6) | "Agile AI-Driven Development": Clarify → Plan → Build → Learn-and-adjust loop; role agents (PM, architect, dev, QA); **right-sized process** (small changes skip planning); **BMad Loop** — builds, verifies, and retros a whole epic unattended | Briefs, specs, architecture docs |
| **OpenAI Codex cloud** | Task → isolated cloud environment → summary + diff → **review before merge** → PR; parallel tasks in dedicated environments; **"compare several attempts"** (best-of-n); intake from GitHub/GitLab/Linear/Slack; scheduled tasks triggered by app events | AGENTS.md + environment config |
| **Google Jules** | Prompt → **generated plan → human approves plan** before any code change → autonomous execution in VM → PR; scheduled tasks; reads AGENTS.md | AGENTS.md |

Sources (fetched 2026-08-29):

- <https://github.com/github/spec-kit> and `spec-driven.md` therein
- <https://kiro.dev/docs/specs/>
- <https://code.claude.com/docs/en/best-practices> (redirect of the Anthropic
  engineering "Claude Code best practices" post)
- <https://agents.md/>
- <https://github.com/bmad-code-org/BMAD-METHOD>
- <https://learn.chatgpt.com/docs/cloud> (Codex cloud)
- <https://jules.google/docs>

---

## 2. Concept-by-concept mapping

| YAMLGraph concept | Published analogue | Convergence quality |
|---|---|---|
| Scripture / copilot-instructions.md | Spec Kit **constitution**, CLAUDE.md, AGENTS.md, Kiro steering | Strong — "executable doctrine" is now a cross-vendor standard |
| FR as governing contract, frozen scope | Kiro `requirements.md` with approval gates; Spec Kit spec/plan/tasks | Strong |
| **Judge** (fresh session, adversarial, APPROVE/AMEND/SPLIT/REJECT) | Spec Kit `/analyze` + assess-extension **go/clarify/kill**; Anthropic fresh-subagent adversarial review & Writer/Reviewer ("the agent doing the work isn't the one grading it" — same anti-anchoring rationale) | Strong, though no provider makes rejection a first-class archived verdict |
| Enforce with verification gates | Anthropic "give Claude a check it can run" + Stop hooks + `/goal`; Spec Kit `/converge` loop | Strong |
| Ring 1 hooks (deterministic, per tool call) | Claude Code hooks — Anthropic explicitly distinguishes advisory CLAUDE.md from deterministic hooks, i.e. `detection_without_enforcement` independently stated | Strong |
| Route by task shape (manual vs pipeline, development-process.md §3.1) | BMAD "right-sized process: small changes go straight to build"; Kiro Quick Spec (no approval gates); Anthropic "if you could describe the diff in one sentence, skip the plan" | Strong — three vendors converged on the same dispatch heuristic |
| Chaplain inbox → autonomous pipeline | GitHub Copilot coding agent (issue → PR); **BMad Loop** (unattended epic + retro); Kiro autonomous task execution; Codex cloud intake from GitHub/GitLab/Linear/Slack (≈ CAP-106 remote inbox); Jules prompt→plan→approve→PR | Moderate — same shape, none carries a judge stage inside the loop |
| Plan approval before execution | Jules blocks code changes until the human approves the generated plan | Weak analogue — the *requester* approves their own plan; no independent fresh-session judge, anchoring unaddressed |
| Race node / hedging | Codex cloud "compare several attempts" (best-of-n parallel runs) | Strong — convergent with the race-node primitive (CAP-91) |
| Inquisitor ~24h audit cadence | Codex/Jules **scheduled tasks** (incl. event-triggered) | Shape only — vendors schedule *work*, not doctrine-compliance audits |
| Investigation-FR-then-fix-FR, condemning test | Spec Kit bug extension `assess → fix → test`; Kiro Bugfix Specs root-cause analysis | Strong |
| Map-node parallel fan-out | Kiro dependency "waves"; Anthropic `/batch` + worktree fan-out | Strong |
| CAP→REQ→test→changelog traceability spine | **No provider ships this.** Closest: Spec Kit lists "V-Model test traceability" as a hypothetical *community extension*; otherwise it lives only in regulated-SDLC standards (DO-178C, IEC 62304 — see feature-request-methodology.md) | Weak — genuinely differentiating |
| Diary → Philosopher → Scripture graduation | Nothing published. BMAD "Learn and adjust" and Anthropic "treat CLAUDE.md like code, prune it" are manual gestures; nobody has a **mechanical** incident→doctrine pipeline with recurrence thresholds and a devil's-advocate gate | None — unique |
| Inquisitor (scheduled audit vs doctrine); instruction-boundary adversarial review of agent output | Nothing published. Anthropic's classifier-reviewed auto mode is per-action risk, not doctrine-compliance auditing | None — unique |

---

## 3. Analysis

**What this confirms.** The FR/judge/enforce rite is not idiosyncratic — it is
the industry's convergent answer to the same failure modes (anchoring,
continuation bias, plausible-wrong-answers). Strongest independent
corroborations: Anthropic arrived at *separation of judgement from generation*
and *deterministic-over-advisory enforcement* using nearly the Scripture's
vocabulary; Spec Kit arrived at a constitution plus kill-verdicts; BMAD and
Kiro both arrived at the §3.1 task-shape dispatch heuristic. Convergent
evolution across five vendors is strong evidence the doctrine's skeleton is
sound, not ritual.

**What no provider has published:**

1. **The closed self-amendment loop** — diary-gate forcing reflection,
   mechanical graduation of recurring traps into enforceable doctrine,
   Inquisitor auditing main against the Scripture. Every published framework
   has a static or manually-pruned doctrine; this repo is the only surveyed
   system where *the process rewrites its own constraints from incident
   evidence*.
2. **Traceability spine as merge-blocking gates**
   (CAP→REQ→`@pytest.mark.req`→changelog-req-gate). Providers treat
   traceability as an optional enterprise extension; here it is Ring 2/3
   blocking infrastructure — a direct import from regulated SDLC that the
   agentic-tooling market has not productized.
3. **Adversarial treatment of the agent's own vendor instructions**
   (`instruction_boundary`, copilot-trailer-gate, `model_as_trusted_peer`). No
   vendor publishes this — unsurprising, since it treats the vendor as the
   threat.

**Divergences examined:**

- **Spec Kit `/converge`** (assess codebase vs spec/plan/tasks, append
  remaining work as new tasks): initially flagged as worth stealing;
  **refuted on re-analysis** — `/converge` is a compensating control for the
  absence of merge-blocking traceability gates. Where criteria become
  REQ-tagged tests re-verified on every commit, convergence is already
  enforced continuously and the FR is an expired contract by design; the
  mature response to stale claims is CAP retirement, not re-assessment.
  Full refutation: [plan-converge-map-mercury-reduce.md](plan-converge-map-mercury-reduce.md) §0.
- **Kiro dependency waves** (build the task dependency graph, execute
  independent tasks concurrently in waves): **refuted on disposition** — the
  capability already exists here at the correct granularities, and the
  granularity waves would add is the one this repo's incident record forbids.
  - *Within a graph run*: `type: map` / fan-out is native parallelism — waves
    are a scheduler for exactly this, already built.
  - *Across changes*: the Judge's SPLIT verdict decomposes an FR into
    independent FRs, and worktree-per-topic pipelines already run them in
    parallel. SPLIT + worktrees *is* the wave scheduler at change granularity.
  - *Within one FR's enforce stage* (Kiro's actual granularity): parallel
    writers in one worktree are the `one_session_one_repo` corruption vector
    (three-strike incident class: shared index, WIP destruction, interpreter
    swaps), and the FR-698 caveat already recorded FR/CAP/REQ **ID-reservation
    races between merely two parallel pipelines**. Kiro affords waves because
    it owns a sandbox with file-scoped tasks and no shared gate
    infrastructure; the chaplain's enforce is one session against shared
    hooks, IDs, and a shared index.
  - The residual real item is not waves but plumbing already seeded in
    development-process.md §3.1: **ID reservation at dispatch**. Import the
    lock, not the scheduler.

**Net result of the divergence analysis: zero imports.** Both candidates
dissolved on contact with the repo's own constraint set — `/converge`
compensates for gates this repo has; waves schedule parallelism this repo
either already has (map, SPLIT+worktrees) or has paid three incidents to
learn not to want (intra-worktree concurrency).

**Seed:** the three unique layers (self-amending doctrine, gated traceability
spine, vendor-adversarial boundary) are exactly the parts a provider *couldn't*
publish — the first requires a long-lived single repo, the second a
regulated-industry mindset, the third distrust of the publisher. Is that a
moat, or a sign they only work at n=1 operator?

**Second seed (from the divergence analysis):** both "worth stealing"
candidates were refuted not by taste but by the repo's own recorded
constraints (`constraint_over_code`, `one_session_one_repo`, the traceability
spine). A provider-comparison survey's real output may not be imports at all,
but *confirmation pressure*: each refuted import names precisely which local
constraint made the imported mechanism unnecessary — the survey as a stress
test of the doctrine's completeness.

## 4. Known issues, evidence-checked (2026-08-29)

Three operator-named defects in the process, measured against the working
tree. They turn out to be one structural fact wearing three costumes.

### 4.1 The process suits fill-in-the-blanks development, not research spikes

Already half-diagnosed in development-process.md §3.1 (task-shape dispatch:
"using the Chaplain for a spike wastes an hour to learn what a 5-minute
prototype would have shown"). What §3.1 does not say: the pipeline's entry
ticket is a *falsifiable acceptance criterion*, and a spike's output is a
question, not a criterion — so spikes cannot enter at all. They route around
the pipeline entirely. Live witness: this very survey — two research docs,
zero gates fired, zero FRs, destined for direct-to-main. Every surveyed
provider ships a governed lightweight lane (Kiro Quick Spec, BMAD
right-sizing, Claude Code explore-first); this repo's lightweight lane is the
*ungoverned* one (83% direct pushes). The spike gap is not the absence of a
lane — it is that the existing lane has no doctrine.

### 4.2 Growth for growth's sake — concentrated in docs and examples

Mass distribution (py+yaml+md lines): core `yamlgraph/` **26,075**;
`examples/` **165,122**; `docs/` **115,295**; `feature-requests/` **189,118**;
`reference/` **30,120**. Periphery ≈ **19× core**. The judge kills 53 of 825
FRs (~6.4%); 7 of 32 `docs/plan-*.md` are referenced by no FR at all. Cause,
not coincidence: every Ring 2/3 gate *taxes change with artifact production*
(diary-gate, demo-gate, changelog-gate each demand a new file per change),
while **no gate ever fires on staleness**. The retirement doctrine
(`growth_as_default`, FR-465/466 CAP arc) covers capability claims — docs and
examples have no retirement mechanism whatsoever. §4.1 is the intake valve:
spike outputs enter through the ungated side door and become exactly this
mass.

### 4.3 Some examples have never been executed by a human

Of **88** demos, **23 (26%)** have no `demo-output.log` at all (mostly
Jan–Mar 2026, predating the FR-206 demo-gate — the gate was never applied
retroactively). Of the 65 that have one, **38 (58%) committed it exactly
once** — at authoring, by the authoring *agent*. The gate proves an agent ran
the demo once at PR time; it has never proven human execution, and for most
demos nothing has ever proven a second execution. `builders_never_call`
(2026-07-17: graphs found unconsumed) already recorded the human half. The
demo corpus doubles as the ~130-tool MCP surface, so this is also an
unaudited API: `who_reads_this_when` fails for most of it.

Provenance, however, is largely intact: **76 of 87 demos (87%) cite an FR in
their creation commits** — the origin story is recoverable from the record
(creation commit → FR problem statement → acceptance criteria → diary
mentions). Only 11 are true orphans, mostly from the pre-gate era. This
changes the shape of the cure: the question "is this example still valid?"
is answerable, but it is *archaeology plus valuation*, not a re-run.

### Synthesis: one blind spot, three symptoms

Every enforcement ring fires on **change events at the merge boundary**. Two
consequences follow mechanically: work that never merges is never governed
(→ 4.1), and artifacts that stop changing exit the enforcement field forever
(→ 4.2, 4.3). The demo-output.log is a *birth certificate*, not a pulse. A
process whose only sensor is the diff is blind to both the unborn and the
dead.

**Third seed (revised same day — the first cut was too mechanical):** an
Inquisitor re-run sweep tests *liveness*, not *value*. Re-running a demo
proves it still executes; it cannot answer "why was this made, and does that
reason still hold?" That is a cognitive research task per example — deduce
the origin story (creation commit → cited FR → problem statement), classify
the current role (regression witness / teaching artifact / spike remnant /
MCP tool), judge whether the motivating problem still exists, and where the
model cannot decide, *ask the operator a value question*. That is an
"88 items × LLM assessment" shape — natively a **map graph**, with the
pattern already proven by `req_witness_audit` (FR-851: map(haiku) over
batches, verdicts, raw persistence, SHA-stamped runner per FR-860):

- *gather* (tool node): per-demo dossier — creation commits, cited FR text,
  README, graph description, demo-output.log age, diary mentions.
- *map* (haiku-tier): origin deduction + role classification + validity
  verdict (`valid / stale-motivation / superseded / undecidable`) + at most
  one operator question where undecidable.
- *reduce*: triage report + a short operator questionnaire. **Humans render
  the value verdicts; retirement FRs are filed only after answers** — the
  FR-851 lesson (235 instrument-gap partials would have auto-filed junk)
  forbids auto-emitting retirements from model verdicts.

Liveness (re-run) stays with the clock-driven Inquisitor; valuation runs as
this audit graph on demand. Together they give docs/examples the predator
that phantom CAPs already have — without laundering value judgements through
a model.

### 4.4 Keep-or-retire: MCP and A2A (evaluated 2026-08-29)

**Operator verdict, same day: "no one speaks a2a to yamlgraph ... nor mcp
for that matter." Both RETIRE.**

**MCP — RETIRE (initial "keep" overturned by the consumer record).**
`.vscode/mcp.json` pointed at `yamlgraph/mcp_server.py`, deleted by FR-717
PR2 on **2026-07-18**. The launch command has failed with ENOENT for ~6
weeks; the ~130 `mcp_yamlgraph_*` tools visible in agent sessions were
served from editor cache, and nobody noticed. Worse for the keep case:
`builders_never_call` (2026-07-17, graphs found unconsumed) **predates the
breakage** — the surface was unconsumed even while it worked. The thesis
("build for agents first") is already satisfied by the transport that won:
CLI wrapped in adapter scripts (`author.sh`, `judge.sh`, `review.sh`),
consumed by agents daily. MCP duplicated that surface for editor-attached
dynamic tool selection — a consumer class that never materialized here.
Registration was fixed same day (`-m yamlgraph.export.mcp`) before the
operator verdict; the retirement FR should remove `.vscode/mcp.json`,
`yamlgraph/export/mcp.py`, and CAP-19/CAP-136. Resurrection condition: a
named external MCP host actually wired to it.

**A2A — RETIRE.** Mass: ~1,600 code lines
(`a2a/server.py`, `a2a/message.py`, `contrib/a2a_client.py`,
`cli/a2a_commands.py`) + ~1,500 test lines + **5 CAPs** (81, 101, 103, 104,
105) + 13 FRs of maintenance history + heavy optional deps (grpcio,
protobuf, starlette). Consumers: **zero** — `send_a2a_message` is referenced
only by its own CAPs, tests, and demo; the `a2a_call` demo is its only graph;
no chaplain/script/example consumes it, and the operator confirms no external
system does either. Last functional (non-mechanical) commit: **2026-04-19**
(FR-253) — four months of pure carrying cost. None of the seven surveyed
providers' workflows speak A2A.

Both retire via the FR-465/466 CAP-retirement path — the specs survive in
the FRs (`constraint_over_code`), and resurrection must disposition the
retirement FRs first. Shared plumbing note: `yamlgraph/discovery.py` is
consumed by the CLI and stays.
