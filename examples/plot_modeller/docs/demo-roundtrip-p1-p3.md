# Demo: the round-trip skeleton, P1-P3 as planned

This walks one real run of the round-trip walking skeleton end-to-end and shows
**what the model planned** — the cast it derived (P1), the chapter briefs it
authored (P1), the prose it drafted (P2), and the deterministic coherence gate's
reading of the authored arc (P3). Every artifact below was written by the
`persist_run` leaf tool (FR-623); nothing here is hand-edited.

- **Graph:** [`graphs/roundtrip_skeleton.yaml`](../graphs/roundtrip_skeleton.yaml)
- **Premise:** `fixtures/synopses/detective-thriller-the-vanished-witness.txt`
- **Run artifacts:** [`demo-run/20260630T072751-062948Z-a9cd56fe/`](demo-run/20260630T072751-062948Z-a9cd56fe/)
- **Model:** `claude-haiku-4-5` (provider `anthropic`) — see `manifest.json`

## How it was produced (no Python runner — one graph YAML)

```bash
set -a; source .env; set +a
YAMLGRAPH_ROUNDTRIP_OUT=examples/plot_modeller/docs/demo-run \
PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
  .venv/bin/yamlgraph graph run \
    examples/plot_modeller/graphs/roundtrip_skeleton.yaml \
    --var premise="$(cat examples/plot_modeller/fixtures/synopses/detective-thriller-the-vanished-witness.txt)"
```

The spine is linear: `derive_cast -> outline_chapter_briefs -> draft_chapter (map)
-> assemble_book -> coherence_gate -> persist_run`. All flow is declared in the
graph; the only Python is the leaf tools (`assemble_book`, `coherence_gate`,
`persist_run`).

---

## P1 - Cast (`derive_cast`)

The synopsis expands into principal interiority sheets — each a goal, a belief,
and an affect arc. Source: [`cast.json`](demo-run/20260630T072751-062948Z-a9cd56fe/cast.json).

| Principal | Goal | Belief | Affect arc |
|-----------|------|--------|------------|
| **Detective Marren** | recover the witness and ledger to convict Consul Drey | the court system can be trusted to deliver justice if given the evidence | from naive faith in institutional integrity to hard-won belief in personal honesty as the only reliable foundation |
| **Pell** | survive and escape the conspiracy that hunts him | the entire legal system is compromised and no one can be trusted | from paralyzed terror and paranoia to fragile hope through one person's refusal to deceive |
| **Magistrate Hagen** | silence Pell and destroy the ledger to protect the guild's control | power flows to those willing to corrupt institutions and eliminate witnesses | from hidden authority to exposed complicity and public disgrace |

The two beliefs are designed to collide: Marren's faith in the institution is
exactly what Hagen exploits, and the story's turn is her belief converting to
Pell's.

---

## P1 - Chapter briefs (`outline_chapter_briefs`)

Each brief authors a `scene_type` (Swain proactive/reactive) and an `eff_affect`
arc — the open/close affect ops the chapter commits to. Source:
[`briefs.json`](demo-run/20260630T072751-062948Z-a9cd56fe/briefs.json).

| Ch | Title | scene_type | Authored affect ops | Entry → Exit |
|----|-------|-----------|---------------------|--------------|
| 1 | The Safe House Burns | proactive | open `Marren/fear` | trial set tomorrow → safe house burned, witness + ledger gone |
| 2 | The Thread Through the Harbor | proactive | open `Marren/doubt` | no case → trail traced to a guild warehouse |
| 3 | The Witness in the Dark | reactive | open `Marren/guilt` | found Pell → must choose: comforting lie or the truth about Hagen |
| 4 | The Truth Spoken | reactive | close `Marren/guilt`, open `Marren/hope` | the choice → truth told, duplicate ledger obtained, Pell will testify |
| 5 | The Reckoning | proactive | close `Marren/hope`, `Marren/fear`, `Marren/doubt` | enter courtroom → Hagen exposed, Drey exiled, court cleansed |

Read the affect column top to bottom and it is a closed arc: four threads open
(`fear`, `doubt`, `guilt`, `hope`) and all four close. The reactive scenes
(ch 3-4) carry the interior turn — guilt opens then closes as Marren resolves the
dilemma — while the proactive scenes (ch 1-2, 5) open and finally discharge the
external tension.

---

## P2 - Prose (`draft_chapter` map)

Each brief is drafted into prose by a map node, dosed by its `scene_type`. The
full assembled book is [`book.md`](demo-run/20260630T072751-062948Z-a9cd56fe/book.md)
(5 chapters, ~27 KB). Opening of Chapter 1:

> ## Chapter 1 - The Safe House Burns
>
> The safe house on Merchant Street was a nondescript brick building, four
> stories, with barred windows and a single entrance guarded by court-appointed
> men. [...]

`assemble_book` orders chapters deterministically by `chapter_id` (never by map
fan-in order) and asserts unique ids before concatenating.

---

## P3 - Coherence gate (`coherence_gate`)

The gate walks the **authored** `eff_affect` arc deterministically (no LLM on the
path) and reports how many authored opens never close, split by the `scene_type`
of the chapter that opened them. Source:
[`coherence.json`](demo-run/20260630T072751-062948Z-a9cd56fe/coherence.json).

```json
{
  "authored_dangling_rate": 0.0,
  "authored_opens": 4,
  "dangling": 0,
  "by_scene_type": {
    "proactive": { "authored_opens": 2, "dangling": 0, "authored_dangling_rate": 0.0 },
    "reactive":  { "authored_opens": 2, "dangling": 0, "authored_dangling_rate": 0.0 }
  }
}
```

This draw is fully closed: 4 opens, 0 dangling. The pop-walk pairs
`open fear (ch1) / close fear (ch5)`, `open doubt (ch2) / close doubt (ch5)`,
`open guilt (ch3) / close guilt (ch4)`, `open hope (ch4) / close hope (ch5)`.

> **What the number means — and does not.** `authored_dangling_rate` measures the
> **plan's** internal closure, not the prose. The FR-613 K=6 read showed this
> metric is the author's *self-report* in an abstract symbol layer decoupled from
> the text, and is **non-reproducible** across draws (an earlier draw of this same
> premise left `Marren/hope` dangling and the prose flipped Marren's gender
> between chapters — a defect the affect gate is blind to). Treat this `0.0` as
> "the plan it authored happens to close," not "the book is coherent." Re-grounding
> the gate in the prose is FR-622.

---

## Run artifacts (`persist_run`, FR-623)

`persist_run` is the deterministic tail leaf: it writes each finished stage to a
run-stamped directory so a run is durable and inspectable without `--export-state`.
[`manifest.json`](demo-run/20260630T072751-062948Z-a9cd56fe/manifest.json) records
provenance (premise, provider/model from the environment, microsecond `run_id`,
`chapter_count`):

| File | Stage | Contents |
|------|-------|----------|
| `manifest.json` | — | run_id, created_utc, premise, provider, model, chapter_count |
| `cast.json` | P1 | derived principal sheets |
| `briefs.json` | P1 | authored chapter briefs (full arc, never truncated) |
| `book.md` | P2 | assembled prose, chapter_id-ordered |
| `coherence.json` | P3 | authored-arc closure report |

The `run_id` (`<UTC ts, microsecond>-<premise hash>`) makes two draws of one
premise distinguishable — exactly what the non-reproducibility finding needs to
diff drafts after the fact.
