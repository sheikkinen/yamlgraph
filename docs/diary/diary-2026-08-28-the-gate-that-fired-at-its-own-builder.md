# The Gate That Fired at Its Own Builder

**Date:** 2026-08-28
**Context:** FR-896 enforcement — precedent traceability for the research
route, built and then immediately dogfooded on its own defect brief.

## What happened

The enforce phase ran the freshly hardened route four times live. Every
failure was a designed gate firing, and every firing taught something
the tests had not:

1. **Run 1:** three personas overflowed the 400-character ceiling. The
   rejection-not-truncation contract held — the run died loudly instead
   of shipping trimmed prose. But the repair exposed a prompt-physics
   fact: character counts are unenforceable instructions for an LLM;
   word and sentence caps hold. The schema constraint is the boundary;
   the prompt phrasing is only aim assistance.
2. **Run 2:** one persona still overflowed. Per `two_strike_split`, no
   third rewording — node-level `on_error: retry` mechanized the
   recovery. Notable: temp-0 Anthropic calls are not bit-deterministic,
   so retry against a hard code gate is a legitimate lever, not a hedge.
3. **Run 3:** the reducer rejected `corpus_census` as an "unknown
   Scripture key". The token names a committed demo directory. My own
   fail-closed validator produced a false positive on genuinely
   committed state — the gate fired at its builder. Witness test first,
   then the fix (bare snake tokens naming committed demo/graph dirs are
   valid citations).
4. **Run 4:** clean. Five rows, five non-echo, zero echo verdicts,
   every internal precedent a validated committed identifier, the
   librarian reporting genuine world precedent (Registered Reports)
   with a reconciled URL.

## The trap

**Gate false positives are a distinct defect class from gate bypasses.**
I spent the FR's whole design budget on preventing echo and fabrication
(rows that should fail but pass), and none on citations that should
pass but fail. The identifier universe of a living repo is larger than
any enumeration made at design time — Scripture keys, FR/CAP numbers,
and paths were my closed list; demo directory names were real committed
state outside it. A fail-closed gate over an under-enumerated identifier
universe converts correct citations into run failures. The cure was not
loosening the gate but widening the recognized universe — with a witness
test extracted from the live failure before the fix, exactly the
Scripture's condemn-then-fix rite compressed into ten minutes.

## Heuristic

When building a fail-closed validator over "things that exist in the
repo", the enumeration of existence-checks is itself a boundary — test
it with citations you did NOT think of while designing, ideally by
running the gate against live model output before freezing it. The live
run is the adversarial fuzzer you cannot write yourself.

## What the dogfood proved

The baseline run (2026-08-28 morning) had a verbatim brief-echo row that
passed every gate. The upgraded route's rerun of the SAME brief produced
zero echo rows and five committed-identifier-grounded findings. Not
because the model got smarter — because the reducer now refuses the
lazy path, and haiku, denied echo, went and found CAP-17, CAP-237, and
Registered Reports instead. Constraint produced capability.

**Seed:** the retry handler logs "failed after N attempts" and discards
the underlying exception detail — diagnosing run 3 required grepping the
first-attempt log line. Should `handle_retry` carry the last exception
message into its final error log line, so live-run forensics don't
depend on the first attempt happening to log before the retry wrapper
swallows it?
