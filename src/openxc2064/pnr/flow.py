"""Backend flow pipeline: packed netlist -> placed & routed DeviceConfig.

The frontend (HDL -> packed netlist) and the one-call `build` that chains
frontend + backend live in `openxc2064.toolchain`, so importing this backend
subpackage does not pull in the lark grammar.
"""

from __future__ import annotations

from openxc2064.device.config import DeviceConfig
from openxc2064.device.fabric import Fabric
from openxc2064.synthesis.rtl_nodes import Netlist

from .constraints import PinConstraints
from .design_view import DesignView
from .placement import AnnealingPlacer, Placement
from .router import PathFinderRouter, RoutingReport


def place_and_route(
    packed: Netlist,
    fabric: Fabric | None = None,
    *,
    seed: int = 0,
    placer: AnnealingPlacer | None = None,
    router: PathFinderRouter | None = None,
    pins: PinConstraints | dict[str, str] | None = None,
) -> tuple[DeviceConfig, Placement, RoutingReport]:
    """The backend pipeline (packed netlist -> placed & routed DeviceConfig).

    `pins` optionally pins top-level pads to chosen IO banks; anything left
    unconstrained is placed freely."""
    fabric = fabric or Fabric.load("xc2064_8x8")
    design = DesignView(packed)
    placement = (placer or AnnealingPlacer()).run(
        design, fabric, seed=seed, pins=pins
    )
    config, report = (router or PathFinderRouter()).run(design, placement, fabric)
    return config, placement, report
