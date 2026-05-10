---
type: fix
scope: watcher
---
- **Watcher standalone scripts**: All `.chaplain/lib/watcher/*.sh` scripts now execute standalone for FSM engine. Extracted shared logging to `common.sh`, added CLI arg parsing, fixed `BASH_SOURCE[0]` sourcing for source-safety, and corrected `machine_name` in YAML configs.
