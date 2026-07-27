"""Simulated-annealing placement.

Cost = sum over data nets of HPWL minus w_direct x direct-connect hits.
The direct-connect table is derived from the fabric (CLB-output-pin ->
CLB-input-pin pips), and a hit only counts when the sink's actual packed pin
matches the pip's destination pin. Clock nets are excluded.

Uses seeded random.Random plus sorted iteration everywhere for determinism.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import dataclass, field

from openxc2064.device.fabric import Fabric

from .constraints import PinConstraints, coerce_pins
from .design_view import DesignView, RoutedNet


class PlacementError(Exception):
    pass


# Single source of truth for the direct-connect reward. Both the annealer and
# placement_cost default to this so a placement is never scored against a
# different objective than the one it was optimised for.
DEFAULT_W_DIRECT = 2.0


def hpwl(points: list[tuple[int, int]]) -> int:
    """Half-perimeter of the bounding box of grid points."""
    rows = [r for r, _ in points]
    cols = [c for _, c in points]
    return (max(rows) - min(rows)) + (max(cols) - min(cols))


def direct_connect_table(fabric: Fabric) -> set[tuple[int, int, str, str]]:
    """(d_row, d_col, out_pin, in_pin) offsets served by a direct pip
    between two CLBs (e.g. X drives the southern neighbour's A pin)."""
    out_pins: dict[str, tuple[int, int, str]] = {}
    in_pins: dict[str, tuple[int, int, str]] = {}
    for cid, site in fabric.clbs.items():
        for pin in ("X", "Y"):
            out_pins[f"{cid}.net_{pin}"] = (site.row, site.col, pin)
        for pin in "ABCD":
            in_pins[f"{cid}.net_{pin}"] = (site.row, site.col, pin)

    table: set[tuple[int, int, str, str]] = set()
    for pip in fabric.pips:
        src = out_pins.get(pip.source)
        dst = in_pins.get(pip.destination)
        if src is not None and dst is not None:
            table.add((dst[0] - src[0], dst[1] - src[1], src[2], dst[2]))
    return table


def _site_coords(fabric: Fabric) -> dict[str, tuple[int, int]]:
    coords: dict[str, tuple[int, int]] = {}
    for cid, site in fabric.clbs.items():
        coords[cid] = (site.row, site.col)
    for bid, bank in fabric.io_banks.items():
        owner = fabric.clbs[bank.owner_cell]
        coords[bid] = (owner.row, owner.col)
    return coords


def _net_cost(
    net: RoutedNet,
    node_coords,
    table: set[tuple[int, int, str, str]],
    w_direct: float,
) -> float:
    points = [node_coords(net.driver[0])]
    points.extend(node_coords(node_id) for node_id, _ in net.sinks)
    cost = float(hpwl(points))

    if net.driver[1] in ("X", "Y"):
        driver_row, driver_col = points[0]
        for (node_id, port), (row, col) in zip(net.sinks, points[1:]):
            if port in "ABCD" and (
                row - driver_row,
                col - driver_col,
                net.driver[1],
                port,
            ) in table:
                cost -= w_direct
    return cost


def placement_cost(
    design: DesignView,
    fabric: Fabric,
    placement: "Placement",
    w_direct: float = DEFAULT_W_DIRECT,
) -> float:
    """Full (non-incremental) cost — the correctness reference."""
    coords = _site_coords(fabric)
    sites = {**placement.clb_sites, **placement.iob_sites}
    table = direct_connect_table(fabric)
    lookup = lambda node_id: coords[sites[node_id]]  # noqa: E731
    return sum(
        _net_cost(net, lookup, table, w_direct)
        for net in design.nets
        if not net.is_clock
    )


@dataclass
class Placement:
    clb_sites: dict[str, str] = field(default_factory=dict)  # node id -> cell id
    iob_sites: dict[str, str] = field(default_factory=dict)  # node id -> bank id

    def site_of(self, node_id: str) -> str:
        return self.clb_sites.get(node_id) or self.iob_sites[node_id]

    def validate(self, design: DesignView, fabric: Fabric) -> list[str]:
        issues: list[str] = []
        for node_id in design.clbs:
            cell = self.clb_sites.get(node_id)
            if cell is None:
                issues.append(f"CLB node '{node_id}' is not placed")
            elif cell not in fabric.clbs:
                issues.append(f"CLB node '{node_id}' placed on unknown cell '{cell}'")
        for node_id in design.iobs:
            bank = self.iob_sites.get(node_id)
            if bank is None:
                issues.append(f"IOB node '{node_id}' is not placed")
            elif bank not in fabric.io_banks:
                issues.append(f"IOB node '{node_id}' placed on unknown bank '{bank}'")
            elif not fabric.io_banks[bank].has_pad:
                issues.append(f"IOB node '{node_id}' placed on padless bank '{bank}'")
        if len(set(self.clb_sites.values())) != len(self.clb_sites):
            issues.append("two CLB nodes share a cell")
        if len(set(self.iob_sites.values())) != len(self.iob_sites):
            issues.append("two IOB nodes share a bank")
        return issues

    def to_json(self) -> str:
        return json.dumps(
            {"clb_sites": self.clb_sites, "iob_sites": self.iob_sites}, indent=2
        )

    @classmethod
    def from_json(cls, text: str) -> "Placement":
        data = json.loads(text)
        return cls(clb_sites=data["clb_sites"], iob_sites=data["iob_sites"])


class AnnealingPlacer:
    def __init__(
        self,
        w_direct: float = DEFAULT_W_DIRECT,
        cooling: float = 0.95,
        moves_per_temperature: int | None = None,
    ):
        self.w_direct = w_direct
        self.cooling = cooling
        self.moves_per_temperature = moves_per_temperature

    def cost(
        self, design: DesignView, fabric: Fabric, placement: "Placement"
    ) -> float:
        """Full placement cost under this placer's own w_direct — the objective
        it optimises. Use this instead of placement_cost's default when
        comparing placements produced by a tuned placer."""
        return placement_cost(design, fabric, placement, self.w_direct)

    def run(
        self,
        design: DesignView,
        fabric: Fabric,
        seed: int = 0,
        pins: "PinConstraints | dict[str, str] | None" = None,
    ) -> Placement:
        """Place every CLB and IOB. `pins` optionally nails chosen pads to
        chosen banks; those IOBs are pre-placed and never moved, while
        everything else anneals as usual."""
        rng = random.Random(seed)

        cells = sorted(fabric.clbs)
        banks = sorted(
            (bid for bid, bank in fabric.io_banks.items() if bank.has_pad),
            key=lambda bid: fabric.io_banks[bid].pad_index,
        )
        clb_nodes = sorted(design.clbs)
        iob_nodes = sorted(design.iobs)
        if len(clb_nodes) > len(cells):
            raise PlacementError(f"{len(clb_nodes)} CLBs > {len(cells)} cells")
        if len(iob_nodes) > len(banks):
            raise PlacementError(f"{len(iob_nodes)} IOBs > {len(banks)} pad banks")

        # pinned IOBs are placed up front and withheld from the move set, so
        # neither they nor their banks can be disturbed by annealing
        pinned = coerce_pins(pins).resolve(design, fabric)
        free_iob_nodes = [node for node in iob_nodes if node not in pinned]
        taken_banks = set(pinned.values())
        free_banks = [bank for bank in banks if bank not in taken_banks]
        if len(free_iob_nodes) > len(free_banks):
            raise PlacementError(
                f"{len(free_iob_nodes)} unpinned IOBs > {len(free_banks)} free "
                f"pad banks ({len(pinned)} banks are pinned)"
            )

        # state: node -> site and site -> node (cell/bank namespaces are disjoint)
        node_site: dict[str, str] = {}
        occupant: dict[str, str] = {}
        for node, site in zip(clb_nodes, rng.sample(cells, len(clb_nodes))):
            node_site[node] = site
            occupant[site] = node
        for node in sorted(pinned):
            node_site[node] = pinned[node]
            occupant[pinned[node]] = node
        for node, site in zip(
            free_iob_nodes, rng.sample(free_banks, len(free_iob_nodes))
        ):
            node_site[node] = site
            occupant[site] = node

        site_coords = _site_coords(fabric)
        table = direct_connect_table(fabric)
        w_direct = self.w_direct

        def node_coords(node_id: str) -> tuple[int, int]:
            return site_coords[node_site[node_id]]

        data_nets = [net for net in design.nets if not net.is_clock]
        nets_of: dict[str, list[int]] = {}
        for index, net in enumerate(data_nets):
            for node_id in {net.driver[0], *(nid for nid, _ in net.sinks)}:
                nets_of.setdefault(node_id, []).append(index)

        net_costs = [
            _net_cost(net, node_coords, table, w_direct) for net in data_nets
        ]
        total = sum(net_costs)

        def propose():
            use_clb = clb_nodes and (not free_iob_nodes or rng.random() < 0.7)
            if use_clb:
                node = rng.choice(clb_nodes)
                target = rng.choice(cells)
            else:
                node = rng.choice(free_iob_nodes)
                target = rng.choice(free_banks)
            if node_site[node] == target:
                return None
            return node, target

        def apply(node: str, target: str):
            old = node_site[node]
            other = occupant.get(target)
            node_site[node] = target
            occupant[target] = node
            if other is not None:
                node_site[other] = old
                occupant[old] = other
            else:
                del occupant[old]
            return old, other

        def revert(node: str, target: str, old: str, other: str | None) -> None:
            node_site[node] = old
            occupant[old] = node
            if other is not None:
                node_site[other] = target
                occupant[target] = other
            else:
                del occupant[target]

        def affected(node: str, other: str | None) -> list[int]:
            indices = set(nets_of.get(node, ()))
            if other is not None:
                indices.update(nets_of.get(other, ()))
            return sorted(indices)

        def move_delta(node: str, other: str | None):
            indices = affected(node, other)
            new_costs = {
                i: _net_cost(data_nets[i], node_coords, table, w_direct)
                for i in indices
            }
            delta = sum(new_costs[i] - net_costs[i] for i in indices)
            return delta, new_costs

        movable = len(clb_nodes) + len(free_iob_nodes)
        if movable == 0 or not data_nets:
            return Placement(
                clb_sites={n: node_site[n] for n in clb_nodes},
                iob_sites={n: node_site[n] for n in iob_nodes},
            )

        # initial temperature from the spread of random move deltas
        samples: list[float] = []
        for _ in range(60):
            move = propose()
            if move is None:
                continue
            node, target = move
            old, other = apply(node, target)
            delta, _ = move_delta(node, other)
            samples.append(abs(delta))
            revert(node, target, old, other)
        spread = statistics.pstdev(samples) if len(samples) > 1 else 1.0
        temperature = max(1.0, 20.0 * spread)
        t_floor = temperature * 1e-3

        inner = self.moves_per_temperature or max(100, 20 * movable)
        while temperature > t_floor:
            accepted = 0
            trials = 0
            for _ in range(inner):
                move = propose()
                if move is None:
                    continue
                trials += 1
                node, target = move
                old, other = apply(node, target)
                delta, new_costs = move_delta(node, other)
                take = delta <= 0 or (
                    delta / temperature < 50
                    and rng.random() < math.exp(-delta / temperature)
                )
                if take:
                    for i, cost in new_costs.items():
                        net_costs[i] = cost
                    total += delta
                    accepted += 1
                else:
                    revert(node, target, old, other)
            temperature *= self.cooling
            if trials and accepted / trials < 0.02:
                break

        # incremental bookkeeping must agree with the reference cost
        reference = sum(
            _net_cost(net, node_coords, table, w_direct) for net in data_nets
        )
        assert abs(total - reference) < 1e-6, "incremental cost drifted"

        return Placement(
            clb_sites={n: node_site[n] for n in clb_nodes},
            iob_sites={n: node_site[n] for n in iob_nodes},
        )
