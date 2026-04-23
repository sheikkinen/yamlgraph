# Reflection: FR-191 Diary Filename Normalization

**Context:** Implementing diary filename convention enforcement at creation boundary in watcher2 critique step to prevent CI diary gate failures through TDD discipline.

**Trap:** **downstream_fix** — Initially focused only on CI gate validation without addressing root cause. The instinct was to add more downstream checks rather than normalize at the creation boundary where the problem originates.

**Heuristic:** Normalize at the boundary where external data enters, not where symptoms manifest. When enforcement exists downstream but creation lacks guidance, move the constraint upstream to the source. The Scripture's "the_one_law" proved foundational: fix at creation, not detection.

**Seed:** How might we apply boundary normalization patterns to other development pipeline constraints? Could pre-commit hooks become a general framework for creation-time validation rather than just post-hoc checking?

---

**Implementation Notes:**
- Successfully applied TDD Red-Green-Refactor with 11 comprehensive acceptance tests
- Achieved 6/7 acceptance criteria (missing documentation update)
- Pre-commit hook design required iteration to handle existing files pragmatically
- Requirement ID confusion (REQ-YG-191 vs REQ-YG-188) revealed importance of capability registry alignment

**Technical Decisions:**
- Case-insensitive regex for existing files to avoid forced normalization
- Scoped hook to files with 'fr' in name to prevent false positives
- Blocking critique failure aligns with Scripture Commandment 6: "expose every fault"