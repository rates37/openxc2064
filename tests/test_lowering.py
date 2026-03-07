import pytest
from openxc2064.synthesis.rtl_nodes import Netlist, Constant
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
