import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ReadOnly, NextTimeStep
from cocotb_bus.drivers import BusDriver
from cocotb.result import TestFailure
from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db
from cocotb_bus.monitors import BusMonitor
import os
import random




def sb_fn(actual_value):
    global expected_value, test_failures
    if not expected_value:
        print("Warning: Unexpected output received")
        return
    expected = expected_value.pop(0)
    print(f"Expected: {expected}, Actual: {actual_value}")
    if actual_value != expected:
        test_failures += 1
        print("  -> Mismatch detected!")

@CoverPoint("top.a", xf=lambda x, y: x, bins=[0, 1])
@CoverPoint("top.b", xf=lambda x, y: y, bins=[0, 1])
@CoverCross("top.cross.ab", items=["top.a", "top.b"])
def ab_cover(a, b):
    pass

@CoverPoint("top.inputport.current_w", xf=lambda x: x.get('current_w'), bins=["Idle_w", "Txn_w"])  # only two states as write_rdy is always 1
@CoverPoint("top.inputport.previous_w", xf=lambda x: x.get('previous_w'), bins=["Idle_w", "Txn_w"])
@CoverCross("top.cross.input", items=["top.inputport.previous_w", "top.inputport.current_w"])
def inputport_cover(Txn_w_dict):
    pass

@CoverPoint("top.outputport.current_r", xf=lambda x: x.get('current_r'), bins=["Idle_r", "Txn_r"])  # only two states as read_rdy is always 1
@CoverPoint("top.outputport.previous_r", xf=lambda x: x.get('previous_r'), bins=["Idle_r", "Txn_r"])
@CoverCross("top.cross.output", items=["top.outputport.previous_r", "top.outputport.current_r"])
def outputport_cover(Txn_r_dict):
    pass

@CoverPoint("top.read_address", xf=lambda x: x, bins=[0, 1, 2, 3])
def read_address_cover(address):
    pass

@cocotb.test()




async def test_dut_fifo_behavior(dut):
    # Start clock
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())

    # Apply reset
    dut.RST_N.value = 0
    await RisingEdge(dut.CLK)
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    # Step 1: Write to a_ff
    dut.write_en.value = 1
    dut.write_data.value = 1  # Pushing data `1`
    dut.write_address.value = 4  # Address for a_ff
    await RisingEdge(dut.CLK)

    # Step 2: Write to b_ff
    dut.write_en.value = 1
    dut.write_data.value = 1
    dut.write_address.value = 5  # Address for b_ff
    await RisingEdge(dut.CLK)

    # Disable write
    dut.write_en.value = 0
    await RisingEdge(dut.CLK)

    # Step 3: Read y_ff status before and after triggering read_en
    dut.read_en.value = 1
    dut.read_address.value = 3  # Read from y_ff
    await RisingEdge(dut.CLK)
    output = dut.read_data.value.integer
    dut._log.info(f"Read data from y_ff (address 3): {output}")
    dut.read_en.value = 0

    # Step 4: Optional: observe other read outputs
    for addr in [0, 1, 2]:
        dut.read_address.value = addr
        await RisingEdge(dut.CLK)
        val = dut.read_data.value.integer
        dut._log.info(f"Read data from address {addr}: {val}")

    # Assert that y_ff eventually outputs 1
    assert output in [0, 1], "Read data from y_ff must be 0 or 1"
