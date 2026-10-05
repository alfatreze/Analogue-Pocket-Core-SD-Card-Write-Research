#!/usr/bin/env python3
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import stress,batch
class StressTests(unittest.TestCase):
    def test_parameter_agreement(self):
        self.assertEqual((ROOT/'rtl/batch_cases.vh').read_text(),batch.rtl_configuration())
        for a,b in zip(stress.configuration()['cases'],batch.configuration()['cases']):
            self.assertEqual((a['region_offset'],a['offset_in_region'],a['pattern'],a['write_lengths'][0]),(b['region_offset'],b['offset_in_region'],b['pattern'],max(b['write_lengths'])))
    def test_full_rtl_file(self):
        data=bytes(int(x,16) for x in (ROOT/'work/sim/stress/full/stress-written.hex').read_text().split())
        self.assertTrue(stress.verify(data)['pass'])
    def test_actual_spi_file(self):
        data=bytes(int(x,16) for x in (ROOT/'work/sim/stress/spi/stress-spi-written.hex').read_text().split())
        self.assertTrue(stress.verify(data,64)['pass'])
    def test_final_operations(self):
        ops=[stress.final_operation(i) for i in range(32)]
        self.assertEqual(set(ops),set(range(9968,10000)))
        self.assertEqual(ops[0],9984);self.assertEqual(ops[31],9983)
    def test_changing_generations(self):
        # Even the 1-byte case changes on each adjacent visit, including low-byte wrap.
        for c in stress.configuration()['cases']:
            length=c['write_lengths'][0]
            for visit in (0,1,254,255,256,310):
                self.assertNotEqual(stress.payload(c['id']+visit*32,length),stress.payload(c['id']+(visit+1)*32,length))
    def test_guards_size_and_old_generation_rejected(self):
        data=bytearray(stress.expected_file());data[8191]^=1
        self.assertEqual(stress.verify(data)['failed_regions'],[0])
        self.assertFalse(stress.verify(stress.expected_file(64))['pass'])
        self.assertFalse(stress.verify(stress.expected_file()[:-1])['pass'])
        self.assertFalse(stress.verify(stress.expected_file()+b'\x00')['pass'])
if __name__=='__main__':unittest.main()
