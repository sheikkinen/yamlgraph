# Diary 2026-08-19 — The Provider's Type Lie, Photographed at 2752×1536

**Context:** FR-826 enforcement — the deviant-daily repo, corpus
sanitization, governed graph authoring, and the first fully autonomous
DeviantArt publish (draw → generate → describe → gate → publish, run
32267564652, "Vigil in the Hollow World").

## The trap fired exactly where the Scripture said it would

The first dispatch witness failed with:

> The image was specified using the image/png media type, but the
> image appears to be a image/jpeg image

`generate.py` asked flux-1.1-pro-ultra for output and saved it as
`.png`. The provider returned JPEG bytes — the delivery URL even said
`tmphabrn5xd.jpg` in the very log line above the failure. Two
boundaries downstream trusted the filename: the Anthropic vision call
declared `data:image/png` and `stash_submit` declared `image/png` in
its multipart tuple.

This is the FR-059 trap verbatim — *the provider's type lie* — and
the cure was the one already written: normalize at the boundary where
external data enters. `detect_media_type()` reads magic bytes
(`\x89PNG`, `\xff\xd8\xff`, RIFF/WEBP) and both consumers now declare
what the bytes ARE, not what the path claims. RED 8c393dd, GREEN
8d88e8f, 51 tests.

**The metacognitive failure:** I *know* this trap. It is in the
Scripture I load every session. Yet I wrote `"image/png"` twice —
once per boundary — because the local smoke path (z-image via the
same download helper) happened to return PNG. A trap you can recite
is not a trap you are immune to; immunity comes only from the
mechanical check. The fixture bug proves it: my own tests wrote
`b"png"` as image content — the tests encoded the same lie.

## Blocklists are boundary problems too (three iterations)

Corpus sanitization took three passes because regex word boundaries
are a *convention*, and filenames/tags don't follow it:

1. `\brape\b` missed "raped"; `\bnina\b` missed "nina_heikkinen" —
   underscore is a word character, so `\b` never fires inside
   snake_case. Cure: letter-lookbehind stems for terms, plain
   substring for names.
2. `source_file` basenames leaked what the prompt filter scrubbed —
   "flux_lora_nina1" survived in the *metadata* column. The leak
   channel was not the field being filtered but the field standing
   next to it. Reduced to numeric id.
3. The secret-scan pattern flagged 429 booru tags as "token-like"
   because `_` was in the base64-ish character class.

Same shape as the media-type bug: the sanitizer normalized one
representation of the data and trusted the adjacent ones.

## What went right

- **Resume-by-design paid off on day one:** the failed first run had
  already committed `drawn`. The rerun resumed the same prompt
  instead of redrawing — the recovery path was exercised by a real
  failure two hours after it was written, not by a synthetic test.
- **Persist-before-publish ordering held:** the failed run rotated
  nothing (died at describe, before refresh); the green run rotated
  DA_REFRESH_TOKEN mid-run (secret timestamp 15:02:54Z) *before* any
  DA side effect, exactly as AC-08's test demanded.
- **The governed authoring route** produced a graph whose `.result`
  envelope contract I would have gotten wrong by hand — the adapter
  discovered it during its own smoke.

**Heuristic (candidate for graduation if it recurs):** *the leak
channel is the adjacent field* — when sanitizing or normalizing one
representation (prompt text, image bytes), audit every co-traveling
representation of the same object (filename, metadata column,
extension, MIME declaration). One object, N representations, and the
filter only saw one.

**Seed:** `detect_media_type` now exists in a satellite repo and the
same trap class lives in yamlgraph's own vision boundary
(FR-769/FR-781 precedents). Should magic-byte media detection be a
yamlgraph utility — one boundary, all consumers — instead of being
rediscovered per satellite? And more generally: can the corpus
extractor's three-iteration blocklist arc be compressed into a
reusable "sanitize one object across all its representations"
checklist that a gate can enforce mechanically?
