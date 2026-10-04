PYTHON ?= python3
IVERILOG ?= iverilog
VVP ?= vvp
TEMPLATE = vendor/core-template/src/fpga

.PHONY: prepare test
prepare:
	$(PYTHON) tools/prepare.py

test:
	mkdir -p work/sim
	$(IVERILOG) -g2012 -I rtl -s tb_probe -o work/sim/probe.vvp sim/tb_probe.sv sim/vendor_models.v rtl/lab_probe.sv rtl/core_bridge_cmd.v $(TEMPLATE)/apf/common.v
	cd work/sim && $(VVP) probe.vvp
	$(PYTHON) sim/test_lab.py
	$(IVERILOG) -g2012 -I rtl -s core_top -o work/sim/top.vvp rtl/core_top.v rtl/lab_probe.sv rtl/lab_video.sv rtl/core_bridge_cmd.v $(TEMPLATE)/apf/common.v sim/vendor_models.v
