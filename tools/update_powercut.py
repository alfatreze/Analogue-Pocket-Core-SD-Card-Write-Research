#!/usr/bin/env python3
"""Audited B006-to-B007R5 card update; requires the exact B006 remount baseline."""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import install

BUILD = 'powercut07r5'
ROOT = install.ROOT
CARD = install.CARD
CORE = 'Cores/alfatreze.CARDWRITE02'
SCRATCH = 'Assets/cardwrite/alfatreze.CARDWRITE02/powercut-b007.bin'
PRESERVE = (
    'Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin',
    'Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin',
    'Assets/cardwrite/alfatreze.CARDWRITE02/stress-b004.bin',
    'Assets/cardwrite/alfatreze.CARDWRITE02/recover-b005-a.bin',
    'Assets/cardwrite/alfatreze.CARDWRITE02/recover-b005-b.bin',
)
HOST_RUN = 'B006-POWER-CYCLE-PREFIX1-001-HOST'
EVIDENCE = ROOT/'work/evidence/update-powercut07r5'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str)+'\n')


def file_hash(path):
    return install.sha(path)


def checked_manifest(build):
    path=ROOT/'work/build'/(build+'-manifest.json')
    manifest=json.loads(path.read_text())
    for relative,expected in manifest['files'].items():
        if file_hash(ROOT/'work/build'/build/relative)!=expected:
            raise ValueError('Frozen source changed: '+build+'/'+relative)
    return manifest


