---
type: feat
scope: race
---
- **FR-709 Real-Provider Race Loser-Teardown Witness**: API-key-guarded integration test racing anthropic vs google live with a 3 s timeout, asserting the FR-707/708 teardown contract against real transports in whichever outcome shape occurs — verdict within budget, post-warm-up thread baseline restored, drain clean or WARNING-with-names, zero net thread growth over 3 consecutive races (the Fly-freeze accumulation signature, absent). Field findings: google rejects client deadlines < 10 s (`LLM_REQUEST_TIMEOUT < 10` breaks the google provider — consumer-relevant for FR-708 deployments), and real cancelled gemini tasks acknowledge cancellation within `CLEANUP_GRACE` (abandon path stays cold on healthy endpoints).
