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
    # LUTs
    lut_f_init: int = 0
    lut_g_init: int = 0
    
    # Optional paired DFF
    dff: DFF | None = None
    
    # Input Routing MUXes
    sel_f_in1: int = 0 # 0: A, 1: B
    sel_f_in2: int = 0 # 0: B, 1: C
    sel_f_in3: int = 0 # 0: C, 1: D, 2: Q
    
    sel_g_in1: int = 0 # 0: A, 1: B
    sel_g_in2: int = 0 # 0: B, 1: C
    sel_g_in3: int = 0 # 0: C, 1: D, 2: Q
    
    # Output Routing MUXes
    sel_x: int = 0 # 0: G, 1: Q, 2: F
    sel_y: int = 0 # 0: G, 1: Q, 2: F
    
    # Clock MUXes
    sel_clk1: int = 0 # 0: G, 1: C, 2: K
    sel_clk2: int = 0 # 0: !CLK1, 1: CLK1, 2: GND
    
    def __post_init__(self):
        super().__post_init__()
        assert len(self.inputs) <= 5, "A CLB is bound to a maximum of 5 inputs (A,B,C,D, + K clock)."
        assert len(self.outputs) <= 2, "A CLB can only drive a maximum of 2 output pins (X, Y)."

@dataclass(eq=False)
class IOB(Node):
    """
    Input/Output Block primitive.
    Wraps external I/O pins of the FPGA.
    """
    ts_mux_sel: int = 0  # 0: OFF (Input), 1: TS PIN, 2: ON (Output)
    in_mux_sel: int = 0  # 0: Combinational, 1: Clocked DFF Q
    pad_name: str = ""
    
    dff: DFF | None = None
    
    @property
    def is_input(self) -> bool:
        # A pad is an input if not permanently driven by a constant OUT ON
        return self.ts_mux_sel == 0 or self.ts_mux_sel == 1
        
    @property
    def is_output(self) -> bool:
        # A pad is an output if not permanently high-Z OFF
        return self.ts_mux_sel == 2 or self.ts_mux_sel == 1
