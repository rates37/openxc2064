"""Negotiated-congestion router over the fabric graph

Each logical net becomes a driver->sinks tree of fabric hops. Trees grow by
repeated Dijkstra from the whole current tree to the nearest unreached sink,
so trunks are shared within a net for free. Between nets, fabric nets are
exclusive: iteration 1 tolerates overuse, then nets touching overused nodes
are ripped up and re-routed under growing present/history congestion costs
(PathFinder) until nothing is shared or the iteration cap is hit.

Hops are recorded in traversal direction. DeviceConfig's drivers list is
the only carrier of true signal flow (a bidirectional pip traversed in
reverse keeps its direction).

The dedicated clock/oscillator/IO-clock distribution nets are reserved:
data nets may never enter them; the clock net may use the clock trunk.
"""

from __future__ import annotations

import heapq
from collections import defaultdict
from dataclasses import dataclass, field

from openxc2064.device.config import DeviceConfig
from openxc2064.device.fabric import Fabric

from .design_view import DesignView, RoutedNet
from .placement import Placement

RESERVED_PREFIXES = ("global.net_clk", "global.net_osc", "global_io.") 
CLOCK_ALLOWED = frozenset({"global.net_clk"}) 

Hop = tuple[str, str, tuple]  # (from_net, to_net, edge_ref)


class RoutingError(Exception):
    pass


@dataclass
class RoutingReport:
    net_hops: dict[str, list[Hop]] = field(default_factory=dict)
    total_hops: int = 0
    iterations: int = 0
    longline_uses: int = 0
    direct_hits: int = 0


def _terminal_fabric_net(terminal: tuple[str, str], placement: Placement) -> str:
    node_id, port = terminal
    if port in ("X", "Y"):
        return f"{placement.clb_sites[node_id]}.net_{port}"
    if port in "ABCD" or port == "K":
        return f"{placement.clb_sites[node_id]}.net_{port}"
    if port == "I":
        return f"{placement.iob_sites[node_id]}.net_I"
    if port == "O":
        return f"{placement.iob_sites[node_id]}.net_O"
    raise ValueError(f"unknown terminal port '{port}'")


