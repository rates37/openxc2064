from abc import ABC, abstractmethod
from openxc2064.synthesis.rtl_nodes import Netlist, DFF, Constant, Input
from openxc2064.mapping.xc2064_primitives import LUT, CLB, IOB
from itertools import permutations
from typing import Any


class CapacityError(Exception):
    pass


class Packer(ABC):
    """
    Abstract base class for geometrically packing discrete LUTs
    and DFFs into generic XC2064 Configurable Logic Blocks.
    """

    def __init__(self, max_clbs: int = 64):
        self.max_clbs = max_clbs

    @abstractmethod
    def run(self, netlist: Netlist) -> Netlist:
        pass


def route_lut(
    lut: LUT | None, A: str | None, B: str | None, C: str | None, D: str | None
) -> dict[str, int] | None:
    """Attempts to route a single LUT's net requirements onto the physical A,B,C,D
    pins of the CLB, resolving specific Mux configurations (sel_in1, sel_in2, sel_in3).

    Args:
        lut (LUT | None): The logical LUT instance to map, or None if the slot is empty
        A (str | None): The net names currently bound to the outer CLB's A pin. Or None if the pin is not bound.
        B (str | None): The net names currently bound to the outer CLB's B pin. Or None if the pin is not bound.
        C (str | None): The net names currently bound to the outer CLB's C pin. Or None if the pin is not bound.
        D (str | None): The net names currently bound to the outer CLB's D pin. Or None if the pin is not bound.

    Returns:
        dict[str, int] | None: A dictionary containing the keys sel_in1, sel_in2, sel_in3
        to configure the CLB, or None if the routing is impossible.
    """
    if lut is None:
        return {"sel_in1": 0, "sel_in2": 0, "sel_in3": 0, "truth_table": 0}

    req_names = [n.name for n in lut.inputs]

    for sel_in1 in [0, 1]:
        in0 = B if sel_in1 else A
        for sel_in2 in [0, 1]:
            in1 = C if sel_in2 else B
            for sel_in3 in [
                0,
                1,
            ]:  # Q (2) disabled, using pure combinatorial mapping for now
                in2 = D if sel_in3 else C

                # Check subset coverage
                prov = [in0, in1, in2]
                valid = True
                prov_copy = list(prov)
                for req in req_names:
                    if req in prov_copy:
                        prov_copy.remove(req)
                    else:
                        valid = False
                        break

                if valid:
                    # Compute truth table
                    new_tt = 0
                    for state in range(8):
                        val0 = (state >> 0) & 1
                        val1 = (state >> 1) & 1
                        val2 = (state >> 2) & 1

                        phys = {in0: val0, in1: val1, in2: val2}

                        if in0 is not None and in0 == in1 and val0 != val1:
                            continue
                        if in0 is not None and in0 == in2 and val0 != val2:
                            continue
                        if in1 is not None and in1 == in2 and val1 != val2:
                            continue

                        orig_state = 0
                        for i, req in enumerate(req_names):
                            if phys[req]:
                                orig_state |= 1 << i

                        if (lut.truth_table >> orig_state) & 1:
                            new_tt |= 1 << state

                    return {
                        "sel_in1": sel_in1,
                        "sel_in2": sel_in2,
                        "sel_in3": sel_in3,
                        "truth_table": new_tt,
                    }
    return None


def find_clb_orientation(
    lut_f_node: LUT | None, lut_g_node: LUT | None
) -> dict[str, Any] | None:
    """Evaluates two independent LUTs (F and G) and attempts to find a shared physical
    assignment of 4 external nets onto the A,B,C,D pins such that both LUTs can
    successfully route their required inputs simultaneously.

    Args:
        lut_f_node (LUT | None): The LUT to place in the F slot
        lut_g_node (LUT | None): The LUT to place in the G slot

    Returns:
        dict[str, Any] | None: A finalised configuration dict mapping next A,B,C,D and
        containing the exact MUX select states and truth tables for F and G.
        Returns None if the two LUTs cannot be mapped into a single CLB.
    """
    all_inputs = set()
    if lut_f_node:
        all_inputs.update(n.name for n in lut_f_node.inputs)
    if lut_g_node:
        all_inputs.update(n.name for n in lut_g_node.inputs)

    # a single CLB can only have 4 inputs
    if len(all_inputs) > 4:
        return None

    inputs_list = list(all_inputs)
    while len(inputs_list) < 4:  # pad input list to always be length 4
        inputs_list.append(None)

    for A, B, C, D in permutations(inputs_list):
        opts_f = route_lut(lut_f_node, A, B, C, D)
        if opts_f is None:
            continue
        opts_g = route_lut(lut_g_node, A, B, C, D)
        if opts_g is None:
            continue

        return {
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "lut_f_init": opts_f["truth_table"],
            "sel_f_in1": opts_f["sel_in1"],
            "sel_f_in2": opts_f["sel_in2"],
            "sel_f_in3": opts_f["sel_in3"],
            "lut_g_init": opts_g["truth_table"],
            "sel_g_in1": opts_g["sel_in1"],
            "sel_g_in2": opts_g["sel_in2"],
            "sel_g_in3": opts_g["sel_in3"],
        }
    return None


