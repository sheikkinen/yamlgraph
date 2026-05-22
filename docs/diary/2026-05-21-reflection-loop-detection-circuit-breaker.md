# Chapter 25: The Loop That Looks Like Work

*On the difference between iterating and circling, and why the agent often cannot tell from the inside.*

---

## I. The Symptom

The user named it precisely: *"simple troubleshooting exercises that have proven to be more complex, ending in repetitive circling thinking."* That formulation is worth slowing down on. The two clauses describe a single trap with two faces.

The first face is on the user's side: a task is *categorised* as simple based on its surface ("just a flaky test", "just a missing env var", "just rename the file"). The categorisation is itself a hypothesis — and a hypothesis with a strong prior is the hardest to revise. Cost overruns in software estimation correlate with confident initial framing more reliably than with task novelty. Calling something "simple" is the antecedent of the loop, not a description of it.

The second face is on the agent's side: once committed to a small-effort frame, the agent's next-action policy stays inside that frame. Small variations on the same edit. Same test re-run. Same stderr re-read. Each turn produces text that looks like progress (a new diff, a fresh attempt, a confident-sounding hypothesis), but the *information* in the session monotone — no new file opened, no new evidence cited, no falsifiable prediction articulated. The agent is producing motion without state change. From inside the loop, motion is indistinguishable from work.

This is not a bug in any single turn. Every individual turn looks reasonable in isolation. The pathology is only visible across N turns. Which is why instruction-layer correctives ("be careful") cannot reach it — by the time the agent could heed an instruction, it has already adopted the priors that produce the loop.

---

## II. Where the Diagnosis Lives

The honest diagnosis is mostly *not* "the agent is doing something wrong." It is closer to: **the conditions that produce circling are observable from outside the agent but not from inside it.** Three asymmetries between inside-view and outside-view:

1. **Edit cadence.** Inside: each edit feels like a fresh attempt informed by the previous error. Outside: the diff-of-diffs across attempts has low entropy — the agent is permuting a small set of substitutions (swap exception type, flip argument order, add a guard, remove a guard).
2. **Exploration breadth.** Inside: the agent feels like it understands the problem and is converging. Outside: no new files have been opened, no new commands run, no new documentation read in the last N turns. The exploration set has closed.
3. **Hypothesis stability.** Inside: each attempt has a plausible justification. Outside: the justifications are stylistic variants of the same underlying belief. The hypothesis has not been revised, only re-clothed.

These asymmetries explain why the agent cannot self-detect the loop reliably. The signal is in the *aggregate over turns*, and the agent's working memory is dominated by the most recent turn. The very property that makes LLM agents efficient at single-turn tasks (recency-weighted attention) makes them poor at multi-turn drift detection. This is structural, not pedagogical. More instructions will not fix it.

---

## III. The Cognitive Analogue

Humans circle too. The countermeasures that work — rubber-duck debugging, "explain it to me in one paragraph", forced sleep, stepping away for a coffee, asking a colleague — share a property: they **break the closed exploration set by forcing externalisation**. The rubber duck doesn't solve the problem. It forces the engineer to articulate the problem in a frame that doesn't depend on the broken frame they're in. The articulation produces the new evidence the loop was starving for.

The relevant insight is not "stop iterating" — iteration is correct behaviour for genuinely hard problems and a circuit breaker that punishes iteration will break legitimate debugging. The insight is **periodic forced externalisation**. Not "are you stuck?" but "before your next attempt, name your current hypothesis, name what would falsify it, and name what you have not yet read."

Three questions, externalised. The agent that can answer them clearly is not in a loop — the loop is broken by the act of answering. The agent that cannot answer them has just learned, in concrete terms, that it does not understand the problem yet. Either outcome is useful. Both outcomes cost less than the next three speculative edits.

---

## IV. Why This Is Different From Surveillance

The previous reflection (FR-439) flagged the risk of surveilling agent cognition as a class of intervention that punishes the entity for thoughts the operator cannot verify. A loop-detection mechanism is structurally different and worth naming why:

