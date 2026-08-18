# Feature Request: FR-820 Stripe Prepaid Credit Purchase for YAMLGraph Serve

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed — blocked on FR-819 enforcement; this is the separate
human-approved FR that FR-819 C-7 requires before any real-money payment
**Effort:** 5–8 days (after FR-819 ships)
**Requested:** 2026-08-18
**First consumer / first event:** an invited YAMLGraph Serve tenant whose
admin-issued test credits are exhausted, at the moment they pay real money on
a Stripe-hosted checkout page and see their credit balance increase without
operator involvement.

**Prior art:** FR-819 (hosted declarative graph runner) explicitly defers
payments: its judgement C-7 forbids real-money payment without a separate
human-approved FR — this FR is that instrument, not a violation of it.
FR-819 amendment A-2 prepared the seams this FR uses: `catalog_version`
stamped on `run_reserve`, `tenant_id` as the first-class key under API
tokens, and `credit_grant` keyed by unique source event. No other FR touches
payments, billing, or stored value.

## Summary

Let YAMLGraph Serve tenants purchase prepaid credits with real money through
Stripe Checkout. A verified Stripe webhook event becomes exactly one
`credit_grant` ledger entry; everything downstream (reserve → debit →
release) is the existing FR-819 ledger, unchanged. Stripe never meters runs;
the ledger never touches cards.

## Value Statement

Invited tenants can fund their own usage without operator-issued credits,
turning YAMLGraph Serve from an operator-subsidized demo into a
self-sustaining service, while Stripe-hosted checkout keeps card data (and
PCI scope) entirely out of the control plane.

## Problem

FR-819 supports admin-issued test credits only. Every tenant top-up is a
manual operator action, which caps the service at hand-held pilot scale and
makes the operator spend ceiling a personal subsidy. The ledger, identity,
and pricing seams were deliberately built payments-ready (FR-819 A-2), but no
purchase path exists.

## Ideal Result

A tenant with an empty balance clicks "buy credits", pays on a Stripe-hosted
page, and returns to a balance that reflects the purchase — granted exactly
once regardless of webhook retries, refunded only from unspent balance,
reconciled nightly against Stripe payouts, and evidenced end-to-end (Stripe
receipt for the money, FR-819 receipt chain for the usage, joined by
`catalog_version`). The operator's manual role reduces to policy: pack
pricing, freeze/refund decisions, and dispute responses.

## Proposed Solution

All new code lives in the FR-819 control plane (`projects/hosted_runner/`);
the gateway and runner are untouched — no new arrows into either trust zone.

### 1. Identity layer above tenant_id

Add a `users` table (email + OAuth or magic-link auth) with
`stripe_customer_id`, mapping one user to one `tenant_id`. API tokens remain
credentials over `tenant_id`; graph/run/ledger schemas do not change.

### 2. Purchase via Stripe Checkout (hosted)

- `POST /v1/billing/checkout` creates a Stripe Checkout Session for a credit
  pack (Stripe Product/Price), with `tenant_id` in metadata, and returns the
  redirect URL. Card data never touches the control plane (SAQ-A scope).
- Credit packs are service-owned configuration: € price ↔ integer
  microcredits granted. Two price systems on purpose: € per pack (Stripe),
  microcredits per token (FR-819 catalog, versioned by `catalog_version`).

### 3. Webhook-only fulfilment

- `POST /v1/billing/webhook` verifies `Stripe-Signature`, then handles
  `checkout.session.completed` by writing one `credit_grant` with
  `source_event = evt_...`. The ledger's unique-source-event constraint makes
  webhook retries and replays idempotent for free.
- The success-redirect URL never grants credits — it is user-controlled.

### 4. Refunds, disputes, freezes

- New ledger entry type `credit_revoke` (append-only preserved): a Stripe
  refund revokes up to the *unspent* balance only; spent credits are final.
- `charge.dispute.created` freezes the tenant (no new reservations at
  `POST /v1/runs`) and revokes unspent credits pending resolution. Run states
  and in-flight runs are untouched.

### 5. Reconciliation

