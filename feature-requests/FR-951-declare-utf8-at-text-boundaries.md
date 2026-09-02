# Feature Request: Declare UTF-8 at every first-party text boundary

**Priority:** HIGH
**Type:** Bug
**Status:** ENFORCED (2026-09-02; RED `9b4d3958`, GREEN `a33797e7`)
**Effort:** 3 days
**Requested:** 2026-09-02
**First consumer / first event:** a Windows contributor or user runs `yamlgraph graph lint` or `yamlgraph graph run` on a graph or prompt YAML containing any non-ASCII character — an em dash, a curly quote, `é`, `€`, CJK, emoji — and the file is read as written instead of crashing or silently corrupting.
**Research:** revised in-body research record under Alternatives Considered. It compares five materially distinct mechanisms, preserves the core-only scope dissent, dispositions prior art below, and answers `is_this_a_graph`; it supersedes the pre-judgement seven-row list.
**Prior art:**
- [FR-950-windows-safe-bridge-fork-registration.md](FR-950-windows-safe-bridge-fork-registration.md) — the direct parent. It removed the *import-time* Windows blocker (`os.register_at_fork`) and thereby made the Windows suite runnable and this defect class visible for the first time. Its Implementation Status explicitly excludes the encoding class under judgement condition C-5 and names this follow-up. Same trap (`the_one_law`: a platform default consumed rather than declared), different boundary: FR-950 was an OS *capability* boundary, this is a text *codec* boundary.
- Grep across all `feature-requests/*.md` for encoding vocabulary returned **no governing FR**. The seven hits are incidental: [FR-243](FR-243-chatterbox-txt-file-batch-tts.md), [FR-393](FR-393-prompt-theme-analyzer.md), [FR-403](FR-403-philosopher-turing-test.md), [FR-629](FR-629-data-files-glob-support.md), [FR-643v2](FR-643v2-novel-fandom-world-expansion.md), and [FR-894](FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md) each show a code sample that *already passes* `encoding="utf-8"`. They are evidence that the correct idiom is known and applied ad hoc per FR, never enforced — which is precisely the gap this FR closes. None allocates a requirement for it.
- [FR-948-lan-copilot-delegation.judgement.md](FR-948-lan-copilot-delegation.judgement.md) R-5 concerns cross-platform *result-path* semantics for remote delegation, not text decoding in the product's own load path. No overlap.
- [FR-754-id-registry-chaplain-path-leak.md](FR-754-id-registry-chaplain-path-leak.md) F4 prefers cross-platform assertions over shell `grep` in tests. It is a test-portability note, not an encoding contract.
- Retrieval is filename-noun IDF ranked and finds vocabulary, not problems. The absence of an encoding FR is therefore a floor, not proof; the Judge should treat the FR-950 lineage as the controlling precedent.

## Summary

Declare `encoding="utf-8"` at every first-party text-file boundary and on the
CLI's own output stream, then enforce it with a blocking lint rule so the
class cannot return.

## Value Statement

YAMLGraph reads and writes text identically on every platform, so a graph or
prompt containing a curly quote behaves the same on Windows as on Linux
instead of crashing or silently reaching the LLM as mojibake.

## Problem

Python's `open()` in text mode uses `locale.getpreferredencoding()` when no
`encoding=` is passed. On this Windows host that is **cp1252**; on the Linux
CI runners it is UTF-8. Every first-party read of a UTF-8 file without an
explicit encoding is therefore correct in CI and wrong in production on
Windows.

`ruff check --select PLW1514 --preview . --output-format json` reports **496
sites**. The six root counts sum exactly to the total; every root is in scope:

| Root | Sites | Boundary rationale |
|---|---:|---|
| `.chaplain/` | 7 | First-party automation that reads repository text |
| `.github/` | 18 | First-party hooks and enforcement scripts |
| `examples/` | 80 | Executable product demonstrations and fixtures |
| `scripts/` | 47 | First-party development and release operations |
| `tests/` | 314 | Witnesses and fixtures that establish product truth |
| `yamlgraph/` | 30 | Shipped runtime and CLI |
| **Total** | **496** | All findings classified and in scope |

