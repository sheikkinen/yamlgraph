# Feature Request: FR-806 — author.sh Brief Pre-Flight: Premise and Budget Checks

**Priority:** MEDIUM
**Type:** Tooling
**Status:** Approved with revisions (judgement folded 2026-08-15)
**Effort:** 0.5–1 day
**Requested:** 2026-08-15
**First consumer / first event:** the next `scripts/author.sh` invocation
whose brief contains a validation premise that would have failed a
ten-second local check — the class that killed FR-789 run 1 (exit 65
after a full authoring run, because `python3 -m http.server` cannot
serve the fixture's `/api/*` premise).

**Seed origin:** FR-791 diary
(`docs/diary/diary-2026-08-15-fr791-orchestrator-capstone.md`), Seed:
"should `author.sh` pre-flight the brief — verify its validation
premises are locally satisfiable and its validation plan fits the CLI
budget — before burning a 15-minute run?"

## Summary

Add a pre-flight stage to `scripts/author.sh` that runs before the
copilot CLI launch: (1) verify locally checkable premises the brief
depends on (files/fixtures referenced by path exist; commands named in
validation steps resolve), and (2) warn when the brief's validation plan
is likely to exceed the backend's hard 900s ceiling (live full-pipeline
smokes named in the brief). Failures print the violated premise and
exit before any tokens are spent; budget findings warn by default.

## Value Statement

For any agent invoking the sole authoring route, versus discovering a
bad premise via a dead run: three incidents in one enforcement day
(FR-789: unsatisfiable fixture-server premise → full-run death at the
report gate; FR-791: live-smoke plan overran the 900s ceiling → hard
timeout → resumed brief; FR-791 negative smoke: brief allowed inferred
`steps_tried` → adapter repair). Each cost a full authoring run. The
brief is code (FR-789 diary: "the brief is code — dry-run its premises");
`two_strike_split` says the third strike moves the check from operator
diligence into the script.

## Problem

`author.sh` treats the brief as opaque prose and launches immediately.
The route's proof artifact (`tmp/draft-authoring-report.md`) is written
only at the end, so a brief with a broken premise fails at the most
expensive possible moment — after authoring, at validation — and the
failure mode is a report-gate death (exit 65) or a CLI timeout, both of
which cost a complete run plus a resumed brief. The operator currently
compensates with a manual dry-run heuristic (applied successfully for
FR-790/791/792); manual diligence that must fire every time is exactly
what graduates to code.

## Ideal Result

`scripts/author.sh tmp/brief.md` prints a short pre-flight block —
premises found, each ✓/✗, estimated validation weight vs ceiling — and
either proceeds or exits 64 naming the first violated premise, before
the copilot CLI is spawned. A clean brief adds seconds; a doomed brief
costs seconds instead of a run.

## Proposed Solution

Keep it mechanical and cheap — no LLM in the pre-flight:

- **Premise extraction (R-2):** scan the brief for workspace-relative
  paths the brief asserts as **existing inputs** — fixtures, fixture
  servers, validation prerequisites — and check existence. Paths named
  as outputs the authoring run is supposed to create (governed
  graph/prompt artifacts) are NOT premises and must not fail pre-flight.
- **Command checking (R-3):** statically identify the executable for
  validation-section commands — never execute any brief-controlled
  command text. Resolution handles environment assignments, `python -m
  ...`, `./relative-script`, and quoted commands; shell substitutions
  and command bodies are never evaluated (brief text is untrusted
  external input per the instruction boundary).
- **Budget heuristic (R-1):** two or more live full-pipeline
  `yamlgraph graph run` smokes in the validation plan warn (the FR-791
  incident was two full-pipeline smokes + authoring against the 900s
  ceiling); three or more narrower live graph-run smokes also warn.
  Warning cites the 900s backend limit and suggests a resumed
  validation-only brief.
