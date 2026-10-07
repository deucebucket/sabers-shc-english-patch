# Contributing

Thanks for helping make Super Heroine Chronicle playable in English. This page covers the rules that keep the project safe to publish and the patch safe to install.

## The one hard rule: no game data

Nothing derived from the game goes into this repository, in any commit, ever. That means:

- no `ShcPack.cpk`, `hash.csv`, EBOOT, PUP, PKG, ISO or any other file from a dump;
- no extracted CSVs or other archive members, patched or not;
- no Japanese source text, headers, IDs, event notes or comments copied out of the game's files;
- no screenshots, textures, audio or video from the game;
- no test fixtures built from game bytes. Tests use synthetic data (see `tools/test_shc_repack.py`).

The only game-derived content allowed is the English text in `translations/en/`. Release bundles ship xdelta patches against the player's own files, never the files themselves. `.gitignore` blocks the obvious extensions, but it is not a substitute for checking your diff before you push.

If you are unsure whether something counts as game data, it does. Ask in an issue first.

## Editing the English text (`translations/en/`)

One TSV per game script CSV. Each file has a header line and then one line per message cell:

```
row	column	english
3	message	It's definitely this way!\nA bird flew that way just now!
```

- `row` is the 1-based row in the original CSV (comment rows count). Do not renumber, reorder or add rows: `tools/merge_tsv.py` uses `row` to find the cell to replace.
- `column` is `message` or `short` (the shortened battle message). Leave it alone.
- `english` is the text. Write `\n` (backslash, n) for a line break inside a message box. Tabs are not allowed inside a cell.
- No Japanese text in `english`. If a cell still needs translating, leave it as it is and mention it in issue #4.
- Keep the game's conventions: ASCII `-` for dashes (the game's font has no em-dash glyph, see #5), straight quotes unless the surrounding file already uses curly ones, and speaker honorifics as the existing text uses them.
- Keep lines short enough for a message box: about 40 characters per line, 3 lines per box, as in the surrounding text.
- Batch your changes (one PR per set of files, with a one-line summary of what changed and why).

To check that a TSV still merges, run `python3 tools/merge_tsv.py translations/en <your extracted csv dir> <out dir>` against your own dump; it exits non-zero on any cell it cannot place.

## Installer files keep CRLF

`installer/INSTALL.bat` and `installer/HOW TO INSTALL.txt` must keep Windows CRLF line endings; `cmd.exe` and Notepad depend on it. `.gitattributes` marks them `-text` so git never converts them. Before committing, verify:

```sh
grep -c $'\r' installer/INSTALL.bat            # must equal the line count
grep -c $'\r' "installer/HOW TO INSTALL.txt"   # must equal the line count
```

If your editor rewrote them with LF, run `unix2dos` on the file (or `sed -i 's/$/\r/'` on a file that has no CR at all) and check again. `install.sh` stays LF.

## Tools

- Python 3 standard library only; no third-party packages.
- Run `python3 tools/test_shc_repack.py` and make sure every test passes.
- Any change to `shc_repack.py` or `shc_cpk_check.py` must keep the release gate strict: a CPK that stores a CRILAYLA stream as a raw member crashes the game (#3). Never relax a gate check to make a build pass.
- `git diff --check` must be clean for LF files (trailing whitespace, missing final newline).

## Pull requests

1. Fork or branch, make your change, run the tests.
2. Check your diff for game data one more time.
3. Open a PR describing what changed and how you verified it (which build you tested, RPCS3 or real PS3). Link the issue it fixes.
4. A maintainer reviews it; text changes are read against the surrounding script, tool changes are re-run.

## Reporting bugs

Use the bug report template. Say whether you are on RPCS3 or a real PS3 (CFW or HEN and firmware version), which patch version you installed, and what happened. A screenshot attached to the issue is fine; just do not commit it to the repository.

## Licensing of contributions

Unless you say otherwise in the PR, contributions to the tools, installers and docs are accepted under the repository's MIT license, and contributions to `translations/en/` under the CC0 1.0 dedication in `LICENSE-TRANSLATIONS`.
