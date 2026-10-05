#!/usr/bin/env python3
"""Bounded System Console transport with explicit remote exit and owned-PID cleanup."""
import hashlib,json,os,re,selectors,shlex,subprocess,time
from pathlib import Path
import vm_build
CONSOLE='/home/taualpha/intelFPGA_lite/25.1std/quartus/sopc_builder/bin/system-console'
def digest(data):return hashlib.sha256(data).hexdigest()
def invocation(remote,tag):
 if not re.fullmatch(r'SDW[A-Z0-9]+',tag):raise ValueError('Invalid transport tag')
 return ('set transport_rc 0; if {[catch {source /home/taualpha/'+remote+'} err]} {puts "'+tag+' ERROR: $err"; set transport_rc 1}; puts "'+tag+' transport done"\n')
def cleanup_owned(pid,ticks):
 code='''import os,signal,json
from pathlib import Path
p=Path('/proc')/str(PID)
try:
 stat=(p/'stat').read_text().rsplit(')',1)[1].split();args=(p/'cmdline').read_bytes().replace(b'\\0',b' ').decode()
 if int(stat[19])!=TICKS or CONSOLE not in args or '-cli -disable_readline' not in args:raise ValueError('Owned process identity changed; no signal')
 os.kill(PID,signal.SIGTERM);print('owned-console-terminated')
except FileNotFoundError:print('owned-console-already-exited')
'''.replace('PID',str(pid)).replace('TICKS',str(ticks)).replace('CONSOLE',repr(CONSOLE))
 run=subprocess.run(vm_build.SSH+['python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=10)
 return {'returncode':run.returncode,'output':run.stdout+run.stderr}
def run(script,tag,deadline_seconds):
 h=digest(script);remote='card-writing-lab/console-session-'+h+'.tcl'
 vm_build.remote('mkdir -p card-writing-lab && cat > '+shlex.quote(remote),script)
 if vm_build.remote('sha256sum '+shlex.quote(remote)).decode().split()[0]!=h:raise ValueError('VM script hash mismatch')
 bootstrap="import os;from pathlib import Path;stat=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split();print('SDW process pid='+str(os.getpid())+' ticks='+stat[19],flush=True);os.environ['_JAVA_OPTIONS']='-Xint';os.execv("+repr(CONSOLE)+",["+repr(CONSOLE)+",'-cli','-disable_readline'])"
 process=subprocess.Popen(vm_build.SSH+['python3 -c '+shlex.quote(bootstrap)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 process.stdin.write(invocation(remote,tag).encode());process.stdin.flush()
 selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ);chunks=[];deadline=time.monotonic()+deadline_seconds;finished=False;natural=False;cleanup=None
 try:
  while time.monotonic()<deadline:
   if not selector.select(timeout=1):
    if process.poll() is not None:break
    continue
   data=os.read(process.stdout.fileno(),65536)
   if not data:break
   chunks.append(data)
   if re.search(rb'(?:^|\n)'+tag.encode()+rb' transport done\r?(?:\n|$)',b''.join(chunks)):finished=True;break
  raw=b''.join(chunks).decode(errors='replace');owner=re.search(r'SDW process pid=(\d+) ticks=(\d+)',raw)
  if finished and owner:
   try:cleanup=cleanup_owned(int(owner[1]),int(owner[2]))
   except subprocess.SubprocessError as e:cleanup={'returncode':1,'output':str(e)}
  process.stdin.close();process.stdin=None
  try:
   tail,_=process.communicate(timeout=15);chunks.append(tail);natural=True
  except subprocess.TimeoutExpired:
   raw=b''.join(chunks).decode(errors='replace');owner=re.search(r'SDW process pid=(\d+) ticks=(\d+)',raw)
   if owner and cleanup is None:
    try:cleanup=cleanup_owned(int(owner[1]),int(owner[2]))
    except subprocess.SubprocessError as e:cleanup={'returncode':1,'output':str(e)}
   process.terminate()
   try:tail,_=process.communicate(timeout=5)
   except subprocess.TimeoutExpired:process.kill();tail,_=process.communicate(timeout=5)
   chunks.append(tail)
 finally:selector.close()
 raw=b''.join(chunks).decode(errors='replace');owner=re.search(r'SDW process pid=(\d+) ticks=(\d+)',raw)
 return {'raw':raw,'script_sha256':h,'transport_done':finished,'natural_exit':natural and cleanup is None,'controlled_exit':natural and finished and cleanup is not None and cleanup['returncode']==0,'returncode':process.returncode,'owned_remote_pid':int(owner[1]) if owner else None,'owned_remote_start_ticks':int(owner[2]) if owner else None,'cleanup':cleanup}
