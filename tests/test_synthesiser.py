import pytest

from openxc2064.hdl.ast_nodes import *
from openxc2064.synthesis import SymbolInfo
from openxc2064.synthesis import Synthesiser, SynthesisException, parse_verilog_literal
from openxc2064.synthesis.rtl_nodes import LogicGate, DFF, Constant, Input, Net

# helper functions:


def create_symbol(name: str, width: int = 1, direction: Direction | None = None, is_reg: bool = False) -> SymbolInfo:
    return SymbolInfo(name=name, is_reg=is_reg, msb=width-1, lsb=0, direction=direction)


def create_mock_library(
    module_name: str,
    contents: list[WireDecl | RegDecl | AssignStmt | Instance | AlwaysComb | AlwaysSeq],
    symbols: dict[str, SymbolInfo]
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
        "b": create_symbol("b", 1, Direction.OUTPUT)
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
        "res_eq": create_symbol("res_eq", 1, Direction.OUTPUT)
    }
    # res_add = a + b;
    # res_eq = a == b;
    contents = [
        AssignStmt(Identifier("res_add"), BinaryOp(
            Identifier("a"), "+", Identifier("b"))),
        AssignStmt(Identifier("res_eq"), BinaryOp(
            Identifier("a"), "==", Identifier("b")))
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
    not_gate = [n for n in netlist.nodes if isinstance(n, LogicGate) and n.op == "LOGIC_NOT"]

    assert len(neg_gate) == 1
    assert len(not_gate) == 1

    assert neg_gate[0].outputs[0].width == 4 # width preserved
    assert not_gate[0].outputs[0].width == 1 # only 1 bit
