from .ast_nodes import *
from dataclasses import dataclass


class HDLValidationError(Exception):
    """Exception raised for errors in the HDL validation process."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


if __name__ == "__main__":
    raise HDLValidationError(
        "This module is not intended to be run as a script.")
