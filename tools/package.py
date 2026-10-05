#!/usr/bin/env python3
"""Qualify collected custom build evidence and package its raw RBF exactly once."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',choices=['minimal01','minimal02','batch03','batch03r1','batch03r2','stress04','stress04r1','stress04r2'],default='minimal01')
    build_id=parser.parse_args().build
    BUILD=ROOT/'work/fpga'/(build_id+'-s1')
    PACKAGE=ROOT/'work/packages'/build_id
    if not (BUILD/'quartus-fit.log').is_file():
        raise SystemExit('Custom compile reports not collected yet; package remains unqualified.')
    log=(BUILD/'quartus-fit.log').read_text()
    if not re.search(r'Full Compilation was successful\. 0 errors',log):
        raise SystemExit('Missing successful full compilation evidence')
    summary=(BUILD/'ap_core.sta.summary').read_text()
    slacks=[float(value) for value in re.findall(r'^Slack\s*:\s*(-?[\d.]+)',summary,re.M)]
    if len(slacks)<8 or min(slacks)<0:
        raise SystemExit('Incomplete or failing multicorner timing summary')
    source_manifest=ROOT/'work/build'/(build_id+'-manifest.json')
    sources=json.loads(source_manifest.read_text())
    for relative,expected in sources['files'].items():
        if sha(ROOT/'work/build'/build_id/relative)!=expected:
            raise SystemExit('Frozen compile stage differs from source manifest')
    raw=BUILD/'ap_core.rbf'
    if not raw.is_file() or raw.stat().st_size==0:
        raise SystemExit('Raw RBF missing')
    # The old template prebuilt may be present in the frozen stage; never use it.
    original=ROOT/'vendor/core-template/src/fpga/output_files/ap_core.rbf'
    if sha(raw)==sha(original):
        raise SystemExit('Collected RBF matches unmodified template; wrong build suspected')
    reverse=bytes(int(f'{byte:08b}'[::-1],2) for byte in range(256))
    bitstream=PACKAGE/'Cores'/('alfatreze.CARDWRITE02' if build_id.startswith(('batch03','stress04')) else 'alfatreze.CARDWRITE'+build_id[-2:])/'bitstream.rbf_r'
    bitstream.write_bytes(raw.read_bytes().translate(reverse))
    if build_id.startswith('stress04'):
        simulation=json.loads((ROOT/'work/evidence/b004r2-simulation-summary.json').read_text())
        if (not simulation.get('pass') or simulation['source_manifest_sha256']!=sha(source_manifest) or
            simulation['configuration_sha256']!=sha(ROOT/'experiments/b004.json')):
            raise SystemExit('Stress simulation/configuration does not match this frozen compile')
    audit={'kind':'custom '+build_id+', full compile and internal timing qualified; Pocket pending',
           'seed':1,'raw_sha256':sha(raw),'rbf_r_sha256':sha(bitstream),
           'minimum_reported_slack_ns':min(slacks),
           'compile_source_manifest_sha256':sha(source_manifest),
           'reports':{p.name:sha(p) for p in BUILD.iterdir() if p.is_file()}}
    if build_id.startswith('stress04'):
        audit['experiment_config_sha256']=sha(ROOT/'experiments/b004.json')
        audit['simulation_summary_sha256']=sha(ROOT/'work/evidence/b004r2-simulation-summary.json')
    (ROOT/'work/evidence'/('custom-build-audit.json' if build_id=='minimal01' else 'custom-build-audit-'+build_id+'.json')).write_text(json.dumps(audit,indent=2)+'\n')
    files={p.relative_to(PACKAGE).as_posix():sha(p) for p in sorted(PACKAGE.rglob('*')) if p.is_file()}
    (PACKAGE.parent/(build_id+'-manifest.json')).write_text(json.dumps({'provenance':audit,'files':files},indent=2)+'\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
