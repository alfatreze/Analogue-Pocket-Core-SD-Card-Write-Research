#!/usr/bin/env python3
"""Build only this project's frozen stage on the existing local Quartus VM."""
import argparse
import hashlib
import io
import json
import re
import shlex
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_ID = 'minimal01'
REMOTE = 'card-writing-lab/minimal01-s1'
KEY = Path.home() / '.ssh/taualpha_vm_ed25519'
SSH = ['ssh', '-i', str(KEY), '-p', '2222', '-o', 'ConnectTimeout=8',
       '-o', 'BatchMode=yes', 'taualpha@127.0.0.1']
QUARTUS = '/home/taualpha/intelFPGA_lite/25.1std/quartus/bin/quartus_sh'


def remote(command, binary=None):
    return subprocess.run(SSH + [command], input=binary, capture_output=True, check=True).stdout


def launch():
    busy = remote('pgrep -a quartus_sh || pgrep -a quartus_map || pgrep -a quartus_fit || true').decode().strip()
    if busy:
        raise SystemExit('Existing Quartus process: refusing to compete.\n' + busy)
    stage = ROOT / 'work/build' / BUILD_ID
    expected = json.loads((stage.parent / (BUILD_ID+'-manifest.json')).read_text())['files']
    for relative, checksum in expected.items():
        path = stage / relative
        if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
            raise SystemExit('Staged source changed: ' + relative)
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w:gz') as bundle:
        bundle.add(stage / 'src', arcname='src')
    remote(f'test ! -e {shlex.quote(REMOTE)} && mkdir -p {shlex.quote(REMOTE)} && tar xzf - -C {shlex.quote(REMOTE)}', archive.getvalue())
    command = (f'cd {shlex.quote(REMOTE)}/src/fpga && '
               f'(setsid nohup env _JAVA_OPTIONS=-Xint {shlex.quote(QUARTUS)} --flow compile ap_core.qpf '
               '< /dev/null > ../../quartus-fit.log 2>&1 &) ; echo started')
    remote(command)
    (ROOT / 'work/evidence').mkdir(parents=True, exist_ok=True)
    (ROOT / 'work/evidence' / ('build-launch-'+BUILD_ID+'.json')).write_text(json.dumps({
        'remote': REMOTE, 'archive_sha256': hashlib.sha256(archive.getvalue()).hexdigest(),
        'source_manifest': 'work/build/'+BUILD_ID+'-manifest.json', 'seed': 1,
        'quartus': QUARTUS, 'java_options': '-Xint (avoid JIT SIGILL under VM emulation)'}, indent=2) + '\n')
    print('Launched isolated build ' + REMOTE)


def status():
    script = f'''d={shlex.quote(REMOTE)}
tail -n 8 "$d/quartus-fit.log"
for f in "$d"/src/fpga/output_files/ap_core.fit.summary "$d"/src/fpga/output_files/ap_core.sta.summary; do
test ! -f "$f" || cat "$f"
done
'''
    print(remote(script).decode())


def collect():
    log = remote(f'cat {REMOTE}/quartus-fit.log').decode()
    if not re.search(r'Full Compilation was successful\. 0 errors', log):
        raise SystemExit('Successful zero-error compilation is not established.')
    out = ROOT / 'work/fpga' / (BUILD_ID+'-s1')
    out.mkdir(parents=True, exist_ok=True)
    for name in ('ap_core.rbf', 'ap_core.sof', 'ap_core.fit.summary', 'ap_core.fit.rpt',
                 'ap_core.sta.summary', 'ap_core.sta.rpt', 'ap_core.map.rpt', 'ap_core.asm.rpt'):
        data = remote(f'cat {REMOTE}/src/fpga/output_files/{name}')
        (out / name).write_bytes(data)
    (out / 'quartus-fit.log').write_text(log)
    summary = (out / 'ap_core.sta.summary').read_text()
    slacks = [float(value) for value in re.findall(r'^Slack\s*:\s*(-?[\d.]+)', summary, re.M)]
    if not slacks or min(slacks) < 0:
        raise SystemExit('Timing gate failed or missing. Reports preserved; not a card candidate.')
    raw = out / 'ap_core.rbf'
    remote_hash = remote(f'sha256sum {REMOTE}/src/fpga/output_files/ap_core.rbf').decode().split()[0]
    local_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
    if local_hash != remote_hash:
        raise SystemExit('VM/local bitstream hash mismatch.')
    print(f'Collected {raw}; SHA-256 {local_hash}; minimum reported slack {min(slacks):+.3f} ns')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['launch', 'status', 'collect'])
    parser.add_argument("--build", choices=["minimal01","minimal02","batch03","batch03r1","batch03r2","stress04","stress04r1","stress04r2","recovery05","guarded06","powercut07","powercut07r1","powercut07r2","powercut07r3","powercut07r4","powercut07r5","cpu08r1"], default="minimal01")
    args = parser.parse_args()
    BUILD_ID = args.build
    REMOTE = "card-writing-lab/"+BUILD_ID+"-s1"
    globals()[args.command]()
