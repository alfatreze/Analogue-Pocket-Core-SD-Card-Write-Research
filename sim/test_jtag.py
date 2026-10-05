#!/usr/bin/env python3
"""Tcl syntax/handshake tests with a fake ISSP service, not physical JTAG proof."""
import subprocess
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import batch
import jtag_batch
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOCK=r'''
set source_value 0
proc after {args} {}
proc get_service_paths {kind} {return {fake_service}}
proc claim_service {args} {return fake_claim}
proc close_service {args} {}
proc issp_get_instance_info {args} {
 return {instance_name SDW3 source_width 32 probe_width 256}
}
proc issp_read_source_data {args} {return [format %08x $::source_value]}
proc issp_write_source_data {handle value} {set ::source_value [expr {$value}]}
proc issp_read_probe_data {args} {
 set c [expr {$::source_value&31}]
 set p [expr {(($::source_value>>5)&3)+1}]
 set header [expr {($::source_value&0x80000000)|0x20008000|($c<<24)|($p<<22)|$::test_status}]
 set packet [expr {(0x53445703<<224)|($header<<192)|(0x4c002020<<160)|([lindex $::offsets $c]<<128)|(([lindex $::lengths $c]<<16 | [expr {$c==30 && $p==2 ? 64 : $c==31 && $p==2 ? 5 : [lindex $::lengths $c]}])<<96)|(0x80000007<<64)|(123<<32)|456}]
 set hex ""
 for {set i 7} {$i>=0} {incr i -1} {append hex [format %08x [expr {($packet>>($i*32))&0xffffffff}]]}
 return $hex
}
'''


class JtagTests(unittest.TestCase):
    def run_script(self,mode,status):
        config=batch.configuration()['cases']
        prefix='set offsets {'+' '.join(str(c['region_offset']+c['offset_in_region']) for c in config)+'}\n'
        prefix+='set lengths {'+' '.join(str(max(c['write_lengths'])) for c in config)+'}\n'
        code=prefix+MOCK+f'\nset test_status {status}\nset mode {mode}\nsource {{{ROOT/"tools/jtag_batch.tcl"}}}\n'
        return subprocess.run(['tclsh'],input=code,text=True,capture_output=True)

    def test_result_count(self):
        run=self.run_script('results',4)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(run.stderr,'')
        self.assertEqual(run.stdout.count('SDW3 record'),38)
        self.assertIn('completed=32 passed=32 failed=0 commands=76',run.stdout)
        self.assertTrue(jtag_batch.decode(run.stdout)['pass'])
        self.assertFalse(jtag_batch.decode(run.stdout.replace('80000007','80000403',1))['pass'])

    def test_ready_start(self):
        run=self.run_script('start',0)
        self.assertIn('requested start',run.stdout)

    def test_busy_start_rejected(self):
        run=self.run_script('start',2)
        self.assertIn('Batch is not READY',run.stderr)
        self.assertNotIn('requested start',run.stdout)


if __name__=='__main__':unittest.main()
