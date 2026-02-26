# Chapter 05: The Diary System

*YAMLGraph Development Pipeline eBook — Volume 1*

---

## 1. What is the Diary?

The Development Diary (`docs/diary.md`) is YAMLGraph's **metacognitive log** — a running record of observations, cognitive traps, heuristics, and forward-looking questions generated during development. It is not a changelog, not a commit log, and not a bug tracker. It is the residue of *thinking about thinking*.

> As defined in `docs/diary.md`:
>
> *Metacognitive reflections on development process.*

The diary answers questions that no other artifact captures: *Why did we choose this approach over that one? What trap did we almost fall into? What should we investigate next?* These reflections compound over time into institutional knowledge — the kind that survives team turnover, agent restarts, and the inevitable amnesia of a long-running project.

The diary is the final step of the Sermon's Distill phase:

> From `.github/copilot-instructions.md`:
>
> **Distill.** After completing a task list, add a metacognitive entry to `docs/diary.md`. Name the cognitive trap or insight. Extract a heuristic. Plant a **Seed:** — a forward-looking question to grow new ideas. If the heuristic proves recurring, graduate it to this Scripture.

Every completed task, every feature request cycle, every audit — all end with a diary entry. The diary is where the project *learns*.

---

## 2. Entry Schema

Diary entries follow a consistent structure that has evolved through practice into a canonical format. Each entry is a Markdown section under the diary's header, separated by horizontal rules.

### The Header

Every entry begins with a level-2 heading that combines a date and a descriptive title:

```markdown
## YYYY-MM-DD: Title — Subtitle
```

The date format (`YYYY-MM-DD`) is enforced by the rotation script, which uses a regex to parse entry dates:

> As defined in `scripts/diary_rotate.py`:
>
> ```python
> DATE_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}):")
> ```

The title portion typically names the activity (e.g., "Inquisitor Audit", "Chaplain", "World Digest") and the subtitle provides specifics (e.g., the FR number, a theme name, or a key finding).

### The Body Fields

A development reflection entry follows this structure:

| Field | Purpose |
|-------|---------|
| **Context** | What was being worked on; the FR, commit range, or situation |
| **Trap** or **Observation** | The cognitive mistake narrowly avoided, or the noteworthy finding |
| **Insight** or **Heuristic** | The generalizable lesson extracted from the specific situation |
| **Seed** | A forward-looking question to drive future exploration |

Here is an actual entry from the diary demonstrating this structure:

> As defined in `docs/diary.md` (entry dated 2026-02-18, implementation paragraph omitted):
>
> ```markdown
> ## 2026-02-18: FR-044d — Data Already Exists, Nobody Reads It
>
> **Context:** FR-044a proposed framework changes to track skipped items.
> FR-044d proposed reading existing `state["errors"]` instead.
>
> **What I discovered:** The framework already writes `PipelineError` to
> `state["errors"]` when `on_error: skip` triggers (line 196 in
> `llm_nodes.py`). The data was there all along — just never surfaced
> to users.
>
> **The pattern:** When proposing new features, ask: "Does this data
> already exist somewhere?" Often the infrastructure is in place but
> not connected. A 40-line utility class (`SkipReport`) that reads
> existing state is cheaper than framework changes to generate new state.
>
> [...]
>
> **Heuristic:** Before adding infrastructure, trace the existing data
> flow. The 10x cheaper solution may be consuming data that's already
> produced but discarded.
>
> **Seed:** What other framework-produced data is being discarded or
> ignored that could be surfaced with a simple consumer, without any
> framework changes?
> ```

### Automated Entries

Not all diary entries are written by humans. The Chaplain pipeline (Chapter 03) and the Diary Digest pipeline (Section 5 below) both generate entries programmatically. These entries follow the same schema but use a prefix to identify their source:

- **Chaplain entries:** `## YYYY-MM-DD: Chaplain — Title`
- **World Digest entries:** `## YYYY-MM-DD: World Digest — Theme`
- **Inquisitor entries:** `## YYYY-MM-DD: Inquisitor Audit — Title`
- **Git Report entries:** `## YYYY-MM-DD: Git Report — Title`

The shared formatting utility enforces this canonical structure:

