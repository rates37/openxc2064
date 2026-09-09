"""Pin (pad) assignment constraints."""

import pytest

from openxc2064.device import Fabric
from openxc2064.pnr import DesignView, PinConstraintError, PinConstraints
from openxc2064.toolchain import compile_hdl_to_packed

COUNTER_HDL = """module counter(input clk, output reg [3:0] count);
    always : seq @(posedge clk)
        count = count + 1;
endmodule
"""


@pytest.fixture(scope="module")
def fabric8() -> Fabric:
    return Fabric.load("xc2064_8x8")


@pytest.fixture(scope="module")
def counter_design():
    return DesignView(compile_hdl_to_packed(COUNTER_HDL, "counter"))


def test_assign_and_assign_bus_name_pads_bitwise():
    pins = PinConstraints().assign("clk", "AA_IO0")
    pins.assign_bus("count", ["AB_IO0", "AB_IO1"])
    assert pins.pins == {
        "clk": "AA_IO0",
        "count[0]": "AB_IO0",
        "count[1]": "AB_IO1",
    }


def test_assign_buses_lays_each_bus_out_in_order():
    banks = [f"B{i}" for i in range(6)]
    pins = PinConstraints().assign_buses([("a", 2), ("b", 3)], banks)

    assert pins.pins == {
        "a[0]": "B0",
        "a[1]": "B1",
        "b[0]": "B2",
        "b[1]": "B3",
        "b[2]": "B4",
    }


def test_assign_buses_rejects_a_pool_that_is_too_small():
    with pytest.raises(PinConstraintError, match="5 pads needed"):
        PinConstraints().assign_buses([("a", 2), ("b", 3)], ["B0", "B1"])


def test_assign_buses_chains_and_shares_a_pool_with_a_scalar(fabric8):
    north = fabric8.pad_banks(edge="N")
    pins = PinConstraints({"clk": fabric8.pad_banks(edge="W")[0]})
    returned = pins.assign_buses([("count", 4)], north)

    assert returned is pins
    assert pins.pins["count[0]"] == north[0]
    assert pins.pins["count[3]"] == north[3]


def test_resolve_maps_pad_names_to_iob_nodes(counter_design, fabric8):
    north = fabric8.pad_banks(edge="N")
    pins = PinConstraints({"clk": fabric8.pad_banks(edge="W")[0]})
    pins.assign_buses([("count", 4)], north)

    resolved = pins.resolve(counter_design, fabric8)

    # every constraint lands on a distinct IOB node and its requested bank
    assert len(resolved) == 5
    assert sorted(resolved.values()) == sorted(
        [fabric8.pad_banks(edge="W")[0], *north[:4]]
    )


def test_resolve_rejects_two_pads_on_one_bank(counter_design, fabric8):
    bank = fabric8.pad_banks(edge="N")[0]
    pins = PinConstraints({"clk": bank, "count[0]": bank})
    with pytest.raises(PinConstraintError, match="claimed by both"):
        pins.resolve(counter_design, fabric8)


def test_resolve_rejects_a_bare_bus_name(counter_design, fabric8):
    pins = PinConstraints({"count": fabric8.pad_banks(edge="N")[0]})
    with pytest.raises(PinConstraintError, match="4 bits wide"):
        pins.resolve(counter_design, fabric8)


def test_constraints_roundtrip_json():
    pins = PinConstraints().assign_buses([("count", 2)], ["AB_IO0", "AB_IO1"])
    assert PinConstraints.from_json(pins.to_json()).pins == pins.pins
