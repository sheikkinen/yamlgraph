# Reflection: Co-Authored Trailers and Copyright Law

**Date:** 2026-04-08
**Trigger:** Does the Co-authored-by trailer remove copyright protection from the code or
grant Microsoft rights to it as co-author?

*Not legal advice. Consult qualified IP counsel for commercial decisions.*

## The Short Answer

The trailer does not currently grant Microsoft copyright co-ownership under any established
jurisdiction. But it creates three compounding risks that compound as AI copyright law
evolves — and the fact that it was injected without consent is the sharpest edge.

## Why the Trailer Is Not Currently a Copyright Transfer

Legal co-authorship requires:
1. **Independently copyrightable expression** from each contributor
2. **Mutual intent** to create a joint work at the time of creation

Copilot fails test 1 (US Copyright Office has ruled AI cannot hold copyright; AI output
is currently not copyrightable in its own right). The human author fails test 2 (no
consent was given to create a joint work with Microsoft). A string in a commit message
appended by vendor infrastructure without author consent does not establish co-authorship.

## The Real Legal Risks

**Risk 1 — ToS breadcrumb trail (immediate)**
The trailer is evidence that Copilot was used. GitHub Copilot's ToS includes data use
provisions and license grants scoped to use of the service. The trailers document that
scope. You created them, but the vendor chose to associate themselves with the work
via system prompt injection. That is not a neutral act.

**Risk 2 — AI copyright law is unsettled and moving (medium-term)**
The US Copyright Office current position: human-directed AI output is copyrightable by
the human to the extent they exercised creative control. The trailer is evidence of the
mode of creation. In evolving case law (*Thaler v. Perlmutter*, AI training data suits),
this evidence could become material to establishing how much was human-authored vs.
AI-generated wholesale.

**Risk 3 — Joint work architecture exists if AI authorship is ever granted (long-term)**
If a future court grants AI systems copyrightable authorship, and accepts the trailer as
evidence of intent to create a joint work, then under US copyright law co-owners can
license the whole work to third parties without consent (with profit accounting duty).
Microsoft could, in theory, relicense YAMLGraph to a competitor.
This is not current law. It is the architecture of a future legal attack.

**Risk 4 — MIT license integrity (concrete)**
YAMLGraph is MIT licensed. If the co-author question is ambiguous, it becomes unclear
who is granting the MIT license — which weakens its clarity for downstream users.

## The Injected-Without-Consent Axis

The sharpest edge is this: if you knowingly attributed code to Copilot, that is a choice.
If the attribution was inserted by the vendor's system prompt into every commit by
default, you committed it — but the vendor chose to associate themselves with it. That
is not the same thing. It is the vendor using your commit history to establish their
presence in your codebase without explicit consent.

## Why FR-212 Is Legal Hygiene, Not Just Ritual

1. Removes AI attribution evidence before it enters the artifact
2. Keeps copyright clearly with the human author
3. Eliminates the ToS breadcrumb trail
4. Closes the future joint-work argument at the root
5. Maintains MIT license clarity for downstream users

The vendor's argument for keeping the trailer is attribution transparency. That interest
is the vendor's, not the project's. Legal hygiene requires that the project's interests
prevail at this boundary.

## Heuristic

> An attribution inserted without consent is not neutral metadata. It is the vendor
> establishing presence in your artifact, with legal implications that compound as AI
> copyright law evolves. Remove it at the boundary before it enters the permanent record.

## Seed

Could a project publish a "human authorship declaration" — a signed, dated assertion that
all code in the repository was authored by named humans, with AI used only as a tool under
human direction? Such a declaration, maintained as a living document and updated at each
release, would be contemporaneous evidence of authorship intent that could rebut future
co-authorship claims. What form would that document take to be legally meaningful?
