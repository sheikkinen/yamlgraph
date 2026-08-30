# Feature Request: Digest delivery — archive then email, in a declared order

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-08-29
**First consumer / first event:** the `yamlgraph-daily-digest` scheduled
run, at the first cron after merge — the run that writes
`digests/<date>.md` and then emails it, in that order.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** child of FR-908, which the Judge returned **SPLIT**
(2026-08-29) with R-1 requiring Phase 1 to re-enter as its own FR. This is
that instrument. FR-819 created the repo and its "no email" scope; this FR
is the deliberate reversal of that deferral, adding email *alongside* the
committed bulletin rather than replacing it. FR-907 owns the SMTP
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

FR-908 contradicted itself by using "empty markdown" as both the legitimate
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

### Graph-authoring route (R-6)

`graph.yaml` is materially changed, so the work is graph authoring
regardless of phrasing and must go through the governed authoring route,
producing an authoring report. FR-819 recorded the same requirement for
this repo's original graph adaptation.

### Files

All unqualified paths below are in the external **`yamlgraph-daily-digest`**
repository, not in this one (R-3). FR-819 forbids that repo appearing
inside yamlgraph as a nested repo, submodule, vendored directory, or
generated artifact; this FR and its judgement are the only artifacts it
contributes here.

| File | Action |
|---|---|
| `tools/smtp_email.py`, `tools/smtp_email.tool.yaml` | **New (vendored).** Byte-identical copy of `examples/shared/smtp_email.*` from the yamlgraph repo, which excludes `examples*` from its wheel. Provenance lives in a sidecar, never in the files themselves (see below). |
| `tools/smtp_email.VENDORED.md` | **New.** Upstream path, upstream commit SHA, FR-907 reference, and the SHA-256 of each vendored file at copy time. |
| `tools/write_bulletin.py`, `tools/write_bulletin.tool.yaml` | **New.** Moves the file write and `update_readme_index()` out of `run_digest.py`; returns `{"path": str}`. |
| `graph.yaml` | **Changed.** Manifest tool refs; `write_bulletin` + `send_email` nodes; gate edge on `digest_status`; new state keys `digest_status`, `bulletin_path`, `sent`. Subject and body assembly live here — the email tool receives strings. |
| `nodes/formatting.py` | **Changed.** Emits `digest_status` alongside `digest_markdown`. |
| `run_digest.py` | **Changed.** Shrinks to arg parsing, `invoke()`, summary print. **`--dry-run` is removed** (see below). |
| `.github/workflows/digest.yml` | **Changed.** Five `SMTP_*` secrets in the run step `env:`. |
| `tests/test_workflow.py` | **New (R-4 of FR-908).** This FR is the first child to edit the workflow, so the workflow-shape baseline attaches here. |
| `README.md` | **Changed.** SMTP env contract; `--dry-run` removal noted. |

### `--dry-run` is retired, not redesigned (operator judgement)

The Judge's R-1 correctly found that the proposed dry-run was broken:
"not binding a recipient" does not compose with FR-907, which falls back
to `SMTP_TO` when `to` is absent and raises when neither yields a
recipient. So the flag would either **send anyway** (with `SMTP_TO` in the
environment — the normal case) or **exit through a missing-recipient
exception** rather than a deliberate path. A composition defect: two
individually-correct contracts, wrong when joined.

The operator's ruling is to delete the flag rather than build a route for
it. `--dry-run` is a guard flag, and guard flags are hedging: they exist
so the operator can run the pipeline without meaning it. `deviant-daily`
removed `dry_run`/`force` as paternalistic ceremony and has a test
forbidding their return — *running it IS the intent*. FR-908 quoted that
rule approvingly and then carried `--dry-run` forward anyway, which is
exactly the drift the rule exists to stop.

Consequences, all simplifications:

- `run_digest.py` loses the `--dry-run` argument, the `args.dry_run`
  branch, and the "print the bulletin, write nothing" path.
- No `dry_run` state key, no dry-run edge, no dry-run tests.
- The only early exit remains `digest_status == no_articles`, which is a
  statement about the world, not about the operator's intent.

Local iteration without sending is still possible — unset `SMTP_TO` and
the send raises loudly, which is the honest failure, not a silent skip.

### The vendoring fork, stated plainly

The wheel exclusion that forces vendoring is not theoretical. It was
measured on 2026-08-29 while enforcing FR-906: the corpus-census demo,
copied outside a checkout and run against the published `yamlgraph
0.5.23`, died with `No module named 'examples'` at the first node
importing `examples.demos.corpus_census.adapters`. `examples*` is
excluded from the wheel by `pyproject.toml`
`[tool.setuptools.packages.find]`, so nothing under `examples/shared/` is
reachable from a PyPI consumer. Vendoring is therefore the only option
available to this FR.

