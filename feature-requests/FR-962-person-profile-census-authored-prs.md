# Feature Request: Person-Profile Census (authored-PRs across owner, pinned-azure)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved with Revisions — R-1..R-5 folded 2026-09-02
**Effort:** 0.75 days
**Requested:** 2026-09-02
**First consumer / first event:** the operator running an honest self-audit
of their own terveystalo footprint since 2026-06-01 immediately after this
FR is enforced — a compact, LLM-classified profile of what he actually shipped,
so he can be roasted by data instead of vibes. Public precedent runs against
`sheikkinen@sheikkinen`.
**Research:** in-body dispositioned research record (§ Research Record: Solution Classes) — five solution classes with precedent lines, preserved disagreement, and the `is_this_a_graph` answer. FR-890 equivalence: same shape as FR-899's accepted in-body record.
**Prior art:**
- [FR-892-corpus-census-pipeline-injected-adapters.md](FR-892-corpus-census-pipeline-injected-adapters.md) — base slot pipeline; this FR is a slot invocation, not a new pipeline.
- [FR-895-census-synthesize-tail.md](FR-895-census-synthesize-tail.md) — synthesize tail + citation boundary; reused; the brief-input adapter is amended (R-2) to identify citations by validated PR `url`, not by row index.
- [FR-899-org-repo-census-azure.md](FR-899-org-repo-census-azure.md) — DISTINCT unit: FR-899 censuses ORG REPOS (unit = repo, reduce target = org portfolio); FR-962 censuses AUTHORED PRS (unit = PR, reduce target = one person). Shared: azure-pinned governance envelope, gh-based adapters, sibling-graph authoring route, LLM-free reducer split. Not overlap — the reducer contract, ledger row model, mechanical rollup, and semantic vocabulary all differ.
- [FR-940-census-judgement-normalization.md](FR-940-census-judgement-normalization.md), [FR-943-census-row-failure-containment.md](FR-943-census-row-failure-containment.md) — precedent, NOT auto-inherited (R-3). FR-962's specialized `reduce_pr_ledger` re-implements the containment law in its own reducer: attributable model-owned failures become typed `row_failed` rows retaining mechanical PR fields; structural identity/completeness/bundle failures remain batch-fatal.
- [FR-893-diary-trap-census.md](FR-893-diary-trap-census.md) — invariant 8 hidden-canary precedent (family match, not exact token) — adopted verbatim (R-4).
- [FR-874-cross-device-agent-memory-sync.md](FR-874-cross-device-agent-memory-sync.md) — REJECTED precedent; its surviving rule (visibility verification as a written precondition before material is committed) is adopted here as R-5. The FR is not overturned.

## Summary

A person-profile invocation of the shared corpus_census pipeline: discover
slot enumerates PRs authored by a person in an owner within a date window via
`gh search prs` with explicit repository-visibility constraints, extract slot
builds a per-PR evidence bundle (title, body head, labels, state, timestamps,
diffstat, URL, base/head SHAs), a map LLM node classifies one intent per PR
(`problem_class`, `change_kind`, `surfaces`, one-sentence intent, one evidence
span from title or body), a deterministic code reducer computes mechanical
rollups (counts by repo, timespan, merge rate, monthly cadence, label /
change_kind / surfaces / problem_class histograms, top-N by size) and enforces
completeness + hidden-canary before rendering, and one FR-895 synthesize call
renders the person brief citing PR URLs. **Every LLM node pins
`provider: azure`** — corp footprint never transits the Anthropic default.

## Value Statement

The operator gets a skimmable, evidence-cited profile of their own PR
footprint (recurring themes, surface concentration, cadence, notable PRs)
produced entirely on the corp-approved Azure endpoint, from one command —
useful for self-audit, honest roasting, and periodic ownership review.

## Problem

