#!/usr/bin/env python3
"""Require the entire fixed B006 resumed campaign, beyond successful prefix replay."""
import hashlib,json
from pathlib import Path
import verify_guarded_resumed
ROOT=verify_guarded_resumed.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(doc,proof):
 labels=['initial-reload-read']
 for i in range(1,6):labels+=['clean-repeat-'+str(i),'read-repeat-'+str(i)]
 for p in range(4):labels+=['pause-r1-p'+str(p)+suffix for suffix in ('-resume','-core-cut-paused','-core-cut-recover')]
 labels+=['final-restore-inactive-record','final-read-both-valid']
 if doc['state']!='completed' or doc['error'] is not None or doc['planned_additional_clean_batches']!=5 or doc['planned_pause_rounds']!=1 or [e['trial'] for e in doc['events']]!=labels:raise ValueError('Full fixed trial sequence required')
 for key,expected in [('committed_saves',325),('commands_including_partial_prefix_sessions',1681),('read_only_sessions',11),('between_command_FPGA_interruptions',4),('reload_journals_reverified',24),('completed_event_count',25)]:
  if proof[key]!=expected:raise ValueError('Incomplete campaign count: '+key)
 final=proof['final_expected_files']
 if not proof['pass'] or not proof['campaign_completed'] or not final['pass'] or final['generation']!=974 or final['valid']!=[True,True]:raise ValueError('Final B006 repaired state differs')
 return True
if __name__=='__main__':
 path=ROOT/'work/evidence/b006-connected-resumed-campaign.json';proof=verify_guarded_resumed.verify('B006',publish=False);check(json.loads(path.read_text()),proof)
 summary=ROOT/'work/evidence/b006-connected-resumed-summary.json'
 if json.loads(summary.read_text())!=proof:raise ValueError('Published independent summary differs')
 out=ROOT/'work/evidence/b006-connected-resumed-completion.json'
 if out.exists():raise ValueError('Existing completion proof; no overwrite')
 out.write_text(json.dumps({'pass':True,'complete_fixed_sequence':True,'summary_sha256':sha(summary),'campaign_sha256':sha(path),'checker_sha256':sha(Path(__file__)),'scope':'All 25 expected events, 325 saves, 4 between-command cuts and repaired final generation 974 independently replayed; host remount/physical power-cut scope separate.'},indent=2)+'\n');print('Full B006 fixed campaign independently verified')
