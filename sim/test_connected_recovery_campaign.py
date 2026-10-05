#!/usr/bin/env python3
import sys,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import connected_recovery_campaign as c
import recovery
class ModelTests(unittest.TestCase):
 def test_initial_cold_packet(self):
  fixture=json.loads((c.ROOT/'work/evidence/b005-physical-jtag-reload-read01.json').read_text());data=fixture['result'];data['_summary_words']=fixture['summary_words']
  self.assertEqual(c.check_summary(data,c.model_files())['generation'],64)
 def test_initial_commit_history(self):
  data=json.loads((c.ROOT/'work/evidence/b005-physical-jtag-clean01.json').read_text())['result'];files=[bytearray(recovery.fixture()),bytearray(recovery.fixture())]
  self.assertEqual(c.apply_commits(data,files)['generation'],64);self.assertEqual(files,c.model_files())
 def test_prefix_preserves_latest(self):
  for point in range(4):
   files=c.model_files();old=bytes(files[1]);c.apply_prefix(files,point);self.assertEqual(bytes(files[1]),old);self.assertEqual(recovery.recover(*(bytes(x[512:1024]) for x in files))['generation'],64)
 def test_foreign_generation_refused(self):
  fixture=json.loads((c.ROOT/'work/evidence/b005-physical-jtag-reload-read01.json').read_text());data=fixture['result'];data['_summary_words']=fixture['summary_words'];data['summary']['selected_generation']=65
  with self.assertRaises(ValueError):c.check_summary(data,c.model_files())
 def test_wrong_recovered_crc_refused(self):
  fixture=json.loads((c.ROOT/'work/evidence/b005-physical-jtag-reload-read01.json').read_text());data=fixture['result'];data['_summary_words']=fixture['summary_words'];data['_summary_words'][13]^=1
  with self.assertRaises(ValueError):c.check_summary(data,c.model_files())
if __name__=='__main__':unittest.main()
