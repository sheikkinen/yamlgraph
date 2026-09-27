# Feature Request: Daily digest ranker survives constrained decoding and fails loudly

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-27
**First consumer / first event:** the `sheikkinen/yamlgraph-daily-digest`
scheduled run at the first 06:00 UTC after merge, at the moment the
`rank_stories` node is bound with `method="json_schema"` and the
Anthropic SDK transforms its schema. Second consumer: the repository
example `examples/daily_digest/`, which carries the identical schema and
fails the same way on any Anthropic run.
**Research:** [FR-1121.research.md](FR-1121.research.md)
**Prior art:** [FR-998](FR-998-anthropic-constrained-structured-output.md)
changed the binder so Anthropic nodes decode under `json_schema`; this
FR changes a consumer schema that binder now rejects and adds no
framework code (the framework-side gate is
[FR-1123](FR-1123-untyped-subschema-constrained-decoding-gate.md)).
[FR-905](FR-905-ranked-story-boundary-validation.md) guards a ranker
that *answers* with garbage and pinned the prompt schema with a test
that names "changing the schema" as a separate FR; this is that FR, and
it closes the complementary gap where the ranker never answers.
[FR-903](FR-903-digest-archive-then-email-ordering.md) introduced
`digest_status` so routing never keys off empty markdown; this FR makes
the runner refuse a `no_articles` status that coexists with recorded
errors. [FR-819](FR-819-github-native-digest-poc-repo.md) chose a floating
`yamlgraph>=0.5.23` floor so the digest dogfoods releases; this FR keeps
that decision and makes the canary loud. [FR-1097](FR-1097-graph-run-completed-errors-exit-3.md)
made the CLI exit status truthful; the digest runs its own
`run_digest.py`, which this FR brings to the same standard.
[FR-1073](FR-1073-map-result-contract.md) row 10 names the digest's
*map* node; the map migration is
[FR-1122](FR-1122-daily-digest-map-contract-migration.md), not this FR.

## Summary

Since yamlgraph 0.5.25 reached the digest on 2026-09-19, every scheduled
run has completed green and published nothing. The ranker's inline
schema `stories: list[Any]` is rejected by Anthropic's constrained
decoder, the node has no `on_error`, the framework's default handler
lets the graph continue with a `None` result, the formatting node reads
`None` as "quiet day", and the runner prints a no-op. Nine days and 298
articles were lost. This FR retypes the schema, makes the ranker fail
the run, and makes the runner refuse to call a day quiet while errors
are recorded.

## Value Statement

The digest's reader gets a bulletin again, and the next framework change
that breaks the ranker turns the Actions run red on its first morning
instead of after a human notices the silence.

## Problem

The causal chain, each link witnessed in the research record:

| Link | Where | Behaviour |
|---|---|---|
| Trigger | PyPI resolves `yamlgraph>=0.5.23` to 0.5.25 on 2026-09-19 | FR-998 binds Anthropic nodes with `method="json_schema"` |
| Break | `prompts/rank_stories.yaml`, `stories: list[Any]` | JSON schema item is `{}`; SDK transform raises `Schema must have a 'type', 'anyOf', 'oneOf', or 'allOf' field.` before any request |
| Swallow | `graph.yaml`, `rank_stories` has no `on_error` | `handle_default` logs, records a `PipelineError`, sets `ranked_stories: None`, continues |
| Masquerade | `nodes/formatting.py` (FR-905) | `None` is classified as "ranker never invoked" → `digest_status: no_articles` |
| Silence | `run_digest.py` | prints the no-op line on `no_articles`, never reads `result["errors"]`, exits 0 |
| Loss | `nodes/filters.py` + workflow commit step | URLs marked seen before ranking; database committed unconditionally |

Every scheduled run from 2026-09-19 to 2026-09-27 shows the same log
shape. The loss is permanent: the 24-hour recency filter runs before
dedup, so restoring the database would not resurface the articles.

## Ideal Result

The digest's ranker schema is a shape every configured provider can
constrain on. A ranker that cannot run fails the node, the graph, the
runner and the Actions job, in that order, and no path exists from a
recorded error to a green run. The FR-905 boundary keeps guarding the
answer; this FR guards the absence of one. The floating version floor
stays, because a canary that fails loudly is worth more than a pin that
fails never.

## Proposed Solution

All graph and prompt edits go through `scripts/author.sh` with a
committed brief under `feature-requests/authoring-briefs/` (FR-767).
The digest repository has no FR directory; its FRs and briefs live here,
as FR-903/904/905 established.

### S-1: Retype the ranker schema (both repositories)

```yaml
# prompts/rank_stories.yaml — digest repo and examples/daily_digest
schema:
  name: RankedStories
  fields:
    stories:
      type: list[dict]
      description: "Top 5-8 stories, each with title, url, summary, relevance, reason"
```

`list[dict]` produces `items: {type: object, additionalProperties: true}`,
which the SDK transform accepts (verified offline 2026-09-27). The
element contract stays where FR-905 put it: `RankedStory` in
`nodes/formatting.py` validates each item and drops non-conforming ones
with a logged reason. No nested `fields:` grammar is added to the
schema loader; that is out of scope.

### S-2: The ranker fails the run

