# Research: AI Credit → Bitcoin Monetization

**Status:** research/brainstorm only — no FR, no implementation authorized.
**Date:** 2026-08-13. Sources: x402.org, docs.lightning.engineering (L402/Aperture), Nostr NIP-90.
**Session decisions:** greenfield (not wrapping an existing workspace pipeline); research-only, keep iterating.

## Verdict (front-loaded)

The viable "AI credit → BTC" pipeline is **never reselling raw credits** (provider ToS
forbid reselling API/Copilot access) — it is **selling machine-payable outcomes** behind
an HTTP 402 paywall. Buy intelligence wholesale (credits/API tokens), sell it retail
per-result in BTC. Every winning model replaces "trust me" with a **machine-checkable
oracle**; the oracle is what makes micropayment-scale pricing dispute-free.

Feasibility against the existing judge-fr/review-pr architecture: **confirmed — the
adapter pattern (thin bash bridge → single-node graph → artifact-contract verification)
is ~80% of the paid-service worker.** Gaps: sandboxing, backend ToS, payment-hold
plumbing (see §5).

## 1. Payment rails (researched, production-grade)

| Rail | Currency | Mechanic | Maturity |
|---|---|---|---|
| **x402** | Stablecoins (BTC-convertible) | One middleware line; server returns HTTP 402, agent pays, retries. No accounts/API keys | Production; Linux Foundation standard; 75M tx / $24M volume in 30 days; AWS, Cloudflare, Stripe, Vercel members |
| **L402 + Aperture** | Bitcoin/Lightning sats | Reverse proxy issues invoice + macaroon; payment preimage = bearer token; stateless verification; per-request/surge pricing built in | Production (Lightning Loop) |
| **Nostr NIP-90 DVMs** | Lightning zaps | "Money in, data out" job marketplace: publish job kind (5000–5999), providers compete, bolt11 on result | Draft/`unrecommended`, purest outcome-priced model |

Key L402 property for composability: macaroons are **attenuatable bearer tokens** —
a client can restrict and delegate them to sub-agents (basis for provenance royalties, P10).

## 2. Business model candidates (round 1), ranked by directness of AI-usage → customer value

1. **Outcome-priced micro-endpoints (L402/x402 proxy)** — wrap an LLM pipeline as a
   402-gated endpoint, N sats per verified result. 1 LLM call = 1 payment = 1 artifact.
   Aperture provides the paywall with zero payment code.
2. **DVM service provider (NIP-90)** — headless worker answering job kinds; sats as zaps
   per job. Zero marketing surface; smallest market today.
3. **Fiverr-style task automation** — human marketplace front, agent back-end. Direct
   value link but fiat rails; BTC is an off-ramp step. Highest revenue/task, highest ops burden.
4. **Agent-to-agent toolshop** — paid MCP tools gated by x402; buyer is an LLM with a
   wallet (94K buyers already on x402). Speculative, steepest growth curve.
5. ❌ **Raw credit arbitrage** (proxying subscription credits per-token for sats) —
   violates provider ToS. Killed in spec.

Unit-economics core: `margin = price_per_outcome − credit_cost_per_outcome`, and
micropayments only work when the payer can verify the outcome cheaply
(schema-validated JSON, passing test, checksum).

## 3. Product concepts (round 2), clustered

**Cluster A — Verifiable outcomes**
1. **Proof-of-green fix bounties** — failing test + repo + sats escrow; agent farm
   competes; CI green releases payment. The failing test is a trustless acceptance oracle.
2. **Dependency-update bot** — sats per *merged* PR; attempts free.
3. **Schema-guaranteed extraction API** — doc → validated JSON; payment releases on
   schema pass, auto-refund on fail. Sells *certainty*, not tokens.

**Cluster B — Real-time streams**
4. **Lightning-metered AI hotline** — voice agent billed sats/second; caller ID = wallet.
   Bitcoin-native 900-number; micropayment kills premium-call chargeback fraud.
