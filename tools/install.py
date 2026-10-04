#!/usr/bin/env python3
"""Plan/verify a new lab core install on the specifically designated CARDWRITE card."""
import argparse
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = Path('/Volumes/CARDWRITE')
UUID = '0C5F72C5-8851-3E82-94F5-5902CF4180FE'
CACHES = ('core_viewby_platform.bin', 'corelist_cache.bin', 'cores_cache.bin',
          'platform_viewby_category.bin', 'platforms_cache.bin')
OS_DIRS = {'.Spotlight-V100', '.Trashes', '.fseventsd', 'System Volume Information'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024*1024), b''):
            h.update(data)
    return h.hexdigest()


def identity():
    info = plistlib.loads(subprocess.check_output(['diskutil','info','-plist',str(CARD)]))
    if info.get('VolumeUUID') != UUID or info.get('MountPoint') != str(CARD):
        raise ValueError('CARDWRITE identity changed; refusing a different volume')
    if not info.get('RemovableMedia') or not info.get('WritableVolume'):
        raise ValueError('Expected a removable writable test card')
    return info


def safe(path, base):
    relative = path.relative_to(base)
    current = base
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlink refused: '+str(current))


def snapshot():
    files = {}
    for root_dir, directories, names in os.walk(CARD, followlinks=False):
        directories[:] = sorted(d for d in directories if d not in OS_DIRS)
        base = Path(root_dir)
        for directory in directories:
            safe(base/directory, CARD)
        for name in sorted(names):
            path = base/name
            safe(path, CARD)
            files[path.relative_to(CARD).as_posix()] = {'size':path.stat().st_size,'sha256':sha(path)}
    return files


def plan(package):
    mapping = {'official-control':'Example Author.Keyboard Mouse Target Data',
               'minimal01':'alfatreze.CARDWRITE01', 'minimal02':'alfatreze.CARDWRITE02'}
    if package not in mapping:
        raise ValueError('Unknown package')
    source = ROOT/'work/packages'/package
    manifest = json.loads((source.parent/(package+'-manifest.json')).read_text())
    if package in ('minimal01','minimal02'):
        audit=ROOT/'work/evidence'/('custom-build-audit.json' if package=='minimal01' else 'custom-build-audit-'+package+'.json')
        if not audit.is_file() or json.loads(audit.read_text())!=manifest['provenance']:
            raise ValueError('Custom build qualification evidence missing or mismatched')
    core = source/'Cores'/mapping[package]
    for name in ('core','data','interact','input','video','audio','variants'):
        json.loads((core/(name+'.json')).read_text())
    if package in ('minimal01','minimal02'):
        metadata=json.loads((core/'core.json').read_text())['core']['metadata']
        for key,limit in {'author':31,'shortname':31,'description':63,'version':31,'url':63}.items():
            if len(metadata.get(key,''))>limit:
                raise ValueError('core.json field limit exceeded: '+key)
        controllers=json.loads((core/'input.json').read_text())['input']['controllers']
        for controller in controllers:
            for button_mapping in controller['mappings']:
                if len(button_mapping['name'])>19:raise ValueError('input mapping label exceeds 19 characters')
    if not (core/'bitstream.rbf_r').is_file():
        raise ValueError('No compiled bitstream; package is not installable')
    if (CARD/'Cores'/mapping[package]).exists():
        raise ValueError('Core already exists; this first-install tool never replaces a core')
    copies = []
    for relative, expected in sorted(manifest['files'].items()):
        parts = Path(relative).parts
        if parts[0] not in ('Cores','Assets','Platforms') or '..' in parts:
            raise ValueError('Unexpected package path')
        src = source/relative
        safe(src, source)
        if sha(src) != expected:
            raise ValueError('Package differs from frozen manifest: '+relative)
        target = CARD/relative
        safe(target,CARD)
        if target.exists() and sha(target) != expected:
            raise ValueError('Would overwrite an existing different file: '+relative)
        copies.append({'path':relative,'size':src.stat().st_size,'sha256':expected,
                       'action':'identical' if target.exists() else 'create'})
    cache_files=[]
    for name in CACHES:
        cache=CARD/'System'/name
        safe(cache,CARD)
        if cache.exists(): cache_files.append({'path':'System/'+name,'sha256':sha(cache)})
    result={'package':package,'volume':str(CARD),'uuid':UUID,'copies':copies,'cache_backup_then_clear':cache_files}
    result['token']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',choices=['official-control','minimal01','minimal02'])
    parser.add_argument('--yes',action='store_true')
    parser.add_argument('--token')
    args=parser.parse_args()
    try:
        info=identity()
        current=plan(args.package)
        evidence=ROOT/'work/evidence'/('install-'+args.package)
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/'volume.json').write_text(json.dumps(info,indent=2,default=str)+'\n')
        (evidence/'plan.json').write_text(json.dumps(current,indent=2)+'\n')
        if not args.yes:
            print(json.dumps(current,indent=2));return 0
        if args.token!=current['token']:
            raise ValueError('Plan token does not match; inspect a current dry-run first')
        before=snapshot()
        (evidence/'before.json').write_text(json.dumps(before,indent=2)+'\n')
        (evidence/'journal.json').write_text(json.dumps({'state':'started','plan':current},indent=2)+'\n')
        for cache in current['cache_backup_then_clear']:
            source=CARD/cache['path'];backup=evidence/'backup'/cache['path']
            backup.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,backup)
            if sha(backup)!=cache['sha256']:raise ValueError('Cache backup mismatch')
        source=ROOT/'work/packages'/args.package
        for item in current['copies']:
            if item['action']=='create':
                target=CARD/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
                # Exclusive create: never overwrite a file that appeared after planning.
                with (source/item['path']).open('rb') as src,target.open('xb') as dest:
                    shutil.copyfileobj(src,dest);dest.flush();os.fsync(dest.fileno())
            if sha(CARD/item['path'])!=item['sha256']:
                raise ValueError('Installed file hash mismatch: '+item['path'])
        for cache in current['cache_backup_then_clear']:
            if sha(CARD/cache['path'])!=cache['sha256']:raise ValueError('Cache changed during install')
            (CARD/cache['path']).unlink()
        os.sync()
        after=snapshot()
        allowed={item['path'] for item in current['copies']}|{c['path'] for c in current['cache_backup_then_clear']}
        unexpected=[name for name in sorted(set(before)|set(after)) if before.get(name)!=after.get(name) and name not in allowed]
        (evidence/'after.json').write_text(json.dumps(after,indent=2)+'\n')
        (evidence/'journal.json').write_text(json.dumps({'state':'failed' if unexpected else 'completed',
            'plan':current,'unexpected_changes':unexpected},indent=2)+'\n')
        if unexpected:raise ValueError('Unexpected file changes: '+repr(unexpected))
        print(f'Installed {args.package}; all {len(current["copies"])} package files verified; protected files unchanged.')
    except (ValueError,OSError,subprocess.CalledProcessError) as error:
        print(str(error),file=sys.stderr);return 1
    return 0


if __name__=='__main__':sys.exit(main())
