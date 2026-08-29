# Feature Request: Refactor yamlgraph-daily-digest into slot-bound reusable tools

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-08-29
**First consumer / first event:** the `yamlgraph-daily-digest` scheduled run
itself, at the first 06:00 UTC cron after Phase 1 merges — the run that
writes `digests/<date>.md`, then emails it, in that order. Second consumer
(Phase 2): a sibling digest repo that binds a different `collect` manifest
and changes no graph.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** FR-819 created this repo and is the direct precedent —
its "repo is the runtime, state store, and publication channel" premise is
preserved, not overturned; email is added alongside the committed bulletin
(see Out of Scope). FR-900 and FR-901 are siblings filed in the same arc:
FR-900 blocks Phase 2, FR-901 supplies the Phase 1 node. FR-892
(corpus-census injected adapters) is the slot pattern Phase 2 copies
verbatim — this FR adds no slot mechanism, only a second application of
it. FR-768 supplies the manifest contract unchanged. No prior FR was
rejected in this territory.

## Summary

`yamlgraph-daily-digest` (created by FR-819) has run green 11/11 days since
2026-08-18, committing a markdown bulletin per day. Refactor it so that
(a) the report is delivered by email after being archived, (b) its
collection stages become reusable FR-768 manifests bound as FR-892 slots,
and (c) the one probabilistic failure in the pipeline is closed at the
boundary. The intent is that a second digest is a new repo with different
slot bindings, not a copy of this one's Python.

## Value Statement

One digest pipeline serves many digests: a new subject area becomes a
`--tool collect=<manifest>` binding and a topics list, while filtering,
analysis, ranking, rendering, and delivery are shared verbatim.

## Problem

The repo works. This is hardening a live pipeline, not rescuing a dead one
— a correction to an earlier reading of a stale local clone. Verified
2026-08-29 after `git pull`:

```
11 consecutive successful scheduled runs, 2026-08-18 → 2026-08-28
digests/2026-08-18.md … 2026-08-28.md, 4.5–5.4 KB each, ~1m20s per run
```

Four defects, in descending order of consequence:

**1. Nobody is delivered the report.** Eleven bulletins sit in a repo. The
FR-819 design explicitly had "no email"; the operator now has SMTP config
and wants delivery. Addressed by FR-901 plus the ordering below.

**2. The rank→format seam is probabilistic.** `prompts/rank_stories.yaml`
declares `stories: type: list[Any]`. `yamlgraph/schema_loader.py` resolves
that to `list[Any]`, which gives the provider **no item structure**, so the
model may return objects or strings. `nodes/formatting.py` then calls
`story.get(...)`. Eleven runs returned dicts. On 2026-08-29 the same
schema, against the same `anthropic/claude-haiku-4-5`, returned a list of
strings and crashed the equivalent renderer in `examples/daily_digest`
(`jinja2.exceptions.UndefinedError: 'str object' has no attribute
'relevance'`). This is not a latent bug; it is a coin flip weighted toward
working, which is the shape that survives review and fails on day 40. The
existing tests in `examples/daily_digest/tests/` all pass because they feed
the formatter well-formed dicts — the seam has no test in either repo.

**3. The tools are not reusable.** `graph.yaml` declares five inline
`type: python, module: nodes.*` tools, which is why `run_digest.py` needs
`sys.path.insert(0, REPO_DIR)`. `RSS_FEEDS` and the HN endpoint are
hardcoded in `nodes/sources.py`. A second digest can only be a fork.

**4. No tests at all.** 14 tracked files, zero test files. The workflow's
cron, concurrency group, and write ceiling are unasserted.

Two known conditions deliberately **not** treated as defects here — see
Out of Scope.

## Ideal Result

The repo is the reference digest: a graph whose collection stage is a
declared contract, whose report is archived to git and then delivered by
mail, whose failures are loud, and whose workflow shape is asserted by
tests. Standing up a second digest requires a topics list and one manifest
— no Python, no graph edits. The minimal path back from that is three
phases, the first of which does not depend on anything unreleased.

## Proposed Solution

### Phase 1 — deliver, in a declared order (unblocked today)

