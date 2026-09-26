# Feature Request: Close every hatch on the unit tier and let it fail

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
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

1. **Credentials.** A session-scoped autouse fixture in `tests/conftest.py`
   sets `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MISTRAL_API_KEY`,
   `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `REPLICATE_API_TOKEN`, `XAI_API_KEY`
   and `LANGSMITH_API_KEY` to `fr1110-sentinel-not-a-key`, and restores them
   afterwards. Same rule as FR-982: python-dotenv never overwrites an
   existing key.
2. **Runtime hatches.** `tests/unit/conftest.py` registers one
   `sys.addaudithook` at import. Audit hooks cannot be removed, so a
   module-level flag is the switch: `pytest_runtest_setup` sets it for items
   under `tests/unit/`, and `pytest_runtest_teardown` clears it. Collection
   and imports run with the flag off. While the flag is set, the hook raises
   `UnitTierViolation` on:
   - **network:** `socket.connect`, `socket.sendto`, `socket.getaddrinfo`,
     loopback included; `AF_UNIX` too;
   - **subprocess:** `subprocess.Popen`, `os.system`, `os.exec`,
     `os.posix_spawn`, `os.spawn`, `os.fork`, any executable including
     `sys.executable` and `git`;
   - **filesystem:** `open` (and `os.listdir`, `os.scandir`, `glob.glob`)
     on any path outside four roots: the `yamlgraph/` package, `tests/`, the
     running test's `tmp_path` / `tempfile.gettempdir()`, and the
     interpreter's `sys.prefix`/`sys.base_prefix` trees (stdlib and site
     packages).
3. **Message.** Each violation names the hatch, the event, the target, the
   test node id and the three dispositions: "replace with a fixture, move to
   tests/integration/, or add a reasoned allowlist line (FR-1110)".
4. **Run.** Run the full unit suite (slow tests included) on Python 3.11 and
   3.13. Commit Phase 1 with `SKIP=pytest` as the RED commit. Record in this
   FR's implementation record, as prose, the count of failing tests per
   hatch and the list of failing modules. The list is not committed as a
   fixture.

### Phase 2 — disposition every failure (GREEN commits)

One commit per hatch, in this order: credentials, network, subprocess,
filesystem. Each failing test gets exactly one disposition:

- **Fixture:** replace the reach with a mock, a fake or a copy under
  `tests/fixtures/`.
- **Move:** move the module to `tests/integration/`, which the hook does not
  touch and the required unit job does not run.
- **Reopen:** add one line to `UNIT_TIER_ALLOWLIST` in
  `tests/unit/conftest.py`: `(hatch, target pattern, reason)`. The reason
  names why a unit test legitimately needs that reach. Example:
  `("subprocess", "git", "worktree/branch tests exercise git on tmp_path repos")`.
  An allowlist entry opens that target for every unit test, so it is a
  change to enforcement infrastructure and is reviewed as such
  (`instruction_boundary_uncrossed`).

The branch merges only when the full unit suite passes on 3.11 and 3.13
with every hatch enforced.

### Out of scope

- Children of an allowlisted subprocess (a Python script started via an
  allowlisted `sys.executable` can still open sockets). Closing that needs an
  OS sandbox; see Alternatives.
- csap: a separate repository. The conftest is portable and can be copied
  there under its own FR.
- `scripts/ramp.sh` running the system `python3`: an environment mismatch,
  which Phase 2 dispositions like any other subprocess failure.

## Acceptance Criteria

- [ ] AC-01: inside a `tests/unit` test, each of the eight provider variables
  equals `fr1110-sentinel-not-a-key`, even with a real value in `.env` and
  in the parent environment; after the session the parent values are
  restored.
- [ ] AC-02: inside a `tests/unit` test, with an empty allowlist, each of
  these raises `UnitTierViolation`, whose message contains the hatch name,
  the test node id and `FR-1110`:
  `socket.create_connection(("127.0.0.1", 9), timeout=0.1)`,
  `subprocess.run([sys.executable, "-c", "pass"])`,
  `subprocess.run(["kubectl", "version"])` (whether or not it is installed),
  `os.system("true")`, and `open` on the repository's `README.md`. Opening a
  file under `tmp_path` and under `tests/` succeeds.
- [ ] AC-03: a `unittest.mock.patch("subprocess.run")` call inside a unit test
  does not raise (a mocked call emits no audit event).
- [ ] AC-04: the hook is inert outside `tests/unit`: in the same
  `pytest tests/` session, a test under `tests/integration/` calls
  `sys.audit("socket.connect", None, ("192.0.2.1", 80))` and
  `sys.audit("subprocess.Popen", "kubectl", ["kubectl"], None, None)`
  without raising. There is no real I/O.
- [ ] AC-05: an allowlist entry reopens exactly its target: with
  `("subprocess", "git", ...)` present, `git --version` succeeds and
  `kubectl version` still raises.
- [ ] AC-06: the RED commit exists on the branch and the implementation
  record carries the Phase 1 counts per hatch. Every allowlist line has a
  non-empty reason. Every moved module is listed with its old and new path.
- [ ] AC-07: the full unit suite passes on Python 3.11 and 3.13 with every
  hatch enforced, and the required `test` jobs pass.
- [ ] AC-08: CAP/REQ entry; tests carry the REQ marker;
  `python scripts/req_coverage.py --strict` passes; changelog fragment; the
  testing section of `CLAUDE.md` names the four hatches, the three
  dispositions and the allowlist in no more than six lines.

## Pre-mortem

"It shipped and failed. What broke?"
- **The allowlist became the hatch.** Phase 2 under deadline pressure adds
  broad entries (`("filesystem", "*", ...)`) to go green. Guard: every entry
  names a concrete target pattern and a reason; `*` is refused, and the
  review reads the allowlist diff before any test diff.
- **Mass move.** Hundreds of modules moved to `tests/integration/` drop out
  of the required job and stop running anywhere. Guard: the implementation
  record lists every move. If moves exceed a third of the Phase 1 failures,
  stop and bring the integration-job question to the operator before
  continuing.
- **The `open` hook is slow.** It fires on every file open during tests.
  The flag check is the fast path; Phase 1 records suite wall time before
  and after. More than 20 % slower is a finding to report, not to hide.
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
