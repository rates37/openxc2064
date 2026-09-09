"""Clock sourcing: ClockSource.OSCILLATOR and the reroute behind it."""

import pytest

from openxc2064.device import Fabric
from openxc2064.device.fabric import OSCILLATOR_NET
from openxc2064.pnr import (
    ClockSource,
    ClockSourceError,
    DesignError,
    DesignView,
    OSCILLATOR_SITE,
    PathFinderRouter,
    PinConstraints,
    PlacementError,
    place_and_route,
    verify_equivalence,
)
from openxc2064.simulator import FabricSimulator
from openxc2064.pnr import AnnealingPlacer, oscillator_clock_iob
from openxc2064.toolchain import build, compile_hdl_to_packed

COUNTER_HDL = """module counter(input clk, output reg [3:0] count);
    always : seq @(posedge clk)
        count = count + 1;
endmodule
"""

COMBINATIONAL_HDL = """module and2(input a, input b, output y);
    assign y = a & b;
endmodule
"""

GATED_CLOCK_HDL = """module gated(input clk, input en, output reg q);
    wire g;
    assign g = clk & en;
    always : seq @(posedge g) q = ~q;
endmodule
"""


@pytest.fixture(scope="module")
def fabric8() -> Fabric:
    return Fabric.load("xc2064_8x8")


@pytest.fixture(scope="module")
def packed_counter():
    return compile_hdl_to_packed(COUNTER_HDL, "counter")


@pytest.fixture(scope="module")
def pad_clocked(packed_counter, fabric8):
    return place_and_route(packed_counter, fabric8, seed=0)


@pytest.fixture(scope="module")
def oscillator_clocked(packed_counter, fabric8):
    return place_and_route(
        packed_counter, fabric8, seed=0, clock=ClockSource.OSCILLATOR
    )


def clock_pad_net(design, placement, fabric):
    """The net_I net of whichever bank the clock pad was placed on."""
    node_id, _ = design.clock_net.driver
    return fabric.io_banks[placement.iob_sites[node_id]].net("net_I")


# ---------- the default is unchanged ----------


def test_pad_is_the_default_clock_source(pad_clocked, packed_counter, fabric8):
    config, placement, _ = pad_clocked
    design = DesignView(packed_counter)

    assert not any(src == OSCILLATOR_NET for src, _ in config.drivers)
    # the clock still leaves the pad it was routed to
    assert any(
        src == clock_pad_net(design, placement, fabric8) for src, _ in config.drivers
    )


# ---------- the oscillator hookup ----------


def test_oscillator_clock_leaves_the_pad_and_enters_the_clock_tree(
    oscillator_clocked, packed_counter, fabric8
):
    config, placement, _ = oscillator_clocked
    design = DesignView(packed_counter)

    # the oscillator drives, and no pad's input buffer does
    assert any(src == OSCILLATOR_NET for src, _ in config.drivers)
    pad_inputs = {f"{bid}.net_I" for bid in fabric8.io_banks}
    clock_sources = {src for src, dst in config.drivers if dst.endswith(".net_K")}
    assert not (clock_sources & pad_inputs)

    # and it reaches the trunk over real, connected hops rather than one
    # fabricated edge: follow the chain from the oscillator forward
    by_source: dict[str, list[str]] = {}
    for src, dst in config.drivers:
        by_source.setdefault(src, []).append(dst)
    reached, frontier = set(), [OSCILLATOR_NET]
    while frontier:
        for nxt in by_source.get(frontier.pop(), ()):
            if nxt not in reached:
                reached.add(nxt)
                frontier.append(nxt)
    k_pins = {dst for dst in reached if dst.endswith(".net_K")}
    assert k_pins, "oscillator does not reach any CLB clock pin"


