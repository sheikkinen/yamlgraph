# Judgement: FR-1033 markdown corpus adapters for the census

**Verdict:** APPROVED WITH REVISIONS — the adapter-only binding is a feasible, single-purpose contrib/example change, but authority activates only after the FR replaces silent population/content loss with fail-closed bounds and freezes each file's byte identity.

**Reviewed against:** `feature-requests/FR-1033-markdown-corpus-census-adapters.md`; `docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md`; `feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md`; `feature-requests/FR-899-org-repo-census-azure.md`; `feature-requests/FR-1032-census-adapter-owned-extract-cache.md`; `feature-requests/FR-1031-census-extract-cache-dir.judgement.md`; `feature-requests/FR-1026-retire-research-provenance-ledger.judgement.md`; `feature-requests/FR-1032-census-adapter-owned-extract-cache.judgement.md`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/corpus_census/tools.py`; `examples/demos/corpus_census/ledger_failures.py`; `examples/demos/corpus_census/adapters/corpus_adapters.py`; `examples/demos/corpus_census/adapters/diary_adapters.py`; `examples/demos/corpus_census/adapters/diary_recurrence.py`; `examples/demos/corpus_census/adapters/census_brief.py`; `examples/demos/corpus_census/adapters/pdf-discover.tool.yaml`; `examples/demos/corpus_census/adapters/pdf-extract.tool.yaml`; `examples/demos/corpus_census/fixtures/fixture_tools.py`; `examples/demos/corpus_census/fixtures/extract.tool.yaml`; `examples/demos/corpus_census/prompts/judge_item.yaml`; `examples/demos/corpus_census/prompts/synthesize_brief.yaml`; `examples/demos/corpus_census/proofs/pdf-library/ledger.md`; `examples/demos/corpus_census/proofs/git-timeline/ledger.md`; `tests/unit/test_fr899_repo_census.py`; `capabilities/CAP-249-tool-slot-binding.yaml`; `reference/patterns/corpus-map-reduce.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem and consumer are concrete. The repository has a reusable census graph with invocation-bound `discover` and `extract` slots (`examples/demos/corpus_census/graph.yaml:43-51,68-85`), while its production adapter module has PDF, git, and GitHub bindings but no general local-Markdown pair (`examples/demos/corpus_census/adapters/corpus_adapters.py:30-89,93-173`). Adding two Python functions and two manifests is therefore the smallest change that closes the mechanical binding gap; no graph, prompt, framework, reducer, or ledger edit is needed.

The proposal is internally coherent about ownership and exclusions. It follows FR-892's rule that a new corpus supplies adapters rather than copying the graph (`feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:29-36,64-85`), rejects fixture reuse because fixtures are test scaffolding, and explicitly excludes graph/prompt changes, ceiling changes, caching, other adapters, and reducer/ledger changes (`feature-requests/FR-1033-markdown-corpus-census-adapters.md:119-121,130-139`). This is one responsibility rather than a bundle.

The research record satisfies the prospective substance gate: it gives six distinct solution classes, evidence or precedent for each, preserved disagreement, and an explicit, correct `is_this_a_graph` answer (`feature-requests/FR-1033-markdown-corpus-census-adapters.md:123-147`; `.github/skills/judge-fr/doctrine.md:118-129`). The cited raw-read record also supplies ten concrete samples with surprising file-level details, including a 306 KB file whose useful invariants are not visible from corpus aggregates (`docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md:10-67,92-100`), satisfying the local raw-output discipline for this census-related proposal.

Most behavior is directly testable: extension filtering, deterministic ordering, missing/empty input failures, UTF-8 decoding policy, manifest wiring, requirement markers, and vocabulary normalization can all be witnessed without inventing a new runtime seam (`feature-requests/FR-1033-markdown-corpus-census-adapters.md:96-117`). The existing reducer already reconciles source indices against discovered items and rejects missing findings (`examples/demos/corpus_census/tools.py:214-221,276-296`).

Strategically this is **Contrib/example**, not a framework primitive. It has one named corpus/use case, reuses the existing slot abstraction, and changes only an example adapter surface. It does not establish a third framework-level need or a new graph abstraction (`.github/skills/judge-fr/doctrine.md:51-57`).

## Required revisions

### R-1: Fail closed when the directory exceeds the map ceiling

Replace the proposed first-`MD_MAX_ITEMS` slice with a count check that raises `ValueError` when the discovered population exceeds 200. Include the actual count and ceiling in the error. Return all sorted `*.md` items only when the complete directory fits.

