from .ast_nodes import *
from dataclasses import dataclass


class HDLValidationError(Exception):
    """Exception raised for errors in the HDL validation process."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


"""
Things to check for during elaboration:
- All instance module names must exist in self.modules
- Parameter overrides must match the parameter names in the module definition
- Connections must match the port names and widths in the module definition
- No duplicate instance names within the same module
- Types of connected signals must be compatible
- Check all signals (wires and reg) are declared before use
- Ensure no circular dependencies in module instantiations
- Handle hierarchical module instantiations
- Report any errors found during the elaboration process using HDLValidationError
"""


@dataclass
class SymbolInfo:
    """Helper class to store signal metadata (only during elaboration)."""

    name: str
    type: str  # 'wire', 'reg', 'port_input', 'port_output', 'port_inout'
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
                    if content.module_name not in self.modules:
                        raise HDLValidationError(
                            f"Module '{content.module_name}' instantiated in '{self.current_module}' is not defined."
                        )
                    # Recursively elaborate the instantiated module
                    self.elaborate(self.modules[content.module_name])
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
            port_type = (
                "port_input"
                if port.direction == Direction.INPUT
                else "port_output"
                if port.direction == Direction.OUTPUT
                else "port_inout"
            )
            self.symbol_table[port.name] = SymbolInfo(
                name=port.name, type=port_type, direction=port.direction
            )

        # collect symbols from wire and reg declarations
        for content in module.contents:
            if isinstance(content, WireDecl):
                if content.name in self.symbol_table:
                    raise HDLValidationError(
                        f"Duplicate wire name '{content.name}' in module '{module.name}'."
                    )
                self.symbol_table[content.name] = SymbolInfo(
                    name=content.name, type="wire"
                )
            elif isinstance(content, RegDecl):
                if content.name in self.symbol_table:
                    raise HDLValidationError(
                        f"Duplicate register name '{content.name}' in module '{module.name}'."
                    )
                self.symbol_table[content.name] = SymbolInfo(
                    name=content.name, type="reg"
                )


if __name__ == "__main__":
    raise HDLValidationError(
        "This module is not intended to be run as a script.")
