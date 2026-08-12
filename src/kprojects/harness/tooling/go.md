- Go managed by the `go` tool; format with `gofmt`, lint with `go vet ./...`,
  test with `go test ./...`
- `gofmt -l` lists offending files but **exits 0 either way** — assert on its
  output, never its status, or the gate passes by not looking (same trap as
  `clippy` without `--all-targets`)
- Pin the toolchain in `go.mod` (`go` + `toolchain` directives) rather than
  relying on whatever version happens to be on PATH
