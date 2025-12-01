# integration tests for RTL simulator using parser -> elaborator -> synthesiser -> simulator
import pytest
from openxc2064.hdl import parse_hdl
from openxc2064.synthesis import HDLElaborator, Synthesiser
from openxc2064.simulator import RTLSimulator


def test_simple_assign() -> None:
    hdl = """
        module simple_assign(input [7:0] a, output [7:0] y);
            assign y = a;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("simple_assign")

    sim = RTLSimulator(netlist)
    sim.set("a", 42)
    sim.step()
    assert sim.get("y") == 42

    sim.set("a", 67)
    sim.step()
    assert sim.get("y") == 67


def test_constant_output() -> None:

    hdl = """
        module constant_test(output [3:0] y);
            assign y = 4'b0110;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("constant_test")

    sim = RTLSimulator(netlist)
    sim.step()
    assert sim.get("y") == 6


def test_bitwise_and() -> None:
    hdl = """
        module and_gate(input [7:0] a, input [7:0] b, output [7:0] y);
            assign y = a & b;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("and_gate")

    sim = RTLSimulator(netlist)
    sim.set("a", 0b11110000)
    sim.set("b", 0b10101010)
    sim.step()
    assert sim.get("y") == 0b10100000


def test_bitwise_or() -> None:
    hdl = """
        module or_gate(input [7:0] a, input [7:0] b, output [7:0] y);
            assign y = a | b;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("or_gate")

    sim = RTLSimulator(netlist)
    sim.set("a", 0b11110000)
    sim.set("b", 0b10101010)
    sim.step()
    assert sim.get("y") == 0b11111010


def test_bitwise_xor() -> None:
    hdl = """
        module xor_gate(input [7:0] a, input [7:0] b, output [7:0] y);
            assign y = a ^ b;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("xor_gate")

    sim = RTLSimulator(netlist)
    sim.set("a", 0b11110000)
    sim.set("b", 0b10101010)
    sim.step()
    assert sim.get("y") == 0b01011010