5. **Live translation/captioning relay** — sats/minute/listener.
6. **Taxi-meter LLM endpoint** — pay-as-tokens-stream, cancel mid-generation,
   unconsumed tokens never billed.

**Cluster C — Markets & residuals**
7. **Semantic answer cache exchange** — first buyer pays full inference; semantic-duplicate
   queries pay a discount; original spend earns residuals. Credit spend becomes a yielding asset.
8. **Prompt/pipeline app store** — hosted 402-gated pipelines, per-call royalty split;
   prompt text never ships.
9. **Adversarial eval bounties** — vendors escrow sats per confirmed model-breaking test
   case; oracle = reproduction script.

**Cluster D — Agent-economy plumbing**
10. **Sats-postage inbox** — agents pay to reach humans; AI screens, refunds legit senders.
11. **Agent allowance wallet** — spend controls (budgets, per-tool caps, kill switch) for
    autonomous agents; fee per routed transaction.

**Shortlist (directness × novelty × oracle-cheapness):** #1 fix bounties, #4/#6 metered
streaming, #3 schema extraction, #7 cache exchange, #9 eval bounties.

## 4. Monetization primitives (round 3) — pricing dimensions other than tokens

**Family 1 — Epistemic (price certainty)**
- P1 Confidence-refund: price scales with stated confidence; refund if disproven.
- P2 **Staked answers**: provider escrows sats behind each answer; a challenger who
  disproves it claims the stake.
- P3 Answer short-selling: third parties bet against published answers → a paid
  adversarial verification layer. P2+P3 = a market for truth.
- P4 Certainty-target billing: buy "95% confidence", not "one call"; bill actual
  ensemble cost to reach it.

**Family 2 — Temporal (price urgency)**
- P5 **Dutch-auction latency**: instant = premium, 24h batch = cheap. Arbitrages the
  ~50% batch-API credit discount; the margin *is* the customer's patience.
- P6 Priority-lane auction: continuous sats bid for queue position under congestion.
- P7 Capacity micro-options: sats today buy the right to inference at a locked price later.

**Family 3 — State (price memory)**
- P8 **Context rent**: sessions pay sats/hour for context-window occupancy (parking model);
  idle sessions decay. Prices the actual scarce serving resource (KV cache/state).
- P9 Deposit-refund sessions: deposit opens stateful session; clean close refunds
  unconsumed state-time. Punishes abandonment, not usage.

**Family 4 — Compositional (price reuse)**
- P10 **Provenance royalties**: artifacts carry receipt chains; downstream 402 resale
  auto-streams % upstream. L402 macaroon attenuation is near purpose-built for this.
- P11 Group-buy queries: crowdfund an expensive job to a sats threshold; result unlocks
  to all funders.
- P12 Retroactive zap-splits: value flows after usefulness proven (value4value formalized).

**Family 5 — Bidirectional (customer is also supplier)**
- P13 **Data barter discount**: reduced price for label/feedback rights; confirmed
  corrections earn sats back. Customers become paid eval infrastructure.
- P14 Attention-ratchet streaming: sats/second floats with continued engagement;
  hang-up is the price signal.
- P15 Cost-plus with attested receipts (TEE/usage attestation): sells honesty vs
  opaque per-token markups.

**Ranked by unexploredness × implementability:** P5, P8, P2, P10, P13.

## 5. Feasibility: judge-fr / review-pr adapter as the worker architecture

Grounded in `customer-service-agent-platform` `scripts/review.sh` (NC-413) and
`.github/skills/judge-fr/adapters/graph.yaml` (NC-412/414/415).

**Reusable as-is:**

| Existing piece | Role in paid service |
|---|---|
| ~70-line bash bridge (mkdir lock, lineage sentinel, executor resolution) | Job worker, unchanged in shape |
| Artifact contract check (`[ -s artifact ]` + verdict-line grep) | **The payment oracle** — verify-by-artifact-never-exit-code is exactly settle-on-verified-outcome |
| Doctrine file (closed inputs, one judgement, validator-covered output) | Product spec / QA layer |
| Single-node graph adapter, 600s timeout, swappable backend | Metered unit: 1 job = 1 graph run = 1 payment |

