#!/usr/bin/env python3
"""B004 independent changing-generation oracle and physical file verifier."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'experiments/b004.json'
def configuration():
    c=json.loads(CONFIG.read_text())
    assert c['pairs']==10000 and c['slot_id']==36 and c['file_size']==262144
    assert len(c['cases'])==32
    for i,x in enumerate(c['cases']):
        assert x['id']==i and x['region_offset']==i*8192
        assert len(x['write_lengths'])==1 and 1<=x['write_lengths'][0]<=4096
        assert 0<=x['offset_in_region'] and x['offset_in_region']+x['write_lengths'][0]<8192
        assert 0<=x['pattern']<=4
    return c
def final_operation(case,pairs=10000):
    assert 32<=pairs<=10000 and 0<=case<32
    return case+((pairs-1-case)//32)*32
def payload(operation,length):
    c=configuration()['cases'][operation%32];mode=c['pattern'];visit=operation//32
    result=bytearray()
    for i in range(length):
        if mode==0:base=0
        elif mode==1:base=255
        elif mode==2:base=170 if i%2==0 else 85
        elif mode==3:base=(i+c['id']+1)%256
        else:base=(i^(i//256)^(c['id']*17)^73^61)%256
        result.append(base^(visit%256)^((visit//256) if i%2 else 0))
    return bytes(result)
def expected_file(pairs=10000):
    c=configuration();data=bytearray([c['guard_byte']])*c['file_size']
    for case in c['cases']:
        length=case['write_lengths'][0];offset=case['region_offset']+case['offset_in_region']
        data[offset:offset+length]=payload(final_operation(case['id'],pairs),length)
    return bytes(data)
def verify(data,pairs=10000):
    expected=expected_file(pairs)
    failures=[i for i in range(32) if data[i*8192:(i+1)*8192]!=expected[i*8192:(i+1)*8192]]
    first=next((i for i,(a,b) in enumerate(zip(data,expected)) if a!=b),None)
    if first is None and len(data)!=len(expected):first=min(len(data),len(expected))
    return {'pass':data==expected,'pairs':pairs,'expected_size':len(expected),'actual_size':len(data),
            'failed_regions':failures,'first_mismatch':first,
            'expected_sha256':hashlib.sha256(expected).hexdigest(),'actual_sha256':hashlib.sha256(data).hexdigest()}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['verify','fixture']);p.add_argument('file',nargs='?',type=Path);p.add_argument('--pairs',type=int,default=10000);a=p.parse_args()
    if a.command=='fixture':
        dest=ROOT/'work/fixtures/stress-b004-initial.bin';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(bytes([165])*262144);print(dest)
    else:
        r=verify(a.file.read_bytes(),a.pairs);print(json.dumps(r,indent=2));raise SystemExit(0 if r['pass'] else 1)
