# 2026-08-20 — The Cookbook Was a Policy Probe

Planning Oulu Civic Intelligence Daily looked like choosing three APIs and
writing a reproducible issue. The acceptance case instead found a contradiction
in gitclaw before any public repository or token was spent: README says feature
tools are expected, graph-authoring doctrine permits optional tools, but the
judge prompt requires graph plus prompts only and rejects external side effects
beyond commit-back. Whether a public GET counts as forbidden was left to model
interpretation — exactly where a frozen policy must not be ambiguous.

**Trap: treating acceptance as downstream confirmation.** If the test is
designed after implementation, it confirms the path the author already chose.
Here, deriving the acceptance fork from a real control-plane use case forced a
new capability class through every contract and exposed that the advertised
tool surface and enforced judge surface disagreed. The cheapest acceptance run
was the one stopped before repository creation.

**Heuristic:** before instantiating a cookbook, pass its defining capability
through the template's actual judge contract. Documentation describes intended
surface; the gate defines executable surface. A disagreement is a policy bug,
not an invitation to phrase the issue more cleverly.

**Seed:** can each gitclaw policy class have one static contract fixture — pure
LLM, read-only public tool, persistent state, and forbidden external write — so
the judge's capability boundary is tested before a live issue pays for it?
