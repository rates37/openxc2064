import pytest

from openxc2064.device import Fabric
from openxc2064.device.fabric import (
    POSSIBLE_MATRIX_CONNECTIONS,
    cell_name,
    decode_relative_net_name,
)


@pytest.fixture(scope="module")
def fabric3() -> Fabric:
    return Fabric.load("xc2064_3x3")


@pytest.fixture(scope="module")
def fabric8() -> Fabric:
    return Fabric.load("xc2064_8x8")


#! canonical net name decoding:
def test_decode_local_net():
    assert decode_relative_net_name("net_A", "BB", 1, 1, 3) == "BB.net_A"


def test_decode_cardinal_neighbours():
    # from BB (row 1, col 1): N is AB, S is CB, W is BA, E is BC, NW is AA
    assert decode_relative_net_name("N.net_X", "BB", 1, 1, 3) == "AB.net_X"
    assert decode_relative_net_name("S.net_A", "BB", 1, 1, 3) == "CB.net_A"
    assert decode_relative_net_name("NW_M0.net_2", "BB", 1, 1, 3) == "AA_M0.net_2"
    assert decode_relative_net_name("W_M1.net_0", "BB", 1, 1, 3) == "BA_M1.net_0"


def test_decode_this_cell_devices():
    assert decode_relative_net_name("T_M0.net_1", "BB", 1, 1, 3) == "BB_M0.net_1"
    assert decode_relative_net_name("T_IO0.net_O", "AB", 0, 1, 3) == "AB_IO0.net_O"


def test_decode_global_long_lines():
    # HU = horizontal line above (index row), HD = below (row + 1)
    assert decode_relative_net_name("global_HU.net_0", "BB", 1, 1, 3) == "global_H1.net_0"
    assert decode_relative_net_name("global_HD.net_0", "BB", 1, 1, 3) == "global_H2.net_0"
    # VL = vertical line to the left (index col), VR = right (col + 1)
    assert decode_relative_net_name("global_VL.net_1", "BB", 1, 1, 3) == "global_V1.net_1"
    assert decode_relative_net_name("global_VR.net_0", "BB", 1, 1, 3) == "global_V2.net_0"
    # absolute references pass through untouched
    assert decode_relative_net_name("global_V0.net_2", "BB", 1, 1, 3) == "global_V0.net_2"
    assert decode_relative_net_name("global.net_clk", "BB", 1, 1, 3) == "global.net_clk"


def test_decode_off_grid_returns_none():
    # AA has no northern or western neighbour
    assert decode_relative_net_name("N.net_X", "AA", 0, 0, 3) is None
    assert decode_relative_net_name("W_M0.net_2", "AA", 0, 0, 3) is None


def test_cell_names():
    assert cell_name(0, 0) == "AA"
    assert cell_name(1, 1) == "BB"
    assert cell_name(7, 7) == "HH"


#! 3x3 fabric structure:
def test_3x3_site_counts(fabric3: Fabric):
    assert fabric3.grid_size == 3
    assert len(fabric3.clbs) == 9
    assert set(fabric3.clbs) == {cell_name(r, c) for r in range(3) for c in range(3)}
    # 2 matrices per cell, plus extras on the top/left edges; AA alone has 6
    assert sum(1 for m in fabric3.matrices.values() if m.owner_cell == "AA") == 6
    assert sum(1 for m in fabric3.matrices.values() if m.owner_cell == "BB") == 2
    assert "global.net_clk" in fabric3.bus_nets


def test_3x3_interior_matrix_aliasing(fabric3: Fabric):
    # a matrix owns its top (0, 1) and right (2, 3) segments; the bottom pins
    # (4, 5) alias the below-neighbour's top segments and the left pins (6, 7)
    # alias the left-neighbour's right segments
    bb_m0 = fabric3.matrices["BB_M0"]
    assert bb_m0.pin_nets == [
        "BB_M0.net_0",
        "BB_M0.net_1",
        "BB_M0.net_2",
        "BB_M0.net_3",
        "CB_M0.net_1",
        "CB_M0.net_0",
        "BA_M0.net_3",
        "BA_M0.net_2",
    ]


def test_3x3_left_edge_matrix_aliasing(fabric3: Fabric):
    # left-edge cells have no western neighbour: M0/M1 alias the same cell's
    # extra M2/M3 matrices instead
    ba_m0 = fabric3.matrices["BA_M0"]
    assert ba_m0.pin_nets[6] == "BA_M2.net_3"
    assert ba_m0.pin_nets[7] == "BA_M2.net_2"