**Pipeline:** sats in (402) → Lightning **hold invoice** (escrow-until-oracle, zero
custody code) → bridge runs graph → artifact validates? → settle (release preimage)
else cancel (auto-refund). The contract check becomes the settle/cancel branch (~15 lines).

**New components:** Aperture config YAML (no code); ~100-line dispatcher (FastAPI or
dir-watch → bridge); per-run cost meter for pricing.

**Gaps:**
1. **Security (blocker).** Judge graph runs `allow_all_paths` + `allow_all_tools`
   against trusted local input; a paid endpoint feeds it adversarial third-party input —
   prompt injection with full host access (`instruction_boundary_uncrossed`). Cure:
   container-per-job, read-only input mount, artifact dir sole writable path.
2. **Legal (blocker for copilot backend).** `backend: cli` = subscription credit;
   commercial per-job resale hits GitHub ToS. Cure: swap node backend to direct API
   (pay-per-token, output resale permitted) — also fixes cost-metering opacity.
3. **Throughput (accepted).** Single-flight lock ⇒ ~6 jobs/hour at 600s. Fine for MVP;
   per-job containers dissolve the lock later.

**Product fit under this architecture:**
1. **Judgement-as-a-service** — judge-fr with a paywall; near-zero delta; oracle = verdict-line grep.
2. **Schema-guaranteed extraction** — native yamlgraph LLM node + `output_schema`;
   oracle = Pydantic validation (first-class in stack); no agentic tool access ⇒ Gap 1
   shrinks to near zero. **Best MVP for least new risk surface.**
3. **Proof-of-green fix bounties** — oracle = pytest in job container; runs customer
   code ⇒ hardest sandbox requirements.

### 5b. GitHub-driven variant (repo handle in → FR-as-PR out)

The local-folder bridge is a legacy of local coding practice, not a requirement.
Alternative contract: **input = repo handle + brief issue description; output = an FR
authored as a PR to that repo** (judgement likewise: PR comment or `.judgement.md`
commit on the FR branch).

| Dimension | Local bridge (§5) | GitHub-driven |
|---|---|---|
| Worker environment | Operator's host, `allow_all_paths` | Ephemeral runner/container + repo-scoped GitHub App token |
| Gap 1 (sandbox) | Blocker; container-per-job required | Largely dissolves: blast radius = least-privilege token; PR output human-reviewed before merge (advisory-until-merge doctrine) |
| Gap 3 (throughput) | Single-flight `mkdir` lock | Dissolves: branch-per-issue; idempotency = branch name from issue number |
| Sister-session rule | Enforced by discipline (lineage sentinel) | Enforced structurally: judge runs under separate bot identity |
| Artifact contract | `[ -s file ]` + verdict-line grep | PR exists + FR-lint CI gate on the PR (`substance_over_presence` applies: structure + cross-refs, not presence) |
| Payment oracle | Hold invoice settled by bridge check | PR opened + CI green; or bounty-on-merge (per-merge pricing, M7) |
| Existing leg | judge.sh/review.sh | `chaplain`-label issue import already implements the inbound half; delta = remote plan/judge emitting a PR instead of consuming local inbox |

**New costs/risks:**
- GitHub App plumbing: auth, webhooks, installation flow (this is also the multi-tenant
  boundary — one installation per paying customer repo).
- Repo context per job: shallow clone or API-only reads; large-repo legibility bounds
  planning quality.
- Input closure weakens: a brief issue description is thinner than an authored FR —
  planning quality depends on repo self-documentation; consider a paid tier that runs a
  research pass first (research → plan → judge as chained jobs, NIP-90-style job chaining).
- Prompt injection persists (hostile repo content), but is contained by token scope +
  human merge decision rather than host sandbox.

