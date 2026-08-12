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

## Next

- Harness survey and rollout across cleo/kai/kubs0 (proposal 749): route every
  Ken-owned repo to kprojects, working-skill-repo, or deliberately bare
- Re-apply to the repos already on the harness so they pick up the repo-URL
  fix and the new marker text
- Sharpen old-harness detection in the skill (exact ATV-Starter Kit and
  Phoenix footprints, learned from real migrations)
- Try `/kproject-init` on 1–2 real projects; fix what chafes

## Later / Ideas

- More stacks if they earn one (go, node) — the per-stack template split makes
  adding one cheap, so wait for a real project rather than pre-building
- GHCP-side equivalent of the init flow (prompt file in `.github/prompts/`?)
- Single-source generation if CLAUDE.md / copilot-instructions.md drift
  becomes a real problem (see kagent-harness for prior art)
