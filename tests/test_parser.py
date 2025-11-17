import pytest
from pathlib import Path
from lark import Lark, Transformer, Token

# Import everything from the files for local testing
from openxc2064.hdl import ASTBuilder, create_parser, parse_hdl
from openxc2064.hdl.ast_nodes import (
    Identifier,
    Number,
    Range,
    Index,
    Direction,
    Port,
    WireDecl,
    RegDecl,
    UnaryOp,
    BinaryOp,
    Indexed,
    AssignStmt,
    Param,
    Connection,
    Instance,
    ProcAssignStmt,
    IfStmt,
    BlockStmt,
    AlwaysComb,
    AlwaysSeq,
    Module,
)


# Helper: parse single module and return it
def parse_single_module(src: str) -> Module:
    mods = parse_hdl(src)
    assert isinstance(mods, list) and len(mods) == 1, "expected single module"
    return mods[0]


# ---------- Basic module and ports ----------
def test_simple_module_and_ports():
    src = "module m(input a, output b); endmodule"
    m = parse_single_module(src)
    assert isinstance(m, Module)
    assert m.name == "m"
    assert len(m.ports) == 2
    p0, p1 = m.ports

    # check first port:
    assert isinstance(p0, Port)
    assert p0.direction == Direction.INPUT
    assert p0.name == "a"
    assert not p0.is_reg

    # check second port:
    assert isinstance(p1, Port)
    assert p1.direction == Direction.OUTPUT
    assert p1.name == "b"
    assert not p1.is_reg


def test_port_with_reg():
    src = "module m(output reg out, input rst); endmodule"
    m = parse_single_module(src)
    assert len(m.ports) == 2
    p0, p1 = m.ports

    # check first port:
    assert p0.direction == Direction.OUTPUT
    assert p0.is_reg is True
    assert p0.name == "out"
    assert p0.range is None

    # check second port:
    assert p1.direction == Direction.INPUT
    assert p1.is_reg is False
    assert p1.name == "rst"
    assert p1.range is None


def test_port_with_range():
    src = "module m(output [7:0] out, input rst); endmodule"
    m = parse_single_module(src)
    assert len(m.ports) == 2
    p0, p1 = m.ports

    # check first port:
    assert p0.direction == Direction.OUTPUT
    assert p0.is_reg is False
    assert p0.name == "out"
    assert isinstance(p0.range, Range)
    assert p0.range.msb == 7 and p0.range.lsb == 0

    # check second port:
    assert p1.direction == Direction.INPUT
    assert p1.is_reg is False
    assert p1.name == "rst"
    assert p1.range is None


def test_port_with_reg_and_range():
    src = "module m(output reg [7:0] out, output reg flag, input rst); endmodule"
    m = parse_single_module(src)
    assert len(m.ports) == 3
    p0, p1, p2 = m.ports

    # check first port:
    assert p0.direction == Direction.OUTPUT
    assert p0.is_reg is True  # this assertion fails
    assert p0.name == "out"
    assert isinstance(p0.range, Range)
    assert p0.range.msb == 7 and p0.range.lsb == 0

    # check second port:
    assert p1.direction == Direction.OUTPUT
    assert p1.is_reg is True
    assert p1.name == "flag"
    assert p1.range is None

    # check third port:
    assert p2.direction == Direction.INPUT
    assert p2.is_reg is False
    assert p2.name == "rst"
    assert p2.range is None


# ---------- Wires, Registers and Assign Statements ----------
def test_wire_declaration():
    src = """
    module m(output flag);
        wire [3:0] data_bus;
        wire flag;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 2
    w0, w1 = m.contents

    # check first wire
    assert isinstance(w0, WireDecl)
    assert w0.name == "data_bus"
    assert isinstance(w0.range, Range)
    assert w0.range.msb == 3 and w0.range.lsb == 0

    # check second wire
    assert isinstance(w1, WireDecl)
    assert w1.name == "flag"
    assert w1.range is None


def test_reg_declaration():
    src = """
    module m(output reg flag);
        reg [7:0] status;
        reg enable;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 2
    r0, r1 = m.contents

    # check first reg
    assert isinstance(r0, RegDecl)
    assert r0.name == "status"
    assert isinstance(r0.range, Range)
    assert r0.range.msb == 7 and r0.range.lsb == 0

    # check second reg
    assert isinstance(r1, RegDecl)
    assert r1.name == "enable"
    assert r1.range is None


def test_assign_statement():
    src = """
    module m(output reg flag);
        wire [3:0] data_bus;
        assign data_bus = 4'b1010;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 2
    w0, a0 = m.contents

    # check wire
    assert isinstance(w0, WireDecl)
    assert w0.name == "data_bus"

    # check assign statement
    assert isinstance(a0, AssignStmt)
    assert isinstance(a0.lhs, Identifier)
    assert a0.lhs.name == "data_bus"
    assert isinstance(a0.rhs, Number)
    assert a0.rhs.value == "4'b1010"


def test_assign_to_ident_statement():
    src = """
    module m(input a);
      wire w;
      wire [3:0] bus;
      assign w = a;
      assign bus[3:0] = a;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 4
    _w0, _w1, a0, a1 = m.contents

    # check first assign statement
    assert isinstance(a0, AssignStmt)
    assert isinstance(a0.lhs, Identifier)
    assert a0.lhs.name == "w"
    assert isinstance(a0.rhs, Identifier)
    assert a0.rhs.name == "a"

    # check second assign statement
    assert isinstance(a1, AssignStmt)
    assert isinstance(a1.lhs, Indexed)
    assert a1.lhs.base.name == "bus"
    assert a1.lhs.index is None
    assert isinstance(a1.lhs.range, Range)
    assert a1.lhs.range.msb == 3 and a1.lhs.range.lsb == 0
    assert isinstance(a1.rhs, Identifier)
    assert a1.rhs.name == "a"


# ---------- ensure failures  ----------
def test_port_error_unrecognized_form_raises():
    bad_src = "module m(output unknown_keyword out); endmodule"
    with pytest.raises(Exception):
        parse_hdl(bad_src)


def test_missing_ports_is_error():
    #  Zero-argument module not allowed by grammar
    bad_src = "module m(); endmodule"
    with pytest.raises(Exception):
        parse_hdl(bad_src)


if __name__ == "__main__":
    test_assign_to_ident_statement()
