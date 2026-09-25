# Feature Request: The graph-authoring guard governs every graph under `examples/`, whatever its file name

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-25
**First consumer / first event:** the first edit to
`examples/demos/innovation_matrix/pipeline.yaml` under
[FR-1088](FR-1088-innovation-matrix-repair.md). FR-1088 records that the
PreToolUse guard does not match that file, so its sole route "is held by
doctrine, not by the hook"
([FR-1088#L110-L115](FR-1088-innovation-matrix-repair.md#L110-L115)). A probe
on 2026-09-25 (Problem, finding 3) shows an unsentineled `create_file` on
that path is approved today.
**Research:** FR-890 research route **skipped by operator decision
(2026-09-25)** for this batch. Substitute: the in-body Alternatives
Considered below (six solution classes, one chosen, one preserved dissent,
each dispositioned, plus an `is_this_a_graph` answer), in the form
FR-1084 uses; plus the census and hook probe in Problem, both run on
2026-09-25 against `main` at `82733de3`.
**Prior art:**
[FR-767](FR-767-graph-authoring-sole-route.md) (Implemented). Created the
guard. Its C-4 is "path-based materiality" and its R-2 forbids a "semantic
classifier in the hook"
([FR-767#L341](FR-767-graph-authoring-sole-route.md#L341),
[#L360](FR-767-graph-authoring-sole-route.md#L360)). This FR keeps the R-2
bright line (every unsentineled write to a governed artifact is denied,
material or not) and changes only which files are governed artifacts: for
editor tools under `examples/`, a file with a top-level `nodes:` key is a
graph whatever its name. That is a one-line text predicate on the artifact,
not a judgement about the edit. The judge must rule whether C-4 allows it;
if not, the preserved dissent (class 1) is the fallback.
[FR-1014](FR-1014-dir-aware-authoring-guard.md) (Enforced). Widened the
`graphs/` arms and kept the `examples/` arms byte-identical
([FR-1014#L187](FR-1014-dir-aware-authoring-guard.md#L187)). This FR changes
only the `examples/` arms. FR-1014's truth-table negatives
(`graphs/<name>/nested/…`, depth > 1) stay approved.
[FR-1011](FR-1011-relocate-chaplain-live-parts.md). Moved the chaplain
graphs into `graphs/<name>/` and removed the `.chaplain` arm. No overlap.
[FR-765](FR-765-graph-authoring-workflow-skill.md). Created the route this
guard holds. Unchanged.
[FR-888](FR-888-main-write-guard-worktree-route.md) / FR-889. Check 7 decides
*where* writes may go; this FR is about *what* is a governed artifact.
Separate check, unchanged.
[FR-927](FR-927-retire-fr902-lane-guard-hooks.md) (Enforced). Retired the
FR-902 lane guard after operator review. Taken as a warning about
false-positive cost: this FR bounds its false positives (terminal arm only)
and names them (H-1).
[FR-1070](FR-1070-innovation-matrix-repair.md) (REJECTED). The FR whose
refile (FR-1088) found this gap. It was rejected for missing research and
grid bound; nothing about the guard. No precedent against this FR.
[FR-1013](FR-1013-chaplain-doctrine-sweep.md) (REJECTED). Rejected because
the process became the deliverable. Taken as a size limit: the fix stays
inside the three predicate surfaces plus their docs.
[FR-1093](FR-1093-authoring-guard-read-only-commands.md) (Withdrawn). Its
read-route denial hint is folded in here as Proposed Solution item 8; its
Problem and census stay in that file as the evidence.
A search of `feature-requests/` for `pre-command-guard`, `governed_path` and
`author.sh` found no REJECTED FR that proposed or refused widening the
governed set.
**Enforcement infrastructure:** this FR changes
`.github/hooks/scripts/pre-command-guard.sh`, a commit backstop and a
pre-commit selector. Per Scripture `instruction_boundary_uncrossed` and
`guard_widening_when_caught`, no guard edit happens before this FR is
judged through `scripts/judge.sh`, and the implementation PR is reviewed as
adversarial input: `scripts/review.sh` plus a human review before merge
(FR-767 C-1 carries over).

## Summary

The FR-767 guard decides "is this a graph?" by file name. 82 tracked graphs
under `examples/` have other names and are not governed; neither are 22
prompts in nested `prompts/<sub>/` folders. This FR makes the editor-tool
arm govern any `examples/**/*.ya?ml` whose content has a top-level `nodes:`
key, makes the terminal arm govern every `examples/**/*.ya?ml` destination
(content cannot be known before a shell write), widens the prompt arm to any
depth under `prompts/`, and makes the commit backstop apply the same rule to
staged content.

## Value Statement

An agent editing `pipeline.yaml`, `turn.yaml` or `worldgen.yaml` gets the
same sole-route denial as for `graph.yaml`, so FR-1088 and every later
graph repair is held by the hook, not by the agent's reading of doctrine.

## Problem

1. **The guard matches names.** `governed_path()`
   ([pre-command-guard.sh#L165-L173](../.github/hooks/scripts/pre-command-guard.sh#L165-L173))
   governs `examples/**/graph.ya?ml`, `examples/**/prompts/*.ya?ml` (one
   level only: `[^/]+`), `graphs/*.ya?ml`, `graphs/<name>/*.ya?ml` and
   `graphs/<name>/prompts/*.ya?ml`. The commit backstop has the same five
   patterns
   ([check_authoring_proof.py#L22-L28](../scripts/check_authoring_proof.py#L22-L28)).
   The README says the three surfaces must agree
   ([README.md#L84-L92](../.github/hooks/README.md#L84-L92)).
2. **Census, 2026-09-25, `main` at `82733de3`, tracked files only.**
   `examples/` holds 718 tracked YAML files (`.yml`: 0).
   | Class | Count | Governed today |
   |---|---:|---|
   | `graph.yaml` | 116 | yes |
   | `prompts/*.yaml` (direct) | 306 | yes |
   | other names with top-level `nodes:` | 82 | **no** |
   | nested `prompts/<sub>/*.yaml` | 22 | **no** |
   | other YAML, no top-level `nodes:` | 192 | no (correct) |

   All 82 also have a top-level `edges:` key: they are graphs, not fragments.
   Examples: `examples/demos/innovation_matrix/pipeline.yaml` and
   `drill-down.yaml`, `interrupt-child.yaml` in both
   `examples/demos/interrupt/subgraphs/` and
   `examples/demos/subgraph/subgraphs/`, `examples/novel_fandom/worldgen.yaml`,
   `examples/dungeon_master/turn.yaml`, `examples/npc/encounter-turn.yaml`,
   `examples/ebook/graph-ch00.yaml`. The 22 nested prompts are real prompts
   loaded by path, e.g. `prompt: chapter/introduction`
   (`examples/ebook/graph-ch00.yaml#L17`); folders:
   `examples/ebook/prompts/{chapter,amend,judge}`,
   `examples/plot_modeller/prompts/{interiority,roundtrip}`.
   None of the 192 other files has a top-level `nodes:`. Five
   `examples/yamlgraph_gen/snippets/` files come close: two have a top-level
   `edges:` only (`snippets/edges/conditional.yaml`, `linear.yaml`), three
   have an indented `nodes:` (`snippets/nodes/*.yaml`). 11 tracked paths
   contain spaces (`examples/novel_fandom/canon seed/…`).
   The operator's earlier count (83 and 133) came from the main checkout's
   working tree: the 83rd file,
   `examples/yamlgraph_gen/outputs/map-test-v3/test-map-demo.yaml`, and 17
   of the 133 `graph.yaml` files are untracked there.
3. **Probe, 2026-09-25.** Payloads piped into the guard with no sentinel
   (audit log redirected to `tmp/`):
   | Payload | Decision |
   |---|---|
   | `create_file` `examples/demos/innovation_matrix/pipeline.yaml` | approve |
   | `replace_string_in_file` `examples/dungeon_master/turn.yaml` | approve |
   | `create_file` `examples/ebook/prompts/chapter/wizard.yaml` | approve |
   | `cp …/innovation_matrix/drill-down.yaml …/innovation_matrix/pipeline.yaml` | approve |
   | `echo nodes: > examples/demos/innovation_matrix/pipeline.yaml` | approve |
   | `cp examples/demos/hello/graph.yaml …/innovation_matrix/pipeline.yaml` | deny, by accident |
   | control: `create_file` `examples/demos/zodiac/graph.yaml` | deny |

   The accidental deny: the copy branch joins the *source* basename onto a
   file destination (`…/pipeline.yaml/graph.yaml`) and that string matches
   the `graph.yaml` arm
   ([pre-command-guard.sh#L219-L222](../.github/hooks/scripts/pre-command-guard.sh#L219-L222)).
   A source with any other name passes. Directory copies are checked only
   for `graph.yaml` and direct `prompts/*.yaml`
   ([#L227-L232](../.github/hooks/scripts/pre-command-guard.sh#L227-L232)),
   so `cp -r` of a folder holding only `pipeline.yaml` passes too.
4. **Doctrine names the files too.** The graph-authoring doctrine binds on
   "the **artifact class, not the task phrasing**" and defines the class as
   "a `graph.yaml` or `prompts/*.yaml`"
   ([doctrine.md#L11-L13](../.github/skills/graph-authoring/doctrine.md#L11-L13)).
   `.github/copilot-instructions.md` line 13 says the same. So the doctrine
   does not say "not the file name"; FR-1088's reading (that doctrine covers
   `pipeline.yaml`) is an inference from the word "class". Hook and doctrine
   agree with each other, and both miss the 82 files.
5. **A content precedent exists in the same hook family.** The PostToolUse
   `yaml-checks.sh` treats a file as a graph when its parsed top level has
   `nodes` and `edges`
   ([yaml-checks.sh#L25-L37](../.github/hooks/scripts/checks/yaml-checks.sh#L25-L37)).
   It parses with PyYAML and swallows every error (`2>/dev/null || true`,
   [#L35](../.github/hooks/scripts/checks/yaml-checks.sh#L35)): fail-open,
   acceptable for an advisory post-edit lint, not for a PreToolUse deny
   (FR-767 C-5). The guard needs a predicate that cannot fail open.
6. **Tests.** [test_authoring_guard.py](../.github/hooks/tests/test_authoring_guard.py)
   covers the four editor tools on `examples/demos/zodiac/graph.yaml`
   (#L123-L137), the governed-path list plus the FR-1014 `graphs/` positives
   (#L140-L154), FR-1014 negatives (#L155-L161), tracked-artifact deny
   (#L163-L168), ungoverned approves (#L170-L181), eight terminal write
   shapes (#L186-L204), read/lint/git approves (#L206-L224), sentinel
   allow/deny cases (#L227-L276) and ambiguous-shape deny (#L278-L279). No case
   uses a graph with another name, a nested prompt, or file content.
   Markers: FR-767 tests carry REQ-YG-527
   ([#L29](../.github/hooks/tests/test_authoring_guard.py#L29)), which is
   CAP-192's branch-deny guidance
   ([ARCHITECTURE.md#L2495](../ARCHITECTURE.md#L2495)), not this guard; the
   FR-1014 tests carry REQ-YG-423 (CAP-158), whose row names
   `governed_path()` and the backstop
   ([ARCHITECTURE.md#L2123](../ARCHITECTURE.md#L2123)). REQ-YG-423 is the
   requirement this FR extends.

## Ideal Result

A write that creates or changes a graph or prompt under `examples/`,
through any tool, is denied without an armed authoring sentinel, whatever
the file is called. A write to a YAML file under `examples/` that is not a
graph and not a prompt is approved through the editor tools. The guard, the
commit backstop and the pre-commit selector give the same answer on one
shared truth table, and a corpus test keeps that true as files are added.

## Proposed Solution

All changes are inside the three predicate surfaces, their tests and their
docs. `graphs/` arms are unchanged.

1. **Graph predicate (one definition).** `is_graph_text(text)`: the text has
   a line matching `^["']?nodes["']?[ \t]*:` (a top-level `nodes` key). A
   plain regex, no YAML import, so it cannot fail open. `nodes:` alone is
   the stricter choice; on the tracked corpus it selects exactly the same
   82 files as `nodes:`+`edges:`. It does not match the indented snippets.
2. **Prompt arm depth.** For `examples/` only, the prompt pattern becomes
   `examples/.+/prompts/.+\.ya?ml$` (any depth under `prompts/`). Governs
   the 22 nested prompts. FR-1014's `graphs/<name>/prompts/` depth rule is
   untouched.
3. **Editor tools** (`create_file`, `replace_string_in_file`,
   `multi_replace_string_in_file`, `apply_patch`). A path is governed when
   `governed_path()` is true, or when it is under `examples/`, ends in
   `.ya?ml`, and any of these is a graph text:
   - the file on disk (if it exists);
   - the incoming text: `content`, `newString`, each `replacements[].newString`,
     or the `+` lines of the patch for that path.

   The first catches edits to existing graphs; the second catches new graphs
   and a non-graph file turned into one. A file that exists but cannot be
   read (not a regular file, permission, decode error) is governed: deny
   (C-5).
4. **Terminal** (`run_in_terminal`, `send_to_terminal`). A shell write can
   put any bytes into a file, and the target may not exist yet, so content
   cannot be checked before the write. Every write shape the guard already
   parses (redirect, `tee`, `sed -i`, `cp`/`mv`/`rsync`/`install`, inline
   writers) whose destination is `examples/**/*.ya?ml` is denied without a
   sentinel. Directory copies into `examples/` are denied when the source
   holds any `*.ya?ml`. Reads, lint and git stay approved. This replaces the
   accidental basename-join deny with an explicit rule. The false positive
   is a data YAML written into `examples/` from the shell (H-1); the denial
   text says to use an editor tool, which checks content.
5. **Commit backstop.** `check_authoring_proof.py` treats a staged new file
   as governed when `GOVERNED` matches, or when it is under `examples/`,
   ends in `.ya?ml`, and its staged blob (`git show :<path>`) is a graph
   text. The `authoring-proof` selector in `.pre-commit-config.yaml` becomes
   `^examples/.*\.ya?ml$|…` so the script runs for those files.
6. **Truth table.** The shared table
   (`tests/unit/test_fr1014_authoring_proof_dir_graphs.py`, or a sibling
   `test_fr1092_*` file importing it) gains `(path, content, provenance,
   expected)` rows. Guard and backstop must agree on every row.
7. **Docs and denial text.** README contract row and section, the Check 6
   header comment
   ([pre-command-guard.sh#L142-L147](../.github/hooks/scripts/pre-command-guard.sh#L142-L147))
   and the denial message
   ([#L269](../.github/hooks/scripts/pre-command-guard.sh#L269)) name the
   content rule and the terminal rule. The doctrine sentence
   ([doctrine.md#L11-L13](../.github/skills/graph-authoring/doctrine.md#L11-L13))
   says "a graph (any YAML with a top-level `nodes:` key) or a prompt".
   `.github/copilot-instructions.md` is not edited.
8. **Read-route hint (from FR-1093).** When the reason is the catch-all
   "unrecognized write shape … (fail closed)", the denial also says:
   read-only? use the editor's read/search tools, `yamlgraph graph lint
   <path>`, or a script under `tmp/` run as `python tmp/<name>.py`; writes
   still go through `scripts/author.sh`. Other reasons keep today's text.
   No allow/deny decision changes. Evidence: FR-1093 Problem §2 (26 agent
   false positives, 0 prevented writes among the 11 recovered).

## Acceptance Criteria

All new tests carry `@pytest.mark.req("REQ-YG-423")`. RED is committed
before any guard edit (Commandment 7).

- [ ] AC-01 (RED): without a sentinel, the guard denies, naming
  `author.sh`: `create_file` and `replace_string_in_file` on
  `examples/demos/innovation_matrix/pipeline.yaml` (tracked, graph on disk);
  `replace_string_in_file` on `examples/dungeon_master/turn.yaml`;
  `create_file` on synthetic `examples/demos/fr1092-synthetic/flow.yaml`
  with content holding a top-level `nodes:`; `apply_patch` `Add File` of the
  same path with a `+nodes:` line; `multi_replace_string_in_file` whose
  `newString` adds a top-level `nodes:` to a synthetic non-graph YAML under
  `examples/`.
- [ ] AC-02 (RED): `create_file` on
  `examples/ebook/prompts/chapter/wizard.yaml` is denied.
- [ ] AC-03 (RED): terminal, no sentinel, denied:
  `cp examples/demos/innovation_matrix/drill-down.yaml examples/demos/innovation_matrix/pipeline.yaml`;
  `echo nodes: > examples/demos/innovation_matrix/pipeline.yaml`;
  `cp -r` of a `tmp_path` folder holding only `pipeline.yaml` into
  `examples/demos/`. Still approved: `cat` and
  `yamlgraph graph lint examples/demos/innovation_matrix/pipeline.yaml`, and
  git operations on that path.
- [ ] AC-04 (no false positive): approved without a sentinel:
  `create_file` on `examples/cwe-classifier/data/fixture_catalog.yaml` with
  non-graph content; `replace_string_in_file` on
  `examples/dependency-taxonomy.yaml`; `create_file` on
  `examples/yamlgraph_gen/snippets/nodes/python-tool.yaml` with its current
  (indented `nodes:`) content. The existing FR-1014 negatives and
  `test_approve_ungoverned_yaml` stay green.
- [ ] AC-05: an armed sentinel allows every AC-01..AC-03 payload.
- [ ] AC-06 (fail closed): a path under `examples/` ending in `.yaml` that
  exists but cannot be read as text (a directory named `x.yaml` in
  `tmp_path`) is denied.
- [ ] AC-07 (backstop): with a staged new
  `examples/demos/fr1092-synthetic/flow.yaml` holding a top-level `nodes:`
  and no report entry, `check_authoring_proof.py` exits 1 and names it; a
  staged new data YAML exits 0; a staged new nested prompt exits 1. The
  selector test matches every truth-table row.
- [ ] AC-08 (corpus witness): a unit test walks `git ls-files` YAML under
  `examples/` and asserts: every file with a top-level `nodes:` and every
  file under `prompts/` at any depth is governed by the editor-tool
  predicate and by the backstop; no other file is. It asserts the property,
  not today's counts, so new files are held to it.
- [ ] AC-09: `.github/hooks/README.md` contract row
  ([#L80](../.github/hooks/README.md#L80)) and section (#L82-L92), the Check
  6 comment, the denial text, the `doctrine.md` sentence, the REQ-YG-423
  row in `ARCHITECTURE.md` and `capabilities/CAP-158-copilot-skill-promotion.yaml`
  describe the content rule and the terminal rule.
  `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: changelog fragment in `changelog/unreleased/`
  (`type: fix`, `scope: hooks`, `req: REQ-YG-423`); FR implementation record;
  diary entry.
- [ ] AC-11: the PR is reviewed through `scripts/review.sh` and by a human
  before merge. The diff touches no check other than Check 6 and no file
  other than those named in this FR.
- [ ] AC-12 (RED): the `load_and_compile` `python -c` probe from FR-1093's
  First-consumer line is still denied, and its output names `tmp/` and
  `yamlgraph graph lint`. A redirect onto a governed path produces the same
  denial text as today, with no read-route line.

## Alternatives Considered

Solution classes (chosen: 2):

1. **Path-wide for every tool: all `examples/**/*.ya?ml` governed.**
   **Preserved dissent.** One rule on both surfaces, no content read,
   plainly inside FR-767 C-4. It loses because it puts 192 data files
   (CWE labels, novel canon, fixtures) behind the sentinel for editor edits
   too. Adding an exclusion list to fix that is `regex_fourth_exclusion`. If
   the judge rules that C-4 forbids reading content, this class is the
   fallback, with the false positives named.
2. **Content for editor tools, path for the terminal.** **Chosen.** The
   editor payload carries the text or the file exists, so the guard can ask
   "is it a graph?" with one regex that cannot fail open. The terminal
   cannot be asked that before the write, so it takes the path-wide rule on
   a surface where the fix for a false positive (use the editor tool) is
   one step. Precedent: `yaml-checks.sh` already detects graphs by content
   in the same hook family.
3. **Rename the 82 files to `graph.yaml`.** Rejected. Many folders hold
   several graphs (`innovation_matrix/` has two; `examples/demos/subgraph/subgraphs/`
   holds four; `examples/ebook/` has one per chapter), so one name per
   folder needs a folder per graph. `innovation_matrix/pipeline.yaml` alone
   is referenced 29 times outside `tmp/`. It also fixes today's files only:
   the next graph named `flow.yaml` is ungoverned again.
4. **Committed manifest of governed files.** Rejected. A new graph is
   ungoverned until someone lists it, which is the gap this FR closes
   (fail-open for new files, against C-5). It adds a fourth list to the
   three FR-1014 already had to keep in agreement.
5. **Doctrine only (no change).** Rejected. That is the current state.
   Problem finding 4: the doctrine itself names `graph.yaml` and
   `prompts/*.yaml`, so it does not cover `pipeline.yaml` on a plain
   reading. `detection_without_enforcement` and `two_strike_split` apply.
6. **Detect after the write (PostToolUse) and revert.** Rejected. FR-767 C-3:
   prevention lives in PreToolUse; PostToolUse is advisory. A revert after
   the write also races other sessions on a shared tree.

`is_this_a_graph`: no. The guard runs before every tool call and must be
deterministic and fast; a model in an enforcement gate is
`model_as_trusted_peer`. The predicate is one regex, not the "complex regex
logic" the conventions warn about. The census was one `grep`.

## Out of scope

- `graphs/` arms and FR-1014's depth rule. Unchanged.
- Graphs outside `examples/` and `graphs/`: 39 under `tests/`, 4 adapter
  graphs under `.github/skills/*/adapters/`, 2 under `docs/spikes/`, and
  `reference/fr-knowledge-graph.yaml`. Not governed today, not governed by
  this FR (H-4).
- `examples/yamlgraph_gen/snippets/` fragments and its 4 prompt scaffolds
  outside `prompts/` (H-5).
- Graphs written in YAML flow style at the top level (`{nodes: …}`). The
  loader accepts them; the tracked corpus has none. The predicate does not
  match them; stated here as a known limit, not handled.
- Retagging FR-767's hook tests from REQ-YG-527 to REQ-YG-423. Recorded in
  Problem finding 6; not changed by this FR (H-6).
- The `.github/copilot-instructions.md` sentence at line 13 (operator,
  2026-09-25: no Scripture edit).

## Human decisions needed

- **H-1 — terminal false positives.** A shell write of a non-graph YAML into
  `examples/` is denied. Suggested default: accept; the editor tools
  remain and check content.
- **H-2 — nested prompts.** Govern the 22 `prompts/<sub>/*.yaml` files.
  Suggested default: yes.
- **H-3 — doctrine wording.** Decided 2026-09-25 (operator): edit
  `doctrine.md#L11-L13` only; `.github/copilot-instructions.md` is not
  edited.
- **H-4 — graphs outside `examples/`/`graphs/`.** Suggested default: out
  of scope; test fixtures are test code and the adapter graphs are
  enforcement infrastructure under their own review.
- **H-5 — `yamlgraph_gen/snippets/`.** Suggested default: ungoverned
  (fragments, not graphs).
- **H-6 — REQ-YG-527 marker on FR-767 tests.** Suggested default: leave
  for a separate hygiene FR; this FR tags only its own tests.

## Related

- [FR-767](FR-767-graph-authoring-sole-route.md),
  [FR-1014](FR-1014-dir-aware-authoring-guard.md),
  [FR-1088](FR-1088-innovation-matrix-repair.md)
- [pre-command-guard.sh](../.github/hooks/scripts/pre-command-guard.sh),
  [check_authoring_proof.py](../scripts/check_authoring_proof.py),
  [test_authoring_guard.py](../.github/hooks/tests/test_authoring_guard.py),
  [yaml-checks.sh](../.github/hooks/scripts/checks/yaml-checks.sh),
  [README.md](../.github/hooks/README.md)
- CAP-158 / REQ-YG-423
