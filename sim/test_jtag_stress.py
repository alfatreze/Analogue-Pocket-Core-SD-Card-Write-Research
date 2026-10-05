#!/usr/bin/env python3
import sys,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import jtag_stress,stress
MOCK=r'''
set source_value 0
proc after {args} {}
proc get_service_paths {kind} {return fake_service}
proc claim_service {args} {return fake_claim}
proc close_service {args} {}
proc issp_get_instance_info {args} {return {instance_name SDW4 source_width 32 probe_width 511}}
proc issp_read_source_data {args} {return [format %08x $::source_value]}
proc issp_write_source_data {handle value} {set ::source_value [expr {$value}]}
proc issp_read_probe_data {args} {
 set op [expr {$::source_value&16383}];set c [expr {$op%32}]
 set h [expr {($::source_value&0x80000000)|($::test_cold<<30)|0x20000000|($::revision<<18)|($::test_status<<14)|16383}]
 set count [expr {$::test_status==0?0:($::test_cold?32:10000)}]
 set commands [expr {$::test_status==0?0:($::test_cold?32:20000)}]
 set words [list 0x53445704 $h $op $count $count 0 $commands [lindex $::offsets $c] [lindex $::lengths $c] [expr {$::test_cold?0x80000006:0x80000007}] [expr {$::test_cold?0:123}] 456 [expr {$::test_cold?0xffffffff:123}] [expr {$::test_cold?0:123}] 456 456]
 set packet "";foreach w $words {append packet [format %08x $w]};return $packet
}
'''
class JtagStressTests(unittest.TestCase):
    def run_script(self,mode,status,cold=0,revision=2):
        cases=stress.configuration()['cases']
        prefix='set offsets {'+' '.join(str(c['region_offset']+c['offset_in_region']) for c in cases)+'}\n'
        prefix+='set lengths {'+' '.join(str(c['write_lengths'][0]) for c in cases)+'}\n'
        code=prefix+MOCK+f'\nset test_status {status}\nset test_cold {cold}\nset revision {revision}\nset mode {mode}\nsource {{{ROOT/"tools/jtag_stress.tcl"}}}\n'
        return subprocess.run(['tclsh'],input=code,text=True,capture_output=True)
    def test_all_10000_records(self):
        r=self.run_script('results',4);self.assertEqual(r.stderr,'');self.assertEqual(r.stdout.count('SDW4 record'),10000)
        self.assertTrue(jtag_stress.decode(r.stdout)['pass'])
        self.assertFalse(jtag_stress.decode(r.stdout.replace('80000007','80000403',1))['pass'])
        self.assertFalse(jtag_stress.decode(r.stdout+'\n'+next(x for x in r.stdout.splitlines() if 'SDW4 record' in x))['pass'])
    def test_failed_session_keeps_successful_records(self):
        raw=self.run_script('results',5).stdout
        raw=raw.replace('passed=10000 failed=0 commands=20000 first_failure=16383','passed=9999 failed=1 commands=20000 first_failure=7')
        lines=[]
        for line in raw.splitlines():
            if 'SDW4 record' in line:
                prefix,encoded=line.split('words=');words=[int(w,16) for w in encoded.split(',')]
                words[1]=(words[1]&0xffffc000)|7;words[4]=9999;words[5]=1
                if words[2]==7:words[9]=0x80000403
                line=prefix+'words='+','.join(f'{w:08x}' for w in words)
            lines.append(line)
        decoded=jtag_stress.decode('\n'.join(lines))
        self.assertFalse(decoded['pass'])
        self.assertFalse(decoded['records'][7]['pass_'])
        self.assertTrue(decoded['records'][39]['pass_'])
        self.assertEqual(sum(not r['pass_'] for r in decoded['records']),1)

    def test_cold_final_indices(self):
        r=self.run_script('results',4,1);self.assertEqual(r.stderr,'');self.assertTrue(jtag_stress.decode(r.stdout)['pass'])
    def test_ready_request(self):
        r=self.run_script('start',0);self.assertIn('SDW4 requested start',r.stdout)
    def test_busy_and_revision_refused(self):
        for status,revision in [(2,2),(0,0),(0,1),(0,3)]:
            r=self.run_script('start',status,revision=revision);self.assertNotIn('requested start',r.stdout);self.assertTrue(r.stderr)
if __name__=='__main__':unittest.main()
