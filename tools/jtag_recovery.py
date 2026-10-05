#!/usr/bin/env python3
"""Access B005's retained ISSP results on the existing VM; never programs FPGA."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import re
import subprocess
import selectors
import os
import time
import vm_build
import recovery

ROOT=vm_build.ROOT
CONSOLE='/home/taualpha/intelFPGA_lite/25.1std/quartus/sopc_builder/bin/system-console'


def decode(raw):
    m=re.search(r'SDW5 summary words=([0-9a-f,]+)',raw)
    if not m:return {'pass':False,'reason':'summary absent'}
    w=[int(x,16) for x in m[1].split(',')]
    if len(w)!=16:return {'pass':False,'reason':'packet length'}
    h=w[1];mode=(h>>28)&3;status=(h>>16)&15;mask=w[5]
    a=w[6]|(w[7]<<32);b=w[8]|(w[9]<<32)
    selected=max(a if mask&1 else 0,b if mask&2 else 0)
    summary=dict(status=status,mode=mode,terminal=(h>>30)&1,state=(h>>8)&255,reason=h&255,
                 completed=w[3],commands=w[4],valid_mask=mask,generation_a=a,generation_b=b,selected_generation=selected)
    records=[]
    for m in re.finditer(r'SDW5 record operation=(\d+) words=([0-9a-f,]+)',raw):
        op=int(m[1]);words=[int(x,16) for x in m[2].split(',')];good=False;g=0
        if len(words)==16:
            g=words[10]|(words[11]<<32)
            expected_crc=recovery.checksum(recovery.record(g)) if 0<g<=recovery.MAX_GENERATION else -1
            good=(words[0]==0x53445705 and (words[1]&0x7fffffff)==(h&0x7fffffff) and
                  words[2]==op and words[3:10]==w[3:10] and
                  words[12] in (0x80000007,0x8000000f) and words[13]==expected_crc and words[15]>0)
        records.append(dict(operation=op,generation=g,words=words,pass_=good))
    good=(w[0]==0x53445705 and ((h>>20)&255)==0 and summary['terminal']==1 and status==4 and summary['reason']==0 and mask in (1,2,3))
    if mode==1:
        good=good and w[3]==0 and w[4]==2 and (w[10]|(w[11]<<32))==selected and w[12]==0x80000006 and w[13]==w[14] and not records
    elif mode in (0,2):
        n=64 if mode==0 else 1
        good=good and w[3]==n and w[4]==2+5*n and [r['operation'] for r in records]==list(range(n)) and all(r['pass_'] for r in records)
        if good:
            good=(w[2]==0 and w[10:]==records[0]['words'][10:] and [r['generation'] for r in records]==list(range(selected-n+1,selected+1)) and
                  all((records[i]['words'][12]^records[i-1]['words'][12])==8 for i in range(1,n)))
            last_b=bool(records[-1]['words'][12]&8)
            good=good and (b if last_b else a)==selected
    else:good=False
    return {'pass':bool(good),'summary':summary,'records':records,'scope':'retained comparisons/recovery; physical final files and power actions checked separately'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['status','results','start','cold','pause','resume'])
    parser.add_argument('--point',type=int,choices=range(4),default=0)
    args=parser.parse_args()
    if args.mode in ('start','cold','pause','resume') and Path('/Volumes/CARDWRITE').exists():
        raise SystemExit('CARDWRITE is mounted on the host; eject and insert it in Pocket first')
    script=('set mode '+args.mode+'\nset point '+str(args.point)+'\n').encode()+(ROOT/'tools/jtag_recovery.tcl').read_bytes()
    digest=hashlib.sha256(script).hexdigest()
    remote='card-writing-lab/jtag-b005-'+digest+'.tcl'
    vm_build.remote('mkdir -p card-writing-lab && cat > '+shlex.quote(remote),script)
    actual=vm_build.remote('sha256sum '+shlex.quote(remote)).decode().split()[0]
    if actual!=digest:raise SystemExit('VM script hash mismatch')
    # System Console dispatches stdin after initialization. Closing SSH stdin at
    # launch can skip --script entirely, with a misleading zero exit status.
    command='env _JAVA_OPTIONS=-Xint '+shlex.quote(CONSOLE)+' -cli -disable_readline'
    process=subprocess.Popen(vm_build.SSH+[command],stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    invocation=('if {[catch {source /home/taualpha/'+remote+
                '} err]} {puts "SDW5 ERROR: $err"}; puts "SDW5 transport done"\n')
    process.stdin.write(invocation.encode());process.stdin.flush()
    chunks=[];deadline=time.monotonic()+(900 if args.mode=='results' else 90);finished=False
    selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
    while time.monotonic()<deadline:
        if not selector.select(timeout=1):
            if process.poll() is not None:break
            continue
        chunk=os.read(process.stdout.fileno(),65536)
        if not chunk:break
        chunks.append(chunk)
        if re.search(rb'(?:^|\n)SDW5 transport done\r?(?:\n|$)',b''.join(chunks)):finished=True;break
    selector.close();process.stdin.close()
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.terminate();process.wait(timeout=10)
    raw=b''.join(chunks).decode(errors='replace')
    summary=re.search(r'SDW5 summary words=([0-9a-f,]+)',raw)
    valid=(finished and 'SDW5 done' in raw and 'SDW5 ERROR:' not in raw and summary is not None)
    if args.mode in ('start','cold','pause','resume'):valid=valid and 'SDW5 requested '+args.mode in raw
    exit_code=0 if valid else 1
    folder=ROOT/'work/evidence/jtag';folder.mkdir(parents=True,exist_ok=True)
    # Exclusive evidence file; do not replace prior capture or infer durable success.
    out=folder/('b005-'+args.mode+'-'+str(time.time_ns())+'.txt')
    out.write_text(raw)
    result=decode(raw) if args.mode=='results' else {'mode':args.mode,'raw_evidence_only':True}
    result.update(exit_code=exit_code,script_sha256=digest)
    out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(raw if args.mode!='results' else '\n'.join(line for line in raw.splitlines() if 'SDW5 summary' in line or 'SDW5 ERROR' in line or 'SDW5 done' in line))
    print('Raw JTAG evidence preserved: '+str(out))
    if exit_code:raise SystemExit(exit_code)
    if args.mode=='results' and not result['pass']:raise SystemExit(1)


if __name__=='__main__':main()
