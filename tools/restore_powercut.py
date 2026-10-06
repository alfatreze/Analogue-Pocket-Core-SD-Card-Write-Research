#!/usr/bin/env python3
"""Restore only the B007 scratch file from a classified torn-write capture."""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import b007_oracle
import install

ROOT = install.ROOT
CARD = install.CARD
SCRATCH = 'Assets/cardwrite/alfatreze.CARDWRITE02/powercut-b007.bin'
UPDATE = ROOT/'work/evidence/update-powercut07r5'
KNOWN_GOOD = ROOT/'work/evidence/runs/B007R5-POWER1-001/result.json'
EVIDENCE = ROOT/'work/evidence/restores'


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str)+'\n')


def checked_run(run_id):
    if not run_id or not all(ch.isalnum() or ch in '-_' for ch in run_id):
        raise ValueError('Invalid source run ID')
    folder = ROOT/'work/evidence/runs'/run_id
    result = json.loads((folder/'result.json').read_text())
    snapshot = json.loads((folder/'after.json').read_text())
    backup = folder/'powercut-b007.bin'
    if (result.get('test_id') != run_id or result.get('build') != 'B007R5' or
        result.get('volume_uuid') != install.UUID or not result.get('collection_pass') or
        result.get('image_classification', {}).get('classification') != 'mixed-old-new'):
        raise ValueError('Source run is not a passing mixed-image B007R5 collection')
    if not backup.is_file() or install.sha(backup) != result.get('scratch_sha256'):
        raise ValueError('Captured torn-file backup does not match its result')
    return folder, result, snapshot, backup


def plan(run_id):
    volume = install.identity()
    if volume.get('VolumeUUID') != install.UUID or not volume.get('RemovableMedia') or not volume.get('WritableVolume'):
        raise ValueError('Unexpected or non-writable CARDWRITE volume')
    journal = json.loads((UPDATE/'journal.json').read_text())
    if journal.get('state') != 'completed' or journal.get('plan', {}).get('volume_uuid') != install.UUID:
        raise ValueError('Completed B007R5 install evidence is required')
    folder, result, captured, backup = checked_run(run_id)
    current = install.snapshot()
    if current != captured:
        raise ValueError('CARDWRITE changed since the read-only torn-file collection')
    if current.get(SCRATCH, {}).get('sha256') != result['scratch_sha256']:
        raise ValueError('Current scratch file no longer matches the captured torn image')
    target = b007_oracle.image(1)
    target_hash = sha_bytes(target)
    known_good = json.loads(KNOWN_GOOD.read_text())
    if (known_good.get('collection_pass') is not True or
        known_good.get('image_classification', {}).get('operation') != 1 or
        known_good.get('scratch_sha256') != target_hash):
        raise ValueError('Tag-1 target does not match the prior verified physical image')
    value = {
        'source_run': run_id,
        'source_torn_sha256': result['scratch_sha256'],
        'source_backup': str(backup.relative_to(ROOT)),
        'target_tag': 1,
        'target_size': len(target),
        'target_sha256': target_hash,
        'volume_uuid': install.UUID,
        'before_snapshot_sha256': sha_bytes(json.dumps(current, sort_keys=True).encode()),
    }
    value['token'] = sha_bytes(json.dumps(value, sort_keys=True).encode())
    return value


def copy_verified(source, target, expected):
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst)
        dst.flush()
        os.fsync(dst.fileno())
    if install.sha(target) != expected:
        raise ValueError('Local forensic backup hash mismatch')


def apply(run_id, reviewed_plan):
    if plan(run_id) != reviewed_plan:
        raise ValueError('CARDWRITE or evidence changed after the dry run')
    folder, result, captured, backup = checked_run(run_id)
    restore_dir = EVIDENCE/run_id
    if restore_dir.exists():
        raise ValueError('Restore evidence folder already exists')
    target_data = b007_oracle.image(1)
    destination = CARD/SCRATCH
    install.safe(destination, CARD)
    temporary = destination.with_name(destination.name+'.restore-tag1')
    install.safe(temporary, CARD)
    if temporary.exists():
        raise ValueError('Restore temporary path already exists')

    restore_dir.mkdir(parents=True)
    copy_verified(backup, restore_dir/'torn-powercut-b007.bin', result['scratch_sha256'])
    (restore_dir/'tag1-powercut-b007.bin').write_bytes(target_data)
    if install.sha(restore_dir/'tag1-powercut-b007.bin') != reviewed_plan['target_sha256']:
        raise ValueError('Prepared tag-1 recovery image hash mismatch')
    write_json(restore_dir/'plan.json', reviewed_plan)
    write_json(restore_dir/'before.json', captured)
    write_json(restore_dir/'journal.json', {'state': 'started', 'plan': reviewed_plan})

    with temporary.open('xb') as stream:
        stream.write(target_data)
        stream.flush()
        os.fsync(stream.fileno())
    if install.sha(temporary) != reviewed_plan['target_sha256']:
        raise ValueError('Temporary restore file hash mismatch')
    if install.sha(destination) != result['scratch_sha256']:
        raise ValueError('Torn scratch file changed before replacement')
    os.replace(temporary, destination)
    os.sync()
    after = install.snapshot()
    stable = install.snapshot() == after
    changed = sorted(path for path in set(captured) | set(after) if captured.get(path) != after.get(path))
    passed = (changed == [SCRATCH] and stable and
              after.get(SCRATCH, {}).get('size') == reviewed_plan['target_size'] and
              after.get(SCRATCH, {}).get('sha256') == reviewed_plan['target_sha256'])
    write_json(restore_dir/'after.json', after)
    write_json(restore_dir/'journal.json', {
        'state': 'completed' if passed else 'failed', 'plan': reviewed_plan,
        'changed_paths': changed, 'stable_during_verification': stable,
        'target_verified': after.get(SCRATCH, {}).get('sha256') == reviewed_plan['target_sha256'],
    })
    if not passed:
        raise ValueError('Restore verification failed; preserve CARDWRITE for inspection')
    print(json.dumps({'state': 'completed', 'restored_path': SCRATCH,
                      'sha256': reviewed_plan['target_sha256'], 'changed_paths': changed,
                      'torn_backup': str((restore_dir/'torn-powercut-b007.bin').relative_to(ROOT))}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--yes', action='store_true')
    parser.add_argument('--token')
    args = parser.parse_args()
    try:
        reviewed = plan(args.run_id)
        restore_dir = EVIDENCE/args.run_id
        if not args.yes:
            print(json.dumps(reviewed, indent=2))
            return 0
        if args.token != reviewed['token']:
            raise ValueError('Restore plan token mismatch; inspect a fresh dry run')
        apply(args.run_id, reviewed)
        return 0
    except (ValueError, OSError, KeyError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
