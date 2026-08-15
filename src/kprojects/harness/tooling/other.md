- No stack the harness could name, so `just check` is yours to write. Ask
  what this repo can actually get wrong — a documents repo's failure mode is
  a stale cross-reference, not a type error
- Add no dependency to make a gate: a stdlib script or a shell one-liner
  keeps a repo that had no dependencies still having none
- Skip what isn't yours to verify — external URLs, machine-local paths
- **Negative-test it.** Plant the error the gate exists to catch and watch it
  exit 1. A gate never seen to fail is not a gate, and the seeded placeholder
  fails on purpose until you replace it