def plan():
    identity=install.identity()
    if identity.get('VolumeUUID')!=install.UUID:raise ValueError('Unexpected removable volume')
    host=ROOT/'work/evidence/runs'/HOST_RUN
    baseline=json.loads((host/'after.json').read_text())
    host_result=json.loads((host/'result.json').read_text())
    host_summary=json.loads((ROOT/'work/evidence/b006-power-cycle-prefix-host-summary.json').read_text())
    prep=json.loads((ROOT/'work/evidence/b006-power-cycle-prefix-preparation.json').read_text())
    if not (host_result.get('pass') and host_result.get('stable_during_collection') and
            host_summary.get('pass') and host_summary.get('stable_during_collection') and prep.get('pass') and
            host_summary['volume_uuid']==install.UUID and
            host_result.get('test_id')=='B006-POWER-CYCLE-PREFIX1-001'):
        raise ValueError('Latest verified B006 cold-remount evidence is missing or failed')
    expected_save_hashes=host_summary['actual_sha256']
    for relative,expected in zip(PRESERVE[-2:],expected_save_hashes):
        if baseline.get(relative,{}).get('sha256')!=expected:
            raise ValueError('B006 power-cycle remount save hashes differ from model')
    current=install.snapshot()
    if current!=baseline:
        raise ValueError('CARDWRITE differs from the latest B006 remount inventory; recollect and review')

    build=ROOT/'work/packages'/BUILD
    package_manifest=json.loads((build.parent/(BUILD+'-manifest.json')).read_text())
    audit=json.loads((ROOT/'work/evidence'/('custom-build-audit-'+BUILD+'.json')).read_text())
    if package_manifest.get('provenance')!=audit or audit.get('minimum_reported_slack_ns',-1)<0:
        raise ValueError('B007R5 package lacks matching successful fit/timing qualification')
    frozen=checked_manifest(BUILD)
    if audit.get('compile_source_manifest_sha256')!=file_hash(ROOT/'work/build'/(BUILD+'-manifest.json')):
        raise ValueError('B007R5 compile manifest mismatch')
    if (not json.loads((ROOT/'work/evidence/b007-simulation-summary.json').read_text()).get('pass') or
        not json.loads((ROOT/'work/evidence/b007-display-review.json').read_text()).get('pass')):
        raise ValueError('B007 RTL or display gate missing')
    prior_manifest=json.loads((ROOT/'work/packages/guarded06-manifest.json').read_text())
    prior_core={p:h for p,h in prior_manifest['files'].items() if p.startswith(CORE+'/')}
    observed_core={p:h['sha256'] for p,h in baseline.items() if p.startswith(CORE+'/')}
    if observed_core!=prior_core:
        raise ValueError('The current physical core does not match qualified B006')

    files=[]
    for relative,expected in sorted(package_manifest['files'].items()):
        path=Path(relative)
        if path.is_absolute() or '..' in path.parts:raise ValueError('Traversal in package path')
        if not (relative.startswith(CORE+'/') or relative=='Platforms/cardwrite.json' or relative==SCRATCH):
            raise ValueError('Unexpected B007R5 package path: '+relative)
        source=build/relative;target=CARD/relative
        install.safe(source,build);install.safe(target,CARD)
        if not source.is_file() or file_hash(source)!=expected:raise ValueError('Package file hash mismatch: '+relative)
        before=current.get(relative,{}).get('sha256')
        if relative==SCRATCH:
            if before is not None:raise ValueError('B007 scratch file already exists; preserve and review it')
            if source.stat().st_size!=262144:raise ValueError('B007 scratch fixture size mismatch')
            action='create'
        else:
            if before is None:raise ValueError('B007 update may not create core/platform paths: '+relative)
            if relative=='Platforms/cardwrite.json' and before!=expected:
                raise ValueError('Shared platform definition would change')
            action='identical' if before==expected else 'replace'
        files.append({'path':relative,'sha256':expected,'before_sha256':before,'action':action})
    if SCRATCH not in [f['path'] for f in files]:raise ValueError('B007 scratch fixture missing from candidate')
    preserved=[]
    for relative in PRESERVE:
        item=current.get(relative)
        if item is None:raise ValueError('Prior output is missing: '+relative)
        preserved.append({'path':relative,'size':item['size'],'sha256':item['sha256']})
    caches=[]
    for name in install.CACHES:
        item=current.get('System/'+name)
        if item:caches.append({'path':'System/'+name,'sha256':item['sha256']})
    result={'build':BUILD,'previous_build':'B006','volume_uuid':install.UUID,
        'baseline_run':HOST_RUN,'baseline_snapshot_sha256':file_hash(host/'after.json'),
        'baseline_host_summary_sha256':file_hash(ROOT/'work/evidence/b006-power-cycle-prefix-host-summary.json'),
        'source_manifest_sha256':file_hash(ROOT/'work/build'/(BUILD+'-manifest.json')),
        'compile_audit_sha256':file_hash(ROOT/'work/evidence'/('custom-build-audit-'+BUILD+'.json')),
        'package_files':files,'preserve':preserved,'cache_backup_then_clear':caches,
        'source_files_count':len(frozen['files'])}
    result['token']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    return result


def copy_verified(source,target,expected,exclusive=False):
    target.parent.mkdir(parents=True,exist_ok=True)
    mode='xb' if exclusive else 'wb'
    with source.open('rb') as src,target.open(mode) as dst:
        shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
    if file_hash(target)!=expected:raise ValueError('Backup/copy hash mismatch: '+str(target))


def archive_b006():
    archive=ROOT/'work/archives/guarded06-before-b007r5'
    if archive.exists():raise ValueError('B006 archive already exists; inspect before continuing')
    sources=[ROOT/'work/build/guarded06',ROOT/'work/build/guarded06-manifest.json',
        ROOT/'work/fpga/guarded06-s1',ROOT/'work/packages/guarded06',
        ROOT/'work/packages/guarded06-manifest.json',ROOT/'work/evidence/custom-build-audit-guarded06.json',
        ROOT/'work/evidence/b006-final-card-verification.json',
        ROOT/'work/evidence/b006-post-install-64-save-summary.json',
        ROOT/'work/evidence/b006-post-install-64-remount-summary.json',
        ROOT/'work/evidence/b006-power-cycle-prefix-jtag-summary.json',
        ROOT/'work/evidence/b006-power-cycle-prefix-host-summary.json',
        ROOT/'work/evidence/b006-power-cycle-prefix-preparation.json',
        ROOT/'work/evidence/runs'/HOST_RUN]
    for source in sources:
        if not source.exists():raise ValueError('Missing B006 archive input: '+str(source))
    archive.mkdir(parents=True)
    for source in sources:
        target=archive/source.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.is_dir():shutil.copytree(source,target)
        else:shutil.copy2(source,target)
    files={p.relative_to(archive).as_posix():file_hash(p) for p in archive.rglob('*') if p.is_file()}
    write_json(archive/'archive-manifest.json',files)
    for relative,digest in files.items():
        if file_hash(archive/relative)!=digest:raise ValueError('B006 archive verification failed')


