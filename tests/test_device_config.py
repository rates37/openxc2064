import itertools
import json
from pathlib import Path

import pytest

from openxc2064.mapping.xc2064_primitives import CLB
from openxc2064.simulator import RTLSimulator
from openxc2064.device import Fabric
from openxc2064.toolchain import compile_hdl_to_packed as compile_to_packed

REPO_ROOT = Path(__file__).parent.parent
COUNTER_EXPORT = REPO_ROOT / "simulator" / "test_designs" / "8 bit counter.json"


def web_logic_cell_eval(muxes: dict, luts: list, a: int, b: int, c: int, d: int, q: int = 0):
    """Reference evaluation of one logic cell using the web simulator's
    semantics, ported from LogicCell.simulate in
    simulator/src/models/LogicCell.ts. luts[0] drives G, luts[1] drives F;
    the LUT index is (mux1 << 2) | (mux2 << 1) | mux3."""
    m6 = b if muxes["m6"] else a
    m8 = c if muxes["m8"] else b
    m13 = (c, d, q)[muxes["m13"]]
    g = 1 if luts[0][(m6 << 2) | (m8 << 1) | m13] else 0

    m18 = b if muxes["m18"] else a
    m20 = c if muxes["m20"] else b
    m24 = (c, d, q)[muxes["m24"]]
    f = 1 if luts[1][(m18 << 2) | (m20 << 1) | m24] else 0

    x = (g, q, f)[muxes["m59"]]
    y = (g, q, f)[muxes["m61"]]
    return x, y


# ---------- CLB translation and truth-table bit order ----------


def test_clb_evaluation_matches_web_simulator():
    # an asymmetric function: y = a & ~b. symmetric functions (AND/OR) are
    # invariant under input-bit reversal, so only an asymmetric truth table
    # can catch a bit-order mismatch between the python and web conventions
    from openxc2064.device.config import logic_cell_settings

    hdl = """module f(input a, input b, output y);
    assign y = a & !b;
endmodule
"""
    packed = compile_to_packed(hdl, "f")
    clb = next(n for n in packed.nodes if isinstance(n, CLB))
    settings = logic_cell_settings(clb)
    muxes = settings["muxes"]
    luts = settings["luts"]

    sim = RTLSimulator(packed)
    for a_v, b_v in itertools.product([0, 1], repeat=2):
        # lowering renames ports to bit level ('a' -> 'a[0]')
        sim.net_values[sim.input_ports["a[0]"]] = a_v
        sim.net_values[sim.input_ports["b[0]"]] = b_v
        sim.step()
        rtl_y = sim.net_values[sim.output_ports["y[0]"]]

        # feed the web evaluator the values on the CLB's physical pins
        pin_values = []
        for pin_net in clb.inputs[:4]:
            pin_values.append(sim.net_values[pin_net.name] if pin_net else 0)
        x, y = web_logic_cell_eval(muxes, luts, *pin_values)

        assert x == rtl_y == (a_v & (1 - b_v)), (
            f"a={a_v} b={b_v}: web sim X={x}, RTL sim y={rtl_y}"
        )


def test_logic_cell_settings_translation():
    from openxc2064.device.config import logic_cell_settings

    clb = CLB(
        id="clb0",
        inputs=[],
        outputs=[],
        lut_f_init=0xB2,
        lut_g_init=0x4D,
        sel_f_in1=1,
        sel_f_in2=0,
        sel_f_in3=2,
        sel_g_in1=0,
        sel_g_in2=1,
        sel_g_in3=1,
        sel_x=2,
        sel_y=0,
        sel_clk1=2,
        sel_clk2=1,
    )
    settings = logic_cell_settings(clb)
    muxes = settings["muxes"]

    # F is the web sim's LUT2 (m18/m20/m24 -> luts[1]); G is LUT1
    assert muxes["m18"] == 1 and muxes["m20"] == 0 and muxes["m24"] == 2
    assert muxes["m6"] == 0 and muxes["m8"] == 1 and muxes["m13"] == 1
    assert muxes["m59"] == 2  # X <- F (LogicCell.ts: m59 drives net_X)
    assert muxes["m61"] == 0  # Y <- G
    assert muxes["m51"] == 2 and muxes["m100"] == 1
    assert muxes["m46"] == 2 and muxes["m56"] == 2  # set/reset held at GND

    assert settings["luts"][0] == [bool((0x4D >> i) & 1) for i in range(8)]
    assert settings["luts"][1] == [bool((0xB2 >> i) & 1) for i in range(8)]


# ---------- DeviceConfig export ----------


@pytest.fixture(scope="module")
def fabric3() -> Fabric:
    return Fabric.load("xc2064_3x3")


@pytest.fixture(scope="module")
def fabric8() -> Fabric:
    return Fabric.load("xc2064_8x8")


