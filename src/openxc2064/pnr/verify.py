"""RTL-vs-fabric equivalence harness used as an acceptance gate for
every placed-and-routed design.

Drives the same input vectors through RTLSimulator and FabricSimulator and
requires every output pad to match cycle-for-cycle. Exhaustive vectors 
when the input count is small, seeded random otherwise.
"""

from __future__ import annotations

import random

from openxc2064.mapping.xc2064_primitives import IOB
from openxc2064.simulator import FabricSimulator, RTLSimulator
from openxc2064.synthesis.rtl_nodes import Netlist

class EquivalenceError(Exception):
    pass


def verify_equivalence(
    packed: Netlist,
    config,
    placement,
    *,
    max_exhaustive_inputs: int = 8,
    random_vectors: int = 200,
    seed: int = 0,
) -> int:
    """Raises EquivalenceError on any mismatch; returns the number of
    vectors checked."""
    

    fabric_sim = FabricSimulator(config)
    if fabric_sim.warnings:
        raise EquivalenceError(
            "fabric simulator warnings (router bug?): "
            + "; ".join(fabric_sim.warnings)
        )
    rtl_sim = RTLSimulator(packed)

    iobs = [n for n in packed.nodes if isinstance(n, IOB)]
    inputs = sorted((n for n in iobs if n.is_input), key=lambda n: n.pad_name)
    outputs = sorted((n for n in iobs if n.is_output), key=lambda n: n.pad_name)
    if not inputs or not outputs:
        raise EquivalenceError("design has no input or no output pads")

    n_inputs = len(inputs)
    if n_inputs <= max_exhaustive_inputs:
        single = [
            tuple((value >> i) & 1 for i in range(n_inputs))
            for value in range(2**n_inputs)
        ]
        vectors = single + single  # second pass exercises sequential state
    else:
        rng = random.Random(seed)
        vectors = [
            tuple(rng.randint(0, 1) for _ in range(n_inputs))
            for _ in range(random_vectors)
        ]

    for step, bits in enumerate(vectors):
        for node, value in zip(inputs, bits):
            rtl_sim.net_values[rtl_sim.input_ports[node.pad_name]] = value
            fabric_sim.set_pad(placement.iob_sites[node.id], value)
        rtl_sim.step()
        fabric_sim.step()
        for node in outputs:
            rtl_value = rtl_sim.net_values[rtl_sim.output_ports[node.pad_name]]
            fabric_value = fabric_sim.get_pad(placement.iob_sites[node.id])
            if rtl_value != fabric_value:
                assignment = {
                    inp.pad_name: v for inp, v in zip(inputs, bits)
                }
                raise EquivalenceError(
                    f"output '{node.pad_name}' mismatch at step {step} "
                    f"(inputs {assignment}): RTL={rtl_value} fabric={fabric_value}"
                )
    return len(vectors)
