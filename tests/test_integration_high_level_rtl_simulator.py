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


def test_bitwise_not() -> None:
    hdl = """
        module not_gate(input [7:0] a, output [7:0] y);
            assign y = ~a;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("not_gate")

    sim = RTLSimulator(netlist)
    sim.set("a", 0b10101010)
    sim.step()
    assert sim.get("y") == 0b01010101


def test_addition() -> None:
    hdl = """
        module adder(input [7:0] a, input [7:0] b, output [7:0] sum);
            assign sum = a + b;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("adder")

    sim = RTLSimulator(netlist)
    sim.set("a", 25)
    sim.set("b", 17)
    sim.step()
    assert sim.get("sum") == 42

    sim.set("a", 69)
    sim.set("b", 67)
    sim.step()
    assert sim.get("sum") == 136


def test_subtraction() -> None:
    hdl = """
        module subtractor(input [7:0] a, input [7:0] b, output [7:0] diff);
            assign diff = a - b;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("subtractor")

    sim = RTLSimulator(netlist)
    sim.set("a", 50)
    sim.set("b", 20)
    sim.step()
    assert sim.get("diff") == 30

    sim.set("a", 69)
    sim.set("b", 67)
    sim.step()
    assert sim.get("diff") == 2


def test_addition_overflow() -> None:
    hdl = """
        module adder_overflow(input [3:0] a, input [3:0] b, output [3:0] sum);
            assign sum = a + b;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("adder_overflow")

    sim = RTLSimulator(netlist)

    # 15 + 1 = 16 wraps to 0
    sim.set("a", 15)
    sim.set("b", 1)
    sim.step()
    assert sim.get("sum") == 0

    # 8 + 9 = 17 wraps to 1
    sim.set("a", 8)
    sim.set("b", 9)
    sim.step()
    assert sim.get("sum") == 1


def test_subtraction_overflow() -> None:
    hdl = """
        module subtractor_overflow(input [3:0] a, input [3:0] b, output [3:0] diff);
            assign diff = a - b;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("subtractor_overflow")
    sim = RTLSimulator(netlist)

    # 0 - 1 = -1 = 15
    sim.set("a", 0)
    sim.set("b", 1)
    sim.step()
    assert sim.get("diff") == 15

    # 0 - 2 = -2 = 14
    sim.set("a", 0)
    sim.set("b", 2)
    sim.step()
    assert sim.get("diff") == 14


def test_equality() -> None:
    hdl = """
        module eq_test(input [7:0] a, input [7:0] b, output equal);
            assign equal = (a == b);
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("eq_test")
    sim = RTLSimulator(netlist)

    sim.set("a", 10)
    sim.set("b", 10)
    sim.step()
    assert sim.get("equal") == 1

    sim.set("a", 10)
    sim.set("b", 20)
    sim.step()
    assert sim.get("equal") == 0


def test_inequality() -> None:
    hdl = """
        module neq_test(input [7:0] a, input [7:0] b, output not_equal);
            assign not_equal = (a != b);
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("neq_test")
    sim = RTLSimulator(netlist)

    sim.set("a", 10)
    sim.set("b", 20)
    sim.step()
    assert sim.get("not_equal") == 1

    sim.set("a", 10)
    sim.set("b", 10)
    sim.step()
    assert sim.get("not_equal") == 0
