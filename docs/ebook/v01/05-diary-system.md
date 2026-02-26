# Chapter 05: The Diary System

> *"After completing a task list, add a metacognitive entry to `docs/diary.md`. Name the cognitive trap or insight. Extract a heuristic. Plant a **Seed:** — a forward-looking question to grow new ideas. If the heuristic proves recurring, graduate it to this Scripture."*
> — The Sermon of the Chaplain, Distill step

---

## 5.1 What Is the Diary?

The diary (`docs/diary.md`) is YAMLGraph's metacognitive log — a structured record of the cognitive process behind development decisions, not merely *what* was done but *how it was thought about*. Every feature, bug fix, and refactoring session ends with a reflection that names traps encountered, extracts reusable heuristics, and plants questions for future exploration.

This is not a changelog. The CHANGELOG records what shipped. The diary records what the team *learned while shipping*. Where CHANGELOG.md says "feat(ebook): FR-103 judge-amend subgraph pattern", the diary says:

> **Trap:** *Downstream Fix.* Initial reaction (FR-101) proposed elaborate 32-node pipeline with per-section persistence and 24 checkpoint calls. This was treating the symptom (hallucination visible late) rather than the cause (verbatim quotes lost at research boundary).

The diary captures the reasoning gap between problem and solution — the part that would otherwise be lost when the PR merges and everyone moves on.

### The Three Voices

The diary has evolved to host three distinct voices, each producing entries with the same structural schema but different perspectives:

| Voice | Prefix | Purpose |
|-------|--------|---------|
| **Developer** | Date + title | First-person metacognitive reflections on implementation work |
| **Chaplain** | `Chaplain —` | Feature request judgments, approvals, and process observations |
| **Inquisitor** | `Inquisitor Audit —` | Compliance audits against the Scripture's Commandments |
| **World Digest** | `World Digest —` | Automated external intelligence from RSS feeds and Hacker News |

*(Source: `docs/diary.md` — entry headers)*

---

## 5.2 Entry Schema

Every diary entry follows a canonical format defined by `format_diary_entry()` in `examples/shared/diary.py`:

```python
def format_diary_entry(
    date_str: str,
    theme: str,
    body: str,
    seed: str,
    prefix: str = "World Digest",
) -> str:
    return f"\n---\n\n## {date_str}: {prefix} — {theme}\n\n{body}\n\n**Seed:** {seed}\n"
```

*(Source: `examples/shared/diary.py`)*

This produces the following Markdown structure:

```markdown
---

## 2026-02-25: World Digest — Theme Name

Body text with observations, analysis, and insights.

**Seed:** A forward-looking question for future exploration?
```

### The Full Schema

A complete diary entry contains these elements:

#### 1. Date and Context Header

```markdown
## YYYY-MM-DD: [Prefix —] Title
```

The date uses ISO 8601 format. The prefix identifies the voice (Chaplain, Inquisitor Audit, World Digest) or is omitted for developer reflections. The title captures the specific topic.

#### 2. Context Block

The opening paragraph establishes *what prompted this reflection* — the commit range, feature request, or incident. This makes entries self-contained and traceable:

```markdown
**Context:** Audit of HEAD (`a9bffc8`), covering 5 commits...
```

Or for development reflections:

```markdown
**Context:** FR-100 pipeline ran successfully but produced 9/10
fabricated Commandments in Ch01 Doctrine. Root cause: research→write
split lost verbatim quotes.
```

#### 3. Observation and Cognitive Insight

The body names the cognitive pattern — the trap that was encountered or the insight that emerged. This is what separates the diary from a plain log:

```markdown
**Trap:** *Downstream Fix.* Initial reaction (FR-101) proposed elaborate
32-node pipeline with per-section persistence and 24 checkpoint calls.
This was treating the symptom (hallucination visible late) rather than
the cause (verbatim quotes lost at research boundary).

**Insight:** The Scripture's `the_one_law` applies directly: "Normalize
at the boundary where external data enters, not downstream where it
manifests."
```

*(Source: `docs/diary.md` — entry "FR-103 Judge-Amend Subgraph")*

The named traps form a growing vocabulary referenced across the codebase:

| Trap Name | Description |
|-----------|-------------|
| **Downstream Fix** | Patching symptoms far from the root cause |
| **Quick Confidence** | Feeling certain too early, skipping verification |
| **Symptom Patch** | Fixing what's visible, not what's causal |
| **Intent Drift** | Gradually deviating from the original objective |

