---
type: feat
scope: hooks
---
- **FR-738 Prior-Art Disposition Gate**: the floor under the FR-737 advisory — a newly added `feature-requests/*.md` with prior-art hits and no `**Prior art:**` line in the **staged blob** fails the commit (`prior-art-gate` pre-commit hook; an unstaged marker doesn't count). Ranking gains placement weighting (filename/H1/Summary = 2, body prose = 1; ties by matched-noun count) and judgement companions inherit their parent FR's status. FR-070 counterfactual re-measured: [REJECTED] at #2, score doubled. Boundary stated honestly: repo-scoped — the ninchat mirror is NC-394.