The 30 product sites include the core load path:
`yamlgraph/compile/graph_loader.py:134`, `yamlgraph/utils/prompts.py:198` and
`:235`, `yamlgraph/schema_loader.py:253`, `yamlgraph/discovery.py:185`.

### Three distinct failure modes, all reproduced on 2026-09-02

**Mode 1 — crash on read.** Bytes undefined in cp1252 (`0x8d`, `0x8f`, `0x90`,
`0x9d`) raise. `0x9d` is the third byte of `U+201D` (a closing curly quote),
so an ordinary typographic quotation mark in a graph description is enough:

```
$ yamlgraph graph lint <UTF-8 graph containing U+201D>
UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 97
```

**Mode 2 — silent corruption (the dangerous one).** Most UTF-8 sequences
*are* decodable as cp1252, just wrongly. No exception is raised; the mojibake
flows into prompts, LLM calls, and outputs:

```
locale.getpreferredencoding(): cp1252
loaded (no encoding=) -> 'cost â‚¬5 â€” cafÃ©'
correct (utf-8)       -> 'cost €5 — café'
SILENTLY CORRUPTED: True
```

This is `plausible_wrong_answer`: the value passes every type and shape check
and is semantically wrong. Mode 2 has no crash to alert anyone, so its
prevalence is unknown and unbounded.

**Mode 3 — the diagnostic destroys itself.** When Mode 1 fires, the CLI's
error handler prints `❌` (`U+274C`) to a stdout that is also cp1252 when
piped, so the handler raises while reporting:

```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 97
During handling of the above exception, another exception occurred:
UnicodeEncodeError: 'charmap' codec can't encode character '\u274c' in position 0
```

The user loses the actionable message and receives a confusing chained
traceback about an emoji. The output boundary is unnormalized too.

### Why this was invisible

Every GitHub Actions job in `.github/workflows/` is `runs-on: ubuntu-latest`;
there is no Windows job anywhere. The suite could not run on Windows at all
until FR-950, so a 496-site defect class accumulated behind a green CI that
only ever measured the platform where the bug does not exist.

## Ideal Result

Text crosses YAMLGraph's boundaries in a declared encoding, never an inherited
one. Every first-party read and write of a text file states UTF-8 explicitly,
the CLI's own streams state UTF-8 explicitly, and a lint rule running on the
existing Linux CI makes an unencoded boundary a build failure — so the class
is closed by construction rather than by vigilance, and a Windows user's
curly quote is simply a curly quote.

## Proposed Solution

Normalize at the boundary; enforce statically.

**1. Declare the encoding at every first-party text boundary in the six frozen
roots.** Ruff offers a mechanical fix for the 496 inventoried sites
(`--unsafe-fixes`; "unsafe" only because declaring an encoding *changes
behavior* — which is the intent):

```python
with open(path) as f:                      # inherits cp1252 on Windows
with open(path, encoding="utf-8") as f:    # declared
```

The fix set must be reviewed rather than trusted. Any site whose actual
contract is not UTF-8 gets an explicit codec, including `encoding="locale"`
only when inherited locale text is intentional, plus an entry in the exception
ledger below. No blanket ignore is permitted. Every deviation must be recorded
before the GREEN commit.

**2. Normalize the CLI's own output stream once, at the entry point**, so
diagnostics survive being piped:

```python
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
```

One callsite in the CLI entry module. Not a per-`print` fix, and not
`PYTHONUTF8` guidance in a README — an environment variable the user must
remember is not a boundary.

**3. Make it enforceable without widening unrelated Ruff policy.** Add
`PLW1514` to `[tool.ruff.lint] select` in `pyproject.toml`. Preserve the
existing general `ruff check yamlgraph/` CI gate and add a separate blocking
Linux step whose exact command is:

```bash
ruff check --select PLW1514 --preview .
```