These are codified in the Scripture's Knowledge Graph:

```yaml
traps: [quick_confidence, downstream_fix, symptom_patch, intent_drift]
```

#### 4. Heuristic

A distilled, reusable rule extracted from the experience:

```markdown
**Heuristic:** When hallucination appears late in pipeline, trace
backward to find where verbatim content was converted to summary.
The fix is moving the raw source access closer to the generation
point — ideally into the same prompt.
```

#### 5. Seed Question

Every entry ends with a forward-looking question — a thread to pull in future work:

```markdown
**Seed:** Could the judge-amend subgraph pattern be generalized as a
reusable validation primitive? A `validate_with_sources` subgraph that
takes content + cited files and returns corrected content?
```

*(Source: `docs/diary.md` — entry "FR-103 Judge-Amend Subgraph")*

### Structured Output for LLM-Generated Entries

When entries are produced by YAMLGraph pipelines (World Digest, Chaplain), the output schema is enforced via Pydantic:

```yaml
# From examples/diary_digest/prompts/synthesize_diary_entry.yaml
schema:
  name: DiaryDigestEntry
  fields:
    theme: { type: str, description: "Short theme name, 2-5 words" }
    body: { type: str, description: "Diary entry body in markdown" }
    seed: { type: str, description: "Forward-looking question" }
```

*(Source: `examples/diary_digest/prompts/synthesize_diary_entry.yaml`)*

The `write_diary` tool in `examples/shared/diary.py` handles both Pydantic models and raw dicts, parsing string representations as a fallback — a boundary normalization that ensures entries always reach the diary regardless of upstream format variations.

---

## 5.3 Why Metacognition?

The Sermon of the Chaplain defines the **Distill** step as the final act in any work sequence:

> *After completing a task list, add a metacognitive entry to `docs/diary.md`. Name the cognitive trap or insight. Extract a heuristic. Plant a **Seed:** — a forward-looking question to grow new ideas.*

This isn't philosophical indulgence. It serves three concrete engineering purposes.

### Naming Cognitive Traps

Unnamed patterns repeat. When a developer encounters the *Downstream Fix* trap — the urge to patch symptoms far from the root cause — and doesn't name it, they'll fall into it again. The diary creates a shared vocabulary:

```markdown
**Trap:** *Downstream Fix.* Initial reaction (FR-101) proposed elaborate
32-node pipeline with per-section persistence and 24 checkpoint calls.
```

Once named, the trap becomes recognizable. Future developers (or the same developer next week) can reference it: "This feels like a Downstream Fix — are we treating the symptom or the cause?" The Agents' Prayer codifies this vigilance:

> *May I fix at the callsite, not the utility.*
> *May I normalize at the boundary, trusting no provider's type.*

### Extracting Heuristics

A heuristic is a trap inverted into a rule. From the diary:

```markdown
**Heuristic:** When the corrective mechanism produces more entropy than
the defects it finds, the mechanism itself needs correction.
```

*(Source: `docs/diary.md` — "Minimal Delta, Compliance Holding, Audit Entropy Peak")*

This heuristic emerged from observing the Inquisitor (automated audit agent) generating 9 audit entries in a single day — more diary entropy than the code changes it was reviewing. The observation became a rule: measure the cost of your quality mechanisms, not just their findings.

### Planting Seeds

Seeds are the diary's investment in future work. Each question opens a thread that may be picked up hours, days, or weeks later:

```markdown
**Seed:** Should `docs/diary.md` be split into `docs/diary.md`
(development reflections only) and `docs/audit-log.md` (Inquisitor
findings), with the Inquisitor writing exclusively to the latter —
preserving the diary's original metacognitive purpose?
```

Seeds are not idle speculation. The digest pipeline actively curates them, maintaining a capped list of the 10 most relevant open questions (see §5.5). When a Seed leads to a feature request, the cycle completes: reflection → question → implementation → reflection.

---

## 5.4 Rotation Logic

As the diary accumulates entries, it grows unwieldy. The rotation script (`scripts/diary_rotate.py`) manages this by archiving old entries and starting fresh files.

### When Rotation Happens

Rotation triggers when the **most recent entry date** in `docs/diary.md` is *before today*:

```python
DIARY = Path("docs/diary.md")
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

*(Source: `scripts/diary_rotate.py`, lines 38–47)*

The check is simple: if the latest entry is from yesterday or earlier, today is a new day and the diary should rotate. This means rotation happens at most once per day, on the first commit of the day.

### How Archives Are Named

The archived file takes the date of the latest entry:

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

*(Source: `scripts/diary_rotate.py`, lines 69–79)*

This produces a chain of dated archives:

```
docs/diary.md                  ← Current (today's entries)
docs/diary-2026-02-24.md       ← Yesterday
docs/diary-2026-02-23.md       ← Day before
docs/diary-2026-02-22.md       ← ...
```

If rotation runs twice on the same date (e.g., manual invocation), the suffix `-N` prevents overwriting: `diary-2026-02-24-1.md`.

### The Rotation Sequence

The full rotation performs five steps:

1. **Check**: Parse the latest `## YYYY-MM-DD:` header from `docs/diary.md`
2. **Archive**: Move `diary.md` → `diary-YYYY-MM-DD.md`
3. **Create Fresh**: Write a new `diary.md` with a header and `Previous:` link
4. **Import**: Pull pending entries from external sources (scheduled pipelines)
5. **Stage**: `git add` both the archive and the fresh diary

```python
if latest < today:
    dest = archive_path(latest)
    summary = one_line_summary(DIARY)

    shutil.move(str(DIARY), str(dest))
    create_fresh_diary(dest.name, summary)
    git_add(dest, DIARY)

# Import scheduled entries AFTER rotation check
imported = import_scheduled_entries()
imported += import_git_reports()
```

*(Source: `scripts/diary_rotate.py`, lines 277–294)*

### The Previous Link

Each fresh diary begins with a link to its predecessor, creating a navigable chain:

```markdown
# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-24.md](diary-2026-02-24.md) — 11 entries from 2026-02-24.

---
```

*(Source: `docs/diary.md` — file header)*

The summary includes entry count and date range, computed by `one_line_summary()`:

```python
def one_line_summary(path: Path) -> str:
    n = entry_count(path)
    dates = set()
    for line in path.read_text().splitlines():
        m = DATE_RE.match(line)
        if m:
            dates.add(m.group(1))
    date_range = sorted(dates)
    if len(date_range) == 1:
        return f"{n} entries from {date_range[0]}"
    return f"{n} entries, {date_range[0]} to {date_range[-1]}"
```

*(Source: `scripts/diary_rotate.py`, lines 55–66)*

### Integration Points

The rotation script supports two execution modes:

| Mode | Command | Purpose |
|------|---------|---------|
| **Rotate** | `python scripts/diary_rotate.py` | Perform rotation if needed |
| **Dry run** | `python scripts/diary_rotate.py --check` | Exit 0 = no rotation needed, exit 1 = rotation needed |

It's designed to run as a **pre-commit hook**, ensuring the diary is always rotated before the first commit of a new day:

```yaml
# .pre-commit-config.yaml
- id: diary-rotate
  entry: python scripts/diary_rotate.py
```

### Importing External Entries

Rotation also imports entries from external pipelines — scheduled YAMLGraph runs that produce diary entries outside the development session:

```python
SCHEDULED_OUTPUTS = Path(os.path.expanduser("~/scheduled-yamlgraphs/outputs"))
```

Two import sources are supported:

1. **Diary entries** (`diary_entry_YYYYMMDD.md`): World Digest entries from the digest pipeline, converted from `# World Digest — Theme` format to the canonical `## YYYY-MM-DD: World Digest — Theme` header
2. **Git reports** (`git_report/report_YYYYMMDD_HHMMSS.txt`): Automated repository activity summaries parsed from CLI output format

*(Source: `scripts/diary_rotate.py`, lines 104–250)*

Import happens *after* rotation — today's fresh diary receives today's external entries, while yesterday's entries were already archived.

---

## 5.5 The Digest Pipeline

The diary doesn't only grow through manual reflection. The `diary_digest` pipeline (`examples/diary_digest/graph.yaml`) automatically scans external sources for developments relevant to YAMLGraph and writes World Digest entries.

### Pipeline Architecture

```
┌─────────────┐    ┌────────────────┐    ┌──────────────┐
│ load_config  │───▶│ fetch_sources   │───▶│ analyze_all  │
│ (feeds.yaml) │    │ (HN + RSS)     │    │ (map node)   │
└─────────────┘    └────────────────┘    └──────┬───────┘
                                                │
                   ┌────────────────┐    ┌──────▼───────┐
                   │ synthesize     │◀───│ filter       │
                   │ _entry (LLM)  │    │ _relevant    │
                   └───────┬───────┘    └──────────────┘
                           │
              ┌────────────▼─────────────┐
              │ write_diary              │
              │ (append to docs/diary.md)│
              └────────────┬─────────────┘
                           │
              ┌────────────▼─────────────┐    ┌──────────────┐
              │ curate_seeds             │───▶│ save_seeds   │
              │ (update seeds.yaml)      │    │              │
              └──────────────────────────┘    └──────────────┘
```

*(Source: `examples/diary_digest/graph.yaml`)*

### Stage 1: Source Collection

The pipeline begins by loading configuration — topic lists, RSS feeds, and existing Seeds from `seeds.yaml`. It also scans diary archive files for raw Seeds (every `**Seed:**` line across all `diary-*.md` files):

```yaml
nodes:
  load_config:
    type: python
    tool: load_config
    state_key: topics

  fetch_sources:
    type: python
    tool: fetch_sources
    state_key: raw_articles
```

### Stage 2: Relevance Scoring

Each article is scored against YAMLGraph's topic areas using a **map node** — parallel LLM calls that process up to 50 articles:

```yaml
analyze_all:
  type: map
  over: "{state.raw_articles}"
  as: article
  max_items: 50
  flatten_output: true
  node:
    type: llm
    prompt: analyze_relevance
    variables:
      title: "{state.article.title}"
      source: "{state.article.source}"
      topics: "{state.topics}"
  collect: scored_articles
  on_error: skip
```

The scoring prompt uses a calibrated 0.0–1.0 scale:

```yaml
# From analyze_relevance.yaml
# 0.0: Completely unrelated (sports, politics)
# 0.2-0.4: Tangentially related (general AI/ML news)
# 0.5-0.7: Moderately relevant (LLM frameworks, agent protocols)
# 0.8-1.0: Directly relevant (LangGraph, Anthropic, MCP, Pydantic)
```

*(Source: `examples/diary_digest/prompts/analyze_relevance.yaml`)*

### Stage 3: Synthesis

Articles scoring above the relevance threshold are synthesized into a single diary entry. The synthesis prompt receives the filtered articles plus recent Seeds, connecting new developments to ongoing questions:

```yaml
system: |
  You are writing a "World Digest" entry for a software engineering diary.
  Your entry should:
  1. Identify a unifying theme across the relevant articles
  2. Briefly describe each relevant development
  3. Connect developments to the project where possible
  4. End with a forward-looking Seed question
```

*(Source: `examples/diary_digest/prompts/synthesize_diary_entry.yaml`)*

The output is a structured `DiaryDigestEntry` (theme, body, seed) that `write_diary` formats and appends to `docs/diary.md`.

### Stage 4: Seed Curation

After writing the entry, the pipeline curates its Seed collection — the running list of open questions:

```yaml
curate_seeds:
  type: llm
  prompt: curate_seeds
  variables:
    seeds: "{state.seeds}"
    raw_seeds: "{state.raw_seeds}"
    date: "{state.date}"
  state_key: seeds
```

The curation prompt manages a living list: add new Seeds from today's entry, retire answered ones, condense related questions, and cap at 10 maximum. This prevents Seed accumulation while keeping the most relevant questions alive.

*(Source: `examples/diary_digest/prompts/curate_seeds.yaml`)*

### Conditional Execution

When no articles meet the relevance threshold, the pipeline skips synthesis and diary writing entirely — a silent no-op rather than a forced entry:

```yaml
edges:
  - from: filter_relevant
    to: synthesize_entry
    condition: relevant_count > 0
  - from: filter_relevant
    to: curate_seeds
    condition: relevant_count == 0
```

*(Source: `examples/diary_digest/graph.yaml`)*

This is enforced both at the graph level (conditional edges) and in the tool layer:

```python
def should_write_entry(articles: list[dict], threshold: float = 0.3) -> bool:
    """Return True only if at least one article scores above threshold.
    When no articles are relevant, the digest should be a silent no-op."""
    if not articles:
        return False
    return any(a.get("relevance_score", 0) >= threshold for a in articles)
```

*(Source: `examples/shared/diary.py`)*

### Running the Digest

```bash
yamlgraph graph run examples/diary_digest/graph.yaml
```

The pipeline is designed to run on a schedule (daily cron), with the rotation script handling import of its output files into the diary on the next commit.

---

## 5.6 Graduating Heuristics

The diary is not an archive — it's a refinery. The Scripture explicitly mandates that recurring patterns graduate from diary entries into permanent doctrine:

> *"If the heuristic proves recurring, graduate it to this Scripture."*

### The Graduation Path

```
Observation (diary entry)
    ↓ recurs 2-3 times
Heuristic (named pattern)
    ↓ proves universally applicable
Doctrine (Scripture / Knowledge Graph)
    ↓ enforced mechanically
Pre-commit hook or CI check
```

### Example: The One Law

The most prominent graduated heuristic is `the_one_law`, which now sits in the Scripture's Knowledge Graph:

```yaml
the_one_law: |
  Normalize at the boundary where external data enters,
  not downstream where it manifests.
```

This didn't start as doctrine. It emerged from repeated diary observations:

1. **First sighting**: A provider returned unexpected types; the fix was applied in the rendering layer (downstream)
2. **Second sighting**: Streaming events had inconsistent formats; patched in the consumer (downstream again)
3. **Pattern named**: "We keep fixing things far from where they break"
4. **Heuristic extracted**: "Normalize at the boundary"
5. **Graduated**: Added to the Knowledge Graph as `the_one_law`, referenced by the Agents' Prayer

The FR-103 diary entry demonstrates the law in action — hallucination appeared in the output (downstream) but the fix was moving raw source access into the generation prompt (boundary):

```markdown
**Insight:** The Scripture's `the_one_law` applies directly: "Normalize
at the boundary where external data enters, not downstream where it
manifests." The fix was merging research+write into a single copilot
node with inline citations.
```

*(Source: `docs/diary.md` — "FR-103 Judge-Amend Subgraph")*

### The Knowledge Graph

Graduated heuristics live in the Scripture's Knowledge Graph — a compact YAML structure that encodes the causal relationships between boundaries, traps, and cures:

```yaml
the_one_law: |
  Normalize at the boundary where external data enters,
  not downstream where it manifests.

boundaries: [schema, provider, state, streaming, platform]
traps: [quick_confidence, downstream_fix, symptom_patch, intent_drift]
```

This is the diary's ultimate output: not a log of past events, but a distilled set of operating principles that shape future decisions.

### Self-Correction in Practice

The diary even diagnoses its own pathologies. When the Inquisitor produced more entropy than value — 9 audit entries in a single day — the diary captured this as a heuristic:

```markdown
**Heuristic:** When the corrective mechanism produces more entropy than
the defects it finds, the mechanism itself needs correction. An
Inquisitor with no memory of prior audits and no minimum-delta gate
will always re-discover and re-record. The fix is structural.
```

*(Source: `docs/diary.md` — "Minimal Delta, Compliance Holding, Audit Entropy Peak")*

This is the diary system working at its most recursive: the metacognitive log diagnosing a problem with the metacognitive log, producing a heuristic about metacognitive overhead. The observation has already seeded proposals for structural fixes — separate audit logs, minimum-delta gates, and session-scoped entry batching.

---

## 5.7 The Lifecycle

Putting it all together, the diary system forms a continuous loop:

```
    ┌──────────────────────────────────────────────┐
    │                                              │
    ▼                                              │
  Work ──▶ Reflect ──▶ Write Entry ──▶ Rotate     │
                           │                       │
                           ▼                       │
                     Extract Heuristic             │
                           │                       │
                      ┌────┴────┐                  │
                      ▼         ▼                  │
                   Plant     Graduate              │
                   Seed      to Doctrine ──────────┘
                      │
                      ▼
                 Future Work
```

The diary is where YAMLGraph thinks about itself. It's where traps get names, heuristics get extracted, and the doctrine evolves. It's the connective tissue between daily development and long-term engineering culture — ensuring that what the team learns isn't just remembered, but codified, curated, and enforced.

---

*Next: [Chapter 06](06-testing-strategy.md) — Testing Strategy and TDD in YAMLGraph*

---
## JUDGMENT

### VERDICT: FAILED

### Files Verified
- `.github/copilot-instructions.md` — verified (Agents' Prayer, Sermon Distill, Knowledge Graph all correct)
- `docs/diary.md` — verified (entry headers, FR-103 entry, Minimal Delta entry all present)
- `examples/shared/diary.py` — verified (`format_diary_entry`, `should_write_entry`, `write_diary` all present)
- `scripts/diary_rotate.py` — verified (`latest_entry_date`, `archive_path`, `one_line_summary`, rotation sequence all present)
- `examples/diary_digest/graph.yaml` — verified (nodes, edges, map node all present)
- `examples/diary_digest/prompts/synthesize_diary_entry.yaml` — issues found
- `examples/diary_digest/prompts/analyze_relevance.yaml` — issues found
- `examples/diary_digest/prompts/curate_seeds.yaml` — verified (referenced but not quoted)
- `.pre-commit-config.yaml` — issues found

### Issues Found

**1. Pre-commit hook entry path is wrong (line 349)**
- Chapter: `entry: python scripts/diary_rotate.py`
- Actual: `entry: .venv/bin/python scripts/diary_rotate.py`

**2. Relevance scoring scale truncated (lines 442–447)**
- Chapter: `0.0: Completely unrelated (sports, politics)`
- Actual: `0.0: Completely unrelated (sports, politics, unrelated tech)`
- Chapter: `0.2-0.4: Tangentially related (general AI/ML news)`
- Actual: `0.2-0.4: Tangentially related (general AI/ML news, Python ecosystem)`
- Chapter: `0.5-0.7: Moderately relevant (LLM frameworks, agent protocols)`
- Actual: `0.5-0.7: Moderately relevant (LLM frameworks, agent protocols, related tools)`
- Chapter: `0.8-1.0: Directly relevant (LangGraph, Anthropic, MCP, Pydantic)`
- Actual: `0.8-1.0: Directly relevant (LangGraph, Anthropic, MCP, A2A, Pydantic updates)`

**3. Synthesis prompt system block significantly truncated (lines 456–463)**
- Missing context paragraph: "The diary tracks metacognition about building YAMLGraph — a YAML-first LLM pipeline framework on LangGraph."
- Item 2 missing: "(1-2 sentences each)"
- Item 4 missing: "inspired by today's developments"
- Missing final lines: "Be concise. This is a working diary, not a newsletter. If any article connects to one of the recent Seeds below, mention it."

**4. DiaryDigestEntry schema seed description truncated (line 157)**
- Chapter: `description: "Forward-looking question"`
- Actual: `description: "Forward-looking question inspired by today's developments"`

**5. Insight quote truncated (lines 566–569)**
- Chapter ends at: "...into a single copilot node with inline citations."
- Actual continues: "— the prompt itself reads the source files, not a separate research node producing summaries."

**6. Entropy heuristic quote truncated (lines 594–598)**
- Chapter ends at: "The fix is structural."
- Actual continues: ": store last-audited SHA, separate audit entries from development reflections, and enforce a cooldown."

**7. Sermon Distill block quote truncated (line 169)**
- Chapter omits the final sentence: "If the heuristic proves recurring, graduate it to this Scripture."
- (Note: the full sentence IS correctly quoted in the epigraph on line 3 and at line 531, making this an internal inconsistency.)

### What to Fix
1. **Line 349**: Change `entry: python scripts/diary_rotate.py` → `entry: .venv/bin/python scripts/diary_rotate.py`
2. **Lines 442–447**: Restore the full parenthetical lists from `analyze_relevance.yaml` (add "unrelated tech", "Python ecosystem", "related tools", "A2A", and "updates")
3. **Lines 456–463**: Restore the full system prompt block from `synthesize_diary_entry.yaml`, or clearly mark the truncation with `...` ellipsis
4. **Line 157**: Change seed description to `"Forward-looking question inspired by today's developments"`
5. **Lines 566–569**: Restore the full sentence from diary.md line 51 (add "— the prompt itself reads the source files, not a separate research node producing summaries.")
6. **Lines 594–598**: Restore the full sentence from diary.md line 97 (add ": store last-audited SHA, separate audit entries from development reflections, and enforce a cooldown.")
7. **Line 169**: Append "If the heuristic proves recurring, graduate it to this Scripture." to match the Distill step verbatim
