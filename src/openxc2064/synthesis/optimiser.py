from .rtl_nodes import Netlist, LogicGate, Constant, Input, Node, Net
from collections import deque

class Optimiser:
    """
    Logic optimiser for a Netlist
    """
    def __init__(self) -> None:
        pass


    def optimise(self, netlist: Netlist, max_iterations: int | None = None) -> Netlist:
        """
        Run repeated optimisation passes over a netlist to produce a minimised
        design. Runs repeatedly until the netlist converges, or until max_iterations
        has been exceeded.

        Operates on (and modifies) the input Netlist.
        """
        converged = False
        iteration = 0
        while not converged:

            changed_tdc = self._trim_dead_code(netlist)
            changed_fc = self._fold_constants(netlist)
            changed_sl = self._simplify_logic(netlist)

            converged = not (changed_tdc or changed_fc or changed_sl)
            iteration += 1

            if max_iterations is not None and iteration >= max_iterations:
                break

        return netlist
    
    def _trim_dead_code(self, netlist: Netlist) -> bool:
        """
        Remove nodes that do not contribute to any output.
        """
        live_node_ids: set[str] = set()
        queue: list[Node] = deque()

        # inputs are always considered "live" since 
        # they will be driven by external sources
        for node in netlist.nodes:
            if isinstance(node, Input):
                live_node_ids.add(node.id)
                queue.append(node)

        # any node driving an output port must be
        # "live"
        for out_net in netlist.outputs:
            if out_net.source is not None:
                live_node_ids.add(out_net.source.id)
                queue.append(out_net.source)
        
        # trace the computational graph backwards, starting from the 
        # nodes that drive outputs
        while len(queue) > 0:
            node = queue.popleft()
            
            # for each node that drives this node
            for in_net in node.inputs:
                if in_net.source is not None and in_net.source.id not in live_node_ids:
                    # the source of this driver must also be considered "live"
                    live_node_ids.add(in_net.source.id)
                    queue.append(in_net.source)

        # now that we have a set of all "active" or "live" nodes, we can
        # remove all other nodes from the netlist
        dead_node_ids: set[str] = set()
        for node in netlist.nodes:
            if node.id not in live_node_ids:
                dead_node_ids.add(node.id)
        
        # if all nodes are used, can return False
        if len(dead_node_ids) == 0:
            return False

        netlist.nodes = [n for n in netlist.nodes if n.id not in dead_node_ids]

        # reconstruct the netlist by traversing remaining nodes and ports:
        # todo: using id() for this is a bit of a smell but it's good enough for now
        # debugging may be more difficult if looking at object ids rather than human
        # readable attributes, but changing would require a bigger refactor, and 
        # this usage is confined to this method only
        live_nets_dict: dict[int, Net] = {}
        for out_net in netlist.outputs:
            live_nets_dict[id(out_net)] = out_net
        for in_net in netlist.inputs:
            live_nets_dict[id(in_net)] = in_net
            
        for node in netlist.nodes:
            for n in node.inputs:
                live_nets_dict[id(n)] = n
            for n in node.outputs:
                live_nets_dict[id(n)] = n

        netlist.nets = list(live_nets_dict.values())

        # clean up sinks/sources on live nodes to remove dangling/dead references:
        for net in netlist.nets:
            net.sinks = [s for s in net.sinks if s.id not in dead_node_ids]
            if net.source is not None and net.source.id in dead_node_ids:
                net.source = None 

        return True

    def _fold_constants(self, netlist: Netlist) -> bool:
        """
        Evaluate constant expressions and replace them with constants.
        """
        pass

    def _simplify_logic(self, netlist: Netlist) -> bool:
        pass
