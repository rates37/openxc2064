import pytest
from openxc2064.synthesis.rtl_nodes import Netlist, Net, LogicGate, DFF, Input, Constant
from openxc2064.simulator import RTLSimulator


def test_simple_wire() -> None:
    netlist = Netlist("simple_wire")
    # create input/output nets:
    inp = netlist.create_net("inp")
    out = netlist.create_net("out")
    netlist.inputs = [inp]
    netlist.outputs = [out]

    netlist.add_input("inp", inp)
    netlist.add_logic("BUF", [inp], [out])

    simulator = RTLSimulator(netlist)
    simulator.set("inp", 1)
    simulator.step()

    assert simulator.get("out") == 1

    simulator.set("inp", 0)
    simulator.step()

    assert simulator.get("out") == 0


def test_multi_bit_wire() -> None:
    netlist = Netlist("multi_bit_wire")

    inp = netlist.create_net("inp", width=3)
    out = netlist.create_net("out", width=3)

    netlist.inputs = [inp]
    netlist.outputs = [out]

    netlist.add_input("inp", inp)
    netlist.add_logic("BUF", [inp], [out])

    sim = RTLSimulator(netlist)
    sim.set("inp", 5)
    sim.step()

    assert sim.get("out") == 5

    sim.set("inp", 1)
    sim.step()

    assert sim.get("out") == 1


def test_constant_value() -> None:
    netlist = Netlist("constant_test")

    const_net = netlist.create_net("const_val", 8)
    out = netlist.create_net("out", 8)

    netlist.outputs = [out]

    netlist.add_const(42, const_net)
    netlist.add_logic("BUF", [const_net], [out])

    sim = RTLSimulator(netlist)
    sim.step()

    assert sim.get("out") == 42


def test_multiple_inputs_outputs() -> None:
    netlist = Netlist("multi_io")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    sum_out = netlist.create_net("sum", 8)
    diff_out = netlist.create_net("diff", 8)

    netlist.inputs = [a, b]
    netlist.outputs = [sum_out, diff_out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("ADD", [a, b], [sum_out])
    netlist.add_logic("SUB", [a, b], [diff_out])

    sim = RTLSimulator(netlist)
    sim.set("a", 10)
    sim.set("b", 3)
    sim.step()

    assert sim.get("sum") == 13
    assert sim.get("diff") == 7

    sim.set("a", 67)
    sim.set("b", 41)
    # check outputs only update after stepping simulator:
    assert sim.get("sum") == 13
    assert sim.get("diff") == 7
    sim.step()
    assert sim.get("sum") == 108
    assert sim.get("diff") == 26