The operator has an unknown-shape distribution of PRs across a customer org.
`gh search prs` returns hundreds of rows of JSON; skim reading loses signal,
and manually building a summary is slow, unrepeatable, and biased toward
whatever the operator remembers doing last week. The default LLM provider
is a data-governance violation for a customer org: PR bodies, review
comments, and diffs are corp data and must only be classified by the
corp-approved (pinned) Azure deployment.

## Ideal Result

One command against `<author>@<owner>:<since>` with an explicit
`visibility=["public"|"private"|"internal", ...]` yields:
1. a JSONL ledger + markdown table, one row per PR: `item_ref`, `repo`,
   `number`, `url`, `title`, `problem_class`, `change_kind`, `surfaces`,
   `intent`, `state`, `created_at`, `merged_at`, `additions`, `deletions`,
   `changed_files`, `labels`, `base_sha`, `head_sha`, `evidence_citation`,
   `classification_status`, `failure_reason` (nullable), `raw_finding`
   (nullable), `model`, `prompt_version`, `source_index`;
2. a mechanical rollup block at the head of the ledger (counts by repo,
   timespan, merge rate, monthly cadence, label / change_kind / surfaces /
   problem_class histograms, top-N PRs by `additions + deletions`,
   classification coverage — all LLM-free);
3. deterministic run metadata (normalized query, collection timestamp,
   discovered/classified/row-failed counts, actual map + synthesis call
   counts, Azure provider/model, prompt versions, run ID, artifact hash);
4. one person-level brief synthesized from the ledger by one azure call
   (recurring themes, surface concentration, cadence, notable PRs cited
   by validated PR URL);
5. a hidden canary (typed `{item_ref, surface_family}` — the family
   withheld from the map prompt) enforced before any artifact is
   emitted; failure raises before ledger or brief exists;
6. zero LLM calls to any provider other than the pinned Azure endpoint;
7. zero customer identifiers committed to this public repo.

The Proposed Solution is the minimal path back: two new adapters + one thin
azure-pinned sibling graph + one prompt pair + one specialized LLM-free
reducer. Nothing in the base corpus_census pipeline changes.

## Proposed Solution

Reuse the corpus_census slot pipeline (FR-892). Add PR-slot adapters next
to the existing `git_*`/`pdf_*`/`gh_*` ones in
[examples/demos/corpus_census/adapters/corpus_adapters.py](../examples/demos/corpus_census/adapters/corpus_adapters.py).
Author a thin azure-pinned sibling graph
`examples/demos/person_profile_census/graph.yaml` via `scripts/author.sh`,
following FR-899's authoring pattern.

### Adapters (slot contract per FR-892: state-dict in, list/str out)

- **`gh_authored_prs_discover(state)`** — `source` grammar:
  `<author>@<owner>:<since>`; `<since>` MUST be an ISO `YYYY-MM-DD` date
  (validated). Malformed source raises `ValueError`. Additional
  required input: `visibility` — a non-empty JSON list drawn from
  `{"public","private","internal"}`, unique under casefold. Fixed argv
  `gh search prs --author <a> --owner <o> --created >=<since> --limit
  <MAX_PRS+1> --visibility <v1> [--visibility <v2>...]
  --json repository,number` via `subprocess.run` (no shell),
  `timeout=60`, `check=True`. **Overflow detection (R-1):** query one
  more than the ceiling; if the response contains `MAX_PRS + 1 = 501`
  items, raise `ValueError` BEFORE returning — never slice. Empty
  result raises `ValueError`. Item identity format:
  `<owner>/<repo>#<number>`. Discovery rejects duplicate identities
  and returns the sorted set.

