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


def prepare_custom(pins, build="minimal01"):
    suffix = "02" if build.startswith(("batch03","stress04","recovery05","guarded06")) else build[-2:]
    label = {"batch03":"B003", "batch03r1":"B003R1", "batch03r2":"B003R2", "stress04":"B004", "stress04r1":"B004R1", "stress04r2":"B004R2", "recovery05":"B005", "guarded06":"B006"}.get(build,suffix)
    core_id = "alfatreze.CARDWRITE" + suffix
    source = ROOT / 'vendor/core-template'
    stage = ROOT / 'work/build' / build
    if stage.exists():
        raise SystemExit('Build output exists; use a new immutable build stage instead of overwriting it.')
    shutil.copytree(source / 'src', stage / 'src', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('output_files','db','incremental_db'))
    core = stage / 'src/fpga/core'
    for path in (ROOT / 'rtl').iterdir():
        if path.is_file():
            shutil.copy2(path, core / path.name)
    qsf = stage / 'src/fpga/ap_core.qsf'
    lines = [line for line in qsf.read_text().splitlines()
             if not any(key in line for key in ('SIGNALTAP', 'SLD_FILE', 'core/core_constraints.sdc'))]
    lines.extend(['set_global_assignment -name ENABLE_SIGNALTAP OFF',
                  'set_global_assignment -name SYSTEMVERILOG_FILE core/lab_probe.sv',
                  'set_global_assignment -name SYSTEMVERILOG_FILE core/lab_video.sv',
                  'set_global_assignment -name SEARCH_PATH core',
                  'set_global_assignment -name NUM_PARALLEL_PROCESSORS 2',
                  'set_global_assignment -name SEED 1'])
    if build in ('minimal02', 'batch03', 'batch03r1', 'batch03r2','stress04','stress04r1','stress04r2','recovery05','guarded06'):
        lines.append('set_global_assignment -name ALLOW_POWER_UP_DONT_CARE OFF')
    if build.startswith('batch03'):
        lines.extend(['set_global_assignment -name VERILOG_MACRO LAB_BATCH=1',
                      'set_global_assignment -name SYSTEMVERILOG_FILE core/lab_batch.sv'])
    if build in ('batch03r1','batch03r2'):
        lines.append('set_global_assignment -name VERILOG_MACRO LAB_BATCH_REV='+build[-1])
    if build.startswith('stress04'):
        lines.extend(['set_global_assignment -name VERILOG_MACRO LAB_STRESS=1',
                      'set_global_assignment -name SYSTEMVERILOG_FILE core/lab_stress.sv'])
    if build in ('stress04r1','stress04r2'):lines.append('set_global_assignment -name VERILOG_MACRO LAB_STRESS_REV='+build[-1])
    if build=='recovery05':
        lines.extend(['set_global_assignment -name VERILOG_MACRO LAB_RECOVERY=1', 'set_global_assignment -name SYSTEMVERILOG_FILE core/lab_recovery.sv'])
    if build=='guarded06':
        lines.extend(['set_global_assignment -name VERILOG_MACRO LAB_RECOVERY=1','set_global_assignment -name VERILOG_MACRO LAB_RECOVERY_GUARDED=1','set_global_assignment -name SYSTEMVERILOG_FILE core/lab_recovery_guarded.sv'])
    qsf.write_text('\n'.join(lines) + '\n')
    # Keep real related PLL outputs grouped together; no false cut between them.
    (core / 'core_constraints.sdc').write_text('''set_clock_groups -asynchronous \\
 -group {bridge_spiclk} \\
 -group {clk_74a} \\
 -group {clk_74b} \\
 -group [get_clocks {*mp1*}]
''')
    manifest(stage, {'template_commit': pins['core-template']['commit'], 'seed': 1,
                     'kind': build+' staged sources; no CPU/external RAM'})
    package = ROOT / 'work/packages' / build
    dest = package / 'Cores' / core_id
    dest.mkdir(parents=True, exist_ok=True)
    for name in JSON_NAMES:
        value = json.loads((source / (name + '.json')).read_text())
        if name == 'core':
            value['core']['metadata'].update(platform_ids=['cardwrite'], shortname='CARDWRITE'+suffix,
                author='alfatreze', description='SD Write Research '+label+' - 32 case batch' if build.startswith('batch03') else 'Card write probe '+suffix+' - 64 byte BRAM FSM',
                version={'batch03':'0.3.0','batch03r1':'0.3.1','batch03r2':'0.3.2','minimal02':'0.2.0'}.get(build,'0.1.0'), date_release='2026-10-05' if build in ('minimal02','batch03','batch03r1','batch03r2') else '2026-10-04',
                url='https://github.com/alfatreze')
        elif name == 'data':
            value['data']['data_slots'] = [dict(name='Batch B003' if build.startswith('batch03') else 'Probe output', id='0x23' if build.startswith('batch03') else '0x22', required=False,
                parameters=2, deferload=True, filename='batch-b003.bin' if build.startswith('batch03') else 'write64.bin')]
        elif name == 'input':
            value['input']['controllers'] = [dict(type='default', mappings=[
                dict(id=0,name='Run 32 write tests' if build.startswith('batch03') else 'Write generation',key='pad_btn_a'),
                dict(id=1,name='Cold read 32 tests' if build.startswith('batch03') else 'Read and compare',key='pad_btn_b')])]
        if build.startswith('stress04'):
            if name=='core':value['core']['metadata'].update(description='SD Write Research '+label+' - 10000 pairs',version='0.4.'+build[-1] if build in ('stress04r1','stress04r2') else '0.4.0',date_release='2026-10-05')
            elif name=='data':value['data']['data_slots']=[dict(name='Stress B004',id='0x24',required=False,parameters=2,deferload=True,filename='stress-b004.bin')]
            elif name=='input':value['input']['controllers']=[dict(type='default',mappings=[dict(id=0,name='Run 10000 pairs',key='pad_btn_a'),dict(id=1,name='Cold read 32 finals',key='pad_btn_b')])]
        if build in ('recovery05','guarded06'):
            if name=='core':value['core']['metadata'].update(description='SD Write Research '+label+(' - whole-file guards' if build=='guarded06' else ' - alternate saves'),version='0.6.0' if build=='guarded06' else '0.5.0',date_release='2026-10-05')
            elif name=='data':value['data']['data_slots']=[dict(name='Recovery '+x.upper(),id=hex(37+i),required=False,parameters=2,deferload=True,filename='recover-b005-'+x+'.bin') for i,x in enumerate(('a','b'))]
            elif name=='input':value['input']['controllers']=[dict(type='default',mappings=[dict(id=0,name='Run 64 saves',key='pad_btn_a'),dict(id=1,name='Recover only',key='pad_btn_b')])]
        json_write(dest / (name + '.json'), value)
    platform = json.loads((source / 'dist/platforms/ex_platform.json').read_text())
    platform['platform'].update(name='Card Writing Lab', category='Research', manufacturer='Tau', year=2026)
    json_write(package / 'Platforms/cardwrite.json', platform)
    (dest / 'info.txt').write_text('Card write research probe '+suffix+'\nA writes generation 1, then 2, etc.\nB reads and compares against expected.\nWRITE CMD OK is not a durability claim.\nVerify write64.bin on the host after Quit.\nDisposable test card only.\nTimeout: quit and relaunch the core.\n')
    if build.startswith('batch03'):
        (dest / 'info.txt').write_text('SD Write Research '+label+' - 32 cases\nA runs one write/read batch.\nB after fresh boot reads prior batch.\nWait for BATCH PASS or FAIL, screenshot.\nQuit, shutdown, verify on computer.\nRetained JTAG probe: SDW3.\nTimeout: reconfigure, never retry live.\n')
    output = package / 'Assets/cardwrite' / core_id / ('batch-b003.bin' if build.startswith('batch03') else 'write64.bin')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Existing-file baseline. First write must visibly replace zero bytes.
    output.write_bytes(bytes([0xa5])*262144 if build.startswith('batch03') else bytes(64))
    if build.startswith('stress04'):
        (dest/'info.txt').write_text('SD Write Research '+label+' - 10000 pairs\nA runs one changing-data stress batch.\nB after fresh boot reads 32 final records.\nWait for STRESS PASS or FAIL, screenshot.\nCollect JTAG before Quit.\nQuit, shutdown, verify file on computer.\nRetained JTAG endpoint: SDW4.\nTimeout: reconfigure, never retry live.\n')
        old=package/'Assets/cardwrite'/core_id/'write64.bin'
        old.unlink()
        (old.parent/'stress-b004.bin').write_bytes(bytes([165])*262144)
    if build=='recovery05':
        (dest/'info.txt').write_text('SD Write Research B005 - alternate saves\nA validates both files and saves 64 generations.\nB validates and recovers only; no writes.\nCollect SDW5 JTAG results before Quit.\nJTAG single-save pause points are a separate test.\nCRC detects damage, not deliberate forgery.\nTimeout/error: reconfigure, never retry live.\n')
        output.unlink()
        for x in ('a','b'):(output.parent/('recover-b005-'+x+'.bin')).write_bytes(bytes([165])*8192)
    if build=='guarded06':
        output.unlink()
        (dest/'info.txt').write_text('SD Write Research B006 - whole-file guards\nReuse existing B005 files in slots 0x25/0x26.\nNever reset existing test output files.\nA: 64 saves, full 8 KiB guard/readback checks.\nB: recovery only, full-file validation.\nInitialize only an exactly blank pair.\nRetained endpoint SDW6; CRC is not authentication.\n')
    manifest(package, {'kind': build+'; not installable until audited bitstream exists',
                       'template_commit': pins['core-template']['commit'], 'seed': 1})
    print(f'Staged {stage}; prepared {package}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", choices=["minimal01","minimal02","batch03","batch03r1","batch03r2","stress04","stress04r1","stress04r2","recovery05","guarded06"], default="minimal01")
    args = parser.parse_args()
    pins = validate_vendor()
    if args.build == "minimal01": prepare_reference(pins)
    prepare_custom(pins, args.build)


if __name__ == '__main__':
    main()
