# FR-759: source-of-truth drift hides in the gap between prose and code

## What happened

FR-759 froze a span schema in prose (`yamlgraph.run.id: str (UUIDv7)`),
implemented it in code (`uuid.uuid4()`), and described it a third time in
`reference/otel-observability.md` (`str (UUID)`, no version). All three
were self-consistent on their own terms — the implementation compiled,
the tests passed (they asserted non-null/string, never a version check),
and the doc read as sensible prose. Nothing was locally wrong. The
reviewer caught the drift only by holding the FR text, the code, and the
doc side by side and noticing the FR said "v7" while nothing downstream
enforced it.

The same shape repeated twice more in one PR: node coverage was
documented and CAP-registered as including `race`, but the compiler
never wrapped it; router was mapped through the same handler as `llm`
and inherited its hardcoded node-type label, so the promised
`yamlgraph.node.type == "router"` never appeared on a real span. Three
independent instances of "the artifact that describes the behavior and
the artifact that produces the behavior stopped agreeing," none of them
caught by a green test suite, because every existing test asserted
shape (a string exists, a span is emitted) rather than the specific
frozen value the FR actually committed to.

## The trap under the trap

`test_disabled_is_true_no_op` and its siblings gated the ENTIRE test
file behind `pytest.importorskip("opentelemetry.sdk")` — a defensible-
looking guard, since most of the file genuinely needs the SDK. But two
of the ten tests exist specifically to prove the DISABLED path works
without the SDK, and a module-level skip silently prevented them from
ever running in the one environment (no `otel` extra) where their
assertion is meaningful. `pytest 1 skipped` looks identical whether the
skip is correct (SDK-dependent test, no SDK) or backwards (no-SDK test,
guarded by an SDK import) — the test runner cannot tell you your skip
condition is inverted for a subset of the file.

## Heuristic

**`plausible_wrong_answer`, applied to schema fields instead of prose:**
a frozen type constraint in an FR ("UUIDv7", not "UUID") is a claim the
test suite must assert at the value level, not the shape level.
`assert isinstance(x, str)` and `assert uuid.UUID(x).version == 7` both
pass for a UUIDv4 test double, but only one of them is testing what the
FR froze. Whenever a schema field carries a version, format, or
enum-of-one constraint tighter than its Python type, the test must
exercise that specific constraint, not the type it happens to share with
looser alternatives.

**Corollary for skip-gated test files:** when a module import-skips the
whole file for an optional dependency, audit whether every test in that
file actually needs the dependency — the "guard the whole file" pattern
silently converts "this test doesn't need X" into "this test never
runs," and the two look the same in green CI.

**Seed:** When a review cites three independent findings in one PR, ask
whether they share a root cause before fixing each in isolation — here,
UUIDv7-as-UUID4, race-unwrapped, and router-mislabeled were three
instances of the same "prose says X in more detail than the code
enforces" pattern, not three unrelated defects. A single audit pass
("for every frozen schema field, does a test assert the field's most
specific stated property, not just its type?") would have caught all
three before review rather than after.

## Follow-up: PR #465 review, round 2 (2026-07-26)

The round-2 finding was a narrower instance of round 1's own P2 fix
applied incompletely: P2 correctly guarded the top-level `import
opentelemetry` so the disabled path never requires the extra, but the
SAME "wrap the import, don't trust the caller's environment" discipline
wasn't propagated to the *second* place OpenTelemetry gets imported —
`_configure_exporter_if_needed()`'s SDK and exporter imports, which only
execute once OTEL is actually enabled. Fixing the entry point (the
top-level check) felt complete because it was the visible boundary named
in the FR text; the second, lazier import site deeper in the same module
was invisible to a review pass that stopped at "does the documented
error path work" rather than "does EVERY OpenTelemetry import in this
file share the same guard."

This is `two_strike_split`'s shape one level down: not a second guard
firing on the same code, but the same fix pattern needing to be applied
a second time within one module because the module has two independent
import boundaries (api-presence, sdk/exporter-presence) that look like
one boundary from the outside (both live under `is_otel_enabled()`'s
umbrella) but fail independently in practice — `opentelemetry-api` and
`opentelemetry-sdk` are genuinely separate PyPI packages that can be
installed independently.

**Heuristic:** When a module imports the same optional third-party
package family at more than one call site, the guard discipline applied
to the first (usually the most visible, entry-point) call site must be
verified — not assumed — at every other call site importing any part of
that family, even ones gated behind a runtime condition (`if
is_otel_enabled()`) that makes them look like they "can't be reached
independently." grep for every `import opentelemetry` (or the
equivalent for any optional-extra package) in the file being reviewed,
not just the one the FR's prose calls out by name.

**Seed:** Could a lint rule or `noqa`-adjacent convention flag "raw
`import <optional-package>` outside a function already proven to be
guarded by the SAME error class" — turning "did every import in this
file get the same treatment" from a manual review question into a
mechanical, repo-wide gate the way `noqa_coverage.py` already does for
undocumented suppressions?