def apply(current):
    if (EVIDENCE/'journal.json').exists():raise ValueError('Existing B007R5 update journal; do not overwrite evidence')
    if plan()!=current:raise ValueError('B007R5 plan changed before backup')
    before=install.snapshot()
    write_json(EVIDENCE/'before.json',before)
    write_json(EVIDENCE/'journal.json',{'state':'started','plan':current})
    backups={p['path'] for p in current['package_files'] if p['action']=='replace'}
    backups|={p['path'] for p in current['preserve']}
    backups|={p['path'] for p in current['cache_backup_then_clear']}
    for relative in sorted(backups):
        path=CARD/relative
        if file_hash(path)!=before[relative]['sha256']:raise ValueError('Card file changed before backup: '+relative)
        copy_verified(path,EVIDENCE/'backup'/relative,before[relative]['sha256'],exclusive=True)
    write_json(EVIDENCE/'backup-manifest.json',{p:before[p] for p in sorted(backups)})
    os.sync()
    archive_b006()
    if plan()!=current:raise ValueError('B007R5 plan changed after verified backup')
    package=ROOT/'work/packages'/BUILD
    for item in current['package_files']:
        if item['action']=='identical':continue
        target=CARD/item['path'];source=package/item['path']
        if item['action']=='create':
            copy_verified(source,target,item['sha256'],exclusive=True)
        else:
            if file_hash(target)!=item['before_sha256']:raise ValueError('Replacement target changed: '+item['path'])
            temporary=target.with_name(target.name+'.b007r5-update')
            copy_verified(source,temporary,item['sha256'],exclusive=True)
            if file_hash(target)!=item['before_sha256']:raise ValueError('Replacement target changed before rename')
            os.replace(temporary,target)
            if file_hash(target)!=item['sha256']:raise ValueError('Replacement hash mismatch')
    for item in current['cache_backup_then_clear']:
        path=CARD/item['path']
        if file_hash(path)!=item['sha256']:raise ValueError('Pocket cache changed before removal')
        path.unlink()
    os.sync()
    after=install.snapshot()
    write_json(EVIDENCE/'after.json',after)
    allowed={f['path'] for f in current['package_files']}|{c['path'] for c in current['cache_backup_then_clear']}
    unexpected=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p) and p not in allowed]
    write_json(EVIDENCE/'journal.json',{'state':'failed' if unexpected else 'completed',
        'plan':current,'unexpected_changes':unexpected})
    if unexpected:raise ValueError('Unexpected card changes: '+repr(unexpected))
    for item in current['preserve']:
        if after.get(item['path'],{}).get('sha256')!=item['sha256']:
            raise ValueError('Protected output changed: '+item['path'])
    print('B007R5 installed; scratch fixture and core hashes verified; B005/B006/B004 outputs preserved.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yes',action='store_true');parser.add_argument('--token')
    args=parser.parse_args()
    try:
        current=plan()
        EVIDENCE.mkdir(parents=True,exist_ok=True)
        write_json(EVIDENCE/'plan.json',current)
        write_json(EVIDENCE/'volume.json',install.identity())
        if not args.yes:
            print(json.dumps(current,indent=2));return 0
        if args.token!=current['token']:raise ValueError('B007R5 plan token mismatch; inspect a fresh dry run')
        apply(current)
    except (ValueError,OSError,KeyError) as exc:
        print(str(exc),file=sys.stderr);return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
