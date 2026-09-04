# YAMLGraph Onboarding — for Developers Coming from HIS / Web-UI Work

Audience: an experienced developer whose background is hospital
information systems and/or web applications, joining YAMLGraph
development. This guide covers the LLM pipeline framework and its
two MIT sibling libraries (Part 5); a companion guide for the
platform that composes all three lives in csap
`docs/onboarding-his-web-dev.md`.

## Part 1: The four mental-model shifts

### 1. YAML is the program, Python is the plumbing

Coming from web work, you expect logic in code and config in files.
YAMLGraph inverts the ratio: 60–80% of a pipeline lives entirely in
`graph.yaml` + `prompts/*.yaml` — nodes, edges, routing, schemas,
prompts. Python appears only at the three-layer boundary
(presentation: CLI/API; side effects: `yamlgraph/tools/`), enforced
mechanically by import-linter (`.importlinter`). If you find yourself
writing Python for orchestration, you are on the wrong layer.

### 2. A core component returns plausible lies

HIS integrations fail deterministically — a malformed HL7 message is
malformed every run. An LLM node returns *different* output per run,
and its failure mode is a well-typed wrong answer, not an exception.
Everything downstream is built against this: Pydantic schemas on
every LLM output (Commandment 5), tolerant matching in tests
(prefix/contains, never exact equality on LLM text), and the
`read_raw_output_first` rule — read N raw samples before trusting
any aggregate metric.

### 3. The state is generated, and you never mutate it

No manual state classes, no `state["key"] = value`. State shape is
derived from `state_key` fields in the graph; node functions return
update dicts and LangGraph merges them. The web-session instinct of
mutating a context object produces bugs the framework is specifically
designed to prevent.

### 4. The process is the hard part, not the code

~200 lines of doctrine (`.github/copilot-instructions.md`) govern
~21k lines of Python, and the doctrine is the irreplaceable artifact
(`constraint_over_code`). Every change flows through
plan → judge → enforce: a feature request in `feature-requests/`,
an independent judgement, then TDD enforcement of the frozen scope.
Coming from HIS change-control this rhythm is familiar — the surprise
is that authoring, judging, and reviewing are themselves executed by
LLM pipelines built with this framework (`scripts/author.sh`,
`scripts/judge.sh`, `scripts/review.sh`), and those routes are
mechanically enforced by PreToolUse hooks. The framework governs its
own development.

## Part 2: First hour (verified commands)

```bash
pip install -e ".[dev]"
pre-commit install && pre-commit install --hook-type commit-msg  # BOTH required

# smoke test
yamlgraph graph lint examples/demos/hello/graph.yaml
yamlgraph graph run examples/demos/hello/graph.yaml \
  --var name="World" --var style="holy see of code" --full

# fast test suite (~20s on 12 cores)
pytest tests/unit/ -q --no-cov -m "not slow" -n auto
```

## Part 3: Week-1 reading path

- **Day 1:** `README.md` → `reference/getting-started.md` (patterns,
  node types, CLI) → run three `examples/demos/` graphs and read
  their `graph.yaml` side-by-side with the output.
- **Day 2:** `ARCHITECTURE.md` (three-layer design, state generation,
  compilation pipeline) → `reference/graph-yaml.md` and
  `reference/prompt-yaml.md` as the language reference.
- **Day 3:** The doctrine: `.github/copilot-instructions.md` — read
  the Knowledge Graph section twice; every `trap:` entry is a paid-for
  production lesson. Then `docs/development-process.md`.
- **Day 4:** Tests as spec: `tests/unit/` files named after FR
  numbers encode incidents; `@pytest.mark.req("REQ-YG-XXX")` links
  every test to a requirement in `ARCHITECTURE.md`
  (`python scripts/req_coverage.py --strict` verifies).
- **Day 5:** Read 10 recent FRs + judgements in `feature-requests/`
  and 5 recent entries in `docs/diary/`. The diary is the
  knowledge-transfer channel — recurring lessons graduate from diary
  to Scripture.

