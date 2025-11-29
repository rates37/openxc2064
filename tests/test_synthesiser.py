import pytest

from openxc2064.hdl import parse_hdl
from openxc2064.hdl.ast_nodes import *
from openxc2064.synthesis import (
    SymbolInfo,
    Synthesiser,
    SynthesisException,
    parse_verilog_literal,
    HDLElaborator,
)
from openxc2064.synthesis.rtl_nodes import LogicGate, DFF, Constant, Input, Net

# helper functions:


def create_symbol(
    name: str, width: int = 1, direction: Direction | None = None, is_reg: bool = False
) -> SymbolInfo:
    return SymbolInfo(
        name=name, is_reg=is_reg, msb=width - 1, lsb=0, direction=direction
    )


def create_mock_library(
    module_name: str,
    contents: list[WireDecl | RegDecl | AssignStmt | Instance | AlwaysComb | AlwaysSeq],
    symbols: dict[str, SymbolInfo],
) -> dict[str, tuple[Module, dict[str, SymbolInfo]]]:
    mod = Module(name=module_name, ports=[], contents=contents)
    return {module_name: (mod, symbols)}


#! Tests:


def test_parse_verilog_literal() -> None:
    # test the parse verilog literal auxiliary function:
    assert parse_verilog_literal("4'b1010") == (10, 4)
    assert parse_verilog_literal("8'hFF") == (0xFF, 8)
    assert parse_verilog_literal("32'd100") == (100, 32)
    assert parse_verilog_literal("10") == (10, 32)  # default width
    assert parse_verilog_literal("'b1000") == (8, 32)  # default width


def test_synth_basic_assign_and_ports() -> None:
    symbols = {
        "a": create_symbol("a", 1, Direction.INPUT),
        "b": create_symbol("b", 1, Direction.OUTPUT),
    }
    contents = [AssignStmt(lhs=Identifier("b"), rhs=Identifier("a"))]
    lib = create_mock_library("test", contents, symbols)

    synth = Synthesiser(lib)
    netlist = synth.synthesise("test")

    # Check inputs
    assert len(netlist.inputs) == 1
    assert netlist.inputs[0].name == "a"

    # Check outputs
    assert len(netlist.outputs) == 1
    assert netlist.outputs[0].name == "b"

    # Check Logic (should be a BUF gate)
    buffs = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "BUF"]
    assert len(buffs) == 1
    assert buffs[0].inputs[0].name == "a"
    assert buffs[0].outputs[0].name == "b"


def test_synth_binary_op_width_propagation() -> None:
    symbols = {
        "a": create_symbol("a", 4, Direction.INPUT),
        "b": create_symbol("b", 4, Direction.INPUT),
        "res_add": create_symbol("res_add", 4, Direction.OUTPUT),
        "res_eq": create_symbol("res_eq", 1, Direction.OUTPUT),
    }
    # res_add = a + b;
    # res_eq = a == b;
    contents = [
        AssignStmt(
            Identifier("res_add"), BinaryOp(Identifier("a"), "+", Identifier("b"))
        ),
        AssignStmt(
            Identifier("res_eq"), BinaryOp(Identifier("a"), "==", Identifier("b"))
        ),
    ]
    lib = create_mock_library("test", contents, symbols)

    synth = Synthesiser(lib)
    netlist = synth.synthesise("test")

    # find gate instances
    add_gate = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "ADD"]
    eq_gate = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "EQ"]

    # Verify add output width (Should be max of its inputs = max(4,4) = 4)
    assert len(add_gate) == 1
    assert len(add_gate[0].outputs) == 1
    assert add_gate[0].outputs[0].width == 4

    # Verify eq output width (Should be 1 since arithmetic == produces 0 or 1 single bit output)
    assert len(eq_gate) == 1
    assert len(eq_gate[0].outputs) == 1
    assert eq_gate[0].outputs[0].width == 1


def test_synth_unary_ops() -> None:
    symbols = {
        "a": create_symbol("a", 4, Direction.INPUT),
        "y_neg": create_symbol("y_neg", 4, Direction.OUTPUT),
        "y_not": create_symbol("y_not", 1, Direction.OUTPUT),
    }

    # y_neg = -a;
    # y_not = !a;
    contents = [
        AssignStmt(Identifier("y_neg"), UnaryOp("-", Identifier("a"))),
        AssignStmt(Identifier("y_not"), UnaryOp("!", Identifier("a"))),
    ]
    lib = create_mock_library("test", contents, symbols)
    synth = Synthesiser(lib)
    netlist = synth.synthesise("test")

    neg_gate = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "NEG"]
    not_gate = [
        n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "LOGIC_NOT"
    ]

    assert len(neg_gate) == 1
    assert len(not_gate) == 1

    assert neg_gate[0].outputs[0].width == 4  # width preserved
    assert not_gate[0].outputs[0].width == 1  # only 1 bit


