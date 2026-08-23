# The Symlink Remembers What Git Forgot

*Session: origin-story archaeology — tracing yamlgraph's creation across four
repos, recovering the 39 devoured FRs, revising Act IV from the recovered
corpus (commits `dbf26ab3`, `03615445`, `8e326bde`).*

## What happened

Asked for the creation story "before the FR era," I found that the project's
own best retrospective — the Philosopher's 4,000-line genesis entry — had
already hit the question and bounced off it: *"code already existed
somewhere else, and was pulled out into its own shape."* It accepted the
repo boundary as the edge of knowable history. One `ls ~/Documents/src`,
four `git rev-list --max-parents=0` calls, and a `file` on a broken symlink
answered what the retrospective could not: the narrator parent (root
`0d76df52`, 2025-11-26), the npc twin (shared root `50e1829e`), the
proto-Scripture living verbatim in the parent's README, and the extraction
fossil `langchain-showcase -> ../langgraph-showcase/` — committed one day
after the extraction, broken by the rename three weeks later.

## Traps and cures observed

**workspace_is_not_boundary, read direction reversed.** The Scripture entry
warns about destructive ops crossing hidden repo boundaries. This session
showed the *epistemic* face of the same trap: lineage questions cannot be
answered from inside one repo, and an agent that treats the workspace as
the world will write "code already existed somewhere else" and stop. The
cheapest cross-boundary probes — sibling `ls`, root-commit hashes — cost
four commands. The Philosopher had tool access too; it lacked the question.

**Filesystem fossils outrank git for provenance of the unrecorded.** The
showcase's distillation has no commit history anywhere — the most
consequential 1,719 lines in the lineage were written between repos,
unwitnessed. The only surviving evidence of parentage is a *broken symlink*:
an artifact git tracked but whose meaning lives in its brokenness (the
target renamed out from under it). Absence of history plus a dangling
pointer told the story that no log could.

**Deletion-record archaeology before reading the deleted artifact** — the
historian's variant of `read_raw_output_first`. My first pass characterized
the devoured-FR era from metadata: deletion commits, numbering collisions,
filename chaos. Verdict: primitive era. Then the operator said "check the
early FRs — they are a core mechanic," and reading the recovered *content*
overturned the narrative: Acceptance Criteria in 24/39, Alternatives
Considered in 18/39, structured rejections with rationale, hand-written
`## Judgment` + `**Verdict:**` sections dated three days before the
Chaplain shipped. The era was structurally mature and procedurally naive —
the exact inverse of what the metadata suggested. Same law, new boundary:
the deletion log tells you THAT something died; only the corpus tells you
WHAT it knew.

**Git deletion is a soft delete; legibility is the real recovery.** The 39
FRs were never gone — every one was a `git show "$c^:$f"` away. What the
memento added was not data but *addressability*: a directory, a provenance
table, links from the narrative. Unreachable history is functionally
identical to lost history until someone builds the index.

**Silent commit failure, caught by ritual.** `git commit -q … | grep -E
'Failed'` swallowed the pre-commit abort (`pre-commit not found` — fresh
terminal, no venv); HEAD verification (`git log -1`) caught it, exactly as
hook-lessons prescribes. The verify-after-commit ritual paid out within the
same session that reads history about rituals paying out.

## The finding that reframes the doctrine

The Judge existed as a *written ritual* before it existed as a pipeline:
FR-040/042 carry manual Judgment sections (2026-02-17) applying what would
become spec_kill reasoning, three days before FR-055 automated it. Every
stage of the modern pipeline appears to follow the same law: **manual
ritual → recurring practice → automation**. The Chaplain didn't invent
judgement; it mechanized a habit that had already proven itself twice. That
is the graduation process (heuristic → FR → Scripture) operating on the
governance system itself, before the graduation process existed.

**Seed:** The unrecorded showcase distillation — the highest-consequence,
lowest-witness artifact in the lineage — was written in the gap *between*
repos, invisible to every future gate. Today's equivalent gap is the agent
session itself: work products that exist in conversation but never reach a
committed artifact. What is the modern `langchain-showcase` being distilled
right now in some session's context window, and would a "between-repos
registry" (session → artifact manifest, FR-742-style briefings) catch the
next unwitnessed creation before its only fossil is a broken pointer?
