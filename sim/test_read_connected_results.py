#!/usr/bin/env python3
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import read_connected_results as c
import recovery
class ConnectedCollectorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'project';self.card=Path(self.tmp.name)/'card';self.root.mkdir();self.card.mkdir()
  self.patches=[patch.object(c,'ROOT',self.root),patch.object(c.install,'CARD',self.card),patch.object(c.install,'identity',return_value={})]
  for p in self.patches:p.start()
  data=[]
  for relative,g in zip(c.ASSETS,(649,648)):
   b=bytearray(recovery.fixture());b[512:1024]=recovery.record(g);data.append(bytes(b));p=self.card/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  p=self.card/'Cores/alfatreze.CARDWRITE02/core.json';p.parent.mkdir(parents=True);p.write_text('{"core":{"metadata":{"version":"0.5.0"}}}')
  (self.card/'protected.bin').write_bytes(b'keep');self.save(self.root/'work/evidence/cleanup-b005/after.json',c.install.snapshot())
  expected=recovery.verify_files(*data);self.campaign=self.root/'work/evidence/b006-connected-campaign.json';self.save(self.campaign,dict(state='completed',expected_final_files=expected))
  self.save(self.root/'work/evidence/b006-connected-summary.json',dict(**{'pass':True},campaign_sha256=c.install.sha(self.campaign),final_expected_files=expected))
 def save(self,p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d))
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.tmp.cleanup()
 def collect(self):return c.collect('B006','CONNECTED-006-TEST','2.7')
 def test_exact_model(self):
  d=self.collect();self.assertTrue(d['pass']);self.assertEqual(d['sd_metadata_version'],'0.5.0');self.assertEqual(d['experiment_build'],'B006')
 def test_guard_changed(self):
  p=self.card/c.ASSETS[0];b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b);self.assertFalse(self.collect()['pass'])
 def test_older_valid_record_refused(self):
  p=self.card/c.ASSETS[0];b=bytearray(p.read_bytes());b[512:1024]=recovery.record(647);p.write_bytes(b);self.assertFalse(self.collect()['pass'])
 def test_protected_change(self):
  (self.card/'protected.bin').write_bytes(b'changed');self.assertFalse(self.collect()['pass'])
 def test_extra_file_bytes(self):
  p=self.card/c.ASSETS[0];p.write_bytes(p.read_bytes()+b'extra');self.assertFalse(self.collect()['pass'])
 def test_running_campaign_refused(self):
  d=json.loads(self.campaign.read_text());d['state']='running';self.save(self.campaign,d)
  with self.assertRaises(ValueError):self.collect()
 def test_existing_trial_preserved(self):
  self.collect()
  with self.assertRaises(ValueError):self.collect()
 def test_invalid_trial_id(self):
  with self.assertRaises(ValueError):c.collect('B006','../escape','2.7')
 def test_readonly_preserves_card(self):
  before=c.install.snapshot();self.collect();self.assertEqual(c.install.snapshot(),before)
 def test_change_during_collection_fails(self):
  snapshot=c.install.snapshot();changed=dict(snapshot,added={'size':1,'sha256':'x'})
  with patch.object(c.install,'snapshot',side_effect=[snapshot,changed]):d=self.collect()
  self.assertFalse(d['pass']);self.assertFalse(d['stable_during_collection'])
 def test_stopped_forensics_never_qualifies_campaign(self):
  d=json.loads(self.campaign.read_text());d['state']='failed';self.save(self.campaign,d)
  summary=json.loads((self.root/'work/evidence/b006-connected-summary.json').read_text());summary.update(campaign_sha256=c.install.sha(self.campaign),evidence_replay_pass=True,**{'pass':False})
  self.save(self.root/'work/evidence/b006-connected-stopped-summary.json',summary)
  result=c.collect('B006','STOPPED-FORENSIC','2.7',True)
  self.assertTrue(result['file_evidence_pass']);self.assertFalse(result['pass']);self.assertFalse(result['campaign_completed'])
if __name__=='__main__':unittest.main()
