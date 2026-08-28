# Diary — 2026-08-28 — The ruler that measured itself kindly

**Arc:** FR-900 — ledger cache-price fix + monthly repo×model cost report.

The operator asked for August costs by repo and model. The ledger's answer
($796) was 10% of the invoice ($7,500). The troubleshoot took three tool
calls, and the decisive one was `read_raw_output_first` applied to a PRICE
SHEET: dumping the raw billing block for one model showed the schema keys
are `cache_read_price` / `cache_write_price` — the parser read `cache_price`,
which has never existed, so every model's cache reads were priced at zero
and the "calibrated 98%-cached best bound" silently priced 98% of all prompt
tokens as free.

**The trap worth naming:** *calibration under a bug becomes doctrine.* The
old docstring carried an anchor — "pure-cache pricing hit 814 cr vs 820.5
actual" — that is arithmetically impossible under the cache=0 defect
(pure-cache would have priced ≈0). The anchor was recorded, trusted, and
cited in the module header for six weeks. A calibration claim is only as
good as the arithmetic that produced it, and nothing re-checks a docstring.
This is `plausible_wrong_answer` in comment form: the number passed shape
checks (it was near another number) and lent false authority. The cure
applied: AC-08 made *removing the stale claim* an acceptance criterion, and
the new anchor records its provenance (invoice, two-device assumption) so a
successor can re-derive it.

**Second observation:** the defect was invisible to every downstream
consumer because zero is a valid price. `gpt-3.5-turbo` legitimately costs
0; a missing key also yields 0. The boundary (`parse_price_sheet`) now
exists as a testable seam, but the deeper lesson is the one_law again —
the models.json schema is a PROVIDER boundary and got no normalization
test when first crossed in July.

**Mechanics friction, for the record:** the RED commit bounced four times
(process-boundary mark, prior-art disposition ×3 files, board drift, noqa
confession, ARCHITECTURE sync) — every bounce a known gate from the
precommit-dry-run memory note, which I consulted only after the first
bounce. Reading one's own memory BEFORE the first commit attempt remains
cheaper than any retry cycle.

**Seed:** a docstring calibration claim is an untested assertion about
arithmetic. Could the confessions/gate machinery host a *calibration
registry* — each anchor line in code paired with a script that re-derives
it from committed evidence, failing CI when the claim and the arithmetic
diverge? The anchor-2 fiction would have died in July.
