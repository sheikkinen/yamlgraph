---
type: fix
scope: examples
---
- **DM v2 LLM failure/denial feedback**: A declined or failed generation is now
  shown to the DM instead of vanishing. An empty completion (the shape a Vertex/
  Gemini content-policy block usually takes) is surfaced as a "request declined"
  message rather than silently blanking the card, and the blank is never persisted
  over the draft (Commandment 6). A provider error recorded by the graph surfaces
  its real reason. The failure renders as a banner above the card — keeping the
  breadcrumb and the DM's draft intact for an in-place retry — and returns 2xx so
  htmx actually swaps it in (a 4xx body was previously dropped, leaving no feedback
  at all).
