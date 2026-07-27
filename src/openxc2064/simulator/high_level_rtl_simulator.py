from __future__ import annotations
from ..synthesis.rtl_nodes import Net, Netlist, DFF, Input, Constant, LogicGate, Node
from ..mapping.xc2064_primitives import LUT, CLB, IOB
from typing import Callable, Tuple, Optional
from collections import deque
import re


class CombinationalLoopError(Exception):
    """Raised when a netlist contains a combinational cycle (a feedback path
    with no register on it), which has no stable evaluation."""


class RTLSimulator:
    # Simulator for the high level RTL representation in synthesis/rtl_nodes.py
    def __init__(self, netlist: Netlist) -> None:
        self.netlist = netlist

        # Map net names to net objects:
        self.net_name_to_net: dict[str, Net] = {}

        # Map port names to net names:
        self.input_ports: dict[str, str] = {}
        self.output_ports: dict[str, str] = {}

        # Store values for all nets:
        self.net_values: dict[str, int] = {}

        # store previous net values (for edge detection):
        self.prev_net_values: dict[str, int] = {}

        # store DFF states:
        self.dff_state: dict[str, int] = {}

        # Operation function map:
        self.ops: dict[str, Callable[[list[int]], int]] = {
            "AND": lambda x: x[0] & x[1] if len(x) >= 2 else 0,
            "OR": lambda x: x[0] | x[1] if len(x) >= 2 else 0,
            "XOR": lambda x: x[0] ^ x[1] if len(x) >= 2 else 0,
            "NOT": lambda x: ~x[0] if len(x) >= 1 else 0,
            "LOGIC_NOT": lambda x: 1 if x[0] == 0 else 0,
            "NEG": lambda x: -x[0] if len(x) >= 1 else 0,
            "BUF": lambda x: x[0] if len(x) >= 1 else 0,
            "ADD": lambda x: x[0] + x[1] if len(x) >= 2 else 0,
            "SUB": lambda x: x[0] - x[1] if len(x) >= 2 else 0,
            "NEQ": lambda x: 1 if (x[0] != x[1]) else 0,
            "EQ": lambda x: 1 if (x[0] == x[1]) else 0,
            "LOGIC_AND": lambda x: 1 if (x[0] != 0 and x[1] != 0) else 0,
            "LOGIC_OR": lambda x: 1 if (x[0] != 0 or x[1] != 0) else 0,
            "MUX": lambda x: x[2] if x[0] else x[1],  # Sel, Else, Then
            "LSHIFT": lambda x: (x[0] << x[1]) if len(x) >= 2 else 0,
            "RSHIFT": lambda x: (x[0] >> x[1]) if len(x) >= 2 else 0,
        }

        self._initialise()

    def set(self, port_spec: str, value: int) -> None:
        # Set an input port (or bits of a port) to a specific value
        port_name, high_bit, low_bit = self._parse_port_spec(port_spec)

        if port_name not in self.input_ports:
            raise ValueError(f"Input port '{port_name}' not found in design.")

        net_name = self.input_ports[port_name]
        net = self.net_name_to_net[net_name]

        if high_bit is None:
            # Setting entire port
            masked_value = self._mask_value(value, net.width)
            self.net_values[net_name] = masked_value
        else:
            # Setting specific bits
            if high_bit >= net.width or low_bit >= net.width:
                raise ValueError(
                    f"Bit index out of range for port '{port_name}' "
                    f"(width={net.width}, requested [{high_bit}:{low_bit}])"
                )

            # Get current value -> modify the bits -> set back
            current = self.net_values.get(net_name, 0)
            new_value = self._set_bits(current, value, high_bit, low_bit, net.width)
            self.net_values[net_name] = new_value

    def get(self, port_spec: str) -> int:
        port_name, high_bit, low_bit = self._parse_port_spec(port_spec)

        if port_name not in self.output_ports:
            raise ValueError(f"Output port '{port_name}' not found in design.")

        net_name = self.output_ports[port_name]
        value = self.net_values.get(net_name, 0)

        if high_bit is None:
            # Get entire port
            return value
        else:
            # Gett specific bits
            net = self.net_name_to_net[net_name]
            if high_bit >= net.width or low_bit >= net.width:
                raise ValueError(
                    f"Bit index out of range for port '{port_name}' "
                    f"(width={net.width}, requested [{high_bit}:{low_bit}])"
                )
            return self._extract_bits(value, high_bit, low_bit)

    def get_net(self, net_spec: str) -> int:
        net_name, high_bit, low_bit = self._parse_port_spec(net_spec)

        if net_name not in self.net_values:
            raise ValueError(f"Net '{net_name}' not found in design.")

        value = self.net_values[net_name]

        if high_bit is None:
            # Getting entire net
            return value
        else:
            # Getting specific bits
            net = self.net_name_to_net[net_name]
            if high_bit >= net.width or low_bit >= net.width:
                raise ValueError(
                    f"Bit index out of range for net '{net_name}' "
                    f"(width={net.width}, requested [{high_bit}:{low_bit}])"
                )
            return self._extract_bits(value, high_bit, low_bit)

    def get_net_signed(self, net_spec: str) -> int:
        net_name, high_bit, low_bit = self._parse_port_spec(net_spec)

        if net_name not in self.net_values:
            raise ValueError(f"Net '{net_name}' not found in design.")

        net = self.net_name_to_net[net_name]

        if high_bit is None:
            # Get entire net
            value = self.net_values[net_name]
            width = net.width
        else:
            # Get specific bits
            if high_bit >= net.width or low_bit >= net.width:
                raise ValueError(
                    f"Bit index out of range for net '{net_name}' "
                    f"(width={net.width}, requested [{high_bit}:{low_bit}])"
                )
            value = self._extract_bits(self.net_values[net_name], high_bit, low_bit)
            width = high_bit - low_bit + 1

        if value & (1 << (width - 1)):
            return value - (1 << width)
        return value

    def step(self) -> None:
        self._propagate_comb()
        self._update_dffs()
        self._propagate_comb()
        self.prev_net_values = self.net_values.copy()

    def reset(self) -> None:
        self._initialise()  # realise it does the same thing lol

    # Private methods:

    def _initialise(self) -> None:
        # build relevant maps
        for n in self.netlist.nets:
            self.net_name_to_net[n.name] = n
            self.net_values[n.name] = 0
            self.prev_net_values[n.name] = 0

        # initialise DFF values to 0:
        for n in self.netlist.nodes:
            if isinstance(n, DFF):
                self.dff_state[n.id] = 0
            elif isinstance(n, CLB) and n.dff:
                self.dff_state[n.dff.id] = 0

        # input / output maps:
        for n in self.netlist.nodes:
            if isinstance(n, Input):
                self.input_ports[n.port_name] = n.outputs[0].name
            elif isinstance(n, IOB):
                if n.is_input and n.inputs[0]:
                    port_name = n.pad_name if n.pad_name else n.inputs[0].name
                    self.input_ports[port_name] = n.inputs[0].name
                if n.is_output and n.outputs[0]:
                    port_name = n.pad_name if n.pad_name else n.outputs[0].name
                    self.output_ports[port_name] = n.outputs[0].name
        
        for n in self.netlist.outputs:
            if n.name not in self.output_ports:
                self.output_ports[n.name] = n.name

        # set constant values
        for n in self.netlist.nodes:
            if isinstance(n, Constant):
                if n.outputs:
                    net = n.outputs[0]
                    value = self._mask_value(n.value, net.width)
                    self.net_values[net.name] = value
                    self.prev_net_values[net.name] = value

        # combinational evaluation order, computed once (raises
        # CombinationalLoopError on register-free feedback)
        self._eval_schedule = self._build_eval_schedule()

        self._propagate_comb()

    def _clb_lut_pins(self, sel_in1: int, sel_in2: int, sel_in3: int) -> set[int]:
        # pin indices (into CLB.inputs = [A, B, C, D, K]) read by one
        # internal LUT, derived from its input mux configuration
        pins = {1 if sel_in1 else 0, 2 if sel_in2 else 1}
        if sel_in3 == 0:
            pins.add(2)
        elif sel_in3 == 1:
            pins.add(3)
        # sel_in3 == 2 reads Q, which is register state, not a comb input
        return pins

    def _output_dependencies(self, node: Node, out_index: int) -> list[Net]:
        # nets that combinationally determine node.outputs[out_index].
        # register-state paths (DFF Q, CLB Q, latched IOB inputs) contribute
        # no edges: they only change on clock edges, between propagations
        if isinstance(node, (Input, Constant, DFF)):
            return []
        if isinstance(node, (LUT, LogicGate)):
            return [n for n in node.inputs if n is not None]
        if isinstance(node, IOB):
            # the pad value reads [PIN_in, OUT, TS]; the IN output follows the
            # pad combinationally unless latched through the IOB flip-flop
            pad_deps = [n for n in node.inputs[:3] if n is not None]
            if out_index == 0 or node.in_mux_sel == 0:
                return pad_deps
            return []
        if isinstance(node, CLB):
            # outputs[0] is X, outputs[1] is Y; each mux selects G, Q or F
            sel = node.sel_x if out_index == 0 else node.sel_y
            if sel == 1:  # Q
                return []
            if sel == 2:  # F
                pins = self._clb_lut_pins(node.sel_f_in1, node.sel_f_in2, node.sel_f_in3)
            else:  # G
                pins = self._clb_lut_pins(node.sel_g_in1, node.sel_g_in2, node.sel_g_in3)
            return [
                node.inputs[i]
                for i in sorted(pins)
                if i < len(node.inputs) and node.inputs[i] is not None
            ]
        # unknown node kind: be conservative
        return [n for n in node.inputs if n is not None]

    def _build_eval_schedule(self) -> list[Node]:
        # net-level dependency graph: an edge dep -> out for every net that
        # combinationally determines a driven net's value
        deps: dict[str, set[str]] = {n.name: set() for n in self.netlist.nets}
        for node in self.netlist.nodes:
            for out_index, out_net in enumerate(node.outputs):
                if out_net is None:
                    continue
                out_deps = deps.setdefault(out_net.name, set())
                for dep in self._output_dependencies(node, out_index):
                    # read-modify-write ops (SET_INDEX/SET_SLICE) read their
                    # own previous value; that is not an ordering edge
                    if dep.name != out_net.name:
                        out_deps.add(dep.name)

        dependents: dict[str, set[str]] = {}
        for out_name, dep_names in deps.items():
            for dep_name in dep_names:
                dependents.setdefault(dep_name, set()).add(out_name)

        # Kahn's algorithm, seeded and tie-broken deterministically
        indegree = {name: len(d) for name, d in deps.items()}
        queue = deque(name for name in deps if indegree[name] == 0)
        order: list[str] = []
        while queue:
            name = queue.popleft()
            order.append(name)
            for dependent in sorted(dependents.get(name, ())):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(dependent)

        if len(order) < len(deps):
            looped = sorted(name for name, d in indegree.items() if d > 0)
            raise CombinationalLoopError(
                f"Combinational loop detected involving nets: {', '.join(looped)}"
            )

        # evaluate each driven net's driver(s) once its dependencies are
        # ready. a node with two outputs appears at both output positions:
        # the later evaluation overwrites any stale sibling-output value
        # before anything scheduled afterwards reads it
        schedule: list[Node] = []
        for name in order:
            net = self.net_name_to_net.get(name)
            if net is None:
                continue
            for driver in net.drivers:
                # inputs are driven externally; constants were set at init
                if not isinstance(driver, (Input, Constant)):
                    schedule.append(driver)
        return schedule

    def _mux_op(self, args: list) -> int:
        # args[0] is the select line, args[1..] are the data inputs
        if len(args) < 2:
            return 0
        select = args[0]
        if 0 <= select < len(args) - 1:
            return args[select + 1]
        return 0  # fallback

    def _mask_value(self, value: int, width: int) -> int:
        # masks a value to fit within specified bit width
        if width <= 0:
            return 0
        return value & ((1 << width) - 1)  # value & {width{1'b1}}

    def _propagate_comb(self) -> None:
        # single pass in topological order: the schedule (built once at init)
        # orders every driven net after its combinational dependencies, so no
        # iterate-until-stable loop or settling cap is needed
        for n in self._eval_schedule:
            self._eval_node(n)

    def _eval_node(self, n: Node) -> None:
        # evaluate one node and write its output nets from current values
        if isinstance(n, LogicGate):
            result = self._eval_gate(n)
            for output_net in n.outputs:
                self.net_values[output_net.name] = self._mask_value(result, output_net.width)

        elif isinstance(n, DFF):
            q_value = self.dff_state.get(n.id, 0)
            if n.outputs:
                output_net = n.outputs[0]
                self.net_values[output_net.name] = self._mask_value(q_value, output_net.width)

        elif isinstance(n, LUT): # assuming LUT ALWAYS has 1-bit width inputs/outputs
            # collect LUT inputs from current state:
            input_values = [self.net_values.get(in_n.name, 0) for in_n in n.inputs]
            # build the k-bit state index from inputs [I0, I1, ..., IK-1]
            state = 0
            for i, val in enumerate(input_values):
                if val:
                    state |= (1 << i)

            # extract the evaluation bit from the LUT truth table config
            result = (n.truth_table >> state) & 1

            if n.outputs:
                self.net_values[n.outputs[0].name] = result

        elif isinstance(n, IOB):
            # inputs: [PIN_in, OUT, TS, IO_CLK]
            # outputs: [PIN_out, IN]
            pin_val_in = self.net_values.get(n.inputs[0].name, 0) if len(n.inputs)>0 and n.inputs[0] else 0
            out_val = self.net_values.get(n.inputs[1].name, 0) if len(n.inputs)>1 and n.inputs[1] else 0
            ts_val = self.net_values.get(n.inputs[2].name, 1) if len(n.inputs)>2 and n.inputs[2] else 1

            internal_ts = 1
            if n.ts_mux_sel == 1:
                internal_ts = ts_val
            elif n.ts_mux_sel == 2:
                internal_ts = 0

            pin_val_out = pin_val_in
            if internal_ts == 0:
                 pin_val_out = out_val

            if len(n.outputs)>0 and n.outputs[0]:
                self.net_values[n.outputs[0].name] = pin_val_out

            # PIN to IN path
            if len(n.outputs)>1 and n.outputs[1]:
                if n.in_mux_sel == 0:
                    self.net_values[n.outputs[1].name] = pin_val_out
                else:
                    q_val = self.dff_state.get(n.dff.id, 0) if n.dff else 0
                    self.net_values[n.outputs[1].name] = q_val

        elif isinstance(n, CLB):
            # Evaluate CLB given strict physical mapping
            A = self.net_values.get(n.inputs[0].name, 0) if len(n.inputs) > 0 and n.inputs[0] else 0
            B = self.net_values.get(n.inputs[1].name, 0) if len(n.inputs) > 1 and n.inputs[1] else 0
            C = self.net_values.get(n.inputs[2].name, 0) if len(n.inputs) > 2 and n.inputs[2] else 0
            D = self.net_values.get(n.inputs[3].name, 0) if len(n.inputs) > 3 and n.inputs[3] else 0

            # Q is the current state of the DFF
            Q = self.dff_state.get(n.dff.id, 0) if n.dff else 0

            # Evaluate LUT F (truth-table bit order matches the web simulator:
            # index = (mux1 << 2) | (mux2 << 1) | mux3, see LogicCell.ts)
            f_in0 = B if n.sel_f_in1 else A
            f_in1 = C if n.sel_f_in2 else B
            f_in2 = D if n.sel_f_in3 == 1 else (Q if n.sel_f_in3 == 2 else C)
            f_state = (f_in0 << 2) | (f_in1 << 1) | f_in2
            F = (n.lut_f_init >> f_state) & 1

            # Evaluate LUT G
            g_in0 = B if n.sel_g_in1 else A
            g_in1 = C if n.sel_g_in2 else B
            g_in2 = D if n.sel_g_in3 == 1 else (Q if n.sel_g_in3 == 2 else C)
            g_state = (g_in0 << 2) | (g_in1 << 1) | g_in2
            G = (n.lut_g_init >> g_state) & 1

            # Drive outputs X and Y based on MUXes
            X = F if n.sel_x == 2 else (Q if n.sel_x == 1 else G)
            Y = F if n.sel_y == 2 else (Q if n.sel_y == 1 else G)

            # Map back to nets
            if len(n.outputs) > 0 and n.outputs[0]:
                self.net_values[n.outputs[0].name] = X  # X

            if len(n.outputs) > 1 and n.outputs[1]:
                self.net_values[n.outputs[1].name] = Y  # Y

    def _eval_gate(self, gate: LogicGate) -> int:
        input_values = [self.net_values.get(n.name, 0) for n in gate.inputs]
        if gate.op in self.ops:
            return self.ops[gate.op](input_values)
        else:
            if ":" in gate.op:
                # must be a slice or index
                parts = gate.op.split(":")
                base_op = parts[0]

                if base_op == "INDEX":
                    idx = int(parts[1])
                    return (input_values[0] >> idx) & 1

                elif base_op == "SLICE":
                    msb = int(parts[1])
                    lsb = int(parts[2])
                    mask = (1 << (abs(msb - lsb) + 1)) - 1
                    return (input_values[0] >> lsb) & mask

                elif base_op == "UPDATE":
                    msb = int(parts[1])
                    lsb = int(parts[2])
                    width = abs(msb - lsb) + 1

                    old_val = input_values[0]
                    new_val = input_values[1]

                    # Create mask for target bits
                    mask = ((1 << width) - 1) << lsb

                    # Clear bits in old_val
                    cleared = old_val & ~mask

                    # Shift new_val to position and mask
                    shifted_new = (new_val << lsb) & mask

                    return cleared | shifted_new

                elif base_op == "SET_INDEX":
                    idx = int(parts[1])
                    curr_val = self.net_values.get(gate.outputs[0].name, 0)
                    new_bit = input_values[0] & 1
                    
                    # Clear the bit at idx
                    cleared = curr_val & ~(1 << idx)
                    # Set the new bit
                    return cleared | (new_bit << idx)

                elif base_op == "SET_SLICE":
                    msb = int(parts[1])
                    lsb = int(parts[2])
                    width = abs(msb - lsb) + 1
                    curr_val = self.net_values.get(gate.outputs[0].name, 0)
                    new_bits = input_values[0] & ((1 << width) - 1)
                    
                    # Create mask for target bits
                    mask = ((1 << width) - 1) << lsb
                    # Clear bits in curr_val
                    cleared = curr_val & ~mask
                    # Set new bits
                    return cleared | (new_bits << lsb)

            raise ValueError(f"Unknown operation: '{gate.op}'")

    def _detect_edge(self, net_name: str, edge_type: str) -> bool:
        # detects if a specific edge type occurred on a net
        # edge_type should be 'posedge' or 'negedge'
        prev_value = self.prev_net_values.get(net_name, 0)
        curr_value = self.net_values.get(net_name, 0)

        if edge_type == "posedge":
            return prev_value == 0 and curr_value == 1
        elif edge_type == "negedge":
            return prev_value == 1 and curr_value == 0
        else:
            raise ValueError(f"Unknown edge_type: '{edge_type}'")

    def _update_dffs(self) -> None:
        # check all dffs for clock edges and update state accordingly
        for n in self.netlist.nodes:
            if isinstance(n, DFF):  # inputs: [D, CLK]
                if len(n.inputs) >= 2:
                    clk_net_name = n.inputs[1].name

                    # check if appropriate edge occurred:
                    if self._detect_edge(clk_net_name, n.edge):
                        d_net = n.inputs[0]
                        d_value = self.net_values.get(d_net.name, 0)
                        d_value_masked = self._mask_value(d_value, d_net.width)
                        self.dff_state[n.id] = d_value_masked
                        
            elif isinstance(n, IOB) and n.dff:
                clk_net_name = n.dff.inputs[1].name if len(n.dff.inputs) >= 2 else None
                if clk_net_name and self._detect_edge(clk_net_name, n.dff.edge):
                    pin_val_in = self.net_values.get(n.inputs[0].name, 0) if len(n.inputs)>0 and n.inputs[0] else 0
                    self.dff_state[n.dff.id] = self._mask_value(pin_val_in, 1)
                    
            elif isinstance(n, CLB) and n.dff:
                # Calculate internal clock state based on current dict (prev or current)
                def calc_clk(vals_dict, dff_q):
                    A = vals_dict.get(n.inputs[0].name, 0) if len(n.inputs)>0 and n.inputs[0] else 0
                    B = vals_dict.get(n.inputs[1].name, 0) if len(n.inputs)>1 and n.inputs[1] else 0
                    C = vals_dict.get(n.inputs[2].name, 0) if len(n.inputs)>2 and n.inputs[2] else 0
                    D = vals_dict.get(n.inputs[3].name, 0) if len(n.inputs)>3 and n.inputs[3] else 0
                    K = vals_dict.get(n.inputs[4].name, 0) if len(n.inputs)>4 and n.inputs[4] else 0
                    
                    g_in0 = B if n.sel_g_in1 else A
                    g_in1 = C if n.sel_g_in2 else B
                    g_in2 = D if n.sel_g_in3 == 1 else (dff_q if n.sel_g_in3 == 2 else C)
                    G = (n.lut_g_init >> ((g_in0<<2)|(g_in1<<1)|g_in2)) & 1
                    
                    clk1 = K if n.sel_clk1 == 2 else (C if n.sel_clk1 == 1 else G)
                    clk2 = 0 if n.sel_clk2 == 2 else (clk1 if n.sel_clk2 == 1 else (1 - clk1))
                    return clk2
                
                q_state = self.dff_state.get(n.dff.id, 0)
                old_clk = calc_clk(self.prev_net_values, q_state)
                new_clk = calc_clk(self.net_values, q_state)
                
                is_edge = False
                if n.dff.edge == "posedge":
                    is_edge = (old_clk == 0 and new_clk == 1)
                else:
                    is_edge = (old_clk == 1 and new_clk == 0)

                if is_edge:
                    # Evaluate F which drives D hardwired
                    A = self.net_values.get(n.inputs[0].name, 0) if len(n.inputs)>0 and n.inputs[0] else 0
                    B = self.net_values.get(n.inputs[1].name, 0) if len(n.inputs)>1 and n.inputs[1] else 0
                    C = self.net_values.get(n.inputs[2].name, 0) if len(n.inputs)>2 and n.inputs[2] else 0
                    D = self.net_values.get(n.inputs[3].name, 0) if len(n.inputs)>3 and n.inputs[3] else 0
                    
                    f_in0 = B if n.sel_f_in1 else A
                    f_in1 = C if n.sel_f_in2 else B
                    f_in2 = D if n.sel_f_in3 == 1 else (q_state if n.sel_f_in3 == 2 else C)
                    F = (n.lut_f_init >> ((f_in0<<2)|(f_in1<<1)|f_in2)) & 1
                    
                    self.dff_state[n.dff.id] = F

    def _parse_port_spec(self, port_spec: str) -> Tuple[str, Optional[int], Optional[int]]:
        # Parse a port specification like "a", "a[2]", or "a[3:1]"

        # Match patterns: port_name[bit] or port_name[high:low] or port_name
        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)(?:\[(\d+)(?::(\d+))?\])?$", port_spec)

        if not match:
            raise ValueError(f"Invalid port specification: '{port_spec}'")

        port_name = match.group(1)

        if match.group(2) is None:
            # No indexing - full port
            return (port_name, None, None)
        elif match.group(3) is None:
            # Single bit: port[bit]
            bit = int(match.group(2))
            return (port_name, bit, bit)
        else:
            # Range: port[high:low]
            high_bit = int(match.group(2))
            low_bit = int(match.group(3))
            if high_bit < low_bit:
                raise ValueError(f"Invalid bit range [{high_bit}:{low_bit}] - high must be >= low")
            return (port_name, high_bit, low_bit)

    def _extract_bits(self, value: int, high_bit: int, low_bit: int) -> int:
        # Extract bits [high:low] from value
        num_bits = high_bit - low_bit + 1
        mask = (1 << num_bits) - 1
        return (value >> low_bit) & mask

    def _set_bits(
        self, original: int, new_bits: int, high_bit: int, low_bit: int, width: int
    ) -> int:
        # Set bits [high:low] in original value to new_bits.
        # Returns the modified value, masked to the specified width.

        num_bits = high_bit - low_bit + 1
        mask = (1 << num_bits) - 1

        # clear the target bits in original
        clear_mask = ~(mask << low_bit)
        cleared = original & clear_mask

        # set the new bits
        new_bits_masked = new_bits & mask
        result = cleared | (new_bits_masked << low_bit)
        return self._mask_value(result, width)
