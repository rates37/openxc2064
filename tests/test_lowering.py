import pytest
from openxc2064.synthesis.rtl_nodes import Netlist, Constant, LogicGate
from openxc2064.synthesis.lowering import LoweringPass
from openxc2064.simulator.high_level_rtl_simulator import RTLSimulator

def test_lowering_constant():
    # test that a 4-bit constant maps to four 1-bit constants
    n = Netlist("test")
    c_net = n.create_net("c", width=4)
    n.add_const(0b1010, c_net) # 10
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    # 4 constants + 2 tie constants (tie0 and tie1 created by LoweringPass)
    consts = [node for node in new_n.nodes if isinstance(node, Constant)]
    assert len(consts) >= 4
    
    # specifically check the mapped nets:
    c0 = lp.net_map["c"][0]
    assert c0.source.value == 0

    c1 = lp.net_map["c"][1]
    assert c1.source.value == 1

    c2 = lp.net_map["c"][2]
    assert c2.source.value == 0

    c3 = lp.net_map["c"][3]
    assert c3.source.value == 1

def test_lowering_bitwise_and():
    n = Netlist("test")
    a_net = n.create_net("a", width=3)
    b_net = n.create_net("b", width=3)
    q_net = n.create_net("q", width=3)
    n.add_input("a", a_net)
    n.add_input("b", b_net)
    n.add_logic("AND", [a_net, b_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    ands = [node for node in new_n.nodes if isinstance(node, LogicGate) and node.op == "AND"]
    assert len(ands) == 3
    
    # verify inputs wire correctly
    assert ands[0].inputs[0].name == "a[0]"
    assert ands[0].inputs[1].name == "b[0]"
    assert ands[0].outputs[0].name == "q[0]"

    assert ands[1].inputs[0].name == "a[1]"
    assert ands[1].inputs[1].name == "b[1]"
    assert ands[1].outputs[0].name == "q[1]"

    assert ands[2].inputs[0].name == "a[2]"
    assert ands[2].inputs[1].name == "b[2]"
    assert ands[2].outputs[0].name == "q[2]"

def test_lowering_bitwise_or():
    n = Netlist("test")
    a_net = n.create_net("a", width=3)
    b_net = n.create_net("b", width=3)
    q_net = n.create_net("q", width=3)
    n.add_input("a", a_net)
    n.add_input("b", b_net)
    n.add_logic("OR", [a_net, b_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    ors = [node for node in new_n.nodes if isinstance(node, LogicGate) and node.op == "OR"]
    assert len(ors) == 3
    
    # verify inputs wire correctly
    assert ors[0].inputs[0].name == "a[0]"
    assert ors[0].inputs[1].name == "b[0]"
    assert ors[0].outputs[0].name == "q[0]"

    assert ors[1].inputs[0].name == "a[1]"
    assert ors[1].inputs[1].name == "b[1]"
    assert ors[1].outputs[0].name == "q[1]"

    assert ors[2].inputs[0].name == "a[2]"
    assert ors[2].inputs[1].name == "b[2]"
    assert ors[2].outputs[0].name == "q[2]"

def test_lowering_add():
    # 2-bit + 2-bit = 2-bit adder
    n = Netlist("test")
    a_net = n.create_net("a", width=2)
    b_net = n.create_net("b", width=2)
    q_net = n.create_net("q", width=2)
    n.add_logic("ADD", [a_net, b_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    # 2-bit ripple carry adder generates:
    # 2 XORs per bit for sum: 4 XORs total
    # 2 ANDs + 1 OR for carry per bit (except last bit has no carry out): 2 ANDs, 1 OR total
    xors = [node for node in new_n.nodes if isinstance(node, LogicGate) and node.op == "XOR"]
    ands = [node for node in new_n.nodes if isinstance(node, LogicGate) and node.op == "AND"]
    ors = [node for node in new_n.nodes if isinstance(node, LogicGate) and node.op == "OR"]
    
    assert len(xors) == 4
    assert len(ands) == 2
    assert len(ors) == 1
    
    # verify sum outputs
    sum_gates = [x for x in xors if x.outputs[0].name.startswith("q[")]
    assert len(sum_gates) == 2

def test_lowering_sub():
    # 2-bit SUB
    n = Netlist("test")
    a_net = n.create_net("a", width=2)
    b_net = n.create_net("b", width=2)
    q_net = n.create_net("q", width=2)
    n.add_logic("SUB", [a_net, b_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    # Subtraction generates NOT gates for B
    nots = [node for node in new_n.nodes if isinstance(node, LogicGate) and node.op == "NOT"]
    assert len(nots) == 2

    # Subtraction in two's complement generates a RCA:
    xors = [node for node in new_n.nodes if isinstance(node, LogicGate) and node.op == "XOR"]
    ands = [node for node in new_n.nodes if isinstance(node, LogicGate) and node.op == "AND"]
    ors = [node for node in new_n.nodes if isinstance(node, LogicGate) and node.op == "OR"]
    
    assert len(xors) == 4
    assert len(ands) == 2
    assert len(ors) == 1
    
    # verify sum outputs
    sum_gates = [x for x in xors if x.outputs[0].name.startswith("q[")]
    assert len(sum_gates) == 2

def test_lowering_eq():
    # 3-bit == 3-bit
    n = Netlist("test")
    a_net = n.create_net("a", width=3)
    b_net = n.create_net("b", width=3)
    q_net = n.create_net("q", width=1)
    n.add_logic("EQ", [a_net, b_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    xors = [node for node in new_n.nodes if getattr(node, "op", "") == "XOR"]
    assert len(xors) == 3
    
    ors = [node for node in new_n.nodes if getattr(node, "op", "") == "OR"]
    assert len(ors) == 2 # 3 inputs to OR tree requires 2 OR gates
    
    nots = [node for node in new_n.nodes if getattr(node, "op", "") == "NOT"]
    assert len(nots) == 1 # Final NOR inversion
    assert nots[0].outputs[0].name == "q[0]"

def test_lowering_slice_index():
    n = Netlist("test")
    bus = n.create_net("bus", width=4)
    idx_out = n.create_net("idx", width=1)
    slice_out = n.create_net("slice", width=2)
    n.add_logic("INDEX:2", [bus], [idx_out])
    n.add_logic("SLICE:3:2", [bus], [slice_out])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    bufs = [node for node in new_n.nodes if getattr(node, "op", "") == "BUF"]
    assert len(bufs) == 3 # 1 for index, 2 for slice
    
    idx_buf = next(b for b in bufs if b.outputs[0].name == "idx[0]")
    assert idx_buf.inputs[0].name == "bus[2]"
    
    slice_bufs = [b for b in bufs if b.outputs[0].name.startswith("slice[")]
    assert slice_bufs[0].inputs[0].name == "bus[2]"
    assert slice_bufs[1].inputs[0].name == "bus[3]"

def test_lowering_lshift():
    n = Netlist("test")
    # A is 4 bits, S (shift amount) is 2 bits
    a_net = n.create_net("a", width=4)
    s_net = n.create_net("s", width=2)
    q_net = n.create_net("q", width=4)
    n.add_logic("LSHIFT", [a_net, s_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    # 2-bit shift requires 2 layers of MUXes
    # With 4-bit data, 4 MUXes per layer = 8 MUX gates total
    muxes = [node for node in new_n.nodes if getattr(node, "op", "") == "MUX"]
    assert len(muxes) == 8
    
    # Check that output is driven by BUF layer which takes MUX output
    bufs = [node for node in new_n.nodes if getattr(node, "op", "") == "BUF"]
    
    # 4 output bits means 4 bufs connected to them
    out_bufs = [b for b in bufs if b.outputs[0].name.startswith("q[")]
    assert len(out_bufs) == 4

def test_lowering_rshift():
    n = Netlist("test")
    a_net = n.create_net("a", width=2)
    s_net = n.create_net("s", width=1)
    q_net = n.create_net("q", width=2)
    n.add_logic("RSHIFT", [a_net, s_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    muxes = [node for node in new_n.nodes if getattr(node, "op", "") == "MUX"]
    assert len(muxes) == 2

    # Check that output is driven by BUF layer which takes MUX output
    bufs = [node for node in new_n.nodes if getattr(node, "op", "") == "BUF"]
    
    # 2 output bits means 2 bufs connected to them
    out_bufs = [b for b in bufs if b.outputs[0].name.startswith("q[")]
    assert len(out_bufs) == 2


def _set_lowered_bus(sim, name, width, value):
    for i in range(width):
        bit_val = 1 if (value & (1 << i)) else 0
        sim.net_values[f"{name}[{i}]"] = bit_val

def _get_lowered_bus(sim, name, width):
    val = 0
    for i in range(width):
        bit = sim.net_values.get(f"{name}[{i}]", 0)
        if bit:
            val |= (1 << i)
    return val

def test_simulator_lowered_addition():
    # 1. Provide High-Level Netlist
    netlist = Netlist("add_test")
    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    sum_out = netlist.create_net("sum", 8)
    netlist.inputs = [a, b]
    netlist.outputs = [sum_out]
    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("ADD", [a, b], [sum_out])

    # 2. Lower it to Bit-Blasted Primitives
    lp = LoweringPass()
    lowered_n = lp.run(netlist)

    # 3. Simulate it
    sim = RTLSimulator(lowered_n)
    
    _set_lowered_bus(sim, "a", 8, 67)
    _set_lowered_bus(sim, "b", 8, 41)
    sim.step()
    assert _get_lowered_bus(sim, "sum", 8) == 108

    _set_lowered_bus(sim, "a", 8, 21)
    _set_lowered_bus(sim, "b", 8, 54)
    sim.step()
    assert _get_lowered_bus(sim, "sum", 8) == 75

def test_simulator_lowered_subtraction():
    netlist = Netlist("sub_test")
    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    diff_out = netlist.create_net("diff", 8)

    netlist.inputs = [a, b]
    netlist.outputs = [diff_out]
    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("SUB", [a, b], [diff_out])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    _set_lowered_bus(sim, "a", 8, 25)
    _set_lowered_bus(sim, "b", 8, 10)
    sim.step()
    assert _get_lowered_bus(sim, "diff", 8) == 15

    _set_lowered_bus(sim, "a", 8, 250)
    _set_lowered_bus(sim, "b", 8, 190)
    sim.step()
    assert _get_lowered_bus(sim, "diff", 8) == 60

def test_simulator_lowered_eq():
    netlist = Netlist("eq_test")
    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    out = netlist.create_net("out", 1)

    netlist.inputs = [a, b]
    netlist.outputs = [out]
    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("EQ", [a, b], [out])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    _set_lowered_bus(sim, "a", 8, 5)
    _set_lowered_bus(sim, "b", 8, 5)
    sim.step()
    assert sim.net_values.get("out[0]") == 1

    _set_lowered_bus(sim, "a", 8, 5)
    _set_lowered_bus(sim, "b", 8, 3)
    sim.step()
    assert sim.net_values.get("out[0]") == 0

def test_simulator_lowered_lshift():
    netlist = Netlist("lshift_test")
    a = netlist.create_net("a", 8)
    shift = netlist.create_net("shift", 3)
    out = netlist.create_net("out", 8)

    netlist.inputs = [a, shift]
    netlist.outputs = [out]
    netlist.add_input("a", a)
    netlist.add_input("shift", shift)
    netlist.add_logic("LSHIFT", [a, shift], [out])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    _set_lowered_bus(sim, "a", 8, 0b00001111)
    # 2 is 010.
    _set_lowered_bus(sim, "shift", 3, 2)
    sim.step()
    assert _get_lowered_bus(sim, "out", 8) == (0b00001111 << 2)

    _set_lowered_bus(sim, "a", 8, 0b00110011)
    _set_lowered_bus(sim, "shift", 3, 1)
    sim.step()
    assert _get_lowered_bus(sim, "out", 8) == (0b00110011 << 1)

def test_simulator_lowered_rshift():
    netlist = Netlist("rshift_test")
    a = netlist.create_net("a", 8)
    shift = netlist.create_net("shift", 3)
    out = netlist.create_net("out", 8)

    netlist.inputs = [a, shift]
    netlist.outputs = [out]
    netlist.add_input("a", a)
    netlist.add_input("shift", shift)
    netlist.add_logic("RSHIFT", [a, shift], [out])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    _set_lowered_bus(sim, "a", 8, 0b11110000)
    _set_lowered_bus(sim, "shift", 3, 2)
    sim.step()
    assert _get_lowered_bus(sim, "out", 8) == (0b11110000 >> 2)

    _set_lowered_bus(sim, "a", 8, 0b01100110)
    _set_lowered_bus(sim, "shift", 3, 1)
    sim.step()
    assert _get_lowered_bus(sim, "out", 8) == (0b01100110 >> 1)
