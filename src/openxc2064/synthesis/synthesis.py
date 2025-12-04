from ..hdl import ast_nodes as ast
from .rtl_nodes import *
from .elaborator import SymbolInfo


class SynthesisException(Exception):
    """Exception raised for errors in the synthesis process."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def parse_verilog_literal(val_str: str) -> tuple[int, int]:
    # parse a Verilog style number literal (e.g., `4'b1010`, `123`, `'hFF`)
    # assumes a 32 bit width if not specified
    val_str = val_str.strip()
    if "'" in val_str:
        parts = val_str.split("'")

        # width:
        width_str = parts[0]
        width = int(width_str) if width_str else 32

        # base / value:
        rest = parts[1]
        base_char = rest[0].lower()
        digits = rest[1:]
        base_map = {"b": 2, "o": 8, "d": 10, "h": 16}
        if base_char not in base_map:
            raise ValueError(f"Unknown base '{base_char}' in literal: `{val_str}`")
        val = int(digits, base_map[base_char])
        return val, width

    else:
        # assume plain decimal:
        return int(val_str), 32


class Synthesiser:
    # takes an AST and converts to a Netlist
    def __init__(self, module_library: dict[str, tuple[ast.Module, dict[str, SymbolInfo]]]) -> None:
        self.library = module_library
        self.netlist: Netlist | None = None
        self.const_count = 0

    def synthesise(self, top_module_name: str) -> Netlist:
        if top_module_name not in self.library:
            raise SynthesisException(f"Top level module '{top_module_name}' not found in project.")

        self.netlist = Netlist(top_module_name)
        self._compile_module_instance(
            module_name=top_module_name, instance_name="", parent_netlist=self.netlist
        )

        return self.netlist

    def _compile_module_instance(
        self, module_name: str, instance_name: str, parent_netlist: Netlist
    ) -> None:
        if module_name not in self.library:
            raise SynthesisException(f"Unknown module '{module_name}'.")
        module_ast, symbol_table = self.library[module_name]
        prefix = f"{instance_name}_" if instance_name else ""
        local_net_map: dict[str, Net] = {}

        # create nets for everything in the symbol table:
        for name, symbol in symbol_table.items():
            name_flat = f"{prefix}{name}"
            net = parent_netlist.create_net(name_flat, symbol.width)
            local_net_map[name] = net

            if instance_name == "":  # if top level module
                if symbol.direction == ast.Direction.INPUT:
                    parent_netlist.add_input(name, net)
                    parent_netlist.inputs.append(net)
                elif symbol.direction == ast.Direction.OUTPUT:
                    parent_netlist.outputs.append(net)

        # process contents of module:
        for item in module_ast.contents:
            if isinstance(item, ast.AssignStmt):
                self._synth_assign(item, local_net_map, parent_netlist)
            elif isinstance(item, ast.AlwaysComb):
                self._synth_comb(item, local_net_map, parent_netlist)
            elif isinstance(item, ast.AlwaysSeq):
                self._synth_seq(item, local_net_map, parent_netlist)
            elif isinstance(item, ast.Instance):
                self._synth_sub_instance(item, local_net_map, parent_netlist, prefix)

    def _synth_sub_instance(
        self,
        inst: ast.Instance,
        current_scope: dict[str, Net],
        netlist: Netlist,
        current_prefix: str,
    ) -> None:
        submodule_name = inst.module_name
        inst_name = inst.instance_name
        child_prefix = f"{current_prefix}{inst_name}"

        self._compile_module_instance(submodule_name, child_prefix, netlist)

        if submodule_name not in self.library:
            raise SynthesisException(f"Unknown module '{submodule_name}'")

        _, child_symbols = self.library[submodule_name]

        for c in inst.connections:
            port_name = c.port_name
            parent_expr = c.expr
            parent_net = self._get_net_expr(parent_expr, current_scope, netlist)
            child_net_name = f"{child_prefix}_{port_name}"
            child_net = next((n for n in netlist.nets if n.name == child_net_name), None)

            if not child_net:
                raise SynthesisException(
                    f"Port '{port_name}' not found on module '{submodule_name}'"
                )

            port_symbol = child_symbols.get(port_name)
            if not port_symbol:
                continue
            if port_symbol.direction == ast.Direction.INPUT:
                netlist.add_logic("BUF", [parent_net], [child_net])
            elif port_symbol.direction == ast.Direction.OUTPUT:
                netlist.add_logic("BUF", [child_net], [parent_net])

    def _get_net_expr(self, expr: ast.Expression, net_map: dict[str, Net], netlist: Netlist) -> Net:
        if isinstance(expr, ast.Identifier):
            if expr.name not in net_map:
                raise SynthesisException(f"Unknown signal '{expr.name}'.")
            return net_map[expr.name]

        elif isinstance(expr, ast.Number):
            val, width = parse_verilog_literal(expr.value)
            name = f"const_{self.const_count}_{expr.value}"
            self.const_count += 1
            const_net = netlist.create_net(name, width=width)
            netlist.add_const(val, const_net)
            return const_net

        elif isinstance(expr, ast.Indexed):
            # base
            base_name = expr.base.name
            if base_name not in net_map:
                raise SynthesisException(f"Unknown signal '{base_name}'.")
            base_net = net_map[base_name]

            # handle single bit index:
            if expr.index:
                # Output width is 1
                out_net = netlist.create_net(f"temp_idx_{len(netlist.nets)}", width=1)
                idx_val = expr.index.index
                # Store operation as "INDEX:<bit>"
                netlist.add_logic(f"INDEX:{idx_val}", [base_net], [out_net])
                return out_net

            # handle range slice:
            elif expr.range:
                # Output width is derived from slice
                msb, lsb = expr.range.msb, expr.range.lsb
                width = abs(msb - lsb) + 1
                out_net = netlist.create_net(f"temp_slice_{len(netlist.nets)}", width=width)
                # Store operation as "SLICE:<msb>:<lsb>"
                netlist.add_logic(f"SLICE:{msb}:{lsb}", [base_net], [out_net])
                return out_net

            raise SynthesisException("Indexed expression missing index or range.")

        elif isinstance(expr, ast.BinaryOp):
            left = self._get_net_expr(expr.left, net_map, netlist)
            right = self._get_net_expr(expr.right, net_map, netlist)

            op_map = {
                "&": "AND",
                "&&": "LOGIC_AND",  # todo: differentiate between bitwise and logical
                "|": "OR",
                "||": "LOGIC_OR",
                "^": "XOR",
                "+": "ADD",
                "-": "SUB",
                "==": "EQ",
                "!=": "NEQ",
                "<<": "LSHIFT",
                ">>": "RSHIFT",
            }
            if expr.op not in op_map:
                raise SynthesisException(f"Operation '{expr.op}' not supported yet.")

            # determine width:
            is_comparison = expr.op in ["==", "!=", "&&", "||"]
            if is_comparison:
                out_width = 1
            else:
                out_width = max(left.width, right.width)
            out = netlist.create_net(f"temp_op_{len(netlist.nets)}", width=out_width)
            netlist.add_logic(op_map[expr.op], [left, right], [out])
            return out

        elif isinstance(expr, ast.UnaryOp):
            operand = self._get_net_expr(expr.operand, net_map, netlist)

            op_map = {"!": "LOGIC_NOT", "-": "NEG", "~": "NOT"}
            if expr.op not in op_map:
                raise SynthesisException(f"Operation '{expr.op}' not supported yet.")
            if expr.op == "!":
                out_width = 1
            else:
                out_width = operand.width
            out = netlist.create_net(f"temp_uop_{len(netlist.nets)}", width=out_width)
            netlist.add_logic(op_map[expr.op], [operand], [out])
            return out

        elif isinstance(expr, ast.ParenExpr):
            return self._get_net_expr(expr.expr, net_map, netlist)

    def _synth_assign(
        self, stmt: ast.AssignStmt, net_map: dict[str, Net], netlist: Netlist
    ) -> None:
        rhs = self._get_net_expr(stmt.rhs, net_map, netlist)
        # todo: fix since might not be driving entire name if indexed
        lhs_name = stmt.lhs.name if isinstance(stmt.lhs, ast.Identifier) else stmt.lhs.base.name
        lhs = net_map[lhs_name]
        netlist.add_logic("BUF", [rhs], [lhs])

    def _synth_comb(self, block: ast.AlwaysComb, net_map: dict[str, Net], netlist: Netlist) -> None:
        initial_scope = {}
        final_scope = self._process_stmt_block(block.stmt, initial_scope, net_map, netlist)
        for name, driving_name in final_scope.items():
            target = net_map[name]
            netlist.add_logic("BUF", [driving_name], [target])

    def _synth_seq(self, block: ast.AlwaysSeq, net_map: dict[str, Net], netlist: Netlist) -> None:
        clk_name = (
            block.signal.name
            if isinstance(block.signal, ast.Identifier)
            else block.signal.base.name
        )
        clk_net = net_map[clk_name]
        edge_type = block.edge

        initial_scope = {}
        final_scope = self._process_stmt_block(block.statements, initial_scope, net_map, netlist)

        for name, next_net in final_scope.items():
            if name in net_map:
                q_net = net_map[name]
                netlist.add_dff([next_net, clk_net], [q_net], edge=edge_type)

    def _process_stmt_block(
        self,
        stmt: ast.Statement,
        scope: dict[str, Net],
        net_map: dict[str, Net],
        netlist: Netlist,
    ) -> dict[str, Net]:
        new_scope = scope.copy()

        if isinstance(stmt, ast.ProcAssignStmt):
            rhs = self._get_net_expr(stmt.expr, net_map, netlist)

            if isinstance(stmt.target, ast.Identifier):
                lhs_name = stmt.target.name
                new_scope[lhs_name] = rhs
            elif isinstance(stmt.target, ast.Indexed):
                lhs_name = stmt.target.base.name

                # Get current value (old_net)
                old_net = new_scope.get(lhs_name)
                if not old_net:
                    old_net = net_map.get(lhs_name)
                if not old_net:
                    raise SynthesisException(f"Cannot assign to unknown signal '{lhs_name}'.")

                if stmt.target.index:
                    # Single bit assignment: target[i] = rhs
                    idx = int(stmt.target.index.index)
                    msb = idx
                    lsb = idx
                elif stmt.target.range:
                    # Slice assignment: target[msb:lsb] = rhs
                    msb = int(stmt.target.range.msb)
                    lsb = int(stmt.target.range.lsb)
                else:
                    raise SynthesisException("Indexed assignment missing index or range.")

                new_net = netlist.create_net(
                    f"partial_result_{len(netlist.nets)}", width=old_net.width
                )
                netlist.add_logic(f"UPDATE:{msb}:{lsb}", [old_net, rhs], [new_net])

                new_scope[lhs_name] = new_net

        elif isinstance(stmt, ast.BlockStmt):
            for s in stmt.statements:
                new_scope = self._process_stmt_block(s, new_scope, net_map, netlist)

        elif isinstance(stmt, ast.IfStmt):
            # todo: review this carefully
            cond = self._get_net_expr(stmt.condition, net_map, netlist)
            then_scope = self._process_stmt_block(stmt.then_stmts, new_scope, net_map, netlist)
            else_scope = new_scope
            if stmt.else_stmts:
                else_scope = self._process_stmt_block(stmt.else_stmts, new_scope, net_map, netlist)

            all_vars = set(then_scope.keys()) | set(else_scope.keys())
            merged = new_scope.copy()

            for v in all_vars:
                t_net = then_scope.get(v)
                if not t_net:
                    t_net = new_scope.get(v)
                if not t_net:
                    t_net = net_map.get(v)

                e_net = else_scope.get(v)
                if not e_net:
                    e_net = new_scope.get(v)
                if not e_net:
                    e_net = net_map.get(v)

                if t_net != e_net and t_net and e_net:
                    mux_width = max(t_net.width, e_net.width)
                    mux_out = netlist.create_net(f"mux_{v}_{len(netlist.nets)}", width=mux_width)
                    netlist.add_logic("MUX", [cond, e_net, t_net], [mux_out])
                    # note the order of inputs list ^^^^^^^^^^^^ is intentional
                    # if cond=0, then the else block gets run -> i.e., index 0 in inputs[1..]
                    # if cond=1 then the then block gets run -> i.e., index 1 in inputs[1..]
                    # allows you to use cond+1 as the index to choose which of the inputs propagates
                    # the output
                    merged[v] = mux_out
                elif t_net:
                    merged[v] = t_net
            new_scope = merged

        return new_scope
