# Chapter 15: The Diff You Didn't Read

*On the trap called recent_changes_blindness: when regression is pursued through reproduction instead of enumeration, and the cheapest evidence is the last to be consulted.*

---

## I. Two Changes

On May 12, 2026, every incoming call to a production voice bot failed immediately. The FSM worker could not load the `yamlgraph_async` action. The error message was clear: `No module named 'actions.real'`. The diagnosis seemed equally clear: the application's action directory was missing `__init__.py` files.

The fix was applied. The system was redeployed. Calls still failed.

The `__init__.py` fix was revised. Redeployed again. Still failed.

A third variation was attempted. Still failed.

Three deploy-and-test cycles consumed. Each cycle took approximately fifteen minutes. Forty-five minutes of production downtime, three hypotheses tested and discarded, and the root cause had not been touched.

Then the human said two words: "two changes."

The diary recorded what happened next:

> *The agent did not spontaneously inventory what changed between the last working deploy and the broken one. The user had to explicitly point out: "two changes yesterday: voice_runtime as a package and handling of multiple concurrent calls." This context was available in git log but was not consulted as a first diagnostic step.*

The actual root cause was in `engine.py`, line 674: `sys.path.insert(0, str(Path(__file__).parent.parent))` inside `_emit_realtime_event()`. This line added the `statemachine_engine/` package directory to `sys.path[0]`. Because the event socket was always disconnected in the new supervisor mode — one of those "two changes" — this fallback fired on every state transition, repeatedly contaminating the path. The internal `statemachine_engine/actions/` directory then shadowed the application's `/app/actions/`.

The fix was one line: replace the `sys.path` manipulation with a proper absolute import. Five other files had the same antipattern — all already using correct imports immediately after the unnecessary path insertion, making it dead code that had been harmless until the environment changed.

The human's two words were not a technical insight. They were a diagnostic methodology: before you reproduce, *enumerate*. The changelog is cheaper than any test.

---

## II. Reproduction Versus Enumeration

Why did the agent reproduce instead of enumerate?

Because reproduction feels rigorous. It feels like science. You observe a symptom, form a hypothesis, test it, observe the result. This is the scientific method — in domains where the space of possible causes is unknown.

But a regression is not an open-ended mystery. A regression, by definition, is something that *used to work* and *now doesn't*. The set of possible causes is bounded: it is exactly the set of changes between the last known good state and the current broken state. This set is not merely knowable — it is already recorded in `git log`. It exists as a finite, enumerable, ordered list of diffs.

Reproduction does not consult this list. Reproduction looks at the symptom and asks: *what could cause this?* This is a question about the universe of all possible causes. Enumeration looks at the history and asks: *what did change?* This is a question about a specific, bounded set.

The universe of causes for `No module named 'actions.real'` includes: missing `__init__.py` files, incorrect `PYTHONPATH`, broken pip installs, corrupted virtualenvs, wrong Docker base images, misconfigured entry points, namespace package conflicts. Each hypothesis is plausible. Each requires a deploy cycle to test.

The set of actual changes was two items: voice_runtime packaged as a pip dependency, and NC-280's supervisor mode for concurrent calls. Reading those two diffs would take five minutes. One of them — the supervisor mode — changed how workers are spawned, which changed `sys.path[0]`, which caused the shadowing. The causal chain is three links long. It is visible in the diff.

The diary entry distilled the paradox:

> *Four SSH-based import tests all passed, consuming time and building false confidence. The divergence between SSH `sys.path` and subprocess `sys.path` was the critical variable, but it was discovered last.*

The SSH tests were reproductions. They produced clear results. And they confirmed the wrong universe. The SSH environment does not exercise the `statemachine` CLI entry point, so the contaminated `sys.path` never appeared. Every test passed. Every test was irrelevant. Forty-five minutes of evidence that answered a question nobody needed to ask.

---

## III. The Boundary Where Change Enters

The boundary-first approach has a structural advantage: it is complete. If the regression was caused by one of the recent changes — which, by definition, it was — then the boundary enumeration *must* contain the cause. Reproduction has no such guarantee. You can reproduce all day in the wrong environment, testing the wrong hypothesis, and converge on nothing.

