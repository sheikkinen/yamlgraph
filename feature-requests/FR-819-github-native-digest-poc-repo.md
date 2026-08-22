# Feature Request: GitHub-Native Daily Digest — Streamlined Proof-of-Concept Repo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Completed 2026-08-19 — AC-07 cron observation satisfied
**Effort:** 1 day
**Requested:** 2026-08-18
**First consumer / first event:** the operator, on the first morning a
scheduled GitHub Actions run commits `digests/YYYY-MM-DD.md` to the new
public repo with zero servers involved. Second consumer: the
`plan-github-chaplain-arbitrary-repo` plan, which needs "yamlgraph runs
unattended in GitHub Actions" proven on a low-risk graph before the
judge pipeline inherits the pattern.

## Summary

Create a new, minimal public repository (working name:
`yamlgraph-daily-digest`) that runs the daily HN digest pipeline
entirely inside GitHub Actions on a cron schedule and publishes the
bulletin by committing markdown back to itself — an auto-updating repo.
No Fly.io, no FastAPI, no Docker, no Resend email. The repo *is* the
runtime, the state store, and the publication channel.

## Value Statement

Proves publicly that a yamlgraph pipeline runs unattended on GitHub
infrastructure with commit-based state and output — the first Proclaim
artifact, and the substrate proof the chaplain-as-action plan depends on.

## Problem

`examples/daily_digest/` demonstrates the pipeline but drags a
deployment stack (Fly.io machine, FastAPI + SlowAPI HTTP layer, Docker
image, persistent volume, Resend email) that exists only because the
cron trigger and the compute were on different machines. GitHub Actions
removes that split: the cron, the compute, the state, and the
publication can all live in one repo. Meanwhile the project has zero
public artifacts demonstrating "yamlgraph executes in GitHub" — the
central claim of the agent-channel strategy remains unproven prose.

## Ideal Result

A public repo where the only moving parts are one workflow file, one
graph, and its prompts. Every morning at 06:00 UTC a run commits
`digests/YYYY-MM-DD.md` and an updated `README.md` index. Anyone —
human or agent — can read the bulletin, star the repo, or fork the
workflow. The git log is the delivery log; the committed dedup state is
the audit trail. Total infrastructure cost: one `ANTHROPIC_API_KEY`
secret.

## Proposed Solution

New repo contents (barebones):

```
yamlgraph-daily-digest/
├── .github/workflows/digest.yml   # cron + workflow_dispatch
├── graph.yaml                     # adapted from examples/daily_digest
├── prompts/                       # analyze/rank prompts (copied)
├── nodes/                         # sources, filters, content, formatting
├── run_digest.py                  # CLI entry: --db, --output
├── digest.db                      # committed dedup/checkpoint state
├── digests/                       # one markdown bulletin per day
└── README.md                      # index of recent digests + how it works
```

Workflow:

```yaml
on:
  schedule: [{cron: "0 6 * * *"}]
  workflow_dispatch:
permissions: {contents: write}
concurrency:
  group: daily-digest
  cancel-in-progress: false
jobs:
  digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      # R-2: yamlgraph from PyPI + only the copied nodes' direct deps —
      # NOT yamlgraph[digest], whose extra drags FastAPI/SlowAPI/Uvicorn/Resend
      - run: pip install yamlgraph feedparser beautifulsoup4 httpx python-dotenv
      - run: python run_digest.py --db digest.db --output digests/
        env: {ANTHROPIC_API_KEY: "${{ secrets.ANTHROPIC_API_KEY }}"}
      - run: |
          git config user.name "digest-bot"
          git config user.email "actions@github.com"
          git add digests/ digest.db README.md
          if git diff --cached --quiet; then
            echo "digest: no-op — no new stories, nothing to commit"
          else
            git commit -m "digest $(date -u +%F)"
            git pull --rebase origin main
            git push
          fi
```

State-race and no-op behavior (R-4): the `concurrency` group with
`cancel-in-progress: false` serializes cron and `workflow_dispatch`
runs; `git pull --rebase` before push absorbs any commit landed since
checkout; when zero new stories pass dedup, `run_digest.py` writes no
bulletin and no README change — the workflow logs the no-op line and
exits green without committing. A same-day second run therefore
produces neither duplicate story entries nor conflicting commits.

Changes vs `examples/daily_digest/`:

1. **Delete on copy:** `Dockerfile`, `fly.toml`, `api/` (FastAPI +
   SlowAPI), `nodes/email.py`, `templates/` (HTML email),
   `scripts/gh-secrets.sh`, all Resend/`RECIPIENT_EMAIL` references.
2. **Add markdown formatter:** replace the `format_email` node with a
   `format_markdown` node rendering the ranked stories to
   `digests/YYYY-MM-DD.md` (title, link, one-paragraph analysis each).
3. **Add README index update:** deterministic Python (not LLM) that
   rewrites a `<!-- digest-index -->` block in `README.md` listing the
   last 14 bulletins.
4. **State:** keep SQLite (`DATABASE_PATH` already env-configurable);
   the file is committed each run. Dedup window unchanged (24h).