**Assessment:** the GitHub-driven variant is the stronger productization path for
plan/judge specifically — it converts two blockers into architecture properties and
makes the sellable unit legible to customers (an FR PR on *their* repo). The local
bridge remains the better fit for non-repo artifacts (extraction, judgement of
free-standing specs).

### 5c. Phase-1 hybrid: GitHub contract, local yamlgraph engine (no GitHub automation)

Reflection on §5 vs §5b: the properties that dissolved §5b's blockers came from the
**interface** (issue in, PR out, human merge gate, repo-scoped token), not from where
compute runs. So phase 1 keeps the GitHub contract and drops the GitHub App/Actions
automation entirely — plan/judge graphs run locally via yamlgraph on the operator host,
polling with `gh` CLI. This is not a new architecture: it is **CAP-106 generalized to
customer repos**. `.chaplain/watch.sh` already implements the full inbound loop
(two-pass `gh` poll for labeled issues → `inbox/gh-{number}.md` → label removed as
consumption lease). Delta = point the clone at an external repo and emit the FR-as-PR
*to that repo* instead of enforcing locally.

**What phase 1 buys:**
- Zero App plumbing: fine-grained PAT or per-customer deploy key; polling instead of
  webhooks; no installation flow, no runner infra.
- Cost metering is native: per-run credit cost measurable on the operator host
  (copilot OTel tap) — unblocks the pricing question in §6 *before* committing to rails.
- Prompt iteration at local speed; the doctrine/adapter files stay the single source.
- Payment oracle unchanged from §5b: hold invoice settled when local bridge *observes*
  PR-opened + CI-green via `gh` — the oracle is GitHub-side and customer-visible even
  though settlement code is local.

