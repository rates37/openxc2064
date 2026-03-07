from openxc2064.synthesis.rtl_nodes import (
    DFF,
    Net,
    Constant,
    Input,
    Node,
    Netlist,
    LogicGate,
)


class LoweringPass:
    """
    Translates a generic, AST-level netlist (containing multi-bit operations
    like ADD, EQ, SUB, etc.) into a bit-level primitive Netlist containing
    only single-bit wires and primitive logic gates (AND, OR, XOR, NOT, MUX,
    DFF, etc.).
    """

    def __init__(self) -> None:
        self.net_map: dict[str, list[Net]] = {}

    def run(self, netlist: Netlist) -> Netlist:
        self.net_map.clear()
        new_netlist = Netlist(netlist.module_name)

        # map all old generic (multi-bit) nets to arrays of 1-bit nets:
        for old_net in netlist.nets:
            arr = []
            for i in range(old_net.width):
                new_n = new_netlist.create_net(f"{old_net.name}[{i}]", width=1)
                arr.append(new_n)
            self.net_map[old_net.name] = arr

        # track top-level I/O mpped to the new 1-bit nets:
        for old_input in netlist.inputs:
            new_netlist.inputs.extend(self.net_map[old_input.name])
        for old_output in netlist.outputs:
            new_netlist.outputs.extend(self.net_map[old_output.name])

        # recreate all logic using primitive expansions only:
        for node in netlist.nodes:
            self._simplify_node(node, new_netlist)

        return new_netlist

    def _simplify_node(self, node: Node, new_netlist: Netlist) -> None:
        if isinstance(node, Input):
            out_arr = self.net_map[node.outputs[0].name]
            for i, net in enumerate(out_arr):
                new_netlist.add_input(f"{node.port_name}[{i}]", net)

        elif isinstance(node, Constant):
            val = node.value
            out_arr = self.net_map[node.outputs[0].name]
            for i, net in enumerate(out_arr):
                bit_val = 1 if (val & (1 << i)) else 0
                new_netlist.add_const(bit_val, net)

        elif isinstance(node, DFF):
            d_arr = self.net_map[node.inputs[0].name]
            clk_arr = self.net_map[node.inputs[1].name]
            q_arr = self.net_map[node.outputs[0].name]
            for i in range(len(q_arr)):
                new_netlist.add_dff([d_arr[i], clk_arr[0]], [q_arr[i]], edge=node.edge)

        elif isinstance(node, LogicGate):
            pass