- **`gh_pr_extract(state)`** — `item` grammar:
  `<owner>/<repo>#<positive-number>`; malformed ref raises
  `ValueError`. Fixed argv `gh api repos/<owner>/<repo>/pulls/<number>`
  via `subprocess.run` (no shell), `timeout=60`, `check=True`. A 404
  raises `CalledProcessError` — no silent skip. Bounds:
  `MAX_BODY_CHARS = 3000`, `MAX_LABELS = 10`, blob cap
  `MAX_CHARS = 4000`. Returns ONE JSON text blob with exactly these
  keys: `repo` (`<owner>/<repo>`), `number` (positive int), `url`
  (validated `https://github.com/<owner>/<repo>/pull/<number>` shape),
  `title`, `state` (mechanical derivation: `merged` when `merged_at`
  is non-null, else the lowercased API `state` in `{open, closed}`),
  `created_at` (ISO), `merged_at` (ISO or `None`), `labels` (first
  `MAX_LABELS` API labels — order and values verbatim from the API),
  `body_head` (up to `MAX_BODY_CHARS`), `additions` (non-negative int),
  `deletions` (non-negative int), `changed_files` (non-negative int),
  `base_sha` (40-hex), `head_sha` (40-hex). This blob is both the LLM
  evidence bundle and the reducer's mechanical-field source. If any
  fixed mechanical field cannot be validated, extraction fails; only
  `body_head` may be truncated for the blob cap.

Test surface: malformed `source` (missing `@`, missing `:`, non-ISO
`since`, unknown `visibility` value, missing `visibility`), empty
result, overflow at 501, missing/failing `gh`, bounds enforcement,
malformed item refs, 404 PR, empty body PR, invalid mechanical fields.

### Judgement split (cheap-map, code-reduce, one-judgement-tail)

- **Map LLM node (pinned azure):** ONE structured judgement per PR —
  `problem_class` (one of a bounded vocabulary passed as
  `--var problem_labels=`, JSON list of non-empty strings, unique
  under casefold), `change_kind` (one of the frozen enum
  `feat|fix|docs|refactor|chore|infra|ops|test|revert`), `surfaces`
  (bounded list, 1..5 distinct members drawn from
  `--var surface_labels=`, unique under casefold), one-sentence
  `intent` (≤ 280 chars), and one `evidence_span` (non-empty substring
  of the extracted `title` OR `body_head`). Rubric passed as
  `--var rubric=`. The prompt receives neither rollup instructions
  nor the hidden-canary expected family.

- **Code reduce (LLM-free, specialized — R-3):** the mechanical rollup
  — total PRs, repos-touched-with-counts, timespan (min/max
  `created_at`), merge rate, monthly cadence buckets, label /
  `change_kind` / `surfaces` / `problem_class` histograms, top-N PRs
  by `additions + deletions`, classification coverage (`judged /
  total`). Semantic histograms EXCLUDE `row_failed` classifications.
  The LLM is never asked to compute any of these.

- **Synthesize tail (pinned azure):** existing FR-895 tail with an
  amended brief-input adapter that identifies each ledger row by
  validated PR `url` (not by row index). Citation boundary rejects
  fabricated URLs — brief cites real PR URLs or the run rejects.

### Ledger contract (specialized `PRLedgerRow` — R-2 + R-3)

New code surface: `examples/demos/person_profile_census/tools.py` —
`reduce_pr_ledger` (LLM-free, specialized) and `PRLedgerRow`:

```python
class PRLedgerRow(BaseModel):
    item_ref: str                    # "<owner>/<repo>#<number>", discovery
    repo: str                        # "<owner>/<repo>"
    number: int                      # positive
    url: HttpUrl                     # validated PR URL — citation identity
    title: str
    state: Literal["open","closed","merged"]      # mechanical (derived)
    created_at: str                                # ISO, mechanical
    merged_at: str | None                          # ISO or None, mechanical
    additions: int                                 # non-negative, mechanical
    deletions: int                                 # non-negative, mechanical
    changed_files: int                             # non-negative, mechanical
    labels: list[str]                              # <= MAX_LABELS, verbatim
    base_sha: str                                  # 40-hex, mechanical
    head_sha: str                                  # 40-hex, mechanical
    classification_status: Literal["judged","row_failed"]  # R-3 discriminator
    problem_class: str | None                              # LLM, judged only
    change_kind: (
        Literal["feat","fix","docs","refactor","chore","infra","ops",
                "test","revert"] | None
    )                                                       # LLM, judged only
    surfaces: list[str] | None                             # LLM, judged only
    intent: str | None                                     # LLM, judged only
    evidence_citation: str | None                          # LLM span, judged
    failure_reason: str | None                             # row_failed only
    raw_finding: str | None                                # row_failed only
    model: str                       # map model id (provenance)
    prompt_version: str
    source_index: int                # provenance: map index
```

