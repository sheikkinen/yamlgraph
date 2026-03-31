---
type: feat
scope: doctrine
---
- **FR-191 Graduate `plausible_wrong_answer` Trap**: Refined trap description from variant-specific ("Silent fallback harder to catch than crash") to pattern-general ("Output passes shape check but is semantically wrong → add assertion beyond type validation"), based on 4 confirmed diary occurrences (FR-165, FR-164, FR-184, FR-185).