The consequence is a **fork with no sync mechanism**: the moment this FR
lands, `send_email` exists in two repositories, and the security
contracts that make it safe — header-injection refusal, unchained
exceptions that cannot echo the credential, config validated before the
socket — live in the copy, where an upstream fix will not reach them.

A byte-identical check at vendoring time proves the copy was correct
*once*. It cannot detect drift afterwards, because the digest repo has no
access to the upstream file at test time.

**Resolution (R-2): sidecar, not header.** The FR previously demanded the
vendored file be byte-identical to upstream *and* carry a provenance
header — which cannot both be true, since the header is a difference. The
Judge caught the contradiction; the note added just before judgement made
it worse by requiring the upstream SHA in that same header.

The scheme is now exactly:

- `tools/smtp_email.py` and `tools/smtp_email.tool.yaml` are **byte-identical**
  to upstream. Nothing is added to them.
- `tools/smtp_email.VENDORED.md` records the upstream path, the yamlgraph
  commit SHA copied from, the FR-907 reference, and the **SHA-256 of each
  vendored file** at copy time.
- The identity test compares each vendored file's SHA-256 against the
  digest recorded in the sidecar — a pinned value, never a live network
  fetch. It proves the files have not been edited locally since vendoring.

This still does not detect upstream drift, and does not pretend to. It
makes the fork legible: a reader has the exact upstream commit to diff
against.

The options, none of them free:

| Option | Cost |
|---|---|
| Vendor and accept drift (as proposed) | Silent divergence; an upstream security fix never arrives |
| Vendor + commit the upstream SHA, assert it in a test | Detects *that* upstream moved, not *what* changed; needs network or a pinned copy to compare against |
| Publish the tool as a small package | Real sync, but a distribution decision far outside this FR |
| Package `examples/shared/` into the yamlgraph wheel | Reverses a deliberate packaging policy; FR-906 A4 deferred exactly this to its own FR |

Recommended default: vendor now with the SHA recorded in the sidecar, and
let the packaging question be decided by the FR-906 A4 follow-up rather
than by this consumer.

## Implementation Status