## Part 4: Rules that will surprise you

- **Never author a graph by hand.** Any task creating or modifying
  `graph.yaml` / `prompts/*.yaml` goes through
  `scripts/author.sh <task-brief.md>` — the route is hook-enforced;
  manual authoring is denied at write time.
- **TDD is gated, not advised:** RED commit (failing test,
  `SKIP=pytest`) and GREEN commit land separately; pre-commit runs
  the unit suite on every commit.
- **The main checkout is OS-write-locked** on governed paths
  (FR-889). Isolated work goes through `scripts/worktree.sh new`;
  a `git pull` that dies with Permission denied mid-checkout leaves
  half-written debris — see `docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md`.
- **Certain phrases are commit-blocked** (pre-commit scans for
  hedging language that signals incomplete refactors); hooks also
  block `--no-verify`, AI co-author trailers, and multiline
  `git commit -m`. Read hook output before retrying — it names the
  violation.
- **Every `# noqa` needs a confession** in `docs/confessions.md`;
  every new capability needs a `capabilities/CAP-*.yaml` entry.

## Part 5: The MIT siblings

YAMLGraph is one of three MIT-licensed libraries that csap composes.
Same owner, same doctrine style, much lighter ceremony — both
siblings take direct commits to main.

### statemachine-engine (`github.com/sheikkinen/statemachine-engine`)

Event-driven FSM framework: YAML-defined workflows, pluggable
actions, SQLite-backed job queue, Unix-socket inter-machine events,
and — the one artifact in the fleet a web-UI developer will
recognize — a **FastAPI/WebSocket monitoring server with a live
Kanban board** for watching FSM instances move through state groups.
~44k LOC under `src/statemachine_engine/` (`core`, `actions`,
`database`, `monitoring`, `ui`, `tools`), 43 test files.

- CLI entry points: `statemachine` (run an engine),
  `statemachine-db` (queue/db inspection), `statemachine-fsm`
  (diagram generation).
- Start with `examples/simple_worker`, then `examples/patient_records`
  (the healthcare-shaped one); `examples/controller_worker` shows
  multi-machine coordination.
- Mental model: this is the engine csap's FSM process embeds. The
  `context_map` event-promotion mechanism and the action interface
  are the seams csap builds on.

### voice_runtime (`github.com/sheikkinen/voice_runtime`)

Provider-agnostic voice call runtime — the audio plumbing extracted
so consumers keep only conversation logic. Small and readable
(~2.8k LOC, 29 test files): `VoiceSession`, audio queues, **mark
synchronization** (`send_mark_and_wait` — how the system knows TTS
playback actually finished at the caller's ear), STT/TTS provider
factories (`create_tts()` / `create_stt()`, ElevenLabs default), and
Twilio transports (`transports/twilio_ws`, `transports/twilio_call`).

- Read the README's outbound-call example end-to-end: session →
  WebSocket registration → speak → mark-wait → `on_committed` STT
  callback. That one page is the whole mental model.
- HIS/web translation: marks are the voice equivalent of an ACK in
  an interface engine — without them you know you *sent* audio, not
  that it *played*. Barge-in and echo-filtering bugs live at this
  boundary.
- Read it before touching csap's Bridge: csap's audio path is this
  library's concepts at platform scale.

### How the three compose

```
csap (platform, governed like a medical device)
 ├─ statemachine-engine  → control flow: states, events, actions
 ├─ voice_runtime        → audio: transports, STT/TTS, marks
 └─ yamlgraph            → decisions: LLM pipelines as one action type
```

Onboarding order for a newcomer: voice_runtime (smallest, concrete),
then statemachine-engine (the control model), then yamlgraph (this
repo — the nondeterministic part), then csap (the composition, where
the hard bugs are seams, not components).

## The one-line orientation

Treat YAMLGraph as a compiler project where the language is YAML, the
runtime is nondeterministic, and the build system reviews your pull
request — the discipline is the product; the Python is regenerable.
