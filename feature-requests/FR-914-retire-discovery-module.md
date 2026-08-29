# Feature Request: Retire `yamlgraph/discovery.py` and make the `is_this_a_graph` cure executable

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-29
**First consumer / first event:** every agent session at the
`is_this_a_graph` moment — the first event is the next time an agent hits
"for each item, ask the model" and follows the Scripture's instruction to
"consult the graph list". Today that instruction names a command that has
not existed since 2026-01-29. The agent gets `invalid choice: 'list'` and
falls through to the scripts/subagents the cure exists to prevent.
**Research:** in-body dispositioned alternatives table below (FR-889 style),
grounded in the mechanical evidence table under Problem — every row was
verified in a worktree at HEAD on 2026-08-29 and is reproducible by the
command shown.
**Prior art:** FR-909/FR-910 (the retirements that orphaned this module — this
FR is their named follow-up, flagged in both PR bodies); FR-853 (graduated
`is_this_a_graph` into Scripture citing both now-dead routes); FR-208 (created
`discovery.py` by extraction); FR-717 (moved the MCP server that consumed it);
FR-465/FR-466/CAP-163 (CAP retirement mechanism — followed, not duplicated);
CAP-169 (retired-CAP file format); concurrent siblings FR-912 (retire skill
export) and FR-913 (retire `graph bench`) — same pruning arc, disjoint
surfaces.

## Summary

Delete `yamlgraph/discovery.py`, retire REQ-YG-206, and replace the
Scripture's phantom `yamlgraph graph list` instruction with a one-line
`rg` command that works today. Zero new code.

## Value Statement

The `is_this_a_graph` cure stops being an instruction to run a command that
does not exist, and the repo sheds a 250-line module with no production
consumer — closing the loop FR-909 and FR-910 opened.

## Ideal Result

An agent that reaches the `is_this_a_graph` moment runs exactly one command
from the Scripture, sees the six indexed graphs with their `Task shapes:`
clauses, and names the matching graph or its absence — without a framework
module, a protocol server, or a CLI subcommand standing between the
question and the answer. `grep -ri discovery yamlgraph/` returns nothing but
an unrelated docstring in `storage/simple_redis.py`; CAP-111 no longer
claims a discovery requirement; the suite and `req_coverage.py --strict`
are green.

## Problem

FR-910's judgement froze **C-3: "Do not delete `yamlgraph/discovery.py`; the
cited research says shared discovery stays because it is CLI-consumed."**
Enforcement was the first moment anyone checked that claim. It is false, and
the surrounding facts are worse than a single stale premise.

| # | Claim | Reality (verified at HEAD, 2026-08-29) | Command |
|---|---|---|---|
| E-1 | `discovery.py` is CLI-consumed | Zero in-package consumers. The only hit outside the module is an unrelated docstring in `storage/simple_redis.py` ("SCAN for key discovery") | `git grep -n 'discovery\|discover_graphs\|DEFAULT_GRAPH_PATTERNS' -- 'yamlgraph/**/*.py'` |
| E-2 | `yamlgraph graph list` is the CLI route | **The command does not exist.** Removed 2026-01-29 in `63d0be8d` "remove graph list command (dead code)" — it was hardcoded to a `graphs/` dir that FR-013 had reorganised away | `yamlgraph graph --help` → `{run,info,validate,lint,codegen,bench,export}` |
| E-3 | The Scripture's cure names a live route | `is_this_a_graph` cited "MCP `yamlgraph_list_graphs` / `yamlgraph graph list`". MCP registration broke 2026-07-18 (FR-717 PR2, retired by FR-910); the CLI command died 2026-01-29. **Both routes were already dead when FR-853 graduated the cure** | `.github/copilot-instructions.md:133` |
| E-4 | `CLAUDE.md` documents a working CLI | Line 150 still advertises `yamlgraph graph list` under "Running Examples" — seven months stale | `rg -n 'graph list' CLAUDE.md` |
| E-5 | Only `discovery.py` can surface the index | The full `Task shapes:` payload is one `rg` away, and returns exactly the six graphs FR-853 froze | `rg -n 'Task shapes:' examples/demos/*/graph.yaml` |
| E-6 | `vulture` is satisfied | `discover_graphs` and `DEFAULT_GRAPH_PATTERNS` are reported dead; FR-910 whitelisted them under protest because C-3 forbade deletion | `python -m vulture yamlgraph vulture_whitelist.py` |

The compound failure is the point. FR-853 graduated a cure into Scripture in
July, citing two routes to a graph list. Neither worked. The recurrence that
justified the graduation — the operator having to point out on 2026-08-22
that parallel haiku analysis was table stakes via the map node — happened
**while the cure was unexecutable**. We have never tested a working cure; we
have tested its absence twice and it failed twice.

Meanwhile `discovery.py` is an implementation in search of a consumer. It was
extracted for two protocol servers (FR-208), both now retired. Keeping it
"because the CLI uses it" describes a CLI that has not existed since January.

## Ideal-Result Backwards: what is the minimal path?

The ideal is *the agent gets the list*. The list is six lines of YAML
`description:` text. The minimal path from ideal to today is a `rg`
invocation. Every other path — restore the CLI command, keep the module,
build a registry — adds machinery between a question and an answer that is
already one grep away.

## Proposed Solution

1. **Doctrine** (enforcement-infrastructure; isolated commit + human
   approval, per the FR-910 C-2 precedent): rewrite the route clause in
   `.github/copilot-instructions.md` `is_this_a_graph` from
   "consult the graph list (`yamlgraph graph list`)" to
   `` consult the index (`rg -n 'Task shapes:' examples/demos/*/graph.yaml`) ``.
   No other part of the entry changes — the moment, the graduation record,
   and the `first_person_tool_horizon` note all stand.
