SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/../hdl/dut1.v
VERILOG_SOURCES += $(PWD)/../hdl/FIFO1.v
VERILOG_SOURCES += $(PWD)/../hdl/FIFO2.v
VERILOG_SOURCES += $(PWD)/wrappers/dut_inst.v

interface:
	rm -rf sim_build/ results.xml  
	$(MAKE) sim MODULE=dut_test TOPLEVEL=dut_inst

include $(shell cocotb-config --makefiles)/Makefile.sim
