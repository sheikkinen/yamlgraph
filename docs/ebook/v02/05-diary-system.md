# Chapter 05: The Diary System

*From the YAMLGraph Development Pipeline eBook*

---

## 1. What is the Diary?

The diary is YAMLGraph's metacognitive log — a persistent record of the cognitive process behind every significant development decision. It lives at `docs/diary.md` and captures not just *what* was built, but *why*, *what traps were encountered*, and *what questions remain open*.

Most engineering projects have commit logs and changelogs. YAMLGraph has those too. But the diary occupies a different niche: it is where the developer steps back from the code and reflects on the *thinking process itself*. Did a quick fix turn into a three-day refactor? The diary names the trap. Did a 32-node pipeline collapse into a 3-node pattern? The diary traces the insight path.

The Scripture's Distill step mandates this practice:

> "After completing a task list, add a metacognitive entry to `docs/diary.md`. Name the cognitive trap or insight. Extract a heuristic. Plant a **Seed:** — a forward-looking question to grow new ideas. If the heuristic proves recurring, graduate it to this Scripture."

The diary is not optional documentation. It is where institutional knowledge compounds — where the next person building a similar pipeline starts with context rather than from zero.

---

## 2. Entry Schema

Every diary entry follows a canonical structure. The heading uses a date-prefixed format with a descriptive title, followed by structured sections that trace the arc from context through insight to forward-looking question.

### The Heading

```
## YYYY-MM-DD: Title — Subtitle
```

The date anchors the entry in time. The title names the work or event. The subtitle captures the conceptual theme — often the trap that was discovered or the insight that emerged.

### The Sections

A development reflection entry contains these sections:

| Section | Purpose |
|---------|---------|
| **Context** | What was happening — the FR, the commit range, the task |
| **Trap** | The cognitive trap encountered (named explicitly) |
| **Insight** | What was learned — the deeper pattern |
| **Heuristic** | A generalizable rule extracted from the experience |
| **Seed** | A forward-looking question to grow new ideas |

### Real Example: The Normalize-at-Boundary Trap

From `docs/diary.md`, this entry traces how a hallucination bug in the eBook pipeline led through three feature request iterations before the root cause was identified:

> *Source: `docs/diary.md`, entry "2026-02-25: FR-103 Judge-Amend Subgraph — The Normalize-at-Boundary Trap"*

```markdown
## 2026-02-25: FR-103 Judge-Amend Subgraph — The Normalize-at-Boundary Trap

**Context:** FR-100 pipeline ran successfully but produced 9/10
fabricated Commandments in Ch01 Doctrine. Root cause: research→write
split lost verbatim quotes. The LLM invented content from summaries
instead of citing source files.

**Trap:** *Downstream Fix.* Initial reaction (FR-101) proposed elaborate
32-node pipeline with per-section persistence and 24 checkpoint calls.
This was treating the symptom (hallucination visible late) rather than
the cause (verbatim quotes lost at research boundary).

**Insight:** The Scripture's `the_one_law` applies directly: "Normalize
at the boundary where external data enters, not downstream where it
manifests." The fix was merging research+write into a single copilot
node with inline citations.

**Heuristic:** When hallucination appears late in pipeline, trace backward
to find where verbatim content was converted to summary. The fix is
moving the raw source access closer to the generation point — ideally
into the same prompt.

**Seed:** Could the judge-amend subgraph pattern be generalized as a
reusable validation primitive?
```

Notice the structure: **Context** sets the scene, **Trap** names the cognitive error (with emphasis), **Insight** connects it to existing doctrine, **Heuristic** extracts a reusable rule, and **Seed** plants a question for future exploration.

### Real Example: The Simplification Arc

This entry from `docs/diary.md` traces an entire feature arc across four FRs:

> *Source: `docs/diary.md`, entry "2026-02-26: FR-103 eBook Pipeline — The Simplification Arc"*

