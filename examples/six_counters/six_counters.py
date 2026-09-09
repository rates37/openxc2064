"""
Run with:
    uv run python examples/six_counters/six_counters.py

    It will generate six_counters.json (in the same directory as this file)
    which can then be used in the web simulator.
"""

from pathlib import Path

from openxc2064 import build
from openxc2064.pnr import PinAssignments

HERE = Path(__file__).parent

HDL = """module counter8(input clk, output reg [7:0] count);
    always : seq @(posedge clk)
        count = count + 1;
endmodule

module six_counters(input clk,
                    output [7:0] c0, output [7:0] c1, output [7:0] c2,
                    output [7:0] c3, output [7:0] c4, output [7:0] c5);
    counter8 u0(.clk(clk), .count(c0));
    counter8 u1(.clk(clk), .count(c1));
    counter8 u2(.clk(clk), .count(c2));
    counter8 u3(.clk(clk), .count(c3));
    counter8 u4(.clk(clk), .count(c4));
    counter8 u5(.clk(clk), .count(c5));
endmodule
"""

config, _, _ = build(
    HDL, "six_counters", pins=PinAssignments.from_file(HERE / "pin_assignments.csv")
)
config.save(HERE / "six_counters.json")
print(f"saved {HERE / 'six_counters.json'}")
