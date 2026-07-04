"""Full-chip configuration and export to the web simulator's save format.

DeviceConfig holds everything the web simulator's import understands
(see simulator/src/SaveSimulation.ts): per-cell mux selects and LUT truth
tables, per-matrix connection matrices, enabled PIPs, IO-bank muxes, and the
`drivers` list (one entry per enabled directed hop — the simulator uses it
to propagate values, so direction is signal flow, source drives destination).

Mapping notes (LogicCell.ts is the source of truth):
- `luts[0]` is the web sim's LUT1 and drives net_G through muxes m6/m8/m13;
  `luts[1]` is LUT2 driving net_F through m18/m20/m24. So the packed CLB's
  F fields map to m18/m20/m24 + luts[1], and G to m6/m8/m13 + luts[0].
- m59 selects net_X (0=G, 1=Q, 2=F) and m61 selects net_Y — the same
  encoding as CLB.sel_x / CLB.sel_y.
- LUT truth-table index = (mux1 << 2) | (mux2 << 1) | mux3, which the packed
  CLB's lut_*_init integers already use (bit i of the int = truthTable[i]).
- Switch matrix `connections[i][j] = 1` means pin i drives pin j
  (SwitchMatrix.simulate copies row -> column), so it is directional.
"""

from __future__ import annotations

import json
from pathlib import Path

from .fabric import Fabric, Pip

# id -> default select, in LogicCell.ts declaration order (m46/m56 default to
# GND so the flip-flop's async set/reset stay inactive)
DEFAULT_CELL_MUXES: dict[str, int] = {
    "m6": 0,
    "m8": 0,
    "m13": 0,
    "m18": 0,
    "m20": 0,
    "m24": 0,
    "m46": 2,
    "m51": 0,
    "m56": 2,
    "m59": 0,
    "m61": 0,
    "m100": 0,
}


def _truth_table_bits(init: int) -> list[bool]:
    """Return a list of 8 booleans representing the truth table bits of a LUT"""
    
    return [bool((init >> i) & 1) for i in range(8)]


def logic_cell_settings(clb) -> dict:
    """Translate a packed CLB node into web-simulator logic cell settings."""
    muxes = dict(DEFAULT_CELL_MUXES)
    muxes["m6"] = clb.sel_g_in1
    muxes["m8"] = clb.sel_g_in2
    muxes["m13"] = clb.sel_g_in3
    muxes["m18"] = clb.sel_f_in1
    muxes["m20"] = clb.sel_f_in2
    muxes["m24"] = clb.sel_f_in3
    muxes["m51"] = clb.sel_clk1
    muxes["m100"] = clb.sel_clk2
    muxes["m59"] = clb.sel_x
    muxes["m61"] = clb.sel_y
    # the packer does not use the flip-flop's async set/reset: hold at GND
    # todo: investigate if async set/reset should be used, not important for now
    muxes["m46"] = 2
    muxes["m56"] = 2
    return {
        "muxes": muxes,
        # luts[0] = LUT1 (G), luts[1] = LUT2 (F)
        "luts": [_truth_table_bits(clb.lut_g_init), _truth_table_bits(clb.lut_f_init)],
    }


class DeviceConfig:
    """A complete chip configuration over a Fabric, exportable to the web
    simulator's save-file JSON."""

    def __init__(self, fabric: Fabric):
        self.fabric = fabric
        self.logic_cells: dict[str, dict] = {
            cid: {
                "muxes": dict(DEFAULT_CELL_MUXES),
                "luts": [[False] * 8, [False] * 8],
            }
            for cid in fabric.clbs
        }
        self.matrix_connections: dict[str, list[list[int]]] = {
            mid: [[0] * 8 for _ in range(8)] for mid in fabric.matrices
        }
        self.enabled_pips: set[tuple[str, str]] = set()
        self.io_banks: dict[str, dict[str, int]] = {
            bid: {"mts": 0, "min": 0} for bid in fabric.io_banks
        }
        self.drivers: list[tuple[str, str]] = []

    #! configuration:
    def configure_clb(self, cell_id: str, clb) -> None:
        if cell_id not in self.logic_cells:
            raise KeyError(f"Unknown cell '{cell_id}'")
        self.logic_cells[cell_id] = logic_cell_settings(clb)

    def configure_iob(self, bank_id: str, mode: str) -> None:
        """mode: 'input' (pad tri-stated, user/external drives it) or
        'output' (the OUT net permanently drives the pad)."""
        if bank_id not in self.io_banks:
            raise KeyError(f"Unknown IO bank '{bank_id}'")
        if mode == "input":
            self.io_banks[bank_id]["mts"] = 0
        elif mode == "output":
            self.io_banks[bank_id]["mts"] = 2
        else:
            raise ValueError(f"Unknown IOB mode '{mode}'")

    def enable_edge(self, src: str, dst: str, ref: tuple) -> None:
        """Enable one routing hop (as returned by Fabric.find_path) with
        signal flowing src -> dst."""
        kind = ref[0]
        if kind == "pip":
            pip: Pip = ref[1]
            self.enabled_pips.add((pip.source, pip.destination))
        elif kind == "matrix":
            _, mid, i, j = ref
            matrix = self.fabric.matrices[mid]
            if matrix.pin_nets[i] == src and matrix.pin_nets[j] == dst:
                self.matrix_connections[mid][i][j] = 1
            elif matrix.pin_nets[j] == src and matrix.pin_nets[i] == dst:
                self.matrix_connections[mid][j][i] = 1
            else:
                raise ValueError(f"edge {ref} does not connect {src} -> {dst}")
        else:
            raise ValueError(f"Unknown edge kind '{kind}'")
        self.drivers.append((src, dst))

    def enable_path(self, hops: list[tuple[str, str, tuple]]) -> None:
        for src, dst, ref in hops:
            self.enable_edge(src, dst, ref)

    #! export:
    def to_dict(self) -> dict:
        logic_cells = [
            {
                "id": cid,
                "muxes": [
                    {"id": mux_id, "select": select}
                    for mux_id, select in cell["muxes"].items()
                ],
                "luts": [
                    {"id": "lut_0", "truthTable": list(cell["luts"][0])},
                    {"id": "lut_1", "truthTable": list(cell["luts"][1])},
                ],
            }
            for cid, cell in self.logic_cells.items()
        ]

        switch_matrices = [
            {
                "id": mid,
                "connections": [list(row) for row in self.matrix_connections[mid]],
                # note: the web sim recomputes world positions itself and its
                # import ignores pos; this is the config-relative position
                "pos": dict(self.fabric.matrices[mid].pos),
            }
            for mid in self.matrix_connections
        ]

        pips = [
            {
                "id": pip.pip_id,
                "source": pip.source,
                "destination": pip.destination,
                "enabled": (pip.source, pip.destination) in self.enabled_pips,
            }
            for pip in self.fabric.pips
        ]

        io_banks = [
            {
                "id": bid,
                "muxes": [
                    {"id": "mts", "select": bank["mts"]},
                    {"id": "min", "select": bank["min"]},
                ],
            }
            for bid, bank in self.io_banks.items()
        ]

        drivers = [{"source": s, "destination": d} for s, d in self.drivers]

        return {
            "logicCells": logic_cells,
            "switchMatrices": switch_matrices,
            "pips": pips,
            "ioBanks": io_banks,
            "drivers": drivers,
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8"
        )
