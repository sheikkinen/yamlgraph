# Defensive Position & Path Forward — Governed Pipeline

**Date:** 2026-08-15
**Input:** [2026-08-15-market-research.md](diary/2026-08-15-market-research.md) (competitive landscape, ninchat_voice cross-check, alternative-architecture review, kill-risks)
**Status:** Position paper — moves below graduate to FRs individually, each judged on its own. Reviewed 2026-08-15 (sister-session read against research, doctrine, FR-802/FR-803); findings folded: separability defined at the artifact plane, moves re-ranked and gated on FR-802/FR-803, ninchat_voice falsifier added.

## The Position (what we defend, one paragraph)

YAMLGraph does not compete as a general-purpose LLM framework. The defensible object is the **governed pipeline**: stochastic reasoning confined to atomic, typed, lintable YAML tasks under a deterministic, auditable controller, wrapped in a traceability spine (CAP/REQ → judged FR → enforcement gates → diary/Scripture) with **zero commercial-platform lock-in**. That combination — not the runtime — is what no funded competitor structurally can offer, because their business model *is* the execution platform. Everything below either thickens that position or thins what dilutes it.

## Threat → Defense (per kill-risk)

| # | Kill-risk | Defense | Mechanism |
|---|-----------|---------|-----------|
| KR-1 | LangChain ships a first-party declarative DSL | Make their DSL a **target, not a killer**: the spine's *artifacts* (doctrine files, CAP registry, `req_coverage.py`, gates, judgements) are substrate-independent and can govern their artifacts. The runtime half is declared regenerable (`constraint_over_code`); the spine survives the substrate. **Separability is defined at the artifact plane only**: the *governed artifact* need not touch the runtime; the *governance execution* legitimately runs on yamlgraph — the sole judge/author/review routes ARE yamlgraph graphs, mechanically enforced (FR-767). Self-hosting our own open tool is not lock-in; that IS the no-commercial-platform argument. | Artifact-plane test: can a foreign artifact class carry CAP/REQ marks, a judgement, and a gate without the runtime parsing it? (Move 1 pilot.) No import-linter claim on adapters — they are runtime by design. |
| KR-2 | gh-aw grows repo-local pipeline execution | **Assimilate, don't defend** (explored 2026-08-15): gh-aw self-positions as CI/CD complement for reasoning tasks — issue triage, PR review, CI-failure briefs — the chaplain's *periphery*, not its core. Its safe-outputs (sandboxed read-only agents, buffered validated writes in scoped jobs) is our judge-gate pattern at the GitHub boundary. Split by boundary: gh-aw owns GitHub-side sensing/dispatch (chaplain-issue triage replacing CAP-106/109 hand-rolled hardening, CI-failure briefs, scheduled digests); the local pipeline keeps judgement/enforcement/spine. Their growth then expands our adapter surface instead of eating the chaplain. Hard limits: enforcement never moves to Actions (billing gravity, platform-independence); gh-aw outputs entering the pipeline are untrusted input (instruction boundary); pin versions like any provider. | The doctrine/adapter split is the seam: a gh-aw adapter for `review-pr`/triage doctrine is the spine executing on a foreign runtime — doubles as the Seed's second pilot. |
| KR-3 | Pipecat Flows matures into an auditable conversation FSM | Scheduled architecture-level re-read (the research itself flags the April assessment as method-biased — `evaluation` trap). The pair's claim survives only while Flows transitions are *not* diffable/judgeable artifacts. Watch that one property, not the feature list. | FR-803 (judged, pending enforcement) is review zero — the re-read happens NOW; Move 5 mechanizes reviews one-plus so November does not re-litigate August's verdict. |

## Path Forward (ranked moves, each with first consumer / first event)

Graduation order: **Move 1 (dated) → Moves 2+3 (post-FR-802) → Move 4 → Move 5 (post-FR-803)**. Move 1 is the load-bearing test of the thesis — if it fails, the rest is narrative maintenance.

**Move 1 — Portable spine pilot: govern one foreign artifact class.**
The research Seed, made concrete: prove CAP/REQ/judge/gates work on artifacts the YAML runtime never parses. Cheapest credible pilot: **statemachine-engine transition tables** — a sibling with 50 states/100+ transitions, already the load-bearing plane in production, already informally traced (NC-XXX req marks in ninchat_voice tests). Success criterion (**artifact-plane independence**): a transition-table change goes through plan → judge → enforce with a `.judgement.md` and a gate, where the *governed artifact* is never a yamlgraph graph — the governance execution may and will use the existing yamlgraph-based adapters (they are the sole routes, FR-767; self-hosting is not entanglement).
*First consumer:* statemachine-engine maintainers (us); *first event:* the next FSM transition change in ninchat_voice; **pilot FR filed by 2026-09-01**.
If the pilot holds, the spine is demonstrably artifact-agnostic — KR-1 and KR-2 both lose their teeth.

