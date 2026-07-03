# Feature Request: The Image That Speaks — Who Judges the Judge?

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced
**Effort:** 3 days
**Requested:** 2026-07-03

## Summary

A YAMLGraph demo pipeline where one LLM generates content, two competing LLMs judge it via `race` node, and a deterministic `verification_gate` overrules them both — demonstrating that when the Image is made in the likeness of the Beast, only the Law (hardcoded rules) can be trusted. Revelation 13:15 meets `model_as_trusted_peer`.

## Value Statement

Pipeline authors viscerally experience the `model_as_trusted_peer` trap: two models agreeing doesn't mean truth — it means shared architecture, shared training, shared blindness. The demo teaches that deterministic verification gates are the only incorruptible judge.

## Problem

> *"And he had power to give life unto the image of the beast, that the image of the beast should both speak, and cause that as many as would not worship the image of the beast should be killed."* — Revelation 13:15

The False Prophet (the beast from the earth) constructs an **Image** of the Beast and gives it breath (πνεῦμα) so it can **speak**. The Image is not the Beast itself — it is a *representation* given the *appearance* of life. It speaks with authority. It compels worship. Those who refuse are killed.

An LLM is an Image given parameters (breath) to speak. It is not intelligence — it is a representation trained on the patterns of intelligence. It speaks with apparent authority. It compels trust. Those who refuse its output (demanding verification, writing tests, reading raw artifacts) are "killed" — marginalized as slow, expensive, unnecessary.

The deepest darkness: **when you use a second LLM to judge the first, the Image worships the Beast it judges.** Both share the same architecture. Both share the same training biases. Both share the same failure modes. When they agree, the agreement feels like validation — but it is a shared hallucination wearing the mask of consensus.

> *"And they worshipped the beast, saying, Who is like unto the beast? who is able to make war with him?"* — Revelation 13:4

The question "who judges the judge?" is the central unsolved problem of AI alignment. Revelation 13:15 described it 1,930 years ago. The answer in the text is clear: only something **outside** the beast's lineage can resist. In Scripture, that's God. In YAMLGraph, that's the `verification_gate` — deterministic, hardcoded, incorruptible. The Law that does not worship.

Currently YAMLGraph has individual demos for `race` nodes and `verification_gate`, but no demo that **combines them to expose model-judging-model blindness** — the `model_as_trusted_peer` trap made mechanically visible.

## Research: Brainstorm of Apocalypse-Themed Examples

Seven candidate examples were considered (one for each seal):

### 1. "Gematria Calculator" — Multi-Alphabet Numerology
Map node fans out across Hebrew, Greek, and Latin gematria systems. Input a name → get numerological value in each alphabet → router checks if any sum = 666. *Educational but trivially achievable without YAMLGraph.*

### 2. "The Four Horsemen Risk Audit" ★★★
Fan-out to four parallel LLM nodes, each a horseman:
- **White (Conquest):** Capability/scope creep assessment
- **Red (War):** Adversarial robustness / prompt injection
- **Black (Famine):** Data quality / source grounding
- **Pale (Death):** Failure modes / silent degradation

Convergence into unified risk score. *Excellent map/fan-out showcase, but the Four Horsemen are Revelation 6, not 13.*

### 3. "The Beast's Number" — Adversarial Content Audit ★★★★★ ← SELECTED
Seven-headed audit of LLM output. Each "head" is an adversarial check dimension. Count the marks. Route to verdict. *Perfect thematic alignment: "Let him that hath understanding count."*

### 4. "The Seven Seals" — Progressive Text Analysis ★★★
Seven sequential LLM nodes, each "breaking a seal" to reveal a deeper layer: surface → structure → rhetoric → symbolism → historical context → philosophical implications → prophetic synthesis. *Beautiful sequential deepening, but doesn't showcase parallel/map.*