> As defined in `examples/shared/diary.py`:
>
> ```python
> def format_diary_entry(
>     date_str: str,
>     theme: str,
>     body: str,
>     seed: str,
>     prefix: str = "World Digest",
> ) -> str:
>     return f"\n---\n\n## {date_str}: {prefix} — {theme}\n\n{body}\n\n**Seed:** {seed}\n"
> ```

Every entry — human or automated — ends with `**Seed:**`. This is not optional. The Seed is the diary's mechanism for continuity: today's observation plants tomorrow's question.

---

## 3. Why Metacognition?

The diary exists because **knowing what you did is not the same as knowing what you learned**. A git log tells you that `examples/shared/diary.py` was refactored. A diary entry tells you *why* the refactoring nearly introduced a subtle bug because three implementations of "slugify" had different edge-case behaviors — and that the heuristic "verify semantic equivalence, not just syntactic similarity" was extracted from that near-miss.

### Naming Cognitive Traps

The diary's most distinctive contribution is its vocabulary of named traps — recurring patterns of faulty reasoning that the project has learned to recognize:

| Trap Name | Description | First Appearance |
|-----------|-------------|------------------|
| **Downstream Fix** | Treating symptoms late in the pipeline instead of fixing the root cause at the boundary | FR-103 (2026-02-25) |
| **False Equivalence** | Assuming syntactically similar code is semantically identical | FR-044c (2026-02-18) |
| **Premature Abstraction** | Labeling invention as "extraction" to bypass scrutiny | FR-044 (2026-02-18) |
| **Accretion through Iteration** | Each iteration adds complexity to solve perceived problems from the prior iteration | FR-103 (2026-02-26) |
| **Quick Confidence** | Feeling certain about an approach before verifying it | Graduated to Scripture |

These traps are catalogued in the Knowledge Graph section of the Scripture itself:

> As defined in `.github/copilot-instructions.md`:
>
> ```yaml
> traps: [quick_confidence, downstream_fix, symptom_patch, intent_drift]
> ```

When a developer or agent encounters one of these patterns, the named trap provides instant recognition — like a code smell, but for reasoning.

### Extracting Heuristics

Every diary entry distills a specific situation into a general rule. These heuristics are the diary's primary output:

> From `docs/diary.md` (2026-02-25):
>
> *"When the same violation persists across 7 audits, stop re-classifying the symptom and diagnose the guard."*

> From `docs/diary.md` (2026-02-25):
>
> *"A doctrine rule flagged three times without correction is not a compliance failure — it is a specification bug."*

> From `docs/diary.md` (2026-02-18):
>
> *"Before extracting "duplicate" code, verify the implementations are semantically equivalent, not just syntactically similar."*

These heuristics are actionable — they change behavior immediately. An agent reading the diary before a refactoring task will encounter the false-equivalence heuristic and slow down before doing a global search-and-replace.

### Planting Seeds

Seeds are forward-looking questions that end every diary entry. They serve three purposes:

1. **Continuity** — They link today's work to tomorrow's opportunities. A Seed planted during a refactoring session might inspire next week's feature request.
2. **Curation** — The Diary Digest pipeline (Section 5) collects Seeds into `seeds.yaml` and prunes them to a focused list of 10, ensuring the best questions survive.
3. **Ideation** — Seeds are deliberately speculative. They ask "Could we...?" and "What if...?" — questions that would be premature in a feature request but are fertile in a diary.

From the actual `examples/diary_digest/seeds.yaml`:

> As defined in `examples/diary_digest/seeds.yaml`:
>
> ```yaml
> - Should bug reports require a minimal reproduction script as an
>   acceptance criterion before any fix is designed — making armchair
>   debugging structurally impossible?
> - Could 'name the verification question' become a concrete workflow
>   gate — a pre-action prompt in the agent's instructions that requires
>   stating a falsifiable question before proceeding?
> - Could protocol archaeology be formalized as a YAMLGraph graph —
>   given a GitHub repo URL, extract endpoint URLs, auth flows,
>   message formats, and error handling into a structured integration
>   brief?
> ```

---

## 4. Rotation Logic

A diary that grows without bound becomes noise. The rotation script (`scripts/diary_rotate.py`) ensures `docs/diary.md` remains a focused window on recent work by archiving older entries to dated files.