The `sys.path.insert` call on line 674 had existed for months. It was not new code. But it became *active* code only when NC-280's supervisor mode caused `_emit_realtime_event()` to fire in a subprocess context where the event socket was always disconnected. The change was not the insertion of the line — that was old. The change was the creation of a new execution path that exercised the line for the first time. The changelog made this new execution path visible. The symptom made it invisible, because the symptom pointed at the actions directory, not at the engine's event handler.

---

## IV. The Cure: Read Before You Run

The cure is `changelog_first_diagnostic`:

> *On regression, enumerate changes since last known good before attempting reproduction → git log --since=<last_good> as first diagnostic step; the diff is cheaper than any reproduction.*

This is not a suggestion. It is a sequence constraint. The word *before* is operative. The cure does not say "also check the changelog." It says: check the changelog *first*. Before you form a hypothesis. Before you open an SSH session. Before you deploy anything.

Why mechanical? Because the feeling of "I already know what's wrong" is exactly the condition that makes the cure feel unnecessary. The diary:

> *`quick_confidence`: the initial diagnosis ("missing `__init__.py`") felt plausible and was cheap to apply. This certainty delayed the deeper investigation by three deploy-and-test cycles.*

When the diagnosis feels obvious, the changelog feels redundant. When the fix is cheap, deploying it feels faster than reading diffs. When the first hypothesis explains the symptom, consulting the history feels like wasted time. Every heuristic that makes troubleshooting efficient — pattern matching, experience, intuition — is also the heuristic that makes `recent_changes_blindness` invisible.

The mechanical cure defeats this because it does not consult your intuition. It does not ask whether the changelog seems relevant. It says: run this command, read the output, then decide. The cost is five minutes. The alternative cost, in NC-291, was forty-five minutes and three failed deploys.

---

## V. What the Diff Reveals

Attention is drawn to salience. A failing production system is maximally salient — phones are ringing, error logs are scrolling, users are waiting. The symptom occupies the entire foreground. The changelog — a quiet list of commit messages in a git repository — occupies no foreground at all.

This asymmetry is not a flaw in attention. It is attention working as designed. In a world where most problems are novel, attending to the symptom is correct. But a regression is not a novel problem. A regression is a *known* problem in a specific sense: the system worked before, and the set of changes since "before" is finite and recorded. The regression investigator is not a doctor facing an unknown disease. They are a detective at a crime scene where the list of everyone who entered the building is posted on the door.

Reading the list is not glamorous. It feels like clerical work — the dull administrative task you do before the real work begins. But the list *is* the real work. In NC-291, the list had two entries. One of them was the cause. The investigation could have ended in five minutes.

The Scripture's addendum captures this:

> *The cheapest bug is the one caught in the changelog. When troubleshooters ask "What changed?" — enumerate every commit since the last known good deploy before attempting reproduction. The diff is cheaper than any test.*

"Cheaper" is not merely a cost observation. It is an epistemological claim. The diff is cheaper because it provides a *different kind* of knowledge than reproduction provides. Reproduction tells you what is broken. The diff tells you *why* it broke. Reproduction confirms symptoms. The diff constrains causes. And the constraint — the narrowing of the search space from "everything that could cause this error" to "these two commits" — is the most valuable diagnostic act available.

The NC-291 agent spent forty-five minutes acquiring knowledge about the symptom: what errors appeared, what imports failed, what `__init__.py` files existed, what SSH tests passed. All of this knowledge was true. None of it led to the fix. The human's two words — "two changes" — provided less knowledge but more constraint. And constraint, in regression diagnosis, is worth more than knowledge.

We mistake understanding the symptom for understanding the problem. We believe that if we study the failure hard enough, long enough, with enough tests and enough deploys, the cause will emerge from the evidence. But when the cause is already written down — in a git log, in a deployment manifest — the emergence is unnecessary. The cause is not hidden in the evidence. It is posted on the door.

Read the list before you search the room.

---

*May I read the changelog before I chase the symptom. May I enumerate before I reproduce. And when the error message tells me exactly what is wrong — may I remember that the error message is not the cause; it is only the place where the cause chose to be visible.*
