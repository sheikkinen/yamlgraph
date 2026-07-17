# 2026-07-17 — The full board, and the ceiling that wasn't one thing

**Context:** "check the now in full. diary." Ran `now.py --tap` — the
complete situation board, every instrument from the 48-hour arc in one
view: 4 live sessions × 8 repos (staged=0, no hazards), FRs in motion
across both repos, plan-state pointer (197 rows), deep-history pointer
(recap), **world pointer (updated 0d ago — fresh as of FR-744 this
morning)**, tap ground truth with altimeter, and live claims with a
STALE flag. Past, present, future, and now world — one command. Then
the routine harvest run turned over two rocks.

**Rock 1: the polling instrument only records when polled.**
`record_compactions` runs in tap.py's main, and nobody had run tap.py
since morning — the board displayed the Enforcer's afternoon
compaction (443K → 95K) while the calibration file still said two
witnesses. The witness harvest is a side effect of a *voluntary* read:
`a_view_without_a_reader` has a sibling — **a sensor without a
schedule records only what its operator happens to see.** The tap file
itself is always-on; the *derivation* (witness extraction) is
poll-gated. Cure candidates: harvest inside now.py's tap section (the
briefing is run often) — one line, FR-739 amendment territory.

**Rock 2: five witnesses killed the single-ceiling model.** The
harvest jumped 2 → 5 and the new witnesses broke the theory the first
two had suggested: peaks at 750,382 and 746,876 (the structural
ceiling, 0.5% apart) — but also 468,932, 527,766, and **228,589**.
Compaction is not one phenomenon: there is a hard ceiling AND
mid-level events (manual /compact, or other triggers) scattered from
228K to 528K. And the ETA logic — conservatively aimed at
`min(peaks)` per the judgement — instantly degenerated: every session
above 228K now reads **"ETA≈0 turns"**, which is vacuous alarm at
board scale. The phantom-witness lesson recurs one level up: last
time a *corrupt record* poisoned the calibration; this time **five
valid records poisoned a wrong model**. Validity checks on witnesses
were necessary but not sufficient — the model over the witnesses is
its own boundary. The conservative choice (min) was correct at n=2
and wrong at n=5; conservatism is not a substitute for a model that
matches the phenomenon's actual structure (bimodal: structural
ceiling vs voluntary events).

**Also witnessed, quietly:** the tap file crossed 100 MB and the
FR-739 rotation fired in production — archive stamped, exporter fd
preserved, reading continued from the archive. AC-05, judged five
days of subjective time ago (yesterday), working unattended. Some
things do survive contact.

**Distilled:** `witnesses_validate_records_not_models` — a
calibration set can be clean while the curve fitted through it is
wrong; every model over field data needs its own falsification check
(here: "are the peaks unimodal?" — answerable by eyeballing five
numbers). And the smaller heuristic: any derivation that runs as a
side effect of a voluntary command will silently lag reality — put
harvests on the most-frequently-run path, not the most logical one.

**Seed:** split the ETA into two questions the data now supports:
distance-to-structural-ceiling (max-cluster ~750K — the involuntary
guillotine) vs "sessions like you also compacted voluntarily around
X" (the mid-level cluster — advisory, not alarm). Three more
witnesses will tell whether the mid-level events cluster at all or
are uniform noise. Second seed: FR-742's posthumous-diary pipeline
assumed sessions die at the ceiling; mid-level voluntary compactions
mean diary debt can occur *without* a session ending — does the
Distill obligation attach to compaction events too?
