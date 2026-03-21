from abc import ABC, abstractmethod
from openxc2064.synthesis.rtl_nodes import Netlist, DFF, Constant, Input
from openxc2064.mapping.xc2064_primitives import LUT, CLB, IOB

class CapacityError(Exception):
    pass

class Packer(ABC):
    """
    Abstract base class for geometrically packing discrete LUTs 
    and DFFs into generic XC2064 Configurable Logic Blocks.
    """
    def __init__(self, max_clbs: int = 64):
        self.max_clbs = max_clbs

    @abstractmethod
    def run(self, netlist: Netlist) -> Netlist:
        pass

