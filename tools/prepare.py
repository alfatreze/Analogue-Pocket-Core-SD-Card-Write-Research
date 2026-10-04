#!/usr/bin/env python3
"""Reproducibly stage sources and two Pocket packages inside this project."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_NAMES = ('core', 'data', 'interact', 'input', 'video', 'audio', 'variants')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def validate_vendor():
    pins = json.loads((ROOT / 'vendor/PINNED.json').read_text())
    for name, pin in pins.items():
        for relative, expected in pin['files'].items():
            path = ROOT / 'vendor' / name / relative
            if not path.is_file() or sha(path) != expected:
                raise SystemExit(f'Pinned source changed: {path}')
    return pins


def manifest(package, provenance):
    result = {'provenance': provenance, 'files': {str(p.relative_to(package)): sha(p)
        for p in sorted(package.rglob('*')) if p.is_file()}}
    json_write(package.parent / (package.name + '-manifest.json'), result)


def prepare_reference(pins):
    source = ROOT / 'vendor/official-targetdata'
    package = ROOT / 'work/packages/official-control'
    metadata = json.loads((source / 'core.json').read_text())['core']['metadata']
    core_id = metadata['author'] + '.' + metadata['shortname']
    target = package / 'Cores' / core_id
    target.mkdir(parents=True, exist_ok=True)
    for name in JSON_NAMES:
        shutil.copy2(source / (name + '.json'), target)
    for name in ('icon.bin',):
        shutil.copy2(source / 'dist' / name, target)
    shutil.copy2(source / 'info.txt', target)
    shutil.copy2(source / 'output/bitstream.rbf_r', target)
    shutil.copytree(source / 'dist/platforms', package / 'Platforms', dirs_exist_ok=True)
    assets = package / 'Assets/ex_platform' / core_id
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / 'dist/assets/ex_image_all.bin', assets)
    manifest(package, {'kind': 'official upstream prebuilt control; RTL-to-bitstream correspondence not independently verified',
                       'commit': pins['official-targetdata']['commit']})


def prepare_custom(pins):
    source = ROOT / 'vendor/core-template'
    stage = ROOT / 'work/build/minimal01'
    if (stage / 'src/fpga/output_files').exists():
        raise SystemExit('Build output exists; use a new immutable build stage instead of overwriting it.')
    shutil.copytree(source / 'src', stage / 'src', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('output_files','db','incremental_db'))
    core = stage / 'src/fpga/core'
    for path in (ROOT / 'rtl').iterdir():
        if path.is_file():
            shutil.copy2(path, core / path.name)
    qsf = stage / 'src/fpga/ap_core.qsf'
    lines = [line for line in qsf.read_text().splitlines()
             if not any(key in line for key in ('SIGNALTAP', 'core/core_constraints.sdc'))]
    lines.extend(['set_global_assignment -name ENABLE_SIGNALTAP OFF',
                  'set_global_assignment -name SYSTEMVERILOG_FILE core/lab_probe.sv',
                  'set_global_assignment -name SYSTEMVERILOG_FILE core/lab_video.sv',
                  'set_global_assignment -name SEARCH_PATH core',
                  'set_global_assignment -name NUM_PARALLEL_PROCESSORS 2',
                  'set_global_assignment -name SEED 1'])
    qsf.write_text('\n'.join(lines) + '\n')
    # Keep real related PLL outputs grouped together; no false cut between them.
    (core / 'core_constraints.sdc').write_text('''set_clock_groups -asynchronous \\
 -group {bridge_spiclk} \\
 -group {clk_74a} \\
 -group {clk_74b} \\
 -group [get_clocks {*mp1*}]
''')
    manifest(stage, {'template_commit': pins['core-template']['commit'], 'seed': 1,
                     'kind': 'minimal01 staged sources; no CPU/external RAM'})
    package = ROOT / 'work/packages/minimal01'
    dest = package / 'Cores/alfatreze.CARDWRITE01'
    dest.mkdir(parents=True, exist_ok=True)
    for name in JSON_NAMES:
        value = json.loads((source / (name + '.json')).read_text())
        if name == 'core':
            value['core']['metadata'].update(platform_ids=['cardwrite'], shortname='CARDWRITE01',
                author='alfatreze', description='Card write probe 01 - 64 byte BRAM FSM',
                version='0.1.0', date_release='2026-10-04')
        elif name == 'data':
            value['data']['data_slots'] = [dict(name='Probe output', id='0x22', required=False,
                parameters=2, deferload=True, filename='write64.bin')]
        elif name == 'input':
            value['input']['controllers'] = [dict(type='default', mappings=[
                dict(id=0,name='Write generation',key='pad_btn_a'),
                dict(id=1,name='Read and compare',key='pad_btn_b')])]
        json_write(dest / (name + '.json'), value)
    platform = json.loads((source / 'dist/platforms/ex_platform.json').read_text())
    platform['platform'].update(name='Card Writing Lab', category='Research', manufacturer='Tau', year=2026)
    json_write(package / 'Platforms/cardwrite.json', platform)
    (dest / 'info.txt').write_text('Card write research probe 01\nA writes generation 1, then 2, etc.\nB reads and compares against expected.\nWRITE CMD OK is not a durability claim.\nVerify write64.bin on the host after Quit.\nDisposable test card only.\nTimeout: quit and relaunch the core.\n')
    output = package / 'Assets/cardwrite/alfatreze.CARDWRITE01/write64.bin'
    output.parent.mkdir(parents=True, exist_ok=True)
    # Existing-file baseline. First write must visibly replace zero bytes.
    output.write_bytes(bytes(64))
    manifest(package, {'kind': 'minimal01; not installable until audited bitstream exists',
                       'template_commit': pins['core-template']['commit'], 'seed': 1})
    print(f'Staged {stage}; prepared {package}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    pins = validate_vendor()
    prepare_reference(pins)
    prepare_custom(pins)


if __name__ == '__main__':
    main()