def test_synth_slicing_indexing() -> None:
    symbols = {
        "bus": create_symbol("bus", 8, Direction.INPUT),
        "bit_out": create_symbol("bit_out", 1, Direction.OUTPUT),
        "slice_out": create_symbol("slice_out", 3, Direction.OUTPUT),
    }

    # bit_out = bus[2];
    # slice_out = bus[4:2]; (3 bits)
    contents = [
        AssignStmt(Identifier("bit_out"), Indexed(Identifier("bus"), index=Index("2"))),
        AssignStmt(
            Identifier("slice_out"), Indexed(Identifier("bus"), range=Range(4, 2))
        ),
    ]
    lib = create_mock_library("test", contents, symbols)
    synth = Synthesiser(lib)
    netlist = synth.synthesise("test")

    # Check Index Gate
    idx_gate = [
        n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "INDEX:2"
    ]
    assert len(idx_gate) == 1
    assert idx_gate[0].outputs[0].width == 1

    # Check Slice Gate
    slice_gate = [
        n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "SLICE:4:2"
    ]
    assert len(slice_gate) == 1
    assert slice_gate[0].outputs[0].width == 3  # 4,3,2 = 3 bits


def test_synth_constants() -> None:
    symbols = {"y": create_symbol("y", 4, Direction.OUTPUT)}
    contents = [AssignStmt(Identifier("y"), Number("4'b1001"))]
    lib = create_mock_library("test", contents, symbols)
    synth = Synthesiser(lib)
    netlist = synth.synthesise("test")

    const_node = [n for n in netlist.nodes if isinstance(n, Constant)]
    assert len(const_node) == 1
    assert const_node[0].value == 9
    assert const_node[0].outputs[0].width == 4


def test_synth_mux() -> None:
    symbols = {
        "sel": create_symbol("sel", 1, Direction.INPUT),
        "a": create_symbol("a", 4, Direction.INPUT),
        "b": create_symbol("b", 4, Direction.INPUT),
        "y": create_symbol("y", 4, Direction.OUTPUT),
    }

    # if (sel) y = a; else y = b;
    if_stmt = IfStmt(
        condition=Identifier("sel"),
        then_stmts=ProcAssignStmt(Identifier("y"), "=", Identifier("a")),
        else_stmts=ProcAssignStmt(Identifier("y"), "=", Identifier("b")),
    )
    contents = [AlwaysComb(stmt=if_stmt)]
    lib = create_mock_library("test", contents, symbols)

    synth = Synthesiser(lib)
    netlist = synth.synthesise("test")

    mux = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "MUX"]
    assert len(mux) == 1
    # MUX inputs = [Cond, Else, Then] -> [sel, b, a]
    mux_inputs = mux[0].inputs
    assert len(mux_inputs) == 3

    assert mux_inputs[0].name == "sel"
    assert mux_inputs[0].width == 1

    assert mux_inputs[1].name == "b"
    assert mux_inputs[1].width == 4

    assert mux_inputs[2].name == "a"
    assert mux_inputs[2].width == 4

    # MUX output width should match inputs
    assert len(mux[0].outputs) == 1
    assert mux[0].outputs[0].width == 4


def test_synth_dff() -> None:
    symbols = {
        "clk": create_symbol("clk", 1, Direction.INPUT),
        "d": create_symbol("d", 1, Direction.INPUT),
        "q": create_symbol("q", 1, Direction.OUTPUT, is_reg=True),
    }

    # always : seq @(negedge clk) q <= d;
    stmt = ProcAssignStmt(Identifier("q"), "<=", Identifier("d"))
    contents = [AlwaysSeq(edge="negedge", signal=Identifier("clk"), statements=stmt)]

    lib = create_mock_library("test", contents, symbols)
    synth = Synthesiser(lib)
    netlist = synth.synthesise("test")

    dff = [n for n in netlist.nodes if isinstance(n, DFF)]
    assert len(dff) == 1
    assert dff[0].edge == "negedge"
    assert len(dff[0].inputs) == 2
    assert dff[0].inputs[0].name == "d"
    assert dff[0].inputs[1].name == "clk"


