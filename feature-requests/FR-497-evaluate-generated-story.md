# Feature Request: FR-497 — Evaluate the generated story (structural gate + LLM rubric)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-16

## Summary

The DM v2 prototype can now generate a complete story end to end
([scripts/generate.py](examples/dungeon_master/scripts/generate.py)) and serialize
it two ways — the machine `story.json` and the reader `story.md`
([api/render.py](examples/dungeon_master/api/render.py)). What it *cannot* do is
say whether the story is any **good**. The only quality signals today are the
per-turn director's `scene_complete` and the `reviewed` flags — gates on *whether
a stage finished*, not on *whether the finished artifact is coherent, faithful, or
well-told*.

This FR adds a **two-tier evaluation** of a finished story, run from its
`story.json`:

1. **Structural tier (deterministic, no LLM)** — a pure, always-on regression gate
   asserting the render invariants on real output: no leaked sheet scaffolding, no
   doubled chapter heading, suppressed `world_state` ledger, monotonic chapter
   numbering, non-empty played chapters. This is the **golden-sample harness**
   seeded by the FR-495/FR-496 diary reflection ("the demo is a test boundary").
2. **Narrative tier (LLM-as-judge, YAML graph + prompt)** — a structured rubric
   that scores the story against the **very contracts the generation pipeline
   promised to honour** (synopsis fidelity, beat preservation, no-invention,
   character consistency, forward-carry continuity, climax/pacing, prose craft).

## Value Statement

A finished story can be **scored and inspected** without a human re-reading the
whole manuscript: the structural tier blocks the regressions we already paid to
fix (FR-495/FR-496) from silently returning under upstream prompt drift, and the
narrative tier gives a per-dimension score with **specific, quotable issues** so a
weak story is diagnosable, not just "felt off". Evaluation is the missing half of
"generate a story" — FR-494 proved we can *produce* one; this proves we can *judge*
one.

## Problem

The generation pipeline makes explicit quality promises in its prompts, but
nothing checks the finished story against them:

- [final_cut.yaml](examples/dungeon_master/prompts/final_cut.yaml) contracts
  **"COMPOSE, do not invent"**, **"preserve every canonical BEAT"**, **"state each
  standing fact once"**, and **"give each beat weight proportionate to its
  importance"** (climax gets the most space). Nothing verifies the final text kept
  these promises.
- [synopsis.yaml](examples/dungeon_master/prompts/synopsis.yaml) commits the story
  to an outline; nothing checks the **played** story matches the synopsis it
  committed to.
- [character.yaml](examples/dungeon_master/prompts/character.yaml) gives each
  character a `DRIVE` / `FLAW` / `ROLE`; nothing checks the characters **act**
  consistently with their own sheet.
- The forward-carry `world_state` ledger (FR-491 J7) is meant to keep chapter
  *N+1* consistent with chapter *N*'s end-state; nothing checks for **continuity
  breaks** (a fact contradicted across chapters).

And on the structural side, the FR-495 (doubled heading) and FR-496 (leaked
`SUMMARY:`/`ROLE:`/… scaffolding) defects were both **invisible to the unit
suite** and only caught by a human reading one live sample. There is no harness
that re-asserts those invariants on real rendered output, so the next prompt
mannerism that reintroduces a leak would ship unnoticed.

This is a **boundary** problem (`evaluation` boundary): the method of evaluation
determines the conclusion. A pure shape check ("is it valid Markdown?") passes a
story that is structurally clean but narratively incoherent; only a rubric that
reads the *substance* against the *contracts* can tell whether the story is good.

## Proposed Solution

Two tiers, sharing one entry point. Neither tier mutates the story; both read
`story.json` (the single source of truth) and, for prose dimensions, the rendered
`story.md`.

### Tier 1 — Structural gate (pure, deterministic, no LLM)

A pure function over the doc + its rendered Markdown, returning a typed report.
This is the cheap, always-green regression gate — it encodes the FR-494/495/496/492
invariants as assertions on real output:

```python
class StructureIssue(BaseModel):
    code: str           # e.g. "leaked-sheet-label", "doubled-heading"
    detail: str         # the offending line / location

class StructureReport(BaseModel):
    ok: bool
    issues: list[StructureIssue]
```

Checks (each a named `code`, each grounded in a frozen prior judgment):

- **`leaked-sheet-label`** — no `SUMMARY:`/`ROLE:`/`ORIGIN:`/`APPEARANCE:`/
  `PERSONALITY:`/`DRIVE:`/`BOND:`/`FLAW:` label survives into `story.md` (FR-496).
- **`doubled-heading`** — no `# Chapter N: Chapter N …` (FR-495).
- **`ledger-leak`** — the `world_state` text never appears in `story.md` (FR-492).
- **`heading-numbering`** — chapter headings are `1..k` in played order (FR-494).
- **`empty-played-chapter`** — every chapter in `chapters.order` with a
  `reviewed`/non-empty text contributes non-empty body (FR-492 raise-on-empty).
- **`missing-frontmatter`** — tagline lead, `# Synopsis`, and (when roster
  non-empty) `# Cast` are present (FR-494 J1/J2).

### Tier 2 — Narrative rubric (LLM-as-judge, YAML graph + prompt)

A new `prompts/story_eval.yaml` with an **inline schema** (Commandment 5 — typed
output, no untyped dicts) and a `graphs/story_eval.yaml` single-LLM node. The judge
is given the **premise**, the **synopsis**, the **cast sheets**, and the **rendered
manuscript**, and scores each dimension 1–5 with a justification and a list of
specific issues:

