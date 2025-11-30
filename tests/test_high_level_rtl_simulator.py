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


def test_2_bit_overflow() -> None:
    netlist = Netlist("bit_width_2")

    inp = netlist.create_net("inp", 2)
    out = netlist.create_net("out", 2)

    netlist.inputs = [inp]
    netlist.outputs = [out]

    netlist.add_input("inp", inp)
    netlist.add_logic("BUF", [inp], [out])

    sim = RTLSimulator(netlist)
    sim.set("inp", 0)
    sim.step()
    assert sim.get("out") == 0

    sim.set("inp", 3)
    sim.step()
    assert sim.get("out") == 3

    sim.set("inp", 4)  # wrap to 0
    sim.step()
    assert sim.get("out") == 0

    sim.set("inp", 5)  # wrap to 1
    sim.step()
    assert sim.get("out") == 1

    sim.set("inp", 255)  # wrap to 3: 255 & 0b11 = 3
    sim.step()
    assert sim.get("out") == 3


def test_8_bit_overflow() -> None:
    netlist = Netlist("bit_width_8")

    inp = netlist.create_net("inp", 8)
    out = netlist.create_net("out", 8)

    netlist.inputs = [inp]
    netlist.outputs = [out]

    netlist.add_input("inp", inp)
    netlist.add_logic("BUF", [inp], [out])

    sim = RTLSimulator(netlist)

    sim.set("inp", 255)
    sim.step()
    assert sim.get("out") == 255

    sim.set("inp", 256)  # wrap to 0
    sim.step()
    assert sim.get("out") == 0

    sim.set("inp", 257)  # wrap to 1
    sim.step()
    assert sim.get("out") == 1


