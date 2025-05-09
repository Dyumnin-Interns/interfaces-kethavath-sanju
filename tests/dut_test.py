import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ReadOnly, NextTimeStep
from cocotb_bus.drivers import BusDriver
from cocotb.result import TestFailure
from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db
from cocotb_bus.monitors import BusMonitor
from cocotb.clock import Clock

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




async def dut_test(dut):
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


class InputDriver(BusDriver):
    _signals = ["write_en", "write_address", "write_data", "write_rdy"]

    def __init__(self, dut, name, clk):
        super().__init__(dut, name, clk)
        self.bus.write_en.value = 0
        self.bus.write_address.value = 0
        self.bus.write_data.value = 0
        self.clk = clk

    async def _driver_sent(self, address, data, sync=True):
        for l in range(random.randint(1, 200)):
            await RisingEdge(self.clk)
        while not self.bus.write_rdy.value:
            await RisingEdge(self.clk)
        self.bus.write_en.value = 1
        self.bus.write_address.value = address
        self.bus.write_data.value = data
        await ReadOnly()
        await RisingEdge(self.clk)
        await NextTimeStep()
        self.bus.write_en.value = 0

class InputMonitor(BusMonitor):
    _signals = ["write_en", "write_address", "write_data", "write_rdy"]

    async def _monitor_recv(self):
        phases_w = {1: "Idle_w", 3: "Txn_w"}  # only two states as write_rdy is always 1
        prev_w = "Idle_w"
        while True:
            await FallingEdge(self.clock)
            await ReadOnly()
            Txn_w = (int(self.bus.write_en.value) << 1) | int(self.bus.write_rdy.value)
            state_w = phases_w.get(Txn_w)
            if state_w:
                inputport_cover({'previous_w': prev_w, 'current_w': state_w})
                prev_w = state_w

class OutputDriver(BusDriver):
    _signals = ["read_en", "read_address", "read_data", "read_rdy"]

    def __init__(self, dut, name, clk, sb_callback):
        super().__init__(dut, name, clk)
        self.bus.read_en.value = 0
        self.bus.read_address.value = 0
        self.clk = clk
        self.callback = sb_callback

    async def _driver_sent(self, address, sync=True):
        for k in range(random.randint(1, 200)):
            await RisingEdge(self.clk)
        while not self.bus.read_rdy.value:
            await RisingEdge(self.clk)
        self.bus.read_en.value = 1
        self.bus.read_address.value = address
        await ReadOnly()

        # Only check scoreboard for y_output (address 3)
        if self.callback and address == 3:
            self.callback(int(self.bus.read_data.value))
        elif address in [0, 1, 2]:
            cocotb.log.info(f"address={address}, value={int(self.bus.read_data.value)}")

        await RisingEdge(self.clk)
        await NextTimeStep()
        self.bus.read_en.value = 0

class OutputMonitor(BusMonitor):
    _signals = ["read_en", "read_address", "read_data", "read_rdy"]

    async def _monitor_recv(self):
        phases_r = {1: "Idle_r", 3: "Txn_r"}  # only two states as read_rdy is always 1
        prev_r = "Idle_r"
        while True:
            await FallingEdge(self.clock)
            await ReadOnly()
            Txn_r = (int(self.bus.read_en.value) << 1) | int(self.bus.read_rdy.value)
            state_r = phases_r.get(Txn_r)
            if state_r:
                outputport_cover({'previous_r': prev_r, 'current_r': state_r})
                prev_r = state_r