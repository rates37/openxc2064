"""Python model of the XC2064 routing fabric.

Built from the JSON exported by the web simulator's config files
(`simulator/scripts/export_configs.ts` writes `data/xc2064_{8x8,3x3}.json`)
Those files are the original source of truth
Generate them with:
    `npm run export-configs` (from inside the `simulator/` directory) after any config change.

This module ports two pieces of `simulator/src/InitialiseSimulation.ts`:

- `decodeRelativeNetName`: turns config-relative net references
  (e.g., `net_A`, `NW_M0.net_2`, `global_HU.net_0`, `T_IO0.net_O`) into
  canonical global net IDs (`BB.net_A`, `AA_M0.net_2`, `global_H1.net_0`,
  `BB_IO0.net_O`).
- the switch-matrix aliasing second pass: each matrix owns its top/right wire
  segments (pins 0-3); pins 4-7 alias the neighbouring matrices' segments

On top of the sites it builds a routing-resource graph: nodes are canonical
net IDs, edges are PIPs (directed) and legal switch-matrix connections
(bidirectional, one per `POSSIBLE_MATRIX_CONNECTIONS` pair).
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"  # assumes the jsons have already been generated

# Fabric policy: the dedicated clock/oscillator/IO-clock distribution nets are
# reachable from IOB inputs but must never carry general data signals. A clock
# net may ride the clock trunk (CLOCK_ALLOWED); everything else is off-limits
# to every net.
RESERVED_PREFIXES = ("global.net_clk", "global.net_osc", "global_io.")
CLOCK_ALLOWED = frozenset({"global.net_clk"})

# The on-chip oscillator's output net. It is an external source like a pad
# (the RC oscillator drives it; the web simulator's Oscillator control toggles
# it directly), not something the router may reach on its own.
OSCILLATOR_NET = "global.net_osc_in"

# The oscillator's distribution nets. Reserved like the clock trunk: only a
# net actually sourced at the oscillator may enter them (pnr.ClockSource).
OSCILLATOR_ALLOWED = frozenset({OSCILLATOR_NET, "global.net_osc"})

# Canvas layout constants, mirroring simulator/src/configs/constants.ts
CELL_WIDTH = 200
CELL_HEIGHT = 320
CELL_MARGIN_X = 320
CELL_MARGIN_Y = 240
CELL_OFFSET_X = 0
CELL_OFFSET_Y = 0

# Legal pin-to-pin connections inside every switch matrix
# (mirrors SwitchMatrix.possibleConnections in simulator/src/models/SwitchMatrix.ts).
# Pin layout: 0,1 top; 2,3 right; 4,5 bottom; 6,7 left.
POSSIBLE_MATRIX_CONNECTIONS = [
    [0, 0, 1, 0, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 0, 1],
    [1, 1, 0, 0, 1, 0, 1, 1],
    [0, 1, 0, 0, 1, 1, 1, 1],
    [1, 1, 1, 1, 0, 0, 1, 0],
    [1, 1, 0, 1, 0, 0, 1, 1],
    [1, 0, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 1, 0, 1, 0, 0],
]

# CLB pin nets, as local net IDs within a cell
CLB_INPUT_PINS = ("net_A", "net_B", "net_C", "net_D", "net_K")
CLB_OUTPUT_PINS = ("net_X", "net_Y")


def cell_name(row: int, col: int) -> str:
    """Grid coordinates to cell ID: (0, 0) -> 'AA' (top-left), row first."""
    return chr(65 + row) + chr(65 + col)


def _pad_world_pos(bconf: dict, row: int, col: int) -> tuple[float, float] | None:
    """Where this bank's pad sits on the canvas, or None if it has no pad.

    Ports the positioning logic in simulator/src/InitialiseSimulation.ts: bank
    position is relative to its cell, pad position relative to its bank.
    """
    pads = bconf.get("pads")
    if not pads:
        return None
    cell_x = col * (CELL_WIDTH + CELL_MARGIN_X) + CELL_OFFSET_X
    cell_y = row * (CELL_HEIGHT + CELL_MARGIN_Y) + CELL_OFFSET_Y
    bank_x = cell_x + CELL_WIDTH / 2 + bconf["pos"]["x"] - bconf["size"]["width"] / 2
    bank_y = cell_y + CELL_HEIGHT / 2 - bconf["size"]["height"] / 2 + bconf["pos"]["y"]
    pad = pads[0]
    return (bank_x + pad["pos"]["x"], bank_y + pad["pos"]["y"])


def decode_relative_net_name(
    net_name: str, cell_id: str, row: int, col: int, grid_size: int
) -> str | None:
    """Resolve a config-relative net reference to a canonical global net ID.

    Port of decodeRelativeNetName in simulator/src/InitialiseSimulation.ts.
    Returns None where the TS code warns and returns '' (a reference that
    points off the grid).
    """
    # unqualified net -> owned by the current cell
    if net_name.startswith("net"):
        return f"{cell_id}.{net_name}"

    # global long lines: relative H/V + U/D/L/R forms resolve to a bus index;
    # anything else ('global_V3.net_0', 'global.net_clk') is already absolute
    if net_name.startswith("global"):
        address = net_name.split("_")[1]
        if len(address) == 1:
            return net_name
        is_horizontal = address.startswith("H")
        direction = address[1]
        if direction not in ("U", "D", "L", "R"):
            return net_name
        suffix = net_name.split(".")[1]
        if not is_horizontal:
            bus_idx = col + (1 if direction == "R" else 0)
            return f"global_V{bus_idx}.{suffix}"
        bus_idx = row + (0 if direction == "U" else 1)
        return f"global_H{bus_idx}.{suffix}"

    # cardinal-relative reference to a neighbouring (or this: 'T') cell,
    # optionally naming a device: 'N.net_X', 'NW_M0.net_2', 'T_IO0.net_O'
    location = net_name.split(".")[0]
    if len(location) <= 2:
        direction = location
        device = ""
    else:
        direction = net_name.split("_")[0]
        device = "_" + net_name.split("_")[1].split(".")[0]

    row_offset = -1 if "N" in direction else (1 if "S" in direction else 0)
    col_offset = -1 if "W" in direction else (1 if "E" in direction else 0)

    new_row, new_col = row + row_offset, col + col_offset
    if not (0 <= new_row < grid_size and 0 <= new_col < grid_size):
        return None  # off-grid reference

    suffix = net_name.split(".")[1]
    return f"{cell_name(new_row, new_col)}{device}.{suffix}"


@dataclass
class Pip:
    """A programmable interconnect point: a directed, switchable connection.

    (source, destination) is the canonical identity; pip_id is the config's
    cosmetic id string, kept only for save-file compatibility."""

    source: str
    destination: str
    owner_cell: str
    bidirectional: bool = False
    pip_id: str = ""


@dataclass
class CLBSite:
    id: str  # cell ID, e.g. 'BB'
    row: int
    col: int
    nets: set[str] = field(default_factory=set)  # global IDs of all local nets

    def input_pin(self, pin: str) -> str:
        # assert pin in 'ABCDK'
        return f"{self.id}.net_{pin}"

    @property
    def input_pins(self) -> list[str]:
        return [f"{self.id}.{n}" for n in CLB_INPUT_PINS]

    @property
    def output_pins(self) -> list[str]:
        return [f"{self.id}.{n}" for n in CLB_OUTPUT_PINS]


@dataclass
class SwitchMatrixSite:
    id: str  # e.g. 'BB_M0'
    owner_cell: str
    index: int
    pos: dict
    # pin index (0-7) -> global net ID or None. pins 0-3 are owned segments;
    # 4-7 alias neighbouring matrices' segments after the aliasing pass
    pin_nets: list[str | None] = field(default_factory=list)
    own_net_ids: set[str] = field(default_factory=set)

    def legal_connections(self) -> list[tuple[int, int]]:
        pairs = []
        for i in range(8):
            for j in range(i + 1, 8):
                if (
                    POSSIBLE_MATRIX_CONNECTIONS[i][j]
                    and self.pin_nets[i] is not None
                    and self.pin_nets[j] is not None
                ):
                    pairs.append((i, j))
        return pairs


@dataclass
class IOBankSite:
    id: str  # e.g. 'AA_IO0'
    owner_cell: str
    index: int  # index within the owning cell
    pad_index: int  # global pad ordering (grid creation order)
    has_pad: bool
    nets: set[str] = field(default_factory=set)
    pad_pos: tuple[float, float] | None = None  # world (x, y) of the pad, if exists

    def net(self, local: str) -> str:
        # assert local in ('net_I', 'net_O', 'net_T', 'net_pad', ...)
        return f"{self.id}.{local}"


class Fabric:
    """The routing-resource view of the device. Used by the Router.

    - `nodes`: every canonical net ID (CLB-local nets, matrix segments,
      IO-bank nets, global long lines and the clock).
    - `neighbors(net)` / `reverse_neighbors(net)`: routing edges, each a
      (other_net, edge_ref) pair where edge_ref identifies the programmable
      element: ('pip', Pip) or ('matrix', matrix_id, pin_i, pin_j).
    """

    def __init__(self, config: dict):
        self.grid_size: int = config["num_cells"]
        self.clbs: dict[str, CLBSite] = {}
        self.matrices: dict[str, SwitchMatrixSite] = {}
        self.io_banks: dict[str, IOBankSite] = {}
        self._pads_by_edge_cache: dict[str, list[str]] | None = None
        self.pips: list[Pip] = []
        self.bus_nets: list[str] = []
        self.nodes: set[str] = set()
        self.warnings: list[str] = []
        self._adj: dict[str, list[tuple[str, tuple]]] = {}
        self._radj: dict[str, list[tuple[str, tuple]]] = {}

        self._build_sites(config)
        self._alias_matrix_pins()
        self._build_pips(config)
        self._build_graph()

    #! loading:
    @classmethod
    def load(cls, name: str = "xc2064_8x8") -> "Fabric":
        path = _DATA_DIR / f"{name}.json"
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    #! construction:
    @staticmethod
    def _matching_blocks(blocks: list[dict], cid: str) -> list[dict]:
        # null blocks exist in the configs (due to trailing commas in the TS arrays)
        return [b for b in blocks if b is not None and cid in b["ids"]]

    def _cell_config(self, config: dict, cid: str) -> tuple[set[str], list[dict]]:
        """Merge all logic_cell blocks for a cell (port of getConfig):
        nets dedupe by ID (later blocks win), pips concatenate."""
        net_ids: set[str] = set()
        pips: list[dict] = []
        for block in self._matching_blocks(config["logic_cell"], cid):
            for net in block["nets"]:
                net_ids.add(net["id"])
            pips.extend(block["pips"])
        return net_ids, pips

    def _build_sites(self, config: dict) -> None:
        n = self.grid_size
        for row in range(n):
            for col in range(n):
                cid = cell_name(row, col)

                net_ids, _ = self._cell_config(config, cid)
                self.clbs[cid] = CLBSite(
                    id=cid, row=row, col=col, nets={f"{cid}.{nid}" for nid in net_ids}
                )

                # switch matrices: matching blocks flattened in config order
                # null entries appear in some blocks. The TS code skips them
                # with optional chaining but they still use an index
                matrix_configs = [
                    m
                    for block in self._matching_blocks(config["switch_matrix"], cid)
                    for m in block["matrices"]
                ]
                for index, mconf in enumerate(matrix_configs):
                    if mconf is None:
                        self.warnings.append(f"null switch matrix config at {cid}_M{index}")
                matrix_configs_by_index = list(enumerate(matrix_configs))
                for index, mconf in matrix_configs_by_index:
                    if mconf is None:
                        continue
                    mid = f"{cid}_M{index}"
                    pin_nets: list[str | None] = [f"{mid}.{net['id']}" for net in mconf["nets"]]
                    pin_nets += [None] * (8 - len(pin_nets))
                    self.matrices[mid] = SwitchMatrixSite(
                        id=mid,
                        owner_cell=cid,
                        index=index,
                        pos=mconf.get("pos", {}),
                        pin_nets=pin_nets,
                        own_net_ids={p for p in pin_nets if p is not None},
                    )

                # IO banks, with the global pad ordering of the TS init code
                bank_configs = [
                    b
                    for block in self._matching_blocks(config["io"], cid)
                    for b in block["io_bank"]
                ]
                for index, bconf in enumerate(bank_configs):
                    if bconf is None:
                        self.warnings.append(f"null io bank config at {cid}_IO{index}")
                        continue
                    bid = f"{cid}_IO{index}"
                    self.io_banks[bid] = IOBankSite(
                        id=bid,
                        owner_cell=cid,
                        index=index,
                        pad_index=len(self.io_banks),
                        has_pad=bool(bconf.get("pads")),
                        nets={f"{bid}.{net['id']}" for net in bconf["nets"]},
                        pad_pos=_pad_world_pos(bconf, row, col),
                    )

        self.bus_nets = [net["id"] for net in config["bus"]]

    @staticmethod
    def _is_placeholder(net_id: str | None) -> bool:
        # config blocks use a net named 'dummy' as an
        # overwrite-me placeholder for the aliasing pass
        return net_id is not None and net_id.split(".")[-1] == "dummy"

    def _alias_matrix_pins(self) -> None:
        """Fill matrix pins 4-7 with the neighbouring matrices' segments.

        Port of the second config setup pass in InitialiseSimulation.ts,
        including its edge cases: left-edge cells alias their own M2/M3,
        top-row matrices M2/M3 alias the local M0/M1, and cell AA (the only
        cell with six matrices) additionally maps M4/M5 down to M0/M1.
        """
        n = self.grid_size
        for matrix in self.matrices.values():
            cid = matrix.owner_cell
            row, col = ord(cid[0]) - 65, ord(cid[1]) - 65
            index = matrix.index

            left_cell = cid[0] + chr(ord(cid[1]) - 1) if col > 0 else None
            bottom_cell = chr(ord(cid[0]) + 1) + cid[1] if row < n - 1 else None
            left_index = index
            bottom_index = index

            # left edge: connect to this cell's own M2/M3 instead
            if left_cell is None and bottom_cell is not None and index < 2:
                left_cell = cid
                left_index = index + 2

            if row == 0:
                if cid == "AA":
                    if index >= 2:
                        bottom_index = index % 2
                    if index >= 4:
                        bottom_cell = cid
                elif index >= 2:
                    bottom_index = index % 2
                    bottom_cell = cid

            def resolve(target_cell: str | None, target_index: int, net_local: str) -> str | None:
                if target_cell is None:
                    return None
                target = self.matrices.get(f"{target_cell}_M{target_index}")
                if target is None:
                    return None
                candidate = f"{target.id}.{net_local}"
                return candidate if candidate in target.own_net_ids else None

            pins = matrix.pin_nets
            if pins[6] is None or self._is_placeholder(pins[6]):
                pins[6] = resolve(left_cell, left_index, "net_3")
            if pins[7] is None or self._is_placeholder(pins[7]):
                pins[7] = resolve(left_cell, left_index, "net_2")
            if pins[4] is None or self._is_placeholder(pins[4]):
                pins[4] = resolve(bottom_cell, bottom_index, "net_1")
            if pins[5] is None or self._is_placeholder(pins[5]):
                pins[5] = resolve(bottom_cell, bottom_index, "net_0")

            # any placeholder that survived aliasing is not a real segment
            for i, pin in enumerate(pins):
                if self._is_placeholder(pin):
                    pins[i] = None

    def _build_pips(self, config: dict) -> None:
        n = self.grid_size
        seen: set[tuple[str, str]] = set()
        for row in range(n):
            for col in range(n):
                cid = cell_name(row, col)
                _, pip_configs = self._cell_config(config, cid)
                for pconf in pip_configs:
                    source = decode_relative_net_name(pconf["source"], cid, row, col, n)
                    destination = decode_relative_net_name(pconf["destination"], cid, row, col, n)
                    if source is None or destination is None:
                        self.warnings.append(
                            f"pip in {cid} points off-grid: "
                            f"{pconf['source']} -> {pconf['destination']}"
                        )
                        continue
                    # (source, destination) is the canonical pip identity
                    # (SaveSimulation.ts matches saved pips the same way)
                    if (source, destination) in seen:
                        self.warnings.append(f"duplicate pip in {cid}: {source} -> {destination}")
                        continue
                    seen.add((source, destination))
                    self.pips.append(
                        Pip(
                            source=source,
                            destination=destination,
                            owner_cell=cid,
                            bidirectional=bool(pconf.get("bidirectional")),
                            pip_id=pconf.get("id", ""),
                        )
                    )

    def _add_edge(self, src: str, dst: str, ref: tuple) -> None:
        self._adj.setdefault(src, []).append((dst, ref))
        self._radj.setdefault(dst, []).append((src, ref))

    def _build_graph(self) -> None:
        for clb in self.clbs.values():
            self.nodes.update(clb.nets)
        for matrix in self.matrices.values():
            self.nodes.update(
                matrix.own_net_ids - {p for p in matrix.own_net_ids if self._is_placeholder(p)}
            )
        for bank in self.io_banks.values():
            self.nodes.update(bank.nets)
        self.nodes.update(self.bus_nets)

        for pip in self.pips:
            for endpoint in (pip.source, pip.destination):
                if endpoint not in self.nodes:
                    self.warnings.append(
                        f"pip references unknown net '{endpoint}' "
                        f"({pip.source} -> {pip.destination}, cell {pip.owner_cell})"
                    )
            self._add_edge(pip.source, pip.destination, ("pip", pip))
            if pip.bidirectional:
                self._add_edge(pip.destination, pip.source, ("pip", pip))

        for matrix in self.matrices.values():
            for i, j in matrix.legal_connections():
                a, b = matrix.pin_nets[i], matrix.pin_nets[j]
                ref = ("matrix", matrix.id, i, j)
                self._add_edge(a, b, ref)
                self._add_edge(b, a, ref)

    #! queries:
    def reserved_nets(self) -> set[str]:
        """The bus nets that data signals may never enter (clock/oscillator/
        IO-clock distribution). Policy defined by RESERVED_PREFIXES."""
        return {net for net in self.bus_nets if net.startswith(RESERVED_PREFIXES)}

    def pad_banks(self, edge: str | None = None) -> list[str]:
        """IO bank IDs in physical pad order, optionally restricted to one
        edge of the die: 'N', 'S', 'W' or 'E'.

        Order runs left-to-right along N and S and top-to-bottom down E and W,
        so a slice is a contiguous physical row of pads. With no edge, the
        pads run clockwise from the top-left: N, then E, then S, then W.

        Which edge a pad is on comes from where it is actually drawn, not from
        its owning cell: a corner cell owns pads on two different edges (on
        the 8x8, AA_IO0/IO1 are the top of the west edge while AA_IO2/IO3 are
        the left of the north edge)."""
        if edge is not None:
            edge = edge.upper()
            if edge not in ("N", "S", "W", "E"):
                raise ValueError(f"unknown edge '{edge}'; expected N, S, W or E")

        by_edge = self._pads_by_edge()
        if edge is not None:
            return list(by_edge[edge])
        return [bid for side in ("N", "E", "S", "W") for bid in by_edge[side]]

    def _pads_by_edge(self) -> dict[str, list[str]]:
        """Pads grouped by the edge they are drawn on, each in physical order."""
        if self._pads_by_edge_cache is not None:
            return self._pads_by_edge_cache

        pads = [
            (bank.id, bank.pad_pos[0], bank.pad_pos[1])
            for bank in self.io_banks.values()
            if bank.has_pad and bank.pad_pos is not None
        ]
        result: dict[str, list[str]] = {"N": [], "E": [], "S": [], "W": []}
        if pads:
            min_x = min(x for _, x, _ in pads)
            max_x = max(x for _, x, _ in pads)
            min_y = min(y for _, _, y in pads)
            max_y = max(y for _, _, y in pads)

            grouped: dict[str, list[tuple[str, float, float]]] = {
                "N": [],
                "E": [],
                "S": [],
                "W": [],
            }
            for bid, x, y in pads:
                # the edge whose boundary this pad hugs most closely
                side = min(
                    (("N", y - min_y), ("S", max_y - y), ("W", x - min_x), ("E", max_x - x)),
                    key=lambda item: item[1],
                )[0]
                grouped[side].append((bid, x, y))

            for side, entries in grouped.items():
                axis = 1 if side in ("N", "S") else 2  # across the edge
                result[side] = [item[0] for item in sorted(entries, key=lambda item: item[axis])]

        self._pads_by_edge_cache = result
        return result

    def neighbors(self, net_id: str) -> list[tuple[str, tuple]]:
        return self._adj.get(net_id, [])

    def reverse_neighbors(self, net_id: str) -> list[tuple[str, tuple]]:
        return self._radj.get(net_id, [])

    def edge_ref(self, src: str, dst: str) -> tuple | None:
        """The edge_ref for the directed hop src -> dst (the same value
        find_path reports), or None if the fabric has no such edge. Lets a
        routed hop be turned back off without re-running the search."""
        for other, ref in self.neighbors(src):
            if other == dst:
                return ref
        return None

    def reachable_sources(self, net_id: str) -> set[str]:
        """All nets from which net_id can be reached (reverse BFS)."""
        seen: set[str] = set()
        frontier = [net_id]
        while frontier:
            current = frontier.pop()
            for src, _ in self.reverse_neighbors(current):
                if src not in seen:
                    seen.add(src)
                    frontier.append(src)
        return seen

    def find_path(
        self, source: str, target: str, blocked: set[str] | None = None
    ) -> list[tuple[str, str, tuple]] | None:
        """BFS shortest route from source net to target net.

        Returns the hops as (from_net, to_net, edge_ref) triples, [] if
        source == target, or None if no route exists. Nets in `blocked`
        (already claimed by other signals) are not entered.
        """
        if source == target:
            return []
        blocked = blocked or set()
        if target in blocked or source in blocked:
            return None

        parent: dict[str, tuple[str, tuple]] = {}
        queue = deque([source])
        seen = {source}
        while queue:
            current = queue.popleft()
            for nxt, ref in self.neighbors(current):
                if nxt in seen or nxt in blocked:
                    continue
                seen.add(nxt)
                parent[nxt] = (current, ref)
                if nxt == target:
                    hops: list[tuple[str, str, tuple]] = []
                    node = target
                    while node != source:
                        prev, edge = parent[node]
                        hops.append((prev, node, edge))
                        node = prev
                    hops.reverse()
                    return hops
                queue.append(nxt)
        return None

    def validate(self) -> list[str]:
        """Structural sanity report (empty list = clean)."""
        issues = list(self.warnings)
        for clb in self.clbs.values():
            for pin in ("net_A", "net_B", "net_C", "net_D", "net_K"):
                net = f"{clb.id}.{pin}"
                if not self.reverse_neighbors(net):
                    issues.append(f"CLB input pin {net} has no incoming routing edges")
            for pin in CLB_OUTPUT_PINS:
                net = f"{clb.id}.{pin}"
                if not self.neighbors(net):
                    issues.append(f"CLB output pin {net} has no outgoing routing edges")
        return issues
