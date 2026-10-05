#!/usr/bin/env python3
"""Additional exact CPU 64-save recovery states, using qualified synthetic transport."""
import hashlib,json,re,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'sim'))
import recovery
from test_recovery_guarded import files
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 q=json.loads((ROOT/'work/evidence/tau-cpu-stress-fast-qualification.json').read_text());base=ROOT/'work/sim/tau-cpu-save-stress-r2';exe=base/'verilated/Vtb_tau_cpu_save_stress'
 if sha(exe)!=q['executable_sha256']:raise ValueError('Qualified executable changed')
 for path,h in q['sources'].items():
  if sha(ROOT/path)!=h:raise ValueError('Qualified source changed')
 if sha(base/'firmware.bin')!=q['firmware_sha256']:raise ValueError('Qualified firmware changed')
 ref=json.loads((ROOT/'work/evidence/tau-cpu-reference.json').read_text())
 for filename,path in [('VexRiscv_Full.v','src/fpga/rtl/VexRiscv_Full.v'),('tgt_cmd.v','src/fpga/core/tgt_cmd.v')]:
  if sha(ROOT/'references/tau-7b98a2e'/filename)!=ref['files'][path]:raise ValueError('Pinned Tau reference changed')
 root=ROOT/'work/sim/tau-cpu-save-states';root.mkdir(exist_ok=False)
 blank=bytes([0xa5])*512;corrupt=bytearray(recovery.record(2));corrupt[200]^=1
 cases=[('blank64',files(blank,blank)),('a-newest64',files(recovery.record(2),recovery.record(1))),('corrupt-newest64',files(recovery.record(1),bytes(corrupt))),('only-b64',files(blank,recovery.record(2))),('identical-tie64',files(recovery.record(7),recovery.record(7))),('high-word64',files(recovery.record(0x12345678abcdef00),recovery.record(0x12345678abcdeeff)))]
 trials=[]
 for name,initial in cases:
  folder=root/name;folder.mkdir();(folder/'firmware.hex').write_bytes((base/'clean64/firmware.hex').read_bytes());(folder/'initial-card.hex').write_text('\n'.join(f'{w:08x}' for w in struct.unpack('>4096I',b''.join(initial)))+'\n')
  expected=[bytearray(x) for x in initial]
  for i in range(64):
   dest,g=recovery.next_destination(bytes(expected[0][512:1024]),bytes(expected[1][512:1024]));expected[dest][512:1024]=recovery.record(g)
  run=subprocess.run([str(exe)],cwd=folder,capture_output=True,text=True);log=folder/'run.log';log.write_text(run.stdout+run.stderr)
  if run.returncode or 'commands=322 reads=66 writes=256 exit=00000000 omitted=0' not in run.stdout:raise ValueError(name+' CPU did not finish correctly; inspect private log')
  words=[int(x,16) for x in re.sub(r'//[^\n]*','',(folder/'final-card.hex').read_text()).split()];actual=struct.pack('>4096I',*words);pair=(actual[:8192],actual[8192:])
  if pair!=tuple(bytes(x) for x in expected) or not recovery.verify_files(*pair,g,expect_generated=True)['pass']:raise ValueError(name+' differs from whole-file independent oracle')
  trials.append({'trial':name,'pass':True,'committed_saves':64,'commands':322,'generation':g,'initial_sha256':[hashlib.sha256(x).hexdigest() for x in initial],'final_sha256':[hashlib.sha256(x).hexdigest() for x in pair],'log_sha256':sha(log)});print(name+' PASS',flush=True)
 report={'pass':True,'trials':trials,'qualified_executable_sha256':q['executable_sha256'],'qualification_sha256':sha(ROOT/'work/evidence/tau-cpu-stress-fast-qualification.json'),'runner_sha256':sha(Path(__file__)),'scope':'Six additional full 64-save actual pinned CPU profiles, exact independent final bytes/guards/CRC/generation. Synthetic word transport; no card persistence, real serialization, production CDC, MMIO compatibility or reset qualification.'}
 (ROOT/'work/evidence/tau-cpu-save-states-simulation.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
