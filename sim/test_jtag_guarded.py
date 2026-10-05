#!/usr/bin/env python3
from pathlib import Path
import sys,subprocess,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import recovery,jtag_guarded
MOCK=r'''
set source_value 0
proc after {args} {}
proc get_service_paths {kind} {return fake_service}
proc claim_service {args} {return fake_claim}
proc close_service {args} {}
proc issp_get_instance_info {args} {return {instance_name SDW6 source_width 32 probe_width 511}}
proc issp_read_source_data {args} {return [format %08x $::source_value]}
proc issp_write_source_data {handle value} {set ::source_value [expr {$value}]}
proc issp_read_probe_data {args} {
 set op [expr {$::source_value&63}]
 set h [expr {($::source_value&0x80000000)|($::terminal<<30)|($::runmode<<28)|($::revision<<20)|($::test_status<<16)|($::test_state<<8)}]
 set w [list 0x53445706 $h $op $::count $::commands 3 63 0 64 0 [expr {$::runmode==1?64:$op+1}] 0 [expr {$::runmode==1?0x80000006:($op%2?0x8000000f:0x80000007)}] [lindex $::crcs [expr {$::runmode==1?63:$op}]] [lindex $::crcs 63] 123]
 set packet "";foreach x $w {append packet [format %08x $x]};return $packet
}
'''
class JtagTests(unittest.TestCase):
 def script(self,mode,status=4,runmode=0,state=18,revision=0,point=0):
  crcs=' '.join(str(recovery.checksum(recovery.record(i))) for i in range(1,65))
  count=0 if runmode==1 or status==0 else 64;commands=0 if status==0 else 2 if runmode==1 else 322
  code=f'set crcs {{{crcs}}}\n'+MOCK+f'\nset mode {mode}\nset point {point}\nset runmode {runmode}\nset terminal {0 if status==8 else 1}\nset revision {revision}\nset test_state {state}\nset test_status {status}\nset count {count}\nset commands {commands}\nsource {{{ROOT/"tools/jtag_guarded.tcl"}}}\n'
  return subprocess.run(['tclsh'],input=code,text=True,capture_output=True)
 def test_64_records(self):
  r=self.script('results');self.assertEqual(r.stderr,'');self.assertTrue(jtag_guarded.decode(r.stdout)['pass'])
  self.assertFalse(jtag_guarded.decode(r.stdout.replace('80000007','80000403',1))['pass'])
  self.assertFalse(jtag_guarded.decode(r.stdout+'\n'+next(l for l in r.stdout.splitlines() if 'SDW6 record' in l))['pass'])
 def test_recovery_only(self):
  r=self.script('results',runmode=1);self.assertEqual(r.stderr,'');self.assertTrue(jtag_guarded.decode(r.stdout)['pass']);self.assertNotIn('SDW6 record',r.stdout)
 def test_ready_and_pause(self):
  for mode in ('start','cold','pause'):
   r=self.script(mode,status=0,state=1);self.assertEqual(r.stderr,'');self.assertIn('requested '+mode,r.stdout)
 def test_busy_revision(self):
  for status,state,revision in ((2,4,0),(0,1,1),(4,18,0)):
   r=self.script('start',status=status,state=state,revision=revision);self.assertTrue(r.stderr);self.assertNotIn('requested start',r.stdout)
 def test_resume_only_paused_single(self):
  r=self.script('resume',status=8,runmode=2,state=14);self.assertEqual(r.stderr,'');self.assertIn('requested resume',r.stdout)
  self.assertTrue(self.script('resume').stderr)
 def test_busy_results(self):self.assertTrue(self.script('results',status=2,state=4).stderr)
if __name__=='__main__':unittest.main()
