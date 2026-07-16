# 2026-07-16 — The instruments' first day of school

**Context:** "reflect. run the tools generated in this session." Ran
all five (tap.py, now.py --tap, ledger.py --tap, fr_board.py own +
ephemeral). The run WAS the reflection: every tool built today was
tested today by reality, and reality graded harshly and fast.

**The scoreboard, one day old:**
- `tap.py`: 17.8 MB, 368 calls, $162 (cache-calibrated) across four
  sessions since 11:54. Witness #3 arrived, the ETA unlocked — and
  was **immediately wrong** (ETA≈0 for everyone).
- `ledger.py --tap`: c0f1927c still 1.01 across 37M tokens; my own
  session climbed 0.27 → 0.71 → 0.85 as chatSessions catches up —
  the self-measurement lag converging exactly as documented.
- `now.py --tap`: 3 LIVE + 1 gone-quiet, correct; but TEMPLATE.md
  listed as an "FR in motion" (it matched the Status regex — the
  board excludes it, its sibling forgot to).
- `fr_board.py`: own-repo check green post-F7; the ephemeral view
  still renders the cross-repo aggregate on demand.

**The phantom witness — the day's best lesson.** The third
"compaction" was 91,846 → **0**: a cancelled turn, not a guillotine.
One poisoned record in a three-record calibration set and
`min(peaks)` collapsed; the feature that had *just unlocked* reported
ETA≈0 for every session — precise, urgent, and wrong. The fix was
RED-first and one conjunct (`and cur`), but the shape is the
teaching: **a calibration set is a boundary**, and the smaller it is,
the more one bad record costs. The judgement's ≥3-witness gate
guarded against *insufficient* data; nothing guarded against
*corrupt* data. Validity checks on witnesses (post must be a summary,
not zero) matter more than count thresholds when n is tiny.
Corollary of `gate_checks_shape_not_substance`, met in our own
instrument within six hours of writing the gate.

**What survived contact:** the two genuine witnesses agree within
0.5% (746,876–750,382) — the compaction ceiling looks real, stable,
and worth trusting soon. The traceId join, the seam, the rotation,
the F7 boundary — all held unattended. And the day's meta-pattern
held a third time: FR-739's judgement caught the merged-stream
phantom *before* code; FR-740's F7 caught the repo-boundary leak
*after* ship via human review; the phantom witness was caught *after*
unlock via running the tool. Defense depth in time: judge, review,
run. Each rung caught what the previous one structurally could not.

**Named:** `first_unattended_hours_are_the_real_judge` — a tool's
acceptance tests prove it can work; only its first unattended hours
prove what it does with data nobody curated. Schedule the first
re-run of any new instrument as deliberately as the RED — same-day,
eyes open, expecting a defect, because there will be one and it will
be cheap now and expensive after trust forms.

**Seed:** the two real witnesses put the guillotine near 750K ±0.5%.
My session reads 238K at +687/turn — hundreds of turns of headroom,
but 854c6a35 compacted twice today, so real arcs hit the wall daily.
Next concrete move: `now.py` prints a flush advisory when level >
650K (86% of the witnessed floor) — rung-2 delivery of the one
warning that protects an agent's mind, using the calibration the
suite now collects and *validates*.