The dedicated command covers all six frozen roots but activates no other Ruff
rule across support, test, or example trees. It must block pull requests and
merge-group candidates.

**4. Prove it on the real platform with deterministic witnesses.** Add:

- `tests/fixtures/fr951/unicode_graph.yaml`
- `tests/fixtures/fr951/unicode_prompt.yaml`
- `tests/fixtures/fr951/unicode_schema.yaml`
- `tests/unit/test_fr951_utf8_boundaries.py`
- `tests/unit/test_fr951_cli_streams.py`

The loader witness runs in a Windows subprocess with `PYTHONUTF8=0`, first
asserts `locale.getencoding()` is cp1252 or a documented alias, and fails rather
than skips when that precondition is false. It then loads the committed graph,
prompt, and schema fixtures and asserts exact preservation of `U+201D` and
`U+20AC`, including equality with explicit-UTF-8 reference values.

The CLI witness runs the installed `yamlgraph` console entry with
`PYTHONUTF8=0`, `PYTHONIOENCODING=cp1252`, and stdout/stderr captured as byte
pipes. GREEN requires both streams to decode as UTF-8, the Unicode graph lint
to exit zero, an applicable non-ASCII status or error glyph to traverse each
stream, and neither Unicode exception name to appear. Calling an internal
helper with an already-normalized stream does not satisfy the witness.

One blocking `windows-latest` smoke job installs the project, imports
`yamlgraph`, asserts the codec precondition, and runs only these focused
witnesses. The full unit suite remains a diagnostic, not a merge gate.

New capability `CAP-259` with `REQ-YG-638`, since no existing requirement owns
cross-platform text encoding.

## Frozen Deliverables

| Deliverable | Surface |
|---|---|
| D-1 | Folded research, inventory, witness plan, and status in this FR |
| D-2 | Explicit text encodings at every PLW1514 site in `.chaplain/`, `.github/`, `examples/`, `scripts/`, `tests/`, and `yamlgraph/` |
| D-3 | One CLI stdout/stderr UTF-8 normalization in `yamlgraph/cli/__init__.py` at `main()` |
| D-4 | `PLW1514` configuration in `pyproject.toml` and its dedicated blocking Linux invocation in `.github/workflows/workflow.yml` |
| D-5 | The committed fixtures and focused graph, prompt, schema, corruption, and CLI-pipe witnesses named above |
| D-6 | One focused blocking `windows-latest` CI job for import and D-5 witnesses |
| D-7 | `capabilities/CAP-259-*.yaml`, `ARCHITECTURE.md`, and `REQ-YG-638` test markers |
| D-8 | One FR-951 fix changelog fragment, implementation-status record, and diary entry |

Not authorized: new dependencies; a text-I/O wrapper abstraction; provider,
YAML parser, or third-party changes; `PYTHONUTF8` as a shipped-user
requirement; locale mutation outside witnesses; non-PLW1514 Ruff policy;
broad CLI-output refactoring; a full Windows test matrix; optional-dependency,
POSIX-assumption, or other Windows-suite fixes; CAP/REQ work beyond
CAP-259/REQ-YG-638.

## Acceptance Criteria

