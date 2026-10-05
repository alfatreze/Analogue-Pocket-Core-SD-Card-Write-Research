#!/usr/bin/env python3
"""Execute exact pinned Tau CPU on isolated command firmware and modeled APF."""
import argparse,subprocess,struct,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--toolchain',type=Path,default=ROOT/'../tau-alpha/toolchain/xpack-riscv-none-elf-gcc-15.2.0-1/bin');args=parser.parse_args();tc=args.toolchain.resolve()
 folder=ROOT/'work/sim/tau-cpu';folder.mkdir(parents=True,exist_ok=True)
 ref=json.loads((ROOT/'work/evidence/tau-cpu-reference.json').read_text())
 for name,original in (('VexRiscv_Full.v','src/fpga/rtl/VexRiscv_Full.v'),('tgt_cmd.v','src/fpga/core/tgt_cmd.v')):
  if sha(ROOT/'references/tau-7b98a2e'/name)!=ref['files'][original]:raise ValueError('Exact pinned Tau source changed')
 sources=('sim/tau_cpu/link.ld','sim/tau_cpu/start.S','sim/tau_cpu/main.c','sim/tb_tau_cpu_card.sv')
 command=[str(tc/'riscv-none-elf-gcc'),'-march=rv32im','-mabi=ilp32','-mno-relax','-O2','-ffreestanding','-nostdlib','-nostartfiles','-Wl,--no-warn-rwx-segments','-T',str(ROOT/sources[0]),str(ROOT/sources[1]),str(ROOT/sources[2]),'-o',str(folder/'firmware.elf')]
 run=subprocess.run(command,capture_output=True,text=True);(folder/'firmware-build.log').write_text(run.stdout+run.stderr)
 if run.returncode:raise RuntimeError(run.stderr)
 subprocess.run([str(tc/'riscv-none-elf-objcopy'),'-O','binary',str(folder/'firmware.elf'),str(folder/'firmware.bin')],check=True)
 data=(folder/'firmware.bin').read_bytes()
 if len(data)>16384:raise ValueError('Firmware exceeds isolated ROM')
 data+=bytes(16384-len(data));(folder/'firmware.hex').write_text('\n'.join(f'{w:08x}' for w in struct.unpack('<4096I',data))+'\n')
 trials=[]
 for label,half,bus,delay in (('60MHz',8.333,0,100),('50MHz',10,0,100),('74MHz',6.734,0,100),('90MHz',5.556,0,100),('60MHz-stalled',8.333,3,1000)):
  exe=folder/(label+'.vvp')
  cmd=['iverilog','-g2012','-s','tb_tau_cpu_card','-Ptb_tau_cpu_card.CPU_HALF_NS='+str(half),'-Ptb_tau_cpu_card.BUS_DELAY='+str(bus),'-Ptb_tau_cpu_card.APF_DELAY='+str(delay),'-o',str(exe),str(ROOT/sources[3]),str(ROOT/'references/tau-7b98a2e/tgt_cmd.v'),str(ROOT/'references/tau-7b98a2e/VexRiscv_Full.v')]
  run=subprocess.run(cmd,capture_output=True,text=True);(folder/(label+'-compile.log')).write_text(run.stdout+run.stderr)
  if run.returncode:raise RuntimeError(run.stderr)
  run=subprocess.run(['vvp',exe.name],cwd=folder,capture_output=True,text=True);log=folder/(label+'.log');log.write_text(run.stdout+run.stderr)
  if run.returncode or 'PASS actual Tau CPU' not in run.stdout:raise RuntimeError('CPU trial failed '+label+'\n'+run.stdout+run.stderr)
  trials.append({'trial':label,'commands':300,'pass':True,'bus_wait_cycles':bus,'modeled_APF_delay_cycles':delay,'log_sha256':sha(log)});print(label+' PASS',flush=True)
 d={'pass':True,'source_revision':ref['source_revision'],'cpu_sha256':ref['files']['src/fpga/rtl/VexRiscv_Full.v'],'trials':trials,'total_commands':1500,'source_hashes':{name:sha(ROOT/name) for name in sources},'runner_sha256':sha(Path(__file__)),'firmware_sha256':sha(folder/'firmware.bin'),'compiler_version':subprocess.check_output([str(tc/'riscv-none-elf-gcc'),'--version'],text=True).splitlines()[0],'scope':'Exact generated VexRiscv executes RV32IM firmware through instruction cache and uncached MMIO on isolated modeled buses/APF. 300 busy extra GO attempts rejected per trial, all selections/errors, sequence wrap and stalled buses. No physical write, payload publication, APF serialization, full Tau SoC/playback or reset qualification.'}
 (ROOT/'work/evidence/tau-cpu-command-simulation.json').write_text(json.dumps(d,indent=2)+'\n')
if __name__=='__main__':main()
