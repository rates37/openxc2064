"""Hand-placed, hand-routed reference designs for verifying the device
model against the web simulator

Run `uv run python -m openxc2064.device.demo_designs` to re/generate
`simulator/test_designs/py_and_gate.json`, then import it in the web
simulator and toggle the input pads.
"""

from __future__ import annotations

from pathlib import Path

from openxc2064.synthesis.rtl_nodes import DFF, Net
from openxc2064.mapping.xc2064_primitives import CLB, IOB
from openxc2064.toolchain import compile_hdl_to_packed

from .config import DeviceConfig
from .fabric import Fabric

AND_GATE_HDL = """module and2(input clk, output reg [31:0] counter);
    always : seq @(posedge clk) begin
        counter <= counter + 1;
    end
endmodule
"""

# a T flip-flop in one CLB with no external feedback: F = ~Q (the F LUT reads
# Q through its third input mux), the DFF latches F on rising K, X exports Q
TOGGLE_FF_SETTINGS = dict(
    lut_f_init=0x55,  # F = ~mux3 for any A/B (bit index = (m1<<2)|(m2<<1)|m3)
    sel_f_in3=2,  # F's third mux reads Q
    sel_x=1,  # X = Q
    sel_clk1=2,  # clock from K
    sel_clk2=1,  # non-inverted
)


def _nearest_bank_route(
    fabric: Fabric,
    banks: list[str],
    used_nets: set[str],
    *,
    to_pin: str | None = None,
    from_pin: str | None = None,
):
    """Pick the pad bank with the shortest route (bank net_I -> to_pin, or
    from_pin -> bank net_O). Returns (bank_id, hops)."""
    best: tuple[str, list] | None = None
    for bank_id in banks:
        bank = fabric.io_banks[bank_id]
        if to_pin is not None:
            hops = fabric.find_path(bank.net("net_I"), to_pin, blocked=used_nets)
        else:
            hops = fabric.find_path(from_pin, bank.net("net_O"), blocked=used_nets)
        if hops is not None and (best is None or len(hops) < len(best[1])):
            best = (bank_id, hops)
    if best is None:
        raise RuntimeError("no routable pad bank found")
    return best


def route_single_clb_design(
    fabric: Fabric, clb: CLB, cell: str
) -> tuple[DeviceConfig, dict]:
    """Hand-place one CLB on `cell` and route its pads with shortest-path
    search: each bound input pin (positions 0-3 = A-D) from its own input
    pad, K (position 4, if bound) from a pad allowed to use the clock tree,
    and the X output to an output pad.

    Returns the DeviceConfig plus a report naming the chosen pad banks.
    """
    config = DeviceConfig(fabric)
    config.configure_clb(cell, clb)

    # candidate pads, in deterministic pad order
    candidate_banks = sorted(
        (b.id for b in fabric.io_banks.values() if b.has_pad),
        key=lambda bid: fabric.io_banks[bid].pad_index,
    )

    # the dedicated clock/oscillator distribution nets are reachable from
    # IOB inputs but must not carry general data signals (fabric policy)
    reserved_nets = fabric.reserved_nets()
    used_nets: set[str] = set()
    report: dict = {
        "cell": cell,
        "inputs": {},
        "clock": None,
        "output": None,
        "route_lengths": {},
    }

    def claim(bank_id: str, hops: list, mode: str) -> None:
        config.enable_path(hops)
        config.configure_iob(bank_id, mode)
        candidate_banks.remove(bank_id)
        for src, dst, _ in hops:
            used_nets.update((src, dst))

    # route each data input to the physical pin the packer assigned it
    for position, pin_net in enumerate(clb.inputs[:4]):
        if pin_net is None:
            continue
        target = f"{cell}.net_{'ABCD'[position]}"
        bank_id, hops = _nearest_bank_route(
            fabric, candidate_banks, used_nets | reserved_nets, to_pin=target
        )
        claim(bank_id, hops, "input")
        report["inputs"][pin_net.name] = bank_id
        report["route_lengths"][pin_net.name] = len(hops)

    # route the clock (K pin), which may legitimately ride the clock tree
    if len(clb.inputs) > 4 and clb.inputs[4] is not None:
        bank_id, hops = _nearest_bank_route(
            fabric, candidate_banks, used_nets, to_pin=f"{cell}.net_K"
        )
        claim(bank_id, hops, "input")
        report["clock"] = bank_id
        report["route_lengths"][clb.inputs[4].name] = len(hops)

    # route the CLB's X output to an output pad
    bank_id, hops = _nearest_bank_route(
        fabric, candidate_banks, used_nets | reserved_nets, from_pin=f"{cell}.net_X"
    )
    claim(bank_id, hops, "output")
    report["output"] = bank_id
    report["route_lengths"]["x"] = len(hops)

    return config, report


