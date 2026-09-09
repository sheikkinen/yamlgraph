# Storage rules

**Never call `fs.rename` directly.** Use `writeFileAtomic`. On Windows the
destination being open — by a virus scanner, the search indexer, or a sync
client — fails the rename with EPERM, so the save is lost intermittently and
more often on better-protected machines. Enforced by `fs-atomic.guard.test.ts`.

Any new persisted preference must be added in three places: the struct field,
the constructor copy, and the save reconstruction. Missing one means the
preference silently resets on restart.
