# Git History Is the Archive

**Date:** 2026-08-21
**FR:** FR-848

## Trap

Deletion felt risky because old outputs, RED/GREEN logs, authoring reports, and
embedded governance looked like evidence. But their presence in the current
tree made a stronger claim: that their subjects were still current. Several
described a cron runtime, examples, and task inputs that had already been
deleted. Preserving evidence in place had become preservation of falsehood.

The distinction is temporal ownership. The working tree describes what exists
now. Git history describes how it came to exist. Asking the working tree to do
both jobs turns every retired design into permanent product surface.

## Heuristic

After a subtractive change, search for artifacts whose only remaining consumer
is history. If an output, report, test log, spike, FR, or review describes no
live contract, delete it from the current tree and trust version control as the
archive. Preserve current authority, not every historical representation of it.

Before local cleanup, separately prove repository boundaries and tracked-file
membership. Historical clutter is removable; untracked work without provenance
is not interchangeable with clutter.

## Seed

Which generated evidence classes should carry an explicit expiry condition so
their producing FR can require retirement when the governed surface disappears?