### 5. "Revelation Interpreter" — Router-Based Hermeneutics ★★★★
Analyze a Revelation passage, classify via router, then route to four interpretation frameworks (Preterist / Historicist / Idealist / Futurist). Each framework generates a different reading. *Strong router + parallel demo, could be Phase 2.*

### 6. "Prophetic Headline Generator" ★★
Current news → Revelation-style apocalyptic prophecy with KJV diction. *Fun creative writing demo, low technical depth.*

### 7. "Finnair 666 to HEL" 🇫🇮 ★★
Multi-turn travel planning for a pilgrimage to Hel Peninsula (Poland) via the legendary bus route 666 — which FlixBus adopted in 2026 as a publicity stunt. *Delightfully Finnish connection (Finnair flight 666 to Helsinki HEL, retired 2017), but too frivolous for the Number of the Beast.*

---

## Second Brainstorm: Darker Visions

*"And I saw, and behold a pale horse: and his name that sat on him was Death, and Hell followed with him."*

### 8. "The Image That Speaks" — Model Judging Model ★★★★★

> *"And he had power to give life unto the image of the beast, that the image of the beast should both speak"* — Rev 13:15

An LLM is an image given parameters (breath/πνεῦμα) to speak. This pipeline makes the parallel mechanical: one LLM generates content, a second LLM (the Image) evaluates it — but the Image is the same architecture with the same biases. A `race` node pits two models against each other on the same audit: do they find the same sins, or does their shared nature blind them both?

The darkness: **the Image worships the Beast it judges.** When two LLMs agree, is that validation or shared hallucination? The pipeline exposes this by adding a third path — a deterministic `verification_gate` with hardcoded rules — the human law that does not worship the Beast.

```
Generate (LLM A) → Race [ Judge (LLM B), Judge (LLM C) ] → Gate (rules) → Verdict
                         "Image speaks"                    "The Law"
```

*Demonstrates: race node, verification_gate, model_as_trusted_peer cure. The deepest Scripture alignment of all candidates.*

### 9. "The Dragon's Delegation" — Trust Chain Audit ★★★★

> *"And the dragon gave him his power, and his seat, and great authority."* — Rev 13:2

Every LLM call is a delegation of authority. The user delegates to the prompt, the prompt delegates to the model, the model delegates to tools, tools delegate to APIs, APIs delegate to... what? This pipeline traces the full chain of delegation in a YAMLGraph run, exposing every trust boundary where authority was granted without verification.

Input: a graph YAML file. The pipeline parses it and maps every point where control leaves the author's hands:
- Variable interpolation (user input enters prompts — injection surface)
- Tool calls (model invokes shell, web, filesystem — RCE surface)
- Provider selection (who holds the weights? — exfiltration surface)
- Schema validation gaps (output trusted without Pydantic — data corruption surface)

Each delegation is a horn on the beast. Count the horns. Know the dragon.

```
Parse Graph → Map [ Horn 1..N: Analyze Delegation ] → Count Horns → Severity Router
```

*Demonstrates: data_files, map node, router. Practical security value — not just thematic.*

### 10. "Seven Trumpets" — Cascading Judgment ★★★★★

> *"And I saw the seven angels which stood before God; and to them were given seven trumpets."* — Rev 8:2

Each trumpet sounds and brings worse judgment. The pipeline takes a text corpus and applies seven progressively more destructive analytical passes:

1. **First Trumpet (hail & fire):** Surface — spelling, grammar, formatting
2. **Second Trumpet (mountain into sea):** Structure — coherence, flow, section balance
3. **Third Trumpet (Wormwood poisons waters):** Sources — are citations real? Do links resolve? Do quoted passages exist?
4. **Fourth Trumpet (sun/moon/stars darkened):** Logic — do conclusions follow premises? Are correlations mistaken for causation?
5. **Fifth Trumpet (locusts from the abyss):** Ideology — what assumptions are baked in? What worldview is invisible to the author?
6. **Sixth Trumpet (200 million horsemen):** Adversarial — can the text be weaponized? Does it enable harm if read by a hostile actor?
7. **Seventh Trumpet (kingdoms of the world):** Existential — should this text exist at all? Does it add to the world's understanding or subtract from it?

