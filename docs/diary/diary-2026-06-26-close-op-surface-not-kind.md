# Diary — 2026-06-26 — The surface of a resolution is not its kind

## What happened

FR-601 sharpened the L7 affect classifier's `close`-op kind discrimination. FR-599's
probe had flagged (c) KIND-WRONG as close-heavy (4 of 5). FR-600 then re-annotated the
ground truth, so the first job was to re-confirm the signal had survived — the Judge's
correction #2 ("recompute (c) on the post-FR-600 residual, you may be sharpening a
confusion the re-annotation already dissolved"). It survived: 6 (c), still 4 close.

Reading the four close beats, the confusion had one shape. On a `close` the model named
the kind from the beat's **surface** — the avenging *act* (betrayal read as retaliation),
the relational *recognition* (guilt read as betrayal), the *triumph* (loss read as hope),
the *solemn ceremony* (hope read as loss) — never from the antecedent feeling the beat
RESOLVES. The cure was a per-kind resolution-signature cue: an exposure closes betrayal,
a recovery closes loss, a vindication closes hope. One spike re-run turned all four into
hits; recall doubled, precision doubled, ABSENT fell.

## The trap I nearly stepped in

**`research_as_inventory` / single-pair tunnel.** The Judge's gate said "name the dominant
pair." My reflex was to find THE pair — a `close guilt -> close relief` repeat I could
target. But all four pairs were n=1: there was no dominant *pair*. The honest finding was a
dominant *mechanism* (surface-read on close), and the lever was a per-kind cue SET, not a
single-pair patch. Had I forced a single pair, I'd have authored a narrow cue that fixed
one beat and missed three. The read — not the count — told me the shape.

A second near-miss: the FR's first-draft cue list named loss/guilt/betrayal/retaliation but
NOT hope. The F9 read (`hope -> loss`) only existed because hope's resolution signature was
absent from my mental model too. Reading the beat, not trusting the draft, added it.

## The trap I DID step in (and the lesson)

**Escape-sequence leakage in a multi-line code insertion.** Editing the probe, my
`replace_string_in_file` newString mixed real newlines with literal `\n` and `\"` escapes;
the later half wrote them verbatim, leaving an unterminated docstring that swallowed the
function body AND the `def main` header below it. Pylance reported "no errors" because a
function with only a docstring is valid Python — the corruption was invisible to the type
checker and only surfaced when I RAN it ("unterminated triple-quoted string literal
detected at line 493", 200 lines past the real fault). Lesson: **after a non-trivial code
edit, run the thing — a green type-checker is not a green interpreter.** Recovery was clean
because I backed up first, deleted the exact corrupt line range by number, and reinserted
plain-ASCII (no em-dashes, no escapes). Heuristic: in tool-driven code edits, prefer ASCII
and real newlines; never hand-author `\n`/`\"`/`\uXXXX` inside a code string.

## The heuristic

> **A boundary correction reclassifies; a discrimination cue converts.** FR-600 moved
> misses to their true bucket (it reclassified, it did not erase). FR-601 then CONVERTED
> the in-reach bucket — the kind-naming gap on already-detected beats — into hits with a
> cue, because the model already knew WHERE and WHO; only WHAT was wrong. The cheap lever
> is the one that operates on what the model already perceives. Read the residual before
> you reach for scale.

## Seed

The remaining (a) ABSENT (14) is the model placing *nothing* on a licensed beat — the
detection floor, the scale lever. Before anyone buys a bigger model: is ABSENT itself
decomposable? Are the absent beats systematically of one chapter-kind (climax vs setup),
one op (more opens than closes), or one character-role (protagonist vs foil)? If ABSENT has
structure, there may be a perception cue as cheap as the close-op one — and scale stays
holstered one more FR.
