# Feature Request: Digest delivery — archive then email, in a declared order

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-29
**First consumer / first event:** the `yamlgraph-daily-digest` scheduled
run, at the first cron after merge — the run that writes
`digests/<date>.md` and then emails it, in that order.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** child of FR-902, which the Judge returned **SPLIT**
(2026-08-29) with R-1 requiring Phase 1 to re-enter as its own FR. This is
that instrument. FR-819 created the repo and its "no email" scope; this FR
is the deliberate reversal of that deferral, adding email *alongside* the
committed bulletin rather than replacing it. FR-901 owns the SMTP
transport and is a hard dependency; this FR must not implement transport.
Siblings FR-904 (slot collection) and FR-905 (rank→format boundary) are
independent and share no surface with this one.

## Summary

Move the bulletin write and README-index update out of `run_digest.py` and
into graph tools, then append an email node after them, so that the
archive is on disk before the network call. Route a no-new-articles run to
END without writing or sending.

## Value Statement

The eleven bulletins this repo has committed since 2026-08-18 reach a
human, and a delivery failure can never destroy the artifact it was
supposed to deliver.

## Problem

`yamlgraph-daily-digest` has run green 11/11 days since 2026-08-18,
committing a markdown bulletin per day that nobody is pushed. FR-819
scoped email out deliberately; the operator now has SMTP configuration and
wants delivery.

Adding a send is not the whole problem. The current shape leaves the two
side effects **unordered**: `run_digest.py` writes the bulletin *after*
`compiled.invoke()` returns, so a send placed anywhere has no defined
relationship to the write. Ordering of side effects belongs in the graph's
edges, not in the incidental sequencing of a runner script — which is also
why the ordering cannot be reused by a second digest without copying the
script.

## Ideal Result

The graph states the delivery contract in its edges: gate, then archive,
then send. A failed send leaves a complete bulletin on the runner and a
red run; a no-op day writes and sends nothing; and the ordering is a
property of the pipeline rather than of one runner script.

## Proposed Solution

```
format_markdown ──▶ gate ──▶ write_bulletin ──▶ send_email ──▶ END
                      └──────────────────────────────────────▶ END   (no-op day)
```

The artifact reaches disk **before** the network call: persist before
publish.

### The no-op predicate (R-5)

FR-902 contradicted itself by using "empty markdown" as both the legitimate
no-new-articles signal and the failure signal. This FR uses an **explicit
status**, never emptiness:

`write_bulletin`'s gate reads a `digest_status` state key set by
`format_markdown`, with exactly two values in this FR's scope:

| `digest_status` | Meaning | Route |
|---|---|---|
| `no_articles` | `filtered_articles` was empty; the ranker was never given anything to rank | END, no write, no send |
| `ready` | a bulletin was rendered from at least one ranked story | write → send |

A third value (`invalid`, for a malformed ranked response) is introduced by
FR-905 and is explicitly **out of scope here** — but the predicate is a
status field from the outset precisely so FR-905 can add that value without
re-litigating the routing.

### Failure algebra, with no new state machinery

| Event | Consequence |
|---|---|
| Send fails | node raises → `run_digest` exits non-zero → the workflow's commit step never runs → `digest.db` is discarded with the runner → the next run retries the whole day cleanly |
| Send succeeds, commit fails | one duplicate email on the next run. Accepted; recorded as a known risk |
| `digest_status == no_articles` | gate → END; nothing written, sent, or committed |

### Files

| File | Action |
|---|---|
| `tools/smtp_email.py`, `tools/smtp_email.tool.yaml` | **New (vendored).** Verbatim copy of `examples/shared/smtp_email.*` from the yamlgraph repo, which excludes `examples*` from its wheel. The copy is recorded as a vendored artifact with its upstream FR-901 provenance in a header comment. |
| `tools/write_bulletin.py`, `tools/write_bulletin.tool.yaml` | **New.** Moves the file write and `update_readme_index()` out of `run_digest.py`; returns `{"path": str}`. |
| `graph.yaml` | **Changed.** Manifest tool refs; `write_bulletin` + `send_email` nodes; gate edge on `digest_status`; new state keys `digest_status`, `bulletin_path`, `sent`. Subject and body assembly live here — the email tool receives strings. |
| `nodes/formatting.py` | **Changed.** Emits `digest_status` alongside `digest_markdown`. |
| `run_digest.py` | **Changed.** Shrinks to arg parsing, `invoke()`, summary print. `--dry-run` continues to work by not binding a recipient, not by a new guard flag. |
| `.github/workflows/digest.yml` | **Changed.** Five `SMTP_*` secrets in the run step `env:`. |
| `tests/test_workflow.py` | **New (R-4).** This FR is the first child to edit the workflow, so the workflow-shape baseline attaches here. |
| `README.md` | **Changed.** SMTP env contract. |

