# Build pipeline (planned)

```
1. EXTRACT   disc dump → find text archives (CPK? SDAT?)
                → unpack → locate script/text files
2. CATALOG   dump every Japanese string to editable JSON, stable IDs
3. TRANSLATE machine first pass → human review → glossary for names/terms
4. REPACK    translated text → rebuild archives (byte-correct)
5. SHIP      xdelta patch vs own dump + one-step patcher (easy install)
```

## Requirements

- Easy install. One step. No hex editors, no manual extraction for players.
- No game data in the repo — tools and translations only.
- Test on real hardware before any release.
