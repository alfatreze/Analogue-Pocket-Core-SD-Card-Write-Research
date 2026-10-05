#!/usr/bin/env python3
"""B005 host oracle and real RTL/command/serial qualification campaign."""
from pathlib import Path
import sys,json,struct,subprocess,unittest,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));import recovery
class OracleTests(unittest.TestCase):
 def test_crc_and_roundtrip(self):
  import zlib
  self.assertEqual(zlib.crc32(b'123456789'),0xcbf43926)
  for g in (1,2,63,64,0xffffffff,0x100000000,recovery.MAX_GENERATION):
   self.assertEqual(recovery.validate(recovery.record(g))['generation'],g)
 def test_every_single_bit_damage(self):
  original=recovery.record(7)
  for bit in range(4096):
   data=bytearray(original);data[bit//8]^=1<<(bit%8);self.assertFalse(recovery.validate(data)['valid'])
 def test_header_semantics_even_with_valid_crc(self):
  for word,value in ((0,0),(1,0x20020),(2,513),(3,0),(4,0),(5,479),(6,1)):
   data=bytearray(recovery.record(1));struct.pack_into('>I',data,word*4,value)
   if word==3:continue # high half zero is allowed
   struct.pack_into('>I',data,28,recovery.checksum(data));self.assertFalse(recovery.validate(data)['valid'])
 def test_all_prefix_interruptions(self):
  # New inactive record cannot hide the valid generation in the other file.
  for old in (bytes([165])*512,recovery.record(1)):
   for cut in range(513):
    torn=recovery.record(3)[:cut]+old[cut:];r=recovery.recover(torn,recovery.record(2))
    self.assertEqual(r['generation'],3 if recovery.validate(torn)['valid'] and recovery.validate(torn)['generation']==3 else 2)
 def test_conflict_and_overflow(self):
  a=recovery.record(2);b=recovery.record(2,bytes([77])*480)
  self.assertEqual(recovery.recover(a,b)['reason'],'conflicting-equal-generation')
  self.assertEqual(recovery.recover(a,a)['selected'],0)
  with self.assertRaises(ValueError):recovery.next_destination(a,b)
  with self.assertRaises(ValueError):recovery.next_destination(recovery.record(recovery.MAX_GENERATION),bytes(512))
 def test_guards_size(self):
  a,b=files(recovery.record(1),recovery.record(2));self.assertTrue(recovery.verify_files(a,b,2)['pass'])
  self.assertFalse(recovery.verify_files(a[:-1],b)['pass'])
  a=bytearray(a);a[-1]^=1;self.assertFalse(recovery.verify_files(a,b)['pass'])
 def test_empty(self):
  self.assertEqual(recovery.recover(bytes(512),bytes(512))['reason'],'no-valid-save')

def files(a=None,b=None):
 result=[bytearray(recovery.fixture()),bytearray(recovery.fixture())]
 for data,record in zip(result,(a,b)):
  if record is not None:data[512:1024]=record
 return tuple(bytes(x) for x in result)

def rtl_run(name,initial,**params):
 folder=ROOT/'work/sim/recovery05'/name;folder.mkdir(parents=True,exist_ok=True)
 (folder/'initial.hex').write_text('\n'.join(f'{b:02x}' for b in b''.join(initial))+'\n')
 command=['iverilog','-g2012','-I',str(ROOT/'rtl'),'-s','tb_recovery','-o',str(folder/'run.vvp')]
 for k,v in params.items():command+=['-Ptb_recovery.'+k+'='+str(v)]
 command += [str(ROOT/p) for p in ('sim/tb_recovery.sv','rtl/lab_recovery.sv','rtl/core_bridge_cmd.v','sim/vendor_models.v','vendor/core-template/src/fpga/apf/common.v','work/sim/io_bridge_peripheral_icarus.v')]
 c=subprocess.run(command,capture_output=True,text=True);(folder/'compile.log').write_text(c.stdout+c.stderr)
 if c.returncode:raise RuntimeError(c.stderr)
 c=subprocess.run(['vvp','run.vvp'],cwd=folder,capture_output=True,text=True);(folder/'run.log').write_text(c.stdout+c.stderr);print(c.stdout.strip(),flush=True)
 if c.returncode:raise RuntimeError('RTL trial failed '+name)
 data=bytes(int(v,16) for v in (folder/'written.hex').read_text().split());assert len(data)==16384
 result=data[:8192],data[8192:]
 assert all(x[:512]==y[:512] and x[1024:]==y[1024:] for x,y in zip(initial,result))
 return result

def campaign():
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(OracleTests)
 if not unittest.TextTestRunner().run(suite).wasSuccessful():raise SystemExit(1)
 subprocess.run([sys.executable,str(ROOT/'sim/adapt_spi.py')],check=True)
 trials=[]
 blank=files();warm=rtl_run('warm64',blank);assert recovery.verify_files(*warm,64,expect_generated=True)['pass'];trials.append('warm64')
 cold=rtl_run('cold64',warm,MODE=1,EXPECT_GEN=64);assert cold==warm;trials.append('cold64')
 initial=files(recovery.record(1),recovery.record(2))
 for label,params,g in [('command',{'COMMAND':1,'COMMITS':64,'EXPECT_GEN':66},66),('spi',{'SPI':1,'COMMITS':64,'EXPECT_GEN':66},66),('single',{'MODE':2,'EXPECT_GEN':3},3),('high-generation',{'MODE':2,'EXPECT_GEN':"64'h100000000"},0x100000000)]:
  seed=files(recovery.record(0xffffffff),None) if label=='high-generation' else initial
  out=rtl_run(label,seed,**params);assert recovery.verify_files(*out,g,expect_generated=True)['pass'];trials.append(label)
 for point in range(4):
  torn=rtl_run('cut'+str(point),initial,MODE=2,HOLD=point,KILL=1)
  assert torn[1]==initial[1] and recovery.verify_files(*torn,2)['pass']
  cold=rtl_run('recover-cut'+str(point),torn,MODE=1,EXPECT_GEN=2);assert cold==torn
  out=rtl_run('resume'+str(point),initial,MODE=2,HOLD=point,EXPECT_GEN=3);assert recovery.verify_files(*out,3,expect_generated=True)['pass']
  trials+=['cut'+str(point),'recover-cut'+str(point),'resume'+str(point)]
 for inject in (1,2,3,4,5,6,7):
  out=rtl_run('fault'+str(inject),initial,COMMITS=2,INJECT=inject,EXPECT_STATUS=7 if inject in (4,7) else 5)
  assert out[1]==initial[1];trials.append('fault'+str(inject))
 corrupt=bytearray(recovery.record(2));corrupt[100]^=1
 cases=[('corrupt-newest',files(recovery.record(1),corrupt),4,1),('blank',blank,6,0),('equal-identical',files(recovery.record(2),recovery.record(2)),4,2),('equal-conflict',files(recovery.record(2),recovery.record(2,bytes([77])*480)),5,0),('overflow',files(recovery.record(recovery.MAX_GENERATION),None),5,0)]
 for word,value in ((0,0),(1,0x20020),(2,513),(4,0),(5,481),(6,1)):
  bad=bytearray(recovery.record(2));struct.pack_into('>I',bad,word*4,value);struct.pack_into('>I',bad,28,recovery.checksum(bad))
  cases.append(('header-invalid-'+str(word),files(recovery.record(1),bad),4,1))
 for label,seed,status,g in cases:
  out=rtl_run(label,seed,MODE=0 if label=='overflow' else 1,EXPECT_STATUS=status,EXPECT_GEN=g);assert out==seed;trials.append(label)
 summary={'pass':True,'build':'B005','rtl_trials':trials,'host_oracle_tests':7,'scope':'RTL, actual command module, pinned serial bridge and independent byte/record oracle. Simulated process restart/prefix cuts do not establish physical SD interruption behavior.'}
 out=ROOT/'work/evidence/b005-simulation-tests.json';out.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':campaign()
