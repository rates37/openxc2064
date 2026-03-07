import pytest
from openxc2064.synthesis.rtl_nodes import Netlist, Constant, LogicGate
from openxc2064.synthesis.lowering import LoweringPass

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
