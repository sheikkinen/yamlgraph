# Case study: the research spikes behind the outsider reader

*A record of what was done, in what order, and what each step turned out to be for. One day (2026-09-05), three spikes, three plans, one standalone repository. Not a method — a case. Written by GitHub Copilot from the session that did the work; the operator's five-word instructions are quoted where they set direction. A second part digs the repository's record for earlier spikes, because the operator said this is a repeating pattern, and it is.*

---

## Part 1 — The outsider, spike by spike

### 0. The trigger (morning)

PR #591 (FR-990, a census of the repository's 242 capability files) was ready to merge. Its body was a pasted `fix(...)` commit message under a `feat` title, in project shorthand — *"enum-leak demotion and junk-drawer cap per FR-990 R-3"*. Four consecutive chat recaps that morning had been the same. The operator, on the fourth: *"these are still team members discussions — outsider would not understand a word."* Then the reframing that produced everything below: not an author-side "write plainly" skill (the writer judging its own clarity has the same blind spot) but *"more akin to the reviewer — an adversary model like judge. 'Outsider view.'"*

### 1. Spike 1 — the reader on the Copilot CLI (§12 of the census plan)

**Instruction:** *"research spike… copy review.sh / graph / prompt logic to a tmp folder… drop PR there and get comments… PR level contents should be analysed by 5.6-sol like the judge."*

**Where:** `/Users/sheikki/Documents/src/outsider-spike/` — a folder **outside the repository**, no `.git`, no `.github/`. Not for convenience: the Copilot CLI loads `.github/copilot-instructions.md` from its working directory, so a reader run inside the repo would have been primed with the whole rulebook. The one design rule — *the reader gets the PR title and body and nothing else* — was only enforceable from outside.

**What was copied, not invented:** `scripts/review.sh`'s wrapper shape (lock, artifact verified by content, exit code not trusted) minus all judge/review doctrine; the judge adapter's `copilot` node with `gpt-5.6-sol` pinned literally (a `{state.model}` template failed silently at the CLI — learned here, recorded, reused in every later adapter).

**Expectations written before the first run** (`EXPECTATIONS.md`): fixture A (the real PR body) should fail — restatement hedged, ≥5 unclear terms; fixture B (the operator-approved plain-language account of the same work) should pass — ≤2 unclear terms, restatement correct. *If A and B are not separated, the outsider is not an outsider.*

**What happened:** A failed as predicted. **B failed too** — 41 items. Told to "be exhaustive", the model interrogated plain English ("what kind of pipeline?") as if it were jargon. The single list had merged two different questions — *what does this word mean* and *where is the evidence* — into one junk drawer. Same failure class the census had found in its own classifier that morning (`author_graph` as the catch-all category), one level up.

**What separated A from B anyway:** the restatement. A: *"instruments and pilots something called the FR-990 CAP journey census… beneficiaries not stated."* B: correct in one read. The comprehension probe worked even when the count didn't.

**One catch nobody had made:** B's §4 said the plain account's *title* claimed a census of 242 while the text reported 30. True. The outsider found a defect in text the operator had approved.

### 2. Spike 1, round 2 — one prompt revision, one body rewrite (§12.7)

Prompt v2: §3 comprehension only, cap eight, ordinary vocabulary excluded; §4 becomes a merge-needs checklist that must skip what the text already states. PR #591's body rewritten from the outsider's list: explanation *plus pointers* (reading order, run command, cost, scope, data handling) *plus* a "what is NOT in this PR" section.

