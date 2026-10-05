#!/usr/bin/env python3
"""Read-only collection of designated-card output and protected-file comparison."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('installer',ROOT/'tools/install.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',choices=['official-control','minimal01','minimal02','batch03r1','batch03r2','stress04','stress04r1','stress04r2'])
    parser.add_argument('--test-id',required=True)
    parser.add_argument('--firmware',required=True)
    parser.add_argument('--generation',type=int,default=1)
    args=parser.parse_args()
    if not args.test_id or not all(c.isalnum() or c in '-_' for c in args.test_id):
        raise SystemExit('Test ID must contain only letters, digits, hyphens, underscores')
    info=installer.identity()
    evidence=ROOT/'work/evidence/runs'/args.test_id
    if evidence.exists():raise SystemExit('Test ID already collected; keep earlier results immutable')
    evidence.mkdir(parents=True)
    relative=('Assets/ex_platform/Example Author.Keyboard Mouse Target Data/saved.bin'
              if args.package=='official-control' else
              'Assets/cardwrite/alfatreze.CARDWRITE02/stress-b004.bin' if args.package.startswith('stress04') else
              'Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin' if args.package.startswith('batch03') else
              'Assets/cardwrite/alfatreze.CARDWRITE'+args.package[-2:]+'/write64.bin')
    output=installer.CARD/relative
    installer.safe(output,installer.CARD)
    baseline_dir='update-stress04r2' if args.package.startswith('stress04') else 'update-batch03' if args.package.startswith('batch03') else 'install-'+args.package
    baseline=json.loads((ROOT/'work/evidence'/baseline_dir/'after.json').read_text())
    after=installer.snapshot()
    # New APF files may be legitimate; list all of them for review, not silently ignore them.
    changed=[p for p in sorted(baseline) if p!=relative and baseline[p]!=after.get(p)]
    added=[p for p in sorted(set(after)-set(baseline)) if p!=relative]
    verification={'pass':False,'reason':'output missing'}
    if output.is_file():
        data=output.read_bytes();(evidence/'output.bin').write_bytes(data)
        command=[sys.executable,str(ROOT/'tools/lab.py')]
        if args.package.startswith('stress04'):
            command=[sys.executable,str(ROOT/'tools/stress.py'),'verify',str(evidence/'output.bin')]
        elif args.package.startswith('batch03'):
            command=[sys.executable,str(ROOT/'tools/batch.py'),'verify',str(evidence/'output.bin')]
        else:
            command+=['verify-control',str(evidence/'output.bin'),'--image','0'] if args.package=='official-control' else ['verify',str(evidence/'output.bin'),'--generation',str(args.generation)]
        check=subprocess.run(command,capture_output=True,text=True)
        verification=json.loads(check.stdout) if check.stdout else {'pass':False,'reason':check.stderr}
    result={'test_id':args.test_id,'firmware':args.firmware,'volume':info,
            'package':args.package,'file_verification':verification,
            'changed_or_missing_protected_files':changed,'new_files_for_review':added,
            'verdict':'file verified; cold reload and actions require user evidence' if verification.get('pass') and not changed else 'failed or inconclusive'}
    (evidence/'result.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
    (evidence/'after.json').write_text(json.dumps(after,indent=2)+'\n')
    print(json.dumps(result,indent=2,default=str))
    return 0 if verification.get('pass') and not changed else 1


if __name__=='__main__':sys.exit(main())
