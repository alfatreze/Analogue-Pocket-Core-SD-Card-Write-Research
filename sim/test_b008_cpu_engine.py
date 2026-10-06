#!/usr/bin/env python3
"""Exact pinned CPU + unchanged B007 engine; synthetic bounded APF only."""
import hashlib,json,re,shutil,struct,subprocess,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,cwd,log):
 r=subprocess.run([str(x) for x in cmd],cwd=cwd,capture_output=True,text=True)
 log.write_text(r.stdout+r.stderr)
 if r.returncode:raise RuntimeError(f'Failed: {log}')
 return r.stdout

def main():
 root=ROOT/'work/sim/b008'/time.strftime('%Y%m%d-%H%M%S');root.mkdir(parents=True)
 sources=['rtl/b008_mailbox.sv','rtl/lab_powercut.sv','references/tau-7b98a2e/VexRiscv_Full.v','sim/tb_b008_cpu_engine.sv','sim/b008/start.S','sim/b008/link.ld','sim/b008/main.c','sim/test_b008_cpu_engine.py','sim/tb_b008_mailbox.sv','tools/b007_oracle.py']
 assert sha(ROOT/sources[1])=='4ea25d793ece1da4424e424ba814b46b76e59c369ae16b137291f1cc880f5946'
 assert sha(ROOT/sources[2])=='1ee38dc4b0f3a2ce08de9df1f8e2bb8fceb628a89adb7f624f38ae44cebe9fcc'
 tc=ROOT/'../tau-alpha/toolchain/xpack-riscv-none-elf-gcc-15.2.0-1/bin'
 trials=[]
 snapshot=root/'sources';snapshot.mkdir()
 for source in sources:
  target=snapshot/source;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,target)
 try:
  run(['iverilog','-g2012','-s','tb_b008_mailbox','-o',root/'mailbox.vvp',ROOT/'sim/tb_b008_mailbox.sv',ROOT/'rtl/b008_mailbox.sv'],ROOT,root/'mailbox-compile.log')
  mailbox_output=run(['vvp',root/'mailbox.vvp'],root,root/'mailbox-run.log')
  assert 'PASS B008 mailbox' in mailbox_output
  print('PASS mailbox directed checks',flush=True)
  for size in (1024,262144):
   build=root/f'verilated-{size}'
   with tempfile.TemporaryDirectory(prefix='apc-b008-') as temporary:
    scratch=Path(temporary)
    for s in sources[:4]:shutil.copy2(ROOT/s,scratch/Path(s).name)
    run(['verilator','--binary','--timing','-j','4','-Wno-fatal','--top-module','tb_b008_cpu_engine',f'-GFILE_BYTES={size}','--Mdir','obj']+[Path(s).name for s in sources[:4]],scratch,root/f'compile-{size}.log')
    shutil.copytree(scratch/'obj',build)
   cases=list(range(11)) if size==1024 else [0]
   for profile in cases:
    ratios=[(8333,0),(10000,2171),(6734,3001),(5556,571)] if profile==0 and size==1024 else [(8333,1777)]
    for half,phase in ratios:
     folder=root/f'bytes{size}-p{profile}-clk{half}';folder.mkdir()
     run([tc/'riscv-none-elf-gcc','-march=rv32im','-mabi=ilp32','-mno-relax','-O2','-ffreestanding','-nostdlib','-nostartfiles','-Wl,--no-warn-rwx-segments',f'-DPROFILE={profile}','-T',ROOT/'sim/b008/link.ld',ROOT/'sim/b008/start.S',ROOT/'sim/b008/main.c','-o',folder/'firmware.elf'],ROOT,folder/'firmware-build.log')
     run([tc/'riscv-none-elf-objcopy','-O','binary',folder/'firmware.elf',folder/'firmware.bin'],ROOT,folder/'objcopy.log')
     firmware=(folder/'firmware.bin').read_bytes();assert len(firmware)<0x3000
     (folder/'firmware.hex').write_text(''.join(f'{x:08x}\n' for x in struct.unpack('<4096I',firmware+bytes(16384-len(firmware)))))
     output=run([build/'Vtb_b008_cpu_engine',f'+profile={profile}',f'+half_ps={half}',f'+phase_ps={phase}'],folder,folder/'run.log')
     assert 'PASS B008 CPU engine' in output
     words=[int(x,16) for x in re.sub(r'//[^\n]*','',(folder/'final-card.hex').read_text()).split()]
     tag=1 if profile in (0,6,8) else 0
     expected=[0x41504357,0x30303700,tag,size]+[((i*0x9e3779b1)^(tag*0x85ebca6b)^0xb007c0de)&0xffffffff for i in range(4,size//4)]
     if profile==4:expected[10]=((10*0x9e3779b1)^0x85ebca6b^0xb007c0de)&0xffffffff
     assert words==expected,'Independent whole-file oracle mismatch'
     if size==262144:
      import sys;sys.path.insert(0,str(ROOT/'tools'));import b007_oracle
      assert struct.pack('>'+str(len(words))+'I',*words)==b007_oracle.image(tag)
     trials.append({'file_bytes':size,'profile':profile,'cpu_half_ps':half,'engine_phase_ps':phase,'pass':True,'output':output.strip(),'firmware_sha256':sha(folder/'firmware.bin'),'log_sha256':sha(folder/'run.log'),'final_file_sha256':hashlib.sha256(struct.pack('>'+str(len(words))+'I',*words)).hexdigest()})
     print(f'PASS {folder.name}',flush=True)
  evidence={'pass':True,'scope':'Isolated exact VexRiscv execution and unchanged B007 engine; synthetic APF, no card or hardware writes; reduced adversarial fixtures and one exact 256KiB B007 oracle trial. Does not qualify physical CPU persistence, metastability/STA, full Tau mapping or playback.','mailbox':{'pass':True,'snapshot_trials':32,'output':mailbox_output.strip(),'log_sha256':sha(root/'mailbox-run.log')},'local_artifacts':str(root.relative_to(ROOT)),'trials':trials,'source_hashes':{s:sha(ROOT/s) for s in sources},'failed_attempts':[{'artifacts':str(p.parent.relative_to(ROOT)),'failure_sha256':sha(p),'error':json.loads(p.read_text())['error'].replace(str(ROOT)+'/', ''),'source_hashes':json.loads(p.read_text())['source_hashes'],'failed_log_sha256':sha(p.parent/'bytes1024-p5-clk8333/run.log')} for p in sorted((ROOT/'work/sim/b008').glob('*/failure.json'))]}
  (ROOT/'work/evidence/b008-cpu-engine-simulation.json').write_text(json.dumps(evidence,indent=2)+'\n')
 except Exception as e:
  (root/'failure.json').write_text(json.dumps({'error':str(e),'passed_trials':trials,'source_hashes':{s:sha(ROOT/s) for s in sources}},indent=2)+'\n');raise
if __name__=='__main__':main()
