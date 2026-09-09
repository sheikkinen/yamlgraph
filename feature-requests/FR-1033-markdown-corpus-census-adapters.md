# Feature Request: FR-1033 markdown corpus adapters for the census

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.25 days
**Requirement:** REQ-YG-674 (new), owned by a new capability **CAP-270 markdown
corpus census binding**. (CAP-269 is reserved by FR-1032 and not yet created.)
**Requested:** 2026-09-09
**First consumer / first event:** classifying harvested public `CLAUDE.md`
files under the invariant-store / state-log / description scheme, at the moment
the census is bound to a local directory of markdown instead of a hand-rolled
script. The scheme is
[docs/diary/2026-09-09-agent-file-triage…](../docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md)
(merged `24e90662`).
**Research:** in-body solution-class table below (FR-889 style).
**Prior art:** [FR-892](FR-892-corpus-census-pipeline-injected-adapters.md) —
establishes that a new corpus supplies adapters, not a new graph; this FR is
one such binding. [FR-899](FR-899-org-repo-census-azure.md) — the precedent for
a per-corpus capability owning a binding.
[FR-1032](FR-1032-census-adapter-owned-extract-cache.md) — caches
`gh_repo_extract`; unrelated here, because a local corpus needs no cache.

## Summary

Add `md_discover` and `md_extract` to
`examples/demos/corpus_census/adapters/corpus_adapters.py`, mirroring the
existing `pdf_discover` / `pdf_extract` pair, plus their two tool manifests.
This binds the existing census graph to a directory of markdown files. No
graph, prompt, or framework change.

## Value Statement

The census already supports PDF, git, GitHub and diary corpora. Markdown files
on disk — the most common shape a corpus arrives in — have no adapter, so every
markdown census so far has been a hand-rolled script.

## Problem

There is no local-markdown binding. `pdf_discover` globs `*.pdf` and
`pdf_extract` requires `pypdf` (`corpus_adapters.py:33-57`). The only
directory-of-text-files pair is `fixtures/fixture_tools.py`, which globs
`*.txt` and exists to serve the demo's tests.

The consequence is concrete and recent: a 620-file public `CLAUDE.md` corpus
was collected and analysed with an ad-hoc script that duplicated the census
topology — discover, extract, map, reduce — and omitted its judgement
normalisation and citation boundary. That is the failure recorded in the diary
entry above.

## Ideal Result

A directory of markdown files is a first-class census corpus, bound with two
`--tool` flags and no new graph. The markdown census reaches the same
normalised ledger and citation-validated brief as every other corpus, so no
future markdown analysis has a reason to be a script.

## Proposed Solution

Two functions in `corpus_adapters.py`, next to the PDF pair:

```python
MD_MAX_ITEMS = 200   # the graph's own map ceiling (graph.yaml config)

def md_discover(state):  # source: a directory -> sorted *.md paths, bounded
def md_extract(state):   # item: a path -> UTF-8 text, bounded by MAX_CHARS
```

Plus `adapters/md-discover.tool.yaml` and `adapters/md-extract.tool.yaml`.

```bash
yamlgraph graph run examples/demos/corpus_census/graph.yaml \
  --tool discover=examples/demos/corpus_census/adapters/md-discover.tool.yaml \
  --tool extract=examples/demos/corpus_census/adapters/md-extract.tool.yaml \
  --var source=<dir> --var provider=inception --var model=mercury-2.5 \
  --var labels='["invariant-store","state-log","description"]' \
  --var rubric="…" --var output_path=… \
  --var brief_path=… --var brief_rubric="…"
```

**The 200 cap is deliberate, not a limitation.** `graph.yaml` sets
`max_map_items: 200` and both map nodes carry `max_items: 200`. Raising it is a
material graph-artifact change requiring the authoring route, and it is not
wanted: the diary entry's own finding is that for extracting practice the
distribution is the wrong object and the tail is the object. A cap forces the
operator to select, which is what the analysis needs. Larger corpora are run as
sharded directories.

