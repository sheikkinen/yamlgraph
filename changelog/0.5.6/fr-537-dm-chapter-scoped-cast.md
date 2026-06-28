---
type: feat
scope: examples
---
- **FR-537 DM v2 chapter-scoped cast**: A chapter now declares its focal `cast` in
  the outline, and the play loop animates only that cast instead of the whole
  reviewed roster. A single `resolve_chapter_cast` leaf unions the authored cast
  with the roster characters named in the chapter's beats (beats-as-floor,
  word-bounded matching), and that resolution is applied at both roster-narrowing
  sites — the prose-control cast (`build_allowed_scene_cast`) and the per-turn
  intents roster built inline in `invoke_turn` (the measured defect: off-chapter
  characters were animated every turn). This is a SCOPE narrowing distinct from
  the lifecycle STATUS gates and composes with them. Authored cast names are
  normalized against the roster at the `expand_chapters` boundary (unknowns dropped
  with a warning); an empty resolved cast falls back to the full reviewed roster,
  so a `cast`-less story reproduces today's behavior (additive feature).
