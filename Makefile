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
	$(PYTHON) sim/adapt_spi.py
	$(IVERILOG) -g2012 -I rtl -s tb_spi -o work/sim/spi.vvp sim/tb_spi.sv rtl/lab_probe.sv $(TEMPLATE)/apf/common.v work/sim/io_bridge_peripheral_icarus.v
	cd work/sim && $(VVP) spi.vvp
	$(PYTHON) sim/test_lab.py
	$(IVERILOG) -g2012 -I rtl -s core_top -o work/sim/top.vvp rtl/core_top.v rtl/lab_probe.sv rtl/lab_video.sv rtl/core_bridge_cmd.v $(TEMPLATE)/apf/common.v sim/vendor_models.v

.PHONY: test-batch
test-batch:
	mkdir -p work/sim/batch
	$(IVERILOG) -g2012 -I rtl -s tb_batch -o work/sim/batch/write.vvp sim/tb_batch.sv rtl/lab_batch.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/batch && $(VVP) write.vvp
	$(PYTHON) sim/test_batch.py
	$(IVERILOG) -g2012 -I rtl -s tb_batch -Ptb_batch.COLD=1 -o work/sim/batch/cold.vvp sim/tb_batch.sv rtl/lab_batch.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/batch && $(VVP) cold.vvp
	for mode in 1 2 3 4 6 7 8; do $(IVERILOG) -g2012 -I rtl -s tb_batch -Ptb_batch.INJECT=$$mode -o work/sim/batch/fault.vvp sim/tb_batch.sv rtl/lab_batch.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v && (cd work/sim/batch && $(VVP) fault.vvp) || exit 1; done

	$(IVERILOG) -g2012 -I rtl -s tb_batch -Ptb_batch.COMMAND=1 -o work/sim/batch/command.vvp sim/tb_batch.sv rtl/lab_batch.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/batch && $(VVP) command.vvp
	$(PYTHON) sim/adapt_spi.py
	$(IVERILOG) -g2012 -I rtl -s tb_batch_spi -o work/sim/batch/spi.vvp sim/tb_batch_spi.sv rtl/lab_batch.sv $(TEMPLATE)/apf/common.v work/sim/io_bridge_peripheral_icarus.v
	cd work/sim/batch && $(VVP) spi.vvp
	$(PYTHON) sim/test_batch.py

	$(IVERILOG) -g2012 -I rtl -s tb_batch -Ptb_batch.JTAG=1 -o work/sim/batch/jtag.vvp sim/tb_batch.sv rtl/lab_batch.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/batch && $(VVP) jtag.vvp
	$(IVERILOG) -g2012 -I rtl -s tb_batch -Ptb_batch.COLD=1 -Ptb_batch.INJECT=5 -o work/sim/batch/empty-cold.vvp sim/tb_batch.sv rtl/lab_batch.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/batch && $(VVP) empty-cold.vvp
	$(PYTHON) sim/test_update.py
	$(PYTHON) sim/test_jtag.py

.PHONY: test-stress
test-stress:
	mkdir -p work/sim/stress/full work/sim/stress/command work/sim/stress/faults work/sim/stress/spi
	$(IVERILOG) -g2012 -I rtl -s tb_stress -o work/sim/stress/full/write.vvp sim/tb_stress.sv rtl/lab_stress.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/stress/full && $(VVP) write.vvp
	$(IVERILOG) -g2012 -I rtl -s tb_stress -Ptb_stress.COLD=1 -o work/sim/stress/full/cold.vvp sim/tb_stress.sv rtl/lab_stress.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/stress/full && $(VVP) cold.vvp
	$(IVERILOG) -g2012 -I rtl -s tb_stress -Ptb_stress.TOTAL_PAIRS=64 -Ptb_stress.COMMAND=1 -o work/sim/stress/command/command.vvp sim/tb_stress.sv rtl/lab_stress.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/stress/command && $(VVP) command.vvp
	for mode in 1 2 3 4 6; do $(IVERILOG) -g2012 -I rtl -s tb_stress -Ptb_stress.TOTAL_PAIRS=64 -Ptb_stress.INJECT=$$mode -o work/sim/stress/faults/fault.vvp sim/tb_stress.sv rtl/lab_stress.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v && (cd work/sim/stress/faults && $(VVP) fault.vvp) || exit 1; done
	$(IVERILOG) -g2012 -I rtl -s tb_stress -Ptb_stress.TOTAL_PAIRS=64 -Ptb_stress.JTAG=1 -o work/sim/stress/command/jtag.vvp sim/tb_stress.sv rtl/lab_stress.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/stress/command && $(VVP) jtag.vvp
	$(IVERILOG) -g2012 -I rtl -s tb_stress -Ptb_stress.TOTAL_PAIRS=64 -Ptb_stress.COLD=1 -Ptb_stress.INJECT=5 -o work/sim/stress/faults/empty.vvp sim/tb_stress.sv rtl/lab_stress.sv rtl/core_bridge_cmd.v sim/vendor_models.v $(TEMPLATE)/apf/common.v
	cd work/sim/stress/faults && $(VVP) empty.vvp
	$(PYTHON) sim/adapt_spi.py
	$(IVERILOG) -g2012 -I rtl -s tb_stress_spi -o work/sim/stress/spi/spi.vvp sim/tb_stress_spi.sv rtl/lab_stress.sv $(TEMPLATE)/apf/common.v work/sim/io_bridge_peripheral_icarus.v
	cd work/sim/stress/spi && $(VVP) spi.vvp
	$(PYTHON) sim/test_stress.py
	$(PYTHON) sim/test_update_stress.py
	$(PYTHON) sim/test_jtag_stress.py
	$(IVERILOG) -g2012 -I rtl -DLAB_STRESS -DLAB_STRESS_REV=2 -s core_top -o work/sim/stress/top.vvp rtl/core_top.v rtl/lab_stress.sv rtl/lab_probe.sv rtl/lab_video.sv rtl/core_bridge_cmd.v $(TEMPLATE)/apf/common.v sim/vendor_models.v
