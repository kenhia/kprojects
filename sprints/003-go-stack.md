# Sprint 003 — Go joins the stack list

2026-08-12 · korg proposal 1195 · covers #741 · slice 1.5 of program 1103

## Goal

Add `go` as a fourth stack, while the stack list is still cheap to change.

The timing *is* the argument. Sprint 002 wrote the list down in this repo;
proposal 1185 is about to write it down again in agent-skills as
`/kproject-init`'s greenfield question. Adding Go afterwards means editing
both repos a second time — the same "touching the installer twice" cost that
fused #699 and #725 into one sprint. #741 itself has been open since
2026-07-28; nothing about it is new scope.

## Decisions

- **`go.mod` is the detector's marker, placed second in `STACK_MARKERS`** —
  after `Cargo.toml`, before `pyproject.toml`. Order is the whole answer for a
  polyglot repo, so it was picked rather than appended. Cargo stays first
  (unchanged behaviour, existing test). `go.mod` goes ahead of
  `pyproject.toml` because `pyproject.toml` is the weakest of the three
  markers: `Cargo.toml` and `go.mod` *define a build*, whereas
  `pyproject.toml` also turns up in repos that are not Python projects at all,
  carrying nothing but ruff settings. A repo with `go.mod` is a Go module.
- **The gate asserts on `gofmt` output, not its exit status.** `gofmt -l`
  prints every offending file and then **exits 0** — so the obvious
  `gofmt -l .` is a gate that passes by not looking. Exactly the class of trap
  as `clippy` without `--all-targets`, which has bitten on kvscf. The check
  captures the output and fails when it is non-empty:

  ```
  @unformatted="$(gofmt -l .)"; if [ -n "$unformatted" ]; then ... exit 1; fi
  ```

  It also prints the offenders and points at `just fmt`, so the failure is
  actionable rather than just red. Mutating `gofmt -w` stays in `just fmt`,
  per 002's rule that a gate must never rewrite your tree.
- **`.gitignore` stanza is upstream's Go list, trimmed.** `*.exe`, `*.test`,
  `*.out`, `go.work`, `go.work.sum`. `go.work` is per-machine by upstream
  guidance; `*.test` and `*.out` are `go test -c` binaries and profile output.
  The cross-platform shared-library entries were dropped as noise for a
  homelab harness.
- **The tooling stanza carries the gofmt warning**, not just the tool names.
  That stanza lives inside the managed block, which a project may not
  hand-edit — so it is the right place for the one fact a Go kproject would
  otherwise have to rediscover.

## Shipped

- `src/kprojects/cli.py` — `go` in `STACKS`, `("go", "go.mod")` in
  `STACK_MARKERS` (ordered deliberately, comment updated), `go` entry in
  `STACK_IGNORES`.
- `src/kprojects/harness/justfile.go` — `check` (gofmt assertion, `go vet
  ./...`, `go test ./...`), `fmt` (`gofmt -w .`), `default`.
- `src/kprojects/harness/tooling/go.md` — the managed-block stanza.
- `tests/test_install.py` — 38 tests, up from 32. New: `go.mod` detection,
  both precedence pairs (`Cargo.toml` > `go.mod` > `pyproject.toml`), the Go
  stanza in the rendered block, Go gitignore entries, Go justfile seeding, and
  a regression guard asserting the `check` recipe *captures* gofmt's output
  rather than trusting its status.
- README, `CLAUDE.md`, `.github/copilot-instructions.md` — the four-stack list
  and the detection order. Both agent files also gained the recipe for adding
  a stack, since this sprint is the proof that it is a five-line change.

## Verification

Written test-first: the six new tests were red before any implementation
(`FileNotFoundError` on `justfile.go`, `KeyError: 'go'`, detection returning
`other`), green after. `just check` passes — ruff format, ruff check, ty,
38 tests.

End to end against a throwaway repo carrying only a `go.mod`: detection
reported `go (detected)` with no flag, seeded `justfile.go`, wrote all five
Go ignores, and composed the Go stanza into `CLAUDE.md` with no Python
guidance present.

The gate itself was exercised with a stubbed `gofmt` on `PATH`, since that is
the only way to reproduce the trap deliberately:

- stub prints `main.go` and exits 0 → `just check` **fails** with exit 1 and
  names the file. A bare `gofmt -l .` would have passed here.
- stub prints nothing → `just check` passes and proceeds to `go vet` /
  `go test`.

## Follow-ups

- **`go vet` / `go test` have not been run against a real Go module.** The
  proposal expected this to happen on cleo (`go1.26.5`, verified 2026-08-10);
  this sprint ran on **kai**, which has no `go` on `PATH` — that is k-homelab
  #750, still open. Everything else is verified; the two commands are
  conventional and unlikely to be wrong, but they are unproven. Worth one
  `just check` on cleo, or after #750 lands.
- Proposal 1185 (slice 2) now has four options to ask about, not three.
