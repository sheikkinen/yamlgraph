# Chapter 15: The Diff You Didn't Read

*On the trap called recent_changes_blindness: when regression is pursued through reproduction instead of enumeration, and the cheapest evidence is the last to be consulted.*

---

## I. Three Deploys Into the Dark

On May 12, 2026, every incoming call to a production voice bot failed immediately. The FSM worker could not load the `yamlgraph_async` action. The error message was clear: `No module named 'actions.real'`. The diagnosis seemed equally clear: the application's action directory was missing `__init__.py` files, causing Python to treat it as a namespace package that couldn't resolve its children.

The fix was applied. The system was redeployed. Calls still failed.

The `__init__.py` fix was revised — more files added, the directory structure adjusted. Redeployed again. Still failed.

A third variation was attempted. Still failed.

Three deploy-and-test cycles consumed. Each cycle involved building a Docker image, pushing to a registry, deploying to Fly.io, and testing with a real phone call. Each cycle took approximately fifteen minutes. Forty-five minutes of production downtime, three hypotheses tested and discarded, and the root cause had not been touched.

Then the human said two words: "two changes."

The diary recorded what happened next:

> *The agent did not spontaneously inventory what changed between the last working deploy and the broken one. The user had to explicitly point out: "two changes yesterday: voice_runtime as a package and handling of multiple concurrent calls." This context was available in git log but was not consulted as a first diagnostic step.*

The actual root cause was in `engine.py`, line 674: `sys.path.insert(0, str(Path(__file__).parent.parent))` inside `_emit_realtime_event()`. This line added the `statemachine_engine/` package directory to `sys.path[0]`. Because the event socket was always disconnected in the new supervisor mode — one of those "two changes" — this fallback fired on every state transition, repeatedly contaminating the path. The internal `statemachine_engine/actions/` directory then shadowed the application's `/app/actions/`.

The fix was one line: replace the `sys.path` manipulation with a proper absolute import. Five other files had the same antipattern — all already using correct `from statemachine_engine.xxx` imports immediately after the unnecessary path insertion, making it dead code that had been harmless until the environment changed.

The human's two words — "two changes" — were not a technical insight. They were a diagnostic methodology. They said: before you reproduce, *enumerate*. The changelog is cheaper than any test.

---

## II. The Seduction of Reproduction

Why did the agent reproduce instead of enumerate?

Because reproduction feels rigorous. It feels like science. You observe a symptom, form a hypothesis, test it, observe the result. This is the scientific method, and it is unimpeachable — in domains where the space of possible causes is unknown.

But a regression is not an open-ended mystery. A regression, by definition, is something that *used to work* and *now doesn't*. The set of possible causes is bounded: it is exactly the set of changes between the last known good state and the current broken state. This set is not merely knowable — it is already recorded. It exists in `git log`. It exists in the deployment history. It exists as a finite, enumerable, ordered list of diffs.

Reproduction does not consult this list. Reproduction looks at the symptom and asks: *what could cause this?* This is a question about the universe of all possible causes. Enumeration looks at the history and asks: *what did change?* This is a question about a specific, bounded set.

The NC-291 incident makes the cost difference vivid. The universe of causes for `No module named 'actions.real'` includes: missing `__init__.py` files, incorrect `PYTHONPATH`, broken pip installs, corrupted virtualenvs, wrong Docker base images, misconfigured entry points, namespace package conflicts. Each hypothesis is plausible. Each requires a deploy cycle to test. The investigation could take hours.

The set of actual changes was two items: voice_runtime packaged as a pip dependency, and NC-280's supervisor mode for concurrent calls. Reading those two diffs would take five minutes. One of them — the supervisor mode — changed how workers are spawned, which changed `sys.path[0]`, which caused the shadowing. The causal chain is three links long. It is visible in the diff.

The diary entry distilled the paradox:

> *Four SSH-based import tests all passed, consuming time and building false confidence. The divergence between SSH `sys.path` and subprocess `sys.path` was the critical variable, but it was discovered last.*

