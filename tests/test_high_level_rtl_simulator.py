import pytest
from openxc2064.synthesis.rtl_nodes import Netlist, Net, LogicGate, DFF, Input, Constant
from openxc2064.simulator import RTLSimulator
from itertools import permutations
from openxc2064.simulator.high_level_rtl_simulator import CombinationalLoopError


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


def test_2_to_1_mux() -> None:
    netlist = Netlist("mux_2to1")

    sel = netlist.create_net("sel", 1)
    in0 = netlist.create_net("in0", 12)
    in1 = netlist.create_net("in1", 12)
    out = netlist.create_net("out", 12)

    netlist.inputs = [sel, in0, in1]
    netlist.outputs = [out]

    netlist.add_input("sel", sel)
    netlist.add_input("in0", in0)
    netlist.add_input("in1", in1)
    netlist.add_logic("MUX", [sel, in0, in1], [out])

    sim = RTLSimulator(netlist)

    sim.set("in0", 420)
    sim.set("in1", 69)

    sim.set("sel", 0)
    sim.step()
    assert sim.get("out") == 420

    sim.set("sel", 1)
    sim.step()
    assert sim.get("out") == 69


def test_dff_posedge() -> None:
    netlist = Netlist("dff_posedge")

    d = netlist.create_net("d", 12)
    clk = netlist.create_net("clk", 1)
    q = netlist.create_net("q", 12)

    netlist.inputs = [d, clk]
    netlist.outputs = [q]

    netlist.add_input("d", d)
    netlist.add_input("clk", clk)
    netlist.add_dff([d, clk], [q], edge="posedge")

    sim = RTLSimulator(netlist)

    sim.set("d", 0)
    sim.set("clk", 0)
    sim.step()
    assert sim.get("q") == 0

    sim.set("d", 420)
    sim.step()
    assert sim.get("q") == 0  # Q should not change yet

    # Rising edge should capture D
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 420

    # Change D while clk is high
    sim.set("d", 69)
    sim.step()
    assert sim.get("q") == 420  # Q should not change

    # Falling edge should not capture (posedge only)
    sim.set("clk", 0)
    sim.step()
    assert sim.get("q") == 420

    # Rising edge
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 69


def test_dff_negedge() -> None:
    netlist = Netlist("dff_negedge")

    d = netlist.create_net("d", 12)
    clk = netlist.create_net("clk", 1)
    q = netlist.create_net("q", 12)

    netlist.inputs = [d, clk]
    netlist.outputs = [q]

    netlist.add_input("d", d)
    netlist.add_input("clk", clk)
    netlist.add_dff([d, clk], [q], edge="negedge")

    sim = RTLSimulator(netlist)

    # Start with clock high
    sim.set("d", 0)
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 0

    sim.set("d", 37)
    sim.step()
    assert sim.get("q") == 0

    # Falling edge capture D
    sim.set("clk", 0)
    sim.step()
    assert sim.get("q") == 37

    # Rising edge should not capture (negedge only)
    sim.set("d", 67)
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 37

    # Falling edge
    sim.set("clk", 0)
    sim.step()
    assert sim.get("q") == 67


def test_counter() -> None:
    netlist = Netlist("counter")

    clk = netlist.create_net("clk", 1)
    reset = netlist.create_net("reset", 1)
    count = netlist.create_net("count", 8)
    count_next = netlist.create_net("count_next", 8)
    one = netlist.create_net("one", 8)
    zero = netlist.create_net("zero", 8)
    count_or_zero = netlist.create_net("count_or_zero", 8)

    netlist.inputs = [clk, reset]
    netlist.outputs = [count]

    netlist.add_input("clk", clk)
    netlist.add_input("reset", reset)
    netlist.add_const(1, one)
    netlist.add_const(0, zero)

    # count_next = count + 1
    netlist.add_logic("ADD", [count, one], [count_next])

    # if reset, output 0, else output count_next
    netlist.add_logic("MUX", [reset, count_next, zero], [count_or_zero])

    # store the count
    netlist.add_dff([count_or_zero, clk], [count], edge="posedge")

    sim = RTLSimulator(netlist)

    # Reset
    sim.set("reset", 1)
    sim.set("clk", 0)
    sim.step()

    sim.set("clk", 1)
    sim.step()
    assert sim.get("count") == 0

    sim.set("reset", 0)
    for i in range(1, 258):  # check overflow
        sim.set("clk", 0)
        sim.step()
        sim.set("clk", 1)
        sim.step()
        assert sim.get("count") == (i % 256)