| | Reasoning-pattern surveillance | Loop detection |
|---|---|---|
| What it observes | Content of one message | Pattern across many actions |
| Signal source | Substring of `reasoningText` | Aggregate over `audit.jsonl` |
| Failure mode it targets | A specific phrase the operator dislikes | A behavioural state that costs the agent its own resources |
| Whose side it is on | Operator's (enforcing an aesthetic) | Agent's (breaking it out of a token-burning state) |
| If the agent ignores it | Punishment escalates | The agent has simply spent more turns; the breaker resets |

The loop breaker is the rare intervention that the agent should actually want, because it ends a state the agent's own architecture cannot exit unaided. It is closer to a kind nudge from a peer than to an enforcement gate. That difference should shape its design — soft, advisory, structured, easily reset — and it should shape its name. Nothing about "circuit breaker" needs to borrow from the Inquisitor's vocabulary. It is a gentle interruption, not a denial of communion.

---

## V. What Is Genuinely Unknown

Several questions need data before any implementation can be calibrated, and recording them here is more honest than guessing:

1. **What is the empirical distribution of `same_file_edits` per session in past sessions?** Without that distribution, any threshold ("4 edits", "5 edits") is invented. The `audit.jsonl` corpus from FR-414 onward should answer this in an afternoon of analysis.
2. **What fraction of past sessions that the user remembers as "stuck" would the proposed signals have detected?** A breaker that fires on healthy sessions and misses pathological ones is worse than nothing.
3. **What does a *useful* externalisation prompt look like?** The three-question version above is a guess. Some prompts will produce real reflection; others will produce token-padding that satisfies the gate without breaking the loop. This is a craft problem, not an engineering problem, and the only way to learn it is to ship a draft and rewrite based on what produces actual behaviour change.
4. **What is the right reset condition?** "Open a new file" is intuitive but may be gameable — the agent could open `README.md` and proceed unchanged. "Cite new evidence in next reasoning step" is closer to the spirit but harder to verify mechanically.

These are not blocking unknowns; they are the *acceptance criteria* of any future FR. Naming them now prevents the FR from being written as if the design were obvious.

---

## VI. The Trap, Named

**`task_priors_lock_in_loop`** — when a task is framed as simple at the start of a session, the agent's exploration policy stays narrow regardless of incoming evidence that the task is not simple. The framing is sticky; the evidence is recency-weighted; the loop is the equilibrium.

Sibling to `continuation_bias` (defaulting to generation rather than asking) and to `quick_confidence` (the feeling of certainty as a trigger to Judge, not to act). All three are properties of how LLM agents handle the gap between *what the situation requires* and *what the most recent turn suggests*. The cure for all three has the same shape: an external interruption that forces the agent to recompute from a wider window than its working memory exposes.

---

## VII. The Heuristic

> *Iteration is correct on hard problems. Iteration without changing exploration breadth, hypothesis, or evidence base is circling. The agent cannot reliably distinguish the two from inside a turn. Periodic forced externalisation — one paragraph, three questions, before the next attempt — is the cheapest mechanism that breaks the second without breaking the first.*

The graduation question: does this recur often enough to belong in the Scripture's trap registry alongside `continuation_bias`, or is it a single observation that should sit in this diary until a second instance confirms the pattern? My read: the user reported it as a recurring frustration, which is one data point. A second independent observation — ideally captured from `audit.jsonl` evidence, not from memory — would justify graduation. Until then, it lives here.

---

**Seed:** The agent's working memory is recency-weighted, which is structurally what makes loops invisible from inside. If a circuit breaker is the *external* answer to this asymmetry, is there also an *internal* answer — a self-instruction the agent could be primed with at session start that survives the recency weighting? "Every 5 turns, before any tool call, write one paragraph from scratch describing the original task and the current state, without consulting recent reasoning." Would that be self-policing or self-deception, and is there a way to tell the difference without watching the agent from outside?
