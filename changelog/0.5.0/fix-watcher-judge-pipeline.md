### Fixed
- **Watcher pipeline judge**: Fixed invalid model name (`claude-sonnet-4-20250514` → `claude-sonnet-4`) causing empty copilot output (FR-309)
- **Watcher pipeline judge**: Aligned event_map vocabulary with prompt (APPROVE/AMEND/REJECT/SPLIT) (FR-309)
- **Watcher pipeline judge**: Changed success fallback from `approve` to `error` to prevent auto-approval on failure (FR-309)
- **Watcher pipeline judge**: Added `judge→failed` transition on error event (FR-309)
- **Watcher pipeline enforce**: Removed session_id dependency; enforce uses fresh session (FR-309)
- **yamlgraph_async action**: Enhanced logging — stderr always logged, expanded truncation, full output on event_map miss (FR-307)
