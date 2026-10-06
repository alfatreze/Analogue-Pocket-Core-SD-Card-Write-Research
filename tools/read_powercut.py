#!/usr/bin/env python3
"""Read-only B007 scratch classification and protected-card remount check."""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import b007_oracle
import install

ROOT=install.ROOT
CARD=install.CARD
SCRATCH='Assets/cardwrite/alfatreze.CARDWRITE02/powercut-b007.bin'
BASELINE=ROOT/'work/evidence/update-powercut07r5/after.json'
UPDATE=ROOT/'work/evidence/update-powercut07r5/journal.json'


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,default=str)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True,help='unique evidence folder name using letters, digits, dash or underscore')
    parser.add_argument('--expected-screenshot',help='user-captured Memories/Screenshots/*.png added since the install baseline')
    args=parser.parse_args()
    if not args.run_id or not all(ch.isalnum() or ch in '-_' for ch in args.run_id):
        raise SystemExit('Invalid run ID')
    info=install.identity()
    journal=json.loads(UPDATE.read_text())
    baseline=json.loads(BASELINE.read_text())
    if journal.get('state')!='completed' or journal.get('plan',{}).get('volume_uuid')!=install.UUID:
        raise SystemExit('Completed B007R5 update evidence for CARDWRITE is required')
    folder=ROOT/'work/evidence/runs'/args.run_id
    if folder.exists():raise SystemExit('Evidence run folder already exists; do not overwrite it')
    install.safe(CARD/SCRATCH,CARD)
    if not (CARD/SCRATCH).is_file():raise SystemExit('B007 scratch file is missing')
    before=install.snapshot()
    expected_screenshot=args.expected_screenshot
    if expected_screenshot:
        screenshot_path=Path(expected_screenshot)
        if (screenshot_path.is_absolute() or '..' in screenshot_path.parts or
            not expected_screenshot.startswith('Memories/Screenshots/') or
            screenshot_path.suffix.lower()!='.png'):
            raise SystemExit('Expected screenshot must be a relative Memories/Screenshots/*.png path')
        if expected_screenshot in baseline or expected_screenshot not in before:
            raise SystemExit('Expected screenshot is not a new file on CARDWRITE')
    raw=(CARD/SCRATCH).read_bytes()
    classification=b007_oracle.classify(raw,[0,1])
    cache_paths={'System/'+name for name in install.CACHES}
    names=sorted(set(baseline)|set(before))
    changed=[];allowed_cache=[];allowed_screenshots=[]
    for relative in names:
        if relative==SCRATCH:continue
        if baseline.get(relative)==before.get(relative):continue
        if relative==expected_screenshot:
            allowed_screenshots.append({'path':relative,**before[relative]})
            continue
        if relative in cache_paths:
            allowed_cache.append({'path':relative,'before':baseline.get(relative),'after':before.get(relative)})
        else:
            changed.append({'path':relative,'before':baseline.get(relative),'after':before.get(relative)})
    # Preserve forensic bytes before the second stable snapshot check.
    folder.mkdir(parents=True)
    write_json(folder/'volume.json',info)
    write_json(folder/'before.json',before)
    with (folder/'powercut-b007.bin').open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    if install.sha(folder/'powercut-b007.bin')!=install.sha(CARD/SCRATCH):
        raise ValueError('Scratch backup hash mismatch')
    after=install.snapshot()
    stable=after==before
    result={'test_id':args.run_id,'build':'B007R5','volume_uuid':install.UUID,
        'scratch_path':SCRATCH,'scratch_size':len(raw),'scratch_sha256':install.sha(CARD/SCRATCH),
        'image_classification':classification,'unrelated_changed_files':changed,
        'reviewed_pocket_cache_changes':allowed_cache,'reviewed_expected_screenshots':allowed_screenshots,
        'stable_during_collection':stable,
        'collection_pass':not changed and stable,
        'scope':'Read-only full-file host classification and protected-content comparison against the verified B007R5 install snapshot. This does not identify the instant or rail at which power was lost.'}
    write_json(folder/'after.json',after)
    write_json(folder/'result.json',result)
    if result['collection_pass']:
        print(json.dumps(result,indent=2))
    else:
        print(json.dumps(result,indent=2),file=sys.stderr)
        raise SystemExit(1)


if __name__=='__main__':main()
