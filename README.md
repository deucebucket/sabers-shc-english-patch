# Saber's English Patch for Super Heroine Chronicle

A fan-made English text patch for **Super Heroine Chronicle** (超ヒロイン戦記, PS3, Bandai Namco, 2014). The game was only released in Japan. This patch translates the in-game text (story dialogue, battle messages, menus, items, UI) into English and installs onto **your own dump** of the game in about a minute. It was made for Saber, a friend who wanted to play it in English, and it is free for anyone else who does too.

Unofficial. Not affiliated with Bandai Namco, Banpresto or any rights holder. **No game files are in this repository or in the download.** You need your own copy of the Japanese PS3 game.

**Screenshot policy:** this repository contains no screenshots or other images from the game. Attach screenshots to bug reports on GitHub if they help explain a problem, but do not commit them here.

## Download and install

Get **`SHC-English-Patch-v3.1.zip`** from the [Releases page](../../releases/latest).

### Windows (the easy way)

1. Unzip the download anywhere (your Desktop is fine).
2. Open your game dump and go into `PS3_GAME\USRDIR`. You should see `ShcPack.cpk` and `hash.csv` there.
3. Drag the `USRDIR` folder and drop it onto **`INSTALL.bat`** (or double-click `INSTALL.bat` and paste the folder path when asked).
4. Wait for "DONE! The game is now in English." and press any key.

The installer checks that your files are the untouched Japanese originals, backs them up as `ShcPack.cpk.original` and `hash.csv.original`, applies the patch, and verifies the result. If anything fails it restores your originals.

### RPCS3

Patch the game folder RPCS3 runs the game from (usually where you put the game, or `RPCS3\dev_hdd0\disc\<game>` or `RPCS3\games\<game>`), then start the game. On first start the game "installs data"; let it finish.

### Real PS3 (CFW or HEN, with webMAN or multiMAN)

1. Patch the game on your PC first (Windows steps above, or `install.sh`).
2. Copy the two patched files, `ShcPack.cpk` and `hash.csv`, from your PC's `USRDIR` to the same place in the game folder on your PS3 (FTP or USB), replacing the old ones.
3. If you already played the game before patching, delete its installed data first: XMB > Game > Game Data Utility > Super Heroine Chronicle.
4. Start the game and let it install data.

### Linux, Steam Deck, Mac

Install `xdelta3` (`sudo apt install xdelta3`, `brew install xdelta`, or your distro's package), then:

```sh
sh install.sh "/path/to/your/game/PS3_GAME/USRDIR"
```

The full guide, including troubleshooting, is in `HOW TO INSTALL.txt` inside the zip (also in [`installer/`](installer/)).

## What's translated (v3.1)

- Story dialogue, battle messages, menus, items, UI and system text.
- Fixed in v3.1: the crash at the first Tsubasa battle in chapter 1 ([#3](../../issues/3)) and the first-run "install data failed" error ([#2](../../issues/2)).

### Known issues

- Some text is still Japanese: some names, speaker tags, parts of the battle UI, the chapter title cards and some prompts. Tracked in [#4](../../issues/4).
- Polish list for the next build (`[END]` bodies in a few map messages, em-dash glyph gaps, curly-quote QA, TOC checksums): [#5](../../issues/5).

Both are planned for v4.

## FAQ

**The game shows a black screen, or the text is still the old build's.**
The game runs the CPK from its *installed* data, not from the disc folder. Delete the installed data and start the game again so it reinstalls from the patched files: on PS3, XMB > Game > Game Data Utility > Super Heroine Chronicle; on RPCS3, delete `dev_hdd0\game\BLJS10244-INSTALL`. Do this every time you switch patch builds.

**"Your ShcPack.cpk isn't the original Japanese file."**
The installer only patches the untouched Japanese file (MD5 `834351ca822e97d6a24facf01cc5e5f4`). Your copy is already modified or comes from a different dump. Copy the original `ShcPack.cpk` back from your dump and run the installer again. If it says "already patched", you are done.

**The game says it failed to install data (Japanese error, then quits).**
`hash.csv` was not replaced. Both `ShcPack.cpk` and `hash.csv` must be the patched versions.

**How do I undo the patch?**
In `USRDIR`, delete `ShcPack.cpk` and `hash.csv`, then rename `ShcPack.cpk.original` to `ShcPack.cpk` and `hash.csv.original` to `hash.csv`.

**Does it work on the Vita version?**
No. This patch is for the PS3 release (BLJS10244) only.

## Building the patch from your own dump

Everything needed to rebuild the patched `ShcPack.cpk` from a dump is in [`tools/`](tools/) (Python 3, no third-party packages):

```sh
# 1. extract the game's CSVs from your own ShcPack.cpk
python3 tools/shc_cpk.py list ShcPack.cpk
python3 tools/shc_cpk.py extract ShcPack.cpk <member path> -o extracted/
# 2. apply the English text onto the extracted CSVs
python3 tools/merge_tsv.py translations/en extracted/ merged/
# 3. repack
python3 tools/shc_repack.py ShcPack.cpk out.cpk replacements.json
# 4. release gate (must print PASS) and unit tests
python3 tools/shc_cpk_check.py out.cpk --orig ShcPack.cpk
python3 tools/test_shc_repack.py
```

Then regenerate `hash.csv` and produce the xdelta patches as described in [`docs/PIPELINE.md`](docs/PIPELINE.md). [`tools/README.md`](tools/README.md) explains each script and the storage rule the gate enforces; [`docs/RESEARCH.md`](docs/RESEARCH.md) has the format notes.

## Contributing

Fixes to the English text, the installers and the tools are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) first. The short version:

- Edit the text in [`translations/en/`](translations/en/) (one TSV per game script; `row`, `column`, `english`). Keep the row numbers, use `\n` for a line break inside a message box, and never add Japanese source text.
- **No game data, ever.** No CPKs, no extracted CSVs, no dumps, no screenshots, nothing derived from the game other than the English text in `translations/en/`.
- `installer/INSTALL.bat` and `installer/HOW TO INSTALL.txt` must keep CRLF line endings (`.gitattributes` marks them `-text`).
- Run `python3 tools/test_shc_repack.py` before opening a pull request.

Bug reports: [open an issue](../../issues/new/choose). Takedown or other contact: see [SECURITY.md](SECURITY.md).

## Credits

- Made for **Saber**.
- Translation: four AI translation agents (including Carl), reviewed by the BucketComps team.
- Patch tooling, research and release engineering: **DeuceBucket**.
- **richard1222**: text cleanup, repacker checksum patch, `merge_tsv.py` and install docs.
- The release bundle includes an unmodified **Xdelta 3.1.0** binary by Joshua MacDonald (GPL v2, source at https://github.com/jmacd/xdelta-gpl).

## License

Proposed, owner to confirm:

- **Tools, installers and documentation** (`tools/`, `installer/`, `docs/`, this README): [MIT License](LICENSE).
- **English translation text** (`translations/en/`): [CC0 1.0 Universal](LICENSE-TRANSLATIONS). The English text was machine-generated by four AI agents and reviewed by the project. As AI-generated text it is offered under CC0 and the project claims no rights over it. The underlying game script belongs to its rights holder.

## Legal

This is an unofficial fan project. It is not affiliated with, endorsed by or connected to Bandai Namco, Banpresto or any other rights holder. Super Heroine Chronicle and all characters, names and game content are the property of their respective owners. No game files, assets or Japanese script text are distributed here; the patch is a binary difference that only works on a copy of the game you already own. If you are a rights holder with a concern, open an issue or see [SECURITY.md](SECURITY.md).