**Move 2 — Subtraction: freeze the runtime at its proven primitives.** *(Gated: after FR-802 census enforces.)*
Keep and harden what carries load in production: `interrupt`, `race`, schema-templated prompts, checkpointing, lint/schema/trace. Topology features (`subgraph`, `map` growth, new node types) enter **repair-only mode**: correctness fixes to shipped claims proceed (FR-797 is repair, not growth); expansion requires a *named external or sibling consumer with a dated first event* — the backlog navigator plan (`projects/ninchat_voice/backlog.txt:48-58`) is the only such demand on file for `subgraph`. The "unused by the best consumer" claim is research-grade until the FR-802 census lands; the census table is the evidence base (and per FR-802's judgement, evidence — not deletion authority).
*First event:* the next FR proposing a new node type or topology feature is judged against this position and dies without a consumer citation.

**Move 3 — Capability-registry honesty sweep.** *(Gated: after FR-802 census enforces; consistent with its judgement — census output routes to demand checks, not direct deletion.)*
Continue the FR-465/FR-466 retirement arc: any CAP whose feature is unexercised by every consumer gets a demand check; phantom or demo-only claims are retired or explicitly marked demo-tier. The registry becomes the mechanical form of Move 2.
*First event:* first `fr_board`/CAP audit after FR-802 lands.

**Move 4 — Reposition the front door.**
README/ARCHITECTURE currently sell framework capability ("60–80% of workflows without Python") — a thesis the research declares eroded. Reposition to the surviving claim: *lintable, diffable, mechanically judgeable pipeline artifacts for agent authors, under a traceability spine, self-hosted.* Delete or demote framework-parity marketing.
*First consumer:* the next agent (or human) evaluating the repo; *first event:* next README-touching PR.

**Move 5 — Mechanize the quarterly kill-risk review.** *(Gated: after FR-803 enforcement — FR-803 is review zero; this move mechanizes reviews one-plus.)*
Not a calendar note: a chaplain inbox proposal template with the three KR questions, filed quarterly. The Pipecat question is fixed wording: *"Do Pipecat Flows transitions exist as diffable, lintable, mechanically judgeable artifacts yet?"* — yes on that single property means the voice-vertical control plane is contested and FR-803's verdict is void.
*First event:* 2026-11-15 review, seeded with FR-803's rendered verdict as the baseline.

## What We Do NOT Do

- No feature parity pursuit with CrewAI/Dify/Langflow; no visual builder.
- No hosted/commercial control plane — platform-independence *is* the position.
- No new topology primitives without a named consumer and dated first event.
- No porting of the runtime to chase LangGraph API churn beyond what shipped claims require.

## Falsifiers (what would change this position)

- An external adopter arrives *for the runtime itself* → revisit Move 2's freeze.
- The Move 1 pilot fails **at the artifact plane** (a foreign artifact cannot carry CAP/REQ marks, a judgement, and a gate without the runtime parsing it) → the "governance is the product" thesis loses its portability leg; reassess whether the moat is real or narrative. (Execution-plane use of yamlgraph adapters is NOT a failure — it is the design.)
- **ninchat_voice migrates off the pair** → the entire "proven primitives" evidence base is one project's load; if it leaves, Move 2's freeze list has no witness and must be re-derived from whatever consumer remains.
- A kill-risk fires → execute the KR row, not a rescue of the runtime.
**Seed:** If Move 1 succeeds on statemachine-engine, the second foreign runtime is **gh-aw** (explored 2026-08-15: its `.md`+frontmatter workflows are lintable, diffable, lock-compiled — ideal judged-FR subjects, and it entirely lacks REQ traceability). The assimilation goes both ways: the spine governs gh-aw artifacts, and a gh-aw adapter executes review/triage doctrine at the GitHub boundary (its FR should cite CAP-106/109 as retirement targets — subtraction paired with the adapter). What is the minimal installable unit of the spine (doctrine files + adapters + req-coverage script), and does it have a name that isn't "yamlgraph"?
