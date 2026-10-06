# shc-english-patch

English caption/text patch for **Super Heroine Chronicle** (PS3, Japan-only, 2014).

The game never left Japan. This project rips the Japanese text out of the PS3 version and puts English back in — dialogue, menus, skills, items, the lot.

## Status

Early. Game dump in hand, toolchain research done, extraction up next.

## The plan

1. Crack the disc dump and find the text archives (CPK expected)
2. Extract every Japanese string into editable files
3. Translate — machine first pass, human review after
4. Repack into the game archives
5. Ship as an easy one-step patcher (xdelta against your own dump)

## Rules

- No game data in this repo. Ever. Tools and translations only — you bring your own dump.
- Unofficial fan project, free forever. Not affiliated with Bandai Namco.

## Docs

- `docs/RESEARCH.md` — what we know so far
- `docs/PIPELINE.md` — the build pipeline
- The wiki is the devlog — it goes live once there is something to log.
