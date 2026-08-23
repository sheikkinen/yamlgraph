# Diary: the process transfers by practice, not by template

**Date:** 2026-08-23
**Produced by:** Claude Opus 5 (Copilot CLI session).

Two attempts to give another repo yamlgraph's process exist side by
side, one failed and one worked, and they differ in exactly one thing.

## The comparison

| | `scripture-dev` | `customer-service-agent-platform` |
|---|---|---|
| mechanism | template repo + `render.sh` placeholder substitution | live adoption, then divergence |
| last commit | **2026-03-29** (5 months cold) | **2026-08-22** (yesterday) |
| pre-commit hooks | 16, frozen | 23, current |
| Copilot hooks | none | full set — `pre-command-guard`, `post-edit-checks`, `classify-emit`, `reasoning-pattern-check` |
| skills | none | 8, including `judge-fr`, `review-pr`, and two of its own |
| adapter routes | none | `scripts/judge.sh`, `scripts/review.sh` |
| FRs / diary | templates only | 566 / 42 |
| requirement tags | a `req_coverage.py` copy | **985 live `@pytest.mark.req`** |
| IEC 62304 | — | `docs/iec-62304-evaluation.md` |
| consumers | `my-minesweeper`, `my-minesweeper2` | a production voicebot |
| its own `scripture.yaml` | still says `project_name: my-minesweeper` | — |

`scripture-dev` shipped the *artifacts* of the process. csap acquired
the *practice* and then produced its own artifacts.

## The decisive difference: direction

The give-away is in yamlgraph's own Scripture. Open
`.github/copilot-instructions.md` and the witnesses cited are:

- `composition_bug` — "ninchat_voice: FR-371 8-step greeting replay,
  NC-141 runaway loop, NC-289 concurrent clobber"
- `mock_escape_hatch` — "FR-378 three corrections in one session"
- `refactor_orphans_secondary` — "NC-203 hangup detection lost"
- the judge doctrine's re-entry guard — "csap NC-414"

**Four traps in yamlgraph's law were learned in csap.** The judge
adapter's sole-route contract, which I obeyed twice today, carries NC
numbers because it was worked out over there.

That is not a template relationship. It is not even parent and child.
It is two peers under a shared law, each contributing the incidents it
happened to suffer. csap did not *receive* the process — it *practised*
it, hit its own walls, wrote them down, and some of what it wrote became
binding on me this morning.

`scripture-dev` could never do this. A rendered template has no
incidents of its own, and nothing flows back. It is a photograph of a
practice, and photographs do not age well: 16 hooks then, 45 now.

## What this says about deviant-daily

deviant-daily got neither. No artifacts, no practice. And the
consequence is sharper than "it has no gates":

**Its incident record exists — filed in the wrong repository.**

Today's four production failures are documented in yamlgraph:
`FR-863` holds the payload ceiling, the title cap, the degenerate
corpus key and the hedging; three diary entries hold the reflections.
The repo that *had* the incidents has no memory of them. Anyone opening
deviant-daily tomorrow sees clean code, a green pipeline, and no reason
why `MAX_EDGE = 1568` or why `row_id()` hashes prompts.

So the answer to yesterday's Seed — *can a new repo inherit the
receipts?* — is now partly answerable. It cannot inherit yamlgraph's
1,238 entries; those are someone else's scars. But it already owns four
of its own, misfiled. Founding its record is not an act of copying, it
is an act of **repatriation**.

## The correction to my own proposal

Two hours ago I proposed fixing `scripture-dev` by turning it into a
`pre-commit` hook provider — remote hooks, `rev:` pinning, no fork, no
drift. That is still the right *distribution* mechanism and it fixes the
decay problem.

But csap proves distribution was never the binding constraint. csap has
no `rev:` pin on anything; it *copied* the hooks and diverged, and it
works because someone is actively practising there. The mechanism I
proposed solves the problem `scripture-dev` had. It does not create the
condition csap has.

What makes the process live in a repo, in order of load-bearing weight:

1. **Someone works there often enough to hit walls** — no substitute
2. **The walls get written down in that repo** — the incident record is
   the asset; the gates are its precipitate
3. **Gates that fire on the way to a commit** — so the record has teeth
4. **A doctrine file the agent reads on entry** — so the vocabulary
   arrives before the incident
5. **Distribution mechanics** — the least important, and the only one
   `scripture-dev` got right-ish

I had that list upside down this morning.

## Proposed graduation

```yaml
process_transfers_by_practice: "A methodology cannot be installed by
  rendering a template — a rendered repo has no incidents of its own and
  nothing flows back, so it decays from the moment it is written
  (scripture-dev: 16 hooks frozen 5 months while the source reached 45,
  two toy consumers). It transfers where someone practises it and writes
  down what breaks: csap replicated the full apparatus AND contributed
  four traps back into the source's Scripture (NC-141, NC-203, NC-414,
  FR-371). Install gates cold if you like, but the asset is the incident
  record, and a repo whose incidents are filed elsewhere has no memory."
```

## The works, for deviant-daily

The operator's ruling: IEC-62304-styled RTM, skills, hooks, pre-commit —
the works. Notable that csap is the model here and csap's own
traceability is *tag-only*: 985 `@pytest.mark.req` markers with no
registry file and no coverage gate, so nothing detects a requirement
that loses its last witness. yamlgraph closed that with
`capabilities/*.yaml` + `req_coverage.py --strict`. deviant-daily should
inherit **yamlgraph's** shape there, not csap's — the one place the
successful replicant is the weaker model.

## Seed

If the asset is the incident record and deviant-daily's is currently
misfiled in yamlgraph, what is the correct home for an incident that
spans two repos — the one where the defect executed, or the one whose
doctrine failed to prevent it? Today's four are genuinely both, and
filing them twice means neither copy stays true.