**Row-level containment (R-3 folded — not inherited from FR-943):**
attributable model-owned failures — a `_map_error` with a valid source
index, or a Pydantic validation error rooted in `problem_class`,
`change_kind`, `surfaces`, `intent`, `evidence_span` — emit exactly one
`classification_status="row_failed"` row retaining ALL mechanical PR
fields; `failure_reason` is a bounded <= 240-char reason;
`raw_finding` preserves the model output deterministically. Semantic
LLM fields are nullable ONLY under that status.

**Batch-fatal (never contained):** non-dict findings; invalid, missing,
duplicate, or out-of-range source indexes; duplicate findings for one
source; missing findings for a discovered item ref; a mechanical bundle
that fails extractor validation; a `row_failed` replacement row that
itself fails validation; a `problem_labels` / `surface_labels` input
that is empty, non-JSON, non-list, or non-unique under casefold.

**Vocabulary discipline:** judged rows enforce canonical
`problem_class` value (case-insensitive lookup against
`problem_labels`, emit caller's canonical spelling — misses are
`row_failed`), 1..5 distinct canonical `surfaces` (same rule),
frozen `change_kind` enum literal, `intent` non-empty single line
<= 280 chars, `evidence_span` mechanically verified as a substring of
the extracted `title` or `body_head`.

Artifacts: `<output_path>` markdown table with mechanical rollup head
+ sibling `.jsonl` (one `PRLedgerRow` per line) + run metadata JSON.

### Azure + visibility preflight (R-5)