- **Modes:** premise failure → exit 64 with the violated line quoted;
  budget finding → warn, proceed. `--no-preflight` escape hatch exempt
  from nothing else (sentinel arming and report gate unchanged;
  `automation_inherits_doctrine`).
- **Traceability (R-4):** new capability `capabilities/CAP-237-author-brief-preflight.yaml`
  providing `REQ-YG-598`; all tests marked
  `@pytest.mark.req("REQ-YG-598")`. Doc surface is exactly
  `.github/skills/graph-authoring/SKILL.md` (brief-writing guidance:
  checked premise forms, budget trigger, `--no-preflight` boundary).
- **Tests:** unit tests for the extractor and checker against brief
  fixtures reproducing the FR-789 failure (asserted-but-absent fixture
  path) and the FR-791 overrun (2 live full-pipeline smokes); a
  shell-level test that a doomed brief exits 64 without spawning the
  backend.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: A brief with a validation prerequisite path asserted as an existing input/fixture/server, where that path is absent, exits 64 before the copilot CLI/backend is spawned and quotes the violated line.
- [ ] AC-02: A brief naming a not-yet-created output graph/prompt path, without asserting it as an existing prerequisite, passes pre-flight.
- [ ] AC-03: A validation-section command whose executable cannot be resolved exits 64 before backend spawn and quotes the violated line.
- [ ] AC-04: Command checking is static: tests prove pre-flight resolves valid executable forms including `python -m ...` and `./relative-script`, and does not execute shell substitutions or command bodies from the brief.
- [ ] AC-05: A brief reproducing the FR-791 class with two live full-pipeline `yamlgraph graph run` smokes prints a 900s-ceiling warning and still proceeds.
- [ ] AC-06: A clean brief passes pre-flight with all mechanically checked premises marked pass and no behavior change to sentinel arming, report-gate verification, or existing route exit semantics.
- [ ] AC-07: `--no-preflight` skips only the pre-flight; report-gate verification remains mandatory.
- [ ] AC-08: Pre-flight logic is unit-tested with `@pytest.mark.req("REQ-YG-598")`; `capabilities/CAP-237-author-brief-preflight.yaml` supplies that requirement; no LLM call exists in the pre-flight path.
- [ ] AC-09: `.github/skills/graph-authoring/SKILL.md` teaches the checked premise forms, the budget warning trigger, and the `--no-preflight` boundary.

## Alternatives Considered

- **Keep the manual dry-run heuristic:** worked for FR-790/791/792 but is memory-dependent diligence; the failure evidence shows it fires only after a first strike per session.
- **LLM-judged brief review:** higher recall on prose premises, but adds cost/latency/nondeterminism to every launch; the three observed failures were all mechanically detectable.
- **Post-hoc only (better report-gate diagnostics):** cheaper to build but pays after the run — the whole point is moving the check before the spend.

## Related

- FR-767 (sentinel-armed sole route — pre-flight slots in front of the same launch path)
- FR-789 (run 1 premise death — AC-01's reproduction), FR-791 (run 1 ceiling timeout — AC-02's reproduction)
- Scripture: `two_strike_split` (third strike → code), FR-789 diary "the brief is code"

**Prior art:** No existing FR touches author.sh launch-time validation. FR-767 established the route and its report gate; this adds a symmetric gate at the entry boundary (`the_one_law`: normalize where external data — the brief — enters).

## Judgement

See `feature-requests/FR-806-author-sh-brief-preflight.judgement.md` —
APPROVED WITH REVISIONS; R-1..R-4 folded above (budget trigger aligned
to the FR-791 incident, premise failures narrowed to asserted existing
inputs, static-inspection-only command checks, CAP-237/REQ-YG-598 and
exact doc surface named). Gates C-1..C-6 accepted: human review before
merge; sentinel/report gate untouched by `--no-preflight`; no execution
of brief commands; failures only on mechanically violated premises;
budget warnings stay advisory; scope stays at launch-time pre-flight.
