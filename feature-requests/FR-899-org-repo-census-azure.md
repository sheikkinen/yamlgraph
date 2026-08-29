# Feature Request: Org Repository Census with Pinned-Azure Delegation

**Priority:** MEDIUM
**Type:** Feature
**Status:** In Progress — enforced 2026-08-28, PR pending; see [FR-899-org-repo-census-azure.judgement.md](FR-899-org-repo-census-azure.judgement.md)
**Effort:** 1.5 days
**Requested:** 2026-08-28
**First consumer / first event:** operator running a customer-organization repository inventory (repo purpose / persons / activity + one corp-level brief) on the corp-approved Azure endpoint, at the next corp platform-audit moment
**Research:** in-body dispositioned research record (§ Research Record: Solution Classes) — five solution classes with precedent lines, preserved disagreement, and the `is_this_a_graph` answer
**Prior art:** FR-896 (cross-repo pattern/model census) — DISTINCT: censuses the author's own dev footprint for pattern/model incidence, mercury-pinned, redaction-gated for a public artifact; FR-899 censuses a CUSTOMER org's repos for purpose/persons/activity under an azure-only compliance boundary with outputs never committed — shared base (FR-892 corpus_census) is reuse, not overlap. FR-893.research.md / FR-895.research.md — research records for the census base and synthesize tail this FR builds ON; cited as foundation, no territorial conflict.

## Summary

A repository-census invocation of the shared corpus_census pipeline (FR-892):
discover slot enumerates an organization's repositories via `gh`, extract slot
builds a per-repo evidence bundle (metadata, README head, contributor
shortlog), a map LLM node renders one purpose judgement per repo, a
deterministic code reduce computes activity and persons mechanically, and one
synthesis call renders the corp-level brief. **Every LLM node pins
`provider: azure`** — corp data never transits the Anthropic default.

## Value Statement

The operator gets a skimmable org-level repository map (what each repo is for,
who owns it, whether it is alive) plus a corp brief, produced entirely on the
corp-approved Azure endpoint, from one command.

## Problem

Customer organizations accumulate dozens of repositories with no maintained
map: purpose is undocumented, ownership is tribal knowledge, and dead repos
are indistinguishable from active ones. Producing this map manually is slow
and unrepeatable. Producing it with the default LLM provider is a data-
governance violation: repo contents and contributor identities are corp data
and must only be analyzed by the corp-approved (pinned) Azure deployment.

## Ideal Result

One command against an org name yields:
1. a JSONL ledger + markdown table, one row per repo: `name`, `purpose`
   (LLM, one sentence), `persons` (top contributors, mechanical), `activity`
   (`active`/`dormant`/`archived`, mechanical), evidence citations;
2. one corp-level brief synthesized from the ledger;
3. zero LLM calls to any provider other than the pinned Azure endpoint;
4. zero customer identifiers committed to this public repo.

## Proposed Solution

Reuse `examples/demos/corpus_census/graph.yaml` unchanged where possible; add
generic **gh-org proof adapters** next to the existing `git_*`/`pdf_*` ones in
[examples/demos/corpus_census/adapters/corpus_adapters.py](../examples/demos/corpus_census/adapters/corpus_adapters.py).

### Adapters (slot contract per FR-892: state-dict in, list/str out)

Mechanical contract (R-4):

- **`gh_org_discover(state)`** — `source` grammar: `<org>` or `<org>:<n>`
  where `<n>` is a positive integer; malformed source raises `ValueError`.
  Fixed argv `gh repo list <org> --limit <n> --json
  name,description,pushedAt,isArchived,isFork,primaryLanguage` via
  `subprocess.run` (no shell), `timeout=60`, `check=True` — missing `gh`
  auth or a failing `gh` command surfaces as `CalledProcessError`, never
  swallowed. Bounds: `MAX_REPOS = 100` (cap applied over `<n>`). Forks and
  archived repos are INCLUDED (archived feeds the `activity` field). Empty
  org raises `ValueError`. Item identity format: `<org>/<name>` (one repo
  per item ref).
