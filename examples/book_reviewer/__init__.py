"""book_reviewer — a stand-alone YAMLGraph example.

Decomposed (map -> reduce) review of a book-shaped Markdown manuscript:
parse -> lint -> per-chapter review (map) -> pairwise continuity (map) ->
synopsis-delivery -> deterministic reduce -> BookReview.

It imports only YAMLGraph framework code, and reads a Markdown manuscript only —
no DM package import and no DM JSON.
See feature-requests/FR-497-book-reviewer-example.md (Judgment J1/J3/J4/J5/J6 + K1-K6).
"""
