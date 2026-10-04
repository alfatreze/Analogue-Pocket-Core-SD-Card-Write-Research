#!/usr/bin/env python3
"""Independent host oracle and project-local fixtures. Never installs to a card."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def record(generation):
    if not 1 <= generation <= 0xffffffff:
        raise ValueError('generation must be in 1..4294967295')
    # Byte-level oracle, not copied/generated from the RTL function.
    payload = bytearray(b'NCW1')
    for word in (1, 64, generation, 0x00010001):
        payload.extend(word.to_bytes(4, 'big'))
    for index in range(5, 15):
        word = ((0x10203040 + (index << 28) + index) & 0xffffffff) ^ generation
        payload.extend(word.to_bytes(4, 'big'))
    checksum = 0
    for offset in range(0, 60, 4):
        checksum ^= int.from_bytes(payload[offset:offset + 4], 'big')
    payload.extend(checksum.to_bytes(4, 'big'))
    return bytes(payload)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def local_output(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    # Generated evidence stays on the host inside this project.
    if not path.is_relative_to(ROOT / 'work'):
        raise ValueError('output must be under this project/work')
    return path


def write_json(path, value):
    path = local_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def file_manifest(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('manifest root must be a directory')
    files = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'symlink refused in fixture: {path}')
        if path.is_file():
            data = path.read_bytes()
            files[path.relative_to(root).as_posix()] = {'size': len(data), 'sha256': digest(data)}
    return {'root': str(root), 'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    fixture = sub.add_parser('fixture')
    fixture.add_argument('--generation', type=int, default=1)
    fixture.add_argument('--out', default='work/fixtures/generation-1.bin')
    verify = sub.add_parser('verify')
    verify.add_argument('file', type=Path)
    verify.add_argument('--generation', type=int, required=True)
    control = sub.add_parser('verify-control')
    control.add_argument('file', type=Path)
    control.add_argument('--image', type=int, choices=range(4), default=0)
    manifest = sub.add_parser('manifest')
    manifest.add_argument('root', type=Path)
    manifest.add_argument('--out', required=True)
    compare = sub.add_parser('compare')
    compare.add_argument('manifest', type=Path)
    compare.add_argument('root', type=Path)
    compare.add_argument('--allow', action='append', default=[])
    args = parser.parse_args()
    try:
        if args.command == 'fixture':
            path = local_output(args.out)
            path.parent.mkdir(parents=True, exist_ok=True)
            data = record(args.generation)
            path.write_bytes(data)
            print(json.dumps({'path': str(path), 'size': len(data), 'sha256': digest(data)}))
        elif args.command in ('verify', 'verify-control'):
            actual = args.file.read_bytes()
            if args.command == 'verify':
                expected = record(args.generation)
                context = {'generation': args.generation}
            else:
                bank = (ROOT / 'vendor/official-targetdata/dist/assets/ex_image_all.bin').read_bytes()
                expected = bank[args.image * 184320:(args.image+1)*184320]
                context = {'image_bank_entry': args.image}
            match = actual == expected
            detail = {'pass': match, 'file': str(args.file), **context,
                      'expected_size': len(expected), 'actual_size': len(actual),
                      'expected_sha256': digest(expected), 'actual_sha256': digest(actual)}
            if not match:
                detail['first_mismatch'] = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), min(len(actual), len(expected)))
                if len(actual) == 64:
                    swapped = b''.join(actual[i:i+4][::-1] for i in range(0,64,4))
                    detail['word_byte_order_reversed'] = swapped == expected
            print(json.dumps(detail, indent=2))
            return 0 if match else 1
        elif args.command == 'manifest':
            value = file_manifest(args.root)
            write_json(args.out, value)
            print(f'Manifest: {len(value["files"])} files -> {local_output(args.out)}')
        elif args.command == 'compare':
            before = json.loads(args.manifest.read_text())['files']
            after = file_manifest(args.root)['files']
            allowed = set(args.allow)
            changes = [{'path': name, 'before': before.get(name), 'after': after.get(name)}
                       for name in sorted(set(before) | set(after))
                       if before.get(name) != after.get(name) and name not in allowed]
            print(json.dumps({'pass': not changes, 'unexpected_changes': changes}, indent=2))
            return 1 if changes else 0
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
