# Feature Request: Daily digest ranker survives constrained decoding and fails loudly

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented (2026-09-27) — yamlgraph #726 (`d7890517`), digest #4 (`0648fbd8`); production witness recorded 2026-09-28 (run 36375149984, 7 stories)
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

### S-4: Witnesses (R-2, R-3, R-5)

Every new test function in this repository carries
`@pytest.mark.req("REQ-YG-664")`, the requirement FR-998 owns
(`FR-998-anthropic-constrained-structured-output.md`, implementation
record); `python scripts/req_coverage.py --strict` must pass. The
digest repository's tests follow its own convention.

- **RED, transform witness (both repositories):** build the committed
  ranker prompt's model with `yamlgraph.schema_loader.build_pydantic_model`
  and pass `model_json_schema()` through
  `anthropic.lib._parse._transform.transform_schema`. Fails on
  `list[Any]` because `stories.items` is untyped; the GREEN commit
  changes `stories` to `list[dict]` and the same transform completes.
  After GREEN, `stories.items.type == "object"` in both prompt files.
  Offline, no key.
- **Declaration assertion (both):** `rank_stories` declares
  `on_error: fail` in the graph file. Shape only; kept because it is
  cheap, never sufficient (R-2).
- **Execution-path witness (both, R-2):** load that repository's real
  graph configuration, force the `rank_stories` LLM execution to raise
  through a stub, assert the *original* exception propagates from graph
  invocation, and assert the downstream formatting node is never
  invoked. FR-1073 is the precedent for a correctly spelled `on_error`
  sitting where nothing reads it; this test is what proves the key is
  read.
- **Runner guard (digest only):** a stubbed completed invocation
  carrying at least two real `PipelineError` instances and
  `digest_status == "no_articles"` makes `run_digest.py` print every
  error to stderr, print no no-op line, and exit 2 before any later
  success or no-op handling.
- **FR-905 retained:** the schema-pin test
  `test_prompt_schema_is_untouched` is *replaced by* the transform
  witness; every other FR-905 test passes with no weakened assertion.
- **Lint, reproducible (R-3):** before each authoring run, the complete
  diagnostic set of `yamlgraph graph lint <graph>` is recorded in that
  run's report; after the run the identical command is recorded again.
  The after set is unchanged or reduced, and no after diagnostic points
  to `rank_stories` or its prompt schema. Both sets are copied into the
  implementation record.

### S-5: Sequencing (R-1, R-4)

Two committed authoring briefs, one per repository boundary, are the
durable inputs; the adapter report is transient evidence:

- `feature-requests/authoring-briefs/fr-1121-example-ranker-brief.md`
  — this repository, `examples/daily_digest/`.
- `feature-requests/authoring-briefs/fr-1121-digest-ranker-brief.md`
  — the external `sheikkinen/yamlgraph-daily-digest` checkout, run
  with `AUTHOR_WORKDIR` pointing at it; nothing from that checkout is
  committed here.

1. This repository: RED transform witness; example prompt and graph
   through `scripts/author.sh` from the first brief; GREEN; changelog
   fragment.
2. Digest repository: RED witnesses; prompt and graph through
   `scripts/author.sh` from the second brief; `run_digest.py` guard and
   tests (Python, not governed); GREEN. PR title
   `fix(digest): FR-1121 ranker schema and loud failure`.
3. Each authoring run produces and verifies the transient
   `tmp/draft-authoring-report.md` in its own checkout. The report is
   not committed; its authored paths, precedent, exact validation
   commands and outcomes, repairs and blocked validation are copied
   into this FR's implementation record, separately per repository.
4. Post-merge production witness (R-4): the first scheduled run after
   merge records its run id and log lines proving exactly one of three
   mutually exclusive outcomes:
   1. `rank_stories` succeeds and the run archives and sends a bulletin;
   2. no articles reach the ranker, `result["errors"]` is empty, the
      ranker is never invoked, and the legitimate no-op exits zero; or
   3. an error is recorded or raised, the runner exits non-zero, no
      no-op line is printed, and the workflow commit step does not
      execute.
   The invariant under test is "no recorded error reaches a green
   quiet-day result", not whether the feed had articles that morning.

