# Feature Request: FR-806 — author.sh Brief Pre-Flight: Premise and Budget Checks

**Priority:** MEDIUM
**Type:** Tooling
**Status:** Proposed
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

- **Premise extraction:** scan the brief for (a) workspace-relative
  paths (fixtures, fixture servers, existing graphs/prompts named as
  inputs) and check existence; (b) fenced/inline commands in validation
  sections and check the executable resolves (`command -v` on the first
  token; venv-aware for `yamlgraph`).
- **Budget heuristic:** count live-smoke invocations named in the
  validation plan (e.g. `graph run` lines that are not `--help`/lint);
  above a configurable threshold (default 2), print a ceiling warning
  citing the 900s backend limit and suggest a resumed validation-only
  brief.
- **Modes:** premise failure → exit 64 with the violated line quoted;
  budget finding → warn, proceed. `--no-preflight` escape hatch exempt
  from nothing else (sentinel arming and report gate unchanged;
  `automation_inherits_doctrine`).
- **Tests:** unit tests for the extractor and checker against brief
  fixtures reproducing the FR-789 failure (nonexistent fixture path) and
  the FR-791 overrun (3+ live smokes); a shell-level test that a doomed
  brief exits 64 without spawning the backend.

## Acceptance Criteria

- [ ] AC-01: A brief referencing a nonexistent workspace path exits 64 before the copilot CLI is spawned, quoting the violated premise (reproduces FR-789 run 1 class).
- [ ] AC-02: A brief whose validation plan names 3+ live `graph run` smokes prints a 900s-ceiling warning (reproduces FR-791 run 1 class) and still proceeds.
- [ ] AC-03: A clean brief (FR-790/792 class) passes pre-flight with all premises ✓ and no behavior change to the route (sentinel, report gate, exit codes intact).
- [ ] AC-04: `--no-preflight` skips only the pre-flight; report-gate verification remains mandatory.
- [ ] AC-05: Pre-flight logic unit-tested with req markers; no LLM call in the pre-flight path.
- [ ] AC-06: `.github/skills/graph-authoring/` docs updated: brief-writing guidance names the checked premise forms so authors write checkable briefs.

## Alternatives Considered

- **Keep the manual dry-run heuristic:** worked for FR-790/791/792 but is memory-dependent diligence; the failure evidence shows it fires only after a first strike per session.
- **LLM-judged brief review:** higher recall on prose premises, but adds cost/latency/nondeterminism to every launch; the three observed failures were all mechanically detectable.
- **Post-hoc only (better report-gate diagnostics):** cheaper to build but pays after the run — the whole point is moving the check before the spend.

## Related

- FR-767 (sentinel-armed sole route — pre-flight slots in front of the same launch path)
- FR-789 (run 1 premise death — AC-01's reproduction), FR-791 (run 1 ceiling timeout — AC-02's reproduction)
- Scripture: `two_strike_split` (third strike → code), FR-789 diary "the brief is code"

**Prior art:** No existing FR touches author.sh launch-time validation. FR-767 established the route and its report gate; this adds a symmetric gate at the entry boundary (`the_one_law`: normalize where external data — the brief — enters).
