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


# --- Fixtures ---
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


if __name__ == "__main__":
    test_port_with_reg_and_range()
