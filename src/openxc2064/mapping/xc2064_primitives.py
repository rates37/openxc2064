from dataclasses import dataclass, field
from openxc2064.synthesis.rtl_nodes import Node, DFF

@dataclass(eq=False)
class LUT(Node):
    """
    Look-Up Table primitive.
    Evaluates boolean logic for up to K inputs (K <= 3 for XC2064) based 
    on a 2^K bit truth table integer mask. The inputs are ordered
    [I0, I1, ..., I_K-1]. I0 is the LEAST significant bit used to index
    into the truth table integer.
    """
    truth_table: int = 0
    k: int = 3
    def __post_init__(self):
        super().__post_init__()
        assert len(self.inputs) <= self.k, f"LUT cannot have more than {self.k} inputs"

@dataclass(eq=False)
class CLB(Node):
    """
    Configurable Logic Block (CLB) macro.
    The fundamental element of the XC2064 logic fabric.
    Encapsulates up to two 3-input LUTs and one D-Flip-Flop.
    """
    # components inside the CLB:
    luts: list[LUT] = field(default_factory=list)
    dff: DFF | None = None
    
    # internal config flags (routing)
    # todo

    def __post_init__(self):
        super().__post_init__()
        assert len(self.inputs) <= 4, "A CLB is bound to a maximum of 4 distinct logical inputs (A,B,C,D)."
        assert len(self.luts) <= 2, "A CLB can house at most two 3-input LUTs."

@dataclass(eq=False)
class IOB(Node):
    """
    Input/Output Block primitive.
    Wraps external I/O pins of the FPGA.
    """
    is_input: bool = True
    is_output: bool = False
    pad_name: str = ""
