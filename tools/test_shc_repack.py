#!/usr/bin/env python3
"""Regression tests for the repack storage rule and the CSV parser model.

    python3 tools/test_shc_repack.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crilayla_comp import compress_crilayla  # noqa: E402
from shc_cpk import decompress_crilayla  # noqa: E402
from shc_repack import choose_storage  # noqa: E402
from shc_csv_model import parse, CsvCrash, count_rows  # noqa: E402

# Byte-identical shape of v3's message/battle/120_Noise_BattleMessage.csv
# (328 bytes, LF line endings, no BOM).  Its CRILAYLA stream is ALSO 328
# bytes, which made the game read the compressed bytes as CSV (issue #3).
NOISE_V3 = (
    b'#Noise battle messages,,,,,,,,,,,\n'
    b'#Skill ID,Message No.,Set No.,Face ID,Voice ID,Shortened message ID,'
    b'Next message ID,Display time (ms),Delay time (ms),Message,'
    b'Shortened message,Comment\n'
    b',4,,,0,,,,,\xe3\x80\x8c\xe2\x80\xa6\xe2\x80\xa6\xe3\x80\x8d,,Dodge\n'
    b',5,,,0,,,,,\xe3\x80\x8c\xe2\x80\xa6\xe2\x80\xa6\xe3\x80\x8d,,No damage\n'
    b',6,,,1,,,,,\xe3\x80\x8c\xe2\x80\xa6\xe2\x80\xa6\xe3\x80\x8d,,Survival line\n'
    b',7,,,2,,,,,\xe3\x80\x8c\xe2\x80\xa6\xe2\x80\xa6\xe3\x80\x8d,,Defeat line\n'
)


class StorageRule(unittest.TestCase):
    def test_noise_v3_is_the_poison_case(self):
        self.assertEqual(len(NOISE_V3), 328)
        comp = compress_crilayla(NOISE_V3)
        self.assertEqual(len(comp), 328, 'compressor output changed; the '
                         'regression this test guards may no longer reproduce')
        self.assertEqual(decompress_crilayla(comp), NOISE_V3)

    def test_choose_storage_stores_raw_when_not_smaller(self):
        stored = choose_storage(NOISE_V3)
        self.assertIs(stored, NOISE_V3)
        self.assertFalse(stored.startswith(b'CRILAYLA'))

    def test_choose_storage_compresses_when_smaller(self):
        raw = b'x,y,z\n' * 200
        comp = choose_storage(raw)
        self.assertTrue(comp.startswith(b'CRILAYLA'))
        self.assertLess(len(comp), len(raw))
        self.assertEqual(decompress_crilayla(comp), raw)

    def test_game_parser_crashes_on_the_raw_stream(self):
        comp = compress_crilayla(NOISE_V3)
        with self.assertRaises(CsvCrash):
            parse(comp)
        # the register state RPCS3 dumped at PC 0x42e518 (issue #3):
        self.assertEqual(count_rows(comp, 0), 1)       # r29 == 1
        self.assertEqual(comp.count(b'"') % 2, 1)      # r22 (in_quote) == 1

    def test_game_parser_accepts_the_csv(self):
        rows = parse(NOISE_V3)
        self.assertEqual(len(rows), 6)
        self.assertEqual(set(rows), {12})


class ParserModel(unittest.TestCase):
    def test_bom_crlf_quoted_newline(self):
        buf = b'\xef\xbb\xbf#a,b,c\r\n1,"two\r\nlines",3\r\n'
        self.assertEqual(parse(buf), [3, 3])

    def test_unclosed_quote_first_row(self):
        with self.assertRaises(CsvCrash):
            parse(b'a,"b,c\nd,e,f\n')

    def test_no_trailing_newline(self):
        self.assertEqual(parse(b'a,b\nc,d'), [2, 2])


if __name__ == '__main__':
    unittest.main(verbosity=2)