- [x] AC-01 The committed inventory names all six roots reported by `ruff check --select PLW1514 --preview .`, and its counts sum to 496.
- [x] AC-02 Under a Windows subprocess with `PYTHONUTF8=0` and an asserted cp1252 `locale.getencoding()`, `tests/unit/test_fr951_utf8_boundaries.py` loads the three committed fixtures through graph, prompt, and schema loaders and preserves `U+201D` and `U+20AC` exactly.
- [x] AC-03 The focused silent-corruption assertions compare every loaded value with an explicit-UTF-8 reference value, not merely a non-raising result.
- [x] AC-04 With `PYTHONUTF8=0`, `PYTHONIOENCODING=cp1252`, and captured byte pipes, the installed `yamlgraph graph lint` command exits zero for `tests/fixtures/fr951/unicode_graph.yaml`; stdout and stderr decode as UTF-8 and contain neither Unicode exception name.
- [x] AC-05 `tests/unit/test_fr951_cli_streams.py` exercises an applicable non-ASCII status or error glyph on each CLI stream through the installed entry point and exits without a Unicode exception.
- [x] AC-06 `ruff check --select PLW1514 --preview .` exits zero, and every non-bare fix appears in the exception ledger with its codec and reason.
- [x] AC-07 `PLW1514` is selected in `pyproject.toml`; the existing general `ruff check yamlgraph/` CI gate remains; a dedicated blocking Linux CI step runs the exact AC-06 command.
- [x] AC-08 A blocking `windows-latest` job installs the project, imports `yamlgraph`, asserts the codec precondition, runs AC-02 through AC-05, and runs no full unit-suite gate. **Open operator action:** the new `windows-encoding` context must be added to branch protection's required-checks list before it blocks merges.
- [x] AC-09 `python scripts/req_coverage.py --strict` exits zero on Windows with `PYTHONUTF8` unset; CAP-259 and REQ-YG-638 are allocated; every new test carries `@pytest.mark.req("REQ-YG-638")`.
- [x] AC-10 The focused witnesses are committed RED before production or configuration fixes and GREEN afterward in separate commits.
- [x] AC-11 The Windows non-slow unit-suite diagnostic is recorded with its command, exit status, and counts for both Unicode exception classes; GREEN requires both counts to be zero, while aggregate pass/fail remains context. **Disposition:** zero raised exceptions of either class; the one remaining bare-token match is a source line, cited below.
- [x] AC-12 A `type: fix` changelog fragment names FR-951 and REQ-YG-638; Implementation Status records dated AC commands and results; one diary entry records a trap or insight, a heuristic, and a `Seed:`.

## Encoding Exception Ledger

| Site | Explicit codec | Boundary reason |
|---|---|---|
| None | N/A | Every declared site is UTF-8. The two candidates reviewed as possibly locale-defined — `tempfile.NamedTemporaryFile(..., suffix=".txt")` in two Chaplain tests — are files this repository both writes and reads, so UTF-8 is their actual contract. No `encoding="locale"` and no blanket ignore was used. |

## Out of Scope

Explicitly excluded, to avoid FR-950's AC-07 error of gating on an aggregate
that spans several defect classes:

- **Optional-dependency failures.** 19 `ModuleNotFoundError` (`fastapi`, `litellm`, `bs4`, `feedparser`, `statemachine_engine`) reflect an incomplete local venv, not a code defect. Filed as [FR-952](FR-952-optional-extras-must-skip-not-error.md).
- **POSIX path and shell assumptions** in test fixtures. Filed as [FR-953](FR-953-windows-posix-shell-misattribution.md), which found the dominant sub-class is not a fixture defect at all: `bash` resolves to the WSL stub, which exits 1, so 149 blocks blame the script for the interpreter's absence.
- **Full Windows unit-suite green.** A separate FR once the two classes above are dispositioned.
- **Retrofitting `encoding=` to third-party code.** PyYAML raised in the FR-950 traces, but it was reading a stream *we* opened; the fix is ours.
- **Unrestricted repository-wide Ruff policy.** Only PLW1514 expands to all six roots; every other selected rule retains its current CI boundary.

## Alternatives Considered