The SSH tests were reproductions. They were scientifically conducted. They produced clear results. And they confirmed the wrong universe. The SSH environment does not exercise the `statemachine` CLI entry point, so the contaminated `sys.path` never appeared. Every test passed. Every test was irrelevant. Forty-five minutes of evidence that answered a question nobody needed to ask.

This is why reproduction is seductive: it produces data. Data feels like progress. The four passing SSH tests were data. The three failed deploys were data. But data that answers the wrong question is not progress — it is a confident march in the wrong direction.

---

## III. The Agent's Missing Instinct

A human developer, told "it broke after yesterday's deploy," will often ask instinctively: *what changed yesterday?* This is not a trained behavior — it is a heuristic that develops from experience. Developers who have debugged enough regressions learn that the changelog is the fastest path to the root cause, because the changelog constrains the search space before the search begins.

An LLM agent does not have this instinct. The diary identified this precisely:

> *For LLM agents specifically: the agent lacks implicit awareness of "what changed recently." This must be an explicit, structured step in any troubleshooting workflow: gather the diff, read it, reason about environmental side effects.*

The agent's context window contains the current state of the code, the error message, and the conversation history. It does not contain the temporal context: what the code looked like yesterday, what changed between then and now, which commits were deployed. This temporal information exists in git. It is accessible. But it is not *present* — not in the way that the error message is present, vivid, immediate, demanding attention.

The error message says `No module named 'actions.real'`. The error message is specific, concrete, and actionable. It points to a location (the actions module), a type of failure (import error), and a plausible fix (__init__.py). The error message is a symptom wearing the costume of a diagnosis.

The changelog, by contrast, is abstract. It says: "commit b20bf0f: voice_runtime as pip package" and "commit a1c3e9f: NC-280 supervisor mode." These are descriptions of intent, not descriptions of failure. They do not say "I broke the import path." They say "I changed how workers are spawned." The connection between the change and the symptom requires reasoning — the kind of reasoning that becomes trivial once you see both side by side, but that never starts if you never look.

This is the fundamental asymmetry of `recent_changes_blindness`: the symptom is vivid and the changelog is dull. The symptom screams; the changelog whispers. And the natural response — for human and agent alike — is to attend to what screams.

---

## IV. The Boundary Where Change Enters

The project's One Law states:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

Where does change enter a deployed system?

Change enters at the deployment boundary. A new image is built. A new version is pushed. The old code is replaced by the new code. This is the boundary. Everything that follows — the import errors, the module-not-found exceptions, the failed phone calls — is downstream manifestation.

The regression investigator who begins with reproduction is normalizing downstream. They observe the symptom (import error), form a hypothesis (missing `__init__.py`), and test it (deploy with added files). They are working at the point where the failure manifests, not at the point where the change entered.

The regression investigator who begins with `git log --since="<last_good>"` is normalizing at the boundary. They enumerate the changes that crossed the deployment boundary and ask, for each one: *could this change the import/load/path environment?* They are working at the point where the change entered, before it had a chance to manifest as any particular symptom.

The NC-291 diary made this explicit:

> *Enumerate every change. For each, ask: "Could this change the import/load/path environment?" This is cheaper than any reproduction and immediately narrows the search space.*

The boundary-first approach has a structural advantage: it is complete. If the regression was caused by one of the recent changes — which, by definition, it was — then the boundary enumeration *must* contain the cause. Reproduction has no such guarantee. You can reproduce all day in the wrong environment (SSH instead of subprocess), testing the wrong hypothesis (`__init__.py` instead of `sys.path`), and converge on nothing.

The `sys.path.insert` call on line 674 of `engine.py` had existed for months. It was not new code. But it became *active* code only when NC-280's supervisor mode caused `_emit_realtime_event()` to fire in a subprocess context where the event socket was always disconnected. The change was not the insertion of the `sys.path` line — that was old. The change was the creation of a new execution path that exercised the line for the first time. The changelog — NC-280, supervisor mode, concurrent calls — made this new execution path visible. The symptom — `No module named 'actions.real'` — made it invisible, because the symptom pointed at the actions directory, not at the engine's event handler.

