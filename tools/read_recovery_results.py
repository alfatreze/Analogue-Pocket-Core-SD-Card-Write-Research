#!/usr/bin/env python3
"""Read-only B005 two-file/guard and protected-content evidence collector."""
import argparse,json,subprocess,sys
from pathlib import Path
import install,recovery
ROOT=install.ROOT
ASSETS=tuple('Assets/cardwrite/alfatreze.CARDWRITE02/'+x for x in recovery.configuration()['files'])
def test_id(value):
 if not value or not all(c.isalnum() or c in '-_' for c in value):raise ValueError('Invalid test ID')
 return value

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--test-id',required=True);p.add_argument('--firmware',required=True)
 p.add_argument('--generation',type=int);p.add_argument('--generation-a',type=int);p.add_argument('--generation-b',type=int);p.add_argument('--generated',action='store_true');p.add_argument('--read-only-baseline')
 args=p.parse_args();test_id(args.test_id);info=install.identity()
 folder=ROOT/'work/evidence/runs'/args.test_id
 if folder.exists():raise ValueError('Existing trial evidence; never overwrite')
 baseline_path=ROOT/'work/evidence/cleanup-b005/after.json'
 if not baseline_path.exists():baseline_path=ROOT/'work/evidence/update-recovery05/after.json'
 baseline=json.loads(baseline_path.read_text())
 if args.read_only_baseline:
  test_id(args.read_only_baseline);baseline=json.loads((ROOT/'work/evidence/runs'/args.read_only_baseline/'after.json').read_text())
 after=install.snapshot();data=[];folder.mkdir(parents=True)
 for relative in ASSETS:
  source=install.CARD/relative;install.safe(source,install.CARD);content=source.read_bytes();(folder/source.name).write_bytes(content);data.append(content)
 verification=recovery.verify_files(*data,expected_generation=args.generation,expect_generated=args.generated)
 expected_pair=(args.generation_a,args.generation_b)
 pair_pass=all(g is None or (r['valid'] and r['generation']==g) for g,r in zip(expected_pair,verification['records']))
 verification['expected_file_generations']=list(expected_pair);verification['file_generations_pass']=pair_pass;verification['pass']=verification['pass'] and pair_pass
 protected=[x for x in baseline if baseline[x]!=after.get(x) and (args.read_only_baseline or x not in ASSETS)]
 added=sorted(set(after)-set(baseline))
 result={'test_id':args.test_id,'build':'B005','firmware_reported':args.firmware,'volume':info,'file_verification':verification,'changed_or_missing_protected_files':sorted(protected),'new_files_for_review':added,'read_only_baseline':args.read_only_baseline,'pass':verification['pass'] and not protected,'physical_actions':'Require separate owner/screenshot/JTAG evidence; exact power actions not inferred from a remount.'}
 (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');(folder/'after.json').write_text(json.dumps(after,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['pass'] else 1
if __name__=='__main__':
 try:sys.exit(main())
 except (ValueError,OSError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
