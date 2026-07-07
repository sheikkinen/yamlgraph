# The Acceptance Run Condemns the Gate

**Date:** 2026-07-07
**Context:** Enforcing FR-691 (plot threads + throughlines). Five pure gates written TDD-first, all 24 unit tests green. Then the real Floodmark canon ran through the pipeline — and two green gates returned `valid: False` on artifacts a human reads as obviously correct.
**Trap:** `plausible_wrong_answer` in the *validator* — a gate whose unit tests pass because the tests share the author's wrong model of the domain.

## The Observation

The gates were beautiful and wrong. Both defects were invisible to the unit suite because I wrote the fixtures and the gate from the same misconception:

1. **Ledger walk assumed balanced raise/release.** Ported from `dungeon_master`'s `validate_plan`, the gate decremented an "open" counter on each release and flagged an underflow. Every unit fixture I wrote paired one raise with one release, so it passed. Then `hilde_gunnar_feud` arrived from the canon: **one** raise (`dawn_raid`) opening a feud that de-escalates over **four** releases (`ledge_stranding`, `deer_recovery`, `clan_divide`, `bonding_rite`). The gate condemned a real, correct thread. A feud does not re-escalate before each step of its dissolution — it opens once and unwinds. My arithmetic model of plot was wrong, and only real plot exposed it.

2. **Distinctness keyed on carriers alone.** The gate rejected `ledge_survival` as a duplicate of `hilde_gunnar_feud` because both are carried by {hilde, gunnar}. But a *feud* and a *survival crisis* between the same two people are different threads — distinctness is `(kind, carriers)`, not carriers. Again: every unit fixture used distinct carrier sets, so the bug slept until two same-carrier threads of different kind met in production.

Both fixes followed the rite: a condemning test first (`test_one_raise_many_releases_passes`, `test_same_carriers_different_kind_passes`), confirmed RED (2 failed / 24 passed), then the gate change, then GREEN (26 passed) — and the same gates now return `valid: True` on the persisted artifacts.

## The Diagnosis

TDD proves the code matches the test. It cannot prove the test matches the world. When the author writes both the gate and its fixtures from one mental model, a green suite certifies internal consistency, not correctness — the unit tests and the gate are two projections of the same assumption, so they agree by construction. This is `plausible_wrong_answer` relocated into the validator: the gate produces a shaped, confident verdict that is semantically wrong, and it is *harder* to catch than a crash because green is the color we trust.

The cure was not a better fixture — I could not have invented these fixtures, because inventing them requires already knowing the domain fact I lacked. The cure was **running the gate against real data I did not author**. The Floodmark canon is an adversarial witness the unit suite could never be: it encodes plot semantics (feuds de-escalate; same people, different conflict) that my synthetic fixtures smoothed away. This is why the Scripture's acceptance-before-enforce step (CAP-116) exists — the acceptance run is not a smoke test, it is the test. It is where the domain gets to disagree with the author.

Note the asymmetry with `read_raw_output_first`: there, the LLM's raw output was the untrusted artifact and the cure was to *read* it. Here the gate is deterministic and the *input* is the untrusted witness — the cure was to *run against real canon and read the violations*. Same law, dual boundary: never trust an artifact you generated to test an assumption you hold.

## Heuristic

**A gate whose fixtures and logic share one author shares one blind spot; run it against real, un-authored data before trusting green.** Unit tests certify that the gate matches its fixtures. Only data you did not write can certify that the fixtures match the world. For any mechanical validator of a domain you are still learning, the acceptance run against real artifacts is the RED that matters — schedule it before declaring the gate done, and treat its first `valid: False` on a hand-verified-correct artifact as a bug in the gate, not the artifact.

## Seed

The two defects were both *over-strict* — the gate rejected valid plot. Over-strict gates get caught because someone stares at a `valid: False` on obviously-good output. But the dual failure — an *over-lax* gate that passes invalid plot — leaves no such trace; a `valid: True` on subtly-broken output is silent. The FR-691 review already found one: the reconcile prompt returned zero latent threads against a canon loaded with `internal_tensions`, and no gate complained because "zero latents" is not yet an invariant. **Seed:** what is the mechanical signature of an over-lax gate — can a validator carry a paired "this should have found something" assertion (a floor, not just a ceiling), so that a suspiciously-clean pass is itself condemnable? When does absence of violations become the violation?