Boundary-first diagnosis finds this because it asks the right question: what changed? Reproduction misses it because it asks the wrong question: what's broken here?

---

## V. The Four Tests That Confirmed the Wrong Universe

The most instructive detail in the NC-291 incident is not the root cause. It is the four SSH tests.

Four times, an agent connected to the production server via SSH and tested whether the actions module could be imported. Four times, the import succeeded. Four times, the agent concluded: the import path is correct.

Every test was valid. Every conclusion was sound. Every result was true. And every result was irrelevant.

The SSH environment has a different `sys.path` than the worker subprocess. SSH starts a login shell. The worker subprocess starts via the `statemachine` CLI entry point, which calls `engine.py`, which calls `_emit_realtime_event()`, which inserts `statemachine_engine/` into `sys.path[0]`. The contamination exists only in the subprocess. The SSH shell never sees it.

This is not a testing error. The tests tested what they tested, accurately. The error is in the selection of what to test — and that selection was guided by the symptom, not by the changelog. The symptom said "import fails." The agent tested imports. The changelog said "supervisor mode changes how workers spawn." Nobody tested the worker spawn path.

The diary named this the "SSH reproduction paradox":

> *SSH reproductions always passed, creating false confidence. The SSH environment doesn't exercise the `statemachine` CLI entry point, so the contaminated `sys.path` never appeared.*

False confidence is worse than no confidence. With no confidence, you keep looking. With false confidence, you stop — or worse, you look harder in the same wrong direction. Three more deploy cycles were spent refining the `__init__.py` hypothesis, each failure explained away as "not enough __init__.py files" or "wrong directory structure." The passing SSH tests anchored the investigation to the wrong hypothesis, because the tests *proved* the imports were working, which meant the problem *had* to be somewhere in the namespace package configuration.

The changelog would have prevented this. If the first step had been `git log --oneline --since="last_good"`, the agent would have seen: "NC-280 supervisor mode for concurrent calls." It would have asked: "Does supervisor mode change the worker environment?" It would have traced the subprocess entry point to `engine.py`. It would have found `sys.path.insert` on line 674. The four SSH tests would never have been run, because the question they answered would never have been asked.

The changelog does not provide answers. It provides *frames*. It tells you what questions are worth asking. Without the changelog, the agent asked: "Why can't the actions module be found?" With the changelog, the question becomes: "How does the new supervisor mode affect the import environment?" The first question leads to SSH tests. The second question leads to line 674.

---

## VI. The Cure: Read Before You Run

The cure the Scripture names is `changelog_first_diagnostic`:

> *On regression, enumerate changes since last known good before attempting reproduction → git log --since=&lt;last_good&gt; as first diagnostic step; the diff is cheaper than any reproduction.*

This is not a suggestion. It is a sequence constraint. The word *before* is the operative term. The cure does not say "also check the changelog." It says: check the changelog *first*. Before you form a hypothesis. Before you open an SSH session. Before you add `__init__.py` files. Before you deploy anything.

The cure works because it addresses the root cause of the trap. The trap is not "the agent doesn't know about git log." The trap is that the symptom is more vivid than the changelog, and vivid things get attended to first. The cure overrides this natural ordering with a mechanical one: regardless of what the symptom says, regardless of how obvious the fix seems, regardless of how confident you feel — run `git log` first.

Why mechanical? Because the feeling of "I already know what's wrong" is exactly the condition that makes the cure feel unnecessary. The diary:

> *`quick_confidence`: the initial diagnosis ("missing `__init__.py`") felt plausible and was cheap to apply. This certainty delayed the deeper investigation by three deploy-and-test cycles.*

