import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock


# @cocotb.test()
async def default_test(dut):
    dut.s_axi_aresetn.value = 1
    await Timer(1, unit="ns")