def test_device_config_schema_matches_web_export(fabric8: Fabric):
    from openxc2064.device.config import DeviceConfig

    ours = DeviceConfig(fabric8).to_dict()
    reference = json.loads(COUNTER_EXPORT.read_text(encoding="utf-8"))

    assert set(ours) == set(reference)

    ref_cell = reference["logicCells"][0]
    our_cell = next(c for c in ours["logicCells"] if c["id"] == ref_cell["id"])
    assert [m["id"] for m in our_cell["muxes"]] == [m["id"] for m in ref_cell["muxes"]]
    assert [lut["id"] for lut in our_cell["luts"]] == ["lut_0", "lut_1"]
    assert all(len(lut["truthTable"]) == 8 for lut in our_cell["luts"])
    # untouched cells carry the web sim's default mux selects
    assert {m["id"]: m["select"] for m in our_cell["muxes"]} == {
        m["id"]: m["select"] for m in ref_cell["muxes"]
    }

    our_matrix = ours["switchMatrices"][0]
    # superset: the reference file predates SaveSimulation.ts gaining 'pos'
    assert set(reference["switchMatrices"][0]) <= set(our_matrix)
    assert len(our_matrix["connections"]) == 8

    assert set(ours["pips"][0]) == set(reference["pips"][0])
    assert set(ours["ioBanks"][0]) == set(reference["ioBanks"][0])


def test_enable_edges(fabric3: Fabric):
    from openxc2064.device.config import DeviceConfig

    config = DeviceConfig(fabric3)

    # a known pip (verified in test_fabric): AA_M0's right segment onto BB's A pin
    hops = fabric3.find_path("AA_M0.net_2", "BB.net_A")
    assert hops is not None and len(hops) == 1
    config.enable_path(hops)

    # a known matrix connection: BB_M0 pins 0 (top) and 2 (right)
    hops = fabric3.find_path("BB_M0.net_0", "BB_M0.net_2")
    assert hops is not None and len(hops) == 1
    config.enable_path(hops)

    out = config.to_dict()
    enabled = [(p["source"], p["destination"]) for p in out["pips"] if p["enabled"]]
    assert enabled == [("AA_M0.net_2", "BB.net_A")]

    bb_m0 = next(m for m in out["switchMatrices"] if m["id"] == "BB_M0")
    assert bb_m0["connections"][0][2] == 1  # pin 0 drives pin 2
    assert bb_m0["connections"][2][0] == 0  # direction matters

    assert {"source": "AA_M0.net_2", "destination": "BB.net_A"} in out["drivers"]
    assert {"source": "BB_M0.net_0", "destination": "BB_M0.net_2"} in out["drivers"]


def test_disable_edge_undoes_enable_edge(fabric3: Fabric):
    from openxc2064.device.config import DeviceConfig

    config = DeviceConfig(fabric3)

    pip_hops = fabric3.find_path("AA_M0.net_2", "BB.net_A")
    matrix_hops = fabric3.find_path("BB_M0.net_0", "BB_M0.net_2")
    config.enable_path(pip_hops)
    config.enable_path(matrix_hops)

    for hops in (pip_hops, matrix_hops):
        for src, dst, ref in hops:
            config.disable_edge(src, dst, ref)

    # both halves are off again: no driver record and no physical resource
    out = config.to_dict()
    assert config.drivers == []
    assert out["drivers"] == []
    assert not [p for p in out["pips"] if p["enabled"]]
    bb_m0 = next(m for m in out["switchMatrices"] if m["id"] == "BB_M0")
    assert bb_m0["connections"][0][2] == 0


def test_edge_ref_recovers_the_ref_a_hop_was_enabled_with(fabric3: Fabric):
    hops = fabric3.find_path("AA_M0.net_2", "BB.net_A")
    src, dst, ref = hops[0]
    assert fabric3.edge_ref(src, dst) == ref
    assert fabric3.edge_ref(dst, src) is None  # a one-way pip has no reverse edge


def test_find_path_avoids_blocked_nets(fabric3: Fabric):
    direct = fabric3.find_path("AA_M0.net_2", "BB.net_A")
    assert direct is not None and len(direct) == 1

    detour = fabric3.find_path(
        "AA_M0.net_2", "BB.net_A", blocked={"BB.net_A"}
    )
    assert detour is None  # target itself blocked -> unreachable


# ---------- the hand-placed, hand-routed demo design ----------


def test_demo_and_gate_builds(tmp_path):
    from openxc2064.device.demo_designs import build_and_gate

    config, report = build_and_gate()
    assert report["cell"] in config.fabric.clbs

    out = config.to_dict()
    assert any(p["enabled"] for p in out["pips"])
    assert len(out["drivers"]) > 0

    # the placed cell has a configured F LUT and exports it on X
    cell_cfg = next(c for c in out["logicCells"] if c["id"] == report["cell"])
    assert any(any(lut["truthTable"]) for lut in cell_cfg["luts"])

    # both input pads and the output pad are distinct, real pads
    # (lowering renames the ports to bit level: 'a' -> 'a[0]')
    pads = [report["inputs"]["a[0]"], report["inputs"]["b[0]"], report["output"]]
    assert len(set(pads)) == 3
    for bank_id in pads:
        assert config.fabric.io_banks[bank_id].has_pad

    # output bank drives its pad; input banks stay tri-stated
    banks = {b["id"]: {m["id"]: m["select"] for m in b["muxes"]} for b in out["ioBanks"]}
    assert banks[report["output"]]["mts"] == 2
    assert banks[report["inputs"]["a[0]"]]["mts"] == 0

    # serialises to loadable json
    path = tmp_path / "and_gate.json"
    config.save(path)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert set(loaded) == {"logicCells", "switchMatrices", "pips", "ioBanks", "drivers"}