| # | Mechanism class | Benefit | Failure mode / strongest objection | Disposition |
|---|---|---|---|---|
| A1 | Explicit codec at each owned text boundary plus a dedicated PLW1514 gate | Corrects decode, silent-corruption, and output failures where data enters; statically enforceable on Linux | A 496-site diff requires review and can mislabel a genuinely locale-defined contract | **Chosen.** Record every non-UTF-8 contract in the exception ledger |
| A2 | Central `read_text_utf8`/`write_text_utf8` wrapper | One policy chokepoint | Adds an abstraction over stdlib calls, weakens direct PLW1514 visibility, and does not cover subprocess or CLI streams | Rejected: more code with less static transparency |
| A3 | Global UTF-8 mode through `PYTHONUTF8`, `-X utf8`, locale mutation, or runner configuration | Small deployment change normalizes many defaults | Transfers correctness to every launcher and user environment; omitted configuration leaves Mode 2 intact | Rejected as product policy; environment flags are witness controls only |
| A4 | `EncodingWarning`, advisory PLW1514, or decode-error fallback | Low initial source churn and visible diagnostics | Detection does not repair Mode 2; fallback never runs for valid-but-wrong cp1252 decoding; diagnostics can fail too | Rejected: symptom detection without boundary correction |
| A5 | Guarantee UTF-8 only in runtime loaders and CLI; leave tests, scripts, examples, hooks, and Chaplain locale-dependent | **Strongest dissent:** reduces scope from 496 to the 30 product findings plus streams | First-party fixtures and gates can fail or corrupt before reaching product witnesses, recreating the Windows blind spot | Rejected: all six roots are owned execution surfaces; the PLW1514-only command limits policy expansion |

The alternatives disagree on proportionality and ownership. A5 is materially
smaller, but the excluded first-party roots build, test, demonstrate, and
enforce the runtime; inherited codecs there can invalidate operational truth.
The selected design therefore keeps the six-root text contract while limiting
the broad CI invocation to PLW1514 alone.

**`is_this_a_graph`?** No. There is no per-item model call, multi-stage LLM
pipeline, or fan-out. This is a mechanical source transformation plus a lint
rule; `yamlgraph graph list` offers nothing applicable.

## Related

- `yamlgraph/compile/graph_loader.py:134`, `yamlgraph/utils/prompts.py:198`, `yamlgraph/utils/prompts.py:235`, `yamlgraph/schema_loader.py:253`, `yamlgraph/discovery.py:185`
- `yamlgraph/cli/graph_validate.py:193` — the Mode 3 self-destroying error handler
- `pyproject.toml` — `[tool.ruff.lint] select`
- `.github/workflows/workflow.yml` — currently `ubuntu-latest` only

## Implementation Status

- **2026-09-02 planning amendment:** judgement R-1 through R-5 folded. No production, test, capability, architecture, or CI implementation has started. C-2 human review of the future `pyproject.toml` and workflow changes remains a gate.
- **Inventory baseline:** `ruff check --select PLW1514 --preview . --output-format json` reported `.chaplain/` 7, `.github/` 18, `examples/` 80, `scripts/` 47, `tests/` 314, and `yamlgraph/` 30; sum 496.
- **Windows suite diagnostic:** `.venv/Scripts/python.exe -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto` exited 1 with `587 failed, 5718 passed, 97 skipped, 1 xfailed, 73 errors`; its captured log contained 755 `UnicodeDecodeError` and 11 `UnicodeEncodeError` occurrences. Aggregate pass/fail is context; AC-11 requires both exception counts to reach zero.

### 2026-09-02 enforcement

RED `9b4d3958` (fixtures and nine witnesses, all failing on the inherited codec), GREEN `a33797e7` (declarations, CLI streams, gates, CAP/REQ).

