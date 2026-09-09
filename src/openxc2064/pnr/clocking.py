"""Clock sourcing: where a design's clock comes from.

By default the clock arrives on an input pad. `ClockSource.OSCILLATOR` binds
the clock port to the on-chip oscillator instead: the placer gives that IOB
the OSCILLATOR_SITE pseudo-site rather than a pad bank, the router sources
the clock net at OSCILLATOR_NET.

Because the binding happens before placement, an oscillator clock costs no
pad. A design whose ports would otherwise not fit gets its clock pin back.

    config, placement, report = build(hdl, "counter", clock=ClockSource.OSCILLATOR)
"""

from __future__ import annotations

from enum import Enum

from .design_view import DesignView


class ClockSourceError(Exception):
    """The design's clock cannot be sourced the way it was asked for."""


class ClockSource(str, Enum):
    """Where a design's clock comes from."""

    PAD = "pad"  # default: an input pad drives the clock tree
    OSCILLATOR = "oscillator"  # the on-chip RC oscillator drives it


def oscillator_clock_iob(design: DesignView) -> str:
    """The IOB node id to bind to the oscillator: the input pad driving the
    design's clock net.

    Raises ClockSourceError if the design has no clock net, or if its clock
    is generated internally (a gated clock, say) and so has no pad to replace.
    """
    clock_net = design.clock_net
    if clock_net is None:
        raise ClockSourceError(
            "design has no clock net (nothing drives a K pin), so there is "
            "nothing to source from the oscillator"
        )

    node_id, port = clock_net.driver
    if port != "I" or node_id not in design.iobs:
        raise ClockSourceError(
            f"clock net '{clock_net.name}' is driven by {node_id}.{port}, not an "
            "input pad; only a pad-sourced clock can be moved onto the oscillator"
        )
    return node_id
