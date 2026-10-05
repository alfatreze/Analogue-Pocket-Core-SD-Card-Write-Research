#!/usr/bin/env python3
"""Access B003's retained ISSP results on the existing VM; never programs FPGA."""
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
import batch

ROOT=vm_build.ROOT
CONSOLE='/home/taualpha/intelFPGA_lite/25.1std/quartus/sopc_builder/bin/system-console'


def decode(raw):
    summary=re.search(r'SDW3 summary status=(\d+) cold=(\d+) terminal=(\d+) completed=(\d+) passed=(\d+) failed=(\d+) commands=(\d+)',raw)
    if not summary:return {'pass':False,'reason':'summary absent'}
    values=dict(zip(('status','cold','terminal','completed','passed','failed','commands'),map(int,summary.groups())))
    records=[]
    expected={(c['id'],p) for c in batch.configuration()['cases']
              for p in (range(len(c['write_lengths']),len(c['write_lengths'])+1)
                        if values['cold'] else range(1,len(c['write_lengths'])+1))}
    for match in re.finditer(r'SDW3 record case=(\d+) ordinal=(\d+) words=([0-9a-f,]+)',raw):
        c,p=int(match[1]),int(match[2]);words=[int(w,16) for w in match[3].split(',')]
        good=False
        if len(words)==8 and (c,p) in expected:
            case=batch.configuration()['cases'][c]
            header,flags=words[1],words[5]
            required=6 if values['cold'] else 7
            good=(words[0]==0x53445703 and (header>>29)&1==1 and
                  (header>>30)&1==values['cold'] and header&15==4 and
                  (header>>24)&31==c and (header>>22)&3==p and
                  (header>>14)&255==2 and words[3]==case['region_offset']+case['offset_in_region'] and
                  words[4]==(max(case['write_lengths'])<<16)|case['write_lengths'][p-1] and
                  flags==0x80000000|required)
        records.append(dict(case=c,ordinal=p,words=words,pass_=good))
    seen=[(r['case'],r['ordinal']) for r in records]
    good=(values['status']==4 and values['terminal']==1 and values['completed']==32 and
          values['passed']==32 and values['failed']==0 and values['commands']==(32 if values['cold'] else 76)
          and set(seen)==expected and len(seen)==len(expected) and all(r['pass_'] for r in records))
    return {'pass':good,'scope':'retained immediate results; physical file and cold actions verified separately',
            'summary':values,'records':records}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['status','results','start','cold'])
    args=parser.parse_args()
    if args.mode in ('start','cold') and Path('/Volumes/CARDWRITE').exists():
        raise SystemExit('CARDWRITE is mounted on the host; eject and insert it in Pocket first')
    script=('set mode '+args.mode+'\n').encode()+(ROOT/'tools/jtag_batch.tcl').read_bytes()
    digest=hashlib.sha256(script).hexdigest()
    remote='card-writing-lab/jtag-b003-'+digest+'.tcl'
    vm_build.remote('mkdir -p card-writing-lab && cat > '+shlex.quote(remote),script)
    actual=vm_build.remote('sha256sum '+shlex.quote(remote)).decode().split()[0]
    if actual!=digest:raise SystemExit('VM script hash mismatch')
    # System Console dispatches stdin after initialization. Closing SSH stdin at
    # launch can skip --script entirely, with a misleading zero exit status.
    command='env _JAVA_OPTIONS=-Xint '+shlex.quote(CONSOLE)+' -cli -disable_readline'
    process=subprocess.Popen(vm_build.SSH+[command],stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    invocation=('if {[catch {source /home/taualpha/'+remote+
                '} err]} {puts "SDW3 ERROR: $err"}; puts "SDW3 transport done"\n')
    process.stdin.write(invocation.encode());process.stdin.flush()
    chunks=[];deadline=time.monotonic()+90;finished=False
    selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
    while time.monotonic()<deadline:
        if not selector.select(timeout=1):
            if process.poll() is not None:break
            continue
        chunk=os.read(process.stdout.fileno(),65536)
        if not chunk:break
        chunks.append(chunk)
        if re.search(rb'(?:^|\n)SDW3 transport done\r?(?:\n|$)',b''.join(chunks)):finished=True;break
    selector.close();process.stdin.close()
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.terminate();process.wait(timeout=10)
    raw=b''.join(chunks).decode(errors='replace')
    summary=re.search(r'SDW3 summary status=(\d+)',raw)
    valid=(finished and 'SDW3 done' in raw and 'SDW3 ERROR:' not in raw and summary is not None)
    if args.mode in ('start','cold'):valid=valid and 'SDW3 requested '+args.mode in raw
    exit_code=0 if valid else 1
    folder=ROOT/'work/evidence/jtag';folder.mkdir(parents=True,exist_ok=True)
    # Exclusive evidence file; do not replace prior capture or infer durable success.
    out=folder/('b003-'+args.mode+'-'+str(time.time_ns())+'.txt')
    out.write_text(raw)
    result=decode(raw) if args.mode=='results' else {'mode':args.mode,'raw_evidence_only':True}
    result.update(exit_code=exit_code,script_sha256=digest)
    out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(raw)
    print('Raw JTAG evidence preserved: '+str(out))
    if exit_code:raise SystemExit(exit_code)
    if args.mode=='results' and not result['pass']:raise SystemExit(1)


if __name__=='__main__':main()
