from __future__ import annotations
from ..synthesis.rtl_nodes import Net, Netlist, DFF, Input, Constant, LogicGate
from typing import Callable


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
        self.ops: dict[str, Callable[[list], int]] = {
            "AND": lambda x: x[0] & x[1] if len(x) >= 2 else 0,
            "OR": lambda x: x[0] | x[1] if len(x) >= 2 else 0,
            "XOR": lambda x: x[0] ^ x[1] if len(x) >= 2 else 0,
            "NOT": lambda x: ~x[0] if len(x) >= 1 else 0,
            "BUF": lambda x: x[0] if len(x) >= 1 else 0,
            "ADD": lambda x: x[0] + x[1] if len(x) >= 2 else 0,
            "SUB": lambda x: x[0] - x[1] if len(x) >= 2 else 0,
            "NEQ": lambda x: 1 if (x[0] != x[1]) else 0 if len(x) >= 2 else 0,
            "MUX": self._mux_op,
            # todo: indexing
        }

        self._initialise()

    def set(self, port_name: str, value: int) -> None:
        if port_name not in self.input_ports:
            raise ValueError(f"Input port '{port_name}' not found in design.")

        net_name = self.input_ports[port_name]
        net = self.net_name_to_net[net_name]

        value_masked = self._mask_value(value, net.width)
        self.net_values[net_name] = value_masked

    def get(self, port_name: str) -> int:
        # gets current value of output port (using unsigned binary)
        if port_name not in self.output_ports:
            raise ValueError(f"Output port '{port_name}' not found in design.")
        net_name = self.output_ports[port_name]
        return self.net_values.get(net_name, 0)

    def get_net(self, net_name: str) -> int:
        # get current value of internal net (basically only for debugging since net name is created automatically by the synthesiser)
        if net_name in self.net_values:
            return self.net_values[net_name]
        raise ValueError(f"Net '{net_name}' not found in design.")

    def get_net_signed(self, net_name: str) -> int:
        if net_name not in self.net_values:
            raise ValueError(f"Net '{net_name}' not found in design.")
        net = self.net_name_to_net[net_name]
        value = self.net_values[net_name]
        width = net.width

        if value & (1 << (width - 1)):  # if it's a negative value
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
        # masks a value to fit within specified bit width using 2's comp
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
                        result_masked = self._mask_value(result, output_net.width)
                        prev_value = self.net_values.get(output_net.name, 0)
                        if prev_value != result_masked:
                            self.net_values[output_net.name] = result_masked
                            changed_flag = True

                elif isinstance(n, DFF):
                    q_value = self.dff_state.get(n.id, 0)
                    if n.outputs:
                        output_net = n.outputs[0]
                        q_value_masked = self._mask_value(q_value, output_net.width)
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
