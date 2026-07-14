# Roadmap

> The general plan for kprojects. Keep it current; detail lives in the
> sprint records.

## Now

- First cut shipped: harness/, install.sh, /kproject-init skill (sprint 001)
- Try `/kproject-init` on 1–2 real projects; fix what chafes

## Next

- Sharpen old-harness detection in the skill (exact ATV-Starter Kit and
  Phoenix footprints, learned from real migrations)
- GHCP-side equivalent of the init flow (prompt file in `.github/prompts/`?)

## Later / Ideas

- Promote instructions/skills to global/user scope once stable (for now
  everything stays in-repo so a GH checkout carries its own setup)
- Single-source generation if CLAUDE.md / copilot-instructions.md drift
  becomes a real problem (see kagent-harness for prior art)
