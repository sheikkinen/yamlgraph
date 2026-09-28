# Problem brief: no evidence-backed map of which upstream LangGraph pains YAMLGraph solves, inherits, or leaves untouched

**Prior art:** FR-892 (corpus_census skeleton, injected discover/extract
slots); FR-899 (org repo census, gh adapters, pinned provider); FR-962
(authored-PRs census, `gh search prs`, 500-item overflow cap); FR-943
(row-level failure containment in the census reducer); FR-1116/FR-1120
(map memo keyed on file bytes or caller-supplied versions such as
`updatedAt`).

## Problem statement

YAMLGraph is built on LangGraph, so every defect class reported upstream is
one of three things for YAMLGraph users: a pain YAMLGraph's YAML layer
removes, a pain it inherits unchanged, or a pain outside YAMLGraph's
surface. Nobody has measured which is which. Roadmap and FR choices about
state, streaming, checkpointing, subgraph config propagation, interrupts
and similar surfaces are made from anecdote (a handful of issues someone
remembers) rather than from the upstream record.

The upstream record is a finite, enumerable corpus: the
`langchain-ai/langgraph` repository reports 7,531 issues and pull requests
(1,654 issues — 587 open; 5,877 PRs — 244 open), measured 2026-09-28 via
the GitHub search API. No existing corpus_census adapter reads GitHub
issues; the existing gh adapters read org repos and one author's PRs.

## Classification

judgement/analysis/generation

## Constraints

- The GitHub search API returns at most 1,000 results per query (measured:
  page 11 of 100 → HTTP 422 "Only the first 1000 search results are
  available"). The population is 7.5× the cap. The REST list endpoint
  `repos/{o}/{r}/issues?state=all` returns issues and PRs together with
  cursor paging (`after=` in the Link header, no `last` rel), 100 per page.
- Issue numbers are shared with GitHub Discussions: 5 of 16 sampled numbers
  returned 404 from the issues endpoint. The population cannot be derived
  from a number range.
- Rate limits measured: core 5,000/hour, search 30/minute.
- A raw read of 12 items found: an issue + its external fix PR (#6534 /
  #8200, interrupt + `Command(goto=…)` resume binding); a checkpoint test
  hardcoding Redis localhost (#9050); a typing request for `StateGraph`
  generics (#5000); docs typo PRs (#3900, #1500, #2000); a CLI docker base
  image PR (#4500); a `create_react_agent` + Gemini question (#5300); and
  unrelated promotional / logo PRs (#7400, #7000). Many PRs are not pain
  reports at all. Labels include `bug`, `question`, `checkpointer`,
  `functional-api`, `type checking`, `external`, `missing-issue-link`,
  `stale`, `invalid`, `duplicate`; most sampled PRs carry no label.
- Cost boundary: per-item LLM classification of 7,531 items at roughly
  2,000 input tokens each is about 15M input tokens. Verified list prices
  2026-09-28: Claude Haiku 4.5 $1 in / $5 out per MTok; Inception Mercury-2
  $0.25 / $0.75.
- Scripture: `read_raw_output_first`, `map_reduce_the_corpus` (cost the
  full census before any smaller alternative), `junk_drawer_cap` (a
  catch-all "other" category eats correct answers), demote-never-drop,
  `plausible_wrong_answer` — category counts that do not sum to the
  population, or cited issue numbers that do not exist, are wrong answers.
- The census adapters must raise on fetch failure; the daily_digest HN
  fetcher logs and returns `[]`, which would silently shrink the corpus.
- Any governed `prompts/*.yaml` or `graph.yaml` artifact is written only via
  `scripts/author.sh`.

## Witnessed incidents

- 2026-09-28: search API probe, page 11 → HTTP 422 (1,000-result cap).
- 2026-09-28: `repos/langchain-ai/langgraph/issues/{6100,2800,800,3000,6800}`
  returned 404 — numbers belong to Discussions or were deleted.
- 2026-09-28: `examples/demos/corpus_census/adapters/` contains no
  gh-issues discover or extract manifest.
