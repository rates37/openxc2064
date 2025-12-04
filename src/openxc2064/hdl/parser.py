from pathlib import Path
from lark import Lark, Transformer, Token
from .ast_nodes import *


GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"

with open(GRAMMAR_PATH) as f:
    hdl_grammar = f.read()


class ASTBuilder(Transformer):
    def IDENT(self, tok: Token) -> str:
        return str(tok)

    def NUMBER(self, tok: Token) -> str:
        return str(tok)

    def RANGE(self, tok: Token) -> Range:
        s = tok.value  # e.g. "[7:0]"
        msb, lsb = map(int, s.strip("[]").split(":"))
        return Range(msb=msb, lsb=lsb)

    def INDEX(self, tok: Token) -> Index:
        s = tok.value  # e.g. "[3]"
        idx = s.strip("[]")
        return Index(index=idx)

    def DIRECTION(self, tok: Token) -> Direction:
        return Direction(tok.value)

    def port(self, items: list) -> Port:
        """
        Possible input shapes are:
        [direction, "reg", name], e.g., ["output", "reg", "out_signal"
        [direction, "reg", range, name], e.g., ["output", "reg", "[3:0]", "out_bus"]
        """
        direction = items[0]
        if len(items) == 3:
            # Shape: [direction, maybe reg, name]
            _, reg_token, name = items
            return Port(
                direction=direction,
                name=name,
                is_reg=(reg_token is not None),
                range=None,
            )

        elif len(items) == 4:
            # Shape: [direction, maybe reg, range_or_name, name_or_range]
            _, reg_token, third, fourth = items

            if isinstance(third, Range):
                # Shape: [dir, reg|None, range, name]
                rng = third
                name = fourth
            else:
                # Shape: [dir, reg, name, ???]  <-- but this pattern cannot happen
                # because in the grammar, RANGE comes before IDENT when both exist
                raise ValueError(f"Unexpected port shape: {items}")

            return Port(
                direction=direction,
                name=name,
                is_reg=(reg_token is not None),
                range=rng,
            )

        else:
            raise ValueError(f"Unexpected port items length: {items}")

    def port_list(self, ports: list) -> list[Port]:
        return ports

    def ident_index(self, items: list) -> Indexed:
        ident, index = items
        return Indexed(base=Identifier(ident), index=index, range=None)

    def ident_range(self, items: list) -> Indexed:
        ident, rng = items
        return Indexed(base=Identifier(ident), index=None, range=rng)

    def ident_only(self, items: list) -> Identifier:
        return Identifier(name=items[0])

    def number_only(self, items: list) -> Number:
        return Number(value=items[0])

    # expressions
    def unary_op(self, items: list) -> UnaryOp:
        op_tok, operand = items
        op = str(op_tok) if isinstance(op_tok, Token) else op_tok
        return UnaryOp(op=op, operand=operand)

    def bin_op(self, items: list) -> BinaryOp:
        if len(items) == 3:
            left, op_tok, right = items
            op = str(op_tok) if isinstance(op_tok, Token) else op_tok
            return BinaryOp(left=left, op=op, right=right)
        if len(items) > 3 and len(items) % 2 == 1:
            left = items[0]
            for i in range(1, len(items), 2):
                op_tok = items[i]
                right = items[i + 1]
                op = str(op_tok) if isinstance(op_tok, Token) else op_tok
                left = BinaryOp(left=left, op=op, right=right)
            return left
        raise ValueError(f"Invalid binary operation with items: {items}")

    def expression(self, items: list) -> Expression:
        return items[0] if items else None

    # declarations:
    def wire_decl(self, items: list) -> WireDecl:
        if len(items) == 2 and isinstance(items[0], Range):
            rng, name = items
            return WireDecl(name=name, range=rng)
        return WireDecl(name=items[-1], range=None)

    def reg_decl(self, items: list) -> RegDecl:
        if len(items) == 2 and isinstance(items[0], Range):
            rng, name = items
            return RegDecl(name=name, range=rng)
        return RegDecl(name=items[-1], range=None)

    # continuous assignment
    def assign_stmt_lhs(self, items: list) -> Identifier | Indexed:
        if len(items) == 1:
            name = items[0]
            if isinstance(name, str):
                return Identifier(name=name)
            return name
        elif len(items) == 2:
            name, second = items[0], items[1]
            if isinstance(second, Index):
                return Indexed(base=Identifier(name), index=second, range=None)
            elif isinstance(second, Range):
                return Indexed(base=Identifier(name), index=None, range=second)
        raise ValueError(f"Invalid assign_stmt_lhs with items: {items}")

    def assign_stmt(self, items: list) -> AssignStmt:
        lhs, rhs = items
        return AssignStmt(lhs=lhs, rhs=rhs)

    # procedural assignment (inside always blocks)
    def proc_assign(self, items: list) -> ProcAssignStmt:
        if len(items) == 3:  # e.g., name, '=', expr
            name, op_tok, expr = items
            op = str(op_tok) if isinstance(op_tok, Token) else op_tok
            target = Identifier(name) if isinstance(name, str) else name
            return ProcAssignStmt(target=target, op=op, expr=expr)
        elif len(items) == 4:  # e.g., name, index/range, '=', expr
            name, second, op_tok, expr = items
            op = str(op_tok) if isinstance(op_tok, Token) else op_tok
            if isinstance(second, Index):
                target = Indexed(base=Identifier(name), index=second, range=None)
            elif isinstance(second, Range):
                target = Indexed(base=Identifier(name), index=None, range=second)
            else:
                target = Identifier(name)  # fallback
            return ProcAssignStmt(target=target, op=op, expr=expr)
        raise ValueError(f"Invalid proc_assign with items: {items}")

    def block(self, items: list) -> BlockStmt:
        return BlockStmt(statements=items)

    def if_stmt(self, items: list) -> IfStmt:
        if len(items) == 2:
            condition, then_stmts = items
            return IfStmt(condition=condition, then_stmts=then_stmts, else_stmts=None)
        elif len(items) == 3:
            condition, then_stmts, else_stmts = items
            return IfStmt(condition=condition, then_stmts=then_stmts, else_stmts=else_stmts)
        raise ValueError(f"Invalid if_stmt with items: {items}")

    def param(self, items: list) -> Param:
        name, value = items
        return Param(name=name, value=value)

    def param_list(self, items: list) -> list[Param]:
        return list(items)

    def connection(self, items: list) -> Connection:
        port_name, expr = items
        return Connection(port_name=port_name, expr=expr)

    def connection_list(self, items: list) -> list[Connection]:
        return list(items)

    def instance(self, items: list) -> Instance:
        module_name = items[0]
        idx = 1
        params = []
        if isinstance(items[idx], list):
            params = items[idx]
        idx += 1
        instance_name = items[idx]
        idx += 1

        connections = items[idx]

        return Instance(
            module_name=module_name,
            params=params,
            instance_name=instance_name,
            connections=connections,
        )

    def module_name(self, items: list) -> str:
        return items[0]

    def module_instance_name(self, items: list) -> str:
        return items[0]

    def sens_posedge(self, items: list) -> tuple[str, Identifier]:
        return ("posedge", Identifier(items[0]))

    def sens_negedge(self, items: list) -> tuple[str, Identifier]:
        return ("negedge", Identifier(items[0]))

    def always_comb(self, items: list) -> AlwaysComb:
        stmt = items[0]
        return AlwaysComb(stmt=stmt)

    def always_seq(self, items: list) -> AlwaysSeq:
        try:
            edge, signal = items[0]
            stmt = items[1]
            return AlwaysSeq(edge=edge, signal=signal, statements=stmt)
        except Exception:
            raise ValueError(f"Invalid always_seq with items: {items}")

    def module_contents(self, items: list) -> list:
        return list(items)

    def module(self, items: list) -> Module:
        name_ident = items[0]
        ports = items[1]
        module_items = items[2] if len(items) > 2 else []
        return Module(name=name_ident, ports=ports, contents=module_items)

    def start(self, items: list) -> list[Module]:
        return list(items)

    def statement(self, items: list) -> Statement:
        return items[0]


def create_parser():
    return Lark(hdl_grammar, start="start", parser="lalr")


def parse_hdl(text: str) -> list[Module]:
    parser = create_parser()
    tree = parser.parse(text)
    ast = ASTBuilder().transform(tree)
    return ast