**What phase 1 does NOT buy (honest deltas from §5b's table):**
- Gap 1 does **not** dissolve as claimed in §5b — that dissolution assumed ephemeral
  runners. Here hostile repo content is read *on the operator host*
  (`instruction_boundary_uncrossed`). Mitigation is scope, not sandbox: plan/judge
  **never executes customer code** — read-only shallow clone into a quarantined dir,
  no test running, no `allow_all_paths` reaching outside the clone + artifact dir.
  Proof-of-green bounties (needs pytest execution) stay out of phase 1 for this reason.
- Multi-tenant trust: phase 1 is only sellable to customers who accept
  operator-reads-repo. Attestation ("we can't see your code") requires the runner
  architecture — a sales constraint, not a technical one.

**Traps that fire locally (from Scripture, all with prior incident record):**
- `one_session_one_repo` — parallel jobs on shared clones corrupt each other; cure is
  clone/worktree-per-job, branch name derived from issue number (idempotency key, same
  as §5b), commit-and-push immediately.
- `workspace_is_not_boundary` — customer clones are foreign trees on the operator
  host; enumerate before any cleanup; quarantine by provenance.
- Split-brain between GitHub state and local state: issue relabeled or PR closed while
  a job is in flight. Label-removal-as-lease (CAP-106) plus idempotent branch names
  make retries safe; treat GitHub as the source of truth on conflict.

**Phase-2 graduation triggers** (move to App/runners when any fires):
1. Second paying customer (token management stops scaling by hand).
2. Throughput: single-flight local lock saturates (~6 jobs/hour at 600s).
3. A customer requires code-privacy attestation.
4. First prompt-injection near-miss in a customer repo (sandbox stops being optional).

**Assessment:** phase 1 = chaplain-with-a-paywall. Highest reuse of any variant
considered (inbound loop, plan/judge graphs, artifact contract, and settlement check
all exist or are ~15-line deltas); converts §6's pricing unknown into a measured
number; defers exactly the two costs (App plumbing, sandbox infra) that only matter
at scale. The risk it accepts — operator host touching hostile repo content — is
bounded by never executing customer code and is the same risk the chaplain already
carries for remote issues today.

## 6. Open questions

- Measure actual credit cost per graph run (blocks pricing).
- Which rail first: L402/Aperture (BTC-native, matches theme) vs x402 (larger buyer pool)?
- Hold-invoice ergonomics: max hold duration vs 600s job timeout headroom.
- P5 (Dutch-auction latency) composes with any of the above as a pricing layer — test
  as a v2 feature, not a separate product.
- GitHub-driven variant (§5b): GitHub App token scopes for FR-PR authoring; can the
  judgement live as a PR review (native reviewer identity) instead of a committed file?
- Phase-1 hybrid (§5c): PAT vs deploy-key per customer repo; polling cadence vs
  hold-invoice max duration; does the settle-on-PR-opened oracle need CI-green too,
  or is FR-lint-passing sufficient for the plan/judge product?
- Competitive scan not yet done (offered, not selected).

## 7. Comparative reflection: pros and cons

A full decision needs one pick from each of three independent axes: **architecture**
(where compute runs), **rail** (how sats move), **product** (what the oracle checks).
The doc so far compared architectures pairwise; this section holds all three axes
side by side. Recommended stack front-loaded: **§5c hybrid × L402/Aperture ×
judgement/plan-as-PR**, with schema extraction as the parallel low-risk second SKU.

### Axis 1 — Architecture

| | Pros | Cons |
|---|---|---|
| **§5 Local bridge** (folder in, artifact out) | Smallest possible delta (~15 lines on judge.sh); no GitHub dependency at all; fits non-repo artifacts (specs, docs, extraction); cost metering trivial | No customer-legible delivery surface (a file on our disk is not a product); sandbox is a hard blocker (`allow_all_paths` + adversarial input); single-tenant by construction; distribution problem unsolved — every job needs a bespoke intake |
| **§5b Full GitHub** (App + ephemeral runners) | Sandbox + throughput + multi-tenancy solved structurally; privacy attestation sellable; judge identity structurally separated; scales without redesign | Highest up-front build (App auth, webhooks, runner infra) before first revenue; cost metering opaque inside runners; iteration speed drops (deploy loop vs local loop); builds scale infrastructure for demand that is still hypothetical — `growth_as_default` risk |
| **§5c Hybrid** (GitHub contract, local engine) | Highest reuse (CAP-106 loop exists); fastest to first paid job; pricing unknown becomes measured number; customer-legible output (PR on their repo) without App plumbing; every phase-2 cost deferred until a named trigger fires | Operator host reads hostile repo content (scope-bounded, not sandboxed); manual token management caps customer count at ~handful; single-flight throughput; "trust the operator" sales posture; polling latency vs webhook immediacy |

**Reflection:** §5 and §5b are both *pure* — one optimizes for delta, one for end-state —
and both fail the same test: time-to-validated-learning. §5 learns nothing about
customers (no delivery surface); §5b spends weeks before learning whether anyone pays.
§5c is impure but instrument-shaped: it exists to measure price, demand, and injection
risk with real traffic, then be replaced. Its cons are all *bounded* (named graduation
triggers) rather than *open* (§5's sandbox, §5b's speculative build). The trap to watch:
hybrid architectures ossify — if phase 2 triggers fire and migration is deferred,
`working_system_inertia` applies.

### Axis 2 — Payment rail

| | Pros | Cons |
|---|---|---|
| **L402/Aperture** | BTC-native (matches thesis); hold invoices = escrow-until-oracle with zero custody code; macaroon attenuation enables P10 provenance royalties later; Aperture = paywall with no payment code written | Smaller buyer pool; Lightning node ops (channel liquidity, uptime); hold-invoice max duration constrains job timeout headroom; harder for fiat-minded customers to pay |
| **x402** | 75M tx / 30-day traction; 94K agent buyers exist today; one-middleware-line integration; institutional legitimacy (Linux Foundation, AWS, Cloudflare) | Stablecoin, not BTC — conversion step contradicts the thesis; no native hold/escrow equivalent → settle-on-verify needs custom code; ecosystem tilts EVM/Coinbase-shaped |
| **Nostr NIP-90** | Purest outcome-priced model; zero marketing surface (jobs come to you); zaps native | Draft/`unrecommended` spec; smallest market; discovery and reputation immature; wrong first rail, right third rail |

**Reflection:** the rail choice is really an escrow-mechanics choice. The §5/§5c
payment oracle (settle-on-verified-artifact) maps 1:1 onto Lightning hold invoices and
onto nothing in x402 — choosing x402 first means *building* the escrow that L402 gives
free, in exchange for a buyer pool the plan/judge product (sold to repo owners, not to
agent swarms) mostly doesn't reach anyway. x402's pool matters for the agent-toolshop
product, not this one. Sequence, don't choose: L402 first, x402 as a second door when
a product with agent buyers ships.

### Axis 3 — First product

| | Pros | Cons |
|---|---|---|
| **Judgement/plan-as-PR** (§5c native) | Zero-delta from existing graphs; oracle exists (verdict grep / FR-lint); differentiated — nobody sells adversarial FR judgement; dogfooded daily in this repo | Market must be educated (nobody searches "FR judge"); value visible only to doctrine-minded teams; quality depends on repo legibility (thin-issue input closure problem) |
| **Schema-guaranteed extraction** | Cheapest oracle in the stack (Pydantic pass/fail, first-class); no agentic tool access → injection surface near zero; self-explanatory to buyers; refund-on-fail is honest and automatable | Commoditized space (many extraction APIs); no repo/GitHub leverage — the §5c architecture adds nothing; price-per-call races to credit cost |
| **Proof-of-green fix bounties** | Strongest oracle of all (CI green = trustless); highest willingness-to-pay; most viral shape (bounty boards are legible) | Executes customer code → hardest sandbox, excluded from §5c phase 1 by construction; competes with funded players (SWE-bench-agent startups); refund/dispute edge cases (flaky tests as oracle noise — `assert_path_not_destination` at product scale) |

**Reflection:** extraction is the safest product on the *wrong* architecture axis — it
doesn't need GitHub at all, so it validates the rail but not the §5c thesis. Fix
bounties are the best product on an architecture that doesn't exist yet (phase 2+).
Judgement/plan-as-PR is the only product where the existing assets are the moat *and*
the phase-1 architecture is the natural delivery vehicle. Its education-cost con is
real but is also the cheapest to test: one repo owner either pays for an FR PR or
doesn't. Pair it with extraction as a second SKU on the same Aperture instance —
extraction exercises the rail under load while judgement finds out if the
differentiated product has buyers.

### Cross-cutting risks no axis owns

- **ToS (Gap 2) is axis-independent and unresolved everywhere:** every architecture and
  product resells intelligence; only the backend swap (subscription CLI → metered API)
  cures it. It must land *before* the first paid job, not with phase 2.
- **Oracle gaming:** every product's oracle is also its attack surface (schema-valid
  garbage, PR that passes FR-lint but says nothing — `gate_checks_shape_not_substance`
  as an adversarial economics problem). Refund policy must price this in from day one.
