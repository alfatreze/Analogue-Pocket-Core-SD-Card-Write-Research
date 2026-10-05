#!/usr/bin/env python3
"""Audited B006 update of the stable core, with verified local backups."""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
import install

BUILD = 'guarded06'
ROOT = install.ROOT
CARD = install.CARD
CORE = 'Cores/alfatreze.CARDWRITE02'
ASSETS = tuple('Assets/cardwrite/alfatreze.CARDWRITE02/recover-b005-'+x+'.bin' for x in ('a','b'))
EVIDENCE = ROOT/'work/evidence/update-guarded06-resumed'
VERIFIED_RUN = None


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str)+'\n')


def plan():
    install.identity()
    install.safe(CARD/CORE,CARD)
    package = ROOT/'work/packages'/BUILD
    new = json.loads((package.parent/(BUILD+'-manifest.json')).read_text())
    audit = json.loads((ROOT/'work/evidence'/('custom-build-audit-'+BUILD+'.json')).read_text())
    if new['provenance'] != audit or audit.get('minimum_reported_slack_ns',-1)<0:
        raise ValueError('Package does not match qualified build evidence')
    prior = json.loads((package.parent/'recovery05-manifest.json').read_text())
    # Before mutation, require the exact previously qualified active core.
    prior_core = {p: h for p,h in prior['files'].items() if p.startswith(CORE+'/')}
    current_core = {p.relative_to(CARD).as_posix():install.sha(p)
                    for p in (CARD/CORE).rglob('*') if p.is_file()}
    if current_core != prior_core:
        raise ValueError('Active core differs from archived B005; review required')
    copies = []
    for relative, expected in sorted(new['files'].items()):
        if Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError('Traversal refused in update path: '+relative)
        if not (relative.startswith(CORE+'/') or relative=='Platforms/cardwrite.json'):
            raise ValueError('Unexpected update path: '+relative)
        source = package/relative
        target = CARD/relative
        install.safe(source, package);install.safe(target, CARD)
        if install.sha(source)!=expected:
            raise ValueError('Package hash mismatch: '+relative)
        before = install.sha(target) if target.exists() else None
        if before is None:raise ValueError('B006 update cannot create new paths or save fixtures')
        if relative=='Platforms/cardwrite.json' and before!=expected:
            raise ValueError('Shared platform would change')
        copies.append(dict(path=relative,sha256=expected,before_sha256=before,
                           action='identical' if before==expected else 'replace' if before else 'create'))
    caches=[]
    for name in install.CACHES:
        path=CARD/'System'/name;install.safe(path,CARD)
        if path.exists():caches.append(dict(path='System/'+name,sha256=install.sha(path)))
    if VERIFIED_RUN is None:raise ValueError('Explicit verified connected remount run required')
    if not VERIFIED_RUN or not all(c.isalnum() or c in '-_' for c in VERIFIED_RUN):raise ValueError('Invalid verified-run ID')
    trial=ROOT/'work/evidence/runs'/VERIFIED_RUN
    result=json.loads((trial/'result.json').read_text())
    summary_path=ROOT/'work/evidence/b006-connected-resumed-summary.json';summary=json.loads(summary_path.read_text())
    if not (result.get('pass') and result.get('exact_connected_model_pass') and result.get('stable_during_collection') and result['experiment_build']=='B006' and result['connected_summary_sha256']==install.sha(summary_path) and summary['pass']):raise ValueError('Verified B006 connected remount gate absent')
    if install.sha(ROOT/'work/evidence/b006-connected-resumed-campaign.json')!=summary['campaign_sha256']:raise ValueError('Connected campaign evidence changed')
    baseline=json.loads((trial/'after.json').read_text());snapshot=install.snapshot()
    if snapshot!=baseline:raise ValueError('Card changed since verified connected remount; preserve/review before updating')
    for relative,expected_hash in zip(ASSETS,summary['final_expected_files']['sha256']):
        if snapshot.get(relative,{}).get('sha256')!=expected_hash or install.sha(trial/Path(relative).name)!=expected_hash:raise ValueError('Connected output/raw host backup mismatch')
    preserved=[]
    for relative in ('Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin','Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin','Assets/cardwrite/alfatreze.CARDWRITE02/stress-b004.bin')+ASSETS:
        path=CARD/relative;install.safe(path,CARD)
        if install.sha(path)!=baseline[relative]['sha256']:
            raise ValueError('Verified prior output changed: '+relative)
        preserved.append(dict(path=relative,sha256=install.sha(path)))
    result=dict(build='B006',verified_run=VERIFIED_RUN,connected_summary_sha256=install.sha(summary_path),stable_core=CORE,volume_uuid=install.UUID,copies=copies,
                cache_backup_then_clear=caches,preserve=preserved)
    result['token']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    return result