def test_3x3_corner_matrix_aliasing(fabric3: Fabric):
    # AA is the only cell with six matrices; M4/M5 sit above M0/M1 and alias
    # them as their bottom neighbours, and define their own left pins
    aa_m4 = fabric3.matrices["AA_M4"]
    assert aa_m4.pin_nets[4] == "AA_M0.net_1"
    assert aa_m4.pin_nets[5] == "AA_M0.net_0"
    assert aa_m4.pin_nets[6] == "AA_M4.net_6"
    assert aa_m4.pin_nets[7] == "AA_M4.net_7"


def test_3x3_clb_input_routing(fabric3: Fabric):
    # hand-decoded from the configs: BB's A pin is fed by the north-western
    # matrices' right segments, the horizontal long line above, and the
    # direct connect from AB's X output
    sources = {s for s, _ in fabric3.reverse_neighbors("BB.net_A")}
    assert {"AA_M0.net_2", "AA_M0.net_3", "AA_M1.net_2", "AA_M1.net_3"} <= sources
    assert "global_H1.net_0" in sources
    assert "AB.net_X" in sources


def test_3x3_clb_output_routing(fabric3: Fabric):
    # BB's X output drives: direct connects north (C/D pins) and south
    # (A/B pins), its own matrices' segments, and the vertical long line
    # to its right
    dests = {d for d, _ in fabric3.neighbors("BB.net_X")}
    assert {"AB.net_C", "AB.net_D", "CB.net_A", "CB.net_B"} <= dests
    assert "BB_M0.net_1" in dests
    assert "global_V2.net_0" in dests


def test_3x3_matrix_edges_respect_legal_connections(fabric3: Fabric):
    # spot check: pins 0-2 may connect, pins 0-1 may not
    assert POSSIBLE_MATRIX_CONNECTIONS[0][2] == 1
    assert POSSIBLE_MATRIX_CONNECTIONS[0][1] == 0
    neigh = {d for d, _ in fabric3.neighbors("BB_M0.net_0")}
    assert "BB_M0.net_2" in neigh
    assert "BB_M0.net_1" not in neigh

    # property: every matrix edge corresponds to a legal pin pair
    for matrix in fabric3.matrices.values():
        for i, j in matrix.legal_connections():
            assert POSSIBLE_MATRIX_CONNECTIONS[i][j] == 1


def test_3x3_matrix_edges_are_bidirectional(fabric3: Fabric):
    matrix = fabric3.matrices["BB_M0"]
    for i, j in matrix.legal_connections():
        a, b = matrix.pin_nets[i], matrix.pin_nets[j]
        assert any(d == b for d, _ in fabric3.neighbors(a))
        assert any(d == a for d, _ in fabric3.neighbors(b))


def test_3x3_k_pin_clock_reachability(fabric3: Fabric):
    # the K (clock) pin is deliberately restricted: it is directly driven
    # only by the global clock tree and the vertical long line to the
    # cell's left. the router's clock handling relies on this.
    direct = {s for s, _ in fabric3.reverse_neighbors("BB.net_K")}
    assert direct == {"global.net_clk", "global_V1.net_1"}


def test_3x3_validation_clean(fabric3: Fabric):
    # every CLB input pin must be drivable and every output pin routable;
    # the only acceptable findings are the config-level warnings collected
    # at load time (duplicate pips, dangling references in the source data)
    issues = fabric3.validate()
    extra = [i for i in issues if i not in fabric3.warnings]
    assert extra == []


#! 8x8 fabric:
def test_8x8_site_counts(fabric8: Fabric):
    assert fabric8.grid_size == 8
    assert len(fabric8.clbs) == 64
    assert len(fabric8.io_banks) == 58
    assert len(fabric8.pips) > 4000
    assert len(fabric8.nodes) > 2000


def test_8x8_validation_clean(fabric8: Fabric):
    issues = fabric8.validate()
    extra = [i for i in issues if i not in fabric8.warnings]
    assert extra == []


def test_8x8_interior_matrix_aliasing(fabric8: Fabric):
    # same aliasing rule holds on the full grid, e.g. DD's M1
    dd_m1 = fabric8.matrices["DD_M1"]
    assert dd_m1.pin_nets[4] == "ED_M1.net_1"
    assert dd_m1.pin_nets[5] == "ED_M1.net_0"
    assert dd_m1.pin_nets[6] == "DC_M1.net_3"
    assert dd_m1.pin_nets[7] == "DC_M1.net_2"


def test_8x8_k_pin_clock_reachability(fabric8: Fabric):
    direct = {s for s, _ in fabric8.reverse_neighbors("DD.net_K")}
    assert direct == {"global.net_clk", "global_V3.net_1"}
