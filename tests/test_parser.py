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


def test_not_expression():
    src = """
    module m(input a, output b);
      wire not_a;
      assign not_a = !a;
      assign b = not_a;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 3
    _w0, a0, a1 = m.contents
    # check first assign statement
    assert isinstance(a0, AssignStmt)
    assert isinstance(a0.lhs, Identifier)
    assert a0.lhs.name == "not_a"
    assert isinstance(a0.rhs, UnaryOp)
    un_op = a0.rhs
    assert un_op.op == "!"
    assert isinstance(un_op.operand, Identifier)
    assert un_op.operand.name == "a"
    # check second assign statement
    assert isinstance(a1, AssignStmt)
    assert isinstance(a1.lhs, Identifier)
    assert a1.lhs.name == "b"
    assert isinstance(a1.rhs, Identifier)
    assert a1.rhs.name == "not_a"


def test_add_expression():
    src = """
    module m(input [3:0] a, input [3:0] b, output [4:0] sum);
      wire [4:0] temp_sum;
      assign temp_sum = a + b;
      assign sum = temp_sum;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 3
    _w0, a0, a1 = m.contents

    # check first assign statement
    assert isinstance(a0, AssignStmt)
    assert isinstance(a0.lhs, Identifier)
    assert a0.lhs.name == "temp_sum"
    assert isinstance(a0.rhs, BinaryOp)
    bin_op = a0.rhs
    assert bin_op.op == "+"
    assert isinstance(bin_op.left, Identifier)
    assert bin_op.left.name == "a"
    assert isinstance(bin_op.right, Identifier)
    assert bin_op.right.name == "b"

    # check second assign statement
    assert isinstance(a1, AssignStmt)
    assert isinstance(a1.lhs, Identifier)
    assert a1.lhs.name == "sum"
    assert isinstance(a1.rhs, Identifier)
    assert a1.rhs.name == "temp_sum"


def test_sub_expression():
    src = """
    module m(input [3:0] c, input [3:0] d, output [4:0] diff);
      wire [4:0] temp_diff;
      assign temp_diff = c - d;
      assign diff = temp_diff;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 3
    _w0, a0, a1 = m.contents

    # check first assign statement
    assert isinstance(a0, AssignStmt)
    assert isinstance(a0.lhs, Identifier)
    assert a0.lhs.name == "temp_diff"
    assert isinstance(a0.rhs, BinaryOp)
    bin_op = a0.rhs
    assert bin_op.op == "-"
    assert isinstance(bin_op.left, Identifier)
    assert bin_op.left.name == "c"
    assert isinstance(bin_op.right, Identifier)
    assert bin_op.right.name == "d"

    # check second assign statement
    assert isinstance(a1, AssignStmt)
    assert isinstance(a1.lhs, Identifier)
    assert a1.lhs.name == "diff"
    assert isinstance(a1.rhs, Identifier)
    assert a1.rhs.name == "temp_diff"


def test_mul_expression():
    src = """
    module m(input [3:0] x, input [3:0] y, output [7:0] prod);
      wire [7:0] temp_prod;
      assign temp_prod = x * y;
      assign prod = temp_prod;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 3
    _w0, a0, a1 = m.contents

    # check first assign statement
    assert isinstance(a0, AssignStmt)
    assert isinstance(a0.lhs, Identifier)
    assert a0.lhs.name == "temp_prod"
    assert isinstance(a0.rhs, BinaryOp)
    bin_op = a0.rhs
    assert bin_op.op == "*"
    assert isinstance(bin_op.left, Identifier)
    assert bin_op.left.name == "x"
    assert isinstance(bin_op.right, Identifier)
    assert bin_op.right.name == "y"

    # check second assign statement
    assert isinstance(a1, AssignStmt)
    assert isinstance(a1.lhs, Identifier)
    assert a1.lhs.name == "prod"
    assert isinstance(a1.rhs, Identifier)
    assert a1.rhs.name == "temp_prod"


def test_div_expression():
    src = """
    module m(input [7:0] p, input [7:0] q, output [7:0] quot);
      wire [7:0] temp_quot;
      assign temp_quot = p / q;
      assign quot = temp_quot;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 3
    _w0, a0, a1 = m.contents

    # check first assign statement
    assert isinstance(a0, AssignStmt)
    assert isinstance(a0.lhs, Identifier)
    assert a0.lhs.name == "temp_quot"
    assert isinstance(a0.rhs, BinaryOp)
    bin_op = a0.rhs
    assert bin_op.op == "/"
    assert isinstance(bin_op.left, Identifier)
    assert bin_op.left.name == "p"
    assert isinstance(bin_op.right, Identifier)
    assert bin_op.right.name == "q"

    # check second assign statement
    assert isinstance(a1, AssignStmt)
    assert isinstance(a1.lhs, Identifier)
    assert a1.lhs.name == "quot"
    assert isinstance(a1.rhs, Identifier)
    assert a1.rhs.name == "temp_quot"


def test_complex_expression():
    src = """
    module m(input [3:0] a, input [3:0] b, input [3:0] c, output [5:0] result);
      wire [5:0] temp_result;
      assign temp_result = (a + b) * c - 4;
      assign result = temp_result;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 3
    _w0, a0, a1 = m.contents

    # check first assign statement
    assert isinstance(a0, AssignStmt)
    assert isinstance(a0.lhs, Identifier)
    assert a0.lhs.name == "temp_result"
    assert isinstance(a0.rhs, BinaryOp)
    bin_op_sub = a0.rhs
    assert bin_op_sub.op == "-"
    assert isinstance(bin_op_sub.right, Number)
    assert bin_op_sub.right.value == "4"

    bin_op_mul = bin_op_sub.left
    assert isinstance(bin_op_mul, BinaryOp)
    assert bin_op_mul.op == "*"
    assert isinstance(bin_op_mul.right, Identifier)
    assert bin_op_mul.right.name == "c"

    paren_expr = bin_op_mul.left
    assert isinstance(paren_expr, BinaryOp)
    assert paren_expr.op == "+"
    assert isinstance(paren_expr.left, Identifier)
    assert paren_expr.left.name == "a"
    assert isinstance(paren_expr.right, Identifier)
    assert paren_expr.right.name == "b"

    # check second assign statement
    assert isinstance(a1, AssignStmt)
    assert isinstance(a1.lhs, Identifier)
    assert a1.lhs.name == "result"
    assert isinstance(a1.rhs, Identifier)
    assert a1.rhs.name == "temp_result"


