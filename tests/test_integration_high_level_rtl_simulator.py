# integration tests for RTL simulator using parser -> elaborator -> synthesiser -> simulator
import pytest
from openxc2064.hdl import parse_hdl
from openxc2064.synthesis import HDLElaborator, Synthesiser
from openxc2064.simulator import RTLSimulator
from itertools import permutations


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


def test_simple_register() -> None:
    hdl = """
        module simple_reg(input clk, input [7:0] d, output reg [7:0] q);
            always : seq @(posedge clk)
                q = d;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("simple_reg")
    sim = RTLSimulator(netlist)

    # Initial state
    sim.set("d", 0)
    sim.set("clk", 0)
    sim.step()
    assert sim.get("q") == 0

    # Set data
    sim.set("d", 42)
    sim.step()
    assert sim.get("q") == 0  # Not captured yet

    # Rising edge
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 42

    # Change data while clk high
    sim.set("d", 69)
    sim.step()
    assert sim.get("q") == 42  # no change

    # Another cycle
    sim.set("clk", 0)
    sim.step()
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 69


def test_counter_with_reset() -> None:
    hdl = """
        module counter(input clk, input reset, output reg [7:0] count);
            always : seq @(posedge clk) begin
                if (reset)
                    count = 8'd0;
                else
                    count = count + 8'd1;
            end
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("counter")
    sim = RTLSimulator(netlist)

    # Reset counter
    sim.set("reset", 1)
    sim.set("clk", 0)
    sim.step()
    sim.set("clk", 1)
    sim.step()
    assert sim.get("count") == 0

    # Count
    sim.set("reset", 0)
    for i in range(1, 258):  # check overflow back to 0
        sim.set("clk", 0)
        sim.step()
        sim.set("clk", 1)
        sim.step()
        assert sim.get("count") == i % 256


def test_negedge_register() -> None:
    hdl = """
        module negedge_reg(input clk, input [7:0] d, output reg [7:0] q);
            always : seq @(negedge clk)
                q = d;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("negedge_reg")
    sim = RTLSimulator(netlist)

    # Start with clock high
    sim.set("d", 0)
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 0

    # Set data
    sim.set("d", 67)
    sim.step()
    assert sim.get("q") == 0

    # Falling edge
    sim.set("clk", 0)
    sim.step()
    assert sim.get("q") == 67

    # Rising edge (no capture)
    sim.set("d", 69)
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q") == 67


def test_mux_always() -> None:

    hdl = """
        module mux2to1(input sel, input [7:0] a, input [7:0] b, output reg [7:0] y);
            always : comb begin
                if (sel)
                    y = b;
                else
                    y = a;
            end
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("mux2to1")
    sim = RTLSimulator(netlist)

    sim.set("a", 42)
    sim.set("b", 69)

    sim.set("sel", 0)
    sim.step()
    assert sim.get("y") == 42

    sim.set("sel", 1)
    sim.step()
    assert sim.get("y") == 69


