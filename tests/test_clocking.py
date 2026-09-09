"""Clock sourcing: ClockSource.OSCILLATOR and the reroute behind it."""

import pytest

from openxc2064.device import Fabric
from openxc2064.device.fabric import OSCILLATOR_NET
from openxc2064.pnr import (
    ClockSource,
    ClockSourceError,
    DesignView,
    PathFinderRouter,
    PinConstraints,
    place_and_route,
    reroute_clock_to_oscillator,
    verify_equivalence,
)
from openxc2064.simulator import FabricSimulator
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

    # the oscillator drives, the pad no longer does
    assert any(src == OSCILLATOR_NET for src, _ in config.drivers)
    assert not any(
        src == clock_pad_net(design, placement, fabric8) for src, _ in config.drivers
    )

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


def test_freed_pad_no_longer_feeds_the_clock(packed_counter, fabric8):
    design = DesignView(packed_counter)
    config, placement, _ = place_and_route(packed_counter, fabric8, seed=0)
    pad_net = clock_pad_net(design, placement, fabric8)
    before = [(src, dst) for src, dst in config.drivers if src == pad_net]
    assert before, "expected the pad-clocked design to drive from the pad"

    hookup = reroute_clock_to_oscillator(config, fabric8, design, placement)

    assert hookup.freed_bank == placement.iob_sites[design.clock_net.driver[0]]
    assert hookup.hops[0][0] == OSCILLATOR_NET
    assert not [(src, dst) for src, dst in config.drivers if src == pad_net]
    # the physical resources behind the old pad hops are off again
    for src, dst in before:
        ref = fabric8.edge_ref(src, dst)
        if ref[0] == "pip":
            pip = ref[1]
            assert (pip.source, pip.destination) not in config.enabled_pips


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
    pins = PinConstraints({"clk": fabric8.pad_banks(edge="W")[0]})
    config, _, _ = build(
        COUNTER_HDL,
        "counter",
        fabric=fabric8,
        pins=pins,
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
