#!/usr/bin/env python3
"""Run B007 full-length RTL and independent host-oracle checks."""
import hashlib
import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'work/evidence/b007-simulation-summary.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', default='powercut07r5')
    stage_id = parser.parse_args().stage
    sim = ROOT / 'work/sim/b007'
    sim.mkdir(parents=True, exist_ok=True)
    compiler = os.environ.get('IVERILOG', 'iverilog')
    runtime = os.environ.get('VVP', 'vvp')
    binary = sim / 'powercut.vvp'
    log = sim / 'powercut.log'
    compile_cmd = [compiler, '-g2012', '-s', 'tb_powercut', '-o', str(binary),
                   'sim/tb_powercut.sv', 'rtl/lab_powercut.sv']
    built = subprocess.run(compile_cmd, cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        log.write_text(built.stdout + built.stderr)
        raise SystemExit('B007 RTL compilation failed; see ' + str(log))
    ran = subprocess.run([runtime, str(binary)], cwd=ROOT, capture_output=True, text=True)
    log.write_text(built.stdout + built.stderr + ran.stdout + ran.stderr)
    if ran.returncode or 'PASS B007' not in ran.stdout:
        raise SystemExit('B007 full-length simulation failed; see ' + str(log))
    jtag_test = subprocess.run(['python3', 'sim/test_jtag_powercut.py'], cwd=ROOT,
                               capture_output=True, text=True)
    jtag_log = sim / 'jtag-decoder.log'
    jtag_log.write_text(jtag_test.stdout + jtag_test.stderr)
    if jtag_test.returncode:
        raise SystemExit('SDW7 decoder tests failed; see ' + str(jtag_log))
    update_test = subprocess.run(['python3', 'sim/test_update_powercut.py'], cwd=ROOT,
                                 capture_output=True, text=True)
    update_log = sim / 'update-plan-tests.log'
    update_log.write_text(update_test.stdout + update_test.stderr)
    if update_test.returncode:
        raise SystemExit('B007R5 update safety tests failed; see ' + str(update_log))

    import sys
    sys.path.insert(0, str(ROOT / 'tools'))
    import b007_oracle
    baseline, updated = b007_oracle.image(0), b007_oracle.image(1)
    mixed = baseline[:len(baseline)//2] + updated[len(updated)//2:]
    corrupted = bytearray(updated)
    corrupted[100] ^= 1
    outcomes = {
        'baseline': b007_oracle.classify(baseline, [0, 1]),
        'updated': b007_oracle.classify(updated, [0, 1]),
        'word_aligned_mix': b007_oracle.classify(mixed, [0, 1]),
        'unknown_corruption': b007_oracle.classify(bytes(corrupted), [0, 1]),
        'wrong_size': b007_oracle.classify(updated[:-1], [0, 1]),
    }
    assert outcomes['baseline']['classification'] == 'exact-operation-image'
    assert outcomes['baseline']['operation'] == 0
    assert outcomes['updated']['classification'] == 'exact-operation-image'
    assert outcomes['updated']['operation'] == 1
    assert outcomes['word_aligned_mix']['classification'] == 'mixed-old-new'
    assert outcomes['unknown_corruption']['classification'] == 'unrecognized-or-damaged'
    assert outcomes['wrong_size']['classification'] == 'wrong-size'

    stage_manifest = ROOT / 'work/build'/(stage_id+'-manifest.json')
    staged_rtl = ROOT / 'work/build'/stage_id/'src/fpga/core/lab_powercut.sv'
    if not staged_rtl.is_file() or sha(staged_rtl) != sha(ROOT/'rtl/lab_powercut.sv'):
        raise SystemExit('Frozen B007 stage RTL differs from the source exercised by simulation')
    summary = {
        'kind': 'B007 active-write RTL plus independent host-image oracle; hardware pending',
        'pass': True,
        'build_stage': stage_id,
        'source_manifest_sha256': sha(stage_manifest),
        'configuration_sha256': sha(ROOT / 'experiments/b007.json'),
        'test_sources': {p: sha(ROOT / p) for p in (
            'rtl/lab_powercut.sv', 'sim/tb_powercut.sv', 'tools/b007_oracle.py',
            'sim/test_powercut.py', 'tools/jtag_powercut.py', 'tools/jtag_powercut.tcl',
            'tools/jtag_powercut_session.py', 'sim/test_jtag_powercut.py', 'tools/update_powercut.py',
            'tools/read_powercut.py', 'sim/test_update_powercut.py')},
        'reports': {'work/sim/b007/powercut.log': sha(log),
            'work/sim/b007/jtag-decoder.log': sha(jtag_log),
            'work/sim/b007/update-plan-tests.log': sha(update_log)},
        'simulation_cases': ['complete baseline cold read and all received-word marks',
            'write locked before cold read', 'alternating full-file source at first/middle/final bridge addresses',
            'stop requested during active write waits for genuine DONE', 'missing plus duplicate receive address is rejected', 'SDW7 snapshot magic',
            'host exact baseline/image, mixed boundary, unknown corruption and size classification'],
        'host_oracle_outcomes': outcomes,
        'note': 'Target transport and persistence are modeled; no Pocket or SD card result is implied.'
    }
    EVIDENCE.write_text(json.dumps(summary, indent=2) + '\n')
    print(ran.stdout.strip())
    print('PASS B007 independent host oracle; evidence: ' + str(EVIDENCE))


if __name__ == '__main__':
    main()
