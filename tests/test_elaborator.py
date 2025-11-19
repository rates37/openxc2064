from openxc2064 import HDLElaborator, HDLValidationError
import pytest
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


def test_simple_module_and_ports():
    # define simple AST:
    parsed_modules = [
        Module(
            name="simple_module",
            ports=[
                Port(name="in1", direction=Direction.INPUT, is_reg=False),
                Port(name="out1", direction=Direction.OUTPUT, is_reg=False),
            ],
            contents=[
                WireDecl(name="internal_wire"),
                AssignStmt(
                    lhs=Identifier(name="out1"),
                    rhs=Identifier(name="in1"),
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)
    elaborator.validate()


def test_recursive_module_instantiation():
    # define AST with recursive module instantiation
    parsed_modules = [
        Module(
            name="top_module",
            ports=[
                Port(name="in1", direction=Direction.INPUT, is_reg=False),
                Port(name="out1", direction=Direction.OUTPUT, is_reg=False),
            ],
            contents=[
                Instance(
                    module_name="top_module",
                    instance_name="child1",
                    connections=[
                        Connection(port_name="in_child", expr=Identifier(name="in1")),
                        Connection(port_name="out_child", expr=Identifier(name="out1")),
                    ],
                    params=[],
                )
            ],
        ),
    ]
    elaborator = HDLElaborator(modules=parsed_modules)

    with pytest.raises(HDLValidationError):
        elaborator.validate()


def test_module_pair_binary_recursion():
    # define AST with two modules instantiating each other
    parsed_modules = [
        Module(
            name="module_a",
            ports=[
                Port(name="in_a", direction=Direction.INPUT, is_reg=False),
                Port(name="out_a", direction=Direction.OUTPUT, is_reg=False),
            ],
            contents=[
                Instance(
                    module_name="module_b",
                    instance_name="inst_b",
                    connections=[
                        Connection(port_name="in_b", expr=Identifier(name="in_a")),
                        Connection(port_name="out_b", expr=Identifier(name="out_a")),
                    ],
                    params=[],
                )
            ],
        ),
        Module(
            name="module_b",
            ports=[
                Port(name="in_b", direction=Direction.INPUT, is_reg=False),
                Port(name="out_b", direction=Direction.OUTPUT, is_reg=False),
            ],
            contents=[
                Instance(
                    module_name="module_a",
                    instance_name="inst_a",
                    connections=[
                        Connection(port_name="in_a", expr=Identifier(name="in_b")),
                        Connection(port_name="out_a", expr=Identifier(name="out_b")),
                    ],
                    params=[],
                )
            ],
        ),
    ]
    elaborator = HDLElaborator(modules=parsed_modules)

    with pytest.raises(HDLValidationError):
        elaborator.validate()
