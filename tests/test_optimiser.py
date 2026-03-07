import pytest

from openxc2064.hdl import parse_hdl
from openxc2064.synthesis import HDLElaborator, Synthesiser, Optimiser

from openxc2064.synthesis.rtl_nodes import Netlist, Constant


def test_dce_basic():
    nl = Netlist(module_name="test")
    # create input/output
    in_net = nl.create_net("in1")
    nl.add_input("in1", in_net)
    out_net = nl.create_net("out1")
    nl.outputs.append(out_net)

    # Route: Input -> AND -> Output
    mid_net1 = nl.create_net("mid1")
    mid_net2 = nl.create_net("mid2")

    # Gate 1: Drives output (LIVE)
    nl.add_logic("BUF", [mid_net1], [out_net])

    # Gate 2: Drives mid_net1 (LIVE)
    nl.add_logic("BUF", [in_net], [mid_net1])

    # Gate 3: Drives mid_net2 (DEAD, should get optimised away)
    nl.add_logic("BUF", [in_net], [mid_net2])

    opt = Optimiser()
    opt._trim_dead_code(nl)

    # Should have 3 nodes: Input, BUF, BUF
    assert len(nl.nodes) == 3
    bufs = [n for n in nl.nodes if getattr(n, "op", "") == "BUF"]
    assert len(bufs) == 2


def test_dce_dff():
    nl = Netlist(module_name="test_mod")
    in_net = nl.create_net("clk")
    nl.add_input("clk", in_net)

    dead_dff_out = nl.create_net("q")
    # Dead DFF
    nl.add_dff([in_net, in_net], [dead_dff_out])

    opt = Optimiser()
    opt._trim_dead_code(nl)

    assert len(nl.nodes) == 1


def test_constant_folding_and_annihilation():
    nl = Netlist(module_name="test_mod")
    in_net = nl.create_net("in1")
    nl.add_input("in1", in_net)

    # out1 = in1 AND 0 -> should become 0
    out_net = nl.create_net("out_and")
    nl.outputs.append(out_net)

    c0_net = nl.create_net("c0")
    nl.add_const(0, c0_net)

    nl.add_logic("AND", [in_net, c0_net], [out_net])

    opt = Optimiser()
    opt.optimise(nl)

    ands = [n for n in nl.nodes if getattr(n, "op", "") == "AND"]
    # The AND gate should be completely gone
    assert len(ands) == 0
    # Output should be driven by a Constant
    assert out_net.source is not None
    assert isinstance(out_net.source, Constant)
    assert out_net.source.value == 0


def test_constant_folding_or_identity():
    nl = Netlist(module_name="test_mod")
    in_net = nl.create_net("in1")
    nl.add_input("in1", in_net)

    # out1 = in1 OR 0 -> should become BUF(in1)
    out_net = nl.create_net("out_or")
    nl.outputs.append(out_net)

    c0_net = nl.create_net("c0")
    nl.add_const(0, c0_net)

    # The gate
    nl.add_logic("OR", [in_net, c0_net], [out_net])

    opt = Optimiser()
    opt.optimise(nl)

    # Original 0 is now dead because it only drove this OR gate
    # So DCE during convergence should eat the 0.
    ors = [n for n in nl.nodes if getattr(n, "op", "") == "OR"]
    assert len(ors) == 0
    bufs = [n for n in nl.nodes if getattr(n, "op", "") == "BUF"]
    assert len(bufs) == 1
    consts = [n for n in nl.nodes if isinstance(n, Constant)]
    assert len(consts) == 0


def test_constant_folding_mux():
    nl = Netlist(module_name="test_mod")

    sel_net = nl.create_net("sel")
    true_net = nl.create_net("t")
    false_net = nl.create_net("f")
    nl.add_input("sel", sel_net)
    nl.add_input("t", true_net)
    nl.add_input("f", false_net)

    out_net = nl.create_net("out")
    nl.outputs.append(out_net)

    # MUX where sel is 1
    sel_const_net = nl.create_net("sel_c")
    nl.add_const(1, sel_const_net)

    nl.add_logic("MUX", [sel_const_net, true_net, false_net], [out_net])

    opt = Optimiser()
    opt.optimise(nl)

    muxes = [n for n in nl.nodes if getattr(n, "op", "") == "MUX"]
    assert len(muxes) == 0
    bufs = [n for n in nl.nodes if getattr(n, "op", "") == "BUF"]
    assert len(bufs) == 1
    # Check that output is driven by BUF which is driven by true_net
    buf_node = out_net.source
    assert buf_node is not None and buf_node.inputs[0] == true_net
