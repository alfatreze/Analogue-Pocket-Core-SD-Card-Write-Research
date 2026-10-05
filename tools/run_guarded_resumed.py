#!/usr/bin/env python3
"""Serialize completed B005 resume -> qualified B006 load/read -> bounded campaign."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
import resume_recovery,jtag_load_resumed,jtag_guarded,connected_guarded_resumed as model,verify_guarded_resumed
ROOT=resume_recovery.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 folder=ROOT/'work/evidence/jtag/b006-resumed-transition';folder.mkdir(exist_ok=False);state={'state':'waiting-for-B005','error':None}
 def save(value,error=None):state.update(state=value,error=error);(folder/'transition.json').write_text(json.dumps(state,indent=2)+'\n')
 def command(label,tool,*args):
  run=subprocess.run([sys.executable,str(ROOT/'tools'/tool),*map(str,args)],capture_output=True,text=True);(folder/(label+'.txt')).write_text(run.stdout+run.stderr)
  if run.returncode:raise ValueError(label+' failed; preserved capture; no retries')
  return run.stdout
 save('waiting-for-B005')
 try:
  while True:
   d=json.loads(resume_recovery.CHECKPOINT.read_text())
   if d['state']=='failed':raise ValueError('B005 resume failed; no B006 loading')
   if d['state']=='completed':break
   time.sleep(5)
  proof=resume_recovery.verify();jtag_load_resumed.resumed_gate()
  qpath=ROOT/'work/evidence/resumed-clients-qualification.json';q=json.loads(qpath.read_text())
  if not q['pass']:raise ValueError('Resumed clients unqualified')
  for group in ('sources','reports'):
   for rel,h in q[group].items():
    if sha(ROOT/rel)!=h:raise ValueError('Resumed client qualification changed')
  state.update(B005_proof_sha256=sha(ROOT/'work/evidence/b005-resumed-summary.json'),client_qualification_sha256=sha(qpath));save('loading-B006')
  command('load','jtag_load_resumed.py','--from-build','B005','--previous-result',ROOT/'work/evidence/jtag'/proof['last_result']);save('B006-loaded-read-only-gate')
  command('cold','jtag_session.py','--build','B006','cold')
  text=command('cold-result','jtag_session.py','--build','B006','results');match=re.search(r'Raw JTAG evidence preserved: (.+)',text)
  if not match:raise ValueError('Initial B006 raw result absent')
  raw=Path(match[1]);d=json.loads(raw.with_suffix('.json').read_text());d['_summary_words']=model.jtag_load_guarded.packet(raw.read_text())[0]
  files=model.model_files(*(v['generation'] for v in proof['final_expected_files']['records']));model.check_summary(d,files)
  if d['summary']['mode']!=1 or d['summary']['commands']!=2 or d['summary']['completed']!=0:raise ValueError('Initial B006 was not read-only')
  state.update(initial_result=raw.with_suffix('.json').name);save('running-B006')
  command('campaign','connected_guarded_resumed.py','--initial-result',raw.with_suffix('.json'),'--batches','5','--rounds','1')
  verified=verify_guarded_resumed.verify('B006');state.update(final_generation=verified['final_expected_files']['generation'],new_B006_saves=verified['committed_saves']);save('completed');print('B006 bounded campaign complete and independently replayed; host remount pending',flush=True)
 except Exception as e:save('failed',str(e));raise
if __name__=='__main__':main()
