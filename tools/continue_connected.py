#!/usr/bin/env python3
"""Serialized B005 completion -> qualified B006 read-only gate -> bounded campaign."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
import recovery,jtag_load_guarded,connected_guarded_campaign as model
ROOT=recovery.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def preserved(output):
 match=re.search(r'Raw JTAG evidence preserved: (.+)',output)
 if not match:raise ValueError('Preserved result path absent')
 raw=Path(match[1]);return raw,json.loads(raw.with_suffix('.json').read_text())
def fresh_ready(raw):
 words,s=jtag_load_guarded.packet(raw)
 if not (s['status']==0 and s['state']==1 and s['completed']==0 and s['commands']==0):raise ValueError('Fresh B006 READY absent; no requests')
 return s
def main():
 public=ROOT/'work/evidence/b006-continuation.json'
 if public.exists():raise ValueError('Existing continuation evidence; no silent rerun')
 if Path('/Volumes/CARDWRITE').exists():raise ValueError('Host-mounted card')
 audit=ROOT/'work/evidence/custom-build-audit-guarded06.json';audit_hash=sha(audit)
 folder=ROOT/'work/evidence/jtag'/('b006-continuation-'+str(time.time_ns()));folder.mkdir()
 doc={'state':'waiting-for-B005','qualified_audit_sha256':audit_hash,'runner_sha256':sha(Path(__file__)),'scope':'Serialized bounded connected research; no physical card remount/power-loss claim.'}
 def save(state,error=None):doc.update(state=state,error=error);public.write_text(json.dumps(doc,indent=2)+'\n')
 def command(tool,*args):
  run=subprocess.run([sys.executable,str(ROOT/'tools'/tool),*map(str,args)],capture_output=True,text=True)
  path=folder/('action-'+str(len(list(folder.glob('action-*.txt'))))+'.txt');path.write_text(run.stdout+run.stderr)
  if run.returncode:raise ValueError('Action failed; stop without retries: '+str(path)+'\n'+run.stdout+run.stderr)
  return run.stdout
 save('waiting-for-B005');deadline=time.monotonic()+3*3600
 try:
  while True:
   baseline=ROOT/'work/evidence/b005-connected-campaign.json';b=json.loads(baseline.read_text())
   if b['state']=='completed':break
   if b['state']=='failed':raise ValueError('B005 failed; no loading')
   if time.monotonic()>deadline:raise ValueError('B005 did not finish within bounded wait; no loading')
   time.sleep(30)
  if sha(audit)!=audit_hash:raise ValueError('Qualified B006 audit changed while waiting')
  save('verifying-B005');command('verify_connected_campaign.py','--build','B005')
  last=ROOT/'work/evidence/jtag'/b['events'][-1]['raw_evidence'];doc['b005_final_result']=last.with_suffix('.json').name
  if b['events'][-1]['kind']!='read-only' or not b['expected_final_files']['pass']:raise ValueError('B005 final state is not repaired/read-only PASS')
  save('loading-B006');output=command('jtag_load_guarded.py','--previous-result',last.with_suffix('.json'),'--from-build','B005')
  match=re.search(r'Load evidence: (.+)',output)
  if not match:raise ValueError('Load evidence absent')
  load=Path(match[1]);doc['load_journal']=load.name;doc['load_journal_sha256']=sha(load)
  save('checking-fresh-B006');raw,_=preserved(command('jtag_guarded.py','status'));fresh_ready(raw.read_text())
  doc['ready_raw_sha256']=sha(raw)
  command('jtag_guarded.py','cold');raw,result=preserved(command('jtag_guarded.py','results'));words,_=jtag_load_guarded.packet(raw.read_text());result['_summary_words']=words
  files=model.model_files(*(r['generation'] for r in b['expected_final_files']['records']));model.check_summary(result,files)
  first={'build':'B006','pass':True,'result':result,'summary_words':words,'raw_sha256':sha(raw),'decoded_sha256':sha(raw.with_suffix('.json')),'load_journal_sha256':sha(load),'qualified_audit_sha256':audit_hash,'scope':'First physical B006 fixed-region guard and record/read-only recovery gate; card stays powered, no remount.'}
  out=ROOT/'work/evidence/b006-physical-jtag-initial-read.json'
  if out.exists():raise ValueError('Initial B006 evidence exists; preserve it')
  out.write_text(json.dumps(first,indent=2)+'\n');doc['first_read_result']=raw.with_suffix('.json').name
  print('B006 initial full-region read-only recovery PASS generation '+str(result['summary']['selected_generation']),flush=True)
  save('B006-campaign-running');command('connected_guarded_campaign.py','--initial-result',raw.with_suffix('.json'),'--batches',5,'--rounds',1)
  save('verifying-B006');command('verify_connected_campaign.py','--build','B006');save('completed');print('B005 and B006 connected campaigns completed; host remount pending.',flush=True)
 except Exception as e:save('failed',str(e));raise
if __name__=='__main__':main()
