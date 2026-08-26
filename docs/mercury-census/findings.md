# Research: Cheap-Map / Code-Reduce (Mercury) — Opportunity Space

**Started:** 2026-08-26
**Method:** repeated `innovation_matrix` runs (capability×constraint ideation,
temp 0.85, fresh context per run — escaping loaded-context bias per FR-890
rationale) from deliberately different angles, plus repo investigation.
Convergence across independent runs is the signal; single-run ideas are noise
until they recur.

## The pattern under study

*Cheap-map, code-reduce, one-judgement-tail* (diary
2026-08-26-cheap-map-code-reduce): fan out one-judgement-per-call LLM nodes on
the cheapest adequate model (mercury-2 = label, haiku = paragraph; opus never
in the fan-out), aggregate with deterministic fail-closed LLM-free code,
spend at most one expensive synthesis call. Four in-repo witnesses: FR-402
(prompt_theme_analyzer), FR-046 (diary_digest), FR-890 (research-route),
philosopher rework (WIP, concurrent device).

## Process log

| # | Angle | Artifact | Status |
|---|-------|----------|--------|
| 0 | Repo investigation: map-node census, model pinning, semantic-work-in-regex sites | chat analysis 2026-08-26 | done |
| 1 | Broad: repo workflow, ingestion, ops, outside software | `runs/run-mercury.txt` | done |
| 2 | Outward/commercial: sampling→census framing, regulated buyers | `runs/run-outward.txt` | done |
| 3 | Latency-specific: what only millisecond judgements enable (real-time interposition) | `runs/run-latency.txt` | done |
| 4 | Individual/civic/consumer: value to persons and society, not enterprises | `runs/run-civic.txt` | done |
| 5 | Forced opposite: where the pattern fails, harms, or is the wrong tool | `runs/run-inverse.txt` | done |
| 6 | Web use cases, operation-class-open verbs; **first canary-gated run** (canaries precommitted in `canaries-rounds-6-8.md`, withheld from prompt) | `runs/run-web.txt` | done — **canary FAIL** |
| 7 | Machine-consumer angle (output consumed by AI systems) | `runs/run-machine.txt` | done — canary partial |
| 8 | Web-grounded via web-research agent graph | `runs/run-grounded-FAILED-OPEN.txt` | **INVALID — search never ran, graph failed open** → REDONE post-FR-891, see below |
| 9 | Operation class TRANSFORM (rewrite/redact/personalize per unit) | `runs/run-transform.txt` | done — canary partial |
| 10 | Grounded commoditization map (fail-closed librarian, post-FR-891) | `runs/run-grounded-commoditization.txt` | done — **canary PASS** |
| 11 | Operation class GENERATE (per-item synthesis at scale) | `runs/run-generate.txt` | done — canary PASS |

## Findings so far (pre-convergence)

### F1 — Inward census (run 0, repo facts)
- 28 of 33 `type: map` graphs pin no model → inherit opus-class default.
  Classifier graphs (icpc-2-rfe, cwe-classifier, memory-curation,
  salvage_classify) fan out at ~100× necessary cost. One-line pins = chore.
- Scripture seeds `diary_graduation_pipeline` and `inquisitor_auto_escalation`
  are literally this pattern, unbuilt because priced at opus rates.
- Anti-candidates named: fr_board parse rescue (fix the boundary, not LLM);
  any deny-path LLM (enforcement/latency-critical → code, FR-890 §3).

### F2 — The structural insight (run 2)
**Sampling → census.** Industries sample because judgement was expensive
(contact-center QA at 1–3%, clinical coding audit, document review, market
research coding). Mercury economics makes the full census affordable; the
LLM-free reduce layer supplies the audit trail regulated buyers require.
The sellable IP is the reduce/boundary layer (span repair, junk-drawer caps,
fail-closed citations, disagreement-as-rows) — the model is a commodity.

### F3 — Asset-proximity ranking (run 2 + workspace grounding)
- Tier 1 (asset + customer exist): contact-center 100% QA (ninchat_voice,
  csap); clinical coding census (icpc-2-rfe + FR-722/727/730 machinery);
  open-text survey coding (questionnaire-api).
- Tier 2 (novel, embryo in repo): semantic DLP — meaning-level leak detection
  (FR-874 finding productized; memory-curation graph is the embryo);
  explainable adjudication stack (FR-890 architecture pointed outward);
  live in-call compliance sentry (diffusion-speed-specific); living
  systematic reviews.
