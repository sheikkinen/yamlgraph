# Development Diary

Metacognitive reflections on development process.

---

## 2026-02-17: FR-030 — Completionism Bias

**Context:** Needed to confirm `mode=invoke` subgraphs stream tokens with `subgraphs=True`.
**What I did:** Spent hours reading LangGraph source (`StreamMessagesHandler`, namespace filtering, callback propagation). Built a mental model. Concluded async conversion was needed. Drafted implementation plan.
**What I should have done:** Run a 10-line test. Would have taken 2 minutes.
**Root cause:** Encountered unfamiliar code → triggered "must understand everything" instinct → skipped empirical validation. This is **completionism bias** — the urge to build complete mental models before acting.
**The trap:** When asking "does X work?", the answer is a test, not source code. Source diving is for "why doesn't X work?" *after* the test fails. I confused investigation types.
**Correction:** The test passed. `subgraphs=True` already works. Phase 2 marked "Not Needed." Research was intellectually satisfying but operationally wasteful.
**Heuristic:** Before reading source, write the question as a test. If the test passes, stop. If it fails, *then* investigate.

---

## 2026-02-17: Building the Diary — Meta on Meta

**Context:** Created this diary file and the "Distill" step in the Sermon.
**What I did:** First draft was verbose (full narrative). Revised to structured format (context/did/should/cause/trap/correction/heuristic). Changed "Reflect" to "Distill" after noticing "reflect" is overloaded AI-speak.
**Insight:** Naming instructions matters. A unique verb ("Distill") signals intent better than a generic one ("Reflect"). The word should name the *posture*, not describe the action.
**Trap avoided:** Almost made the diary performative (writing for the diary, not for insight). The friction test helps: if it's tedious to document *during* work, question whether it's worth capturing.
**Heuristic:** When naming workflow steps, prefer uncommon verbs. Generic instructions get ignored; distinct ones get remembered.

---

## 2026-02-17: FR-038 — Analysis Momentum

**Context:** Reviewed QA architecture (pre-commit, CI, Scripture). Identified gaps between doctrine and practice.
**What happened:** After listing gaps (no security scanning, CI triggers late, docs/adr/ unused), immediately proposed solutions. Then caught myself: *I had just violated the Plan-Judge-Enforce sequence while analyzing the system designed to enforce it.*
**The trap:** **Analysis momentum** — once gaps are identified, the urge to "fix them" bypasses deliberation. The gap list becomes a to-do list by inertia, not by judgment.
**Correction:** Stopped. Labeled proposals as "observation, not prescription." Created FR-038 only after explicit prompt to do so. Followed Plan → Judge → Enforce properly for the commit hook.
**Second insight:** Doctrine contained dead references (`docs/adr/`, `docs/epics/`, `purgatory/`). 31 feature requests exist; 2 ADRs. Practice had diverged. Updated Scripture to match practice, not aspirations.
**Heuristic:** Gap identification is observation, not prescription. Stop after analysis. Let the gap sit. If it matters, it will return as a real problem — and then follow the rite.

---

## 2026-02-17: FR-039 — The Bug That Wasn't

**Context:** FR-039 claimed `__pregel_send` is "sync-only" and returns `None` under `astream()`. The fix options ranged from warning logs to async variants.

**What I did:** Instead of implementing Option B (the "safe" warning-only fix), I investigated. Wrote a test script, checked LangGraph 1.0.6 internals. Discovered:
1. `__pregel_send` is NOT `None` under async — empirically proven
2. The log `FR-006: Subgraph mapped state` fires, confirming `send()` IS called
3. The "missing state" is a stream mode issue: `stream_mode="updates"` excludes accumulated state; `stream_mode="values"` includes it.

**What the original FR author did wrong:** Observed symptom ("state missing after astream"), reasoned from documentation/memory ("pregel_send is sync-only"), concluded bug exists. Never wrote a test to verify the assumption.

**The trap:** **Armchair debugging** — using mental models instead of empirical tests. The symptom was real (state missing), but the diagnosis was wrong (assumed `send=None`). A 10-line test would have shown `send` is available.

