#!/usr/bin/env python3
"""Load qualified B006 over JTAG after a preserved PASS and ABI compatibility checks."""
import argparse,hashlib,json,re,subprocess,sys,time
from pathlib import Path
import vm_build,jtag_recovery,jtag_guarded,resume_recovery
ROOT=vm_build.ROOT
BIN='/home/taualpha/intelFPGA_lite/25.1std/quartus/bin/'
REMOTE='/home/taualpha/card-writing-lab/guarded06-s1/src/fpga/output_files/ap_core.sof'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def live_summary(raw,codec):
 d=codec.decode(raw)
 if 'summary' not in d:raise ValueError('Actual matching endpoint snapshot absent')
 signature='53445705' if codec is jtag_recovery else '53445706'
 if 'summary words='+signature+',' not in raw:raise ValueError('Wrong physical build signature')
 return d['summary']
def packet(raw):
 match=re.search(r'SDW6 summary words=([0-9a-f,]+)',raw)
 if not match:raise ValueError('Actual B006 snapshot absent')
 words=[int(x,16) for x in match[1].split(',')]
 if len(words)!=16 or words[0]!=0x53445706 or ((words[1]>>20)&255)!=0:raise ValueError('B006 signature/revision mismatch')
 return words,jtag_guarded.decode(raw)['summary']
def allowed_pause(raw,point):
 words,s=packet(raw)
 if not (point in range(4) and s['mode']==2 and s['status']==8 and s['state']==14 and not s['terminal'] and s['reason']==0 and s['completed']==0 and s['commands']==2+point):raise ValueError('Not the exact safe B006 between-command pause')
 return s
def compatibility():
 previous=ROOT/'work/packages/recovery05/Cores/alfatreze.CARDWRITE02'
 candidate=ROOT/'work/packages/guarded06/Cores/alfatreze.CARDWRITE02'
 for filename in ('data.json','input.json','interact.json','audio.json','video.json','variants.json'):
  if json.loads((previous/filename).read_text())!=json.loads((candidate/filename).read_text()):raise ValueError('SD metadata ABI changed: '+filename)
 a=json.loads((previous/'core.json').read_text())['core'];b=json.loads((candidate/'core.json').read_text())['core']
 if a['framework']!=b['framework'] or a['cores']!=b['cores']:raise ValueError('Framework/core ABI mismatch')
 for key in ('platform_ids','author','shortname'):
  if a['metadata'][key]!=b['metadata'][key]:raise ValueError('Core identity changed')
 if any(p.is_file() for p in (ROOT/'work/packages/guarded06/Assets').rglob('*')):raise ValueError('Candidate must contain no save fixtures')
 return {'sd_metadata_version':a['metadata']['version'],'jtag_loaded_version':b['metadata']['version'],'unchanged_slot_and_framework_ABI':True,'deliberate_debug_image_difference':True}
def transport_qualification():
 path=ROOT/'work/evidence/console-session-qualification.json';q=json.loads(path.read_text())
 if not q.get('pass'):raise ValueError('New console transport is unqualified')
 for group in ('sources','reports'):
  for relative,h in q[group].items():
   if sha(ROOT/relative)!=h:raise ValueError('Console transport qualification changed')
 return sha(path)
def resumed_gate():
 proof=resume_recovery.verify()
 path=ROOT/'work/evidence/b005-resumed-summary.json'
 if not proof.get('pass') or json.loads(path.read_text())!=proof:raise ValueError('Completed independent resumed proof required')
 return sha(path)
