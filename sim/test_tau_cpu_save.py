#!/usr/bin/env python3
"""Actual Tau CPU generates B005-compatible records using modeled APF buffers."""
import argparse,subprocess,struct,json,hashlib,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));import recovery
from test_recovery_guarded import files
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--toolchain',type=Path,default=ROOT/'../tau-alpha/toolchain/xpack-riscv-none-elf-gcc-15.2.0-1/bin');a=p.parse_args();tc=a.toolchain.resolve()
 folder=ROOT/'work/sim/tau-cpu-save';folder.mkdir(parents=True,exist_ok=True)
 ref=json.loads((ROOT/'work/evidence/tau-cpu-reference.json').read_text())
 for name,original in (('VexRiscv_Full.v','src/fpga/rtl/VexRiscv_Full.v'),('tgt_cmd.v','src/fpga/core/tgt_cmd.v')):
  if sha(ROOT/'references/tau-7b98a2e'/name)!=ref['files'][original]:raise ValueError('Pinned CPU/crossing mismatch')
 sources=('sim/tau_cpu_save/link.ld','sim/tau_cpu_save/start.S','sim/tau_cpu_save/main.c','sim/tb_tau_cpu_save.sv')
 cmd=[str(tc/'riscv-none-elf-gcc'),'-march=rv32im','-mabi=ilp32','-mno-relax','-O2','-ffreestanding','-nostdlib','-nostartfiles','-Wl,--no-warn-rwx-segments','-T',str(ROOT/sources[0]),str(ROOT/sources[1]),str(ROOT/sources[2]),'-o',str(folder/'firmware.elf')]
 run=subprocess.run(cmd,capture_output=True,text=True);(folder/'firmware-build.log').write_text(run.stdout+run.stderr)
 if run.returncode:raise RuntimeError(run.stderr)
 subprocess.run([str(tc/'riscv-none-elf-objcopy'),'-O','binary',str(folder/'firmware.elf'),str(folder/'firmware.bin')],check=True)
 data=(folder/'firmware.bin').read_bytes()
 if len(data)>8192:raise ValueError('Firmware collides with data/stack')
 data+=bytes(16384-len(data));firmware='\n'.join(f'{w:08x}' for w in struct.unpack('<4096I',data))+'\n'
 trials=[]
 cases=[('clean',files(recovery.record(1),recovery.record(2)),0,22,6),('blank',files(),0,22,4),('high-carry',files(recovery.record(0xfffffffe),recovery.record(0xffffffff)),0,22,0x100000003)]
 damaged=bytearray(recovery.record(2));damaged[100]^=1;cases.append(('corrupt-newest',files(recovery.record(1),damaged),0,22,5))
 cases.append(('both-damaged',files(bytes([77])*512,bytes([88])*512),0x13,2,0))
 guard=list(files(recovery.record(1),recovery.record(2)));guard[0]=bytearray(guard[0]);guard[0][8191]^=1;cases.append(('guard-damage',tuple(bytes(x) for x in guard),0x25,1,0))
 cases.append(('equal-conflict',files(recovery.record(2),recovery.record(2,bytes([77])*480)),0x11,2,0))
 cases.append(('exhausted',files(recovery.record(recovery.MAX_GENERATION),None),0x12,2,0))
 for label,initial,code,commands,g in cases:
  out=folder/label;out.mkdir(exist_ok=True);(out/'firmware.hex').write_text(firmware)
  (out/'initial-card.hex').write_text('\n'.join(f'{w:08x}' for w in struct.unpack('>4096I',b''.join(initial)))+'\n')
  exe=out/'run.vvp';cmd=['iverilog','-g2012','-s','tb_tau_cpu_save','-Ptb_tau_cpu_save.EXPECT_EXIT='+str(code),'-Ptb_tau_cpu_save.EXPECT_COMMANDS='+str(commands),'-o',str(exe),str(ROOT/sources[3]),str(ROOT/'references/tau-7b98a2e/tgt_cmd.v'),str(ROOT/'references/tau-7b98a2e/VexRiscv_Full.v')]
  run=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(run.stdout+run.stderr)
  if run.returncode:raise RuntimeError(run.stderr)
  run=subprocess.run(['vvp',exe.name],cwd=out,capture_output=True,text=True);log=out/'run.log';log.write_text(run.stdout+run.stderr)
  if run.returncode or 'PASS actual Tau CPU save prototype' not in run.stdout:raise RuntimeError('CPU save trial failed '+label+'\n'+run.stdout+run.stderr)
  words=[int(w,16) for w in re.sub(r'//[^\n]*','',(out/'final-card.hex').read_text()).split()];final=struct.pack('>'+str(len(words))+'I',*words)
  if len(final)!=16384:raise ValueError('Wrong final file size')
  pair=final[:8192],final[8192:]
  if code:
   if pair!=initial:raise ValueError('Refusal changed files')
  else:
   check=recovery.verify_files(*pair,g,expect_generated=True)
   if not check['pass']:raise ValueError('CPU output differs from independent record oracle')
   if any(x[:512]!=y[:512] or x[1024:]!=y[1024:] for x,y in zip(initial,pair)):raise ValueError('CPU changed guard')
  trials.append({'trial':label,'pass':True,'commands':commands,'expected_exit':code,'expected_generation':g,'final_sha256':[hashlib.sha256(x).hexdigest() for x in pair],'log_sha256':sha(log)});print(label+' PASS',flush=True)
 d={'pass':True,'source_revision':ref['source_revision'],'trials':trials,'firmware_bytes':(folder/'firmware.bin').stat().st_size,'firmware_sha256':sha(folder/'firmware.bin'),'source_hashes':{name:sha(ROOT/name) for name in sources},'runner_sha256':sha(Path(__file__)),'scope':'Actual pinned VexRiscv/target crossing executes C save/recovery code; APF modeled as bounded big-endian word transfers with completed full reads and uncached word staging. Independent host oracle compares full files. No real bridge/serial transport, physical persistence, missing words, power loss, playback or standalone hardware qualification.'}
 (ROOT/'work/evidence/tau-cpu-save-simulation.json').write_text(json.dumps(d,indent=2)+'\n')
if __name__=='__main__':main()