def test_synth_submodule() -> None:
    sub_syms = {
        "in_sig": create_symbol("in_sig", 1, Direction.INPUT),
        "out_sig": create_symbol("out_sig", 1, Direction.OUTPUT),
    }
    sub_contents = [
        AssignStmt(Identifier("out_sig"), UnaryOp("!", Identifier("in_sig")))
    ]
    sub_mod = Module("inv", [], sub_contents)

    # Top level Module
    top_syms = {
        "a": create_symbol("a", 1, Direction.INPUT),
        "z": create_symbol("z", 1, Direction.OUTPUT),
    }
    # inv u0 (.in_sig(a), .out_sig(z));
    inst = Instance(
        module_name="inv",
        instance_name="u0",
        params=[],
        connections=[
            Connection("in_sig", Identifier("a")),
            Connection("out_sig", Identifier("z")),
        ],
    )
    top_mod = Module("top", [], [inst])

    lib = {"inv": (sub_mod, sub_syms), "top": (top_mod, top_syms)}

    synth = Synthesiser(lib)
    netlist = synth.synthesise("top")

    # Look for flattened names
    # Logic: a -> BUF -> u0_in_sig -> LOGIC_NOT -> u0_out_sig -> BUF -> z
    flattened_nets = [n.name for n in netlist.nets]
    assert "u0_in_sig" in flattened_nets
    assert "u0_out_sig" in flattened_nets


#! Test for Synthesis Exceptions:
def test_synth_error_unknown_signal() -> None:
    symbols = {}
    contents = [AssignStmt(Identifier("y"), Identifier("x"))]  # x undefined
    lib = create_mock_library("test", contents, symbols)
    synth = Synthesiser(lib)

    with pytest.raises(SynthesisException) as exc:
        synth.synthesise("test")
    assert "Unknown signal 'x'" in str(exc.value)


def test_synth_error_unknown_module() -> None:
    inst = Instance("bad_mod", [], "u0", [])
    lib = create_mock_library("test", [inst], {})
    synth = Synthesiser(lib)

    with pytest.raises(SynthesisException) as exc:
        synth.synthesise("test")
    assert "Unknown module 'bad_mod'" in str(exc.value)


def test_synth_error_unknown_port() -> None:
    sub_mod = Module("sub", [], [])
    lib = {
        "sub": (sub_mod, {}),
        "top": (
            Module(
                "top",
                [],
                [Instance("sub", [], "u0", [Connection("bad_port", Identifier("x"))])],
            ),
            {"x": create_symbol("x", 1, Direction.INPUT)},
        ),
    }
    synth = Synthesiser(lib)

    with pytest.raises(SynthesisException) as exc:
        synth.synthesise("top")
    assert "Port 'bad_port' not found" in str(exc.value)


def test_synth_error_indexed_missing_range() -> None:
    invalid_idx = Indexed(base=Identifier("a"), index=None, range=None)
    contents = [AssignStmt(Identifier("b"), invalid_idx)]
    symbols = {
        "a": create_symbol("a", 4, Direction.INPUT),
        "b": create_symbol("b", 1, Direction.OUTPUT),
    }
    lib = create_mock_library("test", contents, symbols)
    synth = Synthesiser(lib)

    with pytest.raises(SynthesisException) as exc:
        synth.synthesise("test")
    assert "Indexed expression missing index or range" in str(exc.value)


#! Integration tests with Parser/Elaborator
# Same tests as above, but using the parser and elaborator
#  rather than manually constructing the elaborator output


def test_int_synth_basic_assign_and_ports() -> None:
    HDL_CONTENTS = """module test(input a, output b);
    assign b = a;
endmodule"""
    ast = parse_hdl(HDL_CONTENTS)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("test")

    # Check inputs
    assert len(netlist.inputs) == 1
    assert netlist.inputs[0].name == "a"

    # Check outputs
    assert len(netlist.outputs) == 1
    assert netlist.outputs[0].name == "b"

    # Check Logic (should be a BUF gate)
    buffs = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "BUF"]
    assert len(buffs) == 1
    assert buffs[0].inputs[0].name == "a"
    assert buffs[0].outputs[0].name == "b"