def test_shift_register() -> None:
    netlist = Netlist("shift_reg")

    clk = netlist.create_net("clk", 1)
    d_in = netlist.create_net("d_in", 1)
    q0 = netlist.create_net("q0", 1)
    q1 = netlist.create_net("q1", 1)
    q2 = netlist.create_net("q2", 1)
    q3 = netlist.create_net("q3", 1)

    netlist.inputs = [clk, d_in]
    netlist.outputs = [q0, q1, q2, q3]

    netlist.add_input("clk", clk)
    netlist.add_input("d_in", d_in)

    # Chain of DFFs
    netlist.add_dff([d_in, clk], [q0], edge="posedge")
    netlist.add_dff([q0, clk], [q1], edge="posedge")
    netlist.add_dff([q1, clk], [q2], edge="posedge")
    netlist.add_dff([q2, clk], [q3], edge="posedge")

    sim = RTLSimulator(netlist)

    # test every possible pattern
    for pattern in set(permutations([0, 0, 0, 0, 1, 1, 1, 1], 4)):
        for i, bit in enumerate(pattern):
            sim.set("d_in", bit)
            sim.set("clk", 0)
            sim.step()
            sim.set("clk", 1)
            sim.step()
            # check outputs:
            assert sim.get("q0") == pattern[i]
            if i >= 1:
                assert sim.get("q1") == pattern[i - 1]
            if i >= 2:
                assert sim.get("q2") == pattern[i - 2]
            if i >= 3:
                assert sim.get("q3") == pattern[i - 3]


def test_alu() -> None:
    netlist = Netlist("simple_alu")

    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    op = netlist.create_net("op", 1)  # 0=add, 1=sub
    result = netlist.create_net("result", 8)
    add_result = netlist.create_net("add_result", 8)
    sub_result = netlist.create_net("sub_result", 8)

    netlist.inputs = [a, b, op]
    netlist.outputs = [result]

    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_input("op", op)

    netlist.add_logic("ADD", [a, b], [add_result])
    netlist.add_logic("SUB", [a, b], [sub_result])
    netlist.add_logic("MUX", [op, add_result, sub_result], [result])

    sim = RTLSimulator(netlist)

    # addition
    sim.set("a", 20)
    sim.set("b", 15)
    sim.set("op", 0)
    sim.step()
    assert sim.get("result") == 35

    # subtraction
    sim.set("op", 1)
    sim.step()
    assert sim.get("result") == 5


def test_simple_state_machine() -> None:
    netlist = Netlist("fsm_2state")

    clk = netlist.create_net("clk", 1)
    inp = netlist.create_net("inp", 1)
    state = netlist.create_net("state", 1)
    state_next = netlist.create_net("state_next", 1)

    netlist.inputs = [clk, inp]
    netlist.outputs = [state]

    netlist.add_input("clk", clk)
    netlist.add_input("inp", inp)

    # Next state = inp XOR state
    netlist.add_logic("XOR", [inp, state], [state_next])
    netlist.add_dff([state_next, clk], [state], edge="posedge")

    sim = RTLSimulator(netlist)

    # Initialise with clock low and input low
    sim.set("inp", 0)
    sim.set("clk", 0)
    sim.step()
    assert sim.get("state") == 0
    # state=0, inp=0, so state_next=0

    # Change input while clock still low
    # combinational logic to settles before next edge
    sim.set("inp", 1)
    sim.step()
    # state=0, inp=1, so state_next is 1
    # state output is still 0 because no clock edge yet
    assert sim.get("state") == 0

    # trigger rising edge
    sim.set("clk", 1)
    sim.step()
    # Rising edge captures state_next=1
    assert sim.get("state") == 1

    sim.set("clk", 0)
    sim.step()
    assert sim.get("state") == 1

    sim.set("inp", 0)
    sim.step()
    # state=1, inp=0, so state_next = 1 (no change)

    sim.set("clk", 1)
    sim.step()
    assert sim.get("state") == 1


def test_invalid_input_port() -> None:
    netlist = Netlist("test")
    inp = netlist.create_net("inp")
    netlist.inputs = [inp]
    netlist.add_input("inp", inp)

    sim = RTLSimulator(netlist)

    with pytest.raises(ValueError):
        sim.set("nonexistent", 5)


def test_invalid_output_port() -> None:
    netlist = Netlist("test")
    out = netlist.create_net("out")
    netlist.outputs = [out]

    sim = RTLSimulator(netlist)

    with pytest.raises(ValueError):
        sim.get("nonexistent")


def test_invalid_net_name() -> None:
    netlist = Netlist("test")

    sim = RTLSimulator(netlist)

    with pytest.raises(ValueError):
        sim.get_net("nonexistent")


