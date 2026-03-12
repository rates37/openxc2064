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
    """
    def run(self, netlist: Netlist) -> Netlist:
        new_nl = Netlist(netlist.module_name)
        net_map = {}


        # copy over top level inputs:
        for node in netlist.nodes:
            if isinstance(node, Input):
                new_node = Input(f"in{len(new_nl.nodes)}", inputs=[], outputs=[], port_name=node.port_name)
                new_nl.nodes.append(new_node)
                
                for old_out_net in node.outputs:
                    new_net = new_nl.create_net(old_out_net.name, old_out_net.width)
                    new_node.outputs.append(new_net)
                    new_net.drivers.append(new_node)
                    net_map[old_out_net.name] = new_net
                    new_nl.inputs.append(new_net)
        
        # add outputs and traverse computational graph backwards
        for out_net in netlist.outputs:
            new_out_net = self._map_cone(out_net, new_nl, net_map)
            new_nl.outputs.append(new_out_net)
        
        return new_nl


    def _map_cone(self, target_net: Net, new_nl: Netlist, net_map: dict) -> Net:
        if target_net.name in net_map:
            return net_map[target_net.name]
        
        assert len(target_net.drivers) >= 1
        driver = target_net.drivers[0]
        
        if isinstance(driver, Input):
            raise AssertionError(f"Input nets should have been pre-populated in net_map: {target_net.name}")
        
        # handle DFFs and constants separately (don't waste LUTs on them yet)
        elif isinstance(driver, DFF):
            new_dff = DFF(id=driver.id, inputs=[], outputs=[], edge=driver.edge)
            new_nl.nodes.append(new_dff)
            dff_out_net = new_nl.create_net(target_net.name, target_net.width)
            new_dff.outputs.append(dff_out_net)
            dff_out_net.drivers.append(new_dff)
            
            net_map[target_net.name] = dff_out_net
            
            for in_net in driver.inputs:
                new_in_net = self._map_cone(in_net, new_nl, net_map)
                new_dff.inputs.append(new_in_net)
                new_in_net.sinks.append(new_dff)

            return dff_out_net
        
        
        elif isinstance(driver, Constant):
            new_const = Constant(id=driver.id, inputs=[], outputs=[], value=driver.value)
            new_nl.nodes.append(new_const)
            const_out_net = new_nl.create_net(target_net.name, target_net.width)
            new_const.outputs.append(const_out_net)
            const_out_net.drivers.append(new_const)
            
            net_map[target_net.name] = const_out_net
            return const_out_net
            
        
        
        elif isinstance(driver, LogicGate):
            boundary_nets = {net.name: net for net in driver.inputs}
            
            # greedily try to expand logic gates:
            while True:
                expanded = False
                
                for net_name, net in list(boundary_nets.items()):
                    if len(net.drivers) == 1 and isinstance(net.drivers[0], LogicGate):
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
                new_in_nets.append(self._map_cone(n, new_nl, net_map))
            
            # pre-evaluate the literal numeric 2^K bit mask Truth table
            truth_table = 0
            k = len(cut_inputs)
            
            for state in range(1<<k):
                memo = {}
                for i,n in enumerate(cut_inputs):
                    memo[n.name] = (state >> i) & 1
                
                for n in boundary_nets.values():
                    if len(n.drivers) == 1 and isinstance(n.drivers[0], Constant):
                        memo[n.name] = n.drivers[0].value & 1 # type: ignore
                
                def eval_net(n: Net) -> int:
                    if n.name in memo:
                        return memo[n.name]
                    driver = n.drivers[0]
                    in_vals = [eval_net(i) for i in driver.inputs]
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
                    return res
                    
                bit = eval_net(target_net)
                if bit:
                    truth_table |= (1 << state)

            lut_out_net = new_nl.create_net(target_net.name, target_net.width)
            net_map[target_net.name] = lut_out_net
            
            if k == 0:
                lut_node = Constant(f"const{len(new_nl.nodes)}", inputs=[], outputs=[], value=truth_table&1)
                new_nl.nodes.append(lut_node)
                lut_node.outputs.append(lut_out_net)
                lut_out_net.drivers.append(lut_node)
            else:
                lut_node = LUT(id=f"lut{len(new_nl.nodes)}", inputs=[], outputs=[], truth_table=truth_table, k=k)
                new_nl.nodes.append(lut_node)
                lut_node.outputs.append(lut_out_net)
                lut_out_net.drivers.append(lut_node)
                
                for new_in_net in new_in_nets:
                    lut_node.inputs.append(new_in_net)
                    new_in_net.sinks.append(lut_node)
                    
            return lut_out_net

        else:
            raise ValueError(f"Technology Mapper encountered unsupported Node Primitive driver of type: {type(driver)}")