- Tier 3 (real, no wedge): e-discovery, small-platform moderation,
  localization QA, accessibility audits.

### F4 — Design rule recurring in both runs
Every buyer-grade variant demands: per-judgement stamp (source span, prompt+
model version, confidence), disagreement recorded, humans see exceptions only.
= `artifact_carries_code_identity` seed + evidence-span boundary, already
debugged in-repo.

## Convergence analysis (runs 3–5 executed 2026-08-26; claims below
## reconciled against raw outputs — top-picks read + theme-term frequency grep)

### Convergent classes — recurred across ≥3 independent runs

| Class | Runs | Convergent form |
|---|---|---|
| **Exception-first human review** (machine prepares, human adjudicates; humans see only contested/high-risk items) | 1 (quorum triage, escalation adjudicator), 2 (explainable adjudication stack — top pick, exception-first operating model), 4 (appeal paths ×3, one-click bureaucratic escalation — top pick), 5 (**meaningful veto rights** — top pick: "human-in-the-loop fails when humans are decorative") | Five of five runs. The census never auto-acts; it *re-ranks the human queue*. Run 5 sharpens it: oversight must carry stop/override/ban authority or it is decoration. |
| **Evidence-stamped decision ledger** (source span + prompt/model version + confidence per judgement) | 1 (C1S5 decision ledger — ⭐5), 2 (confidence-weighted ledger, evidence-linked extraction — ⭐5), 4 (evidence packets/checklists for civic escalation), 5 (audit trail as defense) | The audit trail is not a feature — it is the product. Regulated buyers pay for the reduce layer. |
| **Confidence-banded routing with abstention** | 1 (multi-pass quorum), 2 (adaptive confidence router), 3 (escalation on confidence), 5 (**cost-sensitive abstention** — top pick: refuse to decide when error downside is too high) | Abstention must be a first-class output of every cheap call; run 5 adds the harm-weighting: the abstention threshold scales with the cost of being wrong, not a fixed confidence number. |
| **Real-time interposition** | 2 (live compliance sentry, in-the-moment QA coach), 3 (entire run: **"semantic middleware between intent and commitment"** — before-send/before-click intercept as its #1 pick, transactional guardian #2, per-keystroke autocomplete #3), 4 (real-time obligation/scam scanning) | Run 3 names the category better than any prior formulation: the product sits between *intent and commitment*. Diffusion-speed-specific; batch cannot compete. |
| **Census-reveals-the-tail ROI demo** | 1 (always-on sentry over previously unwatched streams), 2 (sampling-to-census conversion product + defect atlas — "prove ROI by showing hidden defect rates in the previously unreviewed tail"), 4 (bureaucratic-obligation census over a person's whole document pile) | The sales motion converges: replay the archive, price the previously invisible defect rate. |

### Two-run candidates (watch list, not yet convergent)
- **Individual-as-auditor** (run 4's distinctive cluster: selective disclosure
  vault — top pick, deadline/obligation scanner, one-click escalation;
  echoed only weakly by run 3 consumer surfaces). Civic-specific twist:
  privacy-preserving *selective disclosure* — help without surrendering the
  full corpus — did not appear in any enterprise-angle run.
- Drift/novelty ingestion filters (runs 1, 2) — real but commodity-adjacent.

### Run 5 (forced opposite) — boundary conditions
- **Correlation-aware aggregation** (run 5's #1 pick): N cheap calls from one
  model are not N independent witnesses — "fake consensus from model
  monoculture." Quorum schemes from runs 1/3 overstate independence;
  persona/prior diversity (FR-890's orthogonal seats) or cross-model
  ensembles are the honest forms.
- **Wrong tool where the item does not carry its answer** (the FR-888
  `prediction-over-undecidable-input` class): no confidence band fixes an
  undecidable item. Move the boundary instead. (Echoes run 0 anti-candidates.)
- **Deny-path prohibition generalizes outward**: a cheap judgement may
  *delay or route*, never *irreversibly deny* (benefits, moderation,
  medical) — run 4 independently demanded appeal paths before run 5 named
  the hazard.
- **Metric-collapse risk**: census output tempts unread dashboards;
  `read_raw_output_first` applies to customers too — deployments need a
  K-raw-samples-read gate or the census becomes compliance theatre
  (`gate_checks_shape_not_substance` at market scale).

## Verdict after convergence

The five-run convergent product shape is ONE architecture:
**census fan-out → evidence-stamped, abstention-capable, correlation-aware
reduce → exception queue with real human veto authority → real-time
(intent-to-commitment intercept) variant where latency permits.**
This is the FR-890 research-route architecture plus the FR-727/730 boundary
machinery, pointed at an external corpus. The repo has already built and
debugged every component except two named gaps the runs surfaced:
cost-sensitive abstention (confidence thresholds today are fixed, not
harm-weighted) and correlation-aware aggregation (no cross-model or
cross-persona independence accounting in any current reducer).

Recommended wedge (asset-proximity × convergence): contact-center census QA
(Tier 1 asset, hits 4 of 5 convergent classes; the run-3 "intent-to-
commitment" real-time coach is its natural v2). Next step: closed problem
brief through `scripts/research.sh` for the wedge — the librarian persona
supplies the "how does the world do call QA today" precedent row this
document lacks.

## Product candidates (2026-08-26, distilled from convergence × asset proximity)

Table stakes for every candidate — the convergent architecture, non-negotiable:
evidence-stamped ledger (span + prompt/model version + confidence per
judgement), cost-sensitive abstention, exception-first queue with real human
veto, correlation-aware aggregation, appeal path wherever a judgement can
disadvantage a person. A candidate that drops one of these re-enters run 5's
failure catalogue.

### P1 — CallCensus: 100% contact-center QA *(recommended wedge)*
- **Buyer:** contact-center ops/compliance lead. Today they QA 1–3% of calls
  by hand.
- **What:** per-turn mercury classification of every call/chat (script
  adherence, mandated disclosures, resolution, escalation misses); code
  aggregates into agent/queue/period views; humans review only exceptions.
- **Wedge sale:** the census-reveals-the-tail motion — replay one month of
  the customer's archived calls, hand them the defect atlas sampling missed.
  Priced in tens of euros of tokens.
- **Assets:** ninchat_voice per-turn checker lineage (NC-388 boundary
  lessons), csap platform, live customer relationship. **Gap:** none
  structural — packaging and a reporting surface.
- **v2:** the run-3 intercept — real-time whisper coach during the call
  (diffusion latency makes it possible; advise-only, never deny-path).
- Hits 5/5 convergent classes. **Effort: weeks, not quarters.**

### P2 — CodingProof: clinical coding census & audit
- **Buyer:** primary-care organizations, national registries, insurers —
  anyone whose ICPC-2/ICD coding quality is audited by sampling today.
- **What:** re-code historical encounter corpora; diff against recorded
  codes; evidence-linked discrepancy report with abstention on undecidable
  entries (the junk-drawer-cap discipline prevents false confidence).
- **Assets:** icpc-2-rfe classifier + the FR-722/727/730 machinery (span
  repair, cap lists, verdict-inflation cures) — the hard 80% already
  debugged against real rubrics. **Gap:** regulatory/procurement cycle;
  healthcare-pilot facts must stay out of this public repo (FR-874).
- **Moat:** the boundary machinery is incident-priced knowledge competitors
  must re-buy with their own failures.

### P3 — OpenCoder: open-text survey coding service
- **Buyer:** market-research firms, HR engagement platforms, public
  consultations — open-text coding is a manual human industry.
- **What:** upload responses + taxonomy → coded dataset with evidence spans,
  confidence bands, disagreement rows, exception list for human coders.
- **Assets:** questionnaire-api sibling; classifier architecture is FR-884
  off the shelf. **Gap:** none technical; nearest to self-serve SaaS of all
  candidates — smallest integration surface (CSV in, CSV out).
- **Sharpest ROI story:** human coding costs ~€1–3/response; census coding
  costs ~€0.001.

### P4 — FactGuard: semantic DLP *(the genuinely new category)*
- **Buyer:** security/compliance teams. Classic DLP is regex/fingerprint;
  it cannot catch a leak of *fact* ("the pilot has no identity check") —
  the FR-874 finding, productized.
- **What:** map over every outbound artifact (doc, commit, ticket, deck) →
  per-span fact-leak judgement against a customer-defined sensitivity
  policy; fail-closed pre-publish gate with human release override.
- **Assets:** memory-curation graph is the embryo; the selective-amnesia
  judgement design (keep/redact/forget with audience as input) is the
  product spec. **Gap:** policy-authoring UX; false-positive floods are the
  run-5 death mode — cost-sensitive abstention is load-bearing here.
- **Risk/reward:** highest novelty, no incumbent category; also the least
  validated demand.

### P5 — SendGuard: intent-to-commitment intercept API
- **Buyer:** platforms and regulated firms (financial advice, healthcare
  comms) embedding a before-send/before-click semantic check.
- **What:** run 3's #1 pick — millisecond middleware between user intent
  and commitment: flags non-compliant advice, missing disclosures, wrong
  recipient/attachment *before* send. Advise-and-delay only, never deny.
- **Assets:** diffusion-latency know-how; csap as first embedding surface.
  **Gap:** this is an API business, different muscle than the census
  products; strongest as P1's v2 rather than standalone.

### P6 — Adjudicator: exception-first case-review stack
- **Buyer:** insurers, public agencies, platforms with appeal queues.
- **What:** machine prepares the evidence packet (per-document cheap
  judgements, ledger, disagreement preserved); human adjudicates with
  logged veto. FR-890's architecture pointed at a customer's case corpus.
- **Gap:** longest sales cycle, deepest workflow integration; a Tier-2
  follow-on once P1/P3 prove the ledger primitives commercially.

### P0 family — corpus cartography (operator additions, 2026-08-26)

P0 generalizes: *distill a corpus the org already owns into a navigable
model*. Same architecture (crawl/enumerate → per-item cheap distillation →
code-assembled map + index), different corpus:

- **P0a — Document-library summarizer (PDF census):** per-page/per-window
  mercury summarization over PDF libraries (contracts, manuals, reports,
  tenders) → library index + per-document abstracts + RAG feed. In-repo
  v0: `examples/demos/book-summary` (page-windowed PDF summary with
  manifest tools, map fan-out, reducer accumulation) — the graph already
  exists; the product is pointing it at a folder instead of a book.
- **P0b — Enterprise-architecture cartographer:** map over a corp GitHub
  organization (the "repo garden") → per-repo distillation (purpose,
  stack, interfaces, dependencies, activity, owners) → code-assembled
  architecture map nobody currently maintains by hand. In-repo v0s:
  `reference/module-map.md` generator (single-repo), diary_index,
  fr-atlas. Buyer: any org whose architecture documentation is stale by
  definition — i.e. all of them. Caveat: output is corp-confidential by
  nature; ownership/visibility check before any committed artifact.

### The time axis (operator addition — a dimension, not a use case)

Every candidate so far treats its corpus as a SNAPSHOT. Adding time as
the map axis turns census into **trend census**: the same per-item
judgement over a time-ordered corpus, reduced into drift/trajectory.

- **Git history analysis** (the exemplar): map over PRs/commits →
  per-item classification (intent, risk, subsystem, review depth,
  incident linkage) → engineering-health timeline: where complexity
  accretes, review coverage drifts, which subsystems eat incidents.
  In-repo precedent: `scripts/extract_fr_graph.py` (FR causal DAG),
  fr_board, chronicle session mining, incident_density_ranking (the
  Scripture cure IS a time-axis census done manually).
- Generalizes across the P-series: call QA over quarters (agent drift),
  coding quality over years (P2's strongest sales artifact — show the
  drift), policy compliance before/after a rule change.
- Convergence link: the run-6 top pick "real-time drift radar" is this
  dimension at streaming timescale; git-PR analysis is the same product
  at repository timescale. One reduce layer, two clock speeds.

### Deprioritized (real, no wedge from here)
ObligationRadar (run-4 civic scanner — govtech/nonprofit funding model, not
this portfolio), LivingReview (guideline bodies; tiny market), e-discovery,
small-platform moderation, localization QA.

### Portfolio logic
P1 → P3 → (P5 as P1-v2) share one reporting/ledger core and prove the
architecture commercially; P2 rides the same core into the regulated-vertical
moat when the procurement window opens; P4 is the venture-grade bet funded
by the others. Build the ledger/reduce core ONCE — it is the actual product;
verticals are configuration.

## Post-mortem: the absent candidate (operator ground truth, 2026-08-26)

The operator's intended acceptance case — **site mapper / summarizer → RAG
ingestion** (crawl site, cheap-summarize every page, code-assemble sitemap +
retrieval index) — never surfaced in five runs or six product candidates.
The misses, in causal order:

1. **The pattern definition contaminated every "independent" run.** I froze
   the pattern as *one-JUDGEMENT-per-call* (classify/score/extract/verify)
   in the diary, then pasted that enumeration into all five domain strings.
   Summarization/distillation — a *transformation* per item, not a
   judgement — was excluded by enumeration before any run started. The five
   angles varied the MARKET, never the OPERATION CLASS. The convergence was
   partly pseudo-convergence: five witnesses sharing my prompt DNA are not
   five witnesses (`are_the_witnesses_one_phenomenon`).
2. **Wrong instrument for the framing risk.** innovation_matrix is ONE
   monolithic call with one prior — mine, injected via the domain string.
   The research-route exists precisely to break the author's framing with
   orthogonal personas — I cited it as "next step" in every summary and
   never fired it. The FR-890 lesson applied recursively: the brief
   author's framing IS the contamination, and I was the brief author.
3. **No web grounding in any run.** All five runs were ungrounded model
   ideation. RAG ingestion is the world's #1 actual use of cheap map-reduce
   (embedding pipelines, crawl-and-index services) — one librarian search
   would have returned it instantly. Compounding: run 2's framing demanded
   "NEW value / NOT developer tooling," filtering out the biggest existing
   market instead of asking "which existing practice does this pattern
   commoditize."
4. **Run 0 inventoried by count, not by task shape.** The map census
   *contained* fi_domain_crawl ("Crawl .fi domains and produce
   sitemap-style overviews" — the site mapper, verbatim), diary_index, and
   book-summary. I extracted one fact (model pinning) and discarded the
   shape taxonomy. `inventory_by_visibility` in a new costume: ranked by
   economics, blind to operation class.
5. **The absent stakeholder: the machine consumer.** Every angle assumed a
   human reviewer/buyer consuming judgements. RAG's consumer is another AI
   system — corpus distillation as infrastructure for retrieval never had a
   seat at the table.

### Correction to the candidate list

**P0 — SiteScribe: crawl → per-page mercury summary/entity extraction →
code-assembled sitemap + RAG-ready index.** Buyer: anyone deploying a
retrieval assistant over their own site/docs/intranet. In-repo assets:
fi_domain_crawl (the demo IS v0), web-research toolbelt, diary_index and
book-summary as corpus-distillation siblings. This is also the correct
*acceptance test* for the pattern itself: obviously parallel, cheap per
item, deterministic assembly, immediately checkable output (does the map
match the site?). It precedes P1–P6 as validation, and unlike them it
requires no customer relationship to test today.

### The governing mechanism (operator, 2026-08-26): the hidden canary

The real defect was not the framing details — it was that **open-ended
ideation calls carry no falsifier**. Any fluent matrix output looks like
research; there is no error signal. The cure is a positive control, lab-
science style: the run initiator holds a **canonical known-true answer**
(here: site mapper/summarizer → RAG, the pattern's textbook use), withheld
from every prompt. After the run, code checks the artifact for the canary
class. **Absence falsifies the entire run** — if the framing filtered out
the answer everyone knows, it filtered unknown candidates too. "Ideas
haven't been researched if this one is not in."

Properties:
- The canary must be HIDDEN from the instrument (in the prompt it becomes
  contamination — leading the witness).
- Recall of the canary validates the run; it says nothing about the novel
  rows (necessary, not sufficient).
- It is the ideation-domain resolution of `gate_checks_shape_not_substance`:
  a substance check that CODE can perform, because the initiator knows one
  true answer in advance.
- Precedent already in-repo, unrecognized as general: FR-890 AC-09/D-9 ran
  the FR-888 brief and checked whether the OS-permissions class surfaced
  without operator help — a one-off canary. Second occurrence today
  (site-mapper absent from five runs). Recurrence bar met.

Applied retroactively: runs 1–5 fail the canary test. Their convergence
table stands only as a catalogue of *hypotheses*; the study must be re-run
canary-gated before the candidate ranking is trusted.

### Methodological amendments (subordinate input-side hygiene)
- Vary the **operation class** (judge / transform / generate / retrieve)
  across ideation runs, not just the market.
- At least one run must be **web-grounded** (librarian seat) — ungrounded
  convergence is convergence of the model's priors with my framing.
- Inventory step must output a **task-shape taxonomy** of existing graphs,
  not only counts and models.
- The dual question is mandatory: not only "what new value" but "which
  existing practice does this commoditize."

## Rounds 6–8: first canary-gated rounds (2026-08-26)

Canaries precommitted in `canaries-rounds-6-8.md` BEFORE the runs, absent
from all prompts. Verdicts from raw-read of full matrix tables:

- **Run 6 (web) — CANARY FAIL.** 25 cells of extraction, monitoring,
  triage, provenance, drift detection — and the site-summarizer→retrieval-
  index class is absent EVEN FROM A WEB-SPECIFIC RUN. Canary B (whole-site
  content audit) also absent as a named product (closest: "web change
  auditor", which explains deltas, not quality). Novel rows are hypotheses
  only.
- **Run 7 (machine consumer) — PARTIAL.** The CLASS surfaced (C1 "cheap
  large-scale semantic compression … machine abstracts per entity",
  "dual-layer compression: machine-readable summary + gloss") but the
  canonical ARTIFACT FORM (llms.txt-style published site summaries,
  site→knowledge-graph services) never appeared as a candidate.
- **Run 8 (grounded) — INVALID, and independently valuable.** The
  search_web call failed before executing; the web-research demo graph
  **failed open**, emitting a fluent knowledge-cutoff market map with zero
  URL citations (verified: all 7 `http` hits in the artifact are API log
  lines). Exit code 0. This is a live witness for FR-890's R-4 fail-closed
  librarian design — and a defect in the shipped demo
  (`examples/demos/web-research`): Commandment 6 violation, silent
  fallback. Notably the model CONFESSED in-text; only the artifact read
  caught it — exit-code trust would have laundered it.

### The new finding: instrument bias explains the canary failures

Run 8's ungrounded text — mere recall of world knowledge — named the canary
immediately ("chunk content … generate embeddings for search/retrieval …
knowledge base indexing, document ingestion"). The same model that cannot
surface RAG ingestion inside an innovation matrix produces it instantly
when asked what the world DOES. The canary failures are not (only) framing
leaks: **the innovation_matrix instrument is structurally biased toward
novelty and against the canonical** — "innovation" framing suppresses
textbook answers by definition. Consequence: an ideation study is a PAIR of
instruments — a divergent generator AND a practice-grounded librarian — and
the canary gates the pair, not either alone. The research-route already has
this shape (personas + librarian); innovation_matrix alone never will.

### Additions to convergence tallies (runs 6–7 evidence)
- Evidence-stamped ledger: now 6 runs (run 6 "provenance graph builder" —
  top pick; run 7 provenance rows in every capability family).
- Exception-first review: now 6 runs (run 6 "exception-only workbench" —
  top pick).
- **Drift/change monitoring promoted from watch list to convergent**: runs
  1, 2, 6 ("real-time drift radar" — run 6 top pick) — price/policy/
  content change census over monitored sites.
- New two-run candidates: page/corpus→structured-object conversion
  (runs 6, 7), schema-validation loops — LLM proposes, code validates
  (runs 6 "consensus reducer", 7 top pick; also the house pattern itself).

## Round 8 redo (2026-08-26, post-FR-891)

The fail-open defect was fixed under FR-891 (fail-closed agent tool
boundary; judgement-approved). Evidence pair:

- **ddgs absent** (`runs/run-grounded-redo-ddgs-absent.txt`): exit 1, no
  summary — `AllToolCallsFailedError: Agent node 'research': all 3 tool
  call(s) failed … first failure: Error: ddgs not installed`. The run 8
  incident class is now mechanically impossible.
- **ddgs present** (`runs/run-grounded-redo.txt`): exit 0, live search
  executed, 26 non-log URL citations in the artifact. Grounded canary
  (commercial crawl-and-index practice) satisfied: the summary names real
  prior art with URLs. Command: `yamlgraph graph run
  examples/demos/web-research/graph.yaml --var topic="Commercial services
  and open-source tools …" --full`.

## Rounds 9–11: operation-class axis + trustworthy grounding (2026-08-26)

Canaries precommitted in `canaries-rounds-9-11.md`. First rounds run AFTER
FR-891 made the grounded librarian fail-closed — run 10 is the study's
first trustworthy web-grounded round.

### Canary verdicts
- **Run 9 (TRANSFORM class, `runs/run-transform.txt`) — PARTIAL.** The
  localization/translation canary surfaced as a cell ("policy-aware
  localization engine", ⭐5) but not as the named whole-book/catalog
  market. Top picks: audit-native transformation system, audience-safe
  mass personalization, compliance-safe rewriting/redaction.
- **Run 10 (grounded commoditization, `runs/run-grounded-commoditization.txt`)
  — PASS.** Firecrawl named 21×, plus Apify, Diffbot, Zyte, Browse AI,
  Unstructured, Crawl4AI; 36 URL-bearing citations, real pricing.
  (First attempt hung: all search engines timed out and ddgs blocked in
  its thread pool with no overall timeout — a NEW defect class the FR-891
  boundary does not cover: bounded against errors, unbounded against
  hangs. The demo declares no node `timeout:`; FR-069 exists unused.
  Seed for a follow-up fix. Retry after network recovery succeeded.)
- **Run 11 (GENERATE class, `runs/run-generate.txt`) — PASS.** "Synthetic
  data marketplaces" (schema-conformant records for training/testing)
  surfaced as a ⭐5 cell — the canary recalled.

### What the grounded round adds (market facts, cited in-artifact)
- The market has three layers: web-to-LLM ingestion (Firecrawl, Apify,
  Diffbot, Zyte, Crawl4AI), document intelligence (Textract ~$0.07/page,
  Google DocAI $0.65–30/1k pages, Unstructured ~$0.03/page, Hyperscience,
  Rossum, ABBYY), and general LLM APIs (commodity).
- **Nobody in the named market sells the evidence-stamped reduce layer.**
  Incumbents sell ingestion (getting data OUT of pages) and OCR-grade
  extraction; the convergent census products sell *judgement with audit
  trail*. Mercury-class semantic judgement prices BELOW incumbent
  OCR/extraction per-page rates — semantic processing at OCR prices is
  the quantified wedge. This grounds the F2/portfolio thesis ("the reduce
  layer is the product") in named-competitor pricing for the first time.

### Convergence updates
- Evidence-stamped ledger/provenance: now ~7 of 8 valid runs (run 9's #1
  pick is literally "audit-native transformation system").
- NEW two-run class: **mass personalization** (run 9 audience-safe
  personalization; run 11 composable assembly lines / personalized
  catalogs) — per-audience variants of one artifact at near-zero cost.
- NEW coupling insight (run 11): "evaluation is the bottleneck of cheap
  generation" — hybrid scoring stacks. Generate-class markets create
  demand for judge-class products; the P-series census/QA products are
  upstream of every generation market. The portfolio is self-reinforcing.
- P4 (semantic DLP) reinforced from the transform side: compliance-safe
  rewriting/redaction is its rewrite-mode twin (detect → redact is one
  product with two verbs).

## The pattern, fleshed out (operator reflection, 2026-08-26): discover–extract–map–reduce

Eleven rounds and the P0-family additions expose that "cheap-map,
code-reduce" under-describes the pattern. Every witness instance is FIVE
stages, and the census products are all the same pipeline with two
sockets swapped:

| Stage | What it does | Who supplies it | Witness examples |
|---|---|---|---|
| **Discover** | Enumerate the corpus into items | **USER (socket 1)** | crawl .fi domains; list PRs; walk PDF pages; list org repos; fetch RSS feeds; list prompt files |
| **Extract** | Get one item's content, boundary-normalized | **USER (socket 2)** | fetch page; git show; read page window; read repo manifest |
| **Map** | One cheap judgement/transform per item | pipeline (pinned mercury/haiku, `on_error: skip`, abstention) | classify theme; score relevance; summarize page; label PR |
| **Reduce** | LLM-free fail-closed aggregation + evidence ledger | pipeline (the sellable IP) | count/threshold; schema-validate; disagreement rows; citation checks |
| **Tail** | ≤1 expensive synthesis, or none | pipeline (optional) | group themes; diary entry; sitemap |

Decomposition check against in-repo witnesses: prompt_theme_analyzer
(list_prompts / inline read / classify / aggregate / group), diary_digest
(feeds / fetch / score / filter / write), book-summary (manifest / page
window / summarize / accumulate / —), fi_domain_crawl (crawl / fetch /
summarize / sitemap / —), icpc2+cwe classifiers (dataset rows / — /
classify / score / —). **Five instances, zero shared code**: each
re-authors the map/reduce skeleton by hand, and only discover+extract
genuinely differ. The pattern name that should be codified:
**discover–extract–map(mercury)–reduce** — a prebaked analysis pipeline
with user-supplied discovery and extraction tools.

### The codification implication: tool passing

- The tool-declaration FORMAT already exists: FR-768 tool manifests
  (`manifest:` key; typed shell/python/graph runtimes; translation-only,
  existing runtimes execute). A discovery tool or extraction tool is
  exactly one manifest file.
- The MISSING capability is invocation-time binding: graphs declare tools
  statically at load; there is no `--tool discover=./crawler.manifest.yaml`
  style injection into a shared pipeline graph. Today the only reuse
  routes are copy-the-graph (drift, witnessed 5×) or graph-as-tool
  composition (FR-658/CAP-111 — inverts the ownership: the user writes
  the outer graph, which is the skeleton re-authoring problem again).
- Codification therefore = one parametric `corpus_census` pipeline
  (pinned map model, frozen reduce/ledger schema, canary/abstention
  hooks) + manifest injection at invocation. The P-series verticals and
  the P0 family become CONFIGURATIONS: a discovery manifest, an
  extraction manifest, a rubric prompt, a reduce schema.
- Doctrine route: closed problem brief → `scripts/research.sh` → FR
  (filed as `feature-requests/research-briefs/corpus-census-skeleton-reuse.md`).

## Status & next steps (as of 2026-08-26, after round 11)

**State:** 11 rounds + repo census. Canary discipline active since round 6
(scoreboard: 6 FAIL, 7 partial, 8 invalid→redone PASS, 9 partial, 10 PASS,
11 PASS). Rounds 1–5 remain a hypothesis catalogue — never canary-gated.
Instrument pair established: divergent generator (innovation_matrix) +
fail-closed grounded librarian (web-research, post-FR-891); the canary
gates the pair. Product candidates P0–P6 stand; the reduce-layer thesis is
now grounded in named-competitor pricing (round 10).

**Open options, ranked:**
1. **Write the P1 wedge brief** (contact-center census QA) and run it
   through `scripts/research.sh` — the study's own recommendation, twice
   deferred; eleven rounds in, marginal ideation yield is falling and
   `builders_never_call` now applies to this study's own conclusions.
2. RETRIEVE operation-class round — the last unexplored verb (canary
   candidate: RAG re-ranking / retrieval filtering with cheap per-chunk
   relevance judgements).
3. Re-run rounds 1–5 canary-gated to upgrade the convergence table from
   hypothesis to evidence (cheap, but mostly confirms what 6–11 already
   re-witnessed).

**Named capability gaps awaiting FRs:** cost-sensitive abstention;
correlation-aware aggregation; agent tool-call hang bound (run-10 incident
— FR-069 per-node timeout exists unused; FR-891 bounds errors, not hangs).

**Pending elsewhere:** `.chaplain/inbox/canary-recall-gate-for-ideation-runs.md`
(graduation proposal); cheap_map_code_reduce Scripture entry waits for the
philosopher commit (4th witness) to land from the concurrent device.

## Sources
- Raw run artifacts preserved in `docs/mercury-census/runs/`:
  `run-mercury.txt` (1), `run-outward.txt` (2), `run-latency.txt` (3),
  `run-civic.txt` (4), `run-inverse.txt` (5), `run-web.txt` (6),
  `run-machine.txt` (7), `run-grounded-FAILED-OPEN.txt` (8),
  `run-transform.txt` (9), `run-grounded-commoditization.txt` (10),
  `run-generate.txt` (11) — .txt because `*.log` is gitignored; rounds
  1–8 were silently excluded from PR #478 by that rule and recovered
  here (dangling-evidence defect, the study's own
  `gate_checks_shape_not_substance` class).
- Canary precommitments: `canaries-rounds-6-8.md`, `canaries-rounds-9-11.md`,
  `canary-fr-891.md`
- diary 2026-08-26-cheap-map-code-reduce-the-mercury-pattern.md
- docs/analysis-fr888-post-mortem-2026-08-25.md (the priced counter-case)