### When Rotation Happens

Rotation is triggered by the **date of the most recent entry** compared to today's date:

> Simplified from `scripts/diary_rotate.py` (the `--check` dry-run branch, `print()` statements, and `import_scheduled_entries()` / `import_git_reports()` calls are omitted for clarity):
>
> ```python
> def main() -> int:
>     if not DIARY.exists():
>         return 0
>
>     latest = latest_entry_date(DIARY)
>     if latest is None:
>         return 0
>
>     today = date.today()
>
>     if latest < today:
>         dest = archive_path(latest)
>         summary = one_line_summary(DIARY)
>         shutil.move(str(DIARY), str(dest))
>         create_fresh_diary(dest.name, summary)
>         git_add(dest, DIARY)
>
>     return 0
> ```

The logic is simple: if the newest entry in the diary is from a past date, the current diary belongs to yesterday and should be archived. Rotation happens *before* any new entries are imported, preventing today's imports from polluting yesterday's archive.

### How Archives Are Named

Archives follow the pattern `diary-YYYY-MM-DD.md`, where the date is the latest entry date in the rotated file:

> As defined in `scripts/diary_rotate.py`:
>
> ```python
> def archive_path(entry_date: date) -> Path:
>     base = Path(f"docs/diary-{entry_date.isoformat()}.md")
>     if not base.exists():
>         return base
>     n = 1
>     while True:
>         candidate = Path(f"docs/diary-{entry_date.isoformat()}-{n}.md")
>         if not candidate.exists():
>             return candidate
>         n += 1
> ```

If `diary-2026-02-25.md` already exists (e.g., from a manual rotation), the script appends a numeric suffix: `diary-2026-02-25-1.md`, `diary-2026-02-25-2.md`, and so on.

The project's `docs/` directory shows this pattern in action:

```
docs/diary.md                  ← Current (today)
docs/diary-2026-02-24.md       ← Yesterday
docs/diary-2026-02-23.md       ← Two days ago
docs/diary-2026-02-22.md       ← ...
docs/diary-2026-02-21.md
docs/diary-2026-02-20.md
docs/diary-2026-02-19.md
docs/diary-2026-02-18.md
docs/diary-2026-02-17.md
```

### The Fresh Diary

After archiving, a new `diary.md` is created with a header and a `Previous:` link that chains the archive history:

> As defined in `scripts/diary_rotate.py`:
>
> ```python
> def create_fresh_diary(prev_filename: str, prev_summary: str) -> None:
>     DIARY.write_text(
>         "# Development Diary\n"
>         "\n"
>         "Metacognitive reflections on development process.\n"
>         "\n"
>         f"Previous: [{prev_filename}]({prev_filename})"
>         f" — {prev_summary}.\n"
>         "\n"
>         "---\n"
>     )
> ```

This produces:

```markdown
# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-24.md](diary-2026-02-24.md) — 11 entries from 2026-02-24.

---
```

The `Previous:` link creates a linked list through the archive, making any entry reachable by following the chain backward.

### Pre-Commit Integration

The rotation script is designed to run as a pre-commit hook:

```bash
python scripts/diary_rotate.py          # rotate if needed
python scripts/diary_rotate.py --check  # dry-run, exit 0 = no rotation needed
```

When rotation occurs, the script calls `git add` on both the archive and the new diary, ensuring the rotation is included in the current commit. This makes rotation invisible to the developer — it happens automatically as part of the commit workflow.

### Importing Scheduled Entries

Before or after rotation, the script imports entries from external sources — specifically from `~/scheduled-yamlgraphs/outputs/`. This handles two categories:

1. **World Digest entries** (`diary_entry_YYYYMMDD.md`) — generated by the scheduled Diary Digest pipeline running overnight.
2. **Git Report entries** (`git_report/report_YYYYMMDD_HHMMSS.txt`) — automated repository analysis reports.

Both import functions parse external formats, convert them to the diary's canonical `## YYYY-MM-DD:` heading format, and append them. Duplicate detection prevents re-importing entries that already exist in the diary.

---

## 5. The Digest Pipeline

