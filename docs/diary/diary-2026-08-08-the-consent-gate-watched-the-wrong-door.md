# The Consent Gate Watched the Wrong Door

**2026-08-08 — FR-782 enforcement, self-portrait example**

## What happened

FR-782 was, on paper, the most privacy-careful FR this repo has judged.
The judgement spent a whole revision (R-2) on one idea: a consent gate
that shows a *summary* of what will be sent is compliance theatre, so
the gate must prove **exact outbound-payload identity** — hash the
bytes, write them to disk, re-verify byte-for-byte after the interrupt.
I built exactly that. Tests for hash equality, tampering, byte counts.
The gate was airtight.

Then I ran it once, for real, against the synthetic fixture, and read
what the model wrote back:

> "Device username 'sheikki' suggests Finnish identity."

Nothing in the fixture contains my name. The fixture is
`Testeri Testinen` and `Fakelinna` and `Placeholder Oy`. The leak came
from the one part of the payload nobody thought of as data: the
**supplementary source availability probes**, which reported
`/Users/sheikki/Library/Safari/History.db` as their path. Four absolute
paths, riding inside the JSON, carrying the account name — through a
consent gate that hashed them perfectly and previewed them faithfully.

The gate did its job. It proved that what I saw was what was sent. It
had nothing to say about *what was in there*, because I had never read
the payload.

## The trap

`gate_checks_shape_not_substance` is already in the Scripture, and I
still walked into its mirror image. The Scripture's framing is about
gates that check presence instead of content. This is a gate that
checks **identity** instead of content — a stronger gate, a better
gate, and equally blind. Cryptographic proof that A equals B says
nothing about whether A should exist.

And the cure was already written down too: `read_raw_output_first`. For
an egress boundary the raw artifact is `synthesis-payload.json`, 4 KB of
plain JSON sitting in the output directory the whole time. One `grep
sheikki` on it — the same one-line probe that ends every one of these
investigations — would have found the leak before the first provider
call. I ran the pipeline instead, and the *model* found it for me, by
doing exactly what the FR said an agent should do with this artifact:
infer who the user is. The system worked so well it incriminated its own
input.

## The second trap, smaller

The governed authoring route forced two round trips: the first graph
used `path: tools.py`, which loads a module without a parent package, so
the tool module's relative imports died in strict mode. My instinct was
to fix the four characters myself — it was *obviously* right, and the
sentinel would have let a manual edit through if I had reached for the
editor before thinking. Writing a second task brief for a one-line
correction felt absurd. It also took four minutes and produced a
recorded repair note in the authoring report. The rule that governs the
trivial case is the only reason the rule exists.

## Heuristic

**`identity_gate_is_not_a_content_gate`** — a boundary that proves *what
you saw is what you sent* is not a boundary that knows *what you sent*.
Hash-equality gates, checksum audits, and signed manifests all answer
"unchanged?", never "acceptable?". Pair every identity gate with one
forced read of the artifact it protects, and assert the content property
you actually care about (here: "no path from `Path.home()` appears in
the payload"). The assertion is one line; the gate around it was ninety.

Corollary, cheaper: **the metadata is data**. Diagnostic fields —
paths, hostnames, versions, timings, "not configured" descriptors —
are written to help the operator and then quietly serialized into the
payload with everything else. Anything that ships inside the egress
envelope is egress, no matter which section of the code produced it.

## Seed

The leak was caught because a *model* read the payload and drew a
conclusion a human skim would not have drawn. That inverts the usual
relationship: we normally treat LLM inference as the risk at an egress
boundary. What if it is the detector? A pre-egress node that asks a
local model one question — *"what can you tell me about this person that
is not explicitly stated?"* — would have printed "their macOS account
name is sheikki" before anything left the machine. Not a redaction
gate (FR-782 rightly forbids those); a **surprise gate**: it reports
what a reader would infer, and the human decides. Cheap, local,
adversarial, and aimed at exactly the class of leak that survives every
structural check — the inference no schema can see.

**Seed:** Should every egress boundary carry an inference probe — a
local model asked "what could a reader conclude from this that the
author did not intend to say?" — as the content half of the gate whose
identity half we already trust?
