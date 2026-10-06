#!/usr/bin/env python3
"""Run a bounded, read-only SDW7 observer through the scoped VM console client."""
import argparse
import json
import time
from pathlib import Path

import console_transport
import jtag_powercut
import vm_build

ROOT = vm_build.ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('status', 'results', 'monitor'))
    parser.add_argument('--duration', type=int, default=300, choices=range(1, 1801))
    parser.add_argument('--poll-ms', type=int, default=25, choices=range(10, 1001))
    args = parser.parse_args()
    if Path('/Volumes/CARDWRITE').exists():
        raise SystemExit('CARDWRITE is mounted on the host; SDW7 expects the card in the Pocket')
    script = (f'set mode {args.mode}\nset duration {args.duration}\nset poll_ms {args.poll_ms}\n').encode()
    script += (ROOT / 'tools/jtag_powercut.tcl').read_bytes()
    transport = console_transport.run(script, 'SDW7', 900 if args.mode == 'monitor' else 90)
    raw = transport.pop('raw')
    decoded = jtag_powercut.decode(raw)
    complete = (transport['transport_done'] and
                (transport['controlled_exit'] or (transport['natural_exit'] and transport['returncode'] == 0)) and
                'SDW7 done' in raw and 'SDW7 ERROR:' not in raw and decoded.get('valid'))
    decoded.update(mode=args.mode, exit_code=0 if complete else 1,
                   script_sha256=transport['script_sha256'], transport=transport)
    output = ROOT / 'work/evidence/jtag'
    output.mkdir(parents=True, exist_ok=True)
    stem = output / ('b007r5-' + args.mode + '-' + str(time.time_ns()))
    stem.with_suffix('.txt').write_text(raw)
    stem.with_suffix('.json').write_text(json.dumps(decoded, indent=2) + '\n')
    if args.mode == 'monitor':
        samples = decoded.get('samples', [])
        active = [row for row in samples if row.get('write_active')]
        first = samples[0] if samples else decoded.get('summary', {})
        last = samples[-1] if samples else decoded.get('summary', {})
        print(json.dumps({
            'mode': args.mode,
            'sample_count': len(samples),
            'first_elapsed_ms': first.get('elapsed_ms'),
            'last_elapsed_ms': last.get('elapsed_ms'),
            'write_active_sample_count': len(active),
            'first_write_active_elapsed_ms': active[0].get('elapsed_ms') if active else None,
            'link_lost': decoded.get('link_lost'),
            'monitor_ended': decoded.get('monitor_ended'),
            'final_state': {key: last.get(key) for key in
                            ('active', 'status', 'state', 'operation', 'completed',
                             'commands', 'elapsed_cycles', 'target_ack', 'target_done',
                             'target_error', 'write_active')},
            'evidence_json': str(stem.with_suffix('.json')),
            'evidence_raw': str(stem.with_suffix('.txt')),
        }, indent=2))
    else:
        print(raw)
        print('B007R5 JTAG evidence: ' + str(stem.with_suffix('.txt')))
    if not complete:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
