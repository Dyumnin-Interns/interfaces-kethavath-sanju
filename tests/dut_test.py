import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ReadOnly, NextTimeStep
from cocotb.clock import Clock
from cocotb_bus.drivers import BusDriver
from cocotb_bus.monitors import BusMonitor
from cocotb.result import TestFailure
from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db

import os
import random

# Constants
WRITE_FIFO_ADDR_A = 4
WRITE_FIFO_ADDR_B = 5
READ_ADDR_Y_OUTPUT = 3
MAX_TEST_ITERATIONS = 50
FIFO_FILL_COUNT = 3

# Scoreboard and expected output
expected_values = []
test_failures = 0


def sb_fn(actual_value):
    global expected_values, test_failures
    if not expected_values:
        cocotb.log.warning("Unexpected output received")
        return

    expected = expected_values.pop(0)
    cocotb.log.info(f"Expected: {expected}, Actual: {actual_value}")
    if actual_value != expected:
        test_failures += 1
        cocotb.log.error("Mismatch detected!")


# --------------
# Coverage Points
# --------------

@CoverPoint("top.a", xf=lambda a, b: a, bins=[0, 1])
@CoverPoint("top.b", xf=lambda a, b: b, bins=[0, 1])
@CoverCross("top.cross.ab", items=["top.a", "top.b"])
def ab_cover(a, b):
    pass


@CoverPoint("top.inputport.current_w", xf=lambda x: x.get('current_w'), bins=["Idle_w", "Txn_w"])
@CoverPoint("top.inputport.previous_w", xf=lambda x: x.get('previous_w'), bins=["Idle_w", "Txn_w"])
@CoverCross("top.cross.input", items=["top.inputport.previous_w", "top.inputport.current_w"])
def inputport_cover(state_dict):
    pass


@CoverPoint("top.outputport.current_r", xf=lambda x: x.get('current_r'), bins=["Idle_r", "Txn_r"])
@CoverPoint("top.outputport.previous_r", xf=lambda x: x.get('previous_r'), bins=["Idle_r", "Txn_r"])
@CoverCross("top.cross.output", items=["top.outputport.previous_r", "top.outputport.current_r"])
def outputport_cover(state_dict):
    pass


@CoverPoint("top.read_address", xf=lambda addr: addr, bins=[0, 1, 2, 3])
def read_address_cover(addr):
    pass


# -------------
# Input Driver
# -------------

class InputDriver(BusDriver):
    _signals = ["write_en", "write_address", "write_data", "write_rdy"]

    def __init__(self, dut, name, clk):
        super().__init__(dut, name, clk)
        self.bus.write_en.value = 0
        self.bus.write_address.value = 0
        self.bus.write_data.value = 0
        self.clk = clk

    async def driver_send_write(self, address, data):
        # Random wait
        for _ in range(random.randint(1, 200)):
            await RisingEdge(self.clk)

        # Wait until ready
        while not self.bus.write_rdy.value:
            await RisingEdge(self.clk)

        self.bus.write_en.value = 1
        self.bus.write_address.value = address
        self.bus.write_data.value = data
        await ReadOnly()
        await RisingEdge(self.clk)
        await NextTimeStep()
        self.bus.write_en.value = 0


# ----------------
# Input Monitor
# ----------------

class InputMonitor(BusMonitor):
    _signals = ["write_en", "write_address", "write_data", "write_rdy"]

    async def _monitor_recv(self):
        phase_map = {1: "Idle_w", 3: "Txn_w"}
        prev_state = "Idle_w"
        while True:
            await FallingEdge(self.clock)
            await ReadOnly()
            txn = (int(self.bus.write_en.value) << 1) | int(self.bus.write_rdy.value)
            state = phase_map.get(txn)
            if state:
                inputport_cover({'previous_w': prev_state, 'current_w': state})
                prev_state = state


# ----------------
# Output Driver
# ----------------

