#!/usr/bin/env python3
"""Bounded B005 connected campaign; preserve evidence and stop on any failure."""
import argparse,hashlib,json,struct,subprocess,sys,time
from pathlib import Path
import recovery,jtag_reload_recovery
ROOT=recovery.ROOT

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def model_files(a=63,b=64):
 files=[bytearray(recovery.fixture()),bytearray(recovery.fixture())]
 for data,g in zip(files,(a,b)):data[512:1024]=recovery.record(g)
 return files

def check_summary(result,files):
 if not result.get('pass'):raise ValueError('Hardware decoder did not pass')
 expected=recovery.recover(*(bytes(x[512:1024]) for x in files));s=result['summary']
 rawgens=[struct.unpack('>Q',bytes(x[524:532]))[0] for x in files]
 mask=sum(int(v)<<i for i,v in enumerate(expected['valid']))
 if (s['selected_generation']!=expected['generation'] or s['valid_mask']!=mask or [s['generation_a'],s['generation_b']]!=rawgens):raise ValueError('Generation/validity differs from independent expected file model')
 if s['mode']==1:
  chosen=expected['selected'];words=jtag_reload_recovery.packet('SDW5 summary words='+','.join(f'{w:08x}' for w in result['_summary_words']))[0]
  if words[13]!=recovery.checksum(bytes(files[chosen][512:1024])):raise ValueError('Recovered CRC differs from independent expected record')
 return expected

def apply_commits(result,files):
 for r in result['records']:
  dest,g=recovery.next_destination(*(bytes(x[512:1024]) for x in files))
  if r['generation']!=g or bool(r['words'][12]&8)!=bool(dest):raise ValueError('Unexpected commit generation/destination')
  files[dest][512:1024]=recovery.record(g)
 return check_summary(result,files)

def apply_prefix(files,point):
 dest,g=recovery.next_destination(*(bytes(x[512:1024]) for x in files));count=128*point
 files[dest][512:512+count]=recovery.record(g)[:count]
 return dest,g

