#!/usr/bin/env python3
"""Prepare exact B006 single-chunk power-cycle expectations from a verified baseline."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import connected_guarded_campaign as campaign
import recovery


def main():
    baseline_id = 'B006-POSTINSTALL-64-REMOUNT01'
    baseline_dir = ROOT / 'work/evidence/runs' / baseline_id
    baseline = json.loads((baseline_dir / 'result.json').read_text())
    if not baseline.get('pass') or baseline.get('experiment_generation') != 1038:
        raise ValueError('Verified generation-1038 host remount required')

    files = [bytearray((baseline_dir / f'recover-b005-{name}.bin').read_bytes())
             for name in ('a', 'b')]
    initial = recovery.verify_files(*(bytes(data) for data in files),
                                    expected_generation=1038, expect_generated=True)
    if not initial['pass'] or initial['sha256'] != baseline['actual_sha256']:
        raise ValueError('Preserved whole-file baseline mismatch')

    dest, generation = campaign.apply_prefix(files, 1)
    expected = recovery.verify_files(*(bytes(data) for data in files),
                                     expected_generation=1038)
    if expected['generation'] != 1038 or expected['valid'] != [False, True]:
        raise ValueError('One-chunk interruption model did not preserve B1038 as the only valid record')
    record_start = recovery.configuration()['record_offset']
    partial = bytes(files[dest][record_start:record_start + 512])
    if recovery.validate(partial)['valid']:
        raise ValueError('One-chunk prefix unexpectedly forms a valid record')

    evidence_dir = ROOT / 'work/evidence/runs/B006-POWER-CYCLE-PREFIX1-001'
    if evidence_dir.exists():
        raise ValueError('Preparation evidence already exists; inspect before retry')
    evidence_dir.mkdir(parents=True)
    for name, data in zip(('a', 'b'), files):
        (evidence_dir / f'expected-{name}.bin').write_bytes(data)

    report = {
        'pass': True,
        'test_id': 'B006-POWER-CYCLE-PREFIX1-001',
        'baseline_test_id': baseline_id,
        'baseline_generation': 1038,
        'pause_point': 1,
        'completed_128_byte_chunks_before_pause': 1,
        'next_generation': generation,
        'partial_destination': 'A' if dest == 0 else 'B',
        'expected_valid_mask': [False, True],
        'expected_recovered_generation': 1038,
        'expected_files_sha256': [hashlib.sha256(data).hexdigest() for data in files],
        'initial_file_sha256': baseline['actual_sha256'],
        'scope': 'Offline preparation only. Model predicts one completed 128-byte inactive-record prefix, followed by full Pocket power-off while no APF command is outstanding. It does not model power loss during an active SD command.',
    }
    (ROOT / 'work/evidence/b006-power-cycle-prefix-preparation.json').write_text(
        json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
