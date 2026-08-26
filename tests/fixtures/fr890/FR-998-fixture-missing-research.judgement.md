# Judgement: FR-998 Colorize CLI graph list output

**Verdict:** REJECTED — the proposal receives no implementation authority because this post-activation FR has no `**Research:**` field or committed research record, and it also targets a stale/nonexistent CLI surface.

**Reviewed against:** `tests/fixtures/fr890/FR-998-fixture-missing-research.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; cited `yamlgraph/cli.py` path from the FR, which is absent in this worktree; current CLI surfaces `yamlgraph/cli/__init__.py` and `yamlgraph/cli/graph_commands.py`.

## What is sound

The user pain is concrete and modest: the first consumer/event is a developer scanning `yamlgraph graph list` when output exceeds one screen (`tests/fixtures/fr890/FR-998-fixture-missing-research.md:8-9`), and the problem statement names the specific readability boundary between graph names and descriptions (`tests/fixtures/fr890/FR-998-fixture-missing-research.md:24-27`). The ideal result preserves a machine-safe escape hatch by requiring `--no-color` and non-TTY suppression (`tests/fixtures/fr890/FR-998-fixture-missing-research.md:29-33`). The proposed dependency posture is appropriately small: it rejects a new `rich`/`textual` dependency in favor of stdlib ANSI output (`tests/fixtures/fr890/FR-998-fixture-missing-research.md:35-38`, `tests/fixtures/fr890/FR-998-fixture-missing-research.md:46-48`).

Strategically, this is a CLI UX improvement, not a framework primitive: it has one named consumer/event and no evidence of broader graph-runtime leverage (`tests/fixtures/fr890/FR-998-fixture-missing-research.md:8-9`, `.github/skills/judge-fr/doctrine.md:51-57`).

## Required revisions

### R-1: Add committed research evidence before re-entry

Add a `**Research:**` field pointing to a committed research record, normally `feature-requests/FR-998.research.md`, or embed an equivalent committed dispositioned alternatives table. The evidence must satisfy the repo-local research rule: genuine solution classes, precedent lines, preserved disagreement, and an explicit `is_this_a_graph` answer (`.github/skills/judge-fr/doctrine.md:118-130`). The current FR intentionally lacks that field (`tests/fixtures/fr890/FR-998-fixture-missing-research.md:11-13`), so the doctrine grants no authority (`.github/skills/judge-fr/doctrine.md:118-121`).

### R-2: Correct the target CLI surface

Replace the stale `yamlgraph/cli.py` reference with the actual command surface, or revise the FR to explicitly authorize adding the missing command. The cited related path is `yamlgraph/cli.py` (`tests/fixtures/fr890/FR-998-fixture-missing-research.md:50-52`), but the current CLI is a package whose parser declares `graph run`, `info`, `validate`, `lint`, `codegen`, `bench`, and `export`, with no `list` subparser in the inspected command block (`yamlgraph/cli/__init__.py:47-260`). Dispatch likewise handles only those graph commands and falls through to "Unknown graph command" otherwise (`yamlgraph/cli/graph_commands.py:319-341`). As written, the FR cannot be enforced as a pure colorization wrapper around an existing `yamlgraph graph list` command.

### R-3: Make acceptance criteria mechanically testable

Rewrite the acceptance criteria into assertions that can be implemented as tests: parser behavior for the chosen command/flag, TTY color output, non-TTY byte identity, and `--no-color` byte identity. The current criteria say "Tests added" without specifying the asserted surface (`tests/fixtures/fr890/FR-998-fixture-missing-research.md:40-45`), while the judge rubric requires every criterion to be mechanically checkable and directly testable (`.github/skills/judge-fr/doctrine.md:43-44`, `.github/skills/judge-fr/doctrine.md:58-61`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | No implementation deliverable is authorized under this FR. |

Not authorized: ANSI color changes, parser changes, a new `graph list` command, dependency additions, broad CLI formatting rewrites, changes to graph discovery semantics, or updates outside the corrected CLI/test surfaces. If the command itself must be added, that is either a revised FR with explicit scope or a separate FR; this draft does not grant that authority.

## Revised acceptance criteria

- [ ] AC-01: The revised FR contains a `**Research:**` field referencing a committed research record or an embedded dispositioned alternatives table that satisfies `.github/skills/judge-fr/doctrine.md:118-130`.
- [ ] AC-02: The revised FR names the actual implementation surface and distinguishes "colorize existing command" from "add a missing `graph list` command."
- [ ] AC-03: The revised FR specifies a test that simulates TTY stdout and asserts graph names render cyan and descriptions render dim.
- [ ] AC-04: The revised FR specifies a test that captures non-TTY output and asserts it is byte-identical to the current uncolored output.
- [ ] AC-05: The revised FR specifies a test that passes `--no-color` and asserts byte-identical uncolored output even when stdout is a TTY.
- [ ] AC-06: The revised FR preserves the no-new-dependency constraint unless research justifies a dependency and the acceptance criteria cover the resulting behavior.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement anything from this FR until the missing committed research evidence is folded into the FR and independently judged. | GATE |
| C-2 | Do not implement against `yamlgraph/cli.py`; the path cited by the FR is stale/absent and must be corrected before enforcement. | GATE |
| C-3 | Do not silently expand scope from colorizing an existing list command into adding a new command without explicit revised scope and tests. | GATE |

Authority granted: none; this FR must return to planning/research before any implementation may begin.
