# Diary: Grading the Polished Audit

**Date:** 2026-07-03
**Source:** docs/2026-07-03-review-fable.md
**Tags:** model-evaluation, audit, verification, provenance

## What Happened

Reviewed a full-package audit produced by Claude Fable 5. The report had
excellent operational shape: tooling baseline, prioritized findings, filed
FRs, and source citations. Most findings pointed at real improvement areas:
the structured-output fallback diagnostic, A2A empty-string fallback, MCP
exception logging, sync/async retry drift, and config-boundary enforcement all
survived direct inspection.

But the polish hid two important overclaims. The review said tool nodes write
the singular state-level `error`; the cited code actually writes nested
tool-result payloads under `state_key`. The later FR partly corrected this by
declaring nested `error` payloads out of scope, but the review artifact itself
had already presented the claim as verified. The node-config finding also
blurred two separate facts: factories receive raw dicts after validation, but
`NodeConfig` currently allows extra keys, so merely passing validated objects
would not catch `promtp:` unless the schema forbids extras.

## Trap: Polished Verification Drift

A review can be structurally excellent and still let a wrong premise ride
inside a true direction. The stronger the report format, the easier it is to
mistake citation density for proof. Filed FRs make the analysis feel
concrete, but an FR can inherit the model's first imprecision unless each
claim is rechecked at the exact boundary it names.

## Grade

High utility, imperfect verification. The model is good at finding real
pressure points and translating them into actionable FRs. It is weaker at
maintaining exact semantic distinctions once a narrative forms: state-level
versus nested payload, validation result versus runtime object, shape check
versus enforcement boundary. This is an A-minus audit as triage, B-plus as
evidence.

## Heuristic

When grading an audit model, score two axes separately: **directional value**
and **claim fidelity**. A finding can deserve an FR while still needing its
evidence sentence rewritten. Treat every phrase like "verified" as a testable
claim, not as a trust token.

## Seed

Could review artifacts require a per-finding evidence table with three fields:
`observed_code`, `inferred_risk`, and `uncertainty`? That would make the model
declare where it saw code and where it extrapolated, preserving good triage
without laundering inference into fact.