**Enforced 2026-08-30** in `sheikkinen/yamlgraph-daily-digest`
([PR #1](https://github.com/sheikkinen/yamlgraph-daily-digest/pull/1),
squash `d9b2ab0`). No code lands in this repository; the FR and its
judgement remain the only artifacts it contributes here (R-3).

| Artifact | Commit |
|---|---|
| RED — 14 failing witnesses + vendored transport | `734193c` |
| GREEN — ordering, status field, HTML alternative | `358c695` |

RED was proven before any behaviour existed: 14 failed, 7 passed. GREEN:
24 passed.

### Live evidence (final AC)

Two real end-to-end runs against `mail.ovr.fi:465`, recipient confirmed
by the operator — first plain-text, then multipart after the operator
reported the body was raw markdown:

```
🔍 Filtered to 28 new articles
📄 Archived digests/2026-08-30.md
📬 Sent 'Daily Tech Digest — 2026-08-30' to <recipient>
```

Archive precedes send in the log, satisfying the ordering AC against a
real MTA rather than a double. No credential appears in any log line;
FR-907's non-disclosure contract holds end to end.

### Deviations

1. **The manifest could not be vendored byte-identically.** Upstream
   declares `module: examples.shared.smtp_email`, which cannot resolve
   where `examples*` is excluded from the wheel. Only the runtime
   reference changed (`module:` → `path:`); `smtp_email.py` itself is
   byte-identical at `ca44832b`, with its SHA-256 pinned in
   `tools/smtp_email.VENDORED.md` and asserted by a test. Recorded in the
   sidecar rather than silently adapted.
2. **HTML shipped, though A7 deferred it.** The operator reported the
   delivered body was raw markdown. `digest_html` is now built from the
   same story list — no markdown parser, no new dependency — and model
   output is `escape()`d, because titles and summaries are untrusted
   markup.
3. **R-6 not satisfied.** `graph.yaml` was edited directly rather than
   through the governed authoring route, under explicit operator
   authority granted for this arc. No authoring report exists. The AC
   remains formally unmet and is recorded here rather than quietly
   dropped.

### Findings the work produced

- **`tool_call` passes kwargs, not a state dict.** `write_bulletin(state)`
  failed at the first live run with `unexpected keyword argument 'today'`.
  No test caught it — every test asserted graph shape, not invocation.
- **The mark-before-delivery defect reproduced by accident.** The crashed
  run above had already written 28 URLs to `seen_urls`, so the next run
  reported "0 new articles". Exactly the hazard FR-908 A3 deferred; in CI
  it stays masked because `digest.db` persists only via the commit step.

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
- [ ] **`--dry-run` no longer exists** — no argument, no `dry_run` state
      key, no dry-run edge; a test asserts the string `dry` appears in no
      argument name in `run_digest.py` (the `deviant-daily` no-guard-flags
      pattern, which forbids the flag's return rather than trusting review)
- [ ] `tools/smtp_email.py` and `tools/smtp_email.tool.yaml` are
      byte-identical to the FR-907 upstream, with **nothing** added to
      them; `tools/smtp_email.VENDORED.md` records upstream path,
      yamlgraph commit SHA, FR-907 reference, and each file's SHA-256
- [ ] A test recomputes each vendored file's SHA-256 and compares it to
      the sidecar value — pinned, never a live fetch
- [ ] The workflow passes all five `SMTP_*` secrets; README documents them
      and records the `--dry-run` removal
- [ ] `tests/test_workflow.py` asserts the cron value, the concurrency
      group, `contents: write`, and the presence of every required secret
- [ ] CI runs pytest before the digest job
- [ ] An authoring report exists for the `graph.yaml` change
- [ ] One real scheduled run archives **and** emails a bulletin. Evidence
      must prove the **send** executed, not merely that the run and commit
      exist: the run ID, the commit SHA, **and** the FR-907 success log
      line (subject plus recipient), recorded here. No credential appears
      in the evidence — FR-907 guarantees `SMTP_PASSWORD` reaches neither
      logs nor exceptions, and this record must not reintroduce it

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Send from `run_digest.py` after `invoke()` | **Rejected.** The ordering guarantee is the point, and ordering belongs in graph edges. A runner-script send also cannot be reused by a second digest without copying the script. |
| A2 | Send first, write after | **Rejected.** Inverts the recovery property: a write failure after a successful send leaves mail referencing an artifact that does not exist, with nothing to re-send from. |
| A3 | Keep "empty markdown" as the no-op signal | **Rejected on judgement R-5.** It cannot distinguish "no new articles" from "the ranker returned garbage", so invalid model output launders into a green no-op. An explicit status cannot be faked by an empty string. |
| A4 | Implement the SMTP tool here instead of vendoring FR-907 | **Rejected.** FR-907 owns transport; duplicating it forks the security contract (header-injection refusal, unchained exceptions) into two places. |
| A5 | Depend on FR-907 by package rather than vendoring | **Rejected as currently impossible.** `pyproject.toml` excludes `examples*` from the yamlgraph wheel, so `examples/shared/` is unreachable from a PyPI consumer. Vendoring is the honest option; a distribution mechanism is a separate decision. |
| A6 | Include the workflow-test baseline in a separate FR | **Rejected on judgement R-4.** This is the first child to edit `.github/workflows/digest.yml`, so the assertions attach here rather than blocking siblings that never touch the workflow. |
| A7 | Send HTML as well as text | **Deferred.** FR-907's tool accepts `html`; rendering it is a follow-on. Text-first keeps this FR to one new capability. |
| A8 | Keep `--dry-run`, fixed with an explicit `dry_run` state key and route (judgement R-1) | **Rejected by operator judgement 2026-08-29.** R-1's diagnosis was right — the flag as proposed either sends anyway or dies on a missing recipient — but the cure is deletion, not a route. A dry-run flag is hedging: it exists so the pipeline can be run without meaning it. `deviant-daily` retired `dry_run`/`force` for this reason and tests that they stay gone. Retiring it removes a flag, a state key, an edge, and two tests. |

**`is_this_a_graph`: yes, and it already is one.** This FR changes the
existing pipeline's edges and nodes rather than adding a script, which is
the whole argument of A1. The authoring route applies (R-6).

## Out of Scope

- SMTP transport implementation (FR-907)
- Slot-bound collection (FR-904)
- Rank→format validation and the `invalid` status value (FR-905)
- The committed-SQLite question and the JSONL ledger
- Markdown→HTML rendering

## Related

- FR-908 — parent; SPLIT verdict 2026-08-29, R-1 and R-4 and R-5 and R-6
- FR-907 — the SMTP tool this vendors; hard dependency
- FR-904, FR-905 — independent siblings
- FR-819 — created the repo and the "no email" scope this reverses