def main():
 p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True);group.add_argument('--previous-result',type=Path);group.add_argument('--core-interruption-point',type=int,choices=range(4));p.add_argument('--from-build',choices=('B005','B006'),default='B005');args=p.parse_args()
 transport_hash=transport_qualification()
 if Path('/Volumes/CARDWRITE').exists():raise ValueError('Host-mounted card; no programming')
 resumed_hash=resumed_gate()
 abi=compatibility();audit=json.loads((ROOT/'work/evidence/custom-build-audit-guarded06.json').read_text())
 sof=ROOT/'work/fpga/guarded06-s1/ap_core.sof';expected=audit['reports']['ap_core.sof']
 if sha(sof)!=expected or audit['minimum_reported_slack_ns']<0:raise ValueError('Qualified SOF mismatch')
 manifest=ROOT/'work/build/guarded06-manifest.json'
 if sha(manifest)!=audit['compile_source_manifest_sha256']:raise ValueError('Frozen manifest mismatch')
 for rel,h in json.loads(manifest.read_text())['files'].items():
  if sha(manifest.parent/'guarded06'/rel)!=h:raise ValueError('Frozen compile source changed')
 package=json.loads((ROOT/'work/packages/guarded06-manifest.json').read_text())
 if package['provenance']!=audit:raise ValueError('Package qualification mismatch')
 for rel,h in package['files'].items():
  if sha(ROOT/'work/packages/guarded06'/rel)!=h:raise ValueError('Qualified package changed')
 codec=jtag_recovery if args.from_build=='B005' else jtag_guarded
 tool='jtag_recovery.py' if args.from_build=='B005' else 'jtag_guarded.py'
 path=args.previous_result.resolve() if args.previous_result else None
 preserved=None
 if path:
  if path.parent!=(ROOT/'work/evidence/jtag').resolve() or path.suffix!='.json':raise ValueError('Preserved private result required')
  preserved=json.loads(path.read_text());raw=path.with_suffix('.txt').read_text()
  if not preserved.get('pass') or codec.decode(raw)!={k:v for k,v in preserved.items() if k not in ('exit_code','script_sha256')}:raise ValueError('Complete preserved raw/decoded PASS required')
 elif args.from_build!='B006':raise ValueError('Pause loading is limited to matching B006')
 status=subprocess.run([sys.executable,str(ROOT/'tools/jtag_session.py'),'--build',args.from_build,'status'],capture_output=True,text=True)
 if status.returncode:raise ValueError('Live status failed: '+status.stdout+status.stderr)
 if path:
  before=live_summary(status.stdout,codec)
  if before!=preserved['summary'] or before['status']!=4 or not before['terminal']:raise ValueError('Live state changed, busy or failed; no programming')
 else:before=allowed_pause(status.stdout,args.core_interruption_point)
 chain=vm_build.remote(BIN+'jtagconfig -n').decode()
 if re.findall(r'^\d+\) .+$',chain,re.M)!=['1) USB-Blaster [5-3]'] or re.findall(r'^  ([0-9A-F]{8})\s+(.+)$',chain,re.M)!=[('02B050DD','5CE(BA4|FA4)')]:raise ValueError('Unexpected/ambiguous JTAG chain')
 if vm_build.remote('sha256sum '+REMOTE).decode().split()[0]!=expected:raise ValueError('VM/local SOF mismatch')
 journal=ROOT/'work/evidence/jtag'/('b006-load-resumed-'+str(time.time_ns())+'.json')
 plan={'state':'planned','completed_B005_resumed_proof_sha256':resumed_hash,'loader_source_sha256':sha(Path(__file__)),'console_transport_qualification_sha256':transport_hash,'loaded_build':'B006','previous_build':args.from_build,'sof_sha256':expected,'before':before,'metadata_compatibility':abi,'preserved_result_sha256':sha(path) if path else None,'core_interruption_point':args.core_interruption_point,'chain':chain,'scope':'Qualified JTAG debug image with unchanged existing-file ABI; SD still contains B005. No power-cycle/remount claim.'}
 journal.write_text(json.dumps(plan,indent=2)+'\n')
 command=BIN+'quartus_pgm -m jtag -c 1 -o '+"'p;"+REMOTE+"@1'"
 run=subprocess.run(vm_build.SSH+[command],capture_output=True,text=True,timeout=60);log=run.stdout+run.stderr;journal.with_suffix('.txt').write_text(log)
 okay=run.returncode==0 and 'Successfully performed operation(s)' in log
 plan.update(state='programmed' if okay else 'failed',returncode=run.returncode,program_log_sha256=sha(journal.with_suffix('.txt')));journal.write_text(json.dumps(plan,indent=2)+'\n')
 if not okay:raise ValueError('Programming outcome unqualified; inspect evidence, never retry blindly')
 print('Qualified B006 loaded over JTAG; require fresh SDW6 READY before any request.');print('Load evidence: '+str(journal))
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,subprocess.SubprocessError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
