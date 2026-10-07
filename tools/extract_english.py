#!/usr/bin/env python3
"""Extract ONLY the English message cells from patched SHC CSVs.

Output: one TSV per source CSV: row<TAB>column<TAB>english. No Japanese text, comments,
event notes, IDs or headers are written, so the output carries no game data.
Usage: extract_english.py <dir with patched CSVs> <out dir>
"""
import csv, io, re, sys
from pathlib import Path

JP = re.compile(r'[぀-ヿ㐀-鿿＀-￯]')
# Message columns by header name (BattleMessage files) or by the Japanese header label
# "message body" (map_message / soulLink files).
WANTED = {'Message', 'Shortened Message', 'メッセージ本文'}

def cols(rows):
    for r in rows[:6]:
        idx = [i for i, c in enumerate(r) if c.strip().lstrip('#') in WANTED]
        if idx:
            return {i: ('message' if r[i].strip() != 'Shortened Message' else 'short') for i in idx}
    return {}

def main(src, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    total = files = skipped_jp = 0
    for f in sorted(Path(src).glob('*.csv')):
        rows = list(csv.reader(io.StringIO(f.read_text(encoding='utf-8-sig'))))
        want = cols(rows)
        lines = []
        for n, r in enumerate(rows, 1):
            if r and r[0].startswith('#'):
                continue
            for i, kind in want.items():
                if i < len(r) and r[i].strip():
                    s = r[i]
                    if JP.search(s):
                        skipped_jp += 1
                        continue
                    lines.append('%d\t%s\t%s' % (n, kind, s.replace('\t', ' ').replace('\r', '').replace('\n', '\\n')))
        if lines:
            (out / (f.stem + '.tsv')).write_text('row\tcolumn\tenglish\n' + '\n'.join(lines) + '\n', encoding='utf-8')
            files += 1; total += len(lines)
    print('files=%d english_cells=%d cells_with_japanese_skipped=%d' % (files, total, skipped_jp))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
