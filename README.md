# openxc2064

An open-source toolchain and development platform for the Xilinx XC2064, the first FPGA.

It takes a Verilog-like HDL and transforms it all the way to a real, simulatable configuration of the chip: parsing, synthesis, optimisation, technology mapping, packing, placement, routing, and finally a bit-accurate simulation of the placed-and-routed fabric.

---

## Getting Started / Setup

### Installation

This project uses [uv](https://docs.astral.sh/uv/) for package management. If you don't have uv installed, you can install it using the [official uv install guide](https://docs.astral.sh/uv/getting-started/installation/).

### Setup

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/rates37/openxc2064.git
cd openxc2064
```

Install the project dependencies:

```bash
uv sync
```

### Running Tests

Run the test suite with pytest:

```bash
uv run pytest
```

### Running Code

To run Python scripts in this project with the correct environment:

```bash
uv run python <script.py>
```

To run an interactive Python repl with the correct environment:

```bash
uv run python
>>> from openxc2064 import *
```

---

## The toolchain at a high level

```
  HDL source
      │
  ┌───┴─────────────────────── FRONT END ──────────────────────────┐
  │  parse -> elaborate -> synthesise -> optimise                  │
  │                   -> lower -> optimise -> map -> pack          │
  └───┬────────────────────────────────────────────────────────────┘
      ▼
  packed netlist            CLBs + IOBs joined by logical nets
      │                     (basically a description of what exists, not where it sits)
      │
  ┌───┴─────────────────────── BACK END ───────────────────────────┐
  │  DesignView → AnnealingPlacer → PathFinderRouter               │
  └───┬────────────────────────────────────────────────────────────┘
      ▼
  DeviceConfig              enabled PIPs, switch-matrix connections,
      │                     logic-cell muxes/LUTs, IO bank modes
      │
      ├──▶ verify_equivalence   RTL netlist vs routed fabric
      ├──▶ FabricSimulator      run the routed design in Python
      ├──▶ config.save(...)     JSON → the browser web simulator
      └──▶ Todo: generate bitstream, program real chip
```

The whole flow has been combined into one call:

```python
from openxc2064 import build

HDL = """module counter(input clk, output reg [3:0] count);
    always : seq @(posedge clk)
        count = count + 1;
endmodule
"""

config, placement, report = build(HDL, "counter", seed=0)
# config is XXX
# placement is XXX
# report is XXX
```

`build` chains the front end and the back end. If you want the two halves
separately (for example to inspect or cache the packed netlist):

```python
from openxc2064.toolchain import compile_hdl_to_packed
from openxc2064.pnr import place_and_route

packed = compile_hdl_to_packed(HDL, "counter")
config, placement, report = place_and_route(packed, seed=0)
```

Both take the same optional arguments:

| argument   | what it does                                                                |
| ---------- | --------------------------------------------------------------------------- |
| `fabric`   | the device to target (defaults to `Fabric.load("xc2064_8x8")`)              |
| `seed`     | the placer's RNG seed; the whole flow is deterministic per seed             |
| `pins`     | pad -> bank constraints, see [Constraining pin assignment](#constraining-pin-assignment) |
| `placer`   | a tuned `AnnealingPlacer` instead of the default                            |
| `router`   | a tuned `PathFinderRouter`, e.g. `PathFinderRouter(max_iterations=100)` for a congested design |
| `clock`    | `ClockSource.PAD` (default) or `ClockSource.OSCILLATOR`, see [Clocking off the on-chip oscillator](#clocking-off-the-on-chip-oscillator) |

Pipeline composition can be seen in [`openxc2064/toolchain.py`](src/openxc2064/toolchain.py).

---

## The HDL

A small Verilog-like language, defined by the grammar in
[`hdl/grammar.lark`](src/openxc2064/hdl/grammar.lark).

```verilog
module alu(input [3:0] a, input [3:0] b, input sel, output reg [3:0] y);
    always : comb
        if (sel)
            y = a + b;
        else
            y = a ^ b;
endmodule
```

Supported constructs:

| Category            | Syntax                                                                                              |
| ------------------- | --------------------------------------------------------------------------------------------------- |
| Ports               | `input`, `output`, `inout`, optional `reg`, optional `[msb:lsb]`                                    |
| Declarations        | `wire x;`, `wire [7:0] bus;`, `reg q;`, `reg [3:0] count;`                                          |
| Continuous assign   | `assign y = expr;`, `assign y[2] = ...`, `assign y[3:0] = ...`                                      |
| Combinational block | `always : comb <statement>` (sensitivity inferred from the body)                                    |
| Sequential block    | `always : seq @(posedge clk) <statement>` (also `negedge`)                                          |
| Statements          | `begin ... end`, `if (...) ... else ...`, `=` and `<=`                                              |
| Operators           | `\|\|` `&&` `==` `!=` `<<` `>>` `+` `-` `*` `/` `\|` `^` `&` and unary `-` `!` `~`                  |
| Literals            | `42`, `4'b1010`, `8'hFF`, `8'o17`, `8'd9`, a sized literal needs its width (so `'hFF` doesn't parse)|
| Instances           | `adder #(.W(4)) u0 (.a(x), .b(y), .sum(s));` named params and ports                               |
| Comments            | `// line` and `/* block */`                                                                         |

