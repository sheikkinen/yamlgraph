# 2026-05-11: Reflection — Marketing E2E Boundary Drift

The failure looked at first like feature bleed: `Voice Coordinator W0/W1/W2` appeared in a marketing test, and the obvious story was that NC-289 concurrency work had leaked into NC-271. The real issue was subtler. W0/W1/W2 were the expected NC-280 supervisor workers; the failure lived at the boundary between public Twilio traffic and internal supervisor-to-worker loopback.

The trap was treating two WebSocket hops as the same trust boundary. Twilio signature validation belongs at the public supervisor edge. Once the supervisor admits a route token and proxies to a worker on loopback, the worker is no longer receiving a Twilio-originated request. Reapplying Twilio validation there converted a valid route into an immediate 1008 policy close, which Twilio surfaced as "stream started, then stopped".

The second trap was test tail latency masquerading as a hang. The mock conversation had already completed, but the outcaller answerer overwrote the schema default with a 30-second post-farewell wait. Shortening that runtime value made the result match the observable intent: finish promptly after farewell and let `end_call` close the session.

Heuristic: when a proxy introduces a new hop, name the security boundary explicitly. Validate at the external ingress, then make the internal contract small, local, and test-covered.

Seed: Can the supervisor expose a health/debug endpoint that shows route-token assignment, worker id, and validation mode for the active call without leaking secrets?
