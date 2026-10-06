#!/usr/bin/env python3
"""Compile the isolated B008 interactive firmware without changing Tau files."""
import hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 tc=ROOT/'../tau-alpha/toolchain/xpack-riscv-none-elf-gcc-15.2.0-1/bin'
 sources=[ROOT/'firmware/b008'/x for x in ('link.ld','start.S','main.c')]
 command=[tc/'riscv-none-elf-gcc','-march=rv32im','-mabi=ilp32','-mno-relax','-O2','-ffreestanding','-nostdlib','-nostartfiles','-Wl,--no-warn-rwx-segments','-T',sources[0],sources[1],sources[2],'-o',folder/'firmware.elf']
 r=subprocess.run(list(map(str,command)),capture_output=True,text=True);(folder/'firmware-build.log').write_text(r.stdout+r.stderr)
 if r.returncode:raise RuntimeError('Firmware compile failed')
 subprocess.run([str(tc/'riscv-none-elf-objcopy'),'-O','binary',str(folder/'firmware.elf'),str(folder/'firmware.bin')],check=True)
 data=(folder/'firmware.bin').read_bytes()
 if len(data)>=0x3000:raise RuntimeError('Firmware exceeds bounded ROM region')
 (folder/'firmware.hex').write_text(''.join(f'{x:08x}\n' for x in struct.unpack('<4096I',data+bytes(16384-len(data)))))
 report={'firmware_bytes':len(data),'sha256':sha(folder/'firmware.bin'),'hex_sha256':sha(folder/'firmware.hex'),'sources':{str(p.relative_to(ROOT)):sha(p) for p in sources},'compiler_sha256':sha(tc/'riscv-none-elf-gcc')}
 (folder/'firmware.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);args=p.parse_args();print(json.dumps(build(args.folder),indent=2))