Two deliberate departures from Verilog: `always` blocks are explicitly tagged `: comb` or `: seq` rather than inferred from the sensitivity list, and module instantiation requires named parameter/port connections (no positional instantiation allowed).

---

## Phase by phase

Each phase below is shown with the real numbers produced by the 4-bit counter above, so you can watch the design change shape as it goes through the different forms of representation/implementation.

### 1. Parse: text to AST

```python
from openxc2064.hdl import parse_hdl
ast = parse_hdl(HDL)          # -> [Module(name='counter', ...)]
```

A [lark](https://lark-parser.org/) grammar produces a parse tree which an `ASTBuilder` transformer rewrites into the typed AST nodes in [`hdl/ast_nodes.py`](src/openxc2064/hdl/ast_nodes.py) — `Module`, `Port`, `Assign`, `AlwaysSeq`, `BinOp`, and so on. This stage is purely syntactic: it doesn't know whether `count` is declared, or how wide it is.

### 2. Elaborate: build and validate the symbol table

```python
from openxc2064.synthesis import HDLElaborator
library = HDLElaborator(ast).get_library()
```

Elaboration walks each module and records every signal's width, direction, and `reg`-ness into a `SymbolInfo` table, then validates the design semantically. All of the following raise `HDLValidationError` here: undeclared identifiers (in expressions, assignment targets, or a sensitivity list), duplicate port/wire/reg declarations, assigning to an `input`, continuous-assigning to a `reg`, procedurally assigning to something not declared `reg`, **multiple drivers on one bit**, unknown instantiated modules or port names, and circular module instantiation. Catching these early means every later stage can assume a well-formed design. The result is a _library_ of elaborated modules, so instantiation can be resolved by name.

### 3. Synthesise: AST to word-level RTL netlist

```python
from openxc2064.synthesis import Synthesiser
netlist = Synthesiser(library).synthesise("counter")
# nodes=4  nets=4
```

The synthesiser flattens the module hierarchy (instances are inlined, with parameters substituted) and converts behavioural code into a graph of `Node`s connected by `Net`s (you can see the relevant types in the RTL netlist in [`synthesis/rtl_nodes.py`](src/openxc2064/synthesis/rtl_nodes.py)). Expressions become `LogicGate` nodes that are still **word-level**: a single `ADD` node carries the whole 4-bit addition, and `always : seq` blocks become `DFF` nodes. Nets still have a `width`.

### 4. Optimise (the first cleanup)

```python
from openxc2064.synthesis import Optimiser
netlist = Optimiser().optimise(netlist)
```

`Optimiser.optimise` runs three passes in a loop until the netlist converges:

- **dead-code trimming**: reverse-reachability from the outputs -> anything that cannot influence an output is removed from the graph
- **constant folding**: gates with fully-constant inputs are replaced by a `Constant`, which then propagates
- **logic simplification** — algebraic identities (`a & 0 → 0`, `a | 0 → a`, `a ^ 0 → a`, double negation, etc.).

Running to a fixed point matters because each pass feeds the others: folding a constant makes a gate dead, deleting it makes its driver dead, and so on.

You can see a more detailed description of this phase [here](docs/optimiser.md).

### 5. Lower: word-level to bit-level primitives

```python
from openxc2064.synthesis import LoweringPass
lowered = LoweringPass().run(netlist)
# nodes=195  gates=157
```

The FPGA has no adders — only 3-input lookup tables. Lowering expands every multi-bit net into an array of 1-bit nets and every word-level operator into a gate-level implementation: `ADD` becomes a ripple-carry chain of XOR/AND/OR, comparisons become XNOR trees, shifts become rewiring, and narrow operands are zero-extended with constant ties. The 4-node counter explodes into 195 nodes, 157 of them gates.

### 6. Optimise again

```python
lowered = Optimiser().optimise(lowered)
# nodes=11  gates=6
```

This second pass is not redundant. Lowering deliberately emits structure it knows is wasteful, such as zero-extension ties, ripple-carry seed bits (`carry_in = 0`), constant operands from literals, because emitting it uniformly is simpler than special-casing. Re-running the optimiser folds all of it away: the counter collapses from **195 nodes to 11**, and 157 gates to 6. Skipping this pass costs real silicon and since the XC2064 is so limited in this aspect, this is super important.

### 7. Technology map: map gates to 3-input LUTs

```python
from openxc2064.mapping.mapper import GreedyMapper
mapped = GreedyMapper(k_max=3).run(lowered)
# luts=5
```

The XC2064's function generators take at most three inputs, so the mapper greedily grows cones of logic backward from each gate, absorbing predecessors while the cone's input count stays <= 3, then assigns each cone into a single `LUT` node with a computed 8-bit truth table. Where a gate feeds several cones, `absorb_multi_sink_gates` (default `True`) duplicates its logic into every consumer, trading a wider fan-out on the cone's inputs for fewer LUTs overall; setting it `False` cuts at the shared net instead and gives that gate its own LUT. The counter's 6 gates become 5 LUTs.

### 8. Pack: LUTs and DFFs into device-specific CLBs and IOBs

```python
from openxc2064.mapping.packer import GreedyPacker
packed = GreedyPacker(max_clbs=64).run(mapped)
# clbs=4  iobs=5
```

A CLB is not just "two LUTs" in a grouping. It holds an F and a G function generator, one flip-flop, and critically, the two LUTs must share the block's four physical input pins A/B/C/D through a fixed network of multiplexers. Packing pairs LUTs (preferring a LUT with its own DFF, and pairs that already share inputs), then solves the pin-assignment puzzle: `route_lut` tries permutations of the cone's inputs against the A/B/C/D pins until it finds mux selects (`sel_f_in1/2/3`, `sel_g_in1/2/3`) that satisfy both LUTs simultaneously, and rejects the pairing if none exists. Top-level ports become `IOB` nodes bound to pads. Exceeding `max_clbs` raises `CapacityError`.

The result is the packed netlist: the front end's output, and the back end's input. It says what blocks exist and which wires connect them, but nothing about where on the chip or through which physical wires / switch matrices.

### 9. DesignView

```python
from openxc2064.pnr import DesignView
view = DesignView(packed)
# routable nets=6   clock net='clk[0]'
```

[`DesignView`](src/openxc2064/pnr/design_view.py) reads the packed netlist once and extracts, for every routable net, its driver and sinks as `(node, pin)` terminals — `(clb, 'X')` or `(iob, 'I')` driving; `(clb, 'A'..'D')`, `(clb, 'K')` or `(iob, 'O')` consuming. Deliberately, terminals stay logical here. They only become fabric net IDs inside the router, once placement is known.

It also acts as another validation layer, and raises `DesignError` for the following:
* a constant driving a routed net (the fabric has no VCC/GND taps, so constants must have been folded away)
* a sink with no driver
* a net with multiple drivers
* more than one clock domain
* tri-state IOBs (bidirectional pads are not supported yet)

Nets that feed a `K` pin are flagged `is_clock`, which changes how both the placer and the router treat them.

### 10. Place: simulated annealing optimisation

```python
from openxc2064.pnr import AnnealingPlacer
placement = AnnealingPlacer().run(view, fabric, seed=0)
# {'clb0': 'AH', 'clb1': 'BH', 'clb2': 'CH', 'clb3': 'DH'}
```

Placement chooses a grid cell (`AA`..`HH`) for every CLB and a pad bank for
every IOB, minimising

```
cost = Σ over data nets of HPWL(net)  −  w_direct × direct_connect_hits
```

HPWL is the half-perimeter of the net's bounding box, which is a standard cheap proxy for wire length. The second term rewards placements that land a driver and its sink on a direct connect: a dedicated pip that wires a CLB's X/Y output straight into a neighbour's A/B/C/D pin, costing no general routing at all. A hit only counts when the sink's actual packed pin matches the pip's destination pin, so the reward reflects a route the router can really take. Clock nets are excluded from the cost, because the clock rides a dedicated global clock line whose length does not depend on position.

The annealer seeds a random placement, derives its starting temperature from the spread of sampled move deltas, then repeatedly swaps/relocates blocks, accepting uphill moves with probability $\exp(-\Delta / T)$ and cooling geometrically until the acceptance ratio collapses. Costs are updated incrementally (only the nets touching the moved blocks are rescored), and an assertion at the end re-computes the full cost to guarantee the incremental updates never drifted from reality. Everything is driven by a seeded `random.Random` with sorted iteration order, so placement is bit-identical across runs and `PYTHONHASHSEED` values.

`w_direct` has a single source of truth: score a placement with `placer.cost(view, fabric, placement)` so you always measure the objective that placer actually optimised.

Pad placement is free by default, which scatters buses across the die. Pass `pins=` to nail chosen ports to chosen banks — see [Constraining pin assignment](#constraining-pin-assignment).

### 11. Route: PathFinder negotiated congestion

```python
from openxc2064.pnr import PathFinderRouter
config, report = PathFinderRouter().run(view, placement, fabric)
# hops=36  iterations=1  longline_uses=7  direct_hits=3
```

Routing turns each logical net into a driver -> sinks tree of concrete fabric hops. A net's tree grows by repeated Dijkstra from the entire current tree to the nearest unreached sink, so trunks are shared within a net for free. Edge costs favour local wires over the global long lines.

Between nets, fabric wires are exclusive. Two signals on one wire is a short. Rather than forbidding overlap outright (which makes routing order decide success), the router uses PathFinder negotiated congestion: the first iteration lets nets overuse wires, then every net touching an overused wire is ripped up and re-routed under present congestion penalties (which grow each iteration) plus history penalties (which accumulate permanently on contested wires). Nets that genuinely need a wire outbid nets that just prefer it, and the process repeats until no wire is shared or `max_iterations` is hit, at which point `RoutingError` names every contested wire.

Two fabric policies are enforced here. The dedicated clock/oscillator distribution nets are reserved: data nets may never enter them, while the clock net may use the clock line. And clock nets are routed first, so the clock claims its trunk before data congestion can complicate things. Hops are recorded in traversal order, because the `drivers` list in the output is the only carrier of true signal direction.

The `RoutingReport` carries `net_hops`, `total_hops`, `iterations`, `longline_uses` and `direct_hits`, which is useful feedback that can be used to tune the cost constants.

### 12. DeviceConfig: the configuration itself

The router's output is a [`DeviceConfig`](src/openxc2064/device/config.py): the complete programmable state of the chip:  which PIPs are enabled, which switch-matrix pin pairs are connected and in which direction, each logic cell's mux selects and LUT truth tables, and each IO bank's mode. It is the same state the web simulator imports, so it serialises straight to JSON:

```python
config.save("counter.json")
# keys: drivers, ioBanks, logicCells, pips, switchMatrices
```

The device model it is built against is [`Fabric`](src/openxc2064/device/fabric.py): every wire and every programmable switch of the chip, loaded from JSON exported out of the web simulator's config files (the ground truth for connectivity). `Fabric.load("xc2064_8x8")` is the full device; `xc2064_3x3` is a small fabric useful for fast and simpler testing.

### Additional verification: RTL vs fabric equivalence

```python
from openxc2064.pnr import verify_equivalence
checks = verify_equivalence(packed, config, placement, clock_cycles=32)
# 64 comparisons, no mismatch
```

This runs the same stimulus through two independent simulators: `RTLSimulator` on the packed netlist (what the design means) and `FabricSimulator` on the routed `DeviceConfig` (what the chip does). It requires every output pad to agree after every step. Any disagreement raises `EquivalenceError` naming the pad, the step, and the input assignment.

Stimulus is exhaustive when the design has few data inputs (<= 8 by default -> all $2^n$ vectors) and seeded-random otherwise. Crucially, a clock pad is not treated as a data bit: when the design has one, the harness drives a real protocol: for each data vector it pulses the clock low -> high for `clock_cycles` cycles and compares after each phase. Without that a sequential design would only ever see the couple of rising edges a vector sweep happens to produce, and would be poorly tested.

### Simulating the placed-and-routed design

```python
from openxc2064.simulator import FabricSimulator

sim = FabricSimulator(config)
assert sim.warnings == []

clk_bank = placement.iob_sites[clk_iob.id]
for _ in range(6):
    for level in (0, 1):
        sim.set_pad(clk_bank, level)
        sim.step()
    print(read_count(sim))      # 1, 2, 3, 4, 5, 6
```

[`FabricSimulator`](src/openxc2064/simulator/fabric_simulator.py) executes the configuration natively on the fabric graph. Instead of iterating until values settle, construction compiles the config: enabled routing edges and active device functions become a net-level dependency graph, topologically sorted once, then flattened into a list of closures over a single integer array, so a `step()` is one allocation-free pass. Logic-cell semantics (LUT index order, output muxes, clock muxes, async set/reset precedence) mirror the web simulator's `LogicCell.ts` exactly.

Construction doubles as a router-bug detector: a net with multiple drivers or a register-free combinational loop raises `FabricSimulationError`, and floating nets that something actually reads are collected in `warnings`. An empty `warnings` list is a meaningful signal that the route is sound.

### Run the design in the web simulator

The saved JSON imports directly into the browser-based simulator in [`simulator/`](simulator/), where you can toggle pads by hand and watch signals propagate through the actual switch matrices:

```bash
cd simulator && npm run dev
```

Some reference designs are generated by:

```bash
uv run python -m openxc2064.device.demo_designs
```

---

### Constraining pin assignment

By default the placer puts every top-level port on whichever pad bank minimises wire length. That is good for routing and bad for reading: an 8-bit counter's output bus ends up scattered around two edges of the die, in no particular order, which makes the result hard to follow in the web simulator or on real hardware.

`PinConstraints` optionally ties chosen pads to chosen banks. It is purely additive, pass nothing and placement behaves exactly as before.

```python
from openxc2064 import build
from openxc2064.device import Fabric
from openxc2064.pnr import PinConstraints

fabric = Fabric.load("xc2064_8x8")

# the clk input will be on the AA_IO0 IOB:
pins = PinConstraints({"clk": "AA_IO0"})

# the cout output will be on 8 consecutive IOBs on the north face of the chip:
pins.assign_bus("count", fabric.pad_banks(edge="N")[4:12])

config, placement, report = build(COUNTER_HDL, "counter", fabric=fabric, pins=pins)
```

The difference for the 8-bit counter:

| pad        | unconstrained | pinned to the north edge |
| ---------- | ------------- | ------------------------ |
| `count[0]` | `FH_IO0`      | `AB_IO0`                 |
| `count[1]` | `GH_IO1`      | `AB_IO1`                 |
| `count[2]` | `HG_IO1`      | `AC_IO0`                 |
| `count[3]` | `HG_IO0`      | `AC_IO1`                 |
| `count[4]` | `HF_IO0`      | `AD_IO0`                 |
| `count[5]` | `HE_IO0`      | `AD_IO1`                 |
| `count[6]` | `HE_IO1`      | `AE_IO0`                 |
| `count[7]` | `HD_IO1`      | `AE_IO1`                 |

Constraining pins costs nothing here, that route came out at 84 hops versus 99 unconstrained, but in general pinning trades routability for layout control, and an impossible set of pins will surface as a `RoutingError`.

### Choosing banks

`Fabric.pad_banks(edge=...)` lists pad-bearing banks in physical order, so a slice of it is a contiguous row of pads:

```python
fabric.pad_banks()             # all 58 banks, in pad order
fabric.pad_banks(edge="N")     # ['AA_IO0', 'AA_IO1', ..., 'AH_IO3']  (20)
fabric.pad_banks(edge="S")     # 16 banks, left to right
fabric.pad_banks(edge="W")     # 11 banks, top to bottom
fabric.pad_banks(edge="E")     # 11 banks, top to bottom
```

Every pad on this device sits on the perimeter. Corner cells (which own four banks rather than two) are counted as part of the north or south edge.

### Naming pads

Pad names are the bit-level names the front end produces: a scalar port `clk` becomes the pad `clk[0]`, and a bus `count` becomes `count[0]`...`count[7]`.

- `assign("clk", bank)`: a bare scalar name is accepted when it is   unambiguous, so `clk` resolves to `clk[0]`
- `assign("count[3]", bank)`: pin one bit of a bus by its exact name
- `assign_bus("count", banks)`: pin `count[i]` to `banks[i]`, the usual way to lay a bus along a row.
- `assign_buses([(port, width), ...], banks)`: lay several buses over one pool of banks, each taking the next contiguous run. Handy when a design has more than one bus to place:

```python
pins.assign_buses(
    [(f"c{i}", 8) for i in range(6)],           # six 8-bit buses
    fabric.pad_banks(edge="N") + fabric.pad_banks(edge="E"),
)
```

It raises `PinConstraintError` up front if the pool cannot hold them all.

Constraints can also be kept in a file, since `to_json()` / `from_json()` round-trip a plain `{pad: bank}` object:

```python
Path("counter.pins.json").write_text(pins.to_json())
pins = PinConstraints.from_json(Path("counter.pins.json").read_text())
```

A plain `dict` works anywhere a `PinConstraints` does:
`build(..., pins={"clk": "AA_IO0"})`.

---

### Clocking off the on-chip oscillator

By default a design's clock arrives on an input pad, which can be toggled by hand
in the web simulator. The device also has an on-chip oscillator, and
`clock=ClockSource.OSCILLATOR` sources the clock from that instead, so the web
simulator's Oscillator control drives the design directly:

```python
from openxc2064 import build
from openxc2064.pnr import ClockSource

config, placement, report = build(
    COUNTER_HDL, "counter", clock=ClockSource.OSCILLATOR
)
config.save("counter.json")   # import it, enable the Oscillator, watch it count
```

The router itself never reaches the oscillator: `global.net_osc` and
`global.net_osc_in` are reserved (`RESERVED_PREFIXES`), so no data net can
stray onto them. Routing happens as usual against the clock pad, then
[`reroute_clock_to_oscillator`](src/openxc2064/pnr/clocking.py) cuts the pad
out of the clock tree — driver record *and* the pip/matrix connection behind
it — and routes the oscillator into the same trunk over real fabric edges.
Everything downstream, the trunk fanning out to every CLB's K pin, is
untouched. You can call it directly on an already-routed config:

```python
from openxc2064.pnr import reroute_clock_to_oscillator

hookup = reroute_clock_to_oscillator(config, fabric, design, placement)
hookup.freed_bank   # 'BA_IO0': the pad the clock no longer uses
hookup.hops         # (('global.net_osc_in', 'global.net_osc'), ...)
```

`verify_equivalence` understands both clock sources, driving `global.net_osc_in`
instead of a pad when the config is oscillator-clocked, so an oscillator design
is checked against its RTL exactly like any other. In the Python simulator that
net is driven with `FabricSimulator.set_net`:

```python
sim = FabricSimulator(config)
for _ in range(6):
    for level in (0, 1):
        sim.set_net("global.net_osc_in", level)
        sim.step()
```

`ClockSourceError` is raised if the design has no clock net at all, or if its
clock is driven by something other than an input pad.

---

## Current limitations

- One clock domain per design: Multiple clock nets raise `DesignError`
- An oscillator-sourced clock still costs a pad: `ClockSource.OSCILLATOR` reroutes  after placement, so the clock port is still allocated an IOB (and then freed).  On a pad-tight design that pad is not available for data
- No tri-state / bidirectional pads: `inout` parses, but a tri-state IOB is   rejected by `DesignView` rather than silently mis-routed
- No timing analysis: Placement and routing optimise wire length and   congestion; there is no static timing model or `Fmax` figure calculated
- No bitstream generation yet: The flow ends at a `DeviceConfig` (JSON), which the fabric simulator and web simulator both consume; emitting real XC2064 bitstream bits is not yet implemented
- Cost constants are first guesses: `w_direct = 2` and the router's long-line base cost were chosen by reasoning, not measurement.