Sibling `person_profile_census` graph starts with `preflight` python
node (reuse FR-899's implementation shape). Fails when any of
`AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, `AZURE_MODEL` is unset OR
when `visibility` is missing or contains any value outside
`{"public","private","internal"}`. Tests assert discover / extract /
LLM never run on preflight failure.

### Hidden-canary gate (R-4)

`canary` input is a typed object:
`{"item_ref": "<owner>/<repo>#<number>", "surface_family": ["ci", "infra"]}`.
`surface_family` is a non-empty list of >= 1 canonical vocabulary
members. Before ledger or brief artifacts are emitted, the reducer
gate fails when:
- the item is absent from the frozen discovery set, OR
- the judged row's `surfaces` shares no member with `surface_family`
  under the FR-893 casefolded substring-family rule, OR
- the canary row is `row_failed`.

The canary is passed to the reducer, NOT to the map prompt (verified
by prompt-input test).

Public demo pins the canary to a real public PR + a family verified
by hand once in a committed fixture (e.g.
`examples/demos/person_profile_census/fixtures/canary.yaml`).

### Azure pinning — compliance boundary

- All LLM nodes carry explicit `provider: azure`, model from
  `AZURE_MODEL`, no `fallback_provider`.
- Sibling graph authored via `scripts/author.sh` sole route
  (FR-767 sentinel).
- Fail-fast: via the preflight node (llm_factory fires too late).
- Both map stages carry `max_items: 500` frozen in YAML (R-1); a
  fixture test with 500 items maps all 500, and a 501-item fixture
  fails discovery before any map.

### Authoring scope freeze

Artifacts created via `scripts/author.sh` (verified by
`tmp/draft-authoring-report.md`, never exit code): exactly
`examples/demos/person_profile_census/graph.yaml` and
`examples/demos/person_profile_census/prompts/*.yaml`
(pr-classify + synthesis prompts). NOT authorized:
generic provider override mechanism, graph inheritance/template
system, changes to `corpus_census` or `repo_census` defaults or
demos, framework map-truncation changes, generic failure-containment
or classification APIs. If implementation appears to require any of
these, enforcement stops and a separate FR enters the pipeline.

### Data locality (R-5, FR-874 rejected-precedent surviving rule)

- Public demo pinned to `sheikkinen@sheikkinen:2026-06-01` with
  `visibility=["public"]` — the operator's own public GitHub owner.
- Mechanical locality audit test: scans every committed
  `person_profile_census` surface (graph defaults, README commands,
  demo output, ledger/brief proofs, fixtures, run metadata) and
  fails if the source is not the pinned public demo string, if
  `visibility` != `["public"]`, if any ledger row's repo owner is
  not `sheikkinen`, or if any output path escapes `tmp/` / the
  demo tree.
- Corp runs: author, owner, since, rubrics, canary, visibility all
  via `--var`; outputs written under `tmp/` or a corp-side path.
  Never committed here.

### Invocation

Public demo (committed):

```bash
yamlgraph graph run examples/demos/person_profile_census/graph.yaml \
  --tool discover=examples/demos/corpus_census/adapters/gh-authored-prs-discover.tool.yaml \
  --tool extract=examples/demos/corpus_census/adapters/gh-pr-extract.tool.yaml \
  --var source='sheikkinen@sheikkinen:2026-06-01' \
  --var visibility='["public"]' \
  --var rubric='Classify this PR: problem_class, change_kind, surfaces, one-sentence intent, one evidence span from title or body.' \
  --var problem_labels='["infra","doctrine","research","enforcement","cleanup"]' \
  --var surface_labels='["backend","infra","docs","tests","tooling","ci","graphs"]' \
  --var canary='{"item_ref":"sheikkinen/yamlgraph#555","surface_family":["ci","infra"]}' \
  --var output_path=tmp/person-profile-sheikkinen.md \
  --var brief_path=tmp/person-profile-sheikkinen.brief.md \
  --var brief_rubric='Profile this engineer from their PR footprint: recurring themes, surface concentration, cadence, notable PRs. Cite PR URLs. Be honest — flag anti-patterns (churn, incomplete arcs, retitles).'
```

Corp run (never committed):

```bash
AZURE_AI_ENDPOINT=... AZURE_AI_API_KEY=... AZURE_MODEL=<pinned-deployment> \
yamlgraph graph run examples/demos/person_profile_census/graph.yaml \
  --tool discover=examples/demos/corpus_census/adapters/gh-authored-prs-discover.tool.yaml \
  --tool extract=examples/demos/corpus_census/adapters/gh-pr-extract.tool.yaml \
  --var source='<author>@<owner>:<since>' \
  --var visibility='["private","internal"]' \
  --var rubric='...' \
  --var canary='{"item_ref":"...","surface_family":[...]}' \
  --var output_path=tmp/person-profile-<author>.md \
  --var brief_path=tmp/person-profile-<author>.brief.md \
  --var brief_rubric='...'
```

## Acceptance Criteria (revised — R-1..R-5 folded)

- [ ] AC-01: The FR retains its substantive in-body research record with five solution classes, precedent/evidence per class, preserved disagreement, and an explicit `is_this_a_graph` answer; the FR-874 citation resolves to `FR-874-cross-device-agent-memory-sync.md` and records its rejected-precedent status.
- [ ] AC-02: Discovery validates `<author>@<owner>:<since>` with an ISO `YYYY-MM-DD` date, fixed no-shell `gh` argv, required `visibility` enum list, timeout/check semantics, loud empty result, stable sorted identities, and duplicate rejection.
- [ ] AC-03: Discovery reads at most 501 results and rejects 501 before extraction or LLM execution; extraction and judgement maps both declare `max_items: 500`; a 500-item fixture maps all 500 and a 501-item fixture emits no output artifact.
- [ ] AC-04: `gh_pr_extract` validates `<owner>/<repo>#<positive-number>`, fails loudly on missing/failing `gh` and 404, and emits exactly the revised bounded bundle including `url`, `base_sha`, and `head_sha`; tests cover body, label, and final-blob bounds, including an empty-body PR.
- [ ] AC-05: The graph's first node is Azure + visibility preflight; missing `AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, `AZURE_MODEL`, or a required/valid `visibility` prevents discovery, extraction, and every LLM call.
- [ ] AC-06: Graph and prompt artifacts are authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` records lint plus a smoke that verifies artifact content, not exit code.
- [ ] AC-07: Every LLM node explicitly resolves to `provider: azure` and `AZURE_MODEL`, has no non-Azure fallback, and a configuration test fails on any other resolution.
- [ ] AC-08: The map prompt asks only for `problem_class`, `change_kind`, `surfaces`, `intent`, and an evidence span from title or body; a prompt-input test proves the prompt receives neither rollup instructions nor the canary's expected family.
- [ ] AC-09: Reducer entry validates both vocabularies; judged rows enforce canonical `problem_class`, one-to-five canonical distinct surfaces, the frozen `change_kind` enum, bounded single-line intent, and mechanically verified evidence substring.
- [ ] AC-10: `PRLedgerRow` validates URL, base/head SHAs, timestamps, non-negative size fields, derived state, capped verbatim-order labels, provenance, and the judged/row-failed discriminator; tests prove no LLM output can add, remove, or alter mechanical fields.
- [ ] AC-11: Attributable model/map failures produce typed `row_failed` rows with mechanical fields, bounded reason, and raw evidence; structural index/completeness/bundle failures abort the batch. Tests cover every class named in the proposal.
- [ ] AC-12: Code computes total PRs, repo counts, timespan, merge rate, monthly cadence, label / change-kind / surfaces / problem-class histograms, top-N by additions + deletions, and classification coverage from frozen fixtures; semantic histograms exclude row-failed classifications.
- [ ] AC-13: Machine-readable run metadata records normalized query, collection timestamp, discovered/classified/row-failed counts, actual call totals, Azure provider/model, prompt versions, run ID, and artifact hash; fixture tests assert exact values.
- [ ] AC-14: FR-895 synthesis consumes validated URL-bearing ledger rows; accepted real URLs render and fabricated PR URLs reject before an accepted brief exists.
- [ ] AC-15: The hidden-canary gate consumes a typed `{item_ref, surface_family}` object withheld from the map prompt and emits no ledger or brief when the item is absent or the semantic family misses; exact and drifted-family matches pass.
- [ ] AC-16: Public demo discovery passes exactly `visibility=["public"]`; the locality audit scans all named committed person-profile surfaces and rejects any other visibility, source, repository owner, or output root. Corp artifacts and identifiers remain uncommitted.
- [ ] AC-17: Changelog fragment, CAP/REQ wiring, `@pytest.mark.req(...)` on every new test, FR status/decision/deviation record, authoring report, and diary reflection are included.

## Alternatives Considered

See § Research Record: Solution Classes.

## Related

- [reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md) — 6-stage architecture pattern with 8 invariants.
- [examples/demos/corpus_census/](../examples/demos/corpus_census/) — base pipeline.
- [examples/demos/repo_census/](../examples/demos/repo_census/) — FR-899 sibling; direct authoring precedent.
- [feature-requests/FR-962-person-profile-census-authored-prs.judgement.md](FR-962-person-profile-census-authored-prs.judgement.md) — judgement; R-1..R-5 folded into this document.

## Research Record: Solution Classes (FR-890 equivalent)

`is_this_a_graph`: **yes** — finite enumerable corpus (a person's PRs
in an owner within a window), one independent structured judgement per
PR, deterministic coverage/identity/aggregate arithmetic:
canonical map shape ([reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md#the-six-stages)).
Chosen path is a corpus_census slot invocation with a thin azure-pinned
sibling graph — not a script, subagent fan-out, or new pipeline.

Prior art retrieved for this brief (filename-noun IDF, `corpus`/`census`/
`profile`/`gh_search`): FR-892 (base), FR-895 (tail), FR-899 (repo unit),
FR-940 (label normalization — precedent NOT inheritance), FR-943 (row
containment — precedent NOT inheritance), FR-893 (invariant-8 canary),
FR-874 (rejected — surviving visibility rule adopted here). Each
dispositioned in § Prior art above.

| # | Solution class | Precedent / evidence | Disposition |
|---|---|---|---|
| 1 | Census-pipeline invocation: bind PR adapters to corpus_census slots + thin azure-pinned sibling graph | FR-892 (slot pipeline); FR-899 (identical shape for repo unit); [reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md#the-six-stages) | **CHOSEN** — reuses slots, map, reducer convention, FR-895 tail; adds only what the new unit requires (URL-identified citations, PR-shaped row model, PR-specific mechanical rollup, PR canary) |
| 2 | Agent-loop analysis: extend an agent with `gh` tools and iterate PRs | `examples/demos/git-report/graph.yaml` (agent, max_iterations 8) | REJECTED — unbounded/expensive per PR; the shape is a map, not an agent; no provider-pinning story; violates cost contract |
| 3 | New standalone graph from scratch (duplicate the corpus_census stages) | corpus_census + repo_census already implement every stage | REJECTED — duplication violates Commandment 4 |
| 4 | Framework-level provider-override flag (`--provider azure` at invocation) | FR-899 preserved this disagreement (§ Research Record class 4): wider blast radius than a pinned sibling graph; deferred until a third pinned-provider census appears | REJECTED for now — this IS the third pinned-provider census after FR-899's `repo_census` if we count the base corpus_census as one. **Preserved disagreement:** this FR marks the crossing of the FR-899 stop-line; a separate FR proposing the override flag should be filed as a follow-up rather than expanded into this scope |
| 5 | Deterministic script only, no LLM (gh + jq render the table and rollup) | rollup, state, timestamps, sizes, labels are fully mechanical from the API | REJECTED — `problem_class`, `change_kind`, `surfaces`, `intent`, and the person brief need semantic reading of PR title/body. But this class WON the sub-question: everything except those four map fields + the brief stays in code. **Preserved disagreement:** a rollup-only script would satisfy the "what did I ship" question at zero LLM cost; the LLM is justified only by the classification columns and the brief |

Additional disposition: run entirely in a corp-side clone instead of
yamlgraph — PARTIAL; adapters/graph/prompts are generic and live here
(public demo pinned to `sheikkinen@sheikkinen`, `visibility=["public"]`);
corp runs pass author, owner, since, visibility, rubrics via `--var`
and write outputs to a corp-side path (R-5 boundary).

## Implementation Status

- 2026-09-02: Filed and routed through `scripts/judge.sh` (sole route).
- 2026-09-02: Judgement APPROVED WITH REVISIONS — five revisions R-1..R-5, eight gate conditions C-1..C-8 (draft judgement: `tmp/draft-judgement.md`). Folded into this FR:
  - R-1: overflow detection (`MAX_PRS+1`, reject on 501); `max_items: 500` frozen on both map stages; deterministic run metadata added to ideal result + AC-13.
  - R-2: added `url`, `base_sha`, `head_sha` to bundle and `PRLedgerRow`; `state` is mechanically derived, not verbatim; `labels` capped verbatim; dropped `linked issues` claim; `evidence_span` may come from title or body; mechanical validation frozen.
  - R-3: deleted the FR-940/FR-943 auto-inheritance claim; specialized `reduce_pr_ledger` re-implements containment with `classification_status` discriminator; vocabulary discipline (canonical `problem_class` + `surfaces`) frozen; structural vs attributable failures separated in AC-11.
  - R-4: canary is a typed `{item_ref, surface_family}` object; family match per FR-893; withheld from map prompt; AC-15 replaces the old circular AC-10.
  - R-5: FR-874 citation corrected to `cross-device-agent-memory-sync.md` (rejected precedent); `visibility` required in discovery + preflight; mechanical locality audit expanded (AC-16).