def test_int_synth_binary_op_width_propagation() -> None:
    HDL_CONTENTS = """module test(input [3:0] a, input [3:0] b, output [3:0] res_add, output res_eq);
    assign res_add = a+b;
    assign res_eq = a == b;
endmodule"""
    ast = parse_hdl(HDL_CONTENTS)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("test")

    # find gate instances
    add_gate = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "ADD"]
    eq_gate = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "EQ"]

    # Verify add output width (Should be max of its inputs = max(4,4) = 4)
    assert len(add_gate) == 1
    assert len(add_gate[0].outputs) == 1
    assert add_gate[0].outputs[0].width == 4

    # Verify eq output width (Should be 1 since arithmetic == produces 0 or 1 single bit output)
    assert len(eq_gate) == 1
    assert len(eq_gate[0].outputs) == 1
    assert eq_gate[0].outputs[0].width == 1


def test_int_synth_unary_ops() -> None:
    HDL_CONTENTS = """module test(input [3:0] a, output [3:0] y_neg, output y_not);
    assign y_neg = -a;
    assign y_not = !a;
endmodule"""
    ast = parse_hdl(HDL_CONTENTS)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("test")

    neg_gate = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "NEG"]
    not_gate = [
        n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "LOGIC_NOT"
    ]

    assert len(neg_gate) == 1
    assert len(not_gate) == 1

    assert neg_gate[0].outputs[0].width == 4  # width preserved
    assert not_gate[0].outputs[0].width == 1  # only 1 bit


def test_int_synth_slicing_indexing() -> None:
    HDL_CONTENTS = """module test(input [7:0] bus, output [2:0] slice_out, output bit_out);
    assign bit_out = bus[2];
    assign slice_out = bus[4:2];
endmodule"""
    ast = parse_hdl(HDL_CONTENTS)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("test")

    # Check Index Gate
    idx_gate = [
        n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "INDEX:2"
    ]
    assert len(idx_gate) == 1
    assert idx_gate[0].outputs[0].width == 1

    # Check Slice Gate
    slice_gate = [
        n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "SLICE:4:2"
    ]
    assert len(slice_gate) == 1
    assert slice_gate[0].outputs[0].width == 3  # 4,3,2 = 3 bits


def test_int_synth_constants() -> None:
    HDL_CONTENTS = """module test(output [3:0] y);
    assign y = 4'b1001;
endmodule"""
    ast = parse_hdl(HDL_CONTENTS)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("test")

    const_node = [n for n in netlist.nodes if isinstance(n, Constant)]
    assert len(const_node) == 1
    assert const_node[0].value == 9
    assert const_node[0].outputs[0].width == 4


def test_int_synth_mux() -> None:
    HDL_CONTENTS = """module test(input sel, input [3:0] a, input [3:0] b, output reg [3:0] y);
    always : comb begin
        if (sel)
            y = a;
        else
            y = b;
    end
endmodule"""
    ast = parse_hdl(HDL_CONTENTS)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("test")

    mux = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "MUX"]
    assert len(mux) == 1
    # MUX inputs = [Cond, Else, Then] -> [sel, b, a]
    mux_inputs = mux[0].inputs
    assert len(mux_inputs) == 3

    assert mux_inputs[0].name == "sel"
    assert mux_inputs[0].width == 1

    assert mux_inputs[1].name == "b"
    assert mux_inputs[1].width == 4

    assert mux_inputs[2].name == "a"
    assert mux_inputs[2].width == 4

    # MUX output width should match inputs
    assert len(mux[0].outputs) == 1
    assert mux[0].outputs[0].width == 4


def test_int_synth_dff() -> None:
    HDL_CONTENTS = """module test(input clk, input d, output reg q);
    always : seq @(negedge clk) 
        q <= d;
endmodule"""
    ast = parse_hdl(HDL_CONTENTS)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("test")

    dff = [n for n in netlist.nodes if isinstance(n, DFF)]
    assert len(dff) == 1
    assert dff[0].edge == "negedge"
    assert len(dff[0].inputs) == 2
    assert dff[0].inputs[0].name == "d"
    assert dff[0].inputs[1].name == "clk"


def test_int_synth_submodule() -> None:
    HDL_CONTENTS = """module inv(input in_sig, output out_sig);
    assign out_sig = !in_sig;
endmodule

module test(input a, output z);
    inv u0 (.in_sig(a), .out_sig(z));
endmodule
"""
    ast = parse_hdl(HDL_CONTENTS)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("test")

    # Look for flattened names
    # Logic: a -> BUF -> u0_in_sig -> LOGIC_NOT -> u0_out_sig -> BUF -> z
    flattened_nets = [n.name for n in netlist.nets]
    assert "u0_in_sig" in flattened_nets
    assert "u0_out_sig" in flattened_nets


if __name__ == "__main__":
    test_int_synth_submodule()