**Provenance is honestly weaker than the pattern's freeze stage.** Items are
file paths, as with every existing local adapter. This FR adds **no content
digest**, so a census records which paths it read, not which bytes. The corpus
pattern asks for immutable identity or recorded snapshot data
(`reference/patterns/corpus-map-reduce.md:57-82`); a directory the operator
controls does not meet that bar. Stating it rather than claiming compliance.

## Acceptance Criteria

Test surface: `tests/unit/test_markdown_corpus_adapters.py`, every test tagged
`@pytest.mark.req("REQ-YG-674")`.

1. `md_discover` returns `*.md` paths sorted, and only `*.md`.
2. `md_discover` raises `NotADirectoryError` for a non-directory source and
   `ValueError` for a directory containing no markdown.
3. A directory holding more than `MD_MAX_ITEMS` files yields exactly
   `MD_MAX_ITEMS`, deterministically the first by sort order.
4. `md_extract` returns UTF-8 text bounded by `MAX_CHARS`, and raises
   `ValueError` for an empty or whitespace-only file.
5. `md_extract` raises `FileNotFoundError` for a missing path; a file with
   invalid UTF-8 bytes is decoded with replacement rather than crashing.
6. End-to-end: the census runs over a temporary markdown corpus with a `labels`
   vocabulary, and every ledger row carries a label from that vocabulary or
   `abstain` — proving the existing FR-940 normalisation applies unchanged.
7. Neither `graph.yaml` nor any prompt is modified, so no authoring report is
   required. Asserted by the PR diff.
8. Wiring: `CAP-270` created owning `REQ-YG-674` with modules for
   `corpus_adapters.py` and the new test file; changelog fragment; FR
   implementation record; diary distillation.

**Not authorized:** graph or prompt changes; raising the map ceiling; a GitHub
file extractor; caching; changes to the fixture adapters, the PDF/git/GitHub
adapters, the reducer, or the ledger schema.

## Research: solution classes

`is_this_a_graph`? **Yes — and it already exists.** `corpus_census` is the
graph; per FR-892 a new corpus supplies adapters, not a new graph. This FR
supplies adapters. That answer is the whole point of the FR: the prior attempt
at this corpus was a script.

| # | Class | Evidence | Disposition |
|---|---|---|---|
| 1 | **New `md_discover`/`md_extract` in `corpus_adapters.py`** | Mirrors `pdf_discover`/`pdf_extract` (`corpus_adapters.py:33-57`) | **Chosen.** Precedented location and shape; no graph change; smallest surface that makes markdown first-class. |
| 2 | Bind the fixture adapters directly | `fixtures/fixture_tools.py` `extract` reads any text file unchanged | Rejected: fixtures are test scaffolding. A demo depending on them breaks the moment a test needs the fixture changed. |
| 3 | Hand-rolled script | Done this session; duplicated the topology and dropped judgement normalisation and the citation boundary | Rejected. It is the defect this FR exists to retire. |
| 4 | GitHub-native discover/extract fetching files live | Would need the file extractor FR-1032 bars, plus a cache | Rejected **for now**: the corpus is already local. This is the honest end state, not the next step. |
| 5 | Add a glob parameter to `pdf_discover` | `corpus_adapters.py:33-42` | Rejected: widens a working adapter's contract for one caller, and `pdf_extract` would still need `pypdf`. |
| 6 | Raise the map ceiling to fit 620 items | `graph.yaml` `max_map_items: 200` | Rejected: material graph change requiring the authoring route, and 200 selected items beats 620 unselected under this corpus's own finding. |

**Preserved disagreement.** Class 4 is defensible as the real target: a census
that cannot refresh its own corpus depends on a snapshot somebody made by hand,
which is precisely the provenance weakness disclosed above. The counter is that
it needs two FRs that do not exist yet, while the corpus does. Class 6 is
defensible if the goal were corpus-wide statistics rather than practice
extraction; it is not.

## Related

- FR-892 slot binding; FR-895 synthesize tail; FR-940 judgement normalisation.
- [reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md)