**Second trap narrowly avoided:** I almost just implemented Option B. Had I added a warning log without investigating, the warning would NEVER fire (because `send` is never `None`). The "fix" would have been no-op code, creating false confidence.

**Why the bug report seemed plausible:** The FR cited the log line as evidence: "FR-006 log fires, but send IS None." In hindsight, this was a red flag — if the log fires, the code REACHED the send() call. The author confused "state not visible" with "state not sent."

**Correction:** FR-039 closed as "Not a Bug." The actual fix is consumer education: use `stream_mode="values"` or `ainvoke()` for interrupt workflows.

**Heuristic:** When a bug report includes technical claims about internals ("X is None under Y"), verify the claim with a test before designing fixes. The symptom might be real while the diagnosis is wrong.

**Meta-heuristic:** Bug reports that propose solutions are often wrong about root cause. The solution-space narrows prematurely around a false hypothesis. Start from symptoms, not proposed fixes.

---

## 2026-02-17: Vuosikello Slot Matching — The Boundary Between Code and LLM Output

**Context:** Psykologia PS1 lesson plans showed random semester assignments (Y1-Y3 syksy/kevät scattered across PS1 topics). User reported "timing seems random." Duration (75 min) and session types were correct.

**What happened:** `load_data.py` filtered vuosikello slots with exact match: `s.get("module","").upper() == module_upper`. But the LLM-generated vuosikello had full module names like `"PS1: Toimiva ja oppiva ihminen"` instead of bare `"PS1"`. Exact match returned 0 results → fallback to ALL slots → round-robin across all 6 semesters for PS1 topics.

**The trap:** **Schema-code impedance mismatch.** The extraction prompt's schema defines `module` as a string field with description "Module code". The code assumes bare codes (`PS1`). The LLM interprets "module code" as the full identifier. Neither is wrong in isolation — the bug lives in the gap between what the LLM produces and what the code expects.

**Why it wasn't caught earlier:** The fallback `if not module_slots: module_slots = slots` was designed as a safety net but silently masked the real failure. With 0 matches, all slots became candidates, producing plausible-looking but incorrect output. No error, no warning, just wrong data — the hardest bug class.

**Second insight:** Dead code detected. `_assign_vuosikello_slot()` function was never called — the logic had been inlined into `load_data()` during a refactor but the old function was left behind. The dead function still had the old `==` match, so even if someone called it, the bug would persist.

**Fix:** Changed to `.startswith(module_upper)` — tolerant of both `"PS1"` and `"PS1: Toimiva ja oppiva ihminen"`. Removed the dead function. Added test G18 that uses the LLM output format. 29/29 GREEN.

**Heuristic:** When code consumes LLM output, use tolerant matching (prefix, contains, regex) rather than exact equality. LLMs are creative with formatting even within structured schemas. The contract should be "starts with the expected code" not "equals the expected code."

**Meta-heuristic:** Silent fallbacks that produce plausible output are worse than loud failures. A `KeyError` would have surfaced this bug on first run. The "defensive" fallback hid it across 20 lessons.

**Graduated to Scripture:** Extended Commandment 6 — "Thou shalt not hedge with silent fallbacks; when a filter yields nothing, raise — never substitute everything." Evidence: two instances in same project (project_dir default, vuosikello fallback), both producing plausible-but-wrong output that passed human review.

---

## 2026-02-17: Studying 81 Psykologia Lessons — The Mirror Test for Generative Pipelines

**Context:** Read 14 lesson plans across all 5 psykologia modules (PS1–PS5, 81 lessons total, 68,733 words). Sampled first, middle, and last lessons from each module. Performed structural, quantitative, and thematic analysis.

### Quantitative Portrait

