# FR-167 Reflection: Removing the Copilot Trailer

**Trap:** `audit_as_ritual` — 3+ audits without fix is ritual, not process.

**Insight:** The Copilot `Co-authored-by` trailer was flagged CALCIFIED-4 through CALCIFIED-6 across five consecutive Inquisitor audits. The proposed cure (FR-132: pre-commit enforcement) would mechanize a ritual that served no functional purpose.

**Heuristic:** When an audit criterion repeatedly yields violations without clear value, question the criterion, not just the compliance gap. Metadata injected by tool conventions is not the same as project requirements.

**Seed:** What other conventions are we enforcing simply because tooling defaults to them?