- **`gh_repo_extract(state)`** — `item` grammar: `<org>/<name>`; malformed
  ref raises `ValueError`. Fixed argv `gh api` calls (each `timeout=60`,
  `check=True`):
  `repos/<org>/<name>` (description, `pushed_at`, `archived`, language),
  `repos/<org>/<name>/readme` (base64 head, decoded, `MAX_README_CHARS =
  3000`), `repos/<org>/<name>/contributors?per_page=5` (`MAX_PERSONS = 5`,
  login order verbatim from API). Missing README (404) yields an explicit
  `readme: none` marker, not a failure. Returns ONE JSON text blob per repo
  with exactly these keys: `name`, `description`, `pushed_at`, `archived`,
  `language`, `readme_head`, `contributors` — this blob is both the LLM
  evidence bundle and the reducer's mechanical-field source. Total blob
  capped at `MAX_CHARS = 4000`.

Test surface: malformed `source`, empty org, missing/failing `gh`,
bounds enforcement (repo cap, README cap, contributor cap), malformed
item refs, 404 README.

### Judgement split (cheap-map, code-reduce, one-judgement-tail)

- **Map LLM node (pinned azure):** ONE judgement per repo — `purpose`
  (one-sentence what/for-whom). Rubric passed as `--var rubric=...`.
- **Code reduce (LLM-free):** `activity` is mechanical —
  `archived` → `archived`; `pushed_at` within N days (default 180) →
  `active`; else `dormant`. `persons` = top contributors from the API,
  verbatim. The LLM is never asked to judge activity or list persons
  (mechanizable levels stay in code — prompt-contract discipline).
- **Synthesis tail (pinned azure):** existing FR-895 synthesize tail; the
  corp brief rubric arrives via `--var brief_rubric=...`. Citation boundary
  validates against the ledger as today.

### Repo-census reducer and ledger contract (R-2)

Activity/persons computation is a REDUCER responsibility, not adapter glue.
New code surface: `examples/demos/repo_census/tools.py` —
`reduce_repo_ledger` (LLM-free, fail-closed). It joins each map finding
(purpose judgement) with its extracted JSON blob by item ref and validates
every row against a Pydantic model:

```python
class RepoLedgerRow(BaseModel):
    name: str                      # "<org>/<name>", from item ref
    purpose: str                   # LLM one-sentence judgement, non-empty
    persons: list[str]             # verbatim API contributor logins, 1..5
    activity: Literal["active", "dormant", "archived"]  # mechanical
    evidence_citation: str         # item ref + evidence span from finding
    model: str                     # map model id
    prompt_version: str
    source_index: int              # provenance: map index
```

Rejection rules (any violation fails the whole reduce, no partial ledger):
missing finding for a discovered repo, duplicate findings for one repo,
empty `purpose`, malformed `activity`, empty `persons` when the API
returned contributors, dangling citation (item ref not in discovery set).
Artifacts: `<output_path>` markdown table + sibling `.jsonl` (one
`RepoLedgerRow` per line), mirroring the FR-892 reducer convention
(`tools.py:117-149`).

`activity` derivation: `archived` when the API blob has `archived: true`;
else `active` when `pushed_at` is within `ACTIVITY_WINDOW_DAYS = 180`
(configurable via `--var activity_window_days=`); else `dormant`.

### Azure preflight (R-3)

