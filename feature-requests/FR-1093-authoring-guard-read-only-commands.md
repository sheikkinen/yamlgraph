# Feature Request: Name the read-only route in the FR-767 authoring guard's fail-closed denial

**Priority:** LOW
**Type:** Enhancement (enforcement documentation; no change to any allow/deny decision)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-25
**First consumer / first event:** the next agent whose read-only
`python -c "from yamlgraph.compile.graph_loader import load_and_compile; load_and_compile('examples/demos/safety-guards/graph.yaml').compile()"`
is denied with "unrecognized write shape touching governed artifact (fail
closed)". Last occurrence: 2026-09-25T14:40 UTC, a subagent drafting the
FR-1086/FR-1087 refiles in `tmp/worktrees/docs/fr-refiles-1082`. Today that
agent reads "Do not work around this guard — write a task brief and run the
adapter" for a command that writes nothing.
**Research:** FR-890 research route **skipped by operator decision for this
batch (2026-09-25)**. Substitute: the in-body Alternatives Considered below
(six solution classes, one chosen, one preserved dissent, each dispositioned,
`is_this_a_graph` answered), in the form FR-1084 uses; plus the audit-log
census in Problem §2 (run 2026-09-25 against `.github/hooks/logs/audit.jsonl`
on the main checkout).
**Prior art:**
[FR-767](FR-767-graph-authoring-sole-route.md) (Implemented). Owns the guard.
Its judgement C-5: "If the terminal command parser cannot prove a governed
write is safe, it must deny … do not fail open"
([FR-767.judgement#L87](FR-767-graph-authoring-sole-route.judgement.md#L87)).
This FR keeps C-5 as written; no command that is denied today becomes allowed.
[FR-1014](FR-1014-dir-aware-authoring-guard.md) (Enforced). Widened the
governed path set to dir-style `graphs/`; bound the truth table to
REQ-YG-423. This FR touches neither the path set nor the truth table.
[FR-888](FR-888-main-write-guard-worktree-route.md) (Completed) and
[FR-889](FR-889-os-enforced-main-write-lock.md) (Enforced). FR-889 deleted
FR-888's terminal write grammar after 5 review rounds and 14 bypass classes
([FR-889.judgement#L11](FR-889-os-enforced-main-write-lock.judgement.md#L11)),
and forbade reimplementing it "in a smaller form"
([#L102](FR-889-os-enforced-main-write-lock.judgement.md#L102)). That is the
precedent that kills class 2 below. Class 6 (preserved dissent) is FR-889's
cure applied to Check 6.
[FR-1086](FR-1086-lint-compile-check.md) (Proposed). `graph lint --build`
would be a CLI read route for exactly the compile probe above. It needs no
guard change: the guard already approves `yamlgraph graph lint <governed>`
([test_authoring_guard.py#L212-L216](../.github/hooks/tests/test_authoring_guard.py#L212-L216)),
and `--build` adds no token the write-shape regex matches. This FR does not
depend on FR-1086 and does not name `--build` until FR-1086 has merged
(Human decision 2).
[FR-1069](FR-1069-lint-builds-graph.md) (SPLIT). Parent of FR-1086; no
authority.
[FR-442](FR-442-pre-command-guard-parse-consolidation.md) (Implemented).
Consolidated the guard's input parse; no bearing on the decision here.
Plan precedent: [docs/issues-2026-09-24.md §7 I](../docs/issues-2026-09-24.md#L767-L775)
chose **not** to file this FR: "File an FR only if a read-only question cannot
be answered that way." This FR is filed at operator request and agrees with
that conclusion for the guard's decision; it differs only in making the read
route visible where the denied agent reads it.
[Diary 2026-08-15](../docs/diary/diary-2026-08-15-fr790-dry-run-heuristic-pays.md#L34-L39)
weighed the same false positive: "the cost of a false positive is one
re-read".
No REJECTED FR on this guard was found (`grep` of `feature-requests/` for
`pre-command-guard` / `authoring-route` / `authoring guard`, 2026-09-25).

**Enforcement-infrastructure notice.** This FR edits
`.github/hooks/scripts/pre-command-guard.sh` (denial text only) and
`.github/hooks/README.md`. It must be judged via `scripts/judge.sh` before any
edit. Its implementation PR is enforcement output and must be reviewed as
adversarial input (`instruction_boundary_uncrossed`). The session that
drafts it must not implement it (`guard_widening_when_caught`).

## Summary

Keep every decision of the FR-767 guard exactly as it is. Change one thing:
when the guard denies with the catch-all reason "unrecognized write shape
touching governed artifact (fail closed)", the denial text also names the
sanctioned read routes. Record the same routes as a row in
`.github/hooks/README.md`. Witness both with hook tests.

## Value Statement

An agent whose read-only probe is denied learns the sanctioned read route
from the denial itself, instead of being told to run the authoring adapter
for a command that writes nothing.

## Problem

1. **The trigger.** `terminal_reason()`
   ([pre-command-guard.sh#L188-L240](../.github/hooks/scripts/pre-command-guard.sh#L188-L240))
   ends with a catch-all: if any token of the command is a governed path and
   the command matches
   `python3?\s+-c|perl\s+-e|ruby\s+-e|\bopen\(|\.write\(|\bdd\b|\btruncate\b`,
   it returns "unrecognized write shape touching governed artifact (fail
   closed)" ([#L233-L239](../.github/hooks/scripts/pre-command-guard.sh#L233-L239)).
   So `python -c "from yamlgraph.compile.graph_loader import load_and_compile;
   load_and_compile('examples/demos/x/graph.yaml')"` is denied.
   `load_and_compile` is the real entry point
   ([graph_loader.py#L420-L433](../yamlgraph/compile/graph_loader.py#L420-L433)).
   This is FR-767 C-5 working as designed; the test that pins it is
   `test_deny_ambiguous_terminal_write`
   ([test_authoring_guard.py#L276-L284](../.github/hooks/tests/test_authoring_guard.py#L276-L284)).
2. **Measured cost (census, 2026-09-25).** `audit.jsonl` holds **29** deny
   rows with reason `authoring-route` and detail "unrecognized write shape"
   (of 103 `authoring-route` denials in total). No worktree-local audit log
   holds any.
   - 3 of the 29 are hook-test fixtures (session id `s1`, no tool-use id);
     26 are agent calls, across 12 sessions, 2026-08-05 to 2026-09-25.
   - The deny row records only the reason, not the command
     ([pre-command-guard.sh#L268](../.github/hooks/scripts/pre-command-guard.sh#L268)).
     The command was recovered for **11 of 26** by joining the tool-use id
     against VS Code chat transcripts and debug logs; 15 are not recoverable.
   - Of the 11 recovered: **0** would have written a governed artifact.
     **5** write nothing at all: a `python3 -c` JSON read plus a `grep` of a
     graph (2026-08-31), two `python -` heredocs that `yaml.safe_load` prompt
     files (2026-09-20), and two `python -c` compiles of
     `examples/demos/safety-guards/graph.yaml` (2026-09-24T15:26,
     2026-09-25T14:40). **6** write only ungoverned files: two heredocs
     editing an authoring brief under `feature-requests/authoring-briefs/`
     (2026-08-31), two `yamlgraph graph run` of `corpus_census` (2026-09-10;
     the token that matched is past the recovered prefix), one `graph run`
     plus a `python3 -c` writing `tmp/*.md` (2026-09-24T15:06), and the
     2026-09-25T14:39 first attempt of the same compile probe.
   - Every recovered case was a false positive. None was a prevented write.
3. **Cost per incident is seconds.** The 2026-09-24 compile probe was re-run
   from a scratch script whose command line names no governed path
   ([issues-2026-09-24.md#L814-L823](../docs/issues-2026-09-24.md#L814-L823));
   the witness it produced is in the same file's appendix
   ([#L842-L848](../docs/issues-2026-09-24.md#L842-L848)). FR-1086 cites that
   error text; FR-1087 AC-01 plans its compile evidence through the authoring
   report. Neither FR records being unable to obtain compile evidence. The
   2026-08-15 diary reports the same: the editor read tool answered in
   seconds.
4. **The real defect is the text, not the decision.** The denial for every
   reason ends "Do not work around this guard — write a task brief and run
   the adapter"
   ([pre-command-guard.sh#L269](../.github/hooks/scripts/pre-command-guard.sh#L269)).
   For a read, the adapter is the wrong route, and the working alternative
   (the scratch script) is literally what the text forbids. An agent that
   obeys the text escalates a read into an authoring run; one that ignores it
   learns to ignore the guard. The README describes the fail-closed branch
   ([README.md#L94-L101](../.github/hooks/README.md#L94-L101)) but names no
   read route.
5. **Workaround adequacy.**
   - Editor read and search tools: do not pass through the guard; adequate
     for reading and grepping governed files.
   - `yamlgraph graph lint <path>`: approved today; adequate for static
     checks, does not compile.
   - Script in `tmp/` run as `python tmp/probe.py`: approved, because the
     guard sees only the command line. Adequate for compile probes. The same
     blind spot would admit a script that writes a governed file; FR-767 does
     not claim to see inside script files, and the commit backstop
     (`authoring-proof`, local-only, new artifacts only,
     [README.md#L115-L118](../.github/hooks/README.md#L115-L118)) is the only
     later check. Documenting this route as the **read** route must not read
     as sanctioning it for writes (Human decision 1).
   - pytest: adequate for committed witnesses, too heavy for a probe.

## Ideal Result

A denied read-only command costs one retry through a named, sanctioned read
route, and the denial says which. The guard allows and denies exactly the
same commands as today; C-5 is untouched.

## Proposed Solution

1. **Denial text, fail-closed reason only.** When `AUTHOR_REASON` is the
   catch-all "unrecognized write shape …" reason, append one line to the
   emitted denial: read-only? use the editor's read/search tools,
   `yamlgraph graph lint <path>`, or a script under `tmp/` run as
   `python tmp/<name>.py`; writes still go through `scripts/author.sh`. All
   other reasons (redirect, `tee`, `sed -i`, copy/move, file-tool writes)
   keep today's text unchanged. No change to `terminal_reason()`,
   `governed_path()`, the sentinel check, or the audit row.
2. **README contract row.** In `.github/hooks/README.md`, under the FR-767
   section, add a "Read-only commands" paragraph and one fenced block listing
   the sanctioned read commands, plus the denied `python -c` example. The
   block is machine-read by the test in AC-03, so the README cannot drift
   from the guard.
3. **No new allow path.** Nothing is added to any allow list. FR-1086's
   `graph lint --build`, once merged, is already approved by the guard and
   joins the README block in that FR's PR or this one, whichever merges
   second (Human decision 2).

## Acceptance Criteria

- [ ] AC-01 (RED): new test in `.github/hooks/tests/test_authoring_guard.py`
  sends the `load_and_compile` `python -c` command of the First-consumer
  line. It asserts decision `deny` (passes today) **and** that the output
  names `tmp/` and `yamlgraph graph lint` (fails today). Committed failing
  before the GREEN change (Commandment 7).
- [ ] AC-02: for each of redirect, `tee`, `cp`, and a `create_file` payload
  onto a governed path, the denial output is byte-identical to today's (no
  read-route line). Pins that the hint is scoped to the fail-closed reason.
- [ ] AC-03 (RED): a test parses the README read-only fenced block. Each
  command marked allowed is sent through the hook with a governed path
  substituted and must be `approve`; the `python -c` example must be
  `deny`. Fails today because the block does not exist.
- [ ] AC-04: every existing test in `test_authoring_guard.py` and
  `tests/unit/test_fr1014_authoring_proof_dir_graphs.py` passes unchanged;
  the diff touches no existing assertion. The implementation PR shows
  `terminal_reason()` and `governed_path()` unchanged (`git diff` of
  `pre-command-guard.sh` limited to the denial text).
- [ ] AC-05: new tests tagged `@pytest.mark.req("REQ-YG-423")`
  (CAP-158, which names the FR-767 guard,
  [CAP-158#L23-L58](../capabilities/CAP-158-copilot-skill-promotion.yaml#L23-L58));
  CAP-158 `fr:` gains FR-1093; `python scripts/req_coverage.py --strict`
  passes.
- [ ] AC-06: changelog fragment in `changelog/unreleased/` (`type: feat`,
  `scope: hooks`, `req: REQ-YG-423`); FR implementation record; diary entry.

## Alternatives Considered

Solution classes (chosen: 1):

1. **Do nothing to the decision; document the read route where the denied
   agent reads it (denial text + README).** Chosen. The census shows 26
   false positives in 57 days, each costing one retry, and zero cases where
   a read could not be done another way. That matches the §7 I plan
   decision. The only concrete defect is that the denial text points reads
   at the authoring adapter. Keeps C-5 intact, adds no allow path, and adds
   no parser.
2. **Parse the `python -c` / heredoc body and allow if no write call is
   found.** Rejected. This is `regex_fourth_exclusion`: the catch-all
   already enumerates seven tokens; a body parser must then enumerate every
   Python write (`Path.write_text`, `shutil`, `os.replace`, `yaml.dump` to a
   handle, `subprocess`, `exec` of a string). FR-889 deleted exactly this
   kind of grammar after 14 bypass classes and forbade a smaller
   reimplementation ([FR-889.judgement#L102](FR-889-os-enforced-main-write-lock.judgement.md#L102)).
   It also cannot satisfy C-5: a parser that "cannot prove a write" is not a
   proof of safety.
3. **Allow-list read-only `yamlgraph` CLI invocations** (`graph lint`,
   `graph info`, `graph validate`). Rejected as unnecessary: none of them
   contain a catch-all token, so they are approved today
   ([test_authoring_guard.py#L212-L216](../.github/hooks/tests/test_authoring_guard.py#L212-L216)).
   An allow list would add a bypass surface (`yamlgraph graph lint x.yaml;
   python -c …` segment tricks) to fix a case that does not occur.
4. **Sanctioned CLI compile route (`graph lint --build`, FR-1086).** Not a
   guard change; complementary. It removes the need for `python -c` compile
   probes once merged and passes the guard with no edit. Chosen class 1 lists
   it when it exists. Not chosen as this FR's solution because it is
   FR-1086's scope and carries its own trust decision (it executes
   graph-declared Python).
5. **Sentinel-free read mode env var** (e.g. `YAMLGRAPH_READ_ONLY=1`
   skips Check 6). Rejected: a bypass by another name
   (`skip_env_as_bypass_by_another_name`). The guard cannot verify the
   claim, so any write can set it; FR-767 C-2 rejected global allow-files
   for the same reason.
6. **Replace Check 6's terminal arm with an OS permission lock on governed
   paths, as FR-889 did for main.** Preserved dissent. It is the principled
   cure: the kernel refuses writes and every read passes with no parsing.
   It loses here because governed paths are written inside worktrees by
   `scripts/author.sh`, so the lock would need a per-run unlock bound to the
   sentinel, a larger change with its own judge. The evidence (seconds per
   false positive) does not pay for it. If a denied read ever costs more
   than a retry, this class is the next step, not class 2.

`is_this_a_graph`: no. The change is a fixed string on one deny branch and a
documentation row; no per-item model judgement is involved. The census in
Problem §2 was 29 rows, read directly.

## Out of scope

- Any change to what the guard allows or denies, to `governed_path()`, to
  the sentinel, or to C-5.
- Logging the denied command in `audit.jsonl` (would have made §2 a
  one-line query instead of a transcript join). Not filed; recorded here as
  an observation for the judge.
- The 3 fixture rows (session `s1`) in the real `audit.jsonl`: hook tests
  write to the live audit log (test pollution). Not filed; recorded here as
  an observation.
- The `_REQ_FR767 = REQ-YG-527` binding in `test_authoring_guard.py`
  ([#L29](../.github/hooks/tests/test_authoring_guard.py#L29)), whose
  CAP-192 describes branch-create denial guidance, not the authoring route.
  Not touched; recorded here as an observation.
- `graph lint --build` itself ([FR-1086](FR-1086-lint-compile-check.md)).

## Human decisions needed

1. **May the README name "script under `tmp/`" as a read route, given the
   same blind spot admits script writes?** Suggested default: **yes**, with
   the README stating in the same paragraph that writes via scripts remain
   forbidden by doctrine and that `authoring-proof` catches new artifacts at
   commit. The alternative (omit it) leaves agents to rediscover it, which
   the census shows they do anyway.
2. **Name `graph lint --build` before FR-1086 merges?** Suggested default:
   **no**. Whichever of the two PRs merges second adds it to the README block
   and the denial line, so no text names a flag that does not exist.
3. **Denial text change or README only?** Suggested default: **both**. The
   denial is the only text the affected agent reads at the moment of
   denial (`who_reads_this_when`); README alone would not reach it.

## Related

- Guard: [FR-767](FR-767-graph-authoring-sole-route.md), [FR-1014](FR-1014-dir-aware-authoring-guard.md)
- Grammar precedent: [FR-888](FR-888-main-write-guard-worktree-route.md), [FR-889](FR-889-os-enforced-main-write-lock.md)
- CLI read route: [FR-1086](FR-1086-lint-compile-check.md); sibling repair [FR-1087](FR-1087-safety-guards-demo-repair.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §7 I, §8
- Capability: [CAP-158](../capabilities/CAP-158-copilot-skill-promotion.yaml) (REQ-YG-423)
