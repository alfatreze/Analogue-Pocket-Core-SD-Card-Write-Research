#!/usr/bin/env python3
"""Additional frozen-B006 RTL checks: all byte prefix cuts and seeded damage."""
import hashlib,json,random,time
from pathlib import Path
import test_recovery_guarded as base
recovery=base.recovery;ROOT=base.ROOT
def main():
 manifest=json.loads((ROOT/'work/build/guarded06-manifest.json').read_text())
 rtl=ROOT/'rtl/lab_recovery_guarded.sv'
 if hashlib.sha256(rtl.read_bytes()).hexdigest()!=manifest['files']['src/fpga/core/lab_recovery_guarded.sv']:raise ValueError('Frozen RTL mismatch')
 report=ROOT/'work/evidence/b006-adversarial-simulation.json'
 if report.exists():raise ValueError('Preserve existing adversarial evidence; no silent rerun')
 trials=[];rng=random.Random(0x53445706);started=time.time()
 def run(name,seed,mode,status,g):
  out=base.rtl_run(name,seed,MODE=mode,EXPECT_STATUS=status,EXPECT_GEN=g)
  if out!=seed:raise ValueError('Read/refusal trial changed simulated files')
  trials.append({'trial':name,'pass':True,'expected_generation':g,'expected_status':status})
  report.write_text(json.dumps({'state':'running','pass':False,'seed':0x53445706,'trials':trials,'scope':'RTL simulation only; no physical interruption evidence'},indent=2)+'\n')
 try:
  for cut in range(513):
   torn=recovery.record(3)[:cut]+recovery.record(1)[cut:]
   run('extra-prefix-byte-'+str(cut),base.files(torn,recovery.record(2)),1,4,3 if recovery.validate(torn)['valid'] and recovery.validate(torn)['generation']==3 else 2)
  for slot in range(2):
   for bit in rng.sample(range(4096),64):
    a=[bytearray(recovery.record(1)),bytearray(recovery.record(2))];a[slot][bit//8]^=1<<(bit%8)
    run('extra-record-slot'+str(slot)+'-bit'+str(bit),base.files(*a),1,4,2 if slot==0 else 1)
  for slot in range(2):
   offsets=list(range(512))+list(range(1024,8192))
   for offset in rng.sample(offsets,8):
    a=list(base.files(recovery.record(1),recovery.record(2)));a[slot]=bytearray(a[slot]);a[slot][offset]^=rng.randrange(1,256)
    run('extra-guard-slot'+str(slot)+'-byte'+str(offset),tuple(bytes(x) for x in a),0,5,0)
 except Exception as e:
  report.write_text(json.dumps({'state':'failed','pass':False,'trials':trials,'error':str(e)},indent=2)+'\n');raise
 d={'state':'completed','pass':True,'build':'B006','seed':0x53445706,'elapsed_seconds':time.time()-started,'trial_count':len(trials),'trials':trials,'rtl_sha256':hashlib.sha256(rtl.read_bytes()).hexdigest(),'testbench_sha256':hashlib.sha256((ROOT/'sim/tb_recovery_guarded.sv').read_bytes()).hexdigest(),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'All 513 byte-prefix replacements of inactive generation 1 with generation 3 while generation 2 stays valid; 128 seeded distinct single-bit corruptions across both records; 16 extra guard corruptions. RTL simulation only, not physical SD interruption/persistence.'}
 report.write_text(json.dumps(d,indent=2)+'\n');print('EXTRA CAMPAIGN PASS',len(trials),flush=True)
if __name__=='__main__':main()