def test_addition_overflow() -> None:
    netlist = Netlist("add_overflow")

    a = netlist.create_net("a", 4)
    b = netlist.create_net("b", 4)
    sum_out = netlist.create_net("sum", 4)

    netlist.inputs = [a, b]
    netlist.outputs = [sum_out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("ADD", [a, b], [sum_out])

    sim = RTLSimulator(netlist)

    # 15 + 1 = 16, wraps to 0
    sim.set("a", 15)
    sim.set("b", 1)
    sim.step()
    assert sim.get("sum") == 0

    # 8 + 9 = 17, wraps to 1
    sim.set("a", 8)
    sim.set("b", 9)
    sim.step()
    assert sim.get("sum") == 1


def test_negative_values_twos_complement() -> None:
    netlist = Netlist("negative_test")

    inp = netlist.create_net("inp", 4)
    out = netlist.create_net("out", 4)

    netlist.inputs = [inp]
    netlist.outputs = [out]

    netlist.add_input("inp", inp)
    netlist.add_logic("BUF", [inp], [out])

    sim = RTLSimulator(netlist)

    # -1 stored as 15 (0xF) in 4-bit 2's complement
    sim.set("inp", -1)
    sim.step()
    assert sim.get("out") == 15
    assert sim.get_net_signed("out") == -1

    # -2 stored as 14
    sim.set("inp", -2)
    sim.step()
    assert sim.get("out") == 14
    assert sim.get_net_signed("out") == -2

    # -8 stored as 8
    sim.set("inp", -8)
    sim.step()
    assert sim.get("out") == 8
    assert sim.get_net_signed("out") == -8


def test_and_gate() -> None:
    netlist = Netlist("and_test")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    out = netlist.create_net("out", 8)

    netlist.inputs = [a, b]
    netlist.outputs = [out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("AND", [a, b], [out])

    sim = RTLSimulator(netlist)

    sim.set("a", 0b11110000)
    sim.set("b", 0b10101010)
    sim.step()
    assert sim.get("out") == 0b10100000

    sim.set("a", 0b11111111)
    sim.set("b", 0b00000000)
    sim.step()
    assert sim.get("out") == 0b00000000


def test_or_gate() -> None:
    netlist = Netlist("or_test")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    out = netlist.create_net("out", 8)

    netlist.inputs = [a, b]
    netlist.outputs = [out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("OR", [a, b], [out])

    sim = RTLSimulator(netlist)

    sim.set("a", 0b11110000)
    sim.set("b", 0b10101010)
    sim.step()
    assert sim.get("out") == 0b11111010

    sim.set("a", 0b11111111)
    sim.set("b", 0b00000000)
    sim.step()
    assert sim.get("out") == 0b11111111


def test_xor_gate() -> None:
    netlist = Netlist("xor_test")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    out = netlist.create_net("out", 8)

    netlist.inputs = [a, b]
    netlist.outputs = [out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("XOR", [a, b], [out])

    sim = RTLSimulator(netlist)

    sim.set("a", 0b11110000)
    sim.set("b", 0b10101010)
    sim.step()
    assert sim.get("out") == 0b01011010

    sim.set("a", 0b11111111)
    sim.set("b", 0b00000000)
    sim.step()
    assert sim.get("out") == 0b11111111

    sim.set("a", 0b00000000)
    sim.set("b", 0b00000000)
    sim.step()
    assert sim.get("out") == 0b00000000

    sim.set("a", 0b11111111)
    sim.set("b", 0b11111111)
    sim.step()
    assert sim.get("out") == 0b00000000


def test_not_gate() -> None:
    netlist = Netlist("not_test")

    inp = netlist.create_net("inp", 8)
    out = netlist.create_net("out", 8)

    netlist.inputs = [inp]
    netlist.outputs = [out]

    netlist.add_input("inp", inp)
    netlist.add_logic("NOT", [inp], [out])

    sim = RTLSimulator(netlist)

    sim.set("inp", 0b10101010)
    sim.step()
    assert sim.get("out") == 0b01010101


def test_equality() -> None:
    netlist = Netlist("eq_test")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    out = netlist.create_net("out", 1)

    netlist.inputs = [a, b]
    netlist.outputs = [out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("EQ", [a, b], [out])

    sim = RTLSimulator(netlist)

    sim.set("a", 5)
    sim.set("b", 5)
    sim.step()
    assert sim.get("out") == 1

    sim.set("a", 5)
    sim.set("b", 3)
    sim.step()
    assert sim.get("out") == 0


def test_inequality() -> None:
    netlist = Netlist("neq_test")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    out = netlist.create_net("out", 1)

    netlist.inputs = [a, b]
    netlist.outputs = [out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("NEQ", [a, b], [out])

    sim = RTLSimulator(netlist)

    sim.set("a", 5)
    sim.set("b", 3)
    sim.step()
    assert sim.get("out") == 1

    sim.set("a", 5)
    sim.set("b", 5)
    sim.step()
    assert sim.get("out") == 0


def test_addition() -> None:
    netlist = Netlist("add_test")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    sum_out = netlist.create_net("sum", 8)

    netlist.inputs = [a, b]
    netlist.outputs = [sum_out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("ADD", [a, b], [sum_out])

    sim = RTLSimulator(netlist)

    sim.set("a", 67)
    sim.set("b", 41)
    sim.step()
    assert sim.get("sum") == 108

    sim.set("a", 21)
    sim.set("b", 54)
    sim.step()
    assert sim.get("sum") == 75


def test_subtraction() -> None:
    netlist = Netlist("sub_test")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    diff_out = netlist.create_net("diff", 8)

    netlist.inputs = [a, b]
    netlist.outputs = [diff_out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("SUB", [a, b], [diff_out])

    sim = RTLSimulator(netlist)

    sim.set("a", 25)
    sim.set("b", 10)
    sim.step()
    assert sim.get("diff") == 15

    sim.set("a", 250)
    sim.set("b", 190)
    sim.step()
    assert sim.get("diff") == 60


def test_subtraction_negative_result() -> None:
    netlist = Netlist("sub_negative")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    diff_out = netlist.create_net("diff", 8)

    netlist.inputs = [a, b]
    netlist.outputs = [diff_out]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("SUB", [a, b], [diff_out])

    sim = RTLSimulator(netlist)

    # -15 wraps to 241 in unsigned
    sim.set("a", 10)
    sim.set("b", 25)
    sim.step()
    assert sim.get("diff") == 241  # -15 2's complement
    assert sim.get_net_signed("diff") == -15
