# Reflection: FR-1156/FR-1157 — the error string was the cheap half

**Date:** 2026-11-13
**FR:** FR-1156 (anthropic floor 2.8.0, literal-aware walker), FR-1157 (CAP-164 registration)

## What happened

PR #768 (FR-1155) went red on 13 tests it never touched. Unpinned CI had resolved anthropic 2.8.0, whose
`transform_schema` changed its untyped-schema error text. The obvious repair was the string. Reading the SDK
source showed the text changed because the rule changed: a primitive `const` or an all-primitive `enum` now
makes a subschema constrainable without `type`. Fixing only the oracle would have left the walker refusing
`Literal["a", 1]` models that the SDK accepts.

The judge rejected round 1 for the dependency side ("whatever cascade the dry run requires") and for an
unfrozen traversal. Round 2 approved once both had witnesses: a probe table against the real transform, a
clean Linux/3.12 install whose freeze equalled the pins, and the declared minimum pair installed alone.
The fast suite in a clean CI-mirror container then found the one thing no targeted run could: the fragment
claimed REQ-YG-712 while CAP-164 did not list FR-1156. The round cap refused a third pass, and the two-line
fix became its own FR.

## Root cause

An exact-string parity test against a vendor's private function is two contracts in one assertion: the
message and the rule behind it. A vendor bump that changes the message is a signal that the rule may have
moved. The Windows host could not be a clean environment for the suite (about 300 environmental failures), so
every gate that compared against it was relative. Docker made an absolute gate possible.

## Heuristic

**When a pinned vendor message changes, read the code that emits it before editing the expected string.**
The message is the cheap half; the predicate that produces it is what the walker has to mirror.

Second: **a host that cannot run the suite green is not an environment, it is a diagnostic.** Run the binding
suite in a container shaped like CI (non-root, CI extras, the committed tree) and record that as the result.

**Seed:** Should the SDK parity test also pin a hash of the private `transform_schema` source, so that a
changed rule fails loudly as "the rule moved" rather than as a string mismatch that invites a string fix?
