# Super Heroine Chronicle: English Patch

Fan English translation for **Super Heroine Chronicle** (PS3, Japan-only, 2014).
Free, unofficial, not affiliated with Bandai Namco. **No game files here.** You patch your own dump.

## Download and install

1. Download **`SHC-English-Patch-v3.1.zip`** from the [Releases](../../releases) page.
2. Unzip it.
3. **Windows:** drag your game's `PS3_GAME\USRDIR` folder onto **`INSTALL.bat`**. That's it.
   **Linux, Steam Deck or Mac:** `sh install.sh "/path/to/PS3_GAME/USRDIR"` (needs `xdelta3`).
4. Start the game. When it says it's installing data, let it finish.

Full step-by-step for RPCS3 and a real PS3 (CFW or HEN) is in **`HOW TO INSTALL.txt`** inside the zip (also in [`installer/`](installer/)).

The installer checks that your files are the original Japanese ones, backs them up (`*.original`), patches, and verifies the result. If anything fails, it puts your originals back.

## What's translated (v3.1)

- Story dialogue, battle messages, menus, items, UI and system text.
- **Fixed in v3.1:** the crash at the first Tsubasa battle in chapter 1, and the first-run "install data failed" error.
- **Still Japanese in places:** some names, speaker tags, parts of the battle UI, the chapter title cards and some prompts. These get fixed in v4 (see the issues).

## For developers

- `tools/` is the extraction and repack pipeline (CPK XOR, CRILAYLA, the @UTF TOC repacker with its release gate).
- `docs/RESEARCH.md` covers the formats, and `docs/PIPELINE.md` covers the build.
- Rules: no game data in the repo, ever. Ship patches only (xdelta against the user's own dump).
