import random

import pytest

from openxc2064.device import Fabric
from openxc2064.pnr.design_view import DesignView
from openxc2064.pnr.flow import compile_hdl_to_packed
from openxc2064.pnr.placement import (
    AnnealingPlacer,
    direct_connect_table,
    hpwl,
    Placement,
    placement_cost,
)

ADDER_HDL = """module adder(input [3:0] a, input [3:0] b, output [3:0] sum);
    assign sum = a + b;
endmodule
"""


@pytest.fixture(scope="module")
def fabric8() -> Fabric:
    return Fabric.load("xc2064_8x8")


@pytest.fixture(scope="module")
def fabric3() -> Fabric:
    return Fabric.load("xc2064_3x3")


@pytest.fixture(scope="module")
def adder_design():
    return DesignView(compile_hdl_to_packed(ADDER_HDL, "adder"))


def test_hpwl():
    assert hpwl([(0, 0)]) == 0
    assert hpwl([(0, 0), (2, 3)]) == 5
    assert hpwl([(1, 1), (1, 4), (3, 2)]) == 2 + 3


def test_direct_connect_table_contains_known_offsets(fabric3):
    table = direct_connect_table(fabric3)
    # hand-decoded from the configs: X drives the southern neighbour's A/B
    # pins and the northern neighbour's C/D pins
    assert (1, 0, "X", "A") in table
    assert (1, 0, "X", "B") in table
    assert (-1, 0, "X", "C") in table
    assert (-1, 0, "X", "D") in table


def test_placement_determinism_and_legality(adder_design, fabric8):
    placer = AnnealingPlacer()
    p1 = placer.run(adder_design, fabric8, seed=1)
    p2 = placer.run(adder_design, fabric8, seed=1)
    assert p1.clb_sites == p2.clb_sites
    assert p1.iob_sites == p2.iob_sites

    for placement in (p1, placer.run(adder_design, fabric8, seed=2)):
        assert placement.validate(adder_design, fabric8) == []
        # injective per site kind
        assert len(set(placement.clb_sites.values())) == len(placement.clb_sites)
        assert len(set(placement.iob_sites.values())) == len(placement.iob_sites)
        for bank_id in placement.iob_sites.values():
            assert fabric8.io_banks[bank_id].has_pad


def test_placement_beats_random(adder_design, fabric8):
    placer = AnnealingPlacer()
    placement = placer.run(adder_design, fabric8, seed=0)
    annealed = placement_cost(adder_design, fabric8, placement)

    rng = random.Random(1234)
    cells = sorted(fabric8.clbs)
    banks = sorted(
        (bid for bid, b in fabric8.io_banks.items() if b.has_pad),
        key=lambda bid: fabric8.io_banks[bid].pad_index,
    )

    random_costs = []
    for _ in range(30):
        chosen_cells = rng.sample(cells, len(adder_design.clbs))
        chosen_banks = rng.sample(banks, len(adder_design.iobs))
        candidate = Placement(
            clb_sites=dict(zip(sorted(adder_design.clbs), chosen_cells)),
            iob_sites=dict(zip(sorted(adder_design.iobs), chosen_banks)),
        )
        random_costs.append(placement_cost(adder_design, fabric8, candidate))
    random_costs.sort()
    median = random_costs[len(random_costs) // 2]

    assert annealed < median, f"annealed {annealed} not better than random median {median}"


def test_placement_roundtrips_json(adder_design, fabric8, tmp_path):
    placement = AnnealingPlacer().run(adder_design, fabric8, seed=3)
    path = tmp_path / "place.json"
    path.write_text(placement.to_json(), encoding="utf-8")
    restored = Placement.from_json(path.read_text(encoding="utf-8"))
    assert restored.clb_sites == placement.clb_sites
    assert restored.iob_sites == placement.iob_sites