```markdown
## 2026-02-26: FR-103 eBook Pipeline — The Simplification Arc

**Context:** FR-100 → FR-101 → FR-102 → FR-103 represents a complete
feature arc for the eBook authoring pipeline.

**Trap:** *Accretion through iteration.* Each FR iteration added
complexity to solve perceived problems:
- FR-100: Initial scaffold with research→write split (hallucination source)
- FR-101: 32-node pipeline with elaborate checkpointing (over-engineered)
- FR-102: Subgraph with input/output mapping (complexity for complexity's sake)
- FR-103: File-based pattern with per-chapter filenames (still 21 nodes)

The breakthrough came when the user asked: "how to run one chapter
separately?" — revealing that the monolithic graph forced full pipeline
runs. The solution wasn't --start-node/--end-node flags; it was
**separate graphs per chapter**.

**Heuristic:** When you find yourself wishing for partial execution flags,
you've designed the wrong unit of work.

**Seed:** Could a `graph-composition` CLI command chain multiple
single-chapter graphs into a batch run?
```

### Entry Variants

Not all entries follow the full trap→insight→heuristic pattern. The diary accommodates several entry types:

**Chaplain entries** — summaries from the automated Chaplain pipeline (Chapter 03):

```markdown
## 2026-02-25: Chaplain — FR-095 Documentation Staleness Monitor Approved

The planning phase proposed FR-095, detailing a lightweight Python script
(scripts/doc_staleness.py) for a pre-commit hook...

**Seed:** How might we identify and automate other classes of documentation
or codebase drift issues using deterministic, non-LLM based checks?
```

**World Digest entries** — automated summaries of relevant external developments (Section 5):

```markdown
## 2026-02-19: World Digest — Theme Title

Body describing relevant developments in the ecosystem.

**Seed:** Forward-looking question inspired by today's developments?
```

**Environment observations** — records of tooling issues and their workarounds:

```markdown
## 2026-02-25: Environment Issue — Disappearing File Edits

**Context:** During FR-093 implementation, multiple replace_string_in_file
operations reported success but changes didn't persist.

**Heuristic:** When tool reports success but behavior doesn't match,
verify file content with `cat` in terminal before debugging logic.

**Seed:** Could we add a verification step to file-editing tools that
re-reads and confirms the change was written?
```

The constant across all variants: every entry ends with a **Seed** — a forward-looking question that keeps the diary alive as a thinking tool rather than a static log.

---

## 3. Why Metacognition?

The diary exists because software engineering failures are rarely *technical*. They are cognitive. The developer knew the right approach but was drawn to a faster-seeming wrong one. The team had the information to prevent the bug but didn't connect the dots. The specification was ambiguous, and nobody noticed until production.

The Sermon of the Chaplain codifies this in the **Distill** step:

> **Distill.** After completing a task list, add a metacognitive entry to `docs/diary.md`. Name the cognitive trap or insight. Extract a heuristic. Plant a **Seed:** — a forward-looking question to grow new ideas. If the heuristic proves recurring, graduate it to this Scripture.

Three specific practices make the diary effective:

### Naming Cognitive Traps

The diary gives names to recurring cognitive errors. This is not merely descriptive — it is *protective*. A named trap is easier to recognize when it appears again:

- **Downstream Fix** — treating symptoms instead of root causes
- **Accretion through iteration** — each fix adding complexity instead of simplifying
- **Quick Confidence** — feeling certain before verifying

From the Knowledge Graph in the Scripture:

```yaml
traps: [quick_confidence, downstream_fix, symptom_patch, intent_drift]
```

When a developer encounters a familiar trap, the name serves as a speed bump. "Wait — this feels like a Downstream Fix. Let me trace backward to the boundary."

### Extracting Heuristics

Every diary entry distills a heuristic — a generalizable rule that can be applied beyond the specific incident. These are not platitudes; they are operational guidance extracted from concrete experience:

> "When hallucination appears late in pipeline, trace backward to find where verbatim content was converted to summary."

> "When the same drift is flagged across 5+ audits without resolution, the finding has graduated from observation to technical debt."

> "When you find yourself wishing for partial execution flags, you've designed the wrong unit of work."

> "When the corrective mechanism produces more entropy than the defects it finds, the mechanism itself needs correction."

