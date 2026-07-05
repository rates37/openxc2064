"""Fabric-level simulator: executes a DeviceConfig over its Fabric.

This is the toolchain's reference model for placed-and-routed designs:
the same configuration state the web simulator
imports (enabled PIPs, directional switch-matrix connections, logic cell
muxes/LUTs, IO bank modes) evaluated natively in Python.

Built for speed on full-device designs. Instead of the web simulator's
iterate-until-settled sweeps, construction compiles the configuration:

- enabled routing edges and active device functions become a net-level
  dependency graph, topologically sorted once (Kahn's alg);
- the schedule is a flat list of closures over one integer value array,
  so a step is a single allocation-free pass (plus the flip-flop update
  between the two passes, mirroring RTLSimulator's step contract);
- construction also acts as a router-bug detector: multiple drivers and
  register-free combinational loops raise FabricSimulationError, floating
  nets that something actually reads are collected in `warnings`.

Logic cell semantics follow simulator/src/models/LogicCell.ts: LUT index is
(mux1 << 2) | (mux2 << 1) | mux3, luts[0]/m6/m8/m13 drive G, luts[1]/m18/
m20/m24 drive F, m59 -> X, m61 -> Y, m51/m100 form the clock, m46/m56 are
the flip-flop's async reset/set (R wins over S, both level-sensitive,
checked at the clock update like the web sim's evaluation loop).
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..device.config import DeviceConfig


class FabricSimulationError(Exception):
    """A structural problem that makes the configuration unsimulatable:
    a net with multiple drivers, or a register-free combinational loop."""


def _mux_sensitive(table: int, position: int) -> bool:
    """Does the 8-bit truth table depend on the mux at `position`?
    position 0 = mux1 (index bit 2), 1 = mux2 (bit 1), 2 = mux3 (bit 0)."""
    flip = (4, 2, 1)[position]
    return any(((table >> i) & 1) != ((table >> (i ^ flip)) & 1) for i in range(8))


def _lut_pins(muxes: dict, which: str, table: int) -> set[int]:
    """Pin indices (0=A..3=D) the F or G LUT actually reads: a mux input
    whose truth-table position is a don't-care (e.g. the defaulted third mux
    of a 2-input function) is not a dependency."""
    if which == "f":
        m1, m2, m3 = muxes["m18"], muxes["m20"], muxes["m24"]
    else:
        m1, m2, m3 = muxes["m6"], muxes["m8"], muxes["m13"]
    pins: set[int] = set()
    if _mux_sensitive(table, 0):
        pins.add(1 if m1 else 0)
    if _mux_sensitive(table, 1):
        pins.add(2 if m2 else 1)
    if _mux_sensitive(table, 2) and m3 != 2:  # m3 == 2 reads Q (state)
        pins.add(2 if m3 == 0 else 3)
    return pins


class FabricSimulator:
    def __init__(self, config: "DeviceConfig"):
        self.config = config
        self.fabric = config.fabric
        self.warnings: list[str] = []

        # net id -> value index; values themselves live in one flat list
        self._index: dict[str, int] = {}
        self._values: list[int] = []

        self._compile()

    #! public interface:
    def set_pad(self, bank_id: str, value: int) -> None:
        """Drive an input pad externally (like clicking it in the web sim)."""
        bank = self.fabric.io_banks[bank_id]
        self._values[self._idx(bank.net("net_pad"))] = 1 if value else 0

    def get_pad(self, bank_id: str) -> int:
        bank = self.fabric.io_banks[bank_id]
        return self._values[self._idx(bank.net("net_pad"))]

    def get_net(self, net_id: str) -> int:
        """Debug access. Nets outside the compiled schedule read as 0."""
        index = self._index.get(net_id)
        return self._values[index] if index is not None else 0

    def step(self) -> None:
        schedule = self._schedule
        for op in schedule:
            op()
        self._update_dffs()
        for op in schedule:
            op()

    #! compilation:
    def _idx(self, net_id: str) -> int:
        index = self._index.get(net_id)
        if index is None:
            index = len(self._values)
            self._index[net_id] = index
            self._values.append(0)
        return index

    def _compile(self) -> None:
        config, fabric = self.config, self.fabric

        # the enabled routing in signal-flow direction: the drivers list,
        # exactly as the web simulator propagates. (Direction cannot be
        # reconstructed from the enabled pips alone, a bidirectional pip
        # traversed in reverse still stores its canonical direction.)
        seen_hops: set[tuple[str, str]] = set()
        hops: list[tuple[str, str]] = []
        for src, dst in config.drivers:
            if (src, dst) not in seen_hops:
                seen_hops.add((src, dst))
                hops.append((src, dst))

        # cross-check: every driver needs an enabled pip (either way round if
        # bidirectional) or matrix connection, and vice versa
        pip_pairs = set(config.enabled_pips)
        pip_reverse = {
            (p.destination, p.source)
            for p in fabric.pips
            if p.bidirectional and (p.source, p.destination) in pip_pairs
        }
        matrix_pairs: set[tuple[str, str]] = set()
        for mid, connections in config.matrix_connections.items():
            pins = fabric.matrices[mid].pin_nets
            for i in range(8):
                row = connections[i]
                for j in range(8):
                    if row[j]:
                        if pins[i] is None or pins[j] is None:
                            self.warnings.append(
                                f"matrix {mid} connection {i}->{j} touches an unbound pin"
                            )
                        else:
                            matrix_pairs.add((pins[i], pins[j]))
        legal_hops = pip_pairs | pip_reverse | matrix_pairs
        for src, dst in hops:
            if (src, dst) not in legal_hops:
                self.warnings.append(
                    f"driver {src} -> {dst} has no enabled pip or matrix connection"
                )
        for src, dst in sorted(pip_pairs):
            if (src, dst) not in seen_hops and (dst, src) not in seen_hops:
                self.warnings.append(f"enabled pip {src} -> {dst} has no driver")
        for src, dst in sorted(matrix_pairs):
            if (src, dst) not in seen_hops:
                self.warnings.append(f"matrix connection {src} -> {dst} has no driver")

        # producers: every net may have at most one driver
        cell_output_nets = {
            f"{cid}.{pin}": (cid, which)
            for cid in fabric.clbs
            for which, pin in enumerate(("net_X", "net_Y"))
        }
        producers: dict[str, str] = {}

        def claim(net: str, description: str) -> None:
            if net in producers:
                raise FabricSimulationError(
                    f"net {net} has multiple drivers: {producers[net]} and {description}"
                )
            producers[net] = description

        for src, dst in hops:
            claim(dst, f"routing hop from {src}")
            if dst in cell_output_nets:
                raise FabricSimulationError(
                    f"net {dst} is a CLB output but is driven by a routing hop from {src}"
                )

        iob_ops: list[tuple[str, str]] = []  # (src_net, dst_net) copies
        for bid, bank_cfg in config.io_banks.items():
            bank = fabric.io_banks[bid]
            mts, min_sel = bank_cfg["mts"], bank_cfg["min"]
            if min_sel != 0:
                self.warnings.append(f"{bid}: latched input (min=1) not supported; treated as combinational")
            if mts == 2:  # output: OUT drives the pad
                claim(bank.net("net_pad"), f"{bid} output buffer")
                iob_ops.append((bank.net("net_O"), bank.net("net_pad")))
            else:  # input (mts 0) or tri-state (1, unsupported -> input)
                if mts == 1:
                    self.warnings.append(f"{bid}: tri-state mode (mts=1) not supported; treated as input")
                # the pad itself is an external source; IN follows it
                claim(bank.net("net_I"), f"{bid} input buffer")
                iob_ops.append((bank.net("net_pad"), bank.net("net_I")))

        # which cell outputs are consumed (i.e., drive at least one hop)?
        hop_sources = {src for src, _ in hops}
        active_outputs = [
            (net, cid, which)
            for net, (cid, which) in cell_output_nets.items()
            if net in hop_sources
        ]
        for net, _, _ in active_outputs:
            claim(net, "CLB output")

        # sequential cells: Q must be observable and the cell in use
        active_cells = {cid for _, cid, _ in active_outputs}
        seq_cells = []
        for cid in active_cells:
            muxes = config.logic_cells[cid]["muxes"]
            q_observed = (
                muxes["m59"] == 1
                or muxes["m61"] == 1
                or muxes["m13"] == 2
                or muxes["m24"] == 2
            )
            if q_observed:
                seq_cells.append(cid)

        # net-level dependency graph
        deps: dict[str, set[str]] = {}

        def add_dep(net: str, dep: str) -> None:
            deps.setdefault(net, set()).add(dep)
            deps.setdefault(dep, set())

        for src, dst in hops:
            add_dep(dst, src)
        for src, dst in iob_ops:
            add_dep(dst, src)
        cell_out_deps: dict[str, list[str]] = {}
        for net, cid, which in active_outputs:
            muxes, g_int, f_int, _ = self._cell_params(cid)
            sel = muxes["m59"] if which == 0 else muxes["m61"]
            if sel == 1:  # Q: register state, no combinational deps
                pin_deps: list[str] = []
            else:
                table = f_int if sel == 2 else g_int
                pins = _lut_pins(muxes, "f" if sel == 2 else "g", table)
                pin_deps = [f"{cid}.net_{'ABCD'[p]}" for p in sorted(pins)]
            cell_out_deps[net] = pin_deps
            deps.setdefault(net, set())
            for dep in pin_deps:
                add_dep(net, dep)

        # topological ordering
        indegree = {net: len(d) for net, d in deps.items()}
        dependents: dict[str, list[str]] = {}
        for net, dep_nets in deps.items():
            for dep in dep_nets:
                dependents.setdefault(dep, []).append(net)
        queue = deque(net for net in deps if indegree[net] == 0)
        order: list[str] = []
        while queue:
            net = queue.popleft()
            order.append(net)
            for dependent in dependents.get(net, ()):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(dependent)
        if len(order) < len(deps):
            looped = sorted(net for net, d in indegree.items() if d > 0)
            raise FabricSimulationError(
                f"combinational loop through the fabric involving: {', '.join(looped)}"
            )

        # compile the schedule: one closure per produced net, in order
        values = self._values
        copy_by_dst = {dst: src for src, dst in hops}
        iob_by_dst = {dst: src for src, dst in iob_ops}
        out_by_net = {net: (cid, which) for net, cid, which in active_outputs}
        self._q: dict[str, int] = {cid: 0 for cid in active_cells}

        def make_copy(si: int, di: int) -> Callable[[], None]:
            def op() -> None:
                values[di] = values[si]

            return op

        schedule: list[Callable[[], None]] = []
        for net in order:
            if net in copy_by_dst:
                schedule.append(make_copy(self._idx(copy_by_dst[net]), self._idx(net)))
            elif net in iob_by_dst:
                schedule.append(make_copy(self._idx(iob_by_dst[net]), self._idx(net)))
            elif net in out_by_net:
                cid, which = out_by_net[net]
                schedule.append(self._make_cell_output_op(cid, which, self._idx(net)))
            # nets with no producer are sources (external pads, floating nets)
        self._schedule = schedule

        # flip-flop update records
        self._seq = [self._make_seq_record(cid) for cid in sorted(seq_cells)]

        # floating-net report: reads with no producer and no external source
        external_sources = {
            fabric.io_banks[bid].net("net_pad")
            for bid, bank_cfg in config.io_banks.items()
            if bank_cfg["mts"] != 2
        }
        produced = set(producers) | external_sources
        reads: dict[str, str] = {}
        for src, dst in hops:
            reads.setdefault(src, f"routing hop to {dst}")
        for net, pin_deps in cell_out_deps.items():
            for dep in pin_deps:
                reads.setdefault(dep, f"CLB output {net}")
        for record in self._seq:
            for net in record["clock_reads"]:
                reads.setdefault(net, f"clock of cell {record['cid']}")
        for bid, bank_cfg in config.io_banks.items():
            if bank_cfg["mts"] == 2:
                reads.setdefault(
                    self.fabric.io_banks[bid].net("net_O"), f"output pad {bid}"
                )
        for net, reader in reads.items():
            if net not in produced:
                self.warnings.append(f"floating net {net} is read by {reader}")

        # match RTLSimulator's initial conditions: the previous clock value is
        # evaluated on the all-zero state, then values settle
        for record in self._seq:
            record["prev_clk"] = self._eval_clk(record)
        for op in self._schedule:
            op()

    def _cell_params(self, cid: str):
        cached = getattr(self, "_params_cache", None)
        if cached is None:
            cached = self._params_cache = {}
        params = cached.get(cid)
        if params is None:
            muxes = self.config.logic_cells[cid]["muxes"]
            luts = self.config.logic_cells[cid]["luts"]
            g_int = sum(1 << i for i, bit in enumerate(luts[0]) if bit)
            f_int = sum(1 << i for i, bit in enumerate(luts[1]) if bit)
            pin_indices = [self._idx(f"{cid}.net_{p}") for p in "ABCD"]
            params = cached[cid] = (muxes, g_int, f_int, pin_indices)
        return params

    def _lut_value(self, cid: str, which: str, q: int) -> int:
        muxes, g_int, f_int, pins = self._cell_params(cid)
        values = self._values
        a, b, c, d = (values[p] for p in pins)
        if which == "f":
            m1, m2, m3, table = muxes["m18"], muxes["m20"], muxes["m24"], f_int
        else:
            m1, m2, m3, table = muxes["m6"], muxes["m8"], muxes["m13"], g_int
        i0 = b if m1 else a
        i1 = c if m2 else b
        i2 = (c, d, q)[m3]
        return (table >> ((i0 << 2) | (i1 << 1) | i2)) & 1

    def _make_cell_output_op(self, cid: str, which: int, out_index: int):
        muxes, g_int, f_int, pins = self._cell_params(cid)
        sel = muxes["m59"] if which == 0 else muxes["m61"]
        values = self._values
        q_state = self._q

        if sel == 1:  # Q

            def op() -> None:
                values[out_index] = q_state.get(cid, 0)

            return op

        if sel == 2:
            m1, m2, m3, table = muxes["m18"], muxes["m20"], muxes["m24"], f_int
        else:
            m1, m2, m3, table = muxes["m6"], muxes["m8"], muxes["m13"], g_int
        pa, pb, pc, pd = pins

        def op() -> None:
            a, b, c, d = values[pa], values[pb], values[pc], values[pd]
            i0 = b if m1 else a
            i1 = c if m2 else b
            i2 = (c, d, q_state.get(cid, 0))[m3]
            values[out_index] = (table >> ((i0 << 2) | (i1 << 1) | i2)) & 1

        return op

    #! flip-flops:
    def _make_seq_record(self, cid: str) -> dict:
        muxes, g_int, _, pins = self._cell_params(cid)
        clock_reads: list[str] = []
        if muxes["m51"] == 2:
            clock_reads.append(f"{cid}.net_K")
        elif muxes["m51"] == 1:
            clock_reads.append(f"{cid}.net_C")
        else:  # clock from LUT G
            clock_reads.extend(
                f"{cid}.net_{'ABCD'[p]}" for p in sorted(_lut_pins(muxes, "g", g_int))
            )
        return {
            "cid": cid,
            "muxes": muxes,
            "pins": pins,
            "k_index": self._idx(f"{cid}.net_K"),
            "clock_reads": clock_reads,
            "prev_clk": 0,
        }

    def _eval_clk(self, record: dict) -> int:
        muxes, cid = record["muxes"], record["cid"]
        values = self._values
        m51 = muxes["m51"]
        if m51 == 2:
            clk1 = values[record["k_index"]]
        elif m51 == 1:
            clk1 = values[record["pins"][2]]  # C pin
        else:
            clk1 = self._lut_value(cid, "g", self._q.get(cid, 0))
        m100 = muxes["m100"]
        if m100 == 2:
            return 0
        return clk1 if m100 == 1 else 1 - clk1

    def _update_dffs(self) -> None:
        values = self._values
        for record in self._seq:
            cid, muxes = record["cid"], record["muxes"]
            clk = self._eval_clk(record)
            rising = record["prev_clk"] == 0 and clk == 1
            record["prev_clk"] = clk

            q = self._q[cid]
            # async reset/set, R wins (LogicCell.ts order)
            m46, m56 = muxes["m46"], muxes["m56"]
            pa, _, pc, pd = record["pins"]
            reset = 0 if m46 == 2 else (self._lut_value(cid, "g", q) if m46 == 0 else values[pd])
            set_ = 0 if m56 == 2 else (values[pa] if m56 == 0 else self._lut_value(cid, "f", q))
            if reset:
                self._q[cid] = 0
            elif set_:
                self._q[cid] = 1
            elif rising:
                self._q[cid] = self._lut_value(cid, "f", q)
