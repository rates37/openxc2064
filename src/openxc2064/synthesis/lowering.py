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
    
    def _add_0(self, netlist: Netlist) -> Net:
        n = netlist.create_net(f"tie0_{len(netlist.nodes)}", 1)
        netlist.add_const(0, n)
        return n

    def _add_1(self, netlist: Netlist) -> Net:
        n = netlist.create_net(f"tie1_{len(netlist.nodes)}", 1)
        netlist.add_const(1, n)
        return n

    def _build_or_tree(self, netlist: Netlist, nets: list[Net], prefix: str) -> Net:
        if len(nets) == 0:
            return self._add_0(netlist)
        if len(nets) == 1:
            return nets[0]
        
        # todo: tweak to balanced binary tree later
        acc = nets[0]
        for i in range(1, len(nets)):
            n_out = netlist.create_net(f"{prefix}_{i}", 1)
            netlist.add_logic("OR", [acc, nets[i]], [n_out])
            acc = n_out
        return acc
    
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
            out_arr = self.net_map[node.outputs[0].name]

            if node.op in ("AND", "OR", "XOR", "LOGIC_AND", "LOGIC_OR"):
                # for bitwise logic, expand into array of 1-bit gates
                a_arr = self.net_map[node.inputs[0].name]
                b_arr = self.net_map[node.inputs[1].name]
                for i in range(len(out_arr)):
                    a_bit = a_arr[i] if i < len(a_arr) else self._add_0(new_netlist)
                    b_bit = b_arr[i] if i < len(b_arr) else self._add_0(new_netlist)
                    real_op = node.op.replace("LOGIC_", "")  # reduce LOGIC_AND to AND at bit level
                    new_netlist.add_logic(real_op, [a_bit, b_bit], [out_arr[i]])

            elif node.op in ("NOT", "LOGIC_NOT", "NEG", "BUF"):
                a_arr = self.net_map[node.inputs[0].name]
                real_op = "NOT" if "NOT" in node.op else "BUF"
                for i in range(len(out_arr)):
                    a_bit = a_arr[i] if i < len(a_arr) else self._add_0(new_netlist)
                    new_netlist.add_logic(real_op, [a_bit], [out_arr[i]])
                    
            elif node.op == "ADD" or node.op == "SUB" or node.op == "NEG":
                a_arr = self.net_map[node.inputs[0].name] if len(node.inputs) > 0 else []
                b_arr = self.net_map[node.inputs[1].name] if len(node.inputs) > 1 else []
                w = len(out_arr)

                if node.op == "NEG":
                    b_arr = a_arr
                    a_arr = []

                # Subtract/Negate using Two's Complement: A-B = A + (~B) + 1
                is_sub = (node.op == "SUB" or node.op == "NEG")

                if is_sub:
                    not_b = []
                    for i in range(w):
                        b_bit = b_arr[i] if i < len(b_arr) else self._add_0(new_netlist)
                        nb = new_netlist.create_net(f"{node.id}_notb_{i}", 1)
                        new_netlist.add_logic("NOT", [b_bit], [nb])
                        not_b.append(nb)
                    b_arr = not_b

                # Ripple Carry Adder logic
                c_net = self._add_1(new_netlist) if is_sub else self._add_0(new_netlist)
                for i in range(w):
                    a_bit = a_arr[i] if i < len(a_arr) else self._add_0(new_netlist)
                    b_bit = b_arr[i] if i < len(b_arr) else self._add_0(new_netlist)
                    s_net = out_arr[i]

                    # S = A ^ B ^ C
                    ab_xor = new_netlist.create_net(f"{node.id}_ab_xor_{i}", 1)
                    new_netlist.add_logic("XOR", [a_bit, b_bit], [ab_xor])
                    new_netlist.add_logic("XOR", [ab_xor, c_net], [s_net])

                    # C_next = (A & B) | (C & (A ^ B))
                    if i < w - 1:
                        ab_and = new_netlist.create_net(f"{node.id}_ab_and_{i}", 1)
                        new_netlist.add_logic("AND", [a_bit, b_bit], [ab_and])

                        c_and = new_netlist.create_net(f"{node.id}_c_and_{i}", 1)
                        new_netlist.add_logic("AND", [c_net, ab_xor], [c_and])

                        c_next = new_netlist.create_net(f"{node.id}_c_{i+1}", 1)
                        new_netlist.add_logic("OR", [ab_and, c_and], [c_next])
                        c_net = c_next

            elif node.op in ("EQ", "NEQ"):
                a_arr = self.net_map[node.inputs[0].name]
                b_arr = self.net_map[node.inputs[1].name]
                w = max(len(a_arr), len(b_arr))

                xor_nets = []
                for i in range(w):
                    a_bit = a_arr[i] if i < len(a_arr) else self._add_0(new_netlist)
                    b_bit = b_arr[i] if i < len(b_arr) else self._add_0(new_netlist)
                    x_net = new_netlist.create_net(f"{node.id}_x_{i}", 1)
                    new_netlist.add_logic("XOR", [a_bit, b_bit], [x_net])
                    xor_nets.append(x_net)

                or_tree_net = self._build_or_tree(new_netlist, xor_nets, f"{node.id}_or")

                out_bit = out_arr[0] # EQ/NEQ is 1-bit result
                if node.op == "EQ":
                    new_netlist.add_logic("NOT", [or_tree_net], [out_bit])
                else:
                    new_netlist.add_logic("BUF", [or_tree_net], [out_bit])
                    
            elif str(node.op).startswith("INDEX:"):
                # statically wire the output to the requested bit in the input array!
                idx = int(node.op.split(":")[1])
                base_arr = self.net_map[node.inputs[0].name]
                new_netlist.add_logic("BUF", [base_arr[idx]], [out_arr[0]])

            elif str(node.op).startswith("SLICE:"):
                msb = int(node.op.split(":")[1])
                lsb = int(node.op.split(":")[2])
                base_arr = self.net_map[node.inputs[0].name]

                step = 1 if msb >= lsb else -1
                idx = 0
                for i in range(lsb, msb + step, step):
                    new_netlist.add_logic("BUF", [base_arr[i]], [out_arr[idx]])
                    idx += 1

            elif str(node.op).startswith("UPDATE:"):
                msb = int(node.op.split(":")[1])
                lsb = int(node.op.split(":")[2])
                old_arr = self.net_map[node.inputs[0].name]
                rhs_arr = self.net_map[node.inputs[1].name]
                
                # copy unchanged bits
                for i in range(len(old_arr)):
                    if lsb <= i <= msb:
                        # Map to the new mapped bit
                        rhs_idx = i - lsb if msb >= lsb else msb - i
                        new_netlist.add_logic("BUF", [rhs_arr[rhs_idx]], [out_arr[i]])
                    else:
                        new_netlist.add_logic("BUF", [old_arr[i]], [out_arr[i]])

            elif node.op == "MUX":
                cond_arr = self.net_map[node.inputs[0].name]
                else_arr = self.net_map[node.inputs[1].name]
                then_arr = self.net_map[node.inputs[2].name]

                cond_bit = cond_arr[0]
                for i in range(len(out_arr)):
                    e_bit = else_arr[i] if i < len(else_arr) else self._add_0(new_netlist)
                    t_bit = then_arr[i] if i < len(then_arr) else self._add_0(new_netlist)
                    new_netlist.add_logic("MUX", [cond_bit, e_bit, t_bit], [out_arr[i]])

            elif node.op in ("LSHIFT", "RSHIFT"):
                data_arr = self.net_map[node.inputs[0].name]
                shift_arr = self.net_map[node.inputs[1].name]
                w = len(out_arr)

                # Barrel Shifter implementation:
                # build log2(W) layers of MUXes. Output of layer 's' is the input to layer 's+1'.
                current_data = data_arr

                for s_bit, s_ctrl_net in enumerate(shift_arr):
                    shift_amount = 1 << s_bit
                    if shift_amount >= w:
                        # Shifting by more than the width just clears the bits, assuming w <= max shift
                        # Note: In many architectures, shift >= width zeroes the output (or is undefined).
                        # Add a MUX layer that zeroes everything if shift_arr[s_bit] is 1.
                        next_data = []
                        for i in range(w):
                            mux_out = new_netlist.create_net(f"{node.id}_l{s_bit}_mux{i}", 1)
                            # if s_ctrl_net == 1: 0, else: current_data[i]
                            new_netlist.add_logic("MUX", [s_ctrl_net, current_data[i], self._add_0(new_netlist)], [mux_out])
                            next_data.append(mux_out)
                        current_data = next_data
                        continue

                    next_data = []
                    for i in range(w):
                        mux_out = new_netlist.create_net(f"{node.id}_l{s_bit}_mux{i}", 1)
                        
                        if node.op == "LSHIFT":
                            # if shift, get from i - shift_amount, else get from i
                            from_idx = i - shift_amount
                            t_bit = current_data[from_idx] if from_idx >= 0 else self._add_0(new_netlist)
                        else:  # RSHIFT
                            from_idx = i + shift_amount
                            t_bit = current_data[from_idx] if from_idx < w else self._add_0(new_netlist)

                        e_bit = current_data[i]
                        # MUX(sel, else, then) -> MUX(s_ctrl_net, unshifted, shifted)
                        new_netlist.add_logic("MUX", [s_ctrl_net, e_bit, t_bit], [mux_out])
                        next_data.append(mux_out)
                    
                    current_data = next_data

                # Final layer output goes to out_arr
                for i in range(w):
                    new_netlist.add_logic("BUF", [current_data[i]], [out_arr[i]])

            else:
                raise ValueError(f"Lowering missing implementation for op: {node.op}")