Each heuristic is earned through pain. That is what gives it weight.

### Planting Seeds

The Seed is the diary's most distinctive feature. Where a traditional post-mortem ends with "lessons learned," the diary ends with a question — an invitation to future exploration:

> "Could a `graph-composition` CLI command chain multiple single-chapter graphs into a batch run?"

> "Should every enforcement hook in `.pre-commit-config.yaml` have a corresponding integration test?"

> "Could 'name the verification question' become a concrete workflow gate?"

Seeds serve multiple purposes. They prevent closure bias — the tendency to mark a task "done" and move on when open questions remain. They create a thread that connects today's work to tomorrow's. And as we'll see in Section 5, seeds feed directly into the automated World Digest pipeline, guiding what external developments are relevant to track.

The `examples/diary_digest/seeds.yaml` file maintains the curated seed list:

> *Source: `examples/diary_digest/seeds.yaml`*

```yaml
# Auto-curated by diary-digest pipeline. Do not edit manually.
# Last updated: 2026-02-21
- Should bug reports require a minimal reproduction script as an
  acceptance criterion before any fix is designed?
- Could YAMLGraph enforce a 'no-silent-fallback' lint rule?
- As model costs approach zero, what new constraint becomes dominant?
- Could 'name the verification question' become a concrete workflow gate?
```

Seeds are harvested from diary entries, curated by the digest pipeline, and fed back into relevance scoring. The diary thinks forward, not just backward.

---

## 4. Rotation Logic

A diary that grows indefinitely becomes noise. YAMLGraph solves this with `scripts/diary_rotate.py` — a rotation script that archives old entries and keeps `docs/diary.md` focused on the current working period.

> *Source: `scripts/diary_rotate.py`*

### When Rotation Happens

Rotation is triggered by a date boundary. The script examines every `## YYYY-MM-DD:` header in the diary, finds the most recent date, and compares it to today:

```python
DATE_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}):")

def latest_entry_date(path: Path) -> date | None:
    """Extract the most recent ## YYYY-MM-DD: header date."""
    latest: date | None = None
    for line in path.read_text().splitlines():
        m = DATE_RE.match(line)
        if m:
            d = date.fromisoformat(m.group(1))
            if latest is None or d > latest:
                latest = d
    return latest
```

If the latest entry date is *before* today, rotation proceeds. This means the diary accumulates all entries for a given day (or multi-day session) and only archives when a new day begins.

### How Archives Are Named

The archive filename encodes the latest entry date:

```python
def archive_path(entry_date: date) -> Path:
    """Return docs/diary-YYYY-MM-DD.md, appending -N if file exists."""
    base = Path(f"docs/diary-{entry_date.isoformat()}.md")
    if not base.exists():
        return base
    n = 1
    while True:
        candidate = Path(f"docs/diary-{entry_date.isoformat()}-{n}.md")
        if not candidate.exists():
            return candidate
        n += 1
```

A day's work produces `diary-2026-02-25.md`. If that already exists (e.g., from a mid-day rotation), the suffix increments: `diary-2026-02-25-1.md`, `diary-2026-02-25-2.md`, and so on.

The project's `docs/` directory shows the archive chain in practice:

```
docs/diary.md                    ← current (active)
docs/diary-2026-02-24.md         ← yesterday
docs/diary-2026-02-23.md
docs/diary-2026-02-22.md
docs/diary-2026-02-21.md
docs/diary-2026-02-20.md
docs/diary-2026-02-19.md
docs/diary-2026-02-18.md
docs/diary-2026-02-17.md
```

### The Rotation Sequence

When the day has changed, the script performs four steps:

1. **Move** the current diary to its archive path (`docs/diary-YYYY-MM-DD.md`)
2. **Create** a fresh `diary.md` with a header and a "Previous" link
3. **Import** any pending entries from scheduled pipelines (World Digests, Git Reports)
4. **Stage** both files with `git add` so the rotation is included in the current commit

The fresh diary starts with a backlink to its predecessor:

```python
def create_fresh_diary(prev_filename: str, prev_summary: str) -> None:
    DIARY.write_text(
        "# Development Diary\n"
        "\n"
        "Metacognitive reflections on development process.\n"
        "\n"
        f"Previous: [{prev_filename}]({prev_filename})"
        f" — {prev_summary}.\n"
        "\n"
        "---\n"
    )
```

The summary line includes entry count and date range:

```
Previous: diary-2026-02-24.md — 11 entries from 2026-02-24.
```

### Integration as Pre-commit Hook

The rotation script is designed to run as a pre-commit hook, ensuring diary archival happens automatically during the normal commit workflow:

```bash
# Standalone
python scripts/diary_rotate.py          # rotate if needed
python scripts/diary_rotate.py --check  # dry-run, exit 0 = no rotation needed

# Pre-commit hook
- id: diary-rotate
  entry: python scripts/diary_rotate.py
```

The `--check` flag enables dry-run mode for CI validation without side effects.

### Importing Scheduled Entries

The rotation script also handles importing entries from external scheduled pipelines. When the World Digest pipeline (Section 5) runs on a schedule, it writes entries to `~/scheduled-yamlgraphs/outputs/`. During rotation, these are converted and appended:

```python
def import_scheduled_entries() -> int:
    """Import pending diary entries from ~/scheduled-yamlgraphs/outputs/."""
    for entry_file in sorted(SCHEDULED_OUTPUTS.glob("diary_entry_*.md")):
        # Convert: "# World Digest — Theme" → "## YYYY-MM-DD: World Digest — Theme"
        # Append to diary, remove processed file
```

Similarly, Git Report entries from automated analysis are imported and formatted. The import happens *after* rotation — ensuring fresh entries land in the new diary, not the archive.

---

## 5. The Digest Pipeline

The diary doesn't just receive human reflections. YAMLGraph includes an automated **World Digest** pipeline that scans external sources for developments relevant to the project and writes them as diary entries.

> *Source: `examples/diary_digest/graph.yaml`*

### Pipeline Architecture

The digest is a 9-node YAMLGraph pipeline:

```
load_config → fetch_sources → analyze_all (map) → filter_relevant
    → synthesize_entry → write_diary → curate_seeds → save_seeds
```

Each node has a specific role:

| Node | Type | Purpose |
|------|------|---------|
| `load_config` | python | Load topics, feeds, and seeds from YAML config |
| `fetch_sources` | python | Fetch articles from HN + RSS feeds |
| `analyze_all` | map | Score each article's relevance (parallel LLM calls) |
| `filter_relevant` | python | Filter by relevance threshold |
| `synthesize_entry` | llm | Compose a diary entry from relevant articles |
| `write_diary` | python | Format and append to `docs/diary.md` |
| `curate_seeds` | llm | Update seed questions based on findings |
| `save_seeds` | python | Write curated seeds to `seeds.yaml` |

### Relevance Scoring

The pipeline uses a map node to score each article in parallel. The relevance prompt scores on a 0.0–1.0 scale:

> *Source: `examples/diary_digest/prompts/analyze_relevance.yaml`*

```yaml
system: |
  Score how relevant each article title is to the project's focus areas.
  Use the full 0.0-1.0 range:
  - 0.0: Completely unrelated
  - 0.2-0.4: Tangentially related (general AI/ML news)
  - 0.5-0.7: Moderately relevant (LLM frameworks, agent protocols)
  - 0.8-1.0: Directly relevant (LangGraph, Anthropic, MCP, Pydantic)

schema:
  name: RelevanceScore
  fields:
    relevance_score: { type: float, description: "0.0-1.0 relevance" }
    reason: { type: str, description: "One sentence explaining the score" }
```

A configurable threshold (default 0.3) determines which articles make the cut. If nothing passes, the pipeline skips diary writing entirely — a silent no-op is better than a vacuous entry:

```python
def should_write_entry(articles: list[dict], threshold: float = 0.3) -> bool:
    """Return True only if at least one article scores above threshold."""
    if not articles:
        return False
    return any(a.get("relevance_score", 0) >= threshold for a in articles)
```

### Entry Synthesis

Relevant articles are passed to the synthesis prompt, which weaves them into a cohesive diary entry with a thematic title:

> *Source: `examples/diary_digest/prompts/synthesize_diary_entry.yaml`*

```yaml
system: |
  You are writing a "World Digest" entry for a software engineering diary.
  Your entry should:
  1. Identify a unifying theme across the relevant articles
  2. Briefly describe each relevant development (1-2 sentences each)
  3. Connect developments to the project where possible
  4. End with a forward-looking Seed question

schema:
  name: DiaryDigestEntry
  fields:
    theme: { type: str, description: "Short theme name, 2-5 words" }
    body: { type: str, description: "Diary entry body in markdown" }
    seed: { type: str, description: "Forward-looking question" }
```

The structured output (Pydantic schema) ensures every generated entry has the right shape. The `write_diary` tool then formats it using the canonical entry format:

> *Source: `examples/shared/diary.py`*

```python
def format_diary_entry(
    date_str: str, theme: str, body: str, seed: str,
    prefix: str = "World Digest",
) -> str:
    return (
        f"\n---\n\n## {date_str}: {prefix} — {theme}\n\n"
        f"{body}\n\n**Seed:** {seed}\n"
    )
```

### The Seed Cycle

The most elegant aspect of the digest pipeline is how it creates a feedback loop with Seeds. The pipeline:

1. **Reads** existing seeds from `seeds.yaml` (harvested from prior diary entries)
2. **Passes** them to the synthesis prompt as context ("Recent Seeds from the diary")
3. **Generates** a new seed inspired by today's developments
4. **Curates** the full seed list — adding new ones, retiring stale ones
5. **Saves** the updated list back to `seeds.yaml`

This means the diary's open questions actively guide what the pipeline considers relevant. A seed like "Could protocol archaeology be formalized as a YAMLGraph graph?" will bias the relevance scorer toward articles about API reverse-engineering or protocol analysis. The diary feeds forward.

### Feed Configuration

The pipeline draws from a curated list of RSS feeds and Hacker News queries:

> *Source: `examples/diary_digest/feeds.yaml`*

```yaml
topics:
  - LangGraph releases and features
  - Anthropic Claude model announcements
  - MCP protocol specification
  - Python async patterns
  - Pydantic updates
  - AI agent orchestration

feeds:
  - https://blog.langchain.dev/rss/
  - https://github.com/langchain-ai/langgraph/releases.atom
  - https://github.com/pydantic/pydantic/releases.atom
  - https://simonwillison.net/atom/everything/
  - https://hnrss.org/best?q=LLM+OR+langchain+OR+agent+OR+anthropic
```

The feed list is intentionally static — manually updated when the project's focus shifts. This is configuration, not code, honoring Commandment 3: "Keep configuration separate and validated."

---

## 6. Graduating Heuristics

The diary is not a final destination. It is a proving ground. The Scripture declares:

> "If the heuristic proves recurring, graduate it to this Scripture."

This graduation path is what separates the diary from a simple log. A heuristic that appears once is an observation. A heuristic that appears three times across different contexts is a *law* — and laws belong in the doctrine, not buried in dated entries.

### The Knowledge Graph

The Scripture already contains a "Knowledge Graph of the Diary" — a distilled structure of graduated patterns:

```yaml
the_one_law: |
  Normalize at the boundary where external data enters,
  not downstream where it manifests.

boundaries: [schema, provider, state, streaming, platform]
traps: [quick_confidence, downstream_fix, symptom_patch, intent_drift]
```

This Knowledge Graph emerged directly from diary entries. The `the_one_law` was first observed in a streaming bug fix, then confirmed in a provider normalization issue, then elevated to universal principle when it explained an LLM hallucination bug (the FR-103 entry from Section 2). Three independent observations, one graduated law.

### The Graduation Path

```
Diary Entry (observation)
    ↓ appears in 2+ entries
Pattern (recurring heuristic)
    ↓ proves universal across contexts
Knowledge Graph (graduated trap/boundary)
    ↓ becomes operational doctrine
Scripture (commandment or law)
```

Consider the trajectory of "Downstream Fix":

