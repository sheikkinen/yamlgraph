# 2026-08-20 — Copy the Control Plane, Not the Costume

GitClaw originally copied skill prose and rebuilt the process around it. The
result looked governed but lacked the executable adapters and hooks that made
the doctrine true. FR-846 reversed the direction: pin one YAMLGraph commit,
mirror the actual control plane, adapt only repository paths, and prove every
route in a clean clone before changing GitClaw behavior.

**Trap: prose parity mistaken for behavioral parity.** A copied `SKILL.md` can
describe a sole route while the adopting repository has no route to execute.
The system then invents prompts and routing to approximate the missing
mechanism. Every approximation becomes another policy surface that can drift.

**Heuristic:** portable doctrine is a closed executable bundle: instruction,
skill, adapter, wrapper, hook, helper, manifest, and artifact witness. Verify
the result by artifacts, not exit status or matching prose.

The clean-clone witnesses paid for themselves twice. The adapted authoring
guard initially failed closed because local indentation was damaged; later the
final review found the planning skill's root template dependency missing even
though skill discovery passed. Both defects were visible before canonical
push.

Remote CI found a third boundary lie: a shell hook invoked ambient `python3`,
so a local activated environment had PyYAML while bootstrap CI did not. The
source hook swallowed the missing import and returned clean-shaped output.
The adaptation now reports parser absence explicitly; environment resolution is
part of the executable bundle contract, not background scenery.

**Seed:** should YAMLGraph publish the executable control bundle as a generated,
signed release artifact so adopters consume one verified closure instead of
reconstructing it from source paths?
