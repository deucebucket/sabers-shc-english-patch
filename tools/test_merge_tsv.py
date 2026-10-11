#!/usr/bin/env python3
"""Tests for tools/merge_tsv.py (issue #10: per-cell line-ending preservation).

Run:  python3 tools/test_merge_tsv.py
"""
import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge_tsv import cell_style, merge_one  # noqa: E402


def write(path, data):
    path.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))


class CellStyleTests(unittest.TestCase):
    def test_crlf(self):
        self.assertEqual(cell_style('a\r\nb\r\nc'), '\r\n')

    def test_lf(self):
        self.assertEqual(cell_style('a\nb'), '\n')

    def test_cr(self):
        self.assertEqual(cell_style('a\rb'), '\r')

    def test_no_breaks(self):
        self.assertEqual(cell_style('plain text'), '\n')

    def test_mixed_dominant_crlf(self):
        # 2 CRLF vs 1 LF -> CRLF wins
        self.assertEqual(cell_style('a\r\nb\r\nc\nd'), '\r\n')

    def test_mixed_dominant_cr(self):
        # 2 CR vs 1 LF -> CR wins
        self.assertEqual(cell_style('a\rb\rc\nd'), '\r')

    def test_tie_breaks_toward_crlf(self):
        self.assertEqual(cell_style('a\r\nb\nc'), '\r\n')


def make_paths(tmp, csv_bytes, tsv_text):
    csv_path = Path(tmp) / 'm.csv'
    tsv_path = Path(tmp) / 'm.tsv'
    out_path = Path(tmp) / 'out.csv'
    write(csv_path, csv_bytes)
    write(tsv_path, tsv_text)
    return tsv_path, csv_path, out_path