The current criterion deliberately returns the lexicographically first 200 files and silently omits the rest (`feature-requests/FR-1033-markdown-corpus-census-adapters.md:79-87,101-105`). That contradicts the corpus contract that completeness is part of the result and that no missing item may be silently dropped (`reference/patterns/corpus-map-reduce.md:24-33,198-220`). It is especially misaligned with the cited finding that the tail, not the distribution or arbitrary prefix, contains the useful practices (`docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md:92-100`). The existing diary adapter provides the aligned precedent by rejecting over-cap batches and requiring the operator to narrow the source (`examples/demos/corpus_census/adapters/diary_adapters.py:25-42`).

Keep sharding operator-controlled and outside this FR, but state that every shard is an independently complete run. Do not describe concatenated shard outputs as one reconciled census because this FR adds no cross-shard identity, coverage, or reduction step.

### R-2: Freeze file identity at discovery and verify it at extraction

Define a typed Markdown item reference containing exactly `path`, raw-byte `sha256`, and raw-byte `bytes`. `md_discover` must read each selected regular file once, compute these values, and return a deterministic serialized item reference accepted by the existing string slot contract. `md_extract` must parse and validate that typed reference, read the file bytes once, and raise a specific `ValueError` if either the byte count or digest differs before decoding.

Path alone records which pathname was observed, not which bytes were judged; the FR acknowledges this gap but still calls the result a first-class census (`feature-requests/FR-1033-markdown-corpus-census-adapters.md:53-56,89-94`). The governing pattern requires file path, SHA-256, and bytes at minimum, and requires model-emitted results to reconcile to collector-owned identity (`reference/patterns/corpus-map-reduce.md:54-82,198-207`). This can be repaired entirely inside the two adapters without changing the graph or ledger: the serialized typed reference remains the ledger's `item_ref`.

Tests must cover deterministic serialization, non-ASCII bytes, mutation between discovery and extraction, byte-count mismatch, digest mismatch, and malformed item-reference validation. Keep invalid UTF-8 decoding with replacement only after raw-byte identity has been verified.

### R-3: Make the content bound fail loudly instead of truncating evidence

Define a Markdown-specific character ceiling and reject a decoded file that exceeds it; do not return `text[:MAX_CHARS]`. The error must name the path, observed character count, and ceiling. Because extraction completes before `judge_items` begins and uses `on_error: fail` (`examples/demos/corpus_census/graph.yaml:75-89,136-141`), this rejects an invalid run before any LLM judgement is made.

Silent truncation would permit a valid-looking ledger row for only the head of a file while attributing the judgement to the whole file (`feature-requests/FR-1033-markdown-corpus-census-adapters.md:63-66,106-109`). That is a plausible-wrong-answer failure, not merely weaker provenance. The cited first-consumer evidence includes a 306 KB, 3,445-line file and says its valuable rules occur in details throughout the artifact (`docs/diary/2026-09-09-agent-file-triage-invariant-store-state-log-description.md:17-34`). This adapter cannot claim to classify such a file unless the whole decoded content fits the declared bound.

Revise the First consumer, Value Statement, Ideal Result, cap rationale, and provenance paragraph to promise a **bounded local-Markdown corpus** only. State explicitly that oversized-file partitioning and file-level reconciliation are a separate graph concern not authorized here. Remove “no future markdown analysis has a reason to be a script”; this adapter does not cover recursive trees, oversized files, cross-shard reconciliation, or live GitHub harvesting.

### R-4: Strengthen the end-to-end and wiring criteria

Make the end-to-end witness load both new manifests through the existing slot-binding path and execute the unchanged graph over at least two temporary Markdown files with a deterministic stubbed LLM boundary. Assert all of the following: discovered count equals ledger-row count; ledger item references carry the expected path/digest/byte identities; row labels are from the supplied vocabulary or `abstain`; both output artifacts exist; and `graph.yaml`, prompts, reducer, and ledger schema are unchanged.

Add direct manifest assertions for runtime type, module-relative path, and function name. Replace “asserted by the PR diff” as an acceptance criterion with a frozen scope condition: a diff is review evidence, not a behavioral test (`feature-requests/FR-1033-markdown-corpus-census-adapters.md:110-116`). Keep all new test functions tagged `REQ-YG-674`, and make CAP-270 list the adapter module, both manifests, and the new test module rather than attributing this example behavior to CAP-249.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Typed Markdown item-reference model plus `md_discover` and `md_extract` in `examples/demos/corpus_census/adapters/corpus_adapters.py` |
| D-2 | `examples/demos/corpus_census/adapters/md-discover.tool.yaml` and `examples/demos/corpus_census/adapters/md-extract.tool.yaml` |
| D-3 | `tests/unit/test_markdown_corpus_adapters.py`, including direct adapter, manifest, mutation, overflow, oversize, and unchanged-graph end-to-end witnesses |
| D-4 | New CAP-270 / REQ-YG-674 registry wiring for the exact adapter, manifest, and test surfaces |
| D-5 | Changelog fragment, FR implementation record, and diary distillation |

