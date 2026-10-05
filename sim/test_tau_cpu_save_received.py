#!/usr/bin/env python3
"""CPU prototype receive-completeness remedy with modeled APF only."""
import argparse,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));import recovery
from test_recovery_guarded import files
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--toolchain',type=Path,default=ROOT/'../tau-alpha/toolchain/xpack-riscv-none-elf-gcc-15.2.0-1/bin');a=p.parse_args();tc=a.toolchain.resolve()
 root=ROOT/'work/sim/tau-cpu-save-received';root.mkdir(parents=True,exist_ok=True)
 sources=('sim/tau_cpu_save/link.ld','sim/tau_cpu_save/start.S','sim/tau_cpu_save/received.c','sim/tb_tau_cpu_save_received.sv')
 cmd=[str(tc/'riscv-none-elf-gcc'),'-march=rv32im','-mabi=ilp32','-mno-relax','-O2','-ffreestanding','-nostdlib','-nostartfiles','-Wl,--no-warn-rwx-segments','-T',str(ROOT/sources[0]),str(ROOT/sources[1]),str(ROOT/sources[2]),'-o',str(root/'firmware.elf')]
 run=subprocess.run(cmd,capture_output=True,text=True);(root/'build.log').write_text(run.stdout+run.stderr)
 if run.returncode:raise RuntimeError(run.stderr)
 subprocess.run([str(tc/'riscv-none-elf-objcopy'),'-O','binary',str(root/'firmware.elf'),str(root/'firmware.bin')],check=True)
 data=(root/'firmware.bin').read_bytes();data+=bytes(16384-len(data));firmware='\n'.join(f'{w:08x}' for w in struct.unpack('<4096I',data))+'\n'
 initial=files(recovery.record(1),recovery.record(2));trials=[]
 cases=[('clean-complete',{'EXPECT_COMMANDS':22},'complete'),('missing-stale-boot-guard',{'OMIT_GUARD_ON':1,'EXPECT_EXIT':0x23,'EXPECT_COMMANDS':1},'unchanged'),('missing-verify-guard',{'OMIT_GUARD_ON':7,'EXPECT_EXIT':0x23,'EXPECT_COMMANDS':7},'new-valid')]
 for name,params,expected in cases:
  folder=root/name;folder.mkdir(exist_ok=True);(folder/'firmware.hex').write_text(firmware);(folder/'initial-card.hex').write_text('\n'.join(f'{w:08x}' for w in struct.unpack('>4096I',b''.join(initial)))+'\n')
  cmd=['iverilog','-g2012','-s','tb_tau_cpu_save_received','-o',str(folder/'run.vvp')]
  for key,value in params.items():cmd+=['-Ptb_tau_cpu_save_received.'+key+'='+str(value)]
  cmd += [str(ROOT/sources[3]),str(ROOT/'references/tau-7b98a2e/tgt_cmd.v'),str(ROOT/'references/tau-7b98a2e/VexRiscv_Full.v')]
  run=subprocess.run(cmd,capture_output=True,text=True);(folder/'compile.log').write_text(run.stdout+run.stderr)
  if run.returncode:raise RuntimeError(run.stderr)
  run=subprocess.run(['vvp','run.vvp'],cwd=folder,capture_output=True,text=True);log=folder/'run.log';log.write_text(run.stdout+run.stderr)
  if run.returncode or 'PASS actual Tau CPU save prototype' not in run.stdout:raise RuntimeError(name+'\n'+run.stdout+run.stderr)
  words=[int(x,16) for x in re.sub(r'//[^\n]*','',(folder/'final-card.hex').read_text()).split()];b=struct.pack('>4096I',*words);pair=(b[:8192],b[8192:])
  if expected=='unchanged':want=initial
  elif expected=='prefix':
   a=bytearray(initial[0]);a[512:640]=recovery.record(3)[:128];want=(bytes(a),initial[1])
  elif expected=='new-valid':want=files(recovery.record(3),recovery.record(2))
  else:want=files(recovery.record(5),recovery.record(6))
  if pair!=want:raise ValueError('Unexpected mutation after injected outcome')
  if name.startswith('missing-') and 'omitted=1' not in run.stdout:raise ValueError('Missing-word diagnostic was not injected')
  trials.append({'trial':name,'expected_outcome_observed':True,'parameters':params,'final_expected_kind':expected,'log_sha256':sha(log),'final_sha256':[hashlib.sha256(x).hexdigest() for x in pair]});print(name+' observed '+expected,flush=True)
 d={'diagnostics_completed':True,'modeled_missing_word_rejected':True,'trials':trials,'source_hashes':{name:sha(ROOT/name) for name in sources},'runner_sha256':sha(Path(__file__)),'firmware_sha256':sha(root/'firmware.bin'),'scope':'Actual CPU prototype modeled APF errors stop after exact prefix/full write; timeout halts before another command. Reduced 500-poll diagnostic budget. CPU clears a receive lease before each read and requires 2048 distinct received-word bits before consuming RX. Missing stale guard words at boot/verification now stop; last valid file is preserved. The model adds the received-mask MMIO contract; a real B007 implementation must wire the actual B006 bridge-word tracking with safe CDC. No physical writes, APF transport or late completion after timeout qualification.'}
 (ROOT/'work/evidence/tau-cpu-save-received-simulation.json').write_text(json.dumps(d,indent=2)+'\n')
if __name__=='__main__':main()