def archive_previous():
    frozen=json.loads((ROOT/'work/build/recovery05-manifest.json').read_text())['files']
    for relative,expected in frozen.items():
        if install.sha(ROOT/'work/build/recovery05'/relative)!=expected:
            raise ValueError('Prior frozen sources changed; do not archive as qualified')
    audit=json.loads((ROOT/'work/evidence/custom-build-audit-recovery05.json').read_text())
    package=ROOT/'work/packages/recovery05'
    prior=json.loads((package.parent/'recovery05-manifest.json').read_text())
    if prior['provenance']!=audit:raise ValueError('Prior package audit differs')
    for relative,h in prior['files'].items():
        if install.sha(package/relative)!=h:raise ValueError('Prior qualified package changed')
    for name,h in audit.get('reports',{}).items():
        if install.sha(ROOT/'work/fpga/recovery05-s1'/name)!=h:raise ValueError('Prior report/bitstream changed')
    archive=ROOT/'work/archives/recovery05-before-b006-resumed'
    if archive.exists():raise ValueError('Prior archive exists; inspect before retrying update')
    archive.mkdir(parents=True)
    paths=['work/build/recovery05','work/build/recovery05-manifest.json',
           'work/fpga/recovery05-s1','work/packages/recovery05',
           'work/packages/recovery05-manifest.json','work/evidence/custom-build-audit-recovery05.json',
           'work/evidence/b005-resumed-summary.json','work/evidence/b005-connected-campaign.json']
    paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/'work/evidence').glob('b005-*') if p.is_file() and p.relative_to(ROOT).as_posix() not in paths]
    paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/'work/evidence/runs').glob('RECOVERY-005-*') if p.is_dir()]
    paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/'work/evidence/jtag').glob('b005-*') if p.is_file() or p.is_dir()]
    for relative in paths:
        src=ROOT/relative;dst=archive/relative
        dst.parent.mkdir(parents=True,exist_ok=True)
        if src.is_dir():shutil.copytree(src,dst)
        else:shutil.copy2(src,dst)
        inputs=[src] if src.is_file() else [p for p in src.rglob('*') if p.is_file()]
        for p in inputs:
            copied=dst if src.is_file() else dst/p.relative_to(src)
            if install.sha(p)!=install.sha(copied):raise ValueError('Archive mismatch')
    files={p.relative_to(archive).as_posix():install.sha(p) for p in archive.rglob('*') if p.is_file()}
    write_json(archive/'archive-manifest.json',files)


def apply(current):
    if (EVIDENCE/'journal.json').exists():raise ValueError('Existing update journal; do not overwrite evidence')
    if plan()!=current:raise ValueError('Plan changed before backup')
    before=install.snapshot();write_json(EVIDENCE/'before.json',before)
    write_json(EVIDENCE/'journal.json',dict(state='started',plan=current))
    archive_previous()
    # All old core files, caches and successful physical output are backed up first.
    paths={p for p in before if p.startswith(CORE+'/')}
    paths|={c['path'] for c in current['cache_backup_then_clear']}
    paths.update(p['path'] for p in current['preserve'])
    for relative in sorted(paths):
        src=CARD/relative;dst=EVIDENCE/'backup'/relative
        install.safe(src,CARD);dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        if install.sha(dst)!=before[relative]['sha256']:raise ValueError('Backup mismatch: '+relative)
    write_json(EVIDENCE/'backup-manifest.json',{p:before[p] for p in sorted(paths)})
    os.sync()
    # Revalidate the approved plan and identity after backup, before card mutation.
    if plan()!=current:raise ValueError('Update plan changed during backup')
    source=ROOT/'work/packages'/BUILD
    for item in current['copies']:
        if item['action']=='identical':continue
        target=CARD/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
        if item['action']=='replace':
            if install.sha(target)!=item['before_sha256']:raise ValueError('Target changed')
            temporary=target.with_name(target.name+'.b006-update')
        else:temporary=target
        # Exclusive create of scratch/staging paths; replacements have verified backups.
        with (source/item['path']).open('rb') as src,temporary.open('xb') as dst:
            shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
        if install.sha(temporary)!=item['sha256']:raise ValueError('Copied hash mismatch')
        if item['action']=='replace':
            if install.sha(target)!=item['before_sha256']:raise ValueError('Target changed before replace')
            os.replace(temporary,target)
        if install.sha(target)!=item['sha256']:raise ValueError('Installed hash mismatch')
    for cache in current['cache_backup_then_clear']:
        if install.sha(CARD/cache['path'])!=cache['sha256']:raise ValueError('Cache changed')
        (CARD/cache['path']).unlink()
    os.sync()
    for item in current['copies']:
        if install.sha(CARD/item['path'])!=item['sha256']:
            raise ValueError('Final package verification mismatch: '+item['path'])
    after=install.snapshot();write_json(EVIDENCE/'after.json',after)
    allowed={p['path'] for p in current['copies']}|{p['path'] for p in current['cache_backup_then_clear']}
    unexpected=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p) and p not in allowed]
    write_json(EVIDENCE/'journal.json',dict(state='failed' if unexpected else 'completed',plan=current,
                                          unexpected_changes=unexpected))
    if unexpected:raise ValueError('Unrelated file changes: '+repr(unexpected))
    print('B006 installed in the same core entry; all hashes verified, prior results preserved.')


def main():
    global VERIFIED_RUN
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verified-run',required=True)
    parser.add_argument('--yes',action='store_true');parser.add_argument('--token')
    args=parser.parse_args();VERIFIED_RUN=args.verified_run
    volume=install.identity()
    current=plan();write_json(EVIDENCE/'plan.json',current)
    write_json(EVIDENCE/'volume.json',volume)
    if not args.yes:print(json.dumps(current,indent=2));return
    if args.token!=current['token']:raise ValueError('Plan token mismatch; review current plan first')
    apply(current)


if __name__=='__main__':
    try:main()
    except (ValueError,OSError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