```yaml
# graph.yaml — digest repo and examples/daily_digest
  rank_stories:
    type: llm
    prompt: rank_stories
    on_error: fail
    state_key: ranked_stories
```

With `on_error: fail`, `handle_fail` re-raises and `compiled.invoke`
propagates; the runner exits non-zero and the workflow's commit step
never runs.

### S-3: The runner never calls a day quiet while errors are recorded

In `run_digest.py`, immediately after `compiled.invoke(...)`:

```python
errors = result.get("errors") or []
if errors:
    for err in errors:
        print(f"✗ {err.node}: {err.message}", file=sys.stderr)
    sys.exit(2)
```

This runs before the `no_articles` branch. It is the belt under S-2's
braces: a future node without `on_error` cannot masquerade either.
Tolerated map failures (FR-1073) never enter `errors`, so a skipped
article does not trip it.

### S-4: Witnesses (digest repository, `tests/test_fr1121_ranker_loud_failure.py`)

- RED first: build the ranker model with
  `yamlgraph.schema_loader.build_pydantic_model` from the prompt file and
  pass `model_json_schema()` through
  `anthropic.lib._parse._transform.transform_schema`; assert no raise.
  Fails on `list[Any]`, passes on `list[dict]`. Offline, no key.
- `rank_stories` in `graph.yaml` declares `on_error: fail`.
- The runner exits non-zero when the invoke result carries a
  `PipelineError` and `digest_status == "no_articles"` (stub the
  compiled graph; assert `SystemExit(2)` and the stderr line).
- Retire FR-905's `test_prompt_schema_is_untouched` in favour of the
  transform witness above; the boundary tests in
  `test_fr905_ranked_validation.py` stay unchanged.
- Same transform witness added under `tests/unit/` here for
  `examples/daily_digest/prompts/rank_stories.yaml`, tagged with the
  REQ ID FR-998 owns.

### S-5: Sequencing

1. This repository: example prompt and graph via `scripts/author.sh`;
   unit witness; changelog fragment.
2. Digest repository: prompt, graph, runner, tests, via the same route
   with the brief committed here; PR title
   `fix(digest): FR-1121 ranker schema and loud failure`.
3. After merge, one `workflow_dispatch` run is the smoke; the next
   06:00 UTC run is the production witness. Its log must show
   `Node rank_stories completed successfully`, an archived bulletin and
   a sent mail, or a non-zero exit with the ranker's error on stderr.

### Not in scope

- A framework gate that refuses untyped subschemas at load or bind
  time: FR-1123.
- The digest's map node under the FR-1073 contract: FR-1122.
- Recovering the 298 lost articles: impossible by construction (see
  Problem).
- Pinning `yamlgraph` to an exact version: rejected below.

## Acceptance Criteria

- [ ] AC-1: the transform witness fails on the committed `list[Any]`
  schema (RED commit) and passes after S-1 (GREEN commit), in both
  repositories.
- [ ] AC-2: `rank_stories` declares `on_error: fail` in both graphs; a
  test asserts it in each repository.
- [ ] AC-3: `run_digest.py` exits 2 and prints every recorded error to
  stderr before any no-op line when `result["errors"]` is non-empty; a
  test proves it with a stubbed graph.
- [ ] AC-4: FR-905's schema pin test is replaced, not deleted, and every
  other FR-905 test passes unchanged.
- [ ] AC-5: every graph and prompt edit has a committed authoring brief
  and an adapter report; `yamlgraph graph lint` reports no new
  diagnostic on either graph.
- [ ] AC-6: the first scheduled run after merge either archives and
  sends a bulletin or exits non-zero; its run id and the relevant log
  lines are recorded in this FR's implementation record.
- [ ] AC-7: changelog fragment in `changelog/unreleased/`; FR
  implementation record; Distill diary entry with a `**Seed:**`.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Pin `yamlgraph==0.6.0` in the digest workflow | Rejected. FR-819 made the digest a release canary; a pin turns it into a museum. The defect was silence, not floating. |
| Per-node structured-output method override (`method: function_calling`) | Rejected. No such graph key exists; adding one is framework scope, and it would hide the untyped field rather than name it. |
| Nested `fields:` grammar in `schema_loader` so `stories` can be `list[RankedStory]` | Rejected here. Correct long-term, but it is a type-grammar change with its own consumers; FR-905's Python boundary already enforces the element shape. Candidate for a later FR. |
| Change the framework default `on_error` for `llm` nodes to `fail` | Out of scope. Framework-wide behaviour change; noted for FR-1123's judge. |
| Roll `digest.db` back to the 2026-09-18 commit | Rejected. Recency filtering precedes dedup; nothing older than 24 h re-enters. |

`is_this_a_graph`: the pipeline is already a graph; the fix is one
prompt schema, one node key, and one runner guard. No new graph.

## Related

- Runs: 35335237346 (last good, 2026-09-18), 35436976071 (first bad,
  2026-09-19), 36315534165 (2026-09-27).
- `yamlgraph/utils/structured_output.py` (FR-998 binder),
  `yamlgraph/node_factory/llm_execution.py` (`handle_error` fallthrough).
- FR-1122 (map migration), FR-1123 (framework gate).
