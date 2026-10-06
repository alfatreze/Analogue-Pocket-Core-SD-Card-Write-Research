#!/usr/bin/env python3
"""Decode B007 SDW7 snapshots without inferring card durability."""
import re

MAGIC = 0x53445707


def decode_words(words):
    if len(words) != 16 or words[0] != MAGIC:
        raise ValueError('SDW7 packet length or magic mismatch')
    h = words[1]
    request = words[13]
    decoded = {
        'snapshot_toggle': (h >> 31) & 1,
        'active': bool((h >> 30) & 1),
        'is_read': bool((h >> 29) & 1),
        'selected_valid': bool((h >> 28) & 1),
        'can_write': bool((h >> 27) & 1),
        'status': (h >> 20) & 0xF,
        'state': (h >> 15) & 0x1F,
        'last_error': (h >> 12) & 7,
        'operation': words[2],
        'completed': words[3],
        'commands': words[4],
        'elapsed_cycles': words[5],
        'received_words': words[6],
        'read_tag_word': words[7],
        'last_bridge_address': words[8],
        'first_receive_address': words[9],
        'last_receive_address': words[10],
        'source_address': words[11],
        'transfer_length': words[12],
        'target_done': bool((request >> 31) & 1),
        'target_ack': bool((request >> 30) & 1),
        'target_read': bool((request >> 29) & 1),
        'target_write': bool((request >> 28) & 1),
        'target_error': (request >> 25) & 7,
        'matches_tag1': bool((request >> 24) & 1),
        'matches_tag0': bool((request >> 23) & 1),
        'word_capacity': words[14],
    }
    decoded['write_active'] = (decoded['active'] and decoded['target_ack'] and
                               not decoded['target_done'] and not decoded['is_read'] and
                               decoded['status'] == 2)
    if words[15] != 0 or decoded['word_capacity'] != 65536 or decoded['transfer_length'] != 262144:
        raise ValueError('SDW7 reserved field, size or capacity mismatch')
    expected_source = 0x10040000 if decoded['is_read'] else 0x10000000
    if decoded['source_address'] != expected_source:
        raise ValueError('SDW7 source address/mode mismatch')
    return decoded


def decode(raw):
    match = re.search(r'SDW7 summary words=([0-9a-fA-F,]+)', raw)
    if not match:
        return {'valid': False, 'reason': 'SDW7 summary absent'}
    samples = []
    for row in re.finditer(r'SDW7 sample n=(\d+) elapsed_ms=(\d+) words=([0-9a-fA-F,]+)', raw):
        parsed = decode_words([int(v, 16) for v in row[3].split(',')])
        samples.append({'sample': int(row[1]), 'elapsed_ms': int(row[2]), **parsed})
    summary = decode_words([int(v, 16) for v in match[1].split(',')])
    return {'valid': True, 'summary': summary, 'samples': samples,
            'link_lost': 'SDW7 link-lost' in raw,
            'monitor_ended': 'SDW7 monitor-ended' in raw,
            'scope': 'JTAG state observations only; does not prove physical SD persistence or cut timing'}
