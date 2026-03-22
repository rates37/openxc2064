import os
from openxc2064.hdl import parse_hdl
from openxc2064.synthesis import HDLElaborator, Synthesiser, Optimiser, LoweringPass
from openxc2064.mapping.mapper import GreedyMapper
from openxc2064.mapping.packer import GreedyPacker
from openxc2064.visualisation import NetlistVisualiser

HDL_ADDER = """
module adder(input [3:0] a, input [3:0] b, output [3:0] sum);
    assign sum = a + b;
endmodule
"""

HDL_REG = """
module simple_reg(input clk, input [3:0] d, output reg [3:0] q);
    always : seq @(posedge clk)
        q = d;
endmodule
"""

HDL_OPT = """
module optimisable(input [3:0] a, input [3:0] b, output [3:0] y);
    wire [3:0] dead_wire;
    wire [3:0] always_zero;
    wire [3:0] always_a;
    
    // Dead code that doesn't feed output
    assign dead_wire = a ^ b;
    
    // Constant folding (A & 0)
    assign always_zero = b & 4'b0000;
    
    // Identity folding (A | 0)
    assign always_a = a | 4'b0000;
    
    // The final output (a ^ 0 = a)
    assign y = always_a ^ always_zero;
endmodule
"""

def main():
    vis = NetlistVisualiser()
    os.makedirs("visualisations", exist_ok=True)
    
    
    def process_hdl(hdl_str, module_name, prefix):
        print(f"\\n--- Processing {module_name} ---")
        ast = parse_hdl(hdl_str)
        symbols = HDLElaborator(ast).get_library()
        
        netlist = Synthesiser(symbols).synthesise(module_name)
        vis.generate_html(netlist, f"visualisations/{prefix}_1_ast.html")
        
        opt_netlist = Optimiser().optimise(netlist)
        vis.generate_html(opt_netlist, f"visualisations/{prefix}_2_opt.html")

        lowered_netlist = LoweringPass().run(opt_netlist)
        vis.generate_html(lowered_netlist, f"visualisations/{prefix}_3_lowered.html")
        
        mapped_netlist = GreedyMapper(k_max=3).run(lowered_netlist)
        vis.generate_html(mapped_netlist, f"visualisations/{prefix}_4_mapped.html")
        
        packed_netlist = GreedyPacker(max_clbs=64).run(mapped_netlist)
        vis.generate_html(packed_netlist, f"visualisations/{prefix}_5_packed.html")

    process_hdl(HDL_ADDER, "adder", "adder")
    process_hdl(HDL_REG, "simple_reg", "reg")
    process_hdl(HDL_OPT, "optimisable", "opt")
    
    print("Done! End-to-end tooling states rendered into 'visualisations/'.")

if __name__ == "__main__":
    main()