The Diary Digest (`examples/diary_digest/graph.yaml`) is a YAMLGraph pipeline that fetches world developments relevant to the project and synthesizes them into a diary entry. It runs on a schedule (typically overnight), connecting the project to the broader AI/ML ecosystem.

### Pipeline Architecture

> As defined in `examples/diary_digest/graph.yaml`:

```
load_config → fetch_sources → analyze_all (map) → filter_relevant
                                                        │
                                          ┌─────────────┴──────────────┐
                                          │                            │
                                   relevant_count > 0          relevant_count == 0
                                          │                            │
                                   synthesize_entry                    │
                                          │                            │
                                     write_diary                       │
                                          │                            │
                                          └──────────┬─────────────────┘
                                                     │
                                              curate_seeds → save_seeds → END
```

The pipeline has seven nodes forming a conditional flow:

1. **`load_config`** — Loads topics of interest and RSS feeds from `feeds.yaml`, curated Seeds from `seeds.yaml`, and raw Seeds extracted from all diary files.

2. **`fetch_sources`** — Pulls articles from Hacker News and configured RSS feeds (LangChain blog, LangGraph releases, Pydantic releases, OpenAI blog, Hugging Face blog, Simon Willison's blog, and topic-filtered HN).

3. **`analyze_all`** — A **map node** that scores each article for relevance using an LLM. Each article title is evaluated against the project's topics of interest and scored 0.0–1.0. Up to 50 articles are processed in parallel with `on_error: skip` ensuring one failure doesn't halt the batch.

4. **`filter_relevant`** — Applies a threshold (default 0.3) to keep only articles scoring above the relevance bar. A utility function determines whether the pipeline should write an entry at all:

> As defined in `examples/shared/diary.py`:
>
> ```python
> def should_write_entry(
>     articles: list[dict],
>     threshold: float = 0.3,
> ) -> bool:
>     if not articles:
>         return False
>     return any(a.get("relevance_score", 0) >= threshold for a in articles)
> ```

5. **`synthesize_entry`** — An LLM node that produces a structured diary entry with `theme`, `body`, and `seed` fields. The prompt connects articles to recent Seeds from the diary, creating continuity:

> As defined in `examples/diary_digest/prompts/synthesize_diary_entry.yaml`:
>
> ```yaml
> schema:
>   name: DiaryDigestEntry
>   fields:
>     theme: { type: str, description: "Short theme name, 2-5 words" }
>     body: { type: str, description: "Diary entry body in markdown" }
>     seed: { type: str, description: "Forward-looking question inspired by today's developments" }
> ```

6. **`write_diary`** — Formats the LLM output using the shared `format_diary_entry()` function and appends it to `docs/diary.md`.

7. **`curate_seeds`** — An LLM node that maintains the `seeds.yaml` file. It adds new Seeds from raw diary entries, retires Seeds that have been answered, condenses related Seeds, and caps the list at 10 items maximum.

### Conditional Flow: The Silent No-Op

When no articles score above the relevance threshold, the pipeline skips `synthesize_entry` and `write_diary` entirely, jumping straight to `curate_seeds`. This is not a failure — it is a deliberate design choice. A day with no relevant developments produces no diary entry. The pipeline is silent when it has nothing to say.

> As defined in `examples/diary_digest/graph.yaml`:
>
> ```yaml
> edges:
>   - from: filter_relevant
>     to: synthesize_entry
>     condition: relevant_count > 0
>   - from: filter_relevant
>     to: curate_seeds
>     condition: relevant_count == 0
> ```

### The Seed Lifecycle

Seeds flow through a complete lifecycle in the Digest pipeline:

1. **Planted** — A diary entry (human or automated) ends with `**Seed:** How might we...?`
2. **Harvested** — The `load_config` node extracts raw Seeds from all diary files.
3. **Curated** — The `curate_seeds` LLM node prunes, merges, and prioritizes the raw Seeds into a focused list of 10.
4. **Persisted** — The curated list is saved to `seeds.yaml`.
5. **Consumed** — The next run's `synthesize_entry` prompt receives the curated Seeds as context, connecting new developments to existing questions.
6. **Answered** — When a Seed inspires action and is resolved, the curation step retires it.

This creates a self-sustaining feedback loop: diary entries plant Seeds, Seeds shape what the Digest looks for, and the Digest writes new entries that plant new Seeds.

---

## 6. Graduating Heuristics

The diary is the nursery. The Scripture is the canon. Between them is a promotion process that turns recurring observations into permanent doctrine.

> From `.github/copilot-instructions.md`:
>
> *"If the heuristic proves recurring, graduate it to this Scripture."*

### The Graduation Path

A heuristic graduates from diary to doctrine through natural selection:

1. **Observed once** — An entry records a specific trap or insight. It lives in the diary as a data point.

2. **Observed again** — A different entry, possibly weeks later, independently discovers the same pattern. The diary now has two data points.

3. **Named** — When a pattern recurs enough to feel familiar, it gets a name. "Downstream Fix," "False Equivalence," "Quick Confidence" — named traps are easier to recognize and communicate than unnamed feelings of unease.

4. **Graduated** — The named trap or heuristic is added to the Scripture's Knowledge Graph:

> As defined in `.github/copilot-instructions.md`:
>
> ```yaml
> the_one_law: |
>   Normalize at the boundary where external data enters,
>   not downstream where it manifests.
>
> boundaries: [schema, provider, state, streaming, platform]
> traps: [quick_confidence, downstream_fix, symptom_patch, intent_drift]
> ```

### Example: The One Law

The clearest example of graduation is `the_one_law` — "Normalize at the boundary where external data enters, not downstream where it manifests."

This started as a specific observation in the diary: during FR-103, the pipeline was hallucinating Commandment content because research summaries lost verbatim quotes. The initial reflex was a downstream fix (elaborate validation nodes). The diary entry named the trap and extracted the heuristic: move raw source access closer to the generation point.

The same pattern appeared across provider normalization, streaming state management, and schema validation. Each occurrence was recorded in the diary. Eventually, the heuristic was distilled into `the_one_law` and promoted to the Scripture, where it now governs all boundary-crossing decisions.

### Example: Audit Entropy

The diary itself produced a graduated insight about its own process. Over the course of 2026-02-25, Inquisitor audits generated over 20 entries for a single day — outnumbering the development reflections they were meant to audit. Multiple diary entries diagnosed the problem with increasing precision:

> From `docs/diary.md` (2026-02-25):
>
> *"When the corrective mechanism produces more entropy than the defects it finds, the mechanism itself needs correction."*

> From `docs/diary.md` (2026-02-25):
>
> *"An audit finding repeated four times without remediation is not drift — it is accepted practice."*

This observation led directly to the rotation script, the proposal for audit batching, and the principle that audit processes must themselves be subject to entropy review — an insight now embedded in how the Inquisitor operates.

### Why Not Graduate Everything?

Not every heuristic belongs in the Scripture. The promotion criteria are:

- **Recurrence** — The pattern appeared independently in multiple contexts.
- **Generality** — The heuristic applies beyond its original domain.
- **Actionability** — Following the heuristic changes behavior in a measurable way.
- **Consensus** — Multiple diary entries converge on the same conclusion.

A heuristic that appears once in a specific context stays in the diary. It's valuable as a historical record but not yet proven enough to become doctrine. The diary is tolerant of noise; the Scripture is not.

---

## Summary

The Diary System is YAMLGraph's mechanism for **learning from its own process**. It operates at three timescales:

| Timescale | Mechanism | Artifact |
|-----------|-----------|----------|
| **Immediate** | A developer or agent completes a task and writes a reflection | A diary entry in `docs/diary.md` |
| **Daily** | The rotation script archives yesterday's entries; the Digest pipeline fetches world developments | Archive files (`diary-YYYY-MM-DD.md`) and World Digest entries |
| **Permanent** | Recurring heuristics graduate from the diary to the Scripture | The Knowledge Graph in `.github/copilot-instructions.md` |

The diary is not a bureaucratic obligation — it is the project's long-term memory. Every named trap prevents a future mistake. Every Seed plants a future feature. Every graduated heuristic strengthens the doctrine. The Sermon says *"let success be codified"* — the diary is where codification begins.

---

*Next: [Chapter 06](06-world-digest.md) — The World Digest Pipeline*


