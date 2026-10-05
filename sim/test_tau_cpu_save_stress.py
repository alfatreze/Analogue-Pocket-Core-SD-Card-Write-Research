#!/usr/bin/env python3
"""CPU prototype receive-completeness remedy with modeled APF only."""
import argparse,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));import recovery
from test_recovery_guarded import files
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--toolchain',type=Path,default=ROOT/'../tau-alpha/toolchain/xpack-riscv-none-elf-gcc-15.2.0-1/bin');a=p.parse_args();tc=a.toolchain.resolve()
 root=ROOT/'work/sim/tau-cpu-save-stress';root.mkdir(parents=True,exist_ok=True)
 ref=json.loads((ROOT/'work/evidence/tau-cpu-reference.json').read_text())
 for filename,original in (('VexRiscv_Full.v','src/fpga/rtl/VexRiscv_Full.v'),('tgt_cmd.v','src/fpga/core/tgt_cmd.v')):
  if sha(ROOT/'references/tau-7b98a2e'/filename)!=ref['files'][original]:raise ValueError('Pinned CPU changed')
 sources=('sim/tau_cpu_save/link.ld','sim/tau_cpu_save/start.S','sim/tau_cpu_save/stress.c','sim/tb_tau_cpu_save_stress.sv')
 cmd=[str(tc/'riscv-none-elf-gcc'),'-march=rv32im','-mabi=ilp32','-mno-relax','-O2','-ffreestanding','-nostdlib','-nostartfiles','-Wl,--no-warn-rwx-segments','-T',str(ROOT/sources[0]),str(ROOT/sources[1]),str(ROOT/sources[2]),'-o',str(root/'firmware.elf')]
 run=subprocess.run(cmd,capture_output=True,text=True);(root/'build.log').write_text(run.stdout+run.stderr)
 if run.returncode:raise RuntimeError(run.stderr)
 subprocess.run([str(tc/'riscv-none-elf-objcopy'),'-O','binary',str(root/'firmware.elf'),str(root/'firmware.bin')],check=True)
 data=(root/'firmware.bin').read_bytes();data+=bytes(16384-len(data));firmware='\n'.join(f'{w:08x}' for w in struct.unpack('<4096I',data))+'\n'
 trials=[]
 cases=[('clean64',{'EXPECT_COMMANDS':322},files(recovery.record(1),recovery.record(2)),66),('high-carry64',{'EXPECT_COMMANDS':322},files(recovery.record(0xfffffffe),recovery.record(0xffffffff)),0x10000003f)]
 for name,params,initial,g in cases:
  folder=root/name;folder.mkdir(exist_ok=True);(folder/'firmware.hex').write_text(firmware);(folder/'initial-card.hex').write_text('\n'.join(f'{w:08x}' for w in struct.unpack('>4096I',b''.join(initial)))+'\n')
  cmd=['iverilog','-g2012','-s','tb_tau_cpu_save_stress','-o',str(folder/'run.vvp')]
  for key,value in params.items():cmd+=['-Ptb_tau_cpu_save_stress.'+key+'='+str(value)]
  cmd += [str(ROOT/sources[3]),str(ROOT/'references/tau-7b98a2e/tgt_cmd.v'),str(ROOT/'references/tau-7b98a2e/VexRiscv_Full.v')]
  run=subprocess.run(cmd,capture_output=True,text=True);(folder/'compile.log').write_text(run.stdout+run.stderr)
  if run.returncode:raise RuntimeError(run.stderr)
  run=subprocess.run(['vvp','run.vvp'],cwd=folder,capture_output=True,text=True);log=folder/'run.log';log.write_text(run.stdout+run.stderr)
  if run.returncode or 'PASS actual Tau CPU save prototype' not in run.stdout:raise RuntimeError(name+'\n'+run.stdout+run.stderr)
  words=[int(x,16) for x in re.sub(r'//[^\n]*','',(folder/'final-card.hex').read_text()).split()];b=struct.pack('>4096I',*words);pair=(b[:8192],b[8192:])
  want=files(recovery.record(g-1),recovery.record(g))
  if pair!=want or not recovery.verify_files(*pair,g,expect_generated=True)['pass']:raise ValueError('Full CPU64 output differs from independent oracle')
  trials.append({'trial':name,'pass':True,'commands':322,'committed_saves':64,'expected_generation':g,'log_sha256':sha(log),'final_sha256':[hashlib.sha256(x).hexdigest() for x in pair]});print(name+' PASS',flush=True)
 d={'pass':True,'trials':trials,'source_hashes':{name:sha(ROOT/name) for name in sources},'runner_sha256':sha(Path(__file__)),'firmware_sha256':sha(root/'firmware.bin'),'scope':'Two full 64-save actual pinned-CPU campaigns, 322 modeled APF commands each, sequence wrap and 32-bit generation carry. Full received-index mask contract and uncached word staging; independent exact final files/guards/CRC. Synthetic transport only, no physical persistence, real serialization or playback qualification.'}
 (ROOT/'work/evidence/tau-cpu-save-stress-simulation.json').write_text(json.dumps(d,indent=2)+'\n')
if __name__=='__main__':main()