1. **First appearance:** A streaming bug was patched at the consumer instead of the producer. Diary noted: "Fix at the boundary, not downstream."
2. **Second appearance:** A hallucination bug was addressed with an elaborate post-processing pipeline instead of fixing the input prompt. Diary noted: "Normalize at the boundary where external data enters."
3. **Graduation:** The pattern was universal enough to become `the_one_law` in the Knowledge Graph, with `downstream_fix` added to the canonical trap list.

### The Agents' Prayer

Even the Agents' Prayer — recited as operational guidance — draws from graduated diary insights:

> *May I fix at the callsite, not the utility.*
> *May I normalize at the boundary, trusting no provider's type.*
> *When I feel certain, let that be the sign to Judge.*

Each line traces back to a diary entry where the opposite was done and the cost was paid. The prayer is not poetry — it is compressed institutional memory, graduated from the diary into doctrine.

### Diary as Living System

The complete lifecycle looks like this:

```
Developer works → encounters trap → writes diary entry
    ↓
Diary accumulates entries → rotation archives old ones
    ↓
World Digest adds external context → seeds guide relevance
    ↓
Recurring heuristics get noticed → graduated to Scripture
    ↓
Scripture guides development → developer encounters new trap
    ↓
(cycle repeats)
```

The diary is not a burden. It is the mechanism by which a project gets smarter over time — not through better tools or more tests, but through naming what went wrong and encoding the fix into the system that prevents recurrence.

As one diary entry put it:

> "A feature that passes every structural gate but skips the Distill step is 90% compliant and 0% reflective. The Distill is where institutional knowledge compounds."

The diary is where that compounding happens.

---

*Next: [Chapter 06: The Inquisitor Audit](06-inquisitor-audit.md)*

---
## JUDGMENT

### VERDICT: FAILED

