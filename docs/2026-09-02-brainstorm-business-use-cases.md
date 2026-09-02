# Business Use Cases — Brainstorm and Ranking

*Date: 2026-09-02*
*Status: brainstorm / position input — nothing here is an FR. Each idea that survives review graduates on its own.*
*Inputs read:* `docs/` (plans, research, diary, mercury-census, whitepaper), `docs-planning/`, `feature-requests/FR-819…FR-828`, `examples/` (all top-level apps + `demos/`), `reference/` (node types, patterns, map-nodes, corpus-map-reduce, coded-classification), `docs/node-type-census-2026-08.md`.

---

## 1. Method

Three questions were asked of the corpus, then a fourth of the answers:

1. What business ideas do the docs already contain, and what verdict did the docs themselves reach?
2. Which examples are product-shaped, and which patterns do they prove?
3. What does the runtime actually make cheap that competitors do not?
4. Given 1–3, which *new* use cases follow — and how do all of them rank?

**Scoring.** Each idea gets three 1–5 scores. Rank order is **Novelty + Value**; **Evidence** breaks ties and is reported so a high-scoring idea with no proof is visible as such.

| Score | Novelty (N) | Value proposal (V) | Evidence (E) |
|---|---|---|---|
| 5 | No incumbent category | Named buyer, regulated pain, budget exists | Running in production or shipped example |
| 3 | Incumbents exist, angle is new | Real pain, buyer plausible, budget unclear | Demo or plan with named consumer |
| 1 | Crowded, parity play | Nice-to-have | Idea only, or refuted |

---

## 2. What the corpus already says (compressed)

### 2.1 Verdicts already reached — do not re-litigate

| Verdict | Where | Consequence for this list |
|---|---|---|
| Framework positioning ("60–80% without Python") is **eroded**; do not compete with CrewAI/Dify/Langflow | `docs/diary/2026-08-15-market-research.md` | Ideas that sell the runtime score N=1 |
| The defensible object is the **governed pipeline** + **auditable-by-construction** evidence, self-hosted, no commercial platform | `docs/plan-defensive-position-governed-pipeline.md`, `docs/whitepaper-auditable-by-construction.md` | Governance/evidence ideas get the strongest E and V |
| Runtime should **shrink** to proven primitives: `interrupt`, `race`, schema-templated prompts, checkpointing, lint/trace | market research cross-check (ninchat_voice) | Ideas needing new topology features need a named consumer |
| `map` is dispositioned **RETIRE** (47 uses, all demos/examples, no committed consumer) | `docs/node-type-census-2026-08.md` | **Tension** — see §5.2: the census portfolio *is* map-reduce |
| Hosted runner (FR-823) approved but payments blocked (FR-820); no hosted control plane is *the position* | `feature-requests/FR-823`, `FR-820` | Serve + Stripe scores low on strategic fit |
| Voice runtime is commodity; **policy, intent taxonomy, care workflows are the product** | `docs/devils-advocate-2026-03-27.md` | Voice ideas score on domain logic, not transport |
| REFUTED / CONDEMNED: `/converge` map-mercury-reduce, browser WebLLM micro-runtime, raw credit arbitrage, opening PRs on strangers' repos | respective docs | Listed in §6, not ranked |

### 2.2 Product concepts already on file

The single most commercial artifact is **`docs/mercury-census/findings.md`** — a ranked portfolio built on one insight: *when a semantic judgement costs a fraction of a cent, exhaustive census replaces sampling.* Convergent architecture: **census fan-out → evidence-stamped, abstention-capable reduce → exception queue with human veto**. Its own instruction: *"Build the ledger/reduce core ONCE — it is the actual product; verticals are configuration."*

