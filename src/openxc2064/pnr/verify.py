"""RTL-vs-fabric equivalence harness used as an acceptance gate for
every placed-and-routed design.

Drives the same input vectors through RTLSimulator and FabricSimulator and
requires every output pad to match cycle-for-cycle. Exhaustive vectors
when the (data) input count is small, seeded random otherwise.

When the design has a clock pad (a net feeding a K pin, driven by an input
IOB) that pad is not treated as a data bit: instead, for each data vector the
harness drives a real clock protocol -- pulsing the clock low->high for a
configurable number of cycles and comparing every output after each phase.
Without this a sequential design is only exercised for the couple of rising
edges an exhaustive/random sweep of the clock bit happens to produce.
"""

from __future__ import annotations

import random

from openxc2064.mapping.xc2064_primitives import IOB
from openxc2064.simulator import FabricSimulator, RTLSimulator
from openxc2064.synthesis.rtl_nodes import Netlist

from .design_view import DesignView

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
    clock_cycles: int = 8,
) -> int:
    """Raises EquivalenceError on any mismatch; returns the number of
    output comparisons performed (one per stepped phase)."""

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

    # a clock pad drives a K pin from an input IOB; it must be pulsed by the
    # protocol below, not swept as a data bit
    clock_net = DesignView(packed).clock_net
    clock_node = None
    if clock_net is not None and clock_net.driver[1] == "I":
        clock_id = clock_net.driver[0]
        clock_node = next((n for n in inputs if n.id == clock_id), None)

    data_inputs = [n for n in inputs if n is not clock_node]

    n_inputs = len(data_inputs)
    if n_inputs <= max_exhaustive_inputs:
        vectors = [
            tuple((value >> i) & 1 for i in range(n_inputs))
            for value in range(2**n_inputs)
        ]
        if clock_node is None:
            vectors = vectors + vectors  # second pass exercises sequential state
    else:
        rng = random.Random(seed)
        vectors = [
            tuple(rng.randint(0, 1) for _ in range(n_inputs))
            for _ in range(random_vectors)
        ]

    checks = 0

    def compare(step: int, bits: tuple, phase: str) -> None:
        nonlocal checks
        checks += 1
        for node in outputs:
            rtl_value = rtl_sim.net_values[rtl_sim.output_ports[node.pad_name]]
            fabric_value = fabric_sim.get_pad(placement.iob_sites[node.id])
            if rtl_value != fabric_value:
                assignment = {inp.pad_name: v for inp, v in zip(data_inputs, bits)}
                raise EquivalenceError(
                    f"output '{node.pad_name}' mismatch at step {step}{phase} "
                    f"(inputs {assignment}): RTL={rtl_value} fabric={fabric_value}"
                )

    for step, bits in enumerate(vectors):
        for node, value in zip(data_inputs, bits):
            rtl_sim.net_values[rtl_sim.input_ports[node.pad_name]] = value
            fabric_sim.set_pad(placement.iob_sites[node.id], value)

        if clock_node is None:
            rtl_sim.step()
            fabric_sim.step()
            compare(step, bits, "")
            continue

        # drive the clock low->high for clock_cycles, comparing each phase
        for cycle in range(clock_cycles):
            for clk in (0, 1):
                rtl_sim.net_values[rtl_sim.input_ports[clock_node.pad_name]] = clk
                fabric_sim.set_pad(placement.iob_sites[clock_node.id], clk)
                rtl_sim.step()
                fabric_sim.step()
                compare(step, bits, f" cycle {cycle} clk={clk}")

    return checks