### Not in scope

- A framework gate that refuses untyped subschemas at load or bind
  time: FR-1123.
- The digest's map node under the FR-1073 contract: FR-1122.
- Recovering the 298 lost articles: impossible by construction (see
  Problem).
- Pinning `yamlgraph` to an exact version: rejected below.

## Acceptance Criteria

The judgement's revised list is binding; it replaces the original
AC-1..AC-7.

- [ ] AC-01: FR-1121 folds R-1 through R-5 before enforcement begins and cites two exact committed authoring briefs under `feature-requests/authoring-briefs/`, each naming its repository boundary and complete artifact/validation surface.
- [ ] AC-02: In each repository, a separate RED commit adds a transform witness that builds the actual committed ranker prompt model and fails because `stories.items` is untyped; the corresponding GREEN commit changes `stories` to `list[dict]` and the same Anthropic SDK transform completes without raising.
- [ ] AC-03: In both prompt files, `model_json_schema()` contains `stories.items.type == "object"` after the change; FR-905's Python `RankedStory` boundary and all of its remaining tests are unchanged and pass.
- [ ] AC-04: `rank_stories` declares `on_error: fail` in both graphs, and a configuration assertion proves the declaration in each repository.
- [ ] AC-05: A behavioral test in each repository loads that repository's graph configuration, forces `rank_stories` execution to raise, proves the original exception propagates from graph invocation, and proves the downstream formatting node is not invoked.
- [ ] AC-06: In the standalone digest, a stubbed completed invocation carrying at least two real `PipelineError` instances and `digest_status == "no_articles"` makes `run_digest.py` print every error to stderr, print no no-op line, and exit 2 before any later success/no-op handling.
- [ ] AC-07: Before and after each authoring run, the same `yamlgraph graph lint <graph>` command is recorded with its complete diagnostic identity set; the after set is unchanged or reduced, and no after diagnostic points to the modified ranker node or prompt schema.
- [ ] AC-08: Each repository's graph and prompt edits are produced through `scripts/author.sh` from its named committed brief. Each run produces a non-empty `tmp/draft-authoring-report.md` satisfying the required headings and artifact checks; the report remains transient, while its paths, precedent, commands, outcomes, repairs, and blocked validation are copied into FR-1121's implementation record.
- [ ] AC-09: Every new YAMLGraph-repository test function carries `@pytest.mark.req("REQ-YG-664")`; the focused tests and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-10: Every FR-905 test other than the replaced schema-pin test passes without weakened assertions; the schema-pin test is replaced by, not merely deleted in favor of, the transform witness.
- [ ] AC-11: The first scheduled run after merge records its run ID and logs proving exactly one outcome: successful ranker plus archived/sent bulletin; legitimate no-input no-op with zero recorded errors and no ranker invocation; or non-zero failure with the error on stderr, no no-op line, and no workflow commit step.
- [ ] AC-12: No framework, map, formatting-boundary, collection, dedup, dependency-floor, workflow-policy, CI, hook, or doctrine surface listed as not authorized is changed.
- [ ] AC-13: This repository receives one scoped changelog fragment and one Distill diary entry containing `**Seed:**`; FR-1121 records RED/GREEN commits for both repositories, exact validation results, the production witness, implementation status, decisions, and deviations.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Pin `yamlgraph==0.6.0` in the digest workflow | Rejected. FR-819 made the digest a release canary; a pin turns it into a museum. The defect was silence, not floating. |
| Per-node structured-output method override (`method: function_calling`) | Rejected. No such graph key exists; adding one is framework scope, and it would hide the untyped field rather than name it. |
| Nested `fields:` grammar in `schema_loader` so `stories` can be `list[RankedStory]` | Rejected here. Correct long-term, but it is a type-grammar change with its own consumers; FR-905's Python boundary already enforces the element shape. Candidate for a later FR. |
| Change the framework default `on_error` for `llm` nodes to `fail` | Out of scope here; filed as [FR-1124](FR-1124-llm-node-default-on-error.md). |
| Roll `digest.db` back to the 2026-09-18 commit | Rejected. Recency filtering precedes dedup; nothing older than 24 h re-enters. |