| Doc idea | One line | Doc's own standing |
|---|---|---|
| Auditable-by-construction | Per-run diff between judged design and actual route; AI Act Art. 12 evidence | "Strongest claim… already proven by production code" |
| P1 CallCensus | 100% contact-centre QA vs 1–3% sampling | Recommended wedge, "weeks not quarters" |
| P2 CodingProof | Clinical ICPC-2/ICD coding census & audit | Moat = incident-priced boundary machinery |
| P3 OpenCoder | Open-text survey coding | Nearest to self-serve SaaS |
| P4 FactGuard | Semantic DLP — leaks of *fact*, not patterns | Highest novelty, least validated |
| P5 SendGuard / P6 Adjudicator | Intent intercept; exception-first case review | Follow-ons |
| P0b EA cartographer | Census of a GitHub org → architecture map | "Stale by definition — i.e. all of them" |
| Portable governance spine | CAP/REQ/judge/gates over artifacts the runtime never parses | Move 1; falsifier defined |
| GitHub chaplain action | Label an issue → judged FR as PR; Copilot is fulfilment | "Enforce does not ship" |
| Outcome-priced 402 endpoints | Sell verified outcomes for sats, never credits | Research only; ToS + sandbox blockers |
| Kertomus synthetic records | FHIR → Finnish narrative records, 690 LoC → ~80 LoC YAML | Detailed port plan |
| Call From Chat | Discord slash command → live PSTN call, human types every word | Five gated phases |
| Fandom / Dungeon Master | Canon-first story generation, story workbench | Conditionally approved, scope cut required |

### 2.3 What the examples prove

Five examples are production-shaped (FastAPI, sessions, deploy files, tests): **`dungeon_master`**, **`booking`**, **`openai_proxy`**, **`daily_digest`**, **`npc`**. Pattern maturity, rather than product surface, lives in **`book_reviewer`**, **`icpc-2-rfe`**, **`cwe-classifier`** (decomposed map → deterministic reduce, "no LLM ever emits a number"), **`memory-curation`** (the only example with a real approval/reversibility contract), and **`api-discovery`** (graph-as-tool composition).

Gaps: `race` appears only in demos; A2A/MCP/skills export are **retired** (FR-909/910/912) — any interop use case must rebuild them.

### 2.4 What the runtime makes cheap

- **Corpus map-reduce** with eight invariants (freeze, partition, typed map, canary-by-family, abstention, deterministic reconcile, coverage arithmetic, egress boundary before the model call). Reference: `reference/patterns/corpus-map-reduce.md`.
- **Coded classification**: cluster fan-out over a closed vocabulary, evidence spans aligned to source, junk-drawer caps, LLM-free crosscheck. Two proven instances.
- **Interrupt + checkpointer** across phone/web/chat: new questionnaire = three YAML files, zero Python; ~€0.85/call at 10k volume (`reference/intent-questionnaire-pattern.md`).
- **Route decision log + Mermaid overlay + `--diff`**: a determinism witness and per-run conformance evidence with an `artifact_hash` over graph and prompts.
- **Lint as a closed error surface** (~1 s, keyless, `Fix:` line on every error, NDJSON) — the one property only gh-aw matches, and gh-aw cannot run locally.
- **Z3-backed guard verification** (W803–W805): a concrete counterexample state for every routing gap.

Constraints that shape use cases: map fan-out is **unbounded** (pre-chunk for rate limits; local LLM servers break), `max_items` **silently truncates** at 100, no nested map/agent/subgraph inside a map, streaming bypasses structured output, text is the only native modality.

---

## 3. Reflection: what the map-reduce pattern is actually for

The pattern fits when all four hold:

1. **Items are independent** — no cross-item state during the map. Chapters, calls, tickets, tests, clauses, tables, articles.
2. **Per-item context is bounded and pre-gathered** — a deterministic node builds an evidence bundle; the LLM judges a bundle, it never searches. (The `/converge` refutation is precisely the case where this was violated.)
3. **The reduce is deterministic** — counting, reconciling, ranking, rendering happen in Python. An LLM in the reduce reintroduces the "almighty prompt" the pattern exists to avoid.
4. **Abstention is a first-class output** — an empty bundle mechanically caps the verdict at `unverifiable`; the model never gets to say "satisfied" on shape alone.

