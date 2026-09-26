# Feature Request: Close every hatch on the unit tier and let it fail

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-26); R-1..R-6 folded
([judgement](FR-1110-unit-test-runtime-sandbox.judgement.md))
**Effort:** 3 days
**Requested:** 2026-09-26
**First consumer / first event:** the first `pytest tests/unit` run after
Phase 1 lands on the branch. Every test that reaches beyond its unit fails
at the exact call, and the failure list becomes the inventory Phase 2
dispositions. After merge, the next agent-authored unit test that reaches
the network, a subprocess, a file outside its roots or a real provider key
fails on its author's first local run.
**Research:** in-body dispositioned alternatives table (§ Alternatives
Considered), FR-889 style. No `scripts/research.sh` run.
**Prior art:**
- [FR-756](FR-756-core-test-isolation.md) (Enforced): classifies unit modules
  as `process` by grepping source for `.chaplain`, `examples/`, `scripts/`.
  It labels; it does not constrain. The FR-1084 census carried
  `pytestmark = pytest.mark.process` and still blocked every PR, because the
  required `test (3.11)`/`test (3.13)` jobs run all of `tests/unit`. This FR
  constrains observed behaviour at runtime, not source text, and leaves the
  marker untouched.
- [FR-982](FR-982-unit-suite-runs-with-tracer-live.md): overrides four
  tracing variables in a session fixture because `yamlgraph/config.py`
  loads `.env` at import. Precedent for the credential hatch.
- FR-1104 / PR #714 (open, retires `core-test`): removes the only CI job that
  ran `-m "not process"`. This FR does not need that job; enforcement
  applies to every run of `tests/unit`.
- Diary [2026-09-26 — the unit test that owned the repository](../docs/diary/diary-2026-09-26-the-unit-test-that-owned-the-repo.md)
  proposed an LLM map-reduce scope census of `tests/unit/`. Superseded: the
  Phase 1 failure list observes what tests touch; a census would guess.

## Summary

Phase 1 closes every hatch at once: credentials, network, subprocess and
filesystem. There is no allowlist, no report mode and no marker exemption.
The suite goes red, and the red list is the inventory. Phase 2 dispositions
every failure: fix it with a fixture, move it to `tests/integration/`, or
reopen one hatch with a one-line, reasoned allowlist entry. The branch
merges when it is green. The RED commit is the proof trail, as in TDD.

## Value Statement

For the operator who merges agent-written tests: a unit test can no longer
hold authority over the network, the cluster, a paid API or the
developer's working tree. Each remaining reach is a named, reviewed
allowlist line instead of an unexamined default.

## Problem

Witnessed on 2026-09-26:

1. **FR-1084 census.** A merge-gating unit test compiled every documented
   graph, imported example tools, and compared doc line numbers
   byte-for-byte. It broke CI three times in one day on unrelated changes.
   Locally it failed a fourth way: an untracked `tmp/diary-discourse-analysis`
   flipped a row. Deleted by operator decision (#713).
2. **csap.** Unit tests ran `kubectl` and required deployed images to be
   SHA-pinned. A red unit test became a request to change production.
3. **Network in the unit tier.** `test_fr784_network_sniff::test_timeout_is_ceiling_not_floor`
   drives a real browser and asserts wall-clock time. It failed at 11.6 s
   under the full parallel suite.
4. **Real keys in every local run.** `yamlgraph/config.py:44` calls
   `load_dotenv()` at import, so every local unit run holds the developer's
   real `ANTHROPIC_API_KEY`. The fake-key run (7148 passed, no Anthropic
   authentication error) proved nothing only because the key had been
   swapped by hand.

`tests/unit/` is the cheapest enforcement slot, so an agent puts any claim
it wants enforced there. Production code has a layer contract
(`import-linter`, FR-218); tests have none. A partial sandbox (a denylist,
a report mode) would leave the unknown reaches open. Closing everything
and reading the failures is the only way to learn what the reaches are.

## Ideal Result

Every `tests/unit` test runs with no reach beyond its own process, its own
`tmp_path`, the package and the test tree, on a laptop and in CI alike,
without a wrapper command. Each exception is one visible allowlist line
with a reason. A new reach fails at the exact call, and the error names
the hatch, the target, the test and where the test should live instead.

## Proposed Solution

No new dependency. All enforcement lives in `tests/unit/conftest.py` (new)
plus one session fixture in `tests/conftest.py`.

### Phase 1 — close every hatch (RED commit)

1. **Credentials (R-1).** At the top of `tests/conftest.py`, before any
   `yamlgraph` import, save the absence or exact value of
   `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MISTRAL_API_KEY`,
   `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `REPLICATE_API_TOKEN`, `XAI_API_KEY`
   and `LANGSMITH_API_KEY`, and set each to `fr1110-sentinel-not-a-key`.
   `yamlgraph/config.py` then loads `.env` without overwriting them
   (python-dotenv never overwrites an existing key). Restore the saved state
   once, at `pytest_sessionfinish`. FR-982's tracing fixture and cache
   clearing stay as they are.
2. **Activation (R-2).** `tests/unit/conftest.py` registers one
   `sys.addaudithook` at import. Audit hooks cannot be removed, so the hook
   reads an active-state record. A function-scoped autouse fixture that
   depends on `tmp_path` sets the record (node id, canonical `tmp_path`)
   immediately before `yield` and clears it in `finally`. Collection,
   imports and integration items run with no record. `tempfile.gettempdir()`
   is not a root: a test reaches only its own `tmp_path`.
3. **Capability matrix (R-3, R-4).** While armed, the hook raises
   `UnitTierViolation` before the side effect:

   | Hatch | Audit events denied | Allowed targets |
   |---|---|---|
   | network | `socket.connect`, `socket.bind`, `socket.sendto`, `socket.sendmsg`, `socket.getaddrinfo`, `socket.gethostbyname`, `socket.gethostbyaddr` | none (loopback and `AF_UNIX` included) |
   | process | `subprocess.Popen`, `os.system`, `os.exec`, `os.posix_spawn`, `os.spawn`, `os.fork`, `os.forkpty` | none (`sys.executable` and `git` included) |
   | filesystem read | `open` in read mode, `os.listdir`, `os.scandir`, `glob.glob` | canonical paths under `yamlgraph/`, `tests/`, the current `tmp_path`, `sys.prefix`, `sys.base_prefix` |
   | filesystem mutation | `open` with a write/append/create/truncate mode or flag, `os.remove`, `os.rename`, `os.mkdir`, `os.rmdir`, `shutil.rmtree`, `os.chmod`, `os.chown`, `os.utime`, `os.symlink`, `os.link`, `os.truncate` | canonical paths under the current `tmp_path` only |

   Target normalization happens before comparison: `str`, `bytes` and
   `PathLike` are resolved relative to the cwd, `..` is collapsed, and
   symlinks are resolved (`os.path.realpath`); a non-existent write target
   is resolved through its parent. An integer file descriptor passes only
   if `os.open` created it under the armed state (so it was already
   checked). Any argument shape the hook cannot normalize raises, naming
   the shape. The exact event list is verified on Python 3.11 and 3.13; the
   implementation record carries the per-Python, per-platform result.
4. **Allowlist (R-4).** `UNIT_TIER_ALLOWLIST` holds typed entries
   `(hatch, target, reason)`. `target` is an exact normalized value: an
   executable basename, a `host:port`, or an absolute path. No regex, glob,
   empty target, `*`, or filesystem root is valid. Invalid entries fail
   collection. It starts empty.
5. **Message.** Each violation names the hatch, the event, the target, the
   test node id and the three dispositions: "replace with a fixture, move to
   tests/integration/, or add a reasoned allowlist line (FR-1110)".
6. **Run (R-5, R-6).** Run the full unit suite (slow tests included) on
   Python 3.11 and 3.13 locally, and record the CI result. Commit Phase 1
   with `SKIP=pytest` as the RED commit. The implementation record gets one
   row per failure: Python version, node id, module, hatch, event,
   normalized target, proposed disposition. The table lives in this FR,
   not in a test fixture. No Phase 2 change starts until the populated
   table is committed.
7. **Performance gate (R-6).** Record three baseline and three sandboxed
   full-unit runs (SHA, Python, worker mode, command, test count, wall
   time). A median slowdown above 20 % stops enforcement for an explicit
   operator decision.

### Phase 2 — disposition every failure (GREEN commits)

One commit per hatch, in this order: credentials, network, process,
filesystem. Phase 2 touches only modules in the committed Phase 1 table; a
newly found failure is appended to the table before it is changed. Each
failing test gets exactly one disposition:

- **Fixture:** replace the reach with a mock, a fake or a copy under
  `tests/fixtures/`.
- **Move:** move the module to `tests/integration/`, which the hook does not
  touch and the required unit job does not run.
- **Reopen:** add one line to `UNIT_TIER_ALLOWLIST` in
  `tests/unit/conftest.py`: `(hatch, exact target, reason)`. The reason
  names why a unit test legitimately needs that reach. Example:
  `("process", "git", "worktree/branch tests exercise git on tmp_path repos")`.
  An allowlist entry opens that target for every unit test, so it is a
  change to enforcement infrastructure and is reviewed as such
  (`instruction_boundary_uncrossed`).

Every allowlist row and every move needs explicit operator approval before
merge. If moves exceed one third of the Phase 1 failures, stop and ask the
operator to choose: approve the exact move list, first file a separately
judged FR for a required integration job, or abandon those moves.

The branch merges only when the full unit suite passes on 3.11 and 3.13
with every hatch enforced.

### Out of scope

Production changes under `yamlgraph/`; CI workflow or required-check
changes; the FR-756 `process` marker; report-only or opt-out modes; marker
exemptions; broad allowlists; integration-test changes other than moves
listed in the approved Phase 1 table; unrelated test repairs. Also:

- Children of an allowlisted subprocess (a Python script started via an
  allowlisted `sys.executable` can still open sockets). Closing that needs an
  OS sandbox; see Alternatives.
- csap: a separate repository. The conftest is portable and can be copied
  there under its own FR.
- `scripts/ramp.sh` running the system `python3`: an environment mismatch,
  which Phase 2 dispositions like any other process failure.

## Acceptance Criteria

Adopted verbatim from the judgement's revised criteria.

- [ ] AC-01: before the first `yamlgraph` import in the pytest process, all eight named credential variables equal `fr1110-sentinel-not-a-key`; separate parent-environment and `.env`-only witnesses prove no real value is observed, and session finish restores absence or the exact inherited value.
- [ ] AC-02: a function-scoped autouse unit fixture arms the hook with the current node id and canonical `tmp_path`, clears it in `finally`, remains active through dependent fixture teardown, and cannot leak active state after a setup, call, or teardown failure.
- [ ] AC-03: the frozen real-operation matrix raises `UnitTierViolation` before each denied network, process, filesystem-read, or filesystem-mutation side effect on Python 3.11 and 3.13; every message contains hatch, event, normalized target, node id, `FR-1110`, and the three dispositions.
- [ ] AC-04: package and test-tree reads and current-`tmp_path` reads/writes succeed; repository-root reads, package/test-tree writes, another test's temporary root, `..` traversal, and symlink escape raise. Integer file-descriptor behavior matches the folded contract.
- [ ] AC-05: patching `subprocess.run` emits no process audit event and succeeds; a real denied `sys.executable`, `kubectl`, and `git` call fails before launch.
- [ ] AC-06: one reviewed exact-target `git` allowlist entry permits only its normalized `git` target; a near match, `kubectl`, every other hatch, and every other target still raise. Invalid or broad entries fail validation at collection.
- [ ] AC-07: in one `pytest tests/` session the hook is inert during collection and for integration items, then re-arms for the next unit item. The focused witnesses pass sequentially and under xdist.
- [ ] AC-08: the Phase 1 RED commit exists and the FR contains the complete failure table for full unit runs, including slow tests, on Python 3.11 and 3.13 and the tested local platform; counts reconcile to table rows by hatch and module.
- [ ] AC-09: every Phase 1 row has exactly one fixture, move, or reviewed reopen disposition; every moved module records old/new path; every allowlist row has explicit human approval; no test module outside the table changes under Phase 2.
- [ ] AC-10: the full unit suite passes sequentially on Python 3.11 and 3.13 with the hook active, both required `test` jobs pass, and the repository's documented xdist non-slow unit command passes with the hook active.
- [ ] AC-11: three matched baseline/sandbox runs show a median wall-time increase of at most 20 percent, or an explicit human decision records why a larger regression is accepted before merge.
- [ ] AC-12: the capability/REQ entry, marked tests, `python scripts/req_coverage.py --strict`, changelog fragment, implementation record, no-more-than-six-line `CLAUDE.md` note, and diary entry with `Seed:` are present and pass their repository checks.

## Pre-mortem

"It shipped and failed. What broke?"
- **The allowlist became the hatch.** Phase 2 under deadline pressure adds
  broad entries (`("filesystem read", "/", ...)`) to go green. Guard: exact
  targets only, validated at collection, and each row needs operator
  approval; the review reads the allowlist diff before any test diff.
- **Mass move.** Hundreds of modules moved to `tests/integration/` drop out
  of the required job and stop running anywhere. Guard: the one-third stop
  rule above.
- **The `open` hook is slow.** It fires on every file open during tests.
  Guard: the performance gate (Phase 1 item 7).
- **Third-party background threads** (telemetry) open sockets during a test,
  and the test gets blamed. Fix at the library's configuration boundary, as
  FR-982 did for tracing, not with an allowlist line.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Denylist of infrastructure CLIs plus report mode (first draft of this FR) | Rejected by the operator: it leaves every unknown reach open, and report mode is a hatch. Closing everything is how the unknown reaches become known. |
| `pytest-socket` plugin | Rejected: new dependency, covers sockets only. |
| OS sandbox (`docker --network none`, `unshare -rn`, macOS `sandbox-exec`) | Refused. It catches child processes, but differs per platform, needs a wrapper command, and does not run on a plain local `pytest`. |
| Clean environment plus minimal `PATH` wrapper (`env -i`) | Rejected: only applies when someone uses the wrapper. |
| LLM map-reduce scope census of `tests/unit/` (diary, #712) | Superseded by the Phase 1 failure list: observed behaviour, not a classification guess. |
| Extend FR-756 source-grep markers | Rejected: the census was marked and still gated merges. |

## Related

- `tests/conftest.py` (FR-982 tracing override, FR-756 process marker)
- `yamlgraph/config.py:44` (`load_dotenv()` at import)
- `.github/workflows/workflow.yml` (`test` job runs `tests/unit`)
- #713, #712, FR-1084 D-6
