# Diary 2026-08-19 — The Satellite Mold: GitHub-Cron YAMLGraphs in Bigger Context

**Context:** FR-819 (`yamlgraph-daily-digest`) and FR-826
(`deviant-daily`) are two instances of the same pattern, built one day
apart. The second took a single session because the first was a mold.
This entry names the pattern, places it in its lineage, and states
honestly where it breaks.

## The pattern

A public GitHub repo that is simultaneously five things:

1. **Runtime** — Actions cron is the scheduler, an ephemeral runner is
   the compute; `pip install yamlgraph` rebuilds the world each morning.
2. **State store** — a committed JSONL ledger; every transition is a
   commit, so the git log IS the transaction log.
3. **Config** — `graph.yaml` + `prompts/*.yaml`; the pipeline logic is
   declarative and diffable.
4. **Publication record** — `posts/*.md` with provenance (date, model,
   prompt, URL); the output archives itself next to the code that made it.
5. **Secrets vault with metabolism** — repo secrets, including the
   self-rotation move: the workflow rewrites its own `DA_REFRESH_TOKEN`
   via a scoped PAT before any side effect.

The compute-heavy parts (image gen, vision, LLM) are all delegated to
APIs — the repo orchestrates thin and delegates heavy. That is what
makes a free ephemeral runner sufficient.

## Lineage — this is not new, only newly composed

- **cron + shell on a VPS** — the ancestor. Full control, but a pet
  server, secret sprawl, and zero audit trail unless you build one.
- **git-scraping** (Simon Willison) and **flat-data** (githubocto) —
  proved "Actions cron + commit-back = database" for *reads*. Our
  pattern extends it to *writes with side effects* (publishing), which
  is why it needed the idempotency ledger and the gate.
- **Serverless cron** (Lambda + EventBridge, Cloud Run + Scheduler) —
  the same shape with an AWS bill, IAM ceremony, and state in a
  separate DB, which severs code from provenance.
- **Orchestrators** (Airflow/Dagster/Prefect) — backfills, sensors,
  retries; magnificent overkill for one run a day, and they are
  infrastructure that must itself be fed.
- **SaaS automation** (Zapier/n8n) — dies at the first multipart OAuth
  upload with rotating refresh tokens.

What yamlgraph adds to the composition: the pipeline is a *judged
artifact*. graph.yaml went through the governed authoring route; the
repo went through plan-judge-enforce; the witnesses are run IDs in an
FR. The automation is not just running — it is *accountable*.

## Consequences, both signs

**What the pattern buys:**
- Zero infra cost and zero pet servers; disaster recovery is `git clone`.
- The one-tree property: code, schedule, state, output, and audit in a
  single URL. An agent (or a successor session) can reconstruct the
  entire truth of the system by reading one repo — this is the
  agent-first thesis made concrete.
- Idempotency comes naturally: read the tree before acting; the ledger
  commit is the lock.
- Public witness: anyone can verify the automation does what it claims.

**What it costs:**
- **Cron is best-effort.** Actions schedules drift by minutes to hours
  under load and are silently dropped sometimes. Fine for daily art;
  disqualifying for anything time-critical. The pattern's cadence floor
  is "roughly daily", not "07:00 sharp".
- **The privacy tax is paid up front.** A public repo made the corpus
  public, which forced the entire C-4 sanitization arc (three
  iterations, blocklists, the adjacent-field leak). Transparency is not
  free; it is a gate you pay before the first commit.
- **Git-as-DB has a scale ceiling** — thousands of small commits, small
  JSONL. At 1 publish/day × 3 commits that is ~1k commits/year: fine
  for a decade, wrong for anything chatty.
- **Single-writer by construction** — the cron is the only writer, which
  is exactly how the pattern dodges the one_session_one_repo trap. Add
  a second writer (manual dispatch racing cron) and the concurrency
  group is the only thing standing between you and index corruption.
- **Self-rotating secrets are a security surface.** A PAT that can
  rewrite the repo's own secrets is the organism's most sensitive
  organ; scope it to one repo, secrets:write, nothing else.
- **Platform coupling.** GitHub down = day skipped. Acceptable for art;
  not for medication reminders. Know which one you are building.

## Use cases — where the mold stamps well

Good fits (daily-ish cadence, public output, API-delegated compute,
small state): content publishers (this repo), digests and newsletters
(FR-819), git-scraping with analysis, changelog/release-notes bots,
fediverse presence bots, nightly LLM-pipeline evals with committed
scorecards, link-rot auditors, dependency digests — and, pointedly,
yamlgraph's own diary sweep: a weekly cron that reads `docs/diary/`,
detects 3+ recurrences, and files graduation proposals to the
chaplain inbox would be this exact mold applied to the doctrine itself
(the `diary_graduation_pipeline` seed already in Scripture).

Poor fits: sub-hourly latency, high-volume state, private data
flowing through public trees, GPU-local compute.

## The insight

**The marginal satellite is approaching free.** FR-819 took days;
FR-826 took one session including a live publish, because corpus +
graph + tools + ledger + workflow + STYLE-CONTRACT + secrets +
witnesses is now a *checklist*, not a design problem. The valuable
artifact this week is not deviant-daily — it is the mold. The mold's
one law: **the pattern holds only while every element fits one tree.**
The moment any single element outgrows it — state size, latency,
privacy — the whole pattern breaks at once, not gracefully. Choose it
by checking all five elements against the tree, and leave it entirely
when one fails; there is no partial exit.

**Heuristic (candidate):** *one-tree test* — before reaching for any
scheduler/DB/orchestrator, ask whether code, schedule, state, output,
and audit all fit a single repo at daily cadence. If yes, the repo IS
the infrastructure. If any one fails, do not bend the pattern —
change platform.

**Seed:** the organism has metabolism (daily commits), memory
(ledger), and an immune system (gate, roster validation) — but no
senses. Closing the loop from publication metrics (DA favourites/
views via the API) back into draw policy would turn a publisher into
an optimizer. Is that desirable, or does feedback-driven draw drift
the gallery toward engagement-bait and away from the operator's
taste? The curated-queue proposal (filed to the chaplain inbox today)
deliberately keeps taste human — the question is whether that line
should ever move.