Provider construction happens inside LLM node execution
(`llm_nodes.py:331-351`), AFTER discovery and extraction — so llm_factory
validation alone would let corp data flow through `gh` before aborting.
Cure: an explicit `preflight` python node is the graph's FIRST node
(`START → preflight → discover`), failing loudly when any of
`AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, `AZURE_MODEL` is unset. Tests
assert that on preflight failure neither discover, extract, nor any LLM
node executes.

### Azure pinning — compliance boundary, not preference

- All LLM nodes in the census invocation carry explicit `provider: azure`
  (model from `AZURE_MODEL`); nothing inherits the corpus_census
  `defaults: anthropic` block.
- Since corpus_census node-level provider is fixed in YAML, this requires
  either (a) a sibling `repo_census` graph variant with azure-pinned nodes,
  or (b) provider override at invocation. Option (a) is chosen: a thin
  `examples/demos/repo_census/graph.yaml` copy with `defaults.provider: azure`,
  both LLM nodes pinned, and no `fallback_provider` — authored via the sole
  route (`scripts/author.sh`, FR-767 sentinel).
- Fail-fast: via the explicit preflight node above (R-3) — NOT via
  llm_factory construction, which fires too late (after discovery).

### Authoring scope freeze (R-6)

Artifacts created via `scripts/author.sh` (verified by
`tmp/draft-authoring-report.md`, never exit code): exactly
`examples/demos/repo_census/graph.yaml` and
`examples/demos/repo_census/prompts/*.yaml` (purpose-judge + synthesis
prompts). NOT authorized: a generic provider override mechanism, graph
inheritance/template system, or any change to `corpus_census` provider
defaults or its existing demos. If implementation appears to require any
of these, enforcement stops and a separate FR enters the pipeline (C-6).

### Data locality (FR-874 precedent — this repo is PUBLIC) (R-5)

- Committed artifacts: generic adapters, graph, prompts, and a demo pinned
  to the named public-safe org **`sheikkinen`** (this repo's own GitHub
  owner, verified via `git remote get-url origin`) — the org string appears
  once as the demo fixture constant.
- Mechanical audit (test, not just PR review): a witness test scans all
  committed repo_census artifacts (`demo-output.log`, fixtures, README
  invocation, ledger/brief proofs) and fails if the demo source string is
  anything other than the pinned public org, or if output paths point
  outside `tmp/`/the demo tree.
- Human PR review of customer-identifier absence is recorded IN ADDITION
  to the mechanical check, not instead of it.
- Corp runs: org name, ledger, brief all via `--var`; outputs written under
  `tmp/` or a corp-side path. Never committed here.

### Invocation

```bash
AZURE_AI_ENDPOINT=... AZURE_AI_API_KEY=... AZURE_MODEL=<pinned-deployment> \
yamlgraph graph run examples/demos/repo_census/graph.yaml \
  --tool discover=adapters/gh-org-discover.tool.yaml \
  --tool extract=adapters/gh-repo-extract.tool.yaml \
  --var source="<org>:100" \
  --var rubric="state this repository's purpose in one sentence: what it does and for whom" \
  --var output_path=tmp/org-census-ledger.md \
  --var brief_path=tmp/org-census-brief.md \
  --var brief_rubric="Summarize this organization's repository portfolio: clusters of purpose, ownership concentration, active vs dormant ratio"
```

## Acceptance Criteria (frozen by judgement)

- [x] AC-01: The FR carries an in-body research record satisfying the FR-890 judge gate: five solution classes, precedent/evidence line per class, preserved disagreement, and an explicit `is_this_a_graph` answer (§ Research Record).
- [x] AC-02: `gh_org_discover` and `gh_repo_extract` implemented behind `.tool.yaml` manifests using fixed `gh` argument vectors; tests cover source parsing, max-repo bound, README/content bound, contributor bound, missing auth or failing `gh`, empty org, and malformed item refs.
- [x] AC-03: A repo-census preflight node runs before discovery and fails loudly when `AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, or `AZURE_MODEL` is missing; tests assert discovery, extraction, and LLM execution are not called on preflight failure.
- [x] AC-04: `examples/demos/repo_census/graph.yaml` and prompts authored via `scripts/author.sh`; `tmp/draft-authoring-report.md` records graph lint and smoke evidence.
- [x] AC-05: Every repo-census LLM node explicitly carries `provider: azure`, model from `AZURE_MODEL`, and no `fallback_provider`; a configuration test fails if any LLM node resolves to a non-Azure provider.
- [x] AC-06: The map prompt asks only for one-sentence repository purpose from the evidence bundle; a prompt/input test proves the LLM is not instructed to compute activity, persons, counts, percentages, or ownership.
- [x] AC-07: `reduce_repo_ledger` is LLM-free and validates the `RepoLedgerRow` Pydantic schema (`name`, `purpose`, `persons`, `activity`, `evidence_citation`, `model`, `prompt_version`, `source_index`); tests reject missing findings, duplicate findings, malformed activity, missing persons, empty purpose, and dangling citations.
- [x] AC-08: `activity` computed deterministically (`archived` / `pushed_at` within window → `active` / else `dormant`); boundary-date tests cover all three outcomes.
- [x] AC-09: `persons` copied verbatim from the top contributor API data, bounded to `MAX_PERSONS`; tests prove no LLM output can add, remove, or reorder persons.
- [x] AC-10: Corp brief rendered through the existing FR-895 citation boundary over the repo ledger; tests cover accepted citations and rejected fabricated repo citations.
- [x] AC-11: Committed demo uses only the pinned public-safe org; a mechanical witness test audits `demo-output.log`, fixtures, docs invocation, and proofs for the demo source string and output paths; human PR review recorded in addition.
- [x] AC-12: Changelog fragment, valid REQ/CAP wiring as needed, `@pytest.mark.req(...)` on new tests, FR status updates, and diary reflection included.

## Research Record: Solution Classes (R-1)

`is_this_a_graph`: **yes** — finite enumerable corpus (org repo list), one
independent semantic judgement per item, deterministic coverage/identity
checks: the canonical map shape (`reference/patterns/corpus-map-reduce.md:24-33`);
the chosen path is a corpus_census invocation, not a script or subagent fan-out.

| # | Solution class | Precedent / evidence | Disposition |
|---|---|---|---|
| 1 | Census-pipeline invocation: bind gh adapters to corpus_census slots, sibling azure-pinned graph | FR-892 (`feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:64-85`): "a new corpus supplies adapters rather than a new graph"; existing `git_*`/`pdf_*` proof adapters (`corpus_adapters.py:30-78`) | **CHOSEN** — reuses slots, map, reducer convention, FR-895 brief tail |
| 2 | Agent-loop analysis: extend `git-report` agent to iterate repos with gh tools | `examples/demos/git-report/graph.yaml:41-46` (agent, max_iterations 8) | REJECTED — unbounded/expensive per repo; census is a map shape, not an agent shape; no provider-pinning story |
| 3 | New standalone graph from scratch | corpus_census graph already implements every stage (`examples/demos/corpus_census/graph.yaml:63-145`) | REJECTED — duplication violates Commandment 4 |
| 4 | Framework provider-override flag (`--provider azure` at invocation) | node-level provider fixed in YAML (`graph.yaml:90-93,113-117`); llm_factory priority chain (CLAUDE.md provider selection) | REJECTED for now — wider blast radius than a pinned sibling graph. **Preserved disagreement:** if a third pinned-provider census appears, the override flag becomes the cheaper mechanism and should be re-proposed as its own FR (C-6 stop-line) |
| 5 | Deterministic script only, no LLM (gh + jq render the table) | `persons`/`activity` are fully mechanical from API fields | REJECTED — `purpose` requires reading README/description semantically; but this class WON the sub-question: everything except purpose/brief stays in code. **Preserved disagreement:** a purpose-less inventory script would satisfy "active or not" alone; the LLM is justified only by the purpose column and corp brief |

Additional disposition: run entirely in corp repo instead of yamlgraph —
PARTIAL; adapters/graph are generic and live here; org name, run config,
and all outputs stay corp-side (FR-874 boundary).

## Related

- [FR-899-org-repo-census-azure.judgement.md](FR-899-org-repo-census-azure.judgement.md) — APPROVED WITH REVISIONS; scope table D-1..D-8, conditions C-1..C-7
- FR-892 corpus_census tool-slot pipeline (base)
- FR-895 synthesize tail + citation boundary
- FR-874 (REJECTED) — public-repo data-locality precedent governing what may be committed
- FR-890 research sole route
- [examples/demos/corpus_census/](../examples/demos/corpus_census/), [examples/demos/git-report/](../examples/demos/git-report/)

## Implementation Status

- 2026-08-28: Judged APPROVED WITH REVISIONS (gpt-5.5 via scripts/judge.sh sole route). Revisions R-1..R-6 folded same day: research record with 5 solution classes + preserved disagreement (R-1); `reduce_repo_ledger` + `RepoLedgerRow` contract frozen (R-2); explicit preflight node before discovery — original llm_factory fail-fast claim was FALSE, provider construction happens after discovery (R-3); mechanical gh adapter contract with bounds/failure semantics (R-4); pinned public demo org + mechanical locality audit test (R-5); authoring scope freeze + not-authorized list (R-6).
- 2026-08-28: Enforced in worktree feat/fr-899. RED commit (37 witnesses, CAP-251/REQ-YG-626) then GREEN. Adapters in `corpus_adapters.py` + manifests; `examples/demos/repo_census/tools.py` (preflight, RepoLedgerRow, LLM-free reducer, FR-895 brief tail reuse). Graph + prompts + README authored via `scripts/author.sh` sole route (lint passed; real sheikkinen:2 smoke passed; one graph-only repair recorded: `module:` binding instead of `path:` to fix dynamic-loader Literal forward-ref). Demo run sheikkinen:5, brief ACCEPTED by citation boundary, committed as demo-output.log. 37/37 witnesses green. Deviations: none — scope as frozen.