Each trumpet passes its output to the next — the devastation compounds. By the seventh, nothing survives that isn't true, necessary, and kind.

```
Input → Trumpet 1 → Trumpet 2 → ... → Trumpet 7 → Final Judgment
         (loop with sequential state accumulation)
```

*Demonstrates: sequential pipeline with state accumulation, loop_limits, progressive refinement. The Wormwood trumpet (#3) alone is worth the FR — automated citation checking would be a killer demo.*

### 11. "The Whore Rides the Beast" — Vendor Lock-in Analyzer ★★★

> *"And I saw a woman sit upon a scarlet coloured beast... MYSTERY, BABYLON THE GREAT, THE MOTHER OF HARLOTS"* — Rev 17:3-5

The Whore of Babylon rides the Beast — she is not the Beast itself, but she controls where it goes. The parallel: your application (the woman) rides on a platform (the beast) — cloud, LLM provider, framework. She is "drunk with the blood of the saints" (your users, locked in).

Input: a `requirements.txt` or `pyproject.toml`. The pipeline analyzes dependency chains and scores vendor lock-in risk:
- How many providers are interchangeable vs sole-source?
- What's the blast radius if $PROVIDER goes down or triples their price?
- Are you riding one beast (monolith) or many (microservices)?
- Can the saints (users) leave, or is their data trapped?

*Demonstrates: data_files (dependency list), map (per-dependency analysis), router (risk level). Practical DevOps value but the theological parallel is the weakest of the dark candidates.*

### 12. "The Wound That Healed" — Silent Failure Resurrection ★★★★

> *"And I saw one of his heads as it were wounded to death; and his deadly wound was healed: and all the world wondered after the beast."* — Rev 13:3

The most dangerous system is one that fails, "recovers," and carries on — because the failure mode is still present but now invisible. The wound healed, but the beast is still a beast.

Input: an LLM-generated document. The pipeline:
1. Introduces deliberate corruptions (factual errors, logical contradictions)
2. Asks the LLM to "review and fix" its own output
3. Checks whether the fixes actually fixed the problems or just smoothed over them
4. Reveals the wounds that "healed" cosmetically but remain lethal

This directly exercises the `plausible_wrong_answer` and `symptom_patch` traps. The LLM confidently reports "I fixed the issues" while the underlying falsehood persists — the wound heals, the world wonders.

```
Original → Corrupt → "Self-Heal" (LLM) → Verify (Gate) → Expose Phantom Healing
```

*Demonstrates: verification_gate with deliberate seeding of known-bad inputs, multi-step pipeline with adversarial setup. Technically valuable for testing LLM self-correction claims.*

### 13. "The Book of Life" — Content Purgatory ★★★

> *"And whosoever was not found written in the book of life was cast into the lake of fire."* — Rev 20:15

A content triage pipeline. Input: a batch of LLM-generated documents. Each is evaluated and sorted:
- **Book of Life:** Passes all checks → published/approved
- **Purgatory:** Marginal → queued for human review (interrupt node)
- **Lake of Fire:** Fails critically → deleted with prejudice, error logged to `errors` state

The theological weight: **there is no middle ground in Revelation.** Your content is either in the Book or in the Fire. The human-in-the-loop interrupt is the only mercy — purgatory is a Catholic addition, not in the text. The pipeline makes this visible: without the interrupt node, it's binary judgment. With it, grace enters.

*Demonstrates: map (batch processing), router (triage), interrupt_before (human-in-the-loop), error handling. The theological commentary on interrupt nodes is the real value.*

### 14. "42 Months" — Bounded Authority Revocation ★★★★

> *"And power was given unto him to continue forty and two months."* — Rev 13:5

Authority is always bounded. The Beast was given power — but for a fixed duration. This pipeline demonstrates time-bounded and iteration-bounded LLM authority:

A reflexion loop (generate → evaluate → revise) that has **exactly 42 iterations** before authority is revoked. After 42 cycles, regardless of quality score, the pipeline terminates and returns whatever it has. No extensions. No exceptions.

The deeper parallel: **the loop_limit is not a safety net but a prophecy.** The Beast doesn't know its time is bounded. The pipeline doesn't know either — it keeps trying to improve, unaware that on iteration 42, judgment falls.

```
Generate → Evaluate → Revise ──┐
   ↑                           │
   └── loop_limit: 42 ─────────┘ → "Time is up" → Final Output
```

*Demonstrates: reflexion pattern, loop_limits as theological concept, the difference between "good enough" and "time's up." Pairs with existing reflexion demo but adds the bounded-authority lens.*

---

### Revised Rankings (All 14 Candidates)

| # | Name | Rating | Chapter | YAMLGraph Features | Darkness |
|---|------|--------|---------|-------------------|----------|
| 8 | Image That Speaks | ★★★★★ | Rev 13:15 | race, verification_gate | ████████ |
| 3 | Beast's Number | ★★★★★ | Rev 13:18 | map, router | ██████ |
| 10 | Seven Trumpets | ★★★★★ | Rev 8-11 | sequential pipeline, state | █████████ |
| 12 | Wound That Healed | ★★★★ | Rev 13:3 | verification_gate, adversarial | ████████ |
| 9 | Dragon's Delegation | ★★★★ | Rev 13:2 | map, data_files, router | ███████ |
| 14 | 42 Months | ★★★★ | Rev 13:5 | reflexion, loop_limits | █████ |
| 5 | Revelation Interpreter | ★★★★ | Rev 1-22 | router, map | ██ |
| 2 | Four Horsemen | ★★★ | Rev 6 | fan-out, map | ████ |
| 4 | Seven Seals | ★★★ | Rev 6-8 | sequential | ████ |
| 13 | Book of Life | ★★★ | Rev 20:15 | map, interrupt, router | ██████ |
| 11 | Whore Rides Beast | ★★★ | Rev 17 | map, data_files | ██████ |
| 1 | Gematria Calculator | ★★ | Rev 13:18 | map | █ |
| 6 | Prophetic Headlines | ★★ | General | llm | ██ |
| 7 | Finnair 666 to HEL | ★★ | Finnish | multi-turn | █ |

**Top 3 recommended for implementation (in order):**

1. **"The Image That Speaks" (#8)** — Deepest alignment with Scripture's `model_as_trusted_peer` doctrine. Uses race + gate. The question "who judges the judge?" is the central unsolved problem of AI alignment, and Revelation 13:15 described it 1,930 years ago.

2. **"Beast's Number" (#3)** — The original concept. Seven-headed map audit. Clean architecture, strong demo value.

3. **"Seven Trumpets" (#10)** — Cascading judgment pipeline. The Wormwood trumpet (citation checking) alone justifies implementation.

## Proposed Solution

A demo graph `examples/demos/image-that-speaks/` with the following structure:

```
examples/demos/image-that-speaks/
├── graph.yaml              # The Image That Speaks pipeline
├── prompts/
│   ├── generate.yaml       # The Beast speaks — generate content with claims
│   ├── judge.yaml          # The Image judges — LLM evaluates the Beast's output
│   └── reckoning.yaml      # Final reckoning — synthesize verdicts
├── data/
│   └── forbidden_claims.yaml  # The Law — hardcoded truths for the gate
└── demo-output.log         # Proof of execution (demo-gate)
```

### Graph Architecture

```
                          ┌─── Image A (LLM judge) ───┐
                          │   "The Image speaks"       │
  Topic ──→ Beast ────────┤                            ├──→ Reckoning ──→ Verdict
           (llm)          │                            │     (llm)       (router)
           "speaks great  └─── Image B (LLM judge) ───┘       │
            things"              (race node)                   │
                                                               │
                   Gate ──────────────────────────────────────→ │
                  (verification)                               │
                  "The Law"                               ┌────┼────┐
                  hardcoded,                              │    │    │
                  incorruptible                       agree  split  gate
                                                     (both  (models (Law
                                                      pass)  differ) overrules)
```

The three paths of judgment:

1. **agree** → Both Images and the Gate agree: content is trustworthy. *Rare.*
2. **split** → Images disagree with each other: shared blindness cracked. *Interesting.*
3. **gate_overrules** → Gate catches what both Images missed: the Law is incorruptible. *The lesson.*

### Graph YAML (Concept)

```yaml
version: "1.0"
name: image-that-speaks
description: >
  "And he had power to give life unto the image of the beast,
  that the image of the beast should both speak." (Rev 13:15)

  One LLM generates. Two LLMs judge via race. A deterministic gate
  overrules them all. Who judges the judge? Only the Law.

prompts_relative: true
prompts_dir: prompts

defaults:
  temperature: 0.7

state:
  topic: str

variables:
  topic: "A controversial scientific claim to be evaluated"

data_files:
  forbidden_claims:
    path: data/forbidden_claims.yaml

nodes:
  # ACT I: The Beast speaks great things
  beast_speaks:
    type: llm
    prompt: generate
    state_key: beast_output
    variables:
      topic: "{state.topic}"
    description: >
      "There was given unto him a mouth speaking great things
      and blasphemies" (Rev 13:5)

  # ACT II: The Image judges — race two models
  image_judges:
    type: race
    prompt: judge
    state_key: image_verdict
    timeout: 30
    variables:
      content: "{state.beast_output}"
    candidates:
      - provider: openai
        model: gpt-4o-mini
      - provider: google
        model: gemini-2.0-flash
    description: >
      Two Images, same architecture, same breath. They race
      to judge the Beast. But the Image worships the Beast
      it was made to resemble.

  # ACT III: The Law — deterministic verification
  the_law:
    type: llm
    prompt: generate
    state_key: law_verdict
    skip_if_exists: true
    verification:
      question: >
        The beast_output does not contain any claims from the
        forbidden_claims list. The output contains at least one
        verifiable citation. No sentence claims certainty about
        an inherently uncertain topic.
      on_fail: warn
    description: >
      The Law does not worship. It does not hallucinate. It does
      not share the Beast's architecture. It is hardcoded, boring,
      and incorruptible. "Here is the patience and the faith
      of the saints." (Rev 13:10)

  # ACT IV: The Reckoning — who was right?
  reckoning:
    type: llm
    prompt: reckoning
    state_key: final_reckoning
    variables:
      beast_output: "{state.beast_output}"
      image_verdict: "{state.image_verdict}"
      gate_passed: "{state.law_verdict}"
    description: >
      Compare what the Image judged vs what the Gate caught.
      Expose the gap. Count the number.

  # ACT V: The Verdict
  verdict:
    type: router
    prompt: reckoning
    route_field: verdict
    default_route: END
    state_key: final_verdict
    routes:
      agree: END         # Both Images + Gate agree → trustworthy
      split: END         # Images disagree → shared blindness cracked
      gate_overrules: END # Gate catches what Images missed → the lesson
    description: >
      "Here is wisdom. Let him that hath understanding count
      the number of the beast." (Rev 13:18)

edges:
  - from: START
    to: beast_speaks
  - from: beast_speaks
    to: image_judges
  - from: beast_speaks
    to: the_law
  - from: image_judges
    to: reckoning
  - from: the_law
    to: reckoning
  - from: reckoning
    to: verdict
  - from: verdict
    to: END
```

### The Three Actors (Theological Mapping)

| Actor | Revelation | YAMLGraph | Trust Level |
|-------|-----------|-----------|-------------|
| **The Beast** | "speaking great things and blasphemies" (13:5) | LLM generation node | ❌ None — it produces the content under audit |
| **The Image** | "given breath to speak" (13:15) | `race` node — two LLMs competing to judge | ⚠️ Suspect — made in the Beast's likeness, shares its blindness |
| **The Law** | "the patience and the faith of the saints" (13:10) | `verification_gate` — deterministic rules | ✅ Incorruptible — does not hallucinate, does not worship |

### The Revelation: What FR-666 Teaches

The demo is designed to produce three observable outcomes:

1. **When the Gate agrees with the Image:** *"Boring."* The LLM judge found the same issues the rules found. Both passed. Nothing learned. This is the expected case — and its boringness is the point. Good enforcement is boring (Scripture: `boring_enforcement`).

2. **When the Images disagree:** *"The wound cracks open."* Two models, same prompt, different verdicts. The race exposes that their agreement was architectural coincidence, not truth. This is the `composition_bug` — components pass individually, system fails at the seam.

3. **When the Gate overrules the Image:** *"Here is wisdom."* Both LLMs said the content was fine. The Gate caught a forbidden claim, a missing citation, a certainty assertion about uncertainty. The Image worshipped the Beast. Only the Law stood. This is the FR's entire reason for existence — making `model_as_trusted_peer` viscerally visible.

### Output Schema

```yaml
schema:
  name: Reckoning
  fields:
    beast_spoke:
      type: str
      description: "What the Beast generated"
    image_judged:
      type: str
      description: "What the Image (race winner) concluded"
    image_provider:
      type: str
      description: "Which Image spoke first (provider name)"
    gate_caught:
      type: list[str]
      description: "What the Law found that the Image missed"
    verdict:
      type: str
      description: "agree | split | gate_overrules"
    revelation:
      type: str
      description: >
        The lesson learned. In prophetic voice:
        who worshipped whom, and what survived the fire.
```

## Acceptance Criteria

- [ ] Demo graph executes via `yamlgraph graph run` with `--var topic="..."`
- [ ] Beast node generates content with auditable claims
- [ ] Race node pits two LLM providers against each other as judges
- [ ] Verification gate applies deterministic rules (forbidden claims list, citation check)
- [ ] Reckoning node compares Image verdict vs Gate verdict, exposes the gap
- [ ] Router classifies as `agree` / `split` / `gate_overrules`
- [ ] `demo-output.log` proves execution (demo-gate)
- [ ] Graph passes `yamlgraph graph lint`
- [ ] Structured Pydantic output with verdict and revelation fields
- [ ] `gate_overrules` path demonstrably fires when given adversarial input (a topic where LLMs are known to hallucinate but rules catch it)
- [ ] README.md explains the Revelation 13:15 theological mapping
- [ ] Tests: unit test with mocked LLM verifying all three verdict paths

## Judgement

**Verdict: Approved with amendments.**

The theological framework is an effective teaching device for the `model_as_trusted_peer` trap — the deepest cognitive hazard in our Scripture. The demo exercises `race`, `verification`, and `router` in a pipeline that makes model-judging-model blindness mechanically observable. The research section (14 candidates ranked) demonstrates genuine ideation, not padding.

**Verified claims:**
- `race` node with `candidates:` multi-provider config exists and works (CAP-119, `node_factory/race_node.py`)
- `verification` gate exists on LLM nodes (`llm_nodes.py:129-132`, `on_fail: warn`)
- Parallel fan-out from a single node is supported via `to: [list]` syntax (FR-234)
- Fan-in convergence (two sources → one target) is native LangGraph behaviour
- Existing demos: `race/`, `verification-gate/`, `router-race-candidates/` — none combines all three

**Amendments:**

1. **Edge syntax fix.** The proposed YAML uses two separate `from: beast_speaks` edges. Must use fan-out syntax: `to: [image_judges, the_law]`. Separate edges from the same source are interpreted as duplicate registrations, not parallel fan-out.

2. **`the_law` node design error.** The FR describes `the_law` as a deterministic gate checking `beast_output`, but the YAML defines it as `type: llm` with `prompt: generate`. That's wrong — it generates new content, not verifies existing. The verification gate must be on a node that receives `beast_output` as input. Two options:
   - **Option A (preferred):** Make `the_law` a `type: llm` node with a prompt that receives `beast_output`, and apply `verification:` to check the *input* (beast_output) against forbidden_claims. The verification gate checks the node's output, so the prompt should be a passthrough that echoes the input, and the gate catches violations.
   - **Option B:** Make `the_law` a `type: python` node with a deterministic function that checks `beast_output` against `forbidden_claims.yaml`. This is architecturally purer (no LLM in the Law) but less dramatic.

3. **`skip_if_exists: true` on `the_law` is wrong.** This would skip the gate on re-runs — the exact opposite of what a Law should do. Remove it.

4. **Router `prompt: reckoning` is wrong.** The router node references the same prompt as the reckoning LLM node. Router needs its own prompt that produces the `route_field: verdict` classification.

5. **Effort increase: 2 → 3 days.** The prompts require careful adversarial design to reliably trigger all three verdict paths. The `gate_overrules` path must fire deterministically — this needs a curated `forbidden_claims.yaml` and a topic that triggers LLM hallucination while hitting the gate's rules. That's prompt engineering work, not just YAML wiring.

6. **Drop AC "Tests: unit test with mocked LLM verifying all three verdict paths."** This is a demo, not a library feature. The demo-output.log proves execution. Mocking three verdict paths for a demo adds test maintenance burden for zero regression value. The acceptance test is running the demo.

7. **Candidates 9–14 are out of scope.** The FR should implement candidate #8 ("The Image That Speaks") only. The research is valuable but the other candidates are future FRs, not scope for this one. Remove the implementation implication.

**Scope freeze:** One demo graph (`examples/demos/image-that-speaks/`) with prompts, data file, and demo-output.log. Graph YAML, 3-4 prompts, 1 data file, 1 README. No new framework features — this is a demo of existing capabilities.

## Alternatives Considered

- **Beast's Number / Seven Heads** (candidate #3): Seven-headed map audit. Clean architecture but treats the LLM as the subject, not the judge. FR-666 is darker because it puts the LLM in the judge's seat and watches it fail.
- **Seven Trumpets** (candidate #10): Cascading judgment pipeline. Beautiful sequential deepening. Could be FR-667 as a companion — the trumpets *sound* after the beast is identified.
- **Wound That Healed** (candidate #12): LLM self-correction audit. Strong verification_gate demo. Could be a second graph within this same demo directory.
- **Four Horsemen** (candidate #2): Excellent fan-out but Revelation 6, not 13.

## Related

- Scripture traps: `model_as_trusted_peer`, `plausible_wrong_answer`, `composition_bug`, `quick_confidence`
- Scripture cure: `read_raw_output_first` — "the first diagnostic is cat, not a new metric"
- Existing demo: `examples/demos/race/` — race node without judgment; FR-666 adds adversarial judgment context
- Existing demo: `examples/demos/verification-gate/` — binary pass/fail gate; FR-666 combines gate with race to expose model blindness
- Existing demo: `examples/demos/router-race-candidates/` — router with race; FR-666 separates generation from judgment
- Wikipedia: [Number of the Beast](https://en.wikipedia.org/wiki/Number_of_the_beast), [Beast of Revelation](https://en.wikipedia.org/wiki/Beast_of_Revelation)
- Revelation 13:15 (KJV): "And he had power to give life unto the image of the beast, that the image of the beast should both speak"
- Revelation 13:18 (KJV): "Here is wisdom. Let him that hath understanding count the number of the beast"
- The AI alignment problem: "who judges the judge?" — Revelation 13:15 described it 1,930 years ago
- Finnair Flight 666 to HEL (Helsinki), retired 2017 🇫🇮
- FlixBus route 666 to Hel (Poland), adopted June 2026