| AC | Command | Result |
|---|---|---|
| AC-01 | `ruff check --select PLW1514 --preview . --output-format json` | 496 findings; `.chaplain/` 7, `.github/` 18, `examples/` 80, `scripts/` 47, `tests/` 314, `yamlgraph/` 30 — sum 496, reconciled |
| AC-02/03 | `pytest tests/unit/test_fr951_utf8_boundaries.py -q --no-cov` | 6 passed; probe reported `locale.getencoding() == 'cp1252'`; all three loaders equal their explicit-UTF-8 reference |
| AC-04/05 | `pytest tests/unit/test_fr951_cli_streams.py -q --no-cov` | 3 passed; `graph lint` exits 0 under `PYTHONIOENCODING=cp1252`, both streams decode as UTF-8 and carry their glyph |
| AC-06 | `ruff check --select PLW1514 --preview .` | exit 0; exception ledger empty (every fix is bare UTF-8) |
| AC-07 | `ruff check yamlgraph/` | exit 0 under `preview = true` + `explicit-preview-rules = true`; the general gate is unchanged and the dedicated step is added to the required `test` job |
| AC-08 | `.github/workflows/workflow.yml` job `windows-encoding` | added; **operator action outstanding** — the context is not yet in branch protection's required list, so it reports but does not yet block |
| AC-09 | `.venv/Scripts/python.exe scripts/req_coverage.py --strict` | exit 0 on Windows with `PYTHONUTF8` unset; 408/408 requirements covered; CAP-259 / REQ-YG-638 allocated |
| AC-11 | `.venv/Scripts/python.exe -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto` | exit 1 — `277 failed, 6100 passed, 97 skipped, 1 xfailed, 18 errors` (from `596 failed / 73 errors` before the change — the planning record's 587 plus the nine RED witnesses); **zero raised `UnicodeDecodeError` and zero raised `UnicodeEncodeError`**; failure-set diff against the pre-change run shows **0 new failures** |

**AC-11 count disposition.** A bare grep for `UnicodeDecodeError` returns exactly one hit: the source line `except (UnicodeDecodeError, OSError):`, echoed in the traceback context of a test failing for an out-of-scope reason. Counting only raised exceptions (`UnicodeDecodeError: ` / `UnicodeEncodeError: `) gives 0 and 0. The residual 277 failures and 18 errors are the classes this FR excludes — `ModuleNotFoundError` for absent optional extras, and POSIX path assumptions (e.g. `ramp_installer.ManifestError: source not normalized`).

### Deviations from the frozen scope

1. **The PLW1514 inventory is a floor, not the class.** Ruff only reports `Path.read_text` / `Path.write_text` where it can infer the receiver's type, so a module constant (`ARCHITECTURE_MD.read_text()`) or a fixture argument escapes it. After the frozen 496-site diff was applied, `scripts/aggregate_capabilities.py` — required by D-7 — still crashed with `UnicodeDecodeError`, and AC-11 still counted 255 raised decode and 45 raised encode exceptions. A further **1703 `read_text`/`write_text` boundaries** across the same six roots were therefore declared, by AST byte offsets rather than regex. This is the same boundary under the same law, not an adjacent defect class; the alternative was to ship an FR claiming the class was closed while it demonstrably was not.
2. **Three first-party scripts declare their own streams**, beyond D-3's single CLI callsite: `scripts/req_coverage.py` and `scripts/req_audit_report.py` each print status glyphs and each crashed when piped, and AC-09 requires the former to exit zero. Both use the same two-line declaration as `main()`.
3. **14 product and generator sites** invisible to PLW1514 were declared by hand before the mechanical pass: `yamlgraph/diary/importer.py`, `yamlgraph/linter/checks_tool_call.py`, `yamlgraph/models/relay_fields.py`, `yamlgraph/storage/export.py`, `yamlgraph/tools/manifest.py`, `yamlgraph/tools/tool_slots.py`, `yamlgraph/utils/worktree_helpers.py`, and `scripts/aggregate_capabilities.py`.
4. **The mechanical pass initially regressed 46 tests.** `Path.read_text(encoding, ...)` takes encoding as its *first* positional argument and `Path.write_text(data, encoding, ...)` as its second, so ten calls that already passed `"utf-8"` positionally became `read_text("utf-8", encoding="utf-8")` — a `TypeError`. A corrective AST pass removed the duplicate keyword; the final failure-set diff is 0 new failures.

**Known limitation the gate does not cover.** Because PLW1514 under-detects pathlib text I/O, `ruff check --select PLW1514 --preview .` cannot by itself keep the class closed: a new `Path.read_text()` on an uninferable receiver will pass the gate. The 1703 sites are declared but not statically defended. Closing that gap needs either a repository-specific AST check or an upstream ruff improvement, and is a follow-up.