| Module | Lessons | Words | Words/Lesson | Semester |
|--------|---------|-------|-------------|----------|
| PS1 | 20 | 17,085 | ~854 | Y1 syksy |
| PS2 | 15 | 12,933 | ~862 | Y1 kevät |
| PS3 | 18 | 15,477 | ~859 | Y2 syksy |
| PS4 | 11 | 9,164 | ~833 | Y2 kevät |
| PS5 | 17 | 14,074 | ~827 | Y3 syksy |
| **Total** | **81** | **68,733** | **~849** | |

Word count is remarkably consistent (~827–862 per lesson). This is a property of the LLM's output length calibration with the prompt rather than intentional quality control.

### Structural Consistency

Every lesson has `## TAVOITTEET` (81/81), `## ARVIOINTI` (81/81), `## ERIYTTÄMINEN` (80/81). The 75-minute time budget is universally honored. Session types rotate correctly: luokkaopetus → työpaja → pienryhmä → vierailu → verkko. The biopsykososiaalinen framework appears 94 times across all content — it's the unifying lens.

### Quality Assessment: What Works

1. **Pedagogical structure is sound.** Each lesson follows: activate → teach → practice → reflect. Bloom's taxonomy is implicitly present (remember → understand → apply → analyze).

2. **Differentiation is built in.** Every lesson has three tiers (syventävä / perus / tukea tarvitsevat). This is rare even in human-authored lesson plans.

