#!/usr/bin/env python3
"""Verify exact card bytes after the B006 single-prefix full-power-cycle test."""
import hashlib
import json
import os
import sys
from pathlib import Path

import install
import recovery

ROOT = install.ROOT
TEST_ID = 'B006-POWER-CYCLE-PREFIX1-001'
ASSETS = tuple(f'Assets/cardwrite/alfatreze.CARDWRITE02/recover-b005-{x}.bin'
               for x in ('a', 'b'))


def collect():
    proof_path = ROOT / 'work/evidence/b006-power-cycle-prefix-jtag-summary.json'
    proof = json.loads(proof_path.read_text())
    if not (proof.get('pass') and proof.get('jtag_recovery_pass') and
            proof.get('host_remount_pending') and
            proof['post_reboot_cold_read']['selected_generation'] == 1038 and
            proof['post_reboot_cold_read']['valid_mask'] == 2):
        raise ValueError('Verified post-power-cycle read-only recovery proof required')

    identity = install.identity()
    evidence_dir = ROOT / 'work/evidence/runs' / f'{TEST_ID}-HOST'
    if evidence_dir.exists():
        raise ValueError('Host evidence already exists; inspect before retry')
    before = install.snapshot()
    baseline = json.loads((ROOT / 'work/evidence/runs/B006-POSTINSTALL-64-REMOUNT01/after.json').read_text())
    expected_dir = ROOT / 'work/evidence/runs' / TEST_ID
    expected_files = [expected_dir / f'expected-{label}.bin' for label in ('a', 'b')]
    expected_hashes = [install.sha(path) for path in expected_files]

    evidence_dir.mkdir(parents=True)
    contents = []
    for relative in ASSETS:
        source = install.CARD / relative
        install.safe(source, install.CARD)
        data = source.read_bytes()
        contents.append(data)
        (evidence_dir / Path(relative).name).write_bytes(data)

    actual = recovery.verify_files(*contents, expected_generation=1038)
    actual_hashes = [hashlib.sha256(data).hexdigest() for data in contents]
    exact = actual_hashes == expected_hashes
    allowed = set(ASSETS) | {f'System/{name}' for name in install.CACHES}
    changed = sorted(path for path, old in baseline.items()
                     if path not in allowed and before.get(path) != old)
    missing = sorted(path for path in baseline if path not in before and path not in allowed)
    added = sorted(set(before) - set(baseline))
    stable = install.snapshot() == before
    install.identity()

    report = {
        'test_id': TEST_ID,
        'volume_uuid': identity['VolumeUUID'],
        'jtag_recovery_proof_sha256': hashlib.sha256(proof_path.read_bytes()).hexdigest(),
        'file_verification': actual,
        'expected_sha256': expected_hashes,
        'actual_sha256': actual_hashes,
        'matches_expected_partial_record_files': exact,
        'changed_or_missing_unrelated_files': sorted(set(changed + missing)),
        'new_files_for_review': added,
        'stable_during_collection': stable,
        'pass': bool(actual['pass'] and exact and not changed and not missing and stable),
        'scope': 'Exact whole-file/guard/CRC check against the independently prepared one-chunk prefix model after full Pocket power cycle; unrelated existing files compared with the pre-test snapshot, apart from Pocket menu caches.'
    }
    (evidence_dir / 'after.json').write_text(json.dumps(before, indent=2) + '\n')
    (evidence_dir / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    final = ROOT / 'work/evidence/b006-power-cycle-prefix-host-summary.json'
    if final.exists():
        raise ValueError('Public host summary already exists; inspect before retry')
    final.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    try:
        result = collect()
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result['pass'] else 1)
    except (ValueError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
