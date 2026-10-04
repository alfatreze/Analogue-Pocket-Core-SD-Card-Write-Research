"""Icarus syntax adaptation of pinned APF SPI; vendor and hardware builds untouched.

Split procedural inout-reg drivers into regs plus continuous assignments and move
forward declarations. No state machine or transaction timing is changed.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'vendor/core-template/src/fpga/apf/io_bridge_peripheral.v'
s=p.read_text()
declarations=[]
for line in s.splitlines():
    if line.strip().startswith('reg ') and any(f' {name};' in line for name in ('rx_latch_idx','rx_dat','rx_byte','rx_byte_done')):
        declarations.append(line)
        s=s.replace(line+'\n','')
extra='\n'.join(declarations)+'\n'
for name in ('phy_spiclk','phy_spimosi','phy_spimiso'):
    s=s.replace('inout   reg', 'inout   wire')
    s=s.replace(name+' <=',name+'_drive <=')
    extra+=f'reg {name}_drive;\nassign {name} = {name}_drive;\n'
s=s.replace('    wire reset_n_s;',extra+'    wire reset_n_s;')
out=ROOT/'work/sim/io_bridge_peripheral_icarus.v'
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(s)
