from __future__ import annotations
from ..synthesis.rtl_nodes import Net, Netlist, DFF, Input, Constant, LogicGate
from typing import Callable, Tuple, Optional
import re


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
            new_value = self._set_bits(
                current, value, high_bit, low_bit, net.width)
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
            value = self._extract_bits(
                self.net_values[net_name], high_bit, low_bit)
            width = high_bit - low_bit + 1

        if value & (1 << (width - 1)):
            return value - (1 << width)
        return value

    def step(self) -> None:
        # cheap implementation right now, # todo need to somehow intertwine the dff updates and the propagate comb?
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

        # input / output maps:
        for n in self.netlist.nodes:
            if isinstance(n, Input):
                self.input_ports[n.port_name] = n.outputs[0].name
        for n in self.netlist.outputs:
            self.output_ports[n.name] = n.name

        # set constant values
        for n in self.netlist.nodes:
            if isinstance(n, Constant):
                if n.outputs:
                    net = n.outputs[0]
                    value = self._mask_value(n.value, net.width)
                    self.net_values[net.name] = value
                    self.prev_net_values[net.name] = value

        self._propagate_comb()

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

    def _propagate_comb(self, max_iterations: int = 50) -> None:
        # propagate logic through combinational logic until stable
        for _ in range(max_iterations):
            changed_flag = False

            for n in self.netlist.nodes:
                if isinstance(n, LogicGate):
                    # evaluate the logic gate:
                    result = self._eval_gate(n)

                    # update output nets:
                    for output_net in n.outputs:
                        result_masked = self._mask_value(
                            result, output_net.width)
                        prev_value = self.net_values.get(output_net.name, 0)
                        if prev_value != result_masked:
                            self.net_values[output_net.name] = result_masked
                            changed_flag = True

                elif isinstance(n, DFF):
                    q_value = self.dff_state.get(n.id, 0)
                    if n.outputs:
                        output_net = n.outputs[0]
                        q_value_masked = self._mask_value(
                            q_value, output_net.width)
                        prev_value = self.net_values.get(output_net.name, 0)
                        if prev_value != q_value_masked:
                            self.net_values[output_net.name] = q_value_masked
                            changed_flag = True

            if not changed_flag:
                break
        else:
            # todo: warn that logic did not settle
            pass

    def _eval_gate(self, gate: LogicGate) -> int:
        input_values = [self.net_values.get(n.name, 0) for n in gate.inputs]
        if gate.op in self.ops:
            return self.ops[gate.op](input_values)
        else:
            if ":" in gate.op:
                # must be a slice or index
                parts = gate.op.split(':')
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

    def _parse_port_spec(self, port_spec: str) -> Tuple[str, Optional[int], Optional[int]]:
        # Parse a port specification like "a", "a[2]", or "a[3:1]"

        # Match patterns: port_name[bit] or port_name[high:low] or port_name
        match = re.match(
            r'^([a-zA-Z_][a-zA-Z0-9_]*)(?:\[(\d+)(?::(\d+))?\])?$', port_spec)

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
                raise ValueError(
                    f"Invalid bit range [{high_bit}:{low_bit}] - high must be >= low")
            return (port_name, high_bit, low_bit)

    def _extract_bits(self, value: int, high_bit: int, low_bit: int) -> int:
        # Extract bits [high:low] from value
        num_bits = high_bit - low_bit + 1
        mask = (1 << num_bits) - 1
        return (value >> low_bit) & mask

    def _set_bits(self, original: int, new_bits: int, high_bit: int, low_bit: int, width: int) -> int:
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
