# Windows: `just` runs recipes through `sh`, which Windows does not ship — put
# Git for Windows' `usr\bin` on PATH (it holds `sh.exe`) or run from Git Bash.
# (Upstream's own requirement: "sh must be available in the PATH".)

# A build tree of the gate's own: a cross-compiled repo already keeps one tree
# per target, and two configurations cannot share a CMakeCache.txt.
build_dir := "build-check"

# List available recipes
default:
    @just --list

# `--no-tests=error` is load-bearing: bare `ctest` prints "No tests were
# found!!!" and exits 0, so without it this gate is loudest when it checks
# nothing. If this project documents a tests-only or native-CI configure mode,
# put those flags on the first line — the gate should not need hardware.

# Run CI gates (configure, build, tests)
check:
    cmake -S . -B {{build_dir}}
    cmake --build {{build_dir}}
    ctest --test-dir {{build_dir}} --output-on-failure --no-tests=error

# Remove the gate's build tree
clean:
    rm -rf {{build_dir}}