5. **Install from PyPI**, not editable checkout — the PoC must consume
   the published package like any adopter would. Dependency-honest
   install (R-2): `pip install yamlgraph feedparser beautifulsoup4
   httpx python-dotenv` — the copied nodes own their direct
   dependencies; the `yamlgraph[digest]` extra is NOT used because it
   installs FastAPI, SlowAPI, Uvicorn, and Resend, contradicting the
   PoC's deployment claim. No package-extra change in this repo.

Graph authoring and repo boundary (R-3): adapting `graph.yaml` and
`prompts/*.yaml` for the PoC is graph authoring and must use the
governed route (`scripts/author.sh`), with the authoring report
retained as enforcement evidence. The PoC repo is a separate GitHub
repository — it must never be committed into yamlgraph as a nested
working tree, submodule, vendored directory, or generated artifact.
The only yamlgraph-repo change authorized by this FR is the
`examples/daily_digest/README.md` pointer.

## Acceptance Criteria

- [ ] AC-01: FR-819 contains the prior-art disposition table (R-1)
- [ ] AC-02: The public `yamlgraph-daily-digest` repo exists outside
      this repository and is not committed as a nested repo, submodule,
      vendored directory, or generated artifact here
- [ ] AC-03: The workflow has `workflow_dispatch`, a 06:00 UTC cron,
      `permissions: contents: write`, a digest-specific `concurrency`
      group with `cancel-in-progress: false`, and a safe refresh
      (`git pull --rebase`) before push
- [ ] AC-04: The workflow installs `yamlgraph` from PyPI and does not
      install FastAPI, SlowAPI, Uvicorn, Resend, or email-only deps
- [ ] AC-05: The PoC repo contains no Fly.io, Docker, FastAPI, Resend,
      email-delivery, or HTTP-server runtime references
- [ ] AC-06: `workflow_dispatch` completes green and commits
      `digests/YYYY-MM-DD.md`, `digest.db`, and an updated README index
- [x] AC-07: At least one scheduled cron run completes green and
      commits a bulletin without human runner access
- [ ] AC-08: A second same-day run proves committed-state dedup — no
      duplicate story entries, no conflicting state commit
- [ ] AC-09: When no new stories are available, no empty bulletin is
      written and the workflow logs the no-op condition clearly
- [ ] AC-10: PoC `README.md` contains a deterministic index block
      listing the latest bulletins
- [ ] AC-11: `examples/daily_digest/README.md` links to the PoC repo as
      the GitHub-native deployment variant
- [ ] AC-12: If any PoC `graph.yaml` or `prompts/*.yaml` is created or
      materially adapted during enforcement, the graph-authoring report
      exists and records lint/smoke validation for those artifacts

## Prior Art Disposition (R-1)

**Prior art:** hook hits dispositioned — FR-690 (event-sequence field;
keyword "poc" only, no domain overlap with a digest deployment PoC) and
FR-081 (copilot node; keyword "digest"/"poc" only — FR-819 uses no
copilot nodes, its graph is llm/python/map). Substantive prior art is
dispositioned in the table below per judgement R-1.

| Prior art | Disposition |
|---|---|
| `examples/daily_digest/` | Source pipeline only; remains Fly.io/FastAPI/Resend in place. Not modified except the README pointer (AC-11). |
| `feature-requests/046-diary-world-digest.md` | Distinguished: FR-046 rejected its "GitHub Action only" option because CI added a dependency for a *development tool* whose consumer was the local diary. FR-819's artifact is a *public publication*, not a dev tool — CI is the natural runtime, and the Action IS the deliverable, not a compromise. |
| `feature-requests/FR-243-github-issues-remote-inbox.md` | Distinguished: FR-243 is remote *intake* (issues → inbox). FR-819 is unattended *execution and publication* on GitHub Actions. The GitHub-as-agent-channel lesson is preserved; no issue-intake scope is taken. |
| `feature-requests/FR-450-judge-demo-hardening.md`, `FR-452`, `FR-453`, `docs/plan-github-chaplain-arbitrary-repo.md` | Downstream consumers, not deliverables. FR-819 proves cron + PyPI install + committed state only; it packages no planner/judge graphs and no Actions Marketplace surface. |

## Alternatives Considered

- **Modify `examples/daily_digest/` in place:** conflates "example of
  the pipeline" with "live deployment"; the example keeps its multi-node
  teaching value, and a PoC repo exercises the real adopter path
  (PyPI install, own secrets, own Actions quota).
- **Keep Resend email alongside:** rejected per scope — the committed
  bulletin IS the delivery; email re-adds a secret, a vendor, and a
  failure mode with no reader the repo doesn't already serve.
- **actions/cache for dedup state:** caches are evictable and invisible;
  committed state is durable and auditable, and "auto-updating repo" is
  the point.
- **GitHub Pages rendering:** deferred; markdown in the repo is readable
  by both humans and agents without a build step.

## Related

- `examples/daily_digest/` — source pipeline (graph, nodes, prompts)
- `docs/plan-github-chaplain-arbitrary-repo.md` — depends on this
  substrate proof
