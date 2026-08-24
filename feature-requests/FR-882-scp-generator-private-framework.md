# Feature Request: FR-882 SCP Generator Framework — Private Corpus-to-Canon Pipeline

**Priority:** LOW
**Type:** Feature
**Status:** Proposed
**Effort:** 2–3 days
**Requested:** 2026-08-24
**First consumer / first event:** the operator, privately: run one
command in a fresh private `scp-lab` clone and get a boundary-gated,
critic-ranked SCP-register containment document to read for enjoyment.
No publishing pipeline exists or is planned; nothing trained or
generated leaves the operator's machines. The product is the private
reading experience plus the framework that produces it.

## Summary

A private sibling repo (`scp-lab`, working name) hosting the full
FR-876/FR-879 architecture transposed to prose: extract a CC BY-SA 3.0
corpus slice from the SCP wiki via the Crom GraphQL API → train the
proven TinyGPT-scale critic (and optionally a generator rung) on the
containment-doc and tale registers → generate candidate documents with
a frontier LLM → score/band/boundary-filter → render the survivor for
private reading. yamlgraph governs (this FR) but gains no code; a
`crom-probe.sh` lands in the sibling `control-plane/probes/` collection
first, proving API access and data shape before any pipeline exists.

## Value Statement

The operator gets private, on-demand SCP-register fiction gated by a
frozen style critic — and the third witnessed instance of the
corpus→critic→filter architecture (images: FR-879; prompts: FR-876;
prose: this), proving the pattern generalizes across media.

## Problem

