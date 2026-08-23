# Diary: the spike ends at a commit, not at a decision

**Date:** 2026-08-23
**Produced by:** Claude Opus 5 (Copilot CLI session).

The operator's question: a repo starts as a research spike where no
process is fine; then it goes live. The authoring agent should be
incentivised to declare that moment, which triggers the ramp-up. What
gets copied, what gets left, what gets tailored — and is this a cookbook
or are there replicable assets?

Four findings, and the first one kills the premise.

## 1. The agent will never declare it, and does not have to

Asking the authoring agent to announce "the spike is over" asks it to
manufacture work for itself at the exact moment its gradient points at
finishing. That is `continuation_bias` with a clipboard. I would not
have declared it in deviant-daily; I did not, for four days, while
publishing to a public gallery on a cron.

But the declaration is unnecessary, because **the transition is already
written in the repo, with a timestamp.** deviant-daily's own log:

```
2026-08-19 71e80b9 ledger: 2026-08-19 -> published      ← first irreversible public effect
2026-08-19 eeca704 feat: enable daily cron 07:00 UTC    ← unattended execution begins
```

Production is not a maturity level, it is a set of properties, each
mechanically detectable:

| Property | Detector |
|---|---|
| runs unattended | `schedule:` appears in a workflow |
| holds credentials | workflow references `secrets.*`; repo has Actions secrets |
| irreversible external effect | code calls a write API; a ledger of published artifacts exists |
| accumulating state | a committed state file that grows (`state/published.jsonl`) |

Any one of these is enough. Three of the four landed in deviant-daily on
its **first day**, in commits with clear subject lines. The repo tells on
itself; nobody has to be honest.

So the design flips: not *incentivise the agent to declare*, but
**detect the declaring commit and refuse to let it pass silently.**
Yesterday's finding said the check for "is the check running?" belongs
one layer above the check. Same here: the check for "is this still a
spike?" belongs in the layer watching the commit, not in the agent
writing it.

Concretely, in the guard that already inspects every command: a `git
commit` whose diff adds `schedule:` or `secrets.` to a workflow, in a
repo with no `.pre-commit-config.yaml`, gets stopped **once** with the
ramp command and the option to record `UNENFORCED.md` instead. That also
answers the warning-fatigue Seed from yesterday — this fires at most
once per repo, at the one moment it is not noise.

## 2. The ramp must be cheaper than the argument about the ramp

It triggers precisely when the operator wants to be doing something
else — that is what "going live" means. If ramping is a two-hour chore
it will be deferred, and deferral is permanent. The only viable target
is one command, minutes, reversible.

That constraint decides the tiering. Not four tiers of philosophy;
tiers defined by **what event triggered them**:

| Tier | Trigger | Content |
|---|---|---|
| 0 spike | new repo | nothing. Correct and deliberate. |
| 1 live | `schedule:` / secret / first external write | tests in CI, `ruff`, pre-commit basics, `AGENTS.md`, incident log |
| 2 governed | second contributor, or first incident that costs money or reputation | FR + judge route, diary gate, changelog gate, requirement IDs |
| 3 regulated | 62304 / MDR context | full RTM with a coverage gate, capability registry, review route |

deviant-daily crossed into Tier 1 on 2026-08-19 and into Tier 2 today,
by the money-or-reputation clause, four times over.

## 3. Copy / tailor / leave — decided by who owns the incident

The sorting rule that survives scrutiny: **an asset is copyable exactly
to the degree that it encodes no local incident.**

**Copy verbatim** — mechanical, domain-free:
- `pre-command-guard.sh` and the Copilot hook set. Evidence: it fired
  twice today on my `pytest | head`, once while my cwd was a different
  repo. It has no yamlgraph in it.
- pre-commit basics: ruff, file-size, trailing whitespace,
  merge-conflict, private-key detection, `--no-verify` block,
  forbidden-phrase list
- CI: run the suite, conventional commits, changelog and diary gates
- FR / judgement / diary templates
- the judge and review adapter routes — csap proved they port, by
  originating them

**Tailor** — shape copies, content is local:
- the doctrine file: inherit traps, cures and questions; **start the
  witness citations empty**. yamlgraph's Scripture cites NC-141,
  FR-371, CVE numbers — carrying those into a new repo makes a document
  nobody owns.
- requirement prefix and registry (yamlgraph `REQ-YG`/CAP; csap
  `VBOT`/`NC`) — the mechanism copies, the IDs are local
- thresholds: coverage %, file-size, complexity are policy, not law
- gates encoding local constraints (DA's 50-char title, the frozen
  roster) — these can only be born from the repo's own incidents

**Leave out:**
- the chaplain FSM runtime — it needs its own operator
- the 226-entry capability registry contents (the *mechanism* is Tier 3)
- 45 hooks wholesale. deviant-daily needs perhaps twelve. A ramp that
  installs everything gets reverted.

## 4. Cookbook *and* assets — but the source must consume what it ships

Both exist today, and the failure of one names the rule.

`scripture-dev` shipped assets it did not use: 16 hooks, frozen at
2026-03-29, and its own `scripture.yaml` still reads
`project_name: my-minesweeper` from a test render. It was a distributor
that was not a consumer, so nothing forced it to stay true.

yamlgraph's `.github/hooks/` and `.github/skills/` are the opposite:
current, exercised every day, already generic. csap's copies are live
for the same reason — someone practises there.

**The replicable asset must live in a repo that runs it daily.** Not a
template repo, not a distribution repo — the working repo, with a
`ramp.sh` that installs a named tier into a target path. Freshness stops
being a maintenance task and becomes a side effect of use.

Which makes `scripture-dev` a retirement candidate, not a revival one:
five months cold, a third of the current hook set, two toy consumers,
zero contributions back. Whatever it holds that yamlgraph lacks should
be lifted out, and the repo archived.

And the cookbook is not optional either — it is the part that says
*which* tier, *what* to tailor, and *when*. Assets without the cookbook
produce a repo with 45 hooks it does not understand; cookbook without
assets produces exactly what happened here, an agent that knew the
doctrine and had nothing enforcing it.

## Proposed graduation

```yaml
production_is_detected_not_declared: "An authoring agent will not
  announce the end of a spike — the announcement creates work at the
  moment its gradient points at finishing. But the transition is written
  in the repo with a timestamp: a schedule: trigger, a secret reference,
  the first irreversible external write, a committed state file that
  grows. Detect the declaring commit and stop it once; do not ask the
  agent to be honest about its own scope. (deviant-daily crossed on
  2026-08-19 in commits 71e80b9 and eeca704 and nothing noticed for four
  days.)"

asset_source_must_be_a_consumer: "A replicable asset decays unless the
  repo that ships it also runs it daily. scripture-dev shipped 16 hooks
  it did not use and froze in five months with its own config left
  pointing at a test project; yamlgraph's hooks stay current because
  they fire on every commit there. Distribute from the working repo, not
  from a template repo."
```

## Seed

Every tier boundary above is triggered by an event that already happened
— a cron enabled, an incident suffered, a second contributor arriving.
The ramp is therefore always at least one day late, and Tier 1 arrives
after the first unattended run rather than before it. Is there a
*prospective* trigger — something detectable in the intent rather than
the artifact, at the moment the agent writes the workflow rather than
the moment it commits — or is process, structurally, always installed
by the light of a fire that has already started?
