# person_profile_census — FR-962

Person-profile census of authored GitHub PRs — a sibling of `repo_census`
(FR-899) using the shared `corpus_census` pipeline (FR-892). Unit is the
authored PR; reduce target is one person.

> **Use only on your own footprint or with the subject's explicit written
> permission.** Profiling another person's authored PRs — even from public
> repositories — may implicate labour law, data-protection law (GDPR
> Art. 4, 6, 22 in the EU), platform terms of service, and employer
> policies. Public availability of the source PR does not by itself
> license aggregated behavioural analysis of the author. The corp-run
> path additionally requires that the subject's employer has authorised
> the LLM analysis under the applicable data-processing agreement. This
> tool ships no consent mechanism; the operator is the accountable
> controller.

## Structure

- `graph.yaml` — the sibling census graph. Azure-pinned (`provider: azure`),
  preflight-first, `max_items: 500` on both map stages. Authored via
  `scripts/author.sh` (FR-767 sole route).
- `prompts/classify_pr.yaml` — one structured classification per PR.
- `prompts/synthesize_person_brief.yaml` — one person-level brief.
- `tools.py` — Azure + visibility preflight, `PRLedgerRow`,
  `reduce_pr_ledger` (LLM-free specialized reducer, R-3), FR-895
  brief-input adapter identifying rows by validated PR `url`,
  citation-boundary `render_brief`.
- `preflight.tool.yaml` — the preflight slot manifest (Azure env +
  visibility).
- `smoke_preflight.tool.yaml` — committed slot manifest binding
  `preflight_smoke` (visibility only, no Azure env check). Used solely by
  the Quickstart below; the committed `graph.yaml` never binds it.
- `gh-profiler.yaml` — a two-model variant (map on one provider,
  synthesis on another). Not part of the FR-962 enforced scope; the
  sibling census graph is `graph.yaml`.
- `proofs/` — public-safe smoke output against `sheikkinen@sheikkinen`.

## Quickstart — reproduce the committed public proof

The committed graph pins `provider: azure`; to reproduce
`proofs/smoke-*.md` against public GitHub without Azure credentials,
build a throwaway anthropic-provider copy and run it. Only the copy is a
throwaway and it is NEVER committed (the FR-767 sentinel refuses it);
`smoke_preflight.tool.yaml` is a committed file — do not delete it:

```bash
# 1. Prerequisites: gh authenticated (public repos), ANTHROPIC_API_KEY set.
# 2. Build a throwaway smoke graph next to tools.py (colocated so Python
#    tool paths resolve; the throwaway lives under a name that is not a
#    committed artifact filename):
sed -e 's|provider: azure|provider: anthropic|g' \
    -e 's|azure_model|smoke_model|g' \
    examples/demos/person_profile_census/graph.yaml \
    > examples/demos/person_profile_census/SMOKE_ONLY.yaml

# 3. Run the smoke against the operator's own public PR footprint,
#    binding the committed smoke preflight (skips the Azure env check):
yamlgraph graph run examples/demos/person_profile_census/SMOKE_ONLY.yaml \
  --tool preflight=examples/demos/person_profile_census/smoke_preflight.tool.yaml \
  --tool discover=examples/demos/corpus_census/adapters/gh-authored-prs-discover.tool.yaml \
  --tool extract=examples/demos/corpus_census/adapters/gh-pr-extract.tool.yaml \
  --var source='sheikkinen@sheikkinen:2026-08-25' \
  --var visibility='["public"]' \
  --var smoke_model='claude-haiku-4-5' \
  --var problem_labels='["doctrine","enforcement","cleanup","infra","research","tests","hotfix","tooling","governance"]' \
  --var surface_labels='["backend","infra","docs","tests","tooling","ci","graphs","hooks","adapters"]' \
  --var rubric='Classify this authored PR by problem_class, change_kind (feat|fix|docs|refactor|chore|infra|ops|test|revert), 1-5 distinct surfaces, one-sentence intent (<=280 chars), and one evidence_span copied verbatim from the title or body_head.' \
  --var output_path=tmp/smoke-ledger.md \
  --var brief_path=tmp/smoke-brief.md \
  --var brief_rubric='Profile this engineer from PR footprint. Themes, surface concentration, cadence, anti-patterns (churn, retitles, phantom-work). Cite PR URLs.'

# 4. Clean up: delete the throwaway graph before any commit.
rm examples/demos/person_profile_census/SMOKE_ONLY.yaml
```

