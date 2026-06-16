# Diary — 2026-06-16 — The witness as a sketch of the function it deserves

**FR-494** — Stand-alone story generation (headless driver + JSON/Markdown export).

## What happened

The live witness (`witness_book_compose.py`) had quietly become the *only* place
that knew how to drive a DM story end to end — synopsis → cast → play every
chapter → Book gate. It reached straight into `doc["chapters"]["cards"][cid]
["turns"][n-1]["direction"]` to step the loop. That walk was load-bearing
production logic wearing a test costume. When the user asked for stand-alone
generation that emits both `story.json` and a reader `story.md`, the honest move
was not to write a *new* driver beside the witness, but to **extract the driver
the witness had been prototyping all along** and leave the witness as a thin
caller over it.

Two pure boundaries fell out cleanly:
- `render.py` — the no-LLM full-story Markdown render. It does not re-derive the
  Book; it calls `compose_book_deterministic` verbatim and *inherits its raise*.
  One composer, one raise, one truth about "a story with no played chapter is not
  a story."
- `generate.py::generate_story` — the single drive loop, adapter-only, stop
  condition `tree.all_chapters_played`, **raising** on cap rather than returning a
  partial doc.

## The trap I named

**driver_in_test_clothing** — when the only end-to-end driver for a system lives
inside a witness/integration script, every new entry point is tempted to either
(a) duplicate the drive loop or (b) import a test module. Both are wrong. The
witness is a *sketch* of a function the production surface deserves; the cure is
to extract the loop into a named, importable generator and reduce the witness to
asserts. The tell: a test reaches through three levels of `doc[...]` to advance
state. Tests should *assert* against state, not *advance* it — advancing is the
system's job.

This is a cousin of the Scripture's `mock_escape_hatch` and `name_the_seam`: the
witness must exercise the real phenomenon (live vertex generation), but the
*mechanism* it exercises belongs in the code under test, not in the witness body.
A witness that owns the drive loop can pass for the wrong reason — its own loop
is the thing being trusted, untested.

## The boundary that kept me honest

The two `story.json` writes — the adapter's per-session scratch copy under
`<out>/<session_id>/story.json` and the deliverable `<out>/story.json` from
`_write_outputs` — are a small redundancy I chose to *keep visible* rather than
paper over. The deliverable pair (`story.json` + `story.md`) is what the CLI
contract promises; the nested scratch is the adapter's own persistence boundary.
Collapsing them would mean teaching `generate_story` about output layout, which
is presentation's concern, not the driver's. Keep the seam; name it in the commit.

## Seed

**Seed:** If every integration witness is a sketch of a function the system
deserves, could a lint rule flag witness/test files that *mutate* domain state
through more than N levels of subscript (`doc["a"]["b"]["c"] = …` or that feed
such a walk into a loop condition) — turning "this test secretly owns a driver"
from a code-review intuition into a mechanical signal?
