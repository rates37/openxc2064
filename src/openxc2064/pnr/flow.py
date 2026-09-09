"""Backend flow pipeline: packed netlist -> placed & routed DeviceConfig.

The frontend (HDL -> packed netlist) and the one-call `build` that chains
frontend + backend live in `openxc2064.toolchain`, so importing this backend
subpackage does not pull in the lark grammar.
"""

from __future__ import annotations

from openxc2064.device.config import DeviceConfig
from openxc2064.device.fabric import Fabric
from openxc2064.synthesis.rtl_nodes import Netlist

from .clocking import ClockSource, ClockSourceError, oscillator_clock_iob
from .constraints import PinConstraints
from .design_view import DesignView
from .pin_assignments import PinAssignmentError, PinAssignments
from .placement import AnnealingPlacer, Placement
from .router import PathFinderRouter, RoutingReport


def place_and_route(
    packed: Netlist,
    fabric: Fabric | None = None,
    *,
    seed: int = 0,
    placer: AnnealingPlacer | None = None,
    router: PathFinderRouter | None = None,
    pins: PinAssignments | PinConstraints | dict[str, str] | None = None,
    clock: ClockSource | str | None = None,
) -> tuple[DeviceConfig, Placement, RoutingReport]:
    """The backend pipeline (packed netlist -> placed & routed DeviceConfig).

    `pins` optionally pins top-level pads to chosen IO banks (a `PinAssignments`
    file), a `PinConstraints`, or a plain {pad: bank} dict; anything left
    unconstrained is placed freely. `clock` chooses where the clock comes
    from: a pad (the default) or the on-chip oscillator. A pin file that
    assigns a signal to OSC sets that itself."""
    fabric = fabric or Fabric.load("xc2064_8x8")
    design = DesignView(packed)

    if isinstance(pins, PinAssignments):
        clock = _clock_from_pin_file(pins, clock)
        if problems := pins.direction_problems(design):
            raise PinAssignmentError("; ".join(problems))
        pins = pins.to_constraints(fabric)

    # bind before placement, so an oscillator clock never claims a pad bank
    oscillator_iobs = frozenset()
    if ClockSource(clock or ClockSource.PAD) is ClockSource.OSCILLATOR:
        oscillator_iobs = frozenset({oscillator_clock_iob(design)})

    placement = (placer or AnnealingPlacer()).run(
        design, fabric, seed=seed, pins=pins, oscillator_iobs=oscillator_iobs
    )
    config, report = (router or PathFinderRouter()).run(design, placement, fabric)
    return config, placement, report


def _clock_from_pin_file(
    plan: PinAssignments, clock: ClockSource | str | None
) -> ClockSource | str:
    from_plan = plan.clock_source()
    if from_plan is None:
        return clock or ClockSource.PAD
    if clock is not None and ClockSource(clock) is not from_plan:
        signals = ", ".join(plan.oscillator_signals())
        raise ClockSourceError(
            f"{plan.source} assigns {signals} to OSC, but clock={ClockSource(clock).value!r} "
            "was passed; drop one of the two"
        )
    return from_plan
