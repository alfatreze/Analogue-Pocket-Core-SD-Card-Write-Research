#!/usr/bin/env python3
"""Validate the SDW7 16-word trace decoder using synthetic packets only."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import jtag_powercut


def packet(*, active=False, is_read=False, status=0, state=1, source=None):
    if source is None:
        source = 0x10040000 if is_read else 0x10000000
    flags = (int(active) << 30) | (int(is_read) << 29) | (1 << 28) | (1 << 27)
    flags |= status << 20 | state << 15
    request = (1 << 30) if active and status == 2 else 0
    return [0x53445707, flags, 7, 3, 9, 1234, 65536, 1, 0x1007FFFC,
            0x10040000, 0x1007FFFC, source, 262144, request, 65536, 0]


def raw_row(prefix, words):
    return prefix + ','.join(f'{word:08x}' for word in words)


class SnapshotTests(unittest.TestCase):
    def test_active_and_monitor_trace(self):
        active = packet(active=True, status=2, state=5)
        raw = 'SDW7 summary words=' + ','.join(f'{word:08x}' for word in active)
        raw += '\n' + raw_row('SDW7 sample n=0 elapsed_ms=12 words=', active)
        result = jtag_powercut.decode(raw)
        self.assertTrue(result['valid'])
        self.assertTrue(result['summary']['active'])
        self.assertTrue(result['summary']['write_active'])
        self.assertEqual(result['samples'][0]['elapsed_ms'], 12)

    def test_arming_is_not_an_active_write(self):
        decoded = jtag_powercut.decode_words(packet(active=True, status=8, state=4))
        self.assertFalse(decoded['target_ack'])
        self.assertFalse(decoded['write_active'])

    def test_cold_read_source_contract(self):
        decoded = jtag_powercut.decode_words(packet(is_read=True, status=5, state=1))
        self.assertEqual(decoded['source_address'], 0x10040000)
        self.assertEqual(decoded['transfer_length'], 262144)

    def test_rejects_bad_length_magic_and_source(self):
        with self.assertRaises(ValueError):
            jtag_powercut.decode_words(packet()[:-1])
        bad = packet();bad[0] = 0
        with self.assertRaises(ValueError):
            jtag_powercut.decode_words(bad)
        bad = packet(is_read=True, source=0x10000000)
        with self.assertRaises(ValueError):
            jtag_powercut.decode_words(bad)

    def test_raw_capture_without_packet_is_not_valid(self):
        self.assertFalse(jtag_powercut.decode('SDW7 done')['valid'])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SnapshotTests)
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        raise SystemExit(1)
