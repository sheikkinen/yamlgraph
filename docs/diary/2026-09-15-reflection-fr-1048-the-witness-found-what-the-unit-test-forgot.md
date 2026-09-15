# The Witness Found What the Unit Test Forgot

**Date:** 2026-09-15
**Trigger:** FR-1048 live witness — the gated integration run, after the unit
suite was already green.

## What happened

The offline unit suite passed 72 tests. The first live run failed two:
the prompt fixture had `nonce: NONCE-7419` — a `: ` sequence that YAML parsed
as a nested mapping key — and opencode's `Session not found` stderr does not
echo the attempted session id, so the AC-17 assertion could never pass. Both
were invisible to mocked `subprocess.run`: the mock never parses YAML, and it
never runs the real CLI whose stderr is missing the id.

## The trap

`mock_escape_hatch`. A mocked subprocess proves the code's *shape*; it cannot
prove the fixture parses or that the real CLI reports what the assertion
assumes. The live witness exists because of a physical phenomenon — a real
process with real stderr — and only exercising that phenomenon surfaced the two
gaps. The unit suite was green the whole time.

## The cure

For any backend that shells out to a real binary, the gated live witness is not
a formality — it is the only test that exercises YAML parsing and the vendor's
actual error strings. Run it before marking the FR implemented, not after.

**Seed:** What two facts are *always* invisible to a mocked subprocess — the
fixture's parseability and the vendor's exact stderr — and which other
subprocess backends (`cli`, `claude`) would a live re-run now catch in the same
gap?
