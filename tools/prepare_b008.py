#!/usr/bin/env python3
"""Freeze B008R1 sources/package metadata after exact SoC and native UI review."""
import hashlib,json,shutil
from pathlib import Path
from prepare import validate_vendor,manifest,json_write
from b008_firmware import build as firmware_build
ROOT=Path(__file__).resolve().parents[1];BUILD='cpu08r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 pins=validate_vendor()
 simulation=json.loads((ROOT/'work/evidence/b008-soc-simulation.json').read_text())
 if not simulation['pass'] or len(simulation['trials'])!=19:raise RuntimeError('Complete SoC trial gate missing')
 for name,expected in simulation['source_hashes'].items():
  if sha(ROOT/name)!=expected:raise RuntimeError('Tested SoC source changed: '+name)
 review=json.loads((ROOT/'work/evidence/b008r1-display-review.json').read_text())
 if not review['pass'] or sha(ROOT/'rtl/b008_video.sv')!=review['video_sha256']:raise RuntimeError('Native UI review missing/changed')
 for name,expected in review['captures'].items():
  if sha(ROOT/name)!=expected:raise RuntimeError('Reviewed capture changed')
 stage=ROOT/'work/build'/BUILD;package=ROOT/'work/packages'/BUILD
 if stage.exists() or package.exists():raise RuntimeError('Immutable stage already exists; choose a new revision')
 source=ROOT/'vendor/core-template'
 shutil.copytree(source/'src',stage/'src',ignore=shutil.ignore_patterns('db','incremental_db','output_files'))
 core=stage/'src/fpga/core'
 mapping={'rtl/b008_core_top.v':'core_top.v','rtl/core_bridge_cmd.v':'core_bridge_cmd.v','rtl/b008_soc.sv':'b008_soc.sv','rtl/b008_mailbox.sv':'b008_mailbox.sv','rtl/b008_video.sv':'b008_video.sv','rtl/lab_powercut.sv':'lab_powercut.sv','rtl/b008_cpu_pll.v':'b008_cpu_pll.v','references/tau-7b98a2e/VexRiscv_Full.v':'VexRiscv_Full.v','rtl/b008_constraints.sdc':'core_constraints.sdc'}
 for name,target in mapping.items():shutil.copy2(ROOT/name,core/target)
 fw=firmware_build(stage/'firmware')
 observed={t['firmware_sha256'] for t in simulation['trials'] if t['interactive_hardware_firmware']}
 if observed!={fw['sha256']}:raise RuntimeError('Staged interactive firmware differs from tested bytes')
 shutil.copy2(stage/'firmware/firmware.hex',core/'b008_firmware.hex')
 shutil.copytree(ROOT/'firmware/b008',stage/'firmware/source')
 qsf=stage/'src/fpga/ap_core.qsf'
 lines=[line for line in qsf.read_text().splitlines() if not any(x in line for x in ('SIGNALTAP','SLD_FILE','core/core_constraints.sdc'))]
 lines+=['set_global_assignment -name ENABLE_SIGNALTAP OFF','set_global_assignment -name SEARCH_PATH core','set_global_assignment -name NUM_PARALLEL_PROCESSORS 2','set_global_assignment -name SEED 1','set_global_assignment -name ALLOW_POWER_UP_DONT_CARE OFF']
 for name in ('b008_soc.sv','b008_mailbox.sv','b008_video.sv','lab_powercut.sv'):lines.append('set_global_assignment -name SYSTEMVERILOG_FILE core/'+name)
 for name in ('VexRiscv_Full.v','b008_cpu_pll.v'):lines.append('set_global_assignment -name VERILOG_FILE core/'+name)
 # Keep synchronizer chain placement/identification explicit, per Quartus setting.
 for pattern in ('*cpu_soc*|*mailbox*|ack1','*cpu_soc*|*mailbox*|req1','*cpu_soc*|*mailbox*|rst1','*cpu_soc*|keys1*','*cpu_soc*|snap1','*cpu_release*'):
  lines.append('set_instance_assignment -name SYNCHRONIZER_IDENTIFICATION "FORCED IF ASYNCHRONOUS" -to "'+pattern+'"')
 qsf.write_text('\n'.join(lines)+'\n')
 provenance={'kind':'B008R1 exact CPU supervisor plus unchanged B007 engine; immutable candidate, no fit/hardware claim','template_commit':pins['core-template']['commit'],'seed':1,'source_mapping':{name:{'staged':'src/fpga/core/'+target,'sha256':sha(ROOT/name)} for name,target in mapping.items()},'firmware':fw,'soc_simulation_sha256':sha(ROOT/'work/evidence/b008-soc-simulation.json'),'native_display_review_sha256':sha(ROOT/'work/evidence/b008r1-display-review.json')}
 manifest(stage,provenance)
 dest=package/'Cores/alfatreze.CARDWRITE02';dest.mkdir(parents=True)
 for name in ('core','data','interact','input','video','audio','variants'):
  value=json.loads((source/(name+'.json')).read_text())
  if name=='core':value['core']['metadata'].update(platform_ids=['cardwrite'],shortname='CARDWRITE02',author='alfatreze',description='SD Write Research B008R1 - CPU engine integration',version='0.8.1',date_release='2026-10-06',url='https://github.com/alfatreze/Analogue-Pocket-Core-SD-Card-Write-Research')
  if name=='data':value['data']['data_slots']=[dict(name='B008 CPU scratch',id='0x27',required=False,parameters=2,deferload=True,filename='cpu-b008.bin')]
  if name=='input':value['input']['controllers']=[dict(type='default',mappings=[dict(id=0,name='CPU start writes',key='pad_btn_a'),dict(id=1,name='CPU cold read / stop',key='pad_btn_b'),dict(id=2,name='Reset CPU; finish active command',key='pad_btn_x')])]
  json_write(dest/(name+'.json'),value)
 (dest/'info.txt').write_text('SD Write Research B008R1\nExact pinned VexRiscv supervises unchanged B007 engine.\nB: cold read before any write. A: start writes.\nB during writes: stop after current target completion.\nX: reset CPU only; engine keeps transfer ownership.\nNew preallocated cpu-b008.bin; preserve B007 scratch and prior saves.\nObserve SDW8 engine / CPU8 firmware snapshots before Quit.\nStop cleanly, power off, verify whole file on host.\nTimeout/fault: no retry; reviewed reconfiguration required.\n')
 # Asset is a new research output, never a reset/overwrite of B007's scratch.
 from b007_oracle import image
 asset=package/'Assets/cardwrite/alfatreze.CARDWRITE02/cpu-b008.bin';asset.parent.mkdir(parents=True);asset.write_bytes(image(0))
 manifest(package,{'kind':'B008R1 metadata/fixture only; no bitstream; NOT INSTALLABLE','compile_source_manifest_sha256':sha(stage.parent/(BUILD+'-manifest.json'))})
 print('Frozen '+str(stage));print('Prepared unqualified package '+str(package))
if __name__=='__main__':main()
