# The promise the book keeps — or waives — FR-693

*2026-07-08*

## What happened

FR-693 closes latent plot threads. A latent thread is a promise the book has not
kept: it was mined from a character's fear or a faction's internal tension, but
it carries no raise event and no release event. Three pure gates enforce
closure: **latent-closure** (every `status: latent` thread needs both a raise
and a release, or a waiver), **waiver-integrity** (every waiver names a live
thread with a reason and a decider), and **byte-identity** (pre-existing event
files are never mutated — revision is additive, new files only). Plus a small
inheritance from FR-690: `create_event` now emits a `sequence` total-order
value.

## The trap resisted: `growth_as_default`

The obvious enforcement move was to *close* all three latent threads by
generating raise/release events. The graph is built for exactly that: an agent
with `create_event`, sequence numbers waiting in the gaps. But the FR's own
"Alternatives Considered" had already flagged the hazard — *"some latents are
texture, not defects; forcing closure invents events nobody wants."* Gunnar's
fear of being useless in peacetime is a throughline, not a datable scene.
Heidrun's legacy is a thematic undertone. The youth's resentment is a tension
the book deliberately leaves simmering. All three are texture.

So the closure was subtractive, not additive: three waivers, each with an honest
reason, in `story/thread_waivers.yaml`. The exit gate is *zero unwaived latents*,
not *zero latents* — and it passes deterministically with no event invented. The
event-creation path stays proven-but-unused: the `sequence` emission is
unit-tested, the agent graph lints clean, and the open-ended run is left to the
operator. The temptation to make the agent *do something* was the trap; the
discipline was to let the waiver file be the answer.

## The insight: the gate reads two surfaces, the fix writes only one

`check_byte_identity` guards the canon event files (mutation = violation).
`check_latent_closure` reads the derived story threads and the waiver file
(regenerable, freely writable). The same pass touches both surfaces but with
opposite rights: canon is append-only, story is rewritable. Naming that split in
the gate — one function per surface, one caller for tests and one for the graph
— kept the additive contract legible. The waiver file is not a workaround for
the gate; it is a first-class closure path the gate was designed to accept.

## The friction: an ID collision I did not cause

Mid-enforcement the chaplain automation pushed FR-700 and claimed CAP-195 /
REQ-YG-531 — the exact band FR-692 had already pushed under. The registry
condemned the duplicate. The cure was mechanical: FR-700 owns the lower band;
FR-692 and FR-693 renumber forward (CAP-196/197, REQ-YG-532–535) via `git mv` +
higher-number-first `sed`. The lesson is not about the numbers; it is that an
autonomous agent sharing `origin/main` is another writer at the boundary, and
its commits must be treated as concurrent external input — `git fetch` before
every push, and expect the band you reserved to be gone.

## Seed

The event-creation path is built but unused — proven only by unit tests and a
lint-clean graph. When does *wiring proven but not run* become a phantom
capability? Should an agent graph that has never executed end-to-end carry the
same CAP claim as one exercised by an acceptance run, or does an unrun graph
deserve a distinct, weaker status in the registry — "wired" vs "enforced"?
