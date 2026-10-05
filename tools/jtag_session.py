#!/usr/bin/env python3
"""New leak-free console client; unchanged B005/B006 Tcl protocol and decoders."""
import argparse,json,sys,time,re
from pathlib import Path
import vm_build,jtag_recovery,jtag_guarded,console_transport
ROOT=vm_build.ROOT
def valid_packet(raw,build):
 tag='SDW5' if build=='B005' else 'SDW6'
 match=re.search(tag+r' summary words=([0-9a-f,]+)',raw)
 if not match:return False
 words=[int(x,16) for x in match[1].split(',')]
 return len(words)==16 and words[0]==(0x53445705 if build=='B005' else 0x53445706) and ((words[1]>>20)&255)==0
def main():
 p=argparse.ArgumentParser();p.add_argument('--build',choices=('B005','B006'),required=True);p.add_argument('mode',choices=('status','results','start','cold','pause','resume'));p.add_argument('--point',type=int,choices=range(4),default=0);a=p.parse_args()
 if a.mode in ('start','cold','pause','resume') and Path('/Volumes/CARDWRITE').exists():raise ValueError('Host-mounted card; no request')
 prefix=a.build.lower();tag='SDW5' if a.build=='B005' else 'SDW6';codec=jtag_recovery if a.build=='B005' else jtag_guarded;filename='jtag_recovery.tcl' if a.build=='B005' else 'jtag_guarded.tcl'
 script=('set mode '+a.mode+'\nset point '+str(a.point)+'\n').encode()+(ROOT/'tools'/filename).read_bytes()
 r=console_transport.run(script,tag,900 if a.mode=='results' else 90);raw=r.pop('raw')
 valid=r['transport_done'] and (r['controlled_exit'] or (r['natural_exit'] and r['returncode']==0)) and tag+' done' in raw and tag+' ERROR:' not in raw and valid_packet(raw,a.build)
 if a.mode in ('start','cold','pause','resume'):valid=valid and tag+' requested '+a.mode in raw
 path=ROOT/'work/evidence/jtag'/(prefix+'-session-'+a.mode+'-'+str(time.time_ns())+'.txt');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(raw)
 result=codec.decode(raw) if a.mode=='results' else {'mode':a.mode,'raw_evidence_only':True};result.update(exit_code=0 if valid else 1,script_sha256=r['script_sha256'])
 path.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');path.with_suffix('.transport.json').write_text(json.dumps(r,indent=2)+'\n')
 print(raw if a.mode!='results' else '\n'.join(x for x in raw.splitlines() if tag+' summary' in x or tag+' ERROR' in x or tag+' done' in x));print('Raw JTAG evidence preserved: '+str(path))
 if not valid or (a.mode=='results' and not result['pass']):raise SystemExit(1)
if __name__=='__main__':
 try:main()
 except (ValueError,OSError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
