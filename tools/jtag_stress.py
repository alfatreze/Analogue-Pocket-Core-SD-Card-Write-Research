#!/usr/bin/env python3
"""Access B004's retained ISSP results on the existing VM; never programs FPGA."""
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
import stress

ROOT=vm_build.ROOT
CONSOLE='/home/taualpha/intelFPGA_lite/25.1std/quartus/sopc_builder/bin/system-console'


def decode(raw):
    summary=re.search(r'SDW4 summary status=(\d+) cold=(\d+) terminal=(\d+) completed=(\d+) passed=(\d+) failed=(\d+) commands=(\d+) first_failure=(\d+)',raw)
    if not summary:return {'pass':False,'reason':'summary absent'}
    values=dict(zip(('status','cold','terminal','completed','passed','failed','commands','first_failure'),map(int,summary.groups())))
    expected=[stress.final_operation(c) for c in range(32)] if values['cold'] else list(range(10000))
    records=[];cases=stress.configuration()['cases']
    for match in re.finditer(r'SDW4 record operation=(\d+) words=([0-9a-f,]+)',raw):
        op=int(match[1]);words=[int(w,16) for w in match[2].split(',')];good=False
        if len(words)==16 and op in range(10000):
            c=cases[op%32];h=words[1]
            good=(words[0]==0x53445704 and (h>>18)&255==2 and (h>>14)&15==values['status'] and
                  (h>>30)&1==values['cold'] and (h>>29)&1==1 and h&16383==values['first_failure'] and
                  words[2]==op and words[3:7]==[values['completed'],values['passed'],values['failed'],values['commands']] and
                  words[7]==c['region_offset']+c['offset_in_region'] and words[8]==c['write_lengths'][0] and
                  words[9]==(0x80000006 if values['cold'] else 0x80000007) and
                  (words[10]==0 if values['cold'] else words[10]>0) and words[11]>0)
        records.append(dict(operation=op,words=words,pass_=good))
    seen=[r['operation'] for r in records]
    target=32 if values['cold'] else 10000
    good=(values['status']==4 and values['terminal']==1 and values['completed']==target and
          values['passed']==target and values['failed']==0 and values['commands']==(32 if values['cold'] else 20000) and
          values['first_failure']==16383 and seen==expected and all(r['pass_'] for r in records))
    if good:
        reads=[r['words'][11] for r in records];writes=[r['words'][10] for r in records]
        stats=[0xffffffff,0,min(reads),max(reads)] if values['cold'] else [min(writes),max(writes),min(reads),max(reads)]
        good=all(r['words'][12:16]==stats for r in records)
    return {'pass':good,'scope':'retained operation comparisons; physical final bytes and shutdown actions checked separately',
            'summary':values,'records':records}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['status','results','start','cold'])
    args=parser.parse_args()
    if args.mode in ('start','cold') and Path('/Volumes/CARDWRITE').exists():
        raise SystemExit('CARDWRITE is mounted on the host; eject and insert it in Pocket first')
    script=('set mode '+args.mode+'\n').encode()+(ROOT/'tools/jtag_stress.tcl').read_bytes()
    digest=hashlib.sha256(script).hexdigest()
    remote='card-writing-lab/jtag-b004-'+digest+'.tcl'
    vm_build.remote('mkdir -p card-writing-lab && cat > '+shlex.quote(remote),script)
    actual=vm_build.remote('sha256sum '+shlex.quote(remote)).decode().split()[0]
    if actual!=digest:raise SystemExit('VM script hash mismatch')
    # System Console dispatches stdin after initialization. Closing SSH stdin at
    # launch can skip --script entirely, with a misleading zero exit status.
    command='env _JAVA_OPTIONS=-Xint '+shlex.quote(CONSOLE)+' -cli -disable_readline'
    process=subprocess.Popen(vm_build.SSH+[command],stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    invocation=('if {[catch {source /home/taualpha/'+remote+
                '} err]} {puts "SDW4 ERROR: $err"}; puts "SDW4 transport done"\n')
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
        if re.search(rb'(?:^|\n)SDW4 transport done\r?(?:\n|$)',b''.join(chunks)):finished=True;break
    selector.close();process.stdin.close()
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.terminate();process.wait(timeout=10)
    raw=b''.join(chunks).decode(errors='replace')
    summary=re.search(r'SDW4 summary status=(\d+)',raw)
    valid=(finished and 'SDW4 done' in raw and 'SDW4 ERROR:' not in raw and summary is not None)
    if args.mode in ('start','cold'):valid=valid and 'SDW4 requested '+args.mode in raw
    exit_code=0 if valid else 1
    folder=ROOT/'work/evidence/jtag';folder.mkdir(parents=True,exist_ok=True)
    # Exclusive evidence file; do not replace prior capture or infer durable success.
    out=folder/('b004-'+args.mode+'-'+str(time.time_ns())+'.txt')
    out.write_text(raw)
    result=decode(raw) if args.mode=='results' else {'mode':args.mode,'raw_evidence_only':True}
    result.update(exit_code=exit_code,script_sha256=digest)
    out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(raw if args.mode!='results' else '\n'.join(line for line in raw.splitlines() if 'SDW4 summary' in line or 'SDW4 ERROR' in line or 'SDW4 done' in line))
    print('Raw JTAG evidence preserved: '+str(out))
    if exit_code:raise SystemExit(exit_code)
    if args.mode=='results' and not result['pass']:raise SystemExit(1)


if __name__=='__main__':main()