class PathFinderRouter:
    def __init__(
        self,
        max_iterations: int = 30,
        longline_base: float = 2.0,
        present_factor: float = 0.5,
        present_growth: float = 1.6,
        history_factor: float = 1.0,
        extra_reserved: frozenset[str] | set[str] = frozenset(),
    ):
        self.max_iterations = max_iterations
        self.longline_base = longline_base
        self.present_factor = present_factor
        self.present_growth = present_growth
        self.history_factor = history_factor
        self.extra_reserved = frozenset(extra_reserved)

    def run(
        self, design: DesignView, placement: Placement, fabric: Fabric
    ) -> tuple[DeviceConfig, RoutingReport]:
        reserved = {
            net for net in fabric.bus_nets if net.startswith(RESERVED_PREFIXES)
        } | self.extra_reserved

        # resolve terminals to fabric nets; route clocks first, then data by
        # descending fanout (deterministic tie-break on name)
        resolved: list[tuple[RoutedNet, str, dict[str, tuple[str, str]]]] = []
        for net in design.nets:
            source = _terminal_fabric_net(net.driver, placement)
            sinks = {
                _terminal_fabric_net(terminal, placement): terminal
                for terminal in net.sinks
            }
            sinks.pop(source, None)  # degenerate self-loop sinks
            resolved.append((net, source, sinks))
        order = sorted(
            resolved, key=lambda entry: (not entry[0].is_clock, -len(entry[2]), entry[0].name)
        )

        usage: dict[str, set[str]] = defaultdict(set)
        history: dict[str, float] = defaultdict(float)
        net_hops: dict[str, list[Hop]] = {}
        net_nodes: dict[str, set[str]] = {}

        present_factor = self.present_factor
        to_route = list(order)
        iterations = 0
        for iteration in range(1, self.max_iterations + 1):
            iterations = iteration
            for entry in to_route:
                self._route_net(
                    entry, fabric, reserved, usage, history, present_factor,
                    net_hops, net_nodes, placement,
                )

            overused = {
                node: users for node, users in usage.items() if len(users) > 1
            }
            if not overused:
                break
            if iteration == self.max_iterations:
                detail = "; ".join(
                    f"{node} wanted by {sorted(users)}"
                    for node, users in sorted(overused.items())
                )
                raise RoutingError(
                    f"congestion unresolved after {iteration} iterations: {detail}"
                )

            for node, users in overused.items():
                history[node] += len(users) - 1
            ripped = set()
            for users in overused.values():
                ripped.update(users)
            to_route = [entry for entry in order if entry[0].name in ripped]
            for entry in to_route:
                name = entry[0].name
                for node in net_nodes.pop(name, ()):
                    usage[node].discard(name)
                net_hops.pop(name, None)
            present_factor *= self.present_growth

        # assemble the device configuration:
        config = DeviceConfig(fabric)
        for node_id, cell in sorted(placement.clb_sites.items()):
            config.configure_clb(cell, design.clbs[node_id])
        for node_id, bank in sorted(placement.iob_sites.items()):
            iob = design.iobs[node_id]
            config.configure_iob(bank, "output" if iob.is_output else "input")

        clb_out_pins = {
            f"{cid}.net_{pin}" for cid in fabric.clbs for pin in ("X", "Y")
        }
        clb_in_pins = {
            f"{cid}.net_{pin}" for cid in fabric.clbs for pin in "ABCD"
        }

        report = RoutingReport(iterations=iterations)
        for name in sorted(net_hops):
            hops = net_hops[name]
            config.enable_path(hops)
            report.net_hops[name] = list(hops)
            report.total_hops += len(hops)
            for src, dst, _ in hops:
                if dst.startswith("global_") or src.startswith("global_"):
                    report.longline_uses += 1
                if src in clb_out_pins and dst in clb_in_pins:
                    report.direct_hits += 1
        return config, report

    #! per-net tree routing:
    def _route_net(
        self,
        entry,
        fabric: Fabric,
        reserved: set[str],
        usage: dict[str, set[str]],
        history: dict[str, float],
        present_factor: float,
        net_hops: dict[str, list[Hop]],
        net_nodes: dict[str, set[str]],
        placement: Placement,
    ) -> None:
        net, source, sinks = entry
        name = net.name
        blocked = (reserved - CLOCK_ALLOWED) if net.is_clock else reserved

        tree = {source}
        hops: list[Hop] = []
        unreached = set(sinks)
        usage[source].add(name)

        while unreached:
            found, parents = self._search(
                fabric, tree, unreached, blocked, usage, history,
                present_factor, name,
            )
            if found is None:
                missing = {sinks[fnet] for fnet in sorted(unreached)}
                raise RoutingError(
                    f"net '{name}': no route from its tree to sink(s) "
                    f"{sorted(unreached)} (terminals {sorted(missing)}); "
                    f"{len(tree)} fabric nets already in the tree"
                )
            path: list[Hop] = []
            node = found
            while node not in tree:
                prev, ref = parents[node]
                path.append((prev, node, ref))
                node = prev
            path.reverse()
            for src, dst, ref in path:
                hops.append((src, dst, ref))
                tree.add(dst)
                usage[dst].add(name)
            unreached.discard(found)

        net_hops[name] = hops
        net_nodes[name] = set(tree)

    def _search(
        self,
        fabric: Fabric,
        tree: set[str],
        targets: set[str],
        blocked: set[str],
        usage: dict[str, set[str]],
        history: dict[str, float],
        present_factor: float,
        name: str,
    ):
        distances: dict[str, float] = {}
        parents: dict[str, tuple[str, tuple]] = {}
        heap: list[tuple[float, str]] = []
        for node in sorted(tree):
            distances[node] = 0.0
            heapq.heappush(heap, (0.0, node))

        while heap:
            dist, current = heapq.heappop(heap)
            if dist > distances.get(current, float("inf")):
                continue
            if current in targets:
                return current, parents
            for nxt, ref in fabric.neighbors(current):
                if nxt in blocked or nxt in tree:
                    continue
                base = self.longline_base if nxt.startswith("global_") else 1.0
                others = len(usage.get(nxt, ()) - {name}) if nxt in usage else 0
                cost = (
                    dist
                    + base * (1.0 + present_factor * others)
                    + self.history_factor * history.get(nxt, 0.0)
                )
                if cost < distances.get(nxt, float("inf")) - 1e-12:
                    distances[nxt] = cost
                    parents[nxt] = (current, ref)
                    heapq.heappush(heap, (cost, nxt))
        return None, parents
