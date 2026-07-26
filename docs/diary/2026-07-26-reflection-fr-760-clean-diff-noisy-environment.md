# 2026-07-26 — Enforcing FR-760: the diff was clean, the noise was the environment

**Context:** FR-760 asked for one honest line: declare `langchain-core`
explicitly instead of letting it arrive transitively via `langgraph` and the
provider packages. Judged scope was razor-narrow — a `pyproject.toml` entry,
a substantive rationale row, and the existing `dependency_rationale.py
--strict` gate. No new scanner, no adapter, no governance redesign.

**The trap that almost fired:** a fresh worktree venv (isolated from the
shared, dirty `main` worktree three other live sessions were touching) came
back with 14 failures on the full unit suite. The reflex is
`recent_changes_blindness`/`downstream_fix`: blame the new dependency line.
Instead, per `changelog_first_diagnostic` and `read_raw_output_first`, I read
the actual tracebacks first: `ModuleNotFoundError: feedparser`,
`ModuleNotFoundError: bs4`, `z3 not installed`, and two full-suite-only
failures that passed in isolation. None mentioned `langchain_core`.

**Verification, not assumption:** I built a *second*, completely unmodified
worktree from `origin/main` with the same optional-package set and ran the
identical suite. It reproduced the exact same 7 residual failures, same
`5058 passed` count, byte-for-byte. That is the mechanical proof the
Scripture demands before writing "pre-existing failure" — a phrase this repo
forbids as a hedge unless backed by a controlled comparison. Here the
comparison existed: my change added zero new failures.

**Heuristic:** when a diff is scoped to one dependency line, the fast path to
"is this my fault?" is not code review of the change — it is running the
*exact same command* on an unmodified sibling checkout and diffing failure
sets. A control worktree is cheaper than reasoning about whether a stray
`ModuleNotFoundError` could possibly be caused by a version bump it never
imports.

**Seed:** the repo's fast unit-test commands (`pytest tests/unit/ -q --no-cov
-m "not slow"`) silently depend on optional extras (`feedparser`, `bs4`, `z3`)
that `pip install -e ".[dev]"` does not install. Should the `dev` extra (or a
documented `make test-env` target) enumerate every extra the *unit* suite
imports, so a freshly built venv is green without tribal knowledge of which
demos/examples need which optional package? (Same seed independently reached
in `diary-2026-07-24-venv-death-and-the-lying-failures.md` — this is its
second confirmed recurrence, a graduation candidate.)

## Follow-up: PR #462 review, round 2 (2026-07-26)

The reviewer's second pass caught a defect the first commit introduced
by its own hand: regenerating `docs/fr-board.md` from a git worktree
mislabeled roughly 200 unrelated FR rows' `repo` column from
`yamlgraph` to `fr-760`, because `scripts/fr_board.py` derived the repo
identity from `Path.cwd().name` — the checkout directory's basename,
not the project's actual name. A worktree at `tmp/worktrees/fr-760` has
dirname `fr-760`; every row the script renders from that checkout
inherits the wrong label, not just the new FR's own row.

**Trap:** I ran the standard pre-commit hook chain (which includes
`fr-board-check`), it passed, and I trusted that as proof the board was
correct — but "passes the regenerate-and-diff check" only proves the
committed file matches what THIS checkout would generate; it says
nothing about whether this checkout's generation logic is itself
sound. A tautological gate can be green while its output is wrong, if
the input to the comparison (the generator) shares the bug being
tested for.

**Heuristic:** any generated-artifact gate that regenerates AND
compares needs its generator function tested independently of the
specific checkout it happened to run from — worktrees, CI runners, and
local clones all have different, unstable directory basenames, and
"stable identifier" fields (a package name, a git remote URL) should be
preferred over path-derived ones for anything committed to the repo.

**Seed:** how many other generated-artifact scripts in this repo derive
identity or scope from `Path.cwd()` or a directory basename rather than
a stable project marker (`pyproject.toml`, git remote)? A one-time grep
audit (`Path.cwd()`, `.parent.name`, `os.getcwd()`) across `scripts/`
could surface siblings of this same worktree-fragility class before a
reviewer finds them one PR at a time.
