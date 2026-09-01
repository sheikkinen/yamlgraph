# 2026-09-01 — Screenshot Is Not a Color Picker

Off-doctrine task: a humorous Etuovi.com-styled listing HTML, no FR, no
graph. Worth reflecting on anyway because the failure mode generalizes.

## What I actually did

Asked to "copy the actual design," I opened the real listing in the
browser, took screenshots, and eyeballed hex values off the rendered
pixels: "that logo looks like a wine-red, call it `#7a1638`." I never once
read the site's actual stylesheet. The corrected version is a plausible
homage — closer than the first navy/gold guess — but it is still a guess
wearing the confidence of a measurement. The operator's own words named
the defect precisely: "this look like *varokaa halpoja kopioita*"
(*beware of cheap knockoffs*) — a knockoff isn't wrong because it tries,
it's wrong because it approximates a source it never actually inspected.

## The trap: screenshot_as_color_picker

I had `mcp_chrome_devtoo_evaluate_script` available (found it via
`tool_search` and never invoked it) and a plain `view-source:` /
network-tab route to the real CSS file, sitting one click from the exact
custom-property values, font stack, and spacing tokens Etuovi actually
ships. Instead I read a JPEG-compressed screenshot with my eyes and
produced a number. This is `read_raw_output_first` violated on a new
boundary: I've applied that Scripture entry to text artifacts (FR prose,
pipeline output) but never to **rendered design** — the raw record for a
website's visual identity is its computed styles and asset URLs, not a
screenshot of them. A screenshot is already a lossy render of the raw
record, the same relationship a summary has to a transcript.

The cheap, boring fix was available the whole time:
`getComputedStyle(el).backgroundColor` / `.color` / `.fontFamily` on the
logo and header elements via `evaluate_script`, or just reading the linked
stylesheet's CSS custom properties directly. Either gives an exact value
in one call. Eyeballing a screenshot gives an approximation dressed as a
finding, and I reported it with the same declarative confidence I'd give
a real measurement ("Etuovi's real wine-red `#7a1638`") — that's
`plausible_wrong_answer` again, just relocated from JSON to hex codes.

## A second, smaller trap: tool-family boundary

I burned several calls discovering that `open_browser_page` /
`read_page` / `screenshot_page` (string UUID `pageId`) and the
`mcp_chrome_devtoo_*` family (numeric `pageId`) are two disjoint driver
backends that don't share a page handle. `mcp_chrome_devtoo_take_snapshot`
rejected the UUID with a schema error; `list_pages` on that family showed
an unrelated blank tab. No amount of retrying fixed it — it needed
switching families entirely, which I never did (I stayed in the
UUID-based family and lost `evaluate_script` as an option, since that's
only exposed under the devtools family in this session). Worth a
repo-memory note so a future session doesn't re-spend the same five calls
finding this out.

## Why the layout also drifted

Separately: the real page renders a responsive breakpoint I captured
mid-viewport (narrower than intended), showing a stacked mobile-ish
layout, while my HTML committed to the two-column desktop structure
described by the earlier text-only fetch. Two different observations of
the *same* site, taken by two different tools at two different implicit
viewport widths, got blended into one "reference." That's not a new
trap — it's `are_the_witnesses_one_phenomenon` — but it's a clean instance:
a text fetch and a screenshot of the same URL are not the same witness
unless they're pinned to the same viewport.

## Heuristics

- `screenshot_as_color_picker`: never transcribe a hex/font/spacing value
  from a rendered screenshot when `getComputedStyle` or the source
  stylesheet is one call away. The screenshot is for layout/composition
  judgment, not for values that have an exact machine-readable source.
- `pin_the_viewport_before_comparing`: when reconciling a DOM/text fetch
  against a screenshot of the same page, fix and record the viewport
  width for both, or treat them as two different pages.

**Seed:** If "copy the actual design" recurs — for a real (non-joke)
brand-fidelity task — is the right first step even a screenshot at all,
or should visual-mimicry work start with a small extraction pass
(`evaluate_script` dumping computed styles + linked CSS URLs for the N
key elements) the way `graph-authoring` starts with precedent search
before any YAML is written? What would a "design-authoring doctrine"
look like if screenshots were demoted to the composition-review step and
computed styles were the only legitimate source for a value that ends up
literally in the CSS?