def test_oscillator_hops_are_real_fabric_edges(oscillator_clocked, fabric8):
    """Every hop the reroute added exists in the fabric, in that direction."""
    config, _, _ = oscillator_clocked
    osc_hops = [
        (src, dst)
        for src, dst in config.drivers
        if src == OSCILLATOR_NET or src.startswith("global.net_osc")
    ]
    assert osc_hops
    for src, dst in osc_hops:
        assert fabric8.edge_ref(src, dst) is not None, f"{src} -> {dst} is not a fabric edge"


def test_oscillator_reroute_leaves_no_half_edited_routing(oscillator_clocked):
    """Regression: cutting the pad out must disable its pip/matrix connection
    too. A stale enabled pip with no driver (or vice versa) shows up here."""
    config, _, _ = oscillator_clocked
    sim = FabricSimulator(config)
    assert sim.warnings == []


def test_oscillator_clock_costs_no_pad(packed_counter, fabric8):
    """The whole point of binding before placement: the clock port does not
    claim one of the device's 58 pad banks."""
    design = DesignView(packed_counter)
    clock_iob = design.clock_net.driver[0]

    pad_cfg, pad_placement, _ = place_and_route(packed_counter, fabric8, seed=0)
    osc_cfg, osc_placement, _ = place_and_route(
        packed_counter, fabric8, seed=0, clock=ClockSource.OSCILLATOR
    )

    def banks(placement):
        return [b for b in placement.iob_sites.values() if b != OSCILLATOR_SITE]

    assert osc_placement.iob_sites[clock_iob] == OSCILLATOR_SITE
    assert len(banks(osc_placement)) == len(banks(pad_placement)) - 1
    # and no IO bank is configured for it, since it owns none
    assert pad_placement.iob_sites[clock_iob] not in banks(osc_placement)
    assert osc_placement.validate(design, fabric8) == []


def test_oscillator_clock_lets_a_pad_tight_design_place(fabric8):
    """A design with a port for every pad only fits once the clock stops
    needing one."""
    width = len(fabric8.pad_banks())  # 58: every pad spoken for by the bus
    hdl = f"""module wide(input clk, output reg [{width - 1}:0] count);
        always : seq @(posedge clk) count = count + 1;
    endmodule"""
    packed = compile_hdl_to_packed(hdl, "wide")

    with pytest.raises(PlacementError, match="IOBs > 58 pad banks"):
        place_and_route(packed, fabric8, seed=0)

    # the oscillator build gets past placement (routing a 100%-saturated
    # device is a separate problem, so only placement is asserted here)
    design = DesignView(packed)
    placer_out = AnnealingPlacer().run(
        design,
        fabric8,
        seed=0,
        oscillator_iobs=frozenset({oscillator_clock_iob(design)}),
    )
    assert placer_out.validate(design, fabric8) == []


def test_pinning_the_clock_and_asking_for_the_oscillator_conflicts(
    packed_counter, fabric8
):
    pins = PinConstraints({"clk": fabric8.pad_banks(edge="W")[0]})
    with pytest.raises(PlacementError, match="also sourced from the oscillator"):
        place_and_route(
            packed_counter, fabric8, seed=0, pins=pins, clock=ClockSource.OSCILLATOR
        )


# ---------- it actually clocks the design ----------


def test_oscillator_clocked_design_matches_rtl(oscillator_clocked, packed_counter):
    config, placement, _ = oscillator_clocked
    assert verify_equivalence(packed_counter, config, placement, clock_cycles=4) > 0


def test_set_net_on_the_oscillator_advances_the_counter(
    oscillator_clocked, packed_counter
):
    config, placement, _ = oscillator_clocked
    design = DesignView(packed_counter)
    sim = FabricSimulator(config)

    count_banks = [
        placement.iob_sites[node_id]
        for node_id, iob in sorted(design.iobs.items(), key=lambda kv: kv[1].pad_name)
        if iob.is_output
    ]

    def read_count() -> int:
        return sum(sim.get_pad(bank) << i for i, bank in enumerate(count_banks))

    seen = []
    for _ in range(4):
        for level in (0, 1):
            sim.set_net(OSCILLATOR_NET, level)
            sim.step()
        seen.append(read_count())
    assert seen == [1, 2, 3, 4]


# ---------- errors ----------


def test_oscillator_needs_a_clock_net(fabric8):
    packed = compile_hdl_to_packed(COMBINATIONAL_HDL, "and2")
    with pytest.raises(ClockSourceError, match="no clock net"):
        place_and_route(packed, fabric8, seed=0, clock=ClockSource.OSCILLATOR)


def test_oscillator_rejects_an_internally_generated_clock(fabric8):
    """A gated clock is driven by a CLB output, not a pad, so there is no pad
    to swap out for the oscillator."""
    packed = compile_hdl_to_packed(GATED_CLOCK_HDL, "gated")
    with pytest.raises(ClockSourceError, match="not an input pad"):
        place_and_route(packed, fabric8, seed=0, clock=ClockSource.OSCILLATOR)


# ---------- what counts as a clock ----------


def test_a_gated_clock_is_a_clock_net_and_routes(fabric8):
    """Any net reaching a K pin is the clock, even one made of logic."""
    packed = compile_hdl_to_packed(GATED_CLOCK_HDL, "gated")
    design = DesignView(packed)
    assert design.clock_net is not None
    assert design.clock_net.driver[1] in "XY"  # driven by a CLB output

    config, placement, _ = place_and_route(packed, fabric8, seed=0)
    assert FabricSimulator(config).warnings == []
    assert verify_equivalence(packed, config, placement, clock_cycles=4) > 0


def test_a_ripple_design_is_rejected_as_two_clock_domains(fabric8):
    ripple = """module ripple(input clk, output reg q0, output reg q1);
        always : seq @(posedge clk) q0 = ~q0;
        always : seq @(posedge q0)  q1 = ~q1;
    endmodule"""
    with pytest.raises(DesignError, match="multiple clock nets"):
        DesignView(compile_hdl_to_packed(ripple, "ripple"))


def test_one_net_may_be_both_clock_and_data(fabric8):
    both = """module both(input clk, input d, output reg q, output y);
        always : seq @(posedge clk) q = d;
        assign y = clk & d;
    endmodule"""
    packed = compile_hdl_to_packed(both, "both")
    design = DesignView(packed)
    clock = design.clock_net
    assert clock is not None
    assert {pin for _, pin in clock.sinks} & set("ABCD")  # data sinks too
    assert any(pin == "K" for _, pin in clock.sinks)

    config, placement, _ = place_and_route(packed, fabric8, seed=0)
    assert verify_equivalence(packed, config, placement, clock_cycles=4) > 0


def test_clock_source_accepts_the_plain_string(packed_counter, fabric8):
    config, _, _ = place_and_route(packed_counter, fabric8, seed=0, clock="oscillator")
    assert any(src == OSCILLATOR_NET for src, _ in config.drivers)


# ---------- build() plumbing ----------


def test_build_passes_clock_and_router_through(fabric8):
    class RecordingRouter(PathFinderRouter):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.calls = 0

        def run(self, *args, **kwargs):
            self.calls += 1
            return super().run(*args, **kwargs)

    router = RecordingRouter(max_iterations=50)
    config, _, _ = build(
        COUNTER_HDL,
        "counter",
        fabric=fabric8,
        pins=PinConstraints().assign_bus("count", fabric8.pad_banks(edge="N")[:4]),
        seed=0,
        router=router,
        clock=ClockSource.OSCILLATOR,
    )

    assert router.calls == 1
    assert router.max_iterations == 50
    assert any(src == OSCILLATOR_NET for src, _ in config.drivers)


def test_build_passes_placer_through(fabric8):
    from openxc2064.pnr import AnnealingPlacer

    class RecordingPlacer(AnnealingPlacer):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def run(self, *args, **kwargs):
            self.calls += 1
            return super().run(*args, **kwargs)

    placer = RecordingPlacer()
    build(COUNTER_HDL, "counter", fabric=fabric8, seed=0, placer=placer)
    assert placer.calls == 1
