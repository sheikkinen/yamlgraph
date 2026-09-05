# Case study: earlier spikes in the record

*Companion to [case-study-research-spike-outsider.md](case-study-research-spike-outsider.md). That document follows one day's three spikes; this one goes back through the repository — and the operator's history before it — for the spikes, prototypes, proofs-of-concept and throwaways that came earlier, and for the move he named: "abandon the overgrown repo and just migrate the plan — redo using the plan." Each case is told from its own plan, judgement and diary, with paths. Where the record contradicts a plan's own claims, that is stated. Written by GitHub Copilot, 2026-09-05; the archaeology was done by a read-only sub-agent over feature-requests/, docs/diary/, docs/, USER.md and the sibling directories, then verified against the primary files.*

---

## 0. Before the repository: five implementations, one intent

[USER.md](../USER.md#L61-L83) gives the sequence from the operator's own hand:

| when | what | what it was for | fate |
|---|---|---|---|
| Jan 2023 | `openai-cli` — Node + curl | raw GPT-3 completions; first artifact `meta.js`, self-explaining self-testing code via prompts | left behind |
| Jan–Feb 2023 | `openai-cmd` | batch prompt pipelines, DALL-E, seeded narrative; classic texts rewritten (Sun Tzu in Orc dialect, Nibelung, Aesop) | left behind |
| early 2023 | `openai-zsh` — pure shell | Finnish primary-care chat simulation: synthetic EHR, ICD-10, SOAP notes, four-step clinical workflow | left behind |
| 2023 | `html-pipeline` | multi-project content factory from rich seed documents (Arvandor, the Seven Deadly Sins taxonomy, *Book of Five Rings* in Finnish) | left behind |
| 2024 | `statemachine-engine` — Python | event-driven FSM coordinating SDXL and Flux workers for the art pipeline | still exists as a sibling repo; its ideas are in `yamlgraph/utils/fsm/` |
| Dec 2025 | **yamlgraph** | "the synthesis — abstraction of everything learned since 2023" | this repository |

What travelled across the five abandonments is named in the same file: not code, but *content* — the seed documents, the domain models, the pipeline shapes, the belief that "code is an expendable artifact; intent is the product," already operational in 2023. The observation he attached to it is the one that explains why redo-from-plan was cheap for him and would be expensive for most: *"The code prompts were naive. The content prompts were immediately expert-level."* When the plan is where the expertise is, the implementation is the part you can afford to throw away.

## 1. `scripture-dev` — a template repository (FR-207, March 2026)

**Question.** Can the process — hooks, doctrine, judge — be distributed to other repositories as a template with a `render.sh`?

**Where.** A separate repository, `scripture-dev`, with sixteen hooks frozen at their March state and two toy consumer repos.

**What happened.** Nothing flowed back. The ramp plan's verdict, five months later ([plan-ramp-spike-to-governed.md L37-44](plan-ramp-spike-to-governed.md#L37-L44)): *"A distributor that is not a consumer has nothing forcing it to stay true."* The template drifted from the source the day it was cut. FR-868 (judged 2026-08-23) classifies its 27 artifacts as duplicate / lift / obsolete, lifts what is missing here, and archives the repo; the salvage lives under `ramp/salvage/`.

**What was carried forward.** The *question* — and its answer, inverted: FR-864's ramp ships *from this repository*, which runs the same assets on every commit, so the distributor is a consumer. Also the measure that decides whether a ramped repo has acquired the process rather than a copy of it: *does anything ever flow back?* (csap contributed four traps to the Scripture; scripture-dev contributed zero.)

**What the record shows today.** [FR-207](../feature-requests/FR-207-standalone-scripture-methodology-repo.md) still reads `Status: Implemented`. It was; it then failed; the plan that supersedes it says so, the plan itself does not. The abandonment is documented one hop away from the thing abandoned.

## 2. Agent SDK planner — a standalone feasibility spike (FR-329, May 2026)

**Question.** Can the Chaplain's Plan step (topic file → FR markdown) be reproduced on the Anthropic Agent SDK without touching yamlgraph core?

**Where.** Inside the repo, `examples/agent-sdk-planner/plan.py`, explicitly "phase 1 standalone."

**What happened.** It worked as a feasibility answer; runtime integration was declared out of scope and never came. The FR's own note: *"comparable deferred backend work exists and was intentionally constrained."*

**What the record shows today.** `plan.py`, `README.md` and `tests/` are still in the tree, `Status: Implemented`. A spike that answered its question and was kept as an example — never promoted, never removed. The first of several "kept in place" outcomes below.

## 3. Copilot instrumentation — a process-mining POC (FR-362, May 2026)

**Question.** Can Copilot session logs be mined to see what the agent actually did?

**What happened.** Findings recorded; the gap it exposed became a separate closure FR (FR-364). The diary for it is the only place the word "POC" is used for a spike in this repository — the vocabulary was already drifting.

## 4. Dungeon Master v1 → v2 — the clearest redo-from-plan (FR-468–473 → FR-474, June 2026)

**Question.** Is an interactive story-generation loop worth building?

**What happened first.** Five FRs (468, 470–473) built a turn loop, an outline system and a beat system — *before the core interaction was proven*. [FR-474](../feature-requests/FR-474-dm-v2-synopsis-prototype.md) says it plainly: *"The first DM prototype grew an over-scoped turn-loop/outline/beat system before its core interaction was proven. It has been detached to `examples/dungeon_master/purgatory/`."*

**The redo.** FR-474 restarts with one goal — *interactive generation of the synopsis* — and, in its judgement, invents the regime that today's spikes still run under without naming it:

- **J3** — *no CAP, no REQ tags, no tests-first while prototyping. Governance is premature before the bet is proven.*
- **J4** — *the deliverable is a decision, not a green pipeline*: the output is a one-line verdict, **keep / kill / reshape**, written back into the FR, *plus whatever throwaway code proved it.*
- **J5** — *promotion tripwire*: when the verdict is *keep*, a successor FR lights the fire; CAP, REQ, tests-first and gates return there, not before.

Verdict was *keep*. The diary ([the phase we skipped](diary/diary-2026-06-07-the-phase-we-skipped.md#L17-L30)) names the trap the five FRs had fallen into — *"optimizing the artifact before validating the bet"* — and adds that the process then committed the same error one level up: *"A polished FR for an unvalidated interaction is exactly the mistake the detached prototype made."* Its seed, still open: *Where does Prototype belong in the Scripture, and how is it bounded?*

**What the record shows today.** `purgatory/` is still in the tree (`plot.yaml`, `prompts/`, `tests/`), added by the same commit that built v2 (`fcb6364c`). Parts were reused. The overgrown thing was not deleted; it was moved out of the way and the plan was rewritten beside it.

## 5. A throwaway that earned a test suite (FR-521, June 2026)

**Question.** Does hypothesis S1 of FR-521 survive a replay with one chapter wiped?

**What happened.** A one-off script answered it (8/16 → 13/16; S1 dead). The reflex was to delete the script. The operator: *"fr for scripted replay of a chapter."* The diary ([the throwaway that earned a test suite](diary/diary-2026-06-18-the-throwaway-that-earned-a-test-suite.md)): *"The disposable script was a reusable primitive wearing throwaway clothes."* Promotion surfaced three defects the throwaway had got away with — coupling, an isolation claim that was false, and metric contamination — *because it was never tested.*

This is the counter-case to the rest of this document: a spike that was **promoted**, not redone, and the promotion is where the defects were found. The two outcomes are not a rule and its exception; they are the same finding from two sides — the spike's code is trustworthy only after the ceremony it skipped.

## 6. Plot Modeller L-spikes (FR-570–593, June 2026)

**Question.** A staircase of them — L1 to L7 — each a research spike with a falsifiable gate that the next level depended on.

**What happened.** Findings fed forward level by level. One diary ([promoting a spike is not solving it](diary/diary-2026-06-25-promoting-a-spike-is-not-solving-it.md#L21-L30)) records the trap that a gate can pass for the wrong reason: recall 0.53 was real *and* was produced by flooding one field with low-precision guesses — *"the recall passed because of the precision wound, not despite it."* The FR had let the one green number license a freeze. Named: `metric_held_means_contract_clean`.

This is the earliest place the record has expectations written *before* the run as a formal gate — today's `EXPECTATIONS.md` convention has its ancestor here, and so does its failure mode: a written expectation can be satisfied by the wrong mechanism.

## 7. DeviantArt publish — a throwaway by declaration (FR-822, August 2026)

**Question.** Can one image be published end-to-end through the DeviantArt API (OAuth PKCE → stash/submit → stash/publish)?

**Where.** `scripts/spikes/da_publish_spike.py`, described in the FR as *"a throwaway spike script … deleted or graduated by Phase 2."*

**What happened.** One publish, one deletion of the test deviation by the operator, findings recorded as AC-01…10 — a clean spike.

**What the record shows today.** The script is still there. It was last touched by FR-951 (UTF-8 declarations at text boundaries) — a throwaway that has started receiving maintenance. "Deleted or graduated" happened as neither.

## 8. `deviant-daily` — the spike that went to production (August 2026)

**What happened.** The DeviantArt pipeline became a repository, then a scheduled workflow with credentials, on 2026-08-19 — commits `71e80b9` (first public publish) and `eeca704` (cron enabled). *"Nothing noticed."* Four days later ([plan-ramp §Why](plan-ramp-spike-to-governed.md#L11-L30)): zero pre-commit hooks, zero CI jobs on its 145 tests, no doctrine file, four production failures in two hours. The doctrine had *travelled* — the agent writing it knew TDD and the boundary vocabulary — but *"everything that says **no** stayed behind, and knowing the rule turned out to be a different physical event from being stopped by it."*

**What it produced.** The ramp family (FR-864 split into 865–869, all judged 2026-08-23) and the sharpest statement in the record about how spikes end ([the spike ends at a commit](diary/diary-2026-08-23-the-spike-ends-at-a-commit.md#L13-L30)): production is not a maturity level but a set of mechanically detectable properties — a `schedule:` in a workflow, a `secrets.` reference, a write API, a growing state file — and *"the agent will never declare it, and does not have to … detect the declaring commit and refuse to let it pass silently."* FR-869 is that detector.

**Relation to the outsider case.** FR-873 (the provider type lie fixed on the deviant-daily side) is the same defect that spike 2 hit today and FR-998 fixed in the framework. The spike-turned-production repo was the first witness; the framework fix came two weeks and one more spike later.

## 9. Today (2026-09-05) — the pattern, one more time

Spike 2 (`outsider-spike-llm/`) grew a ledger, a model pin and a workaround for a framework defect. FR-1001 did not promote it. It specified a fresh repository, `sheikkinen/yamlgraph-outsider`, built from a brief through the authoring route, with its own tests — and *without* the three things the spike had grown. Re-judged in one line: *"thin script, graph owns gh, no ledger."* The spike stays in place as evidence. This is DM v1 → v2 again, at smaller scale and faster: the overgrown thing set aside, the plan rewritten, the rewrite built from the plan.

---

## What the earlier cases show, taken together

**The move is real and repeated.** Pre-history (five times), `scripture-dev` → ramp, DM v1 → v2, spike 2 → `yamlgraph-outsider`. In every instance what was carried was the plan — question, constraints, findings, incident record — and the implementation was set aside rather than cleaned. The Scripture states the rule as a rewrite rule (`constraint_over_code`: *"preserve the spec, schema, and incident record — leave the implementation behind"*); the cases show it was practised before it was written.

**"Throwaway" almost never means deleted.** `da_publish_spike.py`, `agent-sdk-planner/`, `dungeon_master/purgatory/` are all still in the tree; `scripture-dev` needed a judged salvage FR to be archived. Setting aside is what actually happens. The one that was promoted (§5) is the one whose defects were found.

**The regime for spikes was invented once and never lifted.** FR-474's J3/J4/J5 — no governance while prototyping; the deliverable is a keep/kill/reshape verdict plus whatever code proved it; promotion returns the gates — is the rulebook today's spikes ran under. It lives in one FR from June. The 2026-06-07 diary asked where Prototype belongs in the Scripture; it is still a seed.

**Expectations-first has an ancestor and a known failure mode.** The L-spikes' falsifiable gates (§6) precede today's `EXPECTATIONS.md`; `metric_held_means_contract_clean` is the warning that an expectation can pass for the wrong reason. Today's spikes met that failure in a different form — expectations that were *wrong*, and whose wrongness was the design signal.

**Where a spike lives was decided case by case.** Inside the tree (329, 474, 822, the L-spikes), in a separate repo (scripture-dev, deviant-daily), outside any repo (today's three). Each choice had a reason; none was written down as a rule. The two that became production without anyone deciding so (`deviant-daily`, and nearly spike 2) were the ones with a `.git`.

**The status lines lag the outcomes.** FR-207 says Implemented; FR-822 says the script is deleted or graduated; the tree says otherwise. The plan that supersedes an abandoned spike records the abandonment; the abandoned plan does not.

None of this is a proposal. It is what the repository says about itself when asked where its spikes went.
