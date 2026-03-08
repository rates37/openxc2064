import pytest
import itertools
from openxc2064.synthesis.rtl_nodes import Netlist, Constant, LogicGate, DFF
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
    assert c0.drivers[0].value == 0

    c1 = lp.net_map["c"][1]
    assert c1.drivers[0].value == 1

    c2 = lp.net_map["c"][2]
    assert c2.drivers[0].value == 0

    c3 = lp.net_map["c"][3]
    assert c3.drivers[0].value == 1

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

    # Dynamic shifts generate MUX trees
    muxes = [node for node in new_n.nodes if getattr(node, "op", "") == "MUX"]
    # 4 bits shifted by 2-bit control signal = 2 stages * 4 bits/stage = 8 MUXes
    assert len(muxes) == 8
    
    # verify q[0..3] are driven by BUF gates which connect to the final stage of MUXes
    bufs = [node for node in new_n.nodes if getattr(node, "op", "") == "BUF"]
    out_bufs = [b for b in bufs if b.outputs[0].name.startswith("q[")]
    assert len(out_bufs) == 4
    
    # Verify these output BUFs are driven by the generated dynamic MUX network
    assert all("_mux" in b.inputs[0].name for b in out_bufs)
    
def test_lowering_constant_lshift():
    n = Netlist("test")
    a_net = n.create_net("a", width=4)
    s_net = n.create_net("s", width=2)
    q_net = n.create_net("q", width=4)
    
    n.add_const(2, s_net)
    n.add_logic("LSHIFT", [a_net, s_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    # Static shifts should not generate MUX trees, only direct structural routing (i.e. only BUFs)
    muxes = [node for node in new_n.nodes if getattr(node, "op", "") == "MUX"]
    assert len(muxes) == 0# A static LSHIFT should strictly compile to direct wiring with 0 dynamic MUX overhead
    
    bufs = [node for node in new_n.nodes if getattr(node, "op", "") == "BUF" and node.outputs[0].name.startswith("q[")]
    assert len(bufs) == 4 # A 4-bit static LSHIFT must output exactly 4 mapping BUFs

def test_lowering_rshift():
    n = Netlist("test")
    a_net = n.create_net("a", width=3)
    s_net = n.create_net("s", width=2)
    q_net = n.create_net("q", width=3)
    
    n.add_input("s", s_net) # Makes s dynamic
    n.add_logic("RSHIFT", [a_net, s_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    muxes = [node for node in new_n.nodes if getattr(node, "op", "") == "MUX"]
    assert len(muxes) == 6, f"Expected 6 MUXes for a 3-bit RSHIFT with 2-bit control (3 bits * 2 stages), but found {len(muxes)}"

def test_lowering_constant_rshift():
    n = Netlist("test")
    a_net = n.create_net("a", width=3)
    s_net = n.create_net("s", width=2)
    q_net = n.create_net("q", width=3)
    
    n.add_const(1, s_net)
    n.add_logic("RSHIFT", [a_net, s_net], [q_net])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    muxes = [node for node in new_n.nodes if getattr(node, "op", "") == "MUX"]
    assert len(muxes) == 0, "A static RSHIFT should strictly expand to direct wiring with 0 dynamic MUX overhead"
    
    bufs = [node for node in new_n.nodes if getattr(node, "op", "") == "BUF" and node.outputs[0].name.startswith("q[")]
    assert len(bufs) == 3, "A 3-bit static RSHIFT must output exactly 3 mapping BUFs"

def test_lowering_shift_overflow():
    n = Netlist("test")
    a = n.create_net("a", 2)
    s = n.create_net("s", 3)
    q = n.create_net("q", 2)
    n.add_logic("LSHIFT", [a, s], [q])
    
    lp = LoweringPass()
    new_n = lp.run(n)

    # the lower'er expands it into a dynamic Barrel Shifter using
    # nested cascades of MUX layers routing bit transfers over geometric powers of 2.
    # For a 2-bit output and 3-bit shift amount, we expect 2 MUXes per shift bit.
    muxes = [node for node in new_n.nodes if getattr(node, "op", "") == "MUX"]
    assert len(muxes) == 6

def test_lowering_or_tree_minimal():
    lp = LoweringPass()
    n = Netlist("dummy")
    net1 = n.create_net("n1", 1)
    
    res1 = lp._build_or_tree(n, [net1], "test1")
    assert res1 == net1

def test_lowering_unary_ops():
    n = Netlist("test")
    a = n.create_net("a", 2)
    q_not = n.create_net("q_not", 2)
    q_logic_not = n.create_net("q_logic_not", 2)
    q_buf = n.create_net("q_buf", 2)
    q_neg = n.create_net("q_neg", 2)
    
    n.add_logic("NOT", [a], [q_not])
    n.add_logic("LOGIC_NOT", [a], [q_logic_not]) # becomes NOT
    n.add_logic("BUF", [a], [q_buf])
    n.add_logic("NEG", [a], [q_neg])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    nots = [node for node in new_n.nodes if getattr(node, "op", "") == "NOT"]
    bufs = [node for node in new_n.nodes if getattr(node, "op", "") == "BUF"]
    
    # A 2-bit NOT operation ("~A") and a 2-bit LOGIC_NOT operation ("!A") both lower 
    # functionally to exactly two 1-bit NOT gates each, meaning 4 NOT gates total in the netlist.
    # Here isolate specifically the 2 NOT gates driving the output net `q_not`.
    q_not_drivers = [x for x in nots if x.outputs[0].name.startswith("q_not[")]
    assert len(q_not_drivers) == 2, "Expected exactly two 1-bit NOT gates driving the 2-bit q_not net"
    
    # A 2-bit BUF operation lowers to exactly two 1-bit BUF gates.
    q_buf_drivers = [x for x in bufs if x.outputs[0].name.startswith("q_buf[")]
    assert len(q_buf_drivers) == 2, "Expected exactly two 1-bit BUF gates driving the 2-bit q_buf net"

def test_lowering_neq():
    n = Netlist("test")
    a = n.create_net("a", 2)
    b = n.create_net("b", 2)
    q = n.create_net("q", 1)
    n.add_logic("NEQ", [a, b], [q])
    
    lp = LoweringPass()
    new_n = lp.run(n)

    # A 2-bit NEQ comparator evaluates `(A[0] ^ B[0]) | (A[1] ^ B[1])`.
    # So the top-level output `q` is 1-bit and is driven directly 
    # by the evaluated result of the logical OR accumulation tree via a BUF gate.
    q_drivers = [node for node in new_n.nodes if getattr(node, "op", "") == "BUF" and node.outputs[0].name == "q[0]"]
    assert len(q_drivers) == 1 # The root of a NEQ comparator should be a single 1-bit BUF driving the 1-bit output
    # this test is not great and could be improved

def test_lowering_update():
    n = Netlist("test")
    a = n.create_net("a", 4)
    rhs = n.create_net("rhs", 2) # update bits 2:1
    q = n.create_net("q", 4)
    n.add_logic("UPDATE:2:1", [a, rhs], [q])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    # An UPDATE mapping dynamically overwrites specific structural wires without creating arithmetic cost.
    # Since `a` is 4 bits, the output `q` is 4 bits. The Lowering mapping binds all 4 bits
    # structurally using simple 1-bit BUF gates (2 from `rhs_arr`, 2 from `old_arr`).
    bufs = [node for node in new_n.nodes if getattr(node, "op", "") == "BUF" and node.outputs[0].name.startswith("q[")]
    assert len(bufs) == 4  # A 4-bit assignment update must output via exactly 4 BUF wire bridges

def test_lowering_mux():
    n = Netlist("test")
    sel = n.create_net("sel", 1)
    f = n.create_net("f", 2) # else
    t = n.create_net("t", 2) # then
    q = n.create_net("q", 2)
    n.add_logic("MUX", [sel, f, t], [q])
    
    lp = LoweringPass()
    new_n = lp.run(n)
    
    # A 2-bit MUX divides strictly into exactly two parallel 1-bit MUX primitives:
    # `q[0] = MUX(sel, f[0], t[0])` and `q[1] = MUX(sel, f[1], t[1])`.
    muxes = [node for node in new_n.nodes if getattr(node, "op", "") == "MUX"]
    assert len(muxes) == 2  # A 2-bit MUX node should bit-blast into exactly 2 single-bit MUX gates

def test_lowering_unsupported():
    n = Netlist("test")
    a = n.create_net("a", 2)
    q = n.create_net("q", 2)
    n.add_logic("MAGIC_OP", [a], [q])
    
    lp = LoweringPass()
    with pytest.raises(ValueError):
        lp.run(n)



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
    netlist = Netlist("add_test")
    a = netlist.create_net("a", 8)
    b = netlist.create_net("b", 8)
    sum_out = netlist.create_net("sum", 8)
    netlist.inputs = [a, b]
    netlist.outputs = [sum_out]
    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("ADD", [a, b], [sum_out])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    # test a large stride subset:
    for a_val, b_val in itertools.product(range(0, 256, 15), range(0, 256, 15)):
        _set_lowered_bus(sim, "a", 8, a_val)
        _set_lowered_bus(sim, "b", 8, b_val)
        sim.step()
        assert _get_lowered_bus(sim, "sum", 8) == ((a_val + b_val) & 0xFF)

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
    for a_val, b_val in itertools.product(range(0, 256, 15), range(0, 256, 15)):
        _set_lowered_bus(sim, "a", 8, a_val)
        _set_lowered_bus(sim, "b", 8, b_val)
        sim.step()
        assert _get_lowered_bus(sim, "diff", 8) == ((a_val - b_val) & 0xFF)

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
    for a_val, b_val in itertools.product(range(0, 256, 15), range(0, 256, 15)):
        _set_lowered_bus(sim, "a", 8, a_val)
        _set_lowered_bus(sim, "b", 8, b_val)
        sim.step()
        expected = 1 if a_val == b_val else 0
        assert sim.net_values.get("out[0]") == expected
        
    # Explicity test exact equality triggers
    for a_val in range(256):
        _set_lowered_bus(sim, "a", 8, a_val)
        _set_lowered_bus(sim, "b", 8, a_val)
        sim.step()
        assert sim.net_values.get("out[0]") == 1

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
    for a_val in range(256):
        for s_val in range(8): # 3-bit shift
            _set_lowered_bus(sim, "a", 8, a_val)
            _set_lowered_bus(sim, "shift", 3, s_val)
            sim.step()
            expected = (a_val << s_val) & 0xFF
            assert _get_lowered_bus(sim, "out", 8) == expected

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
    for a_val in range(256):
        for s_val in range(8): # 3-bit shift
            _set_lowered_bus(sim, "a", 8, a_val)
            _set_lowered_bus(sim, "shift", 3, s_val)
            sim.step()
            expected = (a_val >> s_val) & 0xFF
            assert _get_lowered_bus(sim, "out", 8) == expected



def test_simulator_lowered_bitwise_and():
    netlist = Netlist("and_test")
    a = netlist.create_net("a", 4)
    b = netlist.create_net("b", 4)
    q = netlist.create_net("q", 4)
    netlist.inputs = [a, b]
    netlist.outputs = [q]
    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("AND", [a, b], [q])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)
    # 4-bit means exhaustive 16x16 = 256 is instant
    for a_val, b_val in itertools.product(range(16), range(16)):
        _set_lowered_bus(sim, "a", 4, a_val)
        _set_lowered_bus(sim, "b", 4, b_val)
        sim.step()
        assert _get_lowered_bus(sim, "q", 4) == (a_val & b_val)

def test_simulator_lowered_bitwise_or():
    netlist = Netlist("or_test")
    a = netlist.create_net("a", 4)
    b = netlist.create_net("b", 4)
    q = netlist.create_net("q", 4)
    netlist.inputs = [a, b]
    netlist.outputs = [q]
    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("OR", [a, b], [q])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)
    for a_val, b_val in itertools.product(range(16), range(16)):
        _set_lowered_bus(sim, "a", 4, a_val)
        _set_lowered_bus(sim, "b", 4, b_val)
        sim.step()
        assert _get_lowered_bus(sim, "q", 4) == (a_val | b_val)

def test_simulator_lowered_bitwise_xor():
    netlist = Netlist("xor_test")
    a = netlist.create_net("a", 4)
    b = netlist.create_net("b", 4)
    q = netlist.create_net("q", 4)
    netlist.inputs = [a, b]
    netlist.outputs = [q]
    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("XOR", [a, b], [q])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)
    for a_val, b_val in itertools.product(range(16), range(16)):
        _set_lowered_bus(sim, "a", 4, a_val)
        _set_lowered_bus(sim, "b", 4, b_val)
        sim.step()
        assert _get_lowered_bus(sim, "q", 4) == (a_val ^ b_val)

def test_simulator_lowered_neq():
    netlist = Netlist("neq_test")
    a = netlist.create_net("a", 4)
    b = netlist.create_net("b", 4)
    out = netlist.create_net("out", 1)

    netlist.inputs = [a, b]
    netlist.outputs = [out]
    netlist.add_input("a", a)
    netlist.add_input("b", b)
    netlist.add_logic("NEQ", [a, b], [out])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    _set_lowered_bus(sim, "a", 4, 5)
    _set_lowered_bus(sim, "b", 4, 5)
    sim.step()
    assert sim.net_values.get("out[0]", 0) == 0

    _set_lowered_bus(sim, "a", 4, 5)
    _set_lowered_bus(sim, "b", 4, 3)
    sim.step()
    assert sim.net_values.get("out[0]", 0) == 1

def test_simulator_lowered_unary_ops():
    netlist = Netlist("unary_test")
    a = netlist.create_net("a", 4)
    q_not = netlist.create_net("q_not", 4)
    q_neg = netlist.create_net("q_neg", 4)
    
    netlist.inputs = [a]
    netlist.outputs = [q_not, q_neg]
    netlist.add_input("a", a)
    netlist.add_logic("NOT", [a], [q_not])
    netlist.add_logic("NEG", [a], [q_neg])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    for a_val in range(16):
        _set_lowered_bus(sim, "a", 4, a_val)
        sim.step()
        
        # bitwise NOT
        assert _get_lowered_bus(sim, "q_not", 4) == (~a_val & 0xF)
        
        # NEG is 2's complement
        assert _get_lowered_bus(sim, "q_neg", 4) == (-a_val & 0xF)

def test_simulator_lowered_mux():
    netlist = Netlist("mux_test")
    sel = netlist.create_net("sel", 1)
    f = netlist.create_net("f", 4)
    t = netlist.create_net("t", 4)
    q = netlist.create_net("q", 4)
    
    netlist.inputs = [sel, f, t]
    netlist.outputs = [q]
    netlist.add_input("sel", sel)
    netlist.add_input("f", f)
    netlist.add_input("t", t)
    netlist.add_logic("MUX", [sel, f, t], [q])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    for sel_val, f_val, t_val in itertools.product([0, 1], range(16), range(16)):
        _set_lowered_bus(sim, "sel", 1, sel_val)
        _set_lowered_bus(sim, "f", 4, f_val)
        _set_lowered_bus(sim, "t", 4, t_val)
        sim.step()
        
        expected = t_val if sel_val else f_val
        assert _get_lowered_bus(sim, "q", 4) == expected

def test_simulator_lowered_slice_index_update():
    netlist = Netlist("slice_index_test")
    a = netlist.create_net("a", 8)
    upd = netlist.create_net("upd", 4)
    
    idx_q = netlist.create_net("idx_q", 1)
    slc_q = netlist.create_net("slc_q", 4)
    upd_q = netlist.create_net("upd_q", 8)

    netlist.inputs = [a, upd]
    netlist.outputs = [idx_q, slc_q, upd_q]
    netlist.add_input("a", a)
    netlist.add_input("upd", upd)
    
    netlist.add_logic("INDEX:3", [a], [idx_q])
    netlist.add_logic("SLICE:5:2", [a], [slc_q])
    netlist.add_logic("UPDATE:5:2", [a, upd], [upd_q])

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    for a_val, upd_val in itertools.product(range(0, 256, 17), range(16)):
        _set_lowered_bus(sim, "a", 8, a_val)
        _set_lowered_bus(sim, "upd", 4, upd_val)
        sim.step()
        
        # INDEX:3
        expected_idx = 1 if (a_val & (1 << 3)) else 0
        assert sim.net_values.get("idx_q[0]", 0) == expected_idx
        
        # SLICE:5:2
        expected_slc = (a_val >> 2) & 0xF
        assert _get_lowered_bus(sim, "slc_q", 4) == expected_slc
        
        # UPDATE:5:2
        expected_upd = (a_val & ~(0xF << 2)) | (upd_val << 2)
        assert _get_lowered_bus(sim, "upd_q", 8) == expected_upd

def test_simulator_lowered_dff():
    from openxc2064.synthesis.rtl_nodes import DFF
    netlist = Netlist("dff_test")
    d = netlist.create_net("d", 4)
    clk = netlist.create_net("clk", 1)
    q = netlist.create_net("q", 4)
    
    netlist.inputs = [d, clk]
    netlist.outputs = [q]
    netlist.add_input("d", d)
    netlist.add_input("clk", clk)
    netlist.add_dff([d, clk], [q], edge="posedge")

    lp = LoweringPass()
    lowered_n = lp.run(netlist)
    sim = RTLSimulator(lowered_n)

    current_q = 0
    for clk, d in [(0, 10), (1, 10), (1, 5), (0, 5), (1, 2), (0, 2)]:
        _set_lowered_bus(sim, "d", 4, d)
        prev_clk = _get_lowered_bus(sim, "clk", 1)
        _set_lowered_bus(sim, "clk", 1, clk)
        sim.step()
        
        if clk == 1 and prev_clk == 0:
            current_q = d
            
        assert _get_lowered_bus(sim, "q", 4) == current_q
