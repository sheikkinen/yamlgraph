# Read notes — FR-881 demo run (read_raw_output_first, AC-09)

Enforcer read of the three selected candidates (full text in the local
table, not committed; hashes below match the sanitized table).

1. `4e747dbe812d` — the `--start` seed "tom of sweden, " steered the
   continuation toward figure-study vocabulary ("tall crimson…
   surreal proportions… comic image") — the seed conditions content,
   not just the opening chars. Invented word "esserting" mid-stream;
   ends cleanly at `<|end|>` with no tag-block coda.
2. `8f5b53cd1666` — longest survivor; drifts from `<prose>` register
   into a full booru coda (`score_9… BREAK,`) — the register-bleed
   pattern from the FR-876 t0.5 sheets recurs at t0.8 in long samples.
   "surrealistic catachedral pople" is char-level phonotactic invention.
3. `5806d3a2edf2` — mixes prose sentence shape ("The scene should in a
   blond of the code") with metadata tags (`source_seret,
   rating_explicit`) — misspelled invented tag `source_seret` shows the
   model reproduces the tag SLOT more faithfully than tag lexemes.

Run-level: 10/12 attempts passed (2 shape rejections, consistent with
the 165/200 t0.8 witness); every candidate carries
`ckpt_sha cd0fb5c2f171 / corpus_sha 5907e2848ca3 / git_sha 6c30063` —
the artifact-carries-code-identity stamp verified in the wild.