Output lands in `tmp/smoke-ledger.md` (mechanical rollup + per-PR table),
`tmp/smoke-ledger.jsonl` (validated `PRLedgerRow` per line),
`tmp/smoke-ledger.run.json` (deterministic run metadata), and
`tmp/smoke-brief.md` (person brief with FR-895 URL citation validation).
`proofs/smoke-*.md` were produced by this command on
`claude-haiku-4-5`. The smoke path renames `azure_model` to
`smoke_model`, so the reducer never sees the model actually used and
reads the `AZURE_MODEL` environment variable instead — the committed
proof records `"azure_model": "unknown"` only because the operator's
environment held no such variable. On a machine where it is set, the
smoke stamps that value into the artifact regardless of which model ran.
Smoke-run model attribution therefore rests on this README, not on the
artifact. FR-967 AC-13 corrects the reducer to require a resolved model.

## Invocation (corp run — never committed)

```bash
AZURE_AI_ENDPOINT=... AZURE_AI_API_KEY=... AZURE_MODEL=<deployment> \
yamlgraph graph run examples/demos/person_profile_census/graph.yaml \
  --max-concurrency 2 \
  --tool preflight=examples/demos/person_profile_census/preflight.tool.yaml \
  --tool discover=examples/demos/corpus_census/adapters/gh-authored-prs-discover.tool.yaml \
  --tool extract=examples/demos/corpus_census/adapters/gh-pr-extract.tool.yaml \
  --var source='<author>@<owner>:<since>' \
  --var visibility='["private"]' \
  --var azure_model="$AZURE_MODEL" \
  --var problem_labels='[...]' \
  --var surface_labels='[...]' \
  --var rubric='...' \
  --var canary='{"item_ref":"...","surface_family":[...]}' \
  --var output_path=tmp/person-profile.md \
  --var brief_path=tmp/person-profile.brief.md \
  --var brief_rubric='...'
```

The CLI value overrides the graph's `config.max_concurrency: 4`; this key bounds how many map items run at once (LangGraph `RunnableConfig["max_concurrency"]`), not how many items exist (`max_items`).

**Pass exactly one `visibility` value.** The discover adapter emits one
`--visibility` flag per entry, and `gh search prs` conjoins them into
`is:private is:internal` — an unsatisfiable intersection, since a pull
request has exactly one visibility. GitHub offers no disjunctive escape:
`is:private OR is:internal` is rejected with HTTP 422 ("Logical
operators only apply to text, not to qualifiers"), and the parenthesised
form is accepted as free text and silently returns zero. FR-966
therefore rejects a multi-value list at the input boundary, before any
network call. Run once per visibility class if a corpus spans more than
one.

Expect `gh` secondary rate limits on large corpora: extraction issues one
`gh` call per discovered PR.

The public demo in `proofs/` was produced on `anthropic/claude-haiku-4-5`
via the Quickstart above (never committed). The committed sibling graph
retains `provider: azure`.

**Two enforcement claims in FR-962 are not yet real** (FR-967). AC-07
requires a configuration test that fails if any LLM node resolves to a
non-Azure provider; no such test exists, so the pin is convention. AC-16
describes a locality audit over the committed person-profile surfaces;
no such audit exists here either — the sibling `repo_census` demo has
one, this demo does not. Treat both as documented intent until FR-967
D-1 lands them.

## Governance

FR-962 froze scope, judgement folded R-1..R-5. See
[feature-requests/FR-962-person-profile-census-authored-prs.md](../../../feature-requests/FR-962-person-profile-census-authored-prs.md).
