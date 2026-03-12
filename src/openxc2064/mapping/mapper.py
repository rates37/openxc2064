from abc import ABC, abstractmethod
from openxc2064.synthesis.rtl_nodes import Netlist 

class TechnologyMapper(ABC):
    """
    Abstract base class for Technology Mapping algorithm.
    Converts a 1-bit wide netlist into K-input LUTs.
    """
    def __init__(self, k_max: int = 3):
        self.k_max = k_max
    
    @abstractmethod
    def run(self, netlist: Netlist) -> Netlist:
        pass
