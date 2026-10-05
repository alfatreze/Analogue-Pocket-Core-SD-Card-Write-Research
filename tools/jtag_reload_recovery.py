#!/usr/bin/env python3
"""Reload only qualified B005 after preserved PASS or an explicit safe pause."""
import argparse,hashlib,json,re,subprocess,sys,time
from pathlib import Path
import jtag_recovery,vm_build
ROOT=vm_build.ROOT
QUARTUS='/home/taualpha/intelFPGA_lite/25.1std/quartus/bin/'
SOF=ROOT/'work/fpga/recovery05-s1/ap_core.sof'
REMOTE='/home/taualpha/card-writing-lab/recovery05-s1/src/fpga/output_files/ap_core.sof'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def packet(raw):
 match=re.search(r'SDW5 summary words=([0-9a-f,]+)',raw)
 if not match:raise ValueError('Actual B005 snapshot absent')
 words=[int(x,16) for x in match[1].split(',')]
 if len(words)!=16 or words[0]!=0x53445705 or ((words[1]>>20)&255)!=0:raise ValueError('B005 signature/revision mismatch')
 return words,jtag_recovery.decode(raw)['summary']
def allowed_snapshot(raw,result=None,point=None):
 words,s=packet(raw)
 if point is not None:
  if not (point in range(4) and s['mode']==2 and s['status']==8 and s['state']==14 and not s['terminal'] and s['reason']==0 and s['completed']==0 and s['commands']==2+point):raise ValueError('Not the exact safe between-command pause')
 else:
  if result is None or not result.get('pass') or s['status']!=4 or not s['terminal']:raise ValueError('Preserved successful terminal results required')
  if s!=result['summary']:raise ValueError('Live state differs from preserved result history')
 return s

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path);p.add_argument('--core-interruption-point',type=int,choices=range(4));args=p.parse_args()
 if Path('/Volumes/CARDWRITE').exists():raise ValueError('Host-mounted CARDWRITE; no reload')
 if (args.result is None)==(args.core_interruption_point is None):raise ValueError('Provide preserved result or explicit pause point')
 audit=json.loads((ROOT/'work/evidence/custom-build-audit-recovery05.json').read_text());expected=audit['reports']['ap_core.sof']
 if sha(SOF)!=expected:raise ValueError('Qualified local SOF changed')
 result=None
 if args.result:
  evidence=(ROOT/'work/evidence/jtag').resolve();path=args.result.resolve()
  if path.parent!=evidence or path.suffix!='.json':raise ValueError('Result must be preserved private JTAG evidence')
  result=json.loads(path.read_text());raw_path=path.with_suffix('.txt')
  if jtag_recovery.decode(raw_path.read_text())!= {k:v for k,v in result.items() if k not in ('exit_code','script_sha256')}:raise ValueError('Preserved raw/decoded history differs')
 status=subprocess.run([sys.executable,str(ROOT/'tools/jtag_recovery.py'),'status'],capture_output=True,text=True)
 if status.returncode:raise ValueError('Status transport failed: '+status.stdout+status.stderr)
 before=allowed_snapshot(status.stdout,result,args.core_interruption_point)
 chain=vm_build.remote(QUARTUS+'jtagconfig -n').decode()
 cables=re.findall(r'^\d+\) .+$',chain,re.M);devices=re.findall(r'^  ([0-9A-F]{8})\s+(.+)$',chain,re.M)
 if cables!=['1) USB-Blaster [5-3]'] or devices!=[('02B050DD','5CE(BA4|FA4)')]:raise ValueError('Unexpected/ambiguous JTAG chain: '+chain)
 remote_hash=vm_build.remote('sha256sum '+REMOTE).decode().split()[0]
 if remote_hash!=expected:raise ValueError('VM SOF differs from qualified local SOF')
 folder=ROOT/'work/evidence/jtag';journal=folder/('b005-reload-'+str(time.time_ns())+'.json')
 plan={'state':'planned','build':'B005','sof_sha256':expected,'before':before,'chain':chain,'preserved_result_sha256':sha(args.result) if args.result else None,'core_interruption_point':args.core_interruption_point,'scope':'FPGA reconfiguration; no power cycle, SD power cut, host remount or durability claim'}
 journal.write_text(json.dumps(plan,indent=2)+'\n')
 # Exact cable/device position verified above. Never retry an unknown programming outcome.
 command=QUARTUS+'quartus_pgm -m jtag -c 1 -o '+"'p;"+REMOTE+"@1'"
 run=subprocess.run(vm_build.SSH+[command],capture_output=True,text=True,timeout=60)
 log=run.stdout+run.stderr;journal.with_suffix('.txt').write_text(log)
 okay=run.returncode==0 and 'Successfully performed operation(s)' in log
 plan.update(state='programmed' if okay else 'failed',returncode=run.returncode,program_log_sha256=sha(journal.with_suffix('.txt')));journal.write_text(json.dumps(plan,indent=2)+'\n')
 if not okay:raise ValueError('Programming result not qualified; inspect preserved log, do not retry blindly')
 print('Qualified B005 SOF reloaded; require a new READY snapshot before any request.',flush=True)
 print('Reload evidence: '+str(journal),flush=True)
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,subprocess.SubprocessError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
