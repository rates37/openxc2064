"""Pin assignments: the CSV pin file."""

from pathlib import Path

import pytest

from openxc2064.device import Fabric
from openxc2064.pnr import (
    ClockSource,
    ClockSourceError,
    DesignView,
    OSCILLATOR_SITE,
    PinAssignmentError,
    PinAssignments,
    PinConstraintError,
    place_and_route,
    verify_equivalence,
)
from openxc2064.pnr.constraints import coerce_pins
from openxc2064.simulator import FabricSimulator
from openxc2064.toolchain import build, compile_hdl_to_packed

COUNTER_HDL = """module counter(input clk, output reg [3:0] count);
    always : seq @(posedge clk)
        count = count + 1;
endmodule
"""

PINS = """# a counter's pins
To,Direction,Location
clk,Input,OSC
count[0],Output,N[0]
count[1],Output,N[1]
count[2],Output,N[2]
count[3],Output,N[3]
"""


@pytest.fixture(scope="module")
def fabric8() -> Fabric:
    return Fabric.load("xc2064_8x8")


@pytest.fixture(scope="module")
def fabric3() -> Fabric:
    return Fabric.load("xc2064_3x3")


@pytest.fixture(scope="module")
def packed_counter():
    return compile_hdl_to_packed(COUNTER_HDL, "counter")


def csv_of(*rows: str) -> str:
    return "To,Direction,Location\n" + "".join(f"{row}\n" for row in rows)


# ---------- parsing ----------


def test_parses_quartus_columns_and_comments():
    plan = PinAssignments.parse(PINS)
    assert [(a.signal, a.bits, a.location, a.slots, a.direction) for a in plan.assignments] == [
        ("clk", None, "OSC", None, "Input"),
        ("count", (0,), "N", (0,), "Output"),
        ("count", (1,), "N", (1,), "Output"),
        ("count", (2,), "N", (2,), "Output"),
        ("count", (3,), "N", (3,), "Output"),
    ]


def test_columns_are_matched_by_name_not_position():
    """A file exported from Quartus carries extra columns in its own order."""
    text = (
        "# Note: The column header names should not be changed\n"
        "To,I/O Standard,Location,Direction,Current Strength\n"
        "count[0],3.3-V LVTTL,N[4],Output,8mA\n"
    )
    plan = PinAssignments.parse(text)
    assert plan.assignments[0].slots == (4,)
    assert plan.assignments[0].direction == "Output"


def test_direction_is_optional():
    plan = PinAssignments.parse(csv_of("rst,,W[0]", "en[2],,E[5]"))
    assert plan.assignments[0].bits is None
    assert plan.assignments[0].direction is None
    assert plan.assignments[1].bits == (2,)
    assert plan.assignments[1].slots == (5,)


def test_range_rows_cover_a_whole_bus():
    plan = PinAssignments.parse(csv_of("count[0:3],Output,N[7:4]"))
    assert plan.assignments[0].bits == (0, 1, 2, 3)
    assert plan.assignments[0].slots == (7, 6, 5, 4)
    assert plan.assignments[0].pads == ["count[0]", "count[1]", "count[2]", "count[3]"]


# ---------- resolution against a device ----------


def test_edge_slots_resolve_to_banks(fabric8):
    pins = PinAssignments.parse(PINS).to_constraints(fabric8)
    north = fabric8.pad_banks(edge="N")
    assert pins.pins == {
        "count[0]": north[0],
        "count[1]": north[1],
        "count[2]": north[2],
        "count[3]": north[3],
    }
    assert "clk" not in pins.pins  # OSC is not a pad


def test_n0_is_the_top_left_pad_as_drawn(fabric8):
    """N[0] is the leftmost pad along the top edge. A corner cell owns pads on
    two edges, so this is AA_IO2 -- AA_IO0/IO1 are the top of the west edge."""
    plan = PinAssignments.parse(csv_of("a,,N[0]", "b,,S[0]", "c,,W[0]", "d,,E[0]"))
    pins = plan.to_constraints(fabric8).pins
    assert pins["a"] == fabric8.pad_banks(edge="N")[0] == "AA_IO2"
    assert pins["b"] == fabric8.pad_banks(edge="S")[0] == "HA_IO0"
    assert pins["c"] == fabric8.pad_banks(edge="W")[0] == "AA_IO0"
    assert pins["d"] == fabric8.pad_banks(edge="E")[0] == "AH_IO0"

    # and it really is the top-left pad on the canvas
    north = [fabric8.io_banks[b].pad_pos for b in fabric8.pad_banks(edge="N")]
    assert north[0][0] == min(x for x, _ in north)
    every = [fabric8.io_banks[b].pad_pos for b in fabric8.pad_banks()]
    assert north[0][1] == min(y for _, y in every)


