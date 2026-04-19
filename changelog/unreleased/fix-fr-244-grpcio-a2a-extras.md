---
type: fix
scope: a2a
---
- **FR-244 grpcio fix**: Add `grpcio>=1.60.0` to `a2a` optional extras and document rationale; required by `a2a-sdk>=1.0` compat layer which imports `grpc` at module level.
