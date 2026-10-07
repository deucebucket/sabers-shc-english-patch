#!/usr/bin/env python3
"""shc_cpk_check.py - Regression gate for a repacked SHC CPK.

Would have caught the v2/v3 Tsubasa-vs-Noise crash (issue #3).

Checks, for every member:
  A. storage consistency: FileSize == ExtractSize  <=> bytes do NOT start
     with "CRILAYLA"; FileSize != ExtractSize <=> bytes DO start with it.
     (CRI's reader decides compression from the TOC alone; the original
     ShcPack.cpk has 0 exceptions in 1,834 members.)
  B. every CRILAYLA member decompresses to exactly ExtractSize bytes.
  C. every *.csv member, as the GAME would see it (raw if stored, else
     decompressed), survives the game's CSV parser (shc_csv_model).
  D. optional, with --orig: every changed *.csv has the same row count and
     the same per-row cell counts as the original member.

Exit status 0 = PASS, 1 = FAIL (every failure is printed).

Usage:
    python3 shc_cpk_check.py patched.cpk [--orig ShcPack.cpk]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shc_cpk import get_files, decompress_crilayla  # noqa: E402
from shc_csv_model import parse, CsvCrash  # noqa: E402


def member_path(f):
    return ((f['dir'] or '') + '/' + f['name']).lstrip('/')


def game_view(data, f):
    """Bytes the game's loader hands to the consumer of this member."""
    raw = data[f['offset']:f['offset'] + f['size']]
    if f['size'] == f['extract_size']:
        return raw, False
    return decompress_crilayla(raw), True


def check(cpk_path, orig_path=None):
    fails = []
    data, files = get_files(cpk_path)
    orig = {}
    if orig_path:
        odata, ofiles = get_files(orig_path)
        for f in ofiles:
            orig[member_path(f)] = (odata, f)
    n_stored = n_comp = n_csv = 0
    for f in files:
        p = member_path(f)
        raw = data[f['offset']:f['offset'] + f['size']]
        is_cri = raw[:8] == b'CRILAYLA'
        stored = f['size'] == f['extract_size']
        if stored and is_cri:
            fails.append('A %s: FileSize==ExtractSize==%d but bytes are a CRILAYLA '
                         'stream; the game will read the compressed bytes as content'
                         % (p, f['size']))
            continue
        if not stored and not is_cri:
            fails.append('A %s: FileSize %d != ExtractSize %d but bytes are not CRILAYLA'
                         % (p, f['size'], f['extract_size']))
            continue
        view, comp = game_view(data, f)
        if comp:
            n_comp += 1
            if len(view) != f['extract_size']:
                fails.append('B %s: decompressed %d bytes, TOC ExtractSize %d'
                             % (p, len(view), f['extract_size']))
                continue
        else:
            n_stored += 1
        if p.lower().endswith('.csv'):
            n_csv += 1
            try:
                rows = parse(view)
            except CsvCrash as e:
                fails.append('C %s: game CSV parser would crash: %s' % (p, e))
                continue
            if p in orig:
                odata, of = orig[p]
                oview, _ = game_view(odata, of)
                if oview != view:
                    try:
                        orows = parse(oview)
                    except CsvCrash as e:
                        orows = None
                    if orows is not None:
                        if len(orows) != len(rows):
                            fails.append('D %s: %d rows, original has %d'
                                         % (p, len(rows), len(orows)))
                        elif orows != rows:
                            bad = [i for i, (a, b) in enumerate(zip(orows, rows)) if a != b]
                            fails.append('D %s: cell count differs on row(s) %s '
                                         '(orig %s vs new %s)'
                                         % (p, bad[:5], [orows[i] for i in bad[:5]],
                                            [rows[i] for i in bad[:5]]))
    print('%s: %d members (%d stored, %d CRILAYLA, %d csv parsed)%s'
          % (os.path.basename(cpk_path), len(files), n_stored, n_comp, n_csv,
             ', compared against ' + os.path.basename(orig_path) if orig_path else ''))
    for line in fails:
        print('FAIL', line)
    print('PASS' if not fails else 'FAIL (%d)' % len(fails))
    return 0 if not fails else 1


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or len(args) not in (1, 3) or (len(args) == 3 and args[1] != '--orig'):
        sys.exit(__doc__)
    sys.exit(check(args[0], args[2] if len(args) == 3 else None))