class MergeOneTests(unittest.TestCase):
    def test_crlf_cell_stays_crlf(self):
        # Two-row CSV (comment + header + one data row); message cell has CRLF.
        csv_bytes = ('#comment\r\n'
                     'ID,Message\r\n'
                     '1,"old line1\r\nold line2"\r\n').encode('utf-8')
        tsv = 'row\tcolumn\tenglish\n3\tmessage\tnew line1\\nnew line2\n'
        with tempfile.TemporaryDirectory() as tmp:
            t, c, o = make_paths(tmp, csv_bytes, tsv)
            n, warn = merge_one(t, c, o)
            self.assertEqual(n, 1)
            out = o.read_bytes()
        self.assertIn(b'new line1\r\nnew line2', out)
        self.assertNotIn(b'new line1\nnew line2', out.replace(b'\r\n', b''))

    def test_lf_cell_stays_lf(self):
        csv_bytes = ('#comment\n'
                     'ID,Message\n'
                     '1,"old line1\nold line2"\n').encode('utf-8')
        tsv = 'row\tcolumn\tenglish\n3\tmessage\tnew line1\\nnew line2\n'
        with tempfile.TemporaryDirectory() as tmp:
            t, c, o = make_paths(tmp, csv_bytes, tsv)
            merge_one(t, c, o)
            out = o.read_bytes()
        self.assertIn(b'new line1\nnew line2', out)
        self.assertNotIn(b'\r\n', out.split(b'new line1')[1].split(b'new line2')[0])

    def test_cr_cell_stays_cr(self):
        csv_bytes = ('#comment\r'
                     'ID,Message\r'
                     '1,"old line1\rold line2"\r').encode('utf-8')
        tsv = 'row\tcolumn\tenglish\n3\tmessage\tnew line1\\nnew line2\n'
        with tempfile.TemporaryDirectory() as tmp:
            t, c, o = make_paths(tmp, csv_bytes, tsv)
            merge_one(t, c, o)
            out = o.read_bytes()
        self.assertIn(b'new line1\rnew line2', out)
        # the in-cell break must be a lone CR, not CRLF
        cell = out.split(b'new line1')[1].split(b'new line2')[0]
        self.assertEqual(cell, b'\r')

    def test_mixed_cell_takes_dominant_style(self):
        csv_bytes = ('#c\r\n'
                     'ID,Message\r\n'
                     '1,"a\r\nb\r\nc\nd"\r\n').encode('utf-8')
        tsv = 'row\tcolumn\tenglish\n3\tmessage\tx\\ny\\nz\n'
        with tempfile.TemporaryDirectory() as tmp:
            t, c, o = make_paths(tmp, csv_bytes, tsv)
            merge_one(t, c, o)
            out = o.read_bytes()
        self.assertIn(b'x\r\ny\r\nz', out)

    def test_cell_without_breaks_unchanged_shape(self):
        csv_bytes = ('#c\r\nID,Message\r\n1,plain old\r\n').encode('utf-8')
        tsv = 'row\tcolumn\tenglish\n3\tmessage\tplain new\n'
        with tempfile.TemporaryDirectory() as tmp:
            t, c, o = make_paths(tmp, csv_bytes, tsv)
            merge_one(t, c, o)
            out = o.read_bytes()
        self.assertIn(b'plain new\r\n', out)
        self.assertNotIn(b'plain old', out)

    def test_lone_cr_file_keeps_cr_row_terminators(self):
        csv_bytes = ('#c\rID,Message\r1,hello\r').encode('utf-8')
        tsv = 'row\tcolumn\tenglish\n3\tmessage\tbye\n'
        with tempfile.TemporaryDirectory() as tmp:
            t, c, o = make_paths(tmp, csv_bytes, tsv)
            merge_one(t, c, o)
            out = o.read_bytes()
        self.assertEqual(out, b'#c\rID,Message\r1,bye\r')

    def test_round_trip_fixture(self):
        # Full merge over a fixture mixing all styles, message+short columns.
        csv_bytes = ('#c1\r\n'
                     'ID,Message,Shortened Message\r\n'
                     '1,"m1a\r\nm1b","s1a\ns1b"\r\n'
                     '2,"m2a\rm2b",plain\r\n').encode('utf-8')
        tsv = ('row\tcolumn\tenglish\n'
               '3\tmessage\tEN1a\\nEN1b\n'
               '3\tshort\tES1a\\nES1b\n'
               '4\tmessage\tEN2a\\nEN2b\n'
               '4\tshort\tES2\n')
        with tempfile.TemporaryDirectory() as tmp:
            t, c, o = make_paths(tmp, csv_bytes, tsv)
            n, warn = merge_one(t, c, o)
            self.assertEqual(n, 4)
            rows = list(csv.reader(io.StringIO(
                o.read_bytes().decode('utf-8'))))
        self.assertEqual(rows[2][1], 'EN1a\r\nEN1b')   # CRLF kept
        self.assertEqual(rows[2][2], 'ES1a\nES1b')     # LF kept
        self.assertEqual(rows[3][1], 'EN2a\rEN2b')     # CR kept
        self.assertEqual(rows[3][2], 'ES2')            # no-break cell
        # untouched structure intact
        self.assertEqual(rows[0], ['#c1'])
        self.assertEqual(rows[1], ['ID', 'Message', 'Shortened Message'])
        self.assertEqual(rows[2][0], '1')
        self.assertEqual(rows[3][0], '2')

    def test_untouched_cells_byte_identical(self):
        # Cells not listed in the TSV must come back byte-for-byte.
        csv_bytes = ('#c\r\n'
                     'ID,Message\r\n'
                     '1,"keep\r\nme",other\r\n'
                     '2,"change\r\nhere",x\r\n').encode('utf-8')
        tsv = 'row\tcolumn\tenglish\n4\tmessage\tnew\\ntext\n'
        with tempfile.TemporaryDirectory() as tmp:
            t, c, o = make_paths(tmp, csv_bytes, tsv)
            merge_one(t, c, o)
            out = o.read_bytes()
        self.assertIn(b'"keep\r\nme"', out)
        self.assertIn(b'new\r\ntext', out)


if __name__ == '__main__':
    unittest.main(verbosity=2)
