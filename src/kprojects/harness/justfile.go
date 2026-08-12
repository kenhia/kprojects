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
