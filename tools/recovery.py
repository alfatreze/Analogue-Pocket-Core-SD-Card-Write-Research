#!/usr/bin/env python3
"""Independent B005 record/oracle; CRC detects accidental damage, not forgery."""
import argparse, hashlib, json, struct, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'experiments/b005.json'
MAGIC=0x53445235
MAX_GENERATION=(1<<64)-1

def configuration():
    c=json.loads(CONFIG.read_text())
    assert c['slot_ids']==[37,38] and c['file_size']==8192 and c['record_offset']==512
    assert c['record_size']==512 and c['header_size']==32 and c['chunk_size']==128
    assert c['clean_commits']==64 and c['guard_byte']==165 and c['format_version']==1
    return c

def payload(generation):
    return bytes((i ^ (i>>8) ^ (generation&255) ^ ((generation>>8)&255) ^ 0x5b)&255 for i in range(480))

def checksum(record):return zlib.crc32(record[:28]+record[32:])&0xffffffff

def record(generation, data=None):
    if not 1<=generation<=MAX_GENERATION:raise ValueError('generation outside nonzero uint64')
    data=payload(generation) if data is None else bytes(data)
    if len(data)!=480:raise ValueError('fixed payload length required')
    header=struct.pack('>7I',MAGIC,0x00010020,512,generation>>32,generation&0xffffffff,480,0)
    result=header+bytes(4)+data
    return result[:28]+struct.pack('>I',checksum(result))+result[32:]

def validate(data):
    if len(data)!=512:return {'valid':False,'reason':'record-size'}
    w=struct.unpack('>8I',data[:32]);generation=(w[3]<<32)|w[4]
    if w[0:3]!=(MAGIC,0x00010020,512) or w[5:7]!=(480,0):return {'valid':False,'reason':'header'}
    if generation==0:return {'valid':False,'reason':'zero-generation'}
    actual=checksum(data)
    if w[7]!=actual:return {'valid':False,'reason':'checksum','stored_crc':w[7],'computed_crc':actual}
    return {'valid':True,'generation':generation,'crc':actual}

def recover(a,b):
    va,vb=validate(a),validate(b);valid=[va['valid'],vb['valid']]
    result={'valid':valid,'records':[va,vb]}
    if not any(valid):return dict(result,selected=None,generation=0,reason='no-valid-save')
    if all(valid) and va['generation']==vb['generation'] and a!=b:
        return dict(result,selected=None,generation=0,reason='conflicting-equal-generation')
    selected=0 if valid[0] and (not valid[1] or va['generation']>=vb['generation']) else 1
    return dict(result,selected=selected,generation=(va,vb)[selected]['generation'],reason='valid-save')

def next_destination(a,b):
    r=recover(a,b)
    if r['reason']=='conflicting-equal-generation':raise ValueError(r['reason'])
    if r['generation']==MAX_GENERATION:raise ValueError('generation-exhausted')
    return (0 if r['selected'] is None else 1-r['selected']),r['generation']+1

def fixture():return bytes([configuration()['guard_byte']])*8192

def verify_files(a,b,expected_generation=None,expect_generated=False):
    c=configuration();offset=c['record_offset'];end=offset+512
    sizes=len(a)==8192 and len(b)==8192
    guards=sizes and all(x[:offset]==bytes([165])*offset and x[end:]==bytes([165])*(8192-end) for x in (a,b))
    result=recover(a[offset:end],b[offset:end])
    result.update(file_sizes=[len(a),len(b)],guards_pass=guards,sha256=[hashlib.sha256(x).hexdigest() for x in (a,b)])
    generated=all(not v['valid'] or x[offset:end]==record(v['generation']) for x,v in zip((a,b),result['records']))
    result['generated_payloads_pass']=generated
    expected_ok=expected_generation is None or result['generation']==expected_generation
    result['pass']=sizes and guards and result['reason']=='valid-save' and expected_ok and (not expect_generated or generated)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('a',type=Path);p.add_argument('b',type=Path);p.add_argument('--generation',type=int);args=p.parse_args()
    r=verify_files(args.a.read_bytes(),args.b.read_bytes(),args.generation);print(json.dumps(r,indent=2));raise SystemExit(0 if r['pass'] else 1)
