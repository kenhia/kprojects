- C/C++ built with `cmake`: configure out-of-source, build with
  `cmake --build`, test with `ctest`
- `ctest` prints "No tests were found!!!" and **exits 0** when nothing is
  registered — pass `--no-tests=error` (CMake ≥ 3.20) or the gate passes
  loudest when there is least to check (same trap as `gofmt -l`)
- The configure flags are the project's own. If the repo documents a
  tests-only or native-CI mode, the gate uses that — a gate needing a
  cross-compiler, a sysroot or hardware is a gate nobody runs
- No formatter in the gate: `clang-format` asserts nothing without a
  committed `.clang-format`. Add `just fmt` once the repo has one
