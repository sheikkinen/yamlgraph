# Problem brief: every corpus-census graph re-authors the same skeleton by hand

**Prior art:** dispositioned in the FR this brief produces (closed-input
brief per FR-890 R-2).

## Problem statement

The repository contains at least five independently authored graphs that
perform the same five-stage task — enumerate a corpus, fetch one item's
content, apply one cheap per-item LLM judgement or transformation,
aggregate deterministically with fail-closed validation, optionally run
one synthesis call. In every instance only the first two stages (corpus
enumeration and per-item content retrieval) genuinely differ; the
remaining stages are re-implemented each time: model pinning is forgotten
(28 of 33 map graphs inherit an expensive default), evidence stamping and
abstention exist in some reducers and not others, disagreement handling
and error-string rejection are re-invented or omitted, and authoring each
new instance requires the full graph-authoring route even though the
analytical skeleton is identical. A documented product study
(docs/mercury-census/findings.md) identifies a family of census-style
analyses over different corpora — websites, PDF libraries, git history,
repository gardens, call archives, survey responses — that are blocked in
practice by the marginal cost of re-authoring the skeleton rather than by
any missing capability. Graphs currently declare their tools statically
at load time; there is no mechanism for a user to supply the two
corpus-specific stages to an existing pipeline at invocation, so reuse
happens by copying whole graphs, which drifts.

## Classification

judgement/analysis/generation

## Constraints

- Three-layer architecture: tools are Layer 3 side-effect modules; graphs
  are YAML logic; the CLI is presentation. Import boundaries enforced by
  import-linter.
- FR-768 tool manifests exist: typed, portable tool declarations
  (shell/python/graph runtimes) translated at graph load into inline
  declarations; translation-only, existing runtimes execute.
- FR-658 graph-as-tool composition and CAP-111 shared-graph invocation
  exist.
- Graph authoring is governed by a sole route (author.sh, FR-767
  sentinel); any solution that requires authoring a new graph per corpus
  inherits that route's cost by design.
- The FR-884 classifier architecture and FR-890 research-route reducer
  are the reference implementations of the fail-closed reduce stage
  (evidence stamping, disagreement rows, error-string rejection).
- Security: user-supplied executable tool definitions are untrusted
  input; shell tools already sanitize variables via shlex.quote.
- Cheap-model pinning discipline: per-call abstraction-span decides the
  map model tier (docs/mercury-census/findings.md, diary
  2026-08-26-cheap-map-code-reduce).

## Witnessed incidents

- 2026-08-26 census (docs/mercury-census/findings.md F1): 28 of 33
  `type: map` graphs pin no model and inherit the opus-class default —
  the pinning discipline does not survive per-instance re-authoring.
- Five in-repo instances decompose identically with zero shared code:
  prompt_theme_analyzer, diary_digest, book-summary, fi_domain_crawl,
  icpc-2-rfe (decomposition table in findings.md, "The pattern, fleshed
  out").
- The product study's P0 family (site mapper, PDF library census,
  enterprise-architecture cartographer, git-PR timeline) was judged
  buildable-in-weeks per instance, with the skeleton re-authoring named
  as the dominant marginal cost.
- FR-891 (2026-08-26): the fail-closed tool boundary had to be fixed at
  the framework level precisely because per-graph reducers do not
  uniformly enforce it — evidence that per-instance re-implementation of
  the reduce stage loses safety properties.
