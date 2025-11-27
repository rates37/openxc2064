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
        for _iteration in range(max_iterations):
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
                    # todo
                    pass

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
