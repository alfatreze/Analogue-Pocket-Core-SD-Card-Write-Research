#!/usr/bin/env python3
"""Separately journal B005's remaining point-3 control/cut and final repair."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
import recovery,jtag_recovery,jtag_reload_session,connected_recovery_campaign as model,verify_connected_campaign
ROOT=recovery.ROOT
CHECKPOINT=ROOT/'work/evidence/jtag/b005-resumed-campaign.json'
SEQUENCE=[('reload',None),('pause',3),('resume',None),('result-save',None),('reload',None),('pause',3),('pause-status',3),('reload-cut',3),('cold',None),('result-read',None),('reload',None),('pause',0),('resume',None),('result-save',None),('reload',None),('cold',None),('result-read',None)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def base():
 prefix=verify_connected_campaign.verify('B005',True,publish=False)
 saved=json.loads((ROOT/'work/evidence/b005-connected-stopped-summary.json').read_text())
 if prefix!=saved:raise ValueError('Stopped prefix changed')
 physical=ROOT/'work/evidence/runs/BOOT-INCIDENT-20261005-01/result.json';host=json.loads(physical.read_text())
 if not host['file_evidence_pass'] or not host['exact_connected_model_pass'] or not host['stable_during_collection'] or host['file_verification']!=prefix['final_expected_files']:raise ValueError('Exact physical stopped prefix required')
 files=[bytearray((physical.parent/('recover-b005-'+label+'.bin')).read_bytes()) for label in ('a','b')]
 if recovery.verify_files(*(bytes(x) for x in files))!=prefix['final_expected_files']:raise ValueError('Preserved physical files changed')
 return files,{'power_return_summary_sha256':sha(ROOT/'work/evidence/b005-power-return-summary.json'),'stopped_campaign_sha256':prefix['campaign_sha256'],'stopped_summary_sha256':sha(ROOT/'work/evidence/b005-connected-stopped-summary.json'),'physical_result_sha256':sha(physical),'initial_file_sha256':[hashlib.sha256(x).hexdigest() for x in files]}
def result_from(raw):
 d=json.loads(raw.with_suffix('.json').read_text());codec=jtag_recovery.decode(raw.read_text())
 if d.get('exit_code')!=0 or codec!={k:v for k,v in d.items() if k not in ('exit_code','script_sha256')}:raise ValueError('Raw/decoded result differs')
 if not codec['pass']:raise ValueError('Retained hardware result failed')
 d['_summary_words']=jtag_reload_session.packet(raw.read_text())[0];return d

def verify(path=CHECKPOINT):
 doc=json.loads(path.read_text())
 if doc['state']!='completed' or doc.get('error'):raise ValueError('Completed resumed trial required')
 files,identity=base()
 if doc['base']!=identity or [(e['kind'],e['point']) for e in doc['events']]!=SEQUENCE:raise ValueError('Wrong base or remaining-trial sequence')
 power=json.loads((ROOT/'work/evidence/b005-power-return-summary.json').read_text());initial=ROOT/'work/evidence/jtag'/power['evidence']['results']['raw_file']
 if sha(initial)!=power['evidence']['results']['raw_sha256']:raise ValueError('Initial recovered endpoint evidence changed')
 initial_data=result_from(initial);model.check_summary(initial_data,files)
 saves=0;last=initial_data['summary']
 for e in doc['events']:
  p=ROOT/'work/evidence/jtag'/e['evidence']
  if p.parent!=ROOT/'work/evidence/jtag' or sha(p)!=e['sha256']:raise ValueError('Evidence identity/hash differs')
  if e['kind'].startswith('reload'):
   journal=json.loads(p.read_text())
   if journal['state']!='programmed' or journal['returncode']!=0 or sha(p.with_suffix('.txt'))!=journal['program_log_sha256'] or 'Successfully performed operation(s)' not in p.with_suffix('.txt').read_text():raise ValueError('Programming journal incomplete')
   audit=json.loads((ROOT/'work/evidence/custom-build-audit-recovery05.json').read_text())
   if journal['sof_sha256']!=audit['reports']['ap_core.sof']:raise ValueError('Unexpected image')
   if e['kind']=='reload-cut':
    if journal['core_interruption_point']!=3 or journal['before']!=last:raise ValueError('Unmatched safe interruption')
    model.apply_prefix(files,3)
   elif journal['core_interruption_point'] is not None:raise ValueError('Unexpected interruption')
   elif last and journal['before']!=last:raise ValueError('Reload before state changed')
  else:
   raw=p.read_text();transport=json.loads(p.with_suffix('.transport.json').read_text())
   if not transport['transport_done'] or not transport['controlled_exit'] or transport['cleanup']['returncode']!=0 or sha(p.with_suffix('.transport.json'))!=e['transport_sha256'] or sha(p.with_suffix('.json'))!=e['decoded_sha256'] or 'SDW5 ERROR:' in raw or 'SDW5 done' not in raw:raise ValueError('Incomplete owned console transport')
   if e['kind'].startswith('result'):
    d=result_from(p)
    if e['kind']=='result-save':model.apply_commits(d,files);saves+=d['summary']['completed']
    else:model.check_summary(d,files)
    last=d['summary']
   elif e['kind']=='pause-status':
    last=jtag_reload_session.allowed_snapshot(raw,point=3)
    if last['selected_generation']!=recovery.recover(*(bytes(x[512:1024]) for x in files))['generation']:raise ValueError('Paused generation mismatch')
   else:
    if 'SDW5 requested '+e['kind'] not in raw:raise ValueError('Request marker missing')
    _,s=jtag_reload_session.packet(raw)
    if e['kind'] in ('pause','cold') and not(s['status']==0 and s['state']==1 and s['completed']==0 and s['commands']==0):raise ValueError('Request not from fresh READY')
    if e['kind']=='resume':jtag_reload_session.allowed_snapshot(raw,point=3 if saves==0 else 0)
 final=recovery.verify_files(*(bytes(x) for x in files),649,expect_generated=True)
 if saves!=2 or not final['pass'] or final['valid']!=[True,True] or doc['expected_final_files']!=final:raise ValueError('Final repaired model differs')
 return {'pass':True,'campaign_sha256':sha(path),'base':identity,'new_commits':saves,'combined_B005_commits':649,'point_3_second_repetition_pass':True,'final_expected_files':final,'last_result':doc['last_result'],'scope':'Independent stopped-prefix replay plus exact host baseline and completed separately resumed point-3/control/repair histories. Predicted new file hashes await next remount; FPGA reloads are between commands, not SD power cuts.'}

def main():
 if Path('/Volumes/CARDWRITE').exists():raise ValueError('Host mounted; no trial')
 if CHECKPOINT.exists():raise ValueError('Existing resumed trial; no silent rerun')
 files,identity=base();power=json.loads((ROOT/'work/evidence/b005-power-return-summary.json').read_text());last=ROOT/'work/evidence/jtag'/Path(power['evidence']['results']['raw_file']).with_suffix('.json');d=result_from(last.with_suffix('.txt'));model.check_summary(d,files)
 doc={'state':'planned','base':identity,'events':[],'last_result':last.name,'expected_final_files':recovery.verify_files(*(bytes(x) for x in files)),'error':None}
 def save(state,error=None):
  doc.update(state=state,error=error,last_result=last.name,expected_final_files=recovery.verify_files(*(bytes(x) for x in files)));CHECKPOINT.write_text(json.dumps(doc,indent=2)+'\n')
 save('planned')
 try:
  for index,(kind,point) in enumerate(SEQUENCE):
   if kind.startswith('reload'):
    args=['--core-interruption-point','3'] if kind=='reload-cut' else ['--result',str(last)]
    cmd=[sys.executable,str(ROOT/'tools/jtag_reload_session.py'),*args];marker='Reload evidence: '
   else:
    mode='results' if kind.startswith('result') else 'status' if kind=='pause-status' else kind
    cmd=[sys.executable,str(ROOT/'tools/jtag_session.py'),'--build','B005',mode]+(['--point',str(point)] if kind=='pause' else []);marker='Raw JTAG evidence preserved: '
   run=subprocess.run(cmd,capture_output=True,text=True);capture=CHECKPOINT.parent/('b005-resume-action-'+str(index)+'.txt');capture.write_text(run.stdout+run.stderr)
   if run.returncode:raise ValueError('Action failed; no retry; '+capture.name)
   match=re.search(re.escape(marker)+r'(.+)',run.stdout)
   if not match:raise ValueError('Action evidence absent')
   p=Path(match[1]);assert p.parent==CHECKPOINT.parent
   event={'kind':kind,'point':point,'evidence':p.name,'sha256':sha(p)}
   if not kind.startswith('reload'):
    event.update(decoded_sha256=sha(p.with_suffix('.json')),transport_sha256=sha(p.with_suffix('.transport.json')))
   if kind=='reload-cut':model.apply_prefix(files,3)
   if kind.startswith('result'):
    d=result_from(p)
    if kind=='result-save':model.apply_commits(d,files)
    else:model.check_summary(d,files)
    last=p.with_suffix('.json')
   if kind=='pause-status':jtag_reload_session.allowed_snapshot(p.read_text(),point=3)
   doc['events'].append(event);save('running');print(str(index)+' '+kind+' PASS',flush=True)
  save('completed');proof=verify();out=ROOT/'work/evidence/b005-resumed-summary.json'
  if out.exists():raise ValueError('Existing proof; no overwrite')
  out.write_text(json.dumps(proof,indent=2)+'\n');print('B005 resumed trial independently verified; both expected records valid at generation 649',flush=True)
 except Exception as e:save('failed',str(e));raise
if __name__=='__main__':main()