### Files Verified
- `.github/copilot-instructions.md` — verified (Distill quote ✅, Knowledge Graph ✅, Agents' Prayer partial quotes ✅)
- `docs/diary.md` — issues found (3 diary entries truncated without indication)
- `scripts/diary_rotate.py` — verified (DATE_RE, latest_entry_date, archive_path ✅; create_fresh_diary missing docstring; format_diary_entry reformatted)
- `examples/diary_digest/seeds.yaml` — issues found (all 4 seeds truncated)
- `examples/diary_digest/feeds.yaml` — issues found (topics and feeds omitted, URL altered)
- `examples/diary_digest/prompts/analyze_relevance.yaml` — issues found (system prompt truncated, schema field missing)
- `examples/diary_digest/prompts/synthesize_diary_entry.yaml` — issues found (system prompt truncated, field description shortened)
- `examples/shared/diary.py` — minor issues (code reformatted, docstrings omitted)
- `examples/diary_digest/graph.yaml` — issues found (node count wrong)

### Issues Found

**1. Factual error — node count (line 358)**
- Chapter says "9-node YAMLGraph pipeline" but `graph.yaml` defines exactly 8 nodes: load_config, fetch_sources, analyze_all, filter_relevant, synthesize_entry, write_diary, curate_seeds, save_seeds.

**2. `seeds.yaml` (lines 213–220) — all 4 seeds truncated**
- Seed 1: chapter ends "…before any fix is designed?" — source continues "— making armchair debugging structurally impossible?"
- Seed 2: chapter ends "…'no-silent-fallback' lint rule?" — source continues "— flagging any `if not results: results = all_items` pattern in Python nodes as a potential vuosikello-class bug?'"
- Seed 3: chapter ends "…what new constraint becomes dominant?" — source continues "— latency, evaluation quality, user trust, or something not yet named — and how should YAMLGraph's architecture prepare for that next shift?"
- Seed 4: chapter ends "…concrete workflow gate?" — source continues "— a pre-action prompt in the agent's instructions that requires stating a falsifiable question before proceeding?"

**3. `feeds.yaml` (lines 467–481) — topics and feeds silently omitted**
- Missing topics: "LangChain ecosystem updates", "A2A protocol specification", "LLM evaluation frameworks", "YAML-driven AI pipelines"
- Missing feeds: `langchain/releases.atom`, `openai.com/blog/rss.xml`, `huggingface.co/blog/feed.xml`, `blog.google/technology/ai/rss/`
- HN URL: chapter has `+OR+anthropic` but source has `+OR+anthropic+OR+pydantic`

**4. `analyze_relevance.yaml` (lines 384–398) — system prompt altered**
- Missing intro: "You are a relevance scorer for a software engineering project called YAMLGraph…"
- Range descriptions shortened: e.g., source 0.0 is "(sports, politics, unrelated tech)" but chapter says "(Completely unrelated)"; source 0.8-1.0 includes "A2A" and says "Pydantic updates" but chapter says "Pydantic"
- Missing outro: "Be generous with tangential relevance…"
- Schema missing `title` field present in source
- `relevance_score` description: chapter "0.0-1.0 relevance" vs source "0.0-1.0 relevance to topics"

**5. `synthesize_diary_entry.yaml` (lines 416–431) — system prompt altered**
- Missing intro: "The diary tracks metacognition about building YAMLGraph…"
- Point 4: chapter "End with a forward-looking Seed question" vs source adds "inspired by today's developments"
- Missing outro: "Be concise. This is a working diary, not a newsletter…"
- `seed` field description: chapter "Forward-looking question" vs source "Forward-looking question inspired by today's developments"

**6. Diary entry "Normalize-at-Boundary" (lines 52–76) — truncated without indication**
- **Insight** truncated: chapter ends "…single copilot node with inline citations." but source continues "— the prompt itself reads the source files, not a separate research node producing summaries."
- **Process** section entirely omitted (no ellipsis or note)
- **Seed** truncated: chapter ends "…reusable validation primitive?" but source continues "A `validate_with_sources` subgraph that takes content + cited files and returns corrected content?"

**7. Diary entry "Simplification Arc" (lines 88–109) — truncated without indication**
- **Context** truncated: missing "The final implementation: 7 per-chapter graphs…"
- FR-103 bullet: chapter "(still 21 nodes)" vs source "(still 21 nodes in main graph)"
- **Heuristic** truncated: missing 2 sentences ("A good pipeline is composed of small…" and "The copilot node pattern…")
- **Seed** truncated: missing "E.g., `yamlgraph graph compose…`"
- **Technical insight**, **User reflection**, **Root cause** sections entirely omitted

**8. Diary entry "Disappearing File Edits" (lines 139–149) — details altered**
- **Heuristic**: chapter says "verify file content with `cat` in terminal" but source says "verify file content with `cat` or `head` in terminal (bypasses any VS Code caching)"
- **Seed**: chapter ends "…confirms the change was written?" but source continues "rather than just reporting success based on the write call?"

**9. Code formatting (minor) — `format_diary_entry`, `should_write_entry`, `create_fresh_diary`**
- Parameters condensed to fewer lines vs source formatting
- Docstrings omitted from all three functions
- `format_diary_entry` return wrapped in parentheses vs single-line in source

### What to Fix

1. **Line 358**: Change "9-node" to "8-node".
2. **seeds.yaml block (lines 213–220)**: Either restore full seed text from source, or add a note like "(seeds shown abbreviated; full text includes elaborative sub-clauses)".
3. **feeds.yaml block (lines 467–481)**: Either show full source content, or explicitly note "Selected entries shown; full list includes 10 topics and 9 feeds." Fix HN URL to include `+OR+pydantic`.
4. **analyze_relevance.yaml block (lines 384–398)**: Restore missing intro/outro paragraphs, fix range descriptions to match source, add missing `title` field to schema, fix `relevance_score` description.
5. **synthesize_diary_entry.yaml block (lines 416–431)**: Restore missing intro/outro, fix point 4 and `seed` field description to match source.
6. **Diary entries (lines 52–76, 88–109, 139–149)**: Either restore omitted text, or mark truncations with `[...]` and add a note like "*Entry abbreviated for clarity; see source for full text.*"
7. **Code snippets**: Restore original formatting and docstrings, or note "(docstrings omitted for brevity)" where applicable.
