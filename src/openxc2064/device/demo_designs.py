"""Hand-placed, hand-routed reference designs for verifying the device
model against the web simulator (docs/plan.md stage D vertical slice).

Run `uv run python -m openxc2064.device.demo_designs` to re/generate
`simulator/test_designs/py_and_gate.json`, then import it in the web
simulator and toggle the input pads.
"""

from __future__ import annotations

from pathlib import Path

from openxc2064.hdl import parse_hdl
from openxc2064.synthesis import HDLElaborator, Synthesiser, Optimiser, LoweringPass
from openxc2064.mapping.mapper import GreedyMapper
from openxc2064.mapping.packer import GreedyPacker
from openxc2064.mapping.xc2064_primitives import CLB, IOB

from .config import DeviceConfig
from .fabric import Fabric

AND_GATE_HDL = """module and2(input a, input b, output y);
    assign y = a & b;
endmodule
"""


def _compile(hdl: str, top: str):
    ast = parse_hdl(hdl)
    library = HDLElaborator(ast).get_library()
    netlist = Synthesiser(library).synthesise(top)
    netlist = Optimiser().optimise(netlist)
    lowered = LoweringPass().run(netlist)
    lowered = Optimiser().optimise(lowered)
    mapped = GreedyMapper(k_max=3).run(lowered)
    return GreedyPacker(max_clbs=64).run(mapped)


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


def build_and_gate(cell: str = "DD") -> tuple[DeviceConfig, dict]:
    """Compile y = a & b, hand-place its single CLB on `cell`, and route the
    pads with shortest-path search over the fabric graph.

    Returns the DeviceConfig plus a report naming the chosen pads.
    """
    fabric = Fabric.load("xc2064_8x8")
    packed = _compile(AND_GATE_HDL, "and2")

    clb = next(n for n in packed.nodes if isinstance(n, CLB))
    input_names = {
        iob.pad_name for iob in packed.nodes if isinstance(iob, IOB) and iob.is_input
    }

    config = DeviceConfig(fabric)
    config.configure_clb(cell, clb)

    # candidate pads, in deterministic pad order
    candidate_banks = sorted(
        (b.id for b in fabric.io_banks.values() if b.has_pad),
        key=lambda bid: fabric.io_banks[bid].pad_index,
    )

    # the dedicated clock/oscillator distribution nets are reachable from
    # IOB inputs but must not carry general data signals
    used_nets: set[str] = {
        net
        for net in fabric.bus_nets
        if net.startswith(("global.net_clk", "global.net_osc", "global_io."))
    }
    report: dict = {"cell": cell, "inputs": {}, "output": None, "route_lengths": {}}

    # route each logical input to the physical pin the packer assigned it
    for position, pin_net in enumerate(clb.inputs[:4]):
        if pin_net is None:
            continue
        signal = pin_net.name
        target = f"{cell}.net_{'ABCD'[position]}"
        bank_id, hops = _nearest_bank_route(
            fabric, candidate_banks, used_nets, to_pin=target
        )
        config.enable_path(hops)
        config.configure_iob(bank_id, "input")
        candidate_banks.remove(bank_id)
        for src, dst, _ in hops:
            used_nets.update((src, dst))
        report["inputs"][signal] = bank_id
        report["route_lengths"][signal] = len(hops)

    # route the CLB's X output to an output pad
    assert signal in input_names  # sanity: inputs really came from the design
    bank_id, hops = _nearest_bank_route(
        fabric, candidate_banks, used_nets, from_pin=f"{cell}.net_X"
    )
    config.enable_path(hops)
    config.configure_iob(bank_id, "output")
    report["output"] = bank_id
    report["route_lengths"]["y"] = len(hops)

    return config, report


def main() -> None:
    out_path = (
        Path(__file__).resolve().parents[3]
        / "simulator"
        / "test_designs"
        / "py_and_gate.json"
    )
    config, report = build_and_gate()
    config.save(out_path)
    print(f"wrote {out_path}")
    print(f"CLB placed on cell {report['cell']}")
    for signal, bank in report["inputs"].items():
        pad = config.fabric.io_banks[bank].pad_index
        print(f"input  '{signal}': pad bank {bank} (pad #{pad})")
    out_bank = report["output"]
    print(f"output 'y': pad bank {out_bank} (pad #{config.fabric.io_banks[out_bank].pad_index})")
    print("route lengths:", report["route_lengths"])
    print()
    print("verify: cd simulator && npm run dev, import this file, then toggle")
    print("the two input pads and watch the output pad follow a AND b.")


if __name__ == "__main__":
    main()