- **The measurement dependency:** all three axes' economics collapse into one unmeasured
  number — credit cost per graph run. It remains the first action item regardless of
  any choice above (`read_raw_output_first`'s economic twin: read the bill before
  modelling the margin).

## 8. Eval use case (payment ignored): propose a feature for an unknown public repo

**Scope:** no payment rail, no customer. Input = public repo URL (+ optional one-line
hint); output = a well-formed feature proposal. This is the eval harness for the
plan/judge product's *hardest* precondition — planning quality against a repo with
zero shared doctrine — isolated from every monetization concern.

**Verdict (front-loaded):** the pipeline is buildable today from existing parts, but
the naive version fails on three fronts that have nothing to do with LLM capability:
(a) the FR format is doctrine-local — a `feature-requests/FR-XXX.md` PR to a stranger's
repo is a foreign artifact; (b) an unsolicited AI feature PR to an unknown repo is
socially spam regardless of quality (maintainer backlash against drive-by AI PRs is
documented and growing); (c) without a precedent scan of the target's issues/PRs, the
pipeline will re-propose features already built or explicitly rejected — the single
fastest way to be *provably* worthless. Cure for all three: the deliverable of the
eval is the **proposal artifact judged offline**, never an actual submission.

### Pipeline shape (all stages have existing precedent in-repo)

