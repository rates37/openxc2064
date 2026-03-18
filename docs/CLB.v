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
    parameter SEL_F_IN3 = 2'b2, // 0: C, 1: D, 2: Q

    parameter SEL_G_IN1 = 1'b0, // 0: A, 1: B
    parameter SEL_G_IN2 = 1'b0, // 0: B, 1: C
    parameter SEL_G_IN3 = 2'b00, // 0: C, 1: D, 2: Q

    parameter SEL_X = 2'b00; // 0: G, 1: Q, 2: F
    parameter SEL_Y = 2'b00; // 0: G, 1: Q, 2: F

    parameter SEL_S = 2'b00; // 0: A, 1: F, 2: GND
    parameter SEL_R = 2'b00; // 0: G, 1: D, 2: GND
    
    parameter SEL_CLK1 = 2'b00; // 0: G, 1: C, 2: K
    parameter SEL_CLK2 = 2'b00; // 0: !CLK1 , 1: CLK1, 2: GND



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
    wire G, F, DFF_S, DFF_R, DFF_CLK1, DFF_Q, DFF_CLK2;

    wire [2:0] LUT_F_IN, LUT_G_IN;

    assign LUT_F_IN[0] = SEL_F_IN1 ? B : A;
    assign LUT_F_IN[1] = SEL_F_IN2 ? C : B;
    assign LUT_F_IN[2] = SEL_F_IN3[0] ? D : SEL_F_IN3[1] ? DFF_Q : C;

    assign LUT_G_IN[0] = SEL_F_IN1 ? B : A;
    assign LUT_G_IN[1] = SEL_F_IN2 ? C : B;
    assign LUT_G_IN[2] = SEL_F_IN3[0] ? D : SEL_F_IN3[1] ? DFF_Q : C;

    LUT3 #(LUT_G_INIT) LG (LUT_G_IN[0], LUT_G_IN[1], LUT_G_IN[2], G);
    LUT3 #(LUT_F_INIT) LF (LUT_F_IN[0], LUT_F_IN[1], LUT_F_IN[2], F);

    DFF DFF(F, DFF_CLK2, DFF_S, DFF_R, DFF_Q);

    assign DFF_CLK2 = SEL_CLK2[0] ? DFF_CLK1 : SEL_CLK2[1] ? 1'b0 : !DFF_CLK1;
    assign DFF_CLK1 = SEL_CLK1[0] ? C : SEL_CLK1[1] ? K : G;

    assign DFF_S = SEL_S[0] ? C : SEL_S[1] ? K : G;
    assign DFF_R = SEL_R[0] ? D : SEL_R[1] ? 1'b0 : G;

    assign X = SEL_X[0] ? DFF_Q : SEL_X[1] ? F : G;
    assign Y = SEL_Y[0] ? DFF_Q : SEL_Y[1] ? F : G;


    // todo
endmodule