2. **Docs**: delete the `yamlgraph graph list` block from `CLAUDE.md`
   (~line 150).
3. **Code**: delete `yamlgraph/discovery.py`; remove its two entries from
   `vulture_whitelist.py` (added by FR-910 under C-3 protest); remove
   `yamlgraph.discovery` from the `.importlinter` layer list and the
   `fsm-contrib-ownership` source-module list.
4. **Tests**: delete `tests/unit/test_discovery.py`; retarget the two
   surviving discovery consumers to the grep surface —
   `tests/unit/test_fr853_task_shapes_index.py` asserts the six indexed
   graphs carry `Task shapes:` **by reading the YAML directly**, and
   `tests/unit/test_fr796_watcher2_witness_curation.py` asserts witness
   curation against the same glob. Both keep their FR's intent; neither
   keeps its import.
5. **Registry**: CAP-111 loses REQ-YG-206 (adopted there by FR-909 for
   exactly this module) and reverts to its FR-255 single-requirement shape;
   REQ-YG-206 is retired. CAP-19 and CAP-81 already carry it in their
   retired historical records.
6. **Changelog**: fragment `type: removal`.

**Boundary:** this FR does NOT restore a `graph list` command, does not
touch `yamlgraph/export/`, `graph_loader.invoke_graph` (REQ-YG-258 stays),
the skill exporter (FR-912's surface), `graph bench` (FR-913's surface), or
any authoring/judge/review adapter script.

## Acceptance Criteria

- [ ] AC-01: `test ! -e yamlgraph/discovery.py`, and `git grep -n 'yamlgraph\.discovery\|discover_graphs\|DEFAULT_GRAPH_PATTERNS' -- yamlgraph tests scripts` returns no matches
- [ ] AC-02: `.github/copilot-instructions.md` `is_this_a_graph` contains no `yamlgraph graph list` and no `yamlgraph_list_graphs`; the command it does name executes successfully from the repo root and prints ≥ 6 lines
- [ ] AC-03: the doctrine edit is its own commit, and the PR body flags it for human approval (FR-910 C-2 precedent)
- [ ] AC-04: `rg -n 'graph list' CLAUDE.md README.md reference/cli.md` returns no matches
- [ ] AC-05: `vulture_whitelist.py` contains no `discover_graphs` / `DEFAULT_GRAPH_PATTERNS` entry and `python -m vulture yamlgraph vulture_whitelist.py` exits 0
- [ ] AC-06: `.importlinter` contains no `yamlgraph.discovery`; `lint-imports` reports all contracts kept
- [ ] AC-07: `tests/unit/test_discovery.py` is deleted; `test_fr853_task_shapes_index.py` and `test_fr796_watcher2_witness_curation.py` pass without importing `yamlgraph.discovery`, and still fail if a `Task shapes:` clause is removed from an indexed graph (mutation-checked, not just green)
- [ ] AC-08: CAP-111 declares only REQ-YG-258; REQ-YG-206 appears in no active capability; `python scripts/validate_capabilities.py` and `python scripts/req_coverage.py --strict` pass
- [ ] AC-09: full unit suite passes; `python scripts/direct_import_scan.py --strict` passes
- [ ] AC-10: changelog fragment under `changelog/unreleased/` with `type: removal` naming FR-914

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| **Restore `yamlgraph graph list` on top of `discovery.py`** (give the orphan its consumer; ~40 lines of Layer-1 presentation) | **REFUTED, with a named revival trigger.** It is the additive default wearing a rescue costume: the module would get a job invented for it rather than a demanded one. The list's entire payload is one `rg` away (E-5). *Trigger:* if an agent misses the instrument index a **third** time with an executable grep clause in place, that is the witnessed need — build the command then, for evidence rather than hypothesis. |
| Keep `discovery.py`, fix only the doctrine text | REFUTED — leaves a 250-line module with zero consumers and two vulture suppressions. `growth_as_default`: the phantom claim survives because nobody checks it, which is exactly how it survived four months already. |
| Keep C-3 as written and do nothing | REFUTED — C-3's premise is factually false (E-1, E-2). A gate binds; a stale reason does not deserve permanent tenure. This FR is the disposition FR-910 explicitly deferred. |
| Delete `discovery.py` and drop the graph-list clause from Scripture entirely | REFUTED — throws out FR-853's twice-witnessed cure along with its broken plumbing. The cure's *moment* is sound; only its *route* was phantom. |
| Fold this into FR-910's PR | REFUTED — C-3 is a GATE in a frozen judgement. Overriding it inside the PR it constrains is exactly the silent scope expansion the gate exists to prevent. |

## Related

- Orphaning FRs: FR-909 (A2A retirement, PR #491), FR-910 (MCP retirement, PR #492) — this FR is named as the follow-up in both PR bodies
- Cure origin: FR-853 (`is_this_a_graph` graduation); diary witness `builders_never_call` (2026-07-17); recurrence 2026-08-22
- Module origin: FR-208 (extraction for the A2A/MCP servers), FR-717 (export seam move)
- Retirement mechanism: FR-465/FR-466, CAP-163, CAP-169
- Concurrent pruning arc: FR-912 (skill export), FR-913 (`graph bench`)
- Enforcement diary: `docs/diary/diary-2026-08-29-the-requirement-that-survived-its-capability.md` (`retirement_orphans_the_tenant`, `gate_premise_may_be_stale`)

## Judgement (pending)

Not yet judged. Route: `scripts/judge.sh feature-requests/FR-914-retire-discovery-module.md`,
in a session other than this one.
