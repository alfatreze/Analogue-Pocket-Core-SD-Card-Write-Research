#!/usr/bin/env python3
"""Archive and remove exactly the two superseded research cores after B005."""
import argparse,json,os,shutil
from pathlib import Path
import install
ROOT=install.ROOT;CARD=install.CARD
EVIDENCE=ROOT/'work/evidence/cleanup-b005'
OLD=('Example Author.Keyboard Mouse Target Data','alfatreze.CARDWRITE01')

def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
def plan():
 install.identity()
 baseline=json.loads((ROOT/'work/evidence/update-recovery05/after.json').read_text())
 before=install.snapshot()
 if before!=baseline:raise ValueError('Card changed since verified B005 installation')
 manifest=json.loads((ROOT/'work/packages/recovery05-manifest.json').read_text())
 for relative,checksum in manifest['files'].items():
  if before.get(relative,{}).get('sha256')!=checksum:raise ValueError('B005 package mismatch')
 paths=sorted(p for p in before if any(p.startswith('Cores/'+core+'/') for core in OLD))
 if not paths:raise ValueError('No superseded research cores found')
 return {'volume_uuid':install.UUID,'remove_after_backup':{p:before[p] for p in paths},'keep_core':'alfatreze.CARDWRITE02','preserve':'All assets, screenshots, prior outputs, platforms and other files'}
def apply(current):
 if (EVIDENCE/'journal.json').exists():raise ValueError('Existing cleanup journal')
 if current!=plan():raise ValueError('Cleanup plan changed')
 before=install.snapshot();write(EVIDENCE/'before.json',before);write(EVIDENCE/'journal.json',{'state':'started','plan':current})
 for relative,info in current['remove_after_backup'].items():
  src=CARD/relative;dst=EVIDENCE/'backup'/relative;install.safe(src,CARD);dst.parent.mkdir(parents=True,exist_ok=True)
  with src.open('rb') as inp,dst.open('xb') as out:shutil.copyfileobj(inp,out);out.flush();os.fsync(out.fileno())
  if install.sha(dst)!=info['sha256']:raise ValueError('Backup mismatch')
 write(EVIDENCE/'backup-manifest.json',current['remove_after_backup']);os.sync()
 if current!=plan():raise ValueError('Cleanup plan changed after backups')
 for relative,info in current['remove_after_backup'].items():
  if install.sha(CARD/relative)!=info['sha256']:raise ValueError('Old core changed')
  (CARD/relative).unlink()
 for core in OLD:
  directory=CARD/'Cores'/core
  if directory.exists():directory.rmdir()
 os.sync();after=install.snapshot();allowed=set(current['remove_after_backup'])
 changed=[p for p in set(before)|set(after) if before.get(p)!=after.get(p) and p not in allowed]
 if any(p in after for p in allowed):changed.append('Removed core still present')
 write(EVIDENCE/'after.json',after);write(EVIDENCE/'journal.json',{'state':'failed' if changed else 'completed','unexpected_changes':sorted(changed),'plan':current})
 if changed:raise ValueError('Unexpected cleanup changes')
 print('Superseded control and CARDWRITE01 backed up and removed; B005 and all test assets preserved.')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');args=p.parse_args()
 current=plan();write(EVIDENCE/'plan.json',current)
 if args.apply:apply(current)
 else:print(json.dumps(current,indent=2))
if __name__=='__main__':main()