class OutputDriver(BusDriver):
    _signals = ["read_en", "read_address", "read_data", "read_rdy"]

    def __init__(self, dut, name, clk, callback=None):
        super().__init__(dut, name, clk)
        self.bus.read_en.value = 0
        self.bus.read_address.value = 0
        self.callback = callback
        self.clk = clk

    async def driver_send_read(self, address):
        for _ in range(random.randint(1, 200)):
            await RisingEdge(self.clk)

        while not self.bus.read_rdy.value:
            await RisingEdge(self.clk)

        self.bus.read_en.value = 1
        self.bus.read_address.value = address
        await ReadOnly()

        if self.callback and address == READ_ADDR_Y_OUTPUT:
            self.callback(int(self.bus.read_data.value))
        else:
            cocotb.log.info(f"Read Addr={address}, Data={int(self.bus.read_data.value)}")

        await RisingEdge(self.clk)
        await NextTimeStep()
        self.bus.read_en.value = 0


# -----------------
# Output Monitor
# -----------------

class OutputMonitor(BusMonitor):
    _signals = ["read_en", "read_address", "read_data", "read_rdy"]

    async def _monitor_recv(self):
        phase_map = {1: "Idle_r", 3: "Txn_r"}
        prev_state = "Idle_r"
        while True:
            await FallingEdge(self.clock)
            await ReadOnly()
            txn = (int(self.bus.read_en.value) << 1) | int(self.bus.read_rdy.value)
            state = phase_map.get(txn)
            if state:
                outputport_cover({'previous_r': prev_state, 'current_r': state})
                prev_state = state


# -------------
# Main Test
# -------------

@cocotb.test()
async def dut_test(dut):
    global expected_values, test_failures

    # Start Clock
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())

    # Reset sequence
    dut.RST_N.value = 1
    await Timer(50, 'ns')
    dut.RST_N.value = 0
    await Timer(50, 'ns')
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    # Drivers and monitors
    w_drv = InputDriver(dut, "", dut.CLK)
    r_drv = OutputDriver(dut, "", dut.CLK, sb_fn)
    InputMonitor(dut, "", dut.CLK, callback=inputport_cover)
    OutputMonitor(dut, "", dut.CLK, callback=outputport_cover)

    # Initial read address coverage
    for addr in range(3):
        read_address_cover(addr)
        await r_drv.driver_send_read(addr)

    # Random stimulus and coverage
    for _ in range(MAX_TEST_ITERATIONS):
        a, b = random.randint(0, 1), random.randint(0, 1)
        expected_values.append(a | b)

        await w_drv.driver_send_write(WRITE_FIFO_ADDR_A, a)
        await w_drv.driver_send_write(WRITE_FIFO_ADDR_B, b)
        ab_cover(a, b)

        for _ in range(200):
            await RisingEdge(dut.CLK)
            await NextTimeStep()

        for addr in range(4):
            read_address_cover(addr)
            await r_drv.driver_send_read(addr)

    # Stimulus to fill FIFO A
    for _ in range(FIFO_FILL_COUNT):
        await w_drv.driver_send_write(WRITE_FIFO_ADDR_A, a)
    for addr in range(3):
        read_address_cover(addr)
        await r_drv.driver_send_read(addr)

    # Stimulus to fill FIFO B
    for _ in range(FIFO_FILL_COUNT):
        await w_drv.driver_send_write(WRITE_FIFO_ADDR_B, b)
    for addr in range(3):
        read_address_cover(addr)
        await r_drv.driver_send_read(addr)

    # Final coverage export
    coverage_db.report_coverage(cocotb.log.info, bins=True)
    output_file = os.path.join(os.getenv("RESULT_PATH", "./"), 'coverage.xml')
    coverage_db.export_to_xml(filename=output_file)

    # Final assertions
    if test_failures > 0:
        raise TestFailure(f"{test_failures} mismatches found")
    elif expected_values:
        raise TestFailure(f"{len(expected_values)} expected values not checked")
    cocotb.log.info("All test vectors passed successfully!")
