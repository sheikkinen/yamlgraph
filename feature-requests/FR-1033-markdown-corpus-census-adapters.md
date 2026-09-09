# Feature Request: FR-1033 bounded local-Markdown corpus adapters for the census

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented (2026-09-09)
**Effort:** 0.25 days
**Requirement:** REQ-YG-674 (new), owned by a new capability **CAP-270 bounded
local-Markdown census binding**, listing the adapter module, both manifests,
and the new test module. (CAP-269 is reserved by FR-1032; CAP-249 is untouched.)
**Requested:** 2026-09-09
**First consumer / first event:** classifying a **bounded** directory of
harvested public `CLAUDE.md` files — at most 200 files, each within the
declared character ceiling — under the invariant-store / state-log /
description scheme, at the moment the census is bound to that directory
instead of a hand-rolled script. Scheme:
[docs/diary/2026-09-09-agent-file-triage…](../docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md)
(merged `24e90662`).
**Research:** in-body solution-class table below (FR-889 style).
**Prior art:** [FR-892](FR-892-corpus-census-pipeline-injected-adapters.md) —
a new corpus supplies adapters, not a new graph; this is one such binding.
[FR-899](FR-899-org-repo-census-azure.md) — precedent for a per-corpus
capability owning a binding.
[FR-1032](FR-1032-census-adapter-owned-extract-cache.md) — caches
`gh_repo_extract`; unrelated, because a local corpus needs no cache.

## Summary

Add `md_discover` and `md_extract` to
`examples/demos/corpus_census/adapters/corpus_adapters.py`, plus their two tool
manifests, binding the existing census graph to a **bounded** directory of
markdown files. Both adapters fail closed rather than silently shrinking the
population or the content. No graph, prompt, reducer, or ledger change.

## Value Statement

The census supports PDF, git, GitHub and diary corpora. A directory of markdown
files — the commonest shape a corpus arrives in — has no adapter, so markdown
censuses have been hand-rolled scripts.

## Problem

There is no local-markdown binding. `pdf_discover` globs `*.pdf` and
`pdf_extract` needs `pypdf` (`corpus_adapters.py:33-57`). The only
directory-of-text pair is `fixtures/fixture_tools.py`, which exists to serve
the demo's own tests.

The consequence is recent and concrete: a 620-file public `CLAUDE.md` corpus
was collected and analysed with an ad-hoc script that duplicated the census
topology — discover, extract, map, reduce — while omitting its judgement
normalisation and citation boundary.

## Ideal Result

A bounded directory of markdown files is a first-class census corpus, bound
with two `--tool` flags and no new graph. Every file the census reports on is a
file it read in full, verified byte-for-byte against what discovery saw. Any
directory or file the adapters cannot honestly cover stops the run with a
named error before a single model call.

## Proposed Solution

Two functions in `corpus_adapters.py`, beside the PDF pair, and a typed item
reference.

**Fail closed on population (R-1).** `md_discover` returns *all* sorted `*.md`
items when the directory fits, and raises `ValueError` naming the observed
count and the ceiling when it does not. It never returns a prefix. The
lexicographically-first-200 slice proposed earlier was silent population loss,
contradicting the corpus contract that completeness is part of the result
(`corpus-map-reduce.md:24-33,198-220`) — and it contradicted its own rationale,
since an alphabetical prefix is not the tail. `diary_adapters.py:25-42` is the
aligned precedent: reject the over-cap batch and require the operator to narrow
the source.

Sharding stays operator-controlled and outside this FR. **Each shard is an
independently complete run.** Concatenated shard outputs are not one reconciled
census: this FR adds no cross-shard identity, coverage, or reduction step.

**Freeze identity at discovery, verify at extraction (R-2).** A typed item
reference carries exactly `path`, raw-byte `sha256`, and raw-byte `bytes`.
`md_discover` reads each selected regular file once, computes them, and returns
a deterministic serialization accepted by the existing string slot contract.
`md_extract` parses and validates that reference, reads the bytes once, and
raises a specific `ValueError` if either byte count or digest differs — *before*
decoding. Invalid UTF-8 is decoded with replacement only after raw-byte
identity is verified. The serialized reference is the ledger's `item_ref`, so
neither graph nor ledger changes.

