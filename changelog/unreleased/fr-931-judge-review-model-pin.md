---
type: feat
scope: judge
req: REQ-YG-632
---
- **FR-931 Judge/Review Model Pin**: The judge and review sole routes
  now pin `gpt-5.6-sol` instead of `gpt-5.5` (later generation, 272k vs
  200k default prompt window, and cheaper at 200/1000 vs 500/3000 credits
  per 1M input/output tokens). A witness test asserts both routes carry a
  non-empty `cli_flags.model` and that the two pins agree, so the pin can
  no longer drift to the CLI ambient default or diverge between routes.
  The authoring adapter is deliberately unchanged. (REQ-YG-632)
