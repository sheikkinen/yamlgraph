---
type: feat
scope: examples
req: REQ-YG-531
---
- **FR-692 World Pressure**: deficit-driven world-building for the novel_fandom example. New world entities must cite the plot thread(s) they pressurize (`check_pressure_admission`) and kinship edges must be mutually acknowledged (`check_reciprocity`); `pressurizes` added to Character/Faction/Location. The three known non-reciprocal edges are repaired additively. Agent graph `world_pressure.yaml` wires the create_* tools plus the reciprocity gate. (REQ-YG-531, REQ-YG-532)
