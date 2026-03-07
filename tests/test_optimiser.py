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


def test_constant_folding_gates_exhaustive():
    nl = Netlist(module_name="test_mod")
    in_a = nl.create_net("a")
    nl.add_input("a", in_a)

    c0 = nl.create_net("c0")
    c1 = nl.create_net("c1")
    nl.add_const(0, c0)
    nl.add_const(1, c1)

    # 1 AND 1 = 1
    out_and11 = nl.create_net("out_and11")
    nl.add_logic("AND", [c1, c1], [out_and11])

    # A AND 1 = A
    out_and_a1 = nl.create_net("out_and_a1")
    nl.add_logic("AND", [in_a, c1], [out_and_a1])

    # 0 OR 0 = 0
    out_or00 = nl.create_net("out_or00")
    nl.add_logic("OR", [c0, c0], [out_or00])

    # A OR 1 = 1
    out_or_a1 = nl.create_net("out_or_a1")
    nl.add_logic("OR", [in_a, c1], [out_or_a1])

    # Const XOR Const = 1 ^ 0 = 1
    out_xor_c = nl.create_net("out_xor_c")
    nl.add_logic("XOR", [c1, c0], [out_xor_c])

    # A XOR 0 = A
    out_xor_a0 = nl.create_net("out_xor_a0")
    nl.add_logic("XOR", [in_a, c0], [out_xor_a0])

    # A XOR 1 = NOT A
    out_xor_a1 = nl.create_net("out_xor_a1")
    nl.add_logic("XOR", [in_a, c1], [out_xor_a1])

    # NOT Const
    out_not_c = nl.create_net("out_not_c")
    nl.add_logic("NOT", [c1], [out_not_c])

    # BUF Const
    out_buf_c = nl.create_net("out_buf_c")
    nl.add_logic("BUF", [c0], [out_buf_c])

    nl.outputs.extend(
        [
            out_and11,
            out_and_a1,
            out_or00,
            out_or_a1,
            out_xor_c,
            out_xor_a0,
            out_xor_a1,
            out_not_c,
            out_buf_c,
        ]
    )

    opt = Optimiser()
    opt.optimise(nl)

    # Checks:
    # out_and11 -> 1
    assert isinstance(out_and11.source, Constant) and out_and11.source.value == 1
    # out_and_a1 -> A
    assert out_and_a1.source.op == "BUF" and out_and_a1.source.inputs[0] == in_a
    # out_or00 -> 0
    assert isinstance(out_or00.source, Constant) and out_or00.source.value == 0
    # out_or_a1 -> 1
    assert isinstance(out_or_a1.source, Constant) and out_or_a1.source.value == 1
    # out_xor_c -> 1
    assert isinstance(out_xor_c.source, Constant) and out_xor_c.source.value == 1
    # out_xor_a0 -> A
    assert out_xor_a0.source.op == "BUF" and out_xor_a0.source.inputs[0] == in_a
    # out_xor_a1 -> ~A
    assert out_xor_a1.source.op == "NOT" and out_xor_a1.source.inputs[0] == in_a
    # out_not_c -> 0
    assert isinstance(out_not_c.source, Constant) and out_not_c.source.value == 0
    # out_buf_c -> 0
    assert isinstance(out_buf_c.source, Constant) and out_buf_c.source.value == 0


def test_constant_folding_mux_advanced():
    nl = Netlist(module_name="test_mod")
    sel = nl.create_net("sel")
    t = nl.create_net("t")
    f = nl.create_net("f")
    nl.add_input("sel", sel)
    nl.add_input("t", t)
    nl.add_input("f", f)

    c0 = nl.create_net("c0")
    c1 = nl.create_net("c1")
    nl.add_const(0, c0)
    nl.add_const(1, c1)

    # MUX with sel=0 -> f
    out_m0 = nl.create_net("out_m0")
    nl.add_logic("MUX", [c0, t, f], [out_m0])

    # MUX with t=1, f=0 -> sel
    out_m_bool1 = nl.create_net("out_m_bool1")
    nl.add_logic("MUX", [sel, c1, c0], [out_m_bool1])

    # MUX with t=0, f=1 -> ~sel
    out_m_bool2 = nl.create_net("out_m_bool2")
    nl.add_logic("MUX", [sel, c0, c1], [out_m_bool2])

    nl.outputs.extend([out_m0, out_m_bool1, out_m_bool2])

    opt = Optimiser()
    opt.optimise(nl)

    # Checks:
    assert out_m0.source.op == "BUF" and out_m0.source.inputs[0] == f
    assert out_m_bool1.source.op == "BUF" and out_m_bool1.source.inputs[0] == sel
    assert out_m_bool2.source.op == "NOT" and out_m_bool2.source.inputs[0] == sel


def test_integration_optimiser():
    hdl_code = """
    module top(input a, input b, output out1, output out2);
        wire unused;
        assign unused = a & b;  // Dead code
        
        assign out1 = a | 1;    // Constant folded to 1
        assign out2 = b ^ 0;    // Constant folded to b
    endmodule
    """
    ast_tree = parse_hdl(hdl_code)
    elaborator = HDLElaborator(ast_tree)
    elaborator.validate()

    syn = Synthesiser(elaborator.get_library())
    netlist = syn.synthesise("top")

    # Nodes before optimiser: Input(a), Input(b), Const(1), Const(0), AND, OR, XOR
    # 7  total

    opt = Optimiser()
    opt_nl = opt.optimise(netlist)

    ands = [n for n in opt_nl.nodes if getattr(n, "op", "") == "AND"]
    assert len(ands) == 0
    ors = [n for n in opt_nl.nodes if getattr(n, "op", "") == "OR"]
    assert len(ors) == 0
    xors = [n for n in opt_nl.nodes if getattr(n, "op", "") == "XOR"]
    assert len(xors) == 0

    consts = [n for n in opt_nl.nodes if isinstance(n, Constant)]
    assert len(consts) >= 1
    bufs = [n for n in opt_nl.nodes if getattr(n, "op", "") == "BUF"]
    assert len(bufs) == 2  # for the XOR replace + the assign BUF

    # verify out1 net source
    out1_net = next(n for n in opt_nl.outputs if n.name == "out1")
    assert isinstance(out1_net.source, Constant)
    assert out1_net.source.value == 1