**Reject oversized files, never truncate (R-3).** `MD_MAX_CHARS = 65536`, a
Markdown-specific ceiling covering the observed corpus (largest file 57,151
bytes). A decoded file exceeding it raises, naming path, observed character
count, and ceiling. Extraction completes before `judge_items` and uses
`on_error: fail` (`graph.yaml:75-89,136-141`), so an invalid run stops before
any model call. Truncating would produce a valid-looking ledger row for a
file's head while attributing the judgement to the whole file — a
plausible-wrong-answer, not merely weaker provenance. The first-consumer
evidence is precisely a case in point: a 306 KB file whose valuable rules are
spread throughout. **This adapter does not cover that file**, and says so by
failing rather than by classifying its first 64 KB.

```bash
yamlgraph graph run examples/demos/corpus_census/graph.yaml \
  --tool discover=examples/demos/corpus_census/adapters/md-discover.tool.yaml \
  --tool extract=examples/demos/corpus_census/adapters/md-extract.tool.yaml \
  --var source=<bounded dir> --var provider=inception --var model=mercury-2.5 \
  --var labels='["invariant-store","state-log","description"]' \
  --var rubric=… --var output_path=… \
  --var brief_path=… --var brief_rubric=…
```

**What this does not cover.** Recursive directory trees, files over the
ceiling, cross-shard reconciliation, and live GitHub harvesting. Oversized-file
partitioning and file-level reconciliation are a separate graph concern, not
authorized here.

## Acceptance Criteria

Test surface: `tests/unit/test_markdown_corpus_adapters.py`, every test tagged
`@pytest.mark.req("REQ-YG-674")`.

1. `md_discover` returns every `*.md` path, sorted, and only `*.md`, for a
   directory at or under the ceiling.
2. A directory exceeding the ceiling raises `ValueError` naming the observed
   count and the ceiling. No prefix is returned under any input.
3. `md_discover` raises `NotADirectoryError` for a non-directory source and
   `ValueError` for a directory containing no markdown.
4. Item references serialize deterministically and round-trip, including
   non-ASCII paths and non-ASCII file bytes.
5. `md_extract` raises a specific `ValueError` when the file mutates between
   discovery and extraction — one case for byte-count mismatch, one for digest
   mismatch — and when the reference itself is malformed.
6. `md_extract` raises `ValueError` naming path, character count and ceiling
   for a file over `MD_MAX_CHARS`; nothing is truncated.
7. A file with invalid UTF-8 decodes with replacement, but only after raw-byte
   identity verification succeeds.
8. End-to-end: both manifests load through the existing slot-binding path and
   the **unchanged** graph runs over at least two temporary markdown files with
   a deterministic stubbed LLM boundary. Asserts discovered count equals
   ledger-row count; ledger item references carry the expected path, digest and
   byte identities; every row label is from the supplied vocabulary or
   `abstain`; both output artifacts exist.
9. Manifest assertions: runtime type, module-relative path, and function name
   for each of the two manifests.
10. Wiring: `CAP-270` created owning `REQ-YG-674`, listing the adapter module,
    both manifests, and the test module; changelog fragment; FR implementation
    record; diary distillation.

**Frozen scope condition** (not an acceptance test — a diff is review evidence,
not a behavioural witness): `graph.yaml`, prompts, the reducer, and the ledger
schema are unchanged, so no authoring report is required.

**Not authorized:** graph or prompt changes; raising the map ceiling; a GitHub
file extractor; caching; recursive traversal; oversized-file partitioning;
cross-shard reconciliation; changes to the fixture, PDF, git, GitHub or diary
adapters, the reducer, or the ledger schema.

## Research: solution classes

`is_this_a_graph`? **Yes — and it already exists.** `corpus_census` is the
graph; per FR-892 a new corpus supplies adapters. This FR supplies adapters.
That answer is the point: the prior attempt at this corpus was a script.

