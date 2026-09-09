"""Top-level toolchain entry points: HDL source -> placed & routed DeviceConfig.

This module owns pipeline composition. The frontend (parse -> synthesise ->
optimise -> lower -> optimise -> map -> pack) lives here.
"""

from __future__ import annotations

from openxc2064.device.config import DeviceConfig
from openxc2064.device.fabric import Fabric
from openxc2064.hdl import parse_hdl
from openxc2064.mapping.mapper import GreedyMapper
from openxc2064.mapping.packer import GreedyPacker
from openxc2064.pnr.clocking import ClockSource
from openxc2064.pnr.constraints import PinConstraints
from openxc2064.pnr.pin_assignments import PinAssignments
from openxc2064.pnr.flow import place_and_route
from openxc2064.pnr.placement import AnnealingPlacer, Placement
from openxc2064.pnr.router import PathFinderRouter, RoutingReport
from openxc2064.synthesis import HDLElaborator, LoweringPass, Optimiser, Synthesiser
from openxc2064.synthesis.rtl_nodes import Netlist


def compile_hdl_to_packed(hdl: str, top: str) -> Netlist:
    """The frontend pipeline: HDL source -> packed netlist
    (parse -> synthesise -> optimise -> lower -> optimise -> map -> pack)."""
    ast = parse_hdl(hdl)
    library = HDLElaborator(ast).get_library()
    netlist = Synthesiser(library).synthesise(top)
    netlist = Optimiser().optimise(netlist)
    lowered = LoweringPass().run(netlist)
    # second optimise: folds the constant-fed gates lowering introduces
    # (zero-extension, ripple-carry seeds) before they consume LUT capacity
    lowered = Optimiser().optimise(lowered)
    mapped = GreedyMapper(k_max=3).run(lowered)
    return GreedyPacker(max_clbs=64).run(mapped)


def build(
    hdl: str,
    top: str,
    *,
    fabric: Fabric | None = None,
    seed: int = 0,
    pins: PinAssignments | PinConstraints | dict[str, str] | None = None,
    placer: AnnealingPlacer | None = None,
    router: PathFinderRouter | None = None,
    clock: ClockSource | str | None = None,
) -> tuple[DeviceConfig, Placement, RoutingReport]:
    """One-call compile: HDL source -> placed & routed DeviceConfig.

    Chains the frontend (`compile_hdl_to_packed`) and the backend
    (`place_and_route`). `pins` optionally pins top-level pads to chosen IO
    banks; anything left unconstrained is placed freely. `placer`/`router`
    swap in tuned instances (e.g. a router with a higher iteration budget),
    and `clock` chooses a pad or the on-chip oscillator as the clock source."""
    packed = compile_hdl_to_packed(hdl, top)
    return place_and_route(
        packed,
        fabric,
        seed=seed,
        placer=placer,
        router=router,
        pins=pins,
        clock=clock,
    )
