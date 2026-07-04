from openxc2064.synthesis.rtl_nodes import Input
from abc import ABC, abstractmethod
from openxc2064.synthesis.rtl_nodes import Netlist, Net, DFF, Constant, LogicGate
from openxc2064.mapping.xc2064_primitives import LUT

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

class GreedyMapper(TechnologyMapper):
    """
    Greedily clusters 1-bit wide netlist into K-input LUTs.

    absorb_multi_sink_gates controls what happens to a gate whose output
    feeds several cones: True (default) duplicates its logic into every
    consuming LUT's truth table (fewer LUTs, wider fan-out of the cone
    inputs); False cuts at the shared net so the gate gets a single LUT of
    its own that all consumers reference.
    """
    def __init__(self, k_max: int = 3, absorb_multi_sink_gates: bool = True):
        super().__init__(k_max)
        self.absorb_multi_sink_gates = absorb_multi_sink_gates

    def run(self, netlist: Netlist) -> Netlist:
        new_nl = Netlist(netlist.module_name)

        # copy over top level inputs:
        for node in netlist.nodes:
            if isinstance(node, Input):
                new_node = Input(new_nl.next_node_id("in"), inputs=[], outputs=[], port_name=node.port_name)
                new_nl.nodes.append(new_node)

                for old_out_net in node.outputs:
                    new_net = new_nl.create_net(old_out_net.name, old_out_net.width)
                    new_node.outputs.append(new_net)
                    new_net.drivers.append(new_node)
                    new_nl.inputs.append(new_net)

        # add outputs and traverse computational graph backwards
        for out_net in netlist.outputs:
            new_out_net = self._map_cone(out_net, new_nl)
            new_nl.outputs.append(new_out_net)

        return new_nl


    def _map_cone(self, target_net: Net, new_nl: Netlist) -> Net:
        already_mapped = new_nl.get_net(target_net.name)
        if already_mapped is not None:
            return already_mapped

        assert len(target_net.drivers) >= 1
        driver = target_net.drivers[0]

        if isinstance(driver, Input):
            raise AssertionError(f"Input nets should have been pre-populated in the new netlist: {target_net.name}")

        # handle DFFs and constants separately (don't waste LUTs on them yet)
        elif isinstance(driver, DFF):
            new_dff = DFF(id=driver.id, inputs=[], outputs=[], edge=driver.edge)
            new_nl.nodes.append(new_dff)
            # created (and registered by name) before recursing, so feedback
            # paths through this DFF resolve to it instead of recursing forever
            dff_out_net = new_nl.create_net(target_net.name, target_net.width)
            new_dff.outputs.append(dff_out_net)
            dff_out_net.drivers.append(new_dff)

            for in_net in driver.inputs:
                new_in_net = self._map_cone(in_net, new_nl)
                new_dff.inputs.append(new_in_net)
                new_in_net.sinks.append(new_dff)

            return dff_out_net


        elif isinstance(driver, Constant):
            # minted (not cloned) id: a cloned "constN" could collide with the
            # "constN" ids minted for constant-folded LUTs below
            new_const = Constant(id=new_nl.next_node_id("const"), inputs=[], outputs=[], value=driver.value)
            new_nl.nodes.append(new_const)
            const_out_net = new_nl.create_net(target_net.name, target_net.width)
            new_const.outputs.append(const_out_net)
            const_out_net.drivers.append(new_const)

            return const_out_net
            
        
        
        elif isinstance(driver, LogicGate):
            boundary_nets = {net.name: net for net in driver.inputs}
            
            # greedily try to expand logic gates:
            while True:
                expanded = False
                
                for net_name, net in list(boundary_nets.items()):
                    if len(net.drivers) == 1 and isinstance(net.drivers[0], LogicGate):
                        if not self.absorb_multi_sink_gates and len(net.sinks) > 1:
                            # leave the shared net as a cut input so its gate
                            # maps to one LUT reused by every consumer
                            continue
                        cand_node = net.drivers[0]
                        # absorb cand_node:
                        new_bounary = {n.name: n for n in boundary_nets.values() if n.name != net_name}
                        for cand_in in cand_node.inputs:
                            new_bounary[cand_in.name] = cand_in
                        
                        k_count = 0
                        for n in new_bounary.values():
                            if not (len(n.drivers) == 1 and isinstance(n.drivers[0], Constant)):
                                k_count += 1
                        if k_count <= self.k_max:
                            boundary_nets = new_bounary
                            expanded = True
                            break
                
                if not expanded:
                    break
            
            # partition into real nets vs constant nets:
            cut_inputs = []
            for n in boundary_nets.values():
                if not (len(n.drivers) == 1 and isinstance(n.drivers[0], Constant)):
                    cut_inputs.append(n)
            
            # map dynamic inputs nets as pre-reqs:
            new_in_nets = []
            for n in cut_inputs:
                new_in_nets.append(self._map_cone(n, new_nl))
            
            # pre-evaluate the literal numeric 2^K bit mask Truth table
            truth_table = 0
            k = len(cut_inputs)

            # constants inside the cone hold the same value in every state
            const_values = {
                n.name: n.drivers[0].value & 1  # type: ignore
                for n in boundary_nets.values()
                if len(n.drivers) == 1 and isinstance(n.drivers[0], Constant)
            }

            for state in range(1<<k):
                memo = dict(const_values)
                for i,n in enumerate(cut_inputs):
                    memo[n.name] = (state >> i) & 1

                if self._eval_cone_net(target_net, memo):
                    truth_table |= (1 << state)

            lut_out_net = new_nl.create_net(target_net.name, target_net.width)

            if k == 0:
                lut_node = Constant(new_nl.next_node_id("const"), inputs=[], outputs=[], value=truth_table&1)
                new_nl.nodes.append(lut_node)
                lut_node.outputs.append(lut_out_net)
                lut_out_net.drivers.append(lut_node)
            else:
                lut_node = LUT(id=new_nl.next_node_id("lut"), inputs=[], outputs=[], truth_table=truth_table, k=k)
                new_nl.nodes.append(lut_node)
                lut_node.outputs.append(lut_out_net)
                lut_out_net.drivers.append(lut_node)
                
                for new_in_net in new_in_nets:
                    lut_node.inputs.append(new_in_net)
                    new_in_net.sinks.append(lut_node)
                    
            return lut_out_net

        else:
            raise ValueError(f"Technology Mapper encountered unsupported Node Primitive driver of type: {type(driver)}")

    def _eval_cone_net(self, target: Net, memo: dict[str, int]) -> int:
        # evaluate one net of a cone for the input assignment held in memo
        # (cut inputs and cone constants are pre-seeded by the caller).
        # iterative post-order traversal: a cone can absorb an arbitrarily
        # long gate chain
        stack = [target]
        while stack:
            n = stack[-1]
            if n.name in memo:
                stack.pop()
                continue

            driver = n.drivers[0]
            pending = [i for i in driver.inputs if i.name not in memo]
            if pending:
                stack.extend(pending)
                continue

            in_vals = [memo[i.name] for i in driver.inputs]
            op = getattr(driver, "op", "")
            if op == "AND":
                res = in_vals[0] & in_vals[1]
            elif op == "OR":
                res = in_vals[0] | in_vals[1]
            elif op == "XOR":
                res = in_vals[0] ^ in_vals[1]
            elif op == "NOT":
                res = (~in_vals[0])&1
            elif op == "BUF":
                res = in_vals[0]
            elif op == "MUX":
                res = in_vals[1] if in_vals[0] == 0 else in_vals[2]
            else:
                raise ValueError(f"Technology Mapper encountered unsupported op: {op}")

            memo[n.name] = res
            stack.pop()

        return memo[target.name]
