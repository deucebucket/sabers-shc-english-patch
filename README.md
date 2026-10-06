# shc-english-patch

English caption/subtitle patch for **Super Heroine Chronicle** (PS3, Japan-only, 2014).

The game never left Japan. This project translates the in-game caption text to English — the dialogue subtitles. A favor project so Saber can play it in English.

## Status

Extraction cracked. The game text lives in plain UTF-8 CSVs inside an XOR-obfuscated CPK (`ShcPack.cpk`: 1,834 files). Translation pipeline is next.

## The plan

1. Crack the disc dump and find the text — done. The CPK "encryption" is CRI LCG XOR; TOC parsed; CRILAYLA decompressed.
2. Extract every Japanese string into editable files — done for `ShcPack.cpk`.
3. Translate with multi-agent review — no machine slop; every line combed by several agents.
4. Repack into the game archives.
5. Ship as an easy one-step patcher (xdelta against your own dump).

## Rules

- No game data in this repo. Ever. Tools and translations only — you bring your own dump.
- Caption text only. Menus, skills, items are out of scope unless that changes.
- No MTL slop: every translated line is reviewed by multiple agents before it ships.
- Unofficial fan project, free forever. Not affiliated with Bandai Namco.

## Docs

- `docs/RESEARCH.md` — what we know so far
- `docs/PIPELINE.md` — the build pipeline
- The wiki is the devlog.
