# YAMLGraph Onboarding — for Developers Coming from HIS / Web-UI Work

Audience: an experienced developer whose background is hospital
information systems and/or web applications, joining YAMLGraph
development. Companion guides exist for the sibling repos
(csap `docs/onboarding-his-web-dev.md`, statemachine-engine,
voice_runtime); this one covers the LLM pipeline framework.

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

## The one-line orientation

Treat YAMLGraph as a compiler project where the language is YAML, the
runtime is nondeterministic, and the build system reviews your pull
request — the discipline is the product; the Python is regenerable.
