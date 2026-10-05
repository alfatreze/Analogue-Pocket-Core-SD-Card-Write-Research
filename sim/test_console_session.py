#!/usr/bin/env python3
import contextlib,io,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import console_transport as c,jtag_session as j
class SessionTests(unittest.TestCase):
 def raw(self,build='B005'):
  tag='SDW5' if build=='B005' else 'SDW6';words=[0x53445705 if build=='B005' else 0x53445706,0xc0000100]+[0]*14
  return tag+' summary words='+','.join(f'{w:08x}' for w in words)+'\n'+tag+' done\n'+tag+' transport done\n'
 def test_correct_signatures(self):
  for b in ('B005','B006'):self.assertTrue(j.valid_packet(self.raw(b),b))
 def test_foreign_signature_refused(self):
  self.assertFalse(j.valid_packet(self.raw().replace('53445705','53445706'),'B005'))
 def test_packet_length_revision(self):
  self.assertFalse(j.valid_packet('SDW5 summary words=53445705,c0000100','B005'))
  self.assertFalse(j.valid_packet(self.raw().replace('c0000100','c0100100'),'B005'))
 def test_tag_injection_refused(self):
  with self.assertRaises(ValueError):c.invocation('card-writing-lab/test.tcl','SDW5; error bad')
 def test_invocation_has_no_unsupported_exit(self):
  s=c.invocation('card-writing-lab/test.tcl','SDW5');self.assertIn('transport done',s);self.assertNotIn('exit ',s)
 def client(self,**changes):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'tools').mkdir();(root/'tools/jtag_recovery.tcl').write_text('fixture')
   response=dict(raw=self.raw(),transport_done=True,natural_exit=False,controlled_exit=True,returncode=143,script_sha256='fixture',cleanup={'returncode':0});response.update(changes)
   with patch.object(j,'ROOT',root),patch.object(j.console_transport,'run',return_value=response),patch.object(sys,'argv',['client','--build','B005','status']),contextlib.redirect_stdout(io.StringIO()):j.main()
 def test_controlled_exit_accepted(self):self.client()
 def test_unverified_cleanup_refused(self):
  with self.assertRaises(SystemExit):self.client(controlled_exit=False)
 def test_missing_marker_refused(self):
  with self.assertRaises(SystemExit):self.client(transport_done=False)
 def test_script_error_refused(self):
  with self.assertRaises(SystemExit):self.client(raw=self.raw()+'SDW5 ERROR: failed\n')
if __name__=='__main__':unittest.main()