def test_priority_encoder() -> None:
    hdl = """
        module priority_encoder(input [3:0] data, output reg [1:0] out);
            always : comb begin
                if (data[3])
                    out = 2'd3;
                else if (data[2])
                    out = 2'd2;
                else if (data[1])
                    out = 2'd1;
                else
                    out = 2'd0;
            end
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("priority_encoder")
    sim = RTLSimulator(netlist)

    test_cases = [
        (0b0001, 0),
        (0b0010, 1),
        (0b0100, 2),
        (0b1000, 3),
        (0b1111, 3),
        (0b0110, 2),
    ]

    for data, expected in test_cases:
        sim.set("data", data)
        sim.step()
        assert sim.get("out") == expected


def test_alu() -> None:
    hdl = """
        module alu(input [7:0] a, input [7:0] b, input [1:0] op, output reg [7:0] result);
            always : comb begin
                if (op == 2'd0)
                    result = a + b;
                else if (op == 2'd1)
                    result = a - b;
                else if (op == 2'd2)
                    result = a & b;
                else
                    result = a | b;
            end
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("alu")
    sim = RTLSimulator(netlist)
    sim.set("a", 20)
    sim.set("b", 10)

    # ADD
    sim.set("op", 0)
    sim.step()
    assert sim.get("result") == 30

    # SUB
    sim.set("op", 1)
    sim.step()
    assert sim.get("result") == 10

    # AND
    sim.set("a", 0b11110000)
    sim.set("b", 0b10101010)
    sim.set("op", 2)
    sim.step()
    assert sim.get("result") == 0b10100000

    # OR
    sim.set("op", 3)
    sim.step()
    assert sim.get("result") == 0b11111010


def test_state_machine() -> None:
    hdl = """
        module fsm(input clk, input reset, input go, output reg done);
            reg [1:0] state;
            
            always : seq @(posedge clk) begin
                if (reset) begin
                    state = 2'd0;
                    done = 1'd0;
                end else begin
                    if (state == 2'd0) begin
                        if (go)
                            state = 2'd1;
                        done = 1'd0;
                    end else if (state == 2'd1) begin
                        state = 2'd2;
                        done = 1'd0;
                    end else if (state == 2'd2) begin
                        state = 2'd0;
                        done = 1'd1;
                    end
                end
            end
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("fsm")
    sim = RTLSimulator(netlist)

    # Helper to do a clock cycle
    def clock_cycle():
        sim.set("clk", 0)
        sim.step()
        sim.set("clk", 1)
        sim.step()

    # Reset
    sim.set("reset", 1)
    sim.set("go", 0)
    clock_cycle()
    assert sim.get("done") == 0

    # Stay idle
    sim.set("reset", 0)
    clock_cycle()
    assert sim.get("done") == 0

    # Start FSM
    sim.set("go", 1)
    clock_cycle()
    assert sim.get("done") == 0

    sim.set("go", 0)

    # Go through states
    clock_cycle()  # State 1 -> 2
    # assert sim.get("done") == 0

    clock_cycle()  # State 2 -> 0, assert done
    assert sim.get("done") == 1

    clock_cycle()  # Back to idle
    assert sim.get("done") == 0


def test_shift_register_hdl() -> None:
    hdl = """
        module shift_reg(input clk, input d_in, output reg [3:0] q);
            always : seq @(posedge clk) begin
                q[3] = q[2];
                q[2] = q[1];
                q[1] = q[0];
                q[0] = d_in;
            end
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("shift_reg")

    sim = RTLSimulator(netlist)

    # test every possible pattern
    for pattern in set(permutations([0, 0, 0, 0, 1, 1, 1, 1], 4)):
        sim.set("clk", 0)
        sim.step()
        for i, bit in enumerate(pattern):
            sim.set("d_in", bit)
            sim.set("clk", 0)
            sim.step()
            sim.set("clk", 1)
            sim.step()

            # check outputs:
            assert sim.get("q[0]") == pattern[i]
            if i >= 1:
                assert sim.get("q[1]") == pattern[i-1]
            if i >= 2:
                assert sim.get("q[2]") == pattern[i-2]
            if i >= 3:
                assert sim.get("q[3]") == pattern[i-3]


def test_simple_sequential() -> None:
    hdl = """
        module simple_sequential(input clk, input d_in, output reg [1:0] q);
            always : seq @(posedge clk) begin
                q[1] = q[0];
                q[0] = d_in;
            end
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()

    synth = Synthesiser(symbols)
    netlist = synth.synthesise("simple_sequential")

    sim = RTLSimulator(netlist)

    # test an example sequence:
    sim.set("clk", 0)
    sim.set("d_in", 0)
    sim.step()
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q[0]") == 0

    sim.set("d_in", 1)
    sim.set("clk", 0)
    sim.step()
    sim.set("clk", 1)
    sim.step()
    assert sim.get("q[0]") == 1
    assert sim.get("q[1]") == 0


def test_shift_operators() -> None:
    hdl = """
        module shifter(input [7:0] a, input [2:0] amt, output [7:0] l_res, output [7:0] r_res);
            assign l_res = a << amt;
            assign r_res = a >> amt;
        endmodule
        """

    ast = parse_hdl(hdl)
    elaborator = HDLElaborator(ast)
    symbols = elaborator.get_library()
    synth = Synthesiser(symbols)
    netlist = synth.synthesise("shifter")
    sim = RTLSimulator(netlist)

    sim.set("a", 0b00010001)  # 17
    sim.set("amt", 2)
    sim.step()
    assert sim.get("l_res") == 0b01000100  # 68
    assert sim.get("r_res") == 0b00000100  # 4

    sim.set("a", 0b11110000)
    sim.set("amt", 4)
    sim.step()
    assert sim.get("l_res") == 0b00000000  # 8bit overflow
    assert sim.get("r_res") == 0b00001111