| # | Class | Evidence | Disposition |
|---|---|---|---|
| 1 | **New `md_discover`/`md_extract` in `corpus_adapters.py`** | Mirrors `pdf_discover`/`pdf_extract` (`corpus_adapters.py:33-57`); fail-closed shape follows `diary_adapters.py:25-42` | **Chosen.** Precedented location; no graph change; smallest surface that makes bounded markdown first-class. |
| 2 | Bind the fixture adapters directly | `fixtures/fixture_tools.py` `extract` reads any text file unchanged | Rejected: fixtures are test scaffolding; a demo depending on them breaks when a test needs them changed. They also carry no identity freeze. |
| 3 | Hand-rolled script | Done this session; duplicated the topology, dropped judgement normalisation and the citation boundary | Rejected. The defect this FR retires. |
| 4 | GitHub-native discover/extract fetching files live | Needs the file extractor FR-1032 bars, plus a cache | Rejected **for now**: the corpus is already local. The honest end state, not the next step. |
| 5 | Add a glob parameter to `pdf_discover` | `corpus_adapters.py:33-42` | Rejected: widens a working adapter's contract for one caller, and `pdf_extract` still needs `pypdf`. |
| 6 | Raise the map ceiling to fit 620 items | `graph.yaml` `max_map_items: 200` | Rejected: material graph change requiring the authoring route, and out of scope here. |

**Preserved disagreement.** Class 4 is defensible as the real target: a census
that cannot refresh its own corpus depends on a snapshot someone made by hand.
The counter is that it needs two FRs that do not exist while the corpus does.
Class 6 is defensible if a single reconciled run over the whole corpus is
required; with fail-closed discovery the operator must instead shard, and this
FR does not pretend those shards reconcile.

## Related

- FR-892 slot binding; FR-895 synthesize tail; FR-940 judgement normalisation.
- [reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md)
- [FR-1033 judgement](FR-1033-markdown-corpus-census-adapters.judgement.md)

## Implementation record (2026-09-09)

Enforced as filed, with **one recorded deviation** from the frozen scope.

**Deviation (D-1 surface).** The judgement froze D-1 to
`corpus_adapters.py`. Adding the adapters there took that module from 364 to
461 lines, past the 450-line hard ceiling in CLAUDE.md's Code Quality
Standards and Commandment 8. Both rules bind and the judgement did not consider
file size, so the adapters live in a new
`examples/demos/corpus_census/adapters/markdown_adapters.py` (112 lines),
following the `diary_adapters.py` precedent for a separate adapter module.
`corpus_adapters.py` returns to its original 364 lines, unmodified. Manifests,
tests, CAP-270 and ARCHITECTURE.md point at the new module. Flagged for the
human rather than absorbed silently.

- **D-1** `MarkdownItemRef`, `md_discover`, `md_extract`, `MD_MAX_ITEMS=200`,
  `MD_MAX_CHARS=65536` in `examples/demos/corpus_census/adapters/markdown_adapters.py`
  (see deviation above).
- **D-2** `md-discover.tool.yaml`, `md-extract.tool.yaml` beside it.
- **D-3** `tests/unit/test_markdown_corpus_adapters.py` — 16 witnesses, all
  tagged `REQ-YG-674`, committed RED before implementation (`99d3c28b`).
- **D-4** `capabilities/CAP-270-markdown-corpus-census.yaml`; REQ-YG-674 and
  CAP-270 registered in `ARCHITECTURE.md`.
- **D-5** changelog fragment; this record; diary distillation.

**Decisions taken during enforcement.**

- Two test assertions about the resolved slot structure were wrong and were
  corrected against observed output, not against a guess: `resolve_tool_slots`
  *removes* the `slot` key and *flattens* the manifest's `runtime` block into
  the tool entry, rather than nesting it. The corrected assertions are stricter
  than the originals (`"slot" not in resolved[...]`).
- `MD_MAX_CHARS = 65536` is a character count applied after decoding, so a
  file of multi-byte characters may exceed 65,536 bytes while passing. The
  ceiling bounds what the model reads, which is the quantity that matters.
- `tests/unit/test_fi_domain_crawl.py` cannot be collected in this environment
  because `bs4` is not installed. That is an absent optional dependency, not a
  test outcome, and is unaffected by this change.
