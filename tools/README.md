# tools

Extraction / repack scripts. You bring your own dump; no game data lives here.

| script | job |
|---|---|
| `shc_cpk.py` | list / extract members of an SHC CPK (LCG-XOR @UTF decrypt, CRILAYLA decompress); `tocinfo` dumps the CPK/TOC/ETOC column schemas |
| `crilayla_comp.py` | CRILAYLA compressor (round-trips with the decompressor) |
| `shc_repack.py` | rebuild a CPK with replaced members (surgical @UTF patch) |
| `shc_csv_model.py` | model of the GAME's CSV parser (EBOOT 0x42e168 / 0x42e25c); tells you if a CSV would crash it |
| `shc_cpk_check.py` | **release gate**: storage-rule, decompress-size and game-CSV-parser checks on a built CPK |
| `test_shc_repack.py` | unit tests for the storage rule and the parser model |

## Build + gate (do not ship a CPK that fails the gate)

```
python3 tools/shc_repack.py ShcPack.cpk out.cpk replacements.json
python3 tools/shc_cpk_check.py out.cpk --orig ShcPack.cpk      # must print PASS
python3 tools/test_shc_repack.py
```

Then update `USRDIR/hash.csv` line 1 with the new size + md5 (keep the BOM and CRLF); the game's first-run
installer refuses the CPK otherwise (issue #2).

## The storage rule (why `shc_cpk_check.py` exists)

CRI's CPK reader decides whether a member is compressed from the TOC alone: `FileSize == ExtractSize`
means stored raw, anything else means CRILAYLA. The original ShcPack.cpk obeys this with zero exceptions
(502 stored, 1,332 compressed). v2/v3 compressed every replaced file unconditionally; for four 328-byte
enemy battle-message CSVs the CRILAYLA stream was *also* 328 bytes, so the game read the compressed bytes
as CSV and crashed on a NULL row (issue #3, PC 0x42e518). `shc_repack.py` now stores a file raw when
compression does not shrink it, and the gate refuses any CPK with a stored-but-CRILAYLA member.

## Release checklist (v4)

- After `shc_repack.py`, run the gate: `shc_cpk_check.py out.cpk --orig ShcPack.cpk` must print PASS.
- The repacker patches `FileOffset`/`FileSize`/`ExtractSize` in the TOC, and also a per-file
  checksum column when the TOC has one (matched by name: `*crc*`/`*checksum*`, CRC32 over the
  stored bytes). Confirm the field first: `python3 tools/shc_cpk.py tocinfo ShcPack.cpk`.
  The game does not verify it, but stale checksums are a latent defect (issue #5).
- Regenerate `USRDIR/hash.csv` from the patched CPK (size + md5, keep BOM and CRLF) and ship it
  as `patch_files/hash.csv.xdelta` in the release bundle (issue #2). The installers verify the
  patched CPK's md5; update the expected hashes in `installer/INSTALL.bat` and `installer/install.sh`.
- Tell users to delete the game's installed data when switching builds
  (`/dev_hdd0/game/BLJS10244-INSTALL`, or XMB > Game > Game Data Utility on PS3); a stale
  install keeps serving the old CPK (issue #2).