3. **Session type diversity is genuine.** Verkko lessons actually redesign for async (Padlet, Mentimeter, breakout rooms). Vierailu lessons name specific visitor types (Oulun yliopiston neurotieteilijä). Työpaja lessons include hands-on experiments (the muisti lesson's word-recall experiment is classroom-ready).

4. **Cross-module references exist.** PS3 muisti lesson references PS1 (aivojen plastisuus). PS5 kypsä ajattelu explicitly prepares for ylioppilaskoe. The curriculum spirals.

5. **Human-sensitive topics handled well.** PS2 identiteetti and PS4 mielenterveyshäiriöt consistently note "turvallisuus" and "ei pakoteta jakamaan henkilökohtaisia kokemuksia." PS5 konformisuus explicitly discusses when conformity is positive (liikennesäännöt) vs. negative (ryhmäpaine).

### Quality Assessment: What Doesn't Work

1. **Formulaic repetition.** Every openning follows the same pattern: "herättelykysymys" → pair work → plenum → teacher introduces objectives. After reading 10+ lessons, the rhythm becomes predictable. A real teacher would vary this.

2. **Phantom resources.** Lessons reference "Oulun yliopiston neurotieteilijä" or "TED-talk" without actual links or names. The materials table lists resources that don't exist. This is scaffolding that a teacher must fill.

3. **Time optimism.** The 75-minute budgets look tight. PS1 lesson 01 allocates 20 min for tutkimusmenetelmät (5 methods + critical evaluation + group work) — ambitious for first-year students. PS3 Kahneman lesson packs theory + 3 heuristiikat + personal reflection + peer feedback into 75 min.

4. **Vocabulary inflation.** Terms like "operationalisointi" and "akkulturaatioprosessit" are introduced without sufficient scaffolding for 16-year-olds. The eriyttäminen section promises "kielellinen tuki" but doesn't provide simplified definitions.

5. **Assessment is generic.** "Formatiivinen: havainnointi" appears in every lesson. The assessment criteria rarely go beyond "käsitteistön hallinta ja soveltaminen." No rubrics with specific point allocations (except PS2 identiteetti case analysis).

### Five Insightful Observations

**Observation 1: The Generator Is the Curriculum, Not the Lesson.**
The pipeline's real value isn't any individual lesson plan — it's the structural guarantee: every module has consistent pedagogy, timing, differentiation, and assessment. A human writing 81 lessons would inevitably drop quality in lesson 60. The generator maintains uniform scaffolding. The insight: treat the pipeline as a curriculum architect, not a lesson author. Teachers fill the content; the pipeline ensures no structural gap.

**Observation 2: LLM Output Calibration Creates False Uniformity.**
Every lesson is ~850 words. This isn't because each topic needs equal treatment — PS4's 75-minute mielenterveyshäiriöiden syvällinen käsittely genuinely needs more depth than PS1's 75-minute oppimisstrategiat intro. But the LLM produces similar-length output regardless. The prompt doesn't differentiate lesson complexity. Future improvement: add a `depth` parameter (introductory / intermediate / advanced) that adjusts expected output length and detail.

**Observation 3: The Biopsykososiaalinen Framework Is Both Strength and Weakness.**
It appears 94 times. As a pedagogical throughline across 3 years, it's excellent — students see human behavior from three lenses repeatedly. But it also becomes a crutch: every analysis task says "bio/psyyk/sosio" without pushing students toward novel frameworks. PS5's kypsä ajattelu lesson hints at this ("tiedon ristiriitaisuuden sietäminen") but doesn't introduce alternative models (ecological, phenomenological, evolutionary). The curriculum teaches one lens well; it doesn't teach lens-switching.

**Observation 4: The Pipeline Reveals What Teachers Actually Need — Not Lesson Plans, But Lesson Plan Skeletons.**
The generated plans are 80% structure (timing, methods, assessment, materials) and 20% content (actual questions, actual data, actual videos). A teacher can't use these as-is — the "tutkimustiivistelmä" in PS1 is a lorem ipsum placeholder, the case studies in PS5 are one-sentence sketches. But the structure is the hard part. Finding a 3-minute video about Asch's experiment is easy; designing a 75-minute lesson arc with proper differentiation is hard. The pipeline solves the hard problem and leaves the easy one. This is the correct division of labor.

**Observation 5: The Spiral Curriculum Works, But Only If Someone Connects the Spirals.**
PS1 teaches muisti as an intro (lesson 08). PS3 teaches muisti deeply (lesson 12, with experiment). PS4 connects it to emootiot. PS5 connects it to persoonallisuus via kognitiiviset vinoumat. The cross-references exist in the metadata but no "spiral curriculum map" is generated. A teacher needs a visual: "Here is how muisti appears across PS1→PS3→PS4→PS5, with increasing depth." This is a missing output artifact that the pipeline could generate — a concept progression map.

### The Meta-Trap

**Observation 6 (meta): Studying generated output creates the illusion of domain expertise.**
After reading 14 lesson plans about psykologia, I can discuss kaksoisprosessointiteoria, kiintymyssuhdetyypit, and Big Five with apparent fluency. But this is surface knowledge acquired through structural repetition, not deep understanding. The trap: confusing "I can describe the lesson plan about X" with "I understand X." This is exactly the arkipsykologia vs. tieteellinen tieto distinction that PS1 lesson 18 teaches. The generated content contains the warning about its own consumption pattern.

**Heuristic:** When a generative pipeline produces domain content, evaluate the pipeline's structural properties (consistency, coverage, differentiation), not the domain accuracy — you lack the expertise to judge the latter. Domain validation requires a domain expert reviewing samples, not an engineer reading all 81 lessons.

**Pipeline heuristic:** After generating content, produce a meta-artifact (concept map, spiral progression, gap analysis) that helps the domain expert navigate the output. Raw lesson files are infrastructure; the navigation layer is the product.

---

## 2026-02-17: The Constraint Shift — When Thinking Speed Approaches Infinity

**Context:** Stepped back from the psykologia lesson review to evaluate the entire YAMLGraph ecosystem: 10 generative pipelines (lesson generator, innovators toolkit, novel generator, storyboard, book translator, kertomus, NPC generator, yamlgraph-gen, questionnaire, feature brainstorm). Read all graph topologies. Counted: 109 python nodes, 91 LLM nodes, 16 map nodes across all graphs.

### The Inventory

| Pipeline | Nodes | Shape | What it generates |
|----------|-------|-------|-------------------|
| Lesson Generator | 3 | linear+map(50) | 81 lesson plans |
| Innovators Toolkit | 13 | 9-way diamond | Innovation reports (9 frameworks) |
| Novel Generator | 7 | multi-loop+map(20) | Short stories with quality gates |
| Storyboard | 3-5 | linear+map | Visual panels + images |
| Book Translator | 9 | 3×map+interrupt | Translated books |
| Kertomus | 14 | 2×map+7-way fan-out/in | Medical records from FHIR |
| NPC Generator | 5-10 | sequential+map | D&D characters + encounters |
| YAMLGraph Gen | 12 | linear cascade | YAMLGraph pipelines (meta) |
| Questionnaire | 7 | conversational loop | Feature request interviews |
| Feature Brainstorm | 1 | agent | Self-improvement proposals |

### The Repeating Patterns

**Pattern 1: Load → Map → Save**
Every generative pipeline reduces to the same skeleton: a Python node loads/transforms data, a map node fans out N parallel LLM calls, a Python node saves results. This is true regardless of domain:
- Lesson generator: `load_data → generate_lessons[map] → save_lessons`
- Book translator: `split_book → translate_all[map] → reassemble`
- Kertomus: `extract_fhir → generate_kertomus[map] → save_results`

The innovation matrix is the same pattern at a lower resolution: `cartesian → expand_all[map] → format_output`. The LLM does the "thinking." Python does the I/O shell. The map does the scaling.

**Pattern 2: Quality Gates Are Afterthoughts**
Only 2 of 10 pipelines have quality gates: novel generator (grade-based loop), book translator (score-based human review). Kertomus has `validate` (LLM-as-judge) but it doesn't gate — it's informational. The other 7 pipelines generate and save with no quality check. The lesson generator's 81 lessons go straight to disk. The innovators toolkit trusts the LLM unconditionally.

This isn't a bug — it's a consequence of cost-per-check being proportional to output volume. If every lesson needs a reviewer LLM call, that doubles API cost. But the cost objection is evaporating.

**Pattern 3: The Template Bootstrap Pattern Exists Only Once**
Only the lesson generator has the bootstrap phase (templates → project-specific prompts). Every other pipeline hardcodes its prompts. The innovators toolkit uses 15 fixed prompts. The novel generator uses 7. None of them can be trivially re-aimed at a new domain without editing YAML.

The lesson generator solved this: Jinja2 templates + `render_templates.py` + SubjectSummaries = instantiate a new subject in one command. But this pattern wasn't extracted as a reusable primitive.

**Pattern 4: Fan-Out Width Is Always Hardcoded**
`max_items: 50`, `max_items: 25`, `max_items: 20`. These are safety limits, not designs. No pipeline reasons about optimal batch size or adjusts parallelism based on content. The lesson generator generates 11–20 lessons regardless of whether the subject has 5 or 50 topics. The book translator translates all chunks equally, whether a chapter is 100 or 10,000 words.

**Pattern 5: Python Nodes Are Glue, Never Logic**
Across all 10 pipelines, every Python node does one of four things: (1) load files, (2) save files, (3) transform data structures (cartesian product, merge, split), (4) format output. No Python node makes decisions. All decisions are in YAML edges, conditions, or LLM nodes. The 3-layer architecture (presentation / logic / side-effects) is empirically real.

### The Constraint Shift

The title says it: **thinking speed is now near-infinite.** What does this change?

**Old constraint (2023):** LLM calls are expensive ($0.01-0.10/call). Design minimizes calls. One LLM pass per lesson. No quality gates. No revisions. No multi-perspective analysis. Generate once, ship.

**Current state (early 2026):** Flash-tier models cost $0.001/call. A 20-lesson module with quality review costs ~$0.04. The entire 81-lesson psykologia corpus cost under $2 total. The constraint has shifted from "can we afford to think?" to "what should we think about?"

**What this means for YAMLGraph:**

**Observation 1: Quality gates should be default, not optional.**
When a lesson costs $0.001 to generate, it costs $0.001 to review with an LLM-as-judge. The novel generator's pattern (generate → analyze → evolve ↺) should be the standard, not the exception. Every map node should have a paired review map. The pipeline should generate, judge, and regenerate failed items automatically. Cost is no longer the objection. The objection was always latency — but with async parallelism, 81 reviews take the same wall-clock time as 1.

**Observation 2: The template bootstrap should be a first-class YAMLGraph feature.**
The `render_templates.py` → project directory pattern is the most powerful thing in the lesson generator, and it's hand-coded. Imagine: `yamlgraph project init --template=lesson-generator --var subject=biologia`. The graph, prompts, and nodes are templated. The bootstrap phase runs automatically. The teacher runs `yamlgraph project run psykologia PS3` and gets 18 lesson plans with quality gates. This is a product, not a demo.

**Observation 3: Multi-perspective generation is now free.**
The innovators toolkit already does this: 9 parallel frameworks analyzing the same problem. But the lesson generator doesn't. Each lesson is generated from one perspective (one prompt, one LLM call). With near-infinite thinking, why not generate each lesson 3 times (constructivist pedagogy, direct instruction, inquiry-based) and let a synthesizer pick the best elements? The biopsykososiaalinen crutch identified in the lesson review exists because the generator never asks "what other lens could we use?"

**Observation 4: The real bottleneck is now evaluation, not generation.**
All 10 pipelines generate. None evaluate well. The kertomus pipeline has `validate` but doesn't act on failures. The novel generator loops but the grade threshold is arbitrary. No pipeline has a measurable quality metric that's tracked over time. With cheap thinking, the pipeline should: generate → evaluate against rubric → iterate → log quality scores → compare against baseline. The infrastructure exists (LangSmith tracing). The practice doesn't.

**Observation 5: Dead patterns should be harvested, not copied.**
The 10 pipelines were built sequentially. Each partially reinvents: save patterns, load patterns, map error handling, progress reporting. The `on_error: skip` pattern appears 15 times — but what happens to skipped items? No pipeline reports "3 of 20 lessons failed, here are the errors." The lesson generator's `save_lessons.py` and the kertomus `result_writer.py` are 60% identical code. With near-infinite thinking, an agent should analyze all 10 pipelines and extract a shared library: `yamlgraph.contrib.io` (load/save/report), `yamlgraph.contrib.quality` (review/grade/iterate), `yamlgraph.contrib.bootstrap` (template/render/init).

### The Meta-Pattern

All 10 pipelines implement the same abstract workflow:

```
Source Material → Decompose → [Map: Generate per-item] → Compose → Output
```

- Lesson generator: curriculum → topics → lesson per topic → save files
- Novel generator: premise → beats → prose per beat → assembled story
- Book translator: book → chunks → translation per chunk → reassembled book
- Kertomus: FHIR bundle → encounters → record per encounter → patient history
- Innovators toolkit: problem → frameworks → analysis per framework → synthesized report

This is ETL with LLM as the T(ransform). The pattern is universal. The variation is in the decomposition strategy and the composition strategy. The LLM call itself is interchangeable — it's "think about X and output Y."

**The insight:** YAMLGraph pipelines are not LLM orchestration frameworks. They are **content factories** that happen to use LLMs as workers. The competitive advantage isn't the LLM call — it's the decomposition (how you break work into parallelizable units) and the quality control (how you ensure each unit meets standards). Both are underinvested relative to the focus on generation.

### The Trap I Almost Fell Into

**Analysis momentum (again).** After identifying 5 observations, I wanted to immediately start coding: extract shared utils, add default quality gates, build `yamlgraph project init`. But these are 5 potential feature requests, not tasks. Each needs its own Plan → Judge → Enforce cycle. The observation that "near-infinite thinking changes everything" doesn't mean "change everything now."

**Heuristic:** When a constraint shift creates N opportunities, rank them by leverage (impact/effort), commit to one, and document the rest as future work. The shift is permanent; the opportunities will still be there tomorrow.

**Meta-observation:** This entire diary entry is an instance of the pattern it describes. I used near-infinite reading speed (14 lessons + 6 graph topologies + quantitative analysis in one session) to identify patterns I couldn't see while building each pipeline individually. The constraint shift enables not just faster generation but faster *meta-cognition about generation*. The diary is the quality gate on the thinking itself.

---

## 2026-02-17: The Funnel — From 5 Observations to 1 Starting Point

**Context:** The Constraint Shift entry produced 5 observations. These were extracted into FR-040 through FR-044. The Judgment phase then filtered them:

| FR | Title | Verdict | Rationale |
|----|-------|---------|-----------|
| FR-040 | Quality gates for map nodes | DEFERRED | Depends on FR-044; users can wire manually |
| FR-041 | Template bootstrap CLI | DEFERRED | N=1 evidence; premature generalization |
| FR-042 | Multi-perspective generation | REJECTED | Already expressible in 10 lines of YAML |
| FR-043 | Evaluation framework | APPROVED (Phase 1) | Valid need, but scoped to schema + logging |
| FR-044 | Shared contrib libraries | APPROVED (Phased) | Foundation that enables FR-040 and FR-043 |

5 observations → 5 FRs → 2 approved (both scoped down) → 1 entry point (FR-044 Phase 1: `SkipReport`, ~50 lines).

### The Trap: Enthusiasm Inflation

The agent (me) proposed all 5 as independent features with full acceptance criteria. The human judgment correctly identified what I missed:

1. **FR-042 is YAGNI.** The existing primitives already express multi-perspective generation. Three `llm` nodes and a synthesizer is 10 lines of YAML. A `perspectives:` DSL saves 6 lines but adds framework surface area. The "biopsykososiaalinen" problem is a prompt quality issue, not a framework issue.

2. **FR-041 is premature generalization.** Only one project uses the bootstrap pattern. Generalizing from N=1 creates dead abstraction. The correct trigger: wait for 2+ projects to manually adopt the pattern, then extract.

3. **FR-040 depends on FR-044.** Quality gates need `collect_failures()` and review aggregation — which are exactly what `contrib.quality` provides. Building the gate before the building blocks is backwards.

4. **FR-043 was scope-creeping.** The full framework (baselines, regression detection, comparison CLI) is a 5-day project. Phase 1 (schema + `--evaluate` + JSON log) is 2 days and proves the concept.

### The Dependency Chain

The judgment revealed a hidden execution order:

```
FR-044 Phase 1 (contrib.progress / SkipReport)
  → FR-044 Phase 2 (contrib.io + contrib.quality)
    → FR-043 Phase 1 (evaluation schema + CLI flag)
      → FR-040 (revisit: review config for map nodes)
```

The 5 "independent" observations were actually one dependency chain. Only the first link (FR-044 Phase 1) was actionable. The rest are sequenced by evidence and dependency, not by priority or enthusiasm.

### The Ratio

Analysis produced: ~3,000 words of diary (Constraint Shift), ~2,800 words of FRs (040–044), ~800 words of judgments. Total: ~6,600 words of analysis.

Approved action: `SkipReport` class, ~50 lines of Python.

Ratio: **~130 words of analysis per line of approved code.** This is not waste — it's the correct investment when the cost of wrong code exceeds the cost of analysis. The rejected FR-042 would have been 3 days of framework work that duplicates existing primitives. The analysis that rejected it took 5 minutes.

### The Cognitive Pattern

**Observation enthusiasm → FR inflation → judgment compression.** The pattern: a rich analysis session generates multiple "we should..." insights. Each insight feels urgent and independent. But judgment reveals dependencies, redundancies, and premature abstractions. The funnel narrows from "5 things we could do" to "1 thing we should do first."

**The trap name:** **Parallel opportunity illusion.** When N opportunities emerge simultaneously, they appear independent. But they share foundations, and building the foundation is the actual first step. The illusion is that you can pursue them in parallel.

**Heuristic:** When analysis produces N feature requests, look for the dependency chain before prioritizing by impact. The highest-impact FR may depend on the lowest-effort one. Start with the foundation, not the headline.

**Meta-heuristic:** The judgment phase is where feature requests go to get real. An FR without judgment is a wish. An FR with judgment has scope, dependencies, and a trigger for revisiting. The judgment section is the most important part of the template — more than the solution, more than the acceptance criteria.