`is_this_a_graph`: the pipeline is already a graph; the fix is one
prompt schema, one node key, and one runner guard. No new graph.

## Judgement fold (2026-09-27)

[Judgement](FR-1121-daily-digest-ranker-schema-loud-failure.judgement.md):
APPROVED WITH REVISIONS. Folded the same day:

- **R-1** → S-5: two exact committed briefs named
  (`fr-1121-example-ranker-brief.md`, `fr-1121-digest-ranker-brief.md`);
  the adapter report is transient and only its content is copied into
  the implementation record.
- **R-2** → S-4: an execution-path witness per repository (original
  exception propagates, formatting node never runs) beside the shape
  assertion.
- **R-3** → S-4: lint before/after with recorded diagnostic sets.
- **R-4** → S-5 item 4: the production witness is an error/no-error
  invariant with three mutually exclusive outcomes; a legitimate
  no-article day stays green.
- **R-5** → S-4: `REQ-YG-664` on every new test here;
  `req_coverage.py --strict`.

Scope frozen to the judgement's D-1..D-7; conditions C-1..C-8 are
gates. `list[dict]` is the whole schema change (C-7).

## Related

- Runs: 35335237346 (last good, 2026-09-18), 35436976071 (first bad,
  2026-09-19), 36315534165 (2026-09-27).
- `yamlgraph/utils/structured_output.py` (FR-998 binder),
  `yamlgraph/node_factory/llm_execution.py` (`handle_error` fallthrough).
- FR-1122 (map migration), FR-1123 (framework gate).

## Implementation record

**Verdict folded:** R-1..R-5 on 2026-09-27; enforced the same day.

### This repository (`sheikkinen/yamlgraph`, PR #726, squash `d7890517`)

| Step | Commit | Evidence |
|---|---|---|
| RED | `9395d50c` | `tests/unit/test_fr1121_ranker_loud_failure.py`: three failures. The execution-path witness's RED log reproduced the incident: `Node rank_stories failed`, then `Executing Python node: format_email`, then `send_email`. |
| Authoring | route run 2026-09-27 16:35Z | `scripts/author.sh feature-requests/authoring-briefs/fr-1121-example-ranker-brief.md`, `AUTHOR_WORKDIR` = this checkout. Authored paths: `examples/daily_digest/graph.yaml` (+`on_error: fail` on `rank_stories`), `examples/daily_digest/prompts/rank_stories.yaml` (`list[Any]` → `list[dict]`). Precedent cited by the report: `examples/demos/corpus_census/graph.yaml` (explicit `on_error: fail`), `examples/demos/corpus_census/prompts/synthesize_brief.yaml` (`list[dict]`). Validation in the report: lint before/after, validate, `pytest -k fr1121` (3 passed). No smoke, by brief. Blocked validation: the paid full-pipeline run, by brief. Repairs: none. |
| GREEN | `02df97a6` | witnesses pass; changelog fragment `changelog/unreleased/fr-1121-daily-digest-ranker-loud-failure.md`. |
| Distill | `fa0bc67d` | `docs/diary/diary-2026-09-27-reflection-fr-1121-the-green-run-that-published-nothing.md`. |
| Gate fix | `1cd1e85b` | FR-1121 registered on CAP-164 so the fragment may cite `REQ-YG-664` (changelog cross-wiring gate). |

Lint identity sets (AC-07), same command before and after
(`yamlgraph graph lint examples/daily_digest/graph.yaml`): `W013 analyze_all`,
`W806`, `W021 rank_stories` — identical. W021 (`skip_if_exists` on a list
field) pre-dates this FR and is not caused by it.

### Digest repository (`sheikkinen/yamlgraph-daily-digest`, PR #4, squash `0648fbd8`)