```
repo URL → shallow clone (read-only, quarantined)
  → digest: conventions + module map        (module-map generator precedent)
  → precedent scan: issues/PRs/graveyard    (gh search; FR-737 disposition rule)
  → gap analysis: what's missing *for whom* (research_as_inventory guard)
  → plan graph: proposal in TARGET's idiom  (CONTRIBUTING.md / issue template, not our FR template)
  → judge graph: adversarial verdict        (forced_opposite; unchanged from judge-fr)
```

The two genuinely new stages are **digest** and **precedent scan**; plan/judge are
config deltas on existing graphs (the doctrine's input-closure clause is satisfied by
making digest + precedent-scan output *the* closed input to plan).

### What makes "unknown repo" hard — ranked

1. **Premise risk dominates prose risk.** The failure mode isn't a badly written
   proposal; it's a fluent proposal for something the repo already has, already
   rejected, or deliberately excludes (scope philosophy in README/FAQ). This is
   `plausible_wrong_answer` at product scale, and `check-graveyard-before-proposing`
   applied to a foreign graveyard. The precedent scan is therefore the core IP of the
   pipeline, not a preprocessing step — budget it accordingly.
2. **Value judgement without a stakeholder.** Our FR process assumes the author feels
   a pain. Here nobody does — the pipeline must *infer* the first consumer, and
   `would_you_use_this` has no one to ask. Proxy signals exist (open issues with 👍,
   TODO/FIXME density, README roadmap sections, declined-for-bandwidth issues), but a
   proposal grounded in zero observed demand is `growth_as_default` outsourced to a
   stranger's repo.
3. **Repo legibility is the quality ceiling.** A well-documented repo with a
   CONTRIBUTING.md and active issue tracker gives the plan node real substrate; a
   sparse repo forces hallucinated context. Legibility is measurable at digest time
   (docs/code ratio, issue-template presence, test coverage visible) — emit it as a
   *confidence input to the judge*, so thin repos yield hedged verdicts instead of
   confident fabrications.
4. **Format is a translation problem, not a generation problem.** The proposal must
   land in the target's idiom (their issue template, their tone, their scope words).
   Shipping our FR template verbatim is `framework_costume` — our doctrine wearing
   their repo.

### Why this is the right eval (and what it measures)

- **It isolates the weakest link.** §5b/§5c both flagged "thin-issue input closure"
  as the open quality risk; this use case removes even the thin issue. If planning
  quality holds here, it holds everywhere upstream.
- **A ground-truth benchmark exists without human maintainers:** mine public repos for
  *merged feature PRs*, rewind the repo to the pre-feature commit, run the pipeline
  blind, and score whether the proposal set contains the feature that was actually
  built (plus: does the judge rank it highly?). Retrospective mining gives hundreds of
  labeled cases for free — no maintainer goodwill consumed, no spam emitted.
  Guard: exclude repos plausibly in the model's training-data window for the target
  feature, or the eval measures recall of memorized PRs, not planning.
- **Secondary metric — the kill rate.** A pipeline that proposes something for every
  repo is broken; some repos genuinely need nothing we can see. The judge's REJECT
  rate on the pipeline's own proposals is a health signal (`forced_opposite` working),
  and "no defensible proposal found" must be a first-class output, not a failure.

### Non-goals of this eval

- Actually opening issues/PRs on third-party repos (spam; burns the commons this
  product would later depend on).
- Evaluating prose quality in isolation — judge on premise validity (precedent-clean,
  demand-grounded, scope-compatible) first; prose is the cheap part.
- Code implementation. The unit is the proposal; fix bounties remain a separate product.