Nightly job sums `credit_grant`/`credit_revoke` against Stripe balance
transactions; any mismatch alerts the operator and blocks further checkout
sessions — mirroring FR-819 `settlement_review`: never silently fabricate or
absorb a discrepancy.

### 6. Compliance posture

- Credits are non-transferable, non-cash-valued, non-withdrawable (already in
  FR-819's purge list) — avoiding the stored-value/e-money regulatory cliff.
- Stripe Tax handles VAT at purchase (credits = electronically supplied
  service).
- Stripe keys live in the control plane only, same custody rule as provider
  keys in the gateway (never in runner or gateway zones).

## Acceptance Criteria

- [ ] AC-01: Checkout session creation is tenant-authenticated, references a
      configured credit pack, and embeds `tenant_id` in session metadata.
- [ ] AC-02: A verified `checkout.session.completed` webhook writes exactly
      one `credit_grant`; replayed/duplicate webhook deliveries write nothing
      further (unique `source_event` proven by test).
- [ ] AC-03: An unsigned or badly signed webhook is rejected and grants
      nothing; the success-redirect path grants nothing.
- [ ] AC-04: Refund flow revokes at most the unspent balance via
      `credit_revoke`; spent credits are never clawed back from settled runs.
- [ ] AC-05: A dispute webhook freezes new reservations for the tenant while
      leaving in-flight runs and terminal states untouched.
- [ ] AC-06: Reconciliation detects a seeded grant/payout mismatch, alerts,
      and blocks new checkout sessions until operator resolution.
- [ ] AC-07: Stripe secret keys and webhook secrets appear only in
      control-plane configuration; tests prove absence from runner/gateway
      artifacts, events, receipts, and logs.
- [ ] AC-08: End-to-end witness (Stripe test mode): buy pack → balance
      increases once → run spends credits → receipts join money to usage via
      `catalog_version`.
- [ ] AC-09: Project-local requirements cover the above;
      `python scripts/req_coverage.py --strict` stays green with no framework
      REQ added.
- [ ] AC-10: Documentation states pack pricing, refund/dispute policy, credit
      expiry policy, VAT handling, and the non-transferable/non-cash nature
      of credits.

## Alternatives Considered

- **Metered/post-paid billing (Stripe usage records):** rejected — FR-819
  chose reserve-then-settle precisely because post-hoc charging cannot bound
  overspend; prepaid packs keep that invariant.
- **Payment Links instead of Checkout Sessions:** rejected — no per-session
  `tenant_id` metadata binding, weaker fulfilment attribution.
- **Grant on redirect success URL:** rejected — user-controlled; webhook is
  the only fulfilment path.
- **Custom card form (Stripe Elements):** rejected for MVP — pulls the
  control plane into larger PCI scope for no MVP benefit over hosted
  Checkout.
- **Subscriptions (monthly credit drip):** deferred — one-off packs prove
  the seam; Billing can be added later without ledger changes.

## Dependencies

- FR-819 enforced through at least D-1, D-5, D-6 (control plane, ledger,
  tenant storage) with A-2 (`catalog_version`) in place.
- Human decisions below resolved before enforcement.

## Questions For The Human (options drafted; blocking before enforcement)

1. **Credit expiry:** (a) never expire, (b) 12 months from purchase
   *(recommended: (b) — bounds dormant liability)*.
2. **Payment methods:** (a) cards only, (b) cards + SEPA. SEPA carries 8-week
   chargeback rights against instantly granted credits
   *(recommended: (a) for MVP)*.
3. **Subscription vs one-off packs:** (a) one-off packs only, (b) add monthly
   drip *(recommended: (a))*.
4. **Business entity / Stripe account jurisdiction and VAT registration:**
   operator to name the entity — no default; this gates Stripe account
   creation itself.

## Related

- `feature-requests/FR-819-hosted-declarative-graph-runner.md` (Sections 4–5,
  Amendments A-1–A-3)
- `feature-requests/FR-819-hosted-declarative-graph-runner.judgement.md`
  (C-7: the gate this FR is designed to lift)
