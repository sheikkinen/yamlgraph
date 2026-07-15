---
type: fix
scope: examples
req: REQ-YG-554
---
- **ICPC-2 language-invariance fixtures + attribution fix**: HP-36 translated to English and German as labeled fixtures with identical expectations — both pass the primary gate first-shot (`-50` primary, 8/8 agreement with the Finnish original), and the A13 residual proves language-invariant (semantic inflation, not a Finnish artifact). Harness attribution hardened from prefix-startswith to exact name + timestamp anchoring (`hp36-…-en` archives no longer misattribute to the prefix fixture); German runs exposed a cross-lingual composition-context mechanism ("Blutdruck" lexically primes the B-chapter cluster → B50/B99 where fi/en compose K50/K86) — recorded on the watch list. (REQ-YG-554)
