from openxc2064 import build

HDL = """module counter(input clk, output reg [3:0] count);
    always : seq @(posedge clk)
        count = count + 1;
endmodule
"""

config, placement, report = build(HDL, "counter", seed=0)

print(config)

config.save("test.json")