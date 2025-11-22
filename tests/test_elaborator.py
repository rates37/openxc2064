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

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "top_module" in str(e.value)


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

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "module_a" in str(e.value)
    assert "module_b" in str(e.value)


def test_duplicate_input_port():
    parsed_modules = [
        Module(
            name="dup_input_module",
            ports=[
                Port(name="in1", direction=Direction.INPUT, is_reg=False),
                Port(name="in1", direction=Direction.INPUT, is_reg=False),  # duplicate
                Port(name="out1", direction=Direction.OUTPUT, is_reg=False),
            ],
            contents=[],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
        # check error message contains the conflicting name
    assert "in1" in str(e.value)


def test_duplicate_output_port():
    parsed_modules = [
        Module(
            name="dup_output_module",
            ports=[
                Port(name="in1", direction=Direction.INPUT, is_reg=False),
                Port(name="out1", direction=Direction.OUTPUT, is_reg=False),
                Port(
                    name="out1", direction=Direction.OUTPUT, is_reg=False
                ),  # duplicate
            ],
            contents=[],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
        # check error message contains the conflicting name
    assert "out1" in str(e.value)


def test_duplicate_wire_declaration():
    parsed_modules = [
        Module(
            name="dup_wire_module",
            ports=[
                Port(name="in1", direction=Direction.INPUT, is_reg=False),
                Port(name="out1", direction=Direction.OUTPUT, is_reg=False),
            ],
            contents=[
                WireDecl(name="internal_wire"),
                WireDecl(name="internal_wire"),  # duplicate
            ],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
        # check error message contains the conflicting name
    assert "internal_wire" in str(e.value)


def test_duplicate_reg_declaration():
    parsed_modules = [
        Module(
            name="dup_reg_module",
            ports=[
                Port(name="in1", direction=Direction.INPUT, is_reg=False),
                Port(name="out1", direction=Direction.OUTPUT, is_reg=False),
            ],
            contents=[
                RegDecl(name="internal_reg"),
                RegDecl(name="internal_reg"),  # duplicate
            ],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
        # check error message contains the conflicting name
    assert "internal_reg" in str(e.value)


def test_wire_named_same_as_port():
    parsed_modules = [
        Module(
            name="wire_port_conflict_module",
            ports=[
                Port(name="in1", direction=Direction.INPUT, is_reg=False),
                Port(name="out1", direction=Direction.OUTPUT, is_reg=False),
            ],
            contents=[
                WireDecl(name="in1"),  # conflicts with port name
            ],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
        # check error message contains the conflicting name
    assert "in1" in str(e.value)


def test_assign_undeclared_lhs():
    parsed_modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("a"),
                AssignStmt(lhs=Identifier("b"), rhs=Identifier("a")),
            ],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "'b'" in str(e.value)


def test_assign_to_reg():
    parsed_modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("w"),
                RegDecl("r"),
                AssignStmt(lhs=Identifier("r"), rhs=Identifier("w")),
            ],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "'r'" in str(e.value)


def test_assign_to_output():
    parsed_modules = [
        Module(
            name="mod",
            ports=[Port(Direction.OUTPUT, name="out")],
            contents=[
                WireDecl("w"),
                AssignStmt(lhs=Identifier("out"), rhs=Identifier("w")),
            ],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)
    elaborator.validate()  # should not raise an error


def test_assign_to_input():
    parsed_modules = [
        Module(
            name="mod",
            ports=[Port(Direction.INPUT, name="input_assign")],
            contents=[
                WireDecl("w"),
                AssignStmt(lhs=Identifier("input_assign"), rhs=Identifier("w")),
            ],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "'input_assign'" in str(e.value)


def test_undeclared_identifier():
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("w"),
                AssignStmt(lhs=Identifier("w"), rhs=Identifier("undefined_signal")),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "'undefined_signal'" in str(e.value)


def test_undeclared_indexed_identifier():
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("w"),
                AssignStmt(
                    lhs=Identifier("w"),
                    rhs=Indexed(base=Identifier("missing"), index=Index("0")),
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "'missing'" in str(e.value)


def test_undeclared_identifier_unary_op():
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("w"),
                AssignStmt(
                    lhs=Identifier("w"),
                    rhs=UnaryOp(op="!", operand=Identifier("missing")),
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "'missing'" in str(e.value)


def test_undeclared_identifier_binary_op():
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("w"),
                WireDecl("known"),
                AssignStmt(
                    lhs=Identifier("w"),
                    rhs=BinaryOp(
                        left=Identifier("known"), op="+", right=Identifier("missing")
                    ),
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "'missing'" in str(e.value)


def test_undeclared_indexed_unary_op():
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("w"),
                AssignStmt(
                    lhs=Identifier("w"),
                    rhs=UnaryOp(
                        op="!",
                        operand=Indexed(
                            base=Identifier("missing_arr"), index=Index("1")
                        ),
                    ),
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "'missing_arr'" in str(e.value)


def test_undeclared_indexed_binary_op():
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("w"),
                WireDecl("a"),
                AssignStmt(
                    lhs=Identifier("w"),
                    rhs=BinaryOp(
                        left=Identifier("a"),
                        op="&&",
                        right=Indexed(base=Identifier("missing_arr"), index=Index("0")),
                    ),
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)

    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()

    assert "'missing_arr'" in str(e.value)


def test_always_comb_valid():
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                RegDecl("r"),
                WireDecl("w"),
                AlwaysComb(
                    stmt=ProcAssignStmt(
                        target=Identifier("r"), op="=", expr=Identifier("w")
                    )
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)
    elaborator.validate()


def test_always_comb_assign_to_wire():
    """Test that procedural assignment (inside always) cannot target a Wire."""
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("w_in"),
                WireDecl("w_out"),
                AlwaysComb(
                    stmt=ProcAssignStmt(
                        target=Identifier("w_out"), op="=", expr=Identifier("w_in")
                    )
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)
    # Expecting error because procedural assignments must target REGs
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "w_out" in str(e.value)


def test_always_seq_valid():
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                WireDecl("clk"),
                WireDecl("d"),
                RegDecl("q"),
                AlwaysSeq(
                    edge="posedge",
                    signal=Identifier("clk"),
                    statements=ProcAssignStmt(
                        target=Identifier("q"), op="<=", expr=Identifier("d")
                    ),
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)
    elaborator.validate()


def test_always_seq_undeclared_sensitivity():
    modules = [
        Module(
            name="mod",
            ports=[],
            contents=[
                RegDecl("q"),
                AlwaysSeq(
                    edge="posedge",
                    signal=Identifier("clk_missing"),
                    statements=ProcAssignStmt(
                        target=Identifier("q"), op="<=", expr=Number("0")
                    ),
                ),
            ],
        )
    ]
    elaborator = HDLElaborator(modules)
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "clk_missing" in str(e.value)


def test_instantiating_unknown_module():
    # test instantiating a module that isn't declared
    modules = [
        Module(
            name="top",
            ports=[],
            contents=[
                Instance(
                    module_name="missing_child",
                    instance_name="u0",
                    params=[],
                    connections=[],
                )
            ],
        )
    ]
    elaborator = HDLElaborator(modules)
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "missing_child" in str(e.value)


def test_instance_port_mismatch():
    # test connecting to a port that doesn't exist on the module
    child = Module(name="child", ports=[], contents=[])
    top = Module(
        name="top",
        ports=[],
        contents=[
            Instance(
                module_name="child",
                instance_name="u0",
                params=[],
                connections=[Connection(port_name="bad_port", expr=Number("1"))],
            )
        ],
    )
    elaborator = HDLElaborator([child, top])
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "bad_port" in str(e.value)


def test_instance_output_driving_reg():
    # test that output port of a module instance cannot drive a reg in the parent
    child = Module(
        name="child", ports=[Port(name="out", direction=Direction.OUTPUT)], contents=[]
    )
    top = Module(
        name="top",
        ports=[],
        contents=[
            RegDecl("r_val"),
            Instance(
                module_name="child",
                instance_name="u0",
                params=[],
                connections=[Connection(port_name="out", expr=Identifier("r_val"))],
            ),
        ],
    )
    elaborator = HDLElaborator([child, top])
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "r_val" in str(e.value)


def test_instance_output_driving_constant():
    # test that output port can't be connected to a constant number
    child = Module(
        name="child", ports=[Port(name="out", direction=Direction.OUTPUT)], contents=[]
    )
    top = Module(
        name="top",
        ports=[],
        contents=[
            Instance(
                module_name="child",
                instance_name="u0",
                params=[],
                connections=[Connection(port_name="out", expr=Number("1"))],
            )
        ],
    )
    elaborator = HDLElaborator([child, top])
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()


def test_two_drivers_for_signal():
    # test where two separate assign statements drive a single wire
    parsed_modules = [
        Module(
            name="mod",
            ports=[Port(Direction.OUTPUT, name="out")],
            contents=[
                WireDecl("w"),
                WireDecl("x"),
                AssignStmt(lhs=Identifier("out"), rhs=Identifier("w")),
                AssignStmt(lhs=Identifier("out"), rhs=Identifier("x")),
            ],
        )
    ]
    elaborator = HDLElaborator(modules=parsed_modules)
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()


def test_two_drivers_assign_instance():
    child = Module(
        name="child", ports=[Port(Direction.OUTPUT, name="c_out")], contents=[]
    )

    top = Module(
        name="top",
        ports=[],
        contents=[
            WireDecl("w"),
            Instance(
                module_name="child",
                instance_name="u0",
                params=[],
                connections=[Connection("c_out", Identifier("w"))],
            ),
            AssignStmt(lhs=Identifier("w"), rhs=Number("0")),
        ],
    )
    elaborator = HDLElaborator([child, top])
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "w" in str(e.value)


def test_two_drivers_always_always():
    mod = Module(
        name="mod",
        ports=[],
        contents=[
            RegDecl("r"),
            WireDecl("clk"),
            AlwaysSeq(
                edge="posedge",
                signal=Identifier("clk"),
                statements=ProcAssignStmt(Identifier("r"), "<=", Number("1")),
            ),
            AlwaysSeq(
                edge="posedge",
                signal=Identifier("clk"),
                statements=ProcAssignStmt(Identifier("r"), "<=", Number("0")),
            ),
        ],
    )
    elaborator = HDLElaborator([mod])
    with pytest.raises(HDLValidationError) as e:
        elaborator.validate()
    assert "r" in str(e.value)


def test_single_driver_multiple_assign_single_block():
    mod = Module(
        name="mod",
        ports=[],
        contents=[
            RegDecl("r"),
            WireDecl("cond"),
            AlwaysComb(
                stmt=BlockStmt(
                    [
                        ProcAssignStmt(Identifier("r"), "=", Number("0")),
                        # 2nd assignment in the same block: Should NOT error
                        IfStmt(
                            condition=Identifier("cond"),
                            then_stmts=ProcAssignStmt(
                                Identifier("r"), "=", Number("1")
                            ),
                        ),
                    ]
                )
            ),
        ],
    )
    elaborator = HDLElaborator([mod])
    elaborator.validate()


def test_partial_assignment_collision():
    mod = Module(
        name="mod",
        ports=[],
        contents=[
            WireDecl("bus", Range(1, 0)),
            # Assign bit 0
            AssignStmt(lhs=Indexed(Identifier("bus"), Index("0")), rhs=Number("0")),
            # Assign bit 1 - Collision on base identifier 'bus'
            AssignStmt(lhs=Indexed(Identifier("bus"), Index("1")), rhs=Number("1")),
        ],
    )
    elaborator = HDLElaborator([mod])
    elaborator.validate()  # shouldn't error since bit 0 and bit 1 of the 'bus' identifier are separate signals


if __name__ == "__main__":
    test_single_driver_multiple_assign_single_block()
