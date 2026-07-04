import itertools
import random

import pytest

from openxc2064.device import Fabric
from openxc2064.device.config import DeviceConfig
from openxc2064.mapping.xc2064_primitives import CLB
from openxc2064.synthesis.rtl_nodes import DFF, Net, Netlist
from openxc2064.simulator import RTLSimulator


@pytest.fixture(scope="module")
def fabric8() -> Fabric:
    return Fabric.load("xc2064_8x8")


@pytest.fixture(scope="module")
def fabric3() -> Fabric:
    return Fabric.load("xc2064_3x3")


def _make_clb(**kwargs) -> CLB:
    """Construct a CLB node with detached inputs/outputs (Node.__post_init__
    cannot handle the None pin padding)."""
    inputs = kwargs.pop("inputs", [None] * 5)
    outputs = kwargs.pop("outputs", [])
    clb = CLB(id=kwargs.pop("id", "clb0"), inputs=[], outputs=[], **kwargs)
    clb.inputs = inputs
    clb.outputs = outputs
    return clb


#! combinational behaviour:
def test_and_gate_demo_simulates():
    from openxc2064.device.demo_designs import build_and_gate
    from openxc2064.simulator.fabric_simulator import FabricSimulator

    config, report = build_and_gate()
    sim = FabricSimulator(config)

    a_bank = report["inputs"]["a[0]"]
    b_bank = report["inputs"]["b[0]"]
    y_bank = report["output"]

    for a_v, b_v in itertools.product([0, 1], repeat=2):
        sim.set_pad(a_bank, a_v)
        sim.set_pad(b_bank, b_v)
        sim.step()
        assert sim.get_pad(y_bank) == (a_v & b_v), f"a={a_v} b={b_v}"


def test_random_comb_clb_matches_rtl_simulator(fabric8: Fabric):
    # a randomly configured combinational CLB,
    # placed and routed on the fabric, must match the RTL simulator's
    # evaluation of the identical CLB node for every pin combination
    from openxc2064.device.demo_designs import route_single_clb_design
    from openxc2064.simulator.fabric_simulator import FabricSimulator

    rng = random.Random(2064)
    for trial in range(5):
        sels = dict(
            sel_f_in1=rng.randint(0, 1),
            sel_f_in2=rng.randint(0, 1),
            sel_f_in3=rng.randint(0, 1),  # keep combinational (no Q)
            sel_g_in1=rng.randint(0, 1),
            sel_g_in2=rng.randint(0, 1),
            sel_g_in3=rng.randint(0, 1),
            sel_x=rng.choice([0, 2]),
            lut_f_init=rng.randint(0, 255),
            lut_g_init=rng.randint(0, 255),
        )

        # fabric side: pins bound to four named signals, routed from pads
        fabric_clb = _make_clb(
            inputs=[Net("pa"), Net("pb"), Net("pc"), Net("pd"), None], **dict(sels)
        )
        config, report = route_single_clb_design(fabric8, fabric_clb, "DD")
        fsim = FabricSimulator(config)

        # RTL side: identical CLB in a plain netlist
        nl = Netlist("ref")
        pin_nets = []
        for name in ("pa", "pb", "pc", "pd"):
            net = nl.create_net(name, 1)
            nl.add_input(name, net)
            pin_nets.append(net)
        x = nl.create_net("x", 1)
        rtl_clb = _make_clb(inputs=pin_nets + [None], outputs=[x], **dict(sels))
        nl.nodes.append(rtl_clb)
        x.drivers.append(rtl_clb)
        nl.outputs.append(x)
        rsim = RTLSimulator(nl)

        for combo in itertools.product([0, 1], repeat=4):
            for name, value in zip(("pa", "pb", "pc", "pd"), combo):
                rsim.set(name, value)
                fsim.set_pad(report["inputs"][name], value)
            rsim.step()
            fsim.step()
            assert fsim.get_pad(report["output"]) == rsim.get("x"), (
                f"trial {trial}, pins {combo}, config {sels}"
            )


#! sequential behaviour:
def test_toggle_ff_demo_simulates():
    from openxc2064.device.demo_designs import build_toggle_ff
    from openxc2064.simulator.fabric_simulator import FabricSimulator

    config, report = build_toggle_ff()
    sim = FabricSimulator(config)

    clk_bank = report["clock"]
    q_bank = report["output"]

    expected = 0
    assert sim.get_pad(q_bank) == expected
    for _ in range(4):
        sim.set_pad(clk_bank, 0)
        sim.step()
        assert sim.get_pad(q_bank) == expected  # no change on falling/low
        sim.set_pad(clk_bank, 1)
        sim.step()
        expected ^= 1
        assert sim.get_pad(q_bank) == expected  # toggles on rising edge


def test_toggle_ff_matches_rtl_simulator():
    from openxc2064.device.demo_designs import TOGGLE_FF_SETTINGS, build_toggle_ff
    from openxc2064.simulator.fabric_simulator import FabricSimulator

    config, report = build_toggle_ff()
    fsim = FabricSimulator(config)

    nl = Netlist("ref")
    k = nl.create_net("k", 1)
    nl.add_input("k", k)
    x = nl.create_net("x", 1)
    clb = _make_clb(
        inputs=[None, None, None, None, k],
        outputs=[x],
        dff=DFF(id="d0", inputs=[], outputs=[]),
        **TOGGLE_FF_SETTINGS,
    )
    nl.nodes.append(clb)
    x.drivers.append(clb)
    nl.outputs.append(x)
    rsim = RTLSimulator(nl)

    for clk in (0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1):
        rsim.set("k", clk)
        rsim.step()
        fsim.set_pad(report["clock"], clk)
        fsim.step()
        assert fsim.get_pad(report["output"]) == rsim.get("x"), f"clk seq at {clk}"


#! router-bug detection:
def test_multiple_drivers_rejected(fabric3: Fabric):
    from openxc2064.simulator.fabric_simulator import (
        FabricSimulationError,
        FabricSimulator,
    )

    config = DeviceConfig(fabric3)
    for source in ("AA_M0.net_2", "AA_M0.net_3"):
        hops = fabric3.find_path(source, "BB.net_A")
        assert hops is not None
        config.enable_path(hops)

    with pytest.raises(FabricSimulationError, match="BB.net_A"):
        FabricSimulator(config)


def test_floating_read_pin_warns(fabric3: Fabric):
    from openxc2064.simulator.fabric_simulator import FabricSimulator

    config = DeviceConfig(fabric3)
    # BB's F LUT (reading A/B/C by default) drives X, X routed onward, but
    # nothing drives the pins
    clb = _make_clb(lut_f_init=0x80, sel_x=2)
    config.configure_clb("BB", clb)
    hops = fabric3.find_path("BB.net_X", "CB.net_A")
    assert hops is not None
    config.enable_path(hops)

    sim = FabricSimulator(config)
    assert any("BB.net_A" in w for w in sim.warnings)


def test_routed_combinational_loop_rejected(fabric8: Fabric):
    from openxc2064.simulator.fabric_simulator import (
        FabricSimulationError,
        FabricSimulator,
    )

    config = DeviceConfig(fabric8)
    # DD's F LUT reads pin A (default muxes) and drives X; routing X back
    # into A closes a register-free loop
    clb = _make_clb(lut_f_init=0x0F, sel_x=2)
    config.configure_clb("DD", clb)
    hops = fabric8.find_path("DD.net_X", "DD.net_A")
    assert hops is not None, "expected a fabric route from DD.net_X to DD.net_A"
    config.enable_path(hops)

    with pytest.raises(FabricSimulationError):
        FabricSimulator(config)
