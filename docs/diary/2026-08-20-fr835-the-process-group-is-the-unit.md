# FR-835: The Process Group Is the Unit

## Trap

A green timeout test watched the session leader and inherited pipes, then called
that process containment. Descendants could close both pipes or outlive the
leader, making the observable child look complete while work remained alive.
Bounding captured bytes after exit made the same mistake in another dimension:
it measured the artifact, not the running system.

## Heuristic

For subprocess boundaries, define the resource and lifecycle unit before writing
the timeout. Bound stdout and stderr while the process runs, start a dedicated
session, keep the deadline active after pipe EOF, and treat a surviving process
group after leader exit as failure. Every cleanup claim needs a witness whose
leader, pipes, and descendant have different lifetimes.

## Seed

Which other runners still prove cancellation only against the direct child when
the contract actually owns a process tree?