```yaml
# prompts/story_eval.yaml (inline schema sketch)
schema:
  name: StoryEvaluation
  fields:
    overall: {type: int, description: "1–5 holistic score"}
    verdict: {type: str, description: "one-line summary judgment"}
    dimensions:
      type: list[Dimension]
      description: "per-dimension scores"
# Dimension: {name: str, score: int(1–5), justification: str, issues: list[str]}
```

Dimensions (each maps to a generation contract, so the rubric is grounded, not
arbitrary):

| Dimension | Grounded in |
|-----------|-------------|
| Premise fidelity | the `--premise` the story was asked to deliver |
| Synopsis coherence | `synopsis.yaml` — story matches its committed outline |
| Beat preservation | `final_cut.yaml` "preserve every canonical BEAT" |
| No invention | `final_cut.yaml` "COMPOSE, do not invent" |
| Character consistency | `character.yaml` DRIVE/FLAW/ROLE acted out |
| Continuity / forward-carry | FR-491 J7 world_state — no cross-chapter contradiction |
| Climax & pacing | `final_cut.yaml` "give each beat weight proportionate" |
| Prose craft | `final_cut.yaml` continuous prose, standing facts stated once |

### Entry point

`scripts/evaluate.py --story outputs/dungeon-master/sample-courier` loads
`story.json`, runs Tier 1 (always), runs Tier 2 (unless `--no-llm`), and writes an
`eval.json` (typed) plus a human `eval.md` report beside the story — derived on
demand, never stored back into `story.json` (mirroring FR-492 J6 / FR-494 no-stored
-derivation rule).

## Acceptance Criteria

- [ ] A pure `evaluate_structure(doc, markdown) -> StructureReport` returns
      `ok=True, issues=[]` for the current fixed sample, and a populated `issues`
      list (correct `code`s) for a doc deliberately carrying a leaked label, a
      doubled heading, or a ledger leak.
- [ ] The structural tier runs with **no LLM and no I/O** and is unit-tested as a
      visibility harness in `examples/dungeon_master/tests/` (no `@pytest.mark.req`,
      FR-474 J3).
- [ ] A **golden-sample** test captures one real captured `story.json` as a
      fixture, renders it, and asserts `evaluate_structure(...).ok is True` — so a
      future prompt drift that reintroduces an FR-495/FR-496 leak fails a check
      (the diary Seed, realised).
- [ ] `prompts/story_eval.yaml` defines an **inline Pydantic schema**
      (`StoryEvaluation` with `overall`, `verdict`, `dimensions[]`); the rubric
      dimensions are the eight contract-grounded ones above.
- [ ] `graphs/story_eval.yaml` runs the judge as a single LLM node over the
      premise + synopsis + cast sheets + rendered manuscript and returns the typed
      `StoryEvaluation` (parse verified with a **mock-LLM** unit test — no live key).
- [ ] `scripts/evaluate.py --story <dir>` writes `eval.json` and `eval.md` beside
      the story; `--no-llm` runs the structural tier alone. A live end-to-end run
      against `outputs/dungeon-master/sample-courier` is captured to a log.
- [ ] The narrative tier is **advisory** for the prototype — it scores and reports;
      it does not block generation. (A hard quality gate is a separate, later FR.)

## Alternatives Considered

- **Single LLM holistic score only.** Rejected: an opaque "7/10" is not actionable
  and cannot catch a structural regression (a leaked label is a *mechanical* defect
  the LLM might gloss over). The cheap deterministic tier must exist and run always;
  the LLM tier adds the narrative judgment the deterministic tier cannot.
- **Feed the evaluation back into a generation revision loop.** Out of scope —
  that couples evaluation to generation and invites a runaway revise loop. Evaluate
  the *finished* artifact first; a revision loop is a separate FR once the rubric is
  trusted.
- **Build an eval dataset + CI quality gate now.** Over-engineered for a prototype
  (FR-474 J3 exempts the DM example from CI gates). Score one story at a time from
  its `story.json`; a corpus/gate can graduate later if the rubric proves stable.
- **Generic `^[A-Z]+:` leak detector.** Rejected (the `regex_fourth_exclusion`
  slide, same as FR-496 J3): match the **known** sheet labels explicitly; a generic
  stripper would false-positive on legitimate prose.

## Related

- [scripts/generate.py](examples/dungeon_master/scripts/generate.py) — produces the story this FR evaluates
- [api/render.py](examples/dungeon_master/api/render.py) — the `story.md` the structural tier inspects
- [prompts/final_cut.yaml](examples/dungeon_master/prompts/final_cut.yaml) / [prompts/synopsis.yaml](examples/dungeon_master/prompts/synopsis.yaml) / [prompts/character.yaml](examples/dungeon_master/prompts/character.yaml) — the contracts the rubric is grounded in
- FR-494 (full-story render), FR-495 (heading dedupe), FR-496 (cast gloss) — the invariants Tier 1 re-asserts
- [docs/diary/diary-2026-06-16-the-sample-that-named-its-own-bugs.md](docs/diary/diary-2026-06-16-the-sample-that-named-its-own-bugs.md) — the **Seed** (golden-sample regression test) this FR realises
- Sample: `outputs/dungeon-master/sample-courier/` (gitignored)
- FR-474 J3: DM prototype exempt from CAP/REQ/CI gates.
