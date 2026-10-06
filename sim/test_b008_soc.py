#!/usr/bin/env python3
"""Exercise the actual B008 synthesizable bus and interactive firmware, no SD IO."""
import hashlib,json,re,shutil,struct,subprocess,tempfile,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import b008_firmware,b007_oracle
from test_b008_cpu_engine import run,sha

def main():
 root=ROOT/'work/sim/b008-soc'/time.strftime('%Y%m%d-%H%M%S');root.mkdir(parents=True)
 sources=['rtl/b008_soc.sv','rtl/b008_mailbox.sv','rtl/lab_powercut.sv','references/tau-7b98a2e/VexRiscv_Full.v','sim/tb_b008_soc.sv','sim/test_b008_soc.py','tools/b008_firmware.py','firmware/b008/main.c','firmware/b008/start.S','firmware/b008/link.ld']
 assert sha(ROOT/sources[2])=='4ea25d793ece1da4424e424ba814b46b76e59c369ae16b137291f1cc880f5946'
 assert sha(ROOT/sources[3])=='1ee38dc4b0f3a2ce08de9df1f8e2bb8fceb628a89adb7f624f38ae44cebe9fcc'
 snapshot=root/'sources'
 for s in sources:
  target=snapshot/s;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/s,target)
 tc=ROOT/'../tau-alpha/toolchain/xpack-riscv-none-elf-gcc-15.2.0-1/bin'
 trials=[]
 try:
  for interactive in (0,1):
   for size in (1024,262144):
    build=root/f'obj-i{interactive}-bytes{size}'
    with tempfile.TemporaryDirectory(prefix='apc-b008-soc-') as temporary:
     scratch=Path(temporary)
     for s in sources[:5]:shutil.copy2(ROOT/s,scratch/Path(s).name)
     run(['verilator','--binary','--timing','-j','4','-Wno-fatal','--top-module','tb_b008_soc',f'-GFILE_BYTES={size}',f'-GINTERACTIVE={interactive}','--Mdir','obj']+[Path(s).name for s in sources[:5]],scratch,root/f'compile-i{interactive}-{size}.log')
     shutil.copytree(scratch/'obj',build)
    cases=[0,6] if interactive else (list(range(11)) if size==1024 else [0])
    for profile in cases:
     ratios=[(8333,0),(10000,2171),(6734,3001),(5556,571)] if not interactive and profile==0 and size==1024 else [(8333,1777)]
     for half,phase in ratios:
      folder=root/f'i{interactive}-bytes{size}-p{profile}-clk{half}';folder.mkdir()
      if interactive:
       firmware=b008_firmware.build(folder)
      else:
       run([tc/'riscv-none-elf-gcc','-march=rv32im','-mabi=ilp32','-mno-relax','-O2','-ffreestanding','-nostdlib','-nostartfiles','-Wl,--no-warn-rwx-segments',f'-DPROFILE={profile}','-T',ROOT/'sim/b008/link.ld',ROOT/'sim/b008/start.S',ROOT/'sim/b008/main.c','-o',folder/'firmware.elf'],ROOT,folder/'firmware-build.log')
       run([tc/'riscv-none-elf-objcopy','-O','binary',folder/'firmware.elf',folder/'firmware.bin'],ROOT,folder/'objcopy.log')
       data=(folder/'firmware.bin').read_bytes();assert len(data)<0x3000
       (folder/'firmware.hex').write_text(''.join(f'{w:08x}\n' for w in struct.unpack('<4096I',data+bytes(16384-len(data)))))
      output=run([build/'Vtb_b008_soc',f'+profile={profile}',f'+half_ps={half}',f'+phase_ps={phase}'],folder,folder/'run.log')
      assert 'PASS B008 synthesizable SoC' in output
      words=[int(x,16) for x in re.sub(r'//[^\n]*','',(folder/'final-card.hex').read_text()).split()]
      tag=1 if profile in (0,6,8) else 0
      expected=[0x41504357,0x30303700,tag,size]+[((i*0x9e3779b1)^(tag*0x85ebca6b)^0xb007c0de)&0xffffffff for i in range(4,size//4)]
      if profile==4:expected[10]=((10*0x9e3779b1)^0x85ebca6b^0xb007c0de)&0xffffffff
      assert words==expected,'Independent whole-file mismatch'
      data=struct.pack('>'+str(len(words))+'I',*words)
      if size==262144:assert data==b007_oracle.image(tag)
      trials.append({'interactive_hardware_firmware':bool(interactive),'file_bytes':size,'profile':profile,'cpu_half_ps':half,'engine_phase_ps':phase,'pass':True,'output':output.strip(),'firmware_sha256':sha(folder/'firmware.bin'),'log_sha256':sha(folder/'run.log'),'final_file_sha256':hashlib.sha256(data).hexdigest()})
      print('PASS '+folder.name,flush=True)
  evidence={'pass':True,'local_artifacts':str(root.relative_to(ROOT)),'source_hashes':{s:sha(ROOT/s) for s in sources},'trials':trials,'scope':'Actual synthesizable CPU/RAM/mailbox bus, with simulation-only exit addresses disabled for four interactive hardware-firmware trials. Modeled APF only; M10K inference/PLL/timing/real Pocket persistence pending.','failed_attempts':[{'artifacts':str(p.parent.relative_to(ROOT)),'sha256':sha(p)} for p in sorted((ROOT/'work/sim/b008-soc').glob('*/failure.json'))]}
  (ROOT/'work/evidence/b008-soc-simulation.json').write_text(json.dumps(evidence,indent=2)+'\n')
 except Exception as error:
  (root/'failure.json').write_text(json.dumps({'error':str(error),'trials':trials,'sources':{s:sha(ROOT/s) for s in sources}},indent=2)+'\n');raise
if __name__=='__main__':main()
