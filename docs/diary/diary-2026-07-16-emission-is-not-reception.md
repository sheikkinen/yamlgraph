# 2026-07-16 — Emission is not reception

**Context:** FR-737's first field firing (NC-393, ninchat_voice), usage
review appended to the FR by the agent it fired at.

**The defect, named:** I shipped a retrieval channel whose entire value
proposition was "the warning lands in the acting agent's context" — and
never witnessed that claim. The hook fired, the audit log said
`feedback`, the human saw the block; the authoring agent's tool result
carried nothing, and the FR went to origin undispositioned. 72 tests
exercised *emission* through `run_hook`, which simulates the harness.
Reception on the real surface: zero tests, zero ACs. The
`mock_escape_hatch` trap in hook-test costume — a unit suite posing as
E2E with respect to the one channel the feature exists to cross.

**The sharper irony:** twenty-four hours earlier I judged FR-736 and
priced its "semantics-neutral" ruling with a wire-fidelity witness —
*a claim that grants convenience must attach the mechanism that would
catch its own error.* Then I enforced FR-737 carrying an unwitnessed
wire claim of my own. Judging others' claims adversarially is easier
than noticing which of my own sentences are claims. The tell, in
retrospect: any sentence of mine containing "lands in" or "reaches" or
"can't fail to see" is a wire claim, and wire claims need one observed
real transit, not N simulated ones.

**The failure's shape is the original incident in miniature.** The
FR-070 resurrection taught that human vague memory was the only
functioning retrieval channel; the cure's first firing taught that
human eyeballs are still the only functioning *delivery* channel. Both
times the mechanical path failed silently and the human path worked.
The system's honest current state: the hook is a human-notification
device with an agent-notification aspiration.

**The cure is boundary relocation, not channel repair.** U-1's
backstop — re-run `prior_art.py` at pre-commit for new FRs, fail when
hits exist without a `**Prior art:**` disposition line — moves the
check to the merge-boundary gate Scripture already names, where
"unseen" is impossible because the gate blocks. Layering: PostToolUse
stays as the fast advisory *when* the channel works; pre-commit is the
floor *whether or not* it does. Repairing the PostToolUse delivery
(why doesn't `emit_result` reach the tool result on this surface?) is
worth one investigation — but the gate must not wait for it.

**What worked deserves the record too (U-4):** cross-project firing,
skimmable format, status-tag triage, and the human loop closing
end-to-end — the omission was caught and retroactively dispositioned on
first firing. An instrument whose first live use finds a real defect
in its own delivery *and* a real omission in its target is earning its
keep twice.

**Seed:** the usage-comments section itself — structured field feedback
(U-1..U-4) appended to a Completed FR by the agent it fired at, follow-
ups pre-named — worked so well it looks like a missing FR lifecycle
stage: Proposed → Judged → Completed → **Field-reviewed**. Should the
first real firing of any enforcement mechanism mandatorily produce a
usage review, the way feat/fix mandates a diary? The gate that has
never fired in anger is unproven; the gate that fired and was reviewed
is calibrated.