- `docs/research-agent-channels-2026-08-18.md` — Proclaim channel arc
- `docs/diary/diary-2026-08-18-missing-last-leg.md` — the missing
  Proclaim/Harvest stages this PoC instantiates

## Judgement (2026-08-18)

**Verdict:** APPROVED WITH REVISIONS — revisions R-1 through R-4
rendered by the judge graph (`scripts/judge.sh`, gpt-5.5, full draft in
`tmp/draft-judgement.md`) are folded into this FR above; authority is
active under the conditions below.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| R-1 | Prior art undispositioned (FR-046 rejected "Action only" option, FR-243, FR-450/452/453) | Prior Art Disposition table added above |
| R-2 | `yamlgraph[digest]` extra installs FastAPI/SlowAPI/Uvicorn/Resend, contradicting the "no FastAPI/Resend" claim | Install pinned to `yamlgraph` + direct node deps; no package-extra change |
| R-3 | Graph-authoring route and repo boundary unstated | PoC graph/prompt adaptation goes through `scripts/author.sh`; PoC repo never vendored into yamlgraph |
| R-4 | No concurrency, push-conflict, or no-op behavior specified | `concurrency` group, `pull --rebase` before push, explicit no-op logging; AC-08/AC-09 |

**Conditions (all GATE):**

1. C-1: Authority begins after R-1–R-4 folded (done above).
2. C-2: Enforcer must not invoke or re-run the judge.
3. C-3: Graph/prompt creation uses the governed graph-authoring route.
4. C-4: PoC repo stays a separate repository boundary.
5. C-5: No scope expansion into Chaplain-as-Action, Marketplace
   packaging, GitHub App work, or Harvest metrics — separate FRs.
6. C-6: No yamlgraph package-metadata change (R-2 option 1 chosen).
7. C-7: Human review required before relying on any new public-repo
   secret or token permission beyond the scoped PoC workflow.

**Purge list:** `yamlgraph[digest]` install reference (replaced);
Resend/email delivery; GitHub Pages; Marketplace packaging.

**Scope frozen:** D-1 PoC repo (workflow, graph, prompts, nodes,
`run_digest.py`, `digests/`, committed `digest.db`, README index);
D-2 one dispatch + one cron run recorded in this FR's implementation
notes; D-3 same-day dedup proof; D-4 example README pointer; D-6
graph-authoring report for adapted artifacts.

### Questions for the human (as options, or 'none')

None — R-2's binary (direct deps vs new extra) was resolved to direct
deps, the strictly smaller change; all other revisions were foldable
without choices.

## Implementation Notes (2026-08-18)

Enforced same day. Repo: <https://github.com/sheikkinen/yamlgraph-daily-digest>

- **D-1** — PoC repo created public; workflow, graph, prompts, nodes,
  `run_digest.py`, `digests/`, committed `digest.db`, README index.
  Initial commit `6880bf7`.
- **C-3 / AC-12** — `graph.yaml` + both prompts authored via
  `scripts/author.sh tmp/task-brief-fr819-digest-graph.md` (governed
  route, gpt-5.5); report retained at `tmp/fr819-authoring-report.md`;
  lint 0 errors, compile smoke `compiles`.
- **AC-06 (D-2)** — `workflow_dispatch` run green; the runner committed
  `digest 2026-08-18` (`a9222a7`): bulletin + `digest.db` + README index.
- **AC-08/AC-09 (D-3)** — second same-day dispatch (run `32171350506`)
  green: `After filtering: 0`, logged `digest: no-op — no new stories,
  nothing to commit`, pushed no commit — committed-state dedup proven
  across ephemeral runners.
- **AC-07** — satisfied 2026-08-19: first scheduled run (event
  `schedule`, run 32224291170) completed green in 1m04s and committed
  `digests/2026-08-19.md` ("digest 2026-08-19") with no human runner
  access.
- **AC-04/R-2** — install line is
  `pip install yamlgraph feedparser beautifulsoup4 httpx python-dotenv`
  (yamlgraph 0.5.22 from PyPI); no FastAPI/SlowAPI/Uvicorn/Resend.
- **AC-11 (D-4)** — pointer added to `examples/daily_digest/README.md`.
- **Deviations:** (1) dropped the sqlite *checkpointer* from the PoC
  graph — ephemeral runners never resume; `digest.db` carries only
  `seen_urls`, keeping committed state minimal. (2) Two boundary fixes
  in `nodes/formatting.py` / `run_digest.py`: ranked stories arrive as
  a plain dict (`{"stories": [...]}`) after serialization — normalize
  at entry; and with zero filtered articles the ranker's output is
  untrusted — the runner treats it as no-op regardless (guards AC-09).
- **C-6** — no yamlgraph package-metadata change; yamlgraph diff is
  docs-only (this FR file, example README pointer, diary).

**Brief provenance (FR-852):** authoring brief committed at
`feature-requests/authoring-briefs/fr-819-digest-graph-brief.md`
(formerly `tmp/task-brief-fr819-digest-graph.md`).
