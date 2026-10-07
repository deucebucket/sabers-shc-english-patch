# Build pipeline

How a release of the patch is built from a player's own dump. Every step runs on your machine against your files; nothing from the game is checked in. Scripts are in [`tools/`](../tools/README.md).

```
own dump ─► 1. EXTRACT ─► 2. MERGE ─► 3. REPACK ─► 4. GATE ─► 5. hash.csv ─► 6. XDELTA ─► 7. BUNDLE
            shc_cpk.py    merge_tsv.py  shc_repack.py  shc_cpk_check.py           xdelta3      zip
```

## 1. Extract

`USRDIR/ShcPack.cpk` is a Criware CPK. Its `@UTF` tables are XOR-obfuscated with CRI's LCG scheme and most members are CRILAYLA-compressed. `shc_cpk.py` undoes both:

```sh
python3 tools/shc_cpk.py list ShcPack.cpk                    # member table
python3 tools/shc_cpk.py tocinfo ShcPack.cpk                 # CPK/TOC/ETOC column schemas
python3 tools/shc_cpk.py extract ShcPack.cpk <member> -o extracted/
```

The game's text lives in UTF-8 CSVs (with BOM, CRLF): `*_BattleMessage.csv`, `map_message_*.csv`, `freeTalk_message_*.csv`, `soulLink_message_*.csv`. Loop over the member list to extract them all.

## 2. Merge the English text

`translations/en/*.tsv` holds only the English cells (`row`, `column`, `english`). `merge_tsv.py` writes them back into the extracted CSVs, preserving BOM, line endings and every untouched cell:

```sh
python3 tools/merge_tsv.py translations/en extracted/ merged/
```

It finds the message columns by header (the original Japanese headers or the English ones) and exits non-zero if any cell cannot be placed, so a broken TSV stops the build.

`shc_csv_model.py` models the game's own CSV parser (EBOOT `0x42e168` / `0x42e25c`) and reports whether a CSV would crash it. Run it on anything hand-edited.

## 3. Repack

`shc_repack.py` rebuilds the CPK with the merged CSVs, patching `FileOffset`, `FileSize`, `ExtractSize` and the per-file checksum column in the TOC in place (a surgical `@UTF` patch, not a full rewrite):

```sh
python3 tools/shc_repack.py ShcPack.cpk out.cpk replacements.json
```

`replacements.json` maps member paths to the files in `merged/`. **The storage rule:** CRI's reader treats `FileSize == ExtractSize` as "stored raw" and anything else as CRILAYLA. The repacker therefore stores a member raw whenever compression does not shrink it; a CRILAYLA stream the same size as its input would be read as plain CSV and crash the game (issue #3).

## 4. Gate

```sh
python3 tools/shc_cpk_check.py out.cpk --orig ShcPack.cpk     # must print PASS
python3 tools/test_shc_repack.py                              # unit tests
```

The gate checks the storage rule, the decompressed sizes and the game-parser model on every member. A build that does not print `PASS` is not shipped. Do not relax a check to make a build pass.

## 5. hash.csv

The game's first-run installer compares `USRDIR/hash.csv` (size and MD5 of `ShcPack.cpk`) with the file; a mismatch aborts the install (issue #2). Regenerate line 1 from the new CPK, keeping the BOM and CRLF.

## 6. xdelta patches

Ship differences, not files:

```sh
xdelta3 -e -9 -s ShcPack.cpk out.cpk      patch_files/ShcPack.cpk.xdelta
xdelta3 -e    -s hash.csv    hash.csv.new patch_files/hash.csv.xdelta
```

Record the original and patched MD5s; the installers check both (`installer/INSTALL.bat`, `installer/install.sh`) and refuse to patch anything but the untouched Japanese file.

## 7. Bundle

The release zip contains `INSTALL.bat`, `install.sh`, `HOW TO INSTALL.txt`, `CHECKSUMS.md5` and `patch_files/` (the two xdelta files, an unmodified `xdelta3.exe` and its license note). `INSTALL.bat` and `HOW TO INSTALL.txt` keep CRLF line endings. No game file is included.

## Before every release

- Gate prints PASS, tests pass.
- Fresh install on RPCS3 from an untouched dump, then play past the first Tsubasa battle (the issue #3 crash site).
- Install on a real PS3 if one is available; delete the installed game data first so the new CPK is actually the one running.
- Update the expected MD5s in both installers and in the release notes.