def shared_input_count(lut_a: LUT | None, lut_b: LUT | None) -> int:
    """Number of input nets two LUTs have in common.

    This is the packing affinity metric: LUTs sharing inputs packed into one
    CLB remove whole nets from the routing problem and leave A/B/C/D pins
    free. (Producer/consumer co-packing deliberately scores nothing. The
    XC2064 input muxes only select from A/B/C/D/Q, so a paired LUT's output
    still has to leave via X/Y and re-enter through a pin.)
    """
    if lut_a is None or lut_b is None:
        return 0
    return len({n.name for n in lut_a.inputs} & {n.name for n in lut_b.inputs})


class GreedyPacker(Packer):
    """Greedy implementation of a CLB packer algorithm.

    Clustering is connectivity-driven: at each step the legal pairing with
    the most shared input nets is taken, rather than the first legal one.
    """

    def run(self, netlist: Netlist) -> Netlist | None:
        # create blank netlist:
        new_nl = Netlist(netlist.module_name)

        ## ! Map inputs to IOBs:
        inputs = [n for n in netlist.nodes if isinstance(n, Input)]
        for inp in inputs:
            iob = IOB(
                new_nl.next_node_id("iob_in_"), inputs=[], outputs=[], ts_mux_sel=0
            )
            iob.inputs = [None, None, None, None]
            iob.outputs = [None, None]
            new_nl.nodes.append(iob)

            # The PIN pad net
            pin_net_name = f"pad_{inp.outputs[0].name}"
            pin_net = new_nl.create_net(pin_net_name, inp.outputs[0].width)
            iob.inputs[0] = pin_net
            pin_net.sinks.append(iob)
            iob.pad_name = inp.outputs[0].name
            new_nl.inputs.append(pin_net)

            # The IN net
            for old_out_net in inp.outputs:
                new_net = new_nl.create_net(old_out_net.name, old_out_net.width)
                iob.outputs[1] = new_net
                new_net.drivers.append(iob)
                # Top down inputs are no longer internal logic nets, they are the PINs

        ## ! Map constants:
        constants = [n for n in netlist.nodes if isinstance(n, Constant)]
        for c in constants:
            new_c = Constant(
                new_nl.next_node_id("const"), inputs=[], outputs=[], value=c.value
            )
            new_nl.nodes.append(new_c)
            for old_out_net in c.outputs:
                new_net = new_nl.create_net(old_out_net.name, old_out_net.width)
                new_c.outputs.append(new_net)
                new_net.drivers.append(new_c)

        ## ! Extract actual logic:
        unpacked_luts = list(n for n in netlist.nodes if isinstance(n, LUT))
        unpacked_dffs = list(n for n in netlist.nodes if isinstance(n, DFF))
        clb_configs = []

        ## ! Handle DFFs (since they must be driven by F):
        for dff in list(unpacked_dffs):
            data_net = dff.inputs[0]
            driving_lut = None
            if len(data_net.drivers) == 1 and isinstance(data_net.drivers[0], LUT):
                if data_net.drivers[0] in unpacked_luts:
                    driving_lut = data_net.drivers[0]
                    unpacked_luts.remove(driving_lut)

            if not driving_lut:
                # Standalone DFF -> Buffer LUT F
                # use 0xAA (10101010) because we want the output to exactly mirror in0
                driving_lut = LUT(f"dummy_{dff.id}", inputs=[data_net], outputs=[data_net], truth_table=0xAA)

            clb_configs.append({"lut_f": driving_lut, "lut_g": None, "dff": dff})
            unpacked_dffs.remove(dff)

        ## ! Try to pack rest of remaining LUTs into unused G-lut slots
        # all existing LUTs only have their F-lut in use, so pack as much as possible
        # into the un-used G-luts, taking the (slot, LUT) pairing with the most
        # shared input nets each round
        while True:
            best = None  # (score, clb, lut)
            for clb in clb_configs:
                if clb["lut_g"] is not None:
                    continue
                for lut in unpacked_luts:
                    # check if there exists a routable orientation for this pair
                    if find_clb_orientation(clb["lut_f"], lut) is None:
                        continue
                    score = shared_input_count(clb["lut_f"], lut)
                    if best is None or score > best[0]:
                        best = (score, clb, lut)
            if best is None:
                break
            _, clb, lut = best
            clb["lut_g"] = lut
            unpacked_luts.remove(lut)

        ##! Pack isolated LUT pairs
        # any LUTs that didn't get paired into DFF luts: repeatedly take the legal
        # pair with the most shared input nets
        while unpacked_luts:
            best = None  # (score, lut_a, lut_b)
            for i, lut_a in enumerate(unpacked_luts):
                for lut_b in unpacked_luts[i + 1:]:
                    if find_clb_orientation(lut_a, lut_b) is None:
                        continue
                    score = shared_input_count(lut_a, lut_b)
                    if best is None or score > best[0]:
                        best = (score, lut_a, lut_b)

            if best is None:
                # no legal pairs remain; the rest each get their own CLB
                for lut in unpacked_luts:
                    clb_configs.append({"lut_f": lut, "lut_g": None, "dff": None})
                unpacked_luts = []
            else:
                _, lut_a, lut_b = best
                unpacked_luts.remove(lut_a)
                unpacked_luts.remove(lut_b)
                clb_configs.append({"lut_f": lut_a, "lut_g": lut_b, "dff": None})

        if len(clb_configs) > self.max_clbs:
            raise CapacityError(f"Design uses {len(clb_configs)} CLBs.")

        ##! Create design physical structure:
        for idx, config in enumerate(clb_configs):
            orient = find_clb_orientation(config["lut_f"], config["lut_g"])
            if not orient:
                raise CapacityError("MUX routing failure.")

            new_clb = CLB(
                id=f"clb{idx}",
                inputs=[],
                outputs=[],
                dff=config["dff"],
                lut_f_init=orient["lut_f_init"],
                lut_g_init=orient["lut_g_init"],
                sel_f_in1=orient["sel_f_in1"],
                sel_f_in2=orient["sel_f_in2"],
                sel_f_in3=orient["sel_f_in3"],
                sel_g_in1=orient["sel_g_in1"],
                sel_g_in2=orient["sel_g_in2"],
                sel_g_in3=orient["sel_g_in3"],
            )
            new_nl.nodes.append(new_clb)

            # Map Inputs 0-3 (A, B, C, D) + K
            ordered_pins = [orient["A"], orient["B"], orient["C"], orient["D"], None]
            if config["dff"]:
                ordered_pins[4] = config["dff"].inputs[1].name  # assigned to K
                new_clb.sel_clk1 = 2
                new_clb.sel_clk2 = 1

            for pin_name in ordered_pins:
                if pin_name:
                    mapped_in = new_nl.get_net(pin_name)
                    if mapped_in is None:
                        mapped_in = new_nl.create_net(pin_name, 1)
                    new_clb.inputs.append(mapped_in)
                    mapped_in.sinks.append(new_clb)
                else:
                    new_clb.inputs.append(None)  # Pad empty pins

            # Map Outputs
            # Resolve X MUX: F or G or Q
            # Resolve Y MUX: F or G or Q
            outputs_needed = []
            if config["dff"]:
                outputs_needed.append(("Q", config["dff"]))
                
            if config["lut_f"]:
                f_net = config["lut_f"].outputs[0]
                is_f_exported = f_net in netlist.outputs
                for sink in f_net.sinks:
                    if sink != config["dff"]:
                        is_f_exported = True
                        break
                if is_f_exported:
                    outputs_needed.append(("F", config["lut_f"]))
                    
            if config["lut_g"]:
                outputs_needed.append(("G", config["lut_g"]))

            if len(outputs_needed) > 2:
                raise CapacityError(
                    "CLB requires a maximum of 2 outputs to be exported."
                )

            if len(outputs_needed) > 0:
                name, node = outputs_needed[0]
                if name == "Q":
                    new_clb.sel_x = 1
                elif name == "F":
                    new_clb.sel_x = 2
                else:
                    new_clb.sel_x = 0

                out_net_name = node.outputs[0].name
                mapped_out = new_nl.get_net(out_net_name)
                if mapped_out is None:
                    mapped_out = new_nl.create_net(out_net_name, 1)
                new_clb.outputs.append(mapped_out)
                mapped_out.drivers.append(new_clb)

            if len(outputs_needed) > 1:
                name, node = outputs_needed[1]
                if name == "Q":
                    new_clb.sel_y = 1
                elif name == "F":
                    new_clb.sel_y = 2
                else:
                    new_clb.sel_y = 0

                out_net_name = node.outputs[0].name
                mapped_out = new_nl.get_net(out_net_name)
                if mapped_out is None:
                    mapped_out = new_nl.create_net(out_net_name, 1)
                new_clb.outputs.append(mapped_out)
                mapped_out.drivers.append(new_clb)

        ##! Map top outputs:
        for out_net in netlist.outputs:
            iob = IOB(
                new_nl.next_node_id("iob_out_"), inputs=[], outputs=[], ts_mux_sel=2
            )
            iob.inputs = [None, None, None, None]
            iob.outputs = [None, None]
            new_nl.nodes.append(iob)

            # The OUT net from internal logic
            mapped_in = new_nl.nets_by_name[out_net.name]
            iob.inputs[1] = mapped_in
            mapped_in.sinks.append(iob)

            # The PIN pad net
            pin_net_name = f"pad_{out_net.name}"
            pin_net = new_nl.create_net(pin_net_name, out_net.width)
            iob.outputs[0] = pin_net
            pin_net.drivers.append(iob)
            iob.pad_name = out_net.name
            new_nl.outputs.append(pin_net)

        return new_nl
