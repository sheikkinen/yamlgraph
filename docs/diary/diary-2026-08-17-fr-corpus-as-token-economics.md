# Diary: FR Corpus as Token Economics

**Date:** 2026-08-17
**Context:** Reflection on the FR system's representation efficiency

## Observation

The FR corpus (779 files, 7.6MB, ~1.9M tokens) is consumed exclusively by LLMs — judge, enforce, review, inquisitor. No human reads them end-to-end. English prose is a convenience inherited from human-readable documentation, not an optimality choice for the actual consumers.

## The Trap

**framework_costume** variant: the FR system wears a "human documentation" costume but its actual consumers are token-processing machines. The prose structure (Value Statement, Alternatives Considered, Related) forces authorial thought — valuable at write-time — but persists as dead weight at read-time.

## Insight: Two-Phase Lifecycle

The FR has two distinct consumers at two distinct moments:

1. **Author at write-time** — needs prose to force clarity (thinking tool)
2. **LLM at judge/enforce/review-time** — needs structured semantics (decision tool)

These are different encodings for different purposes. The current system uses one encoding for both.

## Token Economics

| Format | Avg size | Tokens (est.) | FRs fitting 128k context |
|--------|----------|---------------|--------------------------|
| Current English prose | 10KB | ~2,500 | ~50 |
| Compact YAML | 2-3KB | ~600-750 | ~170-210 |

A 3× improvement in context density means the judge sees 3× more precedent. The `prior-art` hook becomes mechanically stronger.

## Research Direction: Corpus Compression

Transpile existing 779 FRs to compact YAML format. Empirical questions:

1. **Information loss**: What % of prose is load-bearing vs boilerplate?
2. **Judge fidelity**: Does verdict quality degrade on compressed input? (A/B test on ~20 FRs with known judgements)
3. **Round-trip**: Can compressed form reproduce original judgement findings?
4. **Tokenizer behavior**: Does structured YAML actually tokenize more efficiently than prose? (Measure, don't assume — BPE may surprise)

The transpilation itself is a YAMLGraph pipeline: `FR prose → LLM extract → structured YAML → validate fields present`. Dog-fooding opportunity.

## Counter-considerations

- **gate_checks_shape_not_substance**: Compact format makes it trivially easy to file hollow FRs that pass structural validation
- **Ambiguity as feature**: During `Proposed` status, English ambiguity allows the judge to probe intent; YAML forces premature precision
- **Scripture legibility**: The Scripture cites FR content in traps/cures — those citations assume English

## Evolution Analysis: Builder Specs → Governance Artifacts

Tested hypothesis: "Early FRs contain more technical detail, later ones are abstract."

**Result: Partially wrong.** The shift is not abstraction — it's bureaucratization.

| Dimension | Early (FR-071–082) | Late (FR-808–813) |
|-----------|--------------------|--------------------|
| Code blocks | 4-10 per FR | 2-8 per FR |
| Words | 678-1568 | 1013-1302 |
| Sections | 7-8 (informal) | 10-12 (formulaic) |
| Added sections | — | Value Statement, Ideal Result, First Consumer, Implementation Record |
| Content character | Builder spec (file layouts, YAML config) | Governance artifact (regulatory refs, provenance, prior art) |

The template grew from 7 sections to 12. Each FR now carries its genealogy.

## The Causality Layer: Extractable Graph

Late FRs embed a **causal graph** in prose. Relationship types found (FR-800–813):

| Edge type | Occurrences | Semantics |
|-----------|-------------|-----------|
| Prior art | 47 | "this FR is aware of and distinct from" |
| Dependency | 30 | "blocked until this FR is enforced" |
| First consumer | 26 | "this named event triggers the need" |
| Substrate | 7 | "built on top of, consumes contracts from" |
| Blocked until | 4 | hard activation gate |
| Governed by | 3 | "authority derives from" |
| Seed origin | 2 | "this idea originated in diary/FR X" |
| Parent plan | 1 | "part of a larger roadmap" |
| Regression | 3 | "broke something introduced by" |

**This is a DAG hidden in prose.** Each FR spends 30-50% of its tokens establishing its position in this graph — which FRs it depends on, which it supersedes, which diary entry spawned it, which regulatory requirement justifies it.

### The Extractable Structure

```yaml
# Causality map (what's actually load-bearing in FR-813)
FR-813:
  caused_by: FR-811  # introduced the regression
  substrate: [FR-811]  # OTel runner boundary
  first_consumer: {who: ninchat_voice, event: "NC-434 node-recovery retry"}
  prior_art: [FR-811]
  restores: "LangGraph ainvoke(None, config) path"
```

vs the current 7,884 bytes of prose that encodes the same causal facts plus ~5KB of context the judge needed once but no subsequent consumer will re-derive.

### Implications

1. **Separate the graph from the prose**: The causal relationships are structured data. They could be a YAML sidecar (`FR-813.graph.yaml`) extracted at judgement-freeze time.

2. **The prose is write-once, read-rarely**: After judgement, the prose serves only archaeology. The causal graph serves ongoing navigation (prior-art hooks, dependency gates, inquisitor).

3. **Token cost of genealogy**: If 30-50% of late-FR tokens are causal positioning, and the judge already validates these at judgement time, post-judgement consumers (enforce, review, inquisitor) could load only the frozen causality map + acceptance criteria — a 60-70% reduction.

4. **The causality map IS the compressed FR**: For machine consumers, `{caused_by, substrate, first_consumer, prior_art, restores/introduces, acceptance_criteria}` may be the entire load-bearing structure. Everything else is authorial thinking made visible — valuable at write-time, dead weight thereafter.

## Research Direction: Two-Artifact FR

```
feature-requests/
├── FR-813.md                    # Full prose (author's thinking tool, frozen at judgement)
├── FR-813.judgement.md          # Judge verdict (frozen)
└── FR-813.causality.yaml        # Extracted DAG edges + AC (machine-consumable)
```

The `.causality.yaml` is auto-generated at judgement freeze. Post-judgement tools (enforce, review, prior-art hook, inquisitor) load ONLY the causality file. The prose remains for archaeology and human override.

**Validation experiment**: Take 20 FRs, manually extract causality YAML, re-run the prior-art hook using only the YAML corpus. Does it find the same matches? If yes, the prose was never load-bearing for that consumer.

## Seed

The causality map is a knowledge graph. Knowledge graphs have inference — if FR-813 depends on FR-811 which depends on FR-759, then FR-813 transitively requires FR-759's contracts. Currently this transitive closure is re-derived by each judge reading the full chain. Could the causality map provide pre-computed transitive closures, turning O(n) context loading into O(1) lookup? And: is the FR system converging toward a git-like DAG where the prose is the diff and the causality is the commit graph?
