#!/usr/bin/env python3
"""Audited B003 update of the stable core, with verified local backups."""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
import install

BUILD = 'batch03r2'
ROOT = install.ROOT
CARD = install.CARD
CORE = 'Cores/alfatreze.CARDWRITE02'
ASSET = 'Assets/cardwrite/alfatreze.CARDWRITE02/batch-b003.bin'
EVIDENCE = ROOT/'work/evidence/update-batch03'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str)+'\n')


def plan():
    install.identity()
    install.safe(CARD/CORE,CARD)
    package = ROOT/'work/packages'/BUILD
    new = json.loads((package.parent/(BUILD+'-manifest.json')).read_text())
    audit = json.loads((ROOT/'work/evidence'/('custom-build-audit-'+BUILD+'.json')).read_text())
    if new['provenance'] != audit:
        raise ValueError('Package does not match qualified build evidence')
    prior = json.loads((package.parent/'minimal02-manifest.json').read_text())
    # Before mutation, require the exact previously qualified active core.
    prior_core = {p: h for p,h in prior['files'].items() if p.startswith(CORE+'/')}
    current_core = {p.relative_to(CARD).as_posix():install.sha(p)
                    for p in (CARD/CORE).rglob('*') if p.is_file()}
    if current_core != prior_core:
        raise ValueError('Active core differs from archived minimal02; review required')
    copies = []
    for relative, expected in sorted(new['files'].items()):
        if Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError('Traversal refused in update path: '+relative)
        if not (relative.startswith(CORE+'/') or relative==ASSET or relative=='Platforms/cardwrite.json'):
            raise ValueError('Unexpected update path: '+relative)
        source = package/relative
        target = CARD/relative
        install.safe(source, package);install.safe(target, CARD)
        if install.sha(source)!=expected:
            raise ValueError('Package hash mismatch: '+relative)
        before = install.sha(target) if target.exists() else None
        if relative==ASSET and before is not None:
            raise ValueError('B003 scratch file already exists; never reset prior results')
        if relative=='Platforms/cardwrite.json' and before!=expected:
            raise ValueError('Shared platform would change')
        copies.append(dict(path=relative,sha256=expected,before_sha256=before,
                           action='identical' if before==expected else 'replace' if before else 'create'))
    caches=[]
    for name in install.CACHES:
        path=CARD/'System'/name;install.safe(path,CARD)
        if path.exists():caches.append(dict(path='System/'+name,sha256=install.sha(path)))
    result=dict(build='B003R2',stable_core=CORE,volume_uuid=install.UUID,copies=copies,
                cache_backup_then_clear=caches,preserve='Assets/cardwrite/alfatreze.CARDWRITE02/write64.bin')
    result['token']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    return result


def archive_previous():
    frozen=json.loads((ROOT/'work/build/minimal02-manifest.json').read_text())['files']
    for relative,expected in frozen.items():
        if install.sha(ROOT/'work/build/minimal02'/relative)!=expected:
            raise ValueError('Prior frozen sources changed; do not archive as qualified')
    archive=ROOT/'work/archives/minimal02-before-b003'
    if archive.exists():raise ValueError('Prior archive exists; inspect before retrying update')
    archive.mkdir(parents=True)
    for relative in ('work/build/minimal02','work/build/minimal02-manifest.json',
                     'work/fpga/minimal02-s1','work/packages/minimal02',
                     'work/packages/minimal02-manifest.json',
                     'work/evidence/custom-build-audit-minimal02.json'):
        src=ROOT/relative;dst=archive/Path(relative).relative_to('work')
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
    before=install.snapshot();write_json(EVIDENCE/'before.json',before)
    write_json(EVIDENCE/'journal.json',dict(state='started',plan=current))
    archive_previous()
    # All old core files, caches and successful physical output are backed up first.
    paths={p for p in before if p.startswith(CORE+'/')}
    paths|={c['path'] for c in current['cache_backup_then_clear']}
    paths.add(current['preserve'])
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
            temporary=target.with_name(target.name+'.b003-update')
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
    print('B003R2 installed in the same core entry; all hashes verified, prior results preserved.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yes',action='store_true');parser.add_argument('--token')
    args=parser.parse_args()
    volume=install.identity()
    current=plan();write_json(EVIDENCE/'plan.json',current)
    write_json(EVIDENCE/'volume.json',volume)
    if not args.yes:print(json.dumps(current,indent=2));return
    if args.token!=current['token']:raise ValueError('Plan token mismatch; review current plan first')
    apply(current)


if __name__=='__main__':
    try:main()
    except (ValueError,OSError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
