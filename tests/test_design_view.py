import pytest

from openxc2064.mapping.xc2064_primitives import CLB, IOB
from openxc2064.pnr.design_view import DesignError, DesignView
from openxc2064.pnr.flow import compile_hdl_to_packed
from openxc2064.synthesis.rtl_nodes import Netlist

ADDER_HDL = """module adder(input [3:0] a, input [3:0] b, output [3:0] sum);
    assign sum = a + b;
endmodule
"""

REG_ADDER_HDL = """module radder(input [3:0] a, input [3:0] b, output reg [3:0] sum, input clk);
    always : seq @(posedge clk)
        sum = a + b;
endmodule
"""


def _detached_clb(nl: Netlist, pins, outputs, **kwargs) -> CLB:
    clb = CLB(id=nl.next_node_id("clb"), inputs=[], outputs=[], **kwargs)
    clb.inputs = pins  # type: ignore[assignment]
    clb.outputs = outputs
    nl.nodes.append(clb)
    return clb


def _input_iob(nl: Netlist, name: str) -> IOB:
    iob = IOB(nl.next_node_id("iob_in_"), inputs=[], outputs=[], ts_mux_sel=0)
    pad = nl.create_net(f"pad_{name}", 1)
    inner = nl.create_net(name, 1)
    iob.inputs = [pad, None, None, None]
    iob.outputs = [None, inner]
    iob.pad_name = name
    nl.nodes.append(iob)
    return iob


def test_adder_terminals():
    packed = compile_hdl_to_packed(ADDER_HDL, "adder")
    view = DesignView(packed)

    assert view.nets, "expected routable nets"
    assert not any(net.is_clock for net in view.nets)
    for net in view.nets:
        assert net.driver[1] in ("X", "Y", "I")
        assert net.sinks
        for _, port in net.sinks:
            assert port in ("A", "B", "C", "D", "K", "O")

    # 8 input pads drive 8 nets; 4 output pads consume 4 nets
    input_driven = [n for n in view.nets if n.driver[1] == "I"]
    assert len(input_driven) == 8
    output_sinks = sum(1 for n in view.nets for _, p in n.sinks if p == "O")
    assert output_sinks == 4


def test_registered_adder_has_one_clock_net():
    packed = compile_hdl_to_packed(REG_ADDER_HDL, "radder")
    view = DesignView(packed)

    clocks = [n for n in view.nets if n.is_clock]
    assert len(clocks) == 1
    assert view.clock_net is clocks[0]
    assert all(port == "K" for _, port in clocks[0].sinks)
    assert clocks[0].driver[1] == "I"  # clock arrives on a pad


def test_constant_driving_routed_net_rejected():
    nl = Netlist("bad")
    cnet = nl.create_net("c", 1)
    nl.add_const(1, cnet)
    x = nl.create_net("x", 1)
    _detached_clb(nl, [cnet, None, None, None, None], [x], lut_f_init=0xF0, sel_x=2)

    with pytest.raises(DesignError, match="constant"):
        DesignView(nl)


def test_undriven_net_rejected():
    nl = Netlist("bad")
    floating = nl.create_net("floating", 1)
    x = nl.create_net("x", 1)
    _detached_clb(nl, [floating, None, None, None, None], [x], lut_f_init=0xF0, sel_x=2)

    with pytest.raises(DesignError, match="floating"):
        DesignView(nl)


def test_multiple_clock_domains_rejected():
    nl = Netlist("twoclk")
    clk1 = _input_iob(nl, "clk1").outputs[1]
    clk2 = _input_iob(nl, "clk2").outputs[1]
    q1 = nl.create_net("q1", 1)
    q2 = nl.create_net("q2", 1)
    _detached_clb(nl, [None, None, None, None, clk1], [q1], sel_x=1)
    _detached_clb(nl, [None, None, None, None, clk2], [q2], sel_x=1)

    with pytest.raises(DesignError, match="clock"):
        DesignView(nl)