What it buys commercially is one sentence: **"we read all N; here is the coverage arithmetic, the provenance, and the exceptions."** Sampling-based incumbents (QA, audit, coding review, compliance review) cannot say that. That sentence is the value proposal behind every census idea below.

Where it does *not* fit: anything requiring exploration (agent work), anything where items interact (use FSM or a sequential loop), real-time paths (use `race`/`interrupt`), and anything where the vocabulary is open and no reconciliation rule exists (the reduce becomes an LLM again).

Two new *shapes* of the pattern worth naming, because several ideas below depend on them:

- **Cross-product census** — map over pairs (regulation article × internal policy; guideline × care pathway; requirement × test). The reduce is a coverage matrix with gaps and orphans on both axes. This is what `req_witness_audit` already does internally for REQ × test.
- **Temporal census** — the same corpus at two snapshots, or commits over time (mercury-census "trend census"). The reduce is a drift report. `graph export --diff` is the same idea at graph granularity.

---

## 4. Brainstorm: new use cases

Grouped by the primitive they lean on. Each carries a first buyer and the oracle that makes the output checkable, because the monetization research is right that *the oracle is what makes the price dispute-free*.

### 4.1 Cross-product census (map over pairs, deterministic coverage reduce)

**N1 — RegMap: regulation-change impact census.** New or amended regulation (EU AI Act, NIS2, MDR, national decree) × the organisation's SOP/policy corpus → evidence-stamped gap list: which articles have no covering document, which documents cite superseded text, which need review. Abstention when the bundle is thin; exception queue for a compliance officer. *First buyer:* compliance function in a regulated healthcare or fintech org. *Oracle:* every gap cites an article and a document span; reviewer disposes. *Dogfood:* the whitepaper maps AI Act articles to the repo's mechanisms by hand today — run it as a graph.

**N2 — Care-pathway guideline drift census** (RegMap vertical). National guideline updates × local care pathway / triage instruction corpus → drift list with clinical-reviewer veto. *First buyer:* medical director of a primary-care provider. *Oracle:* citation pairs; clinical review. High V in Finnish primary care where guidelines change and local instructions lag.

**N3 — Traceability & conformance gate for regulated software (git-native).** Requirement × test × run-evidence coverage as a CI gate and a per-release evidence pack: orphan requirements, phantom tests, routes executed outside the approved artifact. This is `req_witness_audit` + route overlay + the FR judgement trail, packaged for IEC 62304 / ISO 13485 / AI Act shops that today buy Jama or Polarion and reconcile by hand. It is also **Move 1** (portable spine) with a customer attached. *First buyer:* SaMD startup preparing a notified-body audit. *Oracle:* coverage arithmetic is mechanical; the evidence pack is diffable.

**N4 — AuditPack: per-run conformance evidence bundle.** The runtime half of N3: for every production run, the judged design artifact hash, the route log, the overlay, and the diff, rendered as a bundle a conformity assessor can open. Already produced at call teardown in one healthcare deployment; the product is the packaging and the article mapping. *First buyer:* the same deployment's compliance owner. *Oracle:* the diff is empty or it is not.

### 4.2 Corpus census (map over items, evidence-stamped reduce, exception queue)

**N5 — Patient-safety incident census.** Free-text incident/near-miss reports (HaiPro-class) → coded classification into a closed harm taxonomy with evidence spans, cluster detection across units and time, abstention, human veto. Today these are read by one safety officer, sampled. *First buyer:* patient-safety lead at a hospital district or private provider. *Oracle:* evidence span aligned to the report text; closed vocabulary. Pattern is CodingProof's machinery on a different taxonomy.

