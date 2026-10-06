#!/usr/bin/env python3
"""Create and independently classify deterministic B007 scratch images."""
import argparse
import hashlib
import json
from pathlib import Path

SIZE = 262144
MAGIC = b'APCW007\0'


def image(operation: int) -> bytes:
    if operation not in (0, 1):
        raise ValueError('image tag must be 0 or 1')
    result = bytearray(SIZE)
    result[:8] = MAGIC
    result[8:12] = operation.to_bytes(4, 'big')
    result[12:16] = SIZE.to_bytes(4, 'big')
    for word in range(4, SIZE // 4):
        value = ((word * 0x9E3779B1) ^ ((operation & 1) * 0x85EBCA6B) ^ 0xB007C0DE) & 0xFFFFFFFF
        result[word * 4:word * 4 + 4] = value.to_bytes(4, 'big')
    return bytes(result)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify(actual: bytes, operations: list[int]) -> dict:
    known = {op: image(op) for op in operations}
    matches = [op for op, expected in known.items() if actual == expected]
    if matches:
        return {'classification': 'exact-operation-image', 'operation': matches[0], 'sha256': sha(actual)}
    if len(actual) != SIZE:
        return {'classification': 'wrong-size', 'actual_size': len(actual), 'expected_size': SIZE, 'sha256': sha(actual)}
    adjacent = []
    ordered = sorted(operations)
    for old_op, new_op in zip(ordered, ordered[1:]):
        old, new = known[old_op], known[new_op]
        old_or_new = new_or_old = unknown = 0
        runs = 0
        last_kind = None
        for pos in range(0, SIZE, 4):
            chunk = actual[pos:pos + 4]
            kind = 'old' if chunk == old[pos:pos + 4] else 'new' if chunk == new[pos:pos + 4] else 'unknown'
            if kind == 'old': old_or_new += 1
            elif kind == 'new': new_or_old += 1
            else: unknown += 1
            if kind != last_kind:
                runs += 1
                last_kind = kind
        adjacent.append({'old_operation': old_op, 'new_operation': new_op,
                         'old_words': old_or_new, 'new_words': new_or_old,
                         'unknown_words': unknown, 'class_transitions': max(0, runs - 1)})
    best = min(adjacent, key=lambda row: (row['unknown_words'], row['class_transitions'])) if adjacent else None
    kind = 'mixed-old-new' if best and best['unknown_words'] == 0 and best['old_words'] and best['new_words'] else 'unrecognized-or-damaged'
    return {'classification': kind, 'sha256': sha(actual), 'best_adjacent_pair': best}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    gen = sub.add_parser('generate')
    gen.add_argument('--operation', type=int, required=True)
    gen.add_argument('--output', type=Path, required=True)
    verify = sub.add_parser('verify')
    verify.add_argument('--input', type=Path, required=True)
    verify.add_argument('--operations', type=int, nargs='+', required=True,
                        help='image tags that may have been present (0 is baseline, 1 is updated image)')
    args = parser.parse_args()
    if args.command == 'generate':
        data = image(args.operation)
        args.output.write_bytes(data)
        print(json.dumps({'path': str(args.output), 'size': len(data), 'sha256': sha(data)}, indent=2))
    else:
        result = classify(args.input.read_bytes(), args.operations)
        print(json.dumps(result, indent=2))
        if result['classification'] not in ('exact-operation-image', 'mixed-old-new'):
            raise SystemExit(2)


if __name__ == '__main__':
    main()
