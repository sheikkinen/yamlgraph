# Reflection: FR-435 markdown post-edit hygiene

## Trap
The request framed markdown cleanup as "ruff for md", but the failing boundary was file-type routing, not Ruff capability.

## Insight
A minimal boundary-specific hook solved the real problem faster than extending tooling beyond its intended domain.

## Heuristic
When a fix request names a tool, validate whether the tool is the right boundary owner before extending scope.

Seed: Should each post-edit hook publish a short "covered file types" manifest so capability mismatches are visible before implementation requests?