**N6 — Decision & commitment ledger.** Census over all recorded meeting transcripts in a unit → who committed to what, by when; contradiction detection across meetings; exception queue for unowned or conflicting decisions. Per-meeting summarisers are commodity; the *cross-meeting* reduce with contradiction detection is not. *First buyer:* PMO / chief of staff. *Oracle:* every ledger row quotes its transcript span.

**N7 — Data-catalog semantic census.** Map over tables and columns of a warehouse → semantic description, PII/special-category flag with evidence (sample values never leave the boundary — hash and shape only, matching the OTEL privacy rule), draft GDPR Art. 30 record of processing. *First buyer:* data-protection officer + data platform lead. *Oracle:* flags are reviewable per column; abstention on ambiguous columns.

**N8 — Model-upgrade regression census.** When a provider deprecates a model, replay the frozen verdict corpus (729 judgements, or a customer's own promptfoo suite) across candidate models → migration report with per-case agreement and cost delta. Providers deprecate on a quarterly cadence; every team with prompts in production has this problem and solves it by hand. *First buyer:* any team running LLM features in production. *Oracle:* agreement rate against frozen verdicts. Builds directly on `plan-token-cost-mitigation.md`.

**N9 — Contract-portfolio obligation census.** Clause-level obligations, renewal dates, non-standard terms across all vendor contracts, with abstention and evidence spans. CLM vendors exist; the census + abstention + no-LLM-emits-a-date angle is the differentiator. *First buyer:* procurement/legal ops in a mid-size org.

**N10 — Alert/log census for SRE.** A month of alerts → noise taxonomy, duplicate families, actionability score. Useful, but incumbents and open tooling are strong. Included for completeness.

### 4.3 Coded classification (closed vocabulary, evidence-aligned)

The reference lists candidate taxonomies; ranked here by market and hallucination-intolerance:

**N11 — CPV/UNSPSC spend classification for public procurement analytics.** Every invoice line or tender lot → CPV code with evidence. Ties directly to the existing HVA procurement bulletin corpus (Hilma/TED). *First buyer:* wellbeing-services county procurement unit; consultancies doing spend analysis.

**N12 — Invoice → chart-of-accounts coding with abstention** for accounting firms handling Finnish e-invoices. Crowded (every accounting SaaS ships "AI coding"), but none ship evidence spans and abstention; the differentiator is audit-grade, not accuracy.

**N13 — ESCO occupation & skill coding** for job ads and CVs (public employment services, HR analytics). Moderate market, moderate pain.

### 4.4 Interrupt + checkpointer (multi-turn structured intake)

**N14 — Structured intake as a service.** Schema in, three YAML files out, deployed across phone/web/chat with the same graph: pre-visit medical intake, informed-consent capture with comprehension probes, grant/benefit application intake, incident reporting. Production-proven in voice; the product is the schema-to-deployment path plus the Python scoring boundary (scores never come from the LLM). *First buyer:* provider already running the voice stack; second, a public agency with a form backlog.

### 4.5 Governance & judgement as product

**N15 — Review-history judge.** Mine a customer's merged PR review threads into frozen verdicts, distil to a cheap model, ship as a CI reviewer calibrated to *their* house style with a regression fixture so it cannot drift silently. Competes with generic AI reviewers on calibration and on the frozen-fixture guarantee. *First buyer:* a team with >2 years of review history and a style guide nobody reads.

**N16 — Census-as-code specification.** Publish the corpus map-reduce invariants (freeze, canary-by-family, abstention cap, coverage arithmetic, egress-before-model) as a written spec with a conformance test suite anyone can run against their own implementation. Zero revenue, high thought-leadership value; it names the category the census products sell into and it is the "Proclaim" stage the diary says is missing.

### 4.6 Race + guardrails (real-time)

**N17 — Governed multi-provider gateway.** `openai_proxy` + `race` + guardrails + route log as a drop-in OpenAI-compatible endpoint with per-request conformance evidence. LiteLLM/Portkey own the gateway category; the evidence log is the only differentiator. Low novelty; listed because it is nearly free to ship from existing examples and is a natural on-ramp to N4.

---

## 5. Ranking

Sorted by **N+V**, ties by **E** (higher first). Ideas from the docs are marked *(doc)*; new ones *(new)*.

| # | Idea | N | V | E | N+V | Why it sits here |
|---|---|---|---|---|---|---|
| 1 | Auditable-by-construction / AuditPack (N4) *(doc+new)* | 5 | 5 | 4 | 10 | Only idea with production proof, a named regulatory buyer, and no incumbent category; observability vendors structurally cannot answer "did it stay within the approved design" |
| 2 | P2 CodingProof clinical coding audit *(doc)* | 4 | 5 | 4 | 9 | Two proven pattern instances; moat is the reconciliation machinery; procurement cycle is the cost |
| 3 | Traceability & conformance gate, git-native (N3) *(doc Move 1 + new)* | 4 | 5 | 3 | 9 | Same moat at design time; incumbents are heavy and not git-native; doubles as the portable-spine pilot the strategy already demands |
| 4 | RegMap regulation-impact census (N1) *(new)* | 4 | 5 | 3 | 9 | Cross-product census has no incumbent; AI Act/NIS2 create the budget now; dogfood case exists |
| 5 | P1 CallCensus contact-centre QA *(doc)* | 3 | 5 | 4 | 8 | Doc's recommended wedge; QA-analytics incumbents exist, 100% census with abstention is the angle |
| 6 | Patient-safety incident census (N5) *(new)* | 3 | 5 | 3 | 8 | Same machinery as #2, different taxonomy, buyer with a statutory duty and a sampling problem |
| 7 | Care-pathway guideline drift census (N2) *(new)* | 4 | 4 | 3 | 8 | RegMap vertical; specific, recurring, clinically reviewed |
| 8 | Kertomus synthetic Finnish records *(doc)* | 4 | 4 | 3 | 8 | GDPR-safe test/training data for health-tech; Synthea is English/FHIR only, the narrative layer is novel |
| 9 | P4 FactGuard semantic DLP *(doc)* | 5 | 3 | 2 | 8 | Highest novelty in the corpus, least validated demand; false-positive floods are the death mode; E=2 puts it last among the 8s |
| 10 | Structured intake as a service (N14) *(new)* | 3 | 4 | 4 | 7 | Production-proven primitive; the product is the schema→deployment path |
| 11 | P0b EA cartographer (org repo census) *(doc)* | 3 | 4 | 4 | 7 | `repo_census` demo exists; buyer is universal but budget is soft |
| 12 | Model-upgrade regression census (N8) *(new)* | 3 | 4 | 3 | 7 | Universal, recurring pain; frozen-verdict corpus is the asset; promptfoo is the substrate, not the competitor |
| 13 | Decision & commitment ledger (N6) *(new)* | 3 | 4 | 3 | 7 | Cross-meeting reduce is the novelty; per-meeting summarisers are commodity |
| 14 | Data-catalog semantic census (N7) *(new)* | 3 | 4 | 3 | 7 | DPO pain is real; privacy rule already designed in |
| 15 | GitHub chaplain action for arbitrary repos *(doc)* | 4 | 3 | 3 | 7 | "Sell the front half, Copilot fulfils" is a sharp move; demand signal is zero external adopters so far |
| 16 | Review-history judge (N15) *(new)* | 4 | 3 | 3 | 7 | Calibration + frozen fixture differentiates from generic reviewers |
| 17 | Process mining of agent workflows *(doc)* | 4 | 3 | 3 | 7 | Genuinely new instrument; buyer unclear beyond ourselves |
| 18 | P6 Adjudicator / P5 SendGuard *(doc)* | 3 | 4 | 2 | 7 | Follow-ons to #5; not standalone |
| 19 | Outcome-priced 402 endpoints / fix bounties *(doc)* | 4 | 3 | 1 | 7 | Best oracle story in the corpus, blocked by provider ToS and sandboxing; research only |
| 20 | CPV spend classification (N11) *(new)* | 2 | 4 | 4 | 6 | Adjacent to the live HVA bulletin corpus; crowded analytics market |
| 21 | P3 OpenCoder survey coding *(doc)* | 2 | 4 | 4 | 6 | Nearest to self-serve; most incumbents |
| 22 | Census-as-code spec (N16) *(new)* | 4 | 2 | 4 | 6 | No revenue; names the category; fills the missing Proclaim stage |
| 23 | Contract-portfolio obligation census (N9) *(new)* | 2 | 4 | 3 | 6 | CLM incumbents; census angle is modest |
| 24 | Invoice → chart-of-accounts (N12) *(new)* | 2 | 4 | 3 | 6 | Crowded; audit-grade evidence is the only wedge |
| 25 | Web toolkit / .fi catalog *(doc)* | 3 | 3 | 3 | 6 | Infrastructure with named internal consumers; sells indirectly |
| 26 | Judge distillation *(doc)* | 3 | 3 | 3 | 6 | Internal cost lever first; becomes #12/#16 externally |
| 27 | Call From Chat (Discord → PSTN) *(doc)* | 3 | 3 | 3 | 6 | Well-scoped, human-in-charge; niche operator tool |
| 28 | Auto-publishing satellite repos *(doc)* | 3 | 2 | 5 | 5 | Best "runs unattended" proof; product value is in what they publish, not the mold |
| 29 | Governed multi-provider gateway (N17) *(new)* | 2 | 3 | 4 | 5 | Nearly free from `openai_proxy`; category owned by others |
| 30 | Fandom / Dungeon Master workbench *(doc)* | 3 | 2 | 3 | 5 | Largest example, judged scope-cut; consumer content market, no buyer named |
| 31 | ESCO occupation coding (N13) *(new)* | 2 | 3 | 3 | 5 | Moderate everything |
| 32 | Alert/log census (N10) *(new)* | 2 | 3 | 3 | 5 | Strong open incumbents |
| 33 | SiteScribe / document-library summariser *(doc)* | 1 | 3 | 4 | 4 | Correct acceptance test for the pipeline; commodity as a product |
| 34 | Skills export / marketplaces *(doc)* | 2 | 2 | 2 | 4 | Export surface retired (FR-912); no pull signal |
| 35 | YAMLGraph Serve + Stripe credits *(doc)* | 1 | 2 | 3 | 3 | Contradicts the no-commercial-platform position; competes with funded hosts |
| 36 | Framework positioning ("60–80% without Python") *(doc)* | 1 | 2 | 5 | 3 | Declared eroded by the corpus itself |

### 5.1 Reading the table

- **Ranks 1–7 are one product family.** The census/reduce core with abstention and evidence, sold into regulated buyers, plus the conformance evidence (#1, #3) that lets those buyers accept it. The mercury-census instruction stands: build the ledger/reduce core once; the rest are configurations of it.
- **Healthcare dominates value.** CodingProof, incident census, guideline drift, Kertomus, structured intake all have a named buyer class in Finnish healthcare. That is where the corpus has production evidence and where "auditable" has a statutory meaning.
- **Novelty without evidence is FactGuard.** It is the one idea where the honest move is a demand probe (ten conversations) before any code.
- **The runtime-as-product tail (ranks 34–36) is dead by the corpus's own verdicts** and stays dead here.

### 5.2 The `map` contradiction — a decision, not a finding

The node census marks `map` **RETIRE** for lack of a committed consumer. Ranks 1–14 are all map-reduce. Move 2 says topology features need *"a named external or sibling consumer with a dated first event."* The first funded census engagement **is** that consumer. Until one exists, the freeze is correct and the census products are research; the moment one exists, `map` (and the resumable storage-backed map from the web-toolkit plan) is the load-bearing primitive and should exit repair-only mode. Whoever ranks these ideas is also deciding `map`'s fate.

Two map defects would become customer-visible immediately at census scale and should be fixed before any paid run. Planning state as of 2026-09-02:

| Defect | Covered by | State |
|---|---|---|
| Silent truncation at `max_items` — must raise, never drop scope; coverage arithmetic depends on it | **FR-939** map overflow policy (D-2 of the FR-936 split): typed `on_overflow: error \| truncate`, default `error`, enforced before the first `Send`. Also repairs a second defect it found: `config.max_map_items` is parsed but never reaches `map_edge`, so the documented graph-level cap is inert today | Judged APPROVED WITH REVISIONS 2026-08-31; authority activates on human review of the judgement; **not implemented** — `map_compiler.py` still warns and slices |
| Thread leakage on branch timeout (FR-069) | **FR-936 D-3**, an investigation-first FR for timeout cancellation and resource lifecycle. The bounded shared pool proposed in FR-936 was rejected (it converts leakage into deterministic starvation); the accepted mechanism must terminate work at the provider boundary or in a terminable execution unit and prove post-timeout liveness | **No replacement FR authored yet** — the gap is open |
| `reference/patterns.md` Pattern 12 documents a `source:`/`prompt:`/`state_key:` map shorthand; the schema and compiler accept only `over`/`as`/`node`/`collect` | Nothing. FR-894 touches `patterns.md` only for cross-links from Patterns 8 and 10 | **Uncovered** — a docs fix, one small FR or a fold into FR-939's reference update |

The remaining two FR-936 splits, D-1 input projection (`pass_keys`, full-state copy per `Send`) and D-4 native `RetryPolicy`, are also unauthored. D-1 matters at census scale because every branch checkpoints the whole parent state.

---

## 6. Not ranked — already refuted by the corpus

| Idea | Verdict | Where |
|---|---|---|
| `/converge` FR convergence check | REFUTED same day; compensating control, not a primitive | `docs/plan-converge-map-mercury-reduce.md` |
| Browser WebLLM micro-runtime | CONDEMNED absent a named consumer | `docs/plan-browser-microruntime-webllm.md` |
| Raw credit arbitrage | Killed in spec (provider ToS) | `docs/research-aicredit-monetization.md` |
| Opening PRs on third-party repos | Non-goal; "burns the commons" | same |
| gitclaw as multi-user platform | 3–4/10; containment does not constrain Copilot | `docs/analysis/gitclaw-evaluation.md` |
| Visual builder / hosted control plane / CrewAI parity | "What we do not do" | `docs/plan-defensive-position-governed-pipeline.md` |

---

## 7. Recommended next moves (each is one FR at most)

1. **Write the two wedge briefs the corpus keeps deferring**, but pick the pair that share a buyer: **AuditPack (#1)** and **CodingProof (#2) or incident census (#6)**, both for a healthcare provider that already runs the voice stack. One buyer, one procurement conversation, one evidence story.
2. **Run RegMap on ourselves**: AI Act articles × `docs/` + `reference/` as a graph, replacing the hand-built mapping in the whitepaper. It is a dogfood test of the cross-product census shape and produces the whitepaper's appendix for free.
3. **Fix `max_items` truncation to raise** before any paid census run. It is a one-line defect with a coverage-arithmetic consequence.
4. **Ten-conversation demand probe for FactGuard** before a line of code; record the outcome as a diary entry so the highest-novelty idea has an E score that is not 2.
5. **Decide the `map` question explicitly** (§5.2) rather than letting the census disposition and the census portfolio contradict each other in the record.

**Seed:** if the census/reduce core is the product and every vertical is configuration, what is the smallest installable unit — graph, reducer, canary set, exception-queue renderer — and does that unit have a name that is not "yamlgraph"?
