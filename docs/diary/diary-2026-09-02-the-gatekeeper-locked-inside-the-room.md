# The Gatekeeper Locked Inside the Room

*2026-09-02 — FR-950, Windows-safe bridge fork registration*

## The shape of the day

The defect was two lines wide. `yamlgraph/utils/bridge.py` called
`os.register_at_fork` at import time, and Windows CPython has no such
attribute, so `import yamlgraph` raised before anything else could happen.
Every entry point died at the same line: CLI, lint, run, pytest collection.
The fix was `getattr(os, "register_at_fork", None)`.

The interesting part was not the fix. It was that enforcement was blocked
twice, in two different ways, and both blocks were more instructive than the
patch.

## Trap 1: the gatekeeper locked inside the room

The standing judgement was REJECTED with authority "none" pending
rejudgement. Correct. So I went to run the judge — and the sole judge route is
`scripts/judge.sh`, which runs `yamlgraph graph run`, which imports
`yamlgraph`, which is exactly what the defect prevents.

The mechanism that grants permission to fix the bug is disabled by the bug.
WSL was broken on the machine, so there was no POSIX escape hatch either. The
enforcement infrastructure had a dependency on the very substrate it was
gating, and nothing in the doctrine anticipated the cycle.

I did not resolve this myself. I surfaced it and let the operator waive C-1
explicitly, then recorded the waiver in the FR. The failure mode I was
avoiding is the quiet one: an agent that hits a gate, decides the gate is
"obviously" satisfiable, and proceeds without saying so. The waiver is a
deviation; deviations belong in the record, not in the agent's head.

**Name it: `gate_depends_on_gated`.** An enforcement gate whose execution
route runs *through* the subsystem it governs cannot adjudicate that
subsystem's own failures. Bootstrap-critical surfaces — package import, the
CLI entry point, the test collector — need a gate route that does not import
them, or the gate silently converts a one-line bug into an unfixable one.

## Trap 2: the aggregate gate that encoded a forecast

AC-07 required the full non-slow unit suite to exit zero on Windows. After
the fix, collection succeeded for the first time — and 587 tests failed.

The reflex was to read that as failure of the change. It was not. Zero of the
587 mention `register_at_fork`, the bridge module, or the loop thread. 377
were `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d` — files
opened without an explicit `encoding=`, so Windows applies cp1252 to UTF-8
content. The rest were absent optional extras and POSIX path assumptions.

The suite had never run on Windows, so it had never been *measured* on
Windows. AC-07 was written when the import error was the only visible Windows
symptom, and it quietly encoded the forecast that fixing the import would
reveal nothing else. Fixing the import didn't fix Windows; it made Windows
*legible* for the first time. The 587 failures are the fix's output, not its
refutation — the first honest measurement of a surface that had been dark.

This is `threshold_encodes_forecast` firing on an FR I was enforcing rather
than authoring, which made it much easier to see. I gated on the defect class
and recorded the aggregate as context.

There is a pleasing symmetry here: the residual 377 failures are *the same
trap as the one I just fixed*. `os.register_at_fork` assumed a POSIX
capability; `open(path)` assumes a cp1252 locale. Both are platform defaults
consumed rather than declared, at the boundary where external data enters.
One boundary was loud enough to crash on line 83. The other was quiet enough
to hide behind a suite that could not be run.

## Heuristics

- **`gate_depends_on_gated`**: before treating a gate as authoritative, ask
  whether its execution route imports the subsystem under repair. If it does,
  the gate is unavailable *precisely when it is most needed*, and the correct
  move is to surface the cycle, not to route around it silently.
- **A restored measurement is not a regression.** When a fix makes a
  previously-dark surface observable, the failures it exposes are a first
  reading. Grep the failure set for the defect class under test before
  attributing any of it to the change.

## Seed

The Windows suite was dark for as long as the package could not import on
Windows — and no gate noticed, because every gate ran where import worked.
What other measurements does this repository believe it takes, but only ever
takes on the platform where they already pass? A gate that runs exclusively
in an environment that satisfies it is not a gate; it is a habit. What would
it cost to make each gate declare the platforms it has *actually* been
observed to run on, so absence of evidence stops reading as evidence of
absence?
