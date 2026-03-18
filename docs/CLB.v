// CLB.v
// XC2064 Configurable Logic Block (CLB) with the Option 2 Configuration (2x 3-input)

// 3-Input Look-Up Table (LUT)
module LUT3 #(
    parameter [7:0] INIT = 8'h00 // Truth table configuration byte
)(
    input i0,
    input i1,
    input i2,
    output o
);
    // The output is selected by using the 3 inputs as an index 
    // to the 8-bit INIT parameter.
    assign o = INIT[{i2, i1, i0}];
endmodule


// D Flip-Flop with Asynchronous Set and Reset
module DFF_SR (
    input d,
    input clk,
    input s, // Async Set
    input r, // Async Reset
    output reg q
);
    always @(posedge clk or posedge s or posedge r) begin
        if (s)
            q <= 1'b1;
        else if (r)
            q <= 1'b0;
        else
            q <= d;
    end
endmodule


// Top Level CLB Module
module XC2064_CLB #(
    // LUT Configurations
    parameter [7:0] LUT_F_INIT = 8'h00,
    parameter [7:0] LUT_G_INIT = 8'h00,
    
    // Input Routing Multiplexers
    parameter SEL_F_IN1 = 1'b0, // 0: A, 1: B
    parameter SEL_F_IN2 = 1'b0, // 0: B, 1: C
    // more wires here here (and the ones above might be wrong)
    
    // Internal CLB Routing Multiplexers
    //todo
    input  A,
    input  B,
    input  C,
    input  D,
    input  K, // Clock
    
    output X,
    output Y
);

    // todo
endmodule