def test_one_file_serves_two_fabrics(fabric8, fabric3):
    """Edge slots are device-independent, which literal bank names are not."""
    plan = PinAssignments.parse(PINS)
    on8 = plan.to_constraints(fabric8).pins
    on3 = plan.to_constraints(fabric3).pins
    assert set(on8) == set(on3)
    for pad in on8:
        assert on8[pad] in fabric8.io_banks
        assert on3[pad] in fabric3.io_banks


def test_a_literal_bank_name_still_works(fabric8):
    plan = PinAssignments.parse(csv_of("clk,,AA_IO0"))
    assert plan.to_constraints(fabric8).pins == {"clk": "AA_IO0"}


# ---------- errors, with the offending line ----------


def test_slot_out_of_range_names_the_edge_size(fabric8):
    plan = PinAssignments.parse(csv_of("count[0],Output,E[13]"), source="pins.csv")
    with pytest.raises(PinAssignmentError, match=r"pins.csv:2: E\[13\] is out of range"):
        plan.to_constraints(fabric8)


def test_out_of_range_on_a_small_fabric_but_not_a_big_one(fabric8, fabric3):
    plan = PinAssignments.parse(csv_of("count[0],,E[5]"))
    plan.to_constraints(fabric8)  # the 8x8's east edge has 13 pads
    with pytest.raises(PinAssignmentError, match="east edge has 4 pads"):
        plan.to_constraints(fabric3)


def test_width_mismatch_is_caught_when_read():
    with pytest.raises(PinAssignmentError, match=r"width mismatch .* 8 bits, N\[0:3\] is 4 slots"):
        PinAssignments.parse(csv_of("count[7:0],Output,N[0:3]"))


def test_two_signals_on_one_slot():
    with pytest.raises(PinAssignmentError, match=r"N\[2\] is claimed by both"):
        PinAssignments.parse(csv_of("count[2],,N[2]", "status[0],,N[2]"))


def test_a_signal_assigned_twice():
    with pytest.raises(PinAssignmentError, match=r"count\[1\] is assigned twice"):
        PinAssignments.parse(csv_of("count[1],,N[1]", "count[1],,S[0]"))


def test_unknown_edge_letter():
    with pytest.raises(PinAssignmentError, match="unknown edge 'Q'"):
        PinAssignments.parse(csv_of("clk,,Q[0]"))


def test_unknown_direction():
    with pytest.raises(PinAssignmentError, match="unknown direction 'Sideways'"):
        PinAssignments.parse(csv_of("clk,Sideways,N[0]"))


def test_missing_required_column():
    with pytest.raises(PinAssignmentError, match="missing the 'Location' column"):
        PinAssignments.parse("To,Direction\nclk,Input\n")


def test_a_file_that_forgot_its_header():
    """The first non-comment row is the header, so a bare data row reads as a
    (bad) header and is reported as such."""
    with pytest.raises(PinAssignmentError, match="missing the 'To' and 'Location' column"):
        PinAssignments.parse("clk,Input,OSC\n")


def test_a_file_with_no_rows_at_all():
    with pytest.raises(PinAssignmentError, match="no header row"):
        PinAssignments.parse("# just a comment\n")


def test_oscillator_cannot_take_a_bus():
    with pytest.raises(PinAssignmentError, match="OSC drives one signal"):
        PinAssignments.parse(csv_of("count[3:0],Output,OSC"))


def test_coerce_pins_rejects_a_pin_file_without_a_fabric():
    with pytest.raises(PinConstraintError, match="to_constraints"):
        coerce_pins(PinAssignments.parse(csv_of("clk,,N[0]")))


def test_direction_disagreeing_with_the_design_is_caught(fabric8, packed_counter):
    wrong = csv_of("clk,Output,W[0]", "count[0],Output,N[0]")
    with pytest.raises(PinAssignmentError, match="clk is declared Output"):
        place_and_route(
            packed_counter, fabric8, seed=0, pins=PinAssignments.parse(wrong)
        )


# ---------- the clock source travels with the file ----------


def test_file_sets_the_clock_source(fabric8, packed_counter):
    plan = PinAssignments.parse(PINS)
    assert plan.clock_source() is ClockSource.OSCILLATOR

    config, placement, _ = place_and_route(packed_counter, fabric8, seed=0, pins=plan)

    design = DesignView(packed_counter)
    assert placement.iob_sites[design.clock_net.driver[0]] == OSCILLATOR_SITE
    assert FabricSimulator(config).warnings == []
    assert verify_equivalence(packed_counter, config, placement, clock_cycles=4) > 0


def test_file_without_osc_leaves_the_clock_on_a_pad(fabric8, packed_counter):
    plan = PinAssignments.parse(csv_of("clk,Input,W[0]", "count[0:3],Output,N[0:3]"))
    assert plan.clock_source() is None

    _, placement, _ = place_and_route(packed_counter, fabric8, seed=0, pins=plan)
    design = DesignView(packed_counter)
    assert placement.iob_sites[design.clock_net.driver[0]] == fabric8.pad_banks(edge="W")[0]


def test_conflicting_file_and_clock_argument(fabric8, packed_counter):
    plan = PinAssignments.parse(PINS, source="pins.csv")
    with pytest.raises(ClockSourceError, match="assigns clk to OSC"):
        place_and_route(
            packed_counter, fabric8, seed=0, pins=plan, clock=ClockSource.PAD
        )


def test_build_accepts_a_pin_file(fabric8):
    config, placement, _ = build(
        COUNTER_HDL, "counter", fabric=fabric8, pins=PinAssignments.parse(PINS), seed=0
    )
    banks = [b for b in placement.iob_sites.values() if b != OSCILLATOR_SITE]
    assert len(banks) == 4  # four count bits; the clock costs nothing
    assert FabricSimulator(config).warnings == []


# ---------- files and back-annotation ----------


def test_from_file(tmp_path, fabric8):
    path = tmp_path / "pin_assignments.csv"
    path.write_text(PINS, encoding="utf-8")
    plan = PinAssignments.from_file(path)
    assert plan.source == str(path)
    assert plan.to_constraints(fabric8).pins["count[0]"] == fabric8.pad_banks(edge="N")[0]


def test_the_example_pin_files_parse_and_resolve(fabric8):
    """The files in examples/ are the ones readers copy, so keep them valid."""
    examples = Path(__file__).parent.parent / "examples"
    for name, width in (("counter", 55), ("six_counters", 48)):
        plan = PinAssignments.from_file(examples / name / "pin_assignments.csv")
        assert plan.clock_source() is ClockSource.OSCILLATOR
        assert len(plan.to_constraints(fabric8).pins) == width


def test_to_csv_writes_one_row_per_pin():
    text = PinAssignments.parse(csv_of("count[0:3],Output,N[4:7]")).to_csv()
    assert text.splitlines() == [
        "To,Direction,Location",
        "count[0],Output,N[4]",
        "count[1],Output,N[5]",
        "count[2],Output,N[6]",
        "count[3],Output,N[7]",
    ]


def test_from_placement_round_trips(fabric8, packed_counter):
    design = DesignView(packed_counter)
    plan = PinAssignments.parse(csv_of("clk,Input,W[0]", "count[0:3],Output,S[4:7]"))
    _, placement, _ = place_and_route(packed_counter, fabric8, seed=0, pins=plan)

    back = PinAssignments.from_placement(placement, design, fabric8)
    reparsed = PinAssignments.parse(back.to_csv())

    assert reparsed.to_constraints(fabric8).resolve(design, fabric8) == plan.to_constraints(
        fabric8
    ).resolve(design, fabric8)
    assert PinAssignments.parse(reparsed.to_csv()).to_csv() == reparsed.to_csv()


def test_from_placement_records_directions_and_the_oscillator(fabric8, packed_counter):
    design = DesignView(packed_counter)
    _, placement, _ = place_and_route(
        packed_counter, fabric8, seed=0, pins=PinAssignments.parse(PINS)
    )
    rows = PinAssignments.from_placement(placement, design, fabric8).to_csv().splitlines()

    assert rows[0] == "To,Direction,Location"
    assert "clk[0],Input,OSC" in rows
    assert sum(row.endswith(",Output,N[0]") for row in rows) == 1
    # bus bits come out in numeric order, not lexical
    bits = [r.split(",")[0] for r in rows[1:] if r.startswith("count")]
    assert bits == [f"count[{i}]" for i in range(4)]


def test_from_placement_records_a_free_placement(fabric8, packed_counter):
    """Nothing pinned: the file captures whatever the annealer chose."""
    design = DesignView(packed_counter)
    _, placement, _ = place_and_route(packed_counter, fabric8, seed=0)

    back = PinAssignments.from_placement(placement, design, fabric8)
    resolved = PinAssignments.parse(back.to_csv()).to_constraints(fabric8).resolve(
        design, fabric8
    )
    assert resolved == placement.iob_sites
