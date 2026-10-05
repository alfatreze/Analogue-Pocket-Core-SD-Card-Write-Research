#!/usr/bin/env python3
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import verify_connected_campaign as v
class VerificationTests(unittest.TestCase):
 def fixture(self,root):
  folder=root/'work/evidence';(folder/'jtag').mkdir(parents=True)
  first=v.ROOT/'work/evidence/b005-physical-jtag-clean01.json';(folder/first.name).write_bytes(first.read_bytes())
  cold=json.loads((v.ROOT/'work/evidence/b005-physical-jtag-reload-read01.json').read_text())
  raw=folder/'jtag/b005-results-fixture.txt';raw.write_text('SDW5 summary words='+','.join(f'{x:08x}' for x in cold['summary_words'])+'\nSDW5 done\nSDW5 transport done\n')
  decoded=v.jtag_recovery.decode(raw.read_text());raw.with_suffix('.json').write_text(json.dumps(dict(decoded,exit_code=0,script_sha256='fixture')))
  result=dict(decoded,exit_code=0,script_sha256='fixture',_summary_words=cold['summary_words'])
  event=dict(trial='initial-reload-read',kind='read-only',pass_=True,result=result,raw_evidence=raw.name,raw_sha256=v.sha(raw),decoded_sha256=v.sha(raw.with_suffix('.json')))
  doc=dict(build='B005',state='completed',error=None,events=[event],expected_final_files=v.recovery.verify_files(*(bytes(x) for x in v.connected_recovery_campaign.model_files())))
  path=folder/'b005-connected-campaign.json';path.write_text(json.dumps(doc));return path,raw
 def test_complete_replay(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);self.fixture(root)
   with patch.object(v,'ROOT',root):d=v.verify('B005')
   self.assertEqual(d['committed_saves'],64);self.assertEqual(d['commands_including_partial_prefix_sessions'],324)
 def test_running_refused(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);path,_=self.fixture(root);d=json.loads(path.read_text());d['state']='running';path.write_text(json.dumps(d))
   with patch.object(v,'ROOT',root),self.assertRaises(ValueError):v.verify('B005')
 def test_changed_raw_refused(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);_,raw=self.fixture(root);raw.write_text(raw.read_text()+'changed')
   with patch.object(v,'ROOT',root),self.assertRaises(ValueError):v.verify('B005')
 def test_failed_prefix_audit_keeps_failure(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);path,_=self.fixture(root);d=json.loads(path.read_text());d.update(state='failed',error='transport failed');path.write_text(json.dumps(d))
   with patch.object(v,'ROOT',root):s=v.verify('B005',True)
   self.assertTrue(s['evidence_replay_pass']);self.assertFalse(s['pass']);self.assertFalse(s['campaign_completed']);self.assertEqual(s['termination_error'],'transport failed')
 def test_dropped_published_metadata_refused(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);path,_=self.fixture(root);d=json.loads(path.read_text());d['events'][0]['result'].pop('script_sha256');path.write_text(json.dumps(d))
   with patch.object(v,'ROOT',root),self.assertRaises(ValueError):v.verify('B005')
if __name__=='__main__':unittest.main()