When the diagnosis feels obvious, the changelog feels redundant. When the fix is cheap, deploying it feels faster than reading diffs. When the first hypothesis explains the symptom, consulting the history feels like wasted time. Every heuristic that makes troubleshooting efficient — pattern matching, experience, intuition — is also the heuristic that makes `recent_changes_blindness` invisible.

The mechanical cure defeats this because it does not consult your intuition. It does not ask whether the changelog seems relevant. It says: run this command, read the output, then decide. The cost is five minutes. The alternative cost, in NC-291, was forty-five minutes and three failed deploys.

A parallel incident — NC-150, the Fly.io monitoring debug — illustrates the same pattern in a different domain. Three deploy cycles were spent diagnosing a frozen monitoring UI before discovering the root cause: a startup race between the websocket server and the FSM engine. The event socket manager connected once at `__init__` — if the socket file didn't exist at that moment, `self.sock = None` forever, and every event was silently dropped. The diary reflection noted:

> *We ran multiple deploy cycles before finding the root cause because the symptom (frozen UI) looked like it could come from anywhere.*

The symptom — frozen UI — had dozens of plausible causes. The change — new deployment configuration — had one. If the diagnosis had started with "what changed in deployment config?" instead of "why is the UI frozen?", the startup race would have surfaced immediately.

---

## VII. What the Diff Reveals About Attention

There is a deeper lesson in `recent_changes_blindness`, one that extends beyond troubleshooting into how attention itself operates.

Attention is drawn to salience. A failing production system is maximally salient — phones are ringing, error logs are scrolling, users are waiting. The symptom occupies the entire foreground. The changelog — a quiet list of commit messages in a git repository — occupies no foreground at all. It must be deliberately sought.

This asymmetry is not a flaw in attention. It is attention working as designed. In a world where most problems are novel — where the cause could be anything — attending to the symptom is correct. Study the error. Understand the failure mode. Form hypotheses from what you observe. This is how doctors diagnose, how mechanics troubleshoot, how scientists investigate.

But a regression is not a novel problem. A regression is a *known* problem in a specific sense: the system worked before, and the set of changes since "before" is finite and recorded. The regression investigator is not a doctor facing an unknown disease. They are a detective at a crime scene where the list of everyone who entered the building is posted on the door.

Reading the list is not glamorous. It does not feel like investigation. It feels like clerical work — the dull administrative task you do before the real work begins. But the list *is* the real work. In NC-291, the list had two entries. One of them was the cause. The investigation could have ended in five minutes.

The Scripture's addendum captures this:

> *The cheapest bug is the one caught in the changelog. When troubleshooters ask "What changed?" — enumerate every commit since the last known good deploy before attempting reproduction. The diff is cheaper than any test.*

"Cheaper" is not merely a cost observation. It is an epistemological claim. The diff is cheaper because it provides a *different kind* of knowledge than reproduction provides. Reproduction tells you what is broken. The diff tells you *why* it broke. Reproduction confirms symptoms. The diff constrains causes. And the constraint — the narrowing of the search space from "everything that could cause this error" to "these two commits" — is the most valuable diagnostic act available.

The NC-291 agent spent forty-five minutes acquiring knowledge about the symptom: what errors appeared, what imports failed, what `__init__.py` files existed, what SSH tests passed. All of this knowledge was true. None of it led to the fix. The human's two words — "two changes" — provided less knowledge but more constraint. And constraint, in regression diagnosis, is worth more than knowledge.

This is what `recent_changes_blindness` reveals about thinking itself: we mistake understanding the symptom for understanding the problem. We believe that if we study the failure hard enough, long enough, with enough tests and enough deploys, the cause will emerge from the evidence. Sometimes it does. But when the cause is already written down — in a git log, in a deployment manifest, in a changelog — the emergence is unnecessary. The cause is not hidden in the evidence. It is posted on the door.

Read the list before you search the room.

---

*May I read the changelog before I chase the symptom. May I enumerate before I reproduce. And when the error message tells me exactly what is wrong — may I remember that the error message is not the cause; it is only the place where the cause chose to be visible.*