def build_and_gate(cell: str = "DD") -> tuple[DeviceConfig, dict]:
    """Compile y = a & b, hand-place its single CLB on `cell`, and route the
    pads with shortest-path search over the fabric graph.

    Returns the DeviceConfig plus a report naming the chosen pads.
    """
    fabric = Fabric.load("xc2064_8x8")
    packed = compile_hdl_to_packed(AND_GATE_HDL, "and2")

    clb = next(n for n in packed.nodes if isinstance(n, CLB))
    input_names = {
        iob.pad_name for iob in packed.nodes if isinstance(iob, IOB) and iob.is_input
    }

    config, report = route_single_clb_design(fabric, clb, cell)
    # sanity: the routed inputs really are the design's ports
    # assert set(report["inputs"]) == input_names
    return config, report


def build_toggle_ff(cell: str = "EE") -> tuple[DeviceConfig, dict]:
    """A hand-built T flip-flop: F = ~Q latched on rising K, Q exported on X.

    Exercises the sequential path end to end: clock pad -> clock tree -> K
    pin, the CLB clock muxes, the DFF, and the Q feedback through F's third
    input mux (no external feedback route needed).
    """
    fabric = Fabric.load("xc2064_8x8")

    clb = CLB(
        id="toggle",
        inputs=[],
        outputs=[],
        dff=DFF(id="toggle_dff", inputs=[], outputs=[]),
        **TOGGLE_FF_SETTINGS,
    )
    # detached pin binding (Node.__post_init__ cannot take the None padding;
    # the packer pads unbound pins with None the same way)
    clb.inputs = [None, None, None, None, Net("clk")]  # type: ignore[assignment]

    return route_single_clb_design(fabric, clb, cell)


def _describe(config: DeviceConfig, report: dict) -> None:
    print(f"  CLB placed on cell {report['cell']}")
    for signal, bank in report["inputs"].items():
        pad = config.fabric.io_banks[bank].pad_index
        print(f"  input  '{signal}': pad bank {bank} (pad #{pad})")
    if report["clock"]:
        bank = report["clock"]
        print(f"  clock: pad bank {bank} (pad #{config.fabric.io_banks[bank].pad_index})")
    bank = report["output"]
    print(f"  output: pad bank {bank} (pad #{config.fabric.io_banks[bank].pad_index})")
    print(f"  route lengths: {report['route_lengths']}")


def main() -> None:
    designs_dir = Path(__file__).resolve().parents[3] / "simulator" / "test_designs"

    for name, builder, blurb in (
        ("py_counter32.json", build_and_gate, "toggle the input pads; output = a AND b"),
        # ("py_toggle_ff.json", build_toggle_ff, "toggle the clock pad; output flips each rising edge"),
    ):
        config, report = builder()
        out_path = designs_dir / name
        config.save(out_path)
        print(f"wrote {out_path}")
        _describe(config, report)
        print(f"  verify: {blurb}")
        print()

    print("import these in the web simulator: cd simulator && npm run dev")


if __name__ == "__main__":
    main()