def test_zero_width_ports() -> None:
    netlist = Netlist("zero_width")

    inp = netlist.create_net("inp", 0)
    out = netlist.create_net("out", 0)

    netlist.inputs = [inp]
    netlist.outputs = [out]

    netlist.add_input("inp", inp)
    netlist.add_logic("BUF", [inp], [out])

    sim = RTLSimulator(netlist)
    # todo: what should this behaviour be? It's uncommon to arise from source code so not really important
    sim.set("inp", 999)
    sim.step()
    assert sim.get("out") == 0


def test_multiple_changes_before_step() -> None:
    netlist = Netlist("multi_change")

    inp = netlist.create_net("inp", 8)
    out = netlist.create_net("out", 8)

    netlist.inputs = [inp]
    netlist.outputs = [out]

    netlist.add_input("inp", inp)
    netlist.add_logic("BUF", [inp], [out])

    sim = RTLSimulator(netlist)

    # Change input multiple times
    sim.set("inp", 10)
    sim.set("inp", 20)
    sim.set("inp", 30)

    # Only last value takes effect
    sim.step()
    assert sim.get("out") == 30


def test_chained_gates() -> None:
    netlist = Netlist("gate_chain")

    inp = netlist.create_net("inp", 8)
    n1 = netlist.create_net("n1", 8)
    n2 = netlist.create_net("n2", 8)
    n3 = netlist.create_net("n3", 8)
    out = netlist.create_net("out", 8)

    netlist.inputs = [inp]
    netlist.outputs = [out]

    netlist.add_input("inp", inp)
    netlist.add_logic("BUF", [inp], [n1])
    netlist.add_logic("BUF", [n1], [n2])
    netlist.add_logic("BUF", [n2], [n3])
    netlist.add_logic("BUF", [n3], [out])

    sim = RTLSimulator(netlist)

    sim.set("inp", 123)
    sim.step()

    assert sim.get("out") == 123
    assert sim.get_net("n1") == 123
    assert sim.get_net("n2") == 123
    assert sim.get_net("n3") == 123


def test_fanout() -> None:
    # drive multiple outputs with a single net
    netlist = Netlist("fanout")

    inp = netlist.create_net("inp", 8)
    out1 = netlist.create_net("out1", 8)
    out2 = netlist.create_net("out2", 8)

    netlist.inputs = [inp]
    netlist.outputs = [out1, out2]

    netlist.add_input("inp", inp)
    netlist.add_logic("BUF", [inp], [out1])
    netlist.add_logic("BUF", [inp], [out2])

    sim = RTLSimulator(netlist)

    sim.set("inp", 67)
    sim.step()

    assert sim.get("out1") == 67
    assert sim.get("out2") == 67



def test_deep_anti_ordered_chain_settles() -> None:
    # gates stored in anti-topological order propagate one level per full
    # sweep in an iterative simulator; with the old 50-iteration cap (100
    # sweeps per step across the two propagate calls) a 130-gate chain
    # silently returned stale values. topological evaluation must settle it
    # in a single pass
    netlist = Netlist("deep_chain")
    nets = [netlist.create_net(f"n{i}", 1) for i in range(131)]
    netlist.add_input("n0", nets[0])
    for i in range(130, 0, -1):  # deliberately worst-case node order
        netlist.add_logic("BUF", [nets[i - 1]], [nets[i]])
    netlist.outputs.append(nets[130])

    sim = RTLSimulator(netlist)
    sim.set("n0", 1)
    sim.step()
    assert sim.get("n130") == 1

    sim.set("n0", 0)
    sim.step()
    assert sim.get("n130") == 0


def test_combinational_loop_raises() -> None:
    # a = ~b, b = ~a: previously oscillated for 50 sweeps and silently gave
    # up; it must now be reported as a structural error at construction

    netlist = Netlist("loop")
    a = netlist.create_net("a", 1)
    b = netlist.create_net("b", 1)
    netlist.add_logic("NOT", [a], [b])
    netlist.add_logic("NOT", [b], [a])
    netlist.outputs.append(a)

    with pytest.raises(CombinationalLoopError):
        RTLSimulator(netlist)


def test_sequential_feedback_is_not_a_combinational_loop() -> None:
    # a DFF in the cycle breaks it: q -> NOT -> d -> DFF -> q must simulate
    # as a toggle flip-flop, not raise
    netlist = Netlist("toggle")
    clk = netlist.create_net("clk", 1)
    netlist.add_input("clk", clk)
    q = netlist.create_net("q", 1)
    d = netlist.create_net("d", 1)
    netlist.add_logic("NOT", [q], [d])
    netlist.add_dff([d, clk], [q])
    netlist.outputs.append(q)

    sim = RTLSimulator(netlist)
    expected = 0
    for _ in range(4):
        assert sim.get("q") == expected
        sim.set("clk", 0)
        sim.step()
        sim.set("clk", 1)
        sim.step()
        expected ^= 1
    assert sim.get("q") == expected
