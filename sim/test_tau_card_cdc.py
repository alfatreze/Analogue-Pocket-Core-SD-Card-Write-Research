#!/usr/bin/env python3
"""Run isolated, hash-pinned Tau command crossing; never write the sibling."""
import subprocess,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 folder=ROOT/'work/sim/tau-cdc';folder.mkdir(parents=True,exist_ok=True)
 reference=json.loads((ROOT/'work/evidence/tau-cpu-reference.json').read_text())
 source=ROOT/'references/tau-7b98a2e/tgt_cmd.v';tb=ROOT/'sim/tb_tau_card_cdc.sv'
 if sha(source)!=reference['files']['src/fpga/core/tgt_cmd.v']:raise ValueError('Pinned Tau crossing changed')
 trials=[]
 for rate,half in ((60,8.333),(50,10),(74.25,6.734),(90,5.556)):
  name=str(rate);exe=folder/(name+'.vvp')
  cmd=['iverilog','-g2012','-s','tb_tau_card_cdc','-Ptb_tau_card_cdc.SYS_HALF_NS='+str(half),'-o',str(exe),str(tb),str(source)]
  run=subprocess.run(cmd,capture_output=True,text=True);(folder/(name+'-compile.log')).write_text(run.stdout+run.stderr)
  if run.returncode:raise RuntimeError(run.stderr)
  run=subprocess.run(['vvp',str(exe)],capture_output=True,text=True);log=folder/(name+'.log');log.write_text(run.stdout+run.stderr)
  if run.returncode or 'PASSED (0 failures)' not in run.stdout:raise RuntimeError('CDC failed '+name)
  trials.append({'nominal_cpu_MHz':rate,'commands':300,'pass':True,'log_sha256':sha(log)})
 d={'pass':True,'trials':trials,'source_sha256':sha(source),'testbench_sha256':sha(tb),'runner_sha256':sha(Path(__file__)),'scope':'Copied exact Tau crossing RTL; APF timing modeled. Includes sticky DONE, busy GO ignored, exact one-hot selections for all five commands, all 3-bit errors and 8-bit sequence wrap. No CPU execution, physical SD flush or independent-domain reset qualification.'}
 (ROOT/'work/evidence/tau-cdc-simulation.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
if __name__=='__main__':main()
