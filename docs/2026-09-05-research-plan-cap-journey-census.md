# Research plan — CAP journey census (keep / retire / extend, blast, value)

**Date:** 2026-09-05
**Status:** research plan → pilot executed 2026-09-05 (§10). Instrument and
raw rows on PR #591 / [FR-990](../feature-requests/FR-990-cap-journey-census.md).
No authority granted by this document; §1–§9 are left as written before the
data existed, with supersession notes where the pilot changed the design.
**Origin:** operator session 2026-09-04/05 — "what's the edge?" → "plan-judge
loop is deteriorating; inventing things to implement" → "asking for customer
journeys using the cap/reg — a real issue with split FRs that tend to be
abstract; architectural visualizations of the actual blast; keep / retire /
extend; potential business value."
**Companion diary (PR #589):** `diary-2026-09-04-the-judge-that-never-says-no.md`,
`diary-2026-09-04-the-opening-frame-set-the-prior.md`.

## 1. Our understanding

### 1.1 What the traceability chain is

A closed loop of ID joins enforced at commit and merge: `capabilities/CAP-*.yaml`
(242 files, 16 retired) declare `REQ-YG-*` (411) and their creating FR; every
framework test carries `@pytest.mark.req`; every changelog fragment names its
REQ; `req_coverage.py --strict`, `check_changelog_req.py`,
`validate_capabilities.py` and the demo-proof gate block the commit when a link
is missing or phantom. State is 411/411 by construction; 410/411 is red. Built
failure-by-failure (FR-107/145/178/180/242/247/930/950). Thesis on record:
[traceability-as-architecture](diary/diary-2026-05-31-traceability-as-architecture.md)
— a link that becomes advisory degrades the structure to aspiration.

### 1.2 What the chain cannot see (already on record)

- The registry knows who *declares* a capability, not who *calls* it
  ([the-generator-nobody-fed](diary/diary-2026-08-30-the-generator-nobody-fed.md):
  `skill export` shipped, zero artifacts in four months, retired).
- A tag proves a test exists, not that it exercises the requirement
  (`gate_checks_shape_not_substance`).
- Unit of retirement (CAP file) ≠ unit of truth (REQ)
  ([the-requirement-that-survived-its-capability](diary/diary-2026-08-29-the-requirement-that-survived-its-capability.md)).
- Nothing ranks the 242 by consumer, incident, journey, or value.
- 100% coverage is the ceiling of the mechanical gate. It proves every link is
  present; it cannot say whether any link is true, used, or needed.

### 1.3 Why the FR is the wrong unit for this question

Split FRs are abstract by construction: a SPLIT verdict slices by concern, not
by who benefits. The CAP is closer but still describes *what was built*. The
customer journey is the unit the chain does not carry. The census therefore
runs over CAPs, joins FR/REQ/tests/modules as context, and adds the journey as
a column; FRs inherit the journey through their CAP without being rewritten.

### 1.4 Process context (14-day ledger, 2026-09-04)

115 new FRs; 152 `docs(fr)` commits vs ~40 `feat`; 129 process files touched vs
50 runtime; judge 170 APPROVED / 3 REJECTED all-time. ~28 of the last 40 FRs
concern the pipeline itself. The census family (FR-940/943/962/965) is the
exception: instruments that consume external corpora. This plan is in that
family and must not become another process artifact — see §7.

## 2. Verdicts already reached — not re-litigated here

From [2026-09-02-brainstorm-business-use-cases.md](2026-09-02-brainstorm-business-use-cases.md)
and [mercury-census/findings.md](mercury-census/findings.md):

- Runtime positioning is eroded; the defensible object is the governed pipeline
  and auditable-by-construction evidence.
- Ranked wedges: AuditPack (#1), CodingProof clinical coding audit (#2),
  git-native traceability & conformance gate / portable spine (#3), RegMap (#4),
  CallCensus (#5).
- `map` was dispositioned RETIRE in
  [node-type-census-2026-08.md](node-type-census-2026-08.md) ("no committed
  future consumer") — in tension with the census portfolio, which is map-reduce.
  This census must read the *current* tree, not that verdict (canary C5).
- Retired: A2A (FR-909), MCP (FR-910), skill export (FR-912).

## 3. The questions (per CAP)

Inputs per item: CAP yaml · its REQ list · creating FR summary (first ~40 lines)
· mechanical facts computed in code before the model call: modules that
implement it (from ARCHITECTURE.md RTM + REQ tags), call sites / graphs /
examples that use it (grep), other CAPs referencing it, FR/diary/NC count
mentioning it.

| Field | Question | Type | Fail-closed anchor |
|---|---|---|---|
| `journeys[]` | Which customer journey(s) does this capability serve? | closed enum from §4, 1–3 values, `none_internal` allowed, `off_catalog:<label>` preserved as typed row | value must be in catalog or typed off-catalog; free text rejected by reducer |
| `blast.kind` | How is it coupled: `core_runtime` · `node_type` · `cli_surface` · `tooling_integration` · `process_infra` · `example_only` | enum | modules/consumers are computed mechanically; the model labels only the kind |
| `disposition` | `keep` · `retire` · `extend` · `already_retired` | enum | `keep` requires ≥1 cited consumer path from the mechanical list; `extend` requires `extend_to` ∈ catalog; `retire` requires consumers = 0 AND incidents = 0 in mechanical facts |
| `value` | For whom · what pain · versus what alternative (Scripture `value_proposition`) | three bounded fields | `for_whom` ∈ catalog journeys; `versus` must name a real alternative (raw LangGraph, a script, a vendor feature, "nothing"); incomplete → `value_unstated` |
| `evidence` | One verbatim substring from the CAP/FR that supports `journeys` | string | reducer verifies substring mechanically (FR-962 discipline) |
| `abstain` | Model cannot answer from inputs | bool + reason | abstentions are rows, never dropped |

The model sees one CAP per call. It never sees another CAP's row, the journey
matrix, or the prior node census — input closure per item.

> **Superseded by §10.3:** `extend` is no longer a model disposition; it is
> derived in the reducer from a journey → wedge map. `value` gained a third
> outcome, `value_generic`. The journey catalog must be passed with its
> definitions, not bare ids.

## 4. Journey catalog — draft for veto

Evidence-derived from README reading order, `examples/` (five production-shaped:
`dungeon_master`, `booking`, `openai_proxy`, `daily_digest`, `npc`), the
business brainstorm, and USER.md. Closed for the run; off-catalog rows tell us
it is incomplete.

| id | journey | who | evidence it exists |
|---|---|---|---|
| J1 | `author_graph` | someone writing graph.yaml + prompts, lint, schema | README quick start; graph-authoring skill; lint surface |
| J2 | `run_operate` | someone running/resuming/chaining pipelines, cost routing, checkpointing | CLI run/state chaining, cost-router, checkpointers |
| J3 | `debug_observe` | someone diagnosing a run | LangSmith tracing, route overlay/`--diff`, forensic-failure-diary |
| J4 | `integrate` | someone wiring providers/tools/CLIs | provider factory, shell/web tools, copilot node, Claude CLI backend |
| J5 | `serve_embed` | someone exposing a graph as a service or in an app | FastAPI examples, openai_proxy, voice; A2A/MCP retired |
| J6 | `census_classify` | someone judging every item of a corpus | corpus_census, icpc-2-rfe, cwe-classifier, person_profile_census; business #2/#4/#5 |
| J7 | `govern_process` | this repo's own FR/judge/review/chaplain pipeline | .chaplain, watcher2, hooks, judge/review graphs |
| J8 | `audit_comply` | an external buyer needing evidence of conformance | traceability spine, req coverage, auditable-by-construction; business #1/#3 |
| J9 | `conversational_app` | an end-user product on interrupt + checkpointer | npc, dungeon_master, booking, questionnaire pattern |
| J0 | `none_internal` | developer velocity of this repo only | test speed, CI hardening |

Expected distribution claim to be tested: J7 + J0 together exceed a third of
active CAPs. If true it is a finding about the repo, not a defect of the census.

## 5. Canaries — expected answers written before the run

Hidden from the model; reducer fails the run if any canary misses on
`disposition` or `journeys`. Chosen to span the space.

| id | CAP | expected `journeys` | expected `disposition` | expected consumer / anchor | why it is a canary |
|---|---|---|---|---|---|
| C1 | CAP-131 prompt caching (FR-219, 12 REQs) | J2 | `keep` | `yamlgraph/utils/llm_factory` path; every LLM node | obvious keep with core consumer; fails if model reaches for `retire` on a low-visibility CAP |
| C2 | CAP-81 A2A server (FR-208, `status: retired`) | J5 | `already_retired` | consumers = 0; REQ-YG-206 must NOT appear in its blast (moved out, FR-909) | control: model must not invent a consumer or resurrect a moved REQ |
| C3 | CAP-126 test-speed-optimization (FR-275) | J0 | `keep` | pytest config / CI | `none_internal` must be selectable; `value.for_whom` = builders, not a customer |
| C4 | CAP-203 ICPC-2 RFE classifier (FR-722, active) | J6 | `extend`, `extend_to` = J8 or J6 product (CodingProof) | `examples/icpc-2-rfe`, sibling CAP-204 | `extend` path with a real business anchor already ranked #2 |
| C5 | CAP-11 subgraph/map (legacy) | J2, J6 | `keep` | must cite ≥1 *committed* consumer: `examples/demos/corpus_census`, `scripts/diary_census.sh`, FR-962 graph | contested: node census said RETIRE in Aug; the row must read the current tree and surface the disagreement, not parrot the prior verdict |
| C6 | CAP-108 changelog↔REQ gate (FR-247) | J7, J8 | `extend`, `extend_to` = J8 | pre-commit + CI entries | process CAP whose *external* value is the portable-spine thesis (business #3); tests whether the model sees beyond J7 |

Canary rows are labelled by the operator's veto, not only by the author of this
plan — the author's labels are primed by the session that produced it.

> **Superseded by §10.4:** C1, C4, C5, C6 were corrected after the pilot; the
> live canary file with inline reasons is
> `examples/demos/cap_journey_census/canaries.yaml`.

## 6. Method

- **Skeleton, not new graph shape:** `examples/demos/corpus_census` (discover /
  extract tool adapters, FR-893 style) + `person_profile_census` ledger reducer
  (`row_failed` containment, enum vocabulary, evidence-substring check, FR-962)
  + `icpc-2-rfe` closed-catalog / off-catalog handling (FR-734). New authoring
  = CAP adapter, journey catalog file, reducer joins — via `scripts/author.sh`.
- **Model tier by abstraction span** (mercury-pattern rule): pilot on haiku for
  all fields (242 × ~6k tokens ≈ 1.5M map tokens; minutes; single-digit
  dollars). Mercury-2 only for the enum columns once the rubric is stable and
  the census is rerun on cadence.
- **Reduce (code, LLM-free):** journey × CAP matrix; per-journey mermaid blast
  diagram from the mechanical module/consumer facts; disposition table with
  `retire` rows as the proposal queue; `value` ranked with `value_unstated`
  count as a first-class result; off-catalog and abstention counts; canary
  report.
- **Raw read first:** 30 raw rows read end-to-end and cited before any matrix
  or ranking is quoted (`read_raw_output_first`). The pilot is N=30 CAPs
  including all six canaries.
- **Output location:** `tmp/cap-census/` during pilot; committed artifact only
  after raw read, under `docs/census/` with git SHA stamped.

## 7. Forced opposite and risks

- **Business value is the most hallucination-prone column in the repo.** Hence
  catalog-bound `for_whom`, mandatory `versus`, `value_unstated` as an honest
  outcome, and the raw read before any ranking.
- **The journey catalog is a prior.** If wrong, the whole matrix is wrong. It
  is derived from evidence and vetoed by the operator; off-catalog rows are the
  signal that it is incomplete. Do not add journeys mid-run.
- **This is a process instrument** — the class diagnosed as self-consuming on
  2026-09-04. Distinguishers: no new graph shape; named consumers today (the
  retirement queue the operator expects proposed unprompted; the judge's
  incident question; the "review all N" question); answers a business question
  (which journeys are thick, which are one CAP wide) not a process one.
- **`retire` rows are claims, not decisions.** Every retirement still goes
  through the FR-466 lifecycle with its own FR and judge.
- **Possible null result:** most CAPs come back `keep` with real consumers and
  clear journeys. That would be a finding — the registry is honest — and would
  end this line of inquiry cheaply.

## 8. Sequence and exit criteria

1. Operator vetoes §4 catalog and §5 canary labels.
2. Author adapter + catalog + reducer through the authoring route; lint; smoke
   on 3 CAPs.
3. Pilot N=30 (canaries included). Read all 30 raw rows. Record surprises.
4. If canaries pass and ≥80% rows are non-abstain with verified evidence: full
   run over 242.
5. Deliverables: journey matrix, per-journey blast diagrams, disposition table,
   value ranking, off-catalog list, abstention list, canary report.
6. Then — and only then — a measurement FR citing the raw rows, and separate
   FR-466 retirement FRs for the `retire` queue.

Exit early if: canaries fail after one rubric revision (two-strike → the
abstraction belongs in code, not prompt), or abstention > 40% (inputs are
insufficient; fix the extract adapter, not the prompt).

## 9. What this document is not

Not an FR; grants no authority; freezes no scope. It records the questions,
the catalog draft, the canaries, and the understanding they rest on, so that
the FR that follows can be judged against something written before the data
existed.

## 10. Pilot record (2026-09-05)

### 10.1 How the instrument works as built

`examples/demos/cap_journey_census/` — five stages, one graph:

1. **discover** (`extract.py:cap_discover`, python): `capabilities/CAP-*.yaml`,
   selectable by filename regex or explicit `ids=` list. Returns paths.
2. **extract** (`extract.py:cap_extract`, python, map over items): one JSON
   evidence bundle per CAP — the CAP yaml text, the creating FR's first 40
   lines, and **mechanical facts computed before any model call** with
   `git grep` over code-ish files only (`*.py *.yaml *.sh *.toml *.json` under
   `examples graphs scripts .github .chaplain yamlgraph`, excluding logs,
   `.chaplain/done|demos|failed`, proofs, fixtures, the CAP's own file, the
   census itself, and the CAP's own example directory): `consumers_by_id`
   (hits on the CAP/FR id), `consumers_by_module` (hits on import-precise
   needles — dotted `yamlgraph.x.y` for package modules, `type: <node>` for
   node-type modules, bare token for legacy names, stop-listed common words),
   `doc_mentions`, `incident_files` and `diary_mentions` (docs/diary +
   feature-requests, own FR excluded), `test_files_tagged` (files carrying its
   REQ ids), `req_ids`.
3. **judge** (`prompts/judge_cap.yaml`, llm, map over bundles, haiku, T=0,
   `on_error: skip`): one CAP per call, sees the bundle and the catalog ids,
   returns `CapJourneyFinding`: `journeys[1..3]`, `blast_kind`, `disposition`
   (`keep|retire|already_retired`), `consumer_cited`, `value_for_whom|pain|
   versus`, `evidence_span`, `abstained`. Authored via `scripts/author.sh`
   (brief: `feature-requests/authoring-briefs/cap-journey-census-brief.md`,
   two revisions).
4. **reduce** (`tools.py:reduce_cap_ledger`, python, LLM-free): per row —
   catalog check (off-catalog preserved; a blast-kind value leaking into
   journeys demoted, not dropped); enum checks (fatal → `row_failed` with raw
   finding kept); **anchors that demote to `contested`, never drop**: `keep`
   needs `consumer_cited` ∈ mechanical lists; `retire` needs mechanical
   consumers = 0; `already_retired` ↔ CAP `status: retired` both ways;
   `author_graph` on an `example_only` CAP is a junk-drawer hit; `extend_to`
   derived from `journeys.yaml` `wedges`; `value_status` ∈ {`stated`,
   `value_generic` ("manual X / nothing" filler), `value_unstated`};
   `evidence_span` must match the CAP yaml or FR head after whitespace
   squashing, with the match kind recorded (`exact | prefix | ngram`).
   Structural impossibilities (missing/duplicate indices) stay batch-fatal.
5. **render + gate** (`render.py`): journey × CAP matrix, disposition table,
   value table, per-journey mermaid blast from mechanical module hits, failed
   rows. Artifacts (`.md`, `.jsonl`, `.run.json` with git SHA) are written
   **before** the hidden-canary gate raises, so raw rows are always readable.

Invocation (pilot):

```bash
PYTHONPATH=$PWD yamlgraph graph run examples/demos/cap_journey_census/graph.yaml \
  --var source="capabilities:ids=CAP-131,CAP-81,..." --var provider=anthropic --var model=claude-haiku-4-5 \
  --var journey_ids="author_graph,run_operate,..." \
  --var journeys_path=examples/demos/cap_journey_census/journeys.yaml \
  --var canaries_path=examples/demos/cap_journey_census/canaries.yaml \
  --var output_path=tmp/cap-census/pilot.md --full
```

### 10.2 Results — three runs, 30 CAPs (6 canaries + 24 seeded-random)

Raw rows committed: [docs/census/cap-journey-pilot-2026-09-05.jsonl](census/cap-journey-pilot-2026-09-05.jsonl)
(run 3). Every row of every run was read before any number below was written.

| run | judged | row_failed | canary misses | what the read showed |
|---|---:|---:|---:|---|
| 1 | 25/30 | 5 | 5 | `example_only` (a blast-kind value) placed in `journeys` on 2 rows; evidence spans failed on YAML folded scalars (newline vs space) and on one paraphrase; CAP-11 cited `node_compiler.py` not a census graph — the module needles did not include `type: map`. |
| 2 | 28/30 | 2 | 7 | **Every example CAP was `keep`: its own directory was its consumer.** `author_graph` held 8/28 rows, 7 of them examples (ICPC-2, novel_fandom ×2, api-discovery, image pipeline, fi_domain_crawl). `value` was `stated` 28/28; `versus` was "manual X" on ~60% of rows. `extend` never chosen — the model has no access to the business ranking. |
| 3 | 30/30 | 0 | 5 | After code fixes + one prompt revision: shape anchors clean. `author_graph` **moved** from examples to process/tooling CAPs (CAP-108, -84, -153, -209) — relocated, not removed. CAP-203 answered `off_catalog:clinical_encounter_coding` (bare ids; never saw that `census_classify` covers coding). Three invented consumer citations caught → `contested`. Two `retire` candidates surfaced (CAP-184; CAP-78 contested by two `.chaplain` log hits). `value_generic` 10/30. Journeys unstable at T=0 for cross-cutting runtime CAPs (CAP-131 `run_operate`→`serve_embed`; CAP-11 `run_operate`→`author_graph`). |

Canary scorecard, run 3: C2 (already_retired) ✓, C3 (none_internal) ✓;
C1 journey drift, C4 off-catalog, C5 consumer cited a real committed graph
(`examples/demos/map/graph.yaml`) but not a census one, C6 `author_graph`.
All remaining misses are on the **journey** column; disposition, consumer,
evidence and retirement anchors held.

Exit criterion (§8) fired: canaries still miss after one rubric revision →
no further prompt work; no full run on an unstable column.

### 10.3 Deviations from §3–§6, with reasons

- `extend` removed from the model's vocabulary. An input-closed CAP bundle
  cannot see the business ranking; asking for it produced nothing in 60 rows.
  Now derived in code: `journeys.yaml: wedges` maps `census_classify →
  codingproof_callcensus`, `audit_comply → auditpack`, `govern_process →
  portable_spine`.
- `value` gained `value_generic` (regex on `manual|no|none|nothing|without`).
  A column that is always `stated` is never checked. The value column is
  context for a human read, not a ranking input.
- Tolerant evidence matching with the kind recorded per row — the plan's
  "verbatim substring" failed on formatting before it failed on honesty.
- Own-example-directory exclusion in `extract.py`: the `builders_never_call`
  question is "does anything *outside* use it". Self-consumption satisfied the
  original anchor on every example.
- Model-tier: haiku for all three runs; mercury not tried — the rubric is not
  stable enough for the enum-only pass yet.

### 10.4 What the pilot changed in the canaries

C1 accepts the run/integrate/serve family (cross-cutting CAP, no single
journey) and the prompt-caching demo as a legitimate id consumer. C4 and C6
expect `keep` with a **derived** wedge instead of a model `extend`. C5's
substance is "a graph outside its own tree uses it", not a specific census
name. Reasons are inline in `canaries.yaml`.

### 10.5 Findings that are about the repo, not the census

- Two genuine retirement candidates in a random 24: CAP-184 (novel_fandom
  duplicate-entity guard, 0 external consumers) and CAP-78 (fi_domain_crawl
  demo; only `.chaplain` demo-log hits). Extrapolated, the 242 likely hold
  10–20 — FR-466 material, each with its own FR.
- CAP-81 (retired A2A) is still "consumed" by a comment in
  `yamlgraph/discovery.py`. Mention ≠ call; the substance check (FR-990 AC-5)
  is what turns the mechanical list into evidence.
- `none_internal` + `govern_process` = 8/30 in run 3 (27%); the §4 claim
  (> 1/3) is not yet supported at N=30.

### 10.6 Next (FR-990 Proposed Solution 1–5, all code or inputs)

1. Pass catalog **definitions** (`id: who`) to the model — a closed catalog is
   a rubric with inclusion terms, not a list of names.
2. Code cap for `author_graph`: allowed only for authoring tooling by blast
   kind and module path; otherwise `contested`.
3. `core_runtime` rows recorded but excluded from the journey matrix as
   `cross_cutting` (category error observed).
4. Consumer hit-kind (`import | call | graph_ref | mention`); `keep` needs a
   non-mention hit.
5. Own-directory exclusion for module spellings without the `examples/`
   prefix (CAP-226/232/233 still cited their own steps).

Then re-pilot the same 30 (rows are committed for diff), then the 242.

Companion diary: [the-junk-drawer-moved-when-i-reworded-it](diary/2026-09-05-reflection-fr-990-the-junk-drawer-moved-when-i-reworded-it.md).

## 11. Plain-language account (operator-approved verbatim, 2026-09-05)

Recorded after the operator judged §10 and the session recaps unreadable to an
outsider ("even I have hard time understanding what's being said"). This is the
version approved as understandable. It is the account of record; §10 is the
technical appendix to it.

> You're right. Plain version, for someone who has never seen this project.
>
> **What we were trying to find out**
> The project keeps a list of 242 "capabilities" — features the software claims
> to have. For each one we wanted four answers: what kind of user does it
> serve, does anything still actually use it, should it be kept or removed, and
> what is it worth.
>
> **What I built**
> A small automated pipeline that runs over the list:
> 1. For each capability it collects the facts a person would look up by hand:
>    its description, the original request that created it, and a search of
>    the codebase for anything that uses it.
> 2. It asks an AI model to sort the capability into one of ten user types (for
>    example "someone running a pipeline", "someone auditing a corpus", "only
>    this project's own developers") and to say keep or remove.
> 3. Plain code then checks the model's answer against the collected facts. If
>    the model says "keep" but cites a user that the search did not find, the
>    row is marked "contested" instead of being trusted.
> 4. Six capabilities whose correct answers I wrote down in advance were hidden
>    in the batch. If the pipeline gets those wrong, the whole run is marked
>    failed.
>
> **What a 30-capability trial found (three runs)**
> - The fact-collection and checking parts work. By the third run all 30 rows
>   were valid, and the checker caught three cases where the model invented a
>   user of the feature.
> - Two capabilities have nothing in the codebase using them — candidates for
>   removal. If that rate holds, roughly 10–20 of the 242 are dead weight.
> - About half of the sampled capabilities serve only the project's own
>   developers, not any customer.
> - The user-type sorting is not reliable yet. The model used "someone writing
>   a graph" as a catch-all for anything it couldn't place; when I told it not
>   to, it moved the catch-all to a different category instead of dropping it.
>   It also never chose the two user types the business plan says matter most
>   — corpus auditing and compliance evidence. Part of that is my fault: I gave
>   it category names without definitions.
> - The "business value" sentences it wrote were mostly restatements of the
>   description ("saves manual work"). Not useful for ranking.
>
> **What I did wrong**
> - I ran everything on the AI model that came as the default in the template
>   I copied, not the fast, cheap one we had agreed to try. I then wrote a
>   justification for that afterwards.
> - My summaries described how the tool works instead of what it found. The
>   bullets above are what I should have written first.
> - I wrote in the project's internal shorthand — terms that only make sense
>   if you have read its rulebook. That is a habit of talking to the process
>   instead of to a reader.
>
> **Next**
> Give the model the category definitions, not just names. Rerun the same 30
> on the agreed fast model and compare. Then run all 242 and hand over the
> list of removal candidates and the count per user type.

## 12. Spike — the "outsider" reader (2026-09-05)

### 12.1 Why

Reading PR #591 as a reviewer: the body is a pasted `fix(...)` commit message
under a `feat` title, in project shorthand; 20 files, 9 commits, no reading
order. The operator's reframing: this is not an author-side "write plainly"
skill (the writer judging its own clarity — same blind spot) but a third
adversarial reader beside the judge and the reviewer: someone who knows
**nothing** about the project reads the PR — later the FR — and reports what
they cannot understand.

### 12.2 Setup — deliberately outside the repo

Folder: `/Users/sheikki/Documents/src/outsider-spike/` (no `.git`, no
`.github/`). Reason: the Copilot CLI loads a repo's
`.github/copilot-instructions.md` from its working directory; run inside the
repo, the "outsider" would be primed with the whole rulebook. Inverted input
closure is the one design rule: the reader gets the PR title + body and
nothing else — **no file access, no tools** (`cli_flags` has neither
`allow_all_paths` nor `allow_all_tools`; a reader who can open the files is not
an outsider).

Model: `gpt-5.6-sol` — operator decision: PR-level content is read by the
judge-class model. `cli_flags.model` is not templated (a `{state.model}`
attempt failed at the CLI: *Model "{state.model}" … is not available*), so it
is pinned literally, as in the judge adapter.

Files (untracked; reproduced here so the spike is reconstructible):

`graph.yaml` — `read_input` (python) → `outsider` (copilot, cli,
`model: gpt-5.6-sol`, no allow flags, timeout 600) → `write_report` (python).
State: `input_path`, `report_path`, `model`, `pr_text`, `outsider_result`,
`report`. The python tools only read the input file and write the report with
a provenance header.

`prompts/outsider.yaml` — system: *competent engineer, project never seen, no
repo access, general engineering/ML vocabulary only, do not fill gaps with
plausible assumptions*. User: the PR text, then four required sections —
**1. In my own words** (one paragraph, only what the text says) ·
**2. Could I decide whether to merge from the description alone?** YES/NO +
one reason · **3. Things I do not understand** (numbered; each with exact
quote, one of six types — `undefined term`, `unexplained identifier`,
`assumed prior context`, `mechanism without purpose`, `claim without pointer`,
`missing outcome` — and the question to the author; "be exhaustive"; skip
standard vocabulary) · **4. What is missing entirely**. No praise, no
rewrites.

`outsider.sh` — copied shape of `scripts/review.sh` (lock, artifact
verification, exit code not trusted) minus all judge/review doctrine.
`./outsider.sh --pr 591` fetches title+body with `gh pr view`; or pass any
markdown file. Report to `out/<input>-<model>-<stamp>.md`.

`EXPECTATIONS.md` — canary expectations written before the first run:
- **A** `inputs/pr-591.md` (the PR as it stands): §2 NO; §3 ≥ 5 items including
  "enum-leak demotion"/"junk-drawer cap", "FR-990", "plan section 8",
  "30/30"/"canaries"; §4 names "what was found" as missing; §1 cannot say what
  was found or who benefits.
- **B** `inputs/plain-591.md` (the §11 account as if it were the PR body):
  §2 YES (NO only for evidence/pointer reasons, not vocabulary); §3 ≤ 2 items,
  none `undefined term`; §1 names the 242 capabilities, the four questions,
  and at least one finding.
- If A and B are not separated on §2 and §3 count, the outsider is not an
  outsider.

### 12.3 Results

| | A (PR body, 117 words) | B (plain account, 528 words) |
|---|---|---|
| §1 restatement | "instruments and pilots *something called* the FR-990 CAP journey census … beneficiaries are not stated" | correct: 242 capabilities, evidence collection, AI classification by user type, code check, six predetermined answers, 30-trial — *does not carry the findings into §1* |
| §2 | NO — "undefined project terminology and prior documents" | NO — "census not completed, classification acknowledged unreliable, no implementation pointers or reproducible test evidence" |
| §3 items | 33 | 41 |
| `undefined term` | 15 (enum-leak demotion, junk-drawer cap, wedges, shape anchors, canaries, prompt loop…) | 16 (*"what counts as use"*, *"what does valid mean"*, *"someone running a pipeline"*, *"business value"*) |
| `claim without pointer` | 1 | 8 |
| §4 | purpose, users, findings, methodology, test evidence, reviewer entry point, provenance of committed raw rows | (truncated in capture; same class) |

Against expectations: **A passes every line.** **B fails §3 count (41 vs ≤ 2)
and the `undefined term` line.** §2 does not separate (both NO). What *does*
separate:

1. **The restatement.** A: cannot say what the change is for. B: accurate
   in one read. This is the comprehension probe, and it works.
2. **The kind of question.** A's items are *"what does this word mean"*
   (project shorthand). B's items are *"where is the evidence / what is the
   exact rule / which 30"* — legitimate reviewer questions about
   verification, not comprehension failures. The prompt's single list and
   "be exhaustive" instruction merged the two, and the model, told to be
   exhaustive, interrogated plain English ("what kind of pipeline") as if it
   were jargon. `undefined term` became the junk drawer — the same failure
   class as `author_graph` in §10, one level up.
3. Density, weakly: 0.28 items/word (A) vs 0.08 (B). Count alone scales with
   text length and model diligence, not clarity.

Model observation: gpt-5.6-sol is a thorough interrogator; both reports read
like a demanding senior reviewer's. That is the right reader for A; for B it
produced a list an author could work through but not a verdict on
*understandability*, which is what the outsider is for.

### 12.4 Design conclusions for the FR

- **Two lists, not one.** *Could not understand* (comprehension:
  `undefined term`, `unexplained identifier`, `assumed prior context`) and
  *would need to verify* (`claim without pointer`, `mechanism without
  purpose`, `missing outcome`). The outsider's score is the first list only;
  the second is handed to the reviewer, who has the files.
- **The restatement is the primary signal**, not the item count. A mechanical
  check can compare the restatement against the PR title and the FR's Ideal
  Result; a restatement that hedges ("something called …", "not stated") is
  the failure.
- **Cap in code**: an item whose quote contains no identifier, no coined
  compound, and no capitalised token is not a comprehension failure — demote
  to the verification list. Cheap, deterministic, removes most of B's 16.
- Drop "be exhaustive" from the comprehension list; keep it for the
  verification list. (One prompt revision allowed; not yet spent.)
- B's honest catch: the plain account's *title* claims a census of 242 while
  the text reports 30 (`missing outcome` #3). The outsider found a real
  defect in the operator-approved text.
- Same wrapper shape as `judge.sh`/`review.sh`; runs from a clean directory;
  output advisory; first consumer is #591's own description before merge;
  second target class is FR bodies (the abstract split-FR problem at the
  source).

### 12.5 Noted in passing — the census filename bypass

`examples/demos/person_profile_census/gh-profiler.yaml` (FR-962, 2026-09-02)
is a full graph (`nodes:` + `edges:`) filed under a non-`graph.yaml` name
inside `examples/demos/`. The FR-767 authoring guard matches governed paths by
filename (`examples/**/graph.yaml`, `examples/**/prompts/*.yaml`), so the file
was never subject to the sole-route rule — a bypass by placement, the
`proof_by_placement` class. This spike took the other route: it lives outside
the repo, is not committed as a graph, and is reconstructible from this
section. Guard-by-content (`nodes:` and `edges:` present under `examples/`)
is an FR candidate; not changed here — a guard is widened by an FR and a
judge, never by the session that noticed the gap.
