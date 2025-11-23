from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Net:
    # represents a single wire in the design
    name: str
    width: int = 1
    source: Node | None = None  # the component/input driving this net
    sinks: list[Node] = field(default_factory=list)  # the component inputs that this net drives

    def __repr__(self) -> str:
        return f"Net[{self.name}]"


@dataclass
class Node:
    # base class for all hardware primitives
    id: str
    inputs: list[Net]
    outputs: list[Net]

    def __post_init__(self):
        # link nets to this node
        for n in self.inputs:
            n.sinks.append(self)
        for n in self.outputs:
            # todo: maybe check for multiple drivers here?
            n.source = self


@dataclass
class LogicGate(Node):
    # represents some combinational logic function
    op: str  # one of AND, OR, XOR, NOT, MUX, BUF, ADD, SUB, NEQ, INDEX, ...

    def __repr__(self) -> str:
        inputs = list(map(lambda x: x.name, self.inputs))
        outputs = list(map(lambda x: x.name, self.outputs))
        return f"{self.id}: {self.op}({', '.join(inputs)}) -> ({', '.join(outputs)})"


@dataclass
class DFF(Node):
    # inputs: [D, CLK], output: [Q]
    edge: str = "posedge"  # either posedge or negedge
    def __repr__(self) -> str:
        d_name = self.inputs[0].name if self.inputs else "?"
        clk_name = self.inputs[1].name if len(self.inputs) > 1 else "?"
        q_name = self.outputs[0].name if self.outputs else "?"

        return f"{self.id}: DFF({self.edge}, D = {d_name}, CLK = {clk_name}) -> (Q = {q_name})"


@dataclass
class Input(Node):
    port_name: str

    def __repr__(self) -> str:
        return f"{self.id}: Input({self.port_name})"


@dataclass
class Constant(Node):
    value: int

    def __repr__(self) -> str:
        return f"{self.id}: Const({self.value})"


@dataclass
class Netlist:
    # container for a synthesised circuit

    module_name: str
    # for the top level:
    inputs: list[Net] = field(default_factory=list)
    outputs: list[Net] = field(default_factory=list)

    # for the internal circuit:
    nodes: list[Node] = field(default_factory=list)
    nets: list[Net] = field(default_factory=list)

    def create_net(self, name: str, width: int = 1) -> Net:
        n = Net(name, width)
        self.nets.append(n)
        return n

    def add_logic(self, op: str, inputs: list[Net], outputs: list[Net]) -> LogicGate:
        g = LogicGate(f"g{len(self.nodes)}", inputs, outputs, op)
        self.nodes.append(g)
        return g

    def add_dff(self, inputs: list[Net], outputs: list[Net], edge: str = "posedge") -> DFF:
        d = DFF(f"dff{len(self.nodes)}", inputs, outputs, edge=edge)
        self.nodes.append(d)
        return d

    def add_input(self, port_name: str, net: Net) -> Input:
        i = Input(f"in{len(self.nodes)}", inputs=[], outputs=[net], port_name=port_name)
        self.nodes.append(i)
        return i

    def add_const(self, value: int, net: Net) -> Constant:
        c = Constant(f"const{len(self.nodes)}", inputs=[], outputs=[net], value=value)
        self.nodes.append(c)
        return c
