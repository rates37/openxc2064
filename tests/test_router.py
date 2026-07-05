import pytest

from openxc2064.device import Fabric
from openxc2064.mapping.xc2064_primitives import IOB
from openxc2064.pnr.design_view import DesignView
from openxc2064.pnr.flow import compile_hdl_to_packed, place_and_route
from openxc2064.simulator import FabricSimulator, RTLSimulator
from openxc2064.pnr.verify import verify_equivalence


ADDER_HDL = """module adder(input [3:0] a, input [3:0] b, output [3:0] sum);
    assign sum = a + b;
endmodule
"""

REG_ADDER_HDL = """module radder(input [3:0] a, input [3:0] b, output reg [3:0] sum, input clk);
    always : seq @(posedge clk)
        sum = a + b;
endmodule
"""

SHIFT_HDL = """module shift_reg(input clk, input d_in, output reg [3:0] q);
    always : seq @(posedge clk) begin
        q[3] = q[2];
        q[2] = q[1];
        q[1] = q[0];
        q[0] = d_in;
    end
endmodule
"""

FANOUT_HDL = """module fan(input a, input b, output y1, output y2, output y3);
    assign y1 = a & b;
    assign y2 = a | b;
    assign y3 = a ^ b;
endmodule
"""

RESERVED_PREFIXES = ("global.net_clk", "global.net_osc", "global_io.")


@pytest.fixture(scope="module")
def fabric8() -> Fabric:
    return Fabric.load("xc2064_8x8")


@pytest.fixture(scope="module")
def fabric3() -> Fabric:
    return Fabric.load("xc2064_3x3")


def _route(hdl: str, top: str, fabric: Fabric, seed: int = 0):
    packed = compile_hdl_to_packed(hdl, top)
    config, placement, report = place_and_route(packed, fabric, seed=seed)
    return packed, config, placement, report


def test_adder_end_to_end(fabric8):
    packed, config, placement, report = _route(ADDER_HDL, "adder", fabric8)

    sim = FabricSimulator(config)
    assert sim.warnings == []
    assert report.total_hops > 0

    # exhaustive: 8 inputs -> 256 vectors, twice
    verify_equivalence(packed, config, placement)


def test_registered_adder_end_to_end(fabric8):
    packed, config, placement, report = _route(REG_ADDER_HDL, "radder", fabric8)
    assert FabricSimulator(config).warnings == []
    verify_equivalence(packed, config, placement, max_exhaustive_inputs=6)


def test_shift_register_clock_discipline(fabric8):
    packed = compile_hdl_to_packed(SHIFT_HDL, "shift_reg")
    view = DesignView(packed)
    config, placement, report = place_and_route(packed, fabric8, seed=0)

    clock_names = {n.name for n in view.nets if n.is_clock}
    assert len(clock_names) == 1

    for name, hops in report.net_hops.items():
        touched = {n for hop in hops for n in hop[:2]}
        if name not in clock_names:
            assert not any(
                n.startswith(RESERVED_PREFIXES) for n in touched
            ), f"data net {name} rode a reserved net"

    # the clock reaches every flip-flop's K pin
    clock_hops = report.net_hops[next(iter(clock_names))]
    k_pins = {dst for _, dst, _ in clock_hops if dst.endswith(".net_K")}
    assert len(k_pins) == 4

    verify_equivalence(packed, config, placement)


def test_fanout_net_routes_as_tree(fabric8):
    packed, config, placement, report = _route(FANOUT_HDL, "fan", fabric8)

    # no net enters the same fabric node twice
    for name, hops in report.net_hops.items():
        destinations = [dst for _, dst, _ in hops]
        assert len(destinations) == len(set(destinations)), f"net {name} revisits a node"

    verify_equivalence(packed, config, placement)


def test_small_design_on_3x3(fabric3):
    hdl = """module tiny(input [1:0] a, input [1:0] b, output [1:0] s);
        assign s = a + b;
    endmodule
    """
    packed, config, placement, report = _route(hdl, "tiny", fabric3)
    assert FabricSimulator(config).warnings == []
    verify_equivalence(packed, config, placement)


def test_unroutable_sink_raises_named_error(fabric8):
    from openxc2064.pnr.design_view import DesignView
    from openxc2064.pnr.flow import compile_hdl_to_packed
    from openxc2064.pnr.placement import AnnealingPlacer
    from openxc2064.pnr.router import PathFinderRouter, RoutingError

    packed = compile_hdl_to_packed(
        "module and2(input a, input b, output y);\n assign y = a & b;\nendmodule\n",
        "and2",
    )
    view = DesignView(packed)
    placement = AnnealingPlacer().run(view, fabric8, seed=0)

    # strangle every source that could reach the placed CLB's A and B pins
    cell = next(iter(placement.clb_sites.values()))
    reserved = set()
    for pin in ("A", "B"):
        reserved |= {s for s, _ in fabric8.reverse_neighbors(f"{cell}.net_{pin}")}

    router = PathFinderRouter(extra_reserved=reserved)
    with pytest.raises(RoutingError):
        router.run(view, placement, fabric8)


def test_counter_end_to_end(fabric8):
    # the stage-C stretch goal: an 8-bit counter from HDL through the whole
    # flow, clocked for hundreds of cycles against the RTL simulator
    hdl = """module counter(input clk, output reg [7:0] count);
        always : seq @(posedge clk)
            count = count + 1;
    endmodule
    """
    packed = compile_hdl_to_packed(hdl, "counter")
    config, placement, report = place_and_route(packed, fabric8, seed=0)

    fsim = FabricSimulator(config)
    assert fsim.warnings == []
    rsim = RTLSimulator(packed)

    clk_node = next(n for n in packed.nodes if isinstance(n, IOB) and n.is_input)
    outs = sorted(
        (n for n in packed.nodes if isinstance(n, IOB) and n.is_output),
        key=lambda n: n.pad_name,
    )

    cycles = 300
    for _ in range(cycles):
        for clk in (0, 1):
            rsim.net_values[rsim.input_ports[clk_node.pad_name]] = clk
            fsim.set_pad(placement.iob_sites[clk_node.id], clk)
            rsim.step()
            fsim.step()
            for node in outs:
                rtl_v = rsim.net_values[rsim.output_ports[node.pad_name]]
                fab_v = fsim.get_pad(placement.iob_sites[node.id])
                assert rtl_v == fab_v, f"{node.pad_name}: rtl={rtl_v} fabric={fab_v}"

    value = sum(
        fsim.get_pad(placement.iob_sites[n.id]) << i for i, n in enumerate(outs)
    )
    assert value == cycles % 256
