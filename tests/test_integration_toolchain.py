import pytest
from openxc2064.hdl import parse_hdl
from openxc2064.synthesis import HDLElaborator, Synthesiser, Optimiser, LoweringPass
from openxc2064.mapping.mapper import GreedyMapper
from openxc2064.mapping.packer import GreedyPacker
from openxc2064.simulator import RTLSimulator

def compile_hdl_to_packed_netlist(hdl_source: str, module_name: str):
    ast = parse_hdl(hdl_source)
    symbols = HDLElaborator(ast).get_library()
    netlist = Synthesiser(symbols).synthesise(module_name)
    opt_netlist = Optimiser().optimise(netlist)
    lowered_netlist = LoweringPass().run(opt_netlist)
    mapped_netlist = GreedyMapper(k_max=3).run(lowered_netlist)
    packed_netlist = GreedyPacker(max_clbs=64).run(mapped_netlist)
    return packed_netlist

def set_bus(sim: RTLSimulator, port: str, val: int, width: int = 4):
    for i in range(width):
        port_id = f"{port}[{i}]"
        net_name = sim.input_ports[port_id]
        sim.net_values[net_name] = (val >> i) & 1

def get_bus(sim: RTLSimulator, port: str, width: int = 4) -> int:
    val = 0
    for i in range(width):
        port_id = f"{port}[{i}]"
        net_name = sim.output_ports[port_id]
        val |= sim.net_values[net_name] << i
    return val

def test_full_toolchain_adder():
    hdl = """
    module adder(input [3:0] a, input [3:0] b, output [3:0] sum);
        assign sum = a + b;
    endmodule
    """
    nl = compile_hdl_to_packed_netlist(hdl, "adder")
    sim = RTLSimulator(nl)
    
    set_bus(sim, "a", 5)
    set_bus(sim, "b", 7)
    sim.step()
    assert get_bus(sim, "sum") == 12
    
    set_bus(sim, "a", 15)
    set_bus(sim, "b", 2)
    sim.step()
    assert get_bus(sim, "sum") == 1 # 17 % 16

def test_full_toolchain_registered_adder():
    hdl = """
    module adder(input [3:0] a, input [3:0] b, output reg [3:0] sum, input clk);
        always : seq @(posedge clk)
            sum = a + b;
    endmodule
    """
    nl = compile_hdl_to_packed_netlist(hdl, "adder")
    sim = RTLSimulator(nl)
    
    set_bus(sim, "a", 5)
    set_bus(sim, "b", 7)
    set_bus(sim, "clk", 0, 1)
    sim.step()
    
    set_bus(sim, "clk", 1, 1)
    sim.step()
    assert get_bus(sim, "sum") == 12

def test_full_toolchain_shift_register():
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
    nl = compile_hdl_to_packed_netlist(hdl, "shift_reg")
    sim = RTLSimulator(nl)
    
    # 0 -> 1 -> 0 -> 1
    seq = [1, 0, 1, 0]
    for bit in seq:
        set_bus(sim, "d_in", bit, 1)
        set_bus(sim, "clk", 0, 1)
        sim.step()
        set_bus(sim, "clk", 1, 1)
        sim.step()
        
    assert get_bus(sim, "q") == 0b1010