### Graph-authoring route (R-6)

`graph.yaml` is materially changed, so the work is graph authoring
regardless of phrasing and must go through the governed authoring route,
producing an authoring report. FR-819 recorded the same requirement for
this repo's original graph adaptation.

## Acceptance Criteria

- [ ] `graph.yaml` declares `format_markdown → gate → write_bulletin →
      send_email`, with the gate routing `digest_status == no_articles`
      to END
- [ ] A test asserts the **transition sequence**, not merely the terminal
      state: `write_bulletin` is visited before `send_email`
      (`assert_path_not_destination` — a terminal-state-only assertion
      passes via error-recovery paths)
- [ ] A simulated send failure leaves `digests/<date>.md` written on disk
      and exits non-zero
- [ ] `digest_status == no_articles` produces no write, no send, and no
      commit
- [ ] Routing is driven by `digest_status`, never by empty markdown —
      asserted by a test that renders an empty bulletin with
      `digest_status == ready` and requires it **not** to be treated as a
      no-op
- [ ] `run_digest.py` contains no file-writing and no delivery logic
- [ ] The vendored `tools/smtp_email.py` is byte-identical to the FR-901
      upstream, with provenance recorded in a header comment
- [ ] The workflow passes all five `SMTP_*` secrets; README documents them
- [ ] `tests/test_workflow.py` asserts the cron value, the concurrency
      group, `contents: write`, and the presence of every required secret
- [ ] CI runs pytest before the digest job
- [ ] An authoring report exists for the `graph.yaml` change
- [ ] One real scheduled run archives **and** emails a bulletin, evidenced
      here by run ID and commit SHA

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Send from `run_digest.py` after `invoke()` | **Rejected.** The ordering guarantee is the point, and ordering belongs in graph edges. A runner-script send also cannot be reused by a second digest without copying the script. |
| A2 | Send first, write after | **Rejected.** Inverts the recovery property: a write failure after a successful send leaves mail referencing an artifact that does not exist, with nothing to re-send from. |
| A3 | Keep "empty markdown" as the no-op signal | **Rejected on judgement R-5.** It cannot distinguish "no new articles" from "the ranker returned garbage", so invalid model output launders into a green no-op. An explicit status cannot be faked by an empty string. |
| A4 | Implement the SMTP tool here instead of vendoring FR-901 | **Rejected.** FR-901 owns transport; duplicating it forks the security contract (header-injection refusal, unchained exceptions) into two places. |
| A5 | Depend on FR-901 by package rather than vendoring | **Rejected as currently impossible.** `pyproject.toml` excludes `examples*` from the yamlgraph wheel, so `examples/shared/` is unreachable from a PyPI consumer. Vendoring is the honest option; a distribution mechanism is a separate decision. |
| A6 | Include the workflow-test baseline in a separate FR | **Rejected on judgement R-4.** This is the first child to edit `.github/workflows/digest.yml`, so the assertions attach here rather than blocking siblings that never touch the workflow. |
| A7 | Send HTML as well as text | **Deferred.** FR-901's tool accepts `html`; rendering it is a follow-on. Text-first keeps this FR to one new capability. |

**`is_this_a_graph`: yes, and it already is one.** This FR changes the
existing pipeline's edges and nodes rather than adding a script, which is
the whole argument of A1. The authoring route applies (R-6).

## Out of Scope

- SMTP transport implementation (FR-901)
- Slot-bound collection (FR-904)
- Rank→format validation and the `invalid` status value (FR-905)
- The committed-SQLite question and the JSONL ledger
- Markdown→HTML rendering

## Related

- FR-902 — parent; SPLIT verdict 2026-08-29, R-1 and R-4 and R-5 and R-6
- FR-901 — the SMTP tool this vendors; hard dependency
- FR-904, FR-905 — independent siblings
- FR-819 — created the repo and the "no email" scope this reverses
