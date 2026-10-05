#!/usr/bin/env python3
"""B003 configuration and independent byte oracle; fixtures stay in project/work."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'experiments/b003.json'


def configuration():
    value = json.loads(CONFIG.read_text())
    assert len(value['cases']) == 32 and value['file_size'] == 262144
    for index, case in enumerate(value['cases']):
        assert case['id'] == index and case['region_offset'] == index * 8192
        assert 0 <= case['pattern'] < 5 and 1 <= len(case['write_lengths']) <= 3
        assert all(1 <= n <= 4096 for n in case['write_lengths'])
        assert case['offset_in_region'] + max(case['write_lengths']) < 8192
    return value


def payload(case, ordinal, length):
    # Independent byte calculation. RTL packs four corresponding bytes into words.
    mode, number = case['pattern'], case['id']
    if mode == 0:
        return bytes(length)
    if mode == 1:
        return bytes([255]) * length
    if mode == 2:
        return bytes(170 if i % 2 == 0 else 85 for i in range(length))
    if mode == 3:
        return bytes((i + number + ordinal) % 256 for i in range(length))
    return bytes((i ^ (i // 256) ^ (number * 17) ^ (ordinal * 73) ^ 61) % 256
                 for i in range(length))


def expected_file():
    config = configuration()
    data = bytearray([config['guard_byte']]) * config['file_size']
    for case in config['cases']:
        offset = case['region_offset'] + case['offset_in_region']
        for ordinal, length in enumerate(case['write_lengths'], 1):
            data[offset:offset + length] = payload(case, ordinal, length)
    return bytes(data)


def verify(data):
    config = configuration()
    expected = expected_file()
    failures = []
    for case in config['cases']:
        start = case['region_offset']
        stop = start + config['region_size']
        if data[start:stop] != expected[start:stop]:
            failures.append(case['id'])
    first = next((i for i, (a, b) in enumerate(zip(data, expected)) if a != b), None)
    if first is None and len(data) != len(expected):
        first = min(len(data), len(expected))
    return dict(pass_=data == expected, expected_size=len(expected), actual_size=len(data),
                failed_regions=failures, first_mismatch=first,
                expected_sha256=hashlib.sha256(expected).hexdigest(),
                actual_sha256=hashlib.sha256(data).hexdigest())


def rtl_configuration():
    config = configuration()
    lines = ['// Generated from experiments/b003.json: parameters only, not the byte oracle.']
    for name, width, expression in (
        ('case_offset', 32, lambda c: c['region_offset'] + c['offset_in_region']),
        ('case_max_length', 13, lambda c: max(c['write_lengths'])),
        ('case_passes', 2, lambda c: len(c['write_lengths'])),
        ('case_pattern', 3, lambda c: c['pattern']),
    ):
        lines += [f'function automatic [{width-1}:0] {name}(input [4:0] c);', 'begin case(c)']
        lines += [f"5'd{c['id']}: {name} = {width}'d{expression(c)};" for c in config['cases']]
        lines += [f"default: {name} = 0;", 'endcase end endfunction']
    lines += ['function automatic [12:0] case_length(input [4:0] c, input [1:0] p);',
              'begin', "if (c == 30 && p == 2) case_length = 64;",
              "else if (c == 31 && p == 2) case_length = 5;",
              'else case_length = case_max_length(c);', 'end endfunction']
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['generate-rtl', 'fixture', 'verify'])
    parser.add_argument('file', nargs='?', type=Path)
    args = parser.parse_args()
    if args.command == 'generate-rtl':
        (ROOT / 'rtl/batch_cases.vh').write_text(rtl_configuration())
    elif args.command == 'fixture':
        out = ROOT / 'work/fixtures/batch-b003-initial.bin'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(bytes([configuration()['guard_byte']]) * configuration()['file_size'])
        print(out)
    else:
        result = verify(args.file.read_bytes())
        result['pass'] = result.pop('pass_')
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result['pass'] else 1)
