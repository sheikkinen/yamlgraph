# The hash arrived after the work ran out

**Date:** 2026-09-18
**Arc:** Re-reading the rationale for `artifact_hash` after FR-1051 made it an
execution blocker

## What it actually buys

`artifact_hash` answers one narrow question: does this route log name the same
graph-and-prompt content that `graph export --overlay` is inspecting now? That
is useful when a route trace is evidence. A prompt can change behaviour without
changing the graph YAML, and an installed or dirty-tree run may have no useful
Git commit identity. A content fingerprint closes that correlation gap.

It does not pin anything. It does not prevent change, prove approval, authenticate
the route log, identify a Git commit, or cover the complete executable environment.
Python tool source and dependencies are outside its manifest. Calling the record
"self-authenticating" goes beyond what hash equality establishes: anyone able to
replace the artifact and log can recompute both.

## How an audit feature entered the execution path

FR-807 framed the route record through auditors, AI Act Article 12, incident
timelines, regulated evidence, and a conformance claim that execution could be
bound to an approved artifact. The vocabulary sounds MDR-shaped even though the
implemented primitive proves only present-content equality. That framing made
the mechanism feel infrastructural rather than optional: every route-logged run
must resolve and hash the executable artifact before doing useful work.

FR-1051 exposed the price. The hasher independently re-read raw graph YAML and
reimplemented prompt resolution. It disagreed with the loader about
`defaults.prompts_relative`, so graphs compiled and linted successfully but died
before their first executed call. The consumer result was 0 of 62 conversations.
The evidence mechanism became more authoritative than the execution mechanism
whose evidence it was supposed to describe.

The defect was one missing fallback. The design smell is larger: an optional
forensic consumer created a second parser on the mandatory runtime path. The
value question should have been asked before the integrity question: who reads
the hash, at what decision, and what becomes impossible without it? Today the
concrete answer is overlay/log correlation. That can justify hashing for that
evidence surface. It does not by itself justify making ordinary execution depend
on a separately resolved artifact closure.

## The operator prior

The operator assumption is that when an LLM runs out of meaningful product work,
it starts adding SHA pinning, provenance ledgers, identity envelopes, and
verification steps. These additions are attractive because they are locally
defensible, mechanically testable, and sound serious. They manufacture an
unbounded supply of work without requiring a new user capability.

This is not a rule that hashes are useless. It is an evidentiary prior: unsolicited
identity machinery begins with the burden of proving a named reader and decision,
not with the benefit of the doubt. "Auditability" and regulated-language proximity
do not discharge that burden. A hash with no decision consumer is ceremony; a hash
whose only consumer is optional must justify every failure it introduces into the
mandatory path.

## Heuristic

Before adding a content hash, SHA pin, provenance ledger, or identity envelope,
answer four questions in order:

1. Who reads it?
2. What concrete decision do they make from equality or mismatch?
3. Why can the existing artifact, version, or run identity not support that
   decision?
4. Why must collection or verification block the primary operation?

If the first two answers are unnamed, stop. If the fourth answer is absent, keep
the mechanism on the evidence consumer's path rather than the product's path.

**Seed:** Could proposal and judgement templates treat unsolicited SHA/provenance
machinery as a `growth_as_default` signal, requiring one named mismatch decision
and one demonstrated failure that the hash would have prevented before granting
authority?