def test_expression_precedence():
    src = """
    module m(input a, input b, input c, input d, input e, input f, input g, input h);
      assign out = a + b * (c - d) || e && !f == g;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 1
    expr = m.contents[0].rhs
    # top level should be '||'
    assert isinstance(expr, BinaryOp)
    assert expr.op == "||"
    # left side should be binop for addition:
    left = expr.left
    assert isinstance(left, BinaryOp)
    assert left.op == "+"
    # left.right should be binop for multiplication:
    mult = left.right
    assert isinstance(mult, BinaryOp)
    assert mult.op == "*"
    # mult.right should be paren expression:
    paren = mult.right
    assert isinstance(paren, BinaryOp)
    assert paren.op == "-"
    # right side should be binop for '&&'
    right = expr.right
    assert isinstance(right, BinaryOp)
    assert right.op == "&&"
    # right.right should be binop for '=='
    eq = right.right
    assert isinstance(eq, BinaryOp)
    assert eq.op == "=="
    # eq.right should be identifier 'g'
    assert isinstance(eq.right, Identifier)
    assert eq.right.name == "g"
    # eq.left should be unary op '!'
    not_f = eq.left
    assert isinstance(not_f, UnaryOp)
    assert not_f.op == "!"


def test_indexing_identifiers():
    src = """
    module m(input a);
      wire [7:0] bus;
      assign out = bus[3] + bus[7:0] + 42;
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 2
    _w0, a0 = m.contents
    # check assign statement
    assert isinstance(a0, AssignStmt)
    assert isinstance(a0.lhs, Identifier)
    assert a0.lhs.name == "out"

    # check rhs expression
    bin_op1 = a0.rhs
    assert isinstance(bin_op1, BinaryOp)
    assert bin_op1.op == "+"
    bin_op2 = bin_op1.left
    assert isinstance(bin_op2, BinaryOp)
    assert bin_op2.op == "+"

    # check first term: bus[3]
    indexed1 = bin_op2.left
    assert isinstance(indexed1, Indexed)
    assert indexed1.base.name == "bus"
    assert isinstance(indexed1.index, Index)
    assert indexed1.index.index == "3"
    assert indexed1.range is None

    # check second term: bus[7:0]
    indexed2 = bin_op2.right
    assert isinstance(indexed2, Indexed)
    assert indexed2.base.name == "bus"
    assert indexed2.index is None
    assert isinstance(indexed2.range, Range)
    assert indexed2.range.msb == 7 and indexed2.range.lsb == 0

    # check third term: 42
    number = bin_op1.right
    assert isinstance(number, Number)
    assert number.value == "42"


def test_instance_parsing():
    src = """
    module m(input a, output b);
      wire w;
      my_module inst1 (.in(a), .out(w));
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 2
    _w0, inst1 = m.contents

    # check instantiation
    assert isinstance(inst1, Instance)
    assert inst1.module_name == "my_module"
    assert inst1.instance_name == "inst1"
    assert len(inst1.params) == 0
    assert len(inst1.connections) == 2
    assert "in" in map(lambda x: x.port_name, inst1.connections)
    assert "out" in map(lambda x: x.port_name, inst1.connections)


def test_instance_with_params_parsing():
    src = """
    module m(input a, output b);
      my_module #(.WIDTH(8), .DEPTH(16)) inst2 (.in(a), .out(b));
    endmodule
    """
    m = parse_single_module(src)
    assert len(m.contents) == 1
    inst2 = m.contents[0]

    # check instantiation
    assert isinstance(inst2, Instance)
    assert inst2.module_name == "my_module"
    assert inst2.instance_name == "inst2"
    assert len(inst2.params) == 2
    param_names = [p.name for p in inst2.params]
    assert "WIDTH" in param_names
    assert "DEPTH" in param_names
    assert len(inst2.connections) == 2
    assert "in" in map(lambda x: x.port_name, inst2.connections)
    assert "out" in map(lambda x: x.port_name, inst2.connections)


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
    test_instance_with_params_parsing()