Results 8 / 6 / 5 items across the three fixtures — the count became informative once the junk drawer was capped. And a second finding that decided the production design: **§2 (the model's own yes/no) cannot be trusted.** The rule written to stop false NOs produced a false YES on the old body. So the verdict is derived in code: YES iff §3 ≤ 2 and the restatement carries no hedge marker. The model reports; code decides.

### 3. FR-995 — the plan, from the spike (same day)

*"File the FR, include needed refs to the spike files. cp preferred to reinvention… dogfood with outsider spike."* The FR's Research header pointed at §12 and at the spike copied into `docs/spikes/outsider-reader-2026-09-05/` (graph, prompts v1 and v2, tools, wrapper, inputs, six reports, `EXPECTATIONS.md`). Judged APPROVED WITH REVISIONS; three of the judge's five revisions were things the spike had *shown* but the FR had *softened* — the derived verdict, the fail-closed parser, the attributable ledger row.

Enforced as `scripts/outsider.sh` + `.github/skills/outsider-view/` (PR #592). Reviewed by `scripts/review.sh`: six blocking findings, all real, **none** of them things the outsider had flagged. The informed reviewer and the ignorant reader found disjoint sets. That observation later became a Scripture cure (`two_ends_of_the_knowledge_axis`, PR #595).

### 4. Spike 2 — the reader without Copilot (§13)

**Instruction:** *"next spike outsider, but with llm or agentic node — by definition not relying (much) on copilot features. Target: stand-alone yamlgraph-outsider that gets the PR, runs the graph and posts the comment."* The production reader had two problems the spike was to attack: it needed a Copilot subscription, and it *flickered* — the same positive fixture went NO (5 items) then YES (0 items) two minutes apart.

**Where:** `/Users/sheikki/Documents/src/outsider-spike-llm/`, again outside the repo. Three nodes: fetch PR via `gh` → **`llm` node** on the provider API, `claude-sonnet-4-5`, temperature 0, structured output through the prompt schema → finalize (validate, derive verdict with the unchanged rule, render the same report, optionally comment). Footprint: `pip install yamlgraph`, `gh`, one key. Model choice written into `graph.yaml` *before* the first run, with the reason.

**What broke first, and what it was:** the model returned the two `list[str]` fields as a JSON-encoded *string*; the framework's schema boundary rejected it and the run died. The spike worked around it in code and declared the fields `str`. This was recorded as a "framework FR candidate" — and became **spike 3**.

**Results:** T=0 through the API was stable (6 of 7 items shared across two runs, same verdict) — *the flicker was the transport, not the task.* But sonnet **over-flagged**: every path, every identifier, and on PR #592 it quoted the explanatory parenthetical itself as the thing it did not understand. Under the ≤2 rule no real PR body passes on sonnet. Two models, two failure modes. The fix was named as a reducer rule (drop file paths and self-glossed terms in code), not another prompt reword — the two-strike rule.

**Standalone worked end to end:** fetched #592, read it, posted the comment, ~25 s, no Copilot. Two comments now sit on #592 for the same body, one per model.

### 5. Spike 3 — the framework defect, reproduced (FR-998)

**Instruction:** *"investigate the framework defect (4)."*

Not a new folder this time — a 50-line probe (`docs/spikes/list-type-lie-2026-09-05/probe.py`) that called the framework's own `with_structured_output` path with the exact spike-2 prompt and schema, five times, `include_raw=True` so the raw tool arguments were visible *before* parsing. Three runs under the framework's default (Anthropic forced tool call): all three returned the list as a string — and not even JSON this time, a markdown bullet list, so the spike-2 `json.loads` repair would not have caught it either. Two runs under the provider's constrained decoding (`method="json_schema"`): both correctly typed.

The cause was one default argument at `executor_base.py` L400 plus the fact that the existing fallback keyed on an error string Anthropic never emits. FR-998 was filed with the probe and its output as the research record, judged (five revisions — the judge caught that a binder alone cannot catch a request-time error; the fix had to own invocation), and enforced by a parallel session the same afternoon (PR #599).

### 6. Spike 2 → FR-1001 → a new repository, redone from the plan

The spike-2 folder was never promoted. FR-1001 (*"a standalone repo that gives any PR an outsider view before review"*) took its **findings** — llm node, structured output, model as configuration, the list-as-string workaround now unnecessary after FR-998 — and specified a fresh repository, `sheikkinen/yamlgraph-outsider`, built through the authoring route from a brief, with its own tests, and *without* the parts the spike had grown that the plan rejected (the ledger; provider selection baked into the graph). Judged, re-judged ("thin script, graph owns gh, no ledger"), enforced by another session today. The spike stays where it is, as evidence.

### 7. Two more things the day produced

- **FR-1004** — the committed ledger that FR-995's judge had asked for conflicted across three open PRs within hours. Filed for retirement: the posted comment becomes the record. Its own outsider run (#598) found a hole in the plan — comments are editable — that no one in the loop had written down.
- The outsider read the article that was written about it, and flagged the jargon quoted *as an example of jargon*. It cannot see quotation marks. Kept in the article.

### What the case shows (about this case)

- Every spike lived **outside the governed tree** and was copied back in as evidence, not as code. The reason was concrete each time (instruction loading; no sole-route guard on a throwaway; a probe is not a graph), not a preference.
- Every spike wrote **expectations before running** and every spike's expectations were **partly wrong** — and the wrong half was where the design came from (the junk drawer, the untrustworthy §2, the flicker being transport, the bullet-list encoding).
- Each spike answered **one question** and raised the next; the next got its own spike. Three questions, three folders, three FRs. Nothing was generalised inside a spike.
- The FR is written **from** the spike and is smaller than it: the ledger, the model pin, the string workaround were all spike growth that the plan (or its judge) cut.
- The reproduction beat the argument every time: the judge, the reviewer and the operator all accepted the probe's five runs where they would have argued with a paragraph.

---

## Part 2 — Older spikes in the record

The operator: *"dig older spikes from the repo — some SDKs explored. This is a repeating pattern. Earlier approach was to abandon overgrown repo and just migrate the plan — redo using the plan."* The record agrees. What follows is what the repository itself says, with paths.

### The pre-history: five repositories, each abandoned for the next

[USER.md](../USER.md#L61-L83) dates the pattern to before this repository existed: `openai-cli` (Jan 2023, Node + curl) → `openai-cmd` → `openai-zsh` → `html-pipeline` (2023) → `statemachine-engine` (2024) → **yamlgraph** (Dec 2025, "the synthesis — abstraction of everything learned since 2023"). Five implementations left behind; what travelled was the content prompts, the domain models, the pipeline shape. His own note: *"The code prompts were naive. The content prompts were immediately expert-level."* The plan survived; the code did not need to.

### Inside this repository

| Date | Plan | What was spiked | Where | What happened to it |
|---|---|---|---|---|
| 2026-03-29 | FR-207 | `scripture-dev` — a template repo to distribute the process | separate repo | **Abandoned.** Zero contributions flowed back; *"a distributor that is not a consumer has nothing forcing it to stay true"* ([plan-ramp §](plan-ramp-spike-to-governed.md#L37-L44)). Salvaged by FR-868 (classify 27 artifacts: duplicate / lift / obsolete), replaced by FR-864's ramp. |
| 2026-05-05 | FR-329 | Agent SDK planner, "phase 1 standalone" | `examples/agent-sdk-planner/` | Spike kept as an example; runtime integration explicitly out of scope. |
| 2026-05-10 | FR-362 | Copilot instrumentation process-mining POC | scripts | Findings recorded; gap closure elevated to FR-364. |
| 2026-06-07 | FR-468–473 | Dungeon Master v1 — turn loops, beats, seven FRs deep before the core interaction was proven | `examples/dungeon_master/` | **Detached** to `purgatory/`. Diary: *"optimizing the artifact before validating the bet"* ([the phase we skipped](diary/diary-2026-06-07-the-phase-we-skipped.md#L17-L30)). |
| 2026-06-07 | FR-474 | DM v2 — a *synopsis prototype* only | same dir | Built GREEN, verdict *keep*; established the "J3/J4 regime": prototypes get no CAP, no REQ, no gates; output is a sentence, not a suite. Parts of v1 reused. |
| 2026-06-18 | FR-521 → new FR | a one-off replay script that killed a hypothesis | throwaway | Operator: *"fr for scripted replay of a chapter."* Diary: *"the disposable script was a reusable primitive wearing throwaway clothes"* — promotion surfaced three defects the throwaway had got away with ([the throwaway that earned a test suite](diary/diary-2026-06-18-the-throwaway-that-earned-a-test-suite.md)). |
| 2026-06-25 | Plot Modeller L-spikes (FR-570–593) | staged research spikes, each with a falsifiable gate | `examples/plot_modeller/` | Findings fed forward; one diary names the trap of promoting on a metric that held for the wrong reason ([promoting a spike is not solving it](diary/diary-2026-06-25-promoting-a-spike-is-not-solving-it.md)). |
| 2026-08-19 | FR-822 | DeviantArt publish API spike | `scripts/spikes/da_publish_spike.py` | **Throwaway by design**; script deleted, findings recorded as AC-01…10. |
| 2026-08-19 | (none) | `deviant-daily` — a spike that went to production | separate repo | Nothing noticed for four days; 0 hooks, 0 CI, 4 production failures in two hours. Produced FR-864 (ramp), FR-869 (spike-end detector: *"the agent will never declare it… detect the declaring commit"*) ([the spike ends at a commit](diary/diary-2026-08-23-the-spike-ends-at-a-commit.md)). |
| 2026-09-05 | FR-995 / 998 / 1001 | this case study | outside repo → `docs/spikes/` | Above. FR-1001 is the current instance of the pattern: spike abandoned in place, plan migrated, fresh repo redone from the plan. |

Also in `~/Documents/src/`, by name: `langgraph-poc-narrator`, `langgraph-npc`, `gitclaw`, `gitclaw-1`, `gitclaw-oulu-civic-intelligence`, `yamlgraph-tst`, `yamlgraph-break-glass-audit`, `outsider-spike`, `outsider-spike-llm`, `yamlgraph-outsider`. Several are spikes whose plan lives here and whose code does not.

### What the doctrine already says

- **`constraint_over_code`** ([Scripture](../.github/copilot-instructions.md)): *"216 lines of Scripture produce 21k lines of Python; the constraint is irreplaceable, the code regenerable; in a rewrite preserve the spec, schema, and incident record — leave the implementation behind."* This is the "migrate the plan, redo" rule, stated as a rewrite rule.
- **`spec_kill`**: *"Cheapest bug is the one killed in the spec."*
- **development-process.md** ([L200-207](development-process.md#L200)): *"Exploration inverts the rite: you enforce first (prototype) to discover what the plan should be, and the prototype might legitimately fail. The pipeline treats failure as a defect; exploration treats failure as the purchased information."* — the clearest statement of what a spike is, framed as a reason not to use the Chaplain for one.
- **FR-474's J3/J4 regime**: prototypes are exempt from CAP/REQ/gates and are judged on a sentence — documented inside one FR, nowhere else.

### What the record does not say

- What a spike *is*, as distinct from a POC (FR-362), a prototype (FR-474), a sketch, a throwaway script (FR-822). Four words, used interchangeably, no canonical one.
- **When a spike ends.** FR-869 answers it for the dangerous case (a `schedule:` or `secrets.` commit in an unhooked repo). Nothing answers it for the ordinary case — the folder that quietly grows a ledger, a model pin and a workaround until it is a product nobody judged. Today's spike 2 was two features past that line when FR-1001 cut it back.
- **Where spikes live and what they must leave behind.** Today's convention — outside the tree, `EXPECTATIONS.md` first, copied to `docs/spikes/<name>-<date>/` with raw outputs, cited by the FR's Research header — appears in three folders and no document. The diary of 2026-06-07 asked *"Where does Prototype belong in the Scripture, and how is it bounded?"* and planted it as a seed. It is still a seed.
- **What "redo from the plan" costs and saves.** Five pre-history repos, `scripture-dev`, DM v1, and now spike 2 → `yamlgraph-outsider` were all redone rather than promoted. The record shows the pattern; it does not show a single comparison of redo-from-plan against promote-and-clean, for any of them.

That last gap is the honest end of this case: the pattern is real and repeated, and every instance of it was a judgement call made without a written rule. Whether it should stay that way is a question for a plan, not for a case study.
