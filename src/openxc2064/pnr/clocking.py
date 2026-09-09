"""Clock sourcing: run a routed design's clock off the on-chip oscillator
instead of an input pad.

    config, placement, report = build(hdl, "counter", clock=ClockSource.OSCILLATOR)

The pad the router used is freed as a side effect; it stays configured as an
unused input. Note the design still spends a pad during placement, so this
does not buy back an IO slot on a pad-tight design.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from openxc2064.device.config import DeviceConfig
from openxc2064.device.fabric import OSCILLATOR_NET, Fabric

from .design_view import DesignView
from .placement import Placement


class ClockSourceError(Exception):
    """The design's clock cannot be sourced the way it was asked for."""


class ClockSource(str, Enum):
    """Where a design's clock comes from."""

    PAD = "pad"  # default: an input pad drives the clock tree
    OSCILLATOR = "oscillator"  # the on-chip RC oscillator drives it


@dataclass(frozen=True)
class OscillatorHookup:
    """What reroute_clock_to_oscillator changed."""

    freed_bank: str  # the pad bank the clock no longer uses
    hops: tuple[tuple[str, str], ...]  # oscillator -> clock trunk in flow order


def reroute_clock_to_oscillator(
    config: DeviceConfig,
    fabric: Fabric,
    design: DesignView,
    placement: Placement,
) -> OscillatorHookup:
    """Re-source a routed config's clock from the on-chip oscillator.

    Raises ClockSourceError if the design has no clock, if its clock is not
    driven by an input pad, or if the fabric cannot route the oscillator to
    the clock trunk.
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

    bank = placement.iob_sites[node_id]
    pad_net = fabric.io_banks[bank].net("net_I")

    # the hops leaving the clock pad: the roots of the routed clock tree
    roots = [(src, dst) for src, dst in config.drivers if src == pad_net]
    if not roots:
        raise ClockSourceError(
            f"clock pad '{bank}' drives no routed hop; the design does not look "
            "placed and routed yet"
        )

    # cut the pad out, physical resource included
    for src, dst in roots:
        ref = fabric.edge_ref(src, dst)
        if ref is None:
            raise ClockSourceError(
                f"routed hop {src} -> {dst} has no matching fabric edge"
            )
        config.disable_edge(src, dst, ref)

    # re-drive each orphaned trunk from the oscillator over real fabric edges,
    # keeping clear of every wire another net already holds
    hops: list[tuple[str, str]] = []
    for trunk in sorted({dst for _, dst in roots}):
        if any(dst == trunk for _, dst in config.drivers):
            continue  # an earlier oscillator route already reaches this trunk
        in_use = {net for edge in config.drivers for net in edge}
        path = fabric.find_path(OSCILLATOR_NET, trunk, blocked=in_use - {trunk})
        if path is None:
            raise ClockSourceError(
                f"no free fabric route from {OSCILLATOR_NET} to clock trunk '{trunk}'"
            )
        config.enable_path(path)
        hops.extend((src, dst) for src, dst, _ in path)

    return OscillatorHookup(freed_bank=bank, hops=tuple(hops))