Current shape leaves the two side effects unordered: `run_digest.py` writes
the bulletin *after* `invoke()` returns, so a send added anywhere has no
defined relationship to the write. Move both into the graph:

```
format_markdown ──▶ gate ──▶ write_bulletin ──▶ send_digest ──▶ END
                      └────────────────────────────────────────▶ END   (empty bulletin)
```

The artifact reaches disk **before** the network call —
persist-before-publish, as `deviant-daily/tools/steps.py` enforces around
its DeviantArt calls.

The failure algebra this produces, without any new state machinery:

| Event | Consequence |
|---|---|
| Send fails | node raises → `run_digest` exits non-zero → the workflow's commit step never runs → `digest.db` is discarded with the runner → tomorrow retries the whole day cleanly |
| Send succeeds, commit fails | one duplicate email tomorrow. Accepted; recorded as a known risk |
| No new articles | gate routes to END; no write, no send, no commit — the existing no-op behaviour, moved from Python into an edge |

| File | Action |
|---|---|
| `tools/smtp_send.py`, `tools/smtp_send.tool.yaml` | **New.** Per FR-901. |
| `tools/write_bulletin.py`, `tools/write_bulletin.tool.yaml` | **New.** Moves the file write and `update_readme_index()` out of `run_digest.py`; returns `{"path": str}`. |
| `graph.yaml` | **Changed.** Manifest tool refs; `write_bulletin` + `send_digest` nodes; gate edge on empty `digest_markdown`; state keys `bulletin_path`, `sent`. |
| `run_digest.py` | **Changed.** Shrinks to arg parsing, `invoke()`, summary print. `--dry-run` keeps working by not binding a recipient — not by a new guard flag. |
| `.github/workflows/digest.yml` | **Changed.** Five `SMTP_*` secrets added to the run step `env:`. |
| `README.md` | **Changed.** SMTP env contract documented. |

### Phase 2 — reusable collection (requires FR-900)

Manifest-ise the four existing node modules, then convert collection to a
slot:

```yaml
tools:
  collect:
    slot: true
    contract:
      runtimes: [python]
      args: [config]
```

```bash
yamlgraph graph run graph.yaml --tool collect=sources/hn_rss.tool.yaml
```

This is the `examples/demos/corpus_census` proof applied to digests — one
pipeline, many corpora, zero graph changes. Ship at least **two** source
manifests, because a slot with one binding has not been shown to be a slot:
`sources/hn_rss.tool.yaml` (current behaviour, with `RSS_FEEDS` moved from
module constant to manifest-supplied config) and one genuinely different
source.

Manifest-ising also removes the `sys.path.insert` hack, since manifest
paths resolve relative to the manifest file.

**Hard dependency:** FR-892 `--tool` is absent from every published
yamlgraph. Phase 2 cannot start until FR-900 ships. Phase 1 is unaffected
— FR-768 manifests are in `v0.5.22`.

### Phase 3 — close the rank→format seam

Normalize where the model output enters the deterministic world, not where
it manifests (the one law). In `format_markdown`: validate each ranked item
against a typed model, drop non-conforming items, and **raise if none
survive** — never emit a success-shaped empty bulletin. Optionally
reconcile each `url` against the `analyzed` set per
`reference/patterns/corpus-map-reduce.md`, which additionally catches
invented stories.

Condemning test first: `format_markdown` fed `["a string", "another"]`.

Whether the schema itself gains item structure is a yamlgraph-side question
(`schema_loader.py` has no nested-model support in the `fields:` shorthand)
and is **not** in this FR — the boundary guard is correct regardless of
what the schema later becomes.

## Acceptance Criteria

**Phase 1**
- [ ] Graph declares `format_markdown → gate → write_bulletin → send_digest`;
      the gate edge routes an empty bulletin to END
- [ ] A test proves the write precedes the send (ordering asserted as a
      transition sequence, not inferred from the terminal state)
- [ ] A simulated send failure leaves `digests/<date>.md` written and exits
      non-zero
