#!/usr/bin/env python3
"""Independently replay a finished connected campaign against retained raw evidence."""
import argparse,hashlib,json,statistics,struct
from pathlib import Path
import recovery,jtag_recovery,jtag_guarded,connected_recovery_campaign,connected_guarded_campaign,resume_recovery
ROOT=recovery.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(build,allow_failed=False,publish=True):
 if build!='B006':raise ValueError('This verifier is only for resumed-baseline B006')
 prefix=build.lower();path=ROOT/'work/evidence'/(prefix+'-connected-resumed-campaign.json');doc=json.loads(path.read_text())
 completed=doc['state']=='completed' and doc['error'] is None
 if not completed and not (allow_failed and doc['state']=='failed' and doc['error']):raise ValueError('Completed campaign or explicit stopped-prefix audit required')
 codec=jtag_recovery if build=='B005' else jtag_guarded
 model=connected_recovery_campaign if build=='B005' else connected_guarded_campaign
 if build=='B005':
  first=json.loads((ROOT/'work/evidence/b005-physical-jtag-clean01.json').read_text())['result']
  files=[bytearray(recovery.fixture()),bytearray(recovery.fixture())];model.apply_commits(first,files);commits=64;commands=first['summary']['commands'];cycles=[r['words'][15] for r in first['records']]
 else:
  base=ROOT/'work/evidence/b005-resumed-summary.json'
  if json.loads(base.read_text())!=resume_recovery.verify():raise ValueError('Independent resumed baseline differs')
  if sha(base)!=doc['baseline_sha256']:raise ValueError('B005 baseline changed')
  prior=json.loads(base.read_text())['final_expected_files'];files=model.model_files(*(r['generation'] for r in prior['records']));commits=commands=0;cycles=[]
  if [hashlib.sha256(x).hexdigest() for x in files]!=prior['sha256']:raise ValueError('Initial B006 file model differs')
 reads=pauses=reloads=0;pending=None
 for event in doc['events']:
  raw=ROOT/'work/evidence/jtag'/event['raw_evidence']
  if sha(raw)!=event['raw_sha256']:raise ValueError('Raw evidence changed')
  transport_path=raw.with_suffix('.transport.json');t=json.loads(transport_path.read_text())
  if sha(transport_path)!=event['transport_sha256'] or not t['controlled_exit'] or not t['transport_done'] or t['cleanup']['returncode']!=0:raise ValueError('Owned transport evidence incomplete')
  for key in ('reload','setup_reload'):
   info=event.get(key)
   if info:
    journal=raw.parent/info['evidence'];j=json.loads(journal.read_text())
    if sha(journal)!=info['sha256'] or j['state']!='programmed' or sha(journal.with_suffix('.txt'))!=j['program_log_sha256']:raise ValueError('Reload evidence mismatch')
    reloads+=1
  if event['kind']=='safe-pause':
   words,s=model.jtag_reload_recovery.packet(raw.read_text()) if build=='B005' else model.jtag_load_guarded.packet(raw.read_text())
   if s!=event['summary'] or words!=event['words']:raise ValueError('Paused evidence differs')
   if build=='B005':model.jtag_reload_recovery.allowed_snapshot(raw.read_text(),point=event['point'])
   else:model.jtag_load_guarded.allowed_pause(raw.read_text(),event['point'])
   commands+=s['commands'];pauses+=1;pending=event['point'];continue
  preserved=json.loads(raw.with_suffix('.json').read_text());decoded=dict(preserved);transport_prefix='SDW5' if build=='B005' else 'SDW6'
  if decoded.pop('exit_code')!=0 or transport_prefix+' transport done' not in raw.read_text():raise ValueError('Complete successful transport required')
  decoded.pop('script_sha256')
  if codec.decode(raw.read_text())!=decoded or sha(raw.with_suffix('.json'))!=event['decoded_sha256']:raise ValueError('Raw/decoded evidence differs')
  result=dict(preserved);result['_summary_words']=event['result']['_summary_words']
  if result!=event['result']:raise ValueError('Published retained result differs')
  words=model.jtag_reload_recovery.packet(raw.read_text())[0] if build=='B005' else model.jtag_load_guarded.packet(raw.read_text())[0]
  if words!=result['_summary_words']:raise ValueError('Published summary words differ')
  if pending is not None:
   if not event['trial'].endswith('-core-cut-recover'):raise ValueError('Missing recovery after pause')
   model.apply_prefix(files,pending);pending=None
  if event['kind']=='save':
   model.apply_commits(result,files);commits+=result['summary']['completed'];cycles.extend(r['words'][15] for r in result['records'])
  else:model.check_summary(result,files);reads+=1
  commands+=result['summary']['commands']
 if pending is not None or recovery.verify_files(*(bytes(x) for x in files))!=doc['expected_final_files']:raise ValueError('Final independent replay differs')
 summary={'build':build,'pass':completed,'evidence_replay_pass':True,'campaign_completed':completed,'termination_error':doc['error'],'committed_saves':commits,'commands_including_partial_prefix_sessions':commands,'read_only_sessions':reads,'between_command_FPGA_interruptions':pauses,'reload_journals_reverified':reloads,'completed_event_count':len(doc['events']),'final_expected_files':doc['expected_final_files'],'save_cycle_latency':{'count':len(cycles),'min':min(cycles),'median':statistics.median(cycles),'max':max(cycles),'nominal_clock_Hz':74250000,'scope':'Retained sum of four writes plus verification read; primary units FPGA cycles, excludes boot reads and tooling/reloads'},'campaign_sha256':sha(path),'scope':'Independent replay of raw/decoded/counter/record/CRC and programming histories. Predicted final file hashes remain model outputs until host remount; FPGA cuts are not SD power cuts.'}
 out=ROOT/'work/evidence'/(prefix+('-connected-resumed-summary.json' if completed else '-connected-stopped-summary.json'))
 if not publish:return summary
 if out.exists():raise ValueError('Existing immutable summary; do not overwrite')
 out.write_text(json.dumps(summary,indent=2)+'\n');return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',choices=('B005','B006'),required=True);p.add_argument('--allow-failed',action='store_true');args=p.parse_args();print(json.dumps(verify(args.build,args.allow_failed),indent=2))