class Campaign:
 def __init__(self,args):
  self.args=args;self.folder=ROOT/'work/evidence/jtag'/('b005-connected-'+str(time.time_ns()));self.folder.mkdir()
  self.files=model_files();self.last=args.initial_result;self.events=[]
  self.public=ROOT/'work/evidence/b005-connected-campaign.json'
  if self.public.exists():raise ValueError('Existing campaign evidence; do not overwrite or silently rerun')
  self.save('planned')
 def save(self,state,error=None):
  for label,data in zip(('a','b'),self.files):(self.folder/('expected-'+label+'.bin')).write_bytes(data)
  expected=recovery.verify_files(*(bytes(x) for x in self.files))
  doc={'build':'B005','state':state,'planned_additional_clean_batches':self.args.batches,'planned_pause_rounds':self.args.rounds,'events':self.events,'expected_final_files':expected,'error':error,'scope':'Immediate FPGA/readback and matching-SOF core reload evidence. Prefix interruptions reset only FPGA at verified between-command pauses; not power loss or host-remount/file-guard verification.'}
  self.public.write_text(json.dumps(doc,indent=2)+'\n')
 def command(self,tool,*args):
  run=subprocess.run([sys.executable,str(ROOT/'tools'/tool),*map(str,args)],capture_output=True,text=True)
  capture=self.folder/(f'action-{len(list(self.folder.glob("action-*.txt"))):03d}.txt');capture.write_text(run.stdout+run.stderr)
  if run.returncode:raise ValueError('Action failed; no retries. '+str(capture)+'\n'+run.stdout+run.stderr)
  return run.stdout
 def action(self,mode,point=None):
  args=[mode]+(['--point',str(point)] if point is not None else [])
  output=self.command('jtag_recovery.py',*args)
  match=__import__('re').search(r'Raw JTAG evidence preserved: (.+)',output)
  if not match:raise ValueError('Preserved raw evidence path absent')
  raw=Path(match[1]);data=json.loads(raw.with_suffix('.json').read_text())
  if mode=='results':data['_summary_words']=jtag_reload_recovery.packet(raw.read_text())[0]
  return raw,data
 def reload(self,point=None):
  args=['--result',self.last] if point is None else ['--core-interruption-point',str(point)]
  output=self.command('jtag_reload_recovery.py',*args)
  match=__import__('re').search(r'Reload evidence: (.+)',output)
  if not match:raise ValueError('Reload evidence absent')
  path=Path(match[1]);data=json.loads(path.read_text())
  if data['state']!='programmed':raise ValueError('Reload not qualified')
  return {'evidence':path.name,'sha256':sha(path),'before':data['before'],'sof_sha256':data['sof_sha256']}
 def finish(self,label,kind,reload_info=None):
  raw,data=self.action('results')
  if kind=='save':apply_commits(data,self.files)
  else:check_summary(data,self.files)
  self.last=raw.with_suffix('.json')
  event={'trial':label,'kind':kind,'pass':True,'result':data,'raw_sha256':sha(raw),'decoded_sha256':sha(self.last),'raw_evidence':raw.name,'reload':reload_info}
  self.events.append(event);self.save('running');print(label+' PASS selected generation '+str(data['summary']['selected_generation']),flush=True)
 def session(self,label,mode):
  reload_info=self.reload();self.action(mode);self.finish(label,'save' if mode=='start' else 'read-only',reload_info)
 def run(self):
  # Initial clean and read-only sessions already physically captured by the parent.
  initial=json.loads(self.last.read_text());initial['_summary_words']=jtag_reload_recovery.packet(self.last.with_suffix('.txt').read_text())[0]
  check_summary(initial,self.files)
  self.events.append({'trial':'initial-reload-read','kind':'read-only','pass':True,'result':initial,'raw_sha256':sha(self.last.with_suffix('.txt')),'decoded_sha256':sha(self.last),'raw_evidence':self.last.with_suffix('.txt').name})
  self.save('running')
  for repeat in range(1,self.args.batches+1):
   self.session('clean-repeat-'+str(repeat),'start');self.session('read-repeat-'+str(repeat),'cold')
  for repeat in range(self.args.rounds):
   for point in range(4):
    label=f'pause-r{repeat+1}-p{point}'
    control_reload=self.reload();self.action('pause',point);self.action('resume');self.finish(label+'-resume','save',control_reload)
    setup=self.reload();self.action('pause',point)
    raw,_=self.action('status');words,before=jtag_reload_recovery.packet(raw.read_text())
    jtag_reload_recovery.allowed_snapshot(raw.read_text(),point=point)
    expected=recovery.recover(*(bytes(x[512:1024]) for x in self.files))
    if before['selected_generation']!=expected['generation']:raise ValueError('Paused prior generation differs')
    # Record the live pause before reconfiguration; predicted bytes are explicitly a model.
    self.events.append({'trial':label+'-core-cut-paused','kind':'safe-pause','pass':True,'point':point,'summary':before,'words':words,'raw_sha256':sha(raw),'raw_evidence':raw.name,'setup_reload':setup});self.save('running')
    interruption=self.reload(point);apply_prefix(self.files,point)
    self.action('cold');self.finish(label+'-core-cut-recover','read-only',interruption)
  if self.args.rounds:
   repair=self.reload();self.action('pause',0);self.action('resume');self.finish('final-restore-inactive-record','save',repair)
   self.session('final-read-both-valid','cold')
  self.save('completed');print('CAMPAIGN COMPLETE; host remount verification pending.',flush=True)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--initial-result',required=True,type=Path);p.add_argument('--batches',type=int,default=9);p.add_argument('--rounds',type=int,default=2);args=p.parse_args()
 if not 0<=args.batches<=20 or not 0<=args.rounds<=5:raise ValueError('Bounded campaign limit exceeded')
 if Path('/Volumes/CARDWRITE').exists():raise ValueError('Card is mounted on host')
 args.initial_result=args.initial_result.resolve()
 if args.initial_result.parent!=(ROOT/'work/evidence/jtag').resolve():raise ValueError('Initial result outside preserved JTAG evidence')
 campaign=Campaign(args)
 try:campaign.run()
 except Exception as e:campaign.save('failed',str(e));raise
if __name__=='__main__':main()
