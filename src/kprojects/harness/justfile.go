# Windows: `just` runs recipes through `sh`, which Windows does not ship — put
# Git for Windows' `usr\bin` on PATH (it holds `sh.exe`) or run from Git Bash.
# (Upstream's own requirement: "sh must be available in the PATH".)

# List available recipes
default:
    @just --list

# Run CI gates (format, vet, tests)
check:
    @unformatted="$(gofmt -l .)"; if [ -n "$unformatted" ]; then echo "gofmt: needs formatting (run: just fmt):"; echo "$unformatted"; exit 1; fi
    go vet ./...
    go test ./...

# Apply formatting
fmt:
    gofmt -w .
