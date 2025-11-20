from .ast_nodes import *
from dataclasses import dataclass


class HDLValidationError(Exception):
    """Exception raised for errors in the HDL validation process."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


"""
Things to check for during elaboration:
[x] All instance module names must exist in self.modules
[x] Ensure no circular dependencies in module instantiations
[ ] Parameter overrides must match the parameter names in the module definition
[ ] Connections must match the port names and widths in the module definition
[ ] No duplicate instance names within the same module
[ ] Types of connected signals must be compatible
[ ] Check all signals (wires and reg) are declared before use
[ ] Handle hierarchical module instantiations
"""


@dataclass
class SymbolInfo:
    """Helper class to store signal metadata (only during elaboration)."""

    name: str
    is_reg: bool
    width: int
    # if direction is None, symbol is an internal signal (not port)
    direction: Direction | None = None


class HDLElaborator:
    """Class responsible for elaborating HDL ASTs."""

    def __init__(self, modules: list[Module]) -> None:
        self.modules = {module.name: module for module in modules}
        self.validated_modules = set()  # modules that have been fully validated
        self.elaboration_stack = set()  # modules currently being validated
        self.current_module = ""
        self.symbol_table: dict[str, SymbolInfo] = {}

    def validate(self) -> None:
        # iterates over all modules and validates them
        for module_name, module in self.modules.items():
            if module_name not in self.validated_modules:
                self.elaborate(module)
                self.validated_modules.add(module_name)

    def elaborate(self, module: Module) -> None:
        # validate a single module

        # check for circular instantiation:
        if module.name in self.elaboration_stack:
            raise HDLValidationError(
                f"Circular module instantiation detected in following stack: {'{'}{' '.join(self.elaboration_stack)} {module.name}{'}'}"
            )
        if module.name in self.validated_modules:
            return

        self.elaboration_stack.add(module.name)
        self.current_module = module.name
        self.symbol_table = {}

        try:
            # collect symbols from ports:
            self._collect_symbols(module)
            # Validate module contents
            for content in module.contents:
                # skip wires and registers as they are validated when collecting symbols
                if isinstance(content, WireDecl):
                    continue
                elif isinstance(content, RegDecl):
                    continue
                elif isinstance(content, Instance):
                    self.elaborate(self.modules[content.module_name]) # recursively validate instantiated module FIRST
                    self._validate_instance(content)
                    pass
                elif isinstance(content, AssignStmt):
                    self._validate_assign(content)
                elif isinstance(content, AlwaysComb):
                    self._validate_always_comb(content)
                elif isinstance(content, AlwaysSeq):
                    self._validate_always_seq(content)
                else:
                    pass  # ! todo: other cases here
                self.validated_modules.add(module.name)
        except HDLValidationError as e:
            raise e
        finally:
            self.elaboration_stack.remove(module.name)

        pass

    def _collect_symbols(self, module: Module) -> None:
        # collect symbols from ports
        for port in module.ports:
            if port.name in self.symbol_table:
                raise HDLValidationError(
                    f"Duplicate port name '{port.name}' declared in module '{module.name}'."
                )
            width = self._calculate_range_width(port.range)
            self.symbol_table[port.name] = SymbolInfo(
                name=port.name, is_reg=port.is_reg, direction=port.direction.value, width=width
            )

        # collect symbols from wire and reg declarations
        for content in module.contents:
            if isinstance(content, WireDecl):
                if content.name in self.symbol_table:
                    raise HDLValidationError(
                        f"Duplicate wire name '{content.name}' in module '{module.name}'."
                    )
                width = self._calculate_range_width(content.range)
                self.symbol_table[content.name] = SymbolInfo(
                    name=content.name, is_reg=False, width=width
                )
            elif isinstance(content, RegDecl):
                if content.name in self.symbol_table:
                    raise HDLValidationError(
                        f"Duplicate register name '{content.name}' in module '{module.name}'."
                    )
                width = self._calculate_range_width(content.range)
                self.symbol_table[content.name] = SymbolInfo(
                    name=content.name, is_reg=True, width=width
                )

    def _validate_assign(self, stmt: AssignStmt) -> None:
        # validates an assign statement:

        # Check LHS is in known symbols:
        lhs_name = self._get_target_name(stmt.lhs)
        if lhs_name not in self.symbol_table:
            raise HDLValidationError(
                f"Undeclared signal '{lhs_name}' in LHS of assignment.")

        symbol = self.symbol_table[lhs_name]
        # continuous assignments must target wires or (non-reg) output ports
        if symbol.is_reg:
            raise HDLValidationError(
                f"Illegal continuous assignment to register '{lhs_name}'.")
        elif symbol.direction == Direction.INPUT:
            raise HDLValidationError(
                f"Illegal continuous assignment to input '{lhs_name}'")

        # check RHS:
        self._validate_expression(stmt.rhs)

        # todo: check widths of LHS and RHS to warn about

    def _validate_expression(self, expr: Expression) -> None:
        # recursive expression validator to check all signals used in expression exist
        if isinstance(expr, Identifier):
            if expr.name not in self.symbol_table:
                raise HDLValidationError(
                    f"Undeclared identifier '{expr.name}' used in expression")

        elif isinstance(expr, Number):
            return  # number always valid

        elif isinstance(expr, Indexed):
            if expr.base.name not in self.symbol_table:
                raise HDLValidationError(
                    f"Undeclared identifier '{expr.base.name}' used in expression")

            # todo: validate index is in range

        elif isinstance(expr, UnaryOp):
            self._validate_expression(expr.operand)

        elif isinstance(expr, BinaryOp):
            self._validate_expression(expr.left)
            self._validate_expression(expr.right)

        elif isinstance(expr, ParenExpr):
            self._validate_expression(expr.expr)

    def _validate_always_comb(self, block: AlwaysComb) -> None:
        self._validate_statement(block.stmt, allow_reg_assignment=True)

    def _validate_always_seq(self, block: AlwaysSeq) -> None:
        sens_name = self._get_target_name(block.signal)
        if sens_name not in self._get_target_name(block.signal):
            raise HDLValidationError(
                f"Undeclared signal used in sensitivity list: '{sens_name}'")

        self._validate_statement(block.statements, allow_reg_assignment=True)

    def _validate_statement(self, stmt: Statement, allow_reg_assignment: bool = False) -> None:
        # recursive statement validator:

        if isinstance(stmt, BlockStmt):
            for s in stmt.statements:
                self._validate_statement(s, allow_reg_assignment)

        elif isinstance(stmt, IfStmt):
            self._validate_expression(stmt.condition)
            self._validate_statement(stmt.then_stmts, allow_reg_assignment)
            if stmt.else_stmts:
                self._validate_statement(stmt.else_stmts, allow_reg_assignment)

        elif isinstance(stmt, ProcAssignStmt):
            lhs_name = self._get_target_name(stmt.target)

            if lhs_name not in self.symbol_table:
                raise HDLValidationError(
                    f"Undeclared signal '{lhs_name}' used in procedural assignment.")

            sym = self.symbol_table[lhs_name]

            if sym.direction and sym.direction == Direction.INPUT:
                raise HDLValidationError(
                    f"Procedural assignment to '{lhs_name}' is illegal because it is an input.")
            if not sym.is_reg:
                raise HDLValidationError(
                    f"Procedural assignment to '{lhs_name}' is illegal. Target must be declared as a reg.")
            self._validate_expression(stmt.expr)
        pass

    def _validate_instance(self, instance: Instance) -> None:
        # check module exists in AST:
        if instance.module_name not in self.modules:
            raise HDLValidationError(
                f"Unknown module type '{instance.module_name}' instantiated as '{instance.instance_name}'.")

        target_module = self.modules[instance.module_name]

        # todo: ensure module instance ID is unique

        # validate connections:
        target_ports = {port.name: port for port in target_module.ports}
        connected_ports = set()

        for connection in instance.connections:
            if connection.port_name not in target_ports:
                raise HDLValidationError(
                    f"Port '{connection.port_name}' does not exist in module '{instance.module_name}'.")

            connected_ports.add(connection.port_name)

            # validate expression connected to the port:
            self._validate_expression(connection.expr)

            # check port direction is permitted:
            target_port = target_ports[connection.port_name]

            if target_port.direction == Direction.OUTPUT:
                if not isinstance(connection.expr, (Identifier, Indexed)):
                    raise HDLValidationError(
                        f"Cannot connect expression to output port '{connection.port_name}' of instance '{instance.module_name}'.")

                # check if driving reg with output port (illegal):
                signal_name = self._get_target_name(connection.expr)
                if signal_name in self.symbol_table:
                    signal_info = self.symbol_table[signal_name]
                    if signal_info.is_reg:
                        raise HDLValidationError(
                            f"Cannot drive register '{signal_name}' from instance output '{connection.port_name}'.")

    # util methods:

    def _get_target_name(self, target: Indexed | Identifier) -> str:
        if isinstance(target, Indexed):
            return target.base.name
        elif isinstance(target, Identifier):
            return target.name
        else:
            raise TypeError(
                f"Invalid target: {target} with type: {type(target)}. Method only accepts target of type Indexed or Identifier.")

    def _calculate_range_width(self, range: Range | None) -> int:
        # calculates with from Range object
        if range is None:
            return 1
        return abs(range.msb - range.lsb) + 1


if __name__ == "__main__":
    raise HDLValidationError(
        "This module is not intended to be run as a script.")
