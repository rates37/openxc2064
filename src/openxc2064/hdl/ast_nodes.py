"""
HDL AST Node Definitions for openxc2064 toolchain.
Defines data structures representing HDL constructs."""

from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Identifier:
    name: str


@dataclass
class Number:
    value: str


@dataclass
class Range:
    msb: int
    lsb: int


@dataclass
class Index:
    index: str


class Direction(Enum):
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"


@dataclass
class Port:
    direction: Direction
    name: str
    range: Range | None = None
    is_reg: bool = False


@dataclass
class WireDecl:
    name: str
    range: Range | None = None


@dataclass
class RegDecl:
    name: str
    range: Range | None = None


@dataclass
class UnaryOp:
    op: str
    operand: "Expression"


@dataclass
class BinaryOp:
    left: "Expression"
    op: str
    right: "Expression"


@dataclass
class ParenExpr:
    expr: "Expression"


@dataclass
class Indexed:
    base: Identifier
    index: Index | None = None
    range: Range | None = None


Expression = Identifier | Number | Indexed | UnaryOp | BinaryOp | ParenExpr


@dataclass
class AssignStmt:
    lhs: Identifier | Indexed
    rhs: Expression


@dataclass
class Param:
    name: str
    value: Expression


@dataclass
class Connection:
    port_name: str
    expr: Expression


@dataclass
class Instance:
    module_name: str
    params: list[Param] = []
    instance_name: str
    connections: list[Connection]


@dataclass
class ProcAssignStmt:
    target: Identifier | Indexed
    op: str  # is either = or <=
    expr: Expression


@dataclass
class IfStmt:
    condition: Expression
    then_stmts: "Statement"
    else_stmts: "Statement" | None = None


@dataclass
class BlockStmt:
    statements: list["Statement"]


Statement = ProcAssignStmt | IfStmt | BlockStmt


@dataclass
class AlwaysComb:
    statements: list[Identifier | Indexed]
    stmt: Statement


@dataclass
class AlwaysSeq:
    edge: str
    signal: Identifier | Indexed
    statements: Statement


@dataclass
class Module:
    name: str
    ports: list[Port] = []
    contents: list[WireDecl | RegDecl | AssignStmt | Instance | AlwaysComb | AlwaysSeq]