| Step | Commit | Evidence |
|---|---|---|
| RED | `9c5c88f` | `tests/test_fr1121_ranker_loud_failure.py`: four failures (transform, declaration, propagation with `format_markdown` executing after the failed ranker, runner printing the no-op line and exiting 0 with two recorded errors). |
| Authoring | route run 2026-09-27 16:39Z | `scripts/author.sh feature-requests/authoring-briefs/fr-1121-digest-ranker-brief.md`, `AUTHOR_WORKDIR=C:/src/yamlgraph-daily-digest`. Authored paths: `graph.yaml`, `prompts/rank_stories.yaml`; same two edits. Validation in the report: lint before/after in the digest checkout, `git diff` of the two files. No smoke, by brief. Repairs: none. |
| GREEN | `4721e70` | `run_digest.py` error guard (exit 2, every `PipelineError` to stderr, before any status handling); FR-905's `test_prompt_schema_is_untouched` replaced by the transform witness; 54 of 55 tests pass locally (see note). |

Lint identity sets, `yamlgraph graph lint graph.yaml` in the digest
checkout, before and after: `E601 gate`, `W013 analyze_all`, `W806`,
`W021 rank_stories`, `W022 analyze_all`, `W017 analyze_all` — identical;
none points at `rank_stories`'s policy or schema. E601/W013/W017/W022 are
FR-1122's.

### Deviations and route defects

- **Adapter report location and path format.** Both authoring runs edited
  exactly the briefed files and wrote complete reports, yet
  `scripts/author.sh` exited 65 each time: the Copilot backend lists
  artifacts with Windows backslashes (the wrapper's grep needs `/`), and for
  the external target it wrote the report under the launcher's `tmp/`
  instead of `AUTHOR_WORKDIR`'s. The reports were verified by hand and
  copied aside (`tmp/author-report-fr1121-example.md`,
  `tmp/author-report-fr1121-digest.md`, transient). Filed as a follow-up
  task against `scripts/author.sh`; not fixed here (judgement C-8).
- **Adapter lint claims.** Both reports state "complete output was empty"
  for lint before and after; the same commands run by the enforcer show the
  sets above. Corrected under FR-1125: the launcher's PATH carried an
  extension-less `yamlgraph` shim that PowerShell opened as a text file
  instead of running; the enforcer's recorded sets are the AC-07 evidence.
- **Windows-only local failure.** `test_vendored_copy_matches_its_recorded_digest`
  fails on a `core.autocrlf=true` checkout (raw-byte hash of a CRLF file);
  the LF-normalised hash equals the recorded one. Untouched; passes on the
  Linux runner.
- **Judge in the author's session.** The judgement was rendered by the sole
  route from the same session that authored the FR; the adapter's model
  had its own context. Recorded as a doctrine tension, not hidden.


### Deviation recorded 2026-09-27 (FR-1125)

`list[dict]` was chosen under judgement C-7 on the witness "the Anthropic
SDK transform does not raise". The spike `docs/spikes/constrained-object-2026-09-27/`
shows that transform rewrites an object with no declared properties into
`properties: {}` + `additionalProperties: false`, so the ranker answered
`{"stories": []}` on its first run on 0.6.1 (digest run 36335550129) and
the FR-905 boundary refused it. The schema is retyped to the FR-1054
`output_schema` form with declared item properties under FR-1125; the
FR-1121 witnesses become content witnesses there. Nothing in FR-1121's
loud-failure work is reverted: the loudness is what exposed the hollow form.

### Production witness (AC-11)

Pending: the first scheduled run after digest #4 (06:00 UTC, 2026-09-28).
Record here its run id and which of the three outcomes it proved.

### Production witness recorded (2026-09-28)

Manual `workflow_dispatch` run [36375149984](https://github.com/sheikkinen/yamlgraph-daily-digest/actions/runs/36375149984),
2026-09-28 03:49Z, digest `main` at `9594d91` (after #6), yamlgraph
**0.6.2** from PyPI: 32 new articles filtered, `Analysed 32 of 32 - 0
skipped`, `Node rank_stories completed successfully`, bulletin archived
as `digests/2026-09-28.md` with **7 stories**, mail sent, commit
`09527c2` pushed. First bulletin since 2026-09-18. Outcome 1 of the
three-way invariant; the ranker was invoked with articles and returned a
non-zero story count.
