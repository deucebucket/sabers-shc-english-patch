# Research notes

## The game

Super Heroine Chronicle (超ヒロイン戦記), PS3 + Vita, Japan-only, Feb 2014.
Banpresto/Namco SRPG. No official English version exists.

## Existing patches (Vita only)

- **Tame421 v0.5 (2022)** — usable. Names, skills, items, enemies, shop translated;
  no story text; machine-translated, rough. Replaces `ShcPack.cpk` via rePatch.
  https://www.gamebrew.org/wiki/Super_Heroine_Chronicle_English_Patch_Vita
- **azurekaito15 v0.01 (2017)** — chapter 1 story in real English, but crashes in
  later chapters. Skip it.

No PS3 patch exists. The container on both versions is Criware CPK.

## Caption-patch method (inFAMOUS)

From the InFAMOUS Modding Community server (VZP, Apr 2026): inFAMOUS PS3
cutscene subtitles live in `.BSUB` files — fully reversed format (12-byte
entries: start/end ms, text offset, char count; UTF-16 text at file offset
0x609). Extractor: https://github.com/VZPx/BSUB-X. Game archives are
`.psarc_s` — rename to `.psarc`, extract with UnPSARC. Demoed working in-game.
Proves the extract → edit → repack loop works on PS3.

## Closest relative: SRW-Z3 translation

https://github.com/retro-trans/SRW-Z3 — full open toolchain for another
Banpresto PS3 SRPG. Their pipeline:

```
DATA/STAGE/STG*.SDAT  →  decrypt (RPCS3 --decrypt, offline)
  →  CPK archive (ITOC layout, CRILAYLA)
  →  scenario as UNCOMPILED LUA source in Shift-JIS
```

Just text files — no pointer tables, no binary surgery. They wrote their own
CPK repacker (`tools/cpkpatch.py`) because every existing tool writes ITOC
archives wrong; theirs rebuilds byte-identical. Trick: store replacements
uncompressed so no CRILAYLA compressor is needed. Releases ship as xdelta
patches against your own dump.

**The bet:** SHC is the same dev family and era. If the PS3 disc has the same
SDAT → CPK → Lua layout, that toolchain ports over almost directly.

## CPK tools worth knowing

- CriPakTools (esperknight) + CriPakTools-mod (CaptainSwag101, batch reimport)
- CriFsV2Lib (Sewer56) — fast extractor, no repack
- JFG99/CriPack — rewrite, unfinished
