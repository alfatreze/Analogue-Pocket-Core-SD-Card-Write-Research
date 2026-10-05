import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import verify_guarded_completion as v
class Tests(unittest.TestCase):
 def setUp(self):
  labels=['initial-reload-read']
  for i in range(1,6):labels+=['clean-repeat-'+str(i),'read-repeat-'+str(i)]
  for p in range(4):labels+=['pause-r1-p'+str(p)+s for s in ('-resume','-core-cut-paused','-core-cut-recover')]
  labels+=['final-restore-inactive-record','final-read-both-valid']
  self.doc={'state':'completed','error':None,'planned_additional_clean_batches':5,'planned_pause_rounds':1,'events':[{'trial':x} for x in labels]}
  self.proof={'pass':True,'campaign_completed':True,'committed_saves':325,'commands_including_partial_prefix_sessions':1681,'read_only_sessions':11,'between_command_FPGA_interruptions':4,'reload_journals_reverified':24,'completed_event_count':25,'final_expected_files':{'pass':True,'generation':974,'valid':[True,True]}}
 def test_complete(self):self.assertTrue(v.check(self.doc,self.proof))
 def test_missing_event(self):
  self.doc['events'].pop()
  with self.assertRaises(ValueError):v.check(self.doc,self.proof)
 def test_wrong_order(self):
  self.doc['events'][1],self.doc['events'][2]=self.doc['events'][2],self.doc['events'][1]
  with self.assertRaises(ValueError):v.check(self.doc,self.proof)
 def test_changed_counts(self):
  for key in ('committed_saves','commands_including_partial_prefix_sessions','read_only_sessions','between_command_FPGA_interruptions','reload_journals_reverified','completed_event_count'):
   p=copy.deepcopy(self.proof);p[key]-=1
   with self.assertRaises(ValueError):v.check(self.doc,p)
 def test_torn_final_refused(self):
  self.proof['final_expected_files']['valid']=[True,False]
  with self.assertRaises(ValueError):v.check(self.doc,self.proof)
 def test_failed_refused(self):
  self.doc['state']='failed'
  with self.assertRaises(ValueError):v.check(self.doc,self.proof)
if __name__=='__main__':unittest.main()
