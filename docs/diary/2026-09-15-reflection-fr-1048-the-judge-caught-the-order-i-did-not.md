# The Judge Caught the Order I Did Not

**Date:** 2026-09-15
**Trigger:** FR-1048 `backend: opencode` — the fourth copilot backend, carried
from proposal through three judged revision rounds to enforcement in one session.

## What happened

I proposed a fifth copilot-node backend that shells out to `opencode run`. The
research route surfaced FR-546 — an *already-judged* opencode backend (server/SDK
route) I had not found on my own. The judge's first merits round caught that I had
written "four opencode-only keys" while defining five. Its third round caught
something sharper: my frozen argv placed the prompt **before** `--format`, but
every raw capture in my own evidence file placed the flags first.

I had invented a command order I had not run, then cited evidence that used a
different order. The judge saw the contradiction because it read both texts
against each other — the one thing an author writing both never does.

## The trap

`private_language`, in a new costume. Author, researcher, and enforcer were all me
in one session, so the FR, the evidence, and the code each *sounded* right read
alone — only the judge, reading the FR against the evidence with no memory of my
intent, could see the order mismatch. The contradiction was invisible to every
informed reader and obvious to the one reader given nothing but the two documents.

## The cure

For any frozen external contract (argv, envelope, event vocabulary), the *only*
admissible witness is the raw capture, byte-for-byte, and the plan text must quote
the same bytes. A prose description of a command is a claim; a capture is a fact.
When the plan and the capture disagree, the plan is wrong — never "both are fine".

**Seed:** Does the judge's repeated `APPROVED WITH REVISIONS` (three rounds, each finer than
the last) mean the FR is converging — or that a single judge is a saturating
critic whose nits asymptote toward noise? What is the stopping signal for folding
revisions when no round returns clean?
