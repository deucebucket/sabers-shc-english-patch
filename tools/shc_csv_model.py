#!/usr/bin/env python3
"""shc_csv_model.py - Model of the SHC game's CSV parser (BLJS10244 EBOOT).

Reconstructed from the decrypted EBOOT.elf: count_rows at 0x42e168 and
parse at 0x42e25c (the crash in issue #3 is the store at 0x42e54c).

Rules the game applies, in order:
  1. A UTF-8 BOM (EF BB BF) is skipped.
  2. count_rows: '"' toggles in_quote; an unquoted CR or LF ends a row
     (CR LF counts once); the count is 1 + terminators, minus 1 if the
     last byte is CR/LF.  Allocates that many row records.
  3. pass 2: '"' toggles in_quote; an unquoted ',' adds a cell; an
     unquoted LF (or the last byte of the buffer, when not in a quote)
     closes the row and allocates its cell array.
  4. pass 3: fills cell byte ranges.  Its first action is
     rows[0].cells[0].start = <start>, with NO null check.

So a buffer whose first row is never closed (a quote opened on the first
line and never closed before EOF) makes rows[0].cells NULL and the game
writes to address 0x8: "Access violation writing location 0x8".
A row closed in pass 2 beyond the count from step 2 overruns the heap.

Usage:
    python3 shc_csv_model.py file.csv [...]      -> OK/CRASH per file
"""
import sys


class CsvCrash(Exception):
    """The real parser would dereference NULL / overrun on this input."""


def bom_start(buf):
    return 3 if buf[:3] == b'\xef\xbb\xbf' else 0


def count_rows(buf, start):
    """0x42e168."""
    n = len(buf)
    rows, q, i = 1, 0, start
    while i < n:
        c = buf[i]
        if c == 0x22:
            q ^= 1
        if not q and c in (0x0d, 0x0a):
            rows += 1
            if c == 0x0d and i + 1 < n and buf[i + 1] == 0x0a:
                i += 1
        i += 1
    if n and buf[n - 1] in (0x0a, 0x0d):
        rows -= 1
    return rows


def parse(buf):
    """Return the per-row cell counts the game would compute, or raise."""
    n = len(buf)
    start = bom_start(buf)
    nrows = count_rows(buf, start)
    rows = [None] * nrows
    ncell, q, r = 1, 0, 0
    for i in range(start, n):
        c = buf[i]
        if c == 0x22:
            q ^= 1
        if c == 0x2c and not q:
            ncell += 1
        if q:
            continue
        if c == 0x0a or i == n - 1:
            if r >= nrows:
                raise CsvCrash('pass 2 closes row %d but only %d rows were '
                               'allocated (heap overrun)' % (r, nrows))
            rows[r] = ncell
            r += 1
            ncell = 1
    if rows and rows[0] is None:
        raise CsvCrash('first row never closed (quote open to EOF): '
                       'rows[0].cells is NULL -> write to address 0x8')
    if q:
        raise CsvCrash('quote still open at EOF: %d row(s) unclosed'
                       % sum(1 for x in rows if x is None))
    return rows


def main(argv):
    bad = 0
    for p in argv:
        with open(p, 'rb') as fh:
            b = fh.read()
        try:
            rows = parse(b)
            print('OK    %s rows=%d cells=%s' % (p, len(rows), sorted(set(rows))))
        except CsvCrash as e:
            bad += 1
            print('CRASH %s: %s' % (p, e))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
