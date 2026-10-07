#!/bin/sh
# Super Heroine Chronicle - English Patch v3.1 (Linux / Steam Deck / Mac)
# Usage: sh install.sh /path/to/SHC/PS3_GAME/USRDIR
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
T=${1:-}
[ -z "$T" ] && { printf 'Path to your USRDIR folder: '; read -r T; }
T=${T%/}
[ -f "$T/ShcPack.cpk" ] && [ -f "$T/hash.csv" ] || { echo "[X] ShcPack.cpk or hash.csv not found in $T (pick SHC/PS3_GAME/USRDIR)"; exit 1; }
command -v xdelta3 >/dev/null || { echo "[X] Install xdelta3 first (e.g. sudo apt install xdelta3, or brew install xdelta)"; exit 1; }
md5() { if command -v md5sum >/dev/null; then md5sum "$1" | cut -c1-32; else md5 -q "$1"; fi; }
O=$(md5 "$T/ShcPack.cpk")
[ "$O" = ba93cf943333aec995a00a09b7492b79 ] && { echo "[OK] Already patched."; exit 0; }
[ "$O" = 834351ca822e97d6a24facf01cc5e5f4 ] || { echo "[X] ShcPack.cpk is not the original (md5 $O). Re-copy it from your dump."; exit 1; }
[ -f "$T/ShcPack.cpk.original" ] || cp "$T/ShcPack.cpk" "$T/ShcPack.cpk.original"
[ -f "$T/hash.csv.original" ] || cp "$T/hash.csv" "$T/hash.csv.original"
if xdelta3 -d -f -s "$T/ShcPack.cpk.original" "$HERE/patch_files/ShcPack.cpk.xdelta" "$T/ShcPack.cpk" \
 && xdelta3 -d -f -s "$T/hash.csv.original" "$HERE/patch_files/hash.csv.xdelta" "$T/hash.csv" \
 && [ "$(md5 "$T/ShcPack.cpk")" = ba93cf943333aec995a00a09b7492b79 ]; then
  echo "DONE! The game is now in English. Start it, and if it asks to install data, say yes."
else
  cp "$T/ShcPack.cpk.original" "$T/ShcPack.cpk"; cp "$T/hash.csv.original" "$T/hash.csv"
  echo "[X] Patching failed; your original files were put back."; exit 1
fi
