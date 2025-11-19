from .ast_nodes import *
from dataclasses import dataclass


class HDLValidationError(Exception):
    """Exception raised for errors in the HDL validation process."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class HDLElaborator:
    """Class responsible for elaborating HDL ASTs."""

    def __init__(self, modules: list[Module]) -> None:
        self.symbol_table = {}
        self.modules = {module.name: module for module in modules}
        self.currently_validated_modules: set[str] = set()
        self.current_module = ""

    def elaborate(self, module: Module) -> None:
        self.current_module = module.name
        self.symbol_table = {}

        """
        Things to check for during elaboration:
        - All instance module names must exist in self.modules
        - Parameter overrides must match the parameter names in the module definition
        - Connections must match the port names and widths in the module definition
        - No duplicate instance names within the same module
        - Types of connected signals must be compatible
        - Check all signals (wires and reg) are declared before use
        - Ensure no circular dependencies in module instantiations
        - Generate a flattened representation of the module with all instances resolved
        - Handle hierarchical module instantiations
        - Report any errors found during the elaboration process using HDLValidationError
        """
        pass

    def validate(self) -> None:
        for module_name, module in self.modules.items():
            if module_name not in self.currently_validated_modules:
                self.elaborate(module)
                self.currently_validated_modules.add(module_name)


if __name__ == "__main__":
    raise HDLValidationError(
        "This module is not intended to be run as a script.")
