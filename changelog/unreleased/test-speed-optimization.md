---
type: feat
scope: testing
req: REQ-YG-275
---
- **FR-275 Test Speed Optimization**: Added pytest 'slow' marker infrastructure for selective test execution during development. Tests taking >1 second marked with `@pytest.mark.slow`; configurable `TEST_DELAY_SCALE` environment variable enables accelerated timing; ultra-fast, fast, and slow-only test commands documented in CLAUDE.md for improved development workflow. (REQ-YG-275)
