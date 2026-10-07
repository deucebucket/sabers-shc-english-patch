#!/usr/bin/env python3
"""merge_tsv.py - Apply translations/en/*.tsv onto extracted SHC CSVs.

Inverse of tools/extract_english.py. For each <name>.tsv in the translations
dir, reads <csv_dir>/<name>.csv, replaces the listed message cells, and writes
<out_dir>/<name>.csv, preserving BOM, line endings and all other cells.

TSV format: row<TAB>column<TAB>english   (row is 1-based over ALL csv rows,
including # comment rows; column is 'message' or 'short'; '\\n' in english
means a real line break inside the cell.)

Message columns are detected exactly like extract_english.py: within the first
6 rows, a header whose '#' stripped text is in {'Message', 'Shortened Message',
'\u30e1\u30c3\u30bb\u30fc\u30b8\u672c\u6587'}; 'Shortened Message' maps to the
'short' column, the others to 'message'.

Usage:
    python3 merge_tsv.py <translations/en dir> <extracted csv dir> <out dir>
"""
import csv
import io
import sys
from pathlib import Path

WANTED = {'Message', 'Shortened Message', 'メッセージ本文',
          'メッセージ', '短縮時メッセージ'}
# Headers mapping to the 'short' column (everything else in WANTED is 'message').
SHORT_HEADERS = {'Shortened Message', '短縮時メッセージ'}


def find_columns(rows):
    """Return {col_index: 'message'|'short'}.

    Same as extract_english.cols(), extended with the original Japanese
    headers ('メッセージ', '短縮時メッセージ'): the public TSVs were extracted
    from patched CSVs whose headers had been rewritten in English, but a fresh
    build merges onto the original Japanese-header CSVs.
    """
    for r in rows[:6]:
        idx = [i for i, c in enumerate(r) if c.strip().lstrip('#') in WANTED]
        if idx:
            return {i: ('short' if r[i].strip().lstrip('#') in SHORT_HEADERS
                        else 'message')
                    for i in idx}
    return {}


def merge_one(tsv_path, csv_path, out_path):
    raw = csv_path.read_bytes()
    bom = raw[:3] == b'\xef\xbb\xbf'
    text = raw[3:].decode('utf-8') if bom else raw.decode('utf-8')
    # detect line ending from the first line break
    if '\r\n' in text:
        lineterm = '\r\n'
    elif '\r' in text:
        lineterm = '\r'
    else:
        lineterm = '\n'
    rows = list(csv.reader(io.StringIO(text)))
    want = find_columns(rows)
    if not want:
        return 0, 'no message column found'
    rev = {}
    for i, kind in want.items():
        rev.setdefault(kind, []).append(i)

    applied = 0
    warnings = []
    for ln in tsv_path.read_text(encoding='utf-8').split('\n'):
        if not ln.strip():
            continue
        parts = ln.split('\t')
        if len(parts) < 3 or parts[0] == 'row':
            continue
        try:
            n = int(parts[0])
        except ValueError:
            warnings.append('bad row %r' % parts[0])
            continue
        kind = parts[1]
        eng = '\t'.join(parts[2:]).replace('\\n', '\n')
        if kind not in rev:
            warnings.append('row %d: no %r column in csv' % (n, kind))
            continue
        if n < 1 or n > len(rows):
            warnings.append('row %d out of range (%d rows)' % (n, len(rows)))
            continue
        r = rows[n - 1]
        for i in rev[kind]:
            while len(r) <= i:
                r.append('')
            r[i] = eng
            applied += 1

    buf = io.StringIO()
    csv.writer(buf, lineterminator=lineterm).writerows(rows)
    out = buf.getvalue()
    out_path.write_bytes((b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8'))
    return applied, '; '.join(warnings)


def main(tsv_dir, csv_dir, out_dir):
    tsv_dir, csv_dir, out_dir = Path(tsv_dir), Path(csv_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    total_files = total_cells = 0
    problems = []
    for tsv in sorted(tsv_dir.glob('*.tsv')):
        csv_path = csv_dir / (tsv.stem + '.csv')
        if not csv_path.exists():
            problems.append('%s: no matching csv' % tsv.name)
            continue
        n, warn = merge_one(tsv, csv_path, out_dir / (tsv.stem + '.csv'))
        total_files += 1
        total_cells += n
        if warn:
            problems.append('%s: %s' % (tsv.name, warn))
    print('merged %d files, %d cells' % (total_files, total_cells))
    for p in problems[:20]:
        print('WARN:', p)
    if len(problems) > 20:
        print('... and %d more warnings' % (len(problems) - 20))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit('usage: merge_tsv.py <translations/en dir> <csv dir> <out dir>')
    main(*sys.argv[1:4])
