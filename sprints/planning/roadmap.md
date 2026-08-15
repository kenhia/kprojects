# Roadmap

> The general plan for kprojects. Keep it current; detail lives in the
> sprint records.

## Now

- Installer is portable and stack-aware (sprint 002): `kproject-install` run
  via `uvx`, harness shipped as package data, stack detected from the target.
  Verified end to end from `git+https` on both kai and cleo.
- Point `/kproject-init` at the new invocation and add the greenfield stack
  question (agent-skills #1184; program 1103 slice 2) — until that lands,
  nothing passes `--stack`, so stack-awareness is only reachable by hand
- **Re-apply pass done (sprint 007).** All 14 repos still on the retired bash
  installer's block were re-applied — five of them Rust repos that had been
  instructing agents to use `uv`, `ruff` and `ty`. Closing audit: zero
  `OLD-INSTALLER` rows on kai and cleo; the two on kubs0 are the duplicate
  clone that should be dropped and a checkout sitting on a pre-merge branch.
  What is left is the two batch-5 slices (kdeskdash #1280, kpidash #1279) and
  the installer warts the pass surfaced — the duplicate `target/` gitignore
  line, and detection not seeing subdirectory stack markers.

## Next

- Harness survey and rollout across cleo/kai/kubs0 (proposal 749): route every
  Ken-owned repo to kprojects, working-skill-repo, or deliberately bare
- Sharpen old-harness detection in the skill (exact ATV-Starter Kit and
  Phoenix footprints, learned from real migrations)
- Try `/kproject-init` on 1–2 real projects; fix what chafes

## Later / Ideas

- More stacks if they earn one (node) — the per-stack template split makes
  adding one cheap, so wait for a real project rather than pre-building. Go
  landed in sprint 003 with a population of one; cmake in 006, believed to be
  one and actually two. Each new stack's real work is finding how its gate lies
  when there is nothing to check
- Re-apply the two C repos with `--stack cmake`: **kdeskdash (#1280) first** —
  its block is a pre-detection `install.sh` one still carrying the *python*
  stanza, so it is wrong now — then kpidash (#1279), which is merely less
  specific. Both keep their hand-written gates; those are better than the
  template's
- GHCP-side equivalent of the init flow (prompt file in `.github/prompts/`?)
- Single-source generation if CLAUDE.md / copilot-instructions.md drift
  becomes a real problem (see kagent-harness for prior art)
