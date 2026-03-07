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

    assert slice_bufs[1].inputs[0].name == "bus[3]"
