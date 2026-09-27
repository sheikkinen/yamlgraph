# Problem brief: an unattended digest pipeline that reports green while publishing nothing

**Prior art:** FR-998
(`feature-requests/FR-998-anthropic-constrained-structured-output.md`,
Enforced 2026-09-18, shipped in yamlgraph 0.5.25) switched every
Anthropic `llm` node with an inline `schema:` to constrained
`json_schema` decoding so that `list[str]` fields arrive as lists. Its
witness was a `list[str]` field; no `Any`-typed field was among its
fixtures. FR-905
(`feature-requests/FR-905-ranked-story-boundary-validation.md`,
Enforced 2026-08-30) put a Pydantic boundary in the digest's formatting
node so a ranker that answers with garbage raises instead of emitting an
empty bulletin, and pinned the ranker prompt schema unchanged with a
test that says changing the schema is a separate FR. FR-903 made
archive-before-send an edge and introduced `digest_status` so routing
never keys off empty markdown. FR-819 adapted the repository example
into the standalone `sheikkinen/yamlgraph-daily-digest` repository,
whose workflow installs `yamlgraph>=0.5.23` from PyPI with no ceiling.
FR-1097/FR-1098 made the CLI's `graph run` exit status truthful about
recorded errors; the digest runs through its own `run_digest.py`, not
the CLI. No REJECTED FR was found in this territory.

## Problem statement

`sheikkinen/yamlgraph-daily-digest` is a YAMLGraph pipeline that runs
unattended in GitHub Actions at 06:00 UTC, ranks the day's Hacker News
and RSS stories with an Anthropic model, archives a markdown bulletin,
emails it, and commits the bulletin plus a SQLite dedup database back to
its own repository. Between 2026-09-19 and 2026-09-27 every scheduled
run completed with status success, and no bulletin was archived, sent
or committed. Each daily commit changed only the dedup database.

The run log names the cause. The `rank_stories` node fails with the
message `Schema must have a 'type', 'anyOf', 'oneOf', or 'allOf'
field.` The ranker's inline prompt schema declares
`stories: list[Any]`. Under yamlgraph 0.5.24 that reached the provider
through forced tool calling and was accepted. Under 0.5.25 the same
schema is sent through constrained decoding, and the Anthropic SDK's
strict schema transform rejects an array whose item schema is empty.
The rejection is raised client-side before any request, after the
per-article map stage has already spent its tokens.

Three further properties turned one rejected schema into nine silent
days. The `rank_stories` node declares no `on_error`, and yamlgraph's
default handler for an `llm` node logs the error, records it in state,
sets the node's state key to `None` and lets the graph continue. The
formatting node then sees an absent ranker result, which it treats as
"the ranker was never invoked", and reports `digest_status:
no_articles`, the value the gate routes to END. The runner prints
"no-op, nothing to commit" whenever it sees that status and never reads
the recorded errors. Meanwhile the filter node had already written every
new URL into the dedup database before ranking ran, and the workflow
commits that database unconditionally, so 298 articles were marked seen
and can never be ranked. Because the filter also drops anything older
than 24 hours before dedup, restoring the database would not recover
them.

The open question is what set of changes, in which of the two
repositories, makes this class of failure impossible to mistake for a
quiet day, and whether the fix belongs in the digest's own artifacts, in
the framework's error defaults, or in both.

## Classification

enforcement/latency-critical

## Constraints

- Any `graph.yaml` or `prompts/*.yaml` edit, in either repository, is
  governed authoring and may only go through `scripts/author.sh` with a
  committed brief (FR-767 sole route); no manual or delegated edits.
- The FR-905 boundary in `nodes/formatting.py` stays; its test that pins
  the prompt schema was written to be retired by exactly this kind of
  FR and must be replaced by a witness, not deleted.
- No bug is fixed without a condemning test first. The rejection is
  reproducible offline: build the ranker's Pydantic model through
  `yamlgraph.schema_loader.build_pydantic_model` and pass its JSON
  schema through `anthropic.lib._parse._transform.transform_schema`.
  A witness must not need a provider key.
- The repository example `examples/daily_digest/prompts/rank_stories.yaml`
  carries the identical schema and must not be left behind.
- No silent fallback: a schema the provider refuses must fail loudly at
  the earliest boundary, never downgrade to a looser method without a
  recorded decision. A quiet day and a crashed ranker must be
  distinguishable in state, in the runner's output, and in the exit
  code.
- The digest's unbounded `yamlgraph>=0.5.23` floor is a standing
  decision that the digest is a dogfooding canary for releases; the
  research must say whether that decision survives, and if it does, what
  makes a canary that fails loudly rather than silently.
- The lost articles are unrecoverable by database rollback because the
  24-hour recency filter runs before dedup; no proposal may promise
  their recovery.
- Framework changes to `yamlgraph/` (error defaults, schema-load
  validation) are a separate judged scope; this brief's scope is the
  digest's own artifacts plus whatever cross-reference that separate
  scope needs.
- `is_this_a_graph`: must be answered; the pipeline already is one, and
  the question is whether the fix is graph configuration, prompt schema,
  runner code, or all three.

## Witnessed incidents

- 2026-09-19 10:18Z, GitHub Actions run 35436976071 of
  `sheikkinen/yamlgraph-daily-digest`: first run installing yamlgraph
  0.5.25 (previous day 0.5.24). Log line
  `[ERROR] yamlgraph.error_handlers: Node rank_stories failed: Schema
  must have a 'type', 'anyOf', 'oneOf', or 'allOf' field.` followed by
  `nodes.formatting: No stories to format — nothing to report today`,
  27 filtered articles, run status success, commit touching only
  `digest.db`.
- 2026-09-27 11:24Z, run 36315534165: identical log shape, 25 filtered
  articles, ninth consecutive day. Every `_map_analyze_all_sub` call in
  the same run returned HTTP 200, so the map stage's own schema is
  accepted by constrained decoding.
- 2026-09-18 10:34Z, run 35335237346, the last good day: yamlgraph
  0.5.24, `Node rank_stories completed successfully`, bulletin archived
  and mailed.
- 2026-09-27, offline reproduction on this host against anthropic SDK
  1.3.0 and yamlgraph main: the digest's schema fails
  `transform_schema` with the same message; the same schema with
  `stories: list[dict]` passes; `list[dict[str, Any]]` is not a type the
  schema loader accepts.
- 2026-09-27, `digest.db` on the digest repository's main: 298 rows
  with `first_seen` between 2026-09-19 and 2026-09-27, none of which
  appears in any bulletin.
- `nodes/formatting.py` in the digest repository (FR-905): a `None`
  ranker result is classified as "ranker never invoked" and returns
  `digest_status: no_articles`; only a dict payload counts as "the
  ranker answered".
- `yamlgraph/node_factory/llm_execution.py` on main: with `on_error`
  unset, `handle_error` falls through to `handle_default`, which logs
  and returns an error result; the node's state key becomes `None` and
  execution continues.
- FR-1073's migration census
  (`feature-requests/FR-1073-map-result-contract.md`, row 10) already
  lists `daily_digest/graph.yaml` for a map-level `on_error` move; it
  does not mention the ranker node.
