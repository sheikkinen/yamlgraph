# Diary — 2026-08-18 — The Repo Is the Server (FR-819)

## What happened

Same-day arc: idea ("can we get rid of the fly.io part?") → FR-819 →
judge (canonical route) → enforce → public artifact. The GitHub-native
daily digest now publishes itself: <https://github.com/sheikkinen/yamlgraph-daily-digest>.
Two dispatch runs on GitHub-hosted runners proved the full claim —
first run committed the bulletin from inside the runner, second run
no-opped via the *committed* SQLite dedup state. The repo is
simultaneously runtime (Actions), state store (committed `digest.db`),
and publication channel (committed markdown). Three servers' worth of
architecture (Fly.io machine, FastAPI layer, Docker image) reduced to
one workflow file.

## Traps encountered

1. **The judge caught a dependency lie I shipped in my own FR.**
   `pip install yamlgraph[digest]` while claiming "no FastAPI, no
   Resend" — the extra installs exactly that stack. I wrote the claim
   and the contradiction in the same document and did not see it.
   Instance of `gate_checks_shape_not_substance` applied to myself: the
   FR *looked* dependency-honest because the extra's name matched the
   domain. The cure was the judge reading `pyproject.toml`, not my
   re-reading the FR. Independent input closure works.

2. **`plausible_wrong_answer` at the empty boundary.** With zero new
   articles after dedup, the rank LLM still runs on an empty list and
   may fabricate stories. The first smoke run crashed on a subtler
   version: serialized `ranked_stories` arrived as a plain dict and
   iterating it yielded its *keys* — strings wearing a story costume.
   Both fixed at the boundary (`normalize at entry`; runner distrusts
   the ranker when `filtered_articles` is empty). The example's HTML
   path had silently tolerated the same shape via Jinja's forgiveness —
   markdown's stricter `.get()` exposed it. Stricter consumers are
   free x-rays.

3. **The crash that proved an AC.** The failed first local run consumed
   all URLs into `digest.db` before crashing, so the retry became an
   accidental proof of the no-op path (AC-09) before the happy path had
   ever succeeded. Dedup-by-side-effect means a crashed run *spends*
   the day's articles — worth knowing for ops: recovery from a mid-run
   crash requires resetting state, not just re-running.

## Insight

The Fly.io layer existed for exactly one reason: the cron and the
compute were on different machines. Once they share a machine, the
entire HTTP/202/BackgroundTasks apparatus is revealed as accidental
complexity — not wrong, just a boundary tax paid to a split that no
longer exists. The general form: **when two halves of a system
converge onto one substrate, re-derive the architecture from zero
rather than porting the seam.** We didn't port FastAPI to Actions; we
deleted it.

This is also the first Proclaim artifact from the missing-last-leg arc:
an outward-facing, self-updating, starrable surface whose git log is
its own delivery receipt.

## Seed

The bulletin repo now emits daily commits that nobody measures. The
Harvest half of the arc is still unbuilt: stars, watchers, and traffic
on `yamlgraph-daily-digest` are exactly the external signals the
2026-08-18 research doc said expire unharvested (traffic: 14 days).
Should the digest workflow itself append a weekly `harvest.jsonl` line
— the publication channel measuring its own consumption from inside
the same cron?