- [ ] `run_digest.py` contains no file-writing or delivery logic
- [ ] Workflow passes all five `SMTP_*` secrets; README documents them
- [ ] One real scheduled run archives **and** emails a bulletin, evidenced
      in the FR by run ID and commit SHA

**Phase 2** (after FR-900)
- [ ] `collect` is a slot; at least **two** source manifests bind it
- [ ] Switching sources requires no edit to `graph.yaml`
- [ ] `run_digest.py` no longer mutates `sys.path`
- [ ] Workflow pins `yamlgraph>=<FR-900 version>`

**Phase 3**
- [ ] Condemning test committed RED before the fix (separate commit)
- [ ] Non-conforming ranked items are dropped; all-non-conforming raises
- [ ] No path emits an empty bulletin as success

**Throughout**
- [ ] `tests/test_workflow.py` asserts cron value, concurrency group,
      `contents: write`, and the presence of every required secret —
      the `deviant-daily/tests/test_workflows.py` pattern
- [ ] CI runs pytest before the digest job
- [ ] README updated

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Start a third digest repo instead of refactoring this one | **Rejected.** Two copies of the pipeline already exist (`examples/daily_digest`, this repo); a third is `growth_as_default`. This repo has the running cron and 11 days of production evidence. |
| A2 | Refactor `examples/daily_digest` instead | **Rejected.** It is the Fly.io/FastAPI/Resend variant and is currently broken at `format_email`. The GitHub-native repo is the shape the operator asked for. Its retirement is a separate disposition (see Related). |
| A3 | Replace `digest.db` with a committed JSONL ledger (deviant-daily pattern) | **Deferred with rationale, not rejected.** In CI, `digest.db` persists *only* via the commit step, so a failed run discards its dedupe writes with the runner — the mark-before-delivery bug is accidentally transactional. The residual risk is one duplicate email after a commit failure. Adopting the ledger now would be a large change buying a small delta. Revisit if a duplicate actually occurs. |
| A4 | Keep collection inline; make reuse a documentation pattern | **Rejected.** The stated intent is reusable tools for other digests. Documentation does not stop the second repo from forking `nodes/sources.py`; a slot contract does. |
| A5 | Do Phase 2 first (reuse before delivery) | **Rejected.** Phase 2 is blocked on an unreleased feature; Phase 1 is not, and delivery is the acknowledged user-visible gap. |
| A6 | Fix `list[Any]` in `schema_loader.py` (nested schemas) instead of guarding at the boundary | **Out of scope here, worth its own FR.** A framework change judged in a consumer FR is scope creep, and the boundary guard is required regardless — the model can always return a well-typed lie. |
| A7 | Send HTML mail in Phase 1 | **Deferred.** FR-901's tool accepts `html`; rendering it is a follow-on node. Text-first keeps Phase 1 to one new capability. |
| A8 | Remove `digest.db` from git (4 KB binary churn/day) | **Deferred.** Real (`.git` at 592 KB after 11 days) but not urgent, and it is subsumed by A3 whenever that is taken. |

## Out of Scope

- The committed-SQLite question (A3, A8)
- Framework-side nested schema support (A6)
- Retiring `examples/daily_digest` — proposed separately, per the
  subtraction-disposition expectation
- Any change to the FR-819 "repo is the runtime and publication channel"
  premise; email is added **alongside** the committed bulletin, not
  instead of it

## Related

- FR-901 SMTP digest delivery tool — supplies the `send_digest` node (Phase 1)
- FR-900 release tool slots to PyPI — blocks Phase 2
- FR-819 GitHub-native digest PoC repo — created the repo being refactored
- FR-892 corpus-census pipeline — the slot pattern Phase 2 copies
- FR-768 tool manifests — the declaration mechanism
- `deviant-daily/tools/steps.py`, `tools/ledger.py`,
  `tests/test_workflows.py` — persist-before-publish, ledger (deferred),
  workflow-shape tests
- `reference/patterns/corpus-map-reduce.md` — deterministic reconciliation
- Verified 2026-08-29: `git merge-base --is-ancestor 06d1dfe4 v0.5.22` →
  false; `pyproject.toml` excludes `examples*` from the wheel