Not authorized: any change to `examples/demos/corpus_census/graph.yaml`, its prompts, reducer, ledger schema, fixture adapters, diary/PDF/git/GitHub adapters, or any `yamlgraph/` framework/runtime code; raising the graph map ceiling; recursive discovery; oversized-file partitioning; cross-shard reconciliation; GitHub file extraction; caching; accepting a silently truncated file or silently omitted directory item; claiming exhaustive corpus compliance beyond one bounded, identity-frozen directory run.

## Revised acceptance criteria

- [ ] AC-01: `md_discover` accepts a directory containing one through 200 regular `*.md` files, excludes every other entry, and returns every Markdown item in deterministic path order.
- [ ] AC-02: A non-directory source raises `NotADirectoryError`; an empty Markdown population raises `ValueError`; 201 or more Markdown files raise `ValueError` naming the observed count and ceiling, with no prefix result returned.
- [ ] AC-03: Every discovered item reference is a deterministically serialized typed value containing path, SHA-256 of the exact raw bytes, and exact raw-byte count; malformed references fail validation.
- [ ] AC-04: `md_extract` reads raw bytes once and rejects a file whose current byte count or SHA-256 differs from its discovered identity; tests mutate a file between discovery and extraction and prove failure.
- [ ] AC-05: After identity verification, `md_extract` decodes UTF-8 with replacement, rejects empty or whitespace-only decoded text, and raises `FileNotFoundError` for a missing/non-file path.
- [ ] AC-06: A decoded file at or below the Markdown character ceiling is returned in full; a file one character over raises `ValueError` naming path, observed count, and ceiling. No slicing/truncation path exists.
- [ ] AC-07: The two manifests resolve relative to their own directory to Python runtime functions `md_discover` and `md_extract`, and existing slot-contract validation accepts both bindings.
- [ ] AC-08: An end-to-end test binds both manifests to the unchanged census graph, uses a deterministic stubbed LLM boundary over at least two Markdown files, and proves discovered count equals ledger-row count.
- [ ] AC-09: The end-to-end ledger preserves each typed path/digest/byte item reference, and every judgement is either in the supplied label vocabulary or exactly `abstain`; markdown and JSONL outputs both exist.
- [ ] AC-10: `git diff` for implementation contains no change to graph YAML, prompts, reducer, ledger schema, fixture/diary/PDF/git/GitHub adapters, or `yamlgraph/`; the human scope review records this check.
- [ ] AC-11: CAP-270 owns REQ-YG-674 and lists the adapter module, both manifests, and the test module; every new test has `@pytest.mark.req("REQ-YG-674")`; strict requirement coverage passes.
- [ ] AC-12: RED tests precede GREEN implementation; the changelog fragment, FR implementation status/decisions, and diary distillation with a `Seed:` are complete.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority exists until R-1 through R-4 and AC-01 through AC-12 are folded into FR-1033 and this advisory draft is human-approved. | GATE |
| C-2 | Population overflow and per-file content overflow must fail loudly; neither lexicographic prefix selection nor content slicing is permitted. | GATE |
| C-3 | Every ledger item reference must identify and verify path, raw-byte SHA-256, and raw-byte count before decoding or judgement. | GATE |
| C-4 | The authorized capability is one bounded, non-recursive local-directory run; do not claim cross-shard completeness or support for oversized Markdown files. | GATE |
| C-5 | Keep the existing graph, prompts, reducer, ledger schema, map ceiling, framework, and all unrelated adapters unchanged. | GATE |
| C-6 | Any need for partitioning, cross-shard reconciliation, recursive discovery, a GitHub file source, caching, or graph/prompt edits stops enforcement and returns to a separate FR. | GATE |
| C-7 | The end-to-end witness must exercise manifest binding and the unchanged graph, not only call adapter functions directly. | GATE |

Authority granted: after R-1 through R-4 are folded into FR-1033 and this advisory draft is human-approved, implement only the bounded, identity-frozen local-Markdown discover/extract binding and exact supporting test, capability, changelog, FR-record, and diary surfaces listed above.