- The SCP register is the best available corpus for the critic
  architecture: CC BY-SA 3.0 (rights-clean, unlike sitcom), extreme
  mechanical house style (learnable FORM per FR-876's central finding),
  tens of millions of tokens (30× deviant corpus), a natural register
  split (containment-doc vs tale ≙ `<tag>`/`<prose>` conditioning), and
  community vote scores — thousands of (text, quality) labels no other
  corpus offers.
- The existing pipelines have no prose instance of generate→score→
  filter; novel_fandom has typed-canon gates but no style gate.
- Frontier LLMs write *approximate* SCP pastiche; the register's rigid
  skeleton and redaction conventions are exactly what a frozen critic
  can band sharply — the filter has real work to do here, unlike the
  FR-879 flagship run (zero rejections on a corpus-adjacent brief).

## Ideal Result

In `scp-lab`: `make read` (or equivalent single command) drafts N
candidate containment documents via the `.env` provider, scores them
against the per-register calibrated critic, applies the deterministic
structure gate (required sections present, redaction syntax
well-formed, item number unclaimed in the local canon), and opens the
top survivor for reading — with a rejection table showing why the
others died. The local canon accumulates what the operator chooses to
keep. Everything — corpus, checkpoints, generated canon — stays
private; the only public artifacts are this FR, its judgement, and the
control-plane probe.

## Proposed Solution

**D-A: `crom-probe.sh` in `../control-plane/probes/`** (the 51-probe
convention: phased curl+jq, prove before build):
- Phase 1: Crom GraphQL endpoint reachability, schema introspection.
- Phase 2: fetch one known SCP page — text, rating, tags, license
  block, attribution metadata.
- Phase 3: pagination + rate-limit behavior; estimate corpus slice
  sizes (containment docs vs tales by tag).
- Phase 4: license field audit — confirm CC BY-SA marking per page and
  attribution requirements (author, source URL).

**D-B: private repo `scp-lab`** (new; scaffolds by *copying* the
generic modules from deviant-daily `training/` — model.py, boundary
shape, score.py structure — with provenance headers; the deviant
corpus-specific blocklists do NOT transfer, SCP needs its own
extraction policy):
- `extract/`: Crom API client → corpus JSONL
  `{text, register, rating, tags, author, url}`; operator-reviewed
  content policy at the extraction boundary (the wiki includes
  gore/adult pages; exclusion list is an operator decision recorded in
  the repo, per the FR-826 C-4 pattern); attribution manifest generated
  mechanically (CC BY-SA obligation, kept even though private).
- `training/`: prepare (register prefixes `<doc>`/`<tale>`, seeded
  split), train (the FR-876 recipe, scaled: block 512, ~10M params
  budget permitting), score (per-register calibration, FR-879
  contract: JSONL rows, provenance stamps, truncation flags).
- `generate/`: frontier-LLM drafting node + critic reranker + a
  deterministic SCP structure gate (sections, redaction syntax, item
  number registry) — the code-not-model gate the register uniquely
  affords.
- `eval/`: R-1-style fixture set (genuine SCP held-out / frontier
  pastiche / off-register prose / degenerate) + the vote-correlation
  study: does critic NLL correlate with community rating? (Prediction
  recorded now, FR-879-style: weak — style is necessary, not
  sufficient. The raw read decides.)
- Rejection-statistics table per rung (Markov baseline / critic-ranked)
  as the evaluation, per the FR-876 pattern.

**Explicit non-goals (frozen):** no publishing pipeline of any kind
(no DA, no wiki posting, no GitHub Pages); no published model weights
or corpus redistribution (private repo; CC BY-SA share-alike never
triggered by private use); no yamlgraph core changes; no voice/cast
work (that is the separate stylometry thread); no SCP wiki
contributions.

## Acceptance Criteria

- [ ] AC-01: `crom-probe.sh` in control-plane/probes/ passes all four
      phases; output committed there per probe convention.
- [ ] AC-02: Extraction produces a corpus JSONL with per-row register,
      rating, attribution; operator-approved exclusion policy recorded;
      mechanical scans (paths/tokens/emails) pass; attribution manifest
      generated.
- [ ] AC-03: Training witness per FR-876 R-4 discipline: seeded,
      device/params/wall-clock/git-SHA logged, loss threshold frozen
      BEFORE the run and not lowered after.
- [ ] AC-04: Scorer with per-register calibration and the FR-879 JSONL
      contract; tests for band edges, truncation, malformed input,
      provenance (adapted from deviant-daily's suite).
- [ ] AC-05: R-1 fixture read: ≥5 scored rows spanning genuine SCP /
      pastiche / off-register / degenerate, each with a concrete
      observation, BEFORE the generate stage is built.
- [ ] AC-06: Deterministic structure gate rejects missing sections,
      malformed redaction blocks, and item-number collisions; witnessed
      by tests.
- [ ] AC-07: End-to-end private read: N candidates → rejection table →
      top survivor; the table read with per-candidate notes; evidence
      stays in scp-lab (private).
- [ ] AC-08: Vote-correlation fixture run and READ (spearman + scatter
      + 5 raw outlier reads); result recorded whatever it shows.
- [ ] AC-09: yamlgraph gains no code; this FR + judgement + status
      updates are its only artifacts (plus the probe in control-plane).

## Alternatives Considered

- **Host in yamlgraph examples/:** rejected by operator decision
  (2026-08-24) — corpus and checkpoints are private-by-nature here;
  a public repo hosting CC BY-SA-derived tooling with gitignored data
  invites accidental commits (FR-874 lesson).
- **Fine-tune an open model (LoRA) instead of the from-scratch critic:**
  deferred, same rationale as FR-876 — different lesson, double scope;
  the critic + frontier-generator split is the proven shape. May be a
  follow-up FR after AC-08's evidence.
- **Scrape the wiki HTML directly:** rejected — Crom API exists,
  respects the community's infrastructure, and carries license/rating
  metadata the HTML scrape would have to parse fragilely.
- **Public generator with published model:** explicitly excluded by the
  operator's framing ("enjoy privately"); also avoids the share-alike
  and content-rating questions entirely.

## Prior Art Disposition

**Prior art:** FR-876 (parent architecture: training demo, boundary,
witness discipline — reused wholesale, corpus swapped); FR-879 (critic
contract, calibration, R-1 fixture discipline — the scorer is a port);
FR-655/novel_fandom (typed canon + deterministic reference gates — the
structure gate extends this idea to register syntax; no code shared);
034-novel-generator-demo (LLM-consumer story demo, no training, no
overlap); FR-826/FR-862 (precedent for governing private/sibling-repo
work from a yamlgraph FR). None trains on licensed third-party fiction
or builds a prose critic; territory is new.

## Related

- ../control-plane/probes/ (51-probe convention this extends)
- feature-requests/FR-876-minimal-llm-training-demo.md (+ judgement)
- feature-requests/FR-879-image-pipeline-v2-critic-filter.md (+ judgement)
- examples/novel_fandom/ (typed canon gates)
- Session reflection 2026-08-24: SCP as the rights-clean style corpus;
  voice/stylometry thread deliberately excluded from this FR.

## Decisions (operator, 2026-08-24)

1. **Framework host:** new private sibling repo (`scp-lab`).
2. **Probe location:** `control-plane/probes/crom-probe.sh`.
