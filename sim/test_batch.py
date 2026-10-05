#!/usr/bin/env python3
"""Host oracle checks, configuration agreement and exact RTL full-file comparison."""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('batch',ROOT/'tools/batch.py')
batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)


class BatchTests(unittest.TestCase):
    def test_configuration_agreement(self):
        self.assertEqual((ROOT/'rtl/batch_cases.vh').read_text(),batch.rtl_configuration())

    def test_actual_rtl_file(self):
        data=bytes(int(x,16) for x in (ROOT/'work/sim/batch/batch-written.hex').read_text().split())
        self.assertTrue(batch.verify(data)['pass_'])

    def test_actual_serial_file(self):
        data=bytes(int(x,16) for x in (ROOT/'work/sim/batch/batch-spi-written.hex').read_text().split())
        self.assertTrue(batch.verify(data)['pass_'])

    def test_guard_and_wrong_bytes_rejected(self):
        data=bytearray(batch.expected_file());data[8191]^=1
        self.assertEqual(batch.verify(data)['failed_regions'],[0])
        data=bytearray(batch.expected_file());data[0]^=1
        self.assertFalse(batch.verify(data)['pass_'])
        self.assertFalse(batch.verify(data[:-1])['pass_'])
        self.assertFalse(batch.verify(data+b'\x00')['pass_'])

    def test_shrinking_overwrite_retains_tail(self):
        config=batch.configuration();data=batch.expected_file()
        for index in (30,31):
            c=config['cases'][index];start=c['region_offset']+c['offset_in_region']
            large,small=c['write_lengths']
            self.assertEqual(data[start:start+small],batch.payload(c,2,small))
            self.assertEqual(data[start+small:start+large],batch.payload(c,1,large)[small:])


if __name__=='__main__':unittest.main()
