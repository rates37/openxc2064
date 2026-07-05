"""Design Flow Pipeline: HDL -> packed netlist -> placed & routed DeviceConfig."""

from __future__ import annotations

from openxc2064.device.config import DeviceConfig
from openxc2064.device.fabric import Fabric
from openxc2064.hdl import parse_hdl
from openxc2064.mapping.mapper import GreedyMapper
from openxc2064.mapping.packer import GreedyPacker
from openxc2064.synthesis import HDLElaborator, LoweringPass, Optimiser, Synthesiser
from openxc2064.synthesis.rtl_nodes import Netlist

from .design_view import DesignView
from .placement import AnnealingPlacer, Placement
from .router import PathFinderRouter, RoutingReport


def compile_hdl_to_packed(hdl: str, top: str) -> Netlist:
    """The frontend pipeline (parse -> ... -> packed netlist)"""
    ast = parse_hdl(hdl)
    library = HDLElaborator(ast).get_library()
    netlist = Synthesiser(library).synthesise(top)
    netlist = Optimiser().optimise(netlist)
    lowered = LoweringPass().run(netlist)
    # second optimise: folds the constant-fed gates lowering introduces
    lowered = Optimiser().optimise(lowered)
    mapped = GreedyMapper(k_max=3).run(lowered)
    return GreedyPacker(max_clbs=64).run(mapped)


def place_and_route(
    packed: Netlist,
    fabric: Fabric | None = None,
    *,
    seed: int = 0,
    placer: AnnealingPlacer | None = None,
    router: PathFinderRouter | None = None,
) -> tuple[DeviceConfig, Placement, RoutingReport]:
    """The backend pipeline (packed netlist -> placed & routed DeviceConfig)"""
    fabric = fabric or Fabric.load("xc2064_8x8")
    design = DesignView(packed)
    placement = (placer or AnnealingPlacer()).run(design, fabric, seed=seed)
    config, report = (router or PathFinderRouter()).run(design, placement, fabric)
    return config, placement, report
