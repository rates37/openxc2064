"""Shared reading of a packed netlist for placement and routing (plan B.0).

Extracts, once, the terminals of every routable logical net:

- driver: `(clb_node_id, 'X'|'Y')` resolved from the packed CLB's outputs
  order (outputs[0] is X, outputs[1] is Y, the same order the packer chose
  sel_x/sel_y in), or `(iob_node_id, 'I')` for input pads;
- sinks: `(clb_node_id, 'A'|'B'|'C'|'D')` from the `clb.inputs` pin
  positions, `(clb_node_id, 'K')` for the clock pin, `(iob_node_id, 'O')`
  for output pads.

Sinks are (node, pin) pairs not fabric net IDs

Construction validates loudly: a constant driving a routed net, a sink with
no driver, multiple drivers, or more than one clock domain (MVP restriction)
are all DesignError.
"""

from __future__ import annotations

from dataclasses import dataclass

from openxc2064.mapping.xc2064_primitives import CLB, IOB
from openxc2064.synthesis.rtl_nodes import Constant, Netlist

PIN_LETTERS = "ABCD"

Terminal = tuple[str, str]  # (node id, port)


class DesignError(Exception):
    """The packed netlist cannot be placed/routed as-is."""


@dataclass(frozen=True)
class RoutedNet:
    name: str
    driver: Terminal
    sinks: tuple[Terminal, ...]
    is_clock: bool  # feeds at least one K pin


class DesignView:
    def __init__(self, netlist: Netlist):
        self.netlist = netlist
        self.clbs: dict[str, CLB] = {}
        self.iobs: dict[str, IOB] = {}
        self.warnings: list[str] = []

        drivers: dict[str, list[Terminal]] = {}
        sinks: dict[str, list[Terminal]] = {}
        const_driven: set[str] = set()

        for node in netlist.nodes:
            if isinstance(node, CLB):
                self.clbs[node.id] = node
                for position, net in enumerate(node.outputs):
                    if net is not None:
                        drivers.setdefault(net.name, []).append((node.id, "XY"[position]))
                for position, net in enumerate(node.inputs[:4]):
                    if net is not None:
                        sinks.setdefault(net.name, []).append(
                            (node.id, PIN_LETTERS[position])
                        )
                if len(node.inputs) > 4 and node.inputs[4] is not None:
                    sinks.setdefault(node.inputs[4].name, []).append((node.id, "K"))
            elif isinstance(node, IOB):
                self.iobs[node.id] = node
                if node.is_input and len(node.outputs) > 1 and node.outputs[1] is not None:
                    drivers.setdefault(node.outputs[1].name, []).append((node.id, "I"))
                if node.is_output and len(node.inputs) > 1 and node.inputs[1] is not None:
                    sinks.setdefault(node.inputs[1].name, []).append((node.id, "O"))
            elif isinstance(node, Constant):
                if node.outputs:
                    const_driven.add(node.outputs[0].name)

        nets: list[RoutedNet] = []
        for name in sorted(sinks):
            net_sinks = tuple(sorted(sinks[name]))
            if name in const_driven:
                raise DesignError(
                    f"net '{name}' is driven by a constant but has routed sinks "
                    f"{list(net_sinks)}. the fabric has no VCC/GND taps: constants "
                    "must be folded away before packing"
                )
            net_drivers = drivers.get(name, [])
            if not net_drivers:
                raise DesignError(f"net '{name}' has sinks {list(net_sinks)} but no driver")
            if len(net_drivers) > 1:
                raise DesignError(f"net '{name}' has multiple drivers: {net_drivers}")
            is_clock = any(port == "K" for _, port in net_sinks)
            nets.append(RoutedNet(name, net_drivers[0], net_sinks, is_clock))

        for name in sorted(set(drivers) - set(sinks)):
            self.warnings.append(f"net '{name}' has a driver but no sinks; not routed")

        clocks = [n for n in nets if n.is_clock]
        if len(clocks) > 1:
            raise DesignError(
                "multiple clock nets are not supported yet: "
                f"{[n.name for n in clocks]}"
            )

        self.nets: list[RoutedNet] = nets
        self.clock_net: RoutedNet | None = clocks[0] if clocks else